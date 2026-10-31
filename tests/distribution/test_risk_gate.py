"""Risk tiers from a table on the base ref, on real Git fixtures; LOW must be earned, never assumed."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[2] / 'authoring/scripts'
SCRIPT = SCRIPTS / 'risk_gate.py'
GATE = SCRIPTS / 'acceptance_gate.py'
SPEC = importlib.util.spec_from_file_location('risk_gate', SCRIPT)
risk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(risk)

TABLE = {'schema_version': 1,
         'low': [{'id': 'docs', 'paths': ['docs/*'], 'requires': []},
                 {'id': 'sealed-logic', 'paths': ['src/*'], 'requires': ['acceptance-pass', 'no-untested', 'no-uncovered']}],
         'high': {'paths': ['src/auth/*', '.harness/*']}}
RULE = 'def allowed(amount):\n    return amount >= 10\n'
ACCEPTANCE = ('import unittest\nfrom src.rule import allowed\n'
              'class Acceptance(unittest.TestCase):\n'
              '    def test_minimum_is_twenty(self):\n'
              '        self.assertFalse(allowed(10))\n'
              '        self.assertTrue(allowed(20))\n')


class RiskGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='risk-tests-')
        self.addCleanup(temporary.cleanup)
        self.outside = Path(temporary.name)
        self.root = self.outside / 'repo'
        self.root.mkdir()
        for args in (('init', '-q', '-b', 'main'), ('config', 'user.email', 't@example.invalid'),
                     ('config', 'user.name', 'T'), ('config', 'core.autocrlf', 'false')):
            self.git(*args)
        self.write('.gitignore', '__pycache__/\n')
        self.write('.harness/risk.yaml', json.dumps(TABLE))
        self.write('src/__init__.py', '')
        self.write('src/rule.py', RULE)
        self.write('src/auth/session.py', 'def login(amount):\n    return amount > 0\n')
        self.write('tests/test_rule.py', 'x = 1\n')
        self.write('docs/guide.md', 'guide\n')
        self.commit('base')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True).stdout.decode()

    def write(self, name, text):
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        (self.root / name).write_text(text, encoding='utf-8')

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-qm', message)

    def classify(self):
        result = subprocess.run([sys.executable, str(SCRIPT), 'classify', '--root', str(self.root), '--base', 'main'],
                                capture_output=True, timeout=120)
        decided = json.loads(result.stdout)
        self.assertEqual(result.returncode, {'LOW': 0, 'MED': 10, 'HIGH': 20}[decided['tier']], result.stderr)
        return decided

    def seal_and_fix(self):
        sealed = self.outside / 'author' / 'test_acceptance.py'
        sealed.parent.mkdir(exist_ok=True)
        sealed.write_text(ACCEPTANCE, encoding='utf-8')
        command = subprocess.list2cmdline([sys.executable, '-m', 'unittest', 'acceptance.test_acceptance'])
        subprocess.run([sys.executable, str(GATE), 'seal', '--root', str(self.root), '--base', 'main', '--tests',
                        f'{sealed}=acceptance/test_acceptance.py', '--command', command], check=True, capture_output=True)
        self.write('src/rule.py', RULE.replace('>= 10', '>= 20'))
        return subprocess.run([sys.executable, str(GATE), 'check', '--root', str(self.root)], capture_output=True)

    def test_documentation_in_a_registered_class_is_low_and_unknown_paths_are_med(self):
        self.assertEqual(self.classify()['tier'], 'LOW', 'no change')
        self.write('docs/guide.md', 'guide v2\n')
        self.assertEqual(self.classify()['tier'], 'LOW')
        self.write('README.md', 'new\n')
        decided = self.classify()
        self.assertEqual(decided['tier'], 'MED')
        self.assertIn('README.md', ' '.join(decided['reasons']))

    def test_logic_is_low_only_with_a_passing_sealed_check_that_found_nothing_untested(self):
        self.write('src/rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertIn('acceptance-pass', ' '.join(self.classify()['reasons']))
        self.write('src/rule.py', RULE)
        self.assertEqual(self.seal_and_fix().returncode, 0)
        self.assertEqual(self.classify()['tier'], 'LOW')
        # An extra function no sealed test notices removes the LOW evidence.
        self.write('src/rule.py', 'def discount(amount):\n    return amount // 10\n\n\n' + RULE.replace('>= 10', '>= 20'))
        subprocess.run([sys.executable, str(GATE), 'check', '--root', str(self.root)], capture_output=True)
        decided = self.classify()
        self.assertEqual(decided['tier'], 'MED')
        self.assertIn('no-untested', ' '.join(decided['reasons']))

    def test_sensitive_paths_existing_tests_and_indirect_references_are_high(self):
        cases = {'sensitive path': ('src/auth/session.py', 'def login(amount):\n    return True\n'),
                 'existing test': ('tests/test_rule.py', 'x = 2\n')}
        for label, (name, text) in cases.items():
            with self.subTest(label):
                original = (self.root / name).read_text(encoding='utf-8')
                self.write(name, text)
                self.assertEqual(self.classify()['tier'], 'HIGH')
                self.write(name, original)
        self.write('tests/test_new.py', 'y = 1\n')
        self.assertNotEqual(self.classify()['tier'], 'HIGH', 'adding a test is not weakening one')
        (self.root / 'tests/test_new.py').unlink()
        self.write('src/auth/session.py', 'from src.rule import allowed\n\ndef login(amount):\n    return allowed(amount)\n')
        self.commit('auth uses the rule')
        self.write('src/rule.py', RULE.replace('return amount >= 10', 'return amount >= 20'))
        self.write('src/rule.py', 'def allowed(amount):\n    return amount >= 20\n')
        decided = self.classify()
        self.assertEqual(decided['tier'], 'HIGH')
        self.assertIn('allowed is referenced from a sensitive file: src/auth/session.py', ' '.join(decided['reasons']))

    def test_a_branch_cannot_loosen_its_own_table(self):
        loosened = dict(TABLE, low=[{'id': 'everything', 'paths': ['*'], 'requires': []}], high={'paths': []})
        self.write('.harness/risk.yaml', json.dumps(loosened))
        self.write('src/auth/session.py', 'def login(amount):\n    return True\n')
        self.assertEqual(self.classify()['tier'], 'HIGH')

    def test_paths_changed_by_a_recent_revert_move_up_one_tier(self):
        self.write('docs/guide.md', 'bad\n')
        self.commit('docs: bad guide')
        self.git('revert', '--no-edit', 'HEAD')
        self.write('docs/guide.md', 'guide v3\n')
        decided = self.classify()
        self.assertEqual(decided['tier'], 'MED')
        self.assertIn('reverted within 30 days: docs/guide.md', ' '.join(decided['reasons']))

    def committed_candidate(self):
        self.git('switch', '-q', '-c', 'work')
        self.assertEqual(self.seal_and_fix().returncode, 0)
        self.commit('raise the minimum')

    def integrate(self, files, message):
        self.git('switch', '-q', 'main')
        for name, text in files.items():
            self.write(name, text)
        self.commit(message)
        self.git('switch', '-q', 'work')

    def recheck(self, *extra):
        result = subprocess.run([sys.executable, str(SCRIPT), 'recheck', '--root', str(self.root), '--onto', 'main', *extra],
                                capture_output=True)
        return result.returncode, (json.loads(result.stdout) if result.stdout.strip() else result.stderr.decode())

    def test_recheck_runs_the_sealed_tests_on_the_integration_tip(self):
        self.committed_candidate()
        self.integrate({'docs/guide.md': 'other change\n'}, 'docs: unrelated')
        code, outcome = self.recheck()
        self.assertEqual((code, outcome['verdict']), (0, 'PASS'), outcome)
        self.assertEqual(outcome['onto'], self.git('rev-parse', 'main').strip())
        # A non-sensitive change on the tip that breaks the rule fails the merged tree.
        self.integrate({'src/override.py': 'import src.rule as rule\n\nrule.allowed = lambda amount: True\n',
                        'src/__init__.py': 'from src import override  # noqa: F401\n'}, 'integration change that breaks the rule')
        code, outcome = self.recheck()
        self.assertEqual((code, outcome['verdict']), (1, 'FAIL'), outcome)

    def test_recheck_reclassifies_on_the_tip_runs_regressions_and_refuses_uncommitted_work(self):
        self.committed_candidate()
        self.integrate({'src/auth/session.py': 'from src.rule import allowed\n\ndef login(amount):\n    return allowed(amount)\n'},
                       'auth starts using the rule')
        code, outcome = self.recheck()
        self.assertEqual((code, outcome['verdict']), (1, 'HIGH'), outcome)
        self.assertIn('allowed is referenced from a sensitive file', outcome['reason'])
        self.git('reset', '-q', '--hard', 'HEAD')
        self.git('switch', '-q', 'main')
        self.git('reset', '-q', '--hard', 'HEAD~1')
        self.git('switch', '-q', 'work')
        failing = subprocess.list2cmdline([sys.executable, '-c', 'raise SystemExit(3)'])
        code, outcome = self.recheck('--regression', failing)
        self.assertEqual((code, outcome['verdict']), (1, 'FAIL'), outcome)
        self.assertIn('regression', outcome['reason'])
        self.write('src/rule.py', RULE.replace('>= 10', '>= 30'))
        code, outcome = self.recheck()
        self.assertEqual(code, 2)
        self.assertIn('commit first', outcome)

    def test_symbols_constants_short_names_and_arrow_functions_reach_sensitive_callers(self):
        self.write('src/limits.py', 'LIMIT = 10\n\n\ndef ok(a):\n    return a\n')
        self.write('src/check.ts', 'export const check = (a: number) => {\n  return a > 1;\n};\n')
        self.write('src/auth/session.py', 'from src.limits import LIMIT, ok\n# check() from src/check.ts guards sessions\n')
        self.commit('callers')
        for name, text in (('src/limits.py', 'LIMIT = 20\n\n\ndef ok(a):\n    return a\n'),
                           ('src/limits.py', 'LIMIT = 10\n\n\ndef ok(a):\n    return not a\n'),
                           ('src/check.ts', 'export const check = (a: number) => {\n  return a > 2;\n};\n')):
            with self.subTest(text=text[:24]):
                original = (self.root / name).read_text(encoding='utf-8')
                self.write(name, text)
                self.assertEqual(self.classify()['tier'], 'HIGH')
                self.write(name, original)

    def test_a_sensitive_symlink_is_read_through(self):
        self.write('src/shared.py', 'from src.rule import allowed\n')
        target = self.root / 'src/auth/session.py'
        target.unlink()
        try:
            target.symlink_to(Path('..') / 'shared.py')
        except OSError:
            self.skipTest('symbolic links are not available')
        self.commit('session links to shared')
        self.write('src/rule.py', RULE.replace('>= 10', '>= 20'))
        self.assertEqual(self.classify()['tier'], 'HIGH')

    def test_retyped_tests_and_expectation_files_are_high(self):
        self.write('expectations/output.json', '{"a": 1}\n')
        self.commit('expectations')
        self.write('expectations/output.json', '{"a": 2}\n')
        self.assertEqual(self.classify()['tier'], 'HIGH')
        self.git('checkout', '--', 'expectations/output.json')
        (self.root / 'tests/test_rule.py').unlink()
        try:
            (self.root / 'tests/test_rule.py').symlink_to('../docs/guide.md')
        except OSError:
            self.skipTest('symbolic links are not available')
        self.assertEqual(self.classify()['tier'], 'HIGH')

    def test_cached_evidence_needs_intact_sealed_tests(self):
        self.assertEqual(self.seal_and_fix().returncode, 0)
        self.assertEqual(self.classify()['tier'], 'LOW')
        stored = next((risk.acceptance_gate.state_dir(self.root) / 'tests').iterdir())
        stored.write_text('import unittest\n', encoding='utf-8')
        self.assertEqual(self.classify()['tier'], 'MED')

    def test_the_template_marks_nested_migrations_and_workflows_high(self):
        template = json.loads((SCRIPTS.parent / 'templates/project/risk.yaml').read_text(encoding='utf-8'))
        for path in ('src/db/migrations/001_initial.sql', 'migrations/002.sql', '.github/workflows/ci.yml',
                     'packages/web/.github/workflows/x.yml', 'src/auth/session.ts'):
            with self.subTest(path=path):
                self.assertTrue(risk.matches(path, template['high']['paths']))
        self.assertFalse(risk.matches('src/rule.py', template['high']['paths']))

    def test_with_a_sealed_contract_only_high_changes_still_need_the_independent_verifier(self):
        guard = SCRIPTS / 'completion_guard.py'

        def stop(name):
            edit = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'e', 'name': 'Edit', 'input': {
                'file_path': str(self.root / name), 'old_string': 'a', 'new_string': 'b\n' * 6}}]}}
            transcript = self.outside / 'turn.jsonl'
            transcript.write_text('\n'.join(json.dumps(e) for e in (
                {'type': 'user', 'message': {'content': 'fix'}}, edit)), encoding='utf-8')
            result = subprocess.run([sys.executable, str(guard)], capture_output=True, text=True, input=json.dumps(
                {'hook_event_name': 'Stop', 'cwd': str(self.root), 'transcript_path': str(transcript)}))
            return json.loads(result.stdout)

        self.assertEqual(stop('src/rule.py').get('decision'), 'block', 'without a contract the rule stands')
        self.assertEqual(self.seal_and_fix().returncode, 0)
        self.assertEqual(stop('src/rule.py'), {}, 'a passing sealed check judges a non-HIGH change')
        self.write('src/rule.py', RULE.replace('>= 10', '>= 30'))
        self.assertEqual(stop('src/rule.py').get('decision'), 'block', 'a contract without a passing check is not enough')
        self.write('src/rule.py', RULE.replace('>= 10', '>= 20'))
        self.write('src/auth/session.py', 'def login(amount):\n    return True\n')
        self.assertEqual(stop('src/auth/session.py').get('decision'), 'block', 'HIGH still needs the verifier')

    def test_one_stop_process_runs_the_gate_first_and_drops_a_contract_that_no_longer_applies(self):
        def stop(name, old, new):
            edit = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'e', 'name': 'Edit', 'input': {
                'file_path': str(self.root / name), 'old_string': old, 'new_string': new}}]}}
            transcript = self.outside / 'stale.jsonl'
            transcript.write_text('\n'.join(json.dumps(e) for e in ({'type': 'user', 'message': {'content': 'fix'}}, edit)),
                                  encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPTS / 'completion_guard.py')], capture_output=True, text=True,
                                    input=json.dumps({'hook_event_name': 'Stop', 'cwd': str(self.root),
                                                      'transcript_path': str(transcript)}))
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        sealed = self.outside / 'author' / 'test_acceptance.py'
        sealed.parent.mkdir(exist_ok=True)
        sealed.write_text(ACCEPTANCE, encoding='utf-8')
        command = subprocess.list2cmdline([sys.executable, '-m', 'unittest', 'acceptance.test_acceptance'])
        subprocess.run([sys.executable, str(GATE), 'seal', '--root', str(self.root), '--base', 'main', '--tests',
                        f'{sealed}=acceptance/test_acceptance.py', '--command', command], check=True, capture_output=True)
        blocked = stop('src/rule.py', 'a', 'b')
        self.assertIn('Fix the implementation, not the sealed tests', blocked['reason'],
                      'the gate runs in the Stop process before the guard, with no earlier check')
        self.write('src/rule.py', RULE.replace('>= 10', '>= 20'))
        self.commit('work')
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.git('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        self.write('src/auth/session.py', 'def login(amount):\n    return True\n')
        later = stop('src/auth/session.py', 'amount > 0', 'True')
        self.assertNotIn('decision', later, 'an integrated contract no longer makes a one-line edit HIGH')
        self.assertIn('no longer applies', later['systemMessage'])

    def test_a_one_line_high_change_with_a_contract_still_needs_the_verifier(self):
        self.assertEqual(self.seal_and_fix().returncode, 0)
        self.write('src/auth/session.py', 'def login(amount):\n    return True\n')
        edit = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'e', 'name': 'Edit', 'input': {
            'file_path': str(self.root / 'src/auth/session.py'), 'old_string': 'amount > 0', 'new_string': 'True'}}]}}
        transcript = self.outside / 'one.jsonl'
        transcript.write_text('\n'.join(json.dumps(e) for e in ({'type': 'user', 'message': {'content': 'fix'}}, edit)),
                              encoding='utf-8')
        result = subprocess.run([sys.executable, str(SCRIPTS / 'completion_guard.py')], capture_output=True, text=True,
                                input=json.dumps({'cwd': str(self.root), 'transcript_path': str(transcript)}))
        self.assertEqual(json.loads(result.stdout).get('decision'), 'block')

    def test_reverts_become_regression_tasks_with_their_agent_task(self):
        self.write('docs/guide.md', 'bad\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'docs: bad guide', '-m', 'Agent-Task: T-9')
        bad = self.git('rev-parse', 'HEAD').strip()
        self.git('revert', '--no-edit', 'HEAD')
        result = subprocess.run([sys.executable, str(SCRIPT), 'events', '--root', str(self.root), '--base', 'main'],
                                capture_output=True, text=True, check=True)
        tasks = json.loads(result.stdout)
        self.assertEqual([(t['reverted'], t['agent_tasks'], t['paths']) for t in tasks], [(bad, ['T-9'], ['docs/guide.md'])])

    def events(self):
        result = subprocess.run([sys.executable, str(SCRIPT), 'events', '--root', str(self.root), '--base', 'main'],
                                capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout) if result.returncode == 0 else result.stderr

    def test_reverts_are_found_by_message_body_and_merge_reverts_keep_their_tasks(self):
        self.write('docs/policy.md', 'policy\n')
        self.commit('Revert policy documentation')  # a subject, not a revert
        self.assertEqual(self.events(), (0, []))
        self.git('switch', '-q', '-c', 'feature')
        self.write('docs/feature.md', 'feature\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'feature', '-m', 'Agent-Task: T-feature')
        self.git('switch', '-q', 'main')
        self.git('merge', '-q', '--no-ff', '--no-edit', 'feature')
        self.git('revert', '--no-edit', '-m', '1', 'HEAD')
        self.git('commit', '-q', '--amend', '-m', 'Roll back the feature', '-m',
                 'This reverts commit ' + self.git('rev-parse', 'HEAD~1').strip() + '.')
        code, tasks = self.events()
        self.assertEqual(code, 0)
        self.assertEqual([(t['agent_tasks'], t['paths']) for t in tasks], [(['T-feature'], ['docs/feature.md'])])
        result = subprocess.run([sys.executable, str(SCRIPT), 'events', '--root', str(self.root), '--base', 'no-such-ref'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_additive_regressions_are_low_only_as_new_sealed_tests(self):
        table = json.loads((SCRIPTS.parent / 'templates/project/risk.yaml').read_text(encoding='utf-8'))
        self.write('.harness/risk.yaml', json.dumps(table))
        self.write('eslint.config.js', 'export default [{rules: {"no-eval": "error"}}];\n')
        self.commit('use the shipped template')
        self.write('eslint.config.js', 'export default [];\n')
        self.assertEqual(self.classify()['tier'], 'HIGH', 'weakening lint configuration')
        self.git('checkout', '--', 'eslint.config.js')
        sealed = self.outside / 'author' / 'test_regression.py'
        sealed.parent.mkdir(exist_ok=True)
        sealed.write_text(ACCEPTANCE, encoding='utf-8')
        command = subprocess.list2cmdline([sys.executable, '-m', 'unittest', 'tests.test_regression'])
        self.write('tests/__init__.py', '')
        self.commit('tests package')
        subprocess.run([sys.executable, str(GATE), 'seal', '--root', str(self.root), '--base', 'main', '--tests',
                        f'{sealed}=tests/test_regression.py', '--command', command], check=True, capture_output=True)
        self.write('tests/test_regression.py', ACCEPTANCE)
        self.write('src/rule.py', RULE.replace('>= 10', '>= 20'))
        self.write('src/rule.py', RULE)  # only the regression test is added
        self.write('tests/test_unsealed.py', 'import unittest\n')
        subprocess.run([sys.executable, str(GATE), 'check', '--root', str(self.root)], capture_output=True)
        self.assertNotEqual(self.classify()['tier'], 'LOW', 'an added test that is not sealed is not LOW')
        (self.root / 'tests/test_unsealed.py').unlink()
        self.write('src/rule.py', RULE.replace('>= 10', '>= 20'))
        subprocess.run([sys.executable, str(GATE), 'check', '--root', str(self.root)], capture_output=True)
        decided = self.classify()
        self.assertEqual(decided['tier'], 'LOW', decided['reasons'])
        self.assertIn('additive-regression', decided['reasons'][-1])

    def test_capacity_reads_every_unmerged_commit_and_only_open_top_level_questions(self):
        self.git('switch', '-q', '-c', 'risky', 'main')
        self.write('docs/a.md', 'a\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'risky', '-m', 'Risk: HIGH')
        self.write('docs/b.md', 'b\n')
        self.commit('follow-up without trailers')
        self.git('switch', '-q', 'main')
        self.write('.harness/decisions.md', '## Open questions\n\n1. first?\n2. second?\n- [x] answered\n- third?\n'
                                            '  - context\n  - more context\n')
        result = subprocess.run([sys.executable, str(SCRIPT), 'capacity', '--root', str(self.root), '--onto', 'main'],
                                capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)['counts'], {'open_questions': 3, 'unmerged_high': 1, 'unmerged_med': 0})
        result = subprocess.run([sys.executable, str(SCRIPT), 'capacity', '--root', str(self.root), '--onto', 'nope'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_capacity_counts_open_questions_and_unmerged_high_and_med_work(self):
        def capacity(*extra):
            result = subprocess.run([sys.executable, str(SCRIPT), 'capacity', '--root', str(self.root), '--onto', 'main',
                                     *extra], capture_output=True, text=True)
            return result.returncode, json.loads(result.stdout)
        self.assertEqual(capacity(), (0, capacity()[1]))
        for name, tier in (('high-1', 'HIGH'), ('med-1', 'MED'), ('merged', 'HIGH')):
            self.git('switch', '-q', '-c', name, 'main')
            self.write(f'docs/{name}.md', name + '\n')
            self.git('add', '-A')
            self.git('commit', '-qm', name, '-m', f'Risk: {tier}')
        self.git('switch', '-q', 'main')
        self.git('merge', '-q', '--no-ff', '--no-edit', 'merged')
        self.write('.harness/decisions.md', '# Decisions\n\n## Open questions\n\n- a?\n- b?\n\n## Pending\n\n- c (default x)\n')
        code, outcome = capacity()
        self.assertEqual(outcome['counts'], {'open_questions': 2, 'unmerged_high': 1, 'unmerged_med': 1})
        self.assertEqual(code, 0)
        code, outcome = capacity('--max-high', '1', '--max-questions', '2')
        self.assertEqual((code, sorted(outcome['full'])), (1, ['open_questions', 'unmerged_high']))

    def test_trailers_record_tier_and_acceptance(self):
        self.write('docs/guide.md', 'guide v2\n')
        lines = subprocess.run([sys.executable, str(SCRIPT), 'trailers', '--root', str(self.root), '--base', 'main',
                                '--task', 'T-7'], capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(lines, ['Agent-Task: T-7', 'Risk: LOW', 'Acceptance: none'])


if __name__ == '__main__':
    unittest.main()
