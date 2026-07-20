import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME = REPO_ROOT / "skills" / "execute-codex-goal" / "scripts" / "goal_runtime.py"
CONTRACT_ENGINE = REPO_ROOT / "authoring" / "scripts" / "contract_engine.py"
CONTRACT_FIXTURE = Path(__file__).parent / "fixtures" / "contracts" / "multi"
SMALL_CONTRACT_FIXTURE = Path(__file__).parent / "fixtures" / "contracts" / "small"
SOURCE_FIXTURE = Path(__file__).parent / "fixtures" / "runtime" / "source"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class RuntimeCase:
    def __init__(self, parent: Path, contract_fixture: Path = CONTRACT_FIXTURE):
        self.root = parent
        self.contract = parent / "contract"
        self.source = parent / "source"
        shutil.copytree(contract_fixture, self.contract)
        shutil.copytree(SOURCE_FIXTURE, self.source)
        approved = subprocess.run(
            [
                sys.executable,
                str(CONTRACT_ENGINE),
                "approve",
                "--root",
                str(self.contract),
                "--work-root",
                str(parent),
                "--approved-at",
                "2026-07-19T18:00:00+09:00",
                "--approved-by",
                "human",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if approved.returncode:
            raise AssertionError(approved.stdout + approved.stderr)
        approved_payload = json.loads(approved.stdout)
        self.contract_hash = approved_payload["contract_hash"]
        self.work_id = approved_payload["work_id"]
        self.contract_document = self.contract / ("SPEC.md" if (self.contract / "SPEC.md").is_file() else "GOAL.md")
        self.state = parent / "goal-state.json"
        self.write_state(active=True)

    def write_state(self, *, active: bool, work_id: str | None = None, contract_hash: str | None = None, contract_path: str | None = None, goal_id: str = "goal-1", retrieved_at: str = "2026-07-19T18:00:00+09:00", host: str = "codex.get_goal") -> None:
        payload = {
            "active": active,
            "goal_id": goal_id,
            "retrieved_at": retrieved_at,
            "host": host,
            "objective": {
                "work_id": work_id or self.work_id,
                "contract_path": contract_path or str(self.contract_document.resolve()),
                "contract_hash": contract_hash or self.contract_hash,
            },
            "instruction_hashes": {
                "AGENTS.md": digest(self.source / "AGENTS.md"),
                "CLAUDE.md": digest(self.source / "CLAUDE.md"),
            },
        }
        self.state.write_text(json.dumps(payload), encoding="utf-8")

    def run(self, command: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(RUNTIME),
                command,
                "--contract-root",
                str(self.contract),
                "--source-root",
                str(self.source),
                "--goal-state",
                str(self.state),
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )


class GoalExecutionTests(unittest.TestCase):
    def test_spec_only_contract_executes_implicit_plan_without_contract_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir), SMALL_CONTRACT_FIXTURE)
            spec_hash = digest(runtime.contract_document)
            runtime_state = runtime.contract / "runtime-state.json"

            preflight = runtime.run("preflight")
            selected = runtime.run("next")

            self.assertEqual(preflight.returncode, 0, preflight.stdout)
            self.assertEqual(json.loads(preflight.stdout)["plan_order"], ["SPEC"])
            self.assertEqual(selected.returncode, 0, selected.stdout)
            self.assertEqual(json.loads(selected.stdout)["plan_id"], "SPEC")
            self.assertFalse(runtime_state.exists())

            started = runtime.run("start")
            self.assertEqual(started.returncode, 0, started.stdout)
            self.assertEqual(json.loads(started.stdout)["transition"], "pending->in_progress")
            self.assertEqual(json.loads(runtime_state.read_text(encoding="utf-8")), {"SPEC": "in_progress"})

            after_start = runtime.run("preflight")
            completed = runtime.run("complete", "--plan-id", "SPEC")

            self.assertEqual(json.loads(runtime_state.read_text(encoding="utf-8")), {"SPEC": "completed"})
            self.assertEqual(after_start.returncode, 0, after_start.stdout)
            self.assertEqual(json.loads(after_start.stdout)["contract_hash"], runtime.contract_hash)
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertEqual(digest(runtime.contract_document), spec_hash)

    def test_spec_only_hard_stop_blocks_implicit_plan_and_writes_blocked_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir), SMALL_CONTRACT_FIXTURE)
            self.assertEqual(runtime.run("start").returncode, 0)

            blocked = runtime.run(
                "block",
                "--plan-id",
                "SPEC",
                "--reason",
                "missing required environment",
                "--evidence",
                "targeted test cannot start",
                "--attempt",
                "confirmed executable is absent",
                "--decision",
                "provide the approved executable",
                "--alternative",
                "use an approved fixture with reduced fidelity",
                "--resume",
                "rerun preflight then retry SPEC",
            )

            self.assertEqual(blocked.returncode, 0, blocked.stdout)
            state = json.loads(runtime.contract.joinpath("runtime-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state, {"SPEC": "blocked"})
            document = runtime.contract.joinpath("BLOCKED.md").read_text(encoding="utf-8")
            self.assertIn("Plan SPEC is blocked", document)

    def test_inactive_or_mismatched_goal_preflight_has_zero_mutations(self) -> None:
        cases = (
            ("inactive", {"active": False}),
            ("work", {"active": True, "work_id": "W-wrong"}),
            ("hash", {"active": True, "contract_hash": "sha256:wrong"}),
            ("path", {"active": True, "contract_path": "missing-contract"}),
        )
        for name, values in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                runtime = RuntimeCase(Path(temp_dir))
                runtime.write_state(**values)
                before = tree_snapshot(runtime.root)

                result = runtime.run("start")

                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(tree_snapshot(runtime.root), before)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["status"], "rejected")
                if name == "inactive":
                    self.assertIn("Goal declaration payload", payload)

    def test_instruction_drift_rejects_before_any_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            runtime.source.joinpath("AGENTS.md").write_text("drift\n", encoding="utf-8")
            before = tree_snapshot(runtime.root)

            result = runtime.run("start")

            self.assertEqual(result.returncode, 4, result.stdout)
            self.assertIn("instruction_hash_drift:AGENTS.md", json.loads(result.stdout)["errors"])
            self.assertEqual(tree_snapshot(runtime.root), before)

    def test_unapproved_contract_rejects_before_any_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            goal = runtime.contract / "GOAL.md"
            goal.write_text(
                goal.read_text(encoding="utf-8").replace(
                    "approval.status: approved", "approval.status: pending"
                ),
                encoding="utf-8",
                newline="\n",
            )
            before = tree_snapshot(runtime.root)

            result = runtime.run("start")

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("approval_required", json.loads(result.stdout)["errors"])
            self.assertEqual(tree_snapshot(runtime.root), before)

    def test_preflight_records_read_only_dirty_baseline_and_safe_verification_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            runtime.source.joinpath("existing.txt").write_text("preserve me\n", encoding="utf-8")
            result = runtime.run("preflight")

            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["verification_order"], ["targeted", "feature", "fast"])
            self.assertFalse(payload["live_enabled"])
            self.assertFalse(payload["eval_enabled"])
            self.assertIn("existing.txt", payload["dirty_baseline"]["file_hashes"])
            self.assertIn("git_status", payload["dirty_baseline"])
            baseline_path = Path(payload["dirty_baseline_path"])
            self.assertTrue(baseline_path.is_file())
            original_baseline = baseline_path.read_text(encoding="utf-8")

            runtime.source.joinpath("later.txt").write_text("later\n", encoding="utf-8")
            second = json.loads(runtime.run("preflight").stdout)
            self.assertEqual(Path(second["dirty_baseline_path"]).read_text(encoding="utf-8"), original_baseline)
            self.assertNotIn("later.txt", second["dirty_baseline"]["file_hashes"])

            source_before = tree_snapshot(runtime.source)
            self.assertEqual(runtime.run("start").returncode, 0)
            self.assertEqual(tree_snapshot(runtime.source), source_before)

    def test_goal_state_schema_and_baseline_identity_fail_closed(self) -> None:
        for field in ("goal_id", "retrieved_at", "host"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp_dir:
                runtime = RuntimeCase(Path(temp_dir))
                payload = json.loads(runtime.state.read_text(encoding="utf-8"))
                payload.pop(field)
                runtime.state.write_text(json.dumps(payload), encoding="utf-8")
                result = runtime.run("preflight")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"invalid_goal_state:{field}", json.loads(result.stdout)["errors"])

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            self.assertEqual(runtime.run("preflight").returncode, 0)
            runtime.write_state(active=True, goal_id="different-goal")
            result = runtime.run("start")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dirty_baseline_identity_mismatch", json.loads(result.stdout)["errors"])

    def test_only_one_plan_may_be_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            p2 = runtime.contract / "plans" / "P-02.md"
            p2.write_text(p2.read_text(encoding="utf-8").replace("status: pending", "status: in_progress"), encoding="utf-8")
            result = runtime.run("start")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("plan_already_in_progress", json.loads(result.stdout)["errors"])

    def test_block_transaction_is_recoverable_and_resume_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            self.assertEqual(runtime.run("start").returncode, 0)
            marker = runtime.contract / ".block-transaction.json"
            marker.write_text(json.dumps({"plan_id": "P-01", "blocked_document": "BLOCKED.md"}), encoding="utf-8")

            blocked = runtime.run("next")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("incomplete_block_transaction", json.loads(blocked.stdout)["errors"])

            recovered = runtime.run("recover-block", "--approve-recovery")
            self.assertEqual(recovered.returncode, 0, recovered.stdout)
            self.assertFalse(marker.exists())
            self.assertIn("status: blocked", (runtime.contract / "plans" / "P-01.md").read_text(encoding="utf-8"))
            self.assertTrue((runtime.contract / "BLOCKED.md").is_file())

            denied = runtime.run("resume", "--plan-id", "P-01", "--resolution-evidence", "dependency restored")
            self.assertNotEqual(denied.returncode, 0)
            resumed = runtime.run(
                "resume", "--plan-id", "P-01", "--resolution-evidence", "dependency restored",
                "--approve-resume",
            )
            self.assertEqual(resumed.returncode, 0, resumed.stdout)
            self.assertIn("status: pending", (runtime.contract / "plans" / "P-01.md").read_text(encoding="utf-8"))
            self.assertTrue((runtime.contract / "resolved-blocks" / "P-01.md").is_file())

    def test_dependency_ready_plan_selection_and_transitions_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))

            first = runtime.run("next")
            started = runtime.run("start")
            completed = runtime.run("complete", "--plan-id", "P-01")
            second = runtime.run("next")

            self.assertEqual(first.returncode, 0, first.stdout)
            self.assertEqual(json.loads(first.stdout)["plan_id"], "P-01")
            self.assertEqual(started.returncode, 0, started.stdout)
            self.assertEqual(json.loads(started.stdout)["transition"], "pending->in_progress")
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertEqual(json.loads(completed.stdout)["transition"], "in_progress->completed")
            self.assertEqual(second.returncode, 0, second.stdout)
            self.assertEqual(json.loads(second.stdout)["plan_id"], "P-02")
            self.assertFalse(list(runtime.contract.joinpath("plans").glob("*.tmp")))

    def test_failure_diagnose_regression_and_retry_evidence_is_structured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            events = (
                ("failure", {"command": "python -m unittest targeted", "exit_code": 1}),
                ("diagnose", {"root_cause": "missing boundary check", "minimized": True}),
                ("regression", {"test": "test_boundary", "result": "pass"}),
                ("retry", {"plan_id": "P-01", "result": "pass"}),
            )
            for kind, data in events:
                result = runtime.run("evidence", "--kind", kind, "--data", json.dumps(data))
                self.assertEqual(result.returncode, 0, result.stdout)

            records = [json.loads(line) for line in runtime.contract.joinpath("evidence.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([record["kind"] for record in records], [item[0] for item in events])
            self.assertEqual(records[1]["data"]["root_cause"], "missing boundary check")

    def test_hard_stop_blocks_plan_and_writes_every_mandatory_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = RuntimeCase(Path(temp_dir))
            self.assertEqual(runtime.run("start").returncode, 0)

            blocked = runtime.run(
                "block",
                "--plan-id",
                "P-01",
                "--reason",
                "missing required environment",
                "--evidence",
                "targeted test cannot start",
                "--attempt",
                "confirmed executable is absent",
                "--decision",
                "provide the approved executable",
                "--alternative",
                "use an approved fixture with reduced fidelity",
                "--resume",
                "rerun preflight then retry P-01",
            )

            self.assertEqual(blocked.returncode, 0, blocked.stdout)
            plan = runtime.contract.joinpath("plans", "P-01.md").read_text(encoding="utf-8")
            self.assertIn("status: blocked", plan)
            document = runtime.contract.joinpath("BLOCKED.md").read_text(encoding="utf-8")
            for section in (
                "Blocker", "Impact", "Evidence", "Attempts", "Resume Conditions",
                "Interruption Point", "Completed Plans", "Recommended Decision", "Alternatives",
            ):
                self.assertIn(f"## {section}", document)

    def test_public_skills_are_self_contained_and_enforce_goal_boundaries(self) -> None:
        execute = REPO_ROOT / "skills" / "execute-codex-goal"
        diagnose = REPO_ROOT / "skills" / "diagnose"
        execute_text = execute.joinpath("SKILL.md").read_text(encoding="utf-8")
        diagnose_text = diagnose.joinpath("SKILL.md").read_text(encoding="utf-8")

        self.assertTrue(execute.joinpath("scripts", "goal_runtime.py").is_file())
        self.assertTrue(execute.joinpath("scripts", "contract_engine.py").is_file())
        self.assertIn("Never create or start `/goal`", execute_text)
        self.assertIn("Goal declaration payload", execute_text)
        self.assertIn("targeted -> feature -> fast", execute_text)
        self.assertIn("Live and Eval are disabled by default", execute_text)
        for step in ("Reproduce", "Minimize", "Hypothesize", "Instrument", "Root cause", "Fix", "Regression", "Reverify"):
            self.assertIn(step, diagnose_text)
        self.assertNotIn("tracker", diagnose_text.lower())
        self.assertNotIn("matt pocock", diagnose_text.lower())
        self.assertIn("TESTING.md", diagnose_text)
        self.assertIn(".harness/project.yaml", diagnose_text)


if __name__ == "__main__":
    unittest.main()
