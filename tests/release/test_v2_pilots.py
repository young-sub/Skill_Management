from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "run-v2-pilots.py"


class V2PilotTests(unittest.TestCase):
    def test_runner_freshly_reproduces_three_complete_pilots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilots"
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--output-dir", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )

            diagnostics = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, diagnostics)
            self.assertIn("PASS: 3/3 Harness V2 pilots", diagnostics)
            report = json.loads((output / "harness-v2-pilots.json").read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["result"], "passed")
            self.assertEqual(len(report["pilots"]), 3)
            self.assertEqual(
                [pilot["type"] for pilot in report["pilots"]],
                ["small-spec-bug-fix", "normal-goal-feature", "multi-plan-dag-feature"],
            )
            for pilot in report["pilots"]:
                self.assertEqual(pilot["execution_adapter"], "repo-local-host-adapter")
                self.assertFalse(pilot["live_goal"])
                self.assertEqual(pilot["timing_mode"], "measured")
                self.assertEqual(pilot["question_count"], 0)
                self.assertEqual(pilot["interruptions"], 0)
                self.assertTrue(pilot["design_approved"])
                self.assertTrue(pilot["result_success"])
                self.assertTrue(pilot["archive_success"])
                self.assertFalse(pilot["instruction_drift"])
                self.assertEqual(pilot["work_links"], [])
                self.assertEqual(pilot["active_leftovers"], [])
                self.assertEqual(pilot["worktree_residuals"], [])
                self.assertTrue((output / pilot["human_review_artifact"]).is_file())
                red = pilot["regression_evidence"]["red"]
                self.assertEqual(red["status"], "failed")
                self.assertNotEqual(red["returncode"], 0)
                self.assertIn("AssertionError", red["stderr_summary"])
                self.assertGreaterEqual(red["duration_seconds"], 0)
                self.assertTrue(red["command"])

                plan_cycles = pilot["implementation_cycles"]
                self.assertEqual([cycle["plan_id"] for cycle in plan_cycles], pilot["plans"])
                for cycle in plan_cycles:
                    self.assertTrue(cycle["source_change"]["path"])
                    self.assertTrue(cycle["source_change"]["description"])
                    self.assertEqual(
                        [check["kind"] for check in cycle["checks"]],
                        ["Targeted", "Feature", "Fast"],
                    )
                    for check in cycle["checks"]:
                        self.assertEqual(check["status"], "passed")
                        self.assertEqual(check["returncode"], 0)
                        self.assertTrue(check["command"])
                        self.assertGreaterEqual(check["duration_seconds"], 0)
                        self.assertNotEqual(check.get("timing_mode"), "simulated")
                self.assertEqual(
                    [check["kind"] for check in pilot["verification"]],
                    ["Targeted", "Feature", "Fast", "Full"],
                )
                full_checks = [check for check in pilot["command_evidence"] if check["kind"] == "Full"]
                self.assertEqual(len(full_checks), 1)
                self.assertEqual(full_checks[0]["returncode"], 0)
                self.assertEqual(pilot["regression_evidence"]["green"]["status"], "passed")
            self.assertEqual(report["pilots"][0]["plans"], ["SPEC"])
            self.assertEqual(report["pilots"][1]["plans"], ["P-01"])
            self.assertEqual(report["pilots"][2]["plans"], ["P-01", "P-02", "P-03"])
            self.assertTrue((output / "harness-v2-pilots.md").is_file())


if __name__ == "__main__":
    unittest.main()
