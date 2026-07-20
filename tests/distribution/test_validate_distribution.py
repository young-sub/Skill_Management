from pathlib import Path
import json
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate-distribution.ps1"


class ValidateDistributionTests(unittest.TestCase):
    def test_default_repository_root_validates_checkout(self) -> None:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(VALIDATOR)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 0, diagnostics)
        self.assertIn("Distribution validation passed.", diagnostics)

    def test_rejects_public_skill_when_directory_and_name_differ(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "folder-name"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: different-name\ndescription: fixture\n---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("directory/name mismatch", diagnostics)

    def test_rejects_unsupported_public_skill_frontmatter_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: fixture-skill\n"
                "description: fixture\n"
                "license: unexpected\n"
                "---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("unsupported frontmatter field", diagnostics)

    def test_rejects_missing_required_public_skill_frontmatter_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\n---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("missing required frontmatter field", diagnostics)

    def test_rejects_skill_files_without_frontmatter_delimiters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "name: fixture-skill\ndescription: fixture\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("invalid frontmatter", diagnostics)

    def test_rejects_malformed_frontmatter_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription fixture\n---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("invalid frontmatter line", diagnostics)

    def test_rejects_discoverable_legacy_skill_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            public_dir = fixture_root / "skills" / "fixture-skill"
            public_dir.mkdir(parents=True)
            (public_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            legacy_dir = fixture_root / "legacy-skills" / "old-skill"
            legacy_dir.mkdir(parents=True)
            (legacy_dir / "SKILL.md").write_text(
                "---\nname: old-skill\ndescription: legacy\n---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("legacy skill remains discoverable", diagnostics)

    def test_rejects_resource_references_that_escape_a_public_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: fixture-skill\n"
                "description: fixture\n"
                "---\n\n"
                "Read [shared policy](../../authoring/policy.md).\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("resource reference escapes skill directory", diagnostics)
        self.assertIn("SC_RELATIVE_ESCAPE", diagnostics)

    def test_distribution_validator_runs_structured_self_containment_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n\n"
                "Machine path: `C:\\Users\\fixture\\secret.md`\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("SC_ABSOLUTE_PATH", diagnostics)

    def test_rejects_instruction_mirror_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            (fixture_root / "AGENTS.md").write_text(
                "# Agent router\n",
                encoding="utf-8",
            )
            (fixture_root / "CLAUDE.md").write_text(
                "# Different router\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("instruction mirror drift", diagnostics)

    def test_rejects_instruction_router_over_one_hundred_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            oversized_router = "".join(f"line {index}\n" for index in range(101))
            (fixture_root / "AGENTS.md").write_text(
                oversized_router,
                encoding="utf-8",
            )
            (fixture_root / "CLAUDE.md").write_text(
                oversized_router,
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("instruction router exceeds 100 lines", diagnostics)

    def test_rejects_public_skills_missing_from_distribution_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            for skill_name in ("expected-skill", "unexpected-skill"):
                skill_dir = fixture_root / "skills" / skill_name
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: {skill_name}\ndescription: fixture\n---\n",
                    encoding="utf-8",
                )
            distribution_dir = fixture_root / "distribution"
            distribution_dir.mkdir()
            (distribution_dir / "catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "public_skills": ["expected-skill"],
                        "legacy_skills": [],
                        "future_core_skills": [],
                        "intentionally_absent": [],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("unexpected public skill", diagnostics)

    def test_rejects_catalog_entries_without_a_public_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "present-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: present-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            distribution_dir = fixture_root / "distribution"
            distribution_dir.mkdir()
            (distribution_dir / "catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "public_skills": ["present-skill", "missing-skill"],
                        "legacy_skills": [],
                        "future_core_skills": [],
                        "intentionally_absent": [],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("missing expected public skill", diagnostics)

    def test_rejects_missing_preserved_legacy_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "present-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: present-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            distribution_dir = fixture_root / "distribution"
            distribution_dir.mkdir()
            (distribution_dir / "catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "public_skills": ["present-skill"],
                        "legacy_skills": ["missing-legacy"],
                        "future_core_skills": [],
                        "intentionally_absent": [],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("missing preserved legacy skill", diagnostics)

    def test_rejects_missing_distribution_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            router = "# Router\n"
            (fixture_root / "AGENTS.md").write_text(router, encoding="utf-8")
            (fixture_root / "CLAUDE.md").write_text(router, encoding="utf-8")

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn(
            "missing required distribution artifact: distribution/catalog.json",
            diagnostics,
        )

    def test_rejects_missing_instruction_router_mirrors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            distribution_dir = fixture_root / "distribution"
            distribution_dir.mkdir()
            (distribution_dir / "catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "public_skills": ["fixture-skill"],
                        "legacy_skills": [],
                        "future_core_skills": [],
                        "intentionally_absent": [],
                    }
                ),
                encoding="utf-8",
            )
            (fixture_root / "CLAUDE.md").write_text(
                "# Router\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn(
            "missing required distribution artifact: AGENTS.md",
            diagnostics,
        )

    def test_reports_a_missing_public_skills_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            distribution_dir = fixture_root / "distribution"
            distribution_dir.mkdir()
            (distribution_dir / "catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "public_skills": [],
                        "legacy_skills": [],
                        "future_core_skills": [],
                        "intentionally_absent": [],
                    }
                ),
                encoding="utf-8",
            )
            router = "# Router\n"
            (fixture_root / "AGENTS.md").write_text(router, encoding="utf-8")
            (fixture_root / "CLAUDE.md").write_text(router, encoding="utf-8")

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn(
            "missing required distribution artifact: skills/",
            diagnostics,
        )

    def test_reports_a_missing_legacy_skills_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            distribution_dir = fixture_root / "distribution"
            distribution_dir.mkdir()
            (distribution_dir / "catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "public_skills": ["fixture-skill"],
                        "legacy_skills": [],
                        "future_core_skills": [],
                        "intentionally_absent": [],
                    }
                ),
                encoding="utf-8",
            )
            router = "# Router\n"
            (fixture_root / "AGENTS.md").write_text(router, encoding="utf-8")
            (fixture_root / "CLAUDE.md").write_text(router, encoding="utf-8")

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn(
            "missing required distribution artifact: legacy-skills/",
            diagnostics,
        )

    def test_rejects_unsupported_distribution_catalog_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            skill_dir = fixture_root / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            (fixture_root / "legacy-skills").mkdir()
            distribution_dir = fixture_root / "distribution"
            distribution_dir.mkdir()
            (distribution_dir / "catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "public_skills": ["fixture-skill"],
                        "legacy_skills": [],
                        "future_core_skills": [],
                        "intentionally_absent": [],
                    }
                ),
                encoding="utf-8",
            )
            router = "# Router\n"
            (fixture_root / "AGENTS.md").write_text(router, encoding="utf-8")
            (fixture_root / "CLAUDE.md").write_text(router, encoding="utf-8")

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(VALIDATOR),
                    "-RepositoryRoot",
                    str(fixture_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        diagnostics = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 1, diagnostics)
        self.assertIn("unsupported distribution catalog schema", diagnostics)


if __name__ == "__main__":
    unittest.main()
