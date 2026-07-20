from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "test-install.ps1"


class InstallUpdateSmokeTests(unittest.TestCase):
    def run_fake_smoke(
        self, *, update_mode: str, expect_success: bool = True,
        source_type: str = "local", source_package: str | None = None,
    ) -> tuple[str, dict[str, object]]:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            destination = temp / "destination"
            evidence = temp / "evidence.json"
            fake = temp / "fake-skills.ps1"
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
                "  exit 0\n"
                "}\n"
                "Write-Error \"Unexpected arguments: $($CliArgs -join ' ')\"\nexit 2\n",
                encoding="utf-8",
            )
            env = dict(__import__("os").environ)
            env["HARNESS_FAKE_SOURCE"] = str(ROOT)
            env["HARNESS_FAKE_UPDATE_MODE"] = update_mode
            command = [
                "powershell", "-NoProfile", "-File", str(SCRIPT),
                "-RepositoryRoot", str(ROOT), "-DestinationRoot", str(destination),
                "-SkillsCommand", str(fake), "-SourceType", source_type,
                "-EvidencePath", str(evidence), "-VerifyUpdate",
            ]
            if source_package is not None:
                command.extend(("-SourcePackage", source_package))
            result = subprocess.run(
                command,
                capture_output=True, text=True, check=False, env=env,
            )

            diagnostics = result.stdout + result.stderr
            self.assertEqual(result.returncode == 0, expect_success, diagnostics)
            if not expect_success:
                return diagnostics, {}
            self.assertIn("Install and update smoke test passed for 18 public skills", diagnostics)
            for skill in (ROOT / "skills").glob("*/SKILL.md"):
                for provider in (".agents", ".claude"):
                    source_root = skill.parent
                    installed_root = destination / provider / "skills" / skill.parent.name
                    source_files = {
                        path.relative_to(source_root).as_posix(): path.read_bytes()
                        for path in source_root.rglob("*") if path.is_file()
                    }
                    installed_files = {
                        path.relative_to(installed_root).as_posix(): path.read_bytes()
                        for path in installed_root.rglob("*") if path.is_file()
                    }
                    self.assertEqual(installed_files, source_files)
            return diagnostics, json.loads(evidence.read_text(encoding="utf-8-sig"))

    def test_fake_cli_installs_and_updates_all_public_skills_for_both_providers(self) -> None:
        diagnostics, _ = self.run_fake_smoke(update_mode="full")
        self.assertNotIn("Native update unsupported/no-op for local source", diagnostics)

    def test_local_source_noop_update_falls_back_to_add_refresh(self) -> None:
        diagnostics, _ = self.run_fake_smoke(update_mode="noop")
        self.assertIn("Native update unsupported/no-op for local source", diagnostics)
        self.assertIn("Local source refresh passed for 18 public skills", diagnostics)

    def test_nested_resource_tamper_triggers_complete_tree_refresh(self) -> None:
        diagnostics, _ = self.run_fake_smoke(update_mode="tamper-resource")
        self.assertIn("Native update unsupported/no-op for local source", diagnostics)

    def test_remote_source_parameters_emit_machine_readable_evidence(self) -> None:
        _, evidence = self.run_fake_smoke(
            update_mode="full", source_type="github", source_package="young-sub/Skill_Management"
        )
        self.assertEqual(evidence["schema_version"], 1)
        self.assertEqual(evidence["source_package"], "young-sub/Skill_Management")
        self.assertEqual(evidence["source_type"], "github")
        self.assertEqual(evidence["complete_skill_tree_comparison"]["status"], "passed")
        self.assertEqual(evidence["remote_github_update"]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
