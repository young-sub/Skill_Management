import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.harness.test_core_first_design_execution import contract


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_cutover", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class CoreFirstCutoverTests(unittest.TestCase):
    def test_activation_blocks_nonterminal_legacy_graph_and_is_atomic(self) -> None:
        core = load_core()
        preview = core.preview_project_config({"version": 2, "project": {"name": "x"}, "work": {}})
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            installed_root = root / "installed"
            installed = core.install_harness_cohort(
                ROOT / "skills", installed_root, manifest,
                approved_install_root=str(installed_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            active = root / ".work" / "goals" / "active" / "W-1"
            active.mkdir(parents=True)
            (active / "work.json").write_text(json.dumps({"work_id": "W-1", "state": "in_progress"}), encoding="utf-8")

            blocked = core.activate_harness(
                root, preview, installed_root=installed_root, resource_manifest=manifest,
            )
            self.assertEqual(blocked["status"], "cutover_blocked")
            self.assertNotIn("harness", preview)

            shutil.rmtree(active)
            completed = root / ".work" / "goals" / "completed" / "2026-08" / "W-1"
            completed.mkdir(parents=True)
            (completed / "work.json").write_text(json.dumps({"work_id": "W-1", "state": "completed"}), encoding="utf-8")
            activated = core.activate_harness(
                root, preview, installed_root=installed_root, resource_manifest=manifest,
            )
            self.assertEqual(activated["status"], "activated")
            config = activated["project"]
            self.assertEqual(config["schema_version"], 3)
            self.assertNotIn("harness", config)

    def test_activation_rejects_incomplete_transactions_and_installed_hash_drift(self) -> None:
        core = load_core()
        preview = core.preview_project_config({"version": 2, "project": {"name": "x"}, "work": {}})
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            installed = root / "installed"
            installation = core.install_harness_cohort(
                ROOT / "skills", installed, manifest,
                approved_install_root=str(installed),
            )
            self.assertEqual(installation["status"], "installed", installation)
            journal = root / ".work" / "transactions" / "crashed" / "journal.json"
            journal.parent.mkdir(parents=True)
            journal.write_text(json.dumps({"status": "applying", "kind": "file_transaction"}), encoding="utf-8")
            blocked = core.activate_harness(
                root, preview, installed_root=installed, resource_manifest=manifest,
            )
            self.assertIn("incomplete_transaction:crashed:applying", blocked["blockers"])

            shutil.rmtree(root / ".work")
            (root / ".work" / "transactions" / "journal-less").mkdir(parents=True)
            journal_less = core.activate_harness(
                root, preview, installed_root=installed, resource_manifest=manifest,
            )
            self.assertEqual(journal_less["status"], "cutover_blocked")
            self.assertIn("transaction_journal_missing:journal-less", journal_less["blockers"])

            shutil.rmtree(root / ".work")
            execute_skill = installed / "execute-codex-goal" / "SKILL.md"
            execute_skill.write_text(execute_skill.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
            drifted = core.activate_harness(
                root, preview, installed_root=installed, resource_manifest=manifest,
            )
            self.assertEqual(drifted["status"], "cutover_blocked")
            self.assertTrue(any(item.startswith("installed_resource_drift:") for item in drifted["blockers"]))

    def test_repository_uses_current_router_config_and_docs(self) -> None:
        config = json.loads((ROOT / ".harness" / "project.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["schema_version"], 3)
        self.assertNotIn("harness", config)
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(agents, claude)
        self.assertLess(len(agents.splitlines()), 100)
        self.assertIn("docs/index.md", agents)
        self.assertIn(".harness/project.yaml", agents)
        self.assertNotIn("harness_v2_implementation_plan", agents)
        self.assertNotIn("`main`", agents)
        self.assertTrue((ROOT / "docs" / "index.md").is_file())
        self.assertFalse((ROOT / "docs" / "work-packets" / "ys" / "wp-20260802-007-core-first-harness.md").exists())
        self.assertEqual(set(config["commands"]), {"targeted", "feature", "lint", "type", "build", "full", "live", "eval"})
        self.assertEqual(load_core().build_mapping_plan(ROOT, config["paths"])["unresolved"], [])
        forward = "tests.harness.test_core_first_forward_workflows"
        self.assertIn(forward, config["commands"]["feature"]["argv"])
        harness_rule = next(rule for rule in config["impact"]["rules"] if rule["id"] == "harness-core")
        self.assertIn("tests/harness/test_core_first_forward_workflows.py", harness_rule["tests"])

    def test_active_skills_are_one_manifest_bound_cohort_without_version_branding(self) -> None:
        skills = ("setup-agent-harness", "design-goal", "execute-codex-goal", "close-goal", "maintain-agent-harness")
        for skill in skills:
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("Harness v3", text, skill)
            self.assertIn("scripts/core_harness.py", text, skill)
        execute = (ROOT / "skills" / "execute-codex-goal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("host Goal is optional", execute)
        self.assertNotIn("active Goal", execute)
        self.assertNotIn("contract hash", execute.lower())
        close = (ROOT / "skills" / "close-goal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Impacted", close)
        self.assertNotIn("Targeted, Feature, Fast, and Full must", close)
        for relative in (
            "authoring/scripts/contract_engine.py", "authoring/scripts/goal_runtime.py",
            "authoring/scripts/close_goal.py", "authoring/scripts/render_design_review.py",
            "authoring/scripts/render_completion_review.py", "authoring/scripts/maintain_harness.py",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)
        self.assertFalse((ROOT / "skills" / "project-agent-bootstrap").exists())
        self.assertNotIn("project-agent-bootstrap", load_core().HARNESS_INSTALL_SKILLS)
        workflow = (ROOT / "docs" / "agents" / "workflow.md").read_text(encoding="utf-8")
        self.assertIn(
            "Use the Goal contract lifecycle only when the global Work Packet threshold is met or the user explicitly selects it.",
            workflow,
        )

    def test_design_skill_routes_all_namespace_creation_through_design_create(self) -> None:
        for root in (ROOT / "authoring" / "skills", ROOT / "skills"):
            text = (root / "design-goal" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("`design-create`", text)
            self.assertIn("Never pre-create the work root", text)
            self.assertNotIn("Create `.work/goals/active/<work-id>/contract.json`", text)

    def test_repository_impact_and_ci_descriptors_cover_cutover_surfaces(self) -> None:
        core = load_core()
        config = json.loads((ROOT / ".harness" / "project.yaml").read_text(encoding="utf-8"))
        samples = [".harness/project.yaml", "tests/harness/test_core_first_cutover.py", ".github/workflows/validate-distribution.yml", "skill_recreate_plan.md"]
        selected = core.select_impacted_checks(samples, config)
        self.assertEqual(selected["unresolved"], [])
        self.assertTrue(selected["full_required"])
        workflow = (ROOT / ".github" / "workflows" / "validate-distribution.yml").read_text(encoding="utf-8")
        self.assertNotIn("run-v2-pilots.py", workflow)
        self.assertEqual(workflow.count('python -m unittest discover -s tests -p "test_*.py"'), 1)
        self.assertNotIn("Core-first representative workflows", workflow)

    def test_non_executable_skill_resources_do_not_trigger_full_but_shared_runtime_does(self) -> None:
        core = load_core()
        config = json.loads((ROOT / ".harness" / "project.yaml").read_text(encoding="utf-8"))

        independent = core.select_impacted_checks(["skills/finance-research/SKILL.md"], config)
        shared = core.select_impacted_checks(["skills/design-goal/SKILL.md"], config)
        template = core.select_impacted_checks(["authoring/templates/review/design-item-review.html"], config)
        runtime = core.select_impacted_checks(["authoring/scripts/core_harness.py"], config)

        self.assertEqual(independent["unresolved"], [])
        self.assertFalse(independent["full_required"])
        self.assertFalse(shared["full_required"])
        self.assertFalse(template["full_required"])
        self.assertTrue(runtime["full_required"])

    def test_ordinary_test_edits_are_impacted_only_but_discovery_controls_require_full(self) -> None:
        core = load_core()
        config = json.loads((ROOT / ".harness" / "project.yaml").read_text(encoding="utf-8"))

        ordinary = core.select_impacted_checks(
            ["tests/harness/test_core_first_design_execution.py"], config,
        )
        discovery = core.select_impacted_checks(["tests/harness/__init__.py"], config)

        self.assertEqual(ordinary["unresolved"], [])
        self.assertFalse(ordinary["full_required"])
        self.assertEqual(
            ordinary["feature_commands"],
            [{"feature": "harness-core", "argv": config["impact"]["feature_selectors"]["harness-core"]}],
        )
        self.assertTrue(discovery["full_required"])
        self.assertIn("test_discovery", discovery["full_trigger_ids"])

    def test_public_core_script_exposes_inventory_and_review_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            mapping = root / "mapping.json"
            mapping.write_text(json.dumps({"source_roots": ["src"], "test_roots": []}), encoding="utf-8")
            core_script = ROOT / "skills" / "setup-agent-harness" / "scripts" / "core_harness.py"
            inventory = subprocess.run([sys.executable, str(core_script), "inventory", "--root", str(root), "--mapping", str(mapping)], capture_output=True, text=True, check=False)
            self.assertEqual(inventory.returncode, 0, inventory.stderr)
            self.assertEqual(json.loads(inventory.stdout)["dynamic_evidence"]["status"], "unknown")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract(), ensure_ascii=False), encoding="utf-8")
            output = root / "design.html"
            design_script = ROOT / "skills" / "design-goal" / "scripts" / "core_harness.py"
            rendered = subprocess.run([sys.executable, str(design_script), "render-design", "--contract", str(contract_path), "--output", str(output)], capture_output=True, text=True, check=False)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertIn('data-item-id="I-01"', output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
