from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = (
    REPO_ROOT
    / "skills"
    / "setup-agent-harness"
    / "scripts"
    / "bootstrap_project.py"
)


def load_bootstrap():
    spec = importlib.util.spec_from_file_location("bootstrap_toctou_test", BOOTSTRAP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_bootstrap(root: Path, action: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP), action, "--root", str(root), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


class SetupAgentHarnessTests(unittest.TestCase):
    def _write_relative_command(self, directory: Path, name: str) -> str:
        if os.name == "nt":
            path = directory / f"{name}.cmd"
            path.write_text("@echo off\r\ncd\r\n", encoding="utf-8")
            return f".\\{path.name}"
        path = directory / name
        path.write_text("#!/bin/sh\npwd\n", encoding="utf-8")
        path.chmod(0o755)
        return f"./{path.name}"

    def test_classifies_new_partial_overgrown_and_drift_repositories(self) -> None:
        cases = {
            "NEW_UNCONFIGURED": {},
            "EXISTING_PARTIAL": {"README.md": "# Existing project\n"},
            "EXISTING_OVERGROWN": {
                "AGENTS.md": "".join(f"rule {index}\n" for index in range(101))
            },
            "DRIFT_REPAIR": {
                "AGENTS.md": "# Local rules\n",
                "CLAUDE.md": "# Different rules\n",
                ".harness/project.yaml": "version: 2\n",
            },
        }

        for expected, files in cases.items():
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                for relative_path, content in files.items():
                    path = root / relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8", newline="\n")

                result = run_bootstrap(root, "plan")

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["classification"], expected)

    def test_plan_is_a_dry_run_and_reports_conflict_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = "# Existing project rules\n"
            (root / "AGENTS.md").write_text(existing, encoding="utf-8")
            (root / "CLAUDE.md").write_text("# Conflicting mirror\n", encoding="utf-8")
            before = sorted(path.relative_to(root) for path in root.rglob("*"))

            result = run_bootstrap(root, "plan")

            after = sorted(path.relative_to(root) for path in root.rglob("*"))
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, after)
            self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), existing)
            mirror_conflict = next(
                item for item in payload["conflicts"] if item["path"] == "CLAUDE.md"
            )
            self.assertIn("--- CLAUDE.md (existing)", mirror_conflict["diff"])
            self.assertIn("+++ CLAUDE.md (proposed)", mirror_conflict["diff"])

    def test_apply_refuses_conflicts_without_overwriting_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            agents = "# Existing project rules\n"
            claude = "# Conflicting mirror\n"
            (root / "AGENTS.md").write_text(agents, encoding="utf-8")
            (root / "CLAUDE.md").write_text(claude, encoding="utf-8")

            result = run_bootstrap(root, "apply", "--approve")

            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(payload["status"], "conflict")
            self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), agents)
            self.assertEqual((root / "CLAUDE.md").read_text(encoding="utf-8"), claude)
            self.assertFalse((root / ".harness/project.yaml").exists())

    def test_approved_clean_apply_creates_mirrors_hash_and_work_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            successful = json.dumps([sys.executable, "-c", "print('verified')"])
            missing = json.dumps(["definitely-missing-harness-command"])

            result = run_bootstrap(
                root,
                "apply",
                "--approve",
                "--verify-command-json",
                successful,
                "--verify-command-json",
                missing,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "applied")
            agents = (root / "AGENTS.md").read_bytes()
            self.assertEqual(agents, (root / "CLAUDE.md").read_bytes())
            project = (root / ".harness/project.yaml").read_text(encoding="utf-8")
            self.assertIn(sha256(agents).hexdigest(), project)
            self.assertIn(sys.executable.replace("\\", "/"), project)
            self.assertNotIn("definitely-missing-harness-command", project)
            self.assertIn("verified", payload["verification"]["recorded"][0]["stdout"])
            self.assertEqual(
                payload["verification"]["rejected"][0]["reason"],
                "command_not_found",
            )
            self.assertIn(".work/", (root / ".gitignore").read_text(encoding="utf-8"))
            for relative_path in (".work/active", ".work/archive", ".work/trash"):
                self.assertTrue((root / relative_path).is_dir(), relative_path)

    def test_relative_executable_is_resolved_and_run_from_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            command = self._write_relative_command(root, "verify-root")

            result = run_bootstrap(
                root,
                "apply",
                "--approve",
                "--verify-command-json",
                json.dumps([command]),
            )

            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(payload["verification"]["rejected"], [])
            observed = payload["verification"]["recorded"][0]["stdout"].strip()
            self.assertEqual(Path(observed).resolve(), root.resolve())

    def test_relative_executable_in_caller_cwd_is_not_accepted_for_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root = parent / "project"
            caller = parent / "caller"
            root.mkdir()
            caller.mkdir()
            command = self._write_relative_command(caller, "caller-only")

            result = subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    "apply",
                    "--root",
                    str(root),
                    "--approve",
                    "--verify-command-json",
                    json.dumps([command]),
                ],
                cwd=caller,
                capture_output=True,
                text=True,
                check=False,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(payload["verification"]["recorded"], [])
            self.assertEqual(
                payload["verification"]["rejected"][0]["reason"],
                "command_not_found",
            )

    def test_apply_rejects_reparse_component_without_external_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root = parent / "project"
            external = parent / "external"
            root.mkdir()
            external.mkdir()
            sentinel = external / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")
            try:
                os.symlink(external, root / ".harness", target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")

            result = run_bootstrap(root, "apply", "--approve")

            payload = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(payload["status"], "unsafe_target")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "unchanged\n")
            self.assertFalse((external / "project.yaml").exists())
            self.assertFalse((root / "AGENTS.md").exists())

    def test_apply_rechecks_containment_immediately_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            module = load_bootstrap()
            plan = module.build_plan(root)
            unsafe = [{"path": ".harness/project.yaml", "reason": "reparse_component:injected"}]
            check = mock.Mock(return_value=unsafe)

            with self.assertRaisesRegex(ValueError, "unsafe_target_after_verification"):
                module.apply_plan(root, plan, containment_check=check)

            check.assert_called_once_with(root)
            self.assertEqual(list(root.iterdir()), [])

    def test_apply_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            result = run_bootstrap(root, "apply")

            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads(result.stdout)["status"], "approval_required")
            self.assertEqual(list(root.iterdir()), [])

    def test_validate_rejects_instruction_drift_and_missing_recorded_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            agents = b"# Rules\n"
            (root / "AGENTS.md").write_bytes(agents)
            (root / "CLAUDE.md").write_bytes(b"# Drifted\n")
            (root / ".harness").mkdir()
            (root / ".harness/project.yaml").write_text(
                "version: 2\n"
                "project:\n"
                "  name: fixture\n"
                "  classification: existing_partial\n"
                "instructions:\n"
                "  authoritative: AGENTS.md\n"
                "  mirrors:\n"
                "    - CLAUDE.md\n"
                f"  sha256: {sha256(agents).hexdigest()}\n"
                "work:\n"
                "  root: .work\n"
                "  retention_days: 90\n"
                "  trash_grace_days: 30\n"
                "verification:\n"
                "  targeted_max_seconds: 30\n"
                "  feature_max_seconds: 120\n"
                "  fast_suite_max_seconds: 300\n"
                "  full_suite_runs_per_goal: 1\n"
                "  integration_default: impacted\n"
                "  live_default: false\n"
                "  eval_default: false\n"
                "  commands:\n"
                '    - ["definitely-missing-harness-command"]\n',
                encoding="utf-8",
            )

            result = run_bootstrap(root, "validate")

            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertIn("instruction_mirror_drift", payload["errors"])
            self.assertIn("recorded_command_not_found", payload["errors"])


if __name__ == "__main__":
    unittest.main()
