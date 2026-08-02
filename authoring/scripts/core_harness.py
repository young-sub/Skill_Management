#!/usr/bin/env python3
"""Deterministic Core-First Harness v3 contracts and compatibility checks."""

from __future__ import annotations

import argparse
from copy import deepcopy
from collections import Counter
from datetime import date, datetime, timedelta
from hashlib import sha256
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any
import unicodedata


SCHEMA_VERSION = 3
WORK_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
COHORT_COMPONENTS = ("project", "design", "execute", "close", "maintain", "diagnose")
HARNESS_INSTALL_SKILLS = (
    "setup-agent-harness", "design-goal", "execute-codex-goal", "close-goal",
    "maintain-agent-harness", "diagnose",
)
ITEM_FIELDS = (
    "id", "title", "behavior_type", "what", "steps", "terms", "tests", "done",
    "depends_on", "non_goals", "decision", "material_risks", "priority",
)
BEHAVIOR_TYPES = {"tool", "api", "ui", "bugfix", "migration"}
ITEM_PRIORITIES = {"core", "optional"}
MATERIAL_RISK_FLAGS = {
    "destructive", "security_privacy", "secret_handling",
    "irreversible_migration", "external_cost", "push", "publish",
    "global_configuration",
}


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def validate_work_id(work_id: Any) -> str:
    value = str(work_id)
    if not WORK_ID_PATTERN.fullmatch(value):
        raise ValueError(f"invalid_work_id:{value}")
    return value


def _contract_payload(contract: dict[str, Any]) -> dict[str, Any]:
    payload = {
        key: deepcopy(value) for key, value in contract.items()
        if key not in {"approval", "authorization"}
    }
    for amendment in payload.get("amendments", []):
        if isinstance(amendment, dict):
            amendment.pop("new_contract_digest", None)
    return payload


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
        "commands": {
            name: {
                "id": name, "argv": [], "working_directory": ".", "platform": "any",
                "runtime": "none" if name in {"live", "eval"} else "unknown",
                "capability": "disabled" if name in {"live", "eval"} else "mapping-required",
            }
            for name in ("targeted", "feature", "lint", "type", "build", "full", "live", "eval")
        },
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
    allowed_contract_fields = {
        "schema_version", "work_id", "goal", "scope", "non_goals", "items",
        "authorization", "amendments", "extensions",
    }
    for field in sorted(set(contract) - allowed_contract_fields):
        errors.append(f"contract:unknown_field:{field}")
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported_contract_version:{contract.get('schema_version', 'missing')}")
    for field in ("work_id", "goal", "scope"):
        if not isinstance(contract.get(field), str) or not contract[field].strip():
            errors.append(f"contract:missing:{field}")
    if isinstance(contract.get("work_id"), str):
        try:
            validate_work_id(contract["work_id"])
        except ValueError:
            errors.append("contract:invalid:work_id")
    contract_non_goals = contract.get("non_goals")
    if not isinstance(contract_non_goals, list):
        errors.append("contract:expected_list:non_goals")
    else:
        for index, value in enumerate(contract_non_goals):
            if not isinstance(value, str):
                errors.append(f"contract:non_goals:{index}:expected_string")
    items = contract.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 5:
        errors.append("items:count_out_of_range")
        return errors
    seen: set[str] = set()
    dependency_map: dict[str, list[str]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"item:{index}:expected_object")
            continue
        item_id = str(item.get("id", index))
        for field in sorted(set(item) - set(ITEM_FIELDS)):
            errors.append(f"item:{item_id}:unknown_field:{field}")
        if item_id in seen:
            errors.append(f"item:{item_id}:duplicate_id")
        seen.add(item_id)
        for field in ITEM_FIELDS:
            if field not in item or item[field] in (None, ""):
                errors.append(f"item:{item_id}:missing:{field}")
        for field in ("id", "title", "what"):
            if field in item and (not isinstance(item[field], str) or not item[field].strip()):
                errors.append(f"item:{item_id}:invalid:{field}")
        if item.get("behavior_type") not in BEHAVIOR_TYPES:
            errors.append(f"item:{item_id}:invalid_behavior_type")
        if item.get("priority") not in ITEM_PRIORITIES:
            errors.append(f"item:{item_id}:invalid_priority")
        for field in ("steps", "terms", "tests", "done", "depends_on", "non_goals", "material_risks"):
            if field in item and not isinstance(item[field], list):
                errors.append(f"item:{item_id}:expected_list:{field}")
        for field in ("steps", "depends_on", "non_goals"):
            values = item.get(field)
            if isinstance(values, list):
                if field == "steps" and not values:
                    errors.append(f"item:{item_id}:steps:empty")
                for value_index, value in enumerate(values):
                    if not isinstance(value, str) or (field == "steps" and not value.strip()):
                        errors.append(f"item:{item_id}:{field}:{value_index}:expected_string")
        risks = item.get("material_risks")
        if isinstance(risks, list):
            for risk in risks:
                if risk not in MATERIAL_RISK_FLAGS:
                    errors.append(f"item:{item_id}:invalid_material_risk:{risk}")
        terms = item.get("terms")
        if isinstance(terms, list):
            for term_index, term in enumerate(terms):
                if not isinstance(term, dict):
                    errors.append(f"item:{item_id}:term:{term_index}:expected_object")
                    continue
                if set(term) != {"term", "explanation"}:
                    errors.append(f"item:{item_id}:term:{term_index}:schema_invalid")
                for field in ("term", "explanation"):
                    if not isinstance(term.get(field), str) or not term[field].strip():
                        errors.append(f"item:{item_id}:term:{term_index}:missing:{field}")
        decision = item.get("decision")
        if not isinstance(decision, dict) or set(decision) != {"state"} or decision.get("state") not in {"resolved", "unresolved"}:
            errors.append(f"item:{item_id}:invalid_decision_state")
        tests = item.get("tests")
        if isinstance(tests, list):
            if not tests:
                errors.append(f"item:{item_id}:tests:empty")
            test_ids: set[str] = set()
            for test_index, test in enumerate(tests):
                if not isinstance(test, dict):
                    errors.append(f"item:{item_id}:test:{test_index}:expected_object")
                    continue
                allowed = {"id", "target", "method", "expected", "selector"}
                for field in sorted(set(test) - allowed):
                    errors.append(f"item:{item_id}:test:{test_index}:unknown_field:{field}")
                for field in allowed:
                    if not isinstance(test.get(field), str) or (field != "selector" and not test[field].strip()):
                        errors.append(f"item:{item_id}:test:{test_index}:missing:{field}")
                test_id = str(test.get("id", ""))
                if test_id in test_ids:
                    errors.append(f"item:{item_id}:test:{test_id}:duplicate_id")
                test_ids.add(test_id)
        done = item.get("done")
        if isinstance(done, list):
            if not done:
                errors.append(f"item:{item_id}:done:empty")
            done_ids: set[str] = set()
            for done_index, criterion in enumerate(done):
                if not isinstance(criterion, dict):
                    errors.append(f"item:{item_id}:done:{done_index}:expected_object")
                    continue
                for field in sorted(set(criterion) - {"id", "criterion"}):
                    errors.append(f"item:{item_id}:done:{done_index}:unknown_field:{field}")
                for field in ("id", "criterion"):
                    if not isinstance(criterion.get(field), str) or not criterion[field].strip():
                        errors.append(f"item:{item_id}:done:{done_index}:missing:{field}")
                criterion_id = str(criterion.get("id", ""))
                if criterion_id in done_ids:
                    errors.append(f"item:{item_id}:done:{criterion_id}:duplicate_id")
                done_ids.add(criterion_id)
        dependency_map[item_id] = item.get("depends_on", []) if isinstance(item.get("depends_on"), list) else []
    for item_id, dependencies in dependency_map.items():
        for dependency in dependencies:
            if dependency not in seen:
                errors.append(f"item:{item_id}:missing_dependency:{dependency}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> bool:
        if item_id in visiting:
            return True
        if item_id in visited:
            return False
        visiting.add(item_id)
        cycle = any(
            dependency in dependency_map and visit(dependency)
            for dependency in dependency_map.get(item_id, [])
        )
        visiting.remove(item_id)
        visited.add(item_id)
        return cycle

    if any(visit(item_id) for item_id in dependency_map):
        errors.append("items:dependency_cycle")
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


RESERVED_INVENTORY_ROOTS = {
    ".git", ".work", ".scratch", ".venv", "venv", "__pycache__",
    ".cache", ".pytest_cache", ".mypy_cache", "node_modules", "build", "dist", "back-up",
}


def enumerate_repository_files(
    root: Path, *, max_files: int = 10000, max_bytes: int = 128 * 1024 * 1024,
    timeout_seconds: float = 2.0,
) -> list[Path]:
    root = root.resolve()
    git_marker = root / ".git"
    if git_marker.exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root, capture_output=True, check=False,
        )
        if result.returncode == 0:
            relative_paths = [item.decode("utf-8", errors="surrogateescape") for item in result.stdout.split(b"\0") if item]
            files: list[Path] = []
            for relative in relative_paths:
                parts = PurePosixPath(relative.replace("\\", "/")).parts
                if any(part in RESERVED_INVENTORY_ROOTS for part in parts):
                    continue
                path = _safe_repo_path(root, relative)
                if path.is_file() and not _path_is_alias(path):
                    files.append(path)
            return sorted(files, key=lambda path: path.relative_to(root).as_posix())

    started = time.monotonic()
    files = []
    total_bytes = 0
    for directory, names, filenames in os.walk(root, topdown=True, followlinks=False):
        names[:] = sorted(
            name for name in names
            if name not in RESERVED_INVENTORY_ROOTS and not _path_is_alias(Path(directory) / name)
        )
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if _path_is_alias(path):
                continue
            try:
                size = path.stat().st_size
            except OSError as error:
                raise ValueError(f"inventory_stat_failed:{path}:{error}") from error
            total_bytes += size
            files.append(path)
            if len(files) > max_files or total_bytes > max_bytes or time.monotonic() - started > timeout_seconds:
                raise ValueError("non_git_inventory_budget_exceeded")
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def _relative_files(root: Path) -> list[Path]:
    return enumerate_repository_files(root)


def _hash_roots(root: Path, roots: list[str], *, files: list[Path] | None = None) -> dict[str, str]:
    result: dict[str, str] = {}
    candidates = files if files is not None else enumerate_repository_files(root)
    for relative_root in roots:
        base = _safe_repo_path(root, relative_root)
        if not base.exists():
            continue
        paths = [base] if base.is_file() and base in candidates else [
            path for path in candidates if path == base or base in path.parents
        ]
        for path in paths:
            result[path.relative_to(root).as_posix()] = "sha256:" + sha256(path.read_bytes()).hexdigest()
    return result


def static_inventory(root: Path, mapping: dict[str, Any] | None = None) -> dict[str, Any]:
    """Inspect bytes and declarations only; never execute repository content."""
    root = root.resolve()
    mapping = deepcopy(mapping or {})
    inventory_paths = _relative_files(root)
    files = [path.relative_to(root).as_posix() for path in inventory_paths]
    declared: list[list[str]] = []
    command_pattern = re.compile(r"`([^`\r\n]+)`")
    for path in inventory_paths:
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
    git_directory = root / ".git"
    head_path = git_directory / "HEAD"
    branch = "unknown"
    detached_commit: str | None = None
    if head_path.is_file():
        head = head_path.read_text(encoding="utf-8", errors="replace").strip()
        if head.startswith("ref: refs/heads/"):
            branch = head.removeprefix("ref: refs/heads/")
        elif head:
            branch = "detached"
            detached_commit = head
    worktrees_root = git_directory / "worktrees"
    worktrees = sorted(path.name for path in worktrees_root.iterdir() if path.is_dir()) if worktrees_root.is_dir() else []
    ci_files = sorted(
        path.relative_to(root).as_posix() for path in inventory_paths
        if path.relative_to(root).as_posix().startswith(".github/workflows/")
    )
    authority_names = ("AGENTS.md", "CLAUDE.md", "docs/index.md", "README.md")
    authority_candidates = [name for name in authority_names if (root / name).is_file()]
    candidate_directories = {parent for path in inventory_paths for parent in path.parents if parent != root}
    nested_repositories = sorted(
        path.relative_to(root).as_posix() for path in candidate_directories
        if (path / ".git").exists()
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "files": files,
        "paths": mapping,
        "production_hashes": _hash_roots(root, source_roots, files=inventory_paths),
        "declared_commands": declared,
        "git": {
            "branch": branch,
            "detached_commit": detached_commit,
            "worktrees": worktrees,
            "nested_repositories": nested_repositories,
            "protection": "unknown_static_inventory",
        },
        "ci_files": ci_files,
        "authority_candidates": authority_candidates,
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
            compatible_nesting = False
            if not same and {owner, other_owner} == {"tests", "fixtures"}:
                test_path = path if owner == "tests" else other_path
                fixture_path = path if owner == "fixtures" else other_path
                try:
                    fixture_path.relative_to(test_path)
                    compatible_nesting = True
                except ValueError:
                    pass
            if owner != other_owner and (same or nested) and not compatible_nesting:
                errors.append(f"owner_overlap:{owner}:{relative}:{other_owner}:{other_relative}")
    return sorted(set(errors))


def build_mapping_plan(
    root: Path, mapping: dict[str, Any], *, impact: dict[str, Any] | None = None
) -> dict[str, Any]:
    owners = {
        "source": list(mapping.get("source_roots", [])),
        "tests": list(mapping.get("test_roots", [])),
        "fixtures": list(mapping.get("fixture_roots", [])),
        "documents": list(mapping.get("durable_document_roots", [])),
        "human": list(mapping.get("human_guide_roots", [])),
        "generated": list(mapping.get("generated_roots", [])),
        "work": [str(mapping["ephemeral_work_root"])] if mapping.get("ephemeral_work_root") else [],
    }
    unresolved = validate_path_owners(root, owners)
    entrypoint = mapping.get("documentation_entrypoint")
    if entrypoint and not (root / entrypoint).is_file():
        unresolved.append(f"missing_documentation_entrypoint:{entrypoint}")
    if impact is not None:
        rules = list(impact.get("rules", []))
        for source_root in mapping.get("source_roots", []):
            normalized = str(source_root).replace("\\", "/").rstrip("/") + "/"
            if not any(
                normalized.startswith(str(prefix).replace("\\", "/").rstrip("/") + "/")
                or str(prefix).replace("\\", "/").rstrip("/").startswith(normalized.rstrip("/"))
                for rule in rules for prefix in rule.get("source_prefixes", [])
            ):
                unresolved.append(f"unknown_source_test_impact:{source_root}")
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


def _owned_path_kind(root: Path, relative: str, ownership: dict[str, Any]) -> str | None:
    groups = (
        ("production", ownership.get("source_roots", [])),
        ("tests", ownership.get("test_roots", [])),
        ("fixtures", ownership.get("fixture_roots", [])),
        ("documents", ownership.get("durable_document_roots", [])),
        ("human", ownership.get("human_guide_roots", [])),
        ("test_config", ownership.get("test_config_roots", [])),
        ("ci", ownership.get("ci_roots", [".github/workflows"])),
        ("config", ownership.get("config_roots", [".harness"])),
    )
    candidate = _safe_repo_path(root, relative)
    for kind, roots in groups:
        for configured in roots:
            owner = _safe_repo_path(root, str(configured))
            if candidate == owner or owner in candidate.parents:
                return kind
    return None


def build_cleanup_plan(
    root: Path, *, mode: str, source_roots: list[str], ownership: dict[str, Any] | None = None,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    if mode not in {"document-only", "test-only"}:
        raise ValueError(f"unsupported_cleanup_mode:{mode}")
    root = root.resolve()
    ownership = deepcopy(ownership or {})
    ownership.setdefault("source_roots", list(source_roots))
    production = _hash_roots(root, source_roots)
    allowed = {"documents", "human"} if mode == "document-only" else {"tests", "fixtures", "test_config", "ci"}
    for operation in operations:
        relevant_paths = _operation_paths(operation)
        if not relevant_paths:
            raise ValueError("operation_path_missing")
        for relevant in relevant_paths:
            kind = _owned_path_kind(root, relevant, ownership)
            if kind not in allowed:
                raise ValueError(f"mode_path_forbidden:{mode}:{relevant}:{kind or 'unowned'}")
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


def _durable_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _durable_write_json(path: Path, payload: dict[str, Any]) -> None:
    _durable_write_bytes(
        path,
        (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )


def _restore_transaction_files(root: Path, journal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for record in reversed(journal.get("files", [])):
        try:
            path = _safe_repo_path(root, str(record["path"]))
            if record.get("existed"):
                backup = _safe_repo_path(root, str(record["backup"]))
                content = backup.read_bytes()
                if record.get("pre_hash") != "sha256:" + sha256(content).hexdigest():
                    raise ValueError(f"backup_hash_mismatch:{record['path']}")
                _durable_write_bytes(path, content)
            elif path.is_file() or path.is_symlink():
                path.unlink()
        except (OSError, ValueError, KeyError) as error:
            errors.append(str(error))
    return errors


def _restore_lifecycle_move(root: Path, journal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        source = _safe_repo_path(root, str(journal["source"]))
        destination = _safe_repo_path(root, str(journal["destination"]))
        if source.exists() and destination.exists():
            raise ValueError("lifecycle_recovery_conflict:source_and_destination_exist")
        if destination.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            os.replace(destination, source)
        if not source.is_dir():
            raise ValueError("lifecycle_recovery_source_missing")
        backup = _safe_repo_path(root, str(journal["manifest_backup"]))
        content = backup.read_bytes()
        if journal.get("pre_manifest_hash") != "sha256:" + sha256(content).hexdigest():
            raise ValueError("lifecycle_manifest_backup_hash_mismatch")
        manifest_path = source / "work.json"
        if journal.get("manifest_existed"):
            _durable_write_bytes(manifest_path, content)
        elif manifest_path.exists():
            manifest_path.unlink()
    except (OSError, ValueError, KeyError) as error:
        errors.append(str(error))
    return errors


def recover_transactions(root: Path) -> dict[str, Any]:
    root = root.resolve()
    transactions = root / ".work" / "transactions"
    recovered: list[str] = []
    errors: list[str] = []
    if not transactions.is_dir():
        return {"status": "clean", "recovered": [], "errors": []}
    for journal_path in sorted(transactions.glob("*/journal.json")):
        try:
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"invalid_transaction_journal:{journal_path.parent.name}:{error}")
            continue
        if journal.get("status") != "applying":
            continue
        kind = journal.get("kind")
        if kind == "file_transaction":
            restore_errors = _restore_transaction_files(root, journal)
        elif kind == "lifecycle_move":
            restore_errors = _restore_lifecycle_move(root, journal)
        else:
            errors.append(f"unsupported_transaction_kind:{journal_path.parent.name}")
            continue
        if restore_errors:
            errors.extend(restore_errors)
            continue
        journal["status"] = "recovered"
        journal["recovered_at"] = datetime.now().astimezone().isoformat()
        _durable_write_json(journal_path, journal)
        recovered.append(journal_path.parent.name)
    return {
        "status": "recovery_failed" if errors else ("recovered" if recovered else "clean"),
        "recovered": recovered,
        "errors": errors,
    }


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
    root: Path,
    plan: dict[str, Any],
    *,
    approval_digest: str,
    fault_after: int | None = None,
    crash_after: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    recovery = recover_transactions(root)
    if recovery["status"] == "recovery_failed":
        return {"status": "precondition_failed", "errors": recovery["errors"]}
    expected = canonical_digest({key: value for key, value in plan.items() if key != "digest"})
    if approval_digest != plan.get("digest") or plan.get("digest") != expected:
        return {"status": "approval_required", "expected_digest": plan.get("digest")}
    if str(root) != plan.get("root"):
        return {"status": "precondition_failed", "errors": ["root_drift"]}
    operations = plan.get("operations", [])
    affected = sorted(set(relative for operation in operations for relative in _operation_paths(operation)))
    transaction_id = str(plan["digest"]).removeprefix("sha256:")[:16]
    transaction_root = root / ".work" / "transactions" / transaction_id
    transaction_root.mkdir(parents=True, exist_ok=True)
    journal_path = transaction_root / "journal.json"
    records: list[dict[str, Any]] = []
    try:
        for index, relative in enumerate(affected):
            path = _safe_repo_path(root, relative)
            existed = path.is_file()
            record: dict[str, Any] = {"path": relative, "existed": existed}
            if existed:
                content = path.read_bytes()
                backup = transaction_root / "backups" / f"{index:04d}.bin"
                _durable_write_bytes(backup, content)
                record.update({
                    "backup": backup.relative_to(root).as_posix(),
                    "pre_hash": "sha256:" + sha256(content).hexdigest(),
                })
            records.append(record)
    except (OSError, ValueError) as error:
        return {"status": "precondition_failed", "errors": [str(error)]}
    journal = {
        "schema_version": SCHEMA_VERSION,
        "kind": "file_transaction",
        "status": "applying",
        "plan_digest": plan["digest"],
        "completed_operations": 0,
        "files": records,
    }
    _durable_write_json(journal_path, journal)
    try:
        for number, operation in enumerate(operations, 1):
            action = operation.get("action")
            if action == "write":
                target = _safe_repo_path(root, operation["path"])
                _durable_write_bytes(target, str(operation["content"]).encode("utf-8"))
            elif action == "move":
                source = _safe_repo_path(root, operation["source"])
                target = _safe_repo_path(root, operation["target"])
                if not source.is_file() or target.exists():
                    raise ValueError(f"move_precondition_failed:{operation['source']}:{operation['target']}")
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(source, target)
            elif action == "replace":
                target = _safe_repo_path(root, operation["path"])
                text = target.read_text(encoding="utf-8")
                if operation["old"] not in text:
                    raise ValueError(f"replace_precondition_failed:{operation['path']}")
                _durable_write_bytes(target, text.replace(operation["old"], operation["new"]).encode("utf-8"))
            elif action == "remove":
                target = _safe_repo_path(root, operation["path"])
                if not target.is_file():
                    raise ValueError(f"remove_precondition_failed:{operation['path']}")
                target.unlink()
            else:
                raise ValueError(f"unsupported_operation:{action}")
            journal["completed_operations"] = number
            _durable_write_json(journal_path, journal)
            if crash_after == number:
                os._exit(91)
            if fault_after == number:
                raise RuntimeError(f"fault_injected_after:{number}")
        production_after = _hash_roots(root, list(plan.get("source_roots", [])))
        if production_after != plan.get("production_hashes_before", {}):
            raise RuntimeError("production_hash_drift")
        journal["status"] = "committed"
        journal["post_hashes"] = {
            relative: (
                "sha256:" + sha256(_safe_repo_path(root, relative).read_bytes()).hexdigest()
                if _safe_repo_path(root, relative).is_file()
                else None
            )
            for relative in affected
        }
        _durable_write_json(journal_path, journal)
        return {
            "status": "committed", "transaction_id": transaction_id,
            "production_hashes_before": plan.get("production_hashes_before", {}),
            "production_hashes_after": production_after,
        }
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        restore_errors = _restore_transaction_files(root, journal)
        journal["status"] = "rollback_failed" if restore_errors else "rolled_back"
        journal["error"] = str(error)
        journal["restore_errors"] = restore_errors
        _durable_write_json(journal_path, journal)
        return {
            "status": journal["status"], "transaction_id": transaction_id,
            "error": str(error), "restore_errors": restore_errors,
        }


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
    inherit_env = descriptor.get("inherit_env", True)
    if not isinstance(inherit_env, bool):
        return {"status": "invalid_descriptor", "errors": ["inherit_env_must_be_boolean"]}
    environment = dict(os.environ) if inherit_env else {}
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


def _list_html(values: list[Any], *, class_name: str = "review-list") -> str:
    def visible_text(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("criterion") or value.get("target") or value.get("id") or "")
        return str(value)

    return '<ul class="' + class_name + '">' + "".join(
        f"<li>{html.escape(visible_text(value))}</li>" for value in values
    ) + "</ul>"


def _behavior_label(behavior_type: str) -> str:
    return {
        "migration": "전환 설계", "tool": "도구 흐름", "api": "요청 처리 흐름",
        "ui": "사용자 경험 흐름", "bugfix": "문제 교정 흐름",
    }.get(behavior_type, "동작 흐름")


def _step_roles(behavior_type: str, steps: list[Any]) -> list[str]:
    count = len(steps)
    if count == 0:
        return []
    if behavior_type == "migration":
        roles = ["전환"] * count
        roles[0] = "전제 조건"
        rollback = any(token in str(steps[-1]).casefold() for token in ("rollback", "복구", "되돌"))
        roles[-1] = "복구" if rollback else "완료 상태"
        if count > 2:
            roles[-2] = "검증"
        return roles
    if behavior_type in {"tool", "api"}:
        roles = ["처리"] * count
        roles[0] = "입력"
        roles[-1] = "관찰 결과"
        if count > 3:
            roles[-2] = "검증"
        return roles
    if behavior_type == "ui":
        roles = ["상태 변화"] * count
        roles[0] = "사용자 행동"
        roles[-1] = "화면 결과"
        return roles
    if behavior_type == "bugfix":
        names = ["실패 증상", "원인", "교정 동작", "회귀 검증"]
        return [names[min(index, len(names) - 1)] for index in range(count)]
    return [f"단계 {index + 1}" for index in range(count)]


def _behavior_visual(behavior_type: str, steps: list[Any], *, actual: bool = False) -> str:
    roles = _step_roles(behavior_type, steps)
    nodes = "".join(
        '<li class="flow-step"><span class="stage-label">' + html.escape(role)
        + '</span><p>' + html.escape(str(step)) + "</p></li>"
        for role, step in zip(roles, steps)
    )
    qualifier = "실제 " if actual else ""
    return (
        '<figure class="behavior-visual" data-visual="' + html.escape(behavior_type)
        + '"><figcaption>' + qualifier + _behavior_label(behavior_type)
        + '</figcaption><ol class="behavior-map">' + nodes + "</ol></figure>"
    )


def _design_test_table(tests: list[Any]) -> str:
    rows: list[str] = []
    for index, test in enumerate(tests):
        if isinstance(test, dict):
            target = str(test.get("target", f"검증 항목 {index + 1}"))
            method = str(test.get("method", ""))
            expected = str(test.get("expected", ""))
        else:
            target = f"검증 항목 {index + 1}"
            method = str(test)
            expected = "계획한 동작이 확인된다"
        rows.append(
            '<tr><th scope="row">' + html.escape(target) + '</th><td>'
            + html.escape(method) + '</td><td>' + html.escape(expected) + "</td></tr>"
        )
    return (
        '<div class="table-wrap"><table class="test-table"><thead><tr><th>검증 대상</th>'
        '<th>수행할 테스트</th><th>통과 기준</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table></div>"
    )


def _risk_label(risk: str) -> str:
    return {
        "destructive": "파괴적 변경",
        "security_privacy": "보안·개인정보 변경",
        "secret_handling": "비밀정보 처리",
        "irreversible_migration": "비가역 마이그레이션",
        "external_cost": "외부 비용",
        "push": "원격 push",
        "publish": "외부 publish",
        "global_configuration": "전역 설정 변경",
    }.get(risk, risk)


def _design_context(item: dict[str, Any]) -> str:
    priority = {"core": "핵심", "optional": "선택"}.get(
        str(item.get("priority", "core")), str(item.get("priority", "core"))
    )
    dependencies = [str(value) for value in item.get("depends_on", [])]
    dependency_text = " · ".join(dependencies) + " 이후" if dependencies else "없음"
    details: list[str] = [
        '<p class="item-metadata"><span><strong>우선순위</strong> '
        + html.escape(priority) + '</span><span><strong>선행 Item</strong> '
        + html.escape(dependency_text) + "</span></p>"
    ]
    terms = item.get("terms", [])
    if terms:
        details.append(
            '<dl class="term-list">' + "".join(
                '<div><dt>' + html.escape(str(term["term"])) + '</dt><dd>'
                + html.escape(str(term["explanation"])) + "</dd></div>"
                for term in terms if isinstance(term, dict)
            ) + "</dl>"
        )
    non_goals = item.get("non_goals", [])
    if non_goals:
        details.append(
            '<p class="decision-boundary"><strong>제외 범위</strong> '
            + html.escape(" · ".join(str(value) for value in non_goals)) + "</p>"
        )
    risks = item.get("material_risks", [])
    if risks:
        details.append(
            '<p class="decision-boundary risk"><strong>명시 승인 필요</strong> '
            + html.escape(" · ".join(_risk_label(str(value)) for value in risks)) + "</p>"
        )
    return "".join(details)


def _check_label(kind: Any) -> str:
    labels = {
        "targeted": "관련 동작",
        "feature": "기능 동작",
        "forward": "대표 작업 흐름",
        "full": "저장소 전체",
        "distribution": "배포 일관성",
        "independent review": "독립 검토",
        "fault injection": "실패 복구",
    }
    value = str(kind or "검증")
    return labels.get(value.casefold(), value)


def _result_test_table(checks: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for check in checks:
        status = str(check.get("status", "unknown"))
        status_text = "✓ 통과" if status == "passed" else ("— 제외" if status == "not_required" else "! " + status)
        rows.append(
            '<tr><th scope="row">' + html.escape(_check_label(check.get("kind")))
            + '</th><td>' + html.escape(str(check.get("summary") or "관련 동작 검증"))
            + '</td><td><span class="test-status ' + html.escape(status) + '">' + html.escape(status_text)
            + "</span></td></tr>"
        )
    return (
        '<div class="table-wrap"><table class="test-table"><thead><tr><th>검증 대상</th>'
        '<th>수행한 테스트</th><th>확인 결과</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table></div>"
    )


def _review_template(name: str) -> str:
    candidates = (
        Path(__file__).resolve().parents[1] / "templates" / "review" / name,
        Path(__file__).resolve().parents[1] / "templates" / name,
        Path(__file__).resolve().parent / "templates" / "review" / name,
        Path(__file__).resolve().parent / "templates" / name,
    )
    for candidate in candidates:
        if candidate.is_file():
            content = candidate.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)
            prefix: list[str] = []
            if lines and lines[0].lstrip().casefold().startswith("<!doctype"):
                prefix.append(lines.pop(0))
            generated_markers = (
                "<!-- generated file.", "<!-- source:", "<!-- source-sha256:",
            )
            while lines and (
                not lines[0].strip()
                or lines[0].strip().casefold().startswith(generated_markers)
            ):
                lines.pop(0)
            return "".join(prefix + lines)
    raise FileNotFoundError(f"review_template_missing:{name}")


def render_design_review_v3(contract: dict[str, Any]) -> str:
    """Render the canonical Item projection; never embed contract source text."""
    errors = validate_contract_v3(contract)
    structural = [error for error in errors if "invalid_decision_state" not in error]
    if structural:
        raise ValueError("invalid_contract:" + ";".join(structural))
    cards: list[str] = []
    for item in contract["items"]:
        decision = item.get("decision", {}).get("state")
        behavior_type = str(item.get("behavior_type", "tool"))
        decision_alert = '<span class="status warning">! 결정 필요</span>' if decision == "unresolved" else ""
        cards.append(
            '<article class="item" data-item-id="' + html.escape(item["id"]) + '">'
            '<header class="item-heading"><span class="item-id">' + html.escape(item["id"])
            + '</span><h2>' + html.escape(item["title"]) + "</h2>" + decision_alert + "</header>"
            + '<section class="review-section purpose-section"><h3>핵심 목적</h3><div class="section-body"><p class="lead-copy">'
            + html.escape(item["what"]) + "</p>" + _design_context(item) + "</div></section>"
            + '<section class="review-section process-section"><h3>핵심 프로세스</h3><div class="section-body">'
            + _behavior_visual(behavior_type, item["steps"]) + "</div></section>"
            + '<section class="review-section test-section"><h3>핵심 테스트</h3><div class="section-body">'
            + _design_test_table(item["tests"]) + "</div></section>"
            + '<section class="review-section result-section"><h3>예상 결과</h3><div class="section-body">'
            + _list_html(item["done"], class_name="result-list") + "</div></section></article>"
        )
    summary = (
        '<header class="review-masthead"><div class="document-mark"><span>구현 계획</span><strong>DESIGN / '
        + html.escape(str(contract.get("work_id", ""))) + '</strong></div><h1>'
        + html.escape(contract.get("goal", "")) + '</h1><p class="standfirst">'
        + html.escape(contract.get("scope", ""))
        + (
            '<br><strong>제외 범위</strong> '
            + html.escape(" · ".join(str(value) for value in contract.get("non_goals", [])))
            if contract.get("non_goals") else ""
        )
        + "</p></header>"
    )
    return _review_template("design-item-review.html").replace("{{SUMMARY}}", summary).replace("{{ITEMS}}", "".join(cards)).rstrip() + "\n"


def _has_high_risk(contract: dict[str, Any]) -> bool:
    return any(item.get("material_risks") for item in contract.get("items", []))


def _authorization_record(
    contract: dict[str, Any], *, mode: str, actor: str, authorized_at: str
) -> dict[str, Any]:
    payload = _contract_payload(contract)
    review_html = render_design_review_v3(payload)
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "contract_digest": canonical_digest(payload),
        "review_digest": canonical_digest(review_html),
        "item_ids": [item["id"] for item in payload["items"]],
        "actor": actor,
        "authorized_at": authorized_at,
    }


def authorize_design(
    contract: dict[str, Any], *, intent: str = "default", actor: str,
    authorized_at: str,
) -> dict[str, Any]:
    """Bind a validated canonical Review to default authority, explicit approval, or veto."""
    errors = validate_contract_v3(contract)
    if errors:
        return {"status": "invalid_contract", "errors": errors}
    if any(item.get("decision", {}).get("state") != "resolved" for item in contract["items"]):
        return {"status": "unresolved_decisions"}
    if intent not in {"default", "veto", "explicit_approve"}:
        return {"status": "ambiguous_intent"}
    existing = contract.get("authorization")
    if (
        intent == "default"
        and isinstance(existing, dict)
        and existing.get("mode") == "vetoed"
        and existing.get("contract_digest") == canonical_digest(_contract_payload(contract))
    ):
        return {"status": "vetoed", "contract": deepcopy(contract)}
    mode = {"default": "default", "veto": "vetoed", "explicit_approve": "explicit"}[intent]
    if _has_high_risk(contract) and mode != "explicit":
        if mode == "vetoed":
            vetoed = deepcopy(_contract_payload(contract))
            vetoed["authorization"] = _authorization_record(
                vetoed, mode=mode, actor=actor, authorized_at=authorized_at
            )
            return {"status": "vetoed", "contract": vetoed}
        return {"status": "explicit_approval_required"}
    authorized = deepcopy(_contract_payload(contract))
    authorized["authorization"] = _authorization_record(
        authorized, mode=mode, actor=actor, authorized_at=authorized_at
    )
    return {
        "status": {
            "default": "default_authorized", "explicit": "explicit_authorized",
            "vetoed": "vetoed",
        }[mode],
        "contract": authorized,
    }


def approve_review(
    contract: dict[str, Any], review_html: str, *, utterance: str, actor: str, approved_at: str
) -> dict[str, Any]:
    """Compatibility entrypoint; external HTML is never an authorization input."""
    del review_html
    normalized = utterance.strip().casefold()
    veto = any(token in normalized for token in ("아니", "거부", "중단", "취소", "reject", "deny", "stop", "cancel"))
    outcome = authorize_design(
        contract, intent="veto" if veto else "default", actor=actor, authorized_at=approved_at
    )
    if outcome.get("status") == "default_authorized":
        outcome["status"] = "approved"
    return outcome


def execution_authorized(
    contract: dict[str, Any], review_html: str | None = None, *,
    project: dict[str, Any] | None = None, host_goal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del review_html, host_goal  # review is rendered server-side; Goal tracking is optional.
    errors = validate_contract_v3(contract)
    if errors:
        return {"authorized": False, "errors": ["invalid_contract", *errors]}
    authorization = contract.get("authorization")
    if not isinstance(authorization, dict):
        return {"authorized": False, "errors": ["authorization_required"]}
    allowed_fields = {
        "schema_version", "mode", "contract_digest", "review_digest", "item_ids",
        "actor", "authorized_at",
    }
    if set(authorization) != allowed_fields:
        return {"authorized": False, "errors": ["authorization_schema_invalid"]}
    payload = _contract_payload(contract)
    try:
        canonical_review = render_design_review_v3(payload)
    except ValueError:
        return {"authorized": False, "errors": ["canonical_review_invalid"]}
    expected = _authorization_record(
        payload, mode=str(authorization.get("mode")), actor=str(authorization.get("actor")),
        authorized_at=str(authorization.get("authorized_at")),
    )
    if authorization != expected:
        return {"authorized": False, "errors": ["authorization_bundle_drift"]}
    mode = authorization["mode"]
    if mode == "vetoed":
        return {"authorized": False, "errors": ["design_vetoed"]}
    if mode not in {"default", "explicit"}:
        return {"authorized": False, "errors": ["authorization_mode_invalid"]}
    if _has_high_risk(payload) and mode != "explicit":
        return {"authorized": False, "errors": ["explicit_approval_required"]}
    if project is not None:
        harness = project.get("harness", {})
        active = harness.get("active_cohort")
        active_version = 3 if active == "v3" else active
        support = {
            name: component.get("supports", [])
            for name, component in harness.get("components", {}).items()
            if isinstance(component, dict)
        }
        cohort_errors = validate_cohort(active_version, support)
        if cohort_errors:
            return {"authorized": False, "errors": cohort_errors}
    return {"authorized": True, "errors": [], "review_digest": canonical_digest(canonical_review)}


def convert_legacy_contract(legacy: dict[str, Any]) -> dict[str, Any]:
    status = legacy.get("status", "pending")
    if status in {"in_progress", "blocked", "crash_interrupted"}:
        return {"status": "cutover_blocked", "reason": f"legacy_work_{status}"}
    requirements = list(legacy.get("requirements", []))
    objective = str(legacy.get("objective", ""))
    unresolved = [field for field in ("behavior_type", "observable_tests", "completion_criteria") if not legacy.get(field)]
    test_values = list(legacy.get("observable_tests", requirements or ["Resolve observable tests"]))
    done_values = list(legacy.get("completion_criteria", requirements or ["Resolve completion criteria"]))
    item = {
        "id": "I-01", "title": objective or "Legacy work", "behavior_type": legacy.get("behavior_type", "migration"),
        "what": objective, "steps": requirements or [objective], "terms": [],
        "tests": [
            {
                "id": f"T-{index:02d}", "target": str(value),
                "method": str(value), "expected": str(value), "selector": "",
            }
            for index, value in enumerate(test_values, 1)
        ],
        "done": [
            {"id": f"D-{index:02d}", "criterion": str(value)}
            for index, value in enumerate(done_values, 1)
        ],
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
    amended.pop("approval", None)
    amended.pop("authorization", None)
    item[field] = value
    event = {
        "kind": "approved_amendment", "message_id": message_id, "item_id": item_id,
        "field": field, "actor": actor, "approved_at": approved_at,
        "old_contract_digest": old_digest,
    }
    amended.setdefault("amendments", []).append(event)
    event["new_contract_digest"] = canonical_digest(_contract_payload(amended))
    authorized = authorize_design(
        amended, intent="default", actor=actor, authorized_at=approved_at
    )
    if "contract" not in authorized:
        return {"status": "invalid_amendment", "errors": authorized.get("errors", [authorized["status"]])}
    rebound = authorized["contract"]
    review_html = render_design_review_v3(_contract_payload(rebound))
    return {"status": "applied", "contract": rebound, "event": event, "review_html": review_html}


def canonical_repo_identity(
    root: Path, relative: str, *, case_sensitive: bool | None = None
) -> tuple[str, str]:
    root = root.resolve()
    normalized_input = relative.replace("\\", "/")
    pure = PurePosixPath(normalized_input)
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise ValueError(f"path_escape:{relative}")
    probe = root
    for part in pure.parts:
        if part in {"", "."}:
            continue
        probe = probe / part
        if probe.exists() and _path_is_alias(probe):
            raise ValueError(f"path_alias:{relative}")
    path = _safe_repo_path(root, normalized_input)
    normalized = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
    if case_sensitive is None:
        case_sensitive = os.name != "nt"
    identity = normalized if case_sensitive else normalized.casefold()
    return normalized, identity


def _identities_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right.rstrip("/") + "/") or right.startswith(left.rstrip("/") + "/")


def _git_paths(root: Path, args: list[str]) -> set[str]:
    result = subprocess.run(["git", *args, "-z"], cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise ValueError("git_baseline_failed:" + result.stderr.decode(errors="replace").strip())
    return {
        item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for item in result.stdout.split(b"\0") if item
    }


def collect_git_baseline(root: Path) -> dict[str, Any]:
    root = root.resolve()
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False,
    )
    if revision.returncode:
        raise ValueError("git_base_revision_unavailable:" + revision.stderr.strip())
    staged = _git_paths(root, ["diff", "--cached", "--name-only"])
    unstaged = _git_paths(root, ["diff", "--name-only"])
    deleted = (
        _git_paths(root, ["diff", "--cached", "--diff-filter=D", "--name-only"])
        | _git_paths(root, ["diff", "--diff-filter=D", "--name-only"])
    )
    untracked = _git_paths(root, ["ls-files", "--others", "--exclude-standard"])
    paths = staged | unstaged | deleted | untracked
    entries: list[dict[str, Any]] = []
    for relative in sorted(paths):
        normalized, identity = canonical_repo_identity(root, relative)
        states = []
        if relative in staged:
            states.append("staged")
        if relative in unstaged:
            states.append("unstaged")
        if relative in deleted:
            states.append("deleted")
        if relative in untracked:
            states.append("untracked")
        path = _safe_repo_path(root, normalized)
        worktree_hash = None
        if path.is_file() and not _path_is_alias(path):
            worktree_hash = "sha256:" + sha256(path.read_bytes()).hexdigest()
        index = subprocess.run(
            ["git", "ls-files", "-s", "--", normalized], cwd=root,
            capture_output=True, text=True, check=False,
        )
        index_oid = None
        if index.returncode == 0 and index.stdout.strip():
            fields = index.stdout.split("\t", 1)[0].split()
            if len(fields) >= 2:
                index_oid = fields[1]
        entries.append({
            "path": normalized, "identity": identity, "states": states,
            "index_oid": index_oid, "worktree_hash": worktree_hash,
        })
    payload = {"base_revision": revision.stdout.strip(), "entries": entries}
    return {**payload, "digest": canonical_digest(payload)}


def commit_item(
    root: Path, item_id: str, paths: list[str], *, dirty_baseline: list[str] | dict[str, Any]
) -> dict[str, Any]:
    root = root.resolve()
    try:
        normalized_paths = [canonical_repo_identity(root, path)[0] for path in paths]
        item_identities = [canonical_repo_identity(root, path)[1] for path in normalized_paths]
        if isinstance(dirty_baseline, dict):
            baseline_entries = list(dirty_baseline.get("entries", []))
            baseline_identities = [str(entry.get("identity")) for entry in baseline_entries]
        else:
            baseline_entries = []
            baseline_identities = [canonical_repo_identity(root, path)[1] for path in dirty_baseline]
    except ValueError as error:
        return {"status": "invalid_path", "error": str(error)}
    overlap = sorted(
        path for path, identity in zip(normalized_paths, item_identities)
        if any(_identities_overlap(identity, baseline) for baseline in baseline_identities)
    )
    if overlap:
        return {"status": "dirty_baseline_conflict", "paths": overlap}
    if isinstance(dirty_baseline, dict):
        current = collect_git_baseline(root)
        baseline_by_id = {str(entry["identity"]): entry for entry in baseline_entries}
        current_by_id = {str(entry["identity"]): entry for entry in current["entries"]}
        drift = [
            entry["path"] for identity, entry in baseline_by_id.items()
            if current_by_id.get(identity) != entry
        ]
        unexpected = [
            entry["path"] for identity, entry in current_by_id.items()
            if identity not in baseline_by_id
            and not any(_identities_overlap(identity, item_identity) for item_identity in item_identities)
        ]
        if drift or unexpected:
            return {"status": "dirty_baseline_drift", "paths": sorted(set(drift + unexpected))}
    add = subprocess.run(["git", "add", "--", *normalized_paths], cwd=root, capture_output=True, text=True, check=False)
    if add.returncode:
        return {"status": "git_error", "error": add.stderr.strip()}
    committed = subprocess.run(
        ["git", "commit", "--only", "-m", f"feat(harness): complete {item_id}", "--", *normalized_paths], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if committed.returncode:
        return {"status": "git_error", "error": (committed.stderr or committed.stdout).strip()}
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()
    return {"status": "committed", "item_id": item_id, "commit": revision, "paths": sorted(normalized_paths)}


def start_work(
    root: Path, work_id: str, slug: str, contract: dict[str, Any], *,
    project: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Capture Git/base/baseline state and create one idempotent feature-work manifest."""
    root = root.resolve()
    try:
        work_id = validate_work_id(work_id)
    except ValueError as error:
        return {"status": "invalid_work", "errors": [str(error)]}
    if contract.get("work_id") != work_id:
        return {"status": "invalid_work", "errors": ["contract_work_id_mismatch"]}
    if project is None:
        project_path = root / ".harness" / "project.yaml"
        try:
            project = json.loads(project_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {"status": "authorization_failed", "errors": ["project_configuration_required"]}
    authorization = execution_authorized(contract, project=project)
    if not authorization["authorized"]:
        return {"status": "authorization_failed", "errors": authorization["errors"]}
    work_root = _safe_repo_path(root, f".work/goals/active/{work_id}")
    manifest_path = work_root / "work.json"
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("work_id") == work_id:
            return {"status": "already_started", "manifest": existing}
        return {"status": "conflict", "errors": ["work_identity_conflict"]}
    base_branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=False
    )
    base_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    )
    if base_branch.returncode or base_revision.returncode or not base_branch.stdout.strip():
        return {"status": "git_error", "errors": ["captured_base_unavailable"]}
    normalized_slug = re.sub(r"[^a-z0-9-]+", "-", slug.casefold()).strip("-")
    if not normalized_slug:
        return {"status": "invalid_slug"}
    feature_branch = f"wp-{work_id}-{normalized_slug}"
    baseline = collect_git_baseline(root)
    switched = subprocess.run(
        ["git", "switch", "-c", feature_branch], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if switched.returncode:
        return {"status": "git_error", "errors": [(switched.stderr or switched.stdout).strip()]}
    manifest = {
        "schema_version": SCHEMA_VERSION, "work_id": work_id, "state": "active",
        "created_at": datetime.now().astimezone().isoformat(),
        "source_commit": base_revision.stdout.strip(), "base_branch": base_branch.stdout.strip(),
        "feature_branch": feature_branch, "contract_version": SCHEMA_VERSION,
        "dirty_baseline": baseline,
        "integrity_digest": canonical_digest(_contract_payload(contract)),
        "owned_paths": [f".work/goals/active/{work_id}"],
    }
    try:
        work_root.mkdir(parents=True, exist_ok=False)
        _durable_write_json(manifest_path, manifest)
        _durable_write_json(work_root / "contract.json", contract)
    except OSError as error:
        subprocess.run(["git", "switch", base_branch.stdout.strip()], cwd=root, capture_output=True, check=False)
        subprocess.run(["git", "branch", "-D", feature_branch], cwd=root, capture_output=True, check=False)
        return {"status": "precondition_failed", "errors": [str(error)]}
    return {"status": "started", "manifest": manifest}


def create_worktree(root: Path, *, base: str, branch: str, path: Path) -> dict[str, Any]:
    root = root.resolve()
    destination = path.resolve()
    if destination == root or destination in root.parents or not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        return {"status": "invalid_target"}
    if destination.exists():
        return {"status": "conflict", "errors": ["worktree_destination_exists"]}
    created = subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(destination), base], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if created.returncode:
        return {"status": "git_error", "errors": [(created.stderr or created.stdout).strip()]}
    return {"status": "created", "branch": branch, "path": str(destination), "base": base}


def integrate_worktree(
    root: Path, *, base: str, branch: str, path: Path, project: dict[str, Any],
    approved_exact_path: str | None,
) -> dict[str, Any]:
    root = root.resolve()
    destination = path.resolve()
    if approved_exact_path is None or Path(approved_exact_path).resolve() != destination:
        return {"status": "approval_required", "target": str(destination)}
    if destination == root or destination in root.parents or not destination.is_dir():
        return {"status": "invalid_target", "target": str(destination)}
    current = subprocess.run(
        ["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()
    if current != base:
        return {"status": "precondition_failed", "errors": ["base_branch_not_checked_out"]}
    if base in project.get("git", {}).get("protected_branches", []):
        return {"status": "approval_required", "errors": ["protected_base"]}
    worktree_status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=destination, capture_output=True, text=True, check=False
    )
    if worktree_status.returncode or worktree_status.stdout.strip():
        return {"status": "precondition_failed", "errors": ["worktree_not_clean"]}
    merged = subprocess.run(
        ["git", "merge", "--no-ff", "--no-edit", branch], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if merged.returncode:
        subprocess.run(["git", "merge", "--abort"], cwd=root, capture_output=True, check=False)
        return {"status": "git_error", "errors": [(merged.stderr or merged.stdout).strip()]}
    removed = subprocess.run(
        ["git", "worktree", "remove", str(destination)], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if removed.returncode:
        return {"status": "cleanup_failed", "errors": [(removed.stderr or removed.stdout).strip()]}
    deleted_branch = subprocess.run(
        ["git", "branch", "-d", branch], cwd=root, capture_output=True, text=True, check=False
    )
    if deleted_branch.returncode:
        return {"status": "cleanup_failed", "errors": [(deleted_branch.stderr or deleted_branch.stdout).strip()]}
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()
    return {"status": "integrated", "branch": branch, "base": base, "commit": revision}


def select_impacted_checks(
    changed_paths: list[str], project: dict[str, Any]
) -> dict[str, Any]:
    impact_config = project.get("impact", {})
    rules = impact_config.get("rules", [])
    feature_selectors = impact_config.get("feature_selectors", {})
    full_triggers = set(impact_config.get("full_triggers", []))
    matched_rules: list[str] = []
    tests: list[str] = []
    features: list[str] = []
    trigger_ids: list[str] = []
    unresolved: list[str] = []
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
            for trigger in rule.get("triggers", []):
                if trigger not in trigger_ids:
                    trigger_ids.append(trigger)
    full_trigger_ids = [trigger for trigger in trigger_ids if trigger in full_triggers]
    feature_commands = [
        {"feature": feature, "argv": list(feature_selectors[feature])}
        for feature in features if feature in feature_selectors
    ]
    missing_feature_selectors = [feature for feature in features if feature not in feature_selectors]
    unresolved.extend(f"feature_selector:{feature}" for feature in missing_feature_selectors)
    return {
        "matched_rules": matched_rules, "tests": tests, "features": features,
        "feature_commands": feature_commands, "trigger_ids": trigger_ids,
        "full_trigger_ids": full_trigger_ids,
        "not_required_rule_ids": matched_rules if not full_trigger_ids and not unresolved else [],
        "full_required": bool(full_trigger_ids), "unresolved": unresolved,
    }


def evaluate_result(
    contract: dict[str, Any], result: dict[str, Any], impact: dict[str, Any]
) -> dict[str, Any]:
    result_items = result.get("items", [])
    result_ids = [item.get("id") for item in result_items if isinstance(item, dict)]
    result_by_id = {item.get("id"): item for item in result_items if isinstance(item, dict)}
    evaluated: list[dict[str, Any]] = []
    errors: list[str] = []
    if len(result_ids) != len(set(result_ids)):
        errors.append("duplicate_result_item")
    planned_item_ids = {item["id"] for item in contract.get("items", [])}
    if set(result_ids) - planned_item_ids:
        errors.append("additional_result_item")
    for planned in contract.get("items", []):
        actual = result_by_id.get(planned["id"])
        item_errors: list[str] = []
        if actual is None:
            item_errors.append("missing_result")
        else:
            checks = actual.get("checks", [])
            planned_checks = {test["id"]: test for test in planned.get("tests", []) if isinstance(test, dict)}
            actual_check_ids = [check.get("check_id") for check in checks if isinstance(check, dict)]
            actual_checks = {check.get("check_id"): check for check in checks if isinstance(check, dict)}
            checks_match = (
                len(actual_check_ids) == len(set(actual_check_ids))
                and set(actual_check_ids) == set(planned_checks)
            )
            if checks_match:
                for check_id, planned_check in planned_checks.items():
                    check = actual_checks[check_id]
                    if check.get("status") != "passed":
                        checks_match = False
                        break
            if not checks_match:
                item_errors.append("planned_check_evidence_mismatch")
            criteria = actual.get("criteria")
            planned_criteria = {
                criterion["id"]: criterion for criterion in planned.get("done", [])
                if isinstance(criterion, dict)
            }
            criteria_match = isinstance(criteria, list)
            if criteria_match:
                actual_criterion_ids = [
                    criterion.get("criterion_id") for criterion in criteria if isinstance(criterion, dict)
                ]
                actual_criteria = {
                    criterion.get("criterion_id"): criterion for criterion in criteria if isinstance(criterion, dict)
                }
                criteria_match = (
                    len(actual_criterion_ids) == len(set(actual_criterion_ids))
                    and set(actual_criterion_ids) == set(planned_criteria)
                )
                if criteria_match:
                    for criterion_id, planned_criterion in planned_criteria.items():
                        observed = actual_criteria[criterion_id]
                        if (
                            observed.get("status") not in {"passed", "satisfied"}
                            or observed.get("criterion") != planned_criterion.get("criterion")
                            or not observed.get("evidence")
                        ):
                            criteria_match = False
                            break
            if not criteria_match:
                item_errors.append("planned_done_evidence_mismatch")
            if actual.get("delta", {}).get("material") and actual.get("delta", {}).get("approval") != "approved":
                item_errors.append("material_delta_unapproved")
        evaluated.append({"id": planned["id"], "status": "complete" if not item_errors else "incomplete", "errors": item_errors})
        errors.extend(f"{planned['id']}:{error}" for error in item_errors)
    if impact.get("unresolved"):
        errors.append("unresolved_test_impact")
    full_status = result.get("full", {}).get("status", "unrun")
    if impact.get("full_required") and full_status != "passed":
        errors.append("full_required_but_unrun")
    if not impact.get("full_required") and full_status == "not_required":
        rule = result.get("full", {}).get("rule")
        if not rule or rule not in impact.get("not_required_rule_ids", []):
            errors.append("full_not_required_rule_invalid")
    return {
        "status": "complete" if not errors else "incomplete", "items": evaluated,
        "full": "required" if impact.get("full_required") else full_status,
        "errors": errors,
    }


def render_result_review_v3(
    contract: dict[str, Any], result: dict[str, Any], impact: dict[str, Any] | None = None
) -> str:
    if impact is None:
        rule = result.get("full", {}).get("rule")
        impact = {
            "full_required": result.get("full", {}).get("status") == "passed",
            "unresolved": [], "not_required_rule_ids": [rule] if rule else [],
        }
    evaluation = evaluate_result(contract, result, impact)
    evaluated_by_id = {item["id"]: item for item in evaluation["items"]}
    result_by_id = {item.get("id"): item for item in result.get("items", [])}
    cards: list[str] = []
    completed = 0
    for planned in contract.get("items", []):
        actual = result_by_id.get(planned["id"], {})
        checks = actual.get("checks", [])
        delta = actual.get("delta", {})
        material = bool(delta.get("material"))
        complete = evaluated_by_id.get(planned["id"], {}).get("status") == "complete"
        completed += int(complete)
        status = "✓ 완료" if complete else "! 미완료"
        delta_text = str(delta.get("summary") or ("계획대로 구현됨" if not material else "material delta"))
        outcome_values = list(actual.get("actual_outcomes", []))
        outcomes = _list_html(outcome_values, class_name="outcome-list") if outcome_values else ""
        behavior_type = str(planned.get("behavior_type", "tool"))
        material_notice = (
            '<div class="material-notice"><strong>! 승인 필요</strong><span>' + html.escape(delta_text) + "</span></div>"
            if material else ""
        )
        cards.append(
            '<article class="item" data-item-id="' + html.escape(planned["id"]) + '"><header class="item-heading"><span class="item-id">'
            + html.escape(planned["id"]) + '</span><h2>' + html.escape(planned["title"])
            + '</h2><span class="status">' + status + "</span></header>"
            + '<section class="review-section purpose-section"><h3>핵심 목적</h3><div class="section-body"><p class="lead-copy">'
            + html.escape(str(planned.get("what", ""))) + "</p></div></section>"
            + '<section class="review-section process-section"><h3>핵심 프로세스</h3><div class="section-body">'
            + _behavior_visual(behavior_type, list(actual.get("actual_steps", [])), actual=True) + "</div></section>"
            + '<section class="review-section test-section"><h3>핵심 테스트</h3><div class="section-body">'
            + _result_test_table(checks) + "</div></section>"
            + '<section class="review-section result-section"><h3>핵심 결과</h3><div class="section-body"><p class="lead-copy">'
            + html.escape(str(actual.get("actual", "결과 없음"))) + "</p>" + outcomes + material_notice + "</div></section></article>"
        )
    full = result.get("full", {})
    full_label = "Full 통과" if full.get("status") == "passed" else (
        "Full 제외" if full.get("status") == "not_required" else "Full 미실행"
    )
    summary = (
        '<header class="review-masthead result-masthead"><div class="document-mark"><span>구현 결과</span><strong>RESULT / '
        + html.escape(str(contract.get("work_id", ""))) + '</strong></div><h1>'
        + html.escape(contract.get("goal", "")) + '</h1><p class="standfirst">'
        + str(completed) + " / " + str(len(contract.get("items", []))) + " Item 완료 · "
        + html.escape(full_label) + "</p></header>"
    )
    return _review_template("result-item-review.html").replace("{{SUMMARY}}", summary).replace("{{ITEMS}}", "".join(cards)).rstrip() + "\n"


def _lifecycle_move(
    root: Path, source: Path, destination: Path, manifest: dict[str, Any], *,
    operation: str, fault_after: str | None = None, crash_after: str | None = None,
) -> dict[str, Any]:
    """Move one work directory with durable recovery across process interruption."""
    try:
        work_id = validate_work_id(manifest.get("work_id"))
        source.relative_to(root)
        destination.relative_to(root)
    except ValueError as error:
        return {"status": "invalid_work", "errors": [str(error)]}
    recovery = recover_transactions(root)
    if recovery["status"] == "recovery_failed":
        return {"status": "precondition_failed", "errors": recovery["errors"]}
    manifest_path = source / "work.json"
    manifest_existed = manifest_path.is_file()
    original_manifest = manifest_path.read_bytes() if manifest_existed else b""
    transactions = root / ".work" / "transactions"
    transaction_identity = canonical_digest({"operation": operation, "work_id": work_id})
    transaction_root = transactions / f"{operation}-{transaction_identity.removeprefix('sha256:')[:16]}"
    transaction_root.mkdir(parents=True, exist_ok=True)
    journal_path = transaction_root / "journal.json"
    backup_path = transaction_root / "work.json.preimage"
    _durable_write_bytes(backup_path, original_manifest)
    journal = {
        "schema_version": SCHEMA_VERSION, "kind": "lifecycle_move",
        "operation": operation, "status": "applying",
        "source": source.relative_to(root).as_posix(),
        "destination": destination.relative_to(root).as_posix(),
        "manifest_backup": backup_path.relative_to(root).as_posix(),
        "manifest_existed": manifest_existed,
        "pre_manifest_hash": "sha256:" + sha256(original_manifest).hexdigest(),
    }
    _durable_write_json(journal_path, journal)
    try:
        _durable_write_bytes(
            manifest_path,
            (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"),
        )
        journal["post_manifest_hash"] = "sha256:" + sha256(manifest_path.read_bytes()).hexdigest()
        _durable_write_json(journal_path, journal)
        if crash_after == "manifest":
            os._exit(92)
        if fault_after == "manifest":
            raise RuntimeError("injected_fault_after_manifest")
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)
        journal["moved"] = True
        _durable_write_json(journal_path, journal)
        if crash_after == "move":
            os._exit(92)
        if fault_after == "move":
            raise RuntimeError("injected_fault_after_move")
    except BaseException as error:
        restore_errors = _restore_lifecycle_move(root, journal)
        journal.update({
            "status": "rollback_failed" if restore_errors else "rolled_back",
            "error": type(error).__name__, "restore_errors": restore_errors,
        })
        _durable_write_json(journal_path, journal)
        return {"status": journal["status"], "journal": journal_path.relative_to(root).as_posix()}
    journal["status"] = "committed"
    _durable_write_json(journal_path, journal)
    return {"status": "committed", "journal": journal_path.relative_to(root).as_posix()}


def close_work(
    root: Path, work_id: str, *, completed_at: str, completed_days: int, trash_days: int,
    fault_after: str | None = None, crash_after: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    try:
        work_id = validate_work_id(work_id)
    except ValueError as error:
        return {"status": "invalid_work", "errors": [str(error)]}
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
        "owned_paths": [destination.relative_to(root).as_posix()],
    })
    transaction = _lifecycle_move(
        root, source, destination, manifest, operation="close", fault_after=fault_after,
        crash_after=crash_after,
    )
    if transaction["status"] != "committed":
        return transaction
    return {"status": "completed", "path": destination.relative_to(root).as_posix(), "manifest": manifest}


def audit_work_lifecycle(root: Path) -> dict[str, Any]:
    goals = root / ".work" / "goals"
    seen: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    for state in ("active", "completed", "trash", "legacy-unclassified"):
        state_root = goals / state
        if not state_root.is_dir():
            continue
        depth = 2 if state in {"completed", "trash"} else 1
        directories = sorted(
            path for path in state_root.rglob("*")
            if path.is_dir() and len(path.relative_to(state_root).parts) == depth
        )
        for directory in directories:
            if not (directory / "work.json").is_file():
                findings.append({"rule_id": "work.orphan", "location": directory.relative_to(root).as_posix()})
    for manifest_path in goals.rglob("work.json") if goals.is_dir() else []:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            findings.append({"rule_id": "work.invalid_manifest", "location": str(manifest_path)})
            continue
        work_id = str(manifest.get("work_id", ""))
        location = manifest_path.parent.relative_to(root).as_posix()
        try:
            validate_work_id(work_id)
        except ValueError:
            findings.append({"rule_id": "work.invalid_id", "location": location})
        if manifest_path.parent.name != work_id:
            findings.append({"rule_id": "work.identity_mismatch", "location": location})
        if work_id in seen:
            findings.append({"rule_id": "work.duplicate_id", "location": location})
        seen[work_id] = location
        expected_state = "legacy-unclassified" if "legacy-unclassified" in manifest_path.parts else next(
            (state for state in ("active", "completed", "trash") if state in manifest_path.parts), "unknown"
        )
        if manifest.get("state") != expected_state:
            findings.append({"rule_id": "work.invalid_state", "location": location})
    return {"findings": findings, "work_ids": seen}


def sweep_lifecycle(
    root: Path, *, now: str, fault_after: str | None = None, crash_after: str | None = None
) -> dict[str, Any]:
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
            source = manifest_path.parent
            try:
                work_id = validate_work_id(manifest.get("work_id"))
                source_relative = source.relative_to(completed_root)
                date.fromisoformat(source_relative.parts[0] + "-01")
            except (ValueError, IndexError):
                return {"status": "invalid_work", "errors": ["manifest_identity_or_state_invalid"]}
            if (
                manifest.get("state") != "completed"
                or len(source_relative.parts) != 2
                or source_relative.parts[1] != work_id
            ):
                return {"status": "invalid_work", "errors": ["manifest_identity_or_state_invalid"]}
            destination = _safe_repo_path(
                root, f".work/goals/trash/{moment:%Y-%m-%d}/{work_id}"
            )
            if destination.exists():
                continue
            manifest["state"] = "trash"
            if "owned_paths" in manifest:
                manifest["owned_paths"] = [destination.relative_to(root).as_posix()]
            transaction = _lifecycle_move(
                root, source, destination, manifest, operation="sweep", fault_after=fault_after,
                crash_after=crash_after,
            )
            if transaction["status"] != "committed":
                return transaction
            moved.append(work_id)
    return {"status": "ok", "moved_to_trash": moved, "audit": audit_work_lifecycle(root)}


def _legacy_completion_evidence(entry: Path) -> tuple[str, datetime | None]:
    values: list[datetime] = []
    invalid = False
    for name in ("work.json", "result.json"):
        path = entry / name
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            value = payload.get("completed_at")
            if value:
                values.append(datetime.fromisoformat(str(value)))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            invalid = True
    markdown = entry / "RESULT.md"
    if markdown.is_file():
        try:
            match = re.search(r"(?im)^completed_at\s*:\s*(\S+)\s*$", markdown.read_text(encoding="utf-8"))
            if match:
                values.append(datetime.fromisoformat(match.group(1)))
        except (OSError, UnicodeError, ValueError):
            invalid = True
    identities = {value.isoformat() for value in values}
    if invalid or len(identities) > 1:
        return "contradictory", None
    if not values:
        return "missing", None
    return "trustworthy", values[0]


def classify_legacy_work(
    root: Path, *, completed_days: int = 30, trash_days: int = 7,
    fault_after: str | None = None, crash_after: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    archive = root / ".work" / "archive"
    completed: list[str] = []
    unclassified: list[str] = []
    unresolved: list[str] = []
    if archive.is_dir():
        for entry in sorted(path for path in archive.iterdir() if path.is_dir()):
            work_id = entry.name
            evidence, completed_at = _legacy_completion_evidence(entry)
            if evidence == "contradictory":
                unresolved.append(work_id)
                continue
            if completed_at is None:
                destination = root / ".work" / "goals" / "legacy-unclassified" / work_id
                manifest = {
                    "schema_version": SCHEMA_VERSION, "work_id": work_id,
                    "state": "legacy-unclassified", "created_at": None,
                    "source_commit": None, "reason": "trustworthy_completion_date_missing",
                }
                outcome = unclassified
            else:
                destination = root / ".work" / "goals" / "completed" / f"{completed_at:%Y-%m}" / work_id
                retain_until = completed_at + timedelta(days=completed_days)
                delete_after = retain_until + timedelta(days=trash_days)
                manifest = {
                    "schema_version": SCHEMA_VERSION, "work_id": work_id, "state": "completed",
                    "created_at": None, "source_commit": None, "base_branch": "legacy",
                    "feature_branch": "legacy", "contract_version": SCHEMA_VERSION,
                    "integrity_digest": "legacy-classified", "completed_at": completed_at.isoformat(),
                    "retain_until": retain_until.isoformat(), "delete_after": delete_after.isoformat(),
                    "owned_paths": [destination.relative_to(root).as_posix()],
                }
                outcome = completed
            if destination.exists():
                continue
            transaction = _lifecycle_move(
                root, entry, destination, manifest, operation="classify-legacy",
                fault_after=fault_after, crash_after=crash_after,
            )
            if transaction["status"] != "committed":
                return {
                    **transaction, "completed": completed,
                    "unclassified": unclassified, "unresolved": unresolved,
                }
            outcome.append(work_id)
    return {
        "status": "classified", "completed": completed,
        "unclassified": unclassified, "unresolved": unresolved,
    }


def _path_is_alias(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(metadata, "st_file_attributes", 0) & 0x400)


def delete_trash(
    root: Path,
    relative_target: str,
    *,
    approved_exact_target: str | None,
    now: str | None = None,
    destructive_override: bool = False,
    approved_override_target: str | None = None,
) -> dict[str, Any]:
    normalized = relative_target.replace("\\", "/")
    expected_parts = (".work", "goals", "trash")
    parts = PurePosixPath(normalized).parts
    if approved_exact_target != normalized:
        return {"status": "approval_required", "target": normalized}
    if (
        len(parts) != 5
        or parts[:3] != expected_parts
        or any(part in {"", ".", ".."} for part in parts)
        or PurePosixPath(normalized).is_absolute()
    ):
        return {"status": "invalid_target", "target": normalized}
    try:
        date.fromisoformat(parts[3])
    except ValueError:
        return {"status": "invalid_target", "target": normalized}

    root = root.resolve()
    raw_target = root.joinpath(*parts)
    probe = root
    for part in parts:
        probe = probe / part
        if probe.exists() and _path_is_alias(probe):
            return {"status": "invalid_target", "target": normalized, "reason": "path_alias"}
    if not raw_target.is_dir():
        return {"status": "not_found", "target": normalized}
    trash_root = (root / ".work" / "goals" / "trash").resolve(strict=True)
    target = raw_target.resolve(strict=True)
    if target.parent.parent != trash_root or target.name != parts[4]:
        return {"status": "invalid_target", "target": normalized}

    manifest_path = target / "work.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"status": "invalid_work", "target": normalized, "reason": "manifest_missing_or_invalid"}
    if manifest.get("work_id") != parts[4] or manifest.get("state") != "trash":
        return {"status": "invalid_work", "target": normalized, "reason": "manifest_identity_or_state_invalid"}
    try:
        delete_after = datetime.fromisoformat(str(manifest["delete_after"]))
        moment = datetime.fromisoformat(str(now))
    except (KeyError, TypeError, ValueError):
        return {"status": "invalid_work", "target": normalized, "reason": "delete_after_or_now_invalid"}
    if moment < delete_after:
        override_approved = destructive_override and approved_override_target == normalized
        if not override_approved:
            return {"status": "retention_active", "target": normalized, "delete_after": delete_after.isoformat()}
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


def inspect_legacy_graph(root: Path) -> dict[str, Any]:
    root = root.resolve()
    work: list[dict[str, str]] = []
    blockers: list[str] = []
    goals = root / ".work" / "goals"
    if goals.is_dir():
        for manifest_path in sorted(goals.rglob("work.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                blockers.append(f"invalid_work_manifest:{manifest_path.relative_to(root).as_posix()}")
                continue
            work_id = str(manifest.get("work_id") or manifest_path.parent.name)
            state = str(manifest.get("state", "unknown"))
            work.append({"id": work_id, "state": state})
            if state == "pending":
                conversion = manifest_path.parent / "conversion.json"
                try:
                    evidence = json.loads(conversion.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    evidence = {}
                if not all(evidence.get(key) for key in ("source_digest", "target_digest", "lossless")):
                    blockers.append(f"pending_conversion_unproven:{work_id}")
            elif state not in {"completed", "trash", "legacy-unclassified", "deleted"}:
                blockers.append(f"legacy_work:{work_id}:{state}")
    archive = root / ".work" / "archive"
    if archive.is_dir():
        blockers.extend(f"unclassified_legacy_archive:{path.name}" for path in sorted(archive.iterdir()) if path.is_dir())
    runtime = root / ".work" / "runtime"
    if runtime.is_dir():
        blockers.extend(
            f"legacy_runtime:{path.relative_to(root).as_posix()}"
            for path in sorted(runtime.rglob("*")) if path.is_file()
        )
    transactions = root / ".work" / "transactions"
    if transactions.is_dir():
        for journal_path in sorted(transactions.glob("*/journal.json")):
            try:
                journal = json.loads(journal_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                blockers.append(f"invalid_transaction:{journal_path.parent.name}")
                continue
            if journal.get("status") in {"applying", "rollback_failed"}:
                blockers.append(f"incomplete_transaction:{journal_path.parent.name}")
    return {"work": work, "blockers": blockers}


def _manifest_file_hash(path: Path, hash_mode: str | None) -> str:
    if hash_mode == "bytes":
        content = path.read_bytes()
    elif path.suffix.casefold() in {".json", ".md", ".html", ".py", ".ps1", ".txt", ".yaml", ".yml"}:
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    else:
        content = path.read_bytes()
    return sha256(content).hexdigest()


def _cohort_manifest_files(resource_manifest: dict[str, Any]) -> dict[str, str]:
    files = resource_manifest.get("files")
    if not isinstance(files, dict):
        return {}
    return {
        str(relative): str(digest) for relative, digest in files.items()
        if str(relative).split("/", 1)[0] in HARNESS_INSTALL_SKILLS
    }


COHORT_MANIFEST_RESOURCE = "maintain-agent-harness/resources/public-resource-manifest.json"


def _installed_cohort_files(installed_root: Path) -> set[str]:
    observed: set[str] = set()
    for skill in HARNESS_INSTALL_SKILLS:
        skill_root = installed_root / skill
        if not skill_root.is_dir():
            continue
        for path in skill_root.rglob("*"):
            if path.is_file():
                observed.add(path.relative_to(installed_root).as_posix())
    return observed


def inspect_installed_cohort(installed_root: Path, resource_manifest: dict[str, Any]) -> dict[str, Any]:
    installed_root = installed_root.resolve()
    blockers: list[str] = []
    files = _cohort_manifest_files(resource_manifest)
    if resource_manifest.get("root") != "skills" or not files:
        return {"status": "invalid_manifest", "blockers": ["installed_manifest_invalid"], "components": {}}
    expected_files = set(files) | {COHORT_MANIFEST_RESOURCE}
    observed_files = _installed_cohort_files(installed_root)
    for relative in sorted(observed_files - expected_files):
        blockers.append(f"installed_resource_extra:{relative}")
    for relative in sorted(expected_files - observed_files):
        blockers.append(f"installed_resource_missing:{relative}")
    for relative, expected in sorted(files.items()):
        try:
            path = _safe_repo_path(installed_root, str(relative))
        except ValueError:
            blockers.append(f"installed_resource_invalid:{relative}")
            continue
        if not path.is_file():
            blockers.append(f"installed_resource_missing:{relative}")
            continue
        actual = _manifest_file_hash(path, resource_manifest.get("hash_mode"))
        if actual != expected:
            blockers.append(f"installed_resource_drift:{relative}")
    manifest_resource = installed_root / COHORT_MANIFEST_RESOURCE
    if manifest_resource.is_file():
        try:
            installed_manifest = json.loads(manifest_resource.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            blockers.append(f"installed_resource_drift:{COHORT_MANIFEST_RESOURCE}")
        else:
            if installed_manifest != resource_manifest:
                blockers.append(f"installed_resource_drift:{COHORT_MANIFEST_RESOURCE}")
    legacy_helpers = (
        "contract_engine.py", "goal_runtime.py", "close_goal.py",
        "maintain_harness.py", "render_completion_review.py",
    )
    for helper in legacy_helpers:
        for path in installed_root.glob(f"*/scripts/{helper}"):
            blockers.append(f"legacy_helper_present:{path.relative_to(installed_root).as_posix()}")
    component_skills = {
        "project": "setup-agent-harness", "design": "design-goal",
        "execute": "execute-codex-goal", "close": "close-goal",
        "maintain": "maintain-agent-harness", "diagnose": "diagnose",
    }
    components: dict[str, dict[str, list[int]]] = {}
    for component, skill in component_skills.items():
        skill_path = installed_root / skill / "SKILL.md"
        try:
            text = skill_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            text = ""
        supports = [3] if "Harness v3" in text else []
        components[component] = {"supports": supports}
        if not supports:
            blockers.append(f"installed_component_not_v3:{component}")
    return {"status": "complete" if not blockers else "invalid", "blockers": blockers, "components": components}


def install_harness_cohort(
    source_root: Path, install_root: Path, resource_manifest: dict[str, Any], *,
    approved_install_root: str | None, fault_after: int | None = None,
) -> dict[str, Any]:
    """Atomically replace only the Harness cohort after exact-root approval and staged verification."""
    source_root = source_root.resolve()
    install_root = install_root.resolve()
    if approved_install_root is None or Path(approved_install_root).resolve() != install_root:
        return {"status": "approval_required", "install_root": str(install_root)}
    files = _cohort_manifest_files(resource_manifest)
    if resource_manifest.get("root") != "skills" or not files:
        return {"status": "invalid_manifest"}
    for skill in HARNESS_INSTALL_SKILLS:
        if not (source_root / skill / "SKILL.md").is_file():
            return {"status": "invalid_source", "errors": [f"missing_skill:{skill}"]}
    install_root.parent.mkdir(parents=True, exist_ok=True)
    install_root.mkdir(parents=True, exist_ok=True)
    nonce = f"{os.getpid()}-{time.time_ns()}"
    staging = install_root.parent / f".harness-cohort-stage-{nonce}"
    backup = install_root.parent / f".harness-cohort-backup-{nonce}"
    changed: list[str] = []
    try:
        staging.mkdir()
        backup.mkdir()
        for relative in sorted(files):
            source = _safe_repo_path(source_root, relative)
            target = _safe_repo_path(staging, relative)
            if not source.is_file() or _path_is_alias(source):
                raise ValueError(f"invalid_source_resource:{relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        _durable_write_json(staging / COHORT_MANIFEST_RESOURCE, resource_manifest)
        staged = inspect_installed_cohort(staging, resource_manifest)
        if staged["status"] != "complete":
            raise RuntimeError("staging_invalid:" + ";".join(staged["blockers"]))
        for number, skill in enumerate(HARNESS_INSTALL_SKILLS, 1):
            target = install_root / skill
            saved = backup / skill
            if target.exists():
                if _path_is_alias(target):
                    raise ValueError(f"installed_skill_alias:{skill}")
                os.replace(target, saved)
            changed.append(skill)
            os.replace(staging / skill, target)
            if fault_after == number:
                raise RuntimeError(f"fault_injected_after:{number}")
        observed = inspect_installed_cohort(install_root, resource_manifest)
        if observed["status"] != "complete":
            raise RuntimeError("installed_cohort_verification_failed:" + ";".join(observed["blockers"]))
        tree: dict[str, str] = {
            relative: _manifest_file_hash(install_root / relative, resource_manifest.get("hash_mode"))
            for relative in sorted(files)
        }
        if tree != files or _installed_cohort_files(install_root) != set(files) | {COHORT_MANIFEST_RESOURCE}:
            raise RuntimeError("installed_tree_manifest_mismatch")
        tree[COHORT_MANIFEST_RESOURCE] = canonical_digest(resource_manifest)
        shutil.rmtree(backup)
        shutil.rmtree(staging)
        return {
            "status": "installed", "install_root": str(install_root),
            "skills": list(HARNESS_INSTALL_SKILLS), "tree_digest": canonical_digest(tree),
            "components": observed["components"],
        }
    except (OSError, ValueError, RuntimeError) as error:
        restore_errors: list[str] = []
        for skill in reversed(changed):
            target = install_root / skill
            saved = backup / skill
            try:
                if target.exists():
                    displaced = staging / skill
                    if displaced.exists():
                        shutil.rmtree(displaced)
                    os.replace(target, displaced)
                if saved.exists():
                    os.replace(saved, target)
            except OSError as restore_error:
                restore_errors.append(f"{skill}:{restore_error}")
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        return {
            "status": "rollback_failed" if restore_errors else "rolled_back",
            "error": str(error), "restore_errors": restore_errors,
        }


def maintain_harness(
    root: Path, project: dict[str, Any], *, installed_root: Path | None = None,
    resource_manifest: dict[str, Any] | None = None, today: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic, report-only audit with stable rule identities."""
    root = root.resolve()
    findings: list[dict[str, str]] = []
    checks: dict[str, Any] = {}

    def add(rule_id: str, location: str, message: str, severity: str = "medium") -> None:
        findings.append({
            "rule_id": rule_id, "location": location, "message": message,
            "severity": severity,
        })

    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    if agents.is_file() and claude.is_file() and agents.read_bytes() != claude.read_bytes():
        add("MAINT-INSTRUCTION-DRIFT", "AGENTS.md|CLAUDE.md", "instruction mirrors differ")
    checks["MAINT-INSTRUCTION-DRIFT"] = "checked"

    entrypoint = str(project.get("paths", {}).get("documentation_entrypoint", "docs/index.md"))
    try:
        index = _safe_repo_path(root, entrypoint)
    except ValueError:
        index = root / "__invalid_documentation_entrypoint__"
    if not index.is_file():
        add("MAINT-DOC-REACHABILITY", entrypoint, "documentation entrypoint is missing")
    else:
        try:
            content = index.read_text(encoding="utf-8")
            links = re.findall(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]+)?\)", content)
            for link in links:
                if re.match(r"^[a-z][a-z0-9+.-]*:", link, re.IGNORECASE):
                    continue
                target = (index.parent / link).resolve()
                try:
                    target.relative_to(root)
                except ValueError:
                    add("MAINT-DOC-REACHABILITY", link, "document link escapes repository")
                    continue
                if not target.exists():
                    add("MAINT-DOC-REACHABILITY", link, "document link target is missing")
        except (OSError, UnicodeError) as error:
            add("MAINT-DOC-REACHABILITY", entrypoint, f"documentation entrypoint unreadable:{type(error).__name__}")
    checks["MAINT-DOC-REACHABILITY"] = "checked"

    impact = project.get("impact", {})
    rules = impact.get("rules", [])
    selectors = impact.get("feature_selectors", {})
    mapped_prefixes = [
        str(prefix).replace("\\", "/")
        for rule in rules for prefix in rule.get("source_prefixes", [])
    ]
    for path in enumerate_repository_files(root):
        normalized = path.relative_to(root).as_posix()
        if normalized in {entrypoint, "AGENTS.md", "CLAUDE.md"} or normalized.startswith("docs/"):
            continue
        if not any(normalized.startswith(prefix) for prefix in mapped_prefixes):
            add("MAINT-IMPACT-UNMAPPED", normalized, "tracked surface has no impact rule", "high")
    for rule in rules:
        feature = rule.get("feature")
        if feature not in selectors:
            add("MAINT-IMPACT-SELECTOR", str(rule.get("id", "unnamed")), "feature selector is missing", "high")
    checks["MAINT-IMPACT-UNMAPPED"] = "checked"
    checks["MAINT-IMPACT-SELECTOR"] = "checked"

    current_day = date.fromisoformat(today) if today else date.today()
    for baseline in project.get("baseline", {}).get("findings", []):
        try:
            if date.fromisoformat(str(baseline["review_until"])) < current_day:
                add("MAINT-BASELINE-EXPIRED", str(baseline.get("location", "")), "baseline review date expired")
        except (KeyError, ValueError):
            add("MAINT-BASELINE-INVALID", str(baseline.get("location", "")), "baseline identity or date is invalid")
    checks["MAINT-BASELINE"] = "checked"

    lifecycle = audit_work_lifecycle(root)
    for finding in lifecycle["findings"]:
        add("MAINT-WORK-LIFECYCLE", finding["location"], finding["rule_id"])
    checks["MAINT-WORK-LIFECYCLE"] = lifecycle

    transactions = root / ".work" / "transactions"
    if transactions.is_dir():
        for journal_path in sorted(transactions.glob("*/journal.json")):
            try:
                journal = json.loads(journal_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                add("MAINT-TRANSACTION", journal_path.relative_to(root).as_posix(), "transaction journal is invalid", "high")
                continue
            if journal.get("status") in {"applying", "rollback_failed"}:
                add("MAINT-TRANSACTION", journal_path.relative_to(root).as_posix(), f"transaction is {journal.get('status')}", "high")
    checks["MAINT-TRANSACTION"] = "checked"

    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=False
    )
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
    )
    checks["MAINT-GIT-WORKTREE"] = {
        "branch": branch.stdout.strip() if branch.returncode == 0 else None,
        "worktrees": [line[9:] for line in worktrees.stdout.splitlines() if line.startswith("worktree ")]
        if worktrees.returncode == 0 else [],
    }

    if installed_root is not None and resource_manifest is not None:
        installed = inspect_installed_cohort(installed_root, resource_manifest)
        for blocker in installed["blockers"]:
            add("MAINT-INSTALLED-RESOURCE", str(installed_root), blocker, "high")
        checks["MAINT-INSTALLED-RESOURCE"] = installed

    findings.sort(key=lambda item: (item["rule_id"], item["location"], item["message"]))
    return {"status": "ok" if not findings else "findings", "findings": findings, "checks": checks}


def activate_v3(
    root: Path,
    project: dict[str, Any],
    *,
    installed_root: Path,
    resource_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Activate only from observed repository state and an intact installed cohort."""
    legacy = inspect_legacy_graph(root)
    installed = inspect_installed_cohort(installed_root, resource_manifest)
    blockers = [*legacy["blockers"], *installed["blockers"]]
    if blockers:
        return {"status": "cutover_blocked", "blockers": blockers, "legacy": legacy, "installed": installed}
    activated = deepcopy(project)
    if activated.get("schema_version") != SCHEMA_VERSION:
        return {"status": "cutover_blocked", "blockers": ["project_schema_not_v3"]}
    harness = activated.setdefault("harness", {})
    harness.update({"active_cohort": "v3", "contract_version": 3, "runtime_version": 3, "dormant_cohorts": []})
    harness["components"] = deepcopy(installed["components"])
    errors = validate_cohort(3, {name: value["supports"] for name, value in harness["components"].items()})
    if errors:
        return {"status": "cutover_blocked", "blockers": errors}
    activated.pop("migration", None)
    return {"status": "activated", "project": activated}


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_object:{path}")
    return value


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Core-First Agent Harness v3")
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("--root", type=Path, required=True)
    inventory.add_argument("--mapping", type=Path)
    design = sub.add_parser("render-design")
    design.add_argument("--contract", type=Path, required=True)
    design.add_argument("--output", type=Path, required=True)
    authorize = sub.add_parser("authorize")
    authorize.add_argument("--contract", type=Path, required=True)
    authorize.add_argument("--intent", choices=("default", "veto", "explicit_approve"), default="default")
    authorize.add_argument("--actor", required=True)
    authorize.add_argument("--at", required=True)
    result = sub.add_parser("render-result")
    result.add_argument("--contract", type=Path, required=True)
    result.add_argument("--result", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    impact = sub.add_parser("impacted")
    impact.add_argument("--project", type=Path, required=True)
    impact.add_argument("--changed", action="append", default=[])
    cleanup_plan = sub.add_parser("cleanup-plan")
    cleanup_plan.add_argument("--root", type=Path, required=True)
    cleanup_plan.add_argument("--request", type=Path, required=True)
    cleanup_apply = sub.add_parser("cleanup-apply")
    cleanup_apply.add_argument("--root", type=Path, required=True)
    cleanup_apply.add_argument("--plan", type=Path, required=True)
    cleanup_apply.add_argument("--approval-digest", required=True)
    recover = sub.add_parser("recover")
    recover.add_argument("--root", type=Path, required=True)
    baseline = sub.add_parser("baseline")
    baseline.add_argument("--root", type=Path, required=True)
    start = sub.add_parser("start")
    start.add_argument("--root", type=Path, required=True)
    start.add_argument("--work-id", required=True)
    start.add_argument("--slug", required=True)
    start.add_argument("--contract", type=Path, required=True)
    amend = sub.add_parser("amend")
    amend.add_argument("--contract", type=Path, required=True)
    amend.add_argument("--item-id", required=True)
    amend.add_argument("--field", required=True)
    amend.add_argument("--value", type=Path, required=True)
    amend.add_argument("--message-id", required=True)
    amend.add_argument("--actor", required=True)
    amend.add_argument("--at", required=True)
    amend.add_argument("--risk", required=True)
    complete = sub.add_parser("complete")
    complete.add_argument("--contract", type=Path, required=True)
    complete.add_argument("--result", type=Path, required=True)
    complete.add_argument("--impact", type=Path, required=True)
    commit = sub.add_parser("commit")
    commit.add_argument("--root", type=Path, required=True)
    commit.add_argument("--item-id", required=True)
    commit.add_argument("--path", action="append", required=True)
    commit.add_argument("--baseline", type=Path, required=True)
    worktree_create = sub.add_parser("worktree-create")
    worktree_create.add_argument("--root", type=Path, required=True)
    worktree_create.add_argument("--base", required=True)
    worktree_create.add_argument("--branch", required=True)
    worktree_create.add_argument("--path", type=Path, required=True)
    worktree_integrate = sub.add_parser("worktree-integrate")
    worktree_integrate.add_argument("--root", type=Path, required=True)
    worktree_integrate.add_argument("--base", required=True)
    worktree_integrate.add_argument("--branch", required=True)
    worktree_integrate.add_argument("--path", type=Path, required=True)
    worktree_integrate.add_argument("--project", type=Path, required=True)
    worktree_integrate.add_argument("--approved-exact-path", required=True)
    close = sub.add_parser("close")
    close.add_argument("--root", type=Path, required=True)
    close.add_argument("--work-id", required=True)
    close.add_argument("--contract", type=Path, required=True)
    close.add_argument("--result", type=Path, required=True)
    close.add_argument("--impact", type=Path, required=True)
    close.add_argument("--at", required=True)
    close.add_argument("--completed-days", type=int, required=True)
    close.add_argument("--trash-days", type=int, required=True)
    sweep = sub.add_parser("sweep")
    sweep.add_argument("--root", type=Path, required=True)
    sweep.add_argument("--at", required=True)
    delete = sub.add_parser("delete")
    delete.add_argument("--root", type=Path, required=True)
    delete.add_argument("--target", required=True)
    delete.add_argument("--approved-exact-target", required=True)
    delete.add_argument("--at", required=True)
    delete.add_argument("--destructive-override", action="store_true")
    delete.add_argument("--approved-override-target")
    audit = sub.add_parser("audit-work")
    audit.add_argument("--root", type=Path, required=True)
    maintain = sub.add_parser("maintain")
    maintain.add_argument("--root", type=Path, required=True)
    maintain.add_argument("--project", type=Path, required=True)
    maintain.add_argument("--installed-root", type=Path)
    maintain.add_argument("--manifest", type=Path)
    maintain.add_argument("--today")
    install = sub.add_parser("install-cohort")
    install.add_argument("--source-root", type=Path, required=True)
    install.add_argument("--install-root", type=Path, required=True)
    install.add_argument("--manifest", type=Path, required=True)
    install.add_argument("--approved-install-root", required=True)
    activation = sub.add_parser("activate")
    activation.add_argument("--root", type=Path, required=True)
    activation.add_argument("--project", type=Path, required=True)
    activation.add_argument("--installed-root", type=Path, required=True)
    activation.add_argument("--manifest", type=Path, required=True)
    return parser


def main() -> int:
    args = _cli_parser().parse_args()
    try:
        if args.command == "inventory":
            mapping = _json_object(args.mapping) if args.mapping else {}
            payload = static_inventory(args.root, mapping)
        elif args.command == "render-design":
            page = render_design_review_v3(_json_object(args.contract))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(page, encoding="utf-8", newline="\n")
            payload = {"status": "rendered", "output": str(args.output)}
        elif args.command == "authorize":
            payload = authorize_design(
                _json_object(args.contract), intent=args.intent, actor=args.actor,
                authorized_at=args.at,
            )
        elif args.command == "render-result":
            page = render_result_review_v3(_json_object(args.contract), _json_object(args.result))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(page, encoding="utf-8", newline="\n")
            payload = {"status": "rendered", "output": str(args.output)}
        elif args.command == "impacted":
            payload = select_impacted_checks(args.changed, _json_object(args.project))
        elif args.command == "cleanup-plan":
            request = _json_object(args.request)
            plan = build_cleanup_plan(
                args.root, mode=str(request["mode"]),
                source_roots=list(request.get("source_roots", [])),
                ownership=request.get("ownership"), operations=list(request.get("operations", [])),
            )
            payload = {"status": "planned", "plan": plan}
        elif args.command == "cleanup-apply":
            plan_payload = _json_object(args.plan)
            payload = apply_transaction(
                args.root, plan_payload.get("plan", plan_payload), approval_digest=args.approval_digest
            )
        elif args.command == "recover":
            payload = recover_transactions(args.root)
        elif args.command == "baseline":
            payload = {"status": "collected", "baseline": collect_git_baseline(args.root)}
        elif args.command == "start":
            payload = start_work(
                args.root, args.work_id, args.slug, _json_object(args.contract)
            )
        elif args.command == "amend":
            value = json.loads(args.value.read_text(encoding="utf-8"))
            payload = apply_amendment(
                _json_object(args.contract), item_id=args.item_id, field=args.field,
                value=value, message_id=args.message_id, actor=args.actor,
                approved_at=args.at, risk=args.risk,
            )
        elif args.command == "complete":
            payload = evaluate_result(
                _json_object(args.contract), _json_object(args.result), _json_object(args.impact)
            )
        elif args.command == "commit":
            baseline_payload = _json_object(args.baseline)
            payload = commit_item(
                args.root, args.item_id, args.path,
                dirty_baseline=baseline_payload.get("baseline", baseline_payload),
            )
        elif args.command == "worktree-create":
            payload = create_worktree(
                args.root, base=args.base, branch=args.branch, path=args.path
            )
        elif args.command == "worktree-integrate":
            payload = integrate_worktree(
                args.root, base=args.base, branch=args.branch, path=args.path,
                project=_json_object(args.project), approved_exact_path=args.approved_exact_path,
            )
        elif args.command == "close":
            contract = _json_object(args.contract)
            result = _json_object(args.result)
            impact = _json_object(args.impact)
            evaluation = evaluate_result(contract, result, impact)
            if evaluation["status"] != "complete":
                payload = evaluation
            else:
                active = _safe_repo_path(args.root.resolve(), f".work/goals/active/{args.work_id}")
                _durable_write_json(active / "result.json", result)
                _durable_write_bytes(
                    active / "review" / "result.html",
                    render_result_review_v3(contract, result, impact).encode("utf-8"),
                )
                payload = close_work(
                    args.root, args.work_id, completed_at=args.at,
                    completed_days=args.completed_days, trash_days=args.trash_days,
                )
        elif args.command == "sweep":
            payload = sweep_lifecycle(args.root, now=args.at)
        elif args.command == "delete":
            payload = delete_trash(
                args.root, args.target, approved_exact_target=args.approved_exact_target,
                now=args.at, destructive_override=args.destructive_override,
                approved_override_target=args.approved_override_target,
            )
        elif args.command == "audit-work":
            payload = audit_work_lifecycle(args.root)
            payload["status"] = "ok" if not payload["findings"] else "findings"
        elif args.command == "maintain":
            manifest = _json_object(args.manifest) if args.manifest else None
            if (args.installed_root is None) != (manifest is None):
                raise ValueError("installed_root_and_manifest_must_be_paired")
            payload = maintain_harness(
                args.root, _json_object(args.project), installed_root=args.installed_root,
                resource_manifest=manifest, today=args.today,
            )
        elif args.command == "install-cohort":
            payload = install_harness_cohort(
                args.source_root, args.install_root, _json_object(args.manifest),
                approved_install_root=args.approved_install_root,
            )
        else:
            payload = activate_v3(
                args.root, _json_object(args.project), installed_root=args.installed_root,
                resource_manifest=_json_object(args.manifest),
            )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("status") not in {
            "cutover_blocked", "invalid", "invalid_contract", "authorization_failed",
            "approval_required", "precondition_failed", "incomplete", "conflict",
            "git_error", "invalid_work", "invalid_target", "recovery_failed",
            "explicit_approval_required", "focused_approval_required", "vetoed",
            "unresolved_decisions", "ambiguous_intent", "invalid_amendment",
            "invalid_manifest", "invalid_source", "staging_invalid", "rolled_back",
            "rollback_failed",
            "cleanup_failed",
        } else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"status": "invalid", "errors": [str(error)]}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
