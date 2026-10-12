"""Read-only investigation continuity and reason-specific repair/retirement."""
from copy import deepcopy
import json
import os
import subprocess
import sys
import unittest
import runpy
from unittest.mock import patch

from tests.distribution import test_project_workflow as existing


class WorkflowRefinementTests(unittest.TestCase):
    setUp = existing.ProjectWorkflowTests.setUp
    write = existing.ProjectWorkflowTests.write
    runtime = existing.ProjectWorkflowTests.runtime
    review = existing.ProjectWorkflowTests.review
    invoke = existing.ProjectWorkflowTests.invoke

    def difference(self):
        # Synthetic approval fixture, never an actual user's UI review.
        self.write('docs/decision.md', 'Fixture: explicitly allow candidate terminal-price.\n')
        return {'id': 'variant', 'candidate_id': 'terminal-price', 'feature': 'api',
                'kind': 'intentional_difference', 'expected': 'Common output', 'observed': 'Terminal variant',
                'reproduction': 'Compare source', 'scope': 'Terminal price', 'reason': 'Terminal variant',
                'evidence_refs': ['docs/decision.md'], 'owner_refs': ['src/cli.py'],
                'reconsider': 'Related requirement or guide changes',
                'user_review': {'id': 'fixture-review-1', 'decision': 'intentional_difference',
                    'reference': 'docs/decision.md', 'candidate_id': 'terminal-price',
                    'disposition': 'intentional_difference', 'scope': 'Terminal price',
                    'criteria_refs': ['docs/requirement.md']}}

    def test_revoked_decision_cannot_be_reapproved_by_metadata_or_same_review(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        entry = self.difference()
        state = runtime.record_feedback(self.root, self.project, state, entry)
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['feedback'][0]['status'], 'ACCEPTED')
        original_hashes = deepcopy(state['feedback']['variant']['decision_hashes'])
        self.write('docs/decision.md', 'Fixture: approval withdrawn.\n')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['feedback'][0]['status'], 'OPEN')
        for update in ({'reason': 'Owner explanation'}, {'owner_refs': ['src/api.py']},
                       {'user_review': entry['user_review']}):
            state = runtime.record_feedback(self.root, self.project, state, dict(id='variant', feature='api', **update))
            self.assertEqual(state['feedback']['variant']['decision_hashes'], original_hashes)
            self.assertEqual(runtime.inspect_project(self.root, self.project, state)['feedback'][0]['status'], 'OPEN')
        followup = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=state)
        self.assertEqual(runtime.inspect_project(self.root, self.project, followup)['feedback'][0]['status'], 'OPEN')
        self.write('docs/decision-2.md', 'Fixture: new explicit approval of terminal-price.\n')
        new = dict(entry['user_review'], id='fixture-review-2', reference='docs/decision-2.md')
        renewed = runtime.record_feedback(self.root, self.project, followup,
            {'id': 'variant', 'feature': 'api', 'evidence_refs': ['docs/decision-2.md'], 'user_review': new})
        self.assertEqual(runtime.inspect_project(self.root, self.project, renewed)['feedback'][0]['status'], 'ACCEPTED')
        self.assertEqual(renewed['feedback']['variant']['decision_history'][0]['user_review'], entry['user_review'])
        self.assertEqual(renewed['feedback']['variant']['decision_history'][0]['decision_hashes'], original_hashes)
        later = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=renewed)
        self.assertEqual(runtime.inspect_project(self.root, self.project, later)['feedback'][0]['status'], 'ACCEPTED')

    def test_problem_agreement_and_mismatched_subject_cannot_approve_difference(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        entry = self.difference()
        self.write('docs/problem.md', 'Fixture: this is a bug; I agree it must be fixed.\n')
        cases = [{'decision': 'agree', 'reference': 'docs/problem.md'},
                 dict(entry['user_review'], candidate_id='other-candidate'),
                 dict(entry['user_review'], disposition='fix'),
                 dict(entry['user_review'], scope='Other screen'),
                 dict(entry['user_review'], criteria_refs=[])]
        for review in cases:
            with self.subTest(review=review):
                recorded = runtime.record_feedback(self.root, self.project, state, dict(entry, user_review=review))
                self.assertEqual(runtime.inspect_project(self.root, self.project, recorded)['feedback'][0]['status'], 'OPEN')
        valid = runtime.record_feedback(self.root, self.project, state,
                                        dict(entry, user_review=dict(entry['user_review'], decision='agree')))
        self.assertEqual(runtime.inspect_project(self.root, self.project, valid)['feedback'][0]['status'], 'ACCEPTED')

    def test_classification_roundtrip_preserves_withdrawn_decision_basis(self):
        runtime = self.runtime()
        entry = self.difference()
        state = runtime.record_feedback(self.root, self.project,
            runtime.begin(self.root, self.project, 'feedback', ['api']), entry)
        original = deepcopy(state['feedback']['variant'])
        self.write('docs/decision.md', 'Fixture: approval withdrawn.\n')
        for kind in ('unknown', 'environment_limit', 'requirement_change', 'oracle_tool_error'):
            with self.subTest(kind=kind):
                changed = runtime.record_feedback(self.root, self.project, state,
                    {'id': 'variant', 'feature': 'api', 'kind': kind, 'reason': 'Investigating'})
                returned = runtime.record_feedback(self.root, self.project, changed,
                    {'id': 'variant', 'feature': 'api', 'kind': 'intentional_difference'})
                self.assertEqual(runtime.inspect_project(self.root, self.project, returned)['feedback'][0]['status'], 'OPEN')
                self.assertEqual(returned['feedback']['variant']['decision_hashes'], original['decision_hashes'])
                self.assertEqual(returned['feedback']['variant']['decision_binding'], original['decision_binding'])
                later = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=returned)
                self.assertEqual(runtime.inspect_project(self.root, self.project, later)['feedback'][0]['status'], 'OPEN')
        self.write('docs/new-decision.md', 'Fixture: new explicit approval.\n')
        renewed = runtime.record_feedback(self.root, self.project, returned, dict(id='variant', feature='api',
            evidence_refs=['docs/new-decision.md'], user_review=dict(entry['user_review'],
                id='fixture-review-2', reference='docs/new-decision.md')))
        self.assertEqual(runtime.inspect_project(self.root, self.project, renewed)['feedback'][0]['status'], 'ACCEPTED')
        self.assertEqual(renewed['feedback']['variant']['decision_history'][0]['decision_hashes'], original['decision_hashes'])

    def test_applicable_criteria_connections_and_legacy_require_new_review(self):
        runtime = self.runtime()
        entry = self.difference()
        state = runtime.record_feedback(self.root, self.project,
            runtime.begin(self.root, self.project, 'feedback', ['api']), entry)
        before = deepcopy(state)
        self.write('docs/new-rule.md', 'Fixture: terminal difference forbidden.\n')
        for criteria in (['docs/requirement.md', 'docs/new-rule.md'], ['docs/new-rule.md']):
            with self.subTest(criteria=criteria):
                project = deepcopy(self.project)
                project['extensions']['workflow']['features'][0]['criteria'] = criteria
                audit = runtime.inspect_project(self.root, project, state)
                self.assertEqual(audit['feedback'][0]['status'], 'OPEN')
                self.assertIn('decision_criteria_connections_changed', audit['feedback'][0]['remaining'])
                later = runtime.begin(self.root, project, 'change', ['api'], prior_state=state)
                self.assertEqual(runtime.inspect_project(self.root, project, later)['feedback'][0]['status'], 'OPEN')
        self.assertEqual(state, before, 'Lookup must not migrate or refresh hashes')
        unrelated = deepcopy(self.project)
        unrelated['extensions']['workflow']['features'][1]['criteria'].append('docs/new-rule.md')
        self.assertEqual(runtime.inspect_project(self.root, unrelated, state)['feedback'][0]['status'], 'ACCEPTED')
        legacy = deepcopy(state)
        legacy['feedback']['variant']['decision_binding'].pop('criteria_connections', None)
        audit = runtime.inspect_project(self.root, self.project, legacy)
        self.assertEqual(audit['feedback'][0]['status'], 'OPEN')
        self.assertIn('decision_criteria_connections_required', audit['feedback'][0]['remaining'])
        project = deepcopy(self.project)
        project['extensions']['workflow']['features'][0]['criteria'].append('docs/new-rule.md')
        self.write('docs/new-decision.md', 'Fixture: explicitly reviewed both criteria.\n')
        renewed = runtime.record_feedback(self.root, project, state, dict(id='variant', feature='api',
            evidence_refs=['docs/new-decision.md'], user_review=dict(entry['user_review'], id='fixture-review-2',
                reference='docs/new-decision.md', criteria_refs=['docs/requirement.md', 'docs/new-rule.md'])))
        self.assertEqual(runtime.inspect_project(self.root, project, renewed)['feedback'][0]['status'], 'ACCEPTED')

    def test_related_criterion_reopens_decision_but_unrelated_criterion_does_not(self):
        runtime = self.runtime()
        self.write('docs/unrelated.md', 'Separate CLI documentation.\n')
        self.project['extensions']['workflow']['features'][1]['criteria'] = ['docs/unrelated.md']
        self.write('docs/requirement.md', 'Terminal variant allowed.\n')
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        state = runtime.record_feedback(self.root, self.project, state, self.difference())
        self.write('docs/unrelated.md', 'Separate CLI documentation changed.\n')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['feedback'][0]['status'], 'ACCEPTED')
        before = deepcopy(state)
        self.write('docs/requirement.md', 'Terminal variant forbidden.\n')
        audit = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual(audit['feedback'][0]['status'], 'OPEN')
        self.assertIn('decision_criteria_stale', audit['feedback'][0]['remaining'])
        self.assertNotEqual(audit['status'], 'PASS')
        self.assertEqual(state, before, 'Inspection must not rebind criteria')
        later = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=state)
        self.assertEqual(runtime.inspect_project(self.root, self.project, later)['feedback'][0]['status'], 'OPEN')

    def test_legacy_decision_requires_rebinding_and_target_edit_cannot_inherit_approval(self):
        runtime = self.runtime()
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        entry = self.difference()
        state = runtime.record_feedback(self.root, self.project, state, entry)
        legacy = deepcopy(state)
        legacy['feedback']['variant'].pop('decision_binding', None)
        self.assertEqual(runtime.inspect_project(self.root, self.project, legacy)['feedback'][0]['status'], 'OPEN')
        changed = runtime.record_feedback(self.root, self.project, state,
                                          {'id': 'variant', 'feature': 'api', 'candidate_id': 'different'})
        self.assertEqual(runtime.inspect_project(self.root, self.project, changed)['feedback'][0]['status'], 'OPEN')

    def test_consumed_ui_guide_is_required_and_reopens_the_explicit_variant(self):
        runtime = self.runtime()
        self.write('docs/ui.md', 'Terminal variant allowed by shared guide.\n')
        self.write('src/tokens.css', ':root { --gap: 8px; }\n')
        self.project['extensions']['workflow']['ui_systems'] = {'shared': {
            'guide': 'docs/ui.md', 'tokens': ['src/tokens.css'], 'components': ['src/cli.py'],
            'consumers': ['api'], 'exceptions': []}}
        state = runtime.begin(self.root, self.project, 'feedback', ['api'])
        entry = self.difference()
        missing = runtime.record_feedback(self.root, self.project, state, entry)
        self.assertEqual(runtime.inspect_project(self.root, self.project, missing)['feedback'][0]['status'], 'OPEN')
        entry['user_review']['criteria_refs'].append('docs/ui.md')
        approved = runtime.record_feedback(self.root, self.project, state, entry)
        self.assertEqual(runtime.inspect_project(self.root, self.project, approved)['feedback'][0]['status'], 'ACCEPTED')
        self.write('docs/ui.md', 'Terminal variant forbidden.\n')
        self.assertEqual(runtime.inspect_project(self.root, self.project, approved)['feedback'][0]['status'], 'OPEN')
        later = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=approved)
        self.assertEqual(runtime.inspect_project(self.root, self.project, later)['feedback'][0]['status'], 'OPEN')

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

    def test_hook_distinguishes_task_project_gaps_and_retains_exact_task_under_pressure(self):
        self.write('.harness/project.yaml', json.dumps(self.project))
        _, started = self.invoke('start', '--intent', 'change', '--target', 'api',
            '--request-summary', 'Keep API output', '--outcome-ref', 'docs/requirement.md')
        def hook():
            result = subprocess.run([sys.executable, str(existing.SCRIPT.with_name('workflow_context.py'))],
                input=json.dumps({'cwd': str(self.root), 'hook_event_name': 'UserPromptSubmit'}),
                capture_output=True, text=True, encoding='utf-8',
                env=dict(os.environ, AGENT_WORKFLOW_CONTEXT=started['task_context']))
            output = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
            self.assertLess(len(output), 6000)
            return json.loads(output.split('\n', 1)[1])
        detail = hook()
        self.assertEqual(detail['current_task']['scope']['gap_count'], 6)
        self.assertEqual(detail['current_task']['scope']['project_gap_count'], 12)
        self.assertEqual(detail['current_task']['scope']['out_of_task_count'], 6)
        self.assertEqual(detail['current_task']['scope']['cell_count'], 6)
        snapshot = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        # Large unrelated candidate discovery must never eject the explicitly selected task.
        for i in range(10):
            self.invoke('start', '--intent', 'change', '--target', 'cli', '--request-summary', 'x' * 10000)
        detail = hook()
        self.assertEqual(detail['current_task']['task_id'], started['task']['task_id'])
        self.assertEqual(detail['current_task']['targets'], ['api'])
        self.assertEqual(detail['current_task']['request']['summary'], 'Keep API output')
        self.assertEqual(detail['current_task']['features'][0]['criteria'], ['docs/requirement.md'])
        self.assertTrue(detail['current_task']['next_actions'])
        after = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.invoke('lookup', context=started['task_context'])
        self.invoke('resume', context=started['task_context'])
        hook()
        self.assertEqual(after, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertTrue(all(existing.Path(p).read_bytes() == value for p, value in snapshot.items()))

    def test_hook_shares_inventory_and_selected_configured_audit_within_one_invocation(self):
        self.project['extensions']['workflow']['state'] = '.work/task.json'
        self.write('.harness/project.yaml', json.dumps(self.project))
        _, started = self.invoke('begin', '--state', '.work/task.json', '--intent', 'change', '--target', 'api')
        runtime = self.runtime()
        state = json.loads((self.root / '.work/task.json').read_text())
        context = runtime.task_context(self.root, state, self.root / '.work/task.json')
        self.write('.work/goals/active/W-SAME/work.json', json.dumps({'work_id': 'W-SAME',
            'state': 'active', 'source_commit': state['base'], 'workflow_baseline': state}))
        hook = runpy.run_path(str(existing.SCRIPT.with_name('workflow_context.py')))['context']
        original_loader = runpy.run_path
        def load(path, *args, **kwargs):
            if existing.Path(path).resolve() == existing.SCRIPT.resolve():
                return vars(runtime)
            return original_loader(path, *args, **kwargs)
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=context), patch.object(runpy, 'run_path', load), \
                patch.object(runtime, 'inventory', wraps=runtime.inventory) as inventory, \
                patch.object(runtime, 'inspect_project', wraps=runtime.inspect_project) as inspect:
            detail = json.loads(hook({'cwd': str(self.root), 'hook_event_name': 'UserPromptSubmit'})[
                'hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            self.assertEqual(detail['current_task']['task_id'], state['task_id'])
            self.assertEqual(inventory.call_count, 1, 'One prompt must survey the same sources once')
            self.assertEqual(inspect.call_count, 1, 'Identical configured/selected state must share its audit')
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.write('src/api.py', 'price = 12\n')
        with patch.dict(os.environ, AGENT_WORKFLOW_CONTEXT=context), patch.object(runpy, 'run_path', load):
            updated = json.loads(hook({'cwd': str(self.root), 'hook_event_name': 'UserPromptSubmit'})[
                'hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
        self.assertIn('src/api.py', updated['current_task']['obligations'][0]['changed'],
                      'A later invocation must observe new bytes')

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
                     'reconsider': 'A GUI is introduced', 'user_review': {'id': 'fixture-variant-review',
                         'decision': 'intentional_difference', 'reference': 'docs/map.md',
                         'candidate_id': 'api-price', 'disposition': 'intentional_difference',
                         'scope': 'CLI output', 'criteria_refs': ['docs/requirement.md']}}
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

    def test_changed_requirement_needs_authority_new_revision_and_real_retained_contract(self, kind='requirement_change', added_owner=False):
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
        runner = self.root / 'src/run.py'
        original_runner = runner.read_bytes()
        if added_owner:
            runner.unlink()
        _, start = self.invoke('start', '--intent', 'feedback', '--target', 'api')
        context = start['task_context']
        if added_owner:
            runner.write_bytes(original_runner)
            self.assertNotIn('src/run.py', json.loads((self.root / start['task']['state']).read_text())['baseline'])
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
            if added_owner:
                entry['red_bundle'] = existing.Path(red['verification']['execution']['bundle_path']).relative_to(self.root).as_posix()
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
        if not added_owner:
            self.assertNotIn('red_bundle', confirmed['feedback'][0])
        else:
            saved = json.loads((self.root / start['task']['state']).read_text())
            self.assertNotIn('src/run.py', saved['baseline'])
            self.assertNotIn('src/run.py', saved['feedback']['new-price']['source_before'])
            no_red = deepcopy(saved)
            no_red['feedback']['new-price'].pop('red_bundle')
            self.assertIn('oracle_or_tool_repair_not_observed', runtime.inspect_feedback(self.root,
                runtime.configuration(self.project), no_red)[0]['remaining'])
            present = deepcopy(saved)
            present['feedback']['new-price']['source_before']['src/run.py'] = runtime.file_hash(self.root, 'src/run.py')
            self.assertIn('oracle_or_tool_repair_not_observed', runtime.inspect_feedback(self.root,
                runtime.configuration(self.project), present)[0]['remaining'], 'Red cannot override a present baseline')
            for malformed in (None, 0, 'not-a-hash'):
                invalid = deepcopy(saved)
                invalid['feedback']['new-price']['source_before']['src/run.py'] = malformed
                self.assertIn('oracle_or_tool_repair_not_observed', runtime.inspect_feedback(self.root,
                    runtime.configuration(self.project), invalid)[0]['remaining'], 'Malformed present preimages cannot certify repair')
            config = deepcopy(runtime.configuration(self.project))
            config['features'][0]['sources'].remove('src/run.py')
            self.assertIn('oracle_or_tool_repair_not_observed', runtime.inspect_feedback(self.root, config, saved)[0]['remaining'])
            red_path = self.root / entry['red_bundle']
            binding = json.loads(red_path.read_text())
            bound = json.loads(existing.Path(binding['plan']).read_text())
            raw_file = existing.Path(bound['checks'][0]['raw_observations'][0]['path'])
            original_raw = raw_file.read_bytes()
            try:
                raw_file.write_text(json.dumps({'price': 12, 'zero': 0}))
                self.assertIn('oracle_or_tool_repair_not_observed', runtime.inspect_feedback(self.root,
                    runtime.configuration(self.project), saved)[0]['remaining'], 'Tampered raw cannot certify a repair preimage')
            finally:
                raw_file.write_bytes(original_raw)
            self.assertEqual(runtime.inspect_feedback(self.root, runtime.configuration(self.project), saved)[0]['status'], 'RESOLVED')
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

    def test_new_tool_owner_repair_uses_bound_failure_hash(self):
        self.test_changed_requirement_needs_authority_new_revision_and_real_retained_contract(kind='oracle_tool_error', added_owner=True)

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

    def test_rule_retirement_keeps_quote_and_caller_with_accounted_impact(self):
        runtime = self.runtime()
        feature = self.project['extensions']['workflow']['features'][0]
        feature['sources'].extend(['src/menu.py', 'src/unrelated.py'])
        feature['prevention'] = [{'failure': 'Cap exceeded', 'scope': 'Quote amount', 'check': 'check',
                                 'normal_exception': 'Zero allowed', 'reconsider': 'Cap retired',
                                 'owner_refs': ['src/api.py']}]
        self.write('src/api.py', 'def quote(amount):\n    return min(amount, 10)\n')
        self.write('src/menu.py', 'from api import quote\ndef select(amount):\n    return quote(amount)\n')
        self.write('src/unrelated.py', 'unrelated = 1\n')
        self.write('docs/requirement.md', 'Quote cap ten; zero valid.\n')
        state = runtime.begin(self.root, self.project, 'maintain')
        self.write('docs/change.md', 'Fixture authorization: remove cap, retain quote and callers.\n')
        self.write('docs/requirement.md', 'No quote cap; zero and callers remain valid.\n')
        self.write('src/api.py', 'def quote(amount):\n    return amount\n')
        actual = subprocess.run([sys.executable, '-c',
            'import json,api,menu; print(json.dumps([api.quote(12),api.quote(0),menu.select(12),menu.select(0)]))'],
            cwd=self.root / 'src', capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(actual.stdout), [12, 0, 12, 0])
        self.write('.work/retirement-runtime.json', actual.stdout)
        feature['checks'] = []
        feature['prevention'] = []
        state = self.review(runtime, state, 'api')
        review = deepcopy(state['reviews']['api'])
        proof = {'authorization_refs': ['docs/change.md'], 'requirement_refs': ['docs/requirement.md'],
                 'removed_entrypoints': [], 'removed_callers': [],
                 'entrypoints': [{'name': 'quote(amount)', 'disposition': 'retained', 'reason': 'Only cap removed',
                                  'references': ['src/api.py']}],
                 'callers': [{'name': 'menu.select(amount)', 'disposition': 'retained', 'reason': 'Same contract',
                              'references': ['src/menu.py']}],
                 'retired_failures': [{'failure': 'Cap exceeded', 'scope': 'Quote amount'}],
                 'remaining_impact': 'Twelve now allowed; zero and quote consumers retained.',
                 'references': ['src/api.py', 'src/menu.py', 'docs/change.md', '.work/retirement-runtime.json']}
        review['check_decisions'] = {'check': {'action': 'remove', 'reason': 'requirement_retired', 'retirement': proof}}
        accepted = runtime.record_review(self.root, self.project, state, review)
        row = runtime.inspect_project(self.root, self.project, accepted)['check_retirements'][0]
        self.assertEqual(row['status'], 'PRESERVED', row)
        later = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=accepted)
        self.assertEqual(later['check_links']['api']['checks'], [])
        for field, value in [('authorization_refs', []), ('retired_failures', []), ('entrypoints', []),
                             ('callers', [{'name': 'none', 'disposition': 'not_applicable'}])]:
            with self.subTest(field=field):
                invalid = deepcopy(review)
                invalid['check_decisions']['check']['retirement'][field] = value
                bad = runtime.record_review(self.root, self.project, state, invalid)
                self.assertEqual(runtime.inspect_project(self.root, self.project, bad)['check_retirements'][0]['status'], 'BLOCKED')
        self.write('src/api.py', 'def quote(amount):\n    return min(amount, 10)\n')
        self.write('src/unrelated.py', 'unrelated = 2\n')
        state = self.review(runtime, state, 'api')
        review['basis'] = state['reviews']['api']['basis']
        bad = runtime.record_review(self.root, self.project, state, review)
        row = runtime.inspect_project(self.root, self.project, bad)['check_retirements'][0]
        self.assertEqual(row['status'], 'BLOCKED', row)
        self.assertIn('retired_rule_source_change_not_observed', row['remaining'])
        forged = deepcopy(review)
        forged['check_decisions']['check']['retirement']['entrypoints'][0]['references'] = ['src/unrelated.py']
        bad = runtime.record_review(self.root, self.project, state, forged)
        self.assertEqual(runtime.inspect_project(self.root, self.project, bad)['check_retirements'][0]['status'], 'BLOCKED')

    def test_source_observation_preserves_runtime_unknowns_and_request_scope_in_hook(self):
        import runpy
        runtime = self.runtime()
        survey = self.investigation()
        survey['entries'] = survey['entries'][:1]
        survey['requested_methods'] = ['source', 'runtime']
        survey['entries'][0]['observation_method'] = 'source'
        survey['entries'][0]['unverified'] = [{'id': 'api-price-runtime', 'method': 'runtime',
                                              'reason': 'API runtime has not run'}]
        state = runtime.begin(self.root, {}, 'diagnose', request_summary='Inspect source and runtime')
        state = runtime.record_investigation(self.root, state, survey)
        before = deepcopy(state)
        audit = runtime.inspect_project(self.root, {}, state)['investigation']
        self.assertEqual(audit['total'], 1)
        self.assertEqual(audit['unobserved'], ['api-price-runtime'])
        self.assertEqual(audit['status'], 'PARTIAL')
        preview = runpy.run_path(str(existing.SCRIPT.with_name('workflow_context.py')))['investigation_context'](audit)
        self.assertEqual(preview['unobserved_count'], 1)
        self.assertEqual(preview['requested_methods'], ['source', 'runtime'])
        self.assertEqual(state, before)
        source = deepcopy(survey)
        source['requested_methods'] = ['source']
        separate = runtime.begin(self.root, {}, 'diagnose', request_summary='Source only')
        separate = runtime.record_investigation(self.root, separate, source)
        audit = runtime.inspect_project(self.root, {}, separate)['investigation']
        self.assertEqual(audit['status'], 'READY_FOR_REVIEW')
        self.assertEqual(audit['unobserved'], [])
        self.assertEqual(audit['out_of_scope'], ['api-price-runtime'])
        self.assertEqual(audit['observed_methods'], {'api-price': 'source'})

    def test_legacy_unverified_has_stable_ids_and_never_implies_runtime_observation(self):
        runtime = self.runtime()
        survey = self.investigation()
        survey['entries'] = survey['entries'][:1]
        survey['entries'][0]['unverified'] = ['Runtime API behavior not observed']
        state = runtime.begin(self.root, {}, 'diagnose', request_summary='Legacy source inspection')
        state = runtime.record_investigation(self.root, state, survey)
        audit = runtime.inspect_project(self.root, {}, state)['investigation']
        self.assertEqual(len(audit['unobserved']), 1)
        self.assertEqual(audit['observed_methods'], {'api-price': 'unspecified'})
        update = deepcopy(survey)
        update['next_actions'] = ['Inspect retained observations only']
        updated = runtime.record_investigation(self.root, state, update)
        self.assertEqual(runtime.inspect_project(self.root, {}, updated)['investigation']['unobserved'], audit['unobserved'])
        self.assertEqual(audit['total'], 1)

    def test_unknown_id_cannot_disappear_through_collision_or_wrong_observation_method(self):
        runtime = self.runtime()
        survey = self.investigation()
        survey['entries'] = survey['entries'][:1]
        survey['requested_methods'] = ['source', 'runtime']
        survey['entries'][0]['observation_method'] = 'source'
        survey['entries'][0]['unverified'] = [{'id': 'api-runtime', 'method': 'runtime', 'reason': 'Not executed'}]
        state = runtime.begin(self.root, {}, 'diagnose', request_summary='Source and runtime')
        state = runtime.record_investigation(self.root, state, survey)
        collision = deepcopy(survey)
        collision['entries'][0]['unverified'][0]['id'] = 'api-price'
        with self.assertRaisesRegex(ValueError, 'unverified.*collision'):
            runtime.record_investigation(self.root, runtime.begin(self.root, {}, 'diagnose', request_summary='Collision'), collision)
        replaced = deepcopy(survey)
        replaced['entries'][0]['unverified'] = []
        replaced['entries'].append(dict(survey['entries'][0], id='api-runtime', unverified=[], observation_method='source'))
        with self.assertRaisesRegex(ValueError, 'unverified.*method'):
            runtime.record_investigation(self.root, state, replaced)
        missing = deepcopy(survey)
        missing['entries'][0]['unverified'] = []
        with self.assertRaisesRegex(ValueError, 'unverified_removed'):
            runtime.record_investigation(self.root, state, missing)

    def test_related_followup_carries_unknowns_and_original_stale_observation_without_rebinding(self):
        runtime = self.runtime()
        survey = self.investigation()
        survey['entries'] = survey['entries'][:1]
        survey['requested_methods'] = ['source', 'runtime']
        survey['entries'][0]['observation_method'] = 'source'
        survey['entries'][0]['unverified'] = [{'id': 'api-runtime', 'method': 'runtime', 'reason': 'Not executed'}]
        state = runtime.begin(self.root, self.project, 'diagnose', ['api'], request_summary='Inspect API')
        state = runtime.record_investigation(self.root, state, survey)
        self.write('src/api.py', 'price = 11\n')
        later = runtime.begin(self.root, self.project, 'change', ['api'], prior_state=state)
        audit = runtime.inspect_project(self.root, self.project, later)
        self.assertIn('investigation', audit, 'Related follow-up must retain pending observations')
        self.assertEqual(audit['investigation']['unobserved'], ['api-runtime'])
        self.assertEqual(audit['investigation']['stale'], ['api-price'])
        self.assertEqual(later['investigation'], state['investigation'])
        unconfigured = runtime.begin(self.root, {}, 'diagnose', request_summary='Source and runtime')
        unconfigured = runtime.record_investigation(self.root, unconfigured, survey)
        next_survey = runtime.begin(self.root, {}, 'diagnose', prior_state=unconfigured, request_summary='Continue same survey')
        self.assertEqual(next_survey['investigation'], unconfigured['investigation'])

    def test_scoped_unknown_preview_stays_bounded_with_long_permissions_and_stale_ids(self):
        survey = self.investigation()
        survey['requested_methods'] = ['source']
        source = dict(survey['entries'][0], observation_method='source')
        survey['entries'] = [dict(source, id='observed-' + 'x' * 150 + str(i)) for i in range(6)]
        survey['entries'] += [dict(source, id='unknown-' + 'x' * 150 + str(i), status='unobserved') for i in range(6)]
        survey['entries'] += [dict(source, id='outside-' + 'x' * 150 + str(i), status='unobserved',
                                   observation_method='runtime') for i in range(6)]
        for field in ('allowed', 'forbidden', 'next_actions'):
            survey[field] = [field + 'x' * 1000 for _ in range(6)]
        path = self.write('.work/input.json', json.dumps(survey))
        _, started = self.invoke('start', '--intent', 'diagnose', '--request-summary', 'Source only ' + 'x' * 1000,
                                 '--investigation', str(path))
        self.write('src/api.py', 'price = 11\n')
        hook = subprocess.run([sys.executable, str(existing.SCRIPT.with_name('workflow_context.py'))],
            input=json.dumps({'cwd': str(self.root), 'hook_event_name': 'UserPromptSubmit'}),
            capture_output=True, text=True, encoding='utf-8',
            env=dict(os.environ, AGENT_WORKFLOW_CONTEXT=started['task_context']))
        content = json.loads(hook.stdout)['hookSpecificOutput']['additionalContext']
        self.assertLess(len(content), 6000)
        current = json.loads(content.split('\n', 1)[1])['current_task']
        self.assertEqual(current['task_id'], started['task']['task_id'])
        for key in ('unobserved_count', 'out_of_scope_count', 'stale_count'):
            self.assertEqual(current['investigation'][key], 6)


if __name__ == '__main__':
    unittest.main()
