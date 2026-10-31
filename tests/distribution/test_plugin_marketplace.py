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
        codex_own, claude_own = codex['plugins'][0], claude['plugins'][0]
        self.assertEqual(codex_own['source']['source'], 'local')
        self.assertEqual(codex_own['source']['path'], claude_own['source'])
        package = ROOT / claude_own['source']
        manifest = json.loads((package / 'plugin.json').read_text())
        self.assertEqual(manifest['name'], codex_own['name'])
        self.assertEqual(manifest['name'], claude_own['name'])
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

    def test_readme_installs_from_the_plugin_branch(self):
        # Hosts must read the install-only branch (test_plugin_branch), not the whole repository.
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        commands = [l for l in readme.splitlines() if 'plugin marketplace add' in l and 'Skill_Management' in l]
        self.assertEqual(len(commands), 4)
        for line in commands:
            self.assertRegex(line, r'@plugin$|#plugin$|--ref plugin$', line)

    def test_optional_upstream_entries_track_latest(self):
        # Opt-in upstream plugins: separate installs, never pinned, so upstream releases need no catalog edit.
        codex = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        claude = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        expected = {
            'claude': {'diagram-design': ('github', 'cathrynlavery/diagram-design'),
                       'humanize-korean': ('github', 'epoko77-ai/im-not-ai')},
            # im-not-ai's codex/ folder resolves scripts and references outside itself, so Codex
            # installs a local launcher that keeps a full upstream checkout (test_humanize_korean_codex).
            'codex': {'diagram-design': ('url', 'https://github.com/cathrynlavery/diagram-design.git'),
                      'humanize-korean': ('local', './plugins/humanize-korean-codex')},
        }
        for host, catalog in (('claude', claude), ('codex', codex)):
            optional = {entry['name']: entry['source'] for entry in catalog['plugins'][1:]}
            self.assertEqual(set(optional), set(expected[host]), host)
            for name, source in optional.items():
                kind, location = expected[host][name]
                self.assertEqual(source['source'], kind, name)
                self.assertEqual(source.get('repo', source.get('url', source.get('path'))), location, name)
                self.assertNotIn('ref', source, name)
                self.assertNotIn('sha', source, name)
            self.assertNotIn('dependencies', catalog['plugins'][0], host)
