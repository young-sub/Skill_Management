"""Exercise the distributable tree, including its installed command consumer."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PluginPackageTests(unittest.TestCase):
    def test_package_runs_without_checkout_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'plugin'
            command = [sys.executable, str(ROOT / 'scripts/build_plugin.py'),
                       '--output', str(package)]
            built = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            manifest = json.loads((package / 'plugin.json').read_text())
            compatibility = json.loads((package / '.codex-plugin/plugin.json').read_text())
            self.assertEqual(manifest['name'], compatibility['name'])
            catalog = json.loads((ROOT / 'distribution/catalog.json').read_text())
            self.assertEqual({p.parent.name for p in (package / 'skills').glob('*/SKILL.md')},
                             set(catalog['public_skills']))
            capture = root / 'capture.json'
            run = subprocess.run([sys.executable, str(package / 'scripts/run_check.py'),
                                  '--cwd', str(root), '--output', str(capture), '--',
                                  sys.executable, '-c', 'print(6 * 7)'], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            observed = json.loads(capture.read_text())
            self.assertEqual(observed['stdout'].strip(), '42')
            self.assertEqual(observed['exit_code'], 0)
            self.assertIsNone(observed['behavior_verdict'])
            for script in ('project_workflow.py', 'verification_results.py'):
                help_result = subprocess.run([
                    sys.executable, str(package / 'skills/agent-workflow/scripts' / script),
                    '--help'], cwd=root, capture_output=True)
                self.assertEqual(help_result.returncode, 0, help_result.stderr)
            user_file = package / 'user-note.txt'
            user_file.write_text('preserve me')
            again = subprocess.run(command, capture_output=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(user_file.read_text(), 'preserve me')
            inventory = json.loads((package / 'package-files.json').read_text())
            self.assertNotIn('user-note.txt', inventory['files'])
            self.assertFalse(any('.work' in p or '.env' in p for p in inventory['files']))
            updater = subprocess.run([sys.executable, str(package / 'scripts/update_plugin.py'),
                                      '--help'], cwd=root, capture_output=True)
            self.assertEqual(updater.returncode, 0, updater.stderr)


if __name__ == '__main__':
    unittest.main()
