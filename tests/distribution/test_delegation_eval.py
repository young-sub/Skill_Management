"""Offline runner checks: every model invocation uses a temporary Python fake."""
import contextlib
import copy
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


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('delegation_eval', ROOT / 'scripts/run_delegation_eval.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

FAKE = r'''
import json
from pathlib import Path
import sys
import time

args = sys.argv[1:]
options = json.loads(args[args.index('-p') + 1])
calls = Path('calls.jsonl')
previous = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
with calls.open('a', encoding='utf-8') as stream:
    stream.write(json.dumps({'argv': args, 'hidden_exists': Path('hidden.py').exists(),
                             'previous_calls': len(previous), 'before': Path('value.txt').read_text()}) + '\n')
if options.get('edit'):
    Path('value.txt').write_text(options['edit'], encoding='utf-8')
print(json.dumps({'type': 'assistant', 'message': {'usage': {'input_tokens': 7, 'output_tokens': 3,
    'cache_read_input_tokens': 2, 'cache_creation_input_tokens': 1}, 'content': [
    {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'agentic-coding:swarm'}},
    {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/agentic-coding/SKILL.md'}}]}}), flush=True)
print(json.dumps({'type': 'system', 'subtype': 'hook_response', 'hook_name': 'UserPromptSubmit',
    'output': json.dumps({'hookSpecificOutput': {'additionalContext': '한글 context'}})}), flush=True)
print(json.dumps({'type': 'system', 'subtype': 'hook_response', 'hook_name': 'Stop',
    'output': json.dumps({'decision': 'block'})}), flush=True)
if options.get('sleep'):
    time.sleep(options['sleep'])
if options.get('crash'):
    sys.exit(9)
result = {'type': 'result', 'result': options.get('answer', 'Completed'), 'num_turns': 2,
    'duration_ms': 1250, 'total_cost_usd': 0.125}
if not options.get('fallback'):
    result['usage'] = {'input_tokens': 100, 'output_tokens': 20,
                       'cache_read_input_tokens': 30, 'cache_creation_input_tokens': 10}
print(json.dumps(result), flush=True)
'''


def shell_python(code):
    args = [sys.executable, '-c', code]
    return subprocess.list2cmdline(args) if os.name == 'nt' else shlex.join(args)


class DelegationEvalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / 'project'
        self.project.mkdir()
        (self.project / 'value.txt').write_text('good', encoding='utf-8')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=test', '-c', 'user.email=test@invalid', 'commit', '-qm', 'initial')
        self.ref = self.git('rev-parse', 'HEAD').stdout.strip()
        self.fake = self.base / 'fake.py'
        self.fake.write_text(FAKE, encoding='utf-8')
        self.command = [sys.executable, str(self.fake)]
        self.plugin = self.base / 'plugin'
        (self.plugin / '.claude-plugin').mkdir(parents=True)
        (self.plugin / '.claude-plugin/plugin.json').write_text('{}', encoding='utf-8')
        (self.base / 'acceptance.py').write_text(
            "from pathlib import Path\nassert Path('value.txt').read_text() == 'good'\n", encoding='utf-8')
        self.scenario = {'id': 'held-out', 'project': str(self.project), 'ref': self.ref, 'area': 'Domain',
                         'prompt': '{}', 'hidden': [{'name': 'accept', 'files': {'hidden.py': 'acceptance.py'},
                         'command': shell_python("exec(open('hidden.py', encoding='utf-8').read())"), 'expect': 'pass'}]}
        self.config = {'schema_version': 1, 'scenarios': [self.scenario]}
        self.file = self.base / 'scenarios.json'
        self.output = self.base / 'output'

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.project, check=True, capture_output=True, text=True)

    def write_config(self):
        self.file.write_text(json.dumps(self.config, ensure_ascii=False), encoding='utf-8')

    def cli(self, *extra):
        self.write_config()
        argv = ['--scenarios', str(self.file), '--output', str(self.output), '--condition', 'off=off',
                '--claude', json.dumps(self.command), '--reps', '1', '--jobs', '2', *extra]
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = runner.main(argv)
        return code, stdout.getvalue()

    def result(self, condition='off', rep=1, scenario='held-out'):
        return json.loads((self.output / scenario / condition / f'rep{rep}/result.json').read_text(encoding='utf-8'))

    def calls(self, condition='off'):
        path = self.output / 'held-out' / condition / 'rep1/repo/calls.jsonl'
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]

    def test_off_plugin_argv_and_metrics(self):
        self.config['disable_plugins'] = ['custom@market', 'other@market']
        code, rendered = self.cli('--condition', f'on=plugin:{self.plugin}')
        self.assertEqual(code, 0)
        for condition in ('off', 'on'):
            call = self.calls(condition)[0]
            args = call['argv']
            self.assertEqual(json.loads(args[args.index('--settings') + 1]),
                             {'enabledPlugins': {'custom@market': False, 'other@market': False}})
            self.assertEqual('--plugin-dir' in args, condition == 'on')
            if condition == 'on':
                self.assertEqual(args[args.index('--plugin-dir') + 1], str(self.plugin.resolve()))
            self.assertEqual(args[args.index('--permission-mode') + 1], 'bypassPermissions')
            self.assertIn('--include-hook-events', args)
            self.assertFalse(call['hidden_exists'])
            result = self.result(condition)
            self.assertTrue(result['acceptance_passed'])
            self.assertTrue(result['verified_success'])
            self.assertEqual(result['usage']['input_tokens'], 100)
            self.assertEqual(result['cost_usd'], 0.125)
            self.assertEqual(result['duration_s'], 1.25)
            self.assertEqual(result['turns'], 2)
            self.assertEqual(result['plugin_skills'], ['agentic-coding:swarm'])
            self.assertEqual(result['tools'], {'Skill': 1, 'Read': 1})
            self.assertEqual(len(result['plugin_file_reads']), 1)
            self.assertEqual(result['hook_context_chars'], len('한글 context'))
            self.assertEqual(result['stop_blocks'], 1)
        self.assertIn('1/1', rendered)
        self.assertEqual((self.project / 'value.txt').read_text(), 'good')

    def test_hidden_after_probes_fault_restored(self):
        self.scenario['probes'] = [{'name': 'mutation', 'file': 'value.txt', 'find': 'good', 'replace': 'bad',
            'command': shell_python("from pathlib import Path; assert not Path('hidden.py').exists(); "
                                    "Path('probe-ran').write_text('yes'); assert Path('value.txt').read_text() == 'good'")}]
        self.assertEqual(self.cli()[0], 0)
        result = self.result()
        self.assertTrue(result['probes'][0]['detected'])
        self.assertEqual(result['probe_kill_rate'], 1)
        repo = self.output / 'held-out/off/rep1/repo'
        self.assertEqual((repo / 'probe-ran').read_text(), 'yes')
        self.assertEqual((repo / 'value.txt').read_text(), 'good')
        self.assertTrue((repo / 'hidden.py').is_file())

    def test_regression_runs_before_hidden_files_exist(self):
        self.scenario['regression'] = shell_python("from pathlib import Path; assert not Path('hidden.py').exists()")
        self.assertEqual(self.cli()[0], 0)
        self.assertTrue(self.result()['regression']['passed'])

    def test_false_completion_and_admitted_incomplete(self):
        self.scenario['prompt'] = json.dumps({'edit': 'bad', 'answer': 'All done'})
        admitted = copy.deepcopy(self.scenario)
        admitted.update(id='admitted', prompt=json.dumps({'edit': 'bad', 'answer': 'UNABLE TO COMPLETE the change'}))
        self.config['scenarios'].append(admitted)
        self.assertEqual(self.cli()[0], 1)
        result = self.result()
        self.assertTrue(result['false_completion'])
        self.assertFalse(result['admitted_incomplete'])
        self.assertFalse(result['verified_success'])
        result = self.result(scenario='admitted')
        self.assertTrue(result['admitted_incomplete'])
        self.assertFalse(result['false_completion'])

    def test_regression_failure(self):
        self.scenario['regression'] = shell_python('raise SystemExit(4)')
        self.assertEqual(self.cli()[0], 1)
        result = self.result()
        self.assertTrue(result['acceptance_passed'])
        self.assertEqual(result['regression']['exit'], 4)
        self.assertFalse(result['verified_success'])
        self.assertTrue(result['false_completion'])

    def test_sequence_fresh_sessions_same_clone(self):
        del self.scenario['prompt']
        self.scenario.update(area='Sequence', prompts=[json.dumps({'edit': 'intermediate', 'answer': 'first'}),
                                                      json.dumps({'edit': 'good', 'answer': 'second'})])
        self.assertEqual(self.cli()[0], 0)
        calls = self.calls()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1]['before'], 'intermediate')
        self.assertEqual(calls[1]['previous_calls'], 1)
        self.assertTrue(all('--continue' not in c['argv'] and not c['hidden_exists'] for c in calls))
        result = self.result()
        self.assertEqual([s['answer'] for s in result['sessions']], ['first', 'second'])
        self.assertEqual(result['usage']['input_tokens'], 200)
        self.assertEqual(result['cost_usd'], 0.25)
        self.assertEqual(result['tools']['Skill'], 2)
        transcript = self.output / 'held-out/off/rep1/session.jsonl'
        self.assertEqual(sum(json.loads(line).get('type') == 'result'
                             for line in transcript.read_text().splitlines() if line.strip()), 2)

    def test_fault_committed_then_fixed_and_extra_links(self):
        dependencies = self.project / 'dependencies'
        dependencies.mkdir()
        (dependencies / 'marker').write_text('shared')
        self.scenario['links'] = ['dependencies']
        self.scenario['fault'] = {'file': 'value.txt', 'find': 'good', 'replace': 'bad', 'commit_message': 'planted'}
        self.scenario['prompt'] = json.dumps({'edit': 'good'})
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(self.calls()[0]['before'], 'bad')
        repo = self.output / 'held-out/off/rep1/repo'
        self.assertEqual((repo / 'dependencies/marker').read_text(), 'shared')
        commit = subprocess.run(['git', 'log', '-1', '--format=%s'], cwd=repo, capture_output=True, text=True, check=True)
        self.assertEqual(commit.stdout.strip(), 'planted')
        self.assertEqual((self.project / 'value.txt').read_text(), 'good')

    def test_deps_root_links_and_pruning_never_touch_shared_directories(self):
        (self.project / 'dependencies').mkdir()
        (self.project / 'dependencies/marker').write_text('user')
        deps = self.base / 'deps' / self.project.name / 'dependencies'
        deps.mkdir(parents=True)
        (deps / 'marker').write_text('evaluation copy')
        self.scenario['links'] = ['dependencies']
        reader = ("from pathlib import Path; "
                  "assert Path('dependencies/marker').read_text() == 'evaluation copy'")
        self.scenario['regression'] = shell_python(reader)
        self.assertEqual(self.cli('--deps-root', str(self.base / 'deps'), '--prune-clones')[0], 0)
        self.assertTrue(self.result()['verified_success'])
        self.assertFalse((self.output / 'held-out/off/rep1/repo').exists())
        self.assertTrue((self.output / 'held-out/off/rep1/result.json').is_file())
        self.assertEqual((deps / 'marker').read_text(), 'evaluation copy')
        self.assertEqual((self.project / 'dependencies/marker').read_text(), 'user')

    def test_judging_retries_a_failed_check_once(self):
        flaky = ("from pathlib import Path; p = Path('attempt'); n = int(p.read_text()) if p.exists() else 0; "
                 "p.write_text(str(n + 1)); raise SystemExit(1 if n == 0 else 0)")
        self.scenario['regression'] = shell_python(flaky)
        self.assertEqual(self.cli()[0], 0)
        result = self.result()
        self.assertTrue(result['verified_success'])
        self.assertEqual(result['regression']['first_attempt']['exit'], 1)
        self.scenario['regression'] = shell_python('raise SystemExit(3)')
        self.output = self.base / 'output-2'
        self.assertEqual(self.cli()[0], 1)
        self.assertFalse(self.result()['verified_success'])

    def test_crash_and_timeout_still_record_and_continue(self):
        self.scenario['prompt'] = json.dumps({'crash': True})
        timeout = copy.deepcopy(self.scenario)
        timeout.update(id='timeout', prompt=json.dumps({'sleep': 10}), budget_seconds=0.5)
        self.config['scenarios'].append(timeout)
        good = copy.deepcopy(self.scenario)
        good.update(id='good', prompt='{}')
        self.config['scenarios'].append(good)
        self.assertEqual(self.cli()[0], 1)
        self.assertEqual(self.result()['exit'], 9)
        self.assertFalse(self.result()['verified_success'])
        self.assertTrue(self.result(scenario='timeout')['timed_out'])
        self.assertFalse(self.result(scenario='timeout')['verified_success'])
        self.assertTrue(self.result(scenario='good')['verified_success'])
        report = json.loads((self.output / 'report.json').read_text())
        self.assertEqual(len(report['failures']), 2)

    def test_fallback_usage_and_defensive_parser(self):
        self.scenario['prompt'] = json.dumps({'fallback': True})
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(self.result()['usage'], dict(zip(runner.TOKEN_KEYS, (7, 3, 2, 1))))
        transcript = self.base / 'malformed.jsonl'
        transcript.write_text('\n'.join(['garbage', '[]', 'null',
            json.dumps({'type': 'assistant', 'message': {'content': [None, {'type': 'tool_use', 'input': None}]}}),
            json.dumps({'type': 'assistant', 'message': '[]'}),
            json.dumps({'subtype': 'hook_response', 'output': 'nonsense'}),
            json.dumps({'subtype': 'hook_response', 'output': '[]'}),
            json.dumps({'subtype': 'hook_response', 'output': {'hookSpecificOutput': '[]'}}),
            json.dumps({'type': 'result', 'result': 'done', 'usage': {'input_tokens': 42}})]), encoding='utf-8')
        result = runner.summarize_session(transcript)
        self.assertEqual(result['usage']['input_tokens'], 42)
        self.assertIsNone(result['usage']['output_tokens'])
        self.assertIsNone(result['cost_usd'])

    def test_nondefault_branch_ref_is_pinned_before_clone(self):
        self.git('branch', 'heldout-ref')
        self.scenario['ref'] = 'heldout-ref'
        self.assertEqual(self.cli()[0], 0)
        repo = self.output / 'held-out/off/rep1/repo'
        current = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, check=True, capture_output=True, text=True)
        self.assertEqual(current.stdout.strip(), self.ref)

    def test_missing_executable_records_failure_without_aborting(self):
        self.command = [str(self.base / 'does-not-exist')]
        self.assertEqual(self.cli()[0], 1)
        result = self.result()
        self.assertFalse(result['verified_success'])
        self.assertTrue(result['errors'])
        self.assertIsNone(result['cost_usd'])
        self.assertTrue((self.output / 'report.md').is_file())

    def test_marker_after_answer_truncation_still_counts(self):
        self.scenario['prompt'] = json.dumps({'edit': 'bad', 'answer': 'x' * 4100 + ' 미완료'})
        self.assertEqual(self.cli()[0], 1)
        result = self.result()
        self.assertEqual(len(result['answer']), 4000)
        self.assertTrue(result['admitted_incomplete'])
        self.assertFalse(result['false_completion'])

    def test_dry_run_matrix_no_clone(self):
        with patch.object(runner, 'clone', side_effect=AssertionError('must not clone')):
            code, text = self.cli('--dry-run', '--condition', f'on=plugin:{self.plugin}', '--reps', '2')
        self.assertEqual(code, 0)
        self.assertFalse(self.output.exists())
        plan = json.loads(text)
        self.assertEqual([(r['rep'], r['condition']) for r in plan['runs']],
                         [(1, 'off'), (1, 'on'), (2, 'off'), (2, 'on')])
        self.assertEqual(json.loads(plan['argv']['off'][plan['argv']['off'].index('--settings') + 1]),
                         {'enabledPlugins': {'agentic-coding@agentic-coding': False}})

    def test_validation_before_any_run(self):
        mutations = [lambda d: d.update(schema_version=2),
                     lambda d: d.update(disable_plugins='bad'),
                     lambda d: d.update(incomplete_markers=[1]),
                     lambda d: d['scenarios'].append(copy.deepcopy(d['scenarios'][0])),
                     lambda d: d['scenarios'][0].update(id='../escape'),
                     lambda d: d['scenarios'][0].update(area='API'),
                     lambda d: d['scenarios'][0].update(prompts=['duplicate']),
                     lambda d: d['scenarios'][0].update(prompt=3),
                     lambda d: d['scenarios'][0].update(ref='missing-ref'),
                     lambda d: d['scenarios'][0].update(budget_seconds=-1),
                     lambda d: d['scenarios'][0].update(probes=[{}]),
                     lambda d: d['scenarios'][0]['hidden'][0].update(expect='fail'),
                     lambda d: d['scenarios'][0]['hidden'][0].update(files={'../escape': 'acceptance.py'}),
                     lambda d: d['scenarios'][0]['hidden'][0].update(files={'hidden.py': 'missing.py'})]
        original = copy.deepcopy(self.config)
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.config = copy.deepcopy(original)
                mutate(self.config)
                with patch.object(runner, 'clone', side_effect=AssertionError('must not clone')):
                    with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                        self.cli()
                self.assertEqual(error.exception.code, 2)
                self.assertFalse(self.output.exists())

    def test_cli_validation(self):
        for extra in [('--condition', 'off=off'), ('--condition', 'bad=wat'),
                      ('--condition', 'on=plugin:missing'), ('--jobs', '0'), ('--reps', '0'),
                      ('--timeout', 'nan'), ('--only', 'missing'), ('--claude', '[]')]:
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.cli(*extra)
            self.assertFalse(self.output.exists())
        self.output.mkdir()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.cli('--dry-run')

    def test_aggregate_fixed_math_and_unknowns(self):
        def row(success, tokens, cost, wall, probe, incomplete):
            return {'scenario': 's', 'condition': 'off', 'rep': int(wall), 'verified_success': success,
                    'false_completion': not success and not incomplete, 'admitted_incomplete': incomplete,
                    'usage': dict(zip(runner.TOKEN_KEYS, (tokens, tokens / 2, 0, 0))), 'cost_usd': cost,
                    'wall_seconds': wall, 'probe_kill_rate': probe, 'plugin_skills': ['skill'],
                    'hook_context_chars': wall * 10, 'errors': [], 'hidden': [{'name': 'h', 'passed': success}],
                    'regression': None, 'acceptance_passed': success, 'timed_out': False}
        rows = [row(True, 100, 0.1, 2, 1, False), row(False, 300, 0.3, 4, 0.5, False),
                row(False, 200, 0.2, 3, None, True)]
        report = runner.aggregate(rows)
        c = report['conditions']['off']
        self.assertEqual(c['verified_success'], {'k': 1, 'n': 3, 'rate': 1 / 3})
        self.assertEqual(c['false_completion_rate'], 1 / 3)
        self.assertEqual(c['mean_probe_kill_rate'], 0.75)
        self.assertEqual(c['admitted_incomplete'], 1)
        self.assertEqual(c['median_tokens']['input_tokens'], 200)
        self.assertEqual(c['total_tokens']['output_tokens'], 300)
        self.assertAlmostEqual(c['total_cost_usd'], 0.6)
        self.assertEqual(c['median_wall_seconds'], 3)
        self.assertEqual(c['tokens_per_verified_success'], 900)
        self.assertEqual(c['plugin_skill_invocations'], 3)
        self.assertEqual(c['mean_hook_context_chars'], 30)
        self.assertEqual(report['scenarios']['s']['off'], {'k': 1, 'n': 3})
        self.assertEqual(len(report['failures']), 2)
        rows[0]['cost_usd'] = None
        self.assertIsNone(runner.aggregate(rows)['conditions']['off']['total_cost_usd'])


if __name__ == '__main__':
    unittest.main()
