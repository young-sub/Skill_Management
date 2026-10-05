"""A prompt hook hands off actual project obligations without running work."""
import hashlib
import json
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
            (root / '.work/task.json').write_text('null')
            self.assertIn('workflow_state_must_be_object', invoke()['systemMessage'])
            config.write_text('{}')
            self.assertEqual(invoke(), {})
            config.unlink()
            self.assertEqual(invoke(), {})
            self.assertEqual(invoke(dict(payload, hook_event_name='Stop')), {})


if __name__ == '__main__':
    unittest.main()
