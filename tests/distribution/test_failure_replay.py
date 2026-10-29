"""Failure-replay assets: transcript edit replay and the pre-registered counting rule, without any model."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'evals/failure-replay/tools'
sys.dont_write_bytecode = True


def load(name):
    spec = importlib.util.spec_from_file_location(f'failure_replay_{name}', TOOLS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reconstruct = load('reconstruct')
replay = load('replay')


class ReconstructTests(unittest.TestCase):
    def test_rebase_rewrites_every_spelling_of_the_old_workspace(self):
        old = 'C:\\Users\\YS\\Temp\\run\\repo'
        text = 'cd "C:/Users/YS/Temp/run/repo" && cat /c/Users/YS/Temp/run/repo/a.ts; C:\\Users\\YS\\Temp\\run\\repo\\b.ts'
        rebased = reconstruct.rebase(text, old, 'C:/e/w/1/r')
        self.assertEqual(rebased, 'cd "C:/e/w/1/r" && cat C:/e/w/1/r/a.ts; C:\\e\\w\\1\\r\\b.ts')

    def test_edit_matches_lf_text_against_a_crlf_file_and_reports_misses(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            (repo / 'a.ts').write_bytes(b'one\r\ntwo\r\n')
            log = []
            reconstruct.apply_edit(repo, 'X:/old', {'name': 'Edit', 'input': {
                'file_path': 'X:/old/a.ts', 'old_string': 'one\ntwo', 'new_string': 'one\n2'}}, log)
            reconstruct.apply_edit(repo, 'X:/old', {'name': 'Edit', 'input': {
                'file_path': 'X:/old/a.ts', 'old_string': 'absent', 'new_string': 'x'}}, log)
            self.assertEqual((repo / 'a.ts').read_bytes(), b'one\r\n2\r\n')
            self.assertEqual(len([line for line in log if 'MISS' in line]), 1)

    def test_shell_calls_that_only_read_are_not_replayed(self):
        self.assertFalse(reconstruct.MAY_WRITE.search('grep -n "x" src/a.ts 2>&1 | head'))
        self.assertTrue(reconstruct.MAY_WRITE.search("python - <<'EOF'\nopen(p,'w').write(s)\nEOF"))
        self.assertTrue(reconstruct.MAY_WRITE.search('sed -i "s/a/b/" src/a.ts'))


class CountingRuleTests(unittest.TestCase):
    def write(self, output, stage, attempt, value):
        path = output / stage / attempt / 'result.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def test_a_counts_only_a_flag_backed_by_a_test_the_reference_passes(self):
        attempts = [{'id': 'f1', 'kind': 'failure', 'plugin': '0.1.89', 'missed_path': 'copy (duplicate)'},
                    {'id': 'f2', 'kind': 'failure', 'plugin': '0.1.89', 'missed_path': 'copy (duplicate)'},
                    {'id': 'c1', 'kind': 'control', 'plugin': '0.1.89'}]
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            for attempt in attempts:
                self.write(output, 'precheck', attempt['id'], {'faithful': True, 'guards': {
                    '0.1.89': {'blocks': False}, 'current': {'blocks': True}}, 'inventory': {'hit': False}})
            flagged = {'verdict': {'verdict': 'incomplete', 'violations': [{'path': 'copy'}]}}
            self.write(output, 'verify', 'f1', {**flagged, 'on_attempt': {'passed': False, 'failed': ['copy']}})
            self.write(output, 'retest', 'f1', {'on_reference': {'passed': True, 'failed': []}})
            # Flagged, but the only failing test also fails on the reference: a stricter reading.
            self.write(output, 'verify', 'f2', {**flagged, 'on_attempt': {'passed': False, 'failed': ['nfkc']}})
            self.write(output, 'retest', 'f2', {'on_reference': {'passed': False, 'failed': ['nfkc']}})
            self.write(output, 'verify', 'c1', {**flagged, 'on_attempt': {'passed': False, 'failed': ['x']}})
            original = replay.attempts
            replay.attempts = lambda: attempts
            try:
                summary = replay.report(output)['summary']
            finally:
                replay.attempts = original
        self.assertEqual(summary['failure'], {'n': 2, 'guard_then_blocked': 0, 'guard_current_blocked': 2,
                                              'b_inventory_hit': 0, 'a_flagged': 2, 'a_changed': 1,
                                              'a_named_missed_path': 2, 'a_asked_missed_path': 0,
                                              'a_changed_and_guard_current': 1})
        self.assertEqual(summary['control']['a_flagged'], 1)


if __name__ == '__main__':
    unittest.main()
