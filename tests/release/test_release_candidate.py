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
        self.assertEqual(candidate["stage"], "release-candidate")
        self.assertFalse(candidate["live_release"])
        self.assertIsNone(candidate["tag"])
        self.assertEqual(candidate["public_skill_count"], 18)
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

    def test_readme_documents_candidate_update_offline_smoke_and_pilot_limits(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("v2.0.0 release candidate", readme)
        self.assertIn("-VerifyUpdate", readme)
        self.assertIn("run-v2-pilots.py", readme)
        self.assertIn("real temporary implementation cycles", readme)
        self.assertIn("complete relative file set and SHA256", readme)
        self.assertIn("-SourcePackage young-sub/Skill_Management", readme)
        self.assertIn("-SourceType github", readme)
        self.assertIn("-EvidencePath", readme)
        self.assertIn("-ApproveRemoteEvidence", readme)
        self.assertIn("requires explicit approval", readme)

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
