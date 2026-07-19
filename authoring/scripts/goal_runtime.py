#!/usr/bin/env python3
"""Execute an approved Harness V2 contract inside a human-declared Goal."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


def _load_engine() -> Any:
    path = Path(__file__).with_name("contract_engine.py")
    spec = importlib.util.spec_from_file_location("harness_contract_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("contract_engine_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENGINE = _load_engine()


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected_object")
    return value


def _declaration_payload(state: dict[str, Any]) -> str:
    objective = state.get("objective") if isinstance(state.get("objective"), dict) else {}
    return "\n".join(
        (
            "Goal declaration payload:",
            "Use $execute-codex-goal.",
            f"Work ID: {objective.get('work_id', '<WORK_ID>')}",
            f"Contract: {objective.get('contract_path', '<CONTRACT_PATH>')}",
            f"Approved contract hash: {objective.get('contract_hash', '<CONTRACT_HASH>')}",
            "Execute every approved slice in dependency order.",
            "Stop only for the contract's Hard Stop conditions.",
        )
    )


def _file_hashes(source_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(source_root).parts:
            continue
        result[path.relative_to(source_root).as_posix()] = _digest(path)
    return result


def _git_status(source_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=source_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        return ["unavailable"]
    return result.stdout.splitlines()


def preflight(contract_root: Path, source_root: Path, goal_state: Path) -> tuple[dict[str, Any], int, list[Any]]:
    errors: list[str] = []
    try:
        state = _json(goal_state)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return {"status": "rejected", "errors": [f"invalid_goal_state:{error}"]}, 2, []
    objective = state.get("objective")
    if not isinstance(objective, dict):
        objective = {}
        errors.append("missing_objective")
    if state.get("active") is not True:
        errors.append("inactive_goal")

    resolved_contract = contract_root.resolve()
    contract_payload, contract_code, documents = ENGINE.validate_contract(resolved_contract, None)
    approval = ENGINE.approval_document(documents)
    recorded_path = Path(str(objective.get("contract_path", ""))).resolve()
    if approval is None or recorded_path != approval.path.resolve():
        errors.append("contract_path_mismatch")
    if contract_code or not contract_payload.get("executable"):
        errors.extend(contract_payload.get("errors", []))
        if contract_payload.get("approval_status") != "approved":
            errors.append("approval_required")
    if objective.get("work_id") != contract_payload.get("work_id"):
        errors.append("work_id_mismatch")
    if objective.get("contract_hash") != contract_payload.get("contract_hash"):
        errors.append("contract_hash_mismatch")

    recorded_hashes = state.get("instruction_hashes")
    if not isinstance(recorded_hashes, dict):
        recorded_hashes = {}
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = source_root / name
        if not path.is_file():
            errors.append(f"missing_instruction:{name}")
        elif recorded_hashes.get(name) != _digest(path):
            errors.append(f"instruction_hash_drift:{name}")

    if errors:
        payload: dict[str, Any] = {"status": "rejected", "errors": sorted(set(errors))}
        if "inactive_goal" in errors:
            payload["Goal declaration payload"] = _declaration_payload(state)
        return payload, 4 if any("drift" in error for error in errors) else 2, documents

    payload = {
        "status": "ready",
        "work_id": contract_payload["work_id"],
        "contract_hash": contract_payload["contract_hash"],
        "plan_order": contract_payload["plan_order"],
        "verification_order": ["targeted", "feature", "fast"],
        "live_enabled": False,
        "eval_enabled": False,
        "dirty_baseline": {
            "file_hashes": _file_hashes(source_root),
            "git_status": _git_status(source_root),
        },
    }
    return payload, 0, documents


def _plans(documents: list[Any]) -> dict[str, Any]:
    return {
        document.metadata.get("plan_id", ""): document
        for document in documents
        if document.kind == "plan" and document.metadata.get("plan_id")
    }


def next_plan(documents: list[Any], order: list[str]) -> Any | None:
    plans = _plans(documents)
    for plan_id in order:
        plan = plans[plan_id]
        if plan.metadata.get("status") != "pending":
            continue
        dependencies = json.loads(plan.metadata.get("depends_on", "[]"))
        if all(plans[dependency].metadata.get("status") == "completed" for dependency in dependencies):
            return plan
    return None


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _transition(plan: Any, expected: str, target: str) -> dict[str, Any]:
    current = plan.metadata.get("status", "")
    if current != expected:
        raise ValueError(f"invalid_transition:{current}->{target}")
    lines = plan.path.read_text(encoding="utf-8").splitlines()
    end = lines.index("---", 1)
    for index in range(1, end):
        if lines[index].startswith("status:"):
            lines[index] = f"status: {target}"
            break
    _atomic_text(plan.path, "\n".join(lines).rstrip() + "\n")
    return {"plan_id": plan.metadata["plan_id"], "transition": f"{expected}->{target}"}


def _append_evidence(contract_root: Path, record: dict[str, Any]) -> Path:
    path = contract_root / "evidence.jsonl"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    _atomic_text(path, existing + json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _blocked_document(work_id: str, plan_id: str, completed: list[str], args: argparse.Namespace) -> str:
    completed_text = ", ".join(completed) if completed else "None"
    return f"""---
work_id: {work_id}
kind: blocked
---

## Blocker

{args.reason}

## Impact

Plan {plan_id} and all dependent outcomes are paused.

## Evidence

{args.evidence}

## Attempts

{args.attempt}

## Resume Conditions

{args.resume}

## Interruption Point

Plan {plan_id} is blocked before further implementation.

## Completed Plans

{completed_text}

## Recommended Decision

{args.decision}

## Alternatives

{args.alternative}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "next", "start", "complete", "block", "evidence"):
        child = commands.add_parser(name)
        child.add_argument("--contract-root", type=Path, required=True)
        child.add_argument("--source-root", type=Path, required=True)
        child.add_argument("--goal-state", type=Path, required=True)
        if name in {"complete", "block"}:
            child.add_argument("--plan-id", required=True)
        if name == "block":
            child.add_argument("--reason", required=True)
            child.add_argument("--evidence", required=True)
            child.add_argument("--attempt", required=True)
            child.add_argument("--decision", required=True)
            child.add_argument("--alternative", required=True)
            child.add_argument("--resume", required=True)
        if name == "evidence":
            child.add_argument("--kind", required=True)
            child.add_argument("--data", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    contract_root = args.contract_root.resolve()
    payload, code, documents = preflight(contract_root, args.source_root.resolve(), args.goal_state.resolve())
    if code:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return code
    if args.command == "preflight":
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0

    plans = _plans(documents)
    try:
        if args.command == "next":
            plan = next_plan(documents, payload["plan_order"])
            result = {"status": "ready", "plan_id": plan.metadata["plan_id"] if plan else None}
        elif args.command == "start":
            plan = next_plan(documents, payload["plan_order"])
            if plan is None:
                raise ValueError("no_dependency_ready_plan")
            result = _transition(plan, "pending", "in_progress")
        elif args.command == "complete":
            if args.plan_id not in plans:
                raise ValueError(f"unknown_plan:{args.plan_id}")
            result = _transition(plans[args.plan_id], "in_progress", "completed")
        elif args.command == "evidence":
            data = json.loads(args.data)
            if not isinstance(data, dict):
                raise ValueError("evidence_data_must_be_object")
            evidence_path = _append_evidence(contract_root, {"kind": args.kind, "data": data})
            result = {"status": "recorded", "path": str(evidence_path)}
        else:
            if args.plan_id not in plans:
                raise ValueError(f"unknown_plan:{args.plan_id}")
            result = _transition(plans[args.plan_id], "in_progress", "blocked")
            completed = sorted(
                plan_id for plan_id, plan in plans.items() if plan.metadata.get("status") == "completed"
            )
            blocked_path = contract_root / "BLOCKED.md"
            _atomic_text(
                blocked_path,
                _blocked_document(payload["work_id"], args.plan_id, completed, args),
            )
            result.update({"status": "blocked", "blocked_document": str(blocked_path)})
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"status": "rejected", "errors": [str(error)]}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
