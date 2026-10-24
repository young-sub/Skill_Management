"""Read-only workflow entrypoints survive every project shape and keep non-ASCII text intact."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'authoring/scripts/project_workflow.py'
HOOK = ROOT / 'authoring/scripts/workflow_context.py'
GUARD = ROOT / 'authoring/scripts/completion_guard.py'
OUTCOME = '저장한 가격을 다시 읽으면 10원이다'


def environment():
    env = {k: v for k, v in os.environ.items() if k not in ('AGENT_WORKFLOW_CONTEXT', 'PYTHONIOENCODING', 'PYTHONUTF8')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


class WorkflowRobustnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def project(self, kind):
        root = Path(self.temp.name) / kind
        files = {'src/api.py': 'price = 10\n', 'docs/map.md': 'price\n', 'docs/req.md': 'price is ten\n',
                 '.gitignore': '.work/\n'}
        if kind == 'unconfigured':
            files['.harness/project.yaml'] = json.dumps({'commands': {'test': {'argv': ['python', '-V']}}})
        if kind == 'configured':
            files['.harness/project.yaml'] = json.dumps({'commands': {'check': {'argv': ['python', '-V']}},
                'extensions': {'workflow': {'roots': ['src'], 'features': [
                    {'id': 'api', 'partition': 'service', 'sources': ['src/api.py'], 'map': ['docs/map.md'],
                     'criteria': ['docs/req.md'], 'checks': ['check'],
                     'coverage': [{'id': 'saved-price', 'requirement': 'docs/req.md', 'outcome': OUTCOME,
                                   'perspectives': ['business'], 'areas': ['Domain'], 'kind': 'test', 'check': 'check'}]}]}}},
                ensure_ascii=False)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        for argv in (['git', 'init', '-q'], ['git', 'add', '.'],
                     ['git', '-c', 'user.name=F', '-c', 'user.email=f@invalid', 'commit', '-qm', 'base']):
            subprocess.run(argv, cwd=root, check=True, capture_output=True)
        return root

    def legacy_state(self, root):
        sys.path.insert(0, str(SCRIPT.parent))
        import project_workflow as runtime
        project_file = root / '.harness/project.yaml'
        project = json.loads(project_file.read_text(encoding='utf-8')) if project_file.exists() else {}
        intent = 'init' if runtime.configuration(project) is not None else 'diagnose'
        state = runtime.begin(root, project, intent, request_summary='Survey current verification')
        for key in ('results', 'feedback', 'task_id'):
            state.pop(key, None)
        path = root / '.work/project-verification/state.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(state), encoding='utf-8')
        return '.work/project-verification/state.json'

    def run_cli(self, root, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args, '--root', str(root)],
                              capture_output=True, env=environment(), timeout=120)

    def test_read_only_actions_never_crash_on_any_project_shape(self):
        for kind in ('empty', 'unconfigured', 'configured'):
            root = self.project(kind)
            state = self.legacy_state(root)
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
            for action in ('lookup', 'resume', 'audit', 'maintain'):
                selector = ['--state', state] if action in ('lookup', 'resume') else []
                for mode in ([], ['--summary'], ['--report']):
                    if mode and action == 'maintain':
                        continue
                    with self.subTest(kind=kind, action=action, mode=mode):
                        process = self.run_cli(root, action, *selector, *mode)
                        self.assertNotIn(b'Traceback', process.stderr, process.stderr.decode('utf-8', 'replace'))
                        text = process.stdout.decode('utf-8')
                        if mode == ['--report']:
                            self.assertTrue(text.startswith('# Verification report'), text[:200])
                            continue
                        result = json.loads(text)
                        crash = [f for f in result.get('findings', []) if 'NoneType' in f or 'attribute' in f]
                        self.assertEqual(crash, [], result)
                        if kind == 'configured':
                            self.assertEqual(result.get('connection'), 'CONNECTED')
                        else:
                            self.assertEqual(process.returncode, 3, result)
                            self.assertEqual(result.get('connection', result.get('maintenance', {}).get('status')),
                                             'NOT_CONNECTED' if action != 'maintain' else 'NOT_CONNECTED')
            after = {p: p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
            self.assertEqual(before, after, kind)

    def test_report_bytes_are_utf8_and_unconnected_report_says_so(self):
        root = self.project('configured')
        state = self.legacy_state(root)
        report = self.run_cli(root, 'lookup', '--state', state, '--report')
        self.assertIn(OUTCOME, report.stdout.decode('utf-8'))
        unconnected = self.run_cli(self.project('unconfigured'), 'audit', '--report')
        self.assertIn('Verification is not connected', unconnected.stdout.decode('utf-8'))
        self.assertEqual(unconnected.returncode, 3)

    def test_observed_scenario_prompts_route_to_the_expected_skill(self):
        import runpy
        route = runpy.run_path(str(HOOK))['request_route']
        prompts = json.loads((ROOT / 'tests/distribution/fixtures/route_prompts.json').read_text(encoding='utf-8'))
        for name, (prompt, expected) in prompts.items():
            with self.subTest(name=name):
                self.assertEqual((route(prompt) or {}).get('skill'), expected)
        heldout = json.loads((ROOT / 'tests/distribution/fixtures/route_heldout.json').read_text(encoding='utf-8'))
        for prompt, expected in heldout['prompts']:
            with self.subTest(prompt=prompt):
                self.assertEqual((route(prompt) or {}).get('skill'), expected)
        categories = {'bug': 'diagnose', 'change': 'agent-workflow', 'trivial': None, 'results': 'agent-workflow',
                      'connect': 'setup-project-verification', 'ui': 'agent-workflow',
                      'guardrail': 'agent-workflow', 'resume': 'recall'}
        fresh = json.loads((ROOT / 'tests/distribution/fixtures/route_fresh.json').read_text(encoding='utf-8'))
        for prompt, category in fresh['prompts']:
            with self.subTest(prompt=prompt):
                self.assertEqual((route(prompt) or {}).get('skill'), categories[category])
        fresh2 = json.loads((ROOT / 'tests/distribution/fixtures/route_fresh2.json').read_text(encoding='utf-8'))
        loaded = [bool(route(prompt)) for prompt, category in fresh2['prompts'] if category != 'trivial']
        self.assertGreaterEqual(sum(loaded), len(loaded) - 1, 'non-trivial work loads the plugin')
        self.assertFalse(any(route(prompt) for prompt, category in fresh2['prompts'] if category == 'trivial'))
        for kind in ('unconfigured', 'configured'):
            root = self.project(kind)
            prompt = prompts['L1 customer complaint'][0]
            payload = json.dumps({'cwd': str(root), 'hook_event_name': 'UserPromptSubmit', 'prompt': prompt},
                                 ensure_ascii=False).encode('utf-8')
            process = subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True,
                                     env=environment(), timeout=60)
            context = json.loads(json.loads(process.stdout)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
            with self.subTest(kind=kind):
                self.assertEqual(context['route']['skill'], 'diagnose')

    def test_hooks_decode_raw_utf8_korean_payloads(self):
        root = self.project('unconfigured')
        for prompt, expected in (('상품 저장 버그 고쳐줘', True), ('오늘 점심 메뉴 추천해줘', False)):
            payload = json.dumps({'cwd': str(root), 'hook_event_name': 'UserPromptSubmit', 'prompt': prompt},
                                 ensure_ascii=False).encode('utf-8')
            process = subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True,
                                     env=environment(), timeout=60)
            output = json.loads(process.stdout)
            with self.subTest(prompt=prompt):
                if expected:
                    context = json.loads(output['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
                    self.assertEqual(context['route']['skill'], 'diagnose')
                else:
                    self.assertEqual(output, {})
        korean = Path(self.temp.name) / '한글 프로젝트'
        korean.mkdir()
        transcript = korean / 't.jsonl'
        transcript.write_text('\n'.join(json.dumps(e, ensure_ascii=False) for e in (
            {'type': 'user', 'message': {'content': '고쳐줘'}},
            {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit',
                'input': {'file_path': str(korean / 'app.py')}}]}})), encoding='utf-8')
        payload = json.dumps({'cwd': str(korean), 'transcript_path': str(transcript), 'stop_hook_active': False},
                             ensure_ascii=False).encode('utf-8')
        process = subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True,
                                 env=environment(), timeout=60)
        self.assertEqual(json.loads(process.stdout).get('decision'), 'block', process.stdout)


if __name__ == '__main__':
    unittest.main()
