import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import sys


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_setup", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def tracked_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*") if path.is_file() and ".work" not in path.parts
    }


class CoreFirstSetupTests(unittest.TestCase):
    def test_static_inventory_never_executes_repository_content(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "odd-source").mkdir()
            (root / "odd-source" / "service.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "checks").mkdir()
            (root / "checks" / "check_service.py").write_text("assert True\n", encoding="utf-8")
            (root / "README.md").write_text("Run `python checks/check_service.py`\n", encoding="utf-8")
            mapping = {"source_roots": ["odd-source"], "test_roots": ["checks"]}

            with mock.patch("subprocess.run", side_effect=AssertionError("must not execute")):
                inventory = core.static_inventory(root, mapping)

            self.assertEqual(inventory["dynamic_evidence"]["status"], "unknown")
            self.assertEqual(inventory["paths"]["source_roots"], ["odd-source"])
            self.assertEqual(inventory["paths"]["test_roots"], ["checks"])
            self.assertIn("odd-source/service.py", inventory["production_hashes"])
            self.assertIn(["python", "checks/check_service.py"], inventory["declared_commands"])

    def test_git_inventory_never_opens_ignored_reserved_or_local_files(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / ".gitignore").write_text(
                ".venv/\nvenv/\n.cache/\n.scratch/\n.work/\nagent-env.*.md\nlocal-secret.json\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", ".gitignore", "src/app.py"], cwd=root, check=True)
            for relative in (
                ".venv/huge.json", "venv/locked.toml", ".cache/data.json",
                ".scratch/note.md", ".work/private.json", "agent-env.ys.md", "local-secret.json",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("secret\n", encoding="utf-8")
            ignored = {str((root / relative).resolve()) for relative in (
                ".venv/huge.json", "venv/locked.toml", ".cache/data.json",
                ".scratch/note.md", ".work/private.json", "agent-env.ys.md", "local-secret.json",
            )}
            original_read_text = Path.read_text
            original_read_bytes = Path.read_bytes

            def guarded_read_text(path: Path, *args, **kwargs):
                if str(path.resolve()) in ignored:
                    raise AssertionError(f"ignored file read: {path}")
                return original_read_text(path, *args, **kwargs)

            def guarded_read_bytes(path: Path, *args, **kwargs):
                if str(path.resolve()) in ignored:
                    raise AssertionError(f"ignored file read: {path}")
                return original_read_bytes(path, *args, **kwargs)

            with mock.patch.object(Path, "read_text", guarded_read_text), mock.patch.object(Path, "read_bytes", guarded_read_bytes):
                inventory = core.static_inventory(root, {"source_roots": ["src"], "test_roots": []})

            self.assertIn("src/app.py", inventory["files"])
            self.assertTrue(all(not any(path.startswith(prefix) for prefix in (".venv/", "venv/", ".cache/", ".scratch/", ".work/")) for path in inventory["files"]))
            self.assertNotIn("agent-env.ys.md", inventory["files"])
            self.assertNotIn("local-secret.json", inventory["files"])

    def test_mapping_first_plan_preserves_coherent_brownfield_paths(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ("knowledge", "checks", "product"):
                (root / relative).mkdir()
            (root / "knowledge" / "index.md").write_text("# Current\n", encoding="utf-8")
            plan = core.build_mapping_plan(root, {
                "source_roots": ["product"], "test_roots": ["checks"],
                "durable_document_roots": ["knowledge"],
                "documentation_entrypoint": "knowledge/index.md",
            })
            self.assertEqual(plan["mutations"], [])
            self.assertEqual(plan["mapping"]["durable_document_roots"], ["knowledge"])
            self.assertEqual(plan["unresolved"], [])

    def test_ambiguous_ownership_and_canonical_aliases_fail_without_mutation(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "shared").mkdir()
            before = tracked_snapshot(root)
            errors = core.validate_path_owners(root, {
                "source": ["shared"], "tests": ["shared"],
            }, case_sensitive=False)
            self.assertTrue(any(error.startswith("owner_overlap:") for error in errors))
            self.assertEqual(tracked_snapshot(root), before)

    def test_fixture_nesting_is_compatible_and_inventory_maps_static_git_ci_authority(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ("src", "tests/fixtures", ".git/worktrees/feature", ".github/workflows", "docs"):
                (root / relative).mkdir(parents=True)
            (root / ".git" / "HEAD").write_text("ref: refs/heads/develop\n", encoding="utf-8")
            (root / ".git" / "worktrees" / "feature" / "gitdir").write_text("C:/tmp/feature/.git\n", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text("run: python -m unittest\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("Read docs/index.md\n", encoding="utf-8")
            (root / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")
            mapping = {"source_roots": ["src"], "test_roots": ["tests"], "fixture_roots": ["tests/fixtures"], "durable_document_roots": ["docs"]}
            self.assertEqual(core.validate_path_owners(root, {"source": ["src"], "tests": ["tests"], "fixtures": ["tests/fixtures"], "documents": ["docs"]}), [])
            inventory = core.static_inventory(root, mapping)
            self.assertEqual(inventory["git"]["branch"], "develop")
            self.assertEqual(inventory["git"]["worktrees"], ["feature"])
            self.assertEqual(inventory["ci_files"], [".github/workflows/ci.yml"])
            self.assertIn("AGENTS.md", inventory["authority_candidates"])

    def test_v2_migration_requires_bound_approval_and_rolls_back_fault(self) -> None:
        core = load_core()
        legacy = {"version": 2, "project": {"name": "sample"}, "work": {"root": ".work"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = core.build_project_migration(root, legacy)
            denied = core.apply_transaction(root, plan, approval_digest="wrong")
            self.assertEqual(denied["status"], "approval_required")
            self.assertFalse((root / ".harness" / "project.yaml").exists())

            failed = core.apply_transaction(root, plan, approval_digest=plan["digest"], fault_after=1)
            self.assertEqual(failed["status"], "rolled_back")
            self.assertFalse((root / ".harness" / "project.yaml").exists())

            applied = core.apply_transaction(root, plan, approval_digest=plan["digest"])
            self.assertEqual(applied["status"], "committed")
            config = json.loads((root / ".harness" / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual(config["schema_version"], 3)
            self.assertEqual(config["harness"]["active_cohort"], "v2")

    def test_transaction_recovers_exact_tree_after_process_exit(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = b"original\r\n"
            (root / "existing.txt").write_bytes(original)
            plan = core._plan_with_digest({
                "schema_version": 3,
                "mode": "document-only",
                "root": str(root.resolve()),
                "operations": [
                    {"action": "write", "path": "existing.txt", "content": "changed\n"},
                    {"action": "write", "path": "created.txt", "content": "created\n"},
                ],
                "source_roots": [],
                "production_hashes_before": {},
            })
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            child = """
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('core_crash_child', Path(sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
plan = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
module.apply_transaction(Path(sys.argv[2]), plan, approval_digest=plan['digest'], crash_after=1)
"""

            crashed = subprocess.run(
                [sys.executable, "-c", child, str(CORE_PATH), str(root), str(plan_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(crashed.returncode, 91, crashed.stderr)
            self.assertNotEqual((root / "existing.txt").read_bytes(), original)

            recovered = core.recover_transactions(root)

            self.assertEqual(recovered["status"], "recovered")
            self.assertEqual((root / "existing.txt").read_bytes(), original)
            self.assertFalse((root / "created.txt").exists())

    def test_document_move_preserves_bytes_updates_links_and_production_hashes(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_bytes(b"VALUE = 1\r\n")
            (root / "notes").mkdir()
            original = b"# Guide\r\n"
            (root / "notes" / "guide.md").write_bytes(original)
            (root / "README.md").write_text("See notes/guide.md\n", encoding="utf-8")
            plan = core.build_cleanup_plan(root, mode="document-only", source_roots=["src"], ownership={
                "durable_document_roots": ["notes", "docs"], "human_guide_roots": ["README.md"],
            }, operations=[
                {"action": "move", "source": "notes/guide.md", "target": "docs/guide.md"},
                {"action": "replace", "path": "README.md", "old": "notes/guide.md", "new": "docs/guide.md"},
            ])
            result = core.apply_transaction(root, plan, approval_digest=plan["digest"])
            self.assertEqual(result["status"], "committed")
            self.assertEqual((root / "docs" / "guide.md").read_bytes(), original)
            self.assertIn("docs/guide.md", (root / "README.md").read_text(encoding="utf-8"))
            self.assertEqual(result["production_hashes_before"], result["production_hashes_after"])

    def test_cleanup_modes_reject_cross_owner_paths_before_plan_creation(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ("src", "tests", "docs", ".github/workflows"):
                (root / relative).mkdir(parents=True)
            (root / "README.md").write_text("current\n", encoding="utf-8")
            ownership = {
                "source_roots": ["src"], "test_roots": ["tests"],
                "durable_document_roots": ["docs"], "human_guide_roots": ["README.md"],
                "ci_roots": [".github/workflows"],
            }

            with self.assertRaisesRegex(ValueError, "mode_path_forbidden:test-only:README.md"):
                core.build_cleanup_plan(
                    root, mode="test-only", source_roots=["src"], ownership=ownership,
                    operations=[{"action": "write", "path": "README.md", "content": "changed\n"}],
                )
            with self.assertRaisesRegex(ValueError, "mode_path_forbidden:document-only:tests"):
                core.build_cleanup_plan(
                    root, mode="document-only", source_roots=["src"], ownership=ownership,
                    operations=[{"action": "write", "path": "tests/new_test.py", "content": "pass\n"}],
                )

    def test_mapping_validates_human_work_owners_and_unknown_test_impact(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ("src", "docs", ".work"):
                (root / relative).mkdir(parents=True)
            (root / "docs" / "index.md").write_text("# docs\n", encoding="utf-8")
            plan = core.build_mapping_plan(root, {
                "source_roots": ["src"], "test_roots": [], "fixture_roots": [],
                "generated_roots": [], "durable_document_roots": ["docs"],
                "human_guide_roots": ["docs"], "ephemeral_work_root": ".work",
                "documentation_entrypoint": "docs/index.md",
            }, impact={"rules": []})

            self.assertTrue(any(error.startswith("owner_overlap:documents:docs:human:") for error in plan["unresolved"]))
            self.assertIn("unknown_source_test_impact:src", plan["unresolved"])

    def test_baseline_suppression_requires_exact_unexpired_fingerprint(self) -> None:
        core = load_core()
        baseline = {"rule_id": "docs.orphan", "location": "docs/a.md", "severity": "medium", "fingerprint": "abc", "review_until": "2026-08-31"}
        self.assertTrue(core.finding_is_baselined(baseline, dict(baseline), today="2026-08-02"))
        changed = dict(baseline, fingerprint="def")
        self.assertFalse(core.finding_is_baselined(baseline, changed, today="2026-08-02"))
        self.assertFalse(core.finding_is_baselined(baseline, dict(baseline), today="2026-09-01"))

    def test_dynamic_baseline_runs_only_an_approved_capability(self) -> None:
        core = load_core()
        descriptor = {
            "id": "feature-auth", "capability": "auth", "argv": [sys.executable, "-c", "print('ok')"],
            "working_directory": ".", "source_revision": "abc123", "runtime": "python",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch("subprocess.run", side_effect=AssertionError("unapproved execution")):
                denied = core.run_dynamic_baseline(root, descriptor, approved_capabilities=[])
            self.assertEqual(denied["status"], "not_authorized")
            collected = core.run_dynamic_baseline(root, descriptor, approved_capabilities=["auth"])
            self.assertEqual(collected["status"], "passed")
            self.assertEqual(collected["argv"], descriptor["argv"])
            self.assertEqual(collected["source_revision"], "abc123")
            self.assertGreaterEqual(collected["duration_seconds"], 0)

    def test_semantic_test_inventory_ignores_paths_but_preserves_outcomes(self) -> None:
        core = load_core()
        before = [{"capability": "auth", "suite": "Login", "test": "accepts", "parameter": "admin", "path": "tests/old.py", "outcome": "passed"}]
        after = [{"capability": "auth", "suite": "Login", "test": "accepts", "parameter": "admin", "path": "checks/new.py", "outcome": "passed"}]
        self.assertEqual(core.compare_semantic_test_inventory(before, after), [])
        after[0]["outcome"] = "skipped"
        self.assertIn("semantic_test_inventory_changed", core.compare_semantic_test_inventory(before, after))


if __name__ == "__main__":
    unittest.main()
