import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


class InstallHostTests(unittest.TestCase):
    def test_canonical_helpers_and_existing_target_preservation(self):
        scripts = Path(__file__).resolve().parents[2] / 'scripts'
        spec = importlib.util.spec_from_file_location('install_host', scripts / 'install_host_verifier.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / 'bundle'; bundle.mkdir()
            parent = root / 'authority'; parent.mkdir()
            workspace = root / 'workspace'; workspace.mkdir()
            for name in ['.sandbox/setup_marker.json', '.sandbox-secrets/sandbox_users.json']:
                path = root / name
                path.parent.mkdir(exist_ok=True)
                path.touch()
            names = ['host_verify.py', 'host_result.py', 'windows_job.py', 'host_handoff.py']
            for name in names:
                (bundle / name).write_text('raise SystemExit("candidate helper executed")')
            (bundle / 'driver.py').write_text('print("driver")')
            digest = hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
            config = {'workspace': str(workspace), 'home': str(root), 'codex': sys.executable,
                      'python': sys.executable, 'codex_sha256': digest, 'python_sha256': digest,
                      'timeout': 10, 'cases': [{'id': 'one', 'argv': [sys.executable, '-I', '{authority}/driver.py'],
                                             'saved': 'saved', 'initial_hex': ''}]}
            (bundle / 'execution.json').write_text(json.dumps(config))
            (bundle / 'project_workflow.py').write_text('raise SystemExit("candidate evaluator executed")')
            policy = {'task': 'one', 'snapshot': names + ['driver.py', 'execution.json', 'project_workflow.py'],
                      'cases': [{'id': 'one', 'exit': 0, 'saved_hex': ''}]}
            (bundle / 'policy.json').write_text(json.dumps(policy))
            target = parent / 'installed'
            with patch.object(module, '_probe', return_value={'verified': True}):
                result = module.install(bundle, target)
                self.assertEqual(result['status'], 'INSTALLED')
                for name in names:
                    self.assertEqual((target / name).read_bytes(), (scripts / name).read_bytes())
                self.assertEqual((target / 'project_workflow.py').read_bytes(),
                                 (scripts.parent / 'authoring/scripts/project_workflow.py').read_bytes())
                before = {p.name: p.read_bytes() for p in target.iterdir() if p.is_file()}
                with self.assertRaises(FileExistsError):
                    module.install(bundle, target)
                self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir() if p.is_file()})
                (root / '.sandbox-secrets/sandbox_users.json').unlink()
                with self.assertRaisesRegex(ValueError, 'sandbox_setup_incomplete'):
                    module.install(bundle, parent / 'not-created')
                self.assertFalse((parent / 'not-created').exists())
