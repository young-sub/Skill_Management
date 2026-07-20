from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = REPO_ROOT / "skills" / "setup-agent-harness" / "scripts" / "bootstrap_project.py"


def run(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, env=env, capture_output=True, text=True, check=False
    )


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def refresh_digest(plan: dict[str, object]) -> str:
    canonical = {key: value for key, value in plan.items() if key != "plan_sha256"}
    digest = sha256(
        json.dumps(
            canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    plan["plan_sha256"] = digest
    return digest


class BrownfieldSafeApplyTests(unittest.TestCase):
    def _payload(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertTrue(result.stdout.strip(), result.stderr)
        return json.loads(result.stdout)

    def _init_project(self, root: Path) -> None:
        self.assertEqual(run("git", "init", "-q", cwd=root).returncode, 0)
        run("git", "config", "user.email", "fixture@example.test", cwd=root)
        run("git", "config", "user.name", "Fixture", cwd=root)
        (root / "README.md").write_text("# Existing project\n", encoding="utf-8")
        run("git", "add", "README.md", cwd=root)
        run("git", "commit", "-qm", "fixture", cwd=root)

    def _plan(self, root: Path) -> tuple[Path, dict[str, object]]:
        plan_path = root / ".work/reviewed-plan.json"
        result = run(
            sys.executable,
            str(BOOTSTRAP),
            "reconcile",
            "--root",
            str(root),
            "--report",
            str(plan_path),
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return plan_path, json.loads(result.stdout)

    def _apply(
        self,
        root: Path,
        plan_path: Path,
        digest: str,
        *,
        approve_agent_env: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(BOOTSTRAP),
            "apply-plan",
            "--root",
            str(root),
            "--plan",
            str(plan_path),
            "--approve-plan-sha256",
            digest,
            "--approve-local-only",
            ".work/",
        ]
        if approve_agent_env:
            command.extend(["--approve-local-only", "agent-env.*.md"])
        return run(*command, env=env)

    def test_digest_approval_and_preconditions_fail_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_project(root)
            plan_path, plan = self._plan(root)

            before = snapshot(root)
            bad_digest = self._apply(root, plan_path, "0" * 64)
            self.assertEqual(self._payload(bad_digest)["status"], "plan_digest_mismatch")
            self.assertEqual(snapshot(root), before)

            missing_path_approval = self._apply(
                root, plan_path, str(plan["plan_sha256"]), approve_agent_env=False
            )
            self.assertEqual(
                self._payload(missing_path_approval)["status"], "path_approval_required"
            )
            self.assertEqual(snapshot(root), before)

            (root / "README.md").write_text("# Changed after review\n", encoding="utf-8")
            drifted = snapshot(root)
            changed_input = self._apply(root, plan_path, str(plan["plan_sha256"]))
            payload = self._payload(changed_input)
            self.assertEqual(payload["status"], "precondition_failed")
            self.assertIn("discovery_fingerprint", payload["failed_preconditions"])
            self.assertEqual(snapshot(root), drifted)

    def test_apply_enforces_tracked_invariant_reports_commit_work_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_project(root)
            plan_path, plan = self._plan(root)

            first = self._apply(root, plan_path, str(plan["plan_sha256"]))

            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            report = self._payload(first)
            self.assertEqual(report["status"], "applied")
            self.assertEqual(report["plan_sha256"], plan["plan_sha256"])
            self.assertTrue(report["transaction_id"])
            self.assertEqual(report["verification"]["errors"], [])
            self.assertIn(".harness/project.yaml", report["must_be_committed"])
            self.assertNotEqual(
                run("git", "check-ignore", "-q", "--no-index", ".harness/project.yaml", cwd=root).returncode,
                0,
            )
            self.assertEqual(run("git", "diff", "--cached", "--quiet", cwd=root).returncode, 0)
            gitignore = (root / ".gitignore").read_text(encoding="utf-8")
            self.assertEqual(gitignore.count(".work/"), 1)

            second = self._apply(root, plan_path, str(plan["plan_sha256"]))

            second_report = self._payload(second)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertEqual(second_report["status"], "already_applied")
            self.assertEqual(second_report["mutation_count"], 0)
            self.assertEqual((root / ".gitignore").read_text(encoding="utf-8").count(".work/"), 1)

            (root / "README.md").write_text("# Drift after apply\n", encoding="utf-8")
            drifted = self._apply(root, plan_path, str(plan["plan_sha256"]))
            self.assertEqual(self._payload(drifted)["status"], "precondition_failed")

    def test_ignored_harness_path_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_project(root)
            (root / ".gitignore").write_text(".harness/\n", encoding="utf-8")
            plan_path, plan = self._plan(root)
            before = snapshot(root)

            result = self._apply(root, plan_path, str(plan["plan_sha256"]))

            payload = self._payload(result)
            self.assertEqual(payload["status"], "blocking_decisions")
            self.assertTrue(any(item.get("path") == ".harness/project.yaml" for item in payload["blocking_decisions"]))
            self.assertEqual(snapshot(root), before)

    def test_fault_injection_rolls_back_every_durable_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_project(root)
            plan_path, plan = self._plan(root)
            before = snapshot(root)
            env = os.environ.copy()
            env["HARNESS_FAULT_AFTER_OPERATION"] = "2"

            result = self._apply(root, plan_path, str(plan["plan_sha256"]), env=env)

            payload = self._payload(result)
            self.assertEqual(payload["status"], "rolled_back")
            self.assertTrue(payload["transaction_id"])
            after = snapshot(root)
            self.assertEqual(
                {key: value for key, value in after.items() if "bootstrap-transactions/" not in key},
                before,
            )
            journal = root / ".work/bootstrap-transactions" / payload["transaction_id"] / "journal.json"
            self.assertEqual(json.loads(journal.read_text(encoding="utf-8"))["status"], "rolled_back")

    def test_each_write_boundary_is_fault_injectable_and_journaled(self) -> None:
        with tempfile.TemporaryDirectory() as seed_dir:
            seed_root = Path(seed_dir)
            self._init_project(seed_root)
            _seed_plan_path, seed_plan = self._plan(seed_root)
            operation_count = len(seed_plan["mutations"])

        for boundary in range(1, operation_count + 1):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                self._init_project(root)
                plan_path, plan = self._plan(root)
                before = snapshot(root)
                env = os.environ.copy()
                env["HARNESS_FAULT_AFTER_OPERATION"] = str(boundary)

                result = self._apply(root, plan_path, str(plan["plan_sha256"]), env=env)

                payload = self._payload(result)
                self.assertEqual(payload["status"], "rolled_back")
                journal_path = (
                    root
                    / ".work/bootstrap-transactions"
                    / str(payload["transaction_id"])
                    / "journal.json"
                )
                journal = json.loads(journal_path.read_text(encoding="utf-8"))
                self.assertIn("failure_operation_index", journal)
                self.assertEqual(journal["failure_operation_index"], boundary)
                after = snapshot(root)
                self.assertEqual(
                    {key: value for key, value in after.items() if "bootstrap-transactions/" not in key},
                    before,
                )

    def test_recovery_required_blocks_apply_until_explicit_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_project(root)
            plan_path, plan = self._plan(root)
            env = os.environ.copy()
            env["HARNESS_FAULT_AFTER_OPERATION"] = "2"
            env["HARNESS_FAULT_DURING_ROLLBACK"] = "1"

            failed = self._apply(root, plan_path, str(plan["plan_sha256"]), env=env)
            failure = self._payload(failed)
            self.assertEqual(failure["status"], "recovery_required")

            blocked = self._apply(root, plan_path, str(plan["plan_sha256"]))
            self.assertEqual(self._payload(blocked)["status"], "incomplete_transaction")

            recovered = run(
                sys.executable,
                str(BOOTSTRAP),
                "recover-apply",
                "--root",
                str(root),
                "--transaction",
                failure["transaction_id"],
                "--approve-recovery",
            )
            recovery = self._payload(recovered)
            self.assertEqual(recovered.returncode, 0, recovered.stderr + recovered.stdout)
            self.assertEqual(recovery["status"], "rolled_back")

            final = self._apply(root, plan_path, str(plan["plan_sha256"]))
            self.assertEqual(self._payload(final)["status"], "applied")

    def test_crash_after_target_write_is_recovered_from_write_ahead_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_project(root)
            plan_path, plan = self._plan(root)
            before = snapshot(root)
            env = os.environ.copy()
            env["HARNESS_FAULT_AFTER_TARGET_WRITE"] = "1"

            crashed = self._apply(root, plan_path, str(plan["plan_sha256"]), env=env)

            self.assertNotEqual(crashed.returncode, 0)
            transaction_root = root / ".work/bootstrap-transactions"
            transaction = next(transaction_root.iterdir())
            journal = json.loads((transaction / "journal.json").read_text(encoding="utf-8"))
            self.assertEqual(journal["status"], "committing")
            self.assertEqual(journal["operations"][0]["state"], "applying")

            recovered = run(
                sys.executable,
                str(BOOTSTRAP),
                "recover-apply",
                "--root",
                str(root),
                "--transaction",
                transaction.name,
                "--approve-recovery",
            )

            self.assertEqual(recovered.returncode, 0, recovered.stderr + recovered.stdout)
            after = snapshot(root)
            self.assertEqual(
                {key: value for key, value in after.items() if "bootstrap-transactions/" not in key},
                before,
            )

    def test_tampered_escape_mutation_is_rejected_before_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root = parent / "project"
            root.mkdir()
            self._init_project(root)
            plan_path, plan = self._plan(root)
            mutation = dict(plan["mutations"][0])
            mutation["path"] = "../outside.txt"
            plan["mutations"][0] = mutation
            digest = refresh_digest(plan)
            plan_path.write_text(json.dumps(plan), encoding="utf-8")

            result = self._apply(root, plan_path, digest)

            payload = self._payload(result)
            self.assertEqual(payload["status"], "invalid_plan")
            self.assertFalse((parent / "outside.txt").exists())
            transaction_root = root / ".work/bootstrap-transactions"
            self.assertFalse(transaction_root.exists())

    def test_staging_failure_cleans_unjournaled_transaction_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_project(root)
            plan_path, plan = self._plan(root)
            plan["mutations"][0]["after_content_base64"] = "not-valid-base64!"
            digest = refresh_digest(plan)
            plan_path.write_text(json.dumps(plan), encoding="utf-8")

            result = self._apply(root, plan_path, digest)

            payload = self._payload(result)
            self.assertEqual(payload["status"], "transaction_prepare_failed")
            transaction_root = root / ".work/bootstrap-transactions"
            self.assertTrue(
                not transaction_root.exists() or not any(transaction_root.iterdir())
            )


if __name__ == "__main__":
    unittest.main()
