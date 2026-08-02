# Generated file. Do not edit directly.
# Source: authoring/scripts/core_harness.py
# Source-SHA256: c35e46592a272cb44f04fdba51708900f6fd15c705c9e4d9def571dcac249f5d

#!/usr/bin/env python3
"""Deterministic Core-First Harness v3 contracts and compatibility checks."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter
from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shlex
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
        "contract_digest": canonical_digest(contract),
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
        and bundle.get("contract_digest") == canonical_digest(contract)
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
