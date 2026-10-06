import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest


@unittest.skipUnless(os.name == 'nt', 'Windows job API')
class WindowsJobTests(unittest.TestCase):
    def test_normal_exit_and_detached_child_cleanup(self):
        spec = importlib.util.spec_from_file_location('windows_job', Path(__file__).resolve().parents[2] / 'scripts/windows_job.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as root:
            result = module.run([], [sys.executable, '-I', '-c', 'print("normal")'], cwd=root, timeout=10)
            self.assertEqual(result['exit'], 0)
            self.assertIn('normal', result['stdout'])
            self.assertEqual(result['remaining'], 0)
            self.assertFalse(result['descendants_killed'])
            command = 'import subprocess,sys; subprocess.Popen([sys.executable,"-I","-c","import time;time.sleep(15)"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL)'
            result = module.run([], [sys.executable, '-I', '-c', command], cwd=root, timeout=10)
            self.assertTrue(result['descendants_killed'])
            self.assertEqual(result['remaining'], 0)
            result = module.run([], [sys.executable, '-I', '-c', 'import time;time.sleep(15)'], cwd=root, timeout=1)
            self.assertTrue(result['timed_out'])
            self.assertEqual(result['remaining'], 0)
            escape = 'import subprocess,sys; subprocess.run([sys.executable,"-I","-c","pass"],creationflags=subprocess.CREATE_BREAKAWAY_FROM_JOB)'
            result = module.run([], [sys.executable, '-I', '-c', escape], cwd=root, timeout=10)
            self.assertNotEqual(result['exit'], 0)
            self.assertIn('PermissionError', result['stderr'])
            self.assertEqual(result['remaining'], 0)
