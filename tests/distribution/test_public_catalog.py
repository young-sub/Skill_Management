from pathlib import Path
import json
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class PublicCatalogTests(unittest.TestCase):
    def test_only_supported_and_professional_skills_are_public(self) -> None:
        expected = {
            "finance-research",
            "find-skills",
            "frontend-design",
            "explore-idea",
            "design-goal",
            "execute-codex-goal",
            "diagnose",
            "close-goal",
            "maintain-agent-harness",
            "multi-agent-review",
            "prototype",
            "setup-agent-harness",
            "teach",
            "theme-factory",
            "webapp-testing",
            "web-artifacts-builder",
            "write-a-skill",
            "zoom-out",
        }
        actual = {
            skill_file.parent.name
            for skill_file in (REPO_ROOT / "skills").glob("*/SKILL.md")
        }
        catalog = json.loads(
            (REPO_ROOT / "distribution" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        declared = set(catalog["public_skills"])

        self.assertSetEqual(declared, expected)
        self.assertSetEqual(actual, declared)


if __name__ == "__main__":
    unittest.main()
