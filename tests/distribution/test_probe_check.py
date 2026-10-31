"""Real Git fixtures for the standalone synthetic-fault runner; no network calls."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[2] / 'authoring/scripts/probe_check.py'
SPEC = importlib.util.spec_from_file_location('probe_check', SCRIPT)
probe_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe_check)


# True only while the probe's fault is applied, so a command fails for the fault, not unconditionally.
FAULT = "any('amount > 10' in p.read_text(encoding='utf-8') for p in Path('.').glob('*.py'))"


class ProbeCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='probe-tests-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / '저장소'
        self.root.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Probe Tests')
        self.git('config', 'core.autocrlf', 'false')
        self.write('.gitignore', '__pycache__/\nnode_modules/\n')
        self.write('규칙.py', 'def allowed(amount):\n    return amount >= 10\n')
        self.write('test_rule.py', self.check_source('self.assertTrue(allowed(10))'))
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.registry = self.root / '.harness/probes.json'
        self.output = Path(self.temporary.name) / 'report'
        self.command = [sys.executable, '-m', 'unittest', 'test_rule']

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def check_source(self, assertion):
        return ('import unittest\nfrom 규칙 import allowed\n'
                'class RuleTest(unittest.TestCase):\n'
                f'    def test_rule(self):\n        {assertion}\n')

    def probe(self, **changes):
        value = dict(id='threshold', feature='checkout', rule='minimum amount',
                     perspective='business', layer='Domain', file='규칙.py',
                     find='amount >= 10', replace='amount > 10', command=self.command)
        value.update(changes)
        return value

    def registry_write(self, probes):
        self.write('.harness/probes.json', json.dumps(
            {'schema_version': 1, 'probes': probes}, ensure_ascii=False))

    def snapshot(self):
        return (self.git('status', '--porcelain', '-uall'),
                {str(p.relative_to(self.root)): p.read_bytes()
                 for p in self.root.rglob('*') if p.is_file() and
                 '.git' not in p.relative_to(self.root).parts})

    def invoke(self, *args, expected=0):
        before = self.snapshot()
        result = subprocess.run([sys.executable, str(SCRIPT), *args, '--root', str(self.root)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        stdout = result.stdout.decode('utf-8', errors='replace').replace('\r\n', '\n')
        self.assertEqual(result.returncode, expected, stdout + result.stderr.decode('utf-8', errors='replace'))
        self.assertEqual(self.snapshot(), before, 'User working tree changed')
        self.assertEqual(self.git('worktree', 'list', '--porcelain').count(b'worktree '), 1)
        return stdout

    def results(self):
        return json.loads((self.output / 'report.json').read_text(encoding='utf-8'))['probes']

    def shell_command(self, argv):
        return subprocess.list2cmdline(argv) if os.name == 'nt' else shlex.join(argv)

    def test_killed_matrix_and_exact_restore_between_probes(self):
        original = (self.root / '규칙.py').read_bytes()
        self.registry_write([self.probe(), self.probe(id='again')])
        stdout = self.invoke('probes', '--output', str(self.output))
        self.assertIn('| business | 2/2 |', stdout)
        self.assertEqual([p['status'] for p in self.results()], ['KILLED', 'KILLED'])
        self.assertEqual((self.root / '규칙.py').read_bytes(), original)
        self.assertEqual((self.output / 'report.md').read_text(encoding='utf-8'), stdout)

    def test_origins_summarize_which_guardrails_grew_from_findings(self):
        self.write('test_rule.py', self.check_source('self.assertFalse(allowed(1))'))
        self.registry_write([self.probe(origin='independent-check 2026-10-28 import'),
                             self.probe(id='floor', find='return amount', replace='return True or amount',
                                        origin='independent-check 2026-10-28'),
                             self.probe(id='old')])
        stdout = self.invoke('probes', '--output', str(self.output), expected=1)
        self.assertIn('Origins: independent-check 1/2, unrecorded 0/1', stdout)

    def test_survived(self):
        self.write('test_rule.py', self.check_source('self.assertFalse(allowed(1))'))
        self.registry_write([self.probe()])
        stdout = self.invoke('probes', '--output', str(self.output), expected=1)
        self.assertIn('SURVIVED', stdout)
        self.assertEqual(self.results()[0]['exit'], 0)
        self.assertFalse(self.results()[0]['detected'])

    def test_missing_and_duplicate_find_are_invalid_without_running(self):
        self.registry_write([self.probe(find='missing'), self.probe(id='duplicate', find='amount')])
        with patch.object(probe_check, 'run_command', side_effect=AssertionError('must not run')):
            with probe_check.worktree(self.root, 'HEAD', current=True) as copy:
                for probe in probe_check.load_probes(self.root, self.registry):
                    self.assertEqual(probe_check.probe_result(copy, probe, 5)['status'], 'INVALID')
        stdout = self.invoke('probes', '--output', str(self.output), expected=1)
        self.assertIn('occurs 0 times', stdout)
        self.assertIn('occurs 2 times', stdout)

    def test_registry_errors_before_git_or_commands(self):
        invalid = [self.probe(perspective='unknown'), self.probe(file='../outside.py'),
                   self.probe(file='/absolute.py'), self.probe(file='C:\\outside.py'),
                   self.probe(file='.git/config'), self.probe(command=[]),
                   self.probe(expect_detected=1), self.probe(find=''),
                   self.probe(feature=12), self.probe(unknown='field')]
        missing = self.probe()
        del missing['layer']
        cases = [[p] for p in invalid] + [[missing], [self.probe(), self.probe()]]
        for probes in cases:
            with self.subTest(probes=probes):
                self.registry_write(probes)
                self.invoke('probes', expected=2)
                with patch.object(probe_check, 'git', side_effect=AssertionError('git must not run')), \
                        patch('sys.stderr', new_callable=io.StringIO):
                    self.assertEqual(probe_check.main(['probes', '--root', str(self.root)]), 2)
        self.write('.harness/probes.json', '{broken json')
        self.invoke('probes', expected=2)

    def test_dirty_staged_and_untracked_state_replayed(self):
        self.write('規則追加.txt', 'untracked 한글\n')
        self.write('규칙.py', 'def allowed(amount):\n    return amount >= 20\n')
        self.git('add', '규칙.py')
        self.write('규칙.py', 'def allowed(amount):\n    return amount >= 30\n')
        self.write('새_test.py', self.check_source(
            'self.assertTrue(allowed(30)); self.assertFalse(allowed(20))'))
        self.registry_write([self.probe(find='amount >= 30', replace='amount > 30',
                                      command=[sys.executable, '-m', 'unittest', '새_test'])])
        self.invoke('probes', '--output', str(self.output))
        self.assertEqual(self.results()[0]['status'], 'KILLED')
        self.assertIn('AssertionError', self.results()[0]['tail'])

    def test_timeout_and_cleanup(self):
        self.registry_write([self.probe(command=[sys.executable, '-c', 'import time; time.sleep(20)'])])
        self.invoke('probes', '--timeout', '0.1', '--output', str(self.output), expected=1)
        result = self.results()[0]
        self.assertEqual(result['status'], 'TIMEOUT')
        self.assertFalse(result['detected'])
        self.assertIsNone(result['exit'])

    def test_negative_control_and_unexpected_kill(self):
        self.registry_write([self.probe(expect_detected=False)])
        self.invoke('probes', '--output', str(self.output), expected=1)
        self.assertEqual(self.results()[0]['status'], 'UNEXPECTED_KILL')
        self.write('test_rule.py', self.check_source('self.assertFalse(allowed(1))'))
        self.invoke('probes')

    def test_crashing_fault_is_an_error_not_a_kill(self):
        # A fault that breaks syntax or an import never reaches the assertion under test.
        self.registry_write([self.probe(id='syntax', replace='amount >= ('),
                             self.probe(id='import', find='def allowed', replace='def renamed'),
                             self.probe(id='control', expect_detected=False, replace='amount >= (')])
        stdout = self.invoke('probes', '--output', str(self.output), expected=1)
        results = {p['id']: p for p in self.results()}
        for name in results:
            self.assertEqual(results[name]['status'], 'ERROR', name)
            self.assertFalse(results[name]['detected'], name)
        self.assertIn('SyntaxError', results['syntax']['reason'])
        self.assertIn('ImportError', results['import']['reason'])
        self.assertIn('| business | 0/3 |', stdout)

    def test_a_command_that_fails_without_the_fault_is_invalid(self):
        # Without a passing baseline, a failure after the fault says nothing about the fault.
        broken = [sys.executable, '-c', 'import sys; sys.exit(1)']
        self.registry_write([self.probe(id='broken', command=broken), self.probe()])
        self.invoke('probes', '--output', str(self.output), expected=1)
        results = {p['id']: p for p in self.results()}
        self.assertEqual(results['broken']['status'], 'INVALID')
        self.assertFalse(results['broken']['detected'])
        self.assertIn('without the fault', results['broken']['reason'])
        self.assertEqual(results['threshold']['status'], 'KILLED')

    def test_expect_requires_the_named_failure(self):
        self.registry_write([self.probe(expect='AssertionError'),
                             self.probe(id='counterexample', expect='Falsifying example'),
                             self.probe(id='intended-import', find='def allowed', replace='def renamed',
                                        expect='cannot import name')])
        self.invoke('probes', '--output', str(self.output), expected=1)
        results = {p['id']: p for p in self.results()}
        self.assertEqual(results['threshold']['status'], 'KILLED')
        self.assertEqual(results['intended-import']['status'], 'KILLED')
        self.assertEqual(results['counterexample']['status'], 'ERROR')
        self.assertIn('Falsifying example', results['counterexample']['reason'])
        for bad in ('', '(unclosed', 3):
            with self.subTest(expect=bad):
                self.registry_write([self.probe(expect=bad)])
                self.invoke('probes', expected=2)

    def test_only_and_existing_output_rejected(self):
        self.registry_write([self.probe(), self.probe(id='unselected', find='missing')])
        self.invoke('probes', '--only', 'threshold', '--output', str(self.output))
        self.assertEqual(len(self.results()), 1)
        self.invoke('probes', '--output', str(self.output), expected=2)
        self.invoke('probes', '--only', 'unknown', expected=2)

    def test_command_launch_error_cleans_worktree(self):
        self.registry_write([self.probe(command=['nonexistent-probe-check-command'])])
        self.invoke('probes', expected=2)

    def test_links_created_by_the_command_never_delete_their_targets(self):
        outside = Path(self.temporary.name) / 'outside-deps'
        (outside / 'pkg').mkdir(parents=True)
        (outside / 'pkg' / 'index.js').write_text('keep', encoding='utf-8')
        maker = ('import os, subprocess, sys; from pathlib import Path; target = sys.argv[1]; '
                 "os.path.lexists('deps') or (subprocess.run(['cmd', '/c', 'mklink', '/J', 'deps', target], "
                 "check=True, capture_output=True) if os.name == 'nt' else os.symlink(target, 'deps', "
                 "target_is_directory=True)); sys.exit(FAULT)")
        self.registry_write([self.probe(command=[sys.executable, '-c', maker.replace('FAULT', FAULT), str(outside)])])
        self.invoke('probes')
        self.assertEqual((outside / 'pkg' / 'index.js').read_text(encoding='utf-8'), 'keep')

    def test_link_accepts_a_dependency_directory_that_is_itself_a_link(self):
        self.write('.gitignore', '__pycache__/\n')
        outside = Path(self.temporary.name) / 'shared-deps'
        outside.mkdir()
        (outside / 'marker.txt').write_text('dependency', encoding='utf-8')
        if os.name == 'nt':
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(self.root / 'node_modules'), str(outside)],
                           check=True, capture_output=True)
        else:
            (self.root / 'node_modules').symlink_to(outside, target_is_directory=True)
        command = [sys.executable, '-c',
                   'from pathlib import Path; import sys; '
                   'sys.exit(1 if Path("node_modules/marker.txt").read_text() == "dependency" and ' + FAULT + ' else 0)']
        self.registry_write([self.probe(command=command)])
        self.invoke('probes', '--link', 'node_modules', '--output', str(self.output))
        self.assertTrue(self.results()[0]['detected'])
        self.assertEqual((outside / 'marker.txt').read_text(encoding='utf-8'), 'dependency')

    def test_link_dependency_and_shell_command(self):
        self.write('node_modules/marker.txt', 'dependency')
        command = [sys.executable, '-c',
                   'from pathlib import Path; import sys; '
                   'sys.exit(1 if Path("node_modules/marker.txt").read_text() == "dependency" and ' + FAULT + ' else 0)']
        self.registry_write([self.probe(command=self.shell_command(command))])
        self.invoke('probes', '--link', 'node_modules', '--output', str(self.output))
        self.assertTrue(self.results()[0]['detected'])

    def test_link_preserved_on_timeout_and_partial_setup_failure(self):
        self.write('node_modules/marker.txt', 'keep')
        self.registry_write([self.probe(command=[sys.executable, '-c', 'import time; time.sleep(20)'])])
        self.invoke('probes', '--link', 'node_modules', '--timeout', '0.1', expected=1)
        self.write('occupied/file.txt', 'tracked')
        self.git('add', 'occupied/file.txt')
        self.git('commit', '-qm', 'occupied directory')
        self.invoke('probes', '--link', 'node_modules', 'occupied', expected=2)

    def test_relative_windows_path_and_exact_binary_restore(self):
        self.write('nested/규칙.txt', 'amount >= 10\n')
        probe = self.probe(file='nested\\규칙.txt')
        self.registry_write([probe])
        self.invoke('probes', expected=1)
        with probe_check.worktree(self.root, 'HEAD', current=True) as copy:
            target = copy / 'nested/규칙.txt'
            raw = b'\xef\xbb\xbfamount >= 10\r\n\x00\xff'
            target.write_bytes(raw)
            result = probe_check.probe_result(copy, probe, 5)
            self.assertEqual(result['status'], 'SURVIVED')
            self.assertEqual(target.read_bytes(), raw)

    def test_prove_fails_on_base_passes_on_current(self):
        self.write('규칙.py', 'def allowed(amount):\n    return amount >= 20\n')
        self.write('new/test_new.py', self.check_source('self.assertFalse(allowed(10))'))
        command = self.shell_command([sys.executable, '-m', 'unittest', 'discover', '-s', 'new'])
        stdout = self.invoke('prove', '--base', 'HEAD', '--tests', 'new/test_new.py', '--command', command)
        self.assertIn('PROVEN', stdout)
        self.assertIn('Current exit 0: PASS', stdout)

    def test_prove_also_passes_on_base(self):
        stdout = self.invoke('prove', '--base', 'HEAD', '--tests', 'test_rule.py',
                             '--command', self.shell_command(self.command), expected=1)
        self.assertIn('NOT_PROVEN', stdout)

    def test_prove_rejects_a_base_that_only_crashes(self):
        # The base lacks the new function, so the test fails on import, not on the rule.
        self.write('규칙.py', 'def allowed(amount):\n    return amount >= 10\n\n'
                              'def doubled(amount):\n    return amount * 2\n')
        self.write('new/test_new.py', 'import unittest\nfrom 규칙 import doubled\n'
                                      'class T(unittest.TestCase):\n'
                                      '    def test_it(self):\n        self.assertEqual(doubled(2), 4)\n')
        args = ('prove', '--base', 'HEAD', '--tests', 'new/test_new.py', '--command',
                self.shell_command([sys.executable, '-m', 'unittest', 'discover', '-s', 'new']))
        stdout = self.invoke(*args, expected=1)
        self.assertIn('NOT_PROVEN', stdout)
        self.assertIn('ImportError', stdout)
        self.assertIn('Base exit 1: PROVEN', self.invoke(*args, '--expect', 'cannot import name'))
        self.assertIn('NOT_PROVEN', self.invoke(*args, '--expect', 'AssertionError', expected=1))

    def test_prove_current_failure_and_skip(self):
        self.write('test_rule.py', self.check_source('self.assertFalse(allowed(10))'))
        args = ('prove', '--base', 'HEAD', '--tests', 'test_rule.py',
                '--command', self.shell_command(self.command))
        self.assertIn('FAIL', self.invoke(*args, expected=1))
        self.assertNotIn('Current exit', self.invoke(*args, '--skip-current'))

    def test_prove_missing_test_and_bad_ref(self):
        self.invoke('prove', '--base', 'HEAD', '--tests', 'absent.py', '--command', 'unused', expected=2)
        self.invoke('prove', '--base', 'no-such-ref', '--tests', 'test_rule.py',
                    '--command', 'unused', expected=2)


if __name__ == '__main__':
    unittest.main()
