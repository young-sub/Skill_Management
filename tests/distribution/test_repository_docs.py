from pathlib import Path
import json
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class RepositoryDocsTests(unittest.TestCase):
    def test_readme_documents_the_skill_installation_lifecycle(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for heading in (
            "## Interactive installation",
            "## Non-interactive installation",
            "## Update",
            "## Uninstall",
            "## Project setup",
            "## Verification",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, readme)

        self.assertIn("npx skills@latest add young-sub/Skill_Management", readme)
        self.assertIn("-a codex", readme)
        self.assertIn("-a claude-code", readme)
        self.assertIn("npx skills update", readme)
        self.assertIn("npx skills remove", readme)

    def test_public_catalog_is_represented_in_human_inventory_docs(self) -> None:
        catalog = json.loads(
            (REPO_ROOT / "distribution" / "catalog.json").read_text(
                encoding="utf-8"
            )
        )
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        inventory = (
            REPO_ROOT / "docs" / "architecture" / "skill-inventory.md"
        ).read_text(encoding="utf-8")

        for skill_name in catalog["public_skills"]:
            with self.subTest(skill_name=skill_name):
                self.assertIn(f"`{skill_name}`", readme)
                self.assertIn(f"`{skill_name}`", inventory)


if __name__ == "__main__":
    unittest.main()
