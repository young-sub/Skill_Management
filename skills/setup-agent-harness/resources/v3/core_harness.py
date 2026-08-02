# Generated file. Do not edit directly.
# Source: authoring/scripts/core_harness.py
# Source-SHA256: e173747c6c0a20251bdbdf874fea72a676c2694ea139285e49124e5b6d535378

#!/usr/bin/env python3
"""Deterministic Core-First Harness v3 contracts and compatibility checks."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter
from datetime import date, datetime, timedelta
from hashlib import sha256
import html
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any
import unicodedata


SCHEMA_VERSION = 3
COHORT_COMPONENTS = ("project", "design", "execute", "close", "maintain")
ITEM_FIELDS = (
    "id", "title", "behavior_type", "what", "steps", "terms", "tests", "done",
    "depends_on", "non_goals", "decision", "material_risks", "priority",
)


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _contract_payload(contract: dict[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in contract.items() if key != "approval"}


def preview_project_v3(legacy: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, dormant v3 preview without mutating legacy input."""
    if legacy.get("version") != 2:
        raise ValueError(f"unsupported_project_version:{legacy.get('version', 'missing')}")
    source = deepcopy(legacy)
    project = source.get("project", {})
    work = source.get("work", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "harness": {
            "active_cohort": "v2",
            "contract_version": 2,
            "runtime_version": 2,
            "dormant_cohorts": [3],
            "components": {name: {"supports": [2, 3]} for name in COHORT_COMPONENTS},
        },
        "project": {
            "name": project.get("name", "project"),
            "classification": project.get("classification", "unclassified"),
        },
        "paths": {
            "source_roots": [], "test_roots": [], "fixture_roots": [],
            "generated_roots": [], "durable_document_roots": ["docs"],
            "human_guide_roots": [], "ephemeral_work_root": work.get("root", ".work"),
            "documentation_entrypoint": "docs/index.md",
        },
        "impact": {"rules": [], "feature_selectors": {}, "full_triggers": []},
        "commands": {},
        "documents": {"boundaries": []},
        "work": {
            "retention": {
                "completed_days": work.get("retention_days", 30),
                "trash_days": work.get("trash_grace_days", 7),
            },
            "states": ["active", "completed", "trash", "deleted"],
        },
        "git": {
            "capture_current_base": True, "protected_branches": [],
            "branch_pattern": "wp-{work_id}-{slug}", "commit_per_item": True,
            "worktrees_for_independent_items": True,
        },
        "baseline": {"findings": []},
        "extensions": {},
        "migration": {"from_version": 2, "mode": "preview", "source": source},
    }


def validate_contract_v3(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported_contract_version:{contract.get('schema_version', 'missing')}")
    items = contract.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 5:
        errors.append("items:count:1..5")
        return errors
    seen: set[str] = set()
    dependency_map: dict[str, list[str]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"item:{index}:expected_object")
            continue
        item_id = str(item.get("id", index))
        if item_id in seen:
            errors.append(f"item:{item_id}:duplicate_id")
        seen.add(item_id)
        for field in ITEM_FIELDS:
            if field not in item or item[field] in (None, ""):
                errors.append(f"item:{item_id}:missing:{field}")
        for field in ("steps", "tests", "done", "depends_on", "non_goals", "material_risks"):
            if field in item and not isinstance(item[field], list):
                errors.append(f"item:{item_id}:expected_list:{field}")
        if item.get("decision", {}).get("state") not in {"resolved", "unresolved"}:
            errors.append(f"item:{item_id}:invalid_decision_state")
        dependency_map[item_id] = item.get("depends_on", []) if isinstance(item.get("depends_on"), list) else []
    for item_id, dependencies in dependency_map.items():
        for dependency in dependencies:
            if dependency not in seen:
                errors.append(f"item:{item_id}:missing_dependency:{dependency}")
    return sorted(set(errors))


def build_approval_bundle(
    contract: dict[str, Any], review_html: str, *, utterance: str,
    actor: str, approved_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_digest": canonical_digest(_contract_payload(contract)),
        "review_digest": canonical_digest(review_html),
        "item_ids": [item.get("id") for item in contract.get("items", [])],
        "utterance": utterance,
        "actor": actor,
        "approved_at": approved_at,
    }


def approval_bundle_matches(
    bundle: dict[str, Any], contract: dict[str, Any], review_html: str
) -> bool:
    return (
        bundle.get("schema_version") == SCHEMA_VERSION
        and bundle.get("contract_digest") == canonical_digest(_contract_payload(contract))
        and bundle.get("review_digest") == canonical_digest(review_html)
        and bundle.get("item_ids") == [item.get("id") for item in contract.get("items", [])]
    )


def validate_cohort(active_version: int, support: dict[str, list[int]]) -> list[str]:
    errors: list[str] = []
    if active_version not in {2, 3}:
        errors.append(f"unsupported_active_cohort:{active_version}")
    for component in COHORT_COMPONENTS:
        versions = support.get(component, [])
        if active_version not in versions:
            errors.append(f"mixed_cohort:{component}:{active_version}")
    return errors


def _relative_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts and ".work" not in path.parts),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def _hash_roots(root: Path, roots: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative_root in roots:
        base = _safe_repo_path(root, relative_root)
        if not base.exists():
            continue
        paths = [base] if base.is_file() else sorted(path for path in base.rglob("*") if path.is_file())
        for path in paths:
            result[path.relative_to(root).as_posix()] = "sha256:" + sha256(path.read_bytes()).hexdigest()
    return result


def static_inventory(root: Path, mapping: dict[str, Any] | None = None) -> dict[str, Any]:
    """Inspect bytes and declarations only; never execute repository content."""
    root = root.resolve()
    mapping = deepcopy(mapping or {})
    files = [path.relative_to(root).as_posix() for path in _relative_files(root)]
    declared: list[list[str]] = []
    command_pattern = re.compile(r"`([^`\r\n]+)`")
    for path in _relative_files(root):
        if path.suffix.lower() not in {".md", ".yml", ".yaml", ".toml", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for candidate in command_pattern.findall(text):
            try:
                argv = shlex.split(candidate, posix=True)
            except ValueError:
                continue
            if argv and argv[0].lower() in {"python", "python3", "pytest", "npm", "pnpm", "yarn", "dotnet", "go", "cargo", "powershell"}:
                if argv not in declared:
                    declared.append(argv)
    source_roots = list(mapping.get("source_roots", []))
    return {
        "schema_version": SCHEMA_VERSION,
        "files": files,
        "paths": mapping,
        "production_hashes": _hash_roots(root, source_roots),
        "declared_commands": declared,
        "dynamic_evidence": {
            "status": "unknown", "tests": "unknown", "collection": "unknown",
            "timings": "unknown", "reason": "static_inventory_does_not_execute_repository_content",
        },
    }


def _identity(path: Path, *, case_sensitive: bool) -> str:
    value = unicodedata.normalize("NFC", str(path.resolve(strict=False)))
    return value if case_sensitive else value.casefold()


def _safe_repo_path(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path_escape:{relative}") from error
    probe = candidate
    while probe != root:
        if (probe / ".git").exists():
            raise ValueError(f"nested_repository_boundary:{relative}")
        probe = probe.parent
    return candidate


def validate_path_owners(
    root: Path, owners: dict[str, list[str]], *, case_sensitive: bool | None = None
) -> list[str]:
    root = root.resolve()
    if case_sensitive is None:
        case_sensitive = os.name != "nt"
    entries: list[tuple[str, str, Path]] = []
    errors: list[str] = []
    for owner, paths in owners.items():
        for relative in paths:
            try:
                path = _safe_repo_path(root, relative)
            except ValueError as error:
                errors.append(str(error))
                continue
            entries.append((owner, relative, path))
    for index, (owner, relative, path) in enumerate(entries):
        for other_owner, other_relative, other_path in entries[index + 1:]:
            same = _identity(path, case_sensitive=case_sensitive) == _identity(other_path, case_sensitive=case_sensitive)
            nested = False
            try:
                path.relative_to(other_path)
                nested = True
            except ValueError:
                try:
                    other_path.relative_to(path)
                    nested = True
                except ValueError:
                    pass
            if owner != other_owner and (same or nested):
                errors.append(f"owner_overlap:{owner}:{relative}:{other_owner}:{other_relative}")
    return sorted(set(errors))


def build_mapping_plan(root: Path, mapping: dict[str, Any]) -> dict[str, Any]:
    owners = {
        "source": list(mapping.get("source_roots", [])),
        "tests": list(mapping.get("test_roots", [])),
        "fixtures": list(mapping.get("fixture_roots", [])),
        "documents": list(mapping.get("durable_document_roots", [])),
        "generated": list(mapping.get("generated_roots", [])),
    }
    unresolved = validate_path_owners(root, owners)
    entrypoint = mapping.get("documentation_entrypoint")
    if entrypoint and not (root / entrypoint).is_file():
        unresolved.append(f"missing_documentation_entrypoint:{entrypoint}")
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "mapping-first",
        "mapping": deepcopy(mapping),
        "inventory": static_inventory(root, mapping),
        "mutations": [],
        "unresolved": sorted(set(unresolved)),
    }


def _plan_with_digest(payload: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(payload)
    result["digest"] = canonical_digest(payload)
    return result


def build_project_migration(root: Path, legacy: dict[str, Any]) -> dict[str, Any]:
    preview = preview_project_v3(legacy)
    content = json.dumps(preview, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return _plan_with_digest({
        "schema_version": SCHEMA_VERSION,
        "mode": "project-migration",
        "root": str(root.resolve()),
        "operations": [{"action": "write", "path": ".harness/project.yaml", "content": content}],
        "source_roots": [],
        "production_hashes_before": {},
    })


def build_cleanup_plan(
    root: Path, *, mode: str, source_roots: list[str], operations: list[dict[str, Any]]
) -> dict[str, Any]:
    if mode not in {"document-only", "test-only"}:
        raise ValueError(f"unsupported_cleanup_mode:{mode}")
    root = root.resolve()
    production = _hash_roots(root, source_roots)
    source_paths = [_safe_repo_path(root, item) for item in source_roots]
    for operation in operations:
        relevant = operation.get("path") or operation.get("source") or operation.get("target")
        if not isinstance(relevant, str):
            raise ValueError("operation_path_missing")
        candidate = _safe_repo_path(root, relevant)
        for source_path in source_paths:
            try:
                candidate.relative_to(source_path)
            except ValueError:
                continue
            raise ValueError(f"production_mutation_forbidden:{relevant}")
    return _plan_with_digest({
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "root": str(root),
        "operations": deepcopy(operations),
        "source_roots": list(source_roots),
        "production_hashes_before": production,
    })


def _operation_paths(operation: dict[str, Any]) -> list[str]:
    return [str(operation[key]) for key in ("path", "source", "target") if key in operation]


def _restore_snapshot(root: Path, snapshot: dict[str, bytes | None]) -> None:
    for relative, content in snapshot.items():
        path = _safe_repo_path(root, relative)
        if content is None:
            if path.is_file():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    for relative, content in sorted(snapshot.items(), key=lambda item: len(Path(item[0]).parts), reverse=True):
        if content is None:
            parent = (_safe_repo_path(root, relative)).parent
            while parent != root and parent.name != ".work":
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent


def apply_transaction(
    root: Path, plan: dict[str, Any], *, approval_digest: str, fault_after: int | None = None
) -> dict[str, Any]:
    root = root.resolve()
    expected = canonical_digest({key: value for key, value in plan.items() if key != "digest"})
    if approval_digest != plan.get("digest") or plan.get("digest") != expected:
        return {"status": "approval_required", "expected_digest": plan.get("digest")}
    if str(root) != plan.get("root"):
        return {"status": "precondition_failed", "errors": ["root_drift"]}
    operations = plan.get("operations", [])
    affected = sorted(set(relative for operation in operations for relative in _operation_paths(operation)))
    snapshot: dict[str, bytes | None] = {}
    try:
        for relative in affected:
            path = _safe_repo_path(root, relative)
            snapshot[relative] = path.read_bytes() if path.is_file() else None
    except (OSError, ValueError) as error:
        return {"status": "precondition_failed", "errors": [str(error)]}
    transaction_id = str(plan["digest"]).removeprefix("sha256:")[:16]
    transaction_root = root / ".work" / "transactions" / transaction_id
    transaction_root.mkdir(parents=True, exist_ok=True)
    journal_path = transaction_root / "journal.json"
    journal = {"schema_version": SCHEMA_VERSION, "status": "applying", "plan_digest": plan["digest"], "completed_operations": 0}
    journal_path.write_text(json.dumps(journal, sort_keys=True), encoding="utf-8")
    try:
        for number, operation in enumerate(operations, 1):
            action = operation.get("action")
            if action == "write":
                target = _safe_repo_path(root, operation["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(operation["content"], encoding="utf-8", newline="\n")
            elif action == "move":
                source = _safe_repo_path(root, operation["source"])
                target = _safe_repo_path(root, operation["target"])
                if not source.is_file() or target.exists():
                    raise ValueError(f"move_precondition_failed:{operation['source']}:{operation['target']}")
                content = source.read_bytes()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                source.unlink()
            elif action == "replace":
                target = _safe_repo_path(root, operation["path"])
                text = target.read_text(encoding="utf-8")
                if operation["old"] not in text:
                    raise ValueError(f"replace_precondition_failed:{operation['path']}")
                target.write_text(text.replace(operation["old"], operation["new"]), encoding="utf-8", newline="\n")
            elif action == "remove":
                target = _safe_repo_path(root, operation["path"])
                if not target.is_file():
                    raise ValueError(f"remove_precondition_failed:{operation['path']}")
                target.unlink()
            else:
                raise ValueError(f"unsupported_operation:{action}")
            journal["completed_operations"] = number
            journal_path.write_text(json.dumps(journal, sort_keys=True), encoding="utf-8")
            if fault_after == number:
                raise RuntimeError(f"fault_injected_after:{number}")
        production_after = _hash_roots(root, list(plan.get("source_roots", [])))
        if production_after != plan.get("production_hashes_before", {}):
            raise RuntimeError("production_hash_drift")
        journal["status"] = "committed"
        journal_path.write_text(json.dumps(journal, sort_keys=True), encoding="utf-8")
        return {
            "status": "committed", "transaction_id": transaction_id,
            "production_hashes_before": plan.get("production_hashes_before", {}),
            "production_hashes_after": production_after,
        }
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        _restore_snapshot(root, snapshot)
        journal["status"] = "rolled_back"
        journal["error"] = str(error)
        journal_path.write_text(json.dumps(journal, sort_keys=True), encoding="utf-8")
        return {"status": "rolled_back", "transaction_id": transaction_id, "error": str(error)}


def finding_is_baselined(
    baseline: dict[str, Any], finding: dict[str, Any], *, today: str
) -> bool:
    fields = ("rule_id", "location", "severity", "fingerprint")
    if any(baseline.get(field) != finding.get(field) for field in fields):
        return False
    try:
        return date.fromisoformat(today) <= date.fromisoformat(str(baseline["review_until"]))
    except (KeyError, ValueError):
        return False


def run_dynamic_baseline(
    root: Path, descriptor: dict[str, Any], *, approved_capabilities: list[str]
) -> dict[str, Any]:
    capability = descriptor.get("capability")
    if capability not in approved_capabilities:
        return {"status": "not_authorized", "capability": capability}
    argv = descriptor.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
        return {"status": "invalid_descriptor", "errors": ["argv_required"]}
    try:
        working_directory = _safe_repo_path(root.resolve(), descriptor.get("working_directory", "."))
    except ValueError as error:
        return {"status": "invalid_descriptor", "errors": [str(error)]}
    inherited = descriptor.get("inherit_env", ["SystemRoot", "WINDIR", "TEMP", "TMP"])
    environment = {key: os.environ[key] for key in inherited if key in os.environ}
    for key, value in descriptor.get("env", {}).items():
        if not isinstance(key, str) or not isinstance(value, str):
            return {"status": "invalid_descriptor", "errors": ["env_must_be_string_map"]}
        environment[key] = value
    started = time.monotonic()
    try:
        result = subprocess.run(
            argv, cwd=working_directory, env=environment, capture_output=True, text=True,
            check=False, timeout=descriptor.get("timeout_seconds", 300),
        )
        status = "passed" if result.returncode == 0 else "failed"
        return {
            "status": status, "capability": capability, "command_id": descriptor.get("id"),
            "argv": argv, "working_directory": str(working_directory),
            "source_revision": descriptor.get("source_revision"),
            "runtime": descriptor.get("runtime", sys.implementation.name),
            "platform": sys.platform, "returncode": result.returncode,
            "duration_seconds": round(time.monotonic() - started, 6),
            "stdout": result.stdout, "stderr": result.stderr,
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "status": "collection_error", "capability": capability, "argv": argv,
            "working_directory": str(working_directory), "source_revision": descriptor.get("source_revision"),
            "runtime": descriptor.get("runtime", sys.implementation.name), "platform": sys.platform,
            "duration_seconds": round(time.monotonic() - started, 6), "error": str(error),
        }


def compare_semantic_test_inventory(
    before: list[dict[str, Any]], after: list[dict[str, Any]]
) -> list[str]:
    def semantic(records: list[dict[str, Any]]) -> Counter[tuple[Any, ...]]:
        return Counter(
            (
                record.get("capability"), record.get("suite"), record.get("test"),
                record.get("parameter"), record.get("outcome"), record.get("collection_error"),
            )
            for record in records
        )
    return [] if semantic(before) == semantic(after) else ["semantic_test_inventory_changed"]


def _list_html(values: list[Any]) -> str:
    return "<ul>" + "".join(f"<li>{html.escape(str(value))}</li>" for value in values) + "</ul>"


def _review_template(name: str) -> str:
    candidates = (
        Path(__file__).resolve().parents[1] / "templates" / "review" / name,
        Path(__file__).resolve().parent / "templates" / "review" / name,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError(f"review_template_missing:{name}")


def render_design_review_v3(contract: dict[str, Any]) -> str:
    """Render the canonical Item projection; never embed contract source text."""
    errors = validate_contract_v3(contract)
    structural = [error for error in errors if "invalid_decision_state" not in error]
    if structural:
        raise ValueError("invalid_contract:" + ";".join(structural))
    cards: list[str] = []
    unresolved = 0
    for item in contract["items"]:
        decision = item.get("decision", {}).get("state")
        if decision == "unresolved":
            unresolved += 1
        status = "✓ 결정 완료" if decision == "resolved" else "! 결정 필요"
        terms = "".join(
            '<p class="term"><strong>' + html.escape(str(term.get("term", ""))) + "</strong>: "
            + html.escape(str(term.get("explanation", ""))) + "</p>"
            for term in item.get("terms", [])
        )
        flow = '<div class="flow" aria-label="동작 흐름">' + "".join(
            '<span class="flow-step">' + html.escape(str(step)) + "</span>"
            + ('<span class="arrow" aria-hidden="true">→</span>' if index < len(item["steps"]) - 1 else "")
            for index, step in enumerate(item["steps"])
        ) + "</div>"
        cards.append(
            '<article class="item" data-item-id="' + html.escape(item["id"]) + '">'
            '<header><span class="item-id">' + html.escape(item["id"]) + "</span><h2>"
            + html.escape(item["title"]) + '</h2><span class="status">' + status + "</span></header>"
            + '<section><h3>무엇을 구현하나요</h3><p>' + html.escape(item["what"]) + "</p></section>"
            + '<section><h3>어떻게 동작하나요</h3>' + flow + terms + "</section>"
            + '<section><h3>어떻게 테스트하나요</h3>' + _list_html(item["tests"]) + "</section>"
            + '<section><h3>완료 기준</h3>' + _list_html(item["done"]) + "</section></article>"
        )
    decision_text = "결정 대기 없음" if unresolved == 0 else f"결정 필요 {unresolved}건"
    summary = (
        '<section class="summary"><div class="eyebrow">DESIGN REVIEW</div><h1>'
        + html.escape(contract.get("goal", "")) + "</h1><p>"
        + html.escape(contract.get("scope", "")) + '</p><p class="boundary">범위 밖: '
        + html.escape("; ".join(contract.get("non_goals", []))) + "</p><p>Item "
        + str(len(contract["items"])) + "개 · " + decision_text + "</p></section>"
    )
    return _review_template("design-item-review.html").replace("{{SUMMARY}}", summary).replace("{{ITEMS}}", "".join(cards)).rstrip() + "\n"


def approve_review(
    contract: dict[str, Any], review_html: str, *, utterance: str, actor: str, approved_at: str
) -> dict[str, Any]:
    if any(item.get("decision", {}).get("state") != "resolved" for item in contract.get("items", [])):
        return {"status": "unresolved_decisions"}
    normalized = utterance.strip().casefold().rstrip(".! ")
    affirmative = normalized in {"승인", "승인합니다", "진행", "진행합니다", "approve", "approved", "yes"}
    if not affirmative:
        return {"status": "ambiguous_approval"}
    approved = deepcopy(contract)
    approved["approval"] = build_approval_bundle(
        contract, review_html, utterance=utterance, actor=actor, approved_at=approved_at
    )
    return {"status": "approved", "contract": approved}


def execution_authorized(
    contract: dict[str, Any], review_html: str, *, host_goal: dict[str, Any] | None
) -> dict[str, Any]:
    del host_goal  # tracking is optional; approval is the authority.
    bundle = contract.get("approval")
    if not isinstance(bundle, dict):
        return {"authorized": False, "errors": ["approval_required"]}
    if not approval_bundle_matches(bundle, contract, review_html):
        return {"authorized": False, "errors": ["approval_bundle_drift"]}
    return {"authorized": True, "errors": []}


def convert_legacy_contract(legacy: dict[str, Any]) -> dict[str, Any]:
    status = legacy.get("status", "pending")
    if status in {"in_progress", "blocked", "crash_interrupted"}:
        return {"status": "cutover_blocked", "reason": f"legacy_work_{status}"}
    requirements = list(legacy.get("requirements", []))
    objective = str(legacy.get("objective", ""))
    unresolved = [field for field in ("behavior_type", "observable_tests", "completion_criteria") if not legacy.get(field)]
    item = {
        "id": "I-01", "title": objective or "Legacy work", "behavior_type": legacy.get("behavior_type", "migration"),
        "what": objective, "steps": requirements or [objective], "terms": [],
        "tests": list(legacy.get("observable_tests", requirements or ["Resolve observable tests"])),
        "done": list(legacy.get("completion_criteria", requirements or ["Resolve completion criteria"])),
        "depends_on": [], "non_goals": list(legacy.get("non_goals", [])),
        "decision": {"state": "unresolved" if unresolved else "resolved"},
        "material_risks": [], "priority": "core",
    }
    return {
        "status": "converted",
        "contract": {
            "schema_version": SCHEMA_VERSION, "work_id": legacy.get("work_id", ""),
            "goal": objective, "scope": objective, "non_goals": list(legacy.get("non_goals", [])),
            "items": [item],
        },
        "unresolved_fields": unresolved,
    }


def next_item(contract: dict[str, Any], state: dict[str, str]) -> dict[str, Any] | None:
    ready = [
        item for item in contract.get("items", [])
        if state.get(item["id"], "pending") == "pending"
        and all(state.get(dependency) == "completed" for dependency in item.get("depends_on", []))
    ]
    ready.sort(key=lambda item: (item.get("priority") != "core", contract["items"].index(item)))
    return deepcopy(ready[0]) if ready else None


def apply_amendment(
    contract: dict[str, Any], *, item_id: str, field: str, value: Any, message_id: str,
    actor: str, approved_at: str, risk: str,
) -> dict[str, Any]:
    if risk in {"public_contract", "high", "destructive", "security", "privacy", "irreversible", "external_cost"}:
        return {"status": "focused_approval_required", "item_id": item_id, "field": field, "risk": risk}
    amended = deepcopy(contract)
    item = next((candidate for candidate in amended.get("items", []) if candidate.get("id") == item_id), None)
    if item is None or field not in ITEM_FIELDS:
        return {"status": "invalid_amendment", "errors": ["unknown_item_or_field"]}
    old_digest = canonical_digest(_contract_payload(contract))
    item[field] = value
    event = {
        "kind": "approved_amendment", "message_id": message_id, "item_id": item_id,
        "field": field, "actor": actor, "approved_at": approved_at,
        "old_contract_digest": old_digest,
    }
    amended.setdefault("amendments", []).append(event)
    event["new_contract_digest"] = canonical_digest(_contract_payload(amended))
    return {"status": "applied", "contract": amended, "event": event}


def commit_item(
    root: Path, item_id: str, paths: list[str], *, dirty_baseline: list[str]
) -> dict[str, Any]:
    overlap = sorted(set(paths) & set(dirty_baseline))
    if overlap:
        return {"status": "dirty_baseline_conflict", "paths": overlap}
    for relative in paths:
        _safe_repo_path(root.resolve(), relative)
    add = subprocess.run(["git", "add", "--", *paths], cwd=root, capture_output=True, text=True, check=False)
    if add.returncode:
        return {"status": "git_error", "error": add.stderr.strip()}
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--"], cwd=root,
        capture_output=True, text=True, check=False,
    )
    staged_paths = [line for line in staged.stdout.splitlines() if line]
    unexpected = sorted(set(staged_paths) - set(paths))
    if unexpected:
        subprocess.run(["git", "restore", "--staged", "--", *unexpected], cwd=root, capture_output=True, check=False)
        return {"status": "unexpected_staged_paths", "paths": unexpected}
    committed = subprocess.run(
        ["git", "commit", "-m", f"feat(harness): complete {item_id}"], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if committed.returncode:
        return {"status": "git_error", "error": (committed.stderr or committed.stdout).strip()}
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()
    return {"status": "committed", "item_id": item_id, "commit": revision, "paths": staged_paths}


def select_impacted_checks(
    changed_paths: list[str], project: dict[str, Any]
) -> dict[str, Any]:
    rules = project.get("impact", {}).get("rules", [])
    matched_rules: list[str] = []
    tests: list[str] = []
    features: list[str] = []
    unresolved: list[str] = []
    full_required = False
    for path in changed_paths:
        matches = [
            rule for rule in rules
            if any(path.replace("\\", "/").startswith(prefix.replace("\\", "/")) for prefix in rule.get("source_prefixes", []))
        ]
        if not matches:
            unresolved.append(path)
            continue
        for rule in matches:
            rule_id = str(rule.get("id", "unnamed"))
            if rule_id not in matched_rules:
                matched_rules.append(rule_id)
            for test in rule.get("tests", []):
                if test not in tests:
                    tests.append(test)
            feature = rule.get("feature")
            if feature and feature not in features:
                features.append(feature)
            full_required = full_required or bool(rule.get("full"))
    return {
        "matched_rules": matched_rules, "tests": tests, "features": features,
        "full_required": full_required, "unresolved": unresolved,
    }


def evaluate_result(
    contract: dict[str, Any], result: dict[str, Any], impact: dict[str, Any]
) -> dict[str, Any]:
    result_by_id = {item.get("id"): item for item in result.get("items", [])}
    evaluated: list[dict[str, Any]] = []
    errors: list[str] = []
    for planned in contract.get("items", []):
        actual = result_by_id.get(planned["id"])
        item_errors: list[str] = []
        if actual is None:
            item_errors.append("missing_result")
        else:
            checks = actual.get("checks", [])
            if not checks or any(check.get("status") not in {"passed", "not_required"} for check in checks):
                item_errors.append("relevant_check_failed_or_unrun")
            if not actual.get("done") or not all(actual.get("done", [])):
                item_errors.append("completion_criteria_unmet")
            if actual.get("delta", {}).get("material") and actual.get("delta", {}).get("approval") != "approved":
                item_errors.append("material_delta_unapproved")
        evaluated.append({"id": planned["id"], "status": "complete" if not item_errors else "incomplete", "errors": item_errors})
        errors.extend(f"{planned['id']}:{error}" for error in item_errors)
    if impact.get("unresolved"):
        errors.append("unresolved_test_impact")
    full_status = result.get("full", {}).get("status", "unrun")
    if impact.get("full_required") and full_status != "passed":
        errors.append("full_required_but_unrun")
    if not impact.get("full_required") and full_status == "not_required" and not result.get("full", {}).get("rule"):
        errors.append("full_not_required_rule_missing")
    return {
        "status": "complete" if not errors else "incomplete", "items": evaluated,
        "full": "required" if impact.get("full_required") else full_status,
        "errors": errors,
    }


def render_result_review_v3(contract: dict[str, Any], result: dict[str, Any]) -> str:
    result_by_id = {item.get("id"): item for item in result.get("items", [])}
    cards: list[str] = []
    completed = 0
    for planned in contract.get("items", []):
        actual = result_by_id.get(planned["id"], {})
        checks = actual.get("checks", [])
        done = bool(actual.get("done")) and all(actual.get("done", []))
        checks_ok = bool(checks) and all(check.get("status") in {"passed", "not_required"} for check in checks)
        delta = actual.get("delta", {})
        material = bool(delta.get("material"))
        complete = done and checks_ok and (not material or delta.get("approval") == "approved")
        completed += int(complete)
        status = "✓ 완료" if complete else "! 미완료"
        delta_text = "계획대로 구현됨 (implemented as planned)" if not material else "승인 필요: " + str(delta.get("summary", "material delta"))
        flow = '<div class="flow actual-flow" aria-label="실제 동작 흐름">' + "".join(
            '<span class="flow-step">' + html.escape(str(step)) + "</span>"
            + ('<span class="arrow" aria-hidden="true">→</span>' if index < len(actual.get("actual_steps", [])) - 1 else "")
            for index, step in enumerate(actual.get("actual_steps", []))
        ) + "</div>"
        check_rows = "".join(
            "<li><strong>" + html.escape(str(check.get("kind", "Check"))) + "</strong> · "
            + html.escape(str(check.get("status", "unknown"))) + " · "
            + html.escape(str(check.get("command", ""))) + "</li>"
            for check in checks
        )
        terms = "".join(
            '<p class="term"><strong>' + html.escape(str(term.get("term", ""))) + "</strong>: "
            + html.escape(str(term.get("explanation", ""))) + "</p>"
            for term in planned.get("terms", [])
        )
        cards.append(
            '<article class="item" data-item-id="' + html.escape(planned["id"]) + '"><header><span class="item-id">'
            + html.escape(planned["id"]) + "</span><h2>" + html.escape(planned["title"])
            + '</h2><span class="status">' + status + "</span></header>"
            + '<section><h3>실제 구현</h3><p>' + html.escape(str(actual.get("actual", "결과 없음"))) + "</p></section>"
            + '<section><h3>실제 동작</h3>' + flow + terms + "</section>"
            + '<section><h3>관련 테스트</h3><ul>' + check_rows + "</ul></section>"
            + '<section><h3>완료 기준</h3><p>' + ("충족" if done else "미충족") + "</p></section>"
            + '<section><h3>계획 대비 실제</h3><p class="delta' + (" material" if material else "") + '">' + html.escape(delta_text) + "</p></section></article>"
        )
    summary = (
        '<section class="summary"><div class="eyebrow">RESULT REVIEW</div><h1>'
        + html.escape(contract.get("goal", "")) + "</h1><p>완료 " + str(completed)
        + " / " + str(len(contract.get("items", []))) + "</p></section>"
    )
    return _review_template("result-item-review.html").replace("{{SUMMARY}}", summary).replace("{{ITEMS}}", "".join(cards)).rstrip() + "\n"


def close_work(
    root: Path, work_id: str, *, completed_at: str, completed_days: int, trash_days: int
) -> dict[str, Any]:
    root = root.resolve()
    source = _safe_repo_path(root, f".work/goals/active/{work_id}")
    manifest_path = source / "work.json"
    if not manifest_path.is_file():
        return {"status": "invalid_work", "errors": ["active_manifest_missing"]}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("work_id") != work_id or manifest.get("state") != "active":
        return {"status": "invalid_work", "errors": ["manifest_identity_or_state_invalid"]}
    moment = datetime.fromisoformat(completed_at)
    retain_until = moment + timedelta(days=completed_days)
    delete_after = retain_until + timedelta(days=trash_days)
    destination = _safe_repo_path(root, f".work/goals/completed/{moment:%Y-%m}/{work_id}")
    if destination.exists():
        return {"status": "conflict", "errors": ["completed_destination_exists"]}
    manifest.update({
        "state": "completed", "completed_at": moment.isoformat(),
        "retain_until": retain_until.isoformat(), "delete_after": delete_after.isoformat(),
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
    return {"status": "completed", "path": destination.relative_to(root).as_posix(), "manifest": manifest}


def audit_work_lifecycle(root: Path) -> dict[str, Any]:
    goals = root / ".work" / "goals"
    seen: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    for state in ("active", "completed", "trash", "legacy-unclassified"):
        state_root = goals / state
        if not state_root.is_dir():
            continue
        for directory in sorted(path for path in state_root.rglob("*") if path.is_dir()):
            if not any(child.is_dir() for child in directory.iterdir()) and not (directory / "work.json").is_file():
                findings.append({"rule_id": "work.orphan", "location": directory.relative_to(root).as_posix()})
    for manifest_path in goals.rglob("work.json") if goals.is_dir() else []:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            findings.append({"rule_id": "work.invalid_manifest", "location": str(manifest_path)})
            continue
        work_id = str(manifest.get("work_id", ""))
        location = manifest_path.parent.relative_to(root).as_posix()
        if work_id in seen:
            findings.append({"rule_id": "work.duplicate_id", "location": location})
        seen[work_id] = location
        expected_state = "legacy-unclassified" if "legacy-unclassified" in manifest_path.parts else next(
            (state for state in ("active", "completed", "trash") if state in manifest_path.parts), "unknown"
        )
        if manifest.get("state") != expected_state:
            findings.append({"rule_id": "work.invalid_state", "location": location})
    return {"findings": findings, "work_ids": seen}


def sweep_lifecycle(root: Path, *, now: str) -> dict[str, Any]:
    root = root.resolve()
    moment = datetime.fromisoformat(now)
    completed_root = root / ".work" / "goals" / "completed"
    moved: list[str] = []
    if completed_root.is_dir():
        for manifest_path in sorted(completed_root.rglob("work.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            retain_until = manifest.get("retain_until")
            if not retain_until or datetime.fromisoformat(retain_until) > moment:
                continue
            work_id = str(manifest.get("work_id", ""))
            source = manifest_path.parent
            destination = root / ".work" / "goals" / "trash" / f"{moment:%Y-%m-%d}" / work_id
            if destination.exists():
                continue
            manifest["state"] = "trash"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)
            moved.append(work_id)
    return {"status": "ok", "moved_to_trash": moved, "audit": audit_work_lifecycle(root)}


def classify_legacy_work(root: Path) -> dict[str, Any]:
    root = root.resolve()
    archive = root / ".work" / "archive"
    unclassified: list[str] = []
    if archive.is_dir():
        for entry in sorted(path for path in archive.iterdir() if path.is_dir()):
            work_id = entry.name
            destination = root / ".work" / "goals" / "legacy-unclassified" / work_id
            if destination.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(entry, destination)
            manifest = {
                "schema_version": SCHEMA_VERSION, "work_id": work_id, "state": "legacy-unclassified",
                "created_at": None, "source_commit": None, "reason": "trustworthy_completion_date_missing",
            }
            (destination / "work.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            unclassified.append(work_id)
    return {"status": "classified", "unclassified": unclassified}


def delete_trash(root: Path, relative_target: str, *, approved_exact_target: str | None) -> dict[str, Any]:
    expected_prefix = ".work/goals/trash/"
    normalized = relative_target.replace("\\", "/")
    if approved_exact_target != normalized:
        return {"status": "approval_required", "target": normalized}
    if not normalized.startswith(expected_prefix):
        return {"status": "invalid_target", "target": normalized}
    target = _safe_repo_path(root.resolve(), normalized)
    if not target.is_dir():
        return {"status": "not_found", "target": normalized}
    shutil.rmtree(target)
    return {"status": "deleted", "target": normalized, "recoverable": False}


def compare_findings_to_baseline(
    baseline: list[dict[str, Any]], findings: list[dict[str, Any]], *, today: str
) -> dict[str, Any]:
    baselined: list[dict[str, Any]] = []
    blocking: list[dict[str, Any]] = []
    for finding in findings:
        match = next((item for item in baseline if finding_is_baselined(item, finding, today=today)), None)
        (baselined if match else blocking).append(finding)
    return {"baselined": baselined, "blocking": blocking}
