from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class RepositoryDocsTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
