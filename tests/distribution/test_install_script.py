from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SCRIPT = REPO_ROOT / "scripts" / "test-install.ps1"


class InstallScriptTests(unittest.TestCase):
    def test_installs_local_source_into_isolated_codex_and_claude_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            fixture_repo = temp_root / "fixture-repo"
            skill_dir = fixture_repo / "skills" / "fixture-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: fixture\n---\n",
                encoding="utf-8",
            )
            install_root = temp_root / "install-root"
            fake_cli = temp_root / "fake-skills-cli.ps1"
            fake_cli.write_text(
                "param([Parameter(ValueFromRemainingArguments=$true)]$CliArgs)\n"
                "$source = $CliArgs[2]\n"
                "$expected = @('skills', 'add', $source, '--skill', '*', '-a', 'codex', '-a', 'claude-code', '--copy', '-y')\n"
                "if (($CliArgs -join \"`n\") -ne ($expected -join \"`n\")) {\n"
                "    Write-Error \"Unexpected CLI arguments: $($CliArgs -join ' ')\"\n"
                "    exit 1\n"
                "}\n"
                "$skill = Join-Path $source 'skills\\fixture-skill'\n"
                "$codex = Join-Path (Get-Location) '.agents\\skills\\fixture-skill'\n"
                "$claude = Join-Path (Get-Location) '.claude\\skills\\fixture-skill'\n"
                "New-Item -ItemType Directory -Path (Split-Path $codex -Parent) -Force | Out-Null\n"
                "New-Item -ItemType Directory -Path (Split-Path $claude -Parent) -Force | Out-Null\n"
                "Copy-Item -LiteralPath $skill -Destination $codex -Recurse\n"
                "Copy-Item -LiteralPath $skill -Destination $claude -Recurse\n"
                "exit 0\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-File",
                    str(INSTALL_SCRIPT),
                    "-RepositoryRoot",
                    str(fixture_repo),
                    "-DestinationRoot",
                    str(install_root),
                    "-SkillsCommand",
                    str(fake_cli),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            codex_skill = install_root / ".agents" / "skills" / "fixture-skill" / "SKILL.md"
            claude_skill = install_root / ".claude" / "skills" / "fixture-skill" / "SKILL.md"
            diagnostics = f"{result.stdout}\n{result.stderr}"
            self.assertEqual(result.returncode, 0, diagnostics)
            self.assertTrue(codex_skill.is_file(), diagnostics)
            self.assertTrue(claude_skill.is_file(), diagnostics)
            self.assertIn(
                "Install smoke test passed for codex and claude-code.",
                diagnostics,
            )


if __name__ == "__main__":
    unittest.main()
