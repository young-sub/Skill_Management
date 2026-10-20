"""Both native catalogs resolve to the same complete, current release bytes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PluginMarketplaceTests(unittest.TestCase):
    def test_catalogs_and_release_match_current_builder(self):
        codex = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        claude = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(codex['name'], claude['name'])
        self.assertEqual(len(codex['plugins']), 1)
        self.assertEqual(len(claude['plugins']), 1)
        self.assertEqual(codex['plugins'][0]['source']['source'], 'local')
        self.assertEqual(codex['plugins'][0]['source']['path'], claude['plugins'][0]['source'])
        package = ROOT / claude['plugins'][0]['source']
        manifest = json.loads((package / 'plugin.json').read_text())
        self.assertEqual(manifest['name'], codex['plugins'][0]['name'])
        self.assertEqual(manifest['name'], claude['plugins'][0]['name'])
        inventory = json.loads((package / 'package-files.json').read_text())['files']
        actual = {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in package.rglob('*') if p.is_file()}
        actual.pop('package-files.json')
        self.assertEqual(actual, inventory)
        with tempfile.TemporaryDirectory() as temporary:
            fresh = Path(temporary) / 'plugin'
            built = subprocess.run([sys.executable, str(ROOT / 'scripts/build_plugin.py'),
                                    '--output', str(fresh)], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            expected = json.loads((fresh / 'package-files.json').read_text())['files']
            # Provenance belongs to the frozen source, not later documentation commits.
            expected.pop('build-origin.json')
            inventory.pop('build-origin.json')
            self.assertEqual(set(expected), set(inventory))
            for name in expected:
                # Git checkout EOL conversion varies by host; inventory above stays byte-exact.
                self.assertEqual(
                    (fresh / name).read_bytes().replace(b'\r\n', b'\n'),
                    (package / name).read_bytes().replace(b'\r\n', b'\n'),
                    name,
                )
