"""Read-only viewer for plan-bound verification captures and observations.

The viewer joins an explicit plan with existing ``run_check.py`` captures,
project-adapter assessments, and raw JSON observations.  It never invokes an
argv found in a record and never writes to an evidence directory.  A result's
historical assessment is kept separate from its reuse under the current plan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
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


def _validate_raw_plan(check: dict[str, Any], index: int) -> None:
    descriptors = check.get("raw_observations", [])
    if not isinstance(descriptors, list):
        raise ViewerInputError(f"checks[{index}].raw_observations must be a list")
    for descriptor_index, descriptor in enumerate(descriptors):
        if not isinstance(descriptor, dict):
            raise ViewerInputError(f"checks[{index}].raw_observations[{descriptor_index}] must be an object")
        if not _text(descriptor.get("path")) or not _text(descriptor.get("sha256")) or not isinstance(descriptor.get("pointer"), str):
            raise ViewerInputError(
                f"checks[{index}].raw_observations[{descriptor_index}] needs path, sha256 and pointer"
            )


def _plan_checks(plan: dict[str, Any]) -> list[dict[str, Any]]:
    if plan.get("schema_version") != 1:
        raise ViewerInputError("Plan schema_version must be 1")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ViewerInputError("Plan must contain a nonempty checks list")
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ViewerInputError(f"checks[{index}] must be an object")
        for field in ("id", "feature_id", "expected", "criteria_revision", "required", "selection", "conditions"):
            if field not in check:
                raise ViewerInputError(f"checks[{index}].{field} is required")
        if not _text(check["id"]) or not _text(check["feature_id"]):
            raise ViewerInputError(f"checks[{index}] id and feature_id must be nonempty strings")
        if not isinstance(check["expected"], str) or not check["expected"].strip():
            raise ViewerInputError(f"checks[{index}].expected must be a nonempty string")
        if not _text(check["criteria_revision"]):
            raise ViewerInputError(f"checks[{index}].criteria_revision must be a nonempty string")
        if type(check["required"]) is not bool:
            raise ViewerInputError(f"checks[{index}].required must be boolean")
        selection = check["selection"]
        if not isinstance(selection, dict) or selection.get("status") not in SELECTIONS:
            raise ViewerInputError(f"checks[{index}].selection.status must be selected, excluded or not_required")
        conditions = check["conditions"]
        if not isinstance(conditions, dict):
            raise ViewerInputError(f"checks[{index}].conditions must be an object")
        for group in CONDITION_GROUPS:
            if group not in conditions:
                raise ViewerInputError(f"checks[{index}].conditions.{group} is required")
            if not isinstance(conditions[group], dict):
                raise ViewerInputError(f"checks[{index}].conditions.{group} must be an object")
        if "run_id" in check and not _text(check["run_id"]):
            raise ViewerInputError(f"checks[{index}].run_id must be a nonempty string when supplied")
        _validate_raw_plan(check, index)
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
) -> tuple[str, str, list[str]]:
    sources: list[tuple[str, str]] = []
    if assessment is not None:
        sources.append(("assessment", _status(assessment.get("status"))))
    if observation is not None:
        sources.append(("observation", _status(observation.get("status"))))
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
        historical, historical_source, historical_statuses = _historical(record, assessment, observation)
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


def view_results(
    plan_path: str | Path,
    *,
    record_paths: Iterable[str | Path] = (),
    assessment_paths: Iterable[str | Path] = (),
    observation_paths: Iterable[str | Path] = (),
    current_context_path: str | Path | None = None,
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
    if current_context_path is not None:
        current, _ = _read_json(Path(current_context_path).resolve())
        if not isinstance(current, dict):
            raise ViewerInputError("Current context must be a JSON object")
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--record", dest="records", action="append", default=[])
    parser.add_argument("--assessment", dest="assessments", action="append", default=[])
    parser.add_argument("--observation", dest="observations", action="append", default=[])
    parser.add_argument("--current-context", dest="current_context", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
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
