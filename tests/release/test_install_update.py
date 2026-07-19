from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "test-install.ps1"


class InstallUpdateSmokeTests(unittest.TestCase):
    def run_fake_smoke(self, *, native_update_noop: bool) -> str:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            destination = temp / "destination"
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
                "  if ($env:HARNESS_FAKE_UPDATE_NOOP -eq '1') { exit 0 }\n"
                "  foreach ($entry in Get-ChildItem -LiteralPath (Join-Path $source 'skills') -Directory) {\n"
                "    if (-not (Test-Path (Join-Path $entry.FullName 'SKILL.md'))) { continue }\n"
                "    foreach ($root in @('.agents\\skills', '.claude\\skills')) {\n"
                "      Copy-Item -LiteralPath (Join-Path $entry.FullName 'SKILL.md') -Destination (Join-Path (Get-Location) (Join-Path $root (Join-Path $entry.Name 'SKILL.md'))) -Force\n"
                "    }\n"
                "  }\n"
                "  exit 0\n"
                "}\n"
                "Write-Error \"Unexpected arguments: $($CliArgs -join ' ')\"\nexit 2\n",
                encoding="utf-8",
            )
            env = dict(__import__("os").environ)
            env["HARNESS_FAKE_SOURCE"] = str(ROOT)
            env["HARNESS_FAKE_UPDATE_NOOP"] = "1" if native_update_noop else "0"
            result = subprocess.run(
                ["powershell", "-NoProfile", "-File", str(SCRIPT),
                 "-RepositoryRoot", str(ROOT), "-DestinationRoot", str(destination),
                 "-SkillsCommand", str(fake), "-VerifyUpdate"],
                capture_output=True, text=True, check=False, env=env,
            )

            diagnostics = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, diagnostics)
            self.assertIn("Install and update smoke test passed for 18 public skills", diagnostics)
            for skill in (ROOT / "skills").glob("*/SKILL.md"):
                for provider in (".agents", ".claude"):
                    installed = destination / provider / "skills" / skill.parent.name / "SKILL.md"
                    self.assertEqual(installed.read_bytes(), skill.read_bytes())
            return diagnostics

    def test_fake_cli_installs_and_updates_all_public_skills_for_both_providers(self) -> None:
        diagnostics = self.run_fake_smoke(native_update_noop=False)
        self.assertNotIn("Native update unsupported/no-op for local source", diagnostics)

    def test_local_source_noop_update_falls_back_to_add_refresh(self) -> None:
        diagnostics = self.run_fake_smoke(native_update_noop=True)
        self.assertIn("Native update unsupported/no-op for local source", diagnostics)
        self.assertIn("Local source refresh passed for 18 public skills", diagnostics)


if __name__ == "__main__":
    unittest.main()
