"""A prompt hook hands off actual project obligations without running work."""
import hashlib
import json
import runpy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / 'authoring/scripts/workflow_context.py'
WORKFLOW = ROOT / 'authoring/scripts/project_workflow.py'


class WorkflowHookTests(unittest.TestCase):
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
            def invoke(value=payload):
                result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(value),
                    capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            result = invoke()
            self.assertEqual(result['hookSpecificOutput']['hookEventName'], 'UserPromptSubmit')
            context = result['hookSpecificOutput']['additionalContext']
            self.assertIn('regression', context)
            self.assertIn('map.md', context)
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
            self.assertEqual(invoke(), {})
            config.unlink()
            self.assertEqual(invoke(), {})
            self.assertEqual(invoke(dict(payload, hook_event_name='Stop')), {})


if __name__ == '__main__':
    unittest.main()
