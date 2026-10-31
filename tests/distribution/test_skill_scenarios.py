"""The paid scenario gate judges observed facts; its logic is checked without model runs."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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

    def test_clone_disables_git_longpaths_checks_out_fixed_ref_and_skips_source_modules(self):
        project = self.root / 'source'
        project.mkdir()
        subprocess.run(['git', 'init', '-q', str(project)], check=True)
        def git(*args):
            return subprocess.run(['git', *args], cwd=project, check=True, capture_output=True, text=True)
        git('-c', 'user.name=test', '-c', 'user.email=test@invalid', 'commit', '--allow-empty', '-qm', 'short ref')
        short_ref = git('rev-parse', 'HEAD').stdout.strip()
        long_path = 'public/audio/app.summaryAnswers.protectionComfort/zh-Hans/' + 'a' * 64 + '.mp3'
        long_file = project / Path(long_path)
        long_file.parent.mkdir(parents=True)
        long_file.write_bytes(b'long-path-content')
        git('add', '--', long_path)
        git('-c', 'user.name=test', '-c', 'user.email=test@invalid', 'commit', '-qm', 'long HEAD')
        modules = project / 'node_modules'
        modules.mkdir()
        (modules / 'keep.txt').write_text('source dependency', encoding='utf-8')
        destination = self.root / 'clone'
        commands = []
        real_run = subprocess.run

        def capture(command, *args, **kwargs):
            commands.append(command)
            return real_run(command, *args, **kwargs)

        with patch('subprocess.run', side_effect=capture):
            gate['clone'](project, destination, ref=short_ref, link_modules=False)

        self.assertEqual(commands[0][:8], ['git', '-c', 'core.longpaths=false', 'clone', '-q',
                                           '--local', '--no-hardlinks', '--no-checkout'])
        self.assertIn('--no-checkout', commands[0])
        self.assertTrue(any(command[-3:] == ['checkout', '--detach', short_ref] for command in commands))
        head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=destination,
                              check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(head, short_ref)
        self.assertFalse((destination / Path(long_path)).exists())
        self.assertFalse((destination / 'node_modules').exists())
        self.assertEqual((modules / 'keep.txt').read_text(encoding='utf-8'), 'source dependency')

    def test_fixed_scenarios_are_valid_and_dry_run_spends_nothing(self):
        data = json.loads((ROOT / 'tests/scenarios/skill_routing.json').read_text(encoding='utf-8'))
        ids = [s['id'] for s in data['scenarios']]
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in data['scenarios']:
            with self.subTest(scenario=scenario['id']):
                self.assertIn('skill', scenario['expect'])
                self.assertNotIn('route', scenario['expect'], 'The prompt hook no longer routes')
        process = subprocess.run([sys.executable, str(RUNNER), '--scenarios', str(ROOT / 'tests/scenarios/skill_routing.json'),
                                  '--output', str(self.root / 'never'), '--dry-run'], capture_output=True, timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual([s['id'] for s in json.loads(process.stdout)], ids)
        self.assertFalse((self.root / 'never').exists())


if __name__ == '__main__':
    unittest.main()
