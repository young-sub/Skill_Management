from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ENGINE = ROOT / "authoring" / "scripts" / "contract_engine.py"
GOAL_RUNTIME = ROOT / "authoring" / "scripts" / "goal_runtime.py"
CLOSE_GOAL = ROOT / "authoring" / "scripts" / "close_goal.py"
PILOTS = (
    ("small-spec-bug-fix", "W-PILOT-SMALL", "spec", ("SPEC",)),
    ("normal-goal-feature", "W-PILOT-NORMAL", "goal", ("P-01",)),
    ("multi-plan-dag-feature", "W-PILOT-DAG", "goal", ("P-01", "P-02", "P-03")),
)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(*arguments: str, cwd: Path | None = None) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, *arguments], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(arguments)}\n{result.stdout}{result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"command returned invalid JSON: {' '.join(arguments)}\n{result.stdout}") from error


def spec_document(work_id: str) -> str:
    return f"""---
work_id: {work_id}
kind: spec
approval.status: pending
approval.approved_at:
approval.approved_by:
approval.contract_hash:
---

## Context

An isolated pilot repository contains a reproducible regression.

## Problem

Repair the small deterministic regression.

## User Value

Users receive the expected result.

## Scope

One targeted bug fix.

## Non-Goals

No live provider or network execution.

## Constraints

Use repository-local helpers only.

## Acceptance Criteria

The implicit Plan completes and archives successfully.
"""


def goal_document(work_id: str, plans: tuple[str, ...]) -> str:
    return f"""---
work_id: {work_id}
kind: goal
approval.status: pending
approval.approved_at:
approval.approved_by:
approval.contract_hash:
---

## Objective

Deliver the {len(plans)}-Plan isolated feature pilot.

## Observable Outcomes

Every declared Plan completes in dependency order.

## Plans

{', '.join(plans)}.

## Hard Stops

Stop on contract or instruction drift.

## Verification

Record Targeted, Feature, Fast, and Full checks.

## Completion Criteria

All Plans complete and Completion Review archives the result.
"""


def plan_document(work_id: str, plan_id: str, dependencies: tuple[str, ...]) -> str:
    depends_on = json.dumps(list(dependencies))
    return f"""---
work_id: {work_id}
kind: plan
plan_id: {plan_id}
status: pending
depends_on: {depends_on}
---

## Slice

Implement {plan_id}.

## Outcomes

{plan_id} is observable.

## Changes

Add the isolated pilot behavior.

## Tests

Run the targeted pilot check.

## Verification

Record deterministic verification evidence.

## Evidence

Recorded by the runtime helper.
"""


def write_contract(contract: Path, work_id: str, kind: str, plans: tuple[str, ...]) -> None:
    contract.mkdir(parents=True)
    if kind == "spec":
        (contract / "SPEC.md").write_text(spec_document(work_id), encoding="utf-8", newline="\n")
        return
    (contract / "GOAL.md").write_text(goal_document(work_id, plans), encoding="utf-8", newline="\n")
    plan_root = contract / "plans"
    plan_root.mkdir()
    for index, plan_id in enumerate(plans):
        dependencies = () if index == 0 else ((plans[0],) if len(plans) > 1 else ())
        (plan_root / f"{plan_id}.md").write_text(
            plan_document(work_id, plan_id, dependencies), encoding="utf-8", newline="\n"
        )


def runtime_command(contract: Path, source: Path, state: Path, command: str, *extra: str) -> dict[str, Any]:
    return run_json(
        str(GOAL_RUNTIME), command,
        "--contract-root", str(contract),
        "--source-root", str(source),
        "--goal-state", str(state),
        *extra,
    )


def verification_records(plan_count: int) -> list[dict[str, Any]]:
    seconds = (0.02, 0.04, 0.08, 0.16)
    return [
        {
            "kind": kind,
            "status": "passed",
            "count": plan_count,
            "duration_seconds": duration * plan_count,
            "timing_mode": "simulated",
        }
        for kind, duration in zip(("Targeted", "Feature", "Fast", "Full"), seconds)
    ]


def run_pilot(output: Path, pilot_type: str, work_id: str, kind: str, expected_plans: tuple[str, ...]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"harness-v2-{pilot_type}-") as temporary:
        source = Path(temporary) / "repo"
        contract = source / ".work" / "active" / work_id
        source.mkdir(parents=True)
        (source / "AGENTS.md").write_text("# Pilot instructions\n", encoding="utf-8")
        (source / "CLAUDE.md").write_text("# Pilot instructions\n", encoding="utf-8")
        (source / ".harness").mkdir()
        (source / ".harness" / "project.yaml").write_text("handoff:\n  target: local\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=source, check=True)
        subprocess.run(["git", "add", "AGENTS.md", "CLAUDE.md"], cwd=source, check=True)
        write_contract(contract, work_id, kind, expected_plans)

        approved = run_json(
            str(CONTRACT_ENGINE), "approve", "--root", str(contract),
            "--approved-at", "2026-07-19T00:00:00Z", "--approved-by", "pilot-human",
        )
        contract_document = contract / ("SPEC.md" if kind == "spec" else "GOAL.md")
        state = Path(temporary) / "goal-state.json"
        state.write_text(
            json.dumps(
                {
                    "active": True,
                    "objective": {
                        "work_id": work_id,
                        "contract_path": str(contract_document.resolve()),
                        "contract_hash": approved["contract_hash"],
                    },
                    "instruction_hashes": {
                        "AGENTS.md": digest(source / "AGENTS.md"),
                        "CLAUDE.md": digest(source / "CLAUDE.md"),
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        preflight = runtime_command(contract, source, state, "preflight")
        plans = tuple(preflight["plan_order"])
        if plans != expected_plans:
            raise RuntimeError(f"unexpected Plan order for {pilot_type}: {plans!r}")
        for plan_id in plans:
            selected = runtime_command(contract, source, state, "next")
            if selected.get("plan_id") != plan_id:
                raise RuntimeError(f"DAG selected {selected.get('plan_id')!r}, expected {plan_id!r}")
            runtime_command(contract, source, state, "start")
            for check in verification_records(1):
                runtime_command(
                    contract, source, state, "evidence", "--kind", check["kind"].lower(),
                    "--data", json.dumps(check, sort_keys=True),
                )
            runtime_command(contract, source, state, "complete", "--plan-id", plan_id)

        verification = verification_records(len(plans))
        findings_path = Path(temporary) / "findings.json"
        verification_path = Path(temporary) / "verification.json"
        findings_path.write_text(json.dumps({"findings": []}), encoding="utf-8")
        verification_path.write_text(json.dumps({"checks": verification}), encoding="utf-8")
        closed = run_json(
            str(CLOSE_GOAL), "--contract-root", str(contract), "--source-root", str(source),
            "--findings", str(findings_path), "--verification", str(verification_path),
            "--current-month", "2026-07",
        )
        archive = source / ".work" / "archive" / "2026-07" / work_id
        artifact_relative = Path("artifacts") / f"{pilot_type}-completion-review.html"
        artifact_target = output / artifact_relative
        artifact_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archive / "artifacts" / "completion-review.html", artifact_target)
        active_leftovers = sorted(path.name for path in (source / ".work" / "active").glob("*"))
        tracked = subprocess.run(
            ["git", "grep", "-l", r"\.work/"], cwd=source, capture_output=True, text=True, check=False
        )
        worktree_output = subprocess.run(
            ["git", "worktree", "list", "--porcelain"], cwd=source, capture_output=True, text=True, check=True
        ).stdout
        observed_worktrees = [line.removeprefix("worktree ") for line in worktree_output.splitlines() if line.startswith("worktree ")]
        residuals = [path for path in observed_worktrees if Path(path).resolve() != source.resolve()]

        return {
            "type": pilot_type,
            "work_id": work_id,
            "execution_adapter": "repo-local-helper-simulation",
            "live_goal": False,
            "timing_mode": "simulated",
            "question_count": 0,
            "interruptions": 0,
            "plans": list(plans),
            "design_approved": approved.get("approval_status") == "approved",
            "verification": verification,
            "result_success": (archive / "RESULT.md").is_file() and closed.get("status") == "complete",
            "archive_success": archive.is_dir() and not contract.exists(),
            "instruction_drift": (source / "AGENTS.md").read_bytes() != (source / "CLAUDE.md").read_bytes(),
            "work_links": sorted(tracked.stdout.splitlines()) if tracked.returncode == 0 else [],
            "active_leftovers": active_leftovers,
            "worktree_residuals": residuals,
            "human_review_artifact": artifact_relative.as_posix(),
        }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Harness V2 Pilot Report",
        "",
        "These are deterministic repo-local helper simulations, not live host `/goal` runs.",
        "Timing values are simulated and labeled in the JSON record.",
        "",
        f"Overall result: **{report['result']}**",
        "",
    ]
    for pilot in report["pilots"]:
        lines.extend(
            [
                f"## {pilot['type']}",
                "",
                f"- Plans: {', '.join(pilot['plans'])}",
                f"- Questions / interruptions: {pilot['question_count']} / {pilot['interruptions']}",
                f"- Result / archive: {pilot['result_success']} / {pilot['archive_success']}",
                f"- Human review: [{pilot['human_review_artifact']}]({pilot['human_review_artifact']})",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run three deterministic Harness V2 repository-local pilots.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "pilots")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        pilots = [run_pilot(output, *definition) for definition in PILOTS]
        passed = all(
            pilot["design_approved"] and pilot["result_success"] and pilot["archive_success"]
            and not pilot["instruction_drift"] and not pilot["work_links"]
            and not pilot["active_leftovers"] and not pilot["worktree_residuals"]
            for pilot in pilots
        )
        report = {
            "schema_version": 1,
            "candidate_version": "2.0.0",
            "recorded_date": "2026-07-19",
            "result": "passed" if passed else "failed",
            "pilots": pilots,
        }
        (output / "harness-v2-pilots.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        (output / "harness-v2-pilots.md").write_text(
            render_markdown(report), encoding="utf-8", newline="\n"
        )
        print(f"{'PASS' if passed else 'FAIL'}: {sum(p['result_success'] for p in pilots)}/3 Harness V2 pilots")
        return 0 if passed else 1
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
