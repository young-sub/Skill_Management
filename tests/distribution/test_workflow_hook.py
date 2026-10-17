"""A prompt hook hands off actual project obligations without running work."""
import hashlib
import json
import os
import runpy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / 'authoring/scripts/workflow_context.py'
WORKFLOW = ROOT / 'authoring/scripts/project_workflow.py'


class WorkflowHookTests(unittest.TestCase):
    def test_fresh_unconfigured_checkout_keeps_hook_read_only_without_a_task(self):
        hook = runpy.run_path(str(HOOK))['context']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            (root / 'README.md').write_text('Use the existing native project checks.\n')
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=''):
                result = hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root),
                               'prompt': 'Fix the failing user flow. PRIVATE PROMPT'})
            self.assertEqual(result, {})
            self.assertFalse((root / '.work').exists())
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_unconfigured_hook_bounds_candidate_reads_and_retains_unknown_omissions(self):
        runtime = runpy.run_path(str(WORKFLOW))
        hook = runpy.run_path(str(HOOK))['context']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            (root / '.gitignore').write_text('.work/\n')
            subprocess.run(['git', 'add', '.'], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=t@invalid',
                            'commit', '-qm', 'base'], cwd=root, check=True)
            state = runtime['begin'](root, {}, 'diagnose', request_summary='Investigate current state')
            for index in range(64):
                path = root / '.work/tasks' / f'{index:03}' / 'state.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(dict(state, task_id=str(index),
                    intent='change' if index < 8 else 'diagnose')))
            reads = []
            read_bytes = Path.read_bytes

            def measured_read(path, *args, **kwargs):
                if path.name == 'state.json':
                    reads.append(path)
                return read_bytes(path, *args, **kwargs)

            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=''), mock.patch.object(Path, 'read_bytes', measured_read):
                output = hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root)})
            self.assertLessEqual(len(reads), 8, 'A bounded prompt must not read every retained task')
            detail = json.loads(output['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertEqual(detail['task_record_count'], 64)
            self.assertEqual(detail['task_candidate_omitted'], 56)
            self.assertEqual(detail['task_candidates'], [])
            self.assertFalse(detail['task_discovery_complete'])
            # Exact selection and explicit detailed discovery still inspect later records.
            selected, _ = runtime['task_state'](root, '.work/tasks/063/state.json')
            self.assertEqual(selected['intent'], 'diagnose')
            self.assertEqual(len(runtime['task_candidates'](root, {})), 64)
            binding = runtime['task_context'](root, selected, root / '.work/tasks/063/state.json')
            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=binding):
                selected_output = hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root)})
            selected_detail = json.loads(selected_output['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertEqual(selected_detail['current_task']['task_id'], '63')
            # A later prompt observes changed preview bytes; it does not cache them.
            first_path = root / '.work/tasks/000/state.json'
            first = json.loads(first_path.read_text())
            first['intent'] = 'diagnose'
            first['request']['summary'] = 'Newly observed investigation'
            first_path.write_text(json.dumps(first))
            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=''):
                fresh = hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root)})
            fresh_detail = json.loads(fresh['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertEqual(fresh_detail['task_candidates'][0]['request']['summary'], first['request']['summary'])
            (root / '.work/tasks/063/state.json').write_text('null')
            with self.assertRaisesRegex(ValueError, 'work_target_mismatch'):
                runtime['task_state'](root, '.work/tasks/063/state.json')

    def test_configured_resume_lookup_and_unconfigured_are_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / '.harness').mkdir()
            (root / 'src').mkdir()
            (root / 'src/price.py').write_text('price = 10\n')
            (root / 'map.md').write_text('Price remains ten.\n')
            (root / '.gitignore').write_text('.work/\n')
            project = {'commands': {'price': ['must-not-run']}, 'extensions': {'workflow': {
                'roots': ['src'], 'state': '.work/task.json', 'features': [{'id': 'price',
                'partition': 'domain', 'sources': ['src/price.py'], 'map': ['map.md'],
                'criteria': ['map.md'], 'checks': ['price']}]}}}
            config = root / '.harness/project.yaml'
            config.write_text(json.dumps(project))
            for argv in (['git', 'init', '-q'], ['git', 'add', '.'],
                         ['git', '-c', 'user.name=Fixture', '-c', 'user.email=f@invalid', 'commit', '-qm', 'base']):
                subprocess.run(argv, cwd=root, capture_output=True, check=True)
            subprocess.run([sys.executable, str(WORKFLOW), 'begin', '--root', str(root),
                '--state', '.work/task.json', '--intent', 'feedback', '--target', 'price'], capture_output=True)
            (root / 'src/price.py').write_text('price = 11\n')
            paths = [p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts]
            before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
            payload = {'hook_event_name': 'UserPromptSubmit', 'cwd': str(root / 'src'),
                       'prompt': 'show results only; NEVER ECHO THIS', 'transcript_path': 'must-not-read'}
            def invoke(value=payload, task_context=None):
                env = dict(os.environ)
                env.pop('AGENT_WORKFLOW_CONTEXT', None)
                if task_context:
                    env['AGENT_WORKFLOW_CONTEXT'] = task_context
                result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(value),
                    capture_output=True, text=True, encoding='utf-8', env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            result = invoke()
            self.assertEqual(result['hookSpecificOutput']['hookEventName'], 'UserPromptSubmit')
            context = result['hookSpecificOutput']['additionalContext']
            self.assertIn('regression', context)
            self.assertIn('map.md', context)
            details = json.loads(context.split('\n', 1)[1])
            self.assertIn('scope', details, 'Later work must consume current scope gaps from the existing audit')
            self.assertEqual(details['scope']['status'], 'PARTIAL')
            self.assertTrue(any('UNDECIDED' in gap for gap in details['scope']['gaps']))
            self.assertNotIn('NEVER ECHO THIS', context)
            self.assertNotIn('decision', result)
            self.assertEqual(invoke(), result)
            self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
            self.assertEqual(set(before), {str(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts})
            runtime = runpy.run_path(str(WORKFLOW))
            # Project-level review is ready, while work A still owns an earlier change.
            state = json.loads((root / '.work/task.json').read_text())
            state['intent'] = 'change'
            state['targets'] = []
            for work_id, work_state in [('W-A', state), ('W-B', runtime['begin'](root, project, 'change'))]:
                directory = root / '.work/goals/active' / work_id
                directory.mkdir(parents=True)
                audit = runtime['inspect_project'](root, project, work_state)
                work_state = runtime['record_review'](root, project, work_state, {
                    'feature': 'price', 'basis': audit['features'][0]['basis'],
                    'analysis': 'Reviewed price and requirement.', 'references': ['map.md'], 'findings': []})
                (directory / 'work.json').write_text(json.dumps({'work_id': work_id, 'state': 'active',
                    'source_commit': work_state['base'], 'workflow_baseline': work_state}))
                if work_id == 'W-B':
                    (root / '.work/task.json').write_text(json.dumps(work_state))
            snapshot = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
            context = invoke()['hookSpecificOutput']['additionalContext']
            details = json.loads(context.split('\n', 1)[1])
            self.assertEqual(details['status'], 'READY_FOR_REVIEW')
            self.assertEqual(details['active_work_count'], 2)
            works = {item['work_id']: item for item in details['active_work']}
            self.assertEqual(works['W-A']['status'], 'PARTIAL')
            self.assertIn('verification', works['W-A']['obligations'][0]['requires'])
            self.assertEqual(works['W-B']['status'], 'READY_FOR_REVIEW')
            self.assertNotIn('selected_work_id', details, 'Prompt text is not a trusted session binding')
            a_state, a_path = runtime['work_record'](root, 'W-A')
            binding = runtime['task_context'](root, a_state, a_path, 'W-A')
            linked = json.loads(invoke(task_context=binding)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertIn('current_task', linked, 'Hook must deliver the explicit invocation task, without guessing')
            self.assertEqual(linked['current_task']['work_id'], 'W-A')
            self.assertEqual(linked['current_task']['status'], 'PARTIAL')
            self.assertIn('verification', linked['current_task']['obligations'][0]['requires'])
            self.assertEqual(snapshot, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts})
            (root / '.work/goals/active/W-A/workflow.json').write_text('null')
            details = json.loads(invoke()['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertEqual(details['active_work'][0]['status'], 'BLOCKED')
            self.assertEqual(details['active_work'][1]['status'], 'READY_FOR_REVIEW')
            for index in range(9):
                directory = root / '.work/goals/active' / f'W-Z{index}'
                directory.mkdir()
                (directory / 'work.json').write_text('{}')
            context = invoke()['hookSpecificOutput']['additionalContext']
            details = json.loads(context.split('\n', 1)[1])
            self.assertEqual(details['active_work_count'], 11)
            self.assertEqual(details['active_work_omitted'], 3)
            self.assertEqual(len(details['active_work']), 8)
            self.assertLess(len(context), 6000)
            (root / '.work/task.json').write_text('null')
            self.assertIn('workflow_state_must_be_object', invoke()['systemMessage'])
            config.write_text('{}')
            missing_config = invoke()
            omissions = json.loads(missing_config['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertEqual(omissions['status'], 'NOT_CONFIGURED')
            self.assertEqual(omissions['task_record_count'], 11)
            self.assertEqual(omissions['task_candidate_omitted'], 3)
            self.assertFalse(omissions['task_discovery_complete'])
            config.unlink()
            self.assertEqual(invoke(), missing_config)
            self.assertEqual(invoke(dict(payload, hook_event_name='Stop')), {})


if __name__ == '__main__':
    unittest.main()
