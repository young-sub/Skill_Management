"""Repository adapter checks use real commands in a disposable Git project."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / 'scripts/verify_product.py'
CAPTURE = ROOT / 'scripts/run_check.py'


class VerifyProductTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '.harness').mkdir()
        (self.root / 'docs').mkdir()
        (self.root / '.gitignore').write_text('evidence/\n__pycache__/\n')
        (self.root / 'docs/feature-map.md').write_text(
            '| Feature ID | Name | Action | Result and invariant | Domain | Side effects | Command IDs |\n'
            '| --- | --- | --- | --- | --- | --- | --- |\n'
            '| native-verification | Check | Run | Honest result | tests | evidence | fixture |\n')
        self.argv = [sys.executable, '-m', 'unittest', 'suite']
        (self.root / '.harness/project.yaml').write_text(json.dumps({'commands': {
            'fixture': {'id': 'fixture', 'argv': self.argv, 'working_directory': '.',
                        'runtime': 'python', 'platform': 'any', 'capability': 'fixture'}}}))
        self.suite = self.root / 'suite.py'
        self.suite.write_text('import unittest\nclass Behavior(unittest.TestCase):\n'
                              '    def test_result(self): self.assertEqual(2 + 2, 4)\n')
        self.git('init')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@localhost',
                 'commit', '-m', 'fixture')
        self.output = self.root / 'evidence/run.json'

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args],
                              capture_output=True, check=True)

    def verify(self, *args):
        result = subprocess.run([sys.executable, str(VERIFIER), '--root', str(self.root),
                                 '--feature', 'native-verification', '--check', 'fixture', *args],
                                capture_output=True, text=True, timeout=20)
        self.assertTrue(result.stdout.strip().startswith('{'), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def run_check(self):
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
        record = json.loads(self.output.read_text())
        self.assertIsNone(record['behavior_verdict'])
        self.assertEqual(record['check'], 'fixture')
        self.assertEqual(record['feature'], 'native-verification')
        self.assertEqual(record['run_id'], verdict['run_id'])
        self.assertGreater(verdict['tests_run'], 0)
        return record

    def test_real_command_is_bound_to_feature_and_current_source(self):
        record = self.run_check()
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)

    def test_failure_skip_and_zero_tests_never_pass(self):
        for body, expected in [
            ('import unittest\nclass T(unittest.TestCase):\n def test_fail(self): self.fail("defect")\n', 'ISSUES'),
            ('import unittest\n@unittest.skip("unavailable")\nclass T(unittest.TestCase):\n def test_skip(self): pass\n', 'BLOCKED'),
            ('import unittest\n', 'BLOCKED')]:
            with self.subTest(expected=expected, body=body):
                self.suite.write_text(body)
                path = self.root / 'evidence' / (str(len(list(self.root.glob('evidence/*')))) + '.json')
                code, verdict = self.verify('--output', str(path))
                self.assertNotEqual(code, 0)
                self.assertEqual(verdict['status'], expected, verdict)

    def test_stale_source_and_wrong_binding_are_blocked(self):
        record = self.run_check()
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', 'another-run')
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.suite.write_text(self.suite.read_text() + '# changed after execution\n')
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual(verdict['status'], 'BLOCKED')

    def test_unlinked_missing_or_wrong_target_evidence_never_passes(self):
        record = self.run_check()
        for key, value in [('feature', 'another-feature'), ('check', 'another-check'),
                           ('cwd', str(self.root.parent)), ('argv', ['other-tool']),
                           ('execution', 'timeout'), ('execution', 'unavailable')]:
            with self.subTest(key=key, value=value):
                changed = dict(record, **{key: value})
                self.output.write_text(json.dumps(changed))
                code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
                self.assertNotEqual(code, 0)
                self.assertEqual(verdict['status'], 'BLOCKED', verdict)
        self.output.unlink()
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual(verdict['status'], 'BLOCKED')

    def test_unknown_feature_or_command_does_not_execute(self):
        for args in [('--feature', 'absent'), ('--check', 'absent')]:
            code, verdict = self.verify('--output', str(self.output), *args)
            self.assertEqual(verdict['status'], 'BLOCKED')
            self.assertFalse(self.output.exists())

    def test_existing_output_is_not_reused_as_new_success(self):
        self.run_check()
        original = self.output.read_bytes()
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.assertEqual(self.output.read_bytes(), original)

    def test_source_changed_by_command_cannot_pass(self):
        self.suite.write_text('import unittest\nfrom pathlib import Path\n'
                             'class T(unittest.TestCase):\n'
                             ' def test_changes(self): Path("suite.py").write_text("# mutated")\n')
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual(verdict['status'], 'BLOCKED', verdict)

    def test_map_command_references_are_checked_before_execution(self):
        path = self.root / 'docs/feature-map.md'
        path.write_text(path.read_text().replace('| fixture |', '| missing-command |'))
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.assertFalse(self.output.exists())

    def test_real_timeout_and_malformed_record_are_blocked(self):
        self.suite.write_text('import time\ntime.sleep(30)\n')
        code, verdict = self.verify('--output', str(self.output), '--timeout', '0.2')
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.output.write_text('[]')
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', 'missing')
        self.assertEqual(verdict['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
