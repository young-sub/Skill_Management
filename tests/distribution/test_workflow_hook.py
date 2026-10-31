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
    def test_budget_counts_final_display_omissions_separately_from_discovery(self):
        output = runpy.run_path(str(HOOK))['hook_output']
        summary = {'status': 'TASK_NOT_SELECTED', 'task_candidate_count': 5,
            'task_candidate_omitted': 0, 'task_discovery_complete': True,
            'task_candidates': [{'state': 'x' * 2000} for _ in range(5)],
            'current_task': {'detail': {'action': 'lookup', 'state': '.work/task.json'},
                'ui_system_count': 5, 'ui_system_omitted': 1,
                'ui_systems': [{'guide': 'x' * 1500} for _ in range(4)]}}
        text = output(summary)['hookSpecificOutput']['additionalContext']
        result = json.loads(text.split('\n', 1)[1])
        self.assertLessEqual(len(text), 5500)
        self.assertEqual(result['task_candidate_omitted'], 0, 'Discovery omissions are unchanged')
        self.assertTrue(result['task_discovery_complete'])
        self.assertEqual(result['task_candidate_display_omitted'],
                         5 - len(result.get('task_candidates', [])))
        current = result['current_task']
        self.assertEqual(current['ui_system_omitted'], 5 - len(current.get('ui_systems', [])))

    def test_unselected_prompt_is_silent_and_never_reads_work(self):
        hook = runpy.run_path(str(HOOK))['context']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            (root / '.harness').mkdir()
            (root / '.harness/project.yaml').write_text(json.dumps({'extensions': {'workflow': {
                'roots': ['src'], 'features': [{'id': 'api', 'partition': 'domain',
                    'sources': ['src/api.py'], 'map': ['map.md'], 'criteria': ['map.md'], 'checks': []}],
                'state': '.work/task.json'}}}))
            no_git = mock.Mock(side_effect=AssertionError('unselected prompts must not run git or the runtime'))
            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=''), \
                 mock.patch.dict(hook.__globals__, {'subprocess': mock.Mock(run=no_git)}):
                # Prompts are not routed: questions, results requests and fix requests all stay silent.
                for prompt in ('What does this regex match?', 'show results only', 'Fix the failing user flow',
                               '상품 저장 버그 고쳐줘'):
                    self.assertEqual(hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root), 'prompt': prompt}), {})
            self.assertFalse((root / '.work').exists())

    def test_budget_preserves_blocker_next_action_and_exact_lookup_before_optional_details(self):
        output = runpy.run_path(str(HOOK))['hook_output']
        pointer = {'action': 'lookup', 'state': '.work/tasks/exact/state.json', 'read_only': True}
        summary = {'status': 'SELECTED_TASK', 'current_task': {
            'status': 'PARTIAL', 'task_acceptance': 'BLOCKED',
            'verification_blocker_count': 1, 'verification_blockers': ['prepared_plan_task_mismatch'],
            'next_action_count': 1, 'next_actions': [{'target': 'api', 'requires': ['verification']}],
            'detail': pointer, 'feature_count': 9, 'features': [{'criteria': ['가' * 9000]}],
            'obligations': [{'huge': 'x' * 10000}], 'request': {'summary': 'x' * 10000}}}
        text = output(summary)['hookSpecificOutput']['additionalContext']
        self.assertLess(len(text), 6000)
        current = json.loads(text.split('\n', 1)[1])['current_task']
        self.assertEqual(current['detail'], pointer)
        self.assertEqual(current['verification_blockers'], ['prepared_plan_task_mismatch'])
        self.assertEqual(current['next_actions'], summary['current_task']['next_actions'])
        self.assertEqual(current['task_acceptance'], 'BLOCKED')
        self.assertEqual(current['feature_count'], 9)

    def test_prompt_context_prioritizes_target_ui_guides_and_feature_ui_paths(self):
        runtime = runpy.run_path(str(WORKFLOW))
        hook = runpy.run_path(str(HOOK))['context']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / '.harness').mkdir()
            (root / 'src').mkdir()
            (root / 'docs').mkdir()
            (root / '.gitignore').write_text('.work/\n')
            files = {
                'src/price.py': 'price = 10\n', 'src/cart.py': 'cart = []\n',
                'src/tokens.css': ':root {}\n', 'src/cart_widget.py': 'class CartWidget: pass\n',
                'docs/map.md': 'Features\n', 'docs/testing.md': 'Run relevant checks.\n',
                'docs/ui-price.md': 'Price UI states.\n', 'docs/ui-cart.md': 'Cart UI states.\n',
            }
            for index in range(4):
                files[f'docs/ui-unused-{index}.md'] = 'Unused shared UI guide.\n'
            for index in range(1, 5):
                files[f'docs/ui-cart-{index}.md'] = 'Shared cart UI states.\n'
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            systems = {f'unused-{index}': {'guide': f'docs/ui-unused-{index}.md',
                'tokens': ['src/tokens.css'], 'components': ['src/cart_widget.py'],
                'consumers': [], 'exceptions': []}
                for index in range(4)}
            systems['shared-cart'] = {'guide': 'docs/ui-cart.md', 'tokens': ['src/tokens.css'],
                'components': ['src/cart_widget.py'], 'consumers': ['cart'], 'exceptions': []}
            for index in range(1, 5):
                systems[f'shared-cart-{index}'] = {'guide': f'docs/ui-cart-{index}.md',
                    'tokens': ['src/tokens.css'], 'components': ['src/cart_widget.py'],
                    'consumers': ['cart'], 'exceptions': []}
            project = {'commands': {}, 'extensions': {'workflow': {
                'roots': ['src'], 'state': '.work/task.json',
                'features': [
                    {'id': 'price', 'partition': 'domain', 'sources': ['src/price.py'],
                     'map': ['docs/map.md'], 'criteria': ['docs/testing.md'], 'checks': [],
                     'ui': ['docs/ui-price.md']},
                    {'id': 'cart', 'partition': 'ui', 'sources': ['src/cart.py'],
                     'map': ['docs/map.md'], 'criteria': ['docs/testing.md'], 'checks': []},
                ],
                'ui_systems': systems,
            }}}
            (root / '.harness/project.yaml').write_text(json.dumps(project))
            for argv in (['git', 'init', '-q'], ['git', 'add', '.'],
                         ['git', '-c', 'user.name=Fixture', '-c', 'user.email=f@invalid',
                          'commit', '-qm', 'base']):
                subprocess.run(argv, cwd=root, capture_output=True, check=True)
            state = runtime['begin'](root, project, 'change', ['price', 'cart'])
            state_path = root / '.work/task.json'
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state))
            binding = runtime['task_context'](root, state, state_path)
            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=binding):
                output = hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root)})
            additional_context = output['hookSpecificOutput']['additionalContext']
            self.assertLess(len(additional_context), 6000)
            detail = json.loads(additional_context.split('\n', 1)[1])
            current = detail['current_task']
            features = {feature['id']: feature for feature in current['features']}
            self.assertEqual(features['price'].get('ui'), ['docs/ui-price.md'])
            self.assertIn('docs/ui-price.md', features['price']['reuse']['guides'])
            self.assertEqual(features['cart']['reuse']['shared_ui_count'], 5)
            self.assertEqual(features['cart']['reuse']['shared_ui_omitted'], 1)
            self.assertEqual(current['ui_system_count'], 5)
            self.assertEqual(current['ui_system_omitted'], 1)
            self.assertEqual(len(current['ui_systems']), 4)
            self.assertEqual(current['ui_system_detail'], current['detail'])
            self.assertEqual(current.get('ui_systems', [])[0]['guide'], 'docs/ui-cart.md')
            self.assertNotIn('ui_systems', detail, 'Do not duplicate project UI systems outside the task')

    def test_fresh_unconfigured_checkout_keeps_hook_read_only_without_a_task(self):
        hook = runpy.run_path(str(HOOK))['context']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            (root / 'README.md').write_text('Use the existing native project checks.\n')
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=''):
                self.assertEqual(hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root),
                                       'prompt': 'Fix the failing user flow. PRIVATE PROMPT'}), {})
            self.assertFalse((root / '.work').exists())
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_unconfigured_hook_reads_no_task_until_one_is_selected(self):
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
                self.assertEqual(hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root)}), {})
            self.assertEqual(reads, [], 'An unselected prompt reads no retained task')
            # Exact selection and explicit resume discovery still inspect every record.
            selected, _ = runtime['task_state'](root, '.work/tasks/063/state.json')
            self.assertEqual(selected['intent'], 'diagnose')
            self.assertEqual(len(runtime['task_candidates'](root, {})), 64)
            binding = runtime['task_context'](root, selected, root / '.work/tasks/063/state.json')
            with mock.patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=binding):
                selected_output = hook({'hook_event_name': 'UserPromptSubmit', 'cwd': str(root)})
            selected_detail = json.loads(selected_output['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertEqual(selected_detail['current_task']['task_id'], '63')
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
            self.assertEqual(invoke(), {}, 'No task candidates or status on an unselected prompt')
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
            self.assertEqual(invoke(), {}, 'Unselected prompts stay identical with active work present')
            for work_id, expected in [('W-A', 'PARTIAL'), ('W-B', 'READY_FOR_REVIEW')]:
                selected, _ = runtime['work_record'](root, work_id)
                self.assertEqual(runtime['inspect_project'](root, project, selected)['status'], expected)
            a_state, a_path = runtime['work_record'](root, 'W-A')
            binding = runtime['task_context'](root, a_state, a_path, 'W-A')
            linked = json.loads(invoke(task_context=binding)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertIn('current_task', linked, 'Hook must deliver the explicit invocation task, without guessing')
            self.assertEqual(linked['current_task']['work_id'], 'W-A')
            self.assertEqual(linked['current_task']['status'], 'PARTIAL')
            self.assertIn('verification', linked['current_task']['obligations'][0]['requires'])
            self.assertEqual(snapshot, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts})
            config.write_text('{}')
            self.assertEqual(invoke(), {}, 'Missing configuration does not add setup guidance')
            config.unlink()
            self.assertEqual(invoke(dict(payload, prompt='Translate hello')), {})
            self.assertEqual(invoke(dict(payload, hook_event_name='Stop')), {})


if __name__ == '__main__':
    unittest.main()
