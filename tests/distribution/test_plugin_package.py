"""Exercise the distributable tree, including its installed command consumer."""
import json
import hashlib
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SH = shutil.which('sh')


class PluginPackageTests(unittest.TestCase):
    @unittest.skipUnless(SH, 'POSIX shell required for hook commands')
    def test_hook_commands_with_only_one_python_name(self):
        hooks = json.loads((ROOT / 'distribution/hooks.json').read_text())['hooks']
        with tempfile.TemporaryDirectory(prefix='hook runtime ') as temporary:
            root = Path(temporary)
            package = root / 'plugin with spaces'
            (package / 'hooks').mkdir(parents=True)
            for name in ('workflow_context.py', 'completion_guard.py'):
                shutil.copyfile(ROOT / 'authoring/scripts' / name, package / 'hooks' / name)
            launcher = ROOT / 'distribution/run-hook.sh'
            if launcher.exists():
                shutil.copyfile(launcher, package / 'hooks/run-hook.sh')
            transcript = root / 'turn.jsonl'
            transcript.write_text(json.dumps({'type': 'assistant', 'message': {'content': [
                {'type': 'tool_use', 'name': 'Edit', 'input': {'file_path': str(root / 'app.py'), 'new_string': 'x' + chr(10) * 5}}]}}))
            for runtime in ('python3', 'python', 'broken-python3', 'missing'):
                bin_dir = root / runtime
                bin_dir.mkdir()
                shutil.copy2(SH, bin_dir / ('sh.exe' if os.name == 'nt' else 'sh'))
                if os.name == 'nt':
                    for dll in Path(SH).parent.glob('msys-*.dll'):
                        shutil.copyfile(dll, bin_dir / dll.name)
                if runtime != 'missing':
                    shim = bin_dir / ('python' if runtime == 'broken-python3' else runtime)
                    shim.write_text('#!/bin/sh\nexec "' + Path(sys.executable).as_posix() + '" "$@"\n', newline='')
                    shim.chmod(0o755)
                    if runtime == 'broken-python3':
                        broken = bin_dir / 'python3'
                        broken.write_text('#!/bin/sh\nexit 1\n', newline='')
                        broken.chmod(0o755)
                for variable in ('PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT'):
                    env = {k: v for k, v in os.environ.items()
                           if k not in ('PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT', 'AGENT_WORKFLOW_CONTEXT')}
                    env.update(PATH=str(bin_dir), **{variable: str(package)})
                    for event, entries in hooks.items():
                        with self.subTest(runtime=runtime, variable=variable, event=event):
                            result = subprocess.run([SH, '-c', entries[0]['hooks'][0]['command']],
                                env=env, input=json.dumps({'hook_event_name': event, 'cwd': str(root),
                                    'prompt': 'The output is broken, fix it', 'transcript_path': str(transcript)}),
                                capture_output=True, text=True, timeout=30)
                            if runtime == 'missing':
                                self.assertEqual(result.returncode, 127)
                                self.assertIn('Python 3', result.stderr)
                            else:
                                self.assertEqual(result.returncode, 0, result.stderr)
                                output = json.loads(result.stdout)
                                if event == 'Stop':
                                    self.assertEqual(output['decision'], 'block')
                                else:
                                    self.assertEqual(output, {})  # no selected task, no context
                    if runtime != 'missing':
                        (package / 'hooks/failure.py').write_text('raise SystemExit(23)\n')
                        failed = subprocess.run([SH, str(package / 'hooks/run-hook.sh'), 'failure.py'],
                            env=env, capture_output=True, timeout=30)
                        self.assertEqual(failed.returncode, 23, 'Keep the hook failure, never retry it')

    def test_package_runs_without_checkout_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'plugin'
            command = [sys.executable, str(ROOT / 'scripts/build_plugin.py'),
                       '--output', str(package)]
            built = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            guide = package / 'README.md'
            self.assertTrue(guide.is_file(), 'Portable plugin needs its own entrypoint guide')
            for link in re.findall(r'\[[^]]+\]\(([^)]+)\)', guide.read_text(encoding='utf-8')):
                target = (package / link.split('#', 1)[0]).resolve()
                self.assertTrue(target.is_relative_to(package.resolve()), link)
                self.assertTrue(target.is_file(), link)
            manifest = json.loads((package / 'plugin.json').read_text())
            compatibility = json.loads((package / '.codex-plugin/plugin.json').read_text())
            origin_path = package / 'build-origin.json'
            self.assertTrue(origin_path.is_file(), 'Portable consumers need source identity without querying ancestor Git')
            origin = json.loads(origin_path.read_text(encoding='utf-8'))
            self.assertEqual(origin['version'], manifest['version'])
            self.assertEqual(origin['source_commit'], subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip())
            self.assertEqual(origin['source_tree'], subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD^{tree}'], text=True).strip())
            self.assertEqual(origin['source_dirty'], bool(subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'])))
            self.assertEqual(manifest['name'], compatibility['name'])
            claude_manifest = package / '.claude-plugin/plugin.json'
            self.assertTrue(claude_manifest.is_file(), 'Claude must retain plugin identity independently of its directory name')
            self.assertEqual(json.loads(claude_manifest.read_text()), manifest)
            # Codex 0.160.0 ignores bundled hooks with the portable $schema marker.
            # Keep the working compatibility manifest until that host path is fixed.
            self.assertNotIn('$schema', manifest)
            self.assertEqual(compatibility.get('hooks'), './hooks/hooks.json')
            catalog = json.loads((ROOT / 'distribution/catalog.json').read_text())
            self.assertEqual({p.parent.name for p in (package / 'skills').glob('*/SKILL.md')},
                             set(catalog['public_skills']))
            capture = root / 'capture.json'
            run = subprocess.run([sys.executable, str(package / 'scripts/run_check.py'),
                                  '--cwd', str(root), '--output', str(capture), '--',
                                  sys.executable, '-c', 'print(6 * 7)'], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            observed = json.loads(capture.read_text())
            self.assertEqual(observed['stdout'].strip(), '42')
            self.assertEqual(observed['exit_code'], 0)
            self.assertIsNone(observed['behavior_verdict'])
            hook = json.loads((package / 'hooks/hooks.json').read_text())['hooks']
            self.assertEqual(set(hook), {'UserPromptSubmit', 'Stop'})
            transcript = root / 'transcript.jsonl'
            transcript.write_text('\n'.join(json.dumps(entry) for entry in (
                {'type': 'user', 'message': {'content': 'fix'}},
                {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit',
                    'input': {'file_path': str(root / 'app.py'), 'new_string': 'x' + chr(10) * 5}}]}})), encoding='utf-8')
            stop_command = hook['Stop'][0]['hooks'][0]['commandWindows']
            stop_environment = {k: v for k, v in os.environ.items() if k != 'PLUGIN_ROOT'}
            stop_environment['CLAUDE_PLUGIN_ROOT'] = str(package)
            for active, expected in ((False, 'block'), (True, None)):
                stopped = subprocess.run(['powershell', '-NoProfile', '-Command', stop_command],
                    input=json.dumps({'hook_event_name': 'Stop', 'cwd': str(root), 'stop_hook_active': active,
                                      'transcript_path': str(transcript)}),
                    env=stop_environment, capture_output=True, text=True, timeout=30)
                self.assertEqual(stopped.returncode, 0, stopped.stderr)
                self.assertEqual(json.loads(stopped.stdout).get('decision'), expected)
            # The packaged acceptance hook finds probe_check beside it in the package and is silent
            # in a checkout without a sealed contract.
            acceptance = hook['Stop'][0]['hooks'][1]
            self.assertIn('acceptance_gate.py', acceptance['commandWindows'])
            gated = subprocess.run(['powershell', '-NoProfile', '-Command', acceptance['commandWindows']],
                input=json.dumps({'hook_event_name': 'Stop', 'cwd': str(ROOT)}),
                env=stop_environment, capture_output=True, text=True, timeout=60)
            self.assertEqual((gated.returncode, json.loads(gated.stdout)), (0, {}), gated.stderr)
            hook_command = hook['UserPromptSubmit'][0]['hooks'][0]['commandWindows']
            # Exercise the distributed shell command with the host-provided root.
            for root_variable in ('PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT'):
                environment = {k: v for k, v in os.environ.items()
                               if k not in ('PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT')}
                environment[root_variable] = str(package)
                hooked = subprocess.run(['powershell', '-NoProfile', '-Command', hook_command],
                    input=json.dumps({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root)}),
                    env=environment, capture_output=True, text=True, timeout=30)
                self.assertEqual(hooked.returncode, 0, root_variable + hooked.stdout + hooked.stderr)
                self.assertEqual(json.loads(hooked.stdout), {})
            for script in ('project_workflow.py', 'verification_results.py'):
                help_result = subprocess.run([
                    sys.executable, str(package / 'skills/agent-workflow/scripts' / script),
                    '--help'], cwd=root, capture_output=True)
                self.assertEqual(help_result.returncode, 0, help_result.stderr)
            # A plugin consumer needs no checkout-specific capture path.
            consumer = root / 'consumer'
            consumer.mkdir()
            (consumer / '.gitignore').write_text('.work/\n')
            (consumer / 'probe.py').write_text(
                'import json,sys\nfrom pathlib import Path\n'
                'p=Path(".work/count");p.parent.mkdir(exist_ok=True)\n'
                'p.write_text(str(int(p.read_text())+1) if p.exists() else "1")\n'
                'Path(sys.argv[1]).write_text(json.dumps({"count":1,"cents":115}))\n')
            for argv in (['git', 'init', '-q'], ['git', 'add', '.'],
                         ['git', '-c', 'user.name=Fixture', '-c', 'user.email=f@invalid', 'commit', '-qm', 'base']):
                subprocess.run(argv, cwd=consumer, check=True, capture_output=True)
            before_hook = {str(p): p.read_bytes() for p in consumer.rglob('*') if p.is_file()}
            for root_variable in ('PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT'):
                environment = {k: v for k, v in os.environ.items()
                               if k not in ('PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT', 'AGENT_WORKFLOW_CONTEXT')}
                environment[root_variable] = str(package)
                # The packaged hook runs and, with no selected task, adds nothing to any prompt.
                for prompt in ('The probe output is broken, fix it', 'Translate hello into Korean'):
                    delivered = subprocess.run(['powershell', '-NoProfile', '-Command', hook_command],
                        input=json.dumps({'hook_event_name': 'UserPromptSubmit', 'cwd': str(consumer),
                                          'prompt': prompt}),
                        env=environment, capture_output=True, text=True, timeout=30)
                    self.assertEqual(delivered.returncode, 0, delivered.stderr)
                    self.assertEqual(json.loads(delivered.stdout), {})
            self.assertEqual(before_hook, {str(p): p.read_bytes() for p in consumer.rglob('*') if p.is_file()})
            revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=consumer, text=True).strip()
            viewer = package / 'skills/agent-workflow/scripts/verification_results.py'
            def execute(label, *extra):
                raw = '.work/' + label + '.json'
                plan = root / (label + '-plan.json')
                plan.write_text(json.dumps({'schema_version': 1, 'plan_id': label, 'checks': [{
                    'id': 'price', 'feature_id': 'price', 'expected': '115 cents', 'criteria_revision': '1',
                    'required': True, 'selection': {'status': 'selected', 'reason': 'package execution'},
                    'conditions': {'source': {'revision': revision, 'diff': hashlib.sha256(b'').hexdigest()},
                        'criteria': {'revision': '1'}, 'command': {'argv': [sys.executable, 'probe.py', raw],
                            'cwd': str(consumer)}, 'dependency': {'file_refs': ['probe.py']},
                        'fixture': {'file_refs': ['probe.py']}, 'runtime': {'kind': 'python'}},
                    'raw_observations': [{'path': raw, 'pointer': '$', 'assertions': [
                        {'pointer': '/count', 'equals': 1}, {'pointer': '/cents', 'equals': 115}]}]}]}))
                return subprocess.run([sys.executable, str(viewer), '--execute', '--plan', str(plan),
                    '--evidence-dir', str(consumer / '.work' / label), *extra], cwd=root, capture_output=True, text=True)
            implicit = execute('implicit')
            self.assertEqual(implicit.returncode, 0, implicit.stdout + implicit.stderr)
            self.assertEqual((consumer / '.work/count').read_text(), '1')
            (package / 'plugin.json').rename(package / 'plugin-hidden.json')
            standalone = execute('standalone')
            self.assertEqual(standalone.returncode, 0, standalone.stdout + standalone.stderr)
            self.assertEqual((consumer / '.work/count').read_text(), '2')
            sibling_capture = viewer.with_name('run_check.py')
            sibling_capture.rename(viewer.with_name('run_check-hidden.py'))
            missing = execute('no-manifest')
            self.assertEqual(missing.returncode, 2, missing.stdout + missing.stderr)
            self.assertEqual((consumer / '.work/count').read_text(), '2')
            explicit = execute('explicit', '--run-check', str(package / 'scripts/run_check.py'))
            self.assertEqual(explicit.returncode, 0, explicit.stdout + explicit.stderr)
            self.assertEqual((consumer / '.work/count').read_text(), '3')
            viewer.with_name('run_check-hidden.py').rename(sibling_capture)
            (package / 'plugin-hidden.json').rename(package / 'plugin.json')
            user_file = package / 'user-note.txt'
            user_file.write_text('preserve me')
            again = subprocess.run(command, capture_output=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(user_file.read_text(), 'preserve me')
            inventory = json.loads((package / 'package-files.json').read_text())
            self.assertNotIn('user-note.txt', inventory['files'])
            self.assertEqual(inventory['files']['README.md'], hashlib.sha256(guide.read_bytes()).hexdigest())
            self.assertEqual(inventory['files']['build-origin.json'], hashlib.sha256(origin_path.read_bytes()).hexdigest())
            self.assertFalse(any('.work' in p or '.env' in p for p in inventory['files']))
            updater = subprocess.run([sys.executable, str(package / 'scripts/update_plugin.py'),
                                      '--help'], cwd=root, capture_output=True)
            self.assertEqual(updater.returncode, 0, updater.stderr)


if __name__ == '__main__':
    unittest.main()
