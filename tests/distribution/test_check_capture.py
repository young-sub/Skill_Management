from pathlib import Path
import contextlib
import hashlib
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

RUNNER = Path(__file__).resolve().parents[2] / 'scripts/run_check.py'

class CheckCaptureTests(unittest.TestCase):
    def test_native_json_report_is_captured_with_exit_and_no_verdict(self):
        for native_exit in (0, 7):
            with self.subTest(native_exit=native_exit), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                record, report = root / 'execution.json', root / 'native.json'
                command = 'from pathlib import Path; import json; Path("native.json").write_text(json.dumps({"tests": 2, "passed": 1}), encoding="utf-8"); raise SystemExit(' + str(native_exit) + ')'
                result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp,
                                         '--output', str(record), '--json-report', str(report),
                                         '--', sys.executable, '-c', command], capture_output=True)
                self.assertTrue(record.exists(), result.stderr)
                data = json.loads(record.read_text(encoding='utf-8'))
                self.assertEqual((result.returncode, data['exit_code']), (native_exit, native_exit))
                self.assertEqual(data['json_report']['data'], {'tests': 2, 'passed': 1})
                self.assertEqual(data['json_report']['sha256'], hashlib.sha256(report.read_bytes()).hexdigest())
                self.assertEqual(data['json_report']['path'], str(report.resolve()))
                self.assertIsNone(data['behavior_verdict'])

    def test_preexisting_json_report_cannot_be_reused_or_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / 'old.json'
            report.write_text('{"success":true}', encoding='utf-8')
            result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp,
                                     '--output', str(root / 'run.json'), '--json-report', str(report),
                                     '--', sys.executable, '-c', 'from pathlib import Path; Path("executed").touch()'], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / 'executed').exists())
            self.assertFalse((root / 'run.json').exists())
            self.assertEqual(report.read_text(), '{"success":true}')

    def test_missing_or_malformed_json_report_preserves_execution_and_records_error(self):
        for command in ('pass', 'from pathlib import Path; Path("native.json").write_text("broken")'):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                record = root / 'run.json'
                result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp,
                                         '--output', str(record), '--json-report', str(root / 'native.json'),
                                         '--', sys.executable, '-c', command], capture_output=True)
                self.assertTrue(record.exists(), result.stderr)
                data = json.loads(record.read_text())
                self.assertEqual((result.returncode, data['exit_code']), (0, 0))
                self.assertTrue(data['json_report']['error'])
                self.assertIsNone(data['json_report']['data'])
                self.assertIsNone(data['behavior_verdict'])

    def test_capture_binds_a_unique_run_to_check_and_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / 'execution.json'
            result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp,
                                     '--output', str(record), '--feature', 'native-verification',
                                     '--check', 'fixture', '--', sys.executable, '-c', "print('observed')"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(record.read_text())
            self.assertEqual(data['run_id'], json.loads(result.stdout)['run_id'])
            self.assertEqual((data['feature'], data['check']), ('native-verification', 'fixture'))

    def test_nonfinite_timeout_does_not_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp,
                                     '--output', str(Path(tmp) / 'run.json'), '--timeout', 'nan',
                                     '--', sys.executable, '-c', "print('should not run')"], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((Path(tmp) / 'run.json').exists())

    def test_first_run_creates_output_parents_and_captures_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / 'new' / 'nested' / 'execution.json'
            result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp, '--output', str(record), '--', sys.executable, '-c', "print('first run'); raise SystemExit(7)"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 7, result.stderr)
            data = json.loads(record.read_text(encoding='utf-8'))
            self.assertEqual((data['execution'], data['exit_code']), ('exited', 7))
            self.assertIn('first run', data['stdout'])
            self.assertIsNone(data['behavior_verdict'])

    def run_capture(self, command, env=None):
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / 'execution.json'
            result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp, '--output', str(record), '--', *command], capture_output=True, text=True, env=env)
            self.assertTrue(record.exists(), result.stderr)
            return result.returncode, json.loads(record.read_text(encoding='utf-8'))

    def test_zero_exit_is_execution_only_even_for_fake_passed_and_zero_tests(self):
        code, record = self.run_capture([sys.executable, '-c', "print('passed; Ran 0 tests; OK')"])
        self.assertEqual(code, 0)
        self.assertEqual(record['execution'], 'exited')
        self.assertIsNone(record['behavior_verdict'])
        self.assertIn('Ran 0 tests', record['stdout'])
        self.assertEqual(record['argv'][0], sys.executable)

    def test_nonzero_exit_and_missing_tool_are_different(self):
        code, record = self.run_capture([sys.executable, '-c', 'raise SystemExit(7)'])
        self.assertEqual((code, record['exit_code'], record['execution']), (7, 7, 'exited'))
        code, record = self.run_capture(['a-tool-that-does-not-exist-7239'])
        self.assertNotEqual(code, 0)
        self.assertEqual(record['execution'], 'unavailable')
        self.assertIsNone(record['exit_code'])

    def test_command_runs_without_git_installed(self):
        env = dict(os.environ, PATH='')
        code, record = self.run_capture([sys.executable, '-c', "print('observed')"], env=env)
        self.assertEqual(code, 0)
        self.assertIsNone(record['before'])
        self.assertIn('observed', record['stdout'])

    def test_timeout_records_incomplete_execution_and_stops_owned_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / 'execution.json'
            result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp, '--output', str(record), '--timeout', '0.2', '--', sys.executable, '-c', "import time; print('started', flush=True); time.sleep(30)"], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 124)
            data = json.loads(record.read_text(encoding='utf-8'))
            self.assertEqual(data['execution'], 'timeout')
            self.assertIsNone(data['behavior_verdict'])
            self.assertIn('started', data['stdout'])

    @unittest.skipUnless(os.name == 'nt', 'Windows taskkill')
    def test_timeout_keeps_taskkill_failure_output_and_cleanup_error(self):
        for failure in ('result', 'oserror'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                record = root / 'execution.json'
                with mock.patch.object(sys, 'path', [str(RUNNER.parent), *sys.path]):
                    runner = runpy.run_path(str(RUNNER), run_name='run_check_test')
                runner_subprocess = runner['subprocess']
                original_run = runner_subprocess.run

                def run(argv, *args, **kwargs):
                    if argv and argv[0] == 'taskkill':
                        if failure == 'oserror':
                            raise PermissionError('taskkill denied by test')
                        return subprocess.CompletedProcess(
                            argv, 5, stdout='taskkill output', stderr='taskkill error')
                    return original_run(argv, *args, **kwargs)

                args = [str(RUNNER), '--cwd', str(root), '--output', str(record),
                        '--timeout', '0.1', '--', sys.executable, '-c',
                        'import time; time.sleep(30)']
                with mock.patch.object(runner_subprocess, 'run', side_effect=run), \
                     mock.patch.object(sys, 'argv', args), \
                     contextlib.redirect_stdout(io.StringIO()):
                    code = runner['main']()

                data = json.loads(record.read_text(encoding='utf-8'))
                self.assertEqual(code, 124)
                self.assertEqual((data['execution'], data['exit_code']), ('timeout', None))
                cleanup = data['timeout_tree_cleanup']
                self.assertEqual(cleanup['command'][0], 'taskkill')
                self.assertEqual(cleanup['status'], 'failed')
                self.assertTrue(data['cleanup_incomplete'])
                self.assertEqual(data['timeout_tree_cleanup_exit'], 5 if failure == 'result' else None)
                if failure == 'oserror':
                    self.assertIn('taskkill denied by test', cleanup['error'])
                else:
                    self.assertEqual((cleanup['stdout'], cleanup['stderr']),
                                     ('taskkill output', 'taskkill error'))

    def test_timeout_stops_owned_child_activity_and_preserves_unrelated_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / 'child.py'
            child.write_text('from pathlib import Path\nimport time\n'
                             'for count in range(300):\n'
                             ' Path("heartbeat").write_text(str(count))\n time.sleep(.1)\n')
            unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
            child_pid = None
            try:
                record = root / 'execution.json'
                result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp,
                                         '--output', str(record), '--timeout', '1', '--',
                                         sys.executable, '-c',
                                         'import subprocess,sys,time; '
                                         'p=subprocess.Popen([sys.executable,"child.py"]); '
                                         'from pathlib import Path; Path("child-pid").write_text(str(p.pid)); '
                                         'print(p.pid,flush=True); time.sleep(30)'],
                                        capture_output=True, timeout=12)
                data = json.loads(record.read_text())
                child_pid = int((root / 'child-pid').read_text())
                self.assertEqual(result.returncode, 124)
                self.assertEqual(data['timeout_tree_cleanup_exit'], 0)
                cleanup = data['timeout_tree_cleanup']
                self.assertEqual(cleanup['command'][0], 'taskkill')
                self.assertEqual((cleanup['status'], cleanup['exit_code']), ('succeeded', 0))
                self.assertIsInstance(cleanup['stdout'], str)
                self.assertIsInstance(cleanup['stderr'], str)
                heartbeat = (root / 'heartbeat').read_text()
                time.sleep(.3)
                self.assertEqual((root / 'heartbeat').read_text(), heartbeat)
                self.assertIsNone(unrelated.poll())
            finally:
                unrelated.kill()
                unrelated.wait()
                if child_pid is not None and os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(child_pid), '/T', '/F'], capture_output=True)

    def test_existing_evidence_is_not_overwritten_or_command_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / 'execution.json'
            record.write_text('original', encoding='utf-8')
            marker = Path(tmp) / 'should-not-exist'
            result = subprocess.run([sys.executable, str(RUNNER), '--cwd', tmp, '--output', str(record), '--', sys.executable, '-c', "from pathlib import Path; Path('should-not-exist').touch()"], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(record.read_text(), 'original')
            self.assertFalse(marker.exists())

if __name__ == '__main__':
    unittest.main()
