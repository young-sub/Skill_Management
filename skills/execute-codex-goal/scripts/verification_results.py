# Generated file. Do not edit directly.
# Source: authoring/scripts/verification_results.py
# Source-SHA256: e8d8b3220c9208817447a6ce51281f623aa0830378181a4d614f9987f51addf2

"""Read-only viewer for plan-bound verification captures and observations.

The viewer joins an explicit plan with existing ``run_check.py`` captures,
project-adapter assessments, and raw JSON observations.  It never invokes an
argv found in a record and never writes to an evidence directory.  A result's
historical assessment is kept separate from its reuse under the current plan.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import runpy
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Iterable


CONDITION_GROUPS = ("source", "criteria", "command", "dependency", "fixture", "runtime")
STATUSES = ("PASS", "ISSUES", "BLOCKED", "SKIP", "NOT_RUN", "NOT_REQUIRED", "UNKNOWN")
SELECTIONS = ("selected", "excluded", "not_required")


class ViewerInputError(ValueError):
    """Raised when an input does not have the viewer's explicit shape."""


def _read_json(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ViewerInputError(f"Cannot read {path}: {error}") from error
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError as error:
        raise ViewerInputError(f"Invalid JSON in {path}: {error.msg}") from error


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _status(value: Any) -> str:
    """Accept only the viewer status vocabulary; ERROR is deliberately unknown."""
    if not isinstance(value, str):
        return "UNKNOWN"
    value = value.strip().upper()
    return value if value in STATUSES else "UNKNOWN"


def _status_pair(value: Any) -> tuple[str, str | None]:
    return _status(value), value if isinstance(value, str) else None


def _load_many(paths: Iterable[str | Path], label: str) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for value in paths:
        path = Path(value).resolve()
        data, raw = _read_json(path)
        if not isinstance(data, dict):
            raise ViewerInputError(f"{label} must be a JSON object: {path}")
        loaded.append({"data": data, "path": path, "sha256": _sha256(raw)})
    return loaded


def _validate_raw_plan(check: dict[str, Any], index: int, *, allow_unbound: bool = False) -> None:
    descriptors = check.get("raw_observations", [])
    if not isinstance(descriptors, list):
        raise ViewerInputError(f"checks[{index}].raw_observations must be a list")
    for descriptor_index, descriptor in enumerate(descriptors):
        if not isinstance(descriptor, dict):
            raise ViewerInputError(f"checks[{index}].raw_observations[{descriptor_index}] must be an object")
        if not _text(descriptor.get("path")) or (not allow_unbound and not _text(descriptor.get("sha256"))) or not isinstance(descriptor.get("pointer"), str):
            raise ViewerInputError(
                f"checks[{index}].raw_observations[{descriptor_index}] needs path, sha256 and pointer"
            )
        if "assertions" in descriptor and descriptor["assertions"] is not None and not isinstance(descriptor["assertions"], list):
            raise ViewerInputError(f"checks[{index}].raw_observations[{descriptor_index}].assertions must be a list")


def _plan_checks(plan: dict[str, Any], *, allow_unbound: bool = False) -> list[dict[str, Any]]:
    if plan.get("schema_version") != 1:
        raise ViewerInputError("Plan schema_version must be 1")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ViewerInputError("Plan must contain a nonempty checks list")
    identities: set[tuple[str, str]] = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ViewerInputError(f"checks[{index}] must be an object")
        for field in ("id", "feature_id", "expected", "criteria_revision", "required", "selection", "conditions"):
            if field not in check:
                raise ViewerInputError(f"checks[{index}].{field} is required")
        if not _text(check["id"]) or not _text(check["feature_id"]):
            raise ViewerInputError(f"checks[{index}] id and feature_id must be nonempty strings")
        identity = (check["feature_id"], check["id"])
        if identity in identities:
            raise ViewerInputError(f"Duplicate logical check: {identity[0]}/{identity[1]}")
        identities.add(identity)
        if not isinstance(check["expected"], str) or not check["expected"].strip():
            raise ViewerInputError(f"checks[{index}].expected must be a nonempty string")
        if not _text(check["criteria_revision"]):
            raise ViewerInputError(f"checks[{index}].criteria_revision must be a nonempty string")
        if type(check["required"]) is not bool:
            raise ViewerInputError(f"checks[{index}].required must be boolean")
        selection = check["selection"]
        if not isinstance(selection, dict) or selection.get("status") not in SELECTIONS:
            raise ViewerInputError(f"checks[{index}].selection.status must be selected, excluded or not_required")
        if not _text(selection.get("reason")):
            raise ViewerInputError(f"checks[{index}].selection.reason must be a nonempty string")
        conditions = check["conditions"]
        if not isinstance(conditions, dict):
            raise ViewerInputError(f"checks[{index}].conditions must be an object")
        for group in CONDITION_GROUPS:
            if group not in conditions:
                raise ViewerInputError(f"checks[{index}].conditions.{group} is required")
            if not isinstance(conditions[group], dict):
                raise ViewerInputError(f"checks[{index}].conditions.{group} must be an object")
        if conditions["criteria"].get("revision") != check["criteria_revision"]:
            raise ViewerInputError(f"checks[{index}].criteria_revision must match conditions.criteria.revision")
        if "run_id" in check and not _text(check["run_id"]):
            raise ViewerInputError(f"checks[{index}].run_id must be a nonempty string when supplied")
        _validate_raw_plan(check, index, allow_unbound=allow_unbound)
    return checks


def _condition_groups(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    conditions = value.get("conditions")
    if not isinstance(conditions, dict):
        return {}
    return {group: conditions[group] for group in CONDITION_GROUPS if group in conditions}


def _capture_conditions(record: dict[str, Any] | None) -> dict[str, Any]:
    if not record:
        return {}
    result = _condition_groups(record)
    command = dict(result.get("command", {})) if isinstance(result.get("command"), dict) else {}
    if "argv" in record:
        command["argv"] = record["argv"]
    if "cwd" in record:
        command["cwd"] = record["cwd"]
    if command:
        result["command"] = command
    snapshot = record.get("after") if isinstance(record.get("after"), dict) else record.get("before")
    if isinstance(snapshot, dict):
        source = dict(result.get("source", {})) if isinstance(result.get("source"), dict) else {}
        if "head" in snapshot:
            source["revision"] = snapshot["head"]
        if "tracked_diff_sha256" in snapshot:
            source["diff"] = snapshot["tracked_diff_sha256"]
        if source:
            result["source"] = source
    return result


def _assessment_conditions(data: dict[str, Any] | None) -> dict[str, Any]:
    return _condition_groups(data)


def _current_conditions(data: dict[str, Any] | None) -> dict[str, Any]:
    return _condition_groups(data)


def _missing_or_mismatched(expected: Any, actual: Any, path: str) -> list[str]:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"condition_missing:{path}"]
        findings: list[str] = []
        for key, value in expected.items():
            if key not in actual:
                findings.append(f"condition_missing:{path}.{key}")
            else:
                findings.extend(_missing_or_mismatched(value, actual[key], f"{path}.{key}"))
        return findings
    return [] if expected == actual else [f"condition_mismatch:{path}"]


def _compare_conditions(expected: dict[str, Any], actual: dict[str, Any], prefix: str) -> list[str]:
    findings: list[str] = []
    for group in CONDITION_GROUPS:
        expected_group = expected[group]
        if not expected_group or expected_group.get("status") in {"not_applicable", "unknown", "unavailable"}:
            findings.append(f"condition_missing:{prefix}.{group}: identity required")
            continue
        if group not in actual:
            findings.append(f"condition_missing:{prefix}.{group}")
        else:
            findings.extend(_missing_or_mismatched(expected_group, actual[group], f"{prefix}.{group}"))
    return findings


def _compare_present(expected: dict[str, Any], actual: dict[str, Any], prefix: str) -> list[str]:
    findings: list[str] = []
    for group, value in actual.items():
        if group in expected and expected[group].get("status") != "not_applicable":
            findings.extend(_missing_or_mismatched(expected[group], value, f"{prefix}.{group}"))
    return findings


def _combine_conditions(sources: Iterable[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for source in sources:
        for group, value in source.items():
            if group not in result:
                result[group] = value
    return result


def _json_pointer(document: Any, pointer: str) -> Any:
    if pointer in ("", "$", "/"):
        return document
    if pointer.startswith("$."):
        parts = pointer[2:].replace("[", ".").replace("]", "").split(".")
    elif pointer.startswith("/"):
        parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]
    else:
        return None
    current = document
    for part in (part for part in parts if part):
        try:
            current = current[int(part)] if isinstance(current, list) else current[part]
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    return current


def _meaningful(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _resolve(path_value: str, bases: Iterable[Path]) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    base_list = list(bases)
    for base in base_list:
        candidate = (base / path).resolve()
        if candidate.is_file():
            return candidate
    return ((base_list[0] if base_list else Path.cwd()) / path).resolve()


def _raw_descriptors(source: dict[str, Any] | None, origin: Path) -> list[dict[str, Any]]:
    if not source or "raw_observations" not in source:
        return []
    descriptors = source["raw_observations"]
    if not isinstance(descriptors, list):
        return []
    return [
        {
            "path": item.get("path"),
            "sha256": item.get("sha256"),
            "pointer": item.get("pointer"),
            "producer": item.get("producer"),
            "assertions": item.get("assertions"),
            "origin": str(origin),
        }
        for item in descriptors
        if isinstance(item, dict)
    ]


def _validate_raw(
    descriptors: list[dict[str, Any]], bases: list[Path]
) -> tuple[list[dict[str, Any]], list[str], str, set[Path]]:
    if not descriptors:
        return [], ["raw_missing: no raw observation/assertion pointer"], "UNKNOWN", set()
    verified: list[dict[str, Any]] = []
    findings: list[str] = []
    resolved_paths: set[Path] = set()
    outcome = "REUSABLE"
    for descriptor in descriptors:
        path_value = descriptor.get("path")
        expected_hash = descriptor.get("sha256")
        pointer = descriptor.get("pointer")
        if not isinstance(path_value, str) or not path_value or not isinstance(expected_hash, str) or not expected_hash or not isinstance(pointer, str):
            findings.append("raw_unlinked: path, sha256 and pointer are required")
            outcome = "UNKNOWN"
            continue
        path = _resolve(path_value, [Path(descriptor["origin"]).parent, *bases])
        resolved_paths.add(path)
        try:
            raw = path.read_bytes()
            data = json.loads(raw)
        except FileNotFoundError:
            findings.append(f"raw_missing:{path}")
            outcome = "UNKNOWN"
            continue
        except (OSError, json.JSONDecodeError) as error:
            findings.append(f"raw_unreadable:{path}:{error}")
            outcome = "UNKNOWN"
            continue
        actual_hash = _sha256(raw)
        if actual_hash.lower() != expected_hash.lower():
            findings.append(f"raw_hash_mismatch:{path}")
            outcome = "STALE"
            continue
        value = _json_pointer(data, pointer)
        if not _meaningful(value):
            findings.append(f"raw_pointer_missing:{path}#{pointer}")
            outcome = "UNKNOWN"
            continue
        assertions = descriptor.get('assertions')
        observations = []
        if not isinstance(assertions, list) or not assertions:
            findings.append(f'raw_assertions_missing:{path}')
        else:
            for assertion in assertions:
                if not isinstance(assertion, dict) or not isinstance(assertion.get('pointer'), str):
                    findings.append(f'raw_assertion_invalid:{path}')
                    continue
                actual = _json_pointer(data, assertion['pointer'])
                if 'equals' in assertion:
                    matched = type(actual) is type(assertion['equals']) and actual == assertion['equals']
                elif 'min_count' in assertion:
                    matched = (isinstance(actual, list) and type(assertion['min_count']) is int
                               and assertion['min_count'] > 0 and len(actual) >= assertion['min_count'])
                elif 'min' in assertion:
                    matched = (type(actual) in (int, float) and type(assertion['min']) in (int, float)
                               and assertion['min'] > 0 and actual >= assertion['min'])
                else:
                    matched = False
                observations.append({'assertion': assertion, 'actual': actual, 'matched': matched})
                if not matched:
                    findings.append(f"raw_assertion_mismatch:{path}#{assertion['pointer']}")
        verified.append({
            "path": str(path),
            "sha256": actual_hash,
            "pointer": pointer,
            "producer": descriptor.get("producer"),
            "origin": descriptor["origin"],
            "observations": observations,
            "original_status": data.get("status") if isinstance(data, dict) else None,
        })
    if findings and outcome == "REUSABLE":
        outcome = "UNKNOWN"
    return verified, findings, outcome, resolved_paths


def _validate_raw_producers(
    descriptors: list[dict[str, Any]],
    record_entry: dict[str, Any] | None,
    record: dict[str, Any] | None,
    bases: list[Path],
) -> list[str]:
    """Bind each raw pointer to the selected capture or its native report.

    A raw path and hash establish file identity only.  Current reuse also
    needs an explicit producer declaration so an unrelated PASS artifact
    cannot be attached to a different run.
    """
    findings: list[str] = []
    for descriptor in descriptors:
        producer = descriptor.get("producer")
        if not isinstance(producer, dict):
            findings.append("raw_producer_missing")
            continue
        if not record_entry or not record:
            findings.append("raw_producer_capture_missing")
            continue
        if producer.get("run_id") != record.get("run_id"):
            findings.append("raw_producer_run_mismatch")
        capture_path = producer.get("capture_path")
        if not isinstance(capture_path, str) or not capture_path:
            findings.append("raw_producer_capture_path_missing")
        else:
            resolved_capture = _resolve(capture_path, [Path(descriptor["origin"]).parent, *bases])
            if resolved_capture != record_entry["path"]:
                findings.append("raw_producer_capture_path_mismatch")
        if producer.get("capture_sha256") is not None and producer.get("capture_sha256") != record_entry.get("sha256"):
            findings.append("raw_producer_capture_hash_mismatch")

        invocation = producer.get("argv")
        report_path = producer.get("json_report_path")
        report_hash = producer.get("json_report_sha256")
        if invocation is None and report_path is None and report_hash is None:
            findings.append("raw_producer_invocation_missing")
        if invocation is not None and invocation != record.get("argv"):
            findings.append("raw_producer_argv_mismatch")
        if report_path is not None or report_hash is not None:
            report = record.get("json_report")
            if not isinstance(report, dict):
                findings.append("raw_producer_report_missing")
            else:
                if not isinstance(report_path, str) or not report_path:
                    findings.append("raw_producer_report_path_missing")
                else:
                    resolved_report = _resolve(report_path, [Path(descriptor["origin"]).parent, *bases])
                    actual_report_path = report.get("path")
                    if not isinstance(actual_report_path, str) or _resolve(actual_report_path, bases) != resolved_report:
                        findings.append("raw_producer_report_path_mismatch")
                    if descriptor.get("path") and _resolve(str(descriptor["path"]), bases) != resolved_report:
                        findings.append("raw_producer_raw_path_mismatch")
                if report_hash != report.get("sha256"):
                    findings.append("raw_producer_report_hash_mismatch")
                if descriptor.get("sha256") and descriptor.get("sha256") != report.get("sha256"):
                    findings.append("raw_producer_raw_hash_mismatch")
    return findings


def _find_entry(
    entries: list[dict[str, Any]], feature: str, check: str, run_id: str | None
) -> dict[str, Any] | None:
    matches = [
        entry
        for entry in entries
        if entry["data"].get("feature") == feature and entry["data"].get("check") == check
    ]
    if run_id is not None:
        matches = [entry for entry in matches if entry["data"].get("run_id") == run_id]
    return matches[0] if len(matches) == 1 else None


def _has_target(entries: list[dict[str, Any]], feature: str, check: str) -> bool:
    return any(entry["data"].get("feature") == feature and entry["data"].get("check") == check for entry in entries)


def _entry_data(entry: dict[str, Any] | None) -> dict[str, Any] | None:
    return entry["data"] if entry else None


def _assessment_binds_capture(
    assessment_entry: dict[str, Any] | None, record_entry: dict[str, Any] | None, plan_path: Path
) -> bool:
    if not assessment_entry or not record_entry:
        return False
    assessment = assessment_entry["data"]
    evidence = assessment.get("evidence")
    if assessment.get("check") is not None or not isinstance(evidence, str):
        return False
    return _resolve(evidence, [assessment_entry["path"].parent, plan_path.parent]) == record_entry["path"]


def _validate_assessment_evidence(
    assessment_entry: dict[str, Any] | None,
    record_entry: dict[str, Any] | None,
    plan_path: Path,
) -> list[str]:
    if not assessment_entry or "evidence" not in assessment_entry["data"]:
        return []
    assessment = assessment_entry["data"]
    findings: list[str] = []
    evidence = assessment.get("evidence")
    if not isinstance(evidence, str) or not evidence:
        return ["assessment_evidence_path_missing"]
    if not record_entry:
        return ["assessment_evidence_capture_missing"]
    path = _resolve(evidence, [assessment_entry["path"].parent, plan_path.parent])
    if path != record_entry["path"]:
        findings.append("assessment_evidence_path_mismatch")
    evidence_hash = assessment.get("evidence_sha256", assessment.get("sha256"))
    if not isinstance(evidence_hash, str) or not evidence_hash:
        findings.append("assessment_evidence_hash_missing")
    elif evidence_hash.lower() != str(record_entry["sha256"]).lower():
        findings.append("assessment_evidence_hash_mismatch")
    return findings


def _historical(
    record: dict[str, Any] | None,
    assessment: dict[str, Any] | None,
    observation: dict[str, Any] | None,
    raw: list[dict[str, Any]],
) -> tuple[str, str, list[str]]:
    sources: list[tuple[str, str]] = []
    if assessment is not None:
        sources.append(("assessment", _status(assessment.get("status"))))
    if observation is not None:
        sources.append(("observation", _status(observation.get("status"))))
    for item in raw:
        if item["original_status"] is not None:
            sources.append((f"raw:{item['path']}", _status(item["original_status"])))
    if sources:
        statuses = [status for _, status in sources]
        if "BLOCKED" in statuses:
            status = "BLOCKED"
        elif "ISSUES" in statuses:
            status = "ISSUES"
        elif "UNKNOWN" in statuses:
            status = "UNKNOWN"
        elif "SKIP" in statuses:
            status = "SKIP"
        elif "NOT_RUN" in statuses:
            status = "NOT_RUN"
        elif "NOT_REQUIRED" in statuses:
            status = "NOT_REQUIRED"
        else:
            status = "PASS"
        return status, "+".join(source for source, _ in sources), statuses
    if record is None:
        return "NOT_RUN", "missing", ["NOT_RUN"]
    if record.get("execution") in {"timeout", "unavailable"}:
        return "BLOCKED", "capture.execution", ["BLOCKED"]
    # run_check deliberately leaves behavior_verdict unset; a submitted value
    # or a nonzero exit alone is not a product assessment.
    return "UNKNOWN", "capture", ["UNKNOWN"]


def _selection(check: dict[str, Any]) -> tuple[bool, str | None]:
    selection = check["selection"]
    return selection["status"] == "selected", selection.get("reason") if isinstance(selection.get("reason"), str) else None


def _item_result(
    check: dict[str, Any],
    plan_path: Path,
    records: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    current: dict[str, Any] | None,
) -> dict[str, Any]:
    feature = check["feature_id"]
    check_id = check["id"]
    selected, selection_reason = _selection(check)
    required = check["required"]
    requested_run = _text(check.get("run_id"))
    record_entry = _find_entry(records, feature, check_id, requested_run)
    record = _entry_data(record_entry)
    run_id = _text(record.get("run_id")) if record else requested_run
    plan_descriptors = _raw_descriptors(check, plan_path)
    raw_hint_bases = [plan_path.parent]
    if record and isinstance(record.get("cwd"), str):
        raw_hint_bases.insert(0, Path(record["cwd"]))
    assessment_entry = _find_entry(assessments, feature, check_id, run_id)
    observation_entry = _find_entry(observations, feature, check_id, run_id)
    if observation_entry is None and plan_descriptors:
        raw_hint_paths = {
            _resolve(str(descriptor["path"]), raw_hint_bases)
            for descriptor in plan_descriptors
            if isinstance(descriptor.get("path"), str)
        }
        raw_matches = [entry for entry in observations if entry["path"] in raw_hint_paths]
        if len(raw_matches) == 1:
            # verify-flows.mjs writes status/checks but has no project identity;
            # the plan's explicit raw pointer supplies that missing binding.
            observation_entry = raw_matches[0]
    assessment = _entry_data(assessment_entry)
    observation = _entry_data(observation_entry)
    expected_conditions = check["conditions"]
    reasons: list[str] = []

    fallback_descriptors = _raw_descriptors(assessment, assessment_entry["path"] if assessment_entry else plan_path)
    fallback_descriptors.extend(_raw_descriptors(observation, observation_entry["path"] if observation_entry else plan_path))
    descriptors = plan_descriptors or fallback_descriptors
    bases = [plan_path.parent]
    for entry in (record_entry, assessment_entry, observation_entry):
        if entry:
            bases.append(entry["path"].parent)
    if record and isinstance(record.get("cwd"), str):
        bases.insert(0, Path(record["cwd"]))
    raw, raw_findings, raw_outcome, raw_paths = _validate_raw(descriptors, bases)
    raw_findings.extend(_validate_raw_producers(descriptors, record_entry, record, bases))
    observation_is_raw = bool(observation_entry and observation_entry["path"] in raw_paths)

    if not selected:
        historical, historical_source, historical_statuses = "NOT_REQUIRED", "plan.selection", ["NOT_REQUIRED"]
    else:
        judgment_raw = [item for item in raw if not observation_entry or item["path"] != str(observation_entry["path"])]
        historical, historical_source, historical_statuses = _historical(record, assessment, observation, judgment_raw)
        if not record:
            reasons.append("capture_missing")
            if requested_run and _has_target(records, feature, check_id):
                reasons.append("capture_run_mismatch")
        elif not record.get("run_id"):
            reasons.append("capture_run_missing")
        if not assessment and not observation:
            reasons.append("assessment_missing")

    if record:
        if record.get('execution') != 'exited' or type(record.get('exit_code')) is not int:
            reasons.append('capture_execution_incomplete')
        elif record['exit_code'] != 0:
            reasons.append('capture_native_failure')
        if record.get('cleanup_incomplete') or record.get('behavior_verdict') is not None:
            reasons.append('capture_invalid_completion')
        if not record.get('before') or record.get('before') != record.get('after'):
            reasons.append('capture_source_changed_during_run')
        if record.get("feature") != feature:
            reasons.append("capture_feature_mismatch")
        if record.get("check") != check_id:
            reasons.append("capture_check_mismatch")
        if run_id and record.get("run_id") != run_id:
            reasons.append("capture_run_mismatch")
        if record.get("execution") != "exited":
            reasons.append("capture_not_exited")
        if record.get("exit_code") != 0:
            reasons.append("capture_exit_nonzero")
        if record.get("cleanup_incomplete"):
            reasons.append("capture_cleanup_incomplete")

    assessment_binds = _assessment_binds_capture(assessment_entry, record_entry, plan_path)
    reasons.extend(_validate_assessment_evidence(assessment_entry, record_entry, plan_path))
    for label, data, is_raw_observation in (
        ("assessment", assessment, False),
        ("observation", observation, observation_is_raw),
    ):
        if not data:
            continue
        if not data.get("feature"):
            if not is_raw_observation:
                reasons.append(f"{label}_feature_missing")
        elif data.get("feature") != feature:
            reasons.append(f"{label}_feature_mismatch")
        if not data.get("check"):
            if not (label == "assessment" and assessment_binds) and not is_raw_observation:
                reasons.append(f"{label}_check_missing")
        elif data.get("check") != check_id:
            reasons.append(f"{label}_check_mismatch")
        if not data.get("run_id"):
            if not is_raw_observation:
                reasons.append(f"{label}_run_missing")
        elif run_id and data.get("run_id") != run_id:
            reasons.append(f"{label}_run_mismatch")

    observed_sources = []
    if record:
        observed_sources.append(("capture", _capture_conditions(record)))
    if assessment:
        observed_sources.append(("assessment", _assessment_conditions(assessment)))
    if observation:
        observed_sources.append(("observation", _assessment_conditions(observation)))
    observed_conditions = _combine_conditions(actual for _, actual in observed_sources)
    if selected:
        reasons.extend(_compare_conditions(expected_conditions, observed_conditions, "observed"))
        for label, actual in observed_sources:
            reasons.extend(_compare_present(expected_conditions, actual, f"observed.{label}"))
        reasons.extend(raw_findings)
        if not current:
            reasons.append("current_context_missing")

    if current and isinstance(current.get('checks'), dict):
        current = current['checks'].get(f'{feature}/{check_id}')
    current_conditions = _current_conditions(current)
    current_findings: list[str] = []
    if selected and required:
        # Read Git through a fixed argv, never through a submitted command.
        # A copied historical context file cannot override the current checkout.
        if record and isinstance(record.get('cwd'), str):
            try:
                def git(*tokens: str) -> bytes:
                    return subprocess.check_output(['git', '-C', record['cwd'], *tokens], stderr=subprocess.DEVNULL)
                live_source = {'revision': git('rev-parse', 'HEAD').decode().strip(),
                               'diff': _sha256(git('diff', 'HEAD', '--binary'))}
                for key in ('revision', 'diff'):
                    if expected_conditions['source'].get(key) != live_source[key]:
                        current_findings.append(f'condition_mismatch:current.source.{key}')
                if 'status' in record.get('after', {}) and git('status', '--porcelain').decode('utf-8', errors='replace') != record['after']['status']:
                    current_findings.append('condition_mismatch:current.source.status')
            except (OSError, subprocess.CalledProcessError):
                current_findings.append('condition_missing:current.source.git')
        else:
            current_findings.append('condition_missing:current.source.cwd')
        reasons.extend(current_findings)
        if not current:
            current_findings.append("current_context_missing")
        else:
            current_findings.extend(_compare_conditions(expected_conditions, current_conditions, "current"))
            reasons.extend(_compare_conditions(expected_conditions, current_conditions, "current"))
    if selected and required:
        stale = raw_outcome == "STALE" or any("condition_mismatch:current" in reason for reason in current_findings)
        unknown = raw_outcome == "UNKNOWN" or any(
            reason.startswith((
                "condition_missing:current",
                "condition_missing:observed",
                "condition_mismatch:observed",
                "current_context_missing",
                "raw_",
                "capture_",
                "assessment_",
                "observation_",
            ))
            for reason in reasons + current_findings
        )
        if stale:
            current_reuse = "STALE"
        elif unknown:
            current_reuse = "UNKNOWN"
        else:
            current_reuse = "REUSABLE"
        if historical == "PASS":
            current_status = "PASS" if current_reuse == "REUSABLE" else "UNKNOWN"
        elif historical in {"UNKNOWN", "NOT_RUN"} and current_reuse != "REUSABLE":
            current_status = "UNKNOWN"
        else:
            current_status = historical
    else:
        current_reuse = "NOT_APPLICABLE"
        current_status = "NOT_REQUIRED"

    raw_output = [
        {
            "path": item["path"],
            "sha256": item["sha256"],
            "pointer": item["pointer"],
            "producer": item["producer"],
            "origin": item["origin"],
            "observations": item["observations"],
            "original_status": item["original_status"],
        }
        for item in raw
    ]
    assessment_status, assessment_original = _status_pair(assessment.get("status")) if assessment else (None, None)
    observation_status, observation_original = _status_pair(observation.get("status")) if observation else (None, None)
    return {
        "id": check_id,
        "feature": feature,
        "expected": check["expected"],
        "criteria_revision": check["criteria_revision"],
        "required": required,
        "selected": selected,
        "selection": {"status": check["selection"]["status"], "reason": selection_reason},
        "historical_status": historical,
        "historical_source": historical_source,
        "historical_statuses": historical_statuses,
        "current_reuse": current_reuse,
        "current_status": current_status,
        "run_id": run_id,
        "capture": {
            "path": str(record_entry["path"]) if record_entry else None,
            "sha256": record_entry["sha256"] if record_entry else None,
            "argv": record.get("argv") if record else None,
            "cwd": record.get("cwd") if record else None,
            "execution": record.get("execution") if record else None,
            "exit_code": record.get("exit_code") if record else None,
        },
        "assessment": {
            "path": str(assessment_entry["path"]) if assessment_entry else None,
            "sha256": assessment_entry["sha256"] if assessment_entry else None,
            "status": assessment_status,
            "original_status": assessment_original,
        },
        "observation": {
            "path": str(observation_entry["path"]) if observation_entry else None,
            "sha256": observation_entry["sha256"] if observation_entry else None,
            "status": observation_status,
            "original_status": observation_original,
        },
        "raw": raw_output,
        "conditions": {"expected": expected_conditions, "observed": observed_conditions, "current": current_conditions},
        "reasons": sorted({reason for reason in reasons if reason}),
    }


def _counts(items: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for item in items:
        value = item.get(field, "UNKNOWN")
        counts[value if value in counts else "UNKNOWN"] += 1
    return {key: value for key, value in counts.items() if value}


def _summary(items: list[dict[str, Any]], field: str, *, required_only: bool = False) -> dict[str, Any]:
    included = [item for item in items if item["required"]] if required_only else [item for item in items if item["selected"]]
    statuses = sorted(
        {item.get(field, "UNKNOWN") for item in included}
        | {value for item in included for value in item["historical_statuses"] if value in {"ISSUES", "BLOCKED"}}
    )
    if not included:
        status = "BLOCKED"
    elif statuses == ["PASS"]:
        status = "PASS"
    elif any(value in statuses for value in ("BLOCKED", "UNKNOWN", "SKIP", "NOT_RUN", "NOT_REQUIRED")):
        status = "BLOCKED"
    elif "ISSUES" in statuses:
        status = "ISSUES"
    else:
        status = "BLOCKED"
    return {"status": status, "statuses": statuses, "counts": _counts(included, field)}


def _git_snapshot(cwd: Path) -> dict[str, str]:
    """Read the fixed source identity used by execution and current reuse."""
    def git(*tokens: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(cwd), *tokens], stderr=subprocess.DEVNULL)

    root = Path(git('rev-parse', '--show-toplevel').decode().strip())
    names = git('ls-files', '--others', '--exclude-standard', '--full-name', '-z').decode('utf-8').split('\0')
    untracked = {name: _path_hash(_safe_path(name, root=root, label='untracked source'), 'untracked source')
                 for name in sorted(names) if name}
    return {
        "revision": git("rev-parse", "HEAD").decode().strip(),
        "diff": _sha256(git("diff", "HEAD", "--binary")),
        "status": git("status", "--porcelain").decode("utf-8", errors="replace"),
        "untracked": _sha256(json.dumps(untracked, sort_keys=True).encode('utf-8')),
    }


_PRIVATE_PATH_PARTS = {".env", ".dev.vars", "auth", "auth.json", "credentials", "secrets"}


def _is_alias(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction and is_junction())
    except OSError as error:
        raise ViewerInputError(f"path_unreadable:{path}:{error}") from error


def _private_path(path: Path) -> bool:
    return any(
        part.lower() in _PRIVATE_PATH_PARTS or part.lower().startswith(".env.")
        for part in path.parts
    )


def _reject_alias_components(path: Path, label: str) -> None:
    """Reject symlink/junction components before resolving or reading a path."""
    if not path.is_absolute():
        raise ViewerInputError(f"{label} must be absolute before alias checks")
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        if part in ("", "."):
            continue
        if part == "..":
            cursor = cursor.parent
            continue
        cursor = cursor / part
        if _is_alias(cursor):
            raise ViewerInputError(f"{label} uses an aliased path")


def _safe_cwd(value: Path, label: str) -> Path:
    if not value.is_absolute() or _private_path(value):
        raise ViewerInputError(f"{label}.cwd must be an existing non-aliased absolute directory")
    _reject_alias_components(value, label)
    if not value.is_dir():
        raise ViewerInputError(f"{label}.cwd must be an existing non-aliased absolute directory")
    resolved = value.resolve()
    _reject_alias_components(resolved, label)
    return resolved


def _safe_path(
    value: str,
    *,
    root: Path,
    label: str,
    allow_absolute: bool = False,
    extra_root: Path | None = None,
) -> Path:
    raw = Path(value)
    if not value.strip() or (raw.is_absolute() and not allow_absolute):
        raise ViewerInputError(f"{label} must be a relative path")
    if _private_path(raw):
        raise ViewerInputError(f"{label} points to a private path")
    roots = [root]
    if extra_root is not None:
        roots.append(extra_root)
    checked_roots: list[Path] = []
    for candidate in roots:
        if not candidate.is_absolute():
            raise ViewerInputError(f"{label}.root must be absolute")
        if _private_path(candidate):
            raise ViewerInputError(f"{label}.root points to a private path")
        _reject_alias_components(candidate, f"{label}.root")
        if candidate.exists() and candidate.is_dir():
            checked_roots.append(_safe_cwd(candidate, f"{label}.root"))
        elif candidate.exists():
            raise ViewerInputError(f"{label}.root must be a directory")
        else:
            checked_roots.append(candidate.resolve())
    roots = checked_roots
    candidate = raw if raw.is_absolute() else root / raw
    _reject_alias_components(candidate, label)
    resolved = candidate.resolve()
    if _private_path(resolved):
        raise ViewerInputError(f"{label} points to a private path")
    matching = [candidate_root for candidate_root in roots if resolved == candidate_root or candidate_root in resolved.parents]
    if not matching:
        raise ViewerInputError(f"{label} escapes its allowed root")
    anchor = max(matching, key=lambda item: len(item.parts))
    relative = candidate.relative_to(anchor) if candidate.is_relative_to(anchor) else raw
    cursor = anchor
    for part in relative.parts:
        if part in ("", "."):
            continue
        cursor = cursor / part
        if _is_alias(cursor):
            raise ViewerInputError(f"{label} uses an aliased path")
    return resolved


def _file_refs(group: dict[str, Any], label: str) -> list[str]:
    refs = group.get("file_refs", group.get("files"))
    if refs is None:
        return []
    if not isinstance(refs, list) or not refs:
        raise ViewerInputError(f"{label}.file_refs must be a nonempty list")
    result: list[str] = []
    for index, ref in enumerate(refs):
        if isinstance(ref, str) and ref.strip():
            result.append(ref)
        elif isinstance(ref, dict) and _text(ref.get("path")):
            result.append(str(ref["path"]))
        else:
            raise ViewerInputError(f"{label}.file_refs[{index}] must name a file")
    return result


def _file_hashes(group: dict[str, Any], cwd: Path, label: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for ref in _file_refs(group, label):
        if Path(ref).is_absolute():
            raise ViewerInputError(f"{label}.file_ref_absolute:{ref}")
        path = _safe_path(ref, root=cwd, label=f"{label}.file_ref")
        if not path.is_file():
            raise ViewerInputError(f"{label}.file_ref_missing:{ref}")
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise ViewerInputError(f"{label}.file_ref_unreadable:{ref}:{error}") from error
        hashes[str(path)] = _sha256(raw)
    return hashes


def _runtime_identity(check: dict[str, Any]) -> dict[str, str]:
    argv = check["conditions"]["command"].get("argv")
    if not isinstance(argv, list) or not argv or not isinstance(argv[0], str) or not argv[0].strip():
        raise ViewerInputError("runtime executable is missing from command argv")
    executable = Path(argv[0])
    located = executable if executable.is_absolute() else Path(shutil.which(argv[0]) or "")
    if not located or not located.is_file():
        raise ViewerInputError(f"runtime executable is unavailable: {argv[0]}")
    try:
        resolved = located.resolve()
        raw = resolved.read_bytes()
    except OSError as error:
        raise ViewerInputError(f"runtime executable is unreadable: {argv[0]}: {error}") from error
    identity = {
        "executable": str(resolved),
        "executable_sha256": _sha256(raw),
    }
    try:
        current_executable = Path(sys.executable).resolve()
    except OSError:
        current_executable = Path(sys.executable)
    if resolved == current_executable:
        identity["python_version"] = sys.version
    return identity


def _execution_conditions(check: dict[str, Any], cwd: Path) -> dict[str, Any]:
    conditions = copy.deepcopy(check["conditions"])
    snapshot = _git_snapshot(cwd)
    source = conditions["source"]
    source["revision"] = snapshot["revision"]
    source["diff"] = snapshot["diff"]
    source['untracked'] = snapshot['untracked']
    if "status" in source:
        source["status"] = snapshot["status"]
    conditions["runtime"].update(_runtime_identity(check))
    for name in ("dependency", "fixture"):
        group = conditions[name]
        hashes = _file_hashes(group, cwd, name)
        if hashes:
            group["file_hashes"] = hashes
    return conditions


def _validate_execution_check(
    check: dict[str, Any], index: int, evidence_dir: Path
) -> tuple[Path, dict[str, Any], Path]:
    if _text(check.get("run_id")):
        raise ViewerInputError(f"checks[{index}] execution plan already has a run binding")
    conditions = check["conditions"]
    command = conditions["command"]
    argv = command.get("argv")
    cwd_value = command.get("cwd")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        raise ViewerInputError(f"checks[{index}].conditions.command.argv must be a nonempty string list")
    if not isinstance(cwd_value, str):
        raise ViewerInputError(f"checks[{index}].conditions.command.cwd must be an existing absolute directory")
    cwd = _safe_cwd(Path(cwd_value), f"checks[{index}].conditions.command")
    descriptors = check.get("raw_observations", [])
    if not isinstance(descriptors, list) or len(descriptors) != 1:
        raise ViewerInputError(f"checks[{index}] execution needs exactly one native raw_observation")
    descriptor = descriptors[0]
    if _text(descriptor.get("sha256")) or isinstance(descriptor.get("producer"), dict):
        raise ViewerInputError(f"checks[{index}] execution plan already has a raw binding")
    assertions = descriptor.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        raise ViewerInputError(f"checks[{index}] execution needs explicit native assertions")
    for assertion_index, assertion in enumerate(assertions):
        if not isinstance(assertion, dict) or not isinstance(assertion.get("pointer"), str):
            raise ViewerInputError(f"checks[{index}] assertion {assertion_index} needs a JSON pointer")
        operators = [key for key in ("equals", "min_count", "min") if key in assertion]
        if len(operators) != 1:
            raise ViewerInputError(f"checks[{index}] assertion {assertion_index} needs one explicit comparator")
    report_value = descriptor.get("path")
    if not isinstance(report_value, str) or not report_value.strip():
        raise ViewerInputError(f"checks[{index}] native report path is required")
    report_path = _safe_path(
        report_value,
        root=cwd,
        label=f"checks[{index}].native_report",
        allow_absolute=True,
        extra_root=evidence_dir,
    )
    if _is_alias(report_path) or report_path.exists():
        raise ViewerInputError(f"checks[{index}] native report path already exists: {report_path}")
    return cwd, descriptor, report_path


def _preflight_execution(
    plan: dict[str, Any], checks: list[dict[str, Any]], evidence_dir: Path,
    completed: set[int] | None = None,
) -> dict[int, dict[str, Any]]:
    preconditions: dict[int, dict[str, Any]] = {}
    report_paths: set[Path] = set()
    for index, check in enumerate(checks):
        selected, _ = _selection(check)
        if not selected or index in (completed or set()):
            continue
        cwd, descriptor, report_path = _validate_execution_check(check, index, evidence_dir)
        measured = _execution_conditions(check, cwd)
        expected = check["conditions"]
        for key in ("revision", "diff"):
            if expected["source"].get(key) != measured["source"][key]:
                raise ViewerInputError(f"checks[{index}] pre-run source.{key} does not match current checkout")
        if "status" in expected["source"] and expected["source"]["status"] != measured["source"]["status"]:
            raise ViewerInputError(f"checks[{index}] pre-run source.status does not match current checkout")
        if 'untracked' in expected['source'] and expected['source']['untracked'] != measured['source']['untracked']:
            raise ViewerInputError(f'checks[{index}] pre-run untracked source bytes changed')
        for name in ("dependency", "fixture"):
            expected_hashes = expected[name].get("file_hashes")
            if expected_hashes is not None and expected_hashes != measured[name].get("file_hashes"):
                raise ViewerInputError(f"checks[{index}] pre-run {name}.file_hashes are stale")
        if report_path in report_paths:
            raise ViewerInputError(f"checks[{index}] native report path is reused: {report_path}")
        report_paths.add(report_path)
        preconditions[index] = {"cwd": cwd, "conditions": measured, "report_path": report_path}
    if not preconditions and not completed:
        raise ViewerInputError("execution requires at least one selected check")
    return preconditions


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ViewerInputError(f"execution output already exists: {path}")
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _blocked_execution(message: str, *, plan_path: Path, run_check_path: Path | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "read_only": False,
        "test_commands_executed": 0,
        "status": "BLOCKED",
        "statuses": ["BLOCKED"],
        "historical": {"status": "BLOCKED", "statuses": ["BLOCKED"], "counts": {"BLOCKED": 1}},
        "current": {"status": "BLOCKED", "statuses": ["BLOCKED"], "counts": {"BLOCKED": 1}},
        "items": [],
        "remaining": [message],
        "execution": {"mode": "execute", "plan": str(plan_path), "run_check": str(run_check_path) if run_check_path else None},
    }


def _blocked_bundle(message: str, *, bundle: Any = None) -> dict[str, Any]:
    retained_bundle = str(bundle) if isinstance(bundle, Path) else bundle
    return {
        "schema_version": 1,
        "read_only": True,
        "test_commands_executed": 0,
        "current_source_check": "fixed read-only Git commands; no submitted argv executed",
        "status": "BLOCKED",
        "statuses": ["BLOCKED"],
        "historical": {"status": "BLOCKED", "statuses": ["BLOCKED"], "counts": {"BLOCKED": 1}},
        "current": {"status": "BLOCKED", "statuses": ["BLOCKED"], "counts": {"BLOCKED": 1}},
        "items": [],
        "remaining": [message],
        "bundle": retained_bundle,
    }


def _invalidate_current_result(result: dict[str, Any], reason: str) -> dict[str, Any]:
    """Make a previously joined result fail closed after an identity change."""
    for item in result.get("items", []):
        if item.get("selected"):
            item["current_reuse"] = "STALE"
            item["current_status"] = "UNKNOWN"
            item["reasons"] = sorted(set(item.get("reasons", [])) | {reason})
    items = result.get("items", [])
    current = _summary(items, "current_status", required_only=True)
    result["current"] = current
    result["status"] = current["status"]
    result["statuses"] = current["statuses"]
    result["remaining"] = sorted(
        {reason for item in items for reason in item.get("reasons", []) if reason} | {reason}
    )
    return result


def _path_hash(path: Path, label: str) -> str:
    if _private_path(path):
        raise ViewerInputError(f"{label} points to a private path")
    _reject_alias_components(path, label)
    if not path.is_file():
        raise ViewerInputError(f"{label} is missing: {path}")
    try:
        return _sha256(path.read_bytes())
    except OSError as error:
        raise ViewerInputError(f"{label} is unreadable: {path}: {error}") from error


def _bundle_file(value: Any, *, base: Path, label: str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise ViewerInputError(f"{label} must name a file")
    value_path = Path(value)
    candidate = value_path if value_path.is_absolute() else base / value_path
    if not candidate.is_absolute():
        candidate = candidate.absolute()
    return candidate if _path_hash(candidate, label) else candidate


def _bundle_current_context(plan: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    current: dict[str, Any] = {"checks": {}}
    findings: list[str] = []
    for index, check in enumerate(_plan_checks(plan)):
        selected, _ = _selection(check)
        if not selected:
            continue
        key = f"{check['feature_id']}/{check['id']}"
        command = check["conditions"]["command"]
        cwd_value = command.get("cwd")
        try:
            if not isinstance(cwd_value, str):
                raise ViewerInputError(f"checks[{index}].conditions.command.cwd is missing")
            cwd = _safe_cwd(Path(cwd_value), f"checks[{index}].conditions.command")
            current["checks"][key] = {"conditions": _execution_conditions(check, cwd)}
            runtime = check["conditions"]["runtime"]
            if not isinstance(runtime.get("executable"), str) or not runtime.get("executable_sha256"):
                findings.append(f"runtime_identity_missing:{key}")
        except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
            findings.append(f"current_conditions_unavailable:{key}:{error}")
    return current, findings


def _validate_bundle_report_paths(plan: dict[str, Any], evidence_dir: Path | None) -> None:
    for index, check in enumerate(_plan_checks(plan)):
        selected, _ = _selection(check)
        if not selected:
            continue
        command = check["conditions"]["command"]
        cwd_value = command.get("cwd")
        if not isinstance(cwd_value, str):
            raise ViewerInputError(f"checks[{index}].conditions.command.cwd is missing")
        cwd = _safe_cwd(Path(cwd_value), f"checks[{index}].conditions.command")
        for descriptor_index, descriptor in enumerate(check.get("raw_observations", [])):
            report_value = descriptor.get("path") if isinstance(descriptor, dict) else None
            if not isinstance(report_value, str) or not report_value.strip():
                continue
            _safe_path(
                report_value,
                root=cwd,
                label=f"checks[{index}].raw_observations[{descriptor_index}].path",
                allow_absolute=True,
                extra_root=evidence_dir,
            )
            producer = descriptor.get("producer") if isinstance(descriptor, dict) else None
            if isinstance(producer, dict) and isinstance(producer.get("json_report_path"), str):
                _safe_path(
                    producer["json_report_path"],
                    root=cwd,
                    label=f"checks[{index}].raw_observations[{descriptor_index}].producer.json_report_path",
                    allow_absolute=True,
                    extra_root=evidence_dir,
                )


def view_bundle(bundle: dict[str, Any] | str | Path) -> dict[str, Any]:
    """Revalidate an execution bundle read-only against the current project state."""
    bundle_value: Any = bundle
    bundle_file: Path | None = None
    base = Path.cwd().resolve()
    try:
        if isinstance(bundle, (str, Path)):
            bundle_file = _bundle_file(bundle, base=base, label="bundle")
            bundle_value, _ = _read_json(bundle_file)
            base = bundle_file.parent
        if not isinstance(bundle_value, dict):
            raise ViewerInputError("bundle must be an object or JSON path")
        if isinstance(bundle_value.get("execution"), dict) and isinstance(bundle_value["execution"].get("bundle"), dict):
            bundle_value = bundle_value["execution"]["bundle"]
        source_plan = _bundle_file(bundle_value.get("source_plan"), base=base, label="bundle.source_plan")
        recorded_hash = bundle_value.get("source_plan_sha256")
        if not isinstance(recorded_hash, str) or not recorded_hash:
            raise ViewerInputError("bundle.source_plan_sha256 is required")
        source_hash = _path_hash(source_plan, "bundle.source_plan")
        bound_plan = _bundle_file(bundle_value.get("plan"), base=base, label="bundle.plan")
        evidence_value = bundle_value.get("evidence_dir")
        evidence_dir = None
        if isinstance(evidence_value, str) and evidence_value.strip():
            evidence_candidate = Path(evidence_value) if Path(evidence_value).is_absolute() else base / evidence_value
            if not evidence_candidate.is_absolute():
                evidence_candidate = evidence_candidate.absolute()
            _reject_alias_components(evidence_candidate, "bundle.evidence_dir")
            evidence_dir = evidence_candidate.resolve()
        records = [_bundle_file(value, base=base, label="bundle.record") for value in bundle_value.get("records", [])]
        assessments = [_bundle_file(value, base=base, label="bundle.assessment") for value in bundle_value.get("assessments", [])]
        observations = [_bundle_file(value, base=base, label="bundle.observation") for value in bundle_value.get("observations", [])]
        plan, _ = _read_json(bound_plan)
        if not isinstance(plan, dict):
            raise ViewerInputError("bundle.plan must contain a JSON object")
        original, _ = _read_json(source_plan)
        original_checks = _plan_checks(original, allow_unbound=True)
        bound_checks = _plan_checks(plan)
        if len(original_checks) != len(bound_checks):
            raise ViewerInputError("bound plan changed selected checks")
        for selected, bound in zip(original_checks, bound_checks):
            for field in ("id", "feature_id", "expected", "criteria_revision", "required", "selection"):
                if selected[field] != bound[field]:
                    raise ViewerInputError(f"bound plan changed {field}")
            if _missing_or_mismatched(selected["conditions"], bound["conditions"], "conditions"):
                raise ViewerInputError("bound plan changed selected conditions")
            # Missing raw evidence remains a failed check; present evidence cannot weaken its oracle.
            if bound.get("raw_observations"):
                selected_raw = selected.get("raw_observations", [])
                if len(selected_raw) != len(bound["raw_observations"]):
                    raise ViewerInputError("bound plan changed raw checks")
                for before, after in zip(selected_raw, bound["raw_observations"]):
                    if any(before.get(key) != after.get(key) for key in ("pointer", "assertions")):
                        raise ViewerInputError("bound plan changed raw assertions")
                    cwd = Path(selected["conditions"]["command"]["cwd"])
                    if (cwd / before["path"]).resolve() != Path(after["path"]).resolve():
                        raise ViewerInputError("bound plan changed raw path")
        _validate_bundle_report_paths(plan, evidence_dir)
        current, condition_findings = _bundle_current_context(plan)
        result = view_results(
            bound_plan,
            record_paths=records,
            assessment_paths=assessments,
            observation_paths=observations,
            current_context=current,
        )
        result["bundle"] = copy.deepcopy(bundle_value)
        result["bundle_view"] = {"read_only": True, "source_plan": str(source_plan), "source_plan_sha256": source_hash}
        result["test_commands_executed"] = 0
        for finding in condition_findings:
            result["remaining"] = sorted(set(result.get("remaining", [])) | {finding})
            _invalidate_current_result(result, finding)
        if source_hash.lower() != recorded_hash.lower():
            _invalidate_current_result(result, "source_plan_hash_mismatch")
        return result
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
        return _blocked_bundle(str(error), bundle=bundle_value if isinstance(bundle_value, dict) else bundle)


def _save_execution_bundle(output_dir, prefix, bound_plan, current_checks, records,
                           assessments, plan_file, plan_sha256, completed):
    # ponytail: full snapshots reuse the viewer; partition very large plans before
    # cumulative O(n^2) checkpoint storage warrants a separate journal format.
    plan_path = output_dir / (prefix + 'bound-plan.json')
    context_path = output_dir / (prefix + 'current-context.json')
    bundle_path = output_dir / (prefix + 'bundle.json')
    _write_json(plan_path, bound_plan)
    _write_json(context_path, {'checks': current_checks})
    descriptor = {
        'schema_version': 1, 'plan': str(plan_path), 'current_context': str(context_path),
        'records': [str(path) for path in records],
        'assessments': [str(path) for path in assessments], 'observations': [],
        'source_plan': str(plan_file), 'source_plan_sha256': plan_sha256,
        'evidence_dir': str(output_dir), 'completed_indices': sorted(completed),
    }
    # Publish complete bytes atomically without overwriting another writer.
    pending = bundle_path.with_suffix('.pending.json')
    _write_json(pending, descriptor)
    os.link(pending, bundle_path)
    pending.unlink()
    return descriptor


def execute_plan(
    plan_path: str | Path,
    *,
    run_check_path: str | Path,
    evidence_dir: str | Path,
    timeout: float = 300,
    resume: bool = False,
) -> dict[str, Any]:
    """Execute selected plan commands once, bind their native facts, then use the viewer."""
    plan_file = Path(plan_path).resolve()
    run_check = Path(run_check_path).resolve()
    if not run_check.is_file() or run_check.is_symlink():
        return _blocked_execution("run_check path is missing or unsafe", plan_path=plan_file, run_check_path=run_check)
    plan, plan_raw = _read_json(plan_file)
    if not isinstance(plan, dict):
        return _blocked_execution("Plan must be a JSON object", plan_path=plan_file, run_check_path=run_check)
    output_dir = Path(evidence_dir).resolve()
    try:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(float(timeout)) or timeout <= 0:
            raise ViewerInputError("execution timeout must be finite and positive")
        _reject_alias_components(Path(evidence_dir).absolute(), "evidence_dir")
        output_dir.mkdir(parents=True, exist_ok=True)
        _reject_alias_components(output_dir, "evidence_dir")
    except (OSError, ValueError, TypeError) as error:
        return _blocked_execution(str(error), plan_path=plan_file, run_check_path=run_check)
    completed: set[int] = set()
    prior = None
    try:
        checks = _plan_checks(plan, allow_unbound=True)
        if resume:
            final = output_dir / 'bundle.json'
            checkpoints = sorted(output_dir.glob('checkpoint-*-bundle.json'),
                                 key=lambda path: int(path.name.split('-')[1]))
            saved = final if final.exists() else checkpoints[-1] if checkpoints else None
            interrupted_final = False
            if saved is not None:
                _reject_alias_components(saved, 'resume bundle')
                try:
                    prior, _ = _read_json(saved)
                except ViewerInputError:
                    if saved != final or not checkpoints:
                        raise
                    saved = checkpoints[-1]
                    _reject_alias_components(saved, 'resume checkpoint')
                    prior, _ = _read_json(saved)
                    interrupted_final = True
                if not isinstance(prior, dict):
                    raise ViewerInputError('resume bundle must be an object')
                if (prior.get('source_plan') != str(plan_file)
                        or prior.get('source_plan_sha256') != _sha256(plan_raw)
                        or prior.get('evidence_dir') != str(output_dir)):
                    raise ViewerInputError('resume plan or evidence directory changed')
                observed = view_bundle(saved)
                if saved == final:
                    return observed  # Completed runs are read-only, even when stale or failed.
                indices = prior.get('completed_indices')
                if (not isinstance(indices, list) or not indices
                        or any(type(i) is not int or i < 0 or i >= len(checks) for i in indices)
                        or len(indices) != len(set(indices))):
                    raise ViewerInputError('invalid resume checkpoint indices')
                completed = set(indices)
                items = list(observed.get('items', []))
                optional = [i for i in completed if not checks[i]['required']]
                if optional:
                    # Check execution identity without changing optional acceptance policy.
                    bound, _ = _read_json(Path(prior['plan']))
                    current, findings = _bundle_current_context(bound)
                    if findings:
                        raise ViewerInputError('checkpoint conditions unavailable')
                    entries = [_load_many(prior[name], name)
                               for name in ('records', 'assessments', 'observations')]
                    items.extend(_item_result({**bound['checks'][i], 'required': True},
                        Path(prior['plan']), *entries, current) for i in optional)
                reusable = {(item['feature'], item['id']) for item in items
                            if item['current_status'] == 'PASS' or (
                                item['current_status'] == 'ISSUES'
                                and item['historical_status'] == 'ISSUES' and item['selected']
                                and item['capture']['execution'] == 'exited'
                                and type(item['capture']['exit_code']) is int
                                and all(reason in {'capture_native_failure', 'capture_exit_nonzero'}
                                    or reason.startswith('raw_assertion_mismatch:')
                                    for reason in item['reasons']))}
                if any((checks[i]['feature_id'], checks[i]['id']) not in reusable for i in completed):
                    raise ViewerInputError('completed checkpoint evidence is not currently reusable')
                if completed == {i for i, check in enumerate(checks) if _selection(check)[0]}:
                    # Repair the configured consumer path, preserving a torn descriptor.
                    recovery = output_dir / f'resume-{uuid.uuid4()}.json'
                    _write_json(recovery, prior)
                    if interrupted_final:
                        original = final.read_bytes()
                        backup = output_dir / f'bundle.interrupted-{_sha256(original)}.json'
                        if backup.exists():
                            _reject_alias_components(backup, 'interrupted bundle backup')
                            if backup.read_bytes() != original:
                                raise ViewerInputError('interrupted bundle backup changed')
                        else:
                            os.link(final, backup)
                        if final.read_bytes() != original:
                            raise ViewerInputError('final bundle changed during recovery')
                        os.replace(recovery, final)
                    else:
                        os.link(recovery, final)
                        recovery.unlink()
                    return view_bundle(final)
                if interrupted_final:
                    raise ViewerInputError('damaged final bundle has no complete checkpoint; replay refused')
        for index, check in enumerate(checks):
            if _selection(check)[0] and index not in completed:
                if (output_dir / f'command-{index}-started.json').exists():
                    raise ViewerInputError(f'command outcome unknown:{index}; automatic replay refused')
        preconditions = _preflight_execution(plan, checks, output_dir, completed)
    except (OSError, ValueError, TypeError, KeyError) as error:
        return _blocked_execution(str(error), plan_path=plan_file, run_check_path=run_check)

    bound_plan_path = output_dir / "bound-plan.json"
    current_path = output_dir / "current-context.json"
    bundle_path = output_dir / "bundle.json"
    if (
        bound_plan_path.exists() or bound_plan_path.is_symlink()
        or current_path.exists() or current_path.is_symlink()
        or bundle_path.exists() or bundle_path.is_symlink()
    ):
        return _blocked_execution("execution evidence directory already contains a bound result", plan_path=plan_file, run_check_path=run_check)
    for index, check in enumerate(checks):
        selected, _ = _selection(check)
        if selected and index not in completed:
            slug = f"{index}-{check['feature_id']}-{check['id']}".replace("/", "_").replace("\\", "_")
            capture_path = output_dir / f"{slug}-capture.json"
            if capture_path.exists() or capture_path.is_symlink():
                return _blocked_execution("execution capture path already exists", plan_path=plan_file, run_check_path=run_check)
    bound_plan = copy.deepcopy(plan)
    records: list[Path] = []
    assessments: list[Path] = []
    current_checks: dict[str, dict[str, Any]] = {}
    artifacts: list[dict[str, Any]] = []
    if prior:
        bound_plan, _ = _read_json(Path(prior['plan']))
        records = [Path(path) for path in prior['records']]
        assessments = [Path(path) for path in prior['assessments']]
    for index, check in enumerate(checks):
        if index not in completed:
            bound_plan['checks'][index].pop('raw_observations', None)
        if index in preconditions:
            bound_plan['checks'][index]['conditions'] = preconditions[index]['conditions']
    attempted = 0
    plan_sha256 = _sha256(plan_raw)
    plan_mutated = False
    for index, check in enumerate(checks):
        selected, _ = _selection(check)
        if not selected:
            bound_plan["checks"][index].pop("raw_observations", None)
            continue
        if index in completed:
            continue
        info = preconditions[index]
        try:
            if _path_hash(plan_file, "source plan") != plan_sha256:
                plan_mutated = True
        except ViewerInputError:
            plan_mutated = True
        if plan_mutated:
            bound_plan["checks"][index].pop("raw_observations", None)
            bound_plan["checks"][index].pop("run_id", None)
            current_checks[f"{check['feature_id']}/{check['id']}"] = {
                "conditions": {name: {"status": "unavailable", "reason": "source_plan_changed_during_execution"} for name in CONDITION_GROUPS}
            }
            artifacts.append({
                "check": f"{check['feature_id']}/{check['id']}",
                "status": "BLOCKED",
                "reason": "source_plan_changed_during_execution",
            })
            continue
        try:
            current_before = _execution_conditions(check, info["cwd"])
        except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
            current_before = None
            precondition_reason = f"precondition_unavailable_before_execution:{error}"
        else:
            precondition_reason = None if current_before == info["conditions"] else "precondition_changed_before_execution"
        if precondition_reason:
            bound_plan["checks"][index].pop("raw_observations", None)
            bound_plan["checks"][index].pop("run_id", None)
            current_checks[f"{check['feature_id']}/{check['id']}"] = {
                "conditions": current_before or {}
            }
            artifacts.append({
                "check": f"{check['feature_id']}/{check['id']}",
                "status": "BLOCKED",
                "reason": precondition_reason,
            })
            continue
        slug = f"{index}-{check['feature_id']}-{check['id']}".replace("/", "_").replace("\\", "_")
        capture_path = output_dir / f"{slug}-capture.json"
        report_path = info["report_path"]
        bound_plan["checks"][index]['raw_observations'] = copy.deepcopy(check['raw_observations'])
        bound_plan["checks"][index]["run_id"] = None
        command = [
            sys.executable,
            str(run_check),
            "--cwd",
            str(info["cwd"]),
            "--output",
            str(capture_path),
            "--feature",
            str(check["feature_id"]),
            "--check",
            str(check["id"]),
            "--json-report",
            str(report_path),
            "--timeout",
            str(timeout),
            "--",
            *check["conditions"]["command"]["argv"],
        ]
        _write_json(output_dir / f'command-{index}-started.json', {
            'source_plan_sha256': plan_sha256, 'check_index': index, 'argv': command})
        attempted += 1
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        try:
            if _path_hash(plan_file, "source plan") != plan_sha256:
                plan_mutated = True
        except ViewerInputError:
            plan_mutated = True
        record: dict[str, Any] | None = None
        capture_safe = True
        try:
            _reject_alias_components(capture_path, "capture")
        except ViewerInputError:
            capture_safe = False
        if capture_safe and capture_path.is_file() and not capture_path.is_symlink():
            try:
                record, _ = _read_json(capture_path)
            except (OSError, ValueError):
                record = None
        if not isinstance(record, dict):
            bound_plan["checks"][index].pop("raw_observations", None)
            bound_plan["checks"][index].pop("run_id", None)
            artifacts.append({"check": f"{check['feature_id']}/{check['id']}", "capture": str(capture_path), "run_check_exit": process.returncode})
            continue
        record["conditions"] = info["conditions"]
        _write_capture = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        capture_path.write_text(_write_capture, encoding="utf-8")
        record_raw = capture_path.read_bytes()
        record_hash = _sha256(record_raw)
        records.append(capture_path)
        run_id = record.get("run_id")
        if isinstance(run_id, str) and run_id:
            bound_plan["checks"][index]["run_id"] = run_id
        else:
            bound_plan["checks"][index].pop("run_id", None)
        descriptor = bound_plan["checks"][index]["raw_observations"][0]
        descriptor["path"] = str(report_path)
        descriptor["producer"] = {
            "run_id": run_id,
            "capture_path": str(capture_path),
            "capture_sha256": record_hash,
            "argv": record.get("argv"),
            "json_report_path": str(report_path),
        }
        report_ok = False
        report_hash = None
        try:
            _reject_alias_components(report_path, "native report")
            report_ok = report_path.is_file() and not report_path.is_symlink()
        except ViewerInputError:
            report_ok = False
        if report_ok:
            try:
                report_raw = report_path.read_bytes()
                report_hash = _sha256(report_raw)
                json.loads(report_raw)
            except (OSError, ValueError, json.JSONDecodeError):
                report_ok = False
        if report_hash is not None:
            descriptor["sha256"] = report_hash
            descriptor["producer"]["json_report_sha256"] = report_hash
        if report_ok:
            assessment_path = output_dir / f"{slug}-assessment.json"
            check_descriptor = {
                **descriptor,
                "origin": str(plan_file),
            }
            raw, findings, _, _ = _validate_raw([check_descriptor], [report_path.parent, info["cwd"]])
            matched = bool(raw) and not findings and all(
                observation["matched"] for observation in raw[0]["observations"]
            )
            _write_json(
                assessment_path,
                {
                    "status": "PASS" if matched and record.get("execution") == "exited" and record.get("exit_code") == 0 else "ISSUES",
                    "feature": check["feature_id"],
                    "check": check["id"],
                    "run_id": run_id,
                    "conditions": info["conditions"],
                    "reason": "explicit native report assertions",
                    "evidence": str(capture_path),
                    "evidence_sha256": record_hash,
                },
            )
            assessments.append(assessment_path)
        else:
            bound_plan["checks"][index].pop("raw_observations", None)
        bound_plan["checks"][index]["conditions"] = info["conditions"]
        try:
            current_conditions = _execution_conditions(check, info["cwd"])
        except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
            current_conditions = {name: {"status": "unavailable", "reason": str(error)} for name in CONDITION_GROUPS}
        current_checks[f"{check['feature_id']}/{check['id']}"] = {"conditions": current_conditions}
        artifacts.append({
            "check": f"{check['feature_id']}/{check['id']}",
            "capture": str(capture_path),
            "report": str(report_path),
            "assessment": str(assessments[-1]) if report_ok else None,
            "run_check_exit": process.returncode,
        })
        completed.add(index)
        _save_execution_bundle(output_dir, f'checkpoint-{index}-', bound_plan,
            current_checks, records, assessments, plan_file, plan_sha256, completed)

    bundle_descriptor = _save_execution_bundle(output_dir, '', bound_plan,
        current_checks, records, assessments, plan_file, plan_sha256, completed)
    result = view_bundle(bundle_descriptor)
    result["execution"] = {
        "mode": "execute",
        "commands_attempted": attempted,
        "captures_bound": len(records),
        "plan": str(plan_file),
        "plan_sha256": plan_sha256,
        "source_plan_changed_during_execution": plan_mutated,
        "run_check": str(run_check),
        "bundle_path": str(bundle_path),
        "bundle": {**bundle_descriptor, "path": str(bundle_path)},
        "artifacts": artifacts,
    }
    result["test_commands_executed"] = attempted
    if plan_mutated:
        _invalidate_current_result(result, "source_plan_changed_during_execution")
    return result


def view_results(
    plan_path: str | Path,
    *,
    record_paths: Iterable[str | Path] = (),
    assessment_paths: Iterable[str | Path] = (),
    observation_paths: Iterable[str | Path] = (),
    current_context_path: str | Path | None = None,
    current_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read and join records without executing or modifying any input."""
    plan_file = Path(plan_path).resolve()
    plan, plan_raw = _read_json(plan_file)
    if not isinstance(plan, dict):
        raise ViewerInputError("Plan must be a JSON object")
    records = _load_many(record_paths, "Capture")
    assessments = _load_many(assessment_paths, "Assessment")
    observations = _load_many(observation_paths, "Observation")
    current: dict[str, Any] | None = None
    if current_context_path is not None and current_context is not None:
        raise ViewerInputError("Provide current_context_path or current_context, not both")
    if current_context_path is not None:
        current, _ = _read_json(Path(current_context_path).resolve())
        if not isinstance(current, dict):
            raise ViewerInputError("Current context must be a JSON object")
    elif current_context is not None:
        if not isinstance(current_context, dict):
            raise ViewerInputError("Current context must be a JSON object")
        current = copy.deepcopy(current_context)
    checks = _plan_checks(plan)
    items = [_item_result(check, plan_file, records, assessments, observations, current) for check in checks]
    historical = _summary(items, "historical_status")
    current_summary = _summary(items, "current_status", required_only=True)
    return {
        "schema_version": 1,
        "read_only": True,
        "test_commands_executed": 0,
        "current_source_check": "fixed read-only Git commands; no submitted argv executed",
        "plan": {"path": str(plan_file), "sha256": _sha256(plan_raw), "id": plan.get("plan_id")},
        "historical": historical,
        "current": current_summary,
        "status": current_summary["status"],
        "statuses": current_summary["statuses"],
        "items": items,
        "remaining": sorted({reason for item in items for reason in item["reasons"] if reason}),
    }


def prepare_plan(root: Path, spec_path: Path, output: Path) -> dict[str, Any]:
    """Bind project-selected assertions to registered commands; never execute them."""
    root = _safe_cwd(Path(root).absolute(), 'project')
    spec_file = _safe_path(str(spec_path), root=root, label='spec', allow_absolute=True)
    output = _safe_path(str(output), root=root, label='output', allow_absolute=True)
    if output.exists():
        raise ViewerInputError('Prepared plan output already exists')
    ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '-q', '--', str(output)], capture_output=True)
    if ignored.returncode:
        raise ViewerInputError('Prepared plan output must be Git-ignored to preserve the measured source')
    spec, _ = _read_json(spec_file)
    if not isinstance(spec, dict) or spec.get('schema_version') != 1 or not isinstance(spec.get('checks'), list) or not spec['checks']:
        raise ViewerInputError('Preparation requires schema_version 1 and explicit checks')
    workflow = runpy.run_path(str(Path(__file__).with_name('project_workflow.py')))
    project, _ = _read_json(_safe_path('.harness/project.yaml', root=root, label='project'))
    config = workflow['configuration'](project)
    if config is None:
        raise ViewerInputError('Preparation requires configured workflow features')
    features = {feature['id']: feature for feature in config['features']}
    commands = dict(project.get('commands', {}))
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    checks = []
    for item in spec['checks']:
        allowed = {'id', 'feature_id', 'expected', 'required', 'selection', 'raw_observations', 'dependency', 'fixture'}
        if not isinstance(item, dict) or set(item) != allowed:
            raise ViewerInputError('Preparation checks require only semantic selection, raw assertions, dependency and fixture inputs')
        feature = features.get(item['feature_id'])
        if feature is None or item['id'] not in feature['checks'] or item['id'] not in commands:
            raise ViewerInputError('Preparation check is not registered to the selected Feature')
        descriptor = commands[item['id']]
        command = descriptor if isinstance(descriptor, dict) else {'argv': descriptor}
        cwd = _safe_cwd(_safe_path(command.get('working_directory', '.'), root=root, label='command'), 'command')
        criterion_files = {name: _path_hash(_safe_path(name, root=root, label='criteria'), 'criteria')
                           for name in feature['criteria']}
        revision = workflow['digest'](criterion_files)
        check = copy.deepcopy({key: value for key, value in item.items() if key not in {'dependency', 'fixture'}})
        check['criteria_revision'] = revision
        check['conditions'] = {'source': _git_snapshot(cwd), 'criteria': {'revision': revision},
                               'command': {'argv': command.get('argv'), 'cwd': str(cwd)},
                               'dependency': copy.deepcopy(item['dependency']), 'fixture': copy.deepcopy(item['fixture']),
                               'runtime': {}}
        for group in ('dependency', 'fixture'):
            if not isinstance(check['conditions'][group], dict) or not check['conditions'][group]:
                raise ViewerInputError(f'Preparation requires explicit {group} conditions')
        fixtures = check['conditions']['fixture']
        refs = _file_refs(fixtures, 'fixture')
        refs += [os.path.relpath(root / name, cwd) for name in
                 dict.fromkeys(['.harness/project.yaml'] + feature['criteria'] + feature['map'] + feature.get('ui', []))]
        fixtures.pop('files', None)
        fixtures['file_refs'] = list(dict.fromkeys(refs))
        check['conditions'] = _execution_conditions(check, cwd)
        checks.append(check)
    plan = {'schema_version': 1, 'checks': checks}
    _plan_checks(plan, allow_unbound=True)
    prepared = _preflight_execution(plan, checks, output.parent)
    if any(item['report_path'] == output for item in prepared.values()):
        raise ViewerInputError('Prepared plan output must differ from native report paths')
    _write_json(output, plan)
    return {'status': 'PREPARED', 'plan': str(output), 'checks': len(checks), 'test_commands_executed': 0}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--plan", type=Path)
    source.add_argument("--bundle", type=Path, help="Revalidate a retained execution bundle without running checks")
    source.add_argument('--prepare', type=Path, help='Prepare a plan from project-selected native assertions without executing checks')
    parser.add_argument('--root', type=Path, help='Configured project for --prepare')
    parser.add_argument('--plan-output', type=Path, help='New Git-ignored plan path for --prepare')
    parser.add_argument("--record", dest="records", action="append", default=[])
    parser.add_argument("--assessment", dest="assessments", action="append", default=[])
    parser.add_argument("--observation", dest="observations", action="append", default=[])
    parser.add_argument("--current-context", dest="current_context", type=Path)
    parser.add_argument("--execute", action="store_true", help="Execute selected plan checks through the capture CLI")
    parser.add_argument('--resume', action='store_true', help='Resume the same plan/directory using current completed checkpoints; never replay an unknown launch')
    parser.add_argument("--run-check", type=Path, help="Capture CLI override; an installed agentic-coding plugin uses its bundled scripts/run_check.py")
    parser.add_argument("--evidence-dir", "--output-dir", dest="evidence_dir", type=Path, help="New directory for execution captures and bound results")
    parser.add_argument("--timeout", type=float, default=300, help="Execution timeout passed to run_check.py")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.prepare:
        if not args.root or not args.plan_output or args.execute or args.resume or args.records or args.assessments or args.observations or args.current_context:
            _parser().error('--prepare requires --root and --plan-output, without execution or lookup inputs')
        try:
            result = prepare_plan(args.root, args.prepare, args.plan_output)
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
            result = {'status': 'BLOCKED', 'reason': str(error), 'test_commands_executed': 0}
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
        return 0 if result['status'] == 'PREPARED' else 2
    if args.root or args.plan_output:
        _parser().error('--root and --plan-output require --prepare')
    if args.resume and not args.execute:
        _parser().error('--resume requires --execute')
    if args.bundle:
        if args.execute or args.records or args.assessments or args.observations or args.current_context:
            result = _blocked_bundle("--bundle cannot combine with execution or manual evidence arguments")
        else:
            result = view_bundle(args.bundle)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
        return {"PASS": 0, "ISSUES": 1, "BLOCKED": 2}.get(result.get("status"), 2)
    if args.execute:
        if args.run_check is None and len(Path(__file__).resolve().parents) > 3:
            plugin = Path(__file__).resolve().parents[3]
            try:
                identity = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
                capture = plugin / "scripts/run_check.py"
                if isinstance(identity, dict) and identity.get("name") == "agentic-coding" and capture.is_file():
                    args.run_check = capture
            except (OSError, ValueError):
                pass  # Standalone Skills still require their project's explicit capture tool.
        if args.records or args.assessments or args.observations or args.current_context:
            result = _blocked_execution("--execute cannot combine with lookup evidence arguments", plan_path=args.plan, run_check_path=args.run_check)
        elif args.run_check is None or args.evidence_dir is None:
            result = _blocked_execution("--execute requires --run-check and --evidence-dir", plan_path=args.plan, run_check_path=args.run_check)
        else:
            try:
                result = execute_plan(
                    args.plan,
                    run_check_path=args.run_check,
                    evidence_dir=args.evidence_dir,
                    timeout=args.timeout,
                    resume=args.resume,
                )
            except (OSError, ValueError, TypeError, KeyError) as error:
                result = _blocked_execution(str(error), plan_path=args.plan, run_check_path=args.run_check)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
        return {"PASS": 0, "ISSUES": 1, "BLOCKED": 2}.get(result.get("status"), 2)
    try:
        result = view_results(
            args.plan,
            record_paths=args.records,
            assessment_paths=args.assessments,
            observation_paths=args.observations,
            current_context_path=args.current_context,
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        result = {
            "schema_version": 1,
            "read_only": True,
            "test_commands_executed": 0,
            "status": "BLOCKED",
            "statuses": ["BLOCKED"],
            "historical": {"status": "BLOCKED", "statuses": ["BLOCKED"], "counts": {"BLOCKED": 1}},
            "current": {"status": "BLOCKED", "statuses": ["BLOCKED"], "counts": {"BLOCKED": 1}},
            "items": [],
            "remaining": [str(error)],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
    return {"PASS": 0, "ISSUES": 1, "BLOCKED": 2}.get(result.get("status"), 2)


if __name__ == "__main__":
    raise SystemExit(main())
