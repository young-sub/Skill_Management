"""Two real project commands must retain independent proof after cleanup."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'tests/distribution/fixtures/connected_product'


class ConnectedProductTests(unittest.TestCase):
    def test_two_reports_retain_actual_artifacts_and_refuse_overwrite(self):
        work = ROOT / '.work'
        work.mkdir(exist_ok=True)
        temporary = work / 'connected-product-artifacts' / str(uuid.uuid4())
        temporary.mkdir(parents=True)
        self.assertTrue(temporary.resolve().is_relative_to(work.resolve()))
        reports = []
        for name in ('browser.json', 'second-browser.json'):
            path = Path(temporary) / name
            command = [sys.executable, str(PROJECT / 'run_project.py'), '--report', str(path)]
            result = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True, timeout=180)
            self.assertTrue(path.is_file(), result.stderr)
            raw = json.loads(path.read_text(encoding='utf-8'))
            if raw['status'] == 'BLOCKED' and not raw['execution']['executed']:
                self.skipTest('Existing browser prerequisite unavailable: ' + str(raw['errors']))
            self.assertEqual((result.returncode, raw['status']), (0, 'PASS'), raw['errors'])
            self.assertEqual(raw['counts']['assertions'], 14)
            self.assertFalse(Path(raw['execution']['database_path']).exists())
            self.assertEqual(raw['cleanup']['errors'], [])
            self.assertEqual([service['status'] for service in raw['observed']['services']],
                             ['stopped', 'stopped'])
            self.assertTrue(all(isinstance(service.get('exit_code'), int)
                                for service in raw['observed']['services']))
            reports.append(raw)
        self.assertTrue({a['path'] for a in reports[0]['artifacts']}.isdisjoint(
            {a['path'] for a in reports[1]['artifacts']}))
        for raw in reports:
            for artifact in raw['artifacts']:
                self.assertEqual(hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest(), artifact['sha256'])
        before = {str(p): p.read_bytes() for p in Path(temporary).rglob('*') if p.is_file()}
        refused = subprocess.run(command, cwd=PROJECT, capture_output=True, timeout=30)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(before, {str(p): p.read_bytes() for p in Path(temporary).rglob('*') if p.is_file()})
        print("Retained browser regression proof: " + str(temporary))
