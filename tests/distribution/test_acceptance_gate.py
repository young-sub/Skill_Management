"""The sealed acceptance gate on real Git fixtures: seal before work, judge after, outside the worker's reach."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'authoring/scripts/acceptance_gate.py'
SPEC = importlib.util.spec_from_file_location('acceptance_gate', SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

RULE = 'def allowed(amount):\n    return amount >= 10\n'
# An extra function no acceptance test exercises, kept apart from the rule change by an unchanged line.
UNRELATED = 'def discount(amount):\n    return amount // 10\n\n\n'
ACCEPTANCE = ('import unittest\nfrom rule import allowed\n'
              'class Acceptance(unittest.TestCase):\n'
              '    def test_minimum_is_twenty(self):\n'
              '        self.assertFalse(allowed(10))\n'
              '        self.assertTrue(allowed(20))\n')


class AcceptanceGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='acceptance-tests-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'repo'
        self.root.mkdir()
        for args in (('init', '-q'), ('config', 'user.email', 't@example.invalid'), ('config', 'user.name', 'T'),
                     ('config', 'core.autocrlf', 'false')):
            self.git(*args)
        self.write('.gitignore', '__pycache__/\n')
        self.write('rule.py', RULE)
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.sealed = Path(temporary.name) / 'author' / 'test_acceptance.py'
        self.sealed.parent.mkdir()
        self.sealed.write_text(ACCEPTANCE, encoding='utf-8')
        self.command = subprocess.list2cmdline([sys.executable, '-m', 'unittest', 'discover', '-s', 'acceptance'])

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True).stdout

    def write(self, name, text):
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        (self.root / name).write_text(text, encoding='utf-8')

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *args, '--root', str(self.root)],
                                capture_output=True, timeout=120)
        stdout = result.stdout.decode('utf-8', errors='replace')
        self.assertEqual(result.returncode, expected, stdout + result.stderr.decode('utf-8', errors='replace'))
        return stdout

    def seal(self, *extra, expected=0):
        return self.cli('seal', '--tests', f'{self.sealed}=acceptance/test_acceptance.py',
                        '--command', self.command, *extra, expected=expected)

    def hook(self):
        result = subprocess.run([sys.executable, str(SCRIPT), 'hook'], capture_output=True, timeout=300,
                                input=json.dumps({'hook_event_name': 'Stop', 'cwd': str(self.root)}).encode('utf-8'))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def history(self):
        return gate.results(gate.state_dir(self.root))

    def test_seal_requires_an_assertion_failure_on_the_base_and_keeps_tests_out_of_the_tree(self):
        self.sealed.write_text(ACCEPTANCE.replace('assertFalse(allowed(10))', 'assertTrue(allowed(10))')
                               .replace('assertTrue(allowed(20))', 'assertTrue(allowed(11))'), encoding='utf-8')
        self.assertFalse(json.loads(self.seal(expected=1))['sealed'], 'a test that passes on the base proves nothing')
        self.sealed.write_text(ACCEPTANCE, encoding='utf-8')
        outcome = json.loads(self.seal())
        self.assertEqual((outcome['sealed'], outcome['verdict']), (True, 'assertion_failure'))
        self.assertEqual(self.git('status', '--porcelain', '-uall'), b'', 'sealing writes nothing to the work tree')
        state = gate.state_dir(self.root)
        self.assertTrue((state / 'contract.json').is_file())
        self.assertFalse(state.is_relative_to(self.root) and '.git' not in state.relative_to(self.root).parts)
        self.seal(expected=2)  # a second seal must not silently replace the first

    def test_check_fails_until_the_behavior_changes_and_binds_the_verdict_to_the_tree(self):
        self.seal()
        self.assertIn('Acceptance FAIL', self.cli('check', expected=1))
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertIn('Acceptance PASS', self.cli('check'))
        results = self.history()
        self.assertEqual([r['verdict'] for r in results], ['FAIL', 'PASS'])
        self.assertNotEqual(results[0]['tree'], results[1]['tree'])
        self.assertEqual(results[1]['tree'], gate.tree_id(self.root))
        self.assertEqual(self.git('status', '--porcelain'), b' M rule.py\n', 'checking leaves the tree as it was')

    def test_a_weakened_copy_of_the_test_in_the_tree_is_replaced_by_the_sealed_one(self):
        self.seal()
        self.write('acceptance/test_acceptance.py', ACCEPTANCE.replace('assertFalse(allowed(10))', 'pass'))
        self.assertIn('Acceptance FAIL', self.cli('check', expected=1))

    def test_editing_the_sealed_files_is_detected(self):
        self.seal()
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        tests = gate.state_dir(self.root) / 'tests'
        stored = next(tests.iterdir())
        stored.write_text(stored.read_text(encoding='utf-8').replace('assertFalse(allowed(10))', 'pass'), encoding='utf-8')
        self.assertIn('Acceptance TAMPERED', self.cli('check', expected=1))

    def test_hunks_whose_reversal_fails_no_sealed_test_are_untested(self):
        self.seal()
        self.write('rule.py', UNRELATED + RULE.replace('>= 10', '>= 20'))
        self.write('docs/notes.md', 'notes\n')
        self.write('tests/test_extra.py', 'x = 1\n')
        output = self.cli('check')
        result = self.history()[-1]
        self.assertEqual(result['verdict'], 'PASS')
        self.assertEqual([u['file'] for u in result['untested']], ['rule.py'], output)
        self.assertEqual(result['hunks'], 2, 'documents and test files are not ablated')
        self.assertIn('1 untested change(s)', output)

    def test_uncovered_scenarios_are_reported(self):
        scenarios = Path(self.sealed.parent / 'scenarios.json')
        scenarios.write_text(json.dumps([
            {'scenario': 'amount 10 is refused', 'covered_by': ['acceptance/test_acceptance.py']},
            {'scenario': 'the refusal message names the minimum', 'covered_by': []}]), encoding='utf-8')
        self.seal('--scenarios', str(scenarios))
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertIn('1 uncovered requirement(s): the refusal message names the minimum', self.cli('check'))

    def test_preserve_mode_seals_passing_tests_for_a_refactoring(self):
        preserved = ACCEPTANCE.replace('assertFalse(allowed(10))', 'assertTrue(allowed(10))').replace(
            'assertTrue(allowed(20))', 'assertFalse(allowed(9))')
        self.sealed.write_text(preserved, encoding='utf-8')
        self.seal(expected=1)
        self.assertTrue(json.loads(self.seal('--preserve'))['sealed'])
        self.write('rule.py', 'MINIMUM = 10\n\n\ndef allowed(amount):\n    return amount >= MINIMUM\n')
        self.assertIn('Acceptance PASS', self.cli('check', '--no-ablate'))

    def test_stop_hook_is_silent_without_a_contract_blocks_on_failure_and_stops_after_three(self):
        self.assertEqual(self.hook(), {})
        self.seal()
        first = self.hook()
        self.assertEqual(first['decision'], 'block')
        self.assertIn('Fix the implementation, not the sealed tests', first['reason'])
        self.assertEqual(self.hook()['decision'], 'block')
        self.assertEqual(len(self.history()), 1, 'an unchanged tree reuses its verdict without rerunning')
        self.write('rule.py', RULE.replace('>= 10', '>= 5'))
        self.assertEqual(self.hook()['decision'], 'block')
        self.write('rule.py', RULE.replace('>= 10', '>= 9'))
        stopped = self.hook()
        self.assertNotIn('decision', stopped)
        self.assertIn('stopping for a person', stopped['systemMessage'])
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertIn('STOPPED', self.hook()['systemMessage'], 'after three failures only a person re-seals')
        self.assertIn('Acceptance STOPPED', self.cli('check', expected=1))
        self.cli('clear')
        self.seal()
        self.assertEqual(self.hook(), {}, 'a passing tree with nothing to report is silent')

    def test_stop_hook_reports_untested_changes_without_blocking(self):
        self.seal()
        self.write('rule.py', UNRELATED + RULE.replace('>= 10', '>= 20'))
        decision = self.hook()
        self.assertNotIn('decision', decision)
        self.assertIn('untested change', decision['systemMessage'])

    # --- regressions from the independent review ------------------------------------------------

    def test_a_change_to_a_force_added_ignored_file_needs_a_new_check(self):
        self.write('.gitignore', '__pycache__/\nlocal_rule.py\n')
        self.git('commit', '-qam', 'ignore local_rule')
        self.seal()
        self.write('local_rule.py', 'THRESHOLD = 20\n')
        self.git('add', '-f', 'local_rule.py')
        self.write('rule.py', 'from local_rule import THRESHOLD\n\n\ndef allowed(amount):\n    return amount >= THRESHOLD\n')
        self.assertEqual(self.hook(), {})
        self.write('local_rule.py', 'THRESHOLD = 10\n')
        self.assertEqual(self.hook()['decision'], 'block', 'the edited force-added file changes the tree')

    def test_a_cached_pass_does_not_hide_a_changed_sealed_test(self):
        self.seal()
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertEqual(self.hook(), {})
        stored = next((gate.state_dir(self.root) / 'tests').iterdir())
        stored.write_text('import unittest\n', encoding='utf-8')
        decision = self.hook()
        self.assertEqual(decision['decision'], 'block')
        self.assertIn('TAMPERED', decision['reason'])

    def test_verdicts_say_the_seal_only_detects_tampering(self):
        self.assertEqual(json.loads(self.seal())['integrity'], 'tamper-detection-only')
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertIn('seal is tamper-detection-only', self.cli('check'))

    def test_repeated_stops_on_an_unchanged_failing_tree_block_three_times(self):
        self.seal()
        decisions = [self.hook() for _ in range(5)]
        self.assertEqual([d.get('decision') for d in decisions], ['block', 'block', 'block', None, None])
        self.assertIn('stopping for a person', decisions[-1]['systemMessage'])

    def test_errors_in_an_active_gate_block_instead_of_passing(self):
        self.seal()
        self.write('acceptance/test_acceptance.py/occupied.txt', 'x\n')
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertEqual(self.hook()['decision'], 'block', 'a directory at the sealed path is a gate error')
        (self.root / 'acceptance/test_acceptance.py/occupied.txt').unlink()
        (self.root / 'acceptance/test_acceptance.py').rmdir()
        (gate.state_dir(self.root) / 'contract.json').write_text('{broken', encoding='utf-8')
        decision = self.hook()
        self.assertEqual(decision['decision'], 'block')
        self.assertIn('acceptance gate error', decision['reason'])

    def test_paths_with_spaces_are_reverted_and_restored_one_hunk_at_a_time(self):
        self.write('a b/code.py', 'X = 1\n')
        self.write('a b/__init__.py', '')
        self.git('add', '.')
        self.git('commit', '-qm', 'spaced')
        self.seal()
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        self.write('a b/code.py', 'X = 2\n')
        self.cli('check')
        result = self.history()[-1]
        self.assertEqual(result['hunks'], 2)
        self.assertEqual([u['file'] for u in result['untested']], ['a b/code.py'])

    def test_each_reversal_starts_from_a_clean_copy_without_generated_caches(self):
        cached = ('import pathlib\nCACHE = pathlib.Path("threshold.cache")\nif not CACHE.exists():\n'
                  '    CACHE.write_text("{}")\n\n\ndef allowed(amount):\n    return amount >= int(CACHE.read_text())\n')
        self.write('.gitignore', '__pycache__/\n*.cache\n')
        self.write('rule.py', cached.format(10))
        self.git('commit', '-qam', 'cached threshold')
        self.seal()
        self.write('rule.py', cached.format(20))
        self.cli('check')
        result = self.history()[-1]
        self.assertEqual(result['untested'], [], 'the reverted threshold is caught once the cache is gone')

    def test_binary_and_text_configuration_changes_are_reported(self):
        self.write('rates.bin', '')
        (self.root / 'rates.bin').write_bytes(b'\0\1')
        self.write('requirements.txt', 'a==1\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'data')
        self.seal()
        self.write('rule.py', RULE.replace('>= 10', '>= 20'))
        (self.root / 'rates.bin').write_bytes(b'\0\2')
        self.write('requirements.txt', 'a==2\n')
        self.cli('check')
        result = self.history()[-1]
        self.assertEqual([u['file'] for u in result['untested']], ['requirements.txt'])
        self.assertEqual([u['file'] for u in result['unknown']], ['rates.bin'])

    def test_a_check_without_ablation_does_not_satisfy_the_hook(self):
        self.seal()
        self.write('rule.py', UNRELATED + RULE.replace('>= 10', '>= 20'))
        self.assertIn('Strength not checked', self.cli('check', '--no-ablate'))
        decision = self.hook()
        self.assertIn('untested change', decision['systemMessage'])
        self.assertEqual([r['ablated'] for r in self.history()], [False, True])

    def test_scenarios_may_only_name_sealed_tests(self):
        scenarios = self.sealed.parent / 'scenarios.json'
        scenarios.write_text(json.dumps([{'scenario': 'x', 'covered_by': ['does/not/exist.py']}]), encoding='utf-8')
        self.seal('--scenarios', str(scenarios), expected=2)

    def test_opt_out_and_clear(self):
        self.seal()
        environment = dict(os.environ, AGENT_ACCEPTANCE_GATE='off')
        result = subprocess.run([sys.executable, str(SCRIPT), 'hook'], capture_output=True, env=environment,
                                input=json.dumps({'cwd': str(self.root)}).encode('utf-8'))
        self.assertEqual(json.loads(result.stdout), {})
        self.cli('clear')
        self.assertFalse(gate.state_dir(self.root).exists())
        self.cli('status', expected=3)


if __name__ == '__main__':
    unittest.main()
