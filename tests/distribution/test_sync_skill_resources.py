from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync-skill-resources.ps1"


class SyncSkillResourcesTests(unittest.TestCase):
    def test_copies_canonical_resource_with_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            source = fixture_root / "authoring" / "references" / "testing-policy.md"
            source.parent.mkdir(parents=True)
            source_content = "# Testing policy\n\nRun the focused check first.\n"
            source.write_text(source_content, encoding="utf-8", newline="\n")

            target_skill = fixture_root / "skills" / "fixture-skill"
            target_skill.mkdir(parents=True)
            resource_map = {
                "schema_version": 1,
                "resources": [
                    {
                        "source": "references/testing-policy.md",
                        "targets": [
                            "fixture-skill/references/testing-policy.md",
                        ],
                    }
                ]
            }
            (fixture_root / "authoring" / "resource-map.json").write_text(
                json.dumps(resource_map),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(SYNC_SCRIPT),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            generated = (
                target_skill / "references" / "testing-policy.md"
            )
            diagnostics = f"{result.stdout}\n{result.stderr}"
            self.assertEqual(result.returncode, 0, diagnostics)
            self.assertTrue(generated.is_file(), diagnostics)
            generated_content = generated.read_text(encoding="utf-8")

        expected_hash = sha256(source_content.encode("utf-8")).hexdigest()
        self.assertIn(f"Source-SHA256: {expected_hash}", generated_content)
        self.assertTrue(generated_content.endswith(source_content))

    def test_check_reports_generated_resource_drift_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            source = fixture_root / "authoring" / "references" / "testing-policy.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Canonical\n", encoding="utf-8", newline="\n")
            target = (
                fixture_root
                / "skills"
                / "fixture-skill"
                / "references"
                / "testing-policy.md"
            )
            target.parent.mkdir(parents=True)
            target.write_text("locally edited\n", encoding="utf-8", newline="\n")
            resource_map = {
                "schema_version": 1,
                "resources": [
                    {
                        "source": "references/testing-policy.md",
                        "targets": [
                            "fixture-skill/references/testing-policy.md",
                        ],
                    }
                ]
            }
            (fixture_root / "authoring" / "resource-map.json").write_text(
                json.dumps(resource_map),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(SYNC_SCRIPT),
                    "-RepositoryRoot",
                    str(fixture_root),
                    "-Check",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            target_content = target.read_text(encoding="utf-8")

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("generated resource drift", diagnostics)
        self.assertEqual(target_content, "locally edited\n")

    def test_rejects_targets_outside_the_skills_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            source = fixture_root / "authoring" / "references" / "policy.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Policy\n", encoding="utf-8", newline="\n")
            resource_map = {
                "schema_version": 1,
                "resources": [
                    {
                        "source": "references/policy.md",
                        "targets": ["../escaped.md"],
                    }
                ]
            }
            (fixture_root / "authoring" / "resource-map.json").write_text(
                json.dumps(resource_map),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(SYNC_SCRIPT),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            escaped_target = fixture_root / "escaped.md"
            escaped_exists = escaped_target.exists()

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("target escapes skills directory", diagnostics)
        self.assertFalse(escaped_exists, diagnostics)

    def test_rejects_sources_outside_the_authoring_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            authoring_root = fixture_root / "authoring"
            authoring_root.mkdir(parents=True)
            (fixture_root / "outside.md").write_text(
                "# Not canonical\n",
                encoding="utf-8",
                newline="\n",
            )
            (fixture_root / "skills" / "fixture-skill").mkdir(parents=True)
            resource_map = {
                "schema_version": 1,
                "resources": [
                    {
                        "source": "../outside.md",
                        "targets": ["fixture-skill/references/policy.md"],
                    }
                ]
            }
            (authoring_root / "resource-map.json").write_text(
                json.dumps(resource_map),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(SYNC_SCRIPT),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("source escapes authoring directory", diagnostics)

    def test_rejects_unsupported_resource_map_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            authoring_root = fixture_root / "authoring"
            authoring_root.mkdir(parents=True)
            (fixture_root / "skills").mkdir()
            (authoring_root / "resource-map.json").write_text(
                json.dumps({"schema_version": 2, "resources": []}),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(SYNC_SCRIPT),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("unsupported resource map schema", diagnostics)


if __name__ == "__main__":
    unittest.main()
