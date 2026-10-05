"""Real repository changes drive resumable obligations, never submitted PASS flags."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'authoring/scripts/project_workflow.py'


class ProjectWorkflowTests(unittest.TestCase):
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
        result = runtime.inspect_project(self.root, self.project, state)
        self.assertEqual([o['target'] for o in result['obligations']], ['api'])
        self.write('docs/requirement.md', 'price = twenty\n')
        self.assertEqual(len(runtime.inspect_project(self.root, self.project, state)['obligations']), 2)

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

    def test_changed_work_requires_bound_real_execution_and_rejects_stale_raw(self):
        runtime = self.runtime()
        import runpy
        viewer = runpy.run_path(str(ROOT / 'authoring/scripts/verification_results.py'))
        state = runtime.begin(self.root, self.project, 'change')
        for feature in ('api', 'cli'):
            state = self.review(runtime, state, feature)
        self.write('src/api.py', 'price = 11\n')
        command = [sys.executable, '-c', "import json,runpy; from pathlib import Path; Path('.work/raw.json').write_text(json.dumps({'cases':[runpy.run_path('src/api.py')['price']], 'skipped':0}))"]
        self.project['commands']['check']['argv'] = command
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
                {'pointer': '/cases', 'min_count': 1}, {'pointer': '/cases/0', 'equals': 11},
                {'pointer': '/skipped', 'equals': 0}]}]}]}
        path = self.write('.work/plan.json', json.dumps(plan))
        outcome = viewer['execute_plan'](path, run_check_path=ROOT / 'scripts/run_check.py', evidence_dir=self.root / '.work/run')
        self.assertEqual(outcome['status'], 'PASS', outcome)
        bundle = self.write('.work/bundle.json', json.dumps(outcome['execution']['bundle']))
        state['reviews']['api']['bundle'] = bundle.relative_to(self.root).as_posix()
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'READY_FOR_REVIEW')
        self.write('.work/raw.json', '{"cases": [999], "skipped": 0}')
        self.assertEqual(runtime.inspect_project(self.root, self.project, state)['status'], 'PARTIAL')


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
