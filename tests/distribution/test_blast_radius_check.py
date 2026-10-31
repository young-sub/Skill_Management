"""The delegation boundary check reports worktree use, deny rules and exposed credentials without changing anything."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'authoring/scripts/blast_radius_check.py'
SPEC = importlib.util.spec_from_file_location('blast_radius_check', SCRIPT)
blast = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blast)
TEMPLATE = ROOT / 'authoring/templates/project/claude-delegation-settings.json'


class BlastRadiusCheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='blast-tests-')
        self.addCleanup(temporary.cleanup)
        self.main = Path(temporary.name) / 'main'
        self.main.mkdir()
        for args in (('init', '-q'), ('config', 'user.email', 't@example.invalid'), ('config', 'user.name', 'T')):
            subprocess.run(['git', '-C', str(self.main), *args], check=True)
        (self.main / 'app.py').write_text('x = 1\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(self.main), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.main), 'commit', '-qm', 'base'], check=True)
        self.task = Path(temporary.name) / 'task'
        subprocess.run(['git', '-C', str(self.main), 'worktree', 'add', '-q', str(self.task)], check=True)
        self.addCleanup(subprocess.run, ['git', '-C', str(self.main), 'worktree', 'remove', '--force', str(self.task)],
                        capture_output=True)

    def statuses(self, root, deploy=(), environment=None):
        return {f['check']: f for f in blast.check(root, list(deploy), environment or {})}

    def test_a_linked_worktree_with_the_template_and_no_credentials_passes(self):
        (self.task / '.claude').mkdir()
        (self.task / '.claude/settings.json').write_bytes(TEMPLATE.read_bytes())
        found = self.statuses(self.task)
        self.assertEqual({name: f['status'] for name, f in found.items()},
                         {'worktree': 'OK', 'deny': 'OK', 'secrets': 'OK'})

    def test_the_main_checkout_missing_rules_and_set_credentials_are_reported_by_name_only(self):
        found = self.statuses(self.main, deploy=['wrangler deploy'],
                              environment={'PROD_DATABASE_URL': 'postgres://secret-value', 'EMPTY_TOKEN': '', 'PATH': 'x'})
        self.assertEqual(found['worktree']['status'], 'MISSING')
        self.assertIn('wrangler deploy', found['deny']['detail'])
        self.assertIn('blockWritesOutsideWorkingDirectories', found['deny']['detail'])
        self.assertEqual(found['secrets']['detail'], 'credential-like variables set: PROD_DATABASE_URL')
        self.assertNotIn('secret-value', json.dumps(list(found.values())))

    def test_only_bash_rules_that_match_real_spellings_count(self):
        def deny(rules):
            (self.task / '.claude').mkdir(exist_ok=True)
            (self.task / '.claude/settings.json').write_text(json.dumps({'permissions': {
                'blockWritesOutsideWorkingDirectories': True, 'deny': rules}}), encoding='utf-8')
            return self.statuses(self.task, deploy=['wrangler deploy'])['deny']
        self.assertEqual(deny(['Read(git push --force:*)', 'Read(git push:*)', 'Read(wrangler deploy:*)'])['status'], 'MISSING')
        prefix_only = deny(['Bash(git push --force:*)', 'Bash(git push -f:*)', 'Bash(git push origin --delete:*)',
                            'Bash(wrangler deploy:*)'])
        self.assertEqual(prefix_only['status'], 'MISSING')
        self.assertIn('git push origin :feature', prefix_only['detail'])
        self.assertIn('git push upstream --delete feature', prefix_only['detail'])
        template = json.loads(TEMPLATE.read_text(encoding='utf-8'))['permissions']['deny']
        self.assertEqual(deny(template + ['Bash(wrangler deploy:*)'])['status'], 'OK')

    def test_credential_names_with_suffixes_are_found(self):
        found = self.statuses(self.task, environment={'GH_TOKEN_READONLY': 'x', 'TOKENIZERS_PARALLELISM': 'true'})
        self.assertEqual(found['secrets']['detail'], 'credential-like variables set: GH_TOKEN_READONLY')

    def test_the_cli_changes_nothing_and_exits_nonzero_on_gaps(self):
        before = sorted(p.name for p in self.main.iterdir())
        result = subprocess.run(['python', str(SCRIPT), '--root', str(self.main)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(sorted(p.name for p in self.main.iterdir()), before)


if __name__ == '__main__':
    unittest.main()
