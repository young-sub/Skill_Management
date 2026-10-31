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
        # prove counts only assertion failures; --expect narrows that and never turns a crash into proof.
        self.assertIn('NOT_PROVEN', self.invoke(*args, '--expect', 'cannot import name', expected=1))
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

    def test_prove_rejects_a_base_failure_that_is_an_import_error(self):
        # The new test imports a function the base does not have: an error, not a failed assertion.
        self.write('규칙.py', 'def allowed(amount):\n    return amount >= 10\n\ndef blocked(amount):\n    return amount < 10\n')
        self.write('new/test_new.py', 'import unittest\nfrom 규칙 import blocked\n'
                   'class BlockedTest(unittest.TestCase):\n    def test_blocked(self):\n'
                   '        self.assertTrue(blocked(5))\n')
        command = self.shell_command([sys.executable, '-m', 'unittest', 'discover', '-s', 'new'])
        stdout = self.invoke('prove', '--base', 'HEAD', '--tests', 'new/test_new.py', '--command', command, expected=1)
        self.assertIn('NOT_PROVEN (error: 1 error(s)', stdout)
        self.assertIn('Current exit 0: PASS', stdout)

    def test_prove_without_a_readable_report_is_not_proven(self):
        command = self.shell_command([sys.executable, '-c', 'raise SystemExit(1)'])
        stdout = self.invoke('prove', '--base', 'HEAD', '--tests', 'test_rule.py', '--command', command,
                             '--skip-current', expected=1)
        self.assertIn('NOT_PROVEN (unclassified: exit 1 without a test report', stdout)

    def junit_writer(self, body, code):
        """A command that writes a JUnit report with `body` inside one testcase and exits with `code`."""
        self.write('report_case.py', 'import pathlib, sys\n'
                   'pathlib.Path("out").mkdir(exist_ok=True)\n'
                   f'pathlib.Path("out/junit.xml").write_text({self.junit(body)!r})\n'
                   f'sys.exit({code})\n')
        return self.shell_command([sys.executable, 'report_case.py'])

    def junit(self, body):
        return f'<testsuites><testsuite name="s" tests="1"><testcase name="t">{body}</testcase></testsuite></testsuites>'

    def test_prove_reads_assertion_failures_and_errors_from_a_junit_report(self):
        cases = [('<failure type="AssertionError" message="expected 10 to be 20"/>', 1, 0, 'PROVEN (assertion_failure'),
                 ('<failure message="assert allowed(10) is False"/>', 1, 0, 'PROVEN (assertion_failure'),
                 ('<failure message="AttributeError: module has no attribute blocked"/>', 1, 1, 'NOT_PROVEN (error'),
                 ('<error message="ModuleNotFoundError: No module named app"/>', 1, 1, 'NOT_PROVEN (error'),
                 ('', 0, 1, 'NOT_PROVEN (pass')]
        for body, code, expected, label in cases:
            with self.subTest(body=body):
                command = self.junit_writer(body, code)
                stdout = self.invoke('prove', '--base', 'HEAD', '--tests', 'report_case.py', '--command', command,
                                     '--report', 'out/junit.xml', '--skip-current', expected=expected)
                self.assertIn(label, stdout)
        # A suite that records an import error without any testcase is an error too.
        self.assertEqual(probe_check.junit_counts(io.StringIO(
            '<testsuite name="file" tests="0" failures="0" errors="1"></testsuite>'))['errors'], 1)
        # Exit 1 with no report written means setup or collection failed before any test ran.
        stdout = self.invoke('prove', '--base', 'HEAD', '--tests', 'test_rule.py', '--command',
                             self.shell_command([sys.executable, '-c', 'raise SystemExit(1)']),
                             '--report', 'out/junit.xml', '--skip-current', expected=1)
        self.assertIn('NOT_PROVEN (error: exit 1 and no report out/junit.xml', stdout)

    def test_prove_copies_a_test_from_outside_the_repository_into_both_checkouts(self):
        self.write('규칙.py', 'def allowed(amount):\n    return amount >= 20\n')
        sealed = Path(self.temporary.name) / 'sealed' / 'test_sealed.py'
        sealed.parent.mkdir()
        sealed.write_text(self.check_source('self.assertFalse(allowed(10))'), encoding='utf-8')
        command = self.shell_command([sys.executable, '-m', 'unittest', 'discover', '-s', 'acceptance'])
        stdout = self.invoke('prove', '--base', 'HEAD', '--tests', f'{sealed}=acceptance/test_sealed.py',
                             '--command', command)
        self.assertIn('PROVEN (assertion_failure', stdout)
        self.assertIn('Current exit 0: PASS', stdout)
        self.assertFalse((self.root / 'acceptance').exists(), 'The sealed test never enters the user tree')
        self.invoke('prove', '--base', 'HEAD', '--tests', f'{sealed}=../escape.py', '--command', command, expected=2)

    def test_prove_preserve_requires_passing_on_base_and_now(self):
        command = self.shell_command(self.command)
        self.write('규칙.py', 'def allowed(amount):\n    minimum = 10\n    return amount >= minimum\n')
        stdout = self.invoke('prove', '--base', 'HEAD', '--tests', 'test_rule.py', '--command', command, '--preserve')
        self.assertIn('PRESERVED (pass', stdout)
        self.assertIn('Current exit 0: PASS', stdout)
        self.write('규칙.py', 'def allowed(amount):\n    return amount > 10\n')
        self.assertIn('FAIL (assertion_failure', self.invoke('prove', '--base', 'HEAD', '--tests', 'test_rule.py',
                                                              '--command', command, '--preserve', expected=1))
        self.write('test_rule.py', self.check_source('self.assertFalse(allowed(10))'))
        self.assertIn('NOT_PRESERVED (assertion_failure', self.invoke(
            'prove', '--base', 'HEAD', '--tests', 'test_rule.py', '--command', command, '--preserve', expected=1))

    def test_jest_format_reports_separate_assertion_failures_from_file_errors(self):
        report = {'numRuntimeErrorTestSuites': 0, 'testResults': [
            {'status': 'failed', 'assertionResults': [
                {'status': 'failed', 'failureMessages': ['AssertionError: expected 10 to be 20\n    at test.ts:4']},
                {'status': 'passed', 'failureMessages': []}]},
            {'status': 'failed', 'message': 'Failed to load url ./missing', 'assertionResults': []},
            {'status': 'failed', 'assertionResults': [
                {'status': 'failed', 'failureMessages': ['TypeError: blocked is not a function\n    expect(x)']}]}]}
        self.assertEqual(probe_check.jest_counts(report),
                         {'tests': 3, 'skipped': 0, 'assertions': 1, 'other_failures': 1, 'errors': 1})
        self.assertEqual(probe_check.jest_counts({'numRuntimeErrorTestSuites': 2, 'testResults': []})['errors'], 2)

    def test_failure_kind_comes_from_the_exception_type_not_a_substring(self):
        # Review findings: "unexpected" and module names containing "expected" were read as assertions.
        for text, expected in (
                ("ModuleNotFoundError: No module named 'expected_missing_xyz'", False),
                ('Error: unexpected', False),
                ('testCodeFailure unexpected\nError: unexpected token', False),
                ('E       AttributeError: module has no attribute blocked\n>   assert blocked(5)', False),
                ('assert allowed(10) is False', True),
                ('AssertionError: expected 10 to be 20', True),
                ('testCodeFailure threshold is wrong\n[Error [ERR_TEST_FAILURE]: threshold is wrong] '
                 '{ cause: AssertionError [ERR_ASSERTION]: threshold is wrong }', True),
                ('Error: expect(received).toBe(expected)\n\nExpected: 2\nReceived: 1', True)):
            with self.subTest(text=text[:40]):
                self.assertEqual(probe_check.is_assertion(text), expected)

    def test_a_suite_error_or_non_assertion_failure_beside_an_assertion_is_not_proof(self):
        assertion = {'status': 'failed', 'failureMessages': ['AssertionError: expected 1 to be 2']}
        after_all = {'testResults': [{'status': 'failed', 'message': 'Error: missing configuration',
                                      'assertionResults': [assertion]}]}
        hook = {'testResults': [{'status': 'failed', 'message': '', 'assertionResults': [
            assertion, {'status': 'failed', 'failureMessages': ['Error: missing configuration']}]}]}
        self.assertEqual(probe_check.jest_counts(after_all)['errors'], 1)
        self.assertEqual(probe_check.jest_counts(hook)['other_failures'], 1)
        run = {'timeout': False, 'exit': 1, 'tail': ''}
        for data in (after_all, hook):
            report = self.root / 'r.json'
            report.write_text(json.dumps(data), encoding='utf-8')
            self.assertEqual(probe_check.run_outcome(self.root, run, 'r.json')['verdict'], 'error')

    def test_passing_needs_an_executed_test_and_the_requested_report(self):
        run = {'timeout': False, 'exit': 0, 'tail': ''}
        self.assertEqual(probe_check.run_outcome(self.root, run, 'missing.xml')['verdict'], 'unclassified')
        self.assertEqual(probe_check.run_outcome(self.root, run)['verdict'], 'unclassified')
        skipped = dict(run, tail='Ran 1 test in 0.001s\n\nOK (skipped=1)\n')
        self.assertEqual(probe_check.run_outcome(self.root, skipped)['reason'], 'no test executed')
        (self.root / 'skip.xml').write_text('<testsuite><testcase name="t"><skipped/></testcase></testsuite>',
                                            encoding='utf-8')
        self.assertEqual(probe_check.run_outcome(self.root, run, 'skip.xml')['verdict'], 'unclassified')

    def test_unittest_summary_is_found_before_later_buffered_output(self):
        output = 'F\n' + '=' * 70 + '\nRan 1 test in 0.002s\n\nFAILED (failures=1)\n' + 'x' * 1200
        run = {'timeout': False, 'exit': 1, 'tail': output[-800:], 'output': output}
        self.assertEqual(probe_check.run_outcome(self.root, run)['verdict'], 'assertion_failure')

    def test_preserve_cannot_skip_the_current_run(self):
        command = self.shell_command(self.command)
        self.invoke('prove', '--base', 'HEAD', '--tests', 'test_rule.py', '--command', command,
                    '--preserve', '--skip-current', expected=2)


if __name__ == '__main__':
    unittest.main()
