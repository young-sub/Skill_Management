#!/usr/bin/env python3
"""Deterministic Core-First Harness v3 contracts and compatibility checks."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


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
