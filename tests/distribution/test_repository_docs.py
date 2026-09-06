from pathlib import Path
import json
import re
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
        docs_root = ROOT / "docs"
        index = docs_root / "index.md"
        pending = [index.resolve()]
        reachable = set()

        while pending:
            source = pending.pop()
            if source in reachable:
                continue
            reachable.add(source)
            relative_source = source.relative_to(docs_root.resolve())
            if {"releases", "pilots"}.intersection(relative_source.parts):
                continue
            text = source.read_text(encoding="utf-8")
            links = re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", text)
            for raw_target in links:
                target = raw_target.split("#", 1)[0].strip()
                if not target or re.match(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|//)", target):
                    continue
                resolved = (source.parent / target).resolve()
                self.assertTrue(resolved.is_file() or resolved.is_dir(), f"{source}: {raw_target}")
                if resolved.suffix.lower() == ".md" and resolved.is_relative_to(docs_root.resolve()):
                    pending.append(resolved)

        self.assertTrue(reachable)
        for path in docs_root.rglob("*.md"):
            self.assertIn(path.resolve(), reachable, path)

    def test_current_docs_do_not_depend_on_removed_work_records(self) -> None:
        current = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md", ROOT / "README.md"]
        current.extend(
            path for path in ROOT.joinpath("docs").rglob("*.md")
            if not {"releases", "pilots"}.intersection(path.relative_to(ROOT / "docs").parts)
        )
        for path in current:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("harness_v2_implementation_plan.md", text, path)
            self.assertNotIn("docs/work-packets/", text, path)

if __name__ == "__main__":
    unittest.main()
