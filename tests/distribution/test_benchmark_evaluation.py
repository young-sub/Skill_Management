"""Contract tests for official-evaluator capture; evaluators here are synthetic transports only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CONNECTOR = Path(__file__).resolve().parents[2] / 'scripts/evaluate_benchmark.py'


class BenchmarkEvaluationCaptureTests(unittest.TestCase):
    """The fixture runner checks transport and binding, never official task correctness."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.report = self.root / 'official.json'
        self.marker = self.root / 'executed'
        self.patch = self.root / 'patch.diff'
        self.trace = self.root / 'trace.jsonl'
        self.package = self.root / 'plugin.zip'
        self.patch.write_text('synthetic patch\n', encoding='utf-8')
        self.trace.write_text('{"event":"synthetic"}\n', encoding='utf-8')
        self.package.write_bytes(b'synthetic pinned package')
        self.manifest_path = self.root / 'manifest.json'
        self.output = self.root / 'capture.json'
        self.manifest = self.make_manifest()
        self.write_manifest()

    def digest(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def make_manifest(self, report_payload='{"resolved":false,"fixture":"synthetic_transport_check"}',
                      report_mode='write', exit_code=0):
        code = (
            'from pathlib import Path; import sys; '
            f'Path({str(self.marker)!r}).write_text("ran", encoding="utf-8"); '
            f'mode={report_mode!r}; payload={report_payload!r}; '
            f'p=Path({str(self.report)!r}); '
            'p.write_text(payload, encoding="utf-8") if mode == "write" else None; '
            f'raise SystemExit({exit_code})'
        )
        return {
            'format': 'benchmark-evaluation-manifest-v1',
            'benchmark': {
                'id': 'synthetic-transport-check',
                'task_id': 'fixture-001',
                'data_revision': 'dataset-revision-fixture-1',
                'evaluator_revision': 'evaluator-revision-fixture-1',
                'image_digest': 'sha256:' + ('a' * 64),
            },
            'execution': {
                'argv': [sys.executable, '-c', code],
                'cwd': '.',
                'timeout_seconds': 10,
                'report_path': 'official.json',
                'verdict_pointer': '/resolved',
            },
            'artifacts': {
                'patch': {'path': 'patch.diff', 'sha256': self.digest(self.patch)},
                'trace': {'path': 'trace.jsonl', 'sha256': self.digest(self.trace)},
            },
            'agent': {
                'model': 'synthetic-fixture-model',
                'cli_revision': 'fixture-cli-rev-1',
                'budget': {'max_calls': 1, 'max_seconds': 10},
                'permissions': {'network': False, 'filesystem': 'temporary-fixture'},
            },
            'plugin': {
                'condition': 'on',
                'version': '0.0.0-fixture',
                'source_commit': 'fixture-source-revision',
                'package': {'path': 'plugin.zip', 'sha256': self.digest(self.package)},
            },
            'usage': None,
            'cost': None,
        }

    def write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2), encoding='utf-8')

    def invoke(self):
        return subprocess.run(
            [sys.executable, str(CONNECTOR), '--manifest', str(self.manifest_path),
             '--output', str(self.output)],
            cwd=self.root, capture_output=True, text=True, timeout=20,
        )

    def test_exit_zero_keeps_external_false_verdict_and_pinned_provenance(self):
        result = self.invoke()

        self.assertTrue(self.output.exists(), result.stderr)
        capture = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(capture['capture_status'], 'complete')
        self.assertEqual(capture['external_verdict'], {'pointer': '/resolved', 'value': False})
        self.assertEqual(capture['evaluator_report']['data'], {
            'resolved': False, 'fixture': 'synthetic_transport_check',
        })
        self.assertEqual(capture['evaluator_report']['sha256'], self.digest(self.report))
        self.assertEqual(capture['runner']['exit_code'], 0)
        self.assertEqual(capture['execution_capture']['data']['argv'], self.manifest['execution']['argv'])
        self.assertEqual(capture['execution_capture']['data']['behavior_verdict'], None)
        self.assertEqual(capture['manifest']['sha256'], self.digest(self.manifest_path))
        self.assertEqual(capture['manifest']['data'], json.loads(self.manifest_path.read_text(encoding='utf-8')))
        self.assertEqual(capture['artifacts']['patch']['sha256'], self.digest(self.patch))
        self.assertEqual(capture['artifacts']['trace']['sha256'], self.digest(self.trace))
        self.assertEqual(capture['artifacts']['plugin_package']['sha256'], self.digest(self.package))
        self.assertEqual(capture['usage'], None)
        self.assertEqual(capture['cost'], None)
        self.assertTrue(self.marker.exists())

    def test_missing_or_malformed_report_is_incomplete_even_on_exit_zero(self):
        for mode, payload in (('skip', ''), ('write', '{malformed')):
            with self.subTest(mode=mode):
                self.output.unlink(missing_ok=True)
                Path(str(self.output) + '.run-check.json').unlink(missing_ok=True)
                self.marker.unlink(missing_ok=True)
                self.report.unlink(missing_ok=True)
                self.manifest = self.make_manifest(report_mode=mode, report_payload=payload)
                self.write_manifest()

                result = self.invoke()

                self.assertTrue(self.output.exists(), result.stderr)
                capture = json.loads(self.output.read_text(encoding='utf-8'))
                self.assertEqual(capture['capture_status'], 'incomplete')
                self.assertEqual(capture['runner']['exit_code'], 0)
                self.assertIsNotNone(capture['evaluator_report']['error'])
                self.assertIsNone(capture['external_verdict'])

    def test_off_has_no_package_and_rejects_contradictory_package_identity(self):
        self.manifest['plugin'] = {'condition': 'A', 'version': None, 'source_commit': None, 'package': None}
        self.write_manifest()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        capture = json.loads(self.output.read_bytes())
        self.assertNotIn('plugin_package', capture['artifacts'])
        self.assertIsNone(capture['plugin']['package'])
        self.output.unlink()
        self.report.unlink()
        Path(str(self.output) + '.run-check.json').unlink()
        self.marker.unlink()
        self.manifest['plugin']['package'] = {'path': 'plugin.zip', 'sha256': self.digest(self.package)}
        self.write_manifest()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('OFF', result.stderr)
        self.assertFalse(self.marker.exists())

    def test_unavailable_evaluator_is_incomplete(self):
        self.manifest['execution']['argv'] = [str(self.root / 'missing-evaluator')]
        self.write_manifest()

        result = self.invoke()

        self.assertTrue(self.output.exists(), result.stderr)
        capture = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(capture['capture_status'], 'incomplete')
        self.assertEqual(capture['execution_capture']['data']['execution'], 'unavailable')
        self.assertIsNone(capture['external_verdict'])
        self.assertFalse(self.marker.exists())

    def test_missing_image_or_revision_rejects_before_runner(self):
        for field in ('image_digest', 'data_revision', 'evaluator_revision'):
            with self.subTest(field=field):
                self.output.unlink(missing_ok=True)
                self.marker.unlink(missing_ok=True)
                self.manifest['benchmark'].pop(field)
                self.write_manifest()

                result = self.invoke()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(field, result.stderr)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.marker.exists())
                self.manifest['benchmark'][field] = (
                    'sha256:' + ('a' * 64) if field == 'image_digest' else f'{field}-fixture-1'
                )

    def test_changed_artifact_identity_rejects_before_runner(self):
        self.patch.write_text('changed after manifest pin\n', encoding='utf-8')

        result = self.invoke()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('artifacts.patch identity changed', result.stderr)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.marker.exists())

    def test_existing_output_or_official_report_is_never_reused(self):
        self.output.write_text('old capture', encoding='utf-8')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('output path already exists', result.stderr)
        self.assertEqual(self.output.read_text(encoding='utf-8'), 'old capture')
        self.assertFalse(self.marker.exists())

        self.output.unlink()
        self.report.write_text('{"resolved":true}', encoding='utf-8')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('evaluator report path already exists', result.stderr)
        self.assertEqual(self.report.read_text(encoding='utf-8'), '{"resolved":true}')
        self.assertFalse(self.marker.exists())

    def test_usage_and_cost_references_are_preserved_without_zero_inference(self):
        self.manifest['usage'] = {'status': 'uncollected', 'raw_report_refs': ['usage.json']}
        self.manifest['cost'] = None
        self.write_manifest()

        result = self.invoke()

        self.assertTrue(self.output.exists(), result.stderr)
        capture = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(capture['usage'], self.manifest['usage'])
        self.assertIsNone(capture['cost'])


if __name__ == '__main__':
    unittest.main()
