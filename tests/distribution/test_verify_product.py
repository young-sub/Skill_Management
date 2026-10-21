"""Repository adapter checks use real commands in a disposable Git project."""
import json
import runpy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / 'scripts/verify_product.py'
CAPTURE = ROOT / 'scripts/run_check.py'


class VerifyProductTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '.harness').mkdir()
        (self.root / 'docs').mkdir()
        (self.root / '.gitignore').write_text('evidence/\n__pycache__/\n')
        (self.root / 'docs/feature-map.md').write_text(
            '| Feature ID | Name | Action | Result and invariant | Domain | Side effects | Command IDs |\n'
            '| --- | --- | --- | --- | --- | --- | --- |\n'
            '| native-verification | Check | Run | Honest result | tests | evidence | fixture |\n')
        self.argv = [sys.executable, '-m', 'unittest', 'suite']
        (self.root / '.harness/project.yaml').write_text(json.dumps({'commands': {
            'fixture': {'id': 'fixture', 'argv': self.argv, 'working_directory': '.',
                        'runtime': 'python', 'platform': 'any', 'capability': 'fixture'}}}))
        self.suite = self.root / 'suite.py'
        self.suite.write_text('import unittest\nclass Behavior(unittest.TestCase):\n'
                              '    def test_result(self): self.assertEqual(2 + 2, 4)\n')
        self.git('init')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@localhost',
                 'commit', '-m', 'fixture')
        self.output = self.root / 'evidence/run.json'

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args],
                              capture_output=True, check=True)

    def verify(self, *args):
        result = subprocess.run([sys.executable, str(VERIFIER), '--root', str(self.root),
                                 '--feature', 'native-verification', '--check', 'fixture', *args],
                                capture_output=True, text=True, timeout=20)
        self.assertTrue(result.stdout.strip().startswith('{'), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def run_check(self):
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
        record = json.loads(self.output.read_text())
        self.assertIsNone(record['behavior_verdict'])
        self.assertEqual(record['check'], 'fixture')
        self.assertEqual(record['feature'], 'native-verification')
        self.assertEqual(record['run_id'], verdict['run_id'])
        self.assertGreater(verdict['tests_run'], 0)
        return record

    def enable_scoped_check(self):
        project_path = self.root / '.harness/project.yaml'
        project = json.loads(project_path.read_text())
        project['commands']['fixture']['evidence_inputs'] = ['deps/*.py']
        project['extensions'] = {'workflow': {'roots': ['logic.py'], 'features': [{
            'id': 'native-verification', 'partition': 'verification', 'sources': ['logic.py'],
            'map': ['docs/feature-map.md'], 'criteria': ['docs/criteria.md'], 'checks': ['fixture']} ]}}
        project_path.write_text(json.dumps(project), encoding='utf-8')
        (self.root / 'docs/criteria.md').write_text('The selected unittest result must be current.\n')
        (self.root / 'logic.py').write_text('from deps.helper import VALUE\n')
        (self.root / 'deps').mkdir()
        (self.root / 'deps/__init__.py').write_text('')
        (self.root / 'deps/helper.py').write_text('VALUE = 42\n')
        self.suite.write_text(
            'import unittest\nfrom pathlib import Path\nfrom logic import VALUE\n'
            'class Behavior(unittest.TestCase):\n'
            ' def test_value(self):\n'
            '  p=Path("evidence/count"); p.parent.mkdir(exist_ok=True)\n'
            '  p.write_text(str(int(p.read_text())+1) if p.exists() else "1")\n'
            '  self.assertEqual(VALUE, 42)\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@localhost',
                 'commit', '-m', 'configure scoped check')

    def check_read_only_lookup(self, path, expected, code=0):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes()
                  for p in self.root.rglob('*') if p.is_file() and '.git' not in p.parts}
        result = subprocess.run([sys.executable, str(CAPTURE), '--cwd', str(self.root),
                                 '--lookup', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['source_status'], expected, value)
        self.assertEqual(value['test_commands_executed'], 0)
        after = {p.relative_to(self.root).as_posix(): p.read_bytes()
                 for p in self.root.rglob('*') if p.is_file() and '.git' not in p.parts}
        self.assertEqual(before, after, 'Read-only lookup must not change project or evidence bytes')
        return value

    def test_real_command_is_bound_to_feature_and_current_source(self):
        record = self.run_check()
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)

    def test_workflow_bundle_reuses_native_capture_without_running_tests(self):
        runtime = runpy.run_path(str(ROOT / 'authoring/scripts/project_workflow.py'))
        project = json.loads((self.root / '.harness/project.yaml').read_text())
        project['extensions'] = {'workflow': {'roots': ['suite.py'], 'features': [{
            'id': 'native-verification', 'partition': 'verification', 'sources': ['suite.py'],
            'map': ['docs/feature-map.md'], 'criteria': ['docs/feature-map.md'], 'checks': ['fixture']}]}}
        state = runtime['begin'](self.root, project, 'change')
        self.suite.write_text('import unittest\nfrom pathlib import Path\n'
            'p=Path("evidence/count"); p.parent.mkdir(exist_ok=True)\n'
            'p.write_text(str(int(p.read_text())+1) if p.exists() else "1")\n'
            'class Behavior(unittest.TestCase):\n'
            '    def test_result(self): self.assertEqual(2 + 2, 4)\n')
        bundle = self.root / 'evidence/bundle.json'
        code, verdict = self.verify('--output', str(self.output), '--bundle-output', str(bundle))
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
        feature = {'id': 'native-verification', 'checks': ['fixture']}
        commands = {'fixture': {'argv': self.argv, 'runtime': 'python'}}
        before = {p: p.read_bytes() for p in (self.root / 'evidence').iterdir()}
        observed = runtime['inspect_evidence'](self.root, feature, commands, 'evidence/bundle.json')
        self.assertEqual(observed['status'], 'PASS', observed)
        pending = runtime['inspect_project'](self.root, project, state)
        self.assertIn('verification', pending['obligations'][0]['requires'])
        state = runtime['record_review'](self.root, project, state, {
            'feature': feature['id'], 'basis': pending['features'][0]['basis'],
            'analysis': 'The native suite exercises the required arithmetic behavior.',
            'references': ['suite.py', 'docs/feature-map.md'], 'findings': [],
            'bundle': 'evidence/bundle.json'})
        self.assertEqual(runtime['inspect_project'](self.root, project, state)['status'], 'READY_FOR_REVIEW')
        self.assertEqual(before, {p: p.read_bytes() for p in (self.root / 'evidence').iterdir()})
        self.assertEqual((self.root / 'evidence/count').read_text(), '1')
        feature['checks'].append('missing')
        self.assertEqual(runtime['inspect_evidence'](self.root, feature, commands,
                         'evidence/bundle.json')['status'], 'BLOCKED')

        feature['checks'].pop()
        forged = json.loads(bundle.read_text())
        forged['status'] = 'PASS'
        bundle.write_text(json.dumps(forged))
        record = json.loads(self.output.read_text())
        record['exit_code'] = 1
        self.output.write_text(json.dumps(record))
        self.assertEqual(runtime['inspect_evidence'](self.root, feature, commands,
                         'evidence/bundle.json')['status'], 'BLOCKED')

    def test_all_feature_checks_produce_one_reusable_workflow_bundle(self):
        result = subprocess.run([sys.executable, str(VERIFIER), '--root', str(self.root),
            '--feature', 'native-verification', '--all-checks', '--output', str(self.root / 'evidence/all')],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        verdict = json.loads(result.stdout)
        bundle = Path(verdict['bundle'])
        self.assertEqual(len(json.loads(bundle.read_text())['records']), 1)
        runtime = runpy.run_path(str(ROOT / 'authoring/scripts/project_workflow.py'))
        observed = runtime['inspect_evidence'](self.root,
            {'id': 'native-verification', 'checks': ['fixture']}, {'fixture': self.argv},
            bundle.relative_to(self.root).as_posix())
        self.assertEqual(observed['status'], 'PASS', observed)

    def test_failure_skip_and_zero_tests_never_pass(self):
        for body, expected in [
            ('import unittest\nclass T(unittest.TestCase):\n def test_fail(self): self.fail("defect")\n', 'ISSUES'),
            ('import unittest\n@unittest.skip("unavailable")\nclass T(unittest.TestCase):\n def test_skip(self): pass\n', 'BLOCKED'),
            ('import unittest\n', 'BLOCKED')]:
            with self.subTest(expected=expected, body=body):
                self.suite.write_text(body)
                path = self.root / 'evidence' / (str(len(list(self.root.glob('evidence/*')))) + '.json')
                code, verdict = self.verify('--output', str(path))
                self.assertNotEqual(code, 0)
                self.assertEqual(verdict['status'], expected, verdict)

    def test_unavailable_test_import_is_a_blocker_with_raw_cause(self):
        self.suite.write_text('import missing_task_test_dependency\n')
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual(verdict['status'], 'BLOCKED', verdict)
        self.assertEqual(code, 2)
        self.assertIn('missing_task_test_dependency', self.output.read_text())

    def test_shared_native_check_runs_once_for_selected_features(self):
        project_path = self.root / '.harness/project.yaml'
        project = json.loads(project_path.read_text())
        project['commands']['separate'] = dict(project['commands']['fixture'], id='separate')
        project_path.write_text(json.dumps(project))
        mapping = self.root / 'docs/feature-map.md'
        mapping.write_text(mapping.read_text() +
            '| second | Check | Run | Same shared assertion | tests | evidence | fixture, separate |\n')
        self.suite.write_text('import unittest\nfrom pathlib import Path\n'
            'p=Path("evidence/count"); p.parent.mkdir(exist_ok=True)\n'
            'p.write_text(str(int(p.read_text())+1) if p.exists() else "1")\n'
            'class T(unittest.TestCase):\n def test_value(self): self.assertEqual(2 + 2, 4)\n')
        argv = [sys.executable, str(VERIFIER), '--root', str(self.root), '--features',
                'native-verification', 'second', '--all-checks', '--output', str(self.root / 'evidence/shared')]
        ran = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(ran.returncode, 0, ran.stderr + ran.stdout)
        outcome = json.loads(ran.stdout)
        self.assertEqual((self.root / 'evidence/count').read_text(), '2')
        bundles = {key: json.loads(Path(path).read_text()) for key, path in outcome['bundles'].items()}
        self.assertEqual(bundles['native-verification']['records'][0], bundles['second']['records'][0])
        runtime = runpy.run_path(str(ROOT / 'authoring/scripts/project_workflow.py'))
        for feature, checks in [('native-verification', ['fixture']), ('second', ['fixture', 'separate'])]:
            observed = runtime['inspect_evidence'](self.root, {'id': feature, 'checks': checks},
                project['commands'], Path(outcome['bundles'][feature]).relative_to(self.root).as_posix())
            self.assertEqual(observed['status'], 'PASS', observed)
        self.assertEqual((self.root / 'evidence/count').read_text(), '2', 'Lookup cannot rerun shared checks')
        # A bundle cannot relabel this execution as an unselected consumer.
        forged = dict(bundles['native-verification'], feature='unselected')
        path = self.root / 'evidence/forged.json'
        path.write_text(json.dumps(forged))
        self.assertEqual(runtime['inspect_evidence'](self.root, {'id': 'unselected', 'checks': ['fixture']},
            project['commands'], 'evidence/forged.json')['status'], 'BLOCKED')
        self.suite.write_text(self.suite.read_text().replace('2 + 2, 4', '2 + 2, 400'))
        for feature in outcome['bundles']:
            self.assertEqual(runtime['inspect_evidence'](self.root, {'id': feature, 'checks': ['fixture']},
                project['commands'], Path(outcome['bundles'][feature]).relative_to(self.root).as_posix())['status'], 'BLOCKED')
        argv[-1] = str(self.root / 'evidence/shared-failure')
        failed = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 1, failed.stderr + failed.stdout)
        self.assertEqual(json.loads(failed.stdout)['status'], 'ISSUES')

    def test_scoped_shared_check_unions_distinct_feature_sources(self):
        self.enable_scoped_check()
        project_path = self.root / '.harness/project.yaml'
        project = json.loads(project_path.read_text())
        project['extensions']['workflow']['features'].append({
            'id': 'second', 'partition': 'verification', 'sources': ['other.py'],
            'map': ['docs/feature-map.md'], 'criteria': ['docs/criteria.md'], 'checks': ['fixture']})
        project_path.write_text(json.dumps(project), encoding='utf-8')
        (self.root / 'other.py').write_text('VALUE = 7\n')
        mapping = self.root / 'docs/feature-map.md'
        mapping.write_text(mapping.read_text() +
            '| second | Check | Run | Shared native result | tests | evidence | fixture |\n')
        self.suite.write_text('import unittest\nfrom pathlib import Path\n'
            'from logic import VALUE as LOGIC_VALUE\nfrom other import VALUE as OTHER_VALUE\n'
            'p=Path("evidence/count"); p.parent.mkdir(exist_ok=True)\n'
            'p.write_text(str(int(p.read_text())+1) if p.exists() else "1")\n'
            'class Behavior(unittest.TestCase):\n'
            ' def test_first_source(self): self.assertEqual(LOGIC_VALUE, 42)\n'
            ' def test_second_source(self): self.assertEqual(OTHER_VALUE, 7)\n')
        command = [sys.executable, str(VERIFIER), '--root', str(self.root), '--features',
                   'native-verification', 'second', '--all-checks', '--output',
                   str(self.root / 'evidence/scoped-shared')]
        ran = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(ran.returncode, 0, ran.stderr + ran.stdout)
        outcome = json.loads(ran.stdout)
        self.assertEqual((self.root / 'evidence/count').read_text(), '1',
                         'The shared native check must execute exactly once')
        bundles = {key: json.loads(Path(path).read_text())
                   for key, path in outcome['bundles'].items()}
        first = bundles['native-verification']['records'][0]
        second = bundles['second']['records'][0]
        self.assertEqual(first, second)
        capture = json.loads((self.root / first['path']).read_text())
        self.assertTrue({'logic.py', 'other.py'}.issubset(capture['input_scope']))
        runtime = runpy.run_path(str(ROOT / 'authoring/scripts/project_workflow.py'))
        for feature in ('native-verification', 'second'):
            observed = runtime['inspect_evidence'](
                self.root, {'id': feature, 'checks': ['fixture']}, project['commands'],
                Path(outcome['bundles'][feature]).relative_to(self.root).as_posix())
            self.assertEqual(observed['status'], 'PASS', observed)

    def test_pending_work_selects_only_needed_checks_and_reuses_current_evidence(self, connected=False):
        runtime = runpy.run_path(str(ROOT / 'authoring/scripts/project_workflow.py'))
        self.root.joinpath('.gitignore').write_text('evidence/\n.work/\n__pycache__/\n')
        self.root.joinpath('.work').mkdir()
        project_path = self.root / '.harness/project.yaml'
        project = json.loads(project_path.read_text())
        project['extensions'] = {'workflow': {'roots': ['suite.py'], 'features': [{
            'id': 'native-verification', 'partition': 'verification', 'sources': ['suite.py'],
            'map': ['docs/feature-map.md'], 'criteria': ['docs/feature-map.md'], 'checks': ['fixture']}]}}
        project['commands']['unused'] = dict(project['commands']['fixture'], id='unused',
                                             argv=[sys.executable, '-m', 'unittest', 'must_not_run'])
        self.root.joinpath('other.py').write_text('value = 1\n')
        project['extensions']['workflow']['roots'].append('other.py')
        project['extensions']['workflow']['features'].append({
            'id': 'unaffected', 'partition': 'other', 'sources': ['other.py'],
            'map': ['docs/feature-map.md'], 'criteria': ['docs/feature-map.md'], 'checks': ['unused']})
        mapping = self.root / 'docs/feature-map.md'
        mapping.write_text(mapping.read_text() +
            '| unaffected | Other | Read | One | other | none | unused |\n')
        project_path.write_text(json.dumps(project))
        state = runtime['begin'](self.root, project, 'change')
        self.suite.write_text(self.suite.read_text() + '# implementation changed\n')
        path = self.root / '.work/state.json'
        path.write_text(json.dumps(state))
        command = [sys.executable, str(VERIFIER), '--root', str(self.root), '--pending-state', '.work/state.json',
                   '--all-checks', '--output', str(self.root / 'evidence/pending')]
        if connected:
            binding = runtime['task_context'](self.root, state, path)
            at = command.index('--pending-state')
            command[at:at + 2] = ['--context', binding]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        outcome = json.loads(result.stdout)
        self.assertEqual(outcome['selected_features'], ['native-verification'])
        current = runtime['inspect_project'](self.root, project, state)
        state = runtime['record_review'](self.root, project, state, {
            'feature': 'native-verification', 'basis': current['features'][0]['basis'],
            'analysis': 'Changed implementation checked by the native suite.',
            'references': ['suite.py'], 'findings': [], 'product_findings': ['Separate quality review remains.'],
            'bundle': Path(outcome['bundles']['native-verification']).relative_to(self.root).as_posix()})
        path.write_text(json.dumps(state))
        before = path.read_bytes()
        command[-1] = str(self.root / 'evidence/not-needed')
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        outcome = json.loads(result.stdout)
        self.assertEqual(outcome['status'], 'NOT_REQUIRED')
        self.assertEqual(outcome['workflow_status'], 'PARTIAL', 'Unresolved product gap must stay visible')
        self.assertFalse((self.root / 'evidence/not-needed').exists())
        self.assertEqual(path.read_bytes(), before)
        path.unlink()
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['status'], 'BLOCKED')
        for invalid in ('{}', 'null'):
            path.write_text(invalid)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, 'An empty record is not a zero-impact work baseline')
            self.assertFalse((self.root / 'evidence/not-needed').exists())

    def test_native_unittest_adapter_uses_the_same_connected_request(self):
        self.test_pending_work_selects_only_needed_checks_and_reuses_current_evidence(connected=True)

    def test_stale_source_and_wrong_binding_are_blocked(self):
        record = self.run_check()
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', 'another-run')
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.suite.write_text(self.suite.read_text() + '# changed after execution\n')
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual(verdict['status'], 'BLOCKED')

    def test_untracked_input_byte_change_invalidates_native_capture(self):
        dependency = self.root / 'new_input.py'
        dependency.write_text('value = 10\n')
        self.suite.write_text('import unittest\nfrom new_input import value\n'
                             'class T(unittest.TestCase):\n'
                             ' def test_value(self): self.assertEqual(value, 10)\n')
        record = self.run_check()
        dependency.write_text('value = 11\n')
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual(verdict['status'], 'BLOCKED', verdict)

    def test_declared_scope_reuses_after_unrelated_docs_and_lookup_has_no_side_effects(self):
        self.enable_scoped_check()
        path = self.root / 'evidence/scoped.json'
        code, verdict = self.verify('--output', str(path))
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
        record = json.loads(path.read_text())
        self.assertTrue({'logic.py', 'suite.py', 'deps/helper.py', 'docs/criteria.md',
                         'docs/feature-map.md', '.harness/project.yaml'}.issubset(record['input_scope']))
        (self.root / 'docs/unrelated.md').write_text('A report outside this check.\n')
        self.check_read_only_lookup(path, 'CURRENT')
        self.assertEqual((self.root / 'evidence/count').read_text(), '1')

    def test_declared_scope_invalidates_every_registered_input_and_new_matching_file(self):
        self.enable_scoped_check()
        tracked = ['logic.py', 'suite.py', 'deps/helper.py', 'docs/criteria.md',
                   'docs/feature-map.md', '.harness/project.yaml']
        original = {name: (self.root / name).read_bytes() for name in tracked}
        for index, name in enumerate(tracked):
            with self.subTest(input=name):
                for path, value in original.items():
                    (self.root / path).write_bytes(value)
                evidence = self.root / f'evidence/stale-{index}.json'
                code, verdict = self.verify('--output', str(evidence))
                self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
                target = self.root / name
                if name == 'docs/feature-map.md':
                    target.write_text(target.read_text().replace('| Check |', '| Changed label |'))
                elif name == '.harness/project.yaml':
                    project = json.loads(target.read_text())
                    project['commands']['fixture']['timeout_seconds'] = 321
                    target.write_text(json.dumps(project), encoding='utf-8')
                else:
                    target.write_bytes(target.read_bytes() + b'\n# changed\n')
                code, verdict = self.verify('--evidence', str(evidence),
                                            '--run-id', json.loads(evidence.read_text())['run_id'])
                self.assertEqual(verdict['status'], 'BLOCKED', verdict)
        for path, value in original.items():
            (self.root / path).write_bytes(value)
        evidence = self.root / 'evidence/new-matching-file.json'
        code, verdict = self.verify('--output', str(evidence))
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
        (self.root / 'deps/extra.py').write_text('EXTRA = True\n')
        code, verdict = self.verify('--evidence', str(evidence),
                                    '--run-id', json.loads(evidence.read_text())['run_id'])
        self.assertEqual(verdict['status'], 'BLOCKED', verdict)

    def test_scoped_capture_cannot_omit_registered_inputs(self):
        self.enable_scoped_check()
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
        record = json.loads(self.output.read_text())
        record['input_scope'].remove('suite.py')
        self.output.write_text(json.dumps(record))
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual(verdict['status'], 'BLOCKED', verdict)

    def test_registered_timeout_and_explicit_override_are_applied(self):
        project_path = self.root / '.harness/project.yaml'
        project = json.loads(project_path.read_text())
        project['commands']['fixture']['timeout_seconds'] = 0.15
        project_path.write_text(json.dumps(project), encoding='utf-8')
        self.suite.write_text('import time; time.sleep(0.6)\nimport unittest\n'
                              'class T(unittest.TestCase):\n def test_result(self): self.assertEqual(2 + 2, 4)\n')
        short = self.root / 'evidence/registered-timeout.json'
        code, verdict = self.verify('--output', str(short))
        self.assertNotEqual(code, 0)
        self.assertEqual(verdict['status'], 'BLOCKED', verdict)
        record = json.loads(short.read_text())
        self.assertEqual(record['timeout_seconds'], 0.15)
        self.assertEqual(record['execution'], 'timeout')

        long = self.root / 'evidence/explicit-override.json'
        code, verdict = self.verify('--output', str(long), '--timeout', '3')
        self.assertEqual((code, verdict['status']), (0, 'PASS'), verdict)
        record = json.loads(long.read_text())
        self.assertEqual(record['timeout_seconds'], 3.0)

    def test_unlinked_missing_or_wrong_target_evidence_never_passes(self):
        record = self.run_check()
        for key, value in [('feature', 'another-feature'), ('check', 'another-check'),
                           ('cwd', str(self.root.parent)), ('argv', ['other-tool']),
                           ('execution', 'timeout'), ('execution', 'unavailable')]:
            with self.subTest(key=key, value=value):
                changed = dict(record, **{key: value})
                self.output.write_text(json.dumps(changed))
                code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
                self.assertNotEqual(code, 0)
                self.assertEqual(verdict['status'], 'BLOCKED', verdict)
        self.output.unlink()
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', record['run_id'])
        self.assertEqual(verdict['status'], 'BLOCKED')

    def test_unknown_feature_or_command_does_not_execute(self):
        for args in [('--feature', 'absent'), ('--check', 'absent')]:
            code, verdict = self.verify('--output', str(self.output), *args)
            self.assertEqual(verdict['status'], 'BLOCKED')
            self.assertFalse(self.output.exists())

    def test_existing_output_is_not_reused_as_new_success(self):
        self.run_check()
        original = self.output.read_bytes()
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.assertEqual(self.output.read_bytes(), original)

    def test_source_changed_by_command_cannot_pass(self):
        self.suite.write_text('import unittest\nfrom pathlib import Path\n'
                             'class T(unittest.TestCase):\n'
                             ' def test_changes(self): Path("suite.py").write_text("# mutated")\n')
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual(verdict['status'], 'BLOCKED', verdict)

    def test_map_command_references_are_checked_before_execution(self):
        path = self.root / 'docs/feature-map.md'
        path.write_text(path.read_text().replace('| fixture |', '| missing-command |'))
        code, verdict = self.verify('--output', str(self.output))
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.assertFalse(self.output.exists())

    def test_real_timeout_and_malformed_record_are_blocked(self):
        self.suite.write_text('import time\ntime.sleep(30)\n')
        code, verdict = self.verify('--output', str(self.output), '--timeout', '0.2')
        self.assertEqual(verdict['status'], 'BLOCKED')
        self.output.write_text('[]')
        code, verdict = self.verify('--evidence', str(self.output), '--run-id', 'missing')
        self.assertEqual(verdict['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
