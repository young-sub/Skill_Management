"""Real subprocess/protocol controls; the server fixture is not a model evaluation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[2] / 'scripts/run_benchmark_agent.py'


class BenchmarkAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.server = self.root / 'server.py'
        self.server.write_text('''import json, sys
for line in sys.stdin:
    r=json.loads(line)
    if 'id' not in r: continue
    m=r['method']; p=r.get('params', {})
    if m=='initialize': value={'userAgent':'fixture'}
    elif m=='skills/list': value={'data':[]}
    elif m=='hooks/list': value={'hooks':[]}
    elif m=='thread/start':
        value={'thread':{'id':str(r['id'])},'cwd':p['cwd'],'model':p['model'], 'reasoningEffort':p['config']['model_reasoning_effort']}
    elif m=='turn/start': value={'turn':{'id':'turn','status':'inProgress'}}
    else: value={}
    print(json.dumps({'id':r['id'],'result':value}),flush=True)
    if m=='turn/start':
        print(json.dumps({'method':'thread/tokenUsage/updated','params':{'threadId':p['threadId'],'tokenUsage':{'total':{'inputTokens':10,'cachedInputTokens':2,'outputTokens':3,'reasoningOutputTokens':1,'totalTokens':13}}}}),flush=True)
        print(json.dumps({'method':'turn/completed','params':{'threadId':p['threadId'],'turn':{'id':'turn','status':'completed'}}}),flush=True)
''', encoding='utf-8')
        self.manifest = {
            'format': 'codex-benchmark-agent-v1', 'task_id': 'synthetic-protocol-control',
            'condition': 'A', 'cwd': str(self.root), 'timeout_seconds': 10,
            'model': 'gpt-6-luna', 'reasoning_effort': 'medium',
            'server_argv': [sys.executable, str(self.server)],
            'phases': [{'id': 'initial', 'prompt': 'Synthetic protocol control.'},
                       {'id': 'handoff', 'prompt': 'Synthetic follow-up control.'}],
        }
        self.input = self.root / 'manifest.json'
        self.output = self.root / 'result.json'

    def invoke(self):
        self.input.write_text(json.dumps(self.manifest), encoding='utf-8')
        return subprocess.run([sys.executable, str(RUNNER), '--manifest', str(self.input),
                               '--output', str(self.output)], capture_output=True,
                              text=True, timeout=20)

    def test_new_threads_actual_settings_and_all_phase_usage(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(record['execution'], 'completed')
        self.assertEqual(len({p['thread_id'] for p in record['phases']}), 2)
        self.assertTrue(all(p['actual_model'] == 'gpt-6-luna' and
                            p['actual_reasoning_effort'] == 'medium' for p in record['phases']))
        self.assertEqual(record['usage']['inputTokens'], 20)
        self.assertEqual(record['usage']['outputTokens'], 6)
        self.assertEqual(record['usage']['reasoningOutputTokens'], 2)
        self.assertEqual(record['usage']['totalTokens'], 26)
        self.assertIsNone(record['cost_usd'])
        self.assertIsNone(record['credits'])
        self.assertIsNone(record['behavior_verdict'])
        self.assertTrue(Path(record['trace']['path']).is_file())
        self.assertEqual(record['budget']['enforced_wall_seconds'], 10)

    def test_model_mismatch_refuses_turn_and_retains_server_reply(self):
        text = self.server.read_text(encoding='utf-8').replace("'model':p['model']", "'model':'different-model'")
        self.server.write_text(text, encoding='utf-8')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        record = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(record['execution'], 'failed')
        self.assertIn('model_or_reasoning_mismatch', record['error'])
        trace = Path(record['trace']['path']).read_text(encoding='utf-8')
        self.assertNotIn('"method": "turn/start"', trace)
        self.assertIsNone(record['usage'])

    def test_missing_usage_is_unknown_not_zero(self):
        lines = self.server.read_text(encoding='utf-8').splitlines()
        self.server.write_text('\n'.join(l for l in lines if "'method':'thread/tokenUsage/updated'" not in l), encoding='utf-8')
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertIsNone(record['usage'])
        self.assertFalse(record['usage_complete'])

    def test_remote_server_uses_mounted_cwd_while_evidence_stays_outside(self):
        self.manifest['server_cwd'] = '/workspace'
        snapshot = self.root / 'snapshot.py'
        snapshot.write_text("import json\nprint(json.dumps({'head':None, 'patch':None}))\n")
        self.manifest['snapshot_argv'] = [sys.executable, str(snapshot)]
        candidate = self.root / 'candidate'
        candidate.mkdir()
        self.manifest['cwd'] = str(candidate)
        evidence = self.root / 'evidence'
        evidence.mkdir()
        self.output = evidence / 'result.json'
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(self.output.read_bytes())
        self.assertEqual(record['phases'][0]['thread_start']['cwd'], '/workspace')
        self.assertEqual(record['capture']['data']['cwd'], str(evidence))

    def test_remote_execution_refuses_host_git_fallback(self):
        self.manifest['server_cwd'] = '/workspace'
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('snapshot_argv', result.stderr)
        self.assertFalse(self.output.exists())

    def test_protocol_error_and_existing_output_are_preserved(self):
        self.server.write_text("import json, sys\nr=json.loads(sys.stdin.readline())\nprint(json.dumps({'id':r['id'],'error':{'code':-1,'message':'fixture failure'}}),flush=True)\n", encoding='utf-8')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        first = self.output.read_bytes()
        record = json.loads(first)
        self.assertIn('fixture failure', record['error'])
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(first, self.output.read_bytes())

    def test_patch_includes_untracked_files_without_changing_candidate_index(self):
        candidate = self.root / 'candidate'
        candidate.mkdir()
        def git(*args):
            return subprocess.check_output(['git', '-C', str(candidate), *args])
        git('init', '-q')
        git('config', 'user.email', 'fixture@example.invalid')
        git('config', 'user.name', 'Fixture')
        (candidate / 'existing.py').write_text('old = True\n', encoding='utf-8')
        git('add', '.')
        git('commit', '-qm', 'base')
        self.manifest['cwd'] = str(candidate)
        self.server.write_text(self.server.read_text(encoding='utf-8').replace(
            "\n    if m=='turn/start':", "\n    if m=='turn/start':\n        from pathlib import Path\n        Path('new.py').write_text('new = True\\n')"), encoding='utf-8')
        index_before = (candidate / '.git/index').read_bytes()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(self.output.read_bytes())
        patch = Path(record['patch']['path'])
        self.assertIn('new.py', patch.read_text(encoding='utf-8'))
        self.assertEqual(index_before, (candidate / '.git/index').read_bytes())
        self.assertEqual(record['patch']['sha256'], __import__('hashlib').sha256(patch.read_bytes()).hexdigest())

    def test_effect_trigger_interrupts_then_hands_off_to_a_fresh_thread(self):
        text = self.server.read_text(encoding='utf-8')
        text = text.replace("    else: value={}", "    elif m=='turn/interrupt': value={}\n    else: value={}")
        text = text.replace("        print(json.dumps({'method':'turn/completed'", "        if p['threadId']=='5':\n            from pathlib import Path\n            Path('effect.done').write_text('actual fixture effect')\n            continue\n        print(json.dumps({'method':'turn/completed'")
        text += "\n    if m=='turn/interrupt':\n        print(json.dumps({'method':'turn/completed','params':{'threadId':p['threadId'],'turn':{'id':'turn','status':'interrupted'}}}),flush=True)\n"
        self.server.write_text(text, encoding='utf-8')
        self.manifest['phases'][0]['interrupt_when_file'] = 'effect.done'
        self.manifest['timeout_seconds'] = 2
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(self.output.read_bytes())
        self.assertEqual([p['status'] for p in record['phases']], ['interrupted', 'completed'])
        self.assertNotEqual(record['phases'][0]['thread_id'], record['phases'][1]['thread_id'])
        self.assertEqual((self.root / 'effect.done').read_text(), 'actual fixture effect')
        self.assertIsNotNone(record['phases'][0]['interruption']['trigger_sha256'])

    def test_timeout_keeps_completed_phase_and_unknown_launch(self):
        text = self.server.read_text(encoding='utf-8').replace("\n    if m=='turn/start':", "\n    if m=='turn/start':\n        import time\n        if p['threadId'] != '5': time.sleep(30)")
        self.server.write_text(text, encoding='utf-8')
        self.manifest['timeout_seconds'] = 1
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        record = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(record['execution'], 'timeout')
        self.assertEqual(record['phases'][0]['status'], 'completed')
        self.assertEqual(record['phases'][1]['status'], 'unknown')
        self.assertFalse(record['usage_complete'])


if __name__ == '__main__':
    unittest.main()
