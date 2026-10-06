import hashlib
import json
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class HostVerifyTests(unittest.TestCase):
    def test_host_executes_then_reads_bytes_and_rejects_incomplete_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ['host_verify.py', 'host_result.py', 'windows_job.py']:
                shutil.copyfile(ROOT / 'scripts' / name, root / name)
            workspace = root / 'workspace'
            workspace.mkdir()
            for name in ['.sandbox/setup_marker.json', '.sandbox-secrets/sandbox_users.json']:
                path = root / name
                path.parent.mkdir(exist_ok=True)
                path.touch()
            python_hash = hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
            config = {'workspace': str(workspace), 'home': str(root),
                      'codex': sys.executable, 'python': sys.executable,
                      'codex_sha256': python_hash, 'python_sha256': python_hash, 'timeout': 10,
                      'cases': [{'id': 'price', 'argv': [sys.executable, '-I', '{authority}/driver.py', '{runtime}/saved'],
                                 'saved': 'saved', 'initial_hex': b'old'.hex()}]}
            (root / 'execution.json').write_text(json.dumps(config))
            (root / 'driver.py').write_text('# trusted driver')
            policy = {'task': 'price', 'snapshot': ['driver.py', 'execution.json', 'host_verify.py', 'host_result.py', 'windows_job.py'],
                      'cases': [{'id': 'price', 'exit': 0, 'saved_hex': b'115'.hex()}]}
            (root / 'policy.json').write_text(json.dumps(policy))
            module = runpy.run_path(str(root / 'host_verify.py'))
            real_load = runpy.run_path
            writes = []
            behavior = {'mode': 'normal'}
            def execute(launcher, argv, **kwargs):
                writes.append(argv)
                Path(argv[-1]).write_bytes(b'115')
                if behavior['mode'] == 'missing':
                    Path(argv[-1]).unlink()
                return {'exit': 0, 'stdout': 'PASS', 'stderr': '', 'timed_out': False,
                        'descendants_killed': behavior['mode'] == 'child', 'remaining': 0}
            def load(path):
                return {'run': execute} if Path(path).name == 'windows_job.py' else real_load(path)
            with patch('runpy.run_path', side_effect=load):
                result = module['execute'](root)
                self.assertEqual(result['status'], 'ACCEPTED')
                self.assertEqual(len(writes), 1)
                policy['cases'][0]['saved_hex'] = b'116'.hex()
                (root / 'policy.json').write_text(json.dumps(policy))
                self.assertEqual(module['execute'](root)['status'], 'REJECTED')
                for mode in ['missing', 'child']:
                    behavior['mode'] = mode
                    self.assertEqual(module['execute'](root)['status'], 'BLOCKED')
                policy['snapshot'].remove('driver.py')
                (root / 'policy.json').write_text(json.dumps(policy))
                with self.assertRaisesRegex(ValueError, 'unbound_host_input'):
                    module['execute'](root)
                policy['snapshot'].append('driver.py')
                (root / 'policy.json').write_text(json.dumps(policy))
                config['cases'] = []
                (root / 'execution.json').write_text(json.dumps(config))
                with self.assertRaises(ValueError):
                    module['execute'](root)
                self.assertEqual(len(writes), 4)
                (root / '.sandbox-secrets/sandbox_users.json').unlink()
                with self.assertRaisesRegex(ValueError, 'sandbox_setup_incomplete'):
                    module['require_sandbox_ready'](config)
