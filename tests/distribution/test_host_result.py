"""Host result binding; filesystem authority is separately tested on Windows."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class HostResultTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('host_result', Path(__file__).resolve().parents[2] / 'scripts/host_result.py')
        self.runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runtime)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'snapshot').mkdir()
        (self.root / 'snapshot/app.py').write_text('price = 115')
        self.policy = {'task': 'price', 'snapshot': ['snapshot/app.py'],
                       'cases': [{'id': 'save', 'exit': 0, 'saved_hex': b'115'.hex()},
                                 {'id': 'reject', 'exit': 3, 'saved_hex': b'old'.hex()}]}
        (self.root / 'policy.json').write_text(json.dumps(self.policy))
        self.facts = [{'id': 'save', 'exit': 0, 'saved_hex': b'115'.hex()},
                      {'id': 'reject', 'exit': 3, 'saved_hex': b'old'.hex()}]
        self.executions = [{'id': f['id'], 'exit': f['exit'], 'timed_out': False,
                            'descendants_killed': False, 'remaining': 0} for f in self.facts]

    def finish(self, run, facts):
        return self.runtime.finish(self.root, run['run_id'], facts, executions=self.executions)

    def test_actual_bytes_and_all_cases_required(self):
        for facts, verdict in [(self.facts, 'ACCEPTED'), ([], 'BLOCKED'),
                               (self.facts[:1], 'BLOCKED'),
                               ([self.facts[0], self.facts[0]], 'BLOCKED'),
                               ([dict(self.facts[0], exit=False), self.facts[1]], 'BLOCKED'),
                               (self.facts + [dict(self.facts[0], id='extra')], 'BLOCKED'),
                               ([dict(self.facts[0], saved_hex=b'114'.hex()), self.facts[1]], 'REJECTED')]:
            with self.subTest(facts=facts):
                run = self.runtime.begin(self.root)
                self.assertEqual(self.finish(run, facts)['status'], verdict)

    def test_pending_stale_and_duplicate_finish_are_not_accepted(self):
        run = self.runtime.begin(self.root)
        self.assertEqual(self.runtime.lookup(self.root, run['run_id'], 'price')['status'], 'PENDING')
        self.finish(run, self.facts)
        with self.assertRaises(ValueError):
            self.finish(run, self.facts)
        with self.assertRaises(ValueError):
            self.runtime.lookup(self.root, run['run_id'], 'other-task')
        (self.root / 'snapshot/app.py').write_text('price = 114')
        with self.assertRaises(ValueError):
            self.runtime.lookup(self.root, run['run_id'], 'price')

    def test_policy_change_and_missing_snapshot_block_publication(self):
        for target in ['policy.json', 'snapshot/app.py']:
            with self.subTest(target=target):
                path = self.root / target
                before = path.read_bytes()
                run = self.runtime.begin(self.root)
                path.write_bytes(before + b' ')
                with self.assertRaises(ValueError):
                    self.finish(run, self.facts)
                path.write_bytes(before)
                self.assertEqual(self.runtime.lookup(self.root, run['run_id'], 'price')['status'], 'PENDING')

    def test_policy_cannot_select_outside_authority_or_empty_cases(self):
        for field, value in [('snapshot', ['../outside']), ('cases', [])]:
            policy = dict(self.policy, **{field: value})
            (self.root / 'policy.json').write_text(json.dumps(policy))
            with self.assertRaises(ValueError):
                self.runtime.begin(self.root)

    def test_interrupted_terminal_record_is_not_reused_or_replaced(self):
        run = self.runtime.begin(self.root)
        terminal = self.root / 'runs' / (run['run_id'] + '.result.json')
        terminal.write_text('{"status":"ACCEPTED",')
        before = terminal.read_bytes()
        with self.assertRaises(ValueError):
            self.runtime.lookup(self.root, run['run_id'], 'price')
        with self.assertRaises(ValueError):
            self.finish(run, self.facts)
        self.assertEqual(terminal.read_bytes(), before)

    def test_missing_or_unclean_execution_blocks_matching_bytes(self):
        for executions in [None, [], [dict(self.executions[0], descendants_killed=True), self.executions[1]]]:
            run = self.runtime.begin(self.root)
            result = self.runtime.finish(self.root, run['run_id'], self.facts, executions=executions)
            self.assertEqual(result['status'], 'BLOCKED')
