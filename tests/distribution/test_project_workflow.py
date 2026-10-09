"""Real repository changes drive resumable obligations, never submitted PASS flags."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'authoring/scripts/project_workflow.py'


class ProjectWorkflowTests(unittest.TestCase):
    def invoke(self, action, *args, context=None):
        env = dict(os.environ)
        env.pop('AGENT_WORKFLOW_CONTEXT', None)
        if context is not None:
            env['AGENT_WORKFLOW_CONTEXT'] = context
        process = subprocess.run([sys.executable, str(SCRIPT), action, '--root', str(self.root), *args],
                                 capture_output=True, text=True, encoding='utf-8', env=env)
        self.assertTrue(process.stdout.strip(), 'Workflow entrypoint cannot handle ' + action + ': ' + process.stderr)
        return process, json.loads(process.stdout)

    def test_explicit_context_restores_one_of_multiple_tasks_and_refuses_replacement(self):
        self.write('.harness/project.yaml', json.dumps(self.project))
        _, a = self.invoke('start', '--intent', 'feedback', '--target', 'api')
        self.assertIn('task_context', a, 'Starting ordinary work must return a reusable invocation context')
        _, b = self.invoke('start', '--intent', 'change', '--target', 'cli')
        self.assertNotEqual(a['task_context'], b['task_context'])
        _, ambiguous = self.invoke('resume')
        self.assertEqual(ambiguous['status'], 'BLOCKED')
        self.assertEqual(len(ambiguous['task_candidates']), 2)
        context = a['task_context']
        _, audit = self.invoke('resume', context=context)
        state_path = self.root / audit['task']['state']
        other_path = self.root / b['task']['state']
        other = other_path.read_bytes()
        basis = next(f['basis'] for f in audit['features'] if f['id'] == 'api')
        review = self.write('.work/review.json', json.dumps({'feature': 'api', 'basis': basis,
            'analysis': 'API owner traced; semantic evidence remains pending',
            'references': ['src/api.py'], 'findings': ['Need actual readback']}))
        self.invoke('review', '--review', str(review), context=context)
        feedback = self.write('.work/feedback.json', json.dumps({'id': 'F1', 'feature': 'api',
            'expected': 'Ten', 'observed': 'Eleven', 'reproduction': 'Read the API'}))
        self.invoke('feedback', '--feedback', str(feedback), context=context)
        snapshot = {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()}
        for action in ('resume', 'lookup'):
            _, restored = self.invoke(action, context=context)
            self.assertEqual(restored['task']['task_id'], a['task']['task_id'])
            self.assertIn('api', restored['task']['reviews'])
            self.assertIn('F1', restored['task']['feedback'])
            self.assertEqual(restored['test_commands_executed'], 0)
        self.assertEqual(snapshot, {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()})
        self.assertEqual(other, other_path.read_bytes())
        _, followup = self.invoke('start', '--intent', 'change', '--target', 'api', context=context)
        self.assertNotEqual(followup['task']['task_id'], a['task']['task_id'])
        self.assertIn('F1', followup['task']['feedback'])
        self.assertEqual(state_path.read_bytes(), snapshot[str(state_path)])
        _, conflict = self.invoke('feedback', '--state', b['task']['state'], '--feedback', str(feedback), context=context)
        self.assertEqual(conflict['status'], 'BLOCKED')
        self.assertIn('context_selector_conflict', str(conflict['findings']))
        record = json.loads(state_path.read_text())
        record['task_id'] = 'replacement'
        state_path.write_text(json.dumps(record))
        _, replaced = self.invoke('resume', context=context)
        self.assertEqual(replaced['status'], 'BLOCKED')
        self.assertIn('context_task_identity_changed', str(replaced['findings']))

    def test_connected_prepare_execute_lookup_and_completed_execution_resume(self, expected_label="Eleven"):
        self.project['commands']['check'] = [sys.executable, 'src/run.py', '{report_dir}/native.json']
        self.project['extensions']['workflow']['assertions'] = 'assertions.json'
        self.write('src/run.py', "import json,sys\nfrom pathlib import Path\n"
            "result=10+1\nPath(sys.argv[1]).parent.mkdir(parents=True,exist_ok=True)\n"
            "Path(sys.argv[1]).write_text(json.dumps({'checks':[{'actual':result}]}))\n"
            "p=Path('.work/calls');p.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n")
        self.project['extensions']['workflow']['features'][0]['sources'].append('src/run.py')
        self.write('.harness/project.yaml', json.dumps(self.project))
        self.write('assertions.json', json.dumps({'schema_version': 1, 'checks': [{
            'id': 'check', 'feature_id': 'api', 'expected': expected_label, 'required': True,
            'selection': {'status': 'selected', 'reason': 'Changed arithmetic'},
            'raw_observations': [{'path': '{report_dir}/native.json', 'pointer': '/checks',
                                  'assertions': [{'pointer': '/checks/0/actual', 'equals': 11}]}],
            'dependency': {'file_refs': ['src/api.py']}, 'fixture': {'file_refs': ['docs/requirement.md']}}]}))
        _, started = self.invoke('start', '--intent', 'change', '--target', 'api')
        self.assertIn('task_context', started)
        context = started['task_context']
        _, prepared = self.invoke('prepare', context=context)
        self.assertEqual(prepared['verification']['status'], 'PREPARED', prepared)
        self.assertFalse((self.root / '.work/calls').exists())
        _, executed = self.invoke('execute', '--run-check', str(ROOT / 'scripts/run_check.py'), context=context)
        self.assertEqual(executed['verification']['status'], 'PASS', executed)
        self.assertIn(expected_label, json.dumps(executed, ensure_ascii=False))
        self.assertEqual(executed['test_commands_executed'], 1)
        self.assertEqual((self.root / '.work/calls').read_text(), '1')
        self.assertEqual(executed['features'][0]['verification_status'], 'PASS')
        self.assertFalse(executed['features'][0]['reviewed'])
        before = {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()}
        _, summary = self.invoke('lookup', '--summary', context=context)
        selected = next(f for f in summary['features'] if f['id'] == 'api')
        self.assertEqual(summary['task']['task_id'], started['task']['task_id'])
        self.assertEqual(selected['criteria'], ['docs/requirement.md'])
        self.assertEqual(selected['evidence_status'], 'AVAILABLE')
        self.assertEqual(selected['check_results'][0]['current_status'], 'PASS')
        raw = selected['check_results'][0]['raw'][0]
        self.assertTrue(raw['observations_omitted'])
        self.assertGreater(raw['observation_count'], 0)
        self.assertTrue(raw['path'])
        self.assertTrue(summary['detail_command'])
        self.assertEqual(summary['detail_command']['root'], str(self.root))
        for action, extra in [('lookup', []), ('resume', []), ('execute', ['--resume'])]:
            _, result = self.invoke(action, *extra, '--run-check', str(ROOT / 'scripts/run_check.py'), context=context)
            self.assertEqual(result['test_commands_executed'], 0, result)
        self.assertEqual(before, {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()})
        _, again = self.invoke('prepare', context=context)
        self.assertEqual(again['verification']['status'], 'NOT_REQUIRED', again)
        _, followup = self.invoke('start', '--intent', 'change', '--target', 'api', context=context)
        self.assertTrue(followup['task']['results']['api'])
        _, reused = self.invoke('prepare', context=followup['task_context'])
        self.assertEqual(reused['verification']['status'], 'NOT_REQUIRED', reused)
        _, independent = self.invoke('start', '--intent', 'change', '--target', 'cli')
        self.assertEqual(independent['task']['base'], started['task']['base'])
        self.write('src/api.py', 'price = 12\n')
        stale_before = {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()}
        _, stale = self.invoke('lookup', '--summary', context=context)
        self.assertEqual(stale['features'][0]['check_results'][0]['current_status'], 'UNKNOWN')
        self.assertEqual(stale['features'][0]['check_results'][0]['current_reuse'], 'STALE')
        self.assertEqual(stale['test_commands_executed'], 0)
        self.assertEqual(stale_before, {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()})
        self.assertEqual((self.root / '.work/calls').read_text(), '1')

    def test_legacy_console_execute_and_completed_resume_preserve_unicode(self):
        with patch.dict(os.environ, {'PYTHONIOENCODING': 'cp949'}):
            self.test_connected_prepare_execute_lookup_and_completed_execution_resume(
                expected_label='Eleven \u2013 \U0001f642')

    def test_legacy_console_hook_keeps_unicode_request_and_is_read_only(self):
        self.write('.harness/project.yaml', json.dumps(self.project))
        label = 'Keep \u2013 \U0001f642'
        with patch.dict(os.environ, {'PYTHONIOENCODING': 'utf-8'}):
            _, started = self.invoke('start', '--request-summary', label)
        before = {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()}
        hook = subprocess.run([sys.executable, str(SCRIPT.with_name('workflow_context.py'))],
            input=json.dumps({'cwd': str(self.root), 'hook_event_name': 'UserPromptSubmit'}),
            capture_output=True, text=True, encoding='utf-8',
            env=dict(os.environ, PYTHONIOENCODING='cp949', AGENT_WORKFLOW_CONTEXT=started['task_context']))
        self.assertEqual(hook.returncode, 0, hook.stderr)
        detail = json.loads(json.loads(hook.stdout)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
        self.assertEqual(detail['current_task']['request']['summary'], label)
        self.assertEqual(before, {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()})

    def test_request_context_distinguishes_candidates_and_is_not_inherited(self):
        self.write('.harness/project.yaml', json.dumps(self.project))
        _, first = self.invoke('start', '--intent', 'change', '--target', 'api',
            '--request-summary', 'Keep API price stable', '--outcome-ref', 'docs/requirement.md')
        request = {'summary': 'Keep API price stable', 'outcome_refs': ['docs/requirement.md']}
        self.assertEqual(first['task']['request'], request)
        hook = subprocess.run([sys.executable, str(SCRIPT.with_name('workflow_context.py'))],
            input=json.dumps({'hook_event_name': 'UserPromptSubmit', 'cwd': str(self.root)}),
            capture_output=True, text=True, encoding='utf-8',
            env=dict(os.environ, AGENT_WORKFLOW_CONTEXT=first['task_context']))
        detail = json.loads(json.loads(hook.stdout)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
        self.assertEqual(detail['current_task']['request'], request)

        _, second = self.invoke('start', '--intent', 'change', '--target', 'api',
            '--request-summary', 'Review CLI ownership', '--outcome-ref', 'docs/map.md')
        _, ambiguous = self.invoke('resume')
        self.assertEqual(ambiguous['status'], 'BLOCKED')
        self.assertEqual({c['request']['summary'] for c in ambiguous['task_candidates']},
                         {'Keep API price stable', 'Review CLI ownership'})
        snapshot = {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()}
        _, lookup = self.invoke('lookup', context=first['task_context'])
        self.assertEqual(lookup['task']['request'], request)
        self.assertEqual(snapshot, {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()})
        _, followup = self.invoke('start', '--intent', 'change', context=first['task_context'])
        self.assertIsNone(followup['task']['request'])
        _, bad = self.invoke('start', '--request-summary', 'Missing outcome', '--outcome-ref', '../outside.md')
        self.assertEqual(bad['status'], 'BLOCKED')
        _, bad = self.invoke('lookup', '--request-summary', 'Rewrite old request', context=second['task_context'])
        self.assertEqual(bad['status'], 'BLOCKED')

    def test_long_request_hook_is_bounded_and_preserves_exact_task(self):
        runtime = self.runtime()
        self.write('.harness/project.yaml', json.dumps(self.project))
        summary = 'Long request for retained context: ' + 'x' * 6000
        for index in range(8):
            state = runtime.begin(self.root, self.project, 'change', ['api'],
                                  request_summary=summary, outcome_refs=['docs/requirement.md'])
            path = self.write(f'.work/tasks/{index}/state.json', json.dumps(state))
        snapshot = {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()}
        context = runtime.task_context(self.root, state, path)
        hook = subprocess.run([sys.executable, str(SCRIPT.with_name('workflow_context.py'))],
            input=json.dumps({'hook_event_name': 'UserPromptSubmit', 'cwd': str(self.root)}),
            capture_output=True, text=True, encoding='utf-8',
            env=dict(os.environ, AGENT_WORKFLOW_CONTEXT=context))
        detail = json.loads(hook.stdout)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1]
        self.assertLessEqual(len(detail), 5500)
        parsed = json.loads(detail)
        self.assertEqual(parsed['current_task']['task_id'], state['task_id'])
        self.assertTrue(parsed['current_task']['request']['summary'].startswith('Long request for retained context:'))
        self.assertTrue(parsed['current_task']['request']['detail_omitted'])
        self.assertEqual(snapshot, {str(p): p.read_bytes() for p in (self.root / '.work').rglob('*') if p.is_file()})
        self.assertEqual(json.loads(path.read_text())['request']['summary'], summary)

    def test_dot_inventory_roots_are_rejected_before_empty_inventory(self):
        runtime = self.runtime()
        for root in ('.', './', './src', 'src/./nested'):
            with self.subTest(root=root):
                self.project['extensions']['workflow']['roots'] = [root]
                with self.assertRaisesRegex(ValueError, 'invalid_inventory_root'):
                    runtime.inspect_project(self.root, self.project)
        self.project['extensions']['workflow']['roots'] = ['src']
        self.assertEqual([f['source_count'] for f in runtime.inspect_project(self.root, self.project)['features']], [1, 1])

    def test_connect_validates_explicit_state_before_issuing_context(self):
        self.write('.harness/project.yaml', json.dumps(self.project))
        _, started = self.invoke('start', '--intent', 'change', '--target', 'api')
        path = self.root / started['task']['state']
        record = json.loads(path.read_text())
        record['root'] = str(self.root / 'another-checkout')
        path.write_text(json.dumps(record))
        _, connected = self.invoke('connect', '--state', started['task']['state'])
        self.assertEqual(connected['status'], 'BLOCKED', connected)
        self.assertNotIn('task_context', connected)
        self.assertIn('work_target_mismatch', str(connected['findings']))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, content in {'src/api.py': 'price = 10\n', 'src/cli.py': 'print(10)\n',
                              'docs/map.md': 'API and CLI: price is ten\n',
                              'docs/requirement.md': 'price = ten\n', '.gitignore': '.work/\n'}.items():
            self.write(name, content)
        for argv in (['git', 'init', '-q'], ['git', 'add', '.'],
                     ['git', '-c', 'user.name=Fixture', '-c', 'user.email=f@invalid', 'commit', '-qm', 'base']):
            subprocess.run(argv, cwd=self.root, check=True, capture_output=True)
        self.project = {'commands': {'check': {'argv': ['python', '-m', 'unittest']}},
                        'extensions': {'workflow': {'roots': ['src'], 'features': [
                            {'id': 'api', 'partition': 'service', 'sources': ['src/api.py'],
                             'map': ['docs/map.md'], 'criteria': ['docs/requirement.md'], 'checks': ['check']},
                            {'id': 'cli', 'partition': 'operator', 'sources': ['src/cli.py'],
                             'map': ['docs/map.md'], 'criteria': ['docs/requirement.md'], 'checks': []}
                        ]}}}

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def runtime(self):
        self.assertTrue(SCRIPT.exists(), 'Missing executable workflow obligation owner')
        spec = importlib.util.spec_from_file_location('project_workflow', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def review(self, runtime, state, feature):
        current = runtime.inspect_project(self.root, self.project, state)
        item = next(item for item in current['features'] if item['id'] == feature)
        return runtime.record_review(self.root, self.project, state, {
            'feature': feature, 'basis': item['basis'],
            'analysis': 'Compared entrypoint, requirement, ownership and missing automatic coverage.',
            'references': ['docs/map.md', 'src/' + feature + '.py'], 'findings': []})

    def test_full_init_partitions_resume_and_unlinked_feature(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'PARTIAL')
        state = self.review(runtime, state, 'api')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['partitions']['operator'], 'PARTIAL')
        state = json.loads(json.dumps(state))
        state = self.review(runtime, state, 'cli')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(result['status'], 'READY_FOR_REVIEW', result)
        self.assertEqual(result['unlinked'], ['cli'])
        self.assertEqual(result['enforcement'], 'BLOCKED')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state), result)

    def test_task_matrix_requires_explicit_scope_and_does_not_expand_shared_check(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['coverage'] = [
            {'id': 'price', 'requirement': 'docs/requirement.md', 'outcome': 'Price ten',
             'perspectives': ['business'], 'areas': ['BE/API', 'Domain'], 'kind': 'test', 'check': 'check'},
            {'id': 'owner', 'requirement': 'docs/requirement.md', 'outcome': 'Single state owner',
             'perspectives': ['architecture'], 'areas': ['Domain'], 'kind': 'review'},
            {'id': 'display', 'requirement': 'docs/requirement.md', 'outcome': 'Visible price',
             'perspectives': ['business'], 'areas': ['FE'], 'kind': 'test'}]
        state = runtime.begin(self.root, self.project, 'change')
        self.write('src/api.py', 'price = 10\n# changed\n')
        basis = runtime.inspect_project(self.root, self.project, state)['features'][0]['basis']
        review = {'feature': 'api', 'basis': basis, 'analysis': 'Mapping is current; ownership review remains.',
                  'references': ['src/api.py'], 'findings': [], 'bundle': '.work/native.json',
                  'scope_reviews': {
                      'business:Domain': {'status': 'REQUIRED', 'analysis': 'Price rule changed',
                                          'references': ['src/api.py'], 'coverage': ['price']},
                      'business:FE': {'status': 'REQUIRED', 'analysis': 'Display needs a check',
                                      'references': ['src/api.py'], 'coverage': ['display']},
                      'architecture:Domain': {'status': 'REQUIRED', 'analysis': 'Owner changed',
                                              'references': ['src/api.py'], 'coverage': ['owner']},
                      'architecture:FE': {'status': 'NOT_REQUIRED', 'analysis': 'No UI owner change',
                                          'reason': 'API-only implementation', 'references': ['src/api.py']}}}
        try:
            state = runtime.record_review(self.root, self.project, state, review)
        except ValueError as error:
            self.fail(f'Existing review cannot record task scope decisions: {error}')
        item = {'feature': 'api', 'id': 'check', 'historical_status': 'PASS', 'current_status': 'PASS',
                'current_reuse': 'REUSABLE', 'selected': True, 'reasons': [], 'run_id': 'run',
                'capture': {'argv': ['native'], 'cwd': str(self.root)}, 'raw': [],
                'selection': {'status': 'selected', 'reason': 'price rule changed'}}
        result = runtime.inspect_project(self.root, self.project, state,
            evidence_resolver=lambda *_: {'status': 'PASS', 'findings': [], 'items': [item]})
        matrix = {c['perspective'] + ':' + c['area']: c for c in result['coverage']['matrix'] if c['feature'] == 'api'}
        self.assertEqual(matrix['business:Domain']['status'], 'PASS')
        self.assertEqual(matrix['business:BE/API']['status'], 'UNDECIDED')
        self.assertEqual(matrix['business:FE']['status'], 'MISSING')
        self.assertEqual(matrix['architecture:Domain']['status'], 'NOT_RUN')
        self.assertEqual(matrix['architecture:FE']['status'], 'NOT_REQUIRED')
        self.assertEqual(result['features'][0]['verification_status'], 'PASS')
        self.assertEqual(result['coverage']['status'], 'PARTIAL')
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['coverage']['rows'][0]['evidence']['run_id'], 'run')

    def test_registered_pass_without_scope_decisions_is_not_full_scope_complete(self):
        runtime = self.runtime()
        rows = [{'feature': 'api', 'id': 'price', 'status': 'PASS',
                 'perspectives': ['business'], 'areas': ['Domain']}]
        summary = runtime.coverage_summary(rows)
        self.assertIn('registered_status', summary, 'Registered coverage must be distinguished from scope discovery')
        self.assertEqual(summary['registered_status'], 'COMPLETE')
        self.assertNotEqual(summary['status'], 'COMPLETE')

    def test_omitted_matching_requirement_cannot_complete_scope(self):
        runtime = self.runtime()
        rows = [dict(feature='api', id=name, status=status, perspectives=['architecture'], areas=['Domain'])
                for name, status in [('one', 'PASS'), ('two', 'NOT_RUN')]]
        scopes = {p + ':' + a: {'status': 'NOT_REQUIRED', 'reason': 'Outside this task'}
                  for p in ('business', 'architecture') for a in ('FE', 'BE/API', 'Domain')}
        scopes['architecture:Domain'] = {'status': 'REQUIRED', 'coverage': ['one']}
        matrix = runtime.scope_matrix({'id': 'api'}, {'basis': 'basis', 'scope_reviews': scopes}, 'basis', rows)
        self.assertNotEqual(runtime.coverage_summary(rows, matrix)['status'], 'COMPLETE')

    def test_all_check_exclusions_do_not_become_test_pass(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['coverage'] = [dict(id='unused', requirement='docs/requirement.md', outcome='Other case',
                                    perspectives=['business'], areas=['Domain'], kind='test', check='check')]
        state = runtime.begin(self.root, self.project, 'change', ['api'])
        basis = runtime.inspect_project(self.root, self.project, state)['features'][0]['basis']
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'api', 'basis': basis, 'analysis': 'No product behavior changed', 'references': ['src/api.py'], 'findings': [],
            'scope_reviews': {'unused': {'status': 'NOT_REQUIRED', 'reason': 'No impact on this behavior',
                                        'analysis': 'Inspected unchanged path', 'references': ['src/api.py']}}})
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['features'][0]['verification_status'], 'NOT_REQUIRED')

    def test_architecture_needs_flow_boundary_and_owner_resolution_evidence(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['coverage'] = [{'id': 'owner', 'requirement': 'docs/requirement.md', 'outcome': 'One owner',
                                'perspectives': ['architecture'], 'areas': ['Domain'], 'kind': 'review'}]
        state = runtime.begin(self.root, self.project, 'change')
        basis = runtime.inspect_project(self.root, self.project, state)['features'][0]['basis']
        review = {'feature': 'api', 'basis': basis, 'analysis': 'Reviewed ownership', 'references': ['src/api.py'],
                  'findings': [], 'scope_reviews': {'owner': {'status': 'PASS', 'analysis': 'Looks fine',
                                                          'references': ['src/api.py']}}}
        with self.assertRaisesRegex(ValueError, 'architecture_evidence'):
            runtime.record_review(self.root, self.project, state, review)
        scope = review['scope_reviews']['owner']
        scope['architecture'] = {
            'flows': [{'owner': 'src/api.py', 'call': 'CLI -> API price', 'state': 'API owns price',
                       'data': 'price read -> result', 'references': ['src/api.py', 'src/cli.py']}],
            'boundaries': [{'kind': kind, 'analysis': 'Unchanged in this task', 'references': ['src/api.py']}
                           for kind in ('contract', 'dependency', 'failure')],
            'findings': [{'id': 'duplicate-owner', 'problem': 'CLI stores a copy', 'status': 'open',
                          'owner': 'src/cli.py', 'references': ['src/cli.py']}]}
        state = runtime.record_review(self.root, self.project, state, review)
        current = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(current['coverage']['rows'][0]['status'], 'ISSUES')
        followup = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=state)
        self.assertEqual(followup['reviews']['api'].get('scope_reviews', {}), {})
        self.assertTrue(any(f.get('id') == 'duplicate-owner' for f in
            runtime.inspect_project(self.root, self.project, followup)['product_findings']))
        with self.assertRaisesRegex(ValueError, 'unresolved_architecture_finding'):
            runtime.record_review(self.root, self.project, followup, dict(review, scope_reviews={}))
        changed = json.loads(json.dumps(followup['reviews']['api']))
        changed['inherited_architecture_findings'][0]['status'] = 'fixed'
        with self.assertRaisesRegex(ValueError, 'inherited_architecture_findings'):
            runtime.record_review(self.root, self.project, followup, changed)


        open_state = state
        self.assertEqual(current['coverage']['rows'][0]['evidence']['architecture']['findings'][0]['owner'], 'src/cli.py')
        finding = scope['architecture']['findings'].pop()
        with self.assertRaisesRegex(ValueError, 'unresolved_architecture_finding'):
            runtime.record_review(self.root, self.project, state, review)
        scope['architecture']['findings'].append(finding)
        scope['architecture']['findings'][0].update(status='excluded', reason='CLI copy is an immutable display snapshot')
        state = runtime.record_review(self.root, self.project, state, review)
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['coverage']['rows'][0]['status'], 'PASS')
        feature['coverage'] = []
        basis = runtime.inspect_project(self.root, self.project, open_state)['features'][0]['basis']
        with self.assertRaisesRegex(ValueError, 'unresolved_architecture_finding'):
            runtime.record_review(self.root, self.project, open_state, dict(review, basis=basis, scope_reviews={}))
        finding['status'] = 'open'
        carried = runtime.record_review(self.root, self.project, open_state, dict(review, basis=basis))
        audited = runtime.inspect_project(self.root, self.project, carried)
        self.assertEqual(audited['status'], 'PARTIAL')
        self.assertTrue(any(p.get('owner') == 'src/cli.py' for p in audited['product_findings']))
        self.project['extensions']['workflow']['features'].remove(feature)
        retired = runtime.inspect_project(self.root, self.project, carried)
        self.assertTrue(any(p.get('owner') == 'src/cli.py' for p in retired['product_findings']))
        basis = retired['retired'][0]['basis']
        with self.assertRaisesRegex(ValueError, 'unresolved_architecture_finding'):
            runtime.record_review(self.root, self.project, carried, dict(review, basis=basis, scope_reviews={}))
        reconciled = runtime.record_review(self.root, self.project, carried, dict(review, basis=basis))
        retained = json.dumps(reconciled, sort_keys=True)
        self.assertTrue(any(p.get('owner') == 'src/cli.py' for p in
                            runtime.inspect_project(self.root, self.project, reconciled)['product_findings']))
        self.assertEqual(json.dumps(reconciled, sort_keys=True), retained, 'Retirement audit is read-only')

    def test_changed_review_reference_only_stales_its_scope(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['coverage'] = [dict(id=name, requirement='docs/requirement.md', outcome='Expected rule',
                                    perspectives=['business'], areas=['Domain'], kind='review') for name in ('one', 'two')]
        self.write('docs/one.md', 'one\n')
        self.write('docs/two.md', 'two\n')
        state = runtime.begin(self.root, self.project, 'change')
        basis = runtime.inspect_project(self.root, self.project, state)['features'][0]['basis']
        review = {'feature': 'api', 'basis': basis, 'analysis': 'Rules reviewed separately', 'references': ['src/api.py'],
                  'findings': [], 'scope_reviews': {name: {'status': 'PASS', 'analysis': 'Rule checked',
                                                         'references': ['docs/' + name + '.md']} for name in ('one', 'two')}}
        state = runtime.record_review(self.root, self.project, state, review)
        self.write('docs/one.md', 'one changed\n')
        rows = runtime.inspect_project(self.root, self.project, state)['coverage']['rows']
        self.assertEqual([r['status'] for r in rows], ['STALE', 'PASS'])

    def test_scope_axes_review_exclusion_failure_and_stale_remain_distinct(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['coverage'] = [
            {'id': 'ownership', 'requirement': 'docs/requirement.md', 'outcome': 'Single state owner',
             'perspectives': ['architecture'], 'areas': ['BE/API', 'Domain'], 'kind': 'review'},
            {'id': 'price', 'requirement': 'docs/requirement.md', 'outcome': 'Expected price',
             'perspectives': ['business'], 'areas': ['Domain'], 'kind': 'test', 'check': 'check'}]
        state = self.review(runtime, runtime.begin(self.root, self.project, 'init'), 'api')
        basis = state['reviews']['api']['basis']
        review = dict(state['reviews']['api'], scope_reviews={'ownership': {
            'status': 'NOT_REQUIRED', 'reason': 'No state ownership change',
            'analysis': 'Only presentation changed', 'references': ['src/api.py']}})
        state = runtime.record_review(self.root, self.project, state, review)
        test = {'feature': 'api', 'id': 'check', 'historical_status': 'ISSUES', 'current_status': 'ISSUES',
                'current_reuse': 'REUSABLE', 'selected': True, 'reasons': ['assertion_failed'],
                'run_id': 'run', 'capture': {}, 'raw': [], 'selection': {'status': 'selected', 'reason': 'price changed'}}
        rows = runtime.coverage_rows(feature, state['reviews']['api'], basis, [test])
        self.assertEqual([row['status'] for row in rows], ['NOT_REQUIRED', 'ISSUES'])
        test.update(selected=False, current_status='NOT_REQUIRED')
        self.assertEqual(runtime.coverage_rows(feature, review, basis, [test])[1]['status'], 'NOT_REQUIRED')
        rows = runtime.coverage_rows(feature, review, basis, current_basis='changed')
        self.assertEqual(rows[0]['status'], 'STALE')
        self.assertEqual(runtime.coverage_summary(rows)['areas']['Domain'], {'NOT_RUN': 1, 'STALE': 1})
        state['reviews']['api']['scope_reviews']['ownership'] = {'status': 'PASS'}
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['coverage']['rows'][0]['status'], 'BLOCKED')
        feature['coverage'][0]['areas'] = ['e2e']
        with self.assertRaisesRegex(ValueError, 'coverage_axis'):
            runtime.configuration(self.project)

    def test_feedback_requires_owner_repair_and_bound_failure_normal_evidence(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        feedback = {'id': 'wrong-price', 'feature': 'api', 'observed': 'Price is eleven',
                    'expected': 'Price is ten', 'reproduction': 'Read price from API'}
        state = runtime.record_feedback(self.root, self.project, state, feedback)
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(result['feedback'][0]['status'], 'OPEN')
        self.assertIn('root_cause', result['feedback'][0]['remaining'])
        # Explanation/guide edits cannot discharge the owner repair.
        complete = dict(feedback, trace='api.py -> price', root_cause='Wrong shared constant',
                        failed_prevention='No boundary assertion', repair_paths=['src/api.py'],
                        guardrail={'failure': 'wrong price', 'scope': 'api', 'check': 'check',
                                   'normal_exception': 'zero remains valid', 'reconsider': 'price contract changes',
                                   'regression_pointer': '$.price', 'normal_pointer': '$.zero'},
                        red_bundle='.work/red.json', green_bundle='.work/green.json')
        state = runtime.record_feedback(self.root, self.project, state, complete)
        self.write('docs/map.md', 'Warning: keep price ten\n')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertIn('owner_repair_not_observed', result['feedback'][0]['remaining'])
        self.write('src/api.py', 'price = 10\n# reject invalid input centrally\n')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertNotIn('owner_repair_not_observed', result['feedback'][0]['remaining'])
        self.assertIn('active_prevention_link_missing', result['feedback'][0]['remaining'])
        self.project['extensions']['workflow']['state'] = '.work/current.json'
        self.write('.work/current.json', json.dumps(state))
        subsequent = runtime.begin_work(self.root, self.project)
        self.assertEqual(subsequent['feedback'], state['feedback'])
        # Updating a stage cannot silently drop the original complaint.
        updated = runtime.record_feedback(self.root, self.project, subsequent,
                                          {'id': 'wrong-price', 'feature': 'api', 'trace': 'new caller -> api.py'})
        self.assertEqual(updated['feedback']['wrong-price']['expected'], feedback['expected'])

    def test_shared_ui_owners_reopen_consumers_and_retain_intentional_exceptions(self):
        runtime = self.runtime()
        config = self.project['extensions']['workflow']
        self.write('src/tokens.css', ':root { --space: 1rem; }\n')
        self.write('src/shared.py', 'button = "shared"\n')
        self.write('docs/ui.md', 'Calm layout; code owns spacing. Include keyboard and narrow states.\n')
        config['ui_systems'] = {'shared': {'guide': 'docs/ui.md', 'tokens': ['src/tokens.css'],
            'components': ['src/shared.py'], 'consumers': ['api', 'cli'],
            'exceptions': [{'feature': 'cli', 'reason': 'Terminal flow has no pointer states',
                            'reference': 'docs/ui.md', 'reconsider': 'GUI is introduced'}]}}
        state = runtime.begin(self.root, self.project, 'change')
        for name in ('api', 'cli'):
            state = self.review(runtime, state, name)
        initial = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(initial['unmapped'], [])
        self.assertEqual(initial['ui_systems'][0]['exceptions'][0]['feature'], 'cli')
        self.write('src/tokens.css', ':root { --space: 2rem; }\n')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual([item['target'] for item in result['obligations']], ['api', 'cli'])
        for obligation in result['obligations']:
            self.assertIn('ui_review', obligation['requires'])
            self.assertIn('verification', obligation['requires'])
            self.assertIn('src/tokens.css', obligation['changed'])
        (self.root / 'docs/ui.md').unlink()
        self.assertIn('missing_ui_guide:shared:docs/ui.md', runtime.inspect_project(self.root, self.project, state)['findings'])
        config['features'].pop()
        self.assertIn('removed_ui_consumer:shared:cli', runtime.inspect_project(self.root, self.project, state)['findings'])

    def test_check_removal_retains_missing_detection_preservation_obligation(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['prevention'] = [{'failure': 'Wrong price', 'scope': 'Pricing', 'check': 'check',
                                  'normal_exception': 'Zero valid', 'reconsider': 'Contract changes'}]
        state = runtime.begin(self.root, self.project, 'maintain')
        feature['checks'] = []
        feature['prevention'] = []
        state = self.review(runtime, state, 'api')
        result = runtime.inspect_project(self.root, self.project, state)
        retired = result['check_retirements'][0]
        self.assertEqual(retired['check'], 'check')
        self.assertEqual(retired['status'], 'BLOCKED')
        self.assertIn('preservation_decision_missing', retired['remaining'])
        self.assertIn('check_preservation', next(o for o in result['obligations'] if o['target'] == 'api')['requires'])
        maintenance = runtime.maintenance_summary(self.root, self.project, state)
        self.assertEqual(maintenance['checks'][0]['disposition'], 'retain')
        self.assertIn('No current detection-preservation evidence', maintenance['checks'][0]['retain_reason'])
        self.project['extensions']['workflow']['state'] = '.work/current.json'
        self.write('.work/current.json', json.dumps(state))
        later = runtime.begin(self.root, self.project, 'change')
        self.assertEqual(runtime.inspect_project(self.root, self.project, later)['check_retirements'][0]['status'], 'BLOCKED')

    def test_change_reopens_only_affected_and_typo_does_not(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        self.write('docs/notes.md', 'typo repair\n')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['obligations'], [])
        self.write('src/api.py', 'price = 11\n')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual([o['target'] for o in result['obligations']], ['api'])
        self.assertIn('verification', result['obligations'][0]['requires'])
        self.assertEqual(result['partitions']['operator'], 'READY_FOR_REVIEW')

    def test_host_inputs_bypass_git_and_editable_evidence_without_skipping_reviews(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'change')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        self.write('src/api.py', 'price = 11\n')
        state = self.review(runtime, state, 'api')
        files = runtime.inventory(self.root, ['src'])
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'PARTIAL')
        calls = []

        def resolve(root, feature, commands):
            calls.append(feature['id'])
            self.assertEqual(root, self.root.resolve())
            self.assertEqual(feature['checks'], ['check'])
            self.assertEqual(commands, self.project['commands'])
            return {'status': 'PASS', 'findings': []}

        with patch.object(runtime, 'git', side_effect=AssertionError('Git must not run')), \
                patch.object(runtime, 'inspect_evidence', side_effect=AssertionError('Editable evidence must not load')):
            result = runtime.inspect_project(self.root, self.project, state,
                                             file_inventory=files, evidence_resolver=resolve)
            self.assertEqual(result['status'], 'READY_FOR_REVIEW', result)
            self.assertEqual(calls, ['api'])
            for review in ({}, dict(state['reviews']['api'], basis='stale')):
                altered = dict(state, reviews=dict(state['reviews'], api=review))
                result = runtime.inspect_project(self.root, self.project, altered,
                                                 file_inventory=files, evidence_resolver=resolve)
                self.assertEqual(result['status'], 'PARTIAL')
                self.assertIn('map_review', result['obligations'][0]['requires'])
            self.assertEqual(calls, ['api'], 'Missing/stale semantic review must not be replaced by execution')
            blocked = runtime.inspect_project(self.root, self.project, state, file_inventory=files,
                evidence_resolver=lambda *_: {'status': 'BLOCKED', 'findings': ['host_case_missing']})
            self.assertEqual(blocked['status'], 'PARTIAL')
            self.assertIn('host_case_missing', blocked['findings'])
            empty = runtime.inspect_project(self.root, self.project, state,
                                            file_inventory={}, evidence_resolver=resolve)
            self.assertEqual(empty['status'], 'PARTIAL')
            self.assertIn('missing_source:api:src/api.py', empty['findings'])

    def test_map_readiness_is_separate_from_retained_product_gaps(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        review = dict(state['reviews']['api'], product_findings=['Representative output quality is unverified.'])
        state = runtime.record_review(self.root, self.project, state, review)
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(result.get('mapping_status'), 'READY_FOR_REVIEW', result)
        self.assertEqual(result['status'], 'PARTIAL', 'Product gap must remain visible to close')
        self.assertEqual(result['product_findings'], [
            {'feature': 'api', 'finding': 'Representative output quality is unverified.'}])
        # A source repair can complete the map review without discharging execution.
        self.write('src/api.py', 'price = 11\n')
        state = self.review(runtime, state, 'api')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(result['mapping_status'], 'READY_FOR_REVIEW')
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertIn('verification', result['obligations'][0]['requires'])
        # Legacy findings continue to block mapping; no automatic reclassification.
        state['reviews']['api']['findings'] = ['An entrypoint is not mapped.']
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['mapping_status'], 'PARTIAL')
        for malformed in ('hidden', [None], ['']):
            with self.assertRaisesRegex(ValueError, 'product_findings'):
                runtime.record_review(self.root, self.project, state,
                    dict(state['reviews']['api'], product_findings=malformed))

    def test_declared_document_edit_needs_review_without_product_execution(self):
        runtime = self.runtime()
        config = self.project['extensions']['workflow']
        config['roots'].append('docs')
        feature = config['features'][0]
        feature['sources'].append('docs/*')
        feature['documentation_only'] = {'docs/map.md': 'Descriptive map; no runtime or generator consumes it.'}
        state = runtime.begin(self.root, self.project, 'change')
        for name in ('api', 'cli'):
            state = self.review(runtime, state, name)
        self.write('docs/map.md', 'API and CLI both return ten; clarified references.\n')
        pending = runtime.inspect_project(self.root, self.project, state)
        obligation = next(o for o in pending['obligations'] if o['target'] == 'api')
        self.assertEqual(obligation['changed'], ['docs/map.md'])
        self.assertNotIn('verification', obligation['requires'])
        for name in ('api', 'cli'):
            state = self.review(runtime, state, name)
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'READY_FOR_REVIEW')
        # A mixed change and an exemption added after start cannot hide execution.
        self.write('src/api.py', 'price = 11\n')
        feature['documentation_only']['src/api.py'] = 'Incorrect reclassification after start'
        state = self.review(runtime, state, 'api')
        pending = runtime.inspect_project(self.root, self.project, state)
        self.assertIn('verification', pending['obligations'][0]['requires'])
        self.assertEqual(pending['obligations'][0]['verification_changed'], ['src/api.py'])
        legacy = dict(state)
        legacy.pop('documentation_only')
        self.assertIn('docs/map.md', runtime.inspect_project(self.root, self.project, legacy)['obligations'][0]['verification_changed'])
        # Removal is not a prose-only edit, even for an explicitly declared document.
        (self.root / 'docs/map.md').unlink()
        pending = runtime.inspect_project(self.root, self.project, state)
        self.assertIn('docs/map.md', pending['obligations'][0]['verification_changed'])
        feature['documentation_only'] = {'docs/*': 'Broad exemption'}
        with self.assertRaisesRegex(ValueError, 'documentation_only'):
            runtime.begin(self.root, self.project, 'change')

    def test_new_deleted_duplicate_and_stale_review_cannot_disappear(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        basis = runtime.inspect_project(self.root, self.project, state)['features'][0]['basis']
        self.write('src/new.py', 'worker = True\n')
        self.assertIn('src/new.py', runtime.inspect_project(self.root, self.project, state)['unmapped'])
        self.write('src/api.py', 'price = 12\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            runtime.record_review(self.root, self.project, state, {'feature': 'api', 'basis': basis,
                'analysis': 'review', 'references': ['src/api.py'], 'findings': []})
        (self.root / 'src/cli.py').unlink()
        self.assertTrue(any('missing_source' in f for f in runtime.inspect_project(self.root, self.project, state)['findings']))
        self.project['extensions']['workflow']['features'].append(self.project['extensions']['workflow']['features'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            runtime.inspect_project(self.root, self.project, state)

    def test_shared_criteria_and_command_drift_reopens_consumers(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        self.project['commands']['check']['argv'].append('specific')
        state = self.review(runtime, state, 'api')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual([o['target'] for o in result['obligations']], ['api'])
        self.assertIn('verification', result['obligations'][0]['requires'])
        self.write('docs/requirement.md', 'price = twenty\n')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        self.assertEqual(len(runtime.inspect_project(self.root, self.project, state)['obligations']), 2)

    def test_ui_standard_change_and_legacy_reference_drift_keep_verification(self):
        runtime = self.runtime()
        self.write('docs/ui.md', 'Use the shared spacing tokens.')
        self.project['extensions']['workflow']['features'][0]['ui'] = ['docs/ui.md']
        state = runtime.begin(self.root, self.project, 'change')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['obligations'], [])
        self.write('docs/ui.md', 'Use shared spacing tokens and visible keyboard focus.')
        state = self.review(runtime, state, 'api')
        pending = runtime.inspect_project(self.root, self.project, state)['obligations']
        self.assertEqual([item['target'] for item in pending], ['api'])
        self.assertIn('verification', pending[0]['requires'])
        del state['verification_bases']  # Previously persisted work must not lose the obligation.
        self.assertIn('verification', runtime.inspect_project(self.root, self.project, state)['obligations'][0]['requires'])

    def test_staged_source_deletion_cannot_close_with_only_a_new_review(self):
        runtime = self.runtime()
        self.project['extensions']['workflow']['features'][0]['sources'] = ['src/*']
        state = runtime.begin(self.root, self.project, 'change')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        subprocess.run(['git', 'rm', 'src/api.py'], cwd=self.root, check=True, capture_output=True)
        # Updating the map to the remaining implementation must not erase ownership.
        self.project['extensions']['workflow']['features'][0]['sources'] = ['src/cli.py']
        current = runtime.inspect_project(self.root, self.project, state)
        item = next(item for item in current['features'] if item['id'] == 'api')
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'api', 'basis': item['basis'],
            'analysis': 'The removed API entrypoint is now provided by the remaining CLI.',
            'references': ['docs/map.md', 'src/cli.py'], 'findings': []})
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(result['status'], 'PARTIAL', result)
        pending = next(o for o in result['obligations'] if o['target'] == 'api')
        self.assertEqual(pending['changed'], ['src/api.py'])
        self.assertIn('verification', pending['requires'])
        self.assertEqual(result['partitions']['operator'], 'READY_FOR_REVIEW')
        legacy = dict(state)
        legacy.pop('source_patterns')
        resumed = runtime.inspect_project(self.root, self.project, legacy)
        self.assertEqual(resumed['status'], 'PARTIAL')
        self.assertIn('baseline_source_ownership_unavailable:src/api.py', resumed['findings'])

    def test_non_harness_and_readonly_audit(self):
        runtime = self.runtime()
        self.assertEqual(runtime.inspect_project(self.root, {}, None)['status'], 'NOT_CONFIGURED')
        before = sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*'))
        runtime.inspect_project(self.root, self.project, None)
        self.assertEqual(before, sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob('*')))

    def test_minimal_forged_review_does_not_discharge_semantic_obligations(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        current = runtime.inspect_project(self.root, self.project, state)
        state['reviews'] = {item['id']: {'basis': item['basis'], 'findings': []}
                            for item in current['features']}
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'PARTIAL')

    def test_feedback_ui_survive_resume_and_cannot_close_with_pass_flag(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['ui'] = ['docs/map.md']
        feature['prevention'] = [{'failure': 'negative price', 'check': 'check',
                                  'normal_exception': 'zero is allowed'}]
        state = runtime.begin(self.root, self.project, 'feedback', targets=['api'])
        state['status'] = 'PASS'
        obligation = runtime.inspect_project(self.root, self.project, state)['obligations'][0]
        self.assertTrue({'repair', 'regression', 'normal_case', 'ui_review'} <= set(obligation['requires']))
        state = self.review(runtime, state, 'api')
        remaining = runtime.inspect_project(self.root, self.project, state)['obligations']
        self.assertTrue(any(o['target'] == 'api' and 'regression' in o['requires'] for o in remaining))

    def test_core_maintenance_detects_obligation_without_optional_cli(self):
        from tests.harness.test_core_first_cli_maintain import load_core, project_config
        runtime = self.runtime()
        project = project_config()
        project['extensions'] = self.project['extensions']
        result = load_core().maintain_harness(self.root, project)
        self.assertIn('MAINT-WORKFLOW', result['checks'])
        self.assertTrue(any(f['rule_id'] == 'MAINT-WORKFLOW' for f in result['findings']))

    def test_harness_start_owns_baseline_and_close_cannot_skip_task_obligations(self):
        from tests.harness.test_core_first_design_execution import (
            load_core, authorized_contract, project_policy, write_design_only)
        from tests.harness.test_core_first_close_lifecycle import result_payload
        core = load_core()
        project = project_policy(protected=())
        project['extensions'] = self.project['extensions']
        self.write('.harness/project.yaml', json.dumps(project))
        source = authorized_contract(core, 'W-workflow-auto')
        active, _, _ = write_design_only(self.root, core, source)
        started = core.start_work(self.root, source['work_id'], 'auto', source, project=project)
        self.assertEqual(started['status'], 'started', started)
        self.assertNotIn('workflow_baseline', started['manifest'], 'Do not dump all source hashes into Agent context')
        self.assertEqual(started['workflow']['work_id'], source['work_id'])
        self.assertIn('workflow_baseline', json.loads((active / 'work.json').read_text()))
        original = (active / 'work.json').read_bytes()
        self.write('src/api.py', 'price = 11\n')
        resumed = core.start_work(self.root, source['work_id'], 'auto', source, project=project)
        self.assertEqual(resumed['status'], 'already_started', resumed)
        self.assertEqual(original, (active / 'work.json').read_bytes())
        runtime = self.runtime()
        state, state_path = runtime.work_record(self.root, source['work_id'])
        self.assertEqual(state_path, active / 'workflow.json')
        self.assertNotEqual(state['baseline']['src/api.py'], runtime.file_hash(self.root, 'src/api.py'))
        viewed = subprocess.run([sys.executable, str(SCRIPT), 'audit', '--root', str(self.root),
                                 '--work-id', source['work_id']], capture_output=True, text=True)
        self.assertEqual(viewed.returncode, 2, viewed.stderr)
        self.assertFalse(state_path.exists(), 'Audit must not create a review record')
        basis = runtime.inspect_project(self.root, project, state)['features'][0]['basis']
        review = self.write('.work/start-review.json', json.dumps({'feature': 'api', 'basis': basis,
            'analysis': 'Reviewing the changed price owner.', 'references': ['src/api.py'], 'findings': []}))
        child = self.write('.work/interrupt-work-review.py',
            "import runpy,json,os,sys\n"
            "runtime=runpy.run_path(sys.argv[1])\n"
            "def interrupt(value, stream, **kwargs):\n"
            " stream.write('{');stream.flush();os._exit(23)\n"
            "json.dump=interrupt\n"
            "runtime['main'](sys.argv[2:])\n")
        interrupted = subprocess.run([sys.executable, str(child), str(SCRIPT), 'review',
            '--root', str(self.root), '--work-id', source['work_id'], '--review', str(review)], capture_output=True)
        self.assertEqual(interrupted.returncode, 23, interrupted.stderr)
        self.assertFalse(state_path.exists())
        self.assertEqual(original, (active / 'work.json').read_bytes())
        resumed = core.start_work(self.root, source['work_id'], 'auto', source, project=project)
        self.assertEqual(resumed['status'], 'already_started', resumed)
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        state_path.write_text(json.dumps(state))
        paths = [entry['path'] for entry in core.collect_git_baseline(self.root)['entries']]
        impact = core.select_impacted_checks(paths, project, logic_impact={
            'changed_logic': ['api.price'], 'affected_behaviors': ['price output'],
            'scope': 'local', 'reason': 'One API value changed.', 'tests': ['tests/test_price.py']})
        result = result_payload()
        result['full']['rule'] = impact['not_required_rule_ids'][0]
        closed = core.close_work(self.root, source['work_id'], contract=source,
            result=result, impact=impact, completed_at='2026-10-05T00:00:00+00:00',
            completed_days=30, trash_days=7)
        self.assertEqual(closed['status'], 'incomplete', closed)
        self.assertIn('project_workflow_incomplete', closed['errors'])
        self.assertIn('verification', closed['workflow']['obligations'][0]['requires'])
        self.assertTrue(active.is_dir())
        state['baseline']['src/api.py'] = runtime.file_hash(self.root, 'src/api.py')
        state_path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'baseline_changed'):
            runtime.work_record(self.root, source['work_id'])
        resumed = core.start_work(self.root, source['work_id'], 'auto', source, project=project)
        self.assertEqual(resumed['status'], 'conflict', resumed)

    def test_harness_begin_reuses_only_current_configured_semantic_reviews(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        self.project['extensions']['workflow']['state'] = '.work/map-review.json'
        self.write('.work/map-review.json', json.dumps(state))
        fresh = runtime.begin_work(self.root, self.project)
        self.assertEqual(set(fresh['reviews']), {'api', 'cli'})
        self.assertEqual(runtime.inspect_project(self.root, self.project, fresh)['obligations'], [])
        self.write('src/api.py', 'price = 11\n')
        fresh = runtime.begin_work(self.root, self.project)
        self.assertEqual(set(fresh['reviews']), {'cli'})

    def test_followup_preserves_map_reviews_but_requires_new_scope_decisions(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        state['reviews']['api']['scope_reviews'] = {'old-task': {
            'status': 'NOT_REQUIRED', 'reason': 'Previous request only', 'references': ['src/api.py']}}
        before = json.dumps(state, sort_keys=True)
        fresh = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=state)
        audit = runtime.inspect_project(self.root, self.project, fresh)
        self.assertEqual(set(fresh['reviews']), {'api', 'cli'})
        self.assertEqual(fresh['reviews']['api'].get('scope_reviews', {}), {})
        self.assertTrue(all(f['reviewed'] for f in audit['features']))
        self.assertFalse(any(o['target'] == 'cli' for o in audit['obligations']))
        self.assertEqual(json.dumps(state, sort_keys=True), before)

    def test_followup_keeps_stale_product_findings_until_explicit_disposition(self):
        runtime = self.runtime()
        state = self.review(runtime, runtime.begin(self.root, self.project, 'init'), 'api')
        gap = 'Output quality still needs a representative check'
        state = runtime.record_review(self.root, self.project, state,
            dict(state['reviews']['api'], product_findings=[gap]))
        self.write('src/api.py', 'price = 11\n')
        fresh = runtime.begin(self.root, self.project, 'change', ['cli'], prior_state=state)
        audit = runtime.inspect_project(self.root, self.project, fresh)
        self.assertIn({'feature': 'api', 'finding': gap}, audit['product_findings'])
        self.assertFalse(next(f for f in audit['features'] if f['id'] == 'api')['reviewed'])
        fresh = self.review(runtime, fresh, 'api')
        self.assertIn({'feature': 'api', 'finding': gap},
                      runtime.inspect_project(self.root, self.project, fresh)['product_findings'])
        fresh = runtime.record_review(self.root, self.project, fresh,
            dict(fresh['reviews']['api'], product_findings=[], analysis='Representative output inspected; gap resolved.'))
        self.assertEqual(runtime.inspect_project(self.root, self.project, fresh)['product_findings'], [])

    def test_followup_retains_removed_feature_product_findings(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        state = self.review(runtime, state, 'cli')
        gap = 'Unresolved CLI output discrepancy'
        state = runtime.record_review(self.root, self.project, state,
            dict(state['reviews']['cli'], product_findings=[gap]))
        self.project['extensions']['workflow']['features'].pop()
        audit = runtime.inspect_project(self.root, self.project, state)
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'cli', 'basis': audit['retired'][0]['basis'], 'analysis': 'CLI removed; gap remains',
            'references': ['docs/map.md'], 'findings': [], 'product_findings': [gap]})
        # A reconciliation may own the only remaining record of a retired feature.
        del state['reviews']['cli']
        fresh = runtime.begin(self.root, self.project, 'change', prior_state=state)
        self.assertIn({'feature': 'cli', 'finding': gap},
                      runtime.inspect_project(self.root, self.project, fresh)['product_findings'])

    def test_restored_feature_uses_active_findings_over_old_retirement(self):
        runtime = self.runtime()
        state = self.review(runtime, runtime.begin(self.root, self.project, 'init'), 'cli')
        feature = self.project['extensions']['workflow']['features'].pop()
        audit = runtime.inspect_project(self.root, self.project, state)
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'cli', 'basis': audit['retired'][0]['basis'], 'analysis': 'CLI retirement checked',
            'references': ['docs/map.md'], 'findings': [], 'product_findings': []})
        self.project['extensions']['workflow']['features'].append(feature)
        state = self.review(runtime, state, 'cli')
        gap = 'New issue after restoring CLI'
        state = runtime.record_review(self.root, self.project, state,
            dict(state['reviews']['cli'], product_findings=[gap]))
        state = self.review(runtime, state, 'cli')
        self.assertIn({'feature': 'cli', 'finding': gap},
                      runtime.inspect_project(self.root, self.project, state)['product_findings'])
        self.project['extensions']['workflow']['features'].pop()
        audit = runtime.inspect_project(self.root, self.project, state)
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'cli', 'basis': audit['retired'][0]['basis'], 'analysis': 'Retired again; issue still open',
            'references': ['docs/map.md'], 'findings': []})
        self.assertIn({'feature': 'cli', 'finding': gap},
                      runtime.inspect_project(self.root, self.project, state)['product_findings'])

    def test_legacy_retirement_cannot_shadow_a_new_active_finding(self):
        runtime = self.runtime()
        state = self.review(runtime, runtime.begin(self.root, self.project, 'init'), 'cli')
        self.project['extensions']['workflow']['features'].pop()
        audit = runtime.inspect_project(self.root, self.project, state)
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'cli', 'basis': audit['retired'][0]['basis'], 'analysis': 'Previous retirement complete',
            'references': ['docs/map.md'], 'findings': [], 'product_findings': []})
        # Existing releases could retain both records after remove/restore/remove.
        gap = 'New active finding missing from the older retirement'
        state['reviews']['cli']['product_findings'] = [gap]
        audit = runtime.inspect_project(self.root, self.project, state)
        self.assertIn({'feature': 'cli', 'finding': gap}, audit['product_findings'])
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'cli', 'basis': audit['retired'][0]['basis'], 'analysis': 'Reconciled mapping only',
            'references': ['docs/map.md'], 'findings': []})
        self.assertIn({'feature': 'cli', 'finding': gap},
                      runtime.inspect_project(self.root, self.project, state)['product_findings'])

    def test_private_and_outside_paths_rejected_before_read(self):
        runtime = self.runtime()
        self.project['extensions']['workflow']['features'][0]['criteria'] = ['../outside']
        with self.assertRaisesRegex(ValueError, 'outside_project'):
            runtime.inspect_project(self.root, self.project)
        self.project['extensions']['workflow']['features'][0]['criteria'] = ['.env']
        with self.assertRaisesRegex(ValueError, 'private_path'):
            runtime.inspect_project(self.root, self.project)

    def test_close_recomputes_obligations_even_with_submitted_success(self):
        from tests.harness.test_core_first_close_lifecycle import (
            load_core, started_work, close_impact, result_payload)
        core = load_core()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            active, contract = started_work(core, root, 'W-workflow')
            project, impact = close_impact(core)
            project['extensions'] = self.project['extensions']
            submitted = result_payload()
            submitted['full']['rule'] = impact['not_required_rule_ids'][0]
            result = core.close_work(root, 'W-workflow', contract=contract,
                result=submitted, impact=impact, project=project,
                completed_at='2026-10-05T00:00:00+00:00', completed_days=30, trash_days=7)
            self.assertEqual(result['status'], 'incomplete', result)
            self.assertIn('project_workflow_incomplete', result.get('errors', []))
            self.assertTrue(active.is_dir())

    def test_changed_work_requires_bound_real_execution_and_rejects_stale_raw(self, criteria_only=False):
        runtime = self.runtime()
        import runpy
        viewer = runpy.run_path(str(SCRIPT.with_name('verification_results.py')))
        command = [sys.executable, '-c', "import json,runpy; from pathlib import Path; Path('.work/raw.json').write_text(json.dumps({'cases':[runpy.run_path('src/api.py')['price']], 'skipped':0}))"]
        self.project['commands']['check']['argv'] = command
        if criteria_only:
            self.project['extensions']['workflow']['features'][1]['criteria'] = ['docs/map.md']
        state = runtime.begin(self.root, self.project, 'change')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        if criteria_only:
            self.write('docs/requirement.md', 'Read back exactly ten with no skipped cases.\n')
        else:
            self.write('src/api.py', 'price = 11\n')
        state = self.review(runtime, state, 'api')
        self.assertTrue(runtime.inspect_project(self.root, self.project, state)['obligations'])
        plan = {'schema_version': 1, 'plan_id': 'actual-price', 'checks': [{
            'id': 'check', 'feature_id': 'api', 'expected': 'new price read from implementation',
            'criteria_revision': 'price-eleven', 'required': True,
            'selection': {'status': 'selected', 'reason': 'price source changed'},
            'conditions': {'source': viewer['_git_snapshot'](self.root),
                           'criteria': {'revision': 'price-eleven'},
                           'command': {'argv': command, 'cwd': str(self.root)},
                           'dependency': {'file_refs': ['docs/requirement.md']},
                           'fixture': {'file_refs': ['src/api.py']},
                           'runtime': {'python': sys.version}},
            'raw_observations': [{'path': '.work/raw.json', 'pointer': '$', 'assertions': [
                {'pointer': '/cases', 'min_count': 1}, {'pointer': '/cases/0', 'equals': 10 if criteria_only else 11},
                {'pointer': '/skipped', 'equals': 0}]}]}]}
        path = self.write('.work/plan.json', json.dumps(plan))
        outcome = viewer['execute_plan'](path, run_check_path=ROOT / 'scripts/run_check.py', evidence_dir=self.root / '.work/run')
        self.assertEqual(outcome['status'], 'PASS', outcome)
        bundle = self.write('.work/bundle.json', json.dumps(outcome['execution']['bundle']))
        state['reviews']['api']['bundle'] = bundle.relative_to(self.root).as_posix()
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'READY_FOR_REVIEW')
        self.write('.work/raw.json', '{"cases": [999], "skipped": 0}')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'PARTIAL')

    def test_criteria_only_change_requires_and_accepts_actual_current_execution(self):
        self.test_changed_work_requires_bound_real_execution_and_rejects_stale_raw(criteria_only=True)


    def test_ui_request_cannot_omit_standards_or_behavior_evidence(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'ui', ['api'])
        state = self.review(runtime, state, 'api')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertIn('missing_ui_standard:api', result['findings'])
        self.write('docs/ui.md', 'Shared layout and intentional narrow-screen stacking.')
        self.project['extensions']['workflow']['features'][0]['ui'] = ['docs/ui.md']
        state = self.review(runtime, state, 'api')
        result = runtime.inspect_project(self.root, self.project, state)
        pending = next(item for item in result['obligations'] if item['target'] == 'api')
        self.assertIn('ui_review', pending['requires'])
        self.assertIn('verification', pending['requires'])

    def test_targetless_requests_and_source_changes_during_init_keep_obligations(self):
        runtime = self.runtime()
        for intent in ('feedback', 'ui'):
            with self.assertRaisesRegex(ValueError, 'target_required'):
                runtime.begin(self.root, self.project, intent)
        state = runtime.begin(self.root, self.project, 'init')
        self.write('src/api.py', 'price = 22\n')
        state = self.review(runtime, state, 'api')
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertIn('verification', next(o for o in result['obligations'] if o['target'] == 'api')['requires'])

    def test_removed_feature_requires_explicit_reconciliation_and_can_resume(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        self.project['extensions']['workflow']['features'].pop()
        subprocess.run(['git', 'rm', 'src/cli.py'], cwd=self.root, check=True, capture_output=True)
        state = self.review(runtime, state, 'api')
        audit = runtime.inspect_project(self.root, self.project, state)
        retired = next(o for o in audit['obligations'] if o['target'] == 'cli')
        self.assertIn('removal_review', retired['requires'])
        state = runtime.record_review(self.root, self.project, state, {
            'feature': 'cli', 'basis': retired['basis'],
            'analysis': 'CLI was retired; API still owns the remaining requirement and command.',
            'references': ['docs/map.md', 'docs/requirement.md'], 'findings': []})
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'READY_FOR_REVIEW')

    def test_retirement_keeps_product_findings_until_current_reconciliation(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        state = self.review(runtime, state, 'cli')
        gap = 'Existing CLI callers still depend on the removed price endpoint.'
        state = runtime.record_review(self.root, self.project, state,
            dict(state['reviews']['cli'], product_findings=[gap]))
        self.project['extensions']['workflow']['features'].pop()
        subprocess.run(['git', 'rm', 'src/cli.py'], cwd=self.root, check=True, capture_output=True)
        state = self.review(runtime, state, 'api')
        audit = runtime.inspect_project(self.root, self.project, state)
        self.assertIn({'feature': 'cli', 'finding': gap}, audit['product_findings'])
        retired = next(item for item in audit['retired'] if item['id'] == 'cli')
        review = {'feature': 'cli', 'basis': retired['basis'],
            'analysis': 'Removal mapped, but the remaining caller migration is unresolved.',
            'references': ['docs/map.md'], 'findings': [], 'product_findings': [gap]}
        state = runtime.record_review(self.root, self.project, state, review)
        state = json.loads(json.dumps(state))
        audit = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(audit['mapping_status'], 'READY_FOR_REVIEW', audit)
        self.assertEqual(audit['status'], 'PARTIAL', audit)
        self.assertIn('product_resolution', audit['obligations'][0]['requires'])
        self.assertIn({'feature': 'cli', 'finding': gap}, audit['product_findings'])
        omitted = dict(review)
        omitted.pop('product_findings')
        omission = runtime.record_review(self.root, self.project, state, omitted)
        self.assertEqual(runtime.inspect_project(self.root, self.project, omission)['status'], 'PARTIAL')
        resolved = runtime.record_review(self.root, self.project, state,
            dict(review, analysis='Confirmed callers use the retained API.', product_findings=[]))
        self.assertEqual(runtime.inspect_project(self.root, self.project, resolved)['status'], 'READY_FOR_REVIEW')
        for malformed in (None, {'product_findings': {'wrong': 'shape'}}):
            invalid = json.loads(json.dumps(resolved))
            invalid['retired_reviews']['cli'] = malformed
            with self.assertRaises(ValueError):
                runtime.inspect_project(self.root, self.project, invalid)
        # A stale reconciliation cannot erase the original unresolved finding.
        self.write('src/api.py', 'price = 11\n')
        audit = runtime.inspect_project(self.root, self.project, resolved)
        self.assertIn({'feature': 'cli', 'finding': gap}, audit['product_findings'])
        self.assertEqual(audit['status'], 'PARTIAL')

    def test_process_exit_during_review_preserves_state_and_next_review_resumes(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'init')
        project = self.write('.harness/project.yaml', json.dumps(self.project))
        state_file = self.write('.work/state.json', json.dumps(state))
        basis = runtime.inspect_project(self.root, self.project, state)['features'][0]['basis']
        review = self.write('.work/review.json', json.dumps({'feature': 'api', 'basis': basis,
            'analysis': 'Reviewed unchanged API and its criteria.', 'references': ['docs/map.md'], 'findings': []}))
        args = ['review', '--root', str(self.root), '--state', '.work/state.json', '--review', str(review)]
        child = self.write('.work/interrupt.py',
            "import runpy,json,os,sys\n"
            "runtime=runpy.run_path(sys.argv[1])\n"
            "def interrupt(value, stream, **kwargs):\n"
            " stream.write('{');stream.flush();os._exit(23)\n"
            "json.dump=interrupt\n"
            "runtime['main'](sys.argv[2:])\n")
        before = state_file.read_bytes()
        interrupted = subprocess.run([sys.executable, str(child), str(SCRIPT), *args], capture_output=True)
        self.assertEqual(interrupted.returncode, 23, interrupted.stderr)
        self.assertEqual(state_file.read_bytes(), before)
        resumed = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
        outcome = json.loads(resumed.stdout)
        self.assertIn('api', json.loads(state_file.read_text())['reviews'], outcome)
        self.assertEqual(json.loads(state_file.read_text())['baseline'], state['baseline'])
        begin_args = ['begin', '--root', str(self.root), '--state', '.work/new.json']
        interrupted = subprocess.run([sys.executable, str(child), str(SCRIPT), *begin_args], capture_output=True)
        self.assertEqual(interrupted.returncode, 23)
        self.assertFalse((self.root / '.work/new.json').exists())
        resumed = subprocess.run([sys.executable, str(SCRIPT), *begin_args], capture_output=True, text=True)
        self.assertEqual(json.loads(resumed.stdout)['status'], 'PARTIAL')
        self.assertEqual(json.loads((self.root / '.work/new.json').read_text())['baseline'], state['baseline'])


if __name__ == '__main__':
    unittest.main()
