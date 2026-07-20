from __future__ import annotations

import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
CLOSE = ROOT / "authoring" / "scripts" / "close_goal.py"
ENGINE = ROOT / "authoring" / "scripts" / "contract_engine.py"
FIXTURES = Path(__file__).parent / "fixtures" / "contracts"
MAINTAIN = ROOT / "authoring" / "scripts" / "maintain_harness.py"


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class CloseGoalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.contract = self.root / ".work" / "active" / "W-20260719-102"
        shutil.copytree(FIXTURES / "multi", self.contract)
        (self.root / ".harness").mkdir()
        (self.root / ".harness" / "project.yaml").write_text(
            "handoff:\n  target: local\n", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        approved = subprocess.run(
            [sys.executable, str(ENGINE), "approve", "--root", str(self.contract),
             "--work-root", str(self.root / ".work"), "--approved-at", "2026-07-19T18:00:00+09:00",
             "--approved-by", "human"], capture_output=True, text=True, check=False,
        )
        self.assertEqual(approved.returncode, 0, approved.stdout)
        for plan in (self.contract / "plans").glob("*.md"):
            plan.write_text(plan.read_text(encoding="utf-8").replace("status: pending", "status: completed"), encoding="utf-8")
        self.findings = self.root / "findings.json"
        self.verification = self.root / "verification.json"
        self.write_inputs([], [
            *[{"kind": kind, "status": "passed", "command": f"run {kind}", "evidence": f"{kind} passed", "returncode": 0}
              for kind in ("Targeted", "Feature", "Fast", "Full")],
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
        self.assertFalse((self.root / ".work" / "archive" / "2026-07" / "W-20260719-102").exists())

    def test_tracked_document_work_link_blocks_completion(self) -> None:
        (self.root / "README.md").write_text("See [.work](.work/active/W-20260719-102/GOAL.md).\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, check=True)
        result = self.run_close()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("durable_work_reference:README.md", result.stdout)
        self.assertTrue(self.contract.exists())

    def test_success_archives_outputs_and_marks_unrun_live_eval_unverified(self) -> None:
        result = self.run_close()
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        archived = self.root / ".work" / "archive" / "2026-07" / "W-20260719-102"
        self.assertFalse(self.contract.exists())
        result_md = (archived / "RESULT.md").read_text(encoding="utf-8")
        html = (archived / "artifacts" / "completion-review.html").read_text(encoding="utf-8")
        self.assertTrue((archived / "HANDOFF.md").is_file())
        self.assertIn("Live: unverified", result_md)
        self.assertIn("Eval: unverified", result_md)
        for text in ("W-20260719-102", "Targeted", "Live", "unverified"):
            self.assertIn(text, result_md)
            self.assertIn(text, html)
        self.assertNotIn("<script", html.lower())
        self.assertIn("Deliver a dependency-ordered workflow.", html)

    def test_handoff_is_omitted_when_target_is_none(self) -> None:
        (self.root / ".harness" / "project.yaml").write_text(
            "handoff:\n  target: none\n", encoding="utf-8"
        )
        result = self.run_close()
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        archived = self.root / ".work" / "archive" / "2026-07" / "W-20260719-102"
        self.assertFalse((archived / "HANDOFF.md").exists())

    def test_close_supports_small_spec_only_contract(self) -> None:
        shutil.rmtree(self.contract)
        self.contract = self.root / ".work" / "active" / "W-20260719-101"
        shutil.copytree(FIXTURES / "small", self.contract)
        approved = subprocess.run(
            [sys.executable, str(ENGINE), "approve", "--root", str(self.contract),
             "--work-root", str(self.root / ".work"), "--approved-at", "2026-07-19T18:00:00+09:00",
             "--approved-by", "human"], capture_output=True, text=True, check=False,
        )
        self.assertEqual(approved.returncode, 0, approved.stdout)
        (self.contract / "runtime-state.json").write_text('{"SPEC":"completed"}\n', encoding="utf-8")
        result = self.run_close()
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        archived = self.root / ".work" / "archive" / "2026-07" / "W-20260719-101"
        result_md = (archived / "RESULT.md").read_text(encoding="utf-8")
        self.assertIn("There is no greeting.", result_md)

    def test_unapproved_incomplete_or_invalid_verification_blocks_without_writes(self) -> None:
        cases = ("unapproved", "incomplete", "checks")
        for case in cases:
            with self.subTest(case=case):
                if case == "unapproved":
                    goal = self.contract / "GOAL.md"
                    goal.write_text(goal.read_text(encoding="utf-8").replace("approval.status: approved", "approval.status: pending"), encoding="utf-8")
                elif case == "incomplete":
                    plan = self.contract / "plans" / "P-02.md"
                    plan.write_text(plan.read_text(encoding="utf-8").replace("status: completed", "status: pending"), encoding="utf-8")
                else:
                    self.write_inputs([], [{"kind": "Targeted", "status": "passed", "command": "", "evidence": "", "returncode": 1}])
                result = self.run_close()
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertTrue(self.contract.exists())
                self.assertFalse((self.contract / "RESULT.md").exists())
                self.assertFalse((self.contract / "artifacts" / "completion-review.html").exists())
                self.tearDown(); self.setUp()

    def test_git_ls_files_failure_blocks_close(self) -> None:
        shutil.rmtree(self.root / ".git")
        result = self.run_close()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git_ls_files_failed", result.stdout)
        self.assertTrue(self.contract.exists())

    def test_every_close_write_and_move_target_is_contained_and_not_reparse(self) -> None:
        module = load_script(CLOSE, "close_goal_containment_test")
        archive = self.root / ".work" / "archive" / "2026-07" / self.contract.name
        artifact = self.contract / "artifacts" / "completion-review.html"

        with mock.patch.object(module, "_path_is_reparse", side_effect=lambda path: path == artifact.parent):
            findings = module._unsafe_operation_targets(self.root, self.contract, archive)

        self.assertTrue(any(item["path"].endswith("artifacts") for item in findings))
        outside = self.root.parent / "outside-archive" / self.contract.name
        findings = module._unsafe_operation_targets(self.root, self.contract, outside)
        self.assertTrue(any(item["reason"] == "target_outside_root" for item in findings))


class MaintenanceTests(unittest.TestCase):
    def run_maintain(self, root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(MAINTAIN),
                "--source-root",
                str(root),
                "--current-date",
                "2026-07-19",
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

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

    def test_git_ls_files_failure_is_high_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            result = self.run_maintain(root)

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            finding = next(item for item in report["findings"] if item["kind"] == "git_ls_files_failed")
            self.assertEqual(finding["severity"], "High")
            self.assertEqual(report["status"], "blocked")

    def test_installed_manifest_detects_tampered_body_and_missing_resource(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            installed = Path(temporary) / "installed"
            root.mkdir()
            installed.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            expected = b"# Generated file.\n# Source-SHA256: " + (b"0" * 64) + b"\n\nVALUE = 1\n"
            manifest = Path(temporary) / "public-resource-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "algorithm": "sha256",
                        "root": "skills",
                        "files": {
                            "fixture/scripts/helper.py": sha256(expected).hexdigest(),
                            "fixture/references/policy.md": sha256(b"policy\n").hexdigest(),
                        },
                    }
                ),
                encoding="utf-8",
            )
            helper = installed / "fixture" / "scripts" / "helper.py"
            helper.parent.mkdir(parents=True)
            helper.write_bytes(expected.replace(b"VALUE = 1", b"VALUE = 2"))

            result = self.run_maintain(
                root,
                "--installed-root",
                str(installed),
                "--resource-manifest",
                str(manifest),
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            findings = json.loads(result.stdout)["findings"]
            kinds_by_path = {(item["kind"], item["path"]) for item in findings}
            self.assertIn(
                ("installed_resource_drift", "fixture/scripts/helper.py"),
                kinds_by_path,
            )
            self.assertIn(
                ("missing_installed_resource", "fixture/references/policy.md"),
                kinds_by_path,
            )

    def test_normalized_text_hashes_accept_crlf_but_binary_hashes_remain_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            installed = Path(temporary) / "installed"
            root.mkdir()
            installed.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            expected_text = b"VALUE = 1\n"
            expected_binary = b"\x00\x01\x02\xff"
            manifest = Path(temporary) / "public-resource-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "algorithm": "sha256",
                        "root": "skills",
                        "files": {
                            "fixture/scripts/helper.py": sha256(expected_text).hexdigest(),
                            "fixture/assets/payload.bin": sha256(expected_binary).hexdigest(),
                        },
                    }
                ),
                encoding="utf-8",
            )
            helper = installed / "fixture" / "scripts" / "helper.py"
            payload = installed / "fixture" / "assets" / "payload.bin"
            helper.parent.mkdir(parents=True)
            payload.parent.mkdir(parents=True)
            helper.write_bytes(expected_text.replace(b"\n", b"\r\n"))
            payload.write_bytes(expected_binary)

            clean = self.run_maintain(
                root,
                "--installed-root",
                str(installed),
                "--resource-manifest",
                str(manifest),
            )
            clean_findings = json.loads(clean.stdout)["findings"]
            self.assertFalse(
                any(item["kind"] == "installed_resource_drift" for item in clean_findings),
                clean.stdout,
            )

            helper.write_bytes(b"VALUE = 2\r\n")
            payload.write_bytes(b"\x00\x01\x03\xff")
            tampered = self.run_maintain(
                root,
                "--installed-root",
                str(installed),
                "--resource-manifest",
                str(manifest),
            )
            drift_paths = {
                item["path"]
                for item in json.loads(tampered.stdout)["findings"]
                if item["kind"] == "installed_resource_drift"
            }
            self.assertEqual(
                drift_paths,
                {"fixture/scripts/helper.py", "fixture/assets/payload.bin"},
            )

    def test_resource_headers_use_the_same_normalized_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "authoring" / "references" / "policy.md"
            target = root / "skills" / "fixture" / "references" / "policy.md"
            source.parent.mkdir(parents=True)
            target.parent.mkdir(parents=True)
            source.write_bytes(b"# Policy\r\n")
            digest = sha256(b"# Policy\n").hexdigest()
            target.write_text(
                "<!-- Generated file. Do not edit directly. -->\n"
                "<!-- Source: authoring/references/policy.md -->\n"
                f"<!-- Source-SHA256: {digest} -->\n\n# Policy\n",
                encoding="utf-8",
            )
            (root / "authoring" / "resource-map.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "resources": [
                            {
                                "source": "references/policy.md",
                                "targets": ["fixture/references/policy.md"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)

            result = self.run_maintain(root)
            findings = json.loads(result.stdout)["findings"]
            self.assertFalse(
                any(item["kind"] == "resource_drift" for item in findings),
                result.stdout,
            )

    def test_test_history_flags_budget_trend_staleness_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".harness").mkdir()
            (root / ".harness" / "project.yaml").write_text(
                "verification:\n"
                "  targeted_max_seconds: 30\n"
                "  feature_max_seconds: 120\n"
                "  fast_suite_max_seconds: 300\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            history = root / "test-history.json"
            history.write_text(
                json.dumps(
                    {
                        "tests": [
                            {
                                "id": "test_old",
                                "last_run": "2026-01-01",
                                "fingerprint": "same behavior",
                            },
                            {
                                "id": "test_old",
                                "last_run": "2026-07-18",
                                "fingerprint": "other behavior",
                            },
                            {
                                "id": "test_copy",
                                "last_run": "2026-07-18",
                                "fingerprint": "same behavior",
                            },
                        ],
                        "runs": [
                            {"suite": "targeted", "duration_seconds": 20, "recorded_at": "2026-07-17"},
                            {"suite": "targeted", "duration_seconds": 29, "recorded_at": "2026-07-18"},
                            {"suite": "targeted", "duration_seconds": 35, "recorded_at": "2026-07-19"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_maintain(root, "--test-history", str(history))

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            kinds = {item["kind"] for item in json.loads(result.stdout)["findings"]}
            self.assertTrue(
                {
                    "test_duration_budget_exceeded",
                    "test_duration_regression_trend",
                    "stale_test",
                    "duplicate_test_id",
                    "duplicate_test_candidate",
                }.issubset(kinds),
                kinds,
            )


if __name__ == "__main__":
    unittest.main()
