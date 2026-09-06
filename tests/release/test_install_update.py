from __future__ import annotations

import json
from pathlib import Path
from pathlib import PurePosixPath
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "test-install.ps1"


class InstallUpdateSmokeTests(unittest.TestCase):
    def run_fake_smoke(
        self, *, update_mode: str, expect_success: bool = True,
        source_type: str = "local", source_package: str | None = None,
        approve_remote: bool = False, expected_source_commit: str | None = None,
        resolved_remote_commit: str | None = None,
        resolved_default_commit: str | None = None,
        leave_stale_harness_directories: bool = False,
    ) -> tuple[str, dict[str, object]]:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            destination = temp / "destination"
            evidence = temp / "evidence.json"
            fake = temp / "fake-skills.ps1"
            fake_git = temp / "fake-git.ps1"
            fake.write_text(
                "param([Parameter(ValueFromRemainingArguments=$true)]$CliArgs)\n"
                "$source = $env:HARNESS_FAKE_SOURCE\n"
                "if ($CliArgs[1] -eq 'add') {\n"
                "  foreach ($entry in Get-ChildItem -LiteralPath (Join-Path $source 'skills') -Directory) {\n"
                "    if (-not (Test-Path (Join-Path $entry.FullName 'SKILL.md'))) { continue }\n"
                "    foreach ($root in @('.agents\\skills', '.claude\\skills')) {\n"
                "      $target = Join-Path (Get-Location) (Join-Path $root $entry.Name)\n"
                "      New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null\n"
                "      if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }\n"
                "      Copy-Item -LiteralPath $entry.FullName -Destination $target -Recurse -Force\n"
                "      if (\n"
                "        $env:HARNESS_FAKE_STALE_HARNESS_DIRECTORIES -eq 'true' -and\n"
                "        $entry.Name -in @('setup-agent-harness', 'design-goal', 'execute-codex-goal', 'close-goal', 'maintain-agent-harness', 'diagnose')\n"
                "      ) {\n"
                "        New-Item -ItemType Directory -Path (Join-Path $target 'resources\\v3\\retired-empty') -Force | Out-Null\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "  exit 0\n"
                "}\n"
                "if (($CliArgs -join ' ') -eq 'skills update -p -y') {\n"
                "  if ($env:HARNESS_FAKE_UPDATE_MODE -eq 'noop') { exit 0 }\n"
                "  foreach ($entry in Get-ChildItem -LiteralPath (Join-Path $source 'skills') -Directory) {\n"
                "    if (-not (Test-Path (Join-Path $entry.FullName 'SKILL.md'))) { continue }\n"
                "    foreach ($root in @('.agents\\skills', '.claude\\skills')) {\n"
                "      $target = Join-Path (Get-Location) (Join-Path $root $entry.Name)\n"
                "      if ($env:HARNESS_FAKE_UPDATE_MODE -eq 'full') {\n"
                "        Remove-Item -LiteralPath $target -Recurse -Force\n"
                "        Copy-Item -LiteralPath $entry.FullName -Destination $target -Recurse -Force\n"
                "      } else {\n"
                "        Copy-Item -LiteralPath (Join-Path $entry.FullName 'SKILL.md') -Destination (Join-Path $target 'SKILL.md') -Force\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "  if ($env:HARNESS_FAKE_UPDATE_MODE -eq 'tamper-resource') {\n"
                "    $victim = Get-ChildItem -LiteralPath (Join-Path (Get-Location) '.agents\\skills') -Recurse -File | Where-Object Name -ne 'SKILL.md' | Select-Object -First 1\n"
                "    if ($null -ne $victim) { Set-Content -LiteralPath $victim.FullName -Value 'stale nested resource' -Encoding utf8 }\n"
                "  }\n"
                "  if ($env:HARNESS_FAKE_UPDATE_MODE -eq 'tamper-independent') {\n"
                "    $victim = Get-ChildItem -LiteralPath (Join-Path (Get-Location) '.agents\\skills\\finance-research') -Recurse -File | Select-Object -First 1\n"
                "    if ($null -ne $victim) { Set-Content -LiteralPath $victim.FullName -Value 'stale independent skill' -Encoding utf8 }\n"
                "  }\n"
                "  exit 0\n"
                "}\n"
                "Write-Error \"Unexpected arguments: $($CliArgs -join ' ')\"\nexit 2\n",
                encoding="utf-8",
            )
            fake_git.write_text(
                "param([Parameter(ValueFromRemainingArguments=$true)]$GitArgs)\n"
                "if ($GitArgs -contains '--symref') {\n"
                "  Write-Output \"ref: refs/heads/main`tHEAD\"\n"
                "  Write-Output \"$env:HARNESS_FAKE_DEFAULT_COMMIT`tHEAD\"\n"
                "  exit 0\n"
                "}\n"
                "Write-Output \"$env:HARNESS_FAKE_REMOTE_COMMIT`trefs/tags/release-smoke-test\"\n"
                "exit 0\n",
                encoding="utf-8",
            )
            env = dict(__import__("os").environ)
            env["HARNESS_FAKE_SOURCE"] = str(ROOT)
            env["HARNESS_FAKE_UPDATE_MODE"] = update_mode
            env["HARNESS_FAKE_STALE_HARNESS_DIRECTORIES"] = (
                "true" if leave_stale_harness_directories else "false"
            )
            env["HARNESS_FAKE_REMOTE_COMMIT"] = resolved_remote_commit or expected_source_commit or ""
            env["HARNESS_FAKE_DEFAULT_COMMIT"] = resolved_default_commit or expected_source_commit or ""
            command = [
                "powershell", "-NoProfile", "-File", str(SCRIPT),
                "-RepositoryRoot", str(ROOT), "-DestinationRoot", str(destination),
                "-SkillsCommand", str(fake), "-SourceType", source_type,
                "-EvidencePath", str(evidence), "-VerifyUpdate",
            ]
            if source_package is not None:
                command.extend(("-SourcePackage", source_package))
            if approve_remote:
                command.append("-ApproveRemoteEvidence")
            if expected_source_commit is not None:
                command.extend((
                    "-ExpectedSourceCommit", expected_source_commit,
                    "-GitCommand", str(fake_git),
                ))
            result = subprocess.run(
                command,
                capture_output=True, text=True, check=False, env=env,
            )

            diagnostics = result.stdout + result.stderr
            self.assertEqual(result.returncode == 0, expect_success, diagnostics)
            if not expect_success:
                return diagnostics, {}
            public_skill_count = len(list((ROOT / "skills").glob("*/SKILL.md")))
            self.assertIn(f"Install and update smoke test passed for {public_skill_count} public skills", diagnostics)
            for skill in (ROOT / "skills").glob("*/SKILL.md"):
                for provider in (".agents", ".claude"):
                    source_root = skill.parent
                    installed_root = destination / provider / "skills" / skill.parent.name
                    source_files = {
                        path.relative_to(source_root).as_posix(): path.read_bytes()
                        for path in source_root.rglob("*")
                        if path.is_file()
                        and path.suffix != ".pyc"
                        and "__pycache__" not in path.parts
                    }
                    installed_files = {
                        path.relative_to(installed_root).as_posix(): path.read_bytes()
                        for path in installed_root.rglob("*")
                        if path.is_file()
                        and path.suffix != ".pyc"
                        and "__pycache__" not in path.parts
                    }
                    self.assertEqual(installed_files, source_files)
                    source_directories = {
                        parent.as_posix()
                        for relative in source_files
                        for parent in PurePosixPath(relative).parents
                        if parent.as_posix() != "."
                    }
                    installed_directories = {
                        path.relative_to(installed_root).as_posix()
                        for path in installed_root.rglob("*") if path.is_dir()
                    }
                    self.assertEqual(installed_directories, source_directories)
            return diagnostics, json.loads(evidence.read_text(encoding="utf-8-sig"))

    def test_fake_cli_installs_and_updates_all_public_skills_for_both_providers(self) -> None:
        diagnostics, _ = self.run_fake_smoke(update_mode="full")
        self.assertNotIn("Native update unsupported/no-op for local source", diagnostics)

    def test_install_atomically_replaces_harness_roots_and_removes_stale_directories(self) -> None:
        self.run_fake_smoke(
            update_mode="noop",
            leave_stale_harness_directories=True,
        )

    def test_local_source_noop_update_falls_back_to_add_refresh(self) -> None:
        diagnostics, evidence = self.run_fake_smoke(update_mode="noop")
        self.assertIn("Native update unsupported/no-op for local source", diagnostics)
        public_skill_count = len(list((ROOT / "skills").glob("*/SKILL.md")))
        self.assertIn(f"Local source refresh passed for {public_skill_count} public skills", diagnostics)
        self.assertEqual(evidence["schema_version"], 2)
        self.assertEqual(evidence["evidence_kind"], "local_source_install_refresh")
        expected_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        expected_tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        self.assertEqual(evidence["git_commit"], expected_commit)
        self.assertEqual(evidence["git_tree"], expected_tree)
        self.assertIsInstance(evidence["git_dirty"], bool)
        self.assertIsInstance(evidence["dirty_paths"], list)
        self.assertIn("python", evidence["tool_versions"])
        self.assertIn("skills_command", evidence["tool_versions"])
        self.assertEqual(evidence["result"], "passed")

    def test_nested_resource_tamper_triggers_complete_tree_refresh(self) -> None:
        diagnostics, _ = self.run_fake_smoke(update_mode="tamper-resource")
        self.assertIn("Native update unsupported/no-op for local source", diagnostics)

    def test_remote_update_drift_triggers_complete_tree_refresh(self) -> None:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        diagnostics, evidence = self.run_fake_smoke(
            update_mode="tamper-independent",
            source_type="github",
            source_package="https://github.com/young-sub/Skill_Management/tree/main",
            approve_remote=True,
            expected_source_commit=commit,
        )
        self.assertIn("Native update left drift; running complete source refresh", diagnostics)
        self.assertEqual(evidence["remote_github_update"]["status"], "passed")

    def test_remote_source_parameters_emit_machine_readable_evidence(self) -> None:
        _, evidence = self.run_fake_smoke(
            update_mode="full", source_type="github", source_package="young-sub/Skill_Management"
        )
        self.assertEqual(evidence["schema_version"], 2)
        self.assertEqual(evidence["source_package"], "young-sub/Skill_Management")
        self.assertEqual(evidence["source_type"], "github")
        self.assertEqual(evidence["complete_skill_tree_comparison"]["status"], "passed")
        self.assertEqual(evidence["evidence_kind"], "install_and_update_smoke")
        self.assertEqual(evidence["remote_github_update"]["status"], "not_verified")
        self.assertIn("remote_github_update", evidence["unverified_checks"])
        self.assertNotEqual(evidence["source_type"], "local_source_install_refresh")

    def test_approved_named_remote_ref_bound_to_expected_commit_emits_remote_update_evidence(self) -> None:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        _, evidence = self.run_fake_smoke(
            update_mode="noop",
            source_type="github",
            source_package="https://github.com/young-sub/Skill_Management/tree/release-smoke-400dc9f",
            approve_remote=True,
            expected_source_commit=commit,
        )
        self.assertEqual(evidence["evidence_kind"], "remote_github_update")
        self.assertEqual(evidence["remote_github_update"]["status"], "passed")
        self.assertNotIn("remote_github_update", evidence["unverified_checks"])
        self.assertEqual(
            evidence["installed_tree_before_update_sha256"],
            evidence["installed_tree_after_update_sha256"],
        )
        self.assertRegex(evidence["installed_tree_after_update_sha256"], r"^[0-9A-F]{64}$")

    def test_approved_named_remote_ref_rejects_resolution_to_another_commit(self) -> None:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        diagnostics, _ = self.run_fake_smoke(
            update_mode="noop",
            source_type="github",
            source_package="https://github.com/young-sub/Skill_Management/tree/release-smoke-test",
            approve_remote=True,
            expected_source_commit=commit,
            resolved_remote_commit="0" * 40,
            expect_success=False,
        )
        self.assertIn("Remote source ref does not resolve to ExpectedSourceCommit", diagnostics)

    def test_approved_remote_update_rejects_default_branch_at_another_commit(self) -> None:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        diagnostics, _ = self.run_fake_smoke(
            update_mode="noop",
            source_type="github",
            source_package="https://github.com/young-sub/Skill_Management/tree/release-smoke-test",
            approve_remote=True,
            expected_source_commit=commit,
            resolved_default_commit="0" * 40,
            expect_success=False,
        )
        self.assertIn("Remote default branch does not resolve to ExpectedSourceCommit", diagnostics)


if __name__ == "__main__":
    unittest.main()
