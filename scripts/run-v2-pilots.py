from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

from evidence_provenance import build_provenance


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
        dependencies = () if index == 0 else (plans[index - 1],)
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


def fixture_files(pilot_type: str) -> tuple[str, str, dict[str, str], dict[str, tuple[str, ...]]]:
    if pilot_type == "small-spec-bug-fix":
        initial = "def bounded(value, minimum):\n    return value\n"
        test = '''import unittest
from behavior import bounded

class BehaviorTests(unittest.TestCase):
    def test_enforces_minimum(self):
        self.assertEqual(bounded(2, 5), 5)
'''
        changes = {"SPEC": "def bounded(value, minimum):\n    return max(value, minimum)\n"}
        tests = {"SPEC": ("tests.test_behavior.BehaviorTests.test_enforces_minimum",)}
        return initial, test, changes, tests
    if pilot_type == "normal-goal-feature":
        initial = "def greeting(name):\n    return name\n"
        test = '''import unittest
from behavior import greeting

class BehaviorTests(unittest.TestCase):
    def test_formats_a_greeting(self):
        self.assertEqual(greeting("Ada"), "Hello, Ada!")
'''
        changes = {"P-01": "def greeting(name):\n    return f\"Hello, {name}!\"\n"}
        tests = {"P-01": ("tests.test_behavior.BehaviorTests.test_formats_a_greeting",)}
        return initial, test, changes, tests

    initial = '''def normalize(value):
    return value

def slug(value):
    return normalize(value)

def label(value):
    return f"Feature: {slug(value)}"
'''
    test = '''import unittest
from behavior import label, normalize, slug

class BehaviorTests(unittest.TestCase):
    def test_normalizes_input(self):
        self.assertEqual(normalize(" Beta Release "), "beta release")

    def test_builds_slug(self):
        self.assertEqual(slug(" Beta Release "), "beta-release")

    def test_builds_label(self):
        self.assertEqual(label(" Beta Release "), "[beta-release]")
'''
    changes = {
        "P-01": '''def normalize(value):
    return value.strip().lower()

def slug(value):
    return normalize(value)

def label(value):
    return f"Feature: {slug(value)}"
''',
        "P-02": '''def normalize(value):
    return value.strip().lower()

def slug(value):
    return normalize(value).replace(" ", "-")

def label(value):
    return f"Feature: {slug(value)}"
''',
        "P-03": '''def normalize(value):
    return value.strip().lower()

def slug(value):
    return normalize(value).replace(" ", "-")

def label(value):
    return f"[{slug(value)}]"
''',
    }
    tests = {
        "P-01": ("tests.test_behavior.BehaviorTests.test_normalizes_input",),
        "P-02": ("tests.test_behavior.BehaviorTests.test_builds_slug",),
        "P-03": ("tests.test_behavior.BehaviorTests.test_builds_label",),
    }
    return initial, test, changes, tests


def command_record(source: Path, kind: str, arguments: tuple[str, ...]) -> dict[str, Any]:
    started = time.perf_counter()
    result = subprocess.run(
        [sys.executable, *arguments], cwd=source, capture_output=True, text=True, check=False
    )
    duration = round(time.perf_counter() - started, 3)

    def summary(value: str) -> str:
        normalized = value.replace(str(source), "<pilot-repo>").replace(sys.executable, "python").strip()
        return normalized[-2000:]

    return {
        "kind": kind,
        "status": "passed" if result.returncode == 0 else "failed",
        "command": "python " + " ".join(arguments),
        "returncode": result.returncode,
        "stdout_summary": summary(result.stdout),
        "stderr_summary": summary(result.stderr),
        "duration_seconds": duration,
        "timing_mode": "measured",
        "evidence": f"measured subprocess returned {result.returncode}",
    }


def aggregate_verification(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for kind in ("Targeted", "Feature", "Fast", "Full"):
        matches = [record for record in records if record["kind"] == kind]
        checks.append(
            {
                "kind": kind,
                "status": "passed" if matches and all(item["returncode"] == 0 for item in matches) else "failed",
                "command": " && ".join(item["command"] for item in matches),
                "returncode": 0 if matches and all(item["returncode"] == 0 for item in matches) else 1,
                "evidence": f"{len(matches)} measured subprocess check(s) passed",
                "duration_seconds": round(sum(item["duration_seconds"] for item in matches), 3),
                "timing_mode": "measured",
            }
        )
    return checks


def run_pilot(output: Path, pilot_type: str, work_id: str, kind: str, expected_plans: tuple[str, ...]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"harness-v2-{pilot_type}-") as temporary:
        source = Path(temporary) / "repo"
        contract = source / ".work" / "active" / work_id
        source.mkdir(parents=True)
        initial_source, test_source, changes, plan_tests = fixture_files(pilot_type)
        (source / "AGENTS.md").write_text("# Pilot instructions\n", encoding="utf-8")
        (source / "CLAUDE.md").write_text("# Pilot instructions\n", encoding="utf-8")
        (source / ".harness").mkdir()
        (source / ".harness" / "project.yaml").write_text("handoff:\n  target: local\n", encoding="utf-8")
        (source / "behavior.py").write_text(initial_source, encoding="utf-8", newline="\n")
        tests_root = source / "tests"
        tests_root.mkdir()
        (tests_root / "__init__.py").write_text("", encoding="utf-8")
        (tests_root / "test_behavior.py").write_text(test_source, encoding="utf-8", newline="\n")
        subprocess.run(["git", "init", "-q"], cwd=source, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "add", "AGENTS.md", "CLAUDE.md", ".harness/project.yaml", "behavior.py", "tests"],
            cwd=source, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-c", "user.name=Harness Pilot", "-c", "user.email=pilot@example.invalid",
             "commit", "-qm", "seed failing pilot fixture"],
            cwd=source, check=True, capture_output=True, text=True,
        )
        write_contract(contract, work_id, kind, expected_plans)

        approved = run_json(
            str(CONTRACT_ENGINE), "approve", "--root", str(contract),
            "--work-root", str(source / ".work"),
            "--approved-at", "2026-07-19T00:00:00Z", "--approved-by", "pilot-human",
        )
        contract_document = contract / ("SPEC.md" if kind == "spec" else "GOAL.md")
        state = Path(temporary) / "goal-state.json"
        state.write_text(
            json.dumps(
                {
                    "active": True,
                    "goal_id": f"pilot-{pilot_type}",
                    "retrieved_at": "2026-07-19T00:00:00+00:00",
                    "host": "repo-local-host-adapter",
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
        full_arguments = ("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py")
        red = command_record(source, "RED", full_arguments)
        if red["returncode"] == 0 or "AssertionError" not in red["stderr_summary"]:
            raise RuntimeError(f"pilot {pilot_type} did not reproduce an assertion RED: {red}")

        command_evidence: list[dict[str, Any]] = []
        implementation_cycles: list[dict[str, Any]] = []
        completed_tests: list[str] = []
        for plan_id in plans:
            selected = runtime_command(contract, source, state, "next")
            if selected.get("plan_id") != plan_id:
                raise RuntimeError(f"DAG selected {selected.get('plan_id')!r}, expected {plan_id!r}")
            runtime_command(contract, source, state, "start")
            (source / "behavior.py").write_text(changes[plan_id], encoding="utf-8", newline="\n")
            completed_tests.extend(plan_tests[plan_id])
            check_definitions = (
                ("Targeted", ("-m", "unittest", *plan_tests[plan_id])),
                ("Feature", ("-m", "unittest", *completed_tests)),
                ("Fast", ("-m", "compileall", "-q", "behavior.py", "tests")),
            )
            plan_checks: list[dict[str, Any]] = []
            for check_kind, arguments in check_definitions:
                check = command_record(source, check_kind, arguments)
                if check["returncode"] != 0:
                    raise RuntimeError(f"{pilot_type} {plan_id} {check_kind} failed: {check}")
                plan_checks.append(check)
                command_evidence.append(check)
                runtime_command(
                    contract, source, state, "evidence", "--kind", check_kind.lower(),
                    "--data", json.dumps(check, sort_keys=True),
                )
            runtime_command(contract, source, state, "complete", "--plan-id", plan_id)
            implementation_cycles.append(
                {
                    "plan_id": plan_id,
                    "source_change": {
                        "path": "behavior.py",
                        "description": f"implemented the approved {plan_id} behavior slice",
                    },
                    "checks": plan_checks,
                }
            )

        full = command_record(source, "Full", full_arguments)
        if full["returncode"] != 0:
            raise RuntimeError(f"{pilot_type} Full failed: {full}")
        command_evidence.append(full)
        runtime_command(
            contract, source, state, "evidence", "--kind", "full",
            "--data", json.dumps(full, sort_keys=True),
        )
        verification = aggregate_verification(command_evidence)
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
            "execution_adapter": "repo-local-host-adapter",
            "live_goal": False,
            "timing_mode": "measured",
            "question_count": 0,
            "interruptions": 0,
            "plans": list(plans),
            "design_approved": approved.get("approval_status") == "approved",
            "verification": verification,
            "command_evidence": command_evidence,
            "implementation_cycles": implementation_cycles,
            "regression_evidence": {"red": red, "green": full},
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
        "These are real temporary implementation cycles through a repo-local host adapter, not live host `/goal` runs.",
        "Each pilot captures an assertion RED, explicit Plan source changes, measured subprocess checks, Contract state transitions, and close/archive output.",
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
                f"- RED / final GREEN: {pilot['regression_evidence']['red']['status']} / {pilot['regression_evidence']['green']['status']}",
                f"- Measured command checks: {len(pilot['command_evidence'])}",
                f"- Human review: [{pilot['human_review_artifact']}]({pilot['human_review_artifact']})",
                "",
            ]
        )
    return "\n".join(lines)


def _duration_bucket(seconds: float) -> str:
    if seconds < 1:
        return "under-1s"
    if seconds < 5:
        return "1-5s"
    if seconds < 30:
        return "5-30s"
    return "30s-or-more"


def normalized_baseline(value: Any) -> Any:
    if isinstance(value, list):
        return [normalized_baseline(item) for item in value]
    if not isinstance(value, dict):
        return value
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if key == "duration_seconds":
            normalized["duration_bucket"] = _duration_bucket(float(item))
        elif key == "generated_at":
            normalized[key] = "normalized-at-baseline-update"
        elif key in {"cwd", "source_package"} and isinstance(item, str):
            normalized[key] = "<repository-root>"
        else:
            normalized[key] = normalized_baseline(item)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Run three deterministic Harness V2 repository-local pilots.")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()
    if args.output_dir is not None and args.update_baseline:
        parser.error("--output-dir and --update-baseline are mutually exclusive")
    if args.update_baseline:
        output = (ROOT / "docs" / "pilots").resolve()
    elif args.output_dir is not None:
        output = args.output_dir.resolve()
    else:
        output = Path(tempfile.mkdtemp(prefix="harness-v2-pilot-evidence-")).resolve()
    provenance = build_provenance(
        ROOT,
        command=[sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        source_type="local_checkout",
        source_package=ROOT.as_posix(),
        result="pending",
        unverified_checks=["remote_github_update"],
    )
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
        provenance["result"] = report["result"]
        provenance["evidence_kind"] = "pilot_execution"
        report["evidence"] = provenance
        serialized_report = normalized_baseline(report) if args.update_baseline else report
        (output / "harness-v2-pilots.json").write_text(
            json.dumps(serialized_report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        (output / "harness-v2-pilots.md").write_text(
            render_markdown(serialized_report), encoding="utf-8", newline="\n"
        )
        print(f"{'PASS' if passed else 'FAIL'}: {sum(p['result_success'] for p in pilots)}/3 Harness V2 pilots")
        print(f"Evidence directory: {output}")
        return 0 if passed else 1
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
