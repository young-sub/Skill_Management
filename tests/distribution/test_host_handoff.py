import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class HostHandoffTests(unittest.TestCase):
    def test_fixed_task_snapshot_binding_and_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            host = base / 'host'; host.mkdir()
            candidate = base / 'candidate'; candidate.mkdir()
            for name in ('host_result.py', 'host_handoff.py'):
                shutil.copyfile(ROOT / 'scripts' / name, host / name)
            (host / 'source.py').write_text('value = 10')
            (candidate / 'source.py').write_text('value = 10')
            config = {'candidate': str(candidate), 'files': {'source.py': 'source.py'}}
            (host / 'handoff.json').write_text(json.dumps(config))
            policy = {'task': 'price-task', 'snapshot': ['source.py', 'host_handoff.py', 'handoff.json'],
                      'cases': [{'id': 'price', 'exit': 0, 'saved_hex': '3130'}]}
            (host / 'policy.json').write_text(json.dumps(policy))
            api = runpy.run_path(str(host / 'host_handoff.py'))
            actual_load = runpy.run_path
            executions = []
            mutate_after_execution = False
            def execute(root):
                executions.append(root)
                result = actual_load(str(host / 'host_result.py'))
                run = result['begin'](host)
                if mutate_after_execution:
                    (candidate / 'source.py').write_text('changed while running')
                return result['finish'](host, run['run_id'], policy['cases'], executions=[
                    {'id': 'price', 'exit': 0, 'timed_out': False,
                     'descendants_killed': False, 'remaining': 0}])
            def load(path):
                return {'execute': execute} if Path(path).name == 'host_verify.py' else actual_load(path)
            with patch('runpy.run_path', side_effect=load):
                with self.assertRaisesRegex(ValueError, 'task_mismatch'):
                    api['handoff'](host, 'other-task')
                self.assertEqual(executions, [])
                with self.assertRaises(ValueError):
                    api['handoff'](host, 'price-task', run_id='')
                self.assertEqual(executions, [])
                result = api['handoff'](host, 'price-task')
                self.assertEqual(result['status'], 'ACCEPTED')
                before = {p.name: p.read_bytes() for p in (host / 'runs').iterdir()}
                looked = api['handoff'](host, 'price-task', run_id=result['run_id'])
                self.assertEqual(looked['status'], 'ACCEPTED')
                self.assertEqual(len(executions), 1)
                self.assertEqual(before, {p.name: p.read_bytes() for p in (host / 'runs').iterdir()})
                (candidate / 'source.py').write_text('value = 9')
                with self.assertRaisesRegex(ValueError, 'candidate_snapshot_changed'):
                    api['handoff'](host, 'price-task')
                self.assertEqual(len(executions), 1)
                (candidate / 'source.py').write_text('value = 10')
                mutate_after_execution = True
                stale = api['handoff'](host, 'price-task')
                self.assertEqual(stale['status'], 'BLOCKED')
                self.assertEqual(stale['verification']['status'], 'ACCEPTED')
                self.assertTrue(stale['run_id'])
                config['files'] = {'../outside': 'source.py'}
                (host / 'handoff.json').write_text(json.dumps(config))
                with self.assertRaises(ValueError):
                    api['handoff'](host, 'price-task')
                policy['snapshot'].remove('handoff.json')
                (host / 'policy.json').write_text(json.dumps(policy))
                with self.assertRaisesRegex(ValueError, 'unbound_handoff'):
                    api['handoff'](host, 'price-task')
