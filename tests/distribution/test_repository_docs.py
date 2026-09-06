from pathlib import Path
import json
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]


class RepositoryDocsTests(unittest.TestCase):
    def test_git_policy_requires_commits_for_complete_functional_units(self) -> None:
        repository = json.loads((ROOT / ".harness" / "project.yaml").read_text(encoding="utf-8"))
        template = json.loads(
            (ROOT / "authoring" / "templates" / "project" / "project.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(repository["git"]["commit_per_item"])
        self.assertTrue(template["git"]["commit_per_item"])

    def test_current_documents_are_reachable_and_links_resolve(self) -> None:
        index = ROOT / "docs" / "index.md"
        text = index.read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        self.assertTrue(links)
        for target in links:
            self.assertTrue((index.parent / target).resolve().is_file(), target)
        for path in ROOT.joinpath("docs").rglob("*.md"):
            if "releases" in path.parts:
                continue
            self.assertIn(path.relative_to(ROOT / "docs").as_posix(), [target.split("#", 1)[0] for target in links] + ["index.md"], path)

    def test_current_docs_do_not_depend_on_removed_work_records(self) -> None:
        current = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md", ROOT / "README.md", *ROOT.joinpath("docs").rglob("*.md")]
        for path in current:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("harness_v2_implementation_plan.md", text, path)
            self.assertNotIn("docs/work-packets/", text, path)

    def test_current_user_surfaces_do_not_brand_the_harness_with_a_version(self) -> None:
        skills = (
            "setup-agent-harness", "design-goal", "execute-codex-goal",
            "diagnose", "close-goal", "maintain-agent-harness",
        )
        current = [
            ROOT / "README.md", ROOT / "authoring" / "README.md",
            ROOT / ".harness" / "project.yaml",
            *(path for path in ROOT.joinpath("docs").rglob("*.md")
              if "releases" not in path.parts and "pilots" not in path.parts),
            *(ROOT / "authoring" / "skills" / skill / "SKILL.md" for skill in skills),
            *(ROOT / "skills" / skill / "SKILL.md" for skill in skills),
        ]
        for path in current:
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?i)\bharness v3\b", str(path))
            self.assertNotIn("harness-v3", text.casefold(), str(path))
        self.assertTrue((ROOT / "docs" / "architecture" / "harness.md").is_file())
        self.assertFalse((ROOT / "docs" / "architecture" / "harness-v3.md").exists())

        completed = subprocess.run(
            [sys.executable, str(ROOT / "authoring" / "scripts" / "core_harness.py"), "--help"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotRegex(completed.stdout, r"(?i)\bharness v3\b")


if __name__ == "__main__":
    unittest.main()
