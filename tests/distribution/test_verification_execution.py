import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "authoring" / "scripts" / "verification_results.py"
RUN_CHECK = ROOT / "scripts" / "run_check.py"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VerificationExecutionTests(unittest.TestCase):
    def test_registered_report_directory_runs_twice_without_configuration_edits(self, subdirectory=False):
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
        bundles = []
        for name in ('first', 'second'):
            output = self.project / f'.work/{name}/plan.json'
            if name == 'first':
                prepared = subprocess.run([sys.executable, str(VIEWER), '--prepare', str(spec),
                    '--root', str(self.project), '--plan-output', str(output),
                    '--report-dir', f'.work/{name}/native'], capture_output=True, text=True)
                self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
                self.assertEqual(json.loads(prepared.stdout)['test_commands_executed'], 0)
            else:
                api['prepare_plan'](self.project, spec, output, report_dir=Path(f'.work/{name}/native'))
            result = api['execute_plan'](output, run_check_path=RUN_CHECK,
                                         evidence_dir=self.project / f'.work/{name}/evidence')
            self.assertEqual(result['status'], 'PASS', result)
            self.assertEqual(result['test_commands_executed'], 1)
            bundle = result['execution']['bundle_path']
            self.assertEqual(workflow['inspect_evidence'](
                self.project, feature, config['commands'], str(Path(bundle).relative_to(self.project)))['status'], 'PASS')
            bundles.append(bundle)
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        for bundle in bundles:
            looked_up = api['view_bundle'](bundle)
            self.assertEqual(looked_up['status'], 'PASS', looked_up)
            self.assertEqual(looked_up['test_commands_executed'], 0)
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
