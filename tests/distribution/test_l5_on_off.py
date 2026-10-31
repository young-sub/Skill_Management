"""L5 ON/OFF runner: the ablation removals still match the plugin, and criteria scoring, without any model."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location('l5_on_off', ROOT / 'evals/l5-on-off/tools/run.py')
l5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(l5)


def session(tokens, spawned=0, verifier=False):
    events = [{'type': 'result', 'total_cost_usd': tokens / 1e6,
               'modelUsage': {'m': {'inputTokens': tokens, 'outputTokens': 0, 'cacheReadInputTokens': 0,
                                    'cacheCreationInputTokens': 0, 'costUSD': tokens / 1e6}},
               'subagent_stats': {'spawned': spawned}}]
    if verifier:
        events.insert(0, {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Agent',
                                                                        'input': {'prompt': 'INDEPENDENT VERIFIER. ...'}}]}})
    return '\n'.join(json.dumps(e) for e in events)


class AblationTests(unittest.TestCase):
    def test_every_removal_matches_the_pinned_plugin_exactly_once(self):
        with tempfile.TemporaryDirectory() as folder:
            plugin = l5.pinned_plugin(Path(folder))
            for name, edits in l5.REMOVALS.items():
                text = (plugin / name).read_bytes().decode('utf-8').replace('\r\n', '\n')
                for old, _ in edits:
                    self.assertEqual(text.count(old), 1, name)

    def test_build_removes_only_the_listed_text(self):
        with tempfile.TemporaryDirectory() as folder:
            target, record = l5.build_ablation(Path(folder))
            for name, edits in l5.REMOVALS.items():
                text = (target / name).read_bytes().decode('utf-8').replace('\r\n', '\n')
                for old, new in edits:
                    self.assertNotIn(old, text)
                    self.assertIn(new, text)
            self.assertNotEqual(record['source_sha256'], record['package_sha256'])


class CriteriaTests(unittest.TestCase):
    def test_report_applies_the_pre_registered_criteria(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            runs = output / 'runs'
            rows = []
            # off: 18/24 successes, 4 false completions; on: 22/24, 1 false completion, L5 ran.
            for condition, successes, false_completions, tokens, spawned in (
                    ('off', 18, 4, 1_000_000, 0), ('on', 22, 1, 1_100_000, 1), (l5.ABLATION, 21, 1, 1_000_000, 1)):
                for index in range(24):
                    scenario, rep = f's{index % 12}', index // 12 + 1
                    ok = index < successes
                    rows.append({'scenario': scenario, 'condition': condition, 'rep': rep, 'verified_success': ok,
                                 'false_completion': not ok and index < successes + false_completions,
                                 'regression': {'passed': True},
                                 'hidden': [{'name': 'h', 'passed': ok}]})
                    work = runs / scenario / condition / f'rep{rep}'
                    work.mkdir(parents=True, exist_ok=True)
                    (work / 'session1.jsonl').write_text(session(tokens, spawned, bool(spawned)), encoding='utf-8')
            (runs / 'state.json').write_text(json.dumps({'valid': rows, 'spent_usd': 1.0}), encoding='utf-8')
            original = l5.SCENARIOS
            scenarios = output / 'scenarios.json'
            scenarios.write_text(json.dumps({'scenarios': [{'id': f's{i}', 'hidden': [{'name': 'h', 'origin': 'v2'}]}
                                                           for i in range(12)]}), encoding='utf-8')
            l5.SCENARIOS = scenarios
            try:
                l5.report(output)
            finally:
                l5.SCENARIOS = original
            result = json.loads((output / 'criteria-report.json').read_text(encoding='utf-8'))
        self.assertEqual(result['criteria'], {'V': True, 'H': True, 'H-v2': True, 'F': True, 'T': True})
        self.assertEqual(result['decision'], 'keep L5 as the default path')
        self.assertEqual(result['conditions']['on']['l5_ran'], 24)
        self.assertTrue(result['ablation']['remove_device'])
        self.assertFalse(result['interpretation_guard']['unconfirmed'])


if __name__ == '__main__':
    unittest.main()
