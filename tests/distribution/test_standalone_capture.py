"""Install only one Skill, then execute and resume without a capture override."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.distribution import test_verification_execution as execution


class StandaloneCaptureTests(unittest.TestCase):
    def test_single_skill_executes_and_resumes_without_external_tool(self):
        for skill in ('agent-workflow', 'setup-project-verification',
                      'maintain-project-verification', 'execute-codex-goal',
                      'close-goal', 'maintain-agent-harness'):
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as temporary:
                fixture = execution.VerificationExecutionTests()
                fixture.setUp()
                try:
                    installed = Path(temporary) / skill
                    shutil.copytree(execution.ROOT / 'skills' / skill, installed)
                    plan = fixture._plan()
                    argv = [sys.executable, str(installed / 'scripts/verification_results.py'),
                            '--execute', '--plan', str(plan), '--evidence-dir', str(fixture.evidence)]
                    first = subprocess.run(argv, cwd=temporary, capture_output=True, text=True)
                    self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
                    result = json.loads(first.stdout)
                    self.assertEqual(result['status'], 'PASS', result)
                    self.assertEqual(result['test_commands_executed'], 1)
                    before = {p: p.read_bytes() for p in fixture.evidence.rglob('*') if p.is_file()}
                    resumed = subprocess.run(argv + ['--resume'], cwd=temporary,
                                             capture_output=True, text=True)
                    self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
                    self.assertEqual(json.loads(resumed.stdout)['test_commands_executed'], 0)
                    self.assertEqual(before, {p: p.read_bytes() for p in before})
                finally:
                    fixture.tearDown()
