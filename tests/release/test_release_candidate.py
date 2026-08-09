from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ReleaseCandidateTests(unittest.TestCase):
    def test_release_candidate_matches_the_complete_public_catalog(self) -> None:
        catalog = json.loads((ROOT / "distribution" / "catalog.json").read_text(encoding="utf-8"))
        candidate = json.loads((ROOT / "distribution" / "release-candidate.json").read_text(encoding="utf-8"))

        self.assertEqual(candidate["schema_version"], 2)
        self.assertEqual(candidate["version"], "2.0.0")
        self.assertEqual(candidate["stage"], "stable")
        self.assertTrue(candidate["live_release"])
        self.assertEqual(candidate["tag"], "v2.0.0")
        self.assertEqual(candidate["release_date"], "2026-07-21")
        self.assertEqual(candidate["release_notes"], "../docs/releases/v2.0.0.md")
        self.assertEqual(candidate["public_skill_count"], len(catalog["public_skills"]))
        self.assertEqual(candidate["public_skills"], catalog["public_skills"])
        self.assertEqual(candidate["future_core_skills"], [])
        self.assertEqual(catalog["future_core_skills"], [])
        self.assertRegex(candidate["source_revision"]["git_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(candidate["source_revision"]["git_tree"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            set(candidate["evidence"]),
            {"pilot_execution", "local_source_install_refresh", "remote_github_update"},
        )

    def test_distribution_workflow_uses_supported_node_and_all_local_gates(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate-distribution.yml").read_text(encoding="utf-8")

        self.assertIn("node-version: '22.20.0'", workflow)
        self.assertIn("branches: [develop, main]", workflow)
        self.assertIn('python -m unittest discover -s tests -p "test_*.py"', workflow)
        self.assertIn("scripts/sync-skill-resources.ps1 -Check", workflow)
        self.assertIn("scripts/validate-distribution.ps1", workflow)
        self.assertNotIn("npx skills", workflow)

    def test_readme_routes_current_harness_and_preserves_release_evidence(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("Harness v3", readme)
        self.assertIn("Agent Harness", readme)
        self.assertIn("docs/index.md", readme)
        self.assertIn(".harness/project.yaml", readme)
        self.assertIn("docs/releases/v2.0.0.md", readme)
        self.assertIn("별도 명시적 승인", readme)

    def test_setup_skill_uses_an_explicit_installed_skill_root(self) -> None:
        skill = (ROOT / "skills/setup-agent-harness/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("<skill-root>/scripts/core_harness.py", skill)
        self.assertNotIn("python scripts/core_harness.py", skill)

    def test_release_notes_exist_and_name_the_verified_surfaces(self) -> None:
        notes = (ROOT / "docs/releases/v2.0.0.md").read_text(encoding="utf-8")

        self.assertIn("# Personal Agent Harness v2.0.0", notes)
        self.assertIn("18 public Skills", notes)
        self.assertIn("Brownfield", notes)
        self.assertIn("Verification", notes)
        self.assertIn("https://github.com/young-sub/Skill_Management/tree/v2.0.0", notes)

    def test_remote_update_has_separate_revision_bound_passed_evidence(self) -> None:
        candidate = json.loads((ROOT / "distribution" / "release-candidate.json").read_text(encoding="utf-8"))
        smoke = candidate["external_install_smoke"]
        self.assertEqual(smoke["comparison_scope"], "complete_relative_file_set_sha256")
        remote = smoke["remote_github_update"]
        self.assertEqual(remote["status"], "passed")
        self.assertEqual(remote["source_package"], "young-sub/Skill_Management")
        self.assertIn("-SourceType github", remote["command"])
        self.assertIn("-ExpectedSourceCommit", remote["command"])
        self.assertIn("/tree/release-smoke-", remote["candidate_source_package"])
        self.assertTrue(remote["evidence_path"].endswith(".json"))
        evidence = candidate["evidence"]
        self.assertEqual(evidence["local_source_install_refresh"]["status"], "passed")
        self.assertEqual(evidence["remote_github_update"]["status"], "passed")
        self.assertNotEqual(
            evidence["local_source_install_refresh"]["evidence_kind"],
            evidence["remote_github_update"]["evidence_kind"],
        )


if __name__ == "__main__":
    unittest.main()
