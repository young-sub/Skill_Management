"""Artifact paths must be readable before connected-product services launch."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "tests/distribution/fixtures/connected_product"


class ArtifactAccessTests(unittest.TestCase):
    def setUp(self):
        self.runner = runpy.run_path(str(PROJECT / "run_project.py"))
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def run_blocked(self, artifact_dir):
        report_path = self.root / "reports" / "browser.json"
        server = Mock(side_effect=AssertionError("service must not start"))
        with patch("sys.argv", ["run_project.py", "--report", str(report_path),
                                 "--artifact-dir", str(artifact_dir)]):
            with patch.dict(self.runner["main"].__globals__, {"server_process": server}):
                self.assertEqual(self.runner["main"](), 2)
        raw = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(raw["status"], "BLOCKED")
        self.assertFalse(raw["execution"]["executed"])
        self.assertEqual(raw["observed"]["services"], [])
        self.assertEqual(raw["observed"]["artifact_access"]["visual_observation"], "NOT_PERFORMED")
        self.assertEqual(raw["errors"][0]["phase"], "artifact_access")
        server.assert_not_called()
        return raw

    def test_preflight_creates_reads_and_removes_a_unique_probe(self):
        artifact_dir = self.root / "evidence" / "browser"

        self.runner["preflight_artifact_dir"](artifact_dir)

        self.assertTrue(artifact_dir.is_dir())
        self.assertEqual(list(artifact_dir.iterdir()), [])

    def test_file_in_target_path_blocks_before_service_launch(self):
        blocker = self.root / "not-a-directory"
        blocker.write_bytes(b"preserve this file")
        original = blocker.read_bytes()

        raw = self.run_blocked(blocker / "artifacts")

        self.assertEqual(raw["observed"]["artifact_access"]["preflight"], "FAILED")
        self.assertEqual(blocker.read_bytes(), original)

    def test_runner_read_denial_blocks_and_removes_only_its_probe(self):
        artifact_dir = self.root / "evidence"
        original_read_bytes = Path.read_bytes

        def deny_probe_read(path):
            if path.parent == artifact_dir and path.name.startswith(".artifact-access-"):
                raise PermissionError("simulated artifact read denial")
            return original_read_bytes(path)

        with patch.object(Path, "read_bytes", deny_probe_read):
            raw = self.run_blocked(artifact_dir)

        self.assertEqual(raw["observed"]["artifact_access"]["preflight"], "FAILED")
        self.assertIn("simulated artifact read denial", raw["errors"][0]["message"])
        self.assertEqual(list(artifact_dir.iterdir()), [])

    def test_existing_screenshot_is_never_overwritten(self):
        artifact_dir = self.root / "evidence"
        artifact_dir.mkdir()
        screenshot = artifact_dir / "entry-1280.png"
        screenshot.write_bytes(b"existing evidence")
        original = screenshot.read_bytes()

        raw = self.run_blocked(artifact_dir)

        self.assertEqual(raw["observed"]["artifact_access"]["preflight"], "FAILED")
        self.assertIn("Refusing to overwrite existing artifacts", raw["errors"][0]["message"])
        self.assertEqual(screenshot.read_bytes(), original)

    def test_readable_screenshot_file_is_not_mistaken_for_visual_review(self):
        path = self.root / "history-390.png"
        path.write_bytes(b"screenshot bytes")
        report = {"artifacts": [], "errors": [], "skipped": []}

        with patch.dict(self.runner["record_artifact"].__globals__,
                        {"sha256": Mock(return_value="digest")}):
            self.assertTrue(self.runner["record_artifact"](
                report, "history_mobile_screenshot", path, required=True))

        artifact = report["artifacts"][0]
        self.assertEqual(artifact["browser_capture"], "FILE_PRESENT")
        self.assertIs(artifact["readable_by_runner"], True)
        self.assertEqual(artifact["visual_observation"], "NOT_PERFORMED")

    def test_unreadable_screenshot_is_blocked_without_visual_success(self):
        path = self.root / "history-390.png"
        path.write_bytes(b"screenshot bytes")
        report = {"artifacts": [], "errors": [], "skipped": []}

        with patch.dict(self.runner["record_artifact"].__globals__,
                        {"sha256": Mock(side_effect=PermissionError("denied"))}):
            self.assertFalse(self.runner["record_artifact"](
                report, "history_mobile_screenshot", path, required=True))

        artifact = report["artifacts"][0]
        self.assertEqual(artifact["browser_capture"], "FILE_PRESENT")
        self.assertIs(artifact["readable_by_runner"], False)
        self.assertEqual(artifact["visual_observation"], "NOT_PERFORMED")
        self.assertEqual(report["errors"][0]["message"], "denied")

    def test_missing_required_screenshot_is_not_marked_reviewed(self):
        report = {"artifacts": [], "errors": [], "skipped": []}

        self.assertFalse(self.runner["record_artifact"](
            report, "history_mobile_screenshot", self.root / "missing.png", required=True))

        artifact = report["artifacts"][0]
        self.assertEqual(artifact["browser_capture"], "MISSING")
        self.assertIsNone(artifact["readable_by_runner"])
        self.assertEqual(artifact["visual_observation"], "NOT_PERFORMED")
        self.assertEqual(report["skipped"][0]["reason"], "required evidence is missing")


if __name__ == "__main__":
    unittest.main()
