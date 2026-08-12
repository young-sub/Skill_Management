#!/usr/bin/env python3
"""Deterministic Core-First Agent Harness contracts and compatibility checks."""

from __future__ import annotations

import argparse
from copy import deepcopy
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any
import unicodedata


SCHEMA_VERSION = 3
WORK_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
LEGACY_COMPONENT_NAMES = ("project", "design", "execute", "close", "maintain", "diagnose")
HARNESS_INSTALL_SKILLS = (
    "setup-agent-harness", "design-goal", "execute-codex-goal", "close-goal",
    "maintain-agent-harness", "diagnose",
)
RETIRED_HARNESS_SKILLS = ("project-agent-bootstrap",)
PUBLIC_COMMANDS_BY_SKILL = {
    "setup-agent-harness": frozenset({
        "inventory", "cleanup-plan", "cleanup-apply", "recover",
        "install-cohort", "activate",
    }),
    "design-goal": frozenset({"design-create", "render-design", "authorize"}),
    "execute-codex-goal": frozenset({
        "baseline", "start", "impacted", "amend", "commit",
        "worktree-create", "worktree-integrate",
    }),
    "close-goal": frozenset({"render-result", "complete", "close", "sweep", "delete"}),
    "maintain-agent-harness": frozenset({"audit-work", "maintain", "recover"}),
}
ALL_CLI_COMMANDS = frozenset().union(*PUBLIC_COMMANDS_BY_SKILL.values())
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


def preview_project_config(legacy: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic current project configuration without mutating legacy input."""
    if legacy.get("version") != 2:
        raise ValueError(f"unsupported_project_version:{legacy.get('version', 'missing')}")
    source = deepcopy(legacy)
    project = source.get("project", {})
    work = source.get("work", {})
    return {
        "schema_version": SCHEMA_VERSION,
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
    }


def _legacy_harness_kind(value: Any, migration: Any) -> str | None:
    active = {
        "active_cohort": "v3", "contract_version": 3, "runtime_version": 3,
        "dormant_cohorts": [],
        "components": {name: {"supports": [3]} for name in LEGACY_COMPONENT_NAMES},
    }
    preview = {
        "active_cohort": "v2", "contract_version": 2, "runtime_version": 2,
        "dormant_cohorts": [3],
        "components": {name: {"supports": [2, 3]} for name in LEGACY_COMPONENT_NAMES},
    }
    if value == active and migration is None:
        return "active_matrix"
    if value == preview and isinstance(migration, dict):
        if (
            set(migration) == {"from_version", "mode", "source"}
            and migration.get("from_version") == 2
            and migration.get("mode") == "preview"
            and isinstance(migration.get("source"), dict)
        ):
            return "preview_matrix"
    return None


def validate_project_config(project: dict[str, Any]) -> list[str]:
    """Validate the public project boundary without relying on an optional package."""
    errors: list[str] = []

    def object_fields(
        value: Any, location: str, required: set[str], optional: set[str] | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            errors.append(f"project_config:expected_object:{location}")
            return None
        allowed = required | (optional or set())
        for field in sorted(required - set(value)):
            errors.append(f"project_config:missing:{location + '.' if location else ''}{field}")
        for field in sorted(set(value) - allowed):
            errors.append(f"project_config:unknown_field:{location + '.' if location else ''}{field}")
        return value

    def nonempty_string(value: Any, location: str) -> None:
        if not isinstance(value, str) or not value:
            errors.append(f"project_config:expected_nonempty_string:{location}")

    def string_list(value: Any, location: str, *, allowed: set[str] | None = None) -> None:
        if not isinstance(value, list):
            errors.append(f"project_config:expected_list:{location}")
            return
        if len(value) != len(set(item for item in value if isinstance(item, str))):
            errors.append(f"project_config:duplicate_value:{location}")
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item:
                errors.append(f"project_config:expected_nonempty_string:{location}.{index}")
            elif allowed is not None and item not in allowed:
                errors.append(f"project_config:invalid_value:{location}.{index}:{item}")

    required_top = {
        "schema_version", "project", "paths", "impact", "commands",
        "documents", "work", "git",
    }
    top = object_fields(project, "", required_top, {"baseline", "extensions"})
    if top is None:
        return sorted(set(errors))
    if top.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported_project_schema:{top.get('schema_version', 'missing')}")

    identity = object_fields(top.get("project"), "project", {"name", "classification"})
    if identity is not None:
        nonempty_string(identity.get("name"), "project.name")
        nonempty_string(identity.get("classification"), "project.classification")

    path_fields = {
        "source_roots", "test_roots", "fixture_roots", "generated_roots",
        "durable_document_roots", "human_guide_roots", "ephemeral_work_root",
        "documentation_entrypoint",
    }
    paths = object_fields(top.get("paths"), "paths", path_fields)
    if paths is not None:
        for field in sorted(path_fields - {"ephemeral_work_root", "documentation_entrypoint"}):
            string_list(paths.get(field), f"paths.{field}")
        nonempty_string(paths.get("ephemeral_work_root"), "paths.ephemeral_work_root")
        nonempty_string(paths.get("documentation_entrypoint"), "paths.documentation_entrypoint")

    impact = object_fields(top.get("impact"), "impact", {"rules", "feature_selectors", "full_triggers"})
    if impact is not None:
        rules = impact.get("rules")
        if not isinstance(rules, list):
            errors.append("project_config:expected_list:impact.rules")
        else:
            for index, candidate in enumerate(rules):
                location = f"impact.rules.{index}"
                rule = object_fields(candidate, location, {"id", "source_prefixes", "tests", "feature", "triggers"})
                if rule is None:
                    continue
                nonempty_string(rule.get("id"), f"{location}.id")
                string_list(rule.get("source_prefixes"), f"{location}.source_prefixes")
                string_list(rule.get("tests"), f"{location}.tests")
                nonempty_string(rule.get("feature"), f"{location}.feature")
                string_list(rule.get("triggers"), f"{location}.triggers")
        selectors = impact.get("feature_selectors")
        if not isinstance(selectors, dict):
            errors.append("project_config:expected_object:impact.feature_selectors")
        else:
            for key, argv in selectors.items():
                nonempty_string(key, "impact.feature_selectors.key")
                string_list(argv, f"impact.feature_selectors.{key}")
        string_list(impact.get("full_triggers"), "impact.full_triggers")

    command_names = {"targeted", "feature", "lint", "type", "build", "full", "live", "eval"}
    commands = object_fields(top.get("commands"), "commands", command_names)
    if commands is not None:
        required_command = {"id", "argv", "working_directory", "platform", "runtime", "capability"}
        optional_command = {"source_revision", "inherit_env", "env", "timeout_seconds"}
        for name in sorted(command_names):
            descriptor = object_fields(commands.get(name), f"commands.{name}", required_command, optional_command)
            if descriptor is None:
                continue
            for field in ("id", "working_directory", "platform", "runtime", "capability"):
                nonempty_string(descriptor.get(field), f"commands.{name}.{field}")
            argv = descriptor.get("argv")
            if not isinstance(argv, list):
                errors.append(f"project_config:expected_list:commands.{name}.argv")
            else:
                for index, argument in enumerate(argv):
                    if not isinstance(argument, str):
                        errors.append(f"project_config:expected_string:commands.{name}.argv.{index}")
            if "source_revision" in descriptor and not isinstance(descriptor["source_revision"], str):
                errors.append(f"project_config:expected_string:commands.{name}.source_revision")
            if "inherit_env" in descriptor and not isinstance(descriptor["inherit_env"], bool):
                errors.append(f"project_config:expected_boolean:commands.{name}.inherit_env")
            if "env" in descriptor:
                environment = descriptor["env"]
                if not isinstance(environment, dict) or any(
                    not isinstance(key, str) or not isinstance(value, str)
                    for key, value in environment.items()
                ):
                    errors.append(f"project_config:expected_string_map:commands.{name}.env")
            if "timeout_seconds" in descriptor:
                timeout = descriptor["timeout_seconds"]
                if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
                    errors.append(f"project_config:expected_positive_number:commands.{name}.timeout_seconds")

    documents = object_fields(top.get("documents"), "documents", {"boundaries"})
    if documents is not None:
        boundaries = documents.get("boundaries")
        if not isinstance(boundaries, list):
            errors.append("project_config:expected_list:documents.boundaries")
        else:
            for index, candidate in enumerate(boundaries):
                location = f"documents.boundaries.{index}"
                boundary = object_fields(candidate, location, {"paths", "documents"})
                if boundary is not None:
                    string_list(boundary.get("paths"), f"{location}.paths")
                    string_list(boundary.get("documents"), f"{location}.documents")

    work = object_fields(top.get("work"), "work", {"retention", "states"}, {"legacy_state"})
    if work is not None:
        retention = object_fields(work.get("retention"), "work.retention", {"completed_days", "trash_days"})
        if retention is not None:
            for field in ("completed_days", "trash_days"):
                value = retention.get(field)
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    errors.append(f"project_config:expected_nonnegative_integer:work.retention.{field}")
        string_list(
            work.get("states"), "work.states",
            allowed={"active", "completed", "trash", "deleted"},
        )
        if "legacy_state" in work and work["legacy_state"] != "legacy-unclassified":
            errors.append("project_config:invalid_value:work.legacy_state")

    git = object_fields(
        top.get("git"), "git",
        {"capture_current_base", "protected_branches", "branch_pattern", "commit_per_item", "worktrees_for_independent_items"},
    )
    if git is not None:
        for field in ("capture_current_base", "commit_per_item", "worktrees_for_independent_items"):
            if not isinstance(git.get(field), bool):
                errors.append(f"project_config:expected_boolean:git.{field}")
        string_list(git.get("protected_branches"), "git.protected_branches")
        nonempty_string(git.get("branch_pattern"), "git.branch_pattern")

    if "baseline" in top:
        baseline = object_fields(top["baseline"], "baseline", {"findings"})
        if baseline is not None:
            findings = baseline.get("findings")
            if not isinstance(findings, list):
                errors.append("project_config:expected_list:baseline.findings")
            else:
                for index, candidate in enumerate(findings):
                    location = f"baseline.findings.{index}"
                    finding = object_fields(
                        candidate, location,
                        {"rule_id", "location", "severity", "fingerprint", "review_until"},
                    )
                    if finding is None:
                        continue
                    for field in ("rule_id", "location", "fingerprint", "review_until"):
                        if not isinstance(finding.get(field), str):
                            errors.append(f"project_config:expected_string:{location}.{field}")
                    if finding.get("severity") not in {"low", "medium", "high"}:
                        errors.append(f"project_config:invalid_value:{location}.severity")
    if "extensions" in top and not isinstance(top["extensions"], dict):
        errors.append("project_config:expected_object:extensions")
    return sorted(set(errors))


def normalize_project_config(project: dict[str, Any]) -> dict[str, Any]:
    """Normalize known legacy declarations in memory; never mutate or persist input."""
    if not isinstance(project, dict):
        return {"status": "invalid", "project": {}, "errors": ["project_expected_object"]}
    source = deepcopy(project)
    if source.get("schema_version") != SCHEMA_VERSION:
        return {
            "status": "invalid", "project": source,
            "errors": [f"unsupported_project_schema:{source.get('schema_version', 'missing')}"],
        }
    if "harness" not in source:
        if "migration" in source:
            return {
                "status": "invalid", "project": source,
                "errors": ["orphan_legacy_migration_configuration"],
            }
        errors = validate_project_config(source)
        return {
            "status": "invalid" if errors else "current",
            "project": source, "errors": errors,
        }
    kind = _legacy_harness_kind(source.get("harness"), source.get("migration"))
    if kind is None:
        return {
            "status": "invalid", "project": source,
            "errors": ["unknown_legacy_harness_configuration"],
        }
    source.pop("harness", None)
    source.pop("migration", None)
    errors = validate_project_config(source)
    if errors:
        return {"status": "invalid", "project": source, "errors": errors}
    return {
        "status": "migration_required", "project": source, "errors": [],
        "source_kind": kind,
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


RESERVED_INVENTORY_ROOTS = {
    ".git", ".work", ".worktree", ".scratch", ".venv", "venv", "__pycache__",
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
    root = root.resolve()
    try:
        relative, _ = canonical_repo_identity(root, ".harness/project.yaml")
    except ValueError as error:
        raise ValueError("project_source_invalid:.harness/project.yaml") from error
    target = root.joinpath(*PurePosixPath(relative).parts)
    if target.exists() or target.is_symlink():
        if _path_is_alias(target) or not target.is_file():
            raise ValueError("project_source_invalid:.harness/project.yaml")
        source_bytes = target.read_bytes()
        try:
            observed = json.loads(source_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("project_source_invalid:.harness/project.yaml") from error
        if observed != legacy:
            raise ValueError("project_source_drift:.harness/project.yaml")
        expected_hash = "sha256:" + sha256(source_bytes).hexdigest()
    else:
        expected_hash = None
    if legacy.get("version") == 2:
        normalized = preview_project_config(legacy)
        source_kind = "legacy_v2"
    else:
        outcome = normalize_project_config(legacy)
        if outcome["status"] != "migration_required":
            errors = ";".join(outcome.get("errors", [])) or "migration_not_required"
            raise ValueError(f"project_migration_invalid:{errors}")
        normalized = outcome["project"]
        source_kind = str(outcome["source_kind"])
    content = json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return _plan_with_digest({
        "schema_version": SCHEMA_VERSION,
        "mode": "project-migration",
        "root": str(root),
        "source_kind": source_kind,
        "preconditions": [{
            "path": ".harness/project.yaml", "expected_hash": expected_hash,
        }],
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
    nonce = f"{os.getpid()}-{time.time_ns()}-{secrets.token_hex(8)}"
    temporary = path.with_name(f".{path.name}.{nonce}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    except OSError:
        try:
            if temporary.is_file() or temporary.is_symlink():
                temporary.unlink()
        except OSError:
            pass
        raise


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
        for record in reversed(journal.get("source_file_backups", [])):
            relative, _ = canonical_repo_identity(source, str(record["path"]))
            target = source.joinpath(*PurePosixPath(relative).parts)
            if record.get("existed"):
                file_backup = _safe_repo_path(root, str(record["backup"]))
                file_content = file_backup.read_bytes()
                if record.get("pre_hash") != "sha256:" + sha256(file_content).hexdigest():
                    raise ValueError(f"lifecycle_file_backup_hash_mismatch:{relative}")
                _durable_write_bytes(target, file_content)
            elif target.is_file():
                target.unlink()
            elif target.exists() or target.is_symlink():
                raise ValueError(f"lifecycle_file_restore_conflict:{relative}")
    except (OSError, ValueError, KeyError) as error:
        errors.append(str(error))
    return errors


def _process_is_alive(pid: Any) -> bool:
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        try:
            import ctypes

            process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not process:
                error = ctypes.windll.kernel32.GetLastError()
                return error not in {87, 1168}
            try:
                exit_code = ctypes.c_ulong()
                if not ctypes.windll.kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code)):
                    return True
                return exit_code.value == 259
            finally:
                ctypes.windll.kernel32.CloseHandle(process)
        except (AttributeError, OSError):
            return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _acquire_operation_lock(
    root: Path, name: str,
) -> tuple[Path | None, bytes | None, str | None]:
    root = root.resolve()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        return None, None, f"operation_lock_invalid:{name}"
    try:
        relative, _ = canonical_repo_identity(root, ".work/locks")
    except ValueError:
        return None, None, f"operation_lock_invalid:{name}"
    lock_root = root.joinpath(*PurePosixPath(relative).parts)
    try:
        lock_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None, None, f"operation_lock_invalid:{name}"
    lock_path = lock_root / f"{name}.lock"
    token = secrets.token_hex(16)
    payload = (
        json.dumps({
            "owner_pid": os.getpid(), "token": token,
            "created_at": datetime.now().astimezone().isoformat(),
        }, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary = lock_root / f".{name}.{token}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(2):
            try:
                os.link(temporary, lock_path)
                return lock_path, payload, None
            except FileExistsError:
                if attempt:
                    return None, None, f"operation_lock_busy:{name}"
                try:
                    observed = json.loads(lock_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    return None, None, f"operation_lock_invalid:{name}"
                if (
                    not isinstance(observed, dict)
                    or set(observed) != {"created_at", "owner_pid", "token"}
                    or isinstance(observed["owner_pid"], bool)
                    or not isinstance(observed["owner_pid"], int)
                    or observed["owner_pid"] <= 0
                    or not isinstance(observed["created_at"], str)
                    or not observed["created_at"]
                    or not isinstance(observed["token"], str)
                    or re.fullmatch(r"[0-9a-f]{32}", observed["token"]) is None
                ):
                    return None, None, f"operation_lock_invalid:{name}"
                if _process_is_alive(observed.get("owner_pid")):
                    return None, None, f"operation_lock_busy:{name}"
                quarantine = lock_root / f".{name}.{token}.stale"
                try:
                    os.rename(lock_path, quarantine)
                    quarantine.unlink()
                except OSError:
                    return None, None, f"operation_lock_busy:{name}"
            except OSError:
                return None, None, f"operation_lock_invalid:{name}"
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _release_operation_lock(path: Path | None, payload: bytes | None) -> list[str]:
    if path is None or payload is None:
        return []
    try:
        if path.read_bytes() != payload:
            return [f"operation_lock_ownership_lost:{path.stem}"]
        path.unlink()
    except OSError as error:
        return [f"operation_lock_release_failed:{path.stem}:{error}"]
    return []


def _transaction_inventory(
    root: Path,
) -> tuple[list[tuple[str, Path, dict[str, Any]]], list[str]]:
    transactions = root / ".work" / "transactions"
    if transactions.is_symlink() or _path_is_alias(transactions):
        return [], ["transaction_root_alias"]
    if not transactions.exists():
        return [], []
    if not transactions.is_dir():
        return [], ["transaction_root_not_directory"]
    records: list[tuple[str, Path, dict[str, Any]]] = []
    errors: list[str] = []
    for transaction_root in sorted(transactions.iterdir()):
        name = transaction_root.name
        if _path_is_alias(transaction_root):
            errors.append(f"transaction_alias:{name}")
            continue
        if not transaction_root.is_dir():
            errors.append(f"transaction_artifact_unexpected:{name}")
            continue
        journal_path = transaction_root / "journal.json"
        if not journal_path.is_file() or _path_is_alias(journal_path):
            errors.append(f"transaction_journal_missing:{name}")
            continue
        try:
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append(f"transaction_journal_corrupt:{name}")
            continue
        if not isinstance(journal, dict):
            errors.append(f"transaction_journal_corrupt:{name}")
            continue
        records.append((name, journal_path, journal))
    return records, sorted(set(errors))


def _transaction_blockers(root: Path) -> list[str]:
    records, errors = _transaction_inventory(root)
    for name, _journal_path, journal in records:
        status = journal.get("status")
        if status in {"applying", "rollback_failed"}:
            errors.append(f"incomplete_transaction:{name}:{status}")
        elif status not in {"committed", "rolled_back", "recovered"}:
            errors.append(f"transaction_status_invalid:{name}:{status}")
    return sorted(set(errors))


def _recover_transactions_locked(root: Path) -> dict[str, Any]:
    root = root.resolve()
    recovered: list[str] = []
    records, errors = _transaction_inventory(root)
    for name, journal_path, journal in records:
        status = journal.get("status")
        if status == "rollback_failed":
            errors.append(f"incomplete_transaction:{name}:rollback_failed")
            continue
        if status not in {"applying", "committed", "rolled_back", "recovered"}:
            errors.append(f"transaction_status_invalid:{name}:{status}")
            continue
        if status != "applying":
            continue
        if _process_is_alive(journal.get("owner_pid")):
            errors.append(f"transaction_in_progress:{name}")
            continue
        kind = journal.get("kind")
        if kind == "file_transaction":
            restore_errors = _restore_transaction_files(root, journal)
        elif kind == "lifecycle_move":
            restore_errors = _restore_lifecycle_move(root, journal)
        else:
            errors.append(f"unsupported_transaction_kind:{name}")
            continue
        if restore_errors:
            errors.extend(restore_errors)
            continue
        journal["status"] = "recovered"
        journal["recovered_at"] = datetime.now().astimezone().isoformat()
        _durable_write_json(journal_path, journal)
        recovered.append(name)
    return {
        "status": "recovery_failed" if errors else ("recovered" if recovered else "clean"),
        "recovered": recovered,
        "errors": errors,
    }


def recover_transactions(root: Path) -> dict[str, Any]:
    root = root.resolve()
    lock_path, lock_payload, lock_error = _acquire_operation_lock(root, "transaction")
    if lock_error:
        return {"status": "recovery_failed", "recovered": [], "errors": [lock_error]}
    try:
        return _recover_transactions_locked(root)
    finally:
        _release_operation_lock(lock_path, lock_payload)


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


def _apply_transaction_locked(
    root: Path,
    plan: dict[str, Any],
    *,
    approval_digest: str,
    fault_after: int | None = None,
    crash_after: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    recovery = _recover_transactions_locked(root)
    if recovery["status"] == "recovery_failed":
        return {"status": "precondition_failed", "errors": recovery["errors"]}
    expected = canonical_digest({key: value for key, value in plan.items() if key != "digest"})
    if approval_digest != plan.get("digest") or plan.get("digest") != expected:
        return {"status": "approval_required", "expected_digest": plan.get("digest")}
    if str(root) != plan.get("root"):
        return {"status": "precondition_failed", "errors": ["root_drift"]}
    precondition_errors: list[str] = []
    for precondition in plan.get("preconditions", []):
        relative = str(precondition.get("path", ""))
        try:
            normalized, _ = canonical_repo_identity(root, relative)
            path = root.joinpath(*PurePosixPath(normalized).parts)
            expected_hash = precondition.get("expected_hash")
            if expected_hash is None:
                if path.exists() or path.is_symlink():
                    precondition_errors.append(f"precondition_presence_drift:{relative}")
            elif not path.is_file():
                precondition_errors.append(f"precondition_missing:{relative}")
            else:
                actual_hash = "sha256:" + sha256(path.read_bytes()).hexdigest()
                if actual_hash != expected_hash:
                    precondition_errors.append(f"precondition_hash_drift:{relative}")
        except (OSError, ValueError) as error:
            if str(error).startswith("path_alias:"):
                precondition_errors.append(f"precondition_alias:{relative}")
            else:
                precondition_errors.append(f"precondition_invalid:{relative}:{error}")
    if precondition_errors:
        return {"status": "precondition_failed", "errors": precondition_errors}
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
        "owner_pid": os.getpid(),
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


def apply_transaction(
    root: Path,
    plan: dict[str, Any],
    *,
    approval_digest: str,
    fault_after: int | None = None,
    crash_after: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    lock_path, lock_payload, lock_error = _acquire_operation_lock(root, "transaction")
    if lock_error:
        return {"status": "precondition_failed", "errors": [lock_error]}
    try:
        return _apply_transaction_locked(
            root, plan, approval_digest=approval_digest,
            fault_after=fault_after, crash_after=crash_after,
        )
    finally:
        _release_operation_lock(lock_path, lock_payload)


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
    contract: dict[str, Any], *, mode: str, actor: str, authorized_at: str,
    review_digest: str | None = None,
) -> dict[str, Any]:
    payload = _contract_payload(contract)
    if review_digest is None:
        review_digest = canonical_digest(render_design_review_v3(payload))
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "contract_digest": canonical_digest(payload),
        "review_digest": review_digest,
        "item_ids": [item["id"] for item in payload["items"]],
        "actor": actor,
        "authorized_at": authorized_at,
    }


def _generated_work_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"W-{timestamp}-{secrets.token_hex(8)}"


def design_create(
    root: Path,
    contract: dict[str, Any],
    *,
    slug: str,
    work_id: str | None,
    intent: str,
    actor: str,
    authorized_at: str,
) -> dict[str, Any]:
    """Reserve one work namespace and write its authorized Design projection."""
    root = root.resolve()
    if not root.is_dir():
        return {"status": "invalid_root"}
    normalized_slug = re.sub(r"[^a-z0-9-]+", "-", slug.casefold()).strip("-")
    if not normalized_slug:
        return {"status": "invalid_slug"}
    explicit = work_id is not None
    if explicit:
        try:
            work_id = validate_work_id(work_id)
        except ValueError as error:
            return {"status": "invalid_work", "errors": [str(error)]}
        supplied_work_id = contract.get("work_id")
        if supplied_work_id not in {None, "", work_id}:
            return {"status": "invalid_work", "errors": ["contract_work_id_mismatch"]}
    try:
        active_relative, _ = canonical_repo_identity(root, ".work/goals/active")
        active_root = root.joinpath(*PurePosixPath(active_relative).parts)
    except ValueError as error:
        return {"status": "conflict", "errors": [str(error)]}
    if active_root.is_symlink() or _path_is_alias(active_root):
        return {"status": "conflict", "errors": ["active_work_root_alias"]}

    attempts = 1 if explicit else 16
    for _attempt in range(attempts):
        candidate = work_id if explicit else _generated_work_id()
        assert candidate is not None
        candidate_contract = deepcopy(contract)
        candidate_contract["work_id"] = candidate
        authorization = authorize_design(
            candidate_contract, intent=intent, actor=actor,
            authorized_at=authorized_at,
        )
        if authorization.get("status") not in {"default_authorized", "explicit_authorized"}:
            return authorization
        authorized_contract = authorization["contract"]
        try:
            active_root.mkdir(parents=True, exist_ok=True)
            work_root = active_root / candidate
            work_root.mkdir(exist_ok=False)
        except FileExistsError:
            if explicit:
                return {
                    "status": "conflict", "work_id": candidate,
                    "errors": ["work_identity_conflict"],
                }
            continue
        except OSError as error:
            return {"status": "write_failed", "work_id": candidate, "errors": [str(error)]}
        try:
            _durable_write_json(work_root / "contract.json", authorized_contract)
            _durable_write_bytes(
                work_root / "review" / "design.html",
                render_design_review_v3(_contract_payload(authorized_contract)).encode("utf-8"),
            )
        except OSError as error:
            rollback_errors = _rollback_start_files(work_root, created_root=True)
            return {
                "status": "write_failed", "work_id": candidate,
                "errors": [str(error), *rollback_errors],
            }
        relative = work_root.relative_to(root).as_posix()
        return {
            "status": "created", "work_id": candidate, "slug": normalized_slug,
            "path": relative, "contract": authorized_contract,
        }
    return {"status": "conflict", "errors": ["generated_work_id_collision"]}


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
    del host_goal  # Goal tracking is optional.
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
    if review_html is None:
        try:
            review_digest = canonical_digest(render_design_review_v3(payload))
        except ValueError:
            return {"authorized": False, "errors": ["canonical_review_invalid"]}
    else:
        review_digest = canonical_digest(review_html)
    expected = _authorization_record(
        payload, mode=str(authorization.get("mode")), actor=str(authorization.get("actor")),
        authorized_at=str(authorization.get("authorized_at")),
        review_digest=review_digest,
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
        normalized = normalize_project_config(project)
        if normalized["status"] == "invalid":
            return {"authorized": False, "errors": normalized["errors"]}
    return {"authorized": True, "errors": [], "review_digest": review_digest}


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
    material_amendment_risks = MATERIAL_RISK_FLAGS | {
        "public_contract", "acceptance", "architecture", "high",
        "security", "privacy", "secret", "irreversible",
    }
    if risk in material_amendment_risks:
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
    root: Path, item_id: str, paths: list[str], message: str, *,
    dirty_baseline: list[str] | dict[str, Any],
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
        ["git", "commit", "--only", "-m", message, "--", *normalized_paths], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if committed.returncode:
        return {"status": "git_error", "error": (committed.stderr or committed.stdout).strip()}
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()
    return {"status": "committed", "item_id": item_id, "commit": revision, "paths": sorted(normalized_paths)}


DESIGN_ONLY_FILES = {"contract.json", "review/design.html"}
STARTED_WORK_FILES = {
    "contract.json", "work.json", "review/design.html", "review/result.html",
    "result.json", "evidence.jsonl", "agent/evidence.jsonl",
}
STARTED_WORK_DIRECTORIES = {"review", "agent"}


def _work_artifacts(work_root: Path) -> tuple[set[str], set[str], list[str]]:
    files: set[str] = set()
    directories: set[str] = set()
    errors: list[str] = []
    if _path_is_alias(work_root):
        return files, directories, ["work_root_alias"]
    try:
        candidates = sorted(work_root.rglob("*"))
    except OSError as error:
        return files, directories, [f"work_artifact_unreadable:{error}"]
    for candidate in candidates:
        relative = candidate.relative_to(work_root).as_posix()
        if _path_is_alias(candidate):
            errors.append(f"work_artifact_alias:{relative}")
        elif candidate.is_dir():
            directories.add(relative)
        elif candidate.is_file():
            files.add(relative)
        else:
            errors.append(f"work_artifact_unexpected:{relative}")
    return files, directories, errors


def _read_work_object(path: Path, error_code: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, [error_code]
    if not isinstance(value, dict):
        return None, [error_code]
    return value, []


def _validate_saved_design(
    work_root: Path,
    work_id: str,
    *,
    supplied_contract: dict[str, Any] | None,
    project: dict[str, Any] | None,
    require_review: bool,
    canonical_review: bool = True,
) -> tuple[dict[str, Any] | None, list[str]]:
    stored, errors = _read_work_object(work_root / "contract.json", "stored_contract_corrupt")
    if stored is None:
        return None, errors
    if stored.get("work_id") != work_id:
        errors.append("stored_contract_identity_mismatch")
    if supplied_contract is not None and canonical_digest(stored) != canonical_digest(supplied_contract):
        errors.append("stored_contract_mismatch")
    review_path = work_root / "review" / "design.html"
    observed_review_text: str | None = None
    if require_review or review_path.exists() or review_path.is_symlink():
        try:
            observed_review = review_path.read_bytes()
            observed_review_text = observed_review.decode("utf-8")
            expected_review = (
                render_design_review_v3(_contract_payload(stored)).encode("utf-8")
                if canonical_review else observed_review
            )
        except (OSError, UnicodeError, ValueError, FileNotFoundError):
            errors.append("canonical_review_unreadable")
        else:
            if observed_review != expected_review:
                errors.append("canonical_review_mismatch")
    authorization = execution_authorized(
        stored,
        review_html=observed_review_text if not canonical_review else None,
        project=project,
    )
    if not authorization["authorized"]:
        errors.extend(f"stored_{error}" for error in authorization["errors"])
    return stored, sorted(set(errors))


def _validate_design_only_directory(
    work_root: Path,
    work_id: str,
    *,
    supplied_contract: dict[str, Any] | None = None,
    project: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    files, directories, errors = _work_artifacts(work_root)
    for relative in sorted(files - DESIGN_ONLY_FILES):
        errors.append(f"unexpected_work_artifact:{relative}")
    for relative in sorted(DESIGN_ONLY_FILES - files):
        errors.append(f"missing_design_artifact:{relative}")
    for relative in sorted(directories - {"review"}):
        errors.append(f"unexpected_work_artifact:{relative}")
    stored: dict[str, Any] | None = None
    if not errors:
        stored, saved_errors = _validate_saved_design(
            work_root, work_id, supplied_contract=supplied_contract,
            project=project, require_review=True,
        )
        errors.extend(saved_errors)
    return stored, sorted(set(errors))


def _validate_active_manifest(
    manifest: dict[str, Any], work_id: str, stored_contract: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if manifest.get("work_id") != work_id:
        errors.append("work_identity_conflict")
    if manifest.get("state") != "active":
        errors.append("work_state_conflict")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("work_schema_conflict")
    if manifest.get("contract_version") != SCHEMA_VERSION:
        errors.append("work_contract_version_conflict")
    expected_path = f".work/goals/active/{work_id}"
    if manifest.get("owned_paths") != [expected_path]:
        errors.append("work_owned_paths_conflict")
    if manifest.get("integrity_digest") != canonical_digest(_contract_payload(stored_contract)):
        errors.append("contract_integrity_mismatch")
    for field in ("created_at", "source_commit", "base_branch", "feature_branch"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            errors.append(f"work_manifest_invalid:{field}")
    baseline = manifest.get("dirty_baseline")
    baseline_valid = isinstance(baseline, dict) and set(baseline) == {
        "base_revision", "entries", "digest",
    }
    if baseline_valid:
        base_revision = baseline.get("base_revision")
        entries = baseline.get("entries")
        baseline_valid = (
            isinstance(base_revision, str) and bool(base_revision)
            and base_revision == manifest.get("source_commit")
            and isinstance(entries, list)
            and baseline.get("digest") == canonical_digest({
                "base_revision": base_revision, "entries": entries,
            })
        )
        if baseline_valid:
            allowed_states = {"staged", "unstaged", "deleted", "untracked"}
            for entry in entries:
                if not isinstance(entry, dict) or set(entry) != {
                    "path", "identity", "states", "index_oid", "worktree_hash",
                }:
                    baseline_valid = False
                    break
                states = entry.get("states")
                if not (
                    isinstance(entry.get("path"), str) and entry["path"]
                    and isinstance(entry.get("identity"), str) and entry["identity"]
                    and isinstance(states, list) and bool(states)
                    and len(states) == len(set(states)) and set(states) <= allowed_states
                    and (entry.get("index_oid") is None or isinstance(entry.get("index_oid"), str))
                    and (entry.get("worktree_hash") is None or isinstance(entry.get("worktree_hash"), str))
                ):
                    baseline_valid = False
                    break
    if not baseline_valid:
        errors.append("work_manifest_invalid:dirty_baseline")
    allowed_fields = {
        "schema_version", "work_id", "state", "created_at", "source_commit",
        "base_branch", "feature_branch", "worktree", "completed_at", "retain_until",
        "delete_after", "contract_version", "integrity_digest", "owned_paths",
        "dirty_baseline",
    }
    for field in sorted(set(manifest) - allowed_fields):
        errors.append(f"work_manifest_unknown_field:{field}")
    return sorted(set(errors))


def _incomplete_work_transactions(root: Path) -> list[str]:
    return _transaction_blockers(root)


def _classify_start_root(
    root: Path,
    work_id: str,
    contract: dict[str, Any],
    *,
    project: dict[str, Any],
) -> dict[str, Any]:
    try:
        relative, _ = canonical_repo_identity(root, f".work/goals/active/{work_id}")
        work_root = _safe_repo_path(root, relative)
    except ValueError as error:
        return {
            "classification": "conflict_or_corrupt", "work_root": None,
            "errors": [str(error)],
        }
    transaction_errors = _incomplete_work_transactions(root)
    if transaction_errors:
        return {
            "classification": "conflict_or_corrupt", "work_root": work_root,
            "errors": transaction_errors,
        }
    if work_root.is_symlink() or _path_is_alias(work_root):
        return {
            "classification": "conflict_or_corrupt", "work_root": work_root,
            "errors": ["work_root_alias"],
        }
    if not work_root.exists():
        return {"classification": "missing", "work_root": work_root, "errors": []}
    if not work_root.is_dir():
        return {
            "classification": "conflict_or_corrupt", "work_root": work_root,
            "errors": ["work_root_not_directory"],
        }
    files, directories, artifact_errors = _work_artifacts(work_root)
    if "work.json" not in files:
        _, design_errors = _validate_design_only_directory(
            work_root, work_id, supplied_contract=contract, project=project,
        )
        errors = sorted(set([*artifact_errors, *design_errors]))
        return {
            "classification": "valid_design_only" if not errors else "conflict_or_corrupt",
            "work_root": work_root, "errors": errors,
        }
    errors = list(artifact_errors)
    for relative in sorted(files - STARTED_WORK_FILES):
        errors.append(f"unexpected_work_artifact:{relative}")
    for relative in sorted(directories - STARTED_WORK_DIRECTORIES):
        errors.append(f"unexpected_work_artifact:{relative}")
    stored, saved_errors = _validate_saved_design(
        work_root, work_id, supplied_contract=contract, project=project,
        require_review=False,
    )
    errors.extend(saved_errors)
    manifest, manifest_errors = _read_work_object(
        work_root / "work.json", "work_manifest_corrupt",
    )
    errors.extend(manifest_errors)
    if stored is not None and manifest is not None:
        errors.extend(_validate_active_manifest(manifest, work_id, stored))
    return {
        "classification": "valid_already_started" if not errors else "conflict_or_corrupt",
        "work_root": work_root, "errors": sorted(set(errors)), "manifest": manifest,
    }


def _rollback_start_branch(
    root: Path, *, base_branch: str, feature_branch: str, created: bool,
) -> list[str]:
    if not created:
        return []
    errors: list[str] = []
    switched = subprocess.run(
        ["git", "switch", base_branch], cwd=root, capture_output=True, text=True, check=False,
    )
    if switched.returncode:
        errors.append("start_branch_rollback_switch_failed")
        return errors
    deleted = subprocess.run(
        ["git", "branch", "-D", feature_branch], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if deleted.returncode:
        errors.append("start_branch_rollback_delete_failed")
    return errors


def _rollback_start_files(work_root: Path, *, created_root: bool) -> list[str]:
    errors: list[str] = []
    try:
        if created_root:
            if work_root.is_dir() and not _path_is_alias(work_root):
                shutil.rmtree(work_root)
        else:
            manifest_path = work_root / "work.json"
            if manifest_path.is_file() or manifest_path.is_symlink():
                manifest_path.unlink()
            for temporary in work_root.glob("work.json.tmp*"):
                if temporary.is_file() or temporary.is_symlink():
                    temporary.unlink()
    except OSError as error:
        errors.append(f"start_file_rollback_failed:{error}")
    return errors


def start_work(
    root: Path, work_id: str, slug: str, contract: dict[str, Any], *,
    project: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify Goal state before Git mutation and create one durable work manifest."""
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
    normalized_project = normalize_project_config(project)
    if normalized_project["status"] == "invalid":
        return {
            "status": "authorization_failed", "classification": "conflict_or_corrupt",
            "errors": normalized_project["errors"],
        }
    project = normalized_project["project"]
    authorization = execution_authorized(contract, project=project)
    if not authorization["authorized"]:
        return {
            "status": "authorization_failed", "classification": "conflict_or_corrupt",
            "errors": authorization["errors"],
        }
    classified = _classify_start_root(root, work_id, contract, project=project)
    classification = classified["classification"]
    if classification == "conflict_or_corrupt":
        return {
            "status": "conflict", "classification": classification,
            "errors": classified["errors"],
        }
    if classification == "valid_already_started":
        return {
            "status": "already_started", "classification": classification,
            "manifest": classified["manifest"],
        }
    lock_name = f"start-{work_id}"
    lock_path, lock_payload, lock_error = _acquire_operation_lock(root, lock_name)
    if lock_error:
        return {
            "status": "conflict", "classification": classification,
            "errors": [lock_error],
        }
    try:
        classified = _classify_start_root(root, work_id, contract, project=project)
        classification = classified["classification"]
        if classification == "conflict_or_corrupt":
            return {
                "status": "conflict", "classification": classification,
                "errors": classified["errors"],
            }
        if classification == "valid_already_started":
            return {
                "status": "already_started", "classification": classification,
                "manifest": classified["manifest"],
            }
        work_root = classified["work_root"]
        assert isinstance(work_root, Path)
        manifest_path = work_root / "work.json"
        base_branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=root,
            capture_output=True, text=True, check=False,
        )
        base_revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root,
            capture_output=True, text=True, check=False,
        )
        if base_branch.returncode or base_revision.returncode or not base_branch.stdout.strip():
            return {"status": "git_error", "errors": ["captured_base_unavailable"]}
        normalized_slug = re.sub(r"[^a-z0-9-]+", "-", slug.casefold()).strip("-")
        if not normalized_slug:
            return {"status": "invalid_slug"}
        baseline = collect_git_baseline(root)
        base_branch_name = base_branch.stdout.strip()
        git_policy = project["git"]
        protected_branches = set(git_policy["protected_branches"])
        feature_branch = base_branch_name
        created_branch = False
        if base_branch_name in protected_branches:
            pattern = str(git_policy["branch_pattern"])
            try:
                feature_branch = pattern.format(work_id=work_id, slug=normalized_slug)
            except (KeyError, ValueError):
                return {"status": "invalid_branch_policy"}
            switched = subprocess.run(
                ["git", "switch", "-c", feature_branch], cwd=root,
                capture_output=True, text=True, check=False,
            )
            if switched.returncode:
                return {"status": "git_error", "errors": [(switched.stderr or switched.stdout).strip()]}
            created_branch = True
        manifest = {
            "schema_version": SCHEMA_VERSION, "work_id": work_id, "state": "active",
            "created_at": datetime.now().astimezone().isoformat(),
            "source_commit": base_revision.stdout.strip(), "base_branch": base_branch_name,
            "feature_branch": feature_branch, "contract_version": SCHEMA_VERSION,
            "dirty_baseline": baseline,
            "integrity_digest": canonical_digest(_contract_payload(contract)),
            "owned_paths": [f".work/goals/active/{work_id}"],
        }
        created_work_root = False
        try:
            if classification == "missing":
                work_root.parent.mkdir(parents=True, exist_ok=True)
                work_root.mkdir(exist_ok=False)
                created_work_root = True
                _durable_write_json(work_root / "contract.json", contract)
                _durable_write_bytes(
                    work_root / "review" / "design.html",
                    render_design_review_v3(_contract_payload(contract)).encode("utf-8"),
                )
            _durable_write_json(manifest_path, manifest)
        except OSError as error:
            rollback_errors = _rollback_start_files(work_root, created_root=created_work_root)
            rollback_errors.extend(_rollback_start_branch(
                root, base_branch=base_branch_name, feature_branch=feature_branch,
                created=created_branch,
            ))
            return {
                "status": "precondition_failed", "classification": classification,
                "errors": [str(error), *rollback_errors],
            }
        return {"status": "started", "classification": classification, "manifest": manifest}
    finally:
        _release_operation_lock(lock_path, lock_payload)


def _project_worktree_path(root: Path, branch: str) -> Path | None:
    root = root.resolve()
    parts = branch.split("/")
    if (
        not re.fullmatch(r"[A-Za-z0-9._/-]+", branch)
        or branch.startswith(("/", "-"))
        or branch.endswith(("/", "."))
        or ".." in branch
        or any(not part or part.startswith(".") or part.endswith(".lock") for part in parts)
    ):
        return None
    worktree_root = root / ".worktree"
    if (
        (worktree_root.exists() and not worktree_root.is_dir())
        or _path_is_alias(worktree_root)
    ):
        return None
    return worktree_root / ("wt-" + branch.replace("/", "%2F"))


def create_worktree(root: Path, *, base: str, branch: str) -> dict[str, Any]:
    root = root.resolve()
    destination = _project_worktree_path(root, branch)
    if destination is None:
        return {"status": "invalid_target"}
    if destination.exists():
        return {"status": "conflict", "errors": ["worktree_destination_exists"]}
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", ".worktree/.harness-probe"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if ignored.returncode:
        if ignored.returncode == 1:
            return {"status": "precondition_failed", "errors": ["worktree_root_not_ignored"]}
        return {"status": "git_error", "errors": [(ignored.stderr or ignored.stdout).strip()]}
    destination.parent.mkdir(exist_ok=True)
    created = subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(destination), base], cwd=root,
        capture_output=True, text=True, check=False,
    )
    if created.returncode:
        return {"status": "git_error", "errors": [(created.stderr or created.stdout).strip()]}
    return {"status": "created", "branch": branch, "path": str(destination), "base": base}


def integrate_worktree(
    root: Path, *, base: str, branch: str, project: dict[str, Any],
    approved_exact_path: str | None,
) -> dict[str, Any]:
    root = root.resolve()
    normalized_project = normalize_project_config(project)
    if normalized_project["status"] == "invalid":
        return {"status": "precondition_failed", "errors": normalized_project["errors"]}
    project = normalized_project["project"]
    destination = _project_worktree_path(root, branch)
    if destination is None:
        return {"status": "invalid_target"}
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
    normalized_project = normalize_project_config(project)
    if normalized_project["status"] == "invalid":
        errors = list(normalized_project["errors"])
        return {
            "status": "invalid", "errors": errors,
            "matched_rules": [], "tests": [], "features": [],
            "feature_commands": [], "trigger_ids": [], "full_trigger_ids": [],
            "not_required_rule_ids": [], "full_required": False,
            "unresolved": [f"project_configuration:{error}" for error in errors],
        }
    project = normalized_project["project"]
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
        "status": "selected",
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


def _lifecycle_move_locked(
    root: Path, source: Path, destination: Path, manifest: dict[str, Any], *,
    operation: str, fault_after: str | None = None, crash_after: str | None = None,
    source_writes: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Move one work directory with durable recovery across process interruption."""
    try:
        work_id = validate_work_id(manifest.get("work_id"))
        source.relative_to(root)
        destination.relative_to(root)
    except ValueError as error:
        return {"status": "invalid_work", "errors": [str(error)]}
    recovery = _recover_transactions_locked(root)
    if recovery["status"] == "recovery_failed":
        return {"status": "precondition_failed", "errors": recovery["errors"]}
    manifest_path = source / "work.json"
    manifest_existed = manifest_path.is_file()
    original_manifest = manifest_path.read_bytes() if manifest_existed else b""
    transactions = root / ".work" / "transactions"
    transaction_identity = canonical_digest({"operation": operation, "work_id": work_id})
    transaction_root = transactions / (
        f"{operation}-{transaction_identity.removeprefix('sha256:')[:16]}-{secrets.token_hex(4)}"
    )
    transaction_root.mkdir(parents=True, exist_ok=False)
    journal_path = transaction_root / "journal.json"
    backup_path = transaction_root / "work.json.preimage"
    write_preimages: list[tuple[str, bool, bytes]] = []
    try:
        for relative, _ in sorted((source_writes or {}).items()):
            normalized, _ = canonical_repo_identity(source, relative)
            target = source.joinpath(*PurePosixPath(normalized).parts)
            if target.exists() and not target.is_file():
                raise ValueError(f"lifecycle_source_write_invalid:{normalized}")
            existed = target.is_file()
            write_preimages.append((normalized, existed, target.read_bytes() if existed else b""))
        _durable_write_bytes(backup_path, original_manifest)
        source_file_backups: list[dict[str, Any]] = []
        for index, (relative, existed, content) in enumerate(write_preimages):
            record: dict[str, Any] = {"path": relative, "existed": existed}
            if existed:
                file_backup = transaction_root / "source-files" / f"{index:04d}.preimage"
                _durable_write_bytes(file_backup, content)
                record.update({
                    "backup": file_backup.relative_to(root).as_posix(),
                    "pre_hash": "sha256:" + sha256(content).hexdigest(),
                })
            source_file_backups.append(record)
    except (OSError, ValueError) as error:
        shutil.rmtree(transaction_root, ignore_errors=True)
        return {"status": "precondition_failed", "errors": [str(error)]}
    journal = {
        "schema_version": SCHEMA_VERSION, "kind": "lifecycle_move",
        "operation": operation, "status": "applying",
        "owner_pid": os.getpid(),
        "source": source.relative_to(root).as_posix(),
        "destination": destination.relative_to(root).as_posix(),
        "manifest_backup": backup_path.relative_to(root).as_posix(),
        "manifest_existed": manifest_existed,
        "pre_manifest_hash": "sha256:" + sha256(original_manifest).hexdigest(),
        "source_file_backups": source_file_backups,
    }
    _durable_write_json(journal_path, journal)
    try:
        for relative, content in sorted((source_writes or {}).items()):
            normalized, _ = canonical_repo_identity(source, relative)
            _durable_write_bytes(
                source.joinpath(*PurePosixPath(normalized).parts), content,
            )
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


def _lifecycle_move(
    root: Path, source: Path, destination: Path, manifest: dict[str, Any], *,
    operation: str, fault_after: str | None = None, crash_after: str | None = None,
    source_writes: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    lock_path, lock_payload, lock_error = _acquire_operation_lock(root, "transaction")
    if lock_error:
        return {"status": "precondition_failed", "errors": [lock_error]}
    try:
        return _lifecycle_move_locked(
            root, source, destination, manifest, operation=operation,
            fault_after=fault_after, crash_after=crash_after,
            source_writes=source_writes,
        )
    finally:
        _release_operation_lock(lock_path, lock_payload)


def _transition_work_to_completed(
    root: Path, work_id: str, *, completed_at: str, completed_days: int, trash_days: int,
    fault_after: str | None = None, crash_after: str | None = None,
    source_writes: dict[str, bytes] | None = None,
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
        crash_after=crash_after, source_writes=source_writes,
    )
    if transaction["status"] != "committed":
        return transaction
    return {"status": "completed", "path": destination.relative_to(root).as_posix(), "manifest": manifest}


def close_work(
    root: Path, work_id: str, *, contract: dict[str, Any], result: dict[str, Any],
    impact: dict[str, Any], completed_at: str, completed_days: int, trash_days: int,
    fault_after: str | None = None, crash_after: str | None = None,
) -> dict[str, Any]:
    """Validate and close one active Goal as a single recoverable lifecycle transition."""
    root = root.resolve()
    try:
        work_id = validate_work_id(work_id)
    except ValueError as error:
        return {"status": "invalid_work", "errors": [str(error)]}
    if not isinstance(contract, dict) or contract.get("work_id") != work_id:
        return {"status": "invalid_work", "errors": ["supplied_contract_identity_mismatch"]}
    if not isinstance(result, dict) or not isinstance(impact, dict):
        return {"status": "invalid_work", "errors": ["result_or_impact_invalid"]}
    if (
        isinstance(completed_days, bool) or not isinstance(completed_days, int) or completed_days < 0
        or isinstance(trash_days, bool) or not isinstance(trash_days, int) or trash_days < 0
    ):
        return {"status": "invalid_work", "errors": ["retention_invalid"]}
    try:
        moment = datetime.fromisoformat(completed_at)
    except (TypeError, ValueError):
        return {"status": "invalid_work", "errors": ["completed_at_invalid"]}
    active_relative = f".work/goals/active/{work_id}"
    destination_relative = f".work/goals/completed/{moment:%Y-%m}/{work_id}"
    try:
        canonical_repo_identity(root, active_relative)
        canonical_repo_identity(root, destination_relative)
    except ValueError as error:
        return {"status": "invalid_work", "errors": [str(error)]}
    source = root.joinpath(*PurePosixPath(active_relative).parts)
    destination = root.joinpath(*PurePosixPath(destination_relative).parts)
    if not source.is_dir():
        return {"status": "invalid_work", "errors": ["active_work_missing"]}

    files, directories, artifact_errors = _work_artifacts(source)
    required_files = {"contract.json", "work.json", "review/design.html"}
    artifact_errors.extend(
        f"missing_work_artifact:{relative}" for relative in sorted(required_files - files)
    )
    artifact_errors.extend(
        f"unexpected_work_artifact:{relative}" for relative in sorted(files - STARTED_WORK_FILES)
    )
    artifact_errors.extend(
        f"unexpected_work_artifact:{relative}" for relative in sorted(directories - STARTED_WORK_DIRECTORIES)
    )
    if artifact_errors:
        return {"status": "invalid_work", "errors": sorted(set(artifact_errors))}

    transaction_errors = _incomplete_work_transactions(root)
    if transaction_errors:
        return {"status": "precondition_failed", "errors": transaction_errors}
    stored_contract, contract_errors = _validate_saved_design(
        source, work_id, supplied_contract=contract, project=None, require_review=True,
        canonical_review=False,
    )
    if stored_contract is None or contract_errors:
        return {"status": "invalid_work", "errors": contract_errors}
    manifest, manifest_errors = _read_work_object(source / "work.json", "work_manifest_corrupt")
    if manifest is None:
        return {"status": "invalid_work", "errors": manifest_errors}
    manifest_errors.extend(_validate_active_manifest(manifest, work_id, stored_contract))
    if manifest_errors:
        return {"status": "invalid_work", "errors": sorted(set(manifest_errors))}
    evaluation = evaluate_result(stored_contract, result, impact)
    if evaluation["status"] != "complete":
        return evaluation
    try:
        review_bytes = render_result_review_v3(stored_contract, result, impact).encode("utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        return {"status": "invalid_work", "errors": [f"result_review_invalid:{error}"]}
    if destination.exists() or destination.is_symlink():
        return {"status": "conflict", "errors": ["completed_destination_exists"]}
    result_bytes = (
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    return _transition_work_to_completed(
        root, work_id, completed_at=completed_at, completed_days=completed_days,
        trash_days=trash_days, fault_after=fault_after, crash_after=crash_after,
        source_writes={"result.json": result_bytes, "review/result.html": review_bytes},
    )


def audit_work_lifecycle(root: Path) -> dict[str, Any]:
    goals = root / ".work" / "goals"
    seen: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    design_only: list[str] = []
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
                if state == "active":
                    _, design_errors = _validate_design_only_directory(
                        directory, directory.name,
                    )
                    if not design_errors:
                        design_only.append(directory.name)
                        continue
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
    return {"findings": findings, "work_ids": seen, "design_only": sorted(design_only)}


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
    blockers.extend(_transaction_blockers(root))
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
REQUIRED_COHORT_RESOURCES = frozenset({
    "close-goal/SKILL.md",
    "close-goal/references/documentation-policy.md",
    "close-goal/references/human-readability-policy.md",
    "close-goal/references/testing-policy.md",
    "close-goal/schemas/contract.schema.json",
    "close-goal/schemas/work.schema.json",
    "close-goal/scripts/core_harness.py",
    "close-goal/scripts/render_result_review.py",
    "close-goal/templates/result-item-review.html",
    "design-goal/SKILL.md",
    "design-goal/references/human-readability-policy.md",
    "design-goal/schemas/contract.schema.json",
    "design-goal/scripts/core_harness.py",
    "design-goal/scripts/render_item_review.py",
    "design-goal/templates/design-item-review.html",
    "diagnose/SKILL.md",
    "diagnose/references/goal-execution-policy.md",
    "execute-codex-goal/SKILL.md",
    "execute-codex-goal/references/goal-execution-policy.md",
    "execute-codex-goal/references/testing-policy.md",
    "execute-codex-goal/schemas/contract.schema.json",
    "execute-codex-goal/schemas/work.schema.json",
    "execute-codex-goal/scripts/core_harness.py",
    "execute-codex-goal/templates/design-item-review.html",
    "maintain-agent-harness/SKILL.md",
    "maintain-agent-harness/references/testing-policy.md",
    "maintain-agent-harness/schemas/project.schema.json",
    "maintain-agent-harness/schemas/work.schema.json",
    "maintain-agent-harness/scripts/core_harness.py",
    "setup-agent-harness/SKILL.md",
    "setup-agent-harness/references/documentation-policy.md",
    "setup-agent-harness/schemas/project.schema.json",
    "setup-agent-harness/scripts/core_harness.py",
    "setup-agent-harness/templates/project/AGENTS.md",
    "setup-agent-harness/templates/project/CLAUDE.md",
    "setup-agent-harness/templates/project/TESTING.md",
    "setup-agent-harness/templates/project/project.yaml",
})


def _cohort_manifest_valid(resource_manifest: dict[str, Any]) -> bool:
    if not isinstance(resource_manifest, dict) or set(resource_manifest) != {
        "schema_version", "algorithm", "root", "excludes", "files",
    }:
        return False
    if (
        resource_manifest.get("schema_version") != 1
        or resource_manifest.get("algorithm") != "sha256"
        or resource_manifest.get("root") != "skills"
        or resource_manifest.get("excludes") != [COHORT_MANIFEST_RESOURCE]
    ):
        return False
    files = resource_manifest.get("files")
    if not isinstance(files, dict) or not files:
        return False
    for relative, digest in files.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            return False
        pure = PurePosixPath(relative)
        if (
            pure.is_absolute() or pure.as_posix() != relative
            or any(part in {"", ".", ".."} for part in pure.parts)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            return False
    return True


def _installed_cohort_tree(
    installed_root: Path,
) -> tuple[set[str], set[str], set[str], list[str]]:
    files: set[str] = set()
    directories: set[str] = set()
    aliases: set[str] = set()
    errors: list[str] = []
    for skill in HARNESS_INSTALL_SKILLS:
        skill_root = installed_root / skill
        if _path_is_alias(skill_root):
            aliases.add(skill)
            continue
        if not skill_root.exists():
            continue
        if not skill_root.is_dir():
            errors.append(f"installed_resource_unexpected:{skill}")
            continue
        pending = [skill_root]
        while pending:
            current = pending.pop()
            try:
                entries = sorted(os.scandir(current), key=lambda entry: entry.name)
            except OSError:
                errors.append(
                    f"installed_tree_unreadable:{current.relative_to(installed_root).as_posix()}"
                )
                continue
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(installed_root).as_posix()
                if _path_is_alias(path):
                    aliases.add(relative)
                elif entry.is_dir(follow_symlinks=False):
                    directories.add(relative)
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.add(relative)
                else:
                    errors.append(f"installed_resource_unexpected:{relative}")
    return files, directories, aliases, errors


def _installed_cohort_files(installed_root: Path) -> set[str]:
    return _installed_cohort_tree(installed_root)[0]


def inspect_installed_cohort(installed_root: Path, resource_manifest: dict[str, Any]) -> dict[str, Any]:
    installed_root = Path(os.path.abspath(installed_root))
    blockers: list[str] = []
    if _path_is_alias(installed_root):
        return {
            "status": "invalid", "blockers": ["installed_root_alias"],
            "skills": list(HARNESS_INSTALL_SKILLS),
        }
    if not _cohort_manifest_valid(resource_manifest):
        return {
            "status": "invalid_manifest", "blockers": ["installed_manifest_invalid"],
            "skills": list(HARNESS_INSTALL_SKILLS),
        }
    files = _cohort_manifest_files(resource_manifest)
    declared = set(files)
    for relative in sorted(REQUIRED_COHORT_RESOURCES - declared):
        blockers.append(f"installed_manifest_required_missing:{relative}")
    for relative in sorted(declared - REQUIRED_COHORT_RESOURCES):
        blockers.append(f"installed_manifest_unexpected_resource:{relative}")
    if blockers:
        return {
            "status": "invalid_manifest", "blockers": blockers,
            "skills": list(HARNESS_INSTALL_SKILLS),
        }
    expected_files = set(files) | {COHORT_MANIFEST_RESOURCE}
    observed_files, observed_directories, observed_aliases, tree_errors = _installed_cohort_tree(
        installed_root,
    )
    blockers.extend(tree_errors)
    blockers.extend(
        f"installed_resource_alias:{relative}" for relative in sorted(observed_aliases)
    )
    expected_directories: set[str] = set()
    for relative in expected_files:
        parent = PurePosixPath(relative).parent
        while parent.as_posix() != ".":
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    for relative in sorted(observed_directories - expected_directories):
        blockers.append(f"installed_directory_extra:{relative}")
    for skill in RETIRED_HARNESS_SKILLS:
        retired_path = installed_root / skill
        if retired_path.exists() or retired_path.is_symlink():
            blockers.append(f"retired_skill_present:{skill}")
    for relative in sorted(observed_files - expected_files):
        blockers.append(f"installed_resource_extra:{relative}")
    for relative in sorted(expected_files - observed_files):
        blockers.append(f"installed_resource_missing:{relative}")
    for relative, expected in sorted(files.items()):
        try:
            normalized, _ = canonical_repo_identity(installed_root, str(relative))
            path = installed_root.joinpath(*PurePosixPath(normalized).parts)
        except ValueError as error:
            blocker = (
                f"installed_resource_alias:{relative}"
                if str(error).startswith("path_alias:")
                else f"installed_resource_invalid:{relative}"
            )
            blockers.append(blocker)
            continue
        if not path.is_file():
            blockers.append(f"installed_resource_missing:{relative}")
            continue
        actual = _manifest_file_hash(path, None)
        if actual != expected:
            blockers.append(f"installed_resource_drift:{relative}")
    manifest_resource = installed_root.joinpath(*PurePosixPath(COHORT_MANIFEST_RESOURCE).parts)
    if manifest_resource.is_file():
        try:
            installed_manifest = json.loads(manifest_resource.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            blockers.append(f"installed_resource_drift:{COHORT_MANIFEST_RESOURCE}")
        else:
            if installed_manifest != resource_manifest:
                blockers.append(f"installed_resource_drift:{COHORT_MANIFEST_RESOURCE}")
    blockers = sorted(set(blockers))
    return {
        "status": "complete" if not blockers else "invalid", "blockers": blockers,
        "skills": list(HARNESS_INSTALL_SKILLS),
    }


def install_harness_cohort(
    source_root: Path, install_root: Path, resource_manifest: dict[str, Any], *,
    approved_install_root: str | None, fault_after: int | None = None,
) -> dict[str, Any]:
    """Atomically replace only the Harness cohort after exact-root approval and staged verification."""
    source_root = Path(os.path.abspath(source_root))
    install_root = Path(os.path.abspath(install_root))
    if approved_install_root is None or Path(approved_install_root).resolve() != install_root.resolve():
        return {"status": "approval_required", "install_root": str(install_root)}
    if _path_is_alias(source_root):
        return {"status": "invalid_source", "errors": ["source_root_alias"]}
    if _path_is_alias(install_root):
        return {"status": "invalid_root", "errors": ["install_root_alias"]}
    if not _cohort_manifest_valid(resource_manifest):
        return {"status": "invalid_manifest"}
    files = _cohort_manifest_files(resource_manifest)
    source_manifest = source_root.joinpath(*PurePosixPath(COHORT_MANIFEST_RESOURCE).parts)
    try:
        bundled_manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"status": "invalid_source", "errors": ["bundled_manifest_missing_or_invalid"]}
    if _path_is_alias(source_manifest) or bundled_manifest != resource_manifest:
        return {"status": "invalid_source", "errors": ["bundled_manifest_mismatch"]}
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
            normalized, _ = canonical_repo_identity(source_root, relative)
            source = source_root.joinpath(*PurePosixPath(normalized).parts)
            target = _safe_repo_path(staging, relative)
            if not source.is_file() or _path_is_alias(source):
                raise ValueError(f"invalid_source_resource:{relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        staged_manifest = staging.joinpath(*PurePosixPath(COHORT_MANIFEST_RESOURCE).parts)
        staged_manifest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_manifest, staged_manifest)
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
            relative: _manifest_file_hash(install_root / relative, None)
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

    normalized_project = normalize_project_config(project)
    if normalized_project["status"] == "invalid":
        for error in normalized_project["errors"]:
            add("MAINT-PROJECT-CONFIG", ".harness/project.yaml", error, "high")
        project = {}
    else:
        project = normalized_project["project"]
    checks["MAINT-PROJECT-CONFIG"] = normalized_project

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

    transaction_blockers = _transaction_blockers(root)
    for blocker in transaction_blockers:
        add("MAINT-TRANSACTION", ".work/transactions", blocker, "high")
    checks["MAINT-TRANSACTION"] = {"blockers": transaction_blockers}

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


def activate_harness(
    root: Path,
    project: dict[str, Any],
    *,
    installed_root: Path,
    resource_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Activate only from observed repository state and an intact installed cohort."""
    normalized = normalize_project_config(project)
    legacy = inspect_legacy_graph(root)
    installed = inspect_installed_cohort(installed_root, resource_manifest)
    blockers = [*legacy["blockers"], *installed["blockers"]]
    if normalized["status"] == "invalid":
        blockers.extend(normalized["errors"])
    if blockers:
        return {"status": "cutover_blocked", "blockers": blockers, "legacy": legacy, "installed": installed}
    return {
        "status": "activated", "project": normalized["project"],
        "normalization": normalized["status"],
    }


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_object:{path}")
    return value


def _runtime_cli_owner() -> str:
    script = Path(__file__).resolve()
    if script.parent.name != "scripts":
        return "unknown"
    return script.parent.parent.name


def _cli_parser(owner: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Core-First Agent Harness")
    sub = parser.add_subparsers(dest="command", required=True)
    resolved_owner = _runtime_cli_owner() if owner is None else owner
    allowed = ALL_CLI_COMMANDS if resolved_owner == "authoring" else PUBLIC_COMMANDS_BY_SKILL.get(
        resolved_owner, frozenset(),
    )

    def command(name: str) -> argparse.ArgumentParser | None:
        return sub.add_parser(name) if name in allowed else None

    inventory = command("inventory")
    if inventory:
        inventory.add_argument("--root", type=Path, required=True)
        inventory.add_argument("--mapping", type=Path)
    design_create_parser = command("design-create")
    if design_create_parser:
        design_create_parser.add_argument("--root", type=Path, required=True)
        design_create_parser.add_argument("--contract", type=Path, required=True)
        design_create_parser.add_argument("--slug", required=True)
        design_create_parser.add_argument("--work-id")
        design_create_parser.add_argument(
            "--intent", choices=("default", "explicit_approve"), default="default",
        )
        design_create_parser.add_argument("--actor", required=True)
        design_create_parser.add_argument("--at", required=True)
    design = command("render-design")
    if design:
        design.add_argument("--contract", type=Path, required=True)
        design.add_argument("--output", type=Path, required=True)
    authorize = command("authorize")
    if authorize:
        authorize.add_argument("--contract", type=Path, required=True)
        authorize.add_argument("--intent", choices=("default", "veto", "explicit_approve"), default="default")
        authorize.add_argument("--actor", required=True)
        authorize.add_argument("--at", required=True)
    result = command("render-result")
    if result:
        result.add_argument("--contract", type=Path, required=True)
        result.add_argument("--result", type=Path, required=True)
        result.add_argument("--output", type=Path, required=True)
    impact = command("impacted")
    if impact:
        impact.add_argument("--project", type=Path, required=True)
        impact.add_argument("--changed", action="append", default=[])
    cleanup_plan = command("cleanup-plan")
    if cleanup_plan:
        cleanup_plan.add_argument("--root", type=Path, required=True)
        cleanup_plan.add_argument("--request", type=Path, required=True)
    cleanup_apply = command("cleanup-apply")
    if cleanup_apply:
        cleanup_apply.add_argument("--root", type=Path, required=True)
        cleanup_apply.add_argument("--plan", type=Path, required=True)
        cleanup_apply.add_argument("--approval-digest", required=True)
    recover = command("recover")
    if recover:
        recover.add_argument("--root", type=Path, required=True)
    baseline = command("baseline")
    if baseline:
        baseline.add_argument("--root", type=Path, required=True)
    start = command("start")
    if start:
        start.add_argument("--root", type=Path, required=True)
        start.add_argument("--work-id", required=True)
        start.add_argument("--slug", required=True)
        start.add_argument("--contract", type=Path, required=True)
    amend = command("amend")
    if amend:
        amend.add_argument("--contract", type=Path, required=True)
        amend.add_argument("--item-id", required=True)
        amend.add_argument("--field", required=True)
        amend.add_argument("--value", type=Path, required=True)
        amend.add_argument("--message-id", required=True)
        amend.add_argument("--actor", required=True)
        amend.add_argument("--at", required=True)
        amend.add_argument("--risk", required=True)
    complete = command("complete")
    if complete:
        complete.add_argument("--contract", type=Path, required=True)
        complete.add_argument("--result", type=Path, required=True)
        complete.add_argument("--impact", type=Path, required=True)
    commit = command("commit")
    if commit:
        commit.add_argument("--root", type=Path, required=True)
        commit.add_argument("--item-id", required=True)
        commit.add_argument("--path", action="append", required=True)
        commit.add_argument("--baseline", type=Path, required=True)
        commit.add_argument("--message", required=True)
    worktree_create = command("worktree-create")
    if worktree_create:
        worktree_create.add_argument("--root", type=Path, required=True)
        worktree_create.add_argument("--base", required=True)
        worktree_create.add_argument("--branch", required=True)
    worktree_integrate = command("worktree-integrate")
    if worktree_integrate:
        worktree_integrate.add_argument("--root", type=Path, required=True)
        worktree_integrate.add_argument("--base", required=True)
        worktree_integrate.add_argument("--branch", required=True)
        worktree_integrate.add_argument("--project", type=Path, required=True)
        worktree_integrate.add_argument("--approved-exact-path", required=True)
    close = command("close")
    if close:
        close.add_argument("--root", type=Path, required=True)
        close.add_argument("--work-id", required=True)
        close.add_argument("--contract", type=Path, required=True)
        close.add_argument("--result", type=Path, required=True)
        close.add_argument("--impact", type=Path, required=True)
        close.add_argument("--at", required=True)
        close.add_argument("--completed-days", type=int, required=True)
        close.add_argument("--trash-days", type=int, required=True)
    sweep = command("sweep")
    if sweep:
        sweep.add_argument("--root", type=Path, required=True)
        sweep.add_argument("--at", required=True)
    delete = command("delete")
    if delete:
        delete.add_argument("--root", type=Path, required=True)
        delete.add_argument("--target", required=True)
        delete.add_argument("--approved-exact-target", required=True)
        delete.add_argument("--at", required=True)
        delete.add_argument("--destructive-override", action="store_true")
        delete.add_argument("--approved-override-target")
    audit = command("audit-work")
    if audit:
        audit.add_argument("--root", type=Path, required=True)
    maintain = command("maintain")
    if maintain:
        maintain.add_argument("--root", type=Path, required=True)
        maintain.add_argument("--project", type=Path, required=True)
        maintain.add_argument("--installed-root", type=Path)
        maintain.add_argument("--manifest", type=Path)
        maintain.add_argument("--today")
    install = command("install-cohort")
    if install:
        install.add_argument("--source-root", type=Path, required=True)
        install.add_argument("--install-root", type=Path, required=True)
        install.add_argument("--manifest", type=Path, required=True)
        install.add_argument("--approved-install-root", required=True)
    activation = command("activate")
    if activation:
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
        elif args.command == "design-create":
            payload = design_create(
                args.root, _json_object(args.contract), slug=args.slug,
                work_id=args.work_id, intent=args.intent, actor=args.actor,
                authorized_at=args.at,
            )
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
                args.root, args.item_id, args.path, args.message,
                dirty_baseline=baseline_payload.get("baseline", baseline_payload),
            )
        elif args.command == "worktree-create":
            payload = create_worktree(
                args.root, base=args.base, branch=args.branch
            )
        elif args.command == "worktree-integrate":
            payload = integrate_worktree(
                args.root, base=args.base, branch=args.branch,
                project=_json_object(args.project), approved_exact_path=args.approved_exact_path,
            )
        elif args.command == "close":
            payload = close_work(
                args.root, args.work_id, contract=_json_object(args.contract),
                result=_json_object(args.result), impact=_json_object(args.impact),
                completed_at=args.at, completed_days=args.completed_days,
                trash_days=args.trash_days,
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
        elif args.command == "activate":
            payload = activate_harness(
                args.root, _json_object(args.project), installed_root=args.installed_root,
                resource_manifest=_json_object(args.manifest),
            )
        else:
            raise ValueError(f"unsupported_command:{args.command}")
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("status") not in {
            "cutover_blocked", "invalid", "invalid_contract", "authorization_failed",
            "approval_required", "precondition_failed", "incomplete", "conflict",
            "git_error", "invalid_work", "invalid_target", "recovery_failed",
            "explicit_approval_required", "focused_approval_required", "vetoed",
            "unresolved_decisions", "ambiguous_intent", "invalid_amendment",
            "invalid_manifest", "invalid_source", "staging_invalid", "rolled_back",
            "rollback_failed", "write_failed", "invalid_root", "invalid_slug",
            "invalid_branch_policy",
            "cleanup_failed",
        } else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"status": "invalid", "errors": [str(error)]}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
