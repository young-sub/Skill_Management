"""Two real project commands must retain independent proof after cleanup."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'tests/distribution/fixtures/connected_product'
REQUIRED_ENV = 'CONNECTED_PRODUCT_REQUIRED'


class ConnectedProductTests(unittest.TestCase):
    def handle_unavailable_browser(self, raw, report_path):
        if raw['status'] == 'BLOCKED' and not raw['execution']['executed']:
            message = 'browser prerequisite unavailable; report=%s; errors=%s' % (
                report_path, raw['errors'])
            if os.environ.get(REQUIRED_ENV) == '1':
                self.fail('Required connected-product acceptance could not start: ' + message)
            self.skipTest('Optional connected-product run: ' + message)

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
            self.handle_unavailable_browser(raw, path)
            self.assertEqual((result.returncode, raw['status']), (0, 'PASS'), raw['errors'])
            self.assertEqual(raw['counts'], {
                'assertions': 14, 'passed': 14, 'failed': 0, 'skipped': 0, 'errors': 0})
            saved = {r['response_body']['id']: r['response_body']['quantity'] for r in raw['observed']['api_responses']
                     if r['method'] == 'POST' and r['status'] == 201}
            self.assertEqual(saved, {1: 2, 2: 0})
            self.assertEqual(raw['observed']['database']['after_restart']['rows'],
                             [{'id': identity, 'quantity': value} for identity, value in sorted(saved.items())])
            fresh = [r['response_body']['items'] for r in raw['observed']['api_responses'] if r['method'] == 'GET'][-1]
            self.assertEqual(fresh, raw['observed']['database']['after_restart']['rows'])
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

    def test_api_domain_pass_cannot_hide_a_frontend_payload_error(self):
        temporary = ROOT / '.work/connected-product-artifacts' / str(uuid.uuid4())
        project = temporary / 'project'
        shutil.copytree(PROJECT, project, ignore=shutil.ignore_patterns('__pycache__'))
        runner = runpy.run_path(str(project / 'run_project.py'))
        source = project / 'ui.js'
        source.write_text(source.read_text(encoding='utf-8').replace(
            'JSON.stringify({ quantity })', 'JSON.stringify({ quantity: quantity > 0 ? quantity + 1 : quantity })'), encoding='utf-8')
        domain = subprocess.run([sys.executable, 'test_domain.py'], cwd=project, capture_output=True, text=True)
        self.assertEqual(domain.returncode, 0, domain.stderr)
        database, port_file, log_path = (temporary / name for name in ('api.sqlite', 'port.json', 'server.log'))
        service, log = runner['server_process'](project, database, port_file, log_path)
        observations = {'frontend': {'status': 'NOT_REQUIRED', 'reason': 'Direct API-only task'},
                        'domain': domain.stderr, 'responses': [], 'services': []}
        try:
            ready = runner['wait_for_server'](service, port_file)
            for value, status in ((2, 201), (-1, 422), (0, 201)):
                request = urllib.request.Request(ready['url'] + '/api/items',
                    data=json.dumps({'quantity': value}).encode(), headers={'Content-Type': 'application/json'})
                try:
                    response = urllib.request.urlopen(request, timeout=5)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    actual = json.loads(response.read())
                    observations['responses'].append({'input': value, 'status': response.status, 'response': actual})
                    self.assertEqual(response.status, status)
                    if status == 201:
                        self.assertEqual(actual['quantity'], value)
            before = runner['database_rows'](database)
            self.assertEqual(before, [{'id': 1, 'quantity': 2}, {'id': 2, 'quantity': 0}])
            runner['stop_process'](service)
            observations['services'].append({'pid': service.pid, 'exit_code': service.returncode})
            log.close()
            service, log = runner['server_process'](project, database, port_file, log_path)
            restarted = runner['wait_for_server'](service, port_file)
            with urllib.request.urlopen(restarted['url'] + '/api/items', timeout=5) as response:
                fresh = json.loads(response.read())['items']
            observations.update(before_restart=before, fresh_read=fresh, after_restart=runner['database_rows'](database))
            self.assertEqual(fresh, before)
            self.assertEqual(observations['after_restart'], before)
        finally:
            runner['stop_process'](service)
            observations['services'].append({'pid': service.pid, 'exit_code': service.returncode})
            log.close()
            database.unlink(missing_ok=True)
            port_file.unlink(missing_ok=True)
            (temporary / 'api-observations.json').write_text(json.dumps(observations, indent=2), encoding='utf-8')
        report = temporary / 'fault-browser.json'
        process = subprocess.run([sys.executable, 'run_project.py', '--report', str(report)],
                                 cwd=project, capture_output=True, text=True, timeout=180)
        raw = json.loads(report.read_text(encoding='utf-8'))
        self.handle_unavailable_browser(raw, report)
        self.assertEqual((process.returncode, raw['status']), (1, 'ISSUES'), raw['errors'])
        self.assertFalse(raw['observed']['assertions_by_id']['positive_quantity_api_save']['passed'])
        self.assertEqual(raw['observed']['database']['after_restart']['rows'], [{'id': 1, 'quantity': 3}, {'id': 2, 'quantity': 0}])
        self.assertEqual(raw['cleanup']['errors'], [])
        print('Retained API-only / frontend fault proof: ' + str(temporary))
