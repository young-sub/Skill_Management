import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "authoring" / "scripts" / "verification_results.py"
RUN_CHECK = ROOT / "scripts" / "run_check.py"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VerificationExecutionTests(unittest.TestCase):
    def test_direct_lookup_remeasures_untracked_inputs_without_reexecution(self):
        pending = self.project / 'pending.txt'
        (self.project / 'check.py').write_text(
            "import json\nfrom pathlib import Path\n"
            "Path('result.json').write_text(json.dumps({'checks': [{'sum': "
            "int(Path('pending.txt').read_text()), 'readback': 'ok'}]}))\n")
        self._git('add', 'check.py')
        self._git('commit', '-qm', 'consume a new project input')
        pending.write_text('5')
        _, executed = self._execute(self._plan())
        self.assertEqual(executed['status'], 'PASS', executed)
        bundle = executed['bundle']
        argv = [sys.executable, str(VIEWER), '--plan', bundle['plan'],
                '--current-context', str(self.evidence / 'current-context.json')]
        for key, flag in (('records', '--record'), ('assessments', '--assessment')):
            for path in bundle[key]:
                argv.extend([flag, path])

        def lookup():
            process = subprocess.run(argv, capture_output=True, text=True, check=False)
            return json.loads(process.stdout)

        self.assertEqual(lookup()['status'], 'PASS')
        evidence = {path: path.read_bytes() for path in self.evidence.rglob('*') if path.is_file()}
        raw = (self.project / 'result.json').read_bytes()
        before_status = self._git('status', '--porcelain')
        pending.write_text('6')
        self.assertEqual(before_status, self._git('status', '--porcelain'))
        stale = lookup()
        self.assertEqual(stale['items'][0]['historical_status'], 'PASS')
        self.assertEqual(stale['items'][0]['current_reuse'], 'STALE', stale)
        self.assertIn('condition_mismatch:current.source.untracked', stale['items'][0]['reasons'])
        self.assertEqual(stale['test_commands_executed'], 0)
        self.assertEqual(raw, (self.project / 'result.json').read_bytes())
        self.assertEqual(evidence, {path: path.read_bytes() for path in self.evidence.rglob('*') if path.is_file()})
        pending.write_text('5')
        self.assertEqual(lookup()['status'], 'PASS')
        (self.project / '.env').write_text('synthetic-private-value')
        unavailable = lookup()
        self.assertNotEqual(unavailable['status'], 'PASS')
        self.assertNotIn('synthetic-private-value', json.dumps(unavailable))

    def test_bundle_lookup_rejects_source_change_during_observation(self):
        pending = self.project / 'pending.txt'
        pending.write_text('original untracked bytes')
        plan = self._plan()
        _, executed = self._execute(plan)
        viewer = self._viewer_module()
        self.assertEqual(viewer.view_bundle(executed['bundle'], include_scope=False)['items'][0]['current_status'], 'PASS')
        observe = viewer._bundle_current_context
        for changed in (self.project / 'check.py', pending):
            original = changed.read_bytes()
            def interrupted(*args, **kwargs):
                result = observe(*args, **kwargs)
                changed.write_bytes(original + b'\n# changed during lookup\n')
                return result
            try:
                with self.subTest(changed=changed.name), patch.object(viewer, '_bundle_current_context', interrupted):
                    result = viewer.view_bundle(executed['bundle'], include_scope=False)
                    self.assertEqual(result['items'][0]['current_reuse'], 'STALE')
                    self.assertNotEqual(result['items'][0]['current_status'], 'PASS')
                    self.assertEqual(result['test_commands_executed'], 0)
            finally:
                changed.write_bytes(original)

    def test_source_observation_cache_keeps_command_and_record_cwds_distinct(self):
        import copy

        nested = self.project / 'nested'
        nested.mkdir()
        plan = json.loads(self._plan().read_text(encoding='utf-8'))
        plan['checks'][0]['raw_observations'][0]['sha256'] = '0' * 64
        second = copy.deepcopy(plan['checks'][0])
        second['feature_id'] = 'nested-product'
        second['id'] = 'nested-readback'
        second['conditions']['command']['cwd'] = str(nested)
        plan['checks'].append(second)
        viewer = self._viewer_module()

        with patch.object(viewer, '_git_snapshot', wraps=viewer._git_snapshot) as snapshots:
            viewer._bundle_current_context(plan)

        self.assertEqual(
            {call.args[0] for call in snapshots.call_args_list},
            {self.project.resolve(), nested.resolve()},
            'A command cwd under the same repository still needs its own Git observation',
        )

        # A capture may name a cwd different from the check command cwd. The
        # item-level current-source check must not reuse the other cwd's diff.
        cache = {self.project.resolve(): viewer._git_snapshot(self.project)}
        identity = viewer._current_source_identity(nested, cache)
        self.assertEqual(identity['revision'], cache[self.project.resolve()]['revision'])
        self.assertEqual(set(cache), {self.project.resolve(), nested.resolve()})

    def test_project_lookup_shares_bundle_observation_and_remeasures_next_call(self):
        import copy
        root = self.project
        (root / '.gitignore').write_text('result.json\n.work/\n')
        (root / 'criterion.md').write_text('The captured sum is five.\n')
        self._git('add', '-A')
        self._git('commit', '-qm', 'declared shared native observation')
        workflow_spec = importlib.util.spec_from_file_location('workflow_shared_bundle', VIEWER.with_name('project_workflow.py'))
        workflow = importlib.util.module_from_spec(workflow_spec)
        workflow_spec.loader.exec_module(workflow)
        feature = {'id':'fixture-product','partition':'sum','sources':['check.py'],
                   'map':['criterion.md'],'criteria':['criterion.md'],'checks':['arithmetic-readback'],
                   'coverage':[{'id':'sum','requirement':'criterion.md','outcome':'Captured sum',
                                'perspectives':['business'],'areas':['Domain'],'kind':'test','check':'arithmetic-readback'}]}
        project = {'commands':{'arithmetic-readback':[sys.executable,str(root/'check.py')]},
                   'extensions':{'workflow':{'roots':['check.py'],'features':[
                       feature, dict(feature,id='second-feature')]}}}
        (root/'.harness').mkdir()
        (root/'.harness/project.yaml').write_text(json.dumps(project))
        self._git('add','-A')
        self._git('commit','-qm','shared result scope declarations')
        state = workflow.begin(root,project,'change',['fixture-product','second-feature'])
        plan_path = self._plan()
        plan = json.loads(plan_path.read_text())
        other = copy.deepcopy(plan['checks'][0])
        other['feature_id'] = 'second-feature'
        other['raw_observations'][0]['assertions'][0]['equals'] = 6
        plan['checks'].append(other)
        plan_path.write_text(json.dumps(plan))
        evidence = root/'.work/evidence'
        _, executed = self._execute(plan_path,evidence_dir=evidence)
        self.assertEqual(executed['test_commands_executed'],1)
        bundle = '.work/evidence/bundle.json'
        state['results'] = {name:[bundle] for name in ('fixture-product','second-feature')}
        viewer = self._viewer_module()
        with patch.object(viewer,'view_bundle',wraps=viewer.view_bundle) as observed:
            with patch.dict(sys.modules, {'verification_results': viewer}):
                git_commands = []
                original_check_output = viewer.subprocess.check_output
                def count_git(command,*args,**kwargs):
                    if isinstance(command,(list,tuple)) and command and command[0]=='git':
                        git_commands.append(list(command))
                    return original_check_output(command,*args,**kwargs)
                with patch.object(viewer.subprocess,'check_output',side_effect=count_git), \
                        patch.object(viewer,'_git_snapshot',wraps=viewer._git_snapshot) as snapshots:
                    current = workflow.inspect_project(root,project,state)
                    self.assertEqual(snapshots.call_count,2,'One lookup shares a snapshot and checks it again before returning')
                self.assertEqual(len(git_commands),10,'Source checks are bounded by cwd, not consumer count')
                self.assertEqual(observed.call_count,1,'One lookup must not assess the same native bundle per consumer')
                self.assertEqual([f['check_results'][0]['current_status'] for f in current['features']],['PASS','ISSUES'])
                original = (root/'result.json').read_bytes()
                (root/'result.json').write_text(json.dumps({'checks':[{'sum':7,'readback':'ok'}]}))
                changed = workflow.inspect_project(root,project,state)
                self.assertEqual(observed.call_count,2,'A later lookup must observe changed raw bytes again')
                self.assertTrue(all(f['check_results'][0]['current_status']!='PASS' for f in changed['features']))
                (root/'result.json').write_bytes(original)
                criteria = root/'criterion.md'
                original_criteria = criteria.read_bytes()
                criteria.write_text('The captured sum must be six.\n')
                tracked_source_change = workflow.inspect_project(root,project,state)
                self.assertTrue(all(f['check_results'][0]['current_status']!='PASS'
                                    for f in tracked_source_change['features']),
                                'A fresh lookup must invalidate evidence after tracked source changes')
                criteria.write_bytes(original_criteria)
                untracked = root/'lookup-source-probe.py'
                untracked.write_text('marker = True\n')
                untracked_source_change = workflow.inspect_project(root,project,state)
                self.assertTrue(all(f['check_results'][0]['current_status']!='PASS'
                                    for f in untracked_source_change['features']),
                                'A fresh lookup must invalidate evidence after untracked source changes')
                untracked.unlink()
                cache = {}
                rejected = workflow.inspect_evidence(root,feature,{'arithmetic-readback':['must-not-run']},bundle,bundle_cache=cache)
                accepted = workflow.inspect_evidence(root,feature,project['commands'],bundle,bundle_cache=cache)
                self.assertEqual(next(i for i in rejected['items'] if i['feature']==feature['id'])['current_status'],'BLOCKED')
                self.assertEqual(next(i for i in accepted['items'] if i['feature']==feature['id'])['current_status'],'PASS',
                                 'One consumer cannot mutate the shared native observation for another assessment')
        state_path = root/'.work/state.json'
        state_path.write_text(json.dumps(state))
        scope = {'root':str(root),'state':'.work/state.json','features':project['extensions']['workflow']['features'],
                 'bases':{f['id']:f['basis'] for f in current['features']}}
        reusable = copy.deepcopy(executed['items'])
        for item in reusable:
            item['selected'] = False
            item['selection'] = {'status':'not_required','reason':'current_evidence_reusable'}
        with patch.object(viewer,'view_bundle',wraps=viewer.view_bundle) as observed:
            with patch.dict(sys.modules, {'verification_results': viewer}):
                coverage = viewer._view_coverage({'workflow_scope':scope},reusable)
                self.assertEqual(observed.call_count,1,'One scope observation must not reopen the same reused native bundle per Feature')
                self.assertEqual([r['status'] for r in coverage['rows']],['PASS','ISSUES'])
                (root/'result.json').write_text(json.dumps({'checks':[{'sum':7,'readback':'ok'}]}))
                changed = viewer._view_coverage({'workflow_scope':scope},reusable)
                self.assertEqual(observed.call_count,2,'The next scope observation must remeasure changed raw')
                self.assertTrue(all(r['status']!='PASS' for r in changed['rows']))

    def test_registered_source_scope_invalidates_only_affected_check_and_reruns_it(self):
        import runpy

        api = runpy.run_path(str(VIEWER))
        workflow = runpy.run_path(str(VIEWER.with_name('project_workflow.py')))
        root = self.project
        (root / '.gitignore').write_text('.work/\n__pycache__/\n')
        for directory in ('src/a', 'src/b', 'shared', 'criteria', '.harness'):
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / 'src/a/logic.py').write_text("VALUE = 'A'\n")
        (root / 'src/b/logic.py').write_text("VALUE = 'B'\n")
        (root / 'shared/theme.css').write_text(':root { --gap: 8px; }\n')
        (root / 'shared/button.js').write_text('export const button = true;\n')
        (root / 'criteria/a.md').write_text('Feature A keeps its observed value.\n')
        (root / 'criteria/b.md').write_text('Feature B keeps its observed value.\n')
        (root / 'criteria/ui.md').write_text('Shared controls follow this guide.\n')
        (root / 'unrelated.txt').write_text('outside registered source roots\n')
        for name in ('a', 'b'):
            (root / f'check_{name}.py').write_text(
                "import json, runpy, sys\nfrom pathlib import Path\n"
                f"value = runpy.run_path('src/{name}/logic.py')['VALUE']\n"
                f"counter = Path('.work/calls-{name}')\n"
                "counter.parent.mkdir(exist_ok=True)\n"
                "counter.write_text(str(int(counter.read_text()) + 1) if counter.exists() else '1')\n"
                "report = Path(sys.argv[1])\nreport.parent.mkdir(parents=True, exist_ok=True)\n"
                "report.write_text(json.dumps({'checks': [{'value': value}]}))\n")
        features = []
        checks = []
        for name, letter in (('a', 'A'), ('b', 'B')):
            feature_id, check_id = f'feature-{name}', f'check-{name}'
            criterion = f'criteria/{name}.md'
            features.append({'id': feature_id, 'partition': feature_id, 'sources': [f'src/{name}/*.py'],
                             'map': [criterion], 'criteria': [criterion], 'checks': [check_id]})
            checks.append({'id': check_id, 'feature_id': feature_id, 'expected': f'{letter} remains observable',
                'required': True, 'selection': {'status': 'selected', 'reason': 'changed behavior'},
                'source_scope': 'registered',
                'dependency': {'file_refs': [f'check_{name}.py']}, 'fixture': {'file_refs': [criterion]},
                'raw_observations': [{'path': f'{{report_dir}}/{name}.json', 'pointer': '/checks/0',
                    'assertions': [{'pointer': '/checks/0/value', 'equals': letter}]}]})
        project_config = {'commands': {f'check-{name}': [sys.executable, f'check_{name}.py', f'{{report_dir}}/{name}.json']
                                        for name in ('a', 'b')},
            'extensions': {'workflow': {'roots': ['src', 'shared'], 'assertions': 'assertions.json',
                'features': features, 'ui_systems': {'shared-controls': {'guide': 'criteria/ui.md',
                    'tokens': ['shared/*.css'], 'components': ['shared/*.js'], 'consumers': ['feature-a']}}}}}
        (root / '.harness/project.yaml').write_text(json.dumps(project_config))
        (root / 'assertions.json').write_text(json.dumps({'schema_version': 1, 'checks': checks}))
        self._git('add', '-A')
        self._git('commit', '-qm', 'registered source scope fixture')

        state = workflow['begin'](root, project_config, 'change', ['feature-a', 'feature-b'])
        state_path = root / '.work/task.json'
        state_path.parent.mkdir(parents=True)
        state_path.write_text(json.dumps(state))

        def prepare(name):
            output = root / f'.work/{name}/plan.json'
            output.parent.mkdir(parents=True, exist_ok=True)
            prepared = api['prepare_plan'](root, None, output, report_dir=output.parent / 'native',
                                           pending_state=state_path.relative_to(root))
            return output, prepared

        plan, prepared = prepare('initial')
        self.assertEqual({(row['feature'], row['check']) for row in prepared['selected_checks']},
                         {('feature-a', 'check-a'), ('feature-b', 'check-b')})
        (root / 'unrelated.txt').write_text('unrelated edit between preparation and execution\n')
        initial = api['execute_plan'](plan, run_check_path=RUN_CHECK, evidence_dir=root / '.work/initial/evidence')
        self.assertEqual(initial['status'], 'PASS', initial)
        self.assertEqual(initial['test_commands_executed'], 2)
        bundle = initial['execution']['bundle_path']
        bundle_descriptor = json.loads(Path(bundle).read_text(encoding='utf-8'))
        stale_context = json.loads(Path(bundle_descriptor['current_context']).read_text(encoding='utf-8'))

        def direct_lookup():
            return api['view_results'](bundle_descriptor['plan'],
                record_paths=bundle_descriptor['records'], assessment_paths=bundle_descriptor['assessments'],
                current_context=stale_context, include_scope=False)

        def assert_source_scope(expected_a):
            current = api['view_bundle'](bundle)
            by_feature = {item['feature']: item for item in current['items']}
            self.assertEqual(by_feature['feature-a']['current_reuse'], expected_a, current)
            self.assertEqual(by_feature['feature-b']['current_reuse'], 'REUSABLE', current)
            direct = direct_lookup()
            direct_by_feature = {item['feature']: item for item in direct['items']}
            self.assertEqual(direct_by_feature['feature-a']['current_reuse'], expected_a, direct)
            self.assertEqual(direct_by_feature['feature-b']['current_reuse'], 'REUSABLE', direct)

        (root / 'unrelated.txt').write_text('later unrelated edit outside registered sources\n')
        unaffected = api['view_bundle'](bundle)
        self.assertEqual({(item['feature'], item['current_status'], item['current_reuse'])
                          for item in unaffected['items']},
                         {('feature-a', 'PASS', 'REUSABLE'), ('feature-b', 'PASS', 'REUSABLE')})
        self.assertEqual(unaffected['test_commands_executed'], 0)
        direct_unaffected = direct_lookup()
        self.assertTrue(all(item['current_reuse'] == 'REUSABLE' for item in direct_unaffected['items']),
                        direct_unaffected)

        a_source = root / 'src/a/logic.py'
        a_original = a_source.read_bytes()
        a_source.write_text("VALUE = 'A'  # scoped edit\n")
        assert_source_scope('STALE')
        a_source.write_bytes(a_original)
        assert_source_scope('REUSABLE')

        shared_css = root / 'shared/theme.css'
        css_original = shared_css.read_bytes()
        shared_css.write_text(':root { --gap: 12px; }\n')
        assert_source_scope('STALE')
        shared_css.write_bytes(css_original)
        assert_source_scope('REUSABLE')

        new_source = root / 'src/a/new module.py'
        new_source.write_text("VALUE = 'new source under the registered glob'\n")
        assert_source_scope('STALE')
        new_source.unlink()
        assert_source_scope('REUSABLE')

        a_source.unlink()
        assert_source_scope('STALE')
        a_source.write_bytes(a_original)
        assert_source_scope('REUSABLE')

        a_source.write_text("VALUE = 'A'  # final source edit\n")
        shared_css.write_text(':root { --gap: 12px; }\n')
        new_source.write_text("VALUE = 'new source under the registered glob'\n")
        audited = workflow['inspect_project'](root, project_config, json.loads(state_path.read_text()))
        by_feature = {feature['id']: feature for feature in audited['features']}
        self.assertEqual(by_feature['feature-a']['check_results'][0]['current_reuse'], 'STALE')
        self.assertEqual(by_feature['feature-b']['check_results'][0]['current_status'], 'PASS')

        rerun_plan, rerun_prepared = prepare('rerun-a')
        self.assertEqual(rerun_prepared['selected_checks'], [{'feature': 'feature-a', 'check': 'check-a'}])
        rerun = api['execute_plan'](rerun_plan, run_check_path=RUN_CHECK, evidence_dir=root / '.work/rerun-a/evidence')
        self.assertEqual(rerun['status'], 'PASS', rerun)
        self.assertEqual(rerun['test_commands_executed'], 1)
        self.assertEqual((root / '.work/calls-a').read_text(), '2')
        self.assertEqual((root / '.work/calls-b').read_text(), '1')
        final = workflow['inspect_project'](root, project_config, json.loads(state_path.read_text()))
        self.assertTrue(all(feature['verification_status'] == 'PASS' for feature in final['features']), final)

    def test_registered_shared_check_binds_union_and_runs_once(self):
        import runpy

        api = runpy.run_path(str(VIEWER))
        root = self.project
        (root / '.gitignore').write_text('.work/\n__pycache__/\n')
        for directory in ('src/a', 'src/b', 'criteria', '.harness'):
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / 'src/a/logic.py').write_text("VALUE = 1\n")
        (root / 'src/b/logic.py').write_text("VALUE = 2\n")
        (root / 'criteria/shared.md').write_text('Both Features share this observed requirement.\n')
        (root / 'check_shared.py').write_text(
            "import json, runpy, sys\nfrom pathlib import Path\n"
            "total = runpy.run_path('src/a/logic.py')['VALUE'] + runpy.run_path('src/b/logic.py')['VALUE']\n"
            "counter = Path('.work/shared-calls')\ncounter.parent.mkdir(exist_ok=True)\n"
            "counter.write_text(str(int(counter.read_text()) + 1) if counter.exists() else '1')\n"
            "report = Path(sys.argv[1])\nreport.parent.mkdir(parents=True, exist_ok=True)\n"
            "report.write_text(json.dumps({'checks': [{'sum': total}]}))\n")
        features = [
            {'id': 'feature-a', 'partition': 'feature-a', 'sources': ['src/a/*.py'],
             'map': ['criteria/shared.md'], 'criteria': ['criteria/shared.md'], 'checks': ['shared-readback']},
            {'id': 'feature-b', 'partition': 'feature-b', 'sources': ['src/b/*.py'],
             'map': ['criteria/shared.md'], 'criteria': ['criteria/shared.md'], 'checks': ['shared-readback']},
        ]
        project = {'commands': {'shared-readback': [sys.executable, 'check_shared.py', '{report_dir}/shared.json']},
            'extensions': {'workflow': {'roots': ['src'], 'assertions': 'assertions.json', 'features': features}}}
        checks = [{'id': 'shared-readback', 'feature_id': feature['id'], 'expected': 'Both inputs total three',
            'required': True, 'selection': {'status': 'selected', 'reason': 'Shared behavior changed'},
            'source_scope': 'registered', 'dependency': {'file_refs': ['check_shared.py']},
            'fixture': {'file_refs': ['criteria/shared.md']},
            'raw_observations': [{'path': '{report_dir}/shared.json', 'pointer': '/checks/0',
                'assertions': [{'pointer': '/checks/0/sum', 'equals': 3}]}]} for feature in features]
        (root / '.harness/project.yaml').write_text(json.dumps(project))
        (root / 'assertions.json').write_text(json.dumps({'schema_version': 1, 'checks': checks}))
        self._git('add', '-A')
        self._git('commit', '-qm', 'registered shared producer source scope fixture')

        plan = root / '.work/shared/plan.json'
        plan.parent.mkdir(parents=True)
        patch_snapshot = Mock(wraps=api['_git_snapshot'])
        with patch.dict(api['prepare_plan'].__globals__, _git_snapshot=patch_snapshot):
            prepared = api['prepare_plan'](root, None, plan, report_dir=plan.parent / 'native')
        self.assertEqual(patch_snapshot.call_count, 2,
                         'Shared consumers reuse preparation and independently recheck before publication')
        self.assertEqual(prepared['status'], 'PREPARED', prepared)
        planned = json.loads(plan.read_text(encoding='utf-8'))
        self.assertEqual([check['conditions']['source']['file_patterns'] for check in planned['checks']],
                         [['src/a/*.py', 'src/b/*.py'], ['src/a/*.py', 'src/b/*.py']])
        result = api['execute_plan'](plan, run_check_path=RUN_CHECK, evidence_dir=plan.parent / 'evidence')
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['test_commands_executed'], 1)
        record = json.loads(Path(result['execution']['bundle']['records'][0]).read_text(encoding='utf-8'))
        self.assertEqual(record['shared_features'], ['feature-a', 'feature-b'])
        self.assertEqual((root / '.work/shared-calls').read_text(), '1')

        (root / 'src/b/logic.py').write_text("VALUE = 3  # consumed by the shared producer\n")
        current = api['view_bundle'](result['execution']['bundle_path'])
        self.assertEqual({item['feature']: item['current_reuse'] for item in current['items']},
                         {'feature-a': 'STALE', 'feature-b': 'STALE'}, current)
        self.assertEqual((root / '.work/shared-calls').read_text(), '1', 'lookup must not rerun checks')
        preflight = api['_preflight_execution']
        def change_before_preflight(*args, **kwargs):
            (root / 'src/b/logic.py').write_text('VALUE = 4\n')
            return preflight(*args, **kwargs)
        next_plan = root / '.work/changed/plan.json'
        with patch.dict(api['prepare_plan'].__globals__, _preflight_execution=change_before_preflight):
            with self.assertRaisesRegex(ValueError, 'pre-run source.file_hashes'):
                api['prepare_plan'](root, None, next_plan, report_dir=next_plan.parent / 'native')
        self.assertFalse(next_plan.exists(), 'Preparation cache cannot hide a later source edit')

    def test_native_unobserved_or_skipped_cases_are_not_product_assertion_failures(self):
        (self.project / '.gitignore').write_text('result.json\n.work/\n')
        self._git('add', '.gitignore')
        self._git('commit', '-qm', 'isolated native reports')
        for index, status in enumerate(('BLOCKED', 'SKIP', 'NOT_RUN', 'ERROR')):
            with self.subTest(status=status):
                child = self.root / f'unobserved-{index}.py'
                report = f'.work/native-{index}.json'
                child.write_text("import json\nfrom pathlib import Path\n"
                    "p=Path(" + repr(report) + ");p.parent.mkdir(parents=True,exist_ok=True)\n"
                    "p.write_text(json.dumps({'status':" + repr(status) + ", 'checks':[{'count':0,'skipped':1}]}))\n")
                plan = self._plan(child=child, report=report)
                _, result = self._execute(plan, evidence_dir=self.root / f'evidence-{index}')
                expected = status if status != 'ERROR' else 'UNKNOWN'
                self.assertEqual(result['items'][0]['historical_status'], expected, result)
                self.assertNotEqual(result['items'][0]['assessment']['status'], 'ISSUES',
                                    'Missing/blocked observations cannot be labeled a business assertion failure')

    def test_installed_runtime_files_are_measured_and_drift_invalidates_reuse(self):
        installed = self.root / 'browser-runtime.bin'
        installed.write_bytes(b'public installed runtime v1')
        plan_path = self._plan()
        plan = json.loads(plan_path.read_text())
        plan['checks'][0]['conditions']['dependency']['installed_file_refs'] = [str(installed)]
        plan_path.write_text(json.dumps(plan))
        _, result = self._execute(plan_path)
        self.assertEqual(result['status'], 'PASS', result)
        hashes = result['items'][0]['conditions']['expected']['dependency']['file_hashes']
        self.assertIn(str(installed), hashes, 'Installed browser/library inputs need live identity, not a historical label')
        installed.write_bytes(b'public installed runtime v2')
        module = self._viewer_module()
        before = plan_path.read_bytes()
        current = module.view_bundle(result['execution']['bundle_path'])
        self.assertEqual(current['items'][0]['current_reuse'], 'STALE', current)
        self.assertEqual(current['test_commands_executed'], 0)
        self.assertEqual(before, plan_path.read_bytes())
        for bad in ('relative.dll', str(self.root / 'auth.json'), str(self.root / 'missing.dll')):
            with self.subTest(bad=bad):
                plan['checks'][0]['conditions']['dependency']['installed_file_refs'] = [bad]
                with self.assertRaises(module.ViewerInputError):
                    module._execution_conditions(plan['checks'][0], self.project)

    def test_registered_task_selection_executes_only_pending_and_binds_without_semantic_pass(self, exclude=False, partial=False, replace_task=False, work_id=False):
        import copy
        import runpy
        api = runpy.run_path(str(VIEWER))
        workflow = runpy.run_path(str(VIEWER.with_name('project_workflow.py')))
        original = json.loads(self._plan().read_text())['checks'][0]
        (self.project / '.gitignore').write_text('.work/\n__pycache__/\n')
        (self.project / 'check.py').write_text(
            "import json,sys\nfrom pathlib import Path\n"
            "p=Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True)\n"
            "p.write_text(json.dumps({'checks':[{'sum':5,'readback':'ok'}]}))\n"
            "count=Path('.work/calls');count.write_text(str(int(count.read_text())+1) if count.exists() else '1')\n")
        feature = {'id': 'fixture-product', 'partition': 'orders', 'sources': ['check.py'],
                   'map': ['fixture.json'], 'criteria': ['fixture.json'], 'checks': ['arithmetic-readback'],
                   'coverage': [{'id': 'sum', 'requirement': 'fixture.json', 'outcome': 'Saved sum',
                                 'perspectives': ['business'], 'areas': ['Domain'], 'kind': 'test', 'check': 'arithmetic-readback'},
                                {'id': 'owner', 'requirement': 'fixture.json', 'outcome': 'Single owner',
                                 'perspectives': ['architecture'], 'areas': ['Domain'], 'kind': 'review'}]}
        untouched = dict(feature, id='untouched', sources=['dependency.txt'], checks=['unneeded'], coverage=[])
        config = {'commands': {'arithmetic-readback': [sys.executable, 'check.py', '{report_dir}/result.json'],
                               'unneeded': [sys.executable, 'must_not_run.py', '{report_dir}/unused.json']},
                  'extensions': {'workflow': {'roots': ['check.py', 'dependency.txt'], 'features': [feature, untouched],
                                              'assertions': 'assertions.json'}}}
        (self.project / '.harness').mkdir()
        (self.project / '.harness/project.yaml').write_text(json.dumps(config))
        item = {k: original[k] for k in ('id', 'feature_id', 'expected', 'required', 'selection', 'raw_observations')}
        item['raw_observations'][0]['path'] = '{report_dir}/result.json'
        item.update(dependency={'file_refs': ['dependency.txt']}, fixture={'file_refs': ['fixture.json']})
        unused = copy.deepcopy(item)
        unused.update(id='unneeded', feature_id='untouched')
        unused['raw_observations'][0]['path'] = '{report_dir}/unused.json'
        if exclude:
            feature['checks'].append('unneeded')
            feature['coverage'].append({'id': 'unused', 'requirement': 'fixture.json', 'outcome': 'Other scenario',
                                       'perspectives': ['business'], 'areas': ['Domain'], 'kind': 'test', 'check': 'unneeded'})
            unused['feature_id'] = feature['id']
            (self.project / '.harness/project.yaml').write_text(json.dumps(config))
        specifications = [item, unused]
        if partial:
            feature['checks'].append('extra')
            feature['coverage'].append(dict(feature['coverage'][0], id='extra', check='extra'))
            config['commands']['extra'] = [sys.executable, 'check.py', '{report_dir}/extra.json']
            extra = copy.deepcopy(item)
            extra['id'] = 'extra'
            extra['raw_observations'][0]['path'] = '{report_dir}/extra.json'
            specifications.append(extra)
            (self.project / '.harness/project.yaml').write_text(json.dumps(config))
        (self.project / 'assertions.json').write_text(json.dumps({'schema_version': 1, 'checks': specifications}))
        state = workflow['begin'](self.project, config, 'change')
        with (self.project / 'check.py').open('a') as stream:
            stream.write('# changed behavior\n')
        if exclude:
            basis = workflow['inspect_project'](self.project, config, state)['features'][0]['basis']
            state = workflow['record_review'](self.project, config, state, {
                'feature': feature['id'], 'basis': basis, 'analysis': 'Other scenario is unchanged',
                'references': ['check.py'], 'findings': ['Semantic review is pending'],
                'scope_reviews': {'unused': {'status': 'NOT_REQUIRED', 'reason': 'No change to other scenario',
                                             'analysis': 'Independent scenario', 'references': ['check.py']}}})
        (self.project / '.work').mkdir(exist_ok=True)
        state_path = self.project / '.work/task.json'
        state_path.write_text(json.dumps(state))
        command = [sys.executable, str(VIEWER), '--prepare', '--root', str(self.project),
                   '--pending-state', '.work/task.json', '--plan-output', '.work/run/plan.json', '--report-dir', '.work/run/native']
        if work_id:
            directory = self.project / '.work/goals/active/W-NATIVE'
            directory.mkdir(parents=True)
            (directory / 'work.json').write_text(json.dumps({'work_id': 'W-NATIVE', 'state': 'active',
                                                            'source_commit': state['base'], 'workflow_baseline': state}))
            state_path = directory / 'workflow.json'
            command[command.index('--pending-state'):command.index('--pending-state') + 2] = ['--work-id', 'W-NATIVE']
        prepared = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        selection = json.loads(prepared.stdout)
        self.assertEqual(selection['selected_checks'], [{'feature': 'fixture-product', 'check': name}
                                                      for name in (['arithmetic-readback', 'extra'] if partial else ['arithmetic-readback'])])
        plan = self.project / '.work/run/plan.json'
        self.assertNotIn('untouched', [f['id'] for f in json.loads(plan.read_text())['workflow_scope']['features']],
                         'Task preparation must stay within affected Features')
        if replace_task:
            replacement = workflow['begin'](self.project, config, 'change', ['fixture-product'])
            state_path.write_text(json.dumps(replacement))
        result = api['execute_plan'](plan, run_check_path=RUN_CHECK, evidence_dir=self.project / '.work/run/evidence')
        if replace_task:
            self.assertEqual(result['status'], 'BLOCKED', result)
            self.assertEqual(result['test_commands_executed'], 0)
            self.assertFalse((self.project / '.work/calls').exists())
            return
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['test_commands_executed'], 2 if partial else 1)
        current = workflow['inspect_project'](self.project, config, json.loads(state_path.read_text()))
        self.assertEqual(current['features'][0]['verification_status'], 'PASS')
        self.assertFalse(current['features'][0]['reviewed'])
        self.assertEqual(current['coverage']['rows'][0]['status'], 'PASS')
        self.assertEqual(current['coverage']['rows'][1]['status'], 'NOT_RUN')
        before = state_path.read_bytes()
        looked_up = api['view_bundle'](result['execution']['bundle_path'])
        resumed = api['execute_plan'](plan, run_check_path=RUN_CHECK, evidence_dir=self.project / '.work/run/evidence', resume=True)
        self.assertEqual(looked_up['test_commands_executed'], 0)
        self.assertEqual(resumed['test_commands_executed'], 0)
        self.assertEqual((self.project / '.work/calls').read_text(), '2' if partial else '1')
        self.assertEqual(state_path.read_bytes(), before)
        command[command.index('--plan-output') + 1] = '.work/reused/plan.json'
        command[command.index('--report-dir') + 1] = '.work/reused/native'
        reused = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(reused.returncode, 0, reused.stdout + reused.stderr)
        self.assertEqual(json.loads(reused.stdout)['status'], 'NOT_REQUIRED')
        self.assertFalse((self.project / '.work/reused/plan.json').exists())
        if partial:
            (self.project / '.work/run/native/extra.json').write_text('{"checks":[]}')
            command[command.index('--plan-output') + 1] = '.work/repair/plan.json'
            command[command.index('--report-dir') + 1] = '.work/repair/native'
            prepared = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
            self.assertEqual(json.loads(prepared.stdout)['selected_checks'], [{'feature': 'fixture-product', 'check': 'extra'}])
            repaired = api['execute_plan'](self.project / '.work/repair/plan.json', run_check_path=RUN_CHECK,
                                            evidence_dir=self.project / '.work/repair/evidence')
            self.assertEqual(repaired['test_commands_executed'], 1)
            self.assertEqual((self.project / '.work/calls').read_text(), '3')
            observed = api['view_bundle'](repaired['execution']['bundle_path'])
            self.assertEqual(observed['coverage']['rows'][0]['status'], 'PASS', observed)
            current = workflow['inspect_project'](self.project, config, json.loads(state_path.read_text()))
            self.assertEqual(current['features'][0]['verification_status'], 'PASS', current)

    def test_task_exclusion_is_explained_and_never_executed(self):
        self.test_registered_task_selection_executes_only_pending_and_binds_without_semantic_pass(exclude=True)

    def test_partial_result_reuse_reexecutes_only_unavailable_check(self):
        self.test_registered_task_selection_executes_only_pending_and_binds_without_semantic_pass(partial=True)

    def test_task_state_replacement_refuses_prepared_execution(self):
        self.test_registered_task_selection_executes_only_pending_and_binds_without_semantic_pass(replace_task=True)

    def test_native_task_execution_uses_harness_baseline_without_review_file(self):
        self.test_registered_task_selection_executes_only_pending_and_binds_without_semantic_pass(work_id=True)

    def test_registered_report_directory_runs_twice_without_configuration_edits(self, subdirectory=False, coverage=False, semantic=False, semantic_after=False):
        api = __import__('runpy').run_path(str(VIEWER))
        workflow = __import__('runpy').run_path(str(VIEWER.with_name('project_workflow.py')))
        original = json.loads(self._plan().read_text())['checks'][0]
        (self.project / '.gitignore').write_text('.work/\n__pycache__/\n')
        (self.project / 'check.py').write_text(
            "import json,sys\nfrom pathlib import Path\n"
            "target=Path(sys.argv[1]); target.parent.mkdir(parents=True,exist_ok=True)\n"
            "target.write_text(json.dumps({'checks':[{'sum':5,'readback':'ok'}]}))\n")
        feature = {'id': 'fixture-product', 'partition': 'domain', 'sources': ['check.py'],
                   'map': ['fixture.json'], 'criteria': ['fixture.json'], 'checks': ['arithmetic-readback']}
        if coverage:
            feature['coverage'] = [
                {'id': 'sum', 'requirement': 'fixture.json', 'outcome': 'Correct arithmetic readback',
                 'perspectives': ['business'], 'areas': ['BE/API', 'Domain'],
                 'kind': 'test', 'method': 'cross-layer', 'check': 'arithmetic-readback'},
                {'id': 'ownership', 'requirement': 'fixture.json', 'outcome': 'One state owner',
                 'perspectives': ['architecture'], 'areas': ['Domain'], 'kind': 'review'},
                {'id': 'display', 'requirement': 'fixture.json', 'outcome': 'Display readback',
                 'perspectives': ['business'], 'areas': ['FE'], 'kind': 'test'}]
        command = [sys.executable, 'check.py', '{report_dir}/result.json']
        config = {'commands': {'arithmetic-readback': command},
                  'extensions': {'workflow': {'roots': ['check.py'], 'features': [feature]}}}
        (self.project / '.harness').mkdir()
        config_path = self.project / '.harness/project.yaml'
        config_path.write_text(json.dumps(config))
        item = {k: original[k] for k in ('id', 'feature_id', 'expected', 'required', 'selection', 'raw_observations')}
        item['raw_observations'][0]['path'] = '{report_dir}/result.json'
        item.update(dependency={'file_refs': ['dependency.txt']}, fixture={'file_refs': ['fixture.json']})
        spec = self.project / 'assertions.json'
        spec.write_text(json.dumps({'schema_version': 1, 'checks': [item]}))
        if subdirectory:
            (self.project / 'backend').mkdir()
            for name in ('check.py', 'dependency.txt', 'fixture.json'):
                (self.project / 'backend' / name).write_bytes((self.project / name).read_bytes())
            config['commands']['arithmetic-readback'] = {'argv': command, 'working_directory': 'backend'}
            config_path.write_text(json.dumps(config))
        before = {p: p.read_bytes() for p in (config_path, spec)}
        if semantic:
            state = workflow['begin'](self.project, config, 'init')
            audit = workflow['inspect_project'](self.project, config, state)
            review = {'feature': feature['id'], 'basis': audit['features'][0]['basis'],
                      'analysis': 'Domain owns arithmetic and runner serializes the result', 'references': ['check.py'], 'findings': [],
                      'scope_reviews': {'ownership': {'status': 'PASS', 'analysis': 'No parallel state owner', 'references': ['check.py'],
                          'architecture': {'flows': [{'owner': 'check.py', 'call': 'runner -> arithmetic',
                              'state': 'one result object', 'data': 'sum -> JSON', 'references': ['check.py']}],
                              'boundaries': [{'kind': kind, 'analysis': 'Unchanged runner boundary', 'references': ['check.py']}
                                             for kind in ('contract', 'dependency', 'failure')], 'findings': []}}}}
            state = workflow['record_review'](self.project, config, state, review)
            (self.project / '.work').mkdir(exist_ok=True)
            (self.project / '.work/semantic.json').write_text(json.dumps(state))
        bundles = []
        for name in ('first', 'second'):
            output = self.project / f'.work/{name}/plan.json'
            if name == 'first':
                prepared = subprocess.run([sys.executable, str(VIEWER), '--prepare', str(spec),
                    '--root', str(self.project), '--plan-output', str(output),
                    '--report-dir', f'.work/{name}/native',
                    *(['--workflow-state', '.work/semantic.json'] if semantic and not semantic_after else [])], capture_output=True, text=True)
                self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
                self.assertEqual(json.loads(prepared.stdout)['test_commands_executed'], 0)
            else:
                api['prepare_plan'](self.project, spec, output, report_dir=Path(f'.work/{name}/native'),
                                    workflow_state=Path('.work/semantic.json') if semantic and not semantic_after else None)
            result = api['execute_plan'](output, run_check_path=RUN_CHECK,
                                         evidence_dir=self.project / f'.work/{name}/evidence')
            self.assertEqual(result['status'], 'PASS', result)
            self.assertEqual(result['test_commands_executed'], 1)
            if coverage:
                rows = {row['id']: row for row in result['coverage']['rows']}
                self.assertEqual(rows['sum']['status'], 'PASS')
                self.assertEqual(rows['sum']['areas'], ['BE/API', 'Domain'])
                self.assertEqual(rows['ownership']['status'], 'PASS' if semantic and not semantic_after else 'NOT_RUN')
                self.assertEqual(rows['display']['status'], 'MISSING')
                self.assertEqual(result['coverage']['status'], 'PARTIAL')
                self.assertEqual(rows['sum']['evidence']['run_id'], result['items'][0]['run_id'])
            bundle = result['execution']['bundle_path']
            self.assertEqual(workflow['inspect_evidence'](
                self.project, feature, config['commands'], str(Path(bundle).relative_to(self.project)))['status'], 'PASS')
            bundles.append(bundle)
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        for bundle in bundles:
            looked_up = api['view_bundle'](bundle, **({'workflow_state': Path('.work/semantic.json')} if semantic_after else {}))
            self.assertEqual(looked_up['status'], 'PASS', looked_up)
            self.assertEqual(looked_up['test_commands_executed'], 0)
            if coverage:
                summary = api['summarize_results'](looked_up)
                self.assertEqual(looked_up['coverage']['gaps'], summary['coverage']['gaps'])
                self.assertEqual(looked_up['coverage']['rows'][0]['status'], 'PASS')
                if semantic_after:
                    ownership = next(row for row in looked_up['coverage']['rows'] if row['id'] == 'ownership')
                    self.assertEqual(ownership['historical_status'], 'NOT_RUN')
                    self.assertEqual(ownership['status'], 'PASS')
        if semantic:
            with (self.project / 'check.py').open('a') as stream:
                stream.write('\n# changed owner\n')
            changed = api['view_bundle'](bundles[-1], **({'workflow_state': Path('.work/semantic.json')} if semantic_after else {}))
            semantic_row = next(row for row in changed['coverage']['rows'] if row['id'] == 'ownership')
            self.assertEqual(semantic_row['historical_status'], 'NOT_RUN' if semantic_after else 'PASS')
            self.assertEqual(semantic_row['status'], 'STALE')
        with (self.project / '.gitignore').open('a') as stream:
            stream.write('reports/native-report.json\n')
        with self.assertRaises(ValueError):
            api['prepare_plan'](self.project, spec, self.project / '.work/refused.json',
                                report_dir=Path('reports'))
        self.assertFalse((self.project / '.work/refused.json').exists())
        for directory in (None, Path('tracked-output'), self.root / 'outside', Path('.work/first/native')):
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                api['prepare_plan'](self.project, spec, self.project / '.work/refused.json', report_dir=directory)
        # Only the declared output argument may vary; changing a real argument
        # must not discharge the workflow check with an older captured command.
        changed = {'arithmetic-readback': [sys.executable, 'other.py', '{report_dir}/result.json']}
        self.assertEqual(workflow['inspect_evidence'](self.project, feature, changed,
            str(Path(bundles[-1]).relative_to(self.project)))['status'], 'BLOCKED')
        for invalid in (["{report_dir}/python", 'check.py', '{report_dir}/result.json'],
                        [sys.executable, '{report_dir}/other.py', '{report_dir}/result.json'],
                        [sys.executable, 'check.py', '{report_dir}/../result.json']):
            with self.subTest(command=invalid), self.assertRaises(ValueError):
                config['commands']['arithmetic-readback'] = invalid
                config_path.write_text(json.dumps(config))
                api['prepare_plan'](self.project, spec, self.project / '.work/refused.json',
                                    report_dir=Path('.work/invalid/native'))
            self.assertFalse((self.project / '.work/refused.json').exists())

    def test_report_directory_supports_registered_subdirectory_commands(self):
        self.test_registered_report_directory_runs_twice_without_configuration_edits(subdirectory=True)

    def test_full_stack_scope_survives_prepare_execute_and_lookup(self):
        self.test_registered_report_directory_runs_twice_without_configuration_edits(coverage=True)

    def test_semantic_review_survives_preparation_and_reopens_on_owner_change(self):
        self.test_registered_report_directory_runs_twice_without_configuration_edits(coverage=True, semantic=True)

    def test_semantic_review_can_join_retained_results_without_execution(self):
        self.test_registered_report_directory_runs_twice_without_configuration_edits(coverage=True, semantic=True, semantic_after=True)

    def test_feedback_red_green_normal_and_subsequent_revalidation(self, maintenance=False, bypass=False):
        import runpy
        api = runpy.run_path(str(VIEWER))
        workflow = runpy.run_path(str(VIEWER.with_name('project_workflow.py')))
        original = json.loads(self._plan().read_text())['checks'][0]
        (self.project / '.gitignore').write_text('.work/\n__pycache__/\n')
        (self.project / 'domain.py').write_text('def valid(value):\n    return True\n')
        (self.project / 'check.py').write_text(
            "import json,sys\nfrom pathlib import Path\nfrom domain import valid\n"
            "p=Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True)\n"
            "p.write_text(json.dumps({'checks':[{'rejected':not valid(-1),'normal':valid(0),'alternate':not valid(-2)}]}))\n")
        guardrail = {'failure': 'Negative allowed', 'scope': 'Domain quantities', 'check': 'arithmetic-readback',
                     'normal_exception': 'Zero is valid', 'reconsider': 'Quantity contract changes',
                     'regression_pointer': '$.checks[0].rejected', 'normal_pointer': '$.checks[0].normal'}
        feature = {'id': 'fixture-product', 'partition': 'orders', 'sources': ['domain.py', 'check.py'],
                   'map': ['fixture.json'], 'criteria': ['fixture.json'], 'checks': ['arithmetic-readback'],
                   'prevention': [{key: guardrail[key] for key in ('failure', 'scope', 'check', 'normal_exception', 'reconsider')}]}
        if bypass:
            guardrail['bypass_pointers'] = ['$.checks[0].alternate']
            feature['prevention'][0]['bypass_pointers'] = guardrail['bypass_pointers']
        project = {'commands': {'arithmetic-readback': [sys.executable, 'check.py', '{report_dir}/result.json']},
                   'extensions': {'workflow': {'roots': ['domain.py', 'check.py'], 'state': '.work/state.json', 'features': [feature]}}}
        if maintenance:
            feature['checks'].append('redundant')
            feature['prevention'].append(dict(feature['prevention'][0], check='redundant'))
            project['commands']['redundant'] = [sys.executable, 'check.py', '{report_dir}/redundant.json']
        (self.project / '.harness').mkdir()
        (self.project / '.harness/project.yaml').write_text(json.dumps(project))
        spec = {key: original[key] for key in ('id', 'feature_id', 'expected', 'required', 'selection')}
        spec.update(raw_observations=[{'path': '{report_dir}/result.json', 'pointer': '$.checks[0]', 'assertions': [
            {'pointer': guardrail['regression_pointer'], 'equals': True}, {'pointer': guardrail['normal_pointer'], 'equals': True}]}],
            dependency={'file_refs': ['dependency.txt']}, fixture={'file_refs': ['fixture.json']})
        specs = [spec]
        if bypass:
            spec['raw_observations'][0]['assertions'].append({'pointer': '$.checks[0].alternate', 'equals': True})
        if maintenance:
            redundant = __import__('copy').deepcopy(spec)
            redundant['id'] = 'redundant'
            redundant['raw_observations'][0]['path'] = '{report_dir}/redundant.json'
            specs.append(redundant)
        (self.project / 'assertions.json').write_text(json.dumps({'schema_version': 1, 'checks': specs}))
        state = workflow['begin'](self.project, project, 'feedback', ['fixture-product'])
        complaint = {'id': 'negative', 'feature': 'fixture-product', 'expected': 'Reject negative',
                     'observed': 'Negative accepted', 'reproduction': 'valid(-1) returns True'}
        state = workflow['record_feedback'](self.project, project, state, complaint)
        for stage in ('red', 'green'):
            if stage == 'green':
                (self.project / 'domain.py').write_text('def valid(value):\n    return value >= 0\n')
            output = self.project / f'.work/{stage}/plan.json'
            api['prepare_plan'](self.project, Path('assertions.json'), output, report_dir=Path(f'.work/{stage}/native'))
            outcome = api['execute_plan'](output, run_check_path=RUN_CHECK, evidence_dir=self.project / f'.work/{stage}/evidence')
            self.assertEqual(outcome['status'], 'ISSUES' if stage == 'red' else 'PASS', outcome)
        complaint.update(trace='check.py -> domain.valid -> result', root_cause='Domain accepted every value',
                         failed_prevention='No negative case', repair_paths=['domain.py'], guardrail=guardrail,
                         red_bundle='.work/red/evidence/bundle.json', green_bundle='.work/green/evidence/bundle.json')
        state = workflow['record_feedback'](self.project, project, state, complaint)
        self.assertEqual(workflow['inspect_project'](self.project, project, state)['feedback'][0]['status'], 'RESOLVED')
        if bypass:
            omitted = __import__('copy').deepcopy(state)
            del omitted['feedback']['negative']['guardrail']['bypass_pointers']
            self.assertIn('active_prevention_link_missing',
                workflow['inspect_project'](self.project, project, omitted)['feedback'][0]['remaining'])
            for pointers in (['$.missing'], [guardrail['normal_pointer']], [], ['$.checks[0].alternate'] * 2):
                changed = dict(complaint, guardrail=dict(guardrail, bypass_pointers=pointers))
                self.assertTrue(workflow['feedback_evidence'](self.project, feature, changed), pointers)
            followup = workflow['begin'](self.project, project, 'change', ['fixture-product'], prior_state=state)
            self.assertEqual(followup['feedback']['negative']['guardrail']['bypass_pointers'], guardrail['bypass_pointers'])
            (self.project / 'domain.py').write_text('def valid(value):\n    return value != -1\n')
            bypass_plan = self.project / '.work/bypass/plan.json'
            api['prepare_plan'](self.project, Path('assertions.json'), bypass_plan, report_dir=Path('.work/bypass/native'))
            failed = api['execute_plan'](bypass_plan, run_check_path=RUN_CHECK, evidence_dir=self.project / '.work/bypass/evidence')
            self.assertEqual(failed['status'], 'ISSUES')
            broken = dict(complaint, green_bundle='.work/bypass/evidence/bundle.json')
            self.assertIn('bypass_evidence_missing_or_changed:$.checks[0].alternate',
                          workflow['feedback_evidence'](self.project, feature, broken))
            spec['raw_observations'][0]['assertions'][-1]['equals'] = False
            (self.project / 'assertions.json').write_text(json.dumps({'schema_version': 1, 'checks': [spec]}))
            weak_plan = self.project / '.work/weakened/plan.json'
            api['prepare_plan'](self.project, Path('assertions.json'), weak_plan, report_dir=Path('.work/weakened/native'))
            weakened = api['execute_plan'](weak_plan, run_check_path=RUN_CHECK, evidence_dir=self.project / '.work/weakened/evidence')
            self.assertEqual(weakened['status'], 'PASS')
            broken['green_bundle'] = '.work/weakened/evidence/bundle.json'
            self.assertIn('bypass_evidence_missing_or_changed:$.checks[0].alternate',
                          workflow['feedback_evidence'](self.project, feature, broken))
            return
        if not maintenance:
            state = workflow['record_feedback'](self.project, project, state, dict(complaint,
                id='duplicate', root_cause='Initially misdiagnosed as a caller issue', repair_paths=['check.py']))
            self.assertEqual(workflow['inspect_project'](self.project, project, state)['feedback'][1]['status'], 'OPEN')
            (self.project / '.work/triage.md').write_text('Fixture review: domain negative is the same incident.\n')
            state = workflow['record_feedback'](self.project, project, state, {
                'id': 'duplicate', 'feature': 'fixture-product', 'supersession': {
                    'feedback': 'negative', 'reason': 'The domain owner repaired this incident.',
                    'references': ['.work/triage.md']}})
            self.assertEqual(workflow['inspect_project'](self.project, project, state)['feedback'][1]['status'], 'SUPERSEDED')
        (self.project / '.work/state.json').write_text(json.dumps(state))
        later = workflow['begin_work'](self.project, project)
        self.assertEqual(workflow['inspect_project'](self.project, project, later)['feedback'][0]['status'], 'RESOLVED')
        if not maintenance:
            self.assertEqual(workflow['inspect_project'](self.project, project, later)['feedback'][1]['status'], 'SUPERSEDED')
        if maintenance:
            summary = workflow['maintenance_summary'](self.project, project, state, ['.work/green/evidence/bundle.json'] * 2)
            check = next(row for row in summary['checks'] if row['id'] == 'arithmetic-readback')
            self.assertEqual(check['cost']['unique_runs'], 2)
            self.assertGreater(check['cost']['elapsed_seconds'], 0)
            self.assertEqual(check['declared_overlap'], ['redundant'])
            self.assertEqual(check['same_conditions_outcome_variation'], [])
            self.assertEqual(check['disposition'], 'retain')
            self.assertEqual(summary['execution_cost']['unique_runs'], 4)
            self.assertEqual(summary['check_footprint']['active'], 2)
            # Actual registry consolidation is blocked before proof, then accepted
            # only with old and replacement RED plus current GREEN/normal evidence.
            feature['checks'].remove('redundant')
            feature['prevention'] = [p for p in feature['prevention'] if p['check'] != 'redundant']
            del project['commands']['redundant']
            (self.project / '.harness/project.yaml').write_text(json.dumps(project))
            (self.project / 'assertions.json').write_text(json.dumps({'schema_version': 1, 'checks': [spec]}))
            output = self.project / '.work/after/plan.json'
            api['prepare_plan'](self.project, Path('assertions.json'), output, report_dir=Path('.work/after/native'))
            after = api['execute_plan'](output, run_check_path=RUN_CHECK, evidence_dir=self.project / '.work/after/evidence')
            self.assertEqual(after['status'], 'PASS')
            audit = workflow['inspect_project'](self.project, project, state)
            self.assertEqual(audit['check_retirements'][0]['status'], 'BLOCKED')
            basis = next(f['basis'] for f in audit['features'] if f['id'] == feature['id'])
            review = {'feature': feature['id'], 'basis': basis, 'analysis': 'Both tests detect the same negative quantity defect',
                      'references': ['domain.py', 'fixture.json'], 'findings': [],
                      'check_decisions': {'redundant': {'action': 'consolidate', 'reason': 'Shared domain regression preserves detection',
                          'preservation': [{'guardrail': guardrail, 'red_bundle': '.work/red/evidence/bundle.json',
                                            'green_bundle': '.work/after/evidence/bundle.json'}]}}}
            state = workflow['record_review'](self.project, project, state, review)
            self.assertEqual(workflow['inspect_project'](self.project, project, state)['check_retirements'][0]['status'], 'PRESERVED')
            linked = workflow['maintenance_summary'](self.project, project, state,
                retirements=workflow['inspect_project'](self.project, project, state)['check_retirements'])
            self.assertEqual(linked['check_footprint'], {'prior': 2, 'active': 1,
                'removed_with_proof': ['redundant'], 'removed_without_proof': []})
            self.assertEqual(linked['execution_cost']['unique_runs'], 5)
            self.assertGreater(linked['execution_cost']['elapsed_seconds'], 0)
            self.assertEqual(next(c for c in linked['checks'] if c['id'] == 'arithmetic-readback')['cost']['unique_runs'], 3,
                             'Consolidation proof runs must be consumed without re-entering their history paths')
            # An old detector with a mismatched target cannot prove preservation,
            # even if its raw failing assertion remains in the report.
            red_binding = json.loads((self.project / '.work/red/evidence/bundle.json').read_text())
            old_path = next(Path(p) for p in red_binding['records'] if json.loads(Path(p).read_text())['check'] == 'redundant')
            old_record = json.loads(old_path.read_text())
            old_record['feature'] = 'wrong-target'
            old_path.write_text(json.dumps(old_record))
            self.assertEqual(workflow['inspect_project'](self.project, project, state)['check_retirements'][0]['status'], 'BLOCKED')
            return
        # The positive counterpart must be distinct and the original oracle cannot weaken.
        broken = __import__('copy').deepcopy(state)
        broken['feedback']['negative']['guardrail']['normal_pointer'] = guardrail['regression_pointer']
        self.assertIn('nearby_normal_evidence_missing', workflow['inspect_project'](self.project, project, broken)['feedback'][0]['remaining'])
        (self.project / 'domain.py').write_text('def valid(value):\n    return value > 0\n')
        reopened = workflow['inspect_project'](self.project, project, later)['feedback'][0]
        self.assertEqual(reopened['status'], 'OPEN')
        self.assertIn('repair_revalidation_required', reopened['remaining'])
        delegated = workflow['inspect_project'](self.project, project, later)['feedback'][1]
        self.assertEqual(delegated['status'], 'OPEN')
        self.assertIn('feedback_successor_unresolved', delegated['remaining'])

    def test_maintenance_cost_overlap_and_actual_consolidation_preserve_detection(self):
        self.test_feedback_red_green_normal_and_subsequent_revalidation(maintenance=True)

    def test_feedback_requires_declared_bypass_observations(self):
        self.test_feedback_red_green_normal_and_subsequent_revalidation(bypass=True)

    def test_shared_feature_command_runs_once_and_keeps_independent_assertions(self, second_sum=5):
        import copy
        child = self.project / 'check.py'
        child.write_text(child.read_text() + "\nwith open('calls.txt','a') as stream: stream.write('run\\n')\n")
        (self.project / '.gitignore').write_text('result.json\ncalls.txt\n')
        plan_path = self._plan()
        plan = json.loads(plan_path.read_text())
        other = copy.deepcopy(plan['checks'][0])
        other['feature_id'] = 'second-feature'
        other['raw_observations'][0]['assertions'][0]['equals'] = second_sum
        plan['checks'].append(other)
        plan_path.write_text(json.dumps(plan))
        process, result = self._execute(plan_path)
        self.assertEqual(result['status'], 'PASS' if second_sum == 5 else 'ISSUES', result)
        self.assertEqual(result['test_commands_executed'], 1)
        self.assertEqual((self.project / 'calls.txt').read_text(), 'run\n')
        self.assertEqual([item['current_status'] for item in result['items']],
                         ['PASS', 'PASS' if second_sum == 5 else 'ISSUES'])
        self.assertEqual(len(result['execution']['bundle']['records']), 1)
        record = json.loads(Path(result['execution']['bundle']['records'][0]).read_text())
        self.assertEqual(record['shared_features'], ['fixture-product', 'second-feature'])
        checkpoint = json.loads((self.evidence / 'checkpoint-0-bundle.json').read_text())
        self.assertEqual(checkpoint['completed_indices'], [0, 1])
        _, resumed = self._execute(plan_path, resume=True)
        self.assertEqual(resumed['test_commands_executed'], 0)
        self.assertEqual((self.project / 'calls.txt').read_text(), 'run\n')

    def test_shared_feature_assertion_failure_does_not_inherit_other_pass(self):
        self.test_shared_feature_command_runs_once_and_keeps_independent_assertions(second_sum=6)

    def test_shared_producer_rejects_different_conditions_before_launch(self):
        import copy
        path = self._plan()
        plan = json.loads(path.read_text())
        other = copy.deepcopy(plan['checks'][0])
        other['feature_id'] = 'second-feature'
        other['conditions']['runtime']['id'] = 'different-runtime'
        plan['checks'].append(other)
        path.write_text(json.dumps(plan))
        _, result = self._execute(path)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['test_commands_executed'], 0)
        self.assertFalse((self.project / 'result.json').exists())

    def test_shared_producer_checkpoint_resumes_atomically(self, before_checkpoint=False):
        import copy
        api = self._viewer_module()
        child = self.project / 'check.py'
        child.write_text(child.read_text() + "\nwith open('calls.txt','a') as stream: stream.write('run\\n')\n")
        (self.project / '.gitignore').write_text('result.json\ncalls.txt\n')
        path = self._plan()
        plan = json.loads(path.read_text())
        other = copy.deepcopy(plan['checks'][0])
        other['feature_id'] = 'second-feature'
        plan['checks'].append(other)
        path.write_text(json.dumps(plan))
        save = api._save_execution_bundle

        def interrupt(*args, **kwargs):
            if before_checkpoint or args[1] == '':
                raise RuntimeError('controlled controller interruption')
            return save(*args, **kwargs)

        with patch.object(api, '_save_execution_bundle', side_effect=interrupt):
            with self.assertRaisesRegex(RuntimeError, 'controlled controller'):
                api.execute_plan(path, run_check_path=RUN_CHECK, evidence_dir=self.evidence)
        _, resumed = self._execute(path, resume=True)
        self.assertEqual(resumed['status'], 'BLOCKED' if before_checkpoint else 'PASS', resumed)
        self.assertEqual(resumed['test_commands_executed'], 0)
        self.assertEqual((self.project / 'calls.txt').read_text(), 'run\n')
        if not before_checkpoint:
            self.assertEqual(api.view_bundle(self.evidence / 'bundle.json')['status'], 'PASS')

    def test_shared_producer_unknown_launch_is_not_replayed(self):
        self.test_shared_producer_checkpoint_resumes_atomically(before_checkpoint=True)

    def test_prepare_subdirectory_command_binds_shared_repository_inputs(self):
        import runpy
        api = runpy.run_path(str(VIEWER))
        root = self.project
        (root / 'backend').mkdir()
        (root / '.harness').mkdir()
        (root / '.work').mkdir()
        (root / '.gitignore').write_text('.work/\nbackend/result.json\n')
        (root / 'shared.txt').write_text('shared input')
        (root / 'backend/check.py').write_text("from pathlib import Path\nimport json\nPath('result.json').write_text(json.dumps({'shared':Path('../shared.txt').read_text()}))\n")
        config = {'commands': {'shared': {'argv': [sys.executable, 'check.py'], 'working_directory': 'backend'}},
                  'extensions': {'workflow': {'roots': ['backend'], 'features': [{
                      'id': 'shared', 'partition': 'backend', 'sources': ['backend/*'],
                      'map': ['fixture.json'], 'criteria': ['fixture.json'], 'checks': ['shared']}]}}}
        (root / 'ui.css').write_text(':root { --spacing: 1rem; }')
        config['extensions']['workflow']['roots'].append('ui.css')
        config['extensions']['workflow']['ui_systems'] = {'controls': {
            'guide': 'fixture.json', 'tokens': ['ui.css'], 'components': ['backend/check.py'], 'consumers': ['shared']}}
        (root / '.harness/project.yaml').write_text(json.dumps(config))
        spec = {'schema_version': 1, 'checks': [{'id': 'shared', 'feature_id': 'shared',
            'expected': 'Backend reads the shared repository input', 'required': True,
            'selection': {'status': 'selected', 'reason': 'Shared dependency changed'},
            'dependency': {'repository_file_refs': ['shared.txt']},
            'fixture': {'file_refs': ['check.py']},
            'raw_observations': [{'path': 'result.json', 'pointer': '',
                                  'assertions': [{'pointer': '/shared', 'equals': 'shared input'}]}]}]}
        source, output = root / '.work/spec.json', root / '.work/plan.json'
        source.write_text(json.dumps(spec))
        api['prepare_plan'](root, source, output)
        self.assertFalse((root / 'backend/result.json').exists())
        plan = json.loads(output.read_text())
        self.assertEqual(plan['checks'][0]['conditions']['command']['cwd'], str(root / 'backend'))
        self.assertIn('ui.css', plan['checks'][0]['conditions']['fixture']['repository_file_refs'])
        before = api['_git_snapshot'](root / 'backend')
        (root / 'shared.txt').write_text('changed untracked shared input')
        self.assertNotEqual(before['untracked'], api['_git_snapshot'](root / 'backend')['untracked'])
        blocked = api['execute_plan'](output, run_check_path=RUN_CHECK, evidence_dir=self.evidence)
        self.assertEqual(blocked['status'], 'BLOCKED')
        self.assertFalse((root / 'backend/result.json').exists())
        (root / 'shared.txt').write_text('shared input')
        config_path = root / '.harness/project.yaml'
        config_bytes = config_path.read_bytes()
        config_path.write_bytes(config_bytes + b'\n')
        blocked = api['execute_plan'](output, run_check_path=RUN_CHECK, evidence_dir=self.root / 'changed-config')
        self.assertEqual(blocked['status'], 'BLOCKED')
        self.assertFalse((root / 'backend/result.json').exists())
        config_path.write_bytes(config_bytes)
        observed = api['execute_plan'](output, run_check_path=RUN_CHECK, evidence_dir=self.root / 'valid')
        self.assertEqual(observed['status'], 'PASS', observed)
        self.assertEqual(json.loads((root / 'backend/result.json').read_text())['shared'], 'shared input')
        (root / 'shared.txt').write_text('later mutation')
        self.assertNotEqual(api['view_bundle'](Path(observed['execution']['bundle_path']))['status'], 'PASS')
        for ref in ['../outside.txt', '.env', '.git/config']:
            with self.assertRaises(ValueError):
                api['_file_hashes']({'repository_file_refs': [ref]}, root / 'backend', 'dependency')

    def test_prepare_registered_plan_without_running_and_reject_stale_inputs(self):
        import runpy
        api = runpy.run_path(str(VIEWER))
        original = json.loads(self._plan().read_text())['checks'][0]
        (self.project / '.harness').mkdir()
        (self.project / '.gitignore').write_text('result.json\n.work/\n__pycache__/\n')
        (self.project / 'offset.py').write_text('value = 0\n')
        child = self.project / 'check.py'
        child.write_text(child.read_text().replace("fixture['a'] + fixture['b']", "fixture['a'] + fixture['b'] + __import__('offset').value"))
        config = {'commands': {'arithmetic-readback': original['conditions']['command']['argv']},
                  'extensions': {'workflow': {'roots': ['check.py'], 'features': [{
                      'id': 'fixture-product', 'partition': 'domain', 'sources': ['check.py'],
                      'map': ['fixture.json'], 'criteria': ['fixture.json'], 'checks': ['arithmetic-readback']}]}}}
        (self.project / '.harness/project.yaml').write_text(json.dumps(config))
        spec = {'schema_version': 1, 'checks': [{key: original[key] for key in
                ('id', 'feature_id', 'expected', 'required', 'selection', 'raw_observations')}]}
        spec['checks'][0]['dependency'] = {'file_refs': ['dependency.txt']}
        spec['checks'][0]['fixture'] = {'file_refs': ['fixture.json']}
        source = self.project / '.work/spec.json'
        source.parent.mkdir()
        source.write_text(json.dumps(spec))
        output = self.project / '.work/plan.json'
        result = api['prepare_plan'](self.project, source, output)
        self.assertEqual(result['test_commands_executed'], 0)
        self.assertFalse((self.project / 'result.json').exists())
        plan = json.loads(output.read_text())
        self.assertEqual(plan['checks'][0]['conditions']['command'], original['conditions']['command'])
        self.assertEqual(plan['checks'][0]['raw_observations'], original['raw_observations'])
        with self.assertRaises(ValueError):
            api['prepare_plan'](self.project, source, output)
        for field, value in [('id', 'unregistered'), ('conditions', {'command': {'argv': ['wrong']}}),
                             ('raw_observations', [{'path': '../outside.json', 'pointer': '',
                                                   'assertions': [{'pointer': '/x', 'equals': True}]}]),
                             ('raw_observations', [{'path': '.work/refused.json', 'pointer': '',
                                                   'assertions': [{'pointer': '/x', 'equals': True}]}])]:
            invalid = json.loads(json.dumps(spec))
            invalid['checks'][0][field] = value
            source.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                api['prepare_plan'](self.project, source, self.project / '.work/refused.json')
            self.assertFalse((self.project / '.work/refused.json').exists())
            self.assertFalse((self.project / 'result.json').exists())
        source.write_text(json.dumps(spec))
        original_config = (self.project / '.harness/project.yaml').read_bytes()
        config['commands']['arithmetic-readback'] = [sys.executable, '-c', 'raise SystemExit(99)']
        (self.project / '.harness/project.yaml').write_text(json.dumps(config))
        changed_command = api['execute_plan'](output, run_check_path=RUN_CHECK,
                                               evidence_dir=self.root / 'changed-command')
        self.assertEqual(changed_command['status'], 'BLOCKED', changed_command)
        self.assertFalse((self.project / 'result.json').exists())
        (self.project / '.harness/project.yaml').write_bytes(original_config)
        (self.project / 'offset.py').write_text('value = 1\n')
        changed_source = api['execute_plan'](output, run_check_path=RUN_CHECK,
                                             evidence_dir=self.root / 'changed-source')
        self.assertEqual(changed_source['status'], 'BLOCKED', changed_source)
        self.assertFalse((self.project / 'result.json').exists())
        (self.project / 'offset.py').write_text('value = 0\n')
        (self.project / 'dependency.txt').write_text('changed')
        blocked = api['execute_plan'](output, run_check_path=RUN_CHECK, evidence_dir=self.evidence)
        self.assertEqual(blocked['status'], 'BLOCKED')
        self.assertFalse((self.project / 'result.json').exists())
        current = self.project / '.work/current.json'
        prepared = subprocess.run([sys.executable, str(VIEWER), '--prepare', str(source),
                                   '--root', str(self.project), '--plan-output', str(current)],
                                  capture_output=True, text=True)
        self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
        observed = api['execute_plan'](current, run_check_path=RUN_CHECK, evidence_dir=self.root / 'current-evidence')
        self.assertEqual(observed['status'], 'PASS', observed)
        self.assertEqual(json.loads((self.project / 'result.json').read_text())['checks'][0]['sum'], 5)
        (self.project / '.work/unrelated-note.txt').write_text('scratch work is not source')
        bundle = observed['execution']['bundle_path']
        self.assertEqual(api['view_bundle'](bundle)['status'], 'PASS')
        (self.project / 'offset.py').write_text('value = 2\n')
        self.assertNotEqual(api['view_bundle'](bundle)['status'], 'PASS')

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.evidence = self.root / "evidence"
        self._git("init", "-q")
        self._git("config", "user.name", "fixture")
        self._git("config", "user.email", "fixture@example.invalid")
        (self.project / "dependency.txt").write_text("dep-1\n", encoding="utf-8")
        (self.project / "fixture.json").write_text(
            json.dumps({"a": 2, "b": 3, "readback": "ok"}), encoding="utf-8"
        )
        (self.project / ".gitignore").write_text("result.json\n", encoding="utf-8")
        (self.project / "check.py").write_text(
            """import json\nfrom pathlib import Path\n\nfixture = json.loads(Path('fixture.json').read_text())\nPath('result.json').write_text(json.dumps({'checks': [{'sum': fixture['a'] + fixture['b'], 'readback': fixture['readback']}] }))\n""",
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-qm", "fixture")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.project), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def _plan(
        self,
        *,
        assertions=None,
        child=None,
        report="result.json",
        dependency_refs=None,
        fixture_refs=None,
    ) -> Path:
        head = self._git("rev-parse", "HEAD").strip()
        diff = _digest(self._git("diff", "HEAD", "--binary").encode())
        plan = {
            "schema_version": 1,
            "plan_id": "execution-fixture",
            "checks": [
                {
                    "id": "arithmetic-readback",
                    "feature_id": "fixture-product",
                    "expected": "arithmetic and readback facts are observed",
                    "criteria_revision": "criteria-1",
                    "required": True,
                    "selection": {"status": "selected", "reason": "focused execution"},
                    "conditions": {
                        "source": {"revision": head, "diff": diff},
                        "criteria": {"revision": "criteria-1"},
                        "command": {
                            "argv": [sys.executable, str(child or self.project / "check.py")],
                            "cwd": str(self.project),
                        },
                        "dependency": {"file_refs": dependency_refs or ["dependency.txt"]},
                        "fixture": {"file_refs": fixture_refs or ["fixture.json"]},
                        "runtime": {"id": "fixture-runtime"},
                    },
                    "raw_observations": [
                        {
                            "path": report,
                            "pointer": "$.checks[0]",
                            "assertions": assertions
                            if assertions is not None
                            else [
                                {"pointer": "$.checks[0].sum", "equals": 5},
                                {"pointer": "$.checks[0].readback", "equals": "ok"},
                            ],
                        }
                    ],
                }
            ],
        }
        path = self.root / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def _execute(
        self,
        plan: Path,
        *,
        timeout: str | None = None,
        evidence_dir: Path | None = None,
        resume: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [
            sys.executable,
            str(VIEWER),
            "--execute",
            "--plan",
            str(plan),
            "--run-check",
            str(RUN_CHECK),
            "--evidence-dir",
            str(evidence_dir or self.evidence),
        ]
        if timeout is not None:
            command.extend(["--timeout", timeout])
        if resume:
            command.append('--resume')
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result, json.loads(result.stdout)

    def _viewer_module(self):
        spec = importlib.util.spec_from_file_location("verification_results_fixture", VIEWER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        return module

    def test_legacy_console_execute_and_lookup_keep_unicode_evidence(self):
        plan = self._plan()
        data = json.loads(plan.read_text(encoding='utf-8'))
        label = 'Readback \u2013 \U0001f642'
        data['checks'][0]['expected'] = label
        plan.write_text(json.dumps(data), encoding='utf-8')
        with patch.dict(os.environ, {'PYTHONIOENCODING': 'cp949'}):
            result, payload = self._execute(plan)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload['items'][0]['expected'], label)
            snapshot = {str(p): p.read_bytes() for p in self.evidence.rglob('*') if p.is_file()}
            resumed, same = self._execute(plan, resume=True)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(same['test_commands_executed'], 0)
            self.assertEqual(same['items'][0]['expected'], label)
            self.assertEqual(snapshot, {str(p): p.read_bytes() for p in self.evidence.rglob('*') if p.is_file()})

    def test_execute_child_report_binds_facts_and_current_passes(self) -> None:
        result, payload = self._execute(self._plan())

        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload["current"]["status"], "PASS")
        item = payload["items"][0]
        self.assertEqual(item["current_status"], "PASS")
        self.assertEqual([row["actual"] for row in item["raw"][0]["observations"]], [5, "ok"])
        self.assertEqual(item["capture"]["execution"], "exited")
        self.assertEqual(item["capture"]["exit_code"], 0)
        self.assertEqual(item["raw"][0]["producer"]["run_id"], item["run_id"])
        runtime = item["conditions"]["expected"]["runtime"]
        self.assertTrue(runtime["executable"])
        self.assertEqual(len(runtime["executable_sha256"]), 64)
        self.assertTrue(runtime["python_version"])

    def test_resume_keeps_completed_commands_and_refuses_unknown_launch(self, first_expected=5, first_required=True, terminate_controller=False) -> None:
        import copy
        child = self.project / 'check.py'
        child.write_text("import json,sys\nfrom pathlib import Path\np=Path('.work');p.mkdir(exist_ok=True)\n"
                         "with (p/'calls').open('a') as f:f.write(sys.argv[1]+'\\n')\n"
                         "Path(sys.argv[1]).write_text(json.dumps({'checks':[{'sum':5,'readback':'ok'}]}))\n")
        (self.project / '.gitignore').write_text('.work/\n')
        self._git('add', '.')
        self._git('commit', '-qm', 'two independent checks')
        plan = self._plan(report='.work/first.json')
        value = json.loads(plan.read_text())
        value['checks'][0]['raw_observations'][0]['assertions'][0]['equals'] = first_expected
        value['checks'][0]['required'] = first_required
        value['checks'][0]['conditions']['command']['argv'].append('.work/first.json')
        second = copy.deepcopy(value['checks'][0])
        second['id'] = 'second'
        second['required'] = True
        second['raw_observations'][0]['path'] = '.work/second.json'
        second['conditions']['command']['argv'][-1] = '.work/second.json'
        second['raw_observations'][0]['assertions'][0]['equals'] = 5
        value['checks'].append(second)
        plan.write_text(json.dumps(value))
        module = self._viewer_module()
        original_save = module._save_execution_bundle
        def interrupted(*args, **kwargs):
            result = original_save(*args, **kwargs)
            if args[1] == 'checkpoint-0-':
                raise KeyboardInterrupt('controller interrupted between commands')
            return result
        if terminate_controller:
            ready = self.root / 'checkpoint-ready'
            controller = self.root / 'controller.py'
            controller.write_text(
                "import runpy,sys,time\nfrom pathlib import Path\n"
                "scope=runpy.run_path(sys.argv[1])\n"
                "execute=scope['execute_plan']\n"
                "original=execute.__globals__['_save_execution_bundle']\n"
                "def checkpoint(*args,**kwargs):\n"
                "    result=original(*args,**kwargs)\n"
                "    if args[1]=='checkpoint-0-':\n"
                "        Path(sys.argv[5]).write_text('ready')\n"
                "        while True: time.sleep(1)\n"
                "    return result\n"
                "execute.__globals__['_save_execution_bundle']=checkpoint\n"
                "execute(Path(sys.argv[2]),run_check_path=Path(sys.argv[3]),evidence_dir=Path(sys.argv[4]))\n",
                encoding='utf-8',
            )
            with subprocess.Popen([sys.executable, str(controller), str(VIEWER), str(plan),
                                   str(RUN_CHECK), str(self.evidence), str(ready)]) as process:
                try:
                    deadline = time.monotonic() + 30
                    while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.05)
                    self.assertTrue(ready.exists(), 'controller never reached durable checkpoint')
                    self.assertIsNone(process.poll(), 'controller must still be live before termination')
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=10)
                self.assertNotEqual(process.returncode, 0)
        else:
            with patch.object(module, '_save_execution_bundle', interrupted):
                with self.assertRaises(KeyboardInterrupt):
                    module.execute_plan(plan, run_check_path=RUN_CHECK, evidence_dir=self.evidence)
        self.assertEqual((self.project / '.work/calls').read_text().splitlines(), ['.work/first.json'])
        retained = {p: p.read_bytes() for p in self.evidence.rglob('*') if p.is_file()}
        def refused():
            result = module.execute_plan(plan, run_check_path=RUN_CHECK, evidence_dir=self.evidence, resume=True)
            self.assertEqual(result['status'], 'BLOCKED', result)
            self.assertEqual(result['test_commands_executed'], 0)
            self.assertEqual((self.project / '.work/calls').read_text().splitlines(), ['.work/first.json'])
        original_plan = plan.read_bytes()
        plan.write_bytes(original_plan + b'\n')
        refused()
        plan.write_bytes(original_plan)
        dependency = self.project / 'dependency.txt'
        original_dependency = dependency.read_bytes()
        dependency.write_text('changed dependency')
        refused()
        dependency.write_bytes(original_dependency)
        raw = self.project / '.work/first.json'
        original_raw = raw.read_bytes()
        raw.unlink()
        refused()
        raw.write_bytes(original_raw)
        checkpoint = self.evidence / 'checkpoint-0-bundle.json'
        original_checkpoint = checkpoint.read_bytes()
        checkpoint.write_text('{')
        refused()
        checkpoint.write_bytes(original_checkpoint)
        marker = self.evidence / 'command-1-started.json'
        marker.write_text('{}')  # Crash after durable launch intent, before a finished capture.
        refused()
        marker.unlink()  # Restore the controlled pre-launch fixture, not production recovery.
        _, result = self._execute(plan, resume=True)
        expected_status = 'PASS' if first_expected == 5 else 'ISSUES'
        self.assertEqual(result['status'], expected_status, result)
        self.assertEqual(result['items'][0]['required'], first_required)
        self.assertEqual(result['test_commands_executed'], 1)
        self.assertEqual((self.project / '.work/calls').read_text().splitlines(), ['.work/first.json', '.work/second.json'])
        self.assertTrue(all(p.read_bytes() == raw for p, raw in retained.items()))
        _, repeated = self._execute(plan, resume=True)
        self.assertEqual(repeated['status'], expected_status, repeated)
        self.assertEqual(repeated['test_commands_executed'], 0)

    def test_resume_preserves_known_failure_and_runs_pending_check(self) -> None:
        self.test_resume_keeps_completed_commands_and_refuses_unknown_launch(first_expected=6)

    def test_resume_after_controller_process_is_killed(self) -> None:
        self.test_resume_keeps_completed_commands_and_refuses_unknown_launch(terminate_controller=True)

    def test_resume_selected_optional_check_without_changing_policy(self) -> None:
        self.test_resume_keeps_completed_commands_and_refuses_unknown_launch(first_required=False)

    def test_resume_last_checkpoint_survives_partial_final_bundle(self, torn_descriptor=False, during_publish=False) -> None:
        plan = self._plan()
        module = self._viewer_module()
        original_write = module._write_json
        def interrupted(path, data):
            if during_publish and path.name == 'bundle.pending.json':
                path.write_text('{')
                raise KeyboardInterrupt('descriptor interrupted before atomic publication')
            original_write(path, data)
            if not during_publish and path.name == 'bound-plan.json':
                raise KeyboardInterrupt('final bundle write interrupted')
        with patch.object(module, '_write_json', interrupted):
            with self.assertRaises(KeyboardInterrupt):
                module.execute_plan(plan, run_check_path=RUN_CHECK, evidence_dir=self.evidence)
        if torn_descriptor:
            (self.evidence / 'bundle.json').write_text('{')
        retained = {p: p.read_bytes() for p in self.evidence.rglob('*') if p.is_file()}
        result = module.execute_plan(plan, run_check_path=RUN_CHECK, evidence_dir=self.evidence, resume=True)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['test_commands_executed'], 0)
        self.assertEqual(module.view_bundle(self.evidence / 'bundle.json')['status'], 'PASS')
        for path, data in retained.items():
            if path.name == 'bundle.json':
                backup = self.evidence / ('bundle.interrupted-' + _digest(data) + '.json')
                self.assertEqual(backup.read_bytes(), data)
            else:
                self.assertEqual(path.read_bytes(), data)

    def test_resume_complete_checkpoint_with_torn_final_descriptor(self) -> None:
        self.test_resume_last_checkpoint_survives_partial_final_bundle(torn_descriptor=True)

    def test_resume_checkpoint_before_atomic_final_publication(self) -> None:
        self.test_resume_last_checkpoint_survives_partial_final_bundle(during_publish=True)

    def test_interrupted_capture_enrichment_preserves_success_and_refuses_replay(self) -> None:
        plan = self._plan()
        module = self._viewer_module()
        original_write = Path.write_text
        original_json = module._write_json
        def interrupted(path, data, *args, **kwargs):
            if path.name.endswith(('-capture.json', '-capture.pending.json')):
                original_write(path, '{', encoding='utf-8')
                raise KeyboardInterrupt('interrupted capture enrichment')
            return original_write(path, data, *args, **kwargs)
        def write_json(path, data):
            if path.name.endswith('-capture.pending.json'):
                return interrupted(path, data)
            return original_json(path, data)
        with patch.object(Path, 'write_text', interrupted), patch.object(module, '_write_json', write_json):
            with self.assertRaises(KeyboardInterrupt):
                module.execute_plan(plan, run_check_path=RUN_CHECK, evidence_dir=self.evidence)
        capture = next(self.evidence.glob('*-capture.json'))
        retained = capture.read_bytes()
        record = json.loads(retained)
        self.assertEqual(record['exit_code'], 0)
        self.assertTrue(record['run_id'])
        self.assertTrue((self.project / 'result.json').exists())
        result = module.execute_plan(plan, run_check_path=RUN_CHECK, evidence_dir=self.evidence, resume=True)
        self.assertEqual(result['status'], 'BLOCKED', result)
        self.assertEqual(result['test_commands_executed'], 0)
        self.assertEqual(capture.read_bytes(), retained)

    def test_resume_does_not_retry_a_durably_marked_launch(self) -> None:
        plan = self._plan()
        module = self._viewer_module()
        original_run = module.subprocess.run
        def interrupted(argv, *args, **kwargs):
            if str(RUN_CHECK) in argv:
                self.assertTrue((self.evidence / 'command-0-started.json').is_file())
                raise KeyboardInterrupt('controller lost command outcome')
            return original_run(argv, *args, **kwargs)
        with patch.object(module.subprocess, 'run', interrupted):
            with self.assertRaises(KeyboardInterrupt):
                module.execute_plan(plan, run_check_path=RUN_CHECK, evidence_dir=self.evidence)
        _, result = self._execute(plan, resume=True)
        self.assertEqual(result['status'], 'BLOCKED', result)
        self.assertEqual(result['test_commands_executed'], 0)
        self.assertFalse((self.project / 'result.json').exists())

    def test_failed_explicit_assertion_is_not_pass(self) -> None:
        child = self.project / "bad.py"
        child.write_text(
            "from pathlib import Path\nPath('result.json').write_text('{\"checks\":[{\"sum\": 4, \"readback\": \"ok\"}]}')\n",
            encoding="utf-8",
        )
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload["current"]["status"], "PASS")
        self.assertTrue(any("raw_assertion_mismatch" in reason for reason in payload["remaining"]))

    def test_submitted_pass_string_cannot_hide_a_bad_fact(self) -> None:
        child = self.project / "misleading.py"
        child.write_text(
            "from pathlib import Path\n"
            "Path('result.json').write_text('{\"status\":\"PASS\",\"checks\":[{\"sum\": 4, \"readback\": \"ok\"}]}')\n",
            encoding="utf-8",
        )
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload["current"]["status"], "PASS")

    def test_missing_assertions_block_before_starting_a_child(self) -> None:
        marker = self.project / "preflight-marker"
        child = self.project / "should-not-start.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        plan = self._plan(child=child, assertions=[])

        result, payload = self._execute(plan)

        self.assertEqual(result.returncode, 2, payload)
        self.assertFalse(marker.exists())
        self.assertEqual(payload["test_commands_executed"], 0)

    def test_zero_and_skip_facts_are_rejected_by_explicit_assertions(self) -> None:
        for index, (body, assertion) in enumerate(
            (
                ('{"checks": []}', {"pointer": "$.checks", "min_count": 1}),
                ('{"checks": [{"skipped": true}]}', {"pointer": "$.checks[0].skipped", "equals": False}),
            )
        ):
            with self.subTest(body=body):
                child = self.project / "edge.py"
                (self.project / "result.json").unlink(missing_ok=True)
                child.write_text(
                    f"from pathlib import Path\nPath('result.json').write_text({body!r})\n",
                    encoding="utf-8",
                )
                result, payload = self._execute(
                    self._plan(child=child, assertions=[assertion]),
                    evidence_dir=self.root / f"evidence-{index}",
                )
                self.assertNotEqual(result.returncode, 0, payload)
                self.assertNotEqual(payload["current"]["status"], "PASS")
                self.assertTrue(
                    any(
                        "raw_assertion_mismatch" in reason or "raw_pointer_missing" in reason
                        for reason in payload["remaining"]
                    ),
                    payload,
                )

    def test_missing_native_report_is_blocked(self) -> None:
        child = self.project / "missing.py"
        child.write_text("pass\n", encoding="utf-8")
        result, payload = self._execute(self._plan(child=child))

        self.assertEqual(result.returncode, 2, payload)
        self.assertEqual(payload["current"]["status"], "BLOCKED")
        self.assertTrue(any("raw" in reason or "report" in reason for reason in payload["remaining"]))

    def test_existing_native_report_is_never_reused(self) -> None:
        marker = self.project / "executed"
        (self.project / "result.json").write_text(
            '{"checks":[{"sum":5,"readback":"ok"}]}', encoding="utf-8"
        )
        child = self.project / "should-not-run.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertFalse(marker.exists())

    def test_dependency_change_during_run_makes_result_stale(self) -> None:
        child = self.project / "mutate.py"
        child.write_text(
            "from pathlib import Path\nPath('dependency.txt').write_text('changed\\n')\n"
            "Path('result.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertIn(payload["items"][0]["current_reuse"], {"STALE", "UNKNOWN"})

    def test_lookup_without_execute_does_not_run_selected_command(self) -> None:
        marker = self.project / "lookup-ran"
        child = self.project / "lookup.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        plan = self._plan(child=child)
        result = subprocess.run(
            [sys.executable, str(VIEWER), "--plan", str(plan)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertFalse(marker.exists())
        self.assertEqual(json.loads(result.stdout)["test_commands_executed"], 0)

    def test_view_bundle_remeasures_current_files_without_execution_or_writes(self) -> None:
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bundle = payload["execution"]["bundle"]
        bound = Path(bundle["plan"])
        before = bound.read_bytes()
        (self.project / "fixture.json").write_text(
            json.dumps({"a": 9, "b": 3, "readback": "ok"}), encoding="utf-8"
        )

        viewed = self._viewer_module().view_bundle(bundle)
        persisted = Path(payload["execution"]["bundle_path"])
        persisted_before = persisted.read_bytes()
        viewed_from_path = self._viewer_module().view_bundle(persisted)

        self.assertNotEqual(viewed["status"], "PASS")
        self.assertEqual(viewed_from_path["status"], viewed["status"])
        self.assertEqual(viewed["test_commands_executed"], 0)
        self.assertEqual(bound.read_bytes(), before)
        self.assertEqual(persisted.read_bytes(), persisted_before)
        self.assertTrue(any("current.fixture" in reason for reason in viewed["remaining"]))

    def test_persisted_bundle_view_passes_current_without_execution(self) -> None:
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bundle_path = Path(payload["execution"]["bundle_path"])
        viewed = self._viewer_module().view_bundle(bundle_path)

        self.assertEqual(viewed["status"], "PASS")
        self.assertEqual(viewed["test_commands_executed"], 0)
        self.assertEqual(viewed["items"][0]["capture"]["argv"], [sys.executable, str(self.project / "check.py")])
        lookup = subprocess.run([sys.executable, str(VIEWER), '--bundle', str(bundle_path)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(lookup.stdout)['test_commands_executed'], 0)

    def test_bundle_without_measured_runtime_identity_is_blocked(self) -> None:
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bound = Path(payload["execution"]["bundle"]["plan"])
        plan = json.loads(bound.read_text(encoding="utf-8"))
        plan["checks"][0]["conditions"]["runtime"].pop("executable", None)
        plan["checks"][0]["conditions"]["runtime"].pop("executable_sha256", None)
        bound.write_text(json.dumps(plan), encoding="utf-8")

        viewed = self._viewer_module().view_bundle(Path(payload["execution"]["bundle_path"]))

        self.assertEqual(viewed["status"], "BLOCKED")
        self.assertIn("runtime_identity_missing", " ".join(viewed["remaining"]))

    def test_symlink_file_reference_and_native_report_are_blocked_before_child(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink support is unavailable")
        marker = self.project / "alias-marker"
        child = self.project / "alias-child.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        dependency_link = self.project / "dependency-link.txt"
        report_link = self.project / "report-link.json"
        try:
            os.symlink(self.project / "dependency.txt", dependency_link)
            os.symlink(self.root / "outside-report.json", report_link)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")
        for dependency_refs, report in ((["dependency-link.txt"], "result.json"), (["dependency.txt"], "report-link.json")):
            with self.subTest(dependency_refs=dependency_refs, report=report):
                marker.unlink(missing_ok=True)
                plan = self._plan(child=child, dependency_refs=dependency_refs, report=report)
                result, payload = self._execute(plan)
                self.assertEqual(result.returncode, 2, payload)
                self.assertFalse(marker.exists())

    def test_view_bundle_rejects_mutated_source_plan(self) -> None:
        _, payload = self._execute(self._plan())
        bundle = payload["execution"]["bundle"]
        source_plan = Path(bundle["source_plan"])
        source_plan.write_text(source_plan.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        viewed = self._viewer_module().view_bundle(bundle)

        self.assertEqual(viewed["status"], "BLOCKED")
        self.assertIn("source_plan_hash_mismatch", viewed["remaining"])

    def test_private_or_escaped_file_and_report_paths_block_before_child(self) -> None:
        marker = self.project / "blocked-marker"
        child = self.project / "marker.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        outside = self.root / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        for dependency_refs, report in (([str(outside)], "result.json"), ([".env"], "result.json"), (["dependency.txt"], "../outside-report.json")):
            with self.subTest(dependency_refs=dependency_refs, report=report):
                if dependency_refs == [".env"]:
                    (self.project / ".env").write_text("secret", encoding="utf-8")
                plan = self._plan(child=child, dependency_refs=dependency_refs, report=report)
                result, payload = self._execute(plan)
                self.assertEqual(result.returncode, 2, payload)
                self.assertFalse(marker.exists())

    def test_nonfinite_timeout_blocks_before_child(self) -> None:
        marker = self.project / "timeout-marker"
        child = self.project / "timeout-check.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")

        result, payload = self._execute(self._plan(child=child), timeout="inf")

        self.assertEqual(result.returncode, 2, payload)
        self.assertFalse(marker.exists())

    def test_each_check_remeasures_files_before_starting_the_next_child(self) -> None:
        second_marker = self.project / "second-ran"
        first = self.project / "first.py"
        second = self.project / "second.py"
        first.write_text(
            "from pathlib import Path\n"
            "Path('dependency.txt').write_text('changed\\n')\n"
            "Path('result.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )
        second.write_text(
            f"from pathlib import Path\nPath({str(second_marker)!r}).touch()\n"
            "Path('result-2.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )
        plan = json.loads(self._plan(child=first, report="result.json").read_text(encoding="utf-8"))
        second_check = json.loads(json.dumps(plan["checks"][0]))
        second_check["id"] = "second-check"
        second_check["conditions"]["command"]["argv"] = [sys.executable, str(second)]
        second_check["raw_observations"][0]["path"] = "result-2.json"
        plan["checks"].append(second_check)
        plan_path = self.root / "multi-plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")

        result, payload = self._execute(plan_path)

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertFalse(second_marker.exists())
        self.assertTrue(any("precondition" in reason or "raw" in reason for reason in payload["remaining"]))

    def test_original_plan_mutation_during_child_invalidates_current_pass(self) -> None:
        child = self.project / "mutate-plan.py"
        plan = self._plan(child=child)
        child.write_text(
            f"from pathlib import Path\n"
            f"plan = Path({str(plan)!r})\n"
            "plan.write_text(plan.read_text() + '\\n')\n"
            "Path('result.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )

        result, payload = self._execute(plan)

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload["current"]["status"], "PASS")
        self.assertTrue(payload["execution"]["source_plan_changed_during_execution"])

    def test_bound_criteria_cannot_diverge_from_unchanged_original_plan(self) -> None:
        import runpy
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bundle = payload['execution']['bundle']
        path = Path(bundle['plan'])
        bound = json.loads(path.read_text(encoding='utf-8'))
        bound['checks'][0]['expected'] = 'a different requirement never selected'
        path.write_text(json.dumps(bound), encoding='utf-8')
        viewed = runpy.run_path(str(VIEWER))['view_bundle'](bundle)
        self.assertEqual(viewed['status'], 'BLOCKED', viewed)

    def test_later_check_invalidates_earlier_ignored_fixture_before_return(self) -> None:
        (self.project / '.gitignore').write_text('result.json\nresult-2.json\nexternal.txt\n', encoding='utf-8')
        (self.project / 'external.txt').write_text('before', encoding='utf-8')
        second = self.project / 'second.py'
        second.write_text("from pathlib import Path\nPath('external.txt').write_text('after')\nPath('result-2.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n", encoding='utf-8')
        path = self._plan()
        plan = json.loads(path.read_text(encoding='utf-8'))
        following = json.loads(json.dumps(plan['checks'][0]))
        plan['checks'][0]['conditions']['fixture'] = {'file_refs': ['external.txt']}
        following['id'] = 'later'
        following['conditions']['command']['argv'] = [sys.executable, str(second)]
        following['raw_observations'][0]['path'] = 'result-2.json'
        plan['checks'].append(following)
        path.write_text(json.dumps(plan), encoding='utf-8')
        result, payload = self._execute(path)
        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload['items'][0]['current_status'], 'PASS', payload)


if __name__ == "__main__":
    unittest.main()
