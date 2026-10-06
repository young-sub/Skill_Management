import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class HostVerifyTests(unittest.TestCase):
    def test_workflow_acceptance_uses_bound_snapshot_and_host_cases_without_git(self):
        host = runpy.run_path(str(ROOT / 'scripts/host_verify.py'))
        evaluate = host['workflow_audit']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, source in [('host_result.py', ROOT / 'scripts/host_result.py'),
                                 ('project_workflow.py', ROOT / 'authoring/scripts/project_workflow.py')]:
                shutil.copyfile(source, root / name)
            project_root = root / 'project'
            (project_root / '.harness').mkdir(parents=True)
            (project_root / 'source.py').write_text('value = 10')
            (project_root / 'guide.md').write_text('Value must be ten')
            feature = {'id': 'price', 'partition': 'domain', 'sources': ['source.py'],
                       'map': ['guide.md'], 'criteria': ['guide.md'], 'checks': ['price-check']}
            project = {'commands': {'price-check': ['python', 'check.py']},
                       'extensions': {'workflow': {'roots': ['source.py'], 'features': [feature]}}}
            (project_root / '.harness/project.yaml').write_text(json.dumps(project))
            workflow = runpy.run_path(str(root / 'project_workflow.py'))
            inventory = {'source.py': workflow['file_hash'](project_root, 'source.py')}
            state = {'schema_version': 1, 'root': str(project_root), 'intent': 'change',
                     'baseline': {'source.py': 'old'}, 'reviews': {}}
            with patch('subprocess.run', side_effect=AssertionError('Host must not execute Git or candidate commands')):
                initial = workflow['inspect_project'](project_root, project, state, file_inventory=inventory)
                state['reviews']['price'] = {'basis': initial['features'][0]['basis'],
                    'analysis': 'Host-approved review of ten and its owner',
                    'references': ['source.py', 'guide.md'], 'findings': [], 'bundle': 'must-not-read.json'}
                (project_root / 'state.json').write_text(json.dumps(state))
                policy = {'task': 'price', 'snapshot': ['project_workflow.py', 'project/source.py',
                    'project/guide.md', 'project/state.json', 'project/.harness/project.yaml'],
                    'cases': [{'id': 'saved-price', 'exit': 0, 'saved_hex': '3130'}]}
                (root / 'policy.json').write_text(json.dumps(policy))
                config = {'workflow': {'root': 'project', 'state': 'project/state.json',
                                      'checks': {'price': {'price-check': ['saved-price']}}}}
                facts = [{'id': 'saved-price', 'exit': 0, 'saved_hex': '3130'}]
                executions = [{'id': 'saved-price', 'exit': 0, 'timed_out': False,
                               'descendants_killed': False, 'remaining': 0}]
                self.assertEqual(evaluate(root, config, facts, executions)['status'], 'READY_FOR_REVIEW')
                self.assertEqual(evaluate(root, config, [], [])['status'], 'PARTIAL')
                facts[0]['saved_hex'] = '39'
                self.assertEqual(evaluate(root, config, facts, executions)['status'], 'PARTIAL')
                facts[0]['saved_hex'] = '3130'
                state['reviews']['price']['basis'] = 'stale'
                (project_root / 'state.json').write_text(json.dumps(state))
                self.assertEqual(evaluate(root, config, facts, executions)['status'], 'PARTIAL')
                # Correct behavior alone must not accept stale workflow review.
                for name in ('host_verify.py', 'windows_job.py'):
                    shutil.copyfile(ROOT / 'scripts' / name, root / name)
                    policy['snapshot'].append(name)
                (root / 'driver.py').write_text('# protected driver')
                policy['snapshot'].extend(['driver.py', 'execution.json', 'host_result.py'])
                workspace = root / 'workspace'
                workspace.mkdir()
                for name in ('.sandbox/setup_marker.json', '.sandbox-secrets/sandbox_users.json'):
                    path = root / name
                    path.parent.mkdir(exist_ok=True)
                    path.touch()
                executable_hash = hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
                config.update(workspace=str(workspace), home=str(root), codex=sys.executable,
                    python=sys.executable, codex_sha256=executable_hash, python_sha256=executable_hash,
                    timeout=10, cases=[{'id': 'saved-price', 'argv': [sys.executable, '-I',
                        '{authority}/driver.py', '{runtime}/saved'], 'saved': 'saved', 'initial_hex': ''}])
                (root / 'execution.json').write_text(json.dumps(config))
                (root / 'policy.json').write_text(json.dumps(policy))
                real_load = runpy.run_path
                def execute_case(_launcher, argv, **_kwargs):
                    Path(argv[-1]).write_bytes(b'10')
                    return dict(executions[0], stdout='', stderr='')
                def load(path):
                    return {'run': execute_case} if Path(path).name == 'windows_job.py' else real_load(path)
                with patch('runpy.run_path', side_effect=load):
                    self.assertEqual(host['execute'](root)['status'], 'BLOCKED')
                    state['reviews']['price']['basis'] = initial['features'][0]['basis']
                    (project_root / 'state.json').write_text(json.dumps(state))
                    self.assertEqual(host['execute'](root)['status'], 'ACCEPTED')
                config['workflow']['checks']['price']['price-check'] = ['unrelated']
                with self.assertRaises(ValueError):
                    evaluate(root, config, facts, executions)
                config['workflow']['checks']['price']['price-check'] = ['saved-price']
                policy['snapshot'].remove('project/guide.md')
                (root / 'policy.json').write_text(json.dumps(policy))
                with self.assertRaisesRegex(ValueError, 'unbound_workflow_file'):
                    evaluate(root, config, facts, executions)

    def test_windows_environment_preserved_without_provider_secrets(self):
        module = runpy.run_path(str(ROOT / 'scripts/host_verify.py'))
        with patch.dict(os.environ, {'SYSTEMDRIVE': 'C:', 'PROGRAMDATA': 'C:/ProgramData',
                        'USERNAME': 'host-user', 'OPENAI_API_KEY': 'do-not-forward',
                        'CODEX_HOME': 'ordinary-home'}, clear=True):
            env = module['sandbox_env']({'home': 'isolated-home'})
        self.assertEqual(env, {'SYSTEMDRIVE': 'C:', 'PROGRAMDATA': 'C:/ProgramData',
                              'USERNAME': 'host-user', 'CODEX_HOME': 'isolated-home'})

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
