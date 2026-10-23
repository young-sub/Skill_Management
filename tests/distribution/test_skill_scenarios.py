"""The paid scenario gate judges observed facts; its logic is checked without model runs."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'scripts/run_skill_scenarios.py'
gate = runpy.run_path(str(RUNNER))


def hook(name, output):
    return {'type': 'system', 'subtype': 'hook_response', 'hook_name': name, 'output': output}


class SkillScenarioGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def transcript(self, events):
        path = self.root / 'session.jsonl'
        path.write_text('\n'.join(json.dumps(e, ensure_ascii=False) for e in events), encoding='utf-8')
        return path

    def test_session_facts_and_judgement(self):
        context = 'header\n' + json.dumps({'status': 'NOT_CONFIGURED', 'route': {'skill': 'diagnose'}})
        path = self.transcript([
            hook('UserPromptSubmit', json.dumps({'hookSpecificOutput': {'additionalContext': context}})),
            {'type': 'assistant', 'message': {'content': [
                {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'agentic-coding:diagnose'}},
                {'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'npm test'}}]}},
            hook('Stop', json.dumps({'decision': 'block', 'reason': 'x'})), hook('Stop', '{}'),
            {'type': 'result', 'num_turns': 3, 'total_cost_usd': 0.5, 'duration_ms': 4000, 'result': '연결되지 않음'}])
        facts = gate['summarize_session'](path)
        self.assertEqual((facts['plugin_skills'], facts['routes'], facts['stop_blocks']), (['diagnose'], ['diagnose'], 1))
        self.assertEqual(gate['judge']({'skill': 'diagnose', 'route': 'diagnose', 'answer_mentions': ['연결']}, facts), [])
        self.assertTrue(gate['judge']({'skill': 'agent-workflow'}, facts))
        self.assertTrue(gate['judge']({'skill': None, 'no_plugin_skill': True}, facts))
        self.assertTrue(gate['judge']({'skill': 'diagnose', 'route': None}, facts))
        self.assertTrue(gate['judge']({'skill': 'diagnose', 'answer_mentions': ['setup']}, facts))

    def test_probe_restores_bytes_and_reports_detection(self):
        target = self.root / 'rule.py'
        target.write_bytes(b'LIMIT = 3\r\n')
        check = f'"{sys.executable}" -c "import sys; sys.exit(0 if open(\'rule.py\').read().strip() == \'LIMIT = 3\' else 1)"'
        caught = gate['run_probe'](self.root, {'name': 'limit', 'file': 'rule.py', 'find': 'LIMIT = 3',
                                              'replace': 'LIMIT = 4', 'command': check}, 60)
        self.assertEqual((caught['detected'], caught['ok']), (True, True))
        self.assertEqual(target.read_bytes(), b'LIMIT = 3\r\n')
        missed = gate['run_probe'](self.root, {'name': 'noop', 'file': 'rule.py', 'find': 'LIMIT', 'replace': 'LIMIT',
                                              'command': check}, 60)
        self.assertEqual((missed['detected'], missed['ok']), (False, False))
        with self.assertRaises(ValueError):
            gate['run_probe'](self.root, {'name': 'absent', 'file': 'rule.py', 'find': 'MISSING', 'replace': 'x',
                                          'command': check}, 60)

    def test_fixed_scenarios_are_valid_and_dry_run_spends_nothing(self):
        data = json.loads((ROOT / 'tests/scenarios/skill_routing.json').read_text(encoding='utf-8'))
        ids = [s['id'] for s in data['scenarios']]
        self.assertEqual(len(ids), len(set(ids)))
        route = runpy.run_path(str(ROOT / 'authoring/scripts/workflow_context.py'))['request_route']
        for scenario in data['scenarios']:
            with self.subTest(scenario=scenario['id']):
                self.assertIn('skill', scenario['expect'])
                self.assertEqual((route(scenario['prompt']) or {}).get('skill'), scenario['expect'].get('route'))
        process = subprocess.run([sys.executable, str(RUNNER), '--scenarios', str(ROOT / 'tests/scenarios/skill_routing.json'),
                                  '--output', str(self.root / 'never'), '--dry-run'], capture_output=True, timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual([s['id'] for s in json.loads(process.stdout)], ids)
        self.assertFalse((self.root / 'never').exists())


if __name__ == '__main__':
    unittest.main()
