"""Read-only investigation continuity and reason-specific repair/retirement."""
from copy import deepcopy
import json
import os
import subprocess
import sys
import unittest

from tests.distribution import test_project_workflow as existing


class WorkflowRefinementTests(unittest.TestCase):
    setUp = existing.ProjectWorkflowTests.setUp
    write = existing.ProjectWorkflowTests.write
    runtime = existing.ProjectWorkflowTests.runtime
    review = existing.ProjectWorkflowTests.review
    invoke = existing.ProjectWorkflowTests.invoke

    def investigation(self):
        return {'scope': 'whole-project', 'inventory_status': 'complete',
                'inventory_refs': ['docs/map.md'], 'source_refs': ['src/api.py', 'src/cli.py'],
                'allowed': ['Read source and retained evidence'], 'forbidden': ['Change product or start services'],
                'next_actions': ['Observe CLI in a separately authorized execution'],
                'entries': [
                    {'id': 'api-price', 'location': 'src/api.py', 'access': 'GET /price',
                     'conditions': 'Source inspection only', 'expected': 'Ten', 'observed': 'Constant is ten',
                     'status': 'observed', 'evidence': ['src/api.py'], 'owner': 'product',
                     'hypothesis': 'Runtime behavior remains unverified'},
                    {'id': 'cli-price', 'location': 'src/cli.py', 'access': 'CLI price',
                     'conditions': 'CLI has not run', 'expected': 'Ten', 'status': 'unobserved',
                     'evidence': [], 'owner': 'unknown'}]}

    def test_unconfigured_investigation_survives_fresh_context_without_setup_or_execution(self):
        investigation = self.write('.work/input.json', json.dumps(self.investigation()))
        original = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        _, started = self.invoke('start', '--intent', 'diagnose', '--request-summary', 'Inspect all entrypoints only',
                                 '--investigation', str(investigation))
        self.assertIn('task_context', started, started)
        self.assertEqual(started['status'], 'PARTIAL')
        context = started['task_context']
        saved = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        for action in ('lookup', 'resume'):
            _, result = self.invoke(action, context=context)
            self.assertEqual(result['task']['task_id'], started['task']['task_id'])
            self.assertEqual(result['investigation']['unobserved'], ['cli-price'])
            self.assertEqual(result['investigation']['total'], 2)
            self.assertEqual(result['test_commands_executed'], 0)
        self.assertEqual(saved, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertTrue(all(p.read_bytes() == value for name, value in original.items() for p in [existing.Path(name)]))
        self.assertFalse((self.root / '.harness/project.yaml').exists())
        hook = subprocess.run([sys.executable, str(existing.SCRIPT.with_name('workflow_context.py'))],
            input=json.dumps({'cwd': str(self.root), 'hook_event_name': 'UserPromptSubmit'}),
            capture_output=True, text=True, encoding='utf-8',
            env=dict(os.environ, AGENT_WORKFLOW_CONTEXT=context))
        self.assertEqual(hook.returncode, 0, hook.stderr)
        detail = json.loads(json.loads(hook.stdout)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
        self.assertEqual(detail['current_task']['task_id'], started['task']['task_id'])
        self.assertEqual(detail['current_task']['investigation']['unobserved'], ['cli-price'])
        _, another = self.invoke('start', '--intent', 'diagnose', '--request-summary', 'Independent survey',
                                 '--investigation', str(investigation))
        _, ambiguous = self.invoke('resume')
        self.assertEqual(ambiguous['status'], 'BLOCKED')
        self.assertEqual(len(ambiguous['task_candidates']), 2)
        self.assertNotEqual(another['task']['task_id'], started['task']['task_id'])
        _, execute = self.invoke('prepare', context=context)
        self.assertEqual(execute['status'], 'BLOCKED')

    def test_investigation_update_preserves_denominator_identity_and_observation_bindings(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, {}, 'diagnose', request_summary='Read-only whole project')
        state = runtime.record_investigation(self.root, state, self.investigation())
        identity = runtime.task_identity(state)
        smaller = self.investigation()
        smaller['entries'].pop()
        with self.assertRaisesRegex(ValueError, 'investigation_entry_removed'):
            runtime.record_investigation(self.root, state, smaller)
        changed = self.investigation()
        changed['forbidden'] = []
        with self.assertRaisesRegex(ValueError, 'investigation_scope_changed'):
            runtime.record_investigation(self.root, state, changed)
        changed = self.investigation()
        changed['entries'][1].update(status='observed', observed='Source prints ten', evidence=['src/cli.py'])
        updated = runtime.record_investigation(self.root, state, changed)
        self.assertEqual(runtime.task_identity(updated), identity)
        self.assertEqual(runtime.inspect_project(self.root, {}, updated)['status'], 'READY_FOR_REVIEW')
        self.write('src/cli.py', 'print(11)\n')
        stale = runtime.inspect_project(self.root, {}, updated)
        self.assertEqual(stale['status'], 'PARTIAL')
        self.assertIn('cli-price', stale['investigation']['stale'])
        changed['entries'][1]['evidence'] = []
        with self.assertRaisesRegex(ValueError, 'observed_entry_requires_evidence'):
            runtime.record_investigation(self.root, state, changed)

    def test_configured_task_uses_same_investigation_record(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'change')
        updated = runtime.record_investigation(self.root, state, self.investigation())
        self.assertEqual(state['task_id'], updated['task_id'])
        audit = runtime.inspect_project(self.root, self.project, updated)
        self.assertEqual(audit['investigation']['unobserved'], ['cli-price'])

    def test_unconfigured_hook_bounds_large_investigation_without_losing_remaining_count(self):
        survey = self.investigation()
        survey['entries'] = [dict(survey['entries'][1], id='entry-' + str(i) + 'x' * 100) for i in range(100)]
        survey['next_actions'] = ['Do not guess: ' + 'x' * 10000]
        path = self.write('.work/input.json', json.dumps(survey))
        _, started = self.invoke('start', '--intent', 'diagnose', '--request-summary', 'Read-only survey',
                                 '--investigation', str(path))
        hook = subprocess.run([sys.executable, str(existing.SCRIPT.with_name('workflow_context.py'))],
            input=json.dumps({'cwd': str(self.root), 'hook_event_name': 'UserPromptSubmit'}),
            capture_output=True, text=True, encoding='utf-8',
            env=dict(os.environ, AGENT_WORKFLOW_CONTEXT=started['task_context']))
        output = json.loads(hook.stdout)['hookSpecificOutput']['additionalContext']
        self.assertLess(len(output), 6000)
        detail = json.loads(output.split('\n', 1)[1])
        self.assertEqual(detail['current_task']['investigation']['unobserved_count'], 100)

    def test_feedback_intentional_difference_and_environment_are_not_product_repairs(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        complaint = {'id': 'candidate-1', 'feature': 'api', 'candidate_id': 'api-price',
                     'expected': 'Same layout', 'observed': 'CLI is different', 'reproduction': 'Compare guide',
                     'kind': 'intentional_difference', 'scope': 'CLI output', 'reason': 'Terminal variant',
                     'evidence_refs': ['docs/map.md'], 'owner_refs': ['src/cli.py'],
                     'reconsider': 'A GUI is introduced', 'user_review': {'decision': 'intentional_difference',
                         'reference': 'docs/map.md'}}
        state = runtime.record_feedback(self.root, self.project, state, complaint)
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(result['feedback'][0]['status'], 'ACCEPTED', result['feedback'])
        self.assertFalse(any('repair' in o['requires'] for o in result['obligations']))
        self.assertNotIn('owner_repair_not_observed', result['feedback'][0]['remaining'])
        followup = runtime.begin(self.root, self.project, 'change', prior_state=state)
        self.assertEqual(followup['feedback'], state['feedback'])
        for kind in ('environment_limit', 'unknown'):
            entry = dict(complaint, id=kind, kind=kind, root_cause='User agreed', green_bundle='.work/fake.json')
            state = runtime.record_feedback(self.root, self.project, state, entry)
            row = next(r for r in runtime.inspect_project(self.root, self.project, state)['feedback'] if r['id'] == kind)
            self.assertEqual(row['status'], 'OPEN')
        with self.assertRaisesRegex(ValueError, 'feedback_kind'):
            runtime.record_feedback(self.root, self.project, state, dict(complaint, kind='approved'))

    def test_changed_requirement_needs_authority_new_revision_and_real_retained_contract(self, kind='requirement_change'):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['sources'].append('src/run.py')
        self.project['commands']['check'] = [sys.executable, 'src/run.py', '{report_dir}/native.json']
        self.project['extensions']['workflow']['assertions'] = 'assertions.json'
        self.write('src/run.py', "import json,sys,runpy\nfrom pathlib import Path\n"
                   "price=runpy.run_path('src/api.py')['price']" + ('-2' if kind == 'oracle_tool_error' else '') + "\n"
                   "Path(sys.argv[1]).write_text(json.dumps({'price':price,'zero':0}))\n")
        if kind == 'oracle_tool_error':
            self.write('src/api.py', 'price = 12\n')
            self.write('docs/requirement.md', 'Price twelve; zero remains valid.\n')
            independent = subprocess.run([sys.executable, '-c', "import runpy; print(runpy.run_path('src/api.py')['price'])"],
                                         cwd=self.root, capture_output=True, text=True, check=True)
            self.write('.work/independent.txt', independent.stdout)
        self.write('docs/authorization.md', 'User requests price twelve; zero remains valid.\n')
        self.write('assertions.json', json.dumps({'schema_version': 1, 'checks': [{
            'id': 'check', 'feature_id': 'api', 'expected': 'Price twelve and zero remains valid', 'required': True,
            'selection': {'status': 'selected', 'reason': 'Authorized new price'},
            'raw_observations': [{'path': '{report_dir}/native.json', 'pointer': '$', 'assertions': [
                {'pointer': '/price', 'equals': 12}, {'pointer': '/zero', 'equals': 0}]}],
            'dependency': {'file_refs': ['src/api.py', 'src/run.py']},
            'fixture': {'file_refs': ['docs/requirement.md']}}]}))
        self.write('.harness/project.yaml', json.dumps(self.project))
        _, start = self.invoke('start', '--intent', 'feedback', '--target', 'api')
        context = start['task_context']
        entry = {'id': 'new-price', 'feature': 'api', 'kind': kind,
                 'expected': 'Twelve', 'observed': 'Ten', 'reproduction': 'Read price',
                 'scope': 'API price', 'reason': 'New requirement', 'reconsider': 'Price changes again',
                 'evidence_refs': ['docs/authorization.md'], 'owner_refs': ['src/api.py'],
                 'confirmation': {'check': 'check', 'expected_pointer': '/price', 'normal_pointer': '/zero'}}
        feedback = self.write('.work/feedback.json', json.dumps(entry))
        _, pending = self.invoke('feedback', '--feedback', str(feedback), context=context)
        if kind == 'requirement_change':
            self.assertIn('requirement_change_authorization_required', pending['feedback'][0]['remaining'])
            self.assertIn('criterion_revision_not_observed', pending['feedback'][0]['remaining'])
            self.write('docs/requirement.md', 'Price twelve; zero remains valid.\n')
            self.write('src/api.py', 'price = 12\n')
        else:
            self.assertIn('oracle_or_tool_repair_not_observed', pending['feedback'][0]['remaining'])
            # The independent product path is correct while the actual adapter fails.
            _, prepared = self.invoke('prepare', context=context)
            _, red = self.invoke('execute', '--run-check', str(existing.ROOT / 'scripts/run_check.py'), context=context)
            self.assertEqual(red['verification']['status'], 'ISSUES', red)
            original = self.root / 'src/run.py'
            original.write_text(original.read_text().replace("['price']-2", "['price']"), encoding='utf-8')
            entry.update(trace='API value -> runner subtraction -> observation', root_cause='Adapter subtracts two',
                         repair_paths=['src/run.py'], evidence_refs=['.work/independent.txt'], owner_refs=['src/run.py'])
        _, prepared = self.invoke('prepare', context=context)
        self.assertEqual(prepared['verification']['status'], 'PREPARED', prepared)
        _, executed = self.invoke('execute', '--run-check', str(existing.ROOT / 'scripts/run_check.py'), context=context)
        self.assertEqual(executed['verification']['status'], 'PASS', executed)
        entry['green_bundle'] = existing.Path(executed['verification']['execution']['bundle_path']).relative_to(self.root).as_posix()
        entry['authorization_refs'] = ['docs/authorization.md']
        feedback.write_text(json.dumps(entry), encoding='utf-8')
        _, confirmed = self.invoke('feedback', '--feedback', str(feedback), context=context)
        self.assertEqual(confirmed['feedback'][0]['status'], 'RESOLVED', confirmed['feedback'])
        self.assertNotIn('red_bundle', confirmed['feedback'][0])
        _, later = self.invoke('start', '--intent', 'change', '--target', 'api', context=context)
        self.assertEqual(later['feedback'][0]['status'], 'RESOLVED', later['feedback'])
        _, reused = self.invoke('prepare', context=later['task_context'])
        self.assertEqual(reused['verification']['status'], 'NOT_REQUIRED', reused)
        self.assertEqual(reused['test_commands_executed'], 0)
        self.write('docs/requirement.md', 'Price changed without revalidation.\n')
        _, stale = self.invoke('lookup', context=later['task_context'])
        self.assertEqual(stale['feedback'][0]['status'], 'OPEN')

    def test_independent_tool_error_repairs_adapter_without_changing_product_or_requirement(self):
        self.test_changed_requirement_needs_authority_new_revision_and_real_retained_contract(kind='oracle_tool_error')

    def test_unrelated_investigation_update_cannot_refresh_stale_observations(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, {}, 'diagnose', request_summary='Inspect source')
        state = runtime.record_investigation(self.root, state, self.investigation())
        self.write('src/api.py', 'price = 11\n')
        update = self.investigation()
        update['next_actions'] = ['Reinspect changed API']
        state = runtime.record_investigation(self.root, state, update)
        result = runtime.inspect_project(self.root, {}, state)
        self.assertIn('api-price', result['investigation']['stale'])

    def test_entry_metadata_update_cannot_refresh_stale_observation(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, {}, 'diagnose', request_summary='Inspect source')
        state = runtime.record_investigation(self.root, state, self.investigation())
        self.write('src/api.py', 'price = 11\n')
        update = self.investigation()
        update['entries'][0].update(owner='tool', hypothesis='Reconsider responsibility')
        state = runtime.record_investigation(self.root, state, update)
        result = runtime.inspect_project(self.root, {}, state)
        self.assertIn('api-price', result['investigation']['stale'])

    def test_intentional_difference_waits_for_actual_user_review(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        entry = {'id': 'candidate-1', 'feature': 'api', 'kind': 'intentional_difference',
                 'expected': 'Common layout', 'observed': 'Terminal layout differs', 'reproduction': 'Compare guide',
                 'scope': 'Terminal', 'reason': 'Terminal variant', 'evidence_refs': ['docs/map.md'],
                 'owner_refs': ['src/cli.py'], 'reconsider': 'A GUI is introduced'}
        for decision in (None, 'defer', 'opinion'):
            with self.subTest(decision=decision):
                update = dict(entry)
                if decision:
                    update['user_review'] = {'decision': decision, 'reference': 'docs/map.md'}
                updated = runtime.record_feedback(self.root, self.project, state, update)
                result = runtime.inspect_project(self.root, self.project, updated)
                self.assertEqual(result['feedback'][0]['status'], 'OPEN')

    def test_requirement_retirement_does_not_force_a_replacement_detector(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['prevention'] = [{'failure': 'Legacy price', 'scope': 'Old quote route', 'check': 'check',
                                 'normal_exception': 'New route remains valid', 'reconsider': 'Legacy restored'}]
        feature['coverage'] = [{'id': 'legacy-price', 'requirement': 'docs/requirement.md', 'outcome': 'Legacy price',
                               'perspectives': ['business'], 'areas': ['BE/API'], 'kind': 'test', 'check': 'check'}]
        feature['sources'].append('src/menu.py')
        self.write('src/api.py', 'def legacy_quote():\n    return 10\n')
        self.write('src/menu.py', 'from api import legacy_quote\nitems = [legacy_quote]\n')
        before = subprocess.run([sys.executable, '-c', 'import menu; print(menu.items[0]())'],
                                cwd=self.root / 'src', capture_output=True, text=True, check=True)
        self.assertEqual(before.stdout.strip(), '10')
        state = runtime.begin(self.root, self.project, 'maintain')
        self.write('docs/change.md', 'Authorized removal of legacy route; CLI retained.\n')
        self.write('docs/requirement.md', 'Only CLI price remains.\n')
        self.write('src/api.py', '# Legacy quote entrypoint removed; CLI remains separate.\n')
        self.write('src/menu.py', 'items = []\n')
        removed = subprocess.run([sys.executable, '-c',
            "import api,menu; assert not hasattr(api,'legacy_quote'); assert menu.items == []; print('legacy removed')"],
            cwd=self.root / 'src', capture_output=True, text=True, check=True)
        retained = subprocess.run([sys.executable, 'src/cli.py'], cwd=self.root,
                                  capture_output=True, text=True, check=True)
        self.assertEqual(retained.stdout.strip(), '10')
        self.write('.work/retirement-runtime.json', json.dumps({
            'before': before.stdout, 'removed': removed.stdout, 'retained_cli': retained.stdout}))
        feature['checks'] = []
        feature['prevention'] = []
        feature['coverage'] = []
        state = self.review(runtime, state, 'api')
        review = deepcopy(state['reviews']['api'])
        review['check_decisions'] = {'check': {'action': 'remove', 'reason': 'requirement_retired',
            'retirement': {'authorization_refs': ['docs/change.md'], 'requirement_refs': ['docs/requirement.md'],
                           'retired_failures': [{'failure': 'Legacy price', 'scope': 'Old quote route'}],
                           'removed_entrypoints': ['GET /legacy-quote'], 'removed_callers': ['Old quote menu'],
                           'remaining_impact': 'CLI unchanged; no remaining consumer of legacy route',
                           'references': ['src/api.py', 'src/menu.py', 'src/cli.py', 'docs/change.md',
                                          '.work/retirement-runtime.json']}}}
        state = runtime.record_review(self.root, self.project, state, review)
        row = runtime.inspect_project(self.root, self.project, state)['check_retirements'][0]
        self.assertEqual(row['status'], 'PRESERVED', row)
        self.assertEqual(row['remaining'], [])
        missing = deepcopy(review)
        missing['check_decisions']['check']['retirement']['retired_failures'] = []
        insufficient = runtime.record_review(self.root, self.project, state, missing)
        row = runtime.inspect_project(self.root, self.project, insufficient)['check_retirements'][0]
        self.assertEqual(row['status'], 'BLOCKED', row)
        self.write('docs/change.md', 'Removal revoked; require another decision.\n')
        row = runtime.inspect_project(self.root, self.project, state)['check_retirements'][0]
        self.assertEqual(row['status'], 'BLOCKED', row)
        self.write('docs/change.md', 'Authorized removal of legacy route; CLI retained.\n')
        feature['coverage'] = [{'id': 'still-needed', 'requirement': 'docs/requirement.md', 'outcome': 'Current rule',
                                'perspectives': ['business'], 'areas': ['Domain'], 'kind': 'test', 'check': 'check'}]
        state = self.review(runtime, state, 'api')
        review['basis'] = state['reviews']['api']['basis']
        state = runtime.record_review(self.root, self.project, state, review)
        row = runtime.inspect_project(self.root, self.project, state)['check_retirements'][0]
        self.assertEqual(row['status'], 'BLOCKED')
        self.assertIn('retired_check_still_linked', row['remaining'])


if __name__ == '__main__':
    unittest.main()
