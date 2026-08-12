import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "authoring" / "scripts" / "core_harness.py"
PUBLIC_COMMANDS = {
    "setup-agent-harness": {
        "inventory", "cleanup-plan", "cleanup-apply", "recover", "install-cohort", "activate",
    },
    "design-goal": {"design-create", "render-design", "authorize"},
    "execute-codex-goal": {
        "baseline", "start", "impacted", "amend", "commit",
        "worktree-create", "worktree-integrate",
    },
    "close-goal": {"render-result", "complete", "close", "sweep", "delete"},
    "maintain-agent-harness": {"audit-work", "maintain", "recover"},
}


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_cli", CORE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def load_runtime(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def project_config() -> dict:
    return json.loads(
        (ROOT / "authoring" / "templates" / "project" / "project.yaml").read_text(encoding="utf-8")
    )


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
    def test_transaction_state_is_consistent_across_recover_legacy_and_maintain(self) -> None:
        core = load_core()
        project = project_config()
        cases = {
            "journal-less": "transaction_journal_missing:unfinished",
            "rollback-failed": "incomplete_transaction:unfinished:rollback_failed",
        }
        for case, expected in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                transaction = root / ".work" / "transactions" / "unfinished"
                transaction.mkdir(parents=True)
                if case == "rollback-failed":
                    (transaction / "journal.json").write_text(
                        json.dumps({"status": "rollback_failed", "kind": "file_transaction"}),
                        encoding="utf-8",
                    )

                recovered = core.recover_transactions(root)
                legacy = core.inspect_legacy_graph(root)
                maintained = core.maintain_harness(root, project)

                self.assertEqual(recovered["status"], "recovery_failed", recovered)
                self.assertIn(expected, recovered["errors"])
                self.assertIn(expected, legacy["blockers"])
                self.assertTrue(any(
                    finding["rule_id"] == "MAINT-TRANSACTION" and expected in finding["message"]
                    for finding in maintained["findings"]
                ))

    def test_recover_never_rolls_back_a_live_transaction_owner(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            journal = root / ".work" / "transactions" / "live" / "journal.json"
            journal.parent.mkdir(parents=True)
            journal.write_text(json.dumps({
                "status": "applying", "kind": "file_transaction",
                "owner_pid": os.getpid(), "files": [],
            }), encoding="utf-8")

            recovered = core.recover_transactions(root)

            self.assertEqual(recovered["status"], "recovery_failed", recovered)
            self.assertIn("transaction_in_progress:live", recovered["errors"])
            self.assertEqual(json.loads(journal.read_text(encoding="utf-8"))["status"], "applying")

    @unittest.skipUnless(os.name == "nt", "Windows process liveness semantics")
    def test_windows_process_liveness_fails_safe_on_access_denied(self) -> None:
        import ctypes

        core = load_core()
        kernel32 = mock.Mock()
        kernel32.OpenProcess.return_value = 0
        fake_windll = mock.Mock()
        fake_windll.kernel32 = kernel32

        with mock.patch.object(ctypes, "windll", fake_windll):
            kernel32.GetLastError.return_value = 5
            self.assertTrue(core._process_is_alive(424242))

            kernel32.GetLastError.return_value = 87
            self.assertFalse(core._process_is_alive(424242))

    def test_recover_rejects_non_object_operation_lock_payload(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / ".work" / "locks" / "transaction.lock"
            lock.parent.mkdir(parents=True)
            lock.write_text("[]\n", encoding="utf-8")

            recovered = core.recover_transactions(root)

            self.assertEqual(recovered["status"], "recovery_failed", recovered)
            self.assertIn("operation_lock_invalid:transaction", recovered["errors"])

    def test_maintain_reports_invalid_project_configuration(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            report = core.maintain_harness(
                Path(temp_dir), {"schema_version": 3, "unexpected": True},
            )

        self.assertEqual(report["status"], "findings")
        self.assertTrue(any(
            finding["rule_id"] == "MAINT-PROJECT-CONFIG"
            and "project_config:unknown_field:unexpected" in finding["message"]
            for finding in report["findings"]
        ))
    def test_public_cli_exposes_complete_skill_lifecycle(self) -> None:
        core = load_core()
        commands = set(core._cli_parser()._subparsers._group_actions[0].choices)
        self.assertEqual(commands, set().union(*PUBLIC_COMMANDS.values()))

    def test_isolated_installed_cohort_exposes_only_owned_commands_and_templates(self) -> None:
        core = load_core()
        manifest = json.loads(
            (ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            install_root = container / "skills"
            installed = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            all_commands = set().union(*PUBLIC_COMMANDS.values())
            for index, (skill, expected) in enumerate(PUBLIC_COMMANDS.items()):
                script = install_root / skill / "scripts" / "core_harness.py"
                completed = subprocess.run(
                    ["python", str(script), "--help"], text=True,
                    capture_output=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, f"{skill}: {completed.stderr}")
                runtime = load_runtime(script, f"installed_runtime_{index}")
                choices = set(runtime._cli_parser()._subparsers._group_actions[0].choices)
                self.assertEqual(choices, expected, skill)
                for command in expected:
                    self.assertIn(command, completed.stdout, f"{skill}:{command}")
                for command in all_commands - expected:
                    self.assertNotIn(command, choices, f"{skill}:{command}")

            execute_script = install_root / "execute-codex-goal" / "scripts" / "core_harness.py"
            rejected = subprocess.run(
                ["python", str(execute_script), "render-result"],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("invalid choice", rejected.stderr)
            self.assertNotIn("review_template_missing", rejected.stderr)

            contract_path = container / "contract.json"
            result_path = container / "result.json"
            output_path = container / "result.html"
            contract_path.write_text(json.dumps(contract()), encoding="utf-8")
            result_path.write_text(json.dumps({
                "items": [], "full": {"status": "not_required", "rule": "probe"},
            }), encoding="utf-8")
            close_script = install_root / "close-goal" / "scripts" / "core_harness.py"
            rendered = subprocess.run(
                [
                    "python", str(close_script), "render-result", "--contract", str(contract_path),
                    "--result", str(result_path), "--output", str(output_path),
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertIn('lang="ko"', output_path.read_text(encoding="utf-8"))

    def test_every_exposed_command_runs_with_only_isolated_cohort_resources(self) -> None:
        core = load_core()
        manifest = json.loads(
            (ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            install_root = container / "skills"
            installed = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            manifest_path = container / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            repo = container / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-b", "develop"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "agent@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Agent"], cwd=repo, check=True)
            (repo / ".gitignore").write_text(".work/\n/.worktree/\n", encoding="utf-8")
            (repo / "src").mkdir()
            (repo / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (repo / "docs").mkdir()
            (repo / "docs" / "index.md").write_text("# Docs\n", encoding="utf-8")
            project = project_config()
            project["paths"]["source_roots"] = ["src"]
            project["paths"]["test_roots"] = ["tests"]
            project["paths"]["documentation_entrypoint"] = "docs/index.md"
            project["impact"] = {
                "rules": [{
                    "id": "src", "source_prefixes": ["src/"], "tests": ["tests/test_app.py"],
                    "feature": "src", "triggers": [],
                }],
                "feature_selectors": {"src": ["python", "-m", "unittest", "tests.test_app"]},
                "full_triggers": [],
            }
            project["git"]["protected_branches"] = ["main"]
            project["git"]["branch_pattern"] = "wp-{work_id}-{slug}"
            project_root = repo / ".harness"
            project_root.mkdir()
            project_path = project_root / "project.yaml"
            project_path.write_text(json.dumps(project), encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=repo, check=True, capture_output=True)
            invoked = {skill: set() for skill in PUBLIC_COMMANDS}

            def invoke(skill: str, command: str, *arguments: str, cwd: Path | None = None) -> dict:
                completed = subprocess.run(
                    [
                        "python", str(install_root / skill / "scripts" / "core_harness.py"),
                        command, *arguments,
                    ],
                    cwd=cwd, text=True, capture_output=True, check=False,
                )
                self.assertEqual(
                    completed.returncode, 0,
                    f"{skill}:{command}\n{completed.stderr or completed.stdout}",
                )
                self.assertNotIn("review_template_missing", completed.stderr + completed.stdout)
                invoked[skill].add(command)
                return json.loads(completed.stdout)

            mapping_path = container / "mapping.json"
            mapping_path.write_text(json.dumps({"source_roots": ["src"], "test_roots": []}), encoding="utf-8")
            invoke("setup-agent-harness", "inventory", "--root", str(repo), "--mapping", str(mapping_path))
            request_path = container / "request.json"
            request_path.write_text(json.dumps({
                "mode": "document-only", "source_roots": ["src"],
                "ownership": {"durable_document_roots": ["docs"]},
                "operations": [{"action": "write", "path": "docs/generated.md", "content": "generated\n"}],
            }), encoding="utf-8")
            planned = invoke(
                "setup-agent-harness", "cleanup-plan", "--root", str(repo),
                "--request", str(request_path),
            )
            plan_path = container / "plan.json"
            plan_path.write_text(json.dumps(planned), encoding="utf-8")
            invoke(
                "setup-agent-harness", "cleanup-apply", "--root", str(repo),
                "--plan", str(plan_path), "--approval-digest", planned["plan"]["digest"],
            )
            invoke("setup-agent-harness", "recover", "--root", str(repo))
            second_install = container / "second-install"
            invoke(
                "setup-agent-harness", "install-cohort", "--source-root", str(install_root),
                "--install-root", str(second_install), "--manifest", str(manifest_path),
                "--approved-install-root", str(second_install),
            )
            invoke(
                "setup-agent-harness", "activate", "--root", str(repo),
                "--project", str(project_path), "--installed-root", str(install_root),
                "--manifest", str(manifest_path),
            )

            source = contract()
            source["work_id"] = "W-closure"
            source_path = container / "source.json"
            source_path.write_text(json.dumps(source), encoding="utf-8")
            invoke(
                "design-goal", "authorize", "--contract", str(source_path), "--intent", "default",
                "--actor", "policy", "--at", "2026-08-09T12:00:00+09:00",
            )
            created = invoke(
                "design-goal", "design-create", "--root", str(repo), "--contract", str(source_path),
                "--slug", "closure", "--work-id", "W-closure", "--actor", "policy",
                "--at", "2026-08-09T12:00:00+09:00",
            )
            self.assertEqual(created["status"], "created", created)
            contract_path = repo / created["path"] / "contract.json"
            rendered_design = container / "design.html"
            invoke(
                "design-goal", "render-design", "--contract", str(contract_path),
                "--output", str(rendered_design),
            )

            baseline = invoke("execute-codex-goal", "baseline", "--root", str(repo))
            baseline_path = container / "baseline.json"
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            started = invoke(
                "execute-codex-goal", "start", "--root", str(repo), "--work-id", "W-closure",
                "--slug", "closure", "--contract", str(contract_path),
            )
            self.assertEqual(started["status"], "started", started)
            invoke(
                "execute-codex-goal", "impacted", "--project", str(project_path),
                "--changed", "src/app.py",
            )
            value_path = container / "value.json"
            value_path.write_text(json.dumps("deliver safer behavior"), encoding="utf-8")
            invoke(
                "execute-codex-goal", "amend", "--contract", str(contract_path),
                "--item-id", "I-01", "--field", "what", "--value", str(value_path),
                "--message-id", "closure-amend", "--actor", "human",
                "--at", "2026-08-09T12:30:00+09:00", "--risk", "low",
            )
            (repo / "item.txt").write_text("item\n", encoding="utf-8")
            invoke(
                "execute-codex-goal", "commit", "--root", str(repo), "--item-id", "I-01",
                "--path", "item.txt", "--baseline", str(baseline_path),
                "--message", "feat(example): implement item",
            )
            base_branch = subprocess.run(
                ["git", "branch", "--show-current"], cwd=repo, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            worktree = repo / ".worktree" / "wt-closure-worktree"
            invoke(
                "execute-codex-goal", "worktree-create", "--root", str(repo), "--base", base_branch,
                "--branch", "closure-worktree",
            )
            worktree_baseline = invoke("execute-codex-goal", "baseline", "--root", str(worktree))
            worktree_baseline_path = container / "worktree-baseline.json"
            worktree_baseline_path.write_text(json.dumps(worktree_baseline), encoding="utf-8")
            (worktree / "worktree.txt").write_text("worktree\n", encoding="utf-8")
            invoke(
                "execute-codex-goal", "commit", "--root", str(worktree), "--item-id", "I-02",
                "--path", "worktree.txt", "--baseline", str(worktree_baseline_path),
                "--message", "feat(example): implement worktree item",
            )
            invoke(
                "execute-codex-goal", "worktree-integrate", "--root", str(repo),
                "--base", base_branch, "--branch", "closure-worktree",
                "--project", str(project_path), "--approved-exact-path", str(worktree),
            )

            result = {
                "items": [{
                    "id": item_id, "actual": "delivered", "actual_steps": ["input", "output"],
                    "checks": [{
                        "check_id": "T-01", "kind": "Targeted",
                        "command": "python -m unittest sample", "status": "passed",
                    }],
                    "criteria": [{
                        "criterion_id": "D-01", "criterion": "output is delivered",
                        "status": "passed", "evidence": "observed",
                    }],
                    "delta": {"material": False},
                } for item_id in ("I-01", "I-02")],
                "full": {"status": "not_required", "rule": "src"},
            }
            impact = {"full_required": False, "unresolved": [], "not_required_rule_ids": ["src"]}
            result_path = container / "result.json"
            impact_path = container / "impact.json"
            result_path.write_text(json.dumps(result), encoding="utf-8")
            impact_path.write_text(json.dumps(impact), encoding="utf-8")
            rendered_result = container / "result.html"
            invoke(
                "close-goal", "render-result", "--contract", str(contract_path),
                "--result", str(result_path), "--output", str(rendered_result),
            )
            invoke(
                "close-goal", "complete", "--contract", str(contract_path),
                "--result", str(result_path), "--impact", str(impact_path),
            )
            closed = invoke(
                "close-goal", "close", "--root", str(repo), "--work-id", "W-closure",
                "--contract", str(contract_path), "--result", str(result_path),
                "--impact", str(impact_path), "--at", "2026-08-09T12:00:00+09:00",
                "--completed-days", "30", "--trash-days", "7",
            )
            self.assertEqual(closed["status"], "completed", closed)
            invoke("close-goal", "sweep", "--root", str(repo), "--at", "2026-09-09T12:00:00+09:00")
            trash_target = ".work/goals/trash/2026-09-09/W-closure"
            invoke(
                "close-goal", "delete", "--root", str(repo), "--target", trash_target,
                "--approved-exact-target", trash_target, "--at", "2026-09-16T12:00:00+09:00",
            )

            invoke("maintain-agent-harness", "audit-work", "--root", str(repo))
            invoke(
                "maintain-agent-harness", "maintain", "--root", str(repo),
                "--project", str(project_path), "--installed-root", str(install_root),
                "--manifest", str(manifest_path), "--today", "2026-08-09",
            )
            invoke("maintain-agent-harness", "recover", "--root", str(repo))

            self.assertEqual(invoked, PUBLIC_COMMANDS)

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

    def test_design_create_invalid_root_is_a_failing_cli_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            source = contract()
            source["work_id"] = ""
            contract_path = container / "contract.json"
            contract_path.write_text(json.dumps(source), encoding="utf-8")

            completed = subprocess.run(
                [
                    "python", str(CORE), "design-create", "--root", str(container / "missing"),
                    "--contract", str(contract_path), "--slug", "feature",
                    "--actor", "policy", "--at", "2026-08-09T12:00:00+09:00",
                ],
                text=True, capture_output=True, check=False,
            )

            self.assertEqual(completed.returncode, 2, completed.stderr or completed.stdout)
            self.assertEqual(json.loads(completed.stdout)["status"], "invalid_root")

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

            real_hash = core._manifest_file_hash
            with mock.patch.object(core, "_manifest_file_hash", wraps=real_hash) as hash_file:
                installed = core.install_harness_cohort(
                    ROOT / "skills", install_root, manifest,
                    approved_install_root=str(install_root),
                )

            self.assertEqual(installed["status"], "installed", installed)
            self.assertEqual(hash_file.call_count, 2 * len(core._cohort_manifest_files(manifest)))
            self.assertEqual(core.inspect_installed_cohort(install_root, manifest)["status"], "complete")
            self.assertFalse((install_root / "execute-codex-goal" / "scripts" / "goal_runtime.py").exists())
            self.assertEqual((install_root / "unrelated" / "keep.txt").read_text(encoding="utf-8"), "keep\n")
            self.assertNotIn("tree_digest", installed)
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
            self.assertEqual(
                (install_root / core.COHORT_MANIFEST_RESOURCE).read_bytes(),
                (ROOT / "skills" / core.COHORT_MANIFEST_RESOURCE).read_bytes(),
            )

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

    def test_installed_cohort_rejects_internal_resource_aliases(self) -> None:
        core = load_core()
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "skills"
            installed = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            alias = install_root / "setup-agent-harness" / "scripts" / "core_harness.py"
            target = install_root / "execute-codex-goal" / "scripts" / "core_harness.py"
            alias.unlink()
            try:
                alias.symlink_to(target)
            except OSError as error:
                self.skipTest(f"file symlink unavailable: {error}")

            inspected = core.inspect_installed_cohort(install_root, manifest)

            self.assertEqual(inspected["status"], "invalid", inspected)
            self.assertIn(
                "installed_resource_alias:setup-agent-harness/scripts/core_harness.py",
                inspected["blockers"],
            )

    def test_installed_cohort_rejects_unexpected_empty_directories(self) -> None:
        core = load_core()
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "skills"
            installed = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            (install_root / "design-goal" / "empty").mkdir()

            inspected = core.inspect_installed_cohort(install_root, manifest)

            self.assertEqual(inspected["status"], "invalid", inspected)
            self.assertIn(
                "installed_directory_extra:design-goal/empty",
                inspected["blockers"],
            )

    def test_installed_cohort_rejects_manifest_metadata_drift(self) -> None:
        core = load_core()
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        drifted = json.loads(json.dumps(manifest))
        drifted["algorithm"] = "sha512"

        inspected = core.inspect_installed_cohort(Path(tempfile.gettempdir()) / "unused-cohort", drifted)

        self.assertEqual(inspected["status"], "invalid_manifest", inspected)
        self.assertIn("installed_manifest_invalid", inspected["blockers"])

    def test_installed_cohort_uses_exact_manifest_resources_not_skill_version_text(self) -> None:
        core = load_core()
        manifest = json.loads(
            (ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            installed_root = Path(temp_dir) / "skills"
            installed = core.install_harness_cohort(
                ROOT / "skills", installed_root, manifest,
                approved_install_root=str(installed_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            neutral = json.loads(json.dumps(manifest))
            for skill in core.HARNESS_INSTALL_SKILLS:
                relative = f"{skill}/SKILL.md"
                path = installed_root / relative
                text = path.read_text(encoding="utf-8")
                text = text.replace("Agent Harness v3", "Agent Harness").replace("Harness v3", "Agent Harness")
                path.write_text(text, encoding="utf-8", newline="\n")
                self.assertNotIn("Harness v3", path.read_text(encoding="utf-8"))
                neutral["files"][relative] = core._manifest_file_hash(path, neutral.get("hash_mode"))
            bundled = installed_root / core.COHORT_MANIFEST_RESOURCE
            bundled.write_text(json.dumps(neutral, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

            inspected = core.inspect_installed_cohort(installed_root, neutral)

            self.assertEqual(inspected["status"], "complete", inspected)
            self.assertEqual(inspected["skills"], list(core.HARNESS_INSTALL_SKILLS))

            truncated = json.loads(json.dumps(neutral))
            truncated["files"].pop("diagnose/SKILL.md")
            (installed_root / "diagnose" / "SKILL.md").unlink()
            bundled.write_text(json.dumps(truncated, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
            rejected = core.inspect_installed_cohort(installed_root, truncated)
            self.assertEqual(rejected["status"], "invalid_manifest")
            self.assertIn(
                "installed_manifest_required_missing:diagnose/SKILL.md",
                rejected["blockers"],
            )

    def test_installed_cohort_rejects_retired_alias_but_allows_unrelated_skill(self) -> None:
        core = load_core()
        manifest = json.loads((ROOT / "authoring" / "public-resource-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "skills"
            installed = core.install_harness_cohort(
                ROOT / "skills", install_root, manifest,
                approved_install_root=str(install_root),
            )
            self.assertEqual(installed["status"], "installed", installed)
            unrelated = install_root / "unrelated-skill" / "SKILL.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("unrelated\n", encoding="utf-8")
            alias = install_root / "project-agent-bootstrap" / "SKILL.md"
            alias.parent.mkdir(parents=True)
            alias.write_text("retired\n", encoding="utf-8")

            inspected = core.inspect_installed_cohort(install_root, manifest)

            self.assertEqual(inspected["status"], "invalid")
            self.assertIn(
                "retired_skill_present:project-agent-bootstrap",
                inspected["blockers"],
            )
            self.assertFalse(any("unrelated-skill" in blocker for blocker in inspected["blockers"]))

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
