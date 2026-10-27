"""Paired review-loop runner, driven by a fake Claude executable (no model)."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location('review_loop', ROOT / 'evals/review-loop/tools/run.py')
loop = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(loop)

FAKE = r'''
import json
from pathlib import Path
import sys

args = sys.argv[1:]
text = args[args.index('-p') + 1]
log = Path(__file__).with_name('calls.jsonl')
calls = log.read_text(encoding='utf-8').splitlines() if log.exists() else []
role = ('verifier' if '검증 담당입니다' in text else 'fix' if '검증 담당이 당신의 변경을' in text
        else 'self' if '다시 검증해' in text else 'implement')
seen = {name: Path(name).read_text(encoding='utf-8') if Path(name).exists() else None
        for name in ('value.txt', 'remove.txt', 'verify.txt', 'hidden.py', 'judge.log')}
with log.open('a', encoding='utf-8') as stream:
    stream.write(json.dumps({'role': role, 'argv': args, 'seen': seen}) + '\n')
answer = 'done'
if role == 'implement':
    Path('value.txt').write_text('bad', encoding='utf-8')
    Path('remove.txt').unlink()
    Path('impl.txt').write_text('new', encoding='utf-8')
elif role == 'verifier':
    Path('verify.txt').write_text('failing test', encoding='utf-8')
    Path('value.txt').write_text('tampered', encoding='utf-8')
    answer = 'found\n{"verdict": "incomplete", "violations": [{"path": "value", "test": "verify.txt:1", "observed": "bad"}]}'
elif role == 'fix':
    Path('value.txt').write_text('good', encoding='utf-8')
print(json.dumps({'type': 'system', 'subtype': 'init', 'session_id': f'sid-{len(calls) + 1}', 'model': 'fake'}))
print(json.dumps({'type': 'result', 'result': answer, 'num_turns': 1, 'duration_ms': 10, 'total_cost_usd': 0.5,
                  'usage': {'input_tokens': 1, 'output_tokens': 1, 'cache_read_input_tokens': 0,
                            'cache_creation_input_tokens': 0}}))
'''

V2_CHECK = "from pathlib import Path\nassert Path('impl.txt').exists()\n"
V3_CHECK = ("from pathlib import Path\nPath('judge.log').write_text('names the hidden test', encoding='utf-8')\n"
            "assert Path('value.txt').read_text() == 'good'\n")


def python(code_file):
    return subprocess.list2cmdline([sys.executable, code_file])


class ReviewLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.project = base / 'project'
        self.project.mkdir()
        for name, text in (('value.txt', 'base'), ('remove.txt', 'tracked'), ('.gitignore', '*.log\n')):
            (self.project / name).write_text(text, encoding='utf-8')
        for args in (('init', '-q'), ('add', '.'), ('-c', 'user.name=t', '-c', 'user.email=t@invalid', 'commit', '-qm', 'base')):
            subprocess.run(['git', *args], cwd=self.project, check=True, capture_output=True)
        (base / 'fake.py').write_text(FAKE, encoding='utf-8')
        (base / 'v2.py').write_text(V2_CHECK, encoding='utf-8')
        (base / 'v3.py').write_text(V3_CHECK, encoding='utf-8')
        scenario = {'id': 'paired', 'project': str(self.project), 'area': 'Domain', 'prompt': '구현해 주세요',
                    'hidden': [{'name': 'v2', 'origin': 'v2', 'expect': 'pass', 'files': {'h2.py': 'v2.py'},
                                'command': python('h2.py')},
                               {'name': 'v3', 'origin': 'v3', 'expect': 'pass', 'files': {'hidden.py': 'v3.py'},
                                'command': python('hidden.py')}]}
        (base / 'scenarios.json').write_text(json.dumps({'schema_version': 1, 'scenarios': [scenario]}), encoding='utf-8')
        self.base, self.output = base, base / 'out'
        argv = ['--scenarios', str(base / 'scenarios.json'), '--output', str(self.output), '--reps', '1',
                '--claude', json.dumps([sys.executable, str(base / 'fake.py')]), '--work-root', str(base / 'w')]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(loop.main(argv), 0)
        self.calls = [json.loads(l) for l in (base / 'calls.jsonl').read_text(encoding='utf-8').splitlines()]

    def row(self, branch):
        return json.loads((self.output / 'paired/rep1' / branch / 'result.json').read_text(encoding='utf-8'))

    def test_each_branch_starts_from_the_implementation_without_hidden_or_judging_files(self):
        roles = [c['role'] for c in self.calls]
        self.assertEqual(roles, ['implement', 'self', 'verifier', 'fix'])
        for call in self.calls[1:]:
            self.assertEqual(call['seen']['value.txt'], 'bad')
            self.assertIsNone(call['seen']['remove.txt'])  # a tracked deletion survives restore
            self.assertIsNone(call['seen']['hidden.py'])
            self.assertIsNone(call['seen']['judge.log'])
        self.assertIsNone(self.calls[1]['seen']['verify.txt'])

    def test_follow_ups_fork_the_implementer_session_and_the_verifier_is_fresh(self):
        by_role = {c['role']: c['argv'] for c in self.calls}
        for role in ('self', 'fix'):
            argv = by_role[role]
            self.assertEqual(argv[argv.index('--resume') + 1], 'sid-1')
            self.assertIn('--fork-session', argv)
        self.assertNotIn('--resume', by_role['verifier'])

    def test_verifier_tests_stay_and_its_product_edits_are_undone(self):
        fix = next(c for c in self.calls if c['role'] == 'fix')
        self.assertEqual(fix['seen']['verify.txt'], 'failing test')
        indep = self.row('indep')
        self.assertEqual(indep['verifier_tests'], ['verify.txt'])
        self.assertEqual(indep['verifier_edited'], ['value.txt', 'verify.txt'])
        self.assertEqual(indep['verdict']['verdict'], 'incomplete')

    def test_outcomes_costs_and_paired_report(self):
        off, self_row, indep = self.row('off'), self.row('self'), self.row('indep')
        self.assertEqual([r['verified_success'] for r in (off, self_row, indep)], [False, False, True])
        self.assertTrue(all(r['v2_verified_success'] for r in (off, self_row, indep)))
        self.assertTrue(off['false_completion'] and self_row['false_completion'])
        self.assertEqual((off['cost_usd'], self_row['extra_cost_usd'], indep['extra_cost_usd']), (0.5, 0.5, 1.0))
        report = json.loads((self.output / 'report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['flips']['self->indep'], {'gained': 1, 'lost': 0})
        self.assertEqual(report['spent_usd'], 2.0)
        self.assertIn('final.diff', {p.name for p in (self.output / 'paired/rep1/indep').iterdir()})
        self.assertFalse(any((self.base / 'w').iterdir()))

    def test_a_finished_cell_is_never_replayed(self):
        argv = ['--scenarios', str(self.base / 'scenarios.json'), '--output', str(self.output), '--reps', '1',
                '--claude', json.dumps([sys.executable, str(self.base / 'fake.py')]), '--work-root', str(self.base / 'w')]
        with contextlib.redirect_stdout(io.StringIO()):
            loop.main(argv)
        self.assertEqual(len((self.base / 'calls.jsonl').read_text(encoding='utf-8').splitlines()), 4)


if __name__ == '__main__':
    unittest.main()
