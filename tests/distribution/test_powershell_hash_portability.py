from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PowerShellHashPortabilityTests(unittest.TestCase):
    def test_distribution_scripts_do_not_depend_on_get_file_hash(self) -> None:
        for relative in (
            "scripts/test-install.ps1",
            "scripts/sync-skill-resources.ps1",
            "scripts/validate-distribution.ps1",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("Get-FileHash", source, relative)
            self.assertIn("hash-utils.ps1", source, relative)

    def test_dotnet_sha256_helper_matches_python(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sample = Path(temporary) / "sample.bin"
            sample.write_bytes(b"portable-hash\x00\xff")
            helper = ROOT / "scripts" / "hash-utils.ps1"
            command = (
                f". '{helper}'; "
                f"Get-Sha256Hex -LiteralPath '{sample}'"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), hashlib.sha256(sample.read_bytes()).hexdigest())

    def test_resource_manifest_serialization_is_powershell_version_independent(self) -> None:
        sync_script = (ROOT / "scripts/sync-skill-resources.ps1").read_text(encoding="utf-8")
        manifest = (ROOT / "authoring/public-resource-manifest.json").read_text(encoding="utf-8")

        self.assertIn("ConvertTo-StableManifestJson", sync_script)
        self.assertNotIn("ConvertTo-Json -Depth 5", sync_script)
        self.assertIn("SortedDictionary[string, string]", sync_script)
        self.assertIn("[System.StringComparer]::Ordinal", sync_script)
        self.assertEqual(manifest, manifest.strip() + "\n")
        self.assertNotIn("\n ", manifest)


if __name__ == "__main__":
    unittest.main()
