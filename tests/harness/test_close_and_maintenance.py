from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CLOSE = ROOT / "authoring" / "scripts" / "close_goal.py"
MAINTAIN = ROOT / "authoring" / "scripts" / "maintain_harness.py"


class CloseGoalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / ".work" / "active" / "W-1").mkdir(parents=True)
        self.contract = self.root / ".work" / "active" / "W-1"
        (self.contract / "GOAL.md").write_text(
            "---\nwork_id: W-1\nkind: goal\n---\n\n## Objective\nShip <safe> output.\n",
            encoding="utf-8",
        )
        (self.root / ".harness").mkdir()
        (self.root / ".harness" / "project.yaml").write_text(
            "handoff:\n  target: local\n", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.findings = self.root / "findings.json"
        self.verification = self.root / "verification.json"
        self.write_inputs([], [
            {"kind": "Targeted", "status": "passed", "command": "python -m unittest"},
            {"kind": "Live", "status": "not_run"},
            {"kind": "Eval", "status": "unrun"},
        ])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_inputs(self, findings: list[dict], checks: list[dict]) -> None:
        self.findings.write_text(json.dumps({"findings": findings}), encoding="utf-8")
        self.verification.write_text(json.dumps({"checks": checks}), encoding="utf-8")

    def run_close(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLOSE), "--contract-root", str(self.contract),
             "--source-root", str(self.root), "--findings", str(self.findings),
             "--verification", str(self.verification), "--current-month", "2026-07"],
            capture_output=True, text=True, check=False,
        )

    def test_high_finding_blocks_without_archive(self) -> None:
        self.write_inputs([{"severity": "High", "title": "unsafe <script>alert(1)</script>"}], [])
        result = self.run_close()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("high_finding", result.stdout)
        self.assertTrue(self.contract.exists())
        self.assertFalse((self.root / ".work" / "archive" / "2026-07" / "W-1").exists())

    def test_tracked_document_work_link_blocks_completion(self) -> None:
        (self.root / "README.md").write_text("See [.work](.work/active/W-1/GOAL.md).\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, check=True)
        result = self.run_close()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("durable_work_reference:README.md", result.stdout)
        self.assertTrue(self.contract.exists())

    def test_success_archives_outputs_and_marks_unrun_live_eval_unverified(self) -> None:
        result = self.run_close()
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        archived = self.root / ".work" / "archive" / "2026-07" / "W-1"
        self.assertFalse(self.contract.exists())
        result_md = (archived / "RESULT.md").read_text(encoding="utf-8")
        html = (archived / "artifacts" / "completion-review.html").read_text(encoding="utf-8")
        self.assertTrue((archived / "HANDOFF.md").is_file())
        self.assertIn("Live: unverified", result_md)
        self.assertIn("Eval: unverified", result_md)
        for text in ("W-1", "Targeted", "Live", "unverified"):
            self.assertIn(text, result_md)
            self.assertIn(text, html)
        self.assertNotIn("<script", html.lower())
        self.assertIn("Ship &lt;safe&gt; output.", html)

    def test_handoff_is_omitted_when_target_is_none(self) -> None:
        (self.root / ".harness" / "project.yaml").write_text(
            "handoff:\n  target: none\n", encoding="utf-8"
        )
        result = self.run_close()
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        archived = self.root / ".work" / "archive" / "2026-07" / "W-1"
        self.assertFalse((archived / "HANDOFF.md").exists())

    def test_close_supports_small_spec_only_contract(self) -> None:
        (self.contract / "GOAL.md").unlink()
        (self.contract / "SPEC.md").write_text(
            "---\nwork_id: W-1\nkind: spec\n---\n\n## Problem\nRepair the small regression.\n"
            "\n## User Value\nUsers can finish the workflow.\n",
            encoding="utf-8",
        )
        result = self.run_close()
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        archived = self.root / ".work" / "archive" / "2026-07" / "W-1"
        result_md = (archived / "RESULT.md").read_text(encoding="utf-8")
        self.assertIn("Repair the small regression.", result_md)


class MaintenanceTests(unittest.TestCase):
    def test_report_only_detects_drift_retention_durable_refs_and_residual_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "AGENTS.md").write_text("agent\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text("different\n", encoding="utf-8")
            (root / "README.md").write_text("[bad](.work/active/W-1/GOAL.md) [missing](docs/no.md)\n", encoding="utf-8")
            (root / ".work" / "active" / "W-old").mkdir(parents=True)
            (root / ".work" / "archive" / "2020-01" / "W-old").mkdir(parents=True)
            (root / ".work" / "trash" / "2020-01-01" / "W-trash").mkdir(parents=True)
            residual = root / "residual-worktree"
            residual.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "AGENTS.md", "CLAUDE.md", "README.md"], cwd=root, check=True)
            worktrees = root / "worktrees.json"
            worktrees.write_text(json.dumps({"registered": [], "observed": [str(residual)]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(MAINTAIN), "--source-root", str(root),
                 "--current-date", "2026-07-19", "--worktrees", str(worktrees)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            kinds = {finding["kind"] for finding in report["findings"]}
            self.assertTrue({"instruction_drift", "durable_work_reference", "broken_relative_path",
                             "archive_retention_eligible", "trash_retention_eligible",
                             "unregistered_worktree"}.issubset(kinds))
            self.assertEqual("report-only", report["mode"])
            self.assertTrue(all(action["applied"] is False for action in report["actions"]))
            self.assertTrue((root / ".work" / "archive" / "2020-01" / "W-old").exists())
            self.assertTrue((root / ".work" / "trash" / "2020-01-01" / "W-trash").exists())
            self.assertTrue(residual.exists())


if __name__ == "__main__":
    unittest.main()
