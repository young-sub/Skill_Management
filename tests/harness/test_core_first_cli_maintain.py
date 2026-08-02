import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_cli", CORE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    item = {
        "id": "I-01", "title": "behavior", "behavior_type": "tool",
        "what": "deliver behavior", "steps": ["input", "output"], "terms": [],
        "tests": [{"id": "T-01", "target": "output", "method": "run", "expected": "pass", "selector": "python -m unittest sample"}],
        "done": [{"id": "D-01", "criterion": "output is delivered"}],
        "depends_on": [], "non_goals": [], "decision": {"state": "resolved"},
        "material_risks": [], "priority": "core",
    }
    second = json.loads(json.dumps(item))
    second.update({"id": "I-02", "title": "report", "depends_on": ["I-01"]})
    return {
        "schema_version": 3, "work_id": "W-cli", "goal": "deliver",
        "scope": "one capability", "non_goals": [], "items": [item, second],
    }


class CoreFirstCliMaintainTests(unittest.TestCase):
    def test_public_cli_exposes_complete_skill_lifecycle(self) -> None:
        core = load_core()
        commands = set(core._cli_parser()._subparsers._group_actions[0].choices)
        self.assertTrue({
            "inventory", "render-design", "authorize", "render-result", "impacted",
            "cleanup-plan", "cleanup-apply", "recover", "baseline", "start", "amend",
            "complete", "commit", "worktree-create", "worktree-integrate", "close", "sweep", "delete", "maintain", "install-cohort", "activate",
        }.issubset(commands))

    def test_installed_cli_default_authorizes_canonical_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            contract_path = Path(temp_dir) / "contract.json"
            contract_path.write_text(json.dumps(contract()), encoding="utf-8")
            completed = subprocess.run(
                ["python", str(ROOT / "skills" / "design-goal" / "scripts" / "core_harness.py"),
                 "authorize", "--contract", str(contract_path), "--intent", "default",
                 "--actor", "policy", "--at", "2026-08-02T12:00:00+09:00"],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "default_authorized")
            self.assertEqual(payload["contract"]["authorization"]["mode"], "default")

    def test_maintain_reports_stable_rules_without_mutating_repository(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "docs").mkdir()
            (root / "docs" / "index.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            before = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file() and ".git" not in path.parts}
            project = {
                "paths": {"documentation_entrypoint": "docs/index.md"},
                "impact": {"rules": [], "feature_selectors": {}, "full_triggers": []},
                "baseline": {"findings": []},
            }
            report = core.maintain_harness(root, project)
            rule_ids = {finding["rule_id"] for finding in report["findings"]}
            self.assertIn("MAINT-DOC-REACHABILITY", rule_ids)
            self.assertIn("MAINT-IMPACT-UNMAPPED", rule_ids)
            self.assertIn("MAINT-GIT-WORKTREE", report["checks"])
            after = {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file() and ".git" not in path.parts}
            self.assertEqual(before, after)

    def test_each_harness_skill_links_its_bundled_contract_resources(self) -> None:
        expected = {
            "setup-agent-harness": ("schemas/project.schema.json", "references/documentation-policy.md"),
            "design-goal": ("schemas/contract.schema.json", "references/human-readability-policy.md"),
            "execute-codex-goal": ("schemas/contract.schema.json", "references/testing-policy.md"),
            "close-goal": ("schemas/contract.schema.json", "references/testing-policy.md"),
            "maintain-agent-harness": ("schemas/project.schema.json", "references/testing-policy.md"),
            "diagnose": ("references/goal-execution-policy.md",),
        }
        for skill, links in expected.items():
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            for link in links:
                self.assertIn(f"]({link})", text, f"{skill}:{link}")

    def test_atomic_cohort_install_replaces_legacy_helpers_and_preserves_unrelated_skills(self) -> None:
        core = load_core()
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "skills"
            for skill in core.HARNESS_INSTALL_SKILLS:
                (install_root / skill / "scripts").mkdir(parents=True)
                (install_root / skill / "SKILL.md").write_text("Harness V2\n", encoding="utf-8")
            (install_root / "execute-codex-goal" / "scripts" / "goal_runtime.py").write_text("legacy\n", encoding="utf-8")
            (install_root / "unrelated" ).mkdir()
            (install_root / "unrelated" / "keep.txt").write_text("keep\n", encoding="utf-8")

            installed = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root),
            )

            self.assertEqual(installed["status"], "installed", installed)
            self.assertEqual(core.inspect_installed_cohort(install_root, manifest)["status"], "complete")
            self.assertFalse((install_root / "execute-codex-goal" / "scripts" / "goal_runtime.py").exists())
            self.assertEqual((install_root / "unrelated" / "keep.txt").read_text(encoding="utf-8"), "keep\n")
            self.assertTrue(installed["tree_digest"].startswith("sha256:"))
            expected = set(core._cohort_manifest_files(manifest)) | {
                "maintain-agent-harness/resources/public-resource-manifest.json",
            }
            actual = {
                path.relative_to(install_root).as_posix()
                for skill in core.HARNESS_INSTALL_SKILLS
                for path in (install_root / skill).rglob("*") if path.is_file()
            }
            self.assertEqual(actual, expected)
            self.assertFalse(any(path.suffix == ".pyc" for path in install_root.rglob("*")))

    def test_installed_cohort_rejects_undeclared_files_and_bytecode(self) -> None:
        core = load_core()
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "skills"
            installed = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            extra = install_root / "design-goal" / "scripts" / "__pycache__" / "rogue.cpython-312.pyc"
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_bytes(b"legacy")

            inspected = core.inspect_installed_cohort(install_root, manifest)

            self.assertEqual(inspected["status"], "invalid")
            self.assertIn(
                "installed_resource_extra:design-goal/scripts/__pycache__/rogue.cpython-312.pyc",
                inspected["blockers"],
            )

    def test_atomic_cohort_install_restores_exact_previous_cohort_on_fault(self) -> None:
        core = load_core()
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "skills"
            before = {}
            for index, skill in enumerate(core.HARNESS_INSTALL_SKILLS):
                path = install_root / skill / "SKILL.md"
                path.parent.mkdir(parents=True)
                content = f"legacy-{index}\r\n".encode()
                path.write_bytes(content)
                before[skill] = content

            outcome = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root), fault_after=3,
            )

            self.assertEqual(outcome["status"], "rolled_back", outcome)
            for skill, content in before.items():
                self.assertEqual((install_root / skill / "SKILL.md").read_bytes(), content)
            self.assertFalse(any(install_root.parent.glob(".harness-cohort-stage-*")))
            self.assertFalse(any(install_root.parent.glob(".harness-cohort-backup-*")))


if __name__ == "__main__":
    unittest.main()
