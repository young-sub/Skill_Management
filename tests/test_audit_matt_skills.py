from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.audit_matt_skills import audit_repository


class AuditMattSkillsTests(unittest.TestCase):
    def test_reports_missing_required_target_skill(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()

            report = audit_repository(root)

        self.assertTrue(
            any("domain-modeling" in error and "missing" in error for error in report.errors),
            report.errors,
        )

    def test_reports_folder_and_frontmatter_name_mismatch(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "skills" / "alpha"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: beta\ndescription: mismatch fixture\n---\n",
                encoding="utf-8",
            )

            report = audit_repository(root)

        self.assertTrue(
            any("alpha" in error and "beta" in error and "name mismatch" in error for error in report.errors),
            report.errors,
        )

    def test_reports_duplicate_active_skill_names(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("alpha", "beta"):
                skill_dir = root / "skills" / folder
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    "---\nname: shared\ndescription: duplicate fixture\n---\n",
                    encoding="utf-8",
                )

            report = audit_repository(root)

        self.assertTrue(
            any("duplicate skill name" in error and "shared" in error for error in report.errors),
            report.errors,
        )

    def test_reports_missing_linked_sibling_resource(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "skills" / "alpha"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: alpha\ndescription: resource fixture\n---\n"
                "Read [the contract](REFERENCE.md) before acting.\n",
                encoding="utf-8",
            )

            report = audit_repository(root)

        self.assertTrue(
            any("missing linked resource" in error and "REFERENCE.md" in error for error in report.errors),
            report.errors,
        )

    def test_reports_missing_codex_explicit_only_policy(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "skills" / "to-spec"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: to-spec\ndescription: explicit fixture\n"
                "disable-model-invocation: true\n---\n",
                encoding="utf-8",
            )

            report = audit_repository(root)

        self.assertTrue(
            any("to-spec" in error and "Codex explicit-only policy" in error for error in report.errors),
            report.errors,
        )

    def test_reports_missing_local_planning_publish_contract(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("to-spec", "to-tickets"):
                skill_dir = root / "skills" / name
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: local fixture\n---\n"
                    "Publish to GitHub.\n",
                    encoding="utf-8",
                )

            report = audit_repository(root)

        self.assertTrue(
            any("to-spec" in error and "local_markdown publish contract" in error for error in report.errors),
            report.errors,
        )
        self.assertTrue(
            any("to-tickets" in error and "local_markdown publish contract" in error for error in report.errors),
            report.errors,
        )

    def test_reports_legacy_active_skill_directory(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "skills" / "diagnose"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: diagnose\ndescription: legacy fixture\n---\n",
                encoding="utf-8",
            )

            report = audit_repository(root)

        self.assertTrue(
            any("legacy active skill" in error and "diagnose" in error for error in report.errors),
            report.errors,
        )

    def test_reports_legacy_skill_reference_on_active_surface(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "skills" / "router"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: router\ndescription: legacy reference fixture\n---\n"
                "Delegate requirements to `to-prd`.\n",
                encoding="utf-8",
            )

            report = audit_repository(root)

        self.assertTrue(
            any("legacy active reference" in error and "to-prd" in error for error in report.errors),
            report.errors,
        )

    def test_reports_when_entire_docs_plans_tree_is_not_gitignored(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            (root / ".gitignore").write_text("docs/plans/*.md\n", encoding="utf-8")

            report = audit_repository(root)

        self.assertTrue(
            any("docs/plans" in error and "entire" in error for error in report.errors),
            report.errors,
        )

    def test_reports_active_skill_without_upstream_ownership(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            skill_dir = root / "skills" / "alpha"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: alpha\ndescription: ownership fixture\n---\n",
                encoding="utf-8",
            )
            (root / "UPSTREAMS.md").write_text(
                "| Local skill | Ownership | Notes |\n|---|---|---|\n",
                encoding="utf-8",
            )

            report = audit_repository(root)

        self.assertTrue(
            any("alpha" in error and "ownership" in error for error in report.errors),
            report.errors,
        )

    def test_reports_missing_work_packet_route(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            mode_dir = root / "skills" / "work-packet" / "modes"
            mode_dir.mkdir(parents=True)
            for name in ("init", "ready", "run", "close"):
                (mode_dir / f"{name}.md").write_text("no delegated routes\n", encoding="utf-8")

            report = audit_repository(root)

        self.assertTrue(
            any("Work Packet route" in error and "to-spec" in error for error in report.errors),
            report.errors,
        )


if __name__ == "__main__":
    unittest.main()
