# Generated file. Do not edit directly.
# Source: authoring/scripts/goal_runtime.py
# Source-SHA256: 5133e5a141a68487e7e8a62ece96bf44c968df4298f6cc62289771ab7e922586

#!/usr/bin/env python3
"""Execute an approved Harness V2 contract inside a human-declared Goal."""

from __future__ import annotations

import argparse
from datetime import datetime
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
RUNTIME_STATUSES = {"pending", "in_progress", "completed", "blocked"}
BLOCK_TRANSACTION = ".block-transaction.json"
RESUME_TRANSACTION = ".resume-transaction.json"


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected_object")
    return value


def _objective_fingerprint(state: dict[str, Any]) -> str:
    encoded = json.dumps(
        {"goal_id": state["goal_id"], "objective": state["objective"]},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def _validate_goal_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("active") is not True:
        errors.append("inactive_goal")
    for field in ("goal_id", "retrieved_at", "host"):
        if not isinstance(state.get(field), str) or not state[field].strip():
            errors.append(f"invalid_goal_state:{field}")
    if isinstance(state.get("retrieved_at"), str) and state["retrieved_at"].strip():
        try:
            datetime.fromisoformat(state["retrieved_at"])
        except ValueError:
            errors.append("invalid_goal_state:retrieved_at")
    objective = state.get("objective")
    if not isinstance(objective, dict):
        errors.append("missing_objective")
    else:
        for field in ("work_id", "contract_path", "contract_hash"):
            if not isinstance(objective.get(field), str) or not objective[field].strip():
                errors.append(f"invalid_goal_state:objective.{field}")
    return errors


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


def _is_spec_only(documents: list[Any]) -> bool:
    return any(document.kind == "spec" for document in documents) and not any(
        document.kind == "plan" for document in documents
    )


def _spec_status(contract_root: Path) -> str:
    path = contract_root / "runtime-state.json"
    if not path.exists():
        return "pending"
    state = _json(path)
    status = state.get("SPEC")
    if set(state) != {"SPEC"} or status not in RUNTIME_STATUSES:
        raise ValueError("invalid_runtime_state")
    return status


def _baseline_path(goal_state: Path) -> Path:
    return goal_state.with_name(goal_state.name + ".dirty-baseline.json")


def _load_or_create_baseline(goal_state: Path, source_root: Path, state: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    path = _baseline_path(goal_state)
    fingerprint = _objective_fingerprint(state)
    if path.exists():
        try:
            baseline = _json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return None, [f"invalid_dirty_baseline:{error}"]
        if baseline.get("goal_id") != state["goal_id"] or baseline.get("objective_fingerprint") != fingerprint:
            return None, ["dirty_baseline_identity_mismatch"]
        dirty = baseline.get("dirty_baseline")
        if not isinstance(dirty, dict) or not isinstance(dirty.get("file_hashes"), dict) or not isinstance(dirty.get("git_status"), list):
            return None, ["invalid_dirty_baseline:schema"]
        return baseline, []
    baseline = {
        "goal_id": state["goal_id"],
        "objective_fingerprint": fingerprint,
        "dirty_baseline": {"file_hashes": _file_hashes(source_root), "git_status": _git_status(source_root)},
    }
    _atomic_text(path, json.dumps(baseline, ensure_ascii=False, sort_keys=True) + "\n")
    return baseline, []


def preflight(contract_root: Path, source_root: Path, goal_state: Path, *, allow_block_recovery: bool = False, allow_resume_recovery: bool = False) -> tuple[dict[str, Any], int, list[Any]]:
    errors: list[str] = []
    try:
        state = _json(goal_state)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return {"status": "rejected", "errors": [f"invalid_goal_state:{error}"]}, 2, []
    errors.extend(_validate_goal_state(state))
    objective = state.get("objective")
    if not isinstance(objective, dict):
        objective = {}
        errors.append("missing_objective")
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

    plan_order = contract_payload["plan_order"]
    if _is_spec_only(documents):
        plan_order = ["SPEC"]
        try:
            _spec_status(resolved_contract)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            errors.append(str(error))
    else:
        in_progress = [
            document for document in documents
            if document.kind == "plan" and document.metadata.get("status") == "in_progress"
        ]
        if len(in_progress) > 1:
            errors.append("multiple_in_progress_plans")

    if (resolved_contract / BLOCK_TRANSACTION).exists() and not allow_block_recovery:
        errors.append("incomplete_block_transaction")
    if (resolved_contract / RESUME_TRANSACTION).exists() and not allow_resume_recovery:
        errors.append("incomplete_resume_transaction")

    if errors:
        payload: dict[str, Any] = {"status": "rejected", "errors": sorted(set(errors))}
        if "inactive_goal" in errors:
            payload["Goal declaration payload"] = _declaration_payload(state)
        return payload, 4 if any("drift" in error for error in errors) else 2, documents

    try:
        baseline, baseline_errors = _load_or_create_baseline(goal_state, source_root, state)
    except OSError as error:
        baseline, baseline_errors = None, [f"dirty_baseline_write_failed:{error}"]
    if baseline_errors:
        return {"status": "rejected", "errors": baseline_errors}, 2, documents
    assert baseline is not None
    payload = {
        "status": "ready",
        "work_id": contract_payload["work_id"],
        "contract_hash": contract_payload["contract_hash"],
        "plan_order": plan_order,
        "verification_order": ["targeted", "feature", "fast"],
        "live_enabled": False,
        "eval_enabled": False,
        "dirty_baseline": baseline["dirty_baseline"],
        "dirty_baseline_path": str(_baseline_path(goal_state)),
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


def _transition_spec(contract_root: Path, expected: str, target: str) -> dict[str, Any]:
    current = _spec_status(contract_root)
    if current != expected:
        raise ValueError(f"invalid_transition:{current}->{target}")
    _atomic_text(
        contract_root / "runtime-state.json",
        json.dumps({"SPEC": target}, sort_keys=True) + "\n",
    )
    return {"plan_id": "SPEC", "transition": f"{expected}->{target}"}


def _append_evidence(contract_root: Path, record: dict[str, Any]) -> Path:
    path = contract_root / "evidence.jsonl"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    _atomic_text(path, existing + json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _append_evidence_once(contract_root: Path, record: dict[str, Any]) -> Path:
    path = contract_root / "evidence.jsonl"
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if encoded not in existing:
        _atomic_text(path, "\n".join([*existing, encoded]).rstrip() + "\n")
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


def _recovery_blocked_document(work_id: str, plan_id: str) -> str:
    return f"""---
work_id: {work_id}
kind: blocked
---

## Blocker

Recovered an interrupted block transaction.

## Impact

Plan {plan_id} remains paused.

## Evidence

The durable transaction marker proved the interrupted operation.

## Attempts

The explicit recovery command completed safe ordering.

## Resume Conditions

Resolve the original blocker and use explicit approved resume.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "next", "start", "complete", "block", "resume", "recover-block", "evidence"):
        child = commands.add_parser(name)
        child.add_argument("--contract-root", type=Path, required=True)
        child.add_argument("--source-root", type=Path, required=True)
        child.add_argument("--goal-state", type=Path, required=True)
        if name in {"complete", "block"}:
            child.add_argument("--plan-id", required=True)
        if name == "resume":
            child.add_argument("--plan-id", required=True)
            child.add_argument("--resolution-evidence", required=True)
            child.add_argument("--approve-resume", action="store_true")
        if name == "recover-block":
            child.add_argument("--approve-recovery", action="store_true")
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
    payload, code, documents = preflight(
        contract_root, args.source_root.resolve(), args.goal_state.resolve(),
        allow_block_recovery=args.command == "recover-block",
        allow_resume_recovery=args.command == "resume",
    )
    if code:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return code
    if args.command == "preflight":
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0

    plans = _plans(documents)
    spec_only = _is_spec_only(documents)
    try:
        if args.command == "recover-block":
            if not args.approve_recovery:
                raise ValueError("recovery_approval_required")
            marker_path = contract_root / BLOCK_TRANSACTION
            if not marker_path.is_file():
                raise ValueError("no_incomplete_block_transaction")
            marker = _json(marker_path)
            plan_id = str(marker.get("plan_id", ""))
            if plan_id != "SPEC" and plan_id not in plans:
                raise ValueError(f"unknown_plan:{plan_id}")
            blocked_path = contract_root / "BLOCKED.md"
            if not blocked_path.exists():
                _atomic_text(
                    blocked_path,
                    str(marker.get("blocked_text") or _recovery_blocked_document(payload["work_id"], plan_id)),
                )
            if spec_only and plan_id == "SPEC":
                current = _spec_status(contract_root)
                if current == "in_progress":
                    result = _transition_spec(contract_root, "in_progress", "blocked")
                elif current == "blocked":
                    result = {"plan_id": "SPEC", "transition": "blocked->blocked"}
                else:
                    raise ValueError("invalid_block_recovery_state")
            else:
                current = plans[plan_id].metadata.get("status")
                if current == "in_progress":
                    result = _transition(plans[plan_id], "in_progress", "blocked")
                elif current == "blocked":
                    result = {"plan_id": plan_id, "transition": "blocked->blocked"}
                else:
                    raise ValueError("invalid_block_recovery_state")
            marker_path.unlink()
            result.update({"status": "blocked", "blocked_document": str(blocked_path), "recovered": True})
        elif args.command == "next":
            if spec_only:
                result = {
                    "status": "ready",
                    "plan_id": "SPEC" if _spec_status(contract_root) == "pending" else None,
                }
            else:
                plan = next_plan(documents, payload["plan_order"])
                result = {"status": "ready", "plan_id": plan.metadata["plan_id"] if plan else None}
        elif args.command == "start":
            if spec_only:
                result = _transition_spec(contract_root, "pending", "in_progress")
            else:
                if any(plan.metadata.get("status") == "in_progress" for plan in plans.values()):
                    raise ValueError("plan_already_in_progress")
                plan = next_plan(documents, payload["plan_order"])
                if plan is None:
                    raise ValueError("no_dependency_ready_plan")
                result = _transition(plan, "pending", "in_progress")
        elif args.command == "complete":
            if spec_only and args.plan_id == "SPEC":
                result = _transition_spec(contract_root, "in_progress", "completed")
            elif args.plan_id not in plans:
                raise ValueError(f"unknown_plan:{args.plan_id}")
            else:
                result = _transition(plans[args.plan_id], "in_progress", "completed")
        elif args.command == "evidence":
            data = json.loads(args.data)
            if not isinstance(data, dict):
                raise ValueError("evidence_data_must_be_object")
            evidence_path = _append_evidence(contract_root, {"kind": args.kind, "data": data})
            result = {"status": "recorded", "path": str(evidence_path)}
        elif args.command == "resume":
            if not args.approve_resume:
                raise ValueError("resume_approval_required")
            if not args.resolution_evidence.strip():
                raise ValueError("resolution_evidence_required")
            marker_path = contract_root / RESUME_TRANSACTION
            marker = _json(marker_path) if marker_path.is_file() else None
            if marker is not None and (
                marker.get("plan_id") != args.plan_id
                or marker.get("resolution_evidence") != args.resolution_evidence
            ):
                raise ValueError("resume_transaction_mismatch")
            blocked_path = contract_root / "BLOCKED.md"
            resolved_path = contract_root / "resolved-blocks" / f"{args.plan_id}.md"
            if marker is None:
                if not blocked_path.is_file():
                    raise ValueError("blocked_document_required")
                if resolved_path.exists():
                    raise ValueError("resolved_block_evidence_exists")
                resolved_text = blocked_path.read_text(encoding="utf-8") + f"\n## Resolution Evidence\n\n{args.resolution_evidence}\n"
                _atomic_text(marker_path, json.dumps({
                    "plan_id": args.plan_id,
                    "resolution_evidence": args.resolution_evidence,
                    "resolved_text": resolved_text,
                }, ensure_ascii=False, sort_keys=True) + "\n")
            else:
                resolved_text = str(marker.get("resolved_text", ""))
                if not resolved_text and resolved_path.is_file():
                    resolved_text = resolved_path.read_text(encoding="utf-8")
                if not resolved_text:
                    raise ValueError("invalid_resume_transaction")
            if not resolved_path.exists():
                _atomic_text(resolved_path, resolved_text)
            elif resolved_path.read_text(encoding="utf-8") != resolved_text:
                raise ValueError("resolved_block_evidence_mismatch")
            _append_evidence_once(
                contract_root,
                {"kind": "resolved_block", "data": {"plan_id": args.plan_id, "evidence": args.resolution_evidence}},
            )
            if spec_only and args.plan_id == "SPEC":
                current = _spec_status(contract_root)
                if current not in {"blocked", "pending"}:
                    raise ValueError(f"invalid_resume_recovery_state:{current}")
                result = (
                    _transition_spec(contract_root, "blocked", "pending")
                    if current == "blocked"
                    else {"plan_id": "SPEC", "transition": "pending->pending"}
                )
            elif args.plan_id not in plans:
                raise ValueError(f"unknown_plan:{args.plan_id}")
            else:
                current = plans[args.plan_id].metadata.get("status")
                if current not in {"blocked", "pending"}:
                    raise ValueError(f"invalid_resume_recovery_state:{current}")
                result = (
                    _transition(plans[args.plan_id], "blocked", "pending")
                    if current == "blocked"
                    else {"plan_id": args.plan_id, "transition": "pending->pending"}
                )
            if blocked_path.exists():
                blocked_path.unlink()
            marker_path.unlink()
            result.update({"status": "resumed", "resolved_block": str(resolved_path)})
        else:
            if not (spec_only and args.plan_id == "SPEC") and args.plan_id not in plans:
                raise ValueError(f"unknown_plan:{args.plan_id}")
            completed = [] if spec_only else sorted(
                plan_id for plan_id, plan in plans.items() if plan.metadata.get("status") == "completed"
            )
            blocked_path = contract_root / "BLOCKED.md"
            blocked_text = _blocked_document(payload["work_id"], args.plan_id, completed, args)
            marker_path = contract_root / BLOCK_TRANSACTION
            _atomic_text(
                marker_path,
                json.dumps({"plan_id": args.plan_id, "blocked_document": "BLOCKED.md", "blocked_text": blocked_text}, ensure_ascii=False, sort_keys=True) + "\n",
            )
            _atomic_text(blocked_path, blocked_text)
            if spec_only and args.plan_id == "SPEC":
                result = _transition_spec(contract_root, "in_progress", "blocked")
            else:
                result = _transition(plans[args.plan_id], "in_progress", "blocked")
            marker_path.unlink()
            result.update({"status": "blocked", "blocked_document": str(blocked_path)})
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"status": "rejected", "errors": [str(error)]}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
