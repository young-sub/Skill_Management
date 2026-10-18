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
                'assertions': 16, 'passed': 16, 'failed': 0, 'skipped': 0, 'errors': 0})
            saved = {r['response_body']['id']: r['response_body']['quantity'] for r in raw['observed']['api_responses']
                     if r['method'] == 'POST' and r['status'] == 201}
            self.assertEqual(saved, {1: 2, 2: 0})
            self.assertEqual(raw['observed']['database']['after_restart']['rows'],
                             [{'id': identity, 'quantity': value} for identity, value in sorted(saved.items())])
            successful_history_reads = [r['response_body']['items'] for r in raw['observed']['api_responses']
                                        if r['method'] == 'GET' and r['status'] == 200 and
                                        isinstance(r['response_body'], dict) and 'items' in r['response_body']]
            self.assertTrue(successful_history_reads)
            fresh = successful_history_reads[-1]
            self.assertEqual(fresh, raw['observed']['database']['after_restart']['rows'])
            self.assertFalse(Path(raw['execution']['database_path']).exists())
            self.assertEqual(raw['cleanup']['errors'], [])
            self.assertEqual([service['status'] for service in raw['observed']['services']],
                             ['stopped', 'stopped'])
            self.assertTrue(all(isinstance(service.get('exit_code'), int)
                                for service in raw['observed']['services']))
            self.assertEqual({artifact['kind'] for artifact in raw['artifacts'] if 'screenshot' in artifact['kind']}, {
                'entry_desktop_screenshot', 'entry_mobile_screenshot',
                'history_desktop_screenshot', 'history_mobile_screenshot',
                'history_mobile_after_restart_screenshot'})
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
        temporary.mkdir(parents=True)
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

    def test_shared_ui_accepts_larger_token_and_rejects_focus_drift(self):
        temporary = ROOT / '.work/connected-product-artifacts/style-variants' / str(uuid.uuid4())
        temporary.mkdir(parents=True)
        variants = (
            ('larger-token', '--control-size: 44px;', '--control-size: 48px;', 'PASS'),
            ('history-focus-defect', None,
             '\n@media (min-width: 43rem) { app-nav[active="history"] .site-nav :focus-visible { outline: none !important; } }\n',
             'ISSUES'),
        )
        for name, original, mutation, expected_status in variants:
            variant_root = temporary / name
            variant_root.mkdir()
            project = variant_root / 'project'
            shutil.copytree(PROJECT, project, ignore=shutil.ignore_patterns('__pycache__'))
            styles = project / 'shared.css'
            css = styles.read_text(encoding='utf-8')
            if original:
                self.assertEqual(css.count(original), 1)
                css = css.replace(original, mutation)
            else:
                css += mutation
            styles.write_text(css, encoding='utf-8')
            report = temporary / name / 'browser.json'
            result = subprocess.run([sys.executable, 'run_project.py', '--report', str(report)],
                                    cwd=project, capture_output=True, text=True, timeout=180)
            self.assertTrue(report.is_file(), result.stderr)
            raw = json.loads(report.read_text(encoding='utf-8'))
            self.handle_unavailable_browser(raw, report)
            expected_code = 0 if expected_status == 'PASS' else 1
            self.assertEqual((result.returncode, raw['status']), (expected_code, expected_status), raw['errors'])
            self.assertEqual(raw['cleanup']['errors'], [])
            ui = raw['observed']['browser']['before_restart']['shared_ui']
            decision = raw['observed']['assertions_by_id']['shared_ui_mobile_acceptance']
            if expected_status == 'PASS':
                self.assertTrue(decision['passed'])
                self.assertEqual(ui['desktop']['entry']['control_size_token'], '48px')
                self.assertTrue(ui['acceptance']['targets_meet_token'])
            else:
                self.assertFalse(decision['passed'])
                self.assertFalse(ui['acceptance']['focus_visible_on_both_routes'])
                self.assertTrue(ui['desktop']['entry']['keyboard_focus']['focus_visible'])
                self.assertEqual(ui['desktop']['history']['keyboard_focus']['outline_style'], 'none')
                self.assertTrue(ui['mobile']['history']['keyboard_focus']['focus_visible'])
                self.assertEqual([check['id'] for check in raw['checks'] if not check['passed']],
                                 ['shared_ui_mobile_acceptance'])
        print('Retained shared UI intended-style/focus-defect proof: ' + str(temporary))
