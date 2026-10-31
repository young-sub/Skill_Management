"""The install-only `plugin` branch carries exactly the catalogs and plugins of its source commit."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('publish_plugin_branch', ROOT / 'scripts/publish_plugin_branch.py')
publish_branch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish_branch)


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), '-c', 'core.quotepath=false', *args], capture_output=True,
                          text=True, encoding='utf-8', check=True).stdout


class PluginBranchTests(unittest.TestCase):
    def test_branch_holds_only_install_files_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'r'
            subprocess.run(['git', 'clone', '-q', '--no-checkout', '--no-local', str(ROOT), str(repo)], check=True)
            for key, value in (('user.name', 'Plugin Branch Test'), ('user.email', 'test@example.invalid')):
                git(repo, 'config', key, value)  # CI runners have no Git identity for commit-tree
            first = publish_branch.publish(repo=repo, source='HEAD')
            self.assertTrue(first['changed'])
            names = git(repo, 'ls-tree', '-r', '--name-only', 'plugin').split('\n')[:-1]
            self.assertEqual({n for n in names if '/' not in n}, {'README.md', '.gitattributes'})
            self.assertEqual({n.split('/')[0] for n in names if '/' in n}, set(publish_branch.PATHS))
            # Every published plugin/catalog blob is the source blob, byte for byte.
            source = git(repo, 'ls-tree', '-r', 'HEAD', '--', *publish_branch.PATHS)
            published = git(repo, 'ls-tree', '-r', 'plugin', '--', *publish_branch.PATHS)
            self.assertEqual(published, source)
            self.assertIn('plugins/agentic-coding/** -text', git(repo, 'show', 'plugin:.gitattributes'))
            # Same content again: no new commit; the branch stays a fast-forward line.
            again = publish_branch.publish(repo=repo, source='HEAD')
            self.assertFalse(again['changed'])
            self.assertEqual(again['commit'], first['commit'])
            # Windows Git without core.longpaths fails past 259; a Codex staging prefix reached 153.
            self.assertEqual([n for n in names if len(n) > 259 - 153], [])
