"""Read-only verification-result viewer checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "authoring" / "scripts" / "verification_results.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VerificationResultViewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cwd = str(self.root / "project")
        (self.root / "project").mkdir()
        for argv in (["git", "init", "-q"], ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-qm", "baseline"]):
            subprocess.run(argv, cwd=self.cwd, check=True, capture_output=True)
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.cwd, text=True).strip()
        diff = hashlib.sha256(subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=self.cwd)).hexdigest()
        self.conditions = {
            "source": {"revision": revision, "diff": diff},
            "criteria": {"revision": "criteria-1"},
            "command": {"argv": ["node", "verify-flows.mjs"], "cwd": self.cwd},
            "dependency": {"revision": "deps-1"},
            "fixture": {"id": "fixture-1", "hash": "fixture-1-hash"},
            "runtime": {"id": "runtime-1", "build": "build-1"},
        }
        self.plan = self.root / "plan.json"
        self.record = self.root / "capture.json"
        self.assessment = self.root / "assessment.json"
        self.observation = self.root / "observation.json"
        self.raw = self.root / "raw.json"
        self.current = self.root / "current.json"

    def write(self, path: Path, value: object) -> Path:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def make_plan(self, *checks: dict, raw_for: Path | None = None) -> None:
        for check in checks:
            check.setdefault("feature_id", "product-save")
            check.setdefault("criteria_revision", "criteria-1")
            check.setdefault("required", True)
            check.setdefault("selection", {"status": "selected", "reason": "changed behavior"})
            check.setdefault("conditions", self.conditions)
            if raw_for is not None:
                check.setdefault(
                    "raw_observations",
                    [{
                        "path": str(raw_for),
                        "sha256": digest(raw_for),
                        "pointer": "$.checks[0]",
                        "assertions": [{"pointer": "/checks", "min_count": 1}, {"pointer": "/checks/0/actual", "equals": 3500}],
                        "producer": {
                            "run_id": check.get("run_id", "run-1"),
                            "capture_path": str(self.record),
                            "argv": self.conditions["command"]["argv"],
                        },
                    }],
                )
        self.write(self.plan, {"schema_version": 1, "plan_id": "plan-1", "checks": list(checks)})

    def make_capture(
        self,
        *,
        run_id: str = "run-1",
        check: str = "save-flow",
        execution: str = "exited",
        exit_code: int | None = 0,
    ) -> None:
        self.write(
            self.record,
            {
                "run_id": run_id,
                "feature": "product-save",
                "check": check,
                "argv": self.conditions["command"]["argv"],
                "cwd": self.cwd,
                "before": {"head": self.conditions["source"]["revision"], "tracked_diff_sha256": self.conditions["source"]["diff"]},
                "after": {"head": self.conditions["source"]["revision"], "tracked_diff_sha256": self.conditions["source"]["diff"]},
                "execution": execution,
                "exit_code": exit_code,
                "stdout": "observed",
                "stderr": "",
            },
        )

    def make_raw(self, *, status: str = "passed") -> None:
        self.write(self.raw, {"checks": [{"name": "saved price", "status": status, "actual": 3500}]})

    def make_assessment(
        self,
        *,
        status: str = "PASS",
        run_id: str = "run-1",
        check: str = "save-flow",
    ) -> None:
        self.write(
            self.assessment,
            {
                "status": status,
                "feature": "product-save",
                "check": check,
                "run_id": run_id,
                "conditions": self.conditions,
                "reason": "selected browser assertion",
            },
        )

    def make_observation(
        self,
        *,
        status: str = "PASS",
        run_id: str = "run-1",
        check: str = "save-flow",
    ) -> None:
        self.write(
            self.observation,
            {
                "status": status,
                "feature": "product-save",
                "check": check,
                "run_id": run_id,
                "conditions": self.conditions,
            },
        )

    def make_current(self, conditions: dict | None = None) -> None:
        self.write(self.current, {"conditions": conditions or self.conditions})

    def check(self, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [sys.executable, str(VIEWER), "--plan", str(self.plan), "--record", str(self.record)]
        if self.assessment.exists():
            command.extend(["--assessment", str(self.assessment)])
        if self.observation.exists():
            command.extend(["--observation", str(self.observation)])
        if self.current.exists():
            command.extend(["--current-context", str(self.current)])
        command.extend(extra)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result, json.loads(result.stdout)

    def test_summary_preserves_verdicts_and_evidence_without_replaying_commands(self) -> None:
        marker = self.root / 'must-not-run'
        self.conditions['command']['argv'] = [sys.executable, '-c',
            f'from pathlib import Path; Path({str(marker)!r}).touch()']
        self.make_raw()
        self.make_plan({'id': 'save-flow', 'expected': 'price survives reload'},
                       {'id': 'optional', 'expected': 'unaffected', 'required': False,
                        'selection': {'status': 'excluded', 'reason': 'unchanged'}}, raw_for=self.raw)
        self.make_capture()
        self.make_observation()
        self.make_current()
        before = {p: p.read_bytes() for p in self.root.glob('*.json')}
        for status in ('PASS', 'ISSUES', 'BLOCKED'):
            with self.subTest(status=status):
                self.make_assessment(status=status)
                full_process, full = self.check()
                short_process, short = self.check('--summary')
                self.assertEqual(short_process.returncode, full_process.returncode)
                for item in full['items']:
                    item.pop('conditions')
                    item['raw_availability'] = 'AVAILABLE'
                    for raw in item['raw']:
                        raw['observation_count'] = len(raw['observations'])
                        raw['observations_omitted'] = bool(raw['observations'])
                        raw.pop('observations')
                self.assertIn('without --summary', short['detail_hint'])
                full['detail_hint'] = short['detail_hint']
                self.assertEqual(short, full)
                self.assertEqual(short['test_commands_executed'], 0)
        self.assertFalse(marker.exists())
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_summary_rejects_execution_and_preparation(self) -> None:
        for mode in ('--execute', '--prepare'):
            args = ['--plan', str(self.plan), '--execute'] if mode == '--execute' else ['--prepare', str(self.plan)]
            result = subprocess.run([sys.executable, str(VIEWER), *args, '--summary'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('--summary requires read-only lookup', result.stderr)

    def test_summary_distinguishes_missing_raw_from_omitted_observations(self) -> None:
        self.make_raw()
        self.make_plan({'id': 'save-flow', 'expected': 'saved price'}, raw_for=self.raw)
        self.make_capture()
        self.make_assessment()
        self.make_observation()
        self.make_current()
        _, available = self.check('--summary')
        self.assertEqual(available['items'][0]['raw_availability'], 'AVAILABLE')
        self.raw.unlink()
        before = {p: p.read_bytes() for p in self.root.glob('*.json')}
        _, missing = self.check('--summary')
        self.assertEqual(missing['items'][0]['raw_availability'], 'UNAVAILABLE')
        self.assertNotEqual(missing['items'][0]['current_status'], 'PASS')
        self.assertEqual(missing['test_commands_executed'], 0)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_pass_requires_linked_raw_assertion_and_reports_reusable_history(self) -> None:
        check = {"id": "save-flow", "expected": "entered price survives save and reload"}
        self.make_raw()
        self.make_plan(check, raw_for=self.raw)
        self.make_capture()
        self.make_assessment()
        self.make_observation()
        self.make_current()

        result, payload = self.check()

        self.assertEqual(result.returncode, 0, payload)
        item = payload["items"][0]
        self.assertEqual(item["historical_status"], "PASS")
        self.assertEqual(item["current_reuse"], "REUSABLE")
        self.assertEqual(item["current_status"], "PASS")
        self.assertEqual(payload["current"]["status"], "PASS")
        self.assertEqual(item["raw"][0]["pointer"], "$.checks[0]")
        self.assertEqual(item["raw"][0]["sha256"], digest(self.raw))

    def test_viewer_is_read_only_and_stale_source_cannot_be_current_pass(self) -> None:
        marker = self.root / "must-not-run"
        self.conditions["command"]["argv"] = [
            sys.executable,
            "-c",
            f"from pathlib import Path; Path({str(marker)!r}).touch()",
        ]
        self.make_raw()
        self.make_plan(
            {"id": "save-flow", "expected": "entered price survives save and reload"},
            raw_for=self.raw,
        )
        self.make_capture()
        self.make_assessment()
        self.make_observation()
        stale = dict(self.conditions)
        stale["source"] = {"revision": "source-2", "diff": "diff-1"}
        self.make_current(stale)

        result, payload = self.check()

        self.assertEqual(result.returncode, 2, payload)
        item = payload["items"][0]
        self.assertEqual(item["historical_status"], "PASS")
        self.assertEqual(item["current_reuse"], "STALE")
        self.assertNotEqual(item["current_status"], "PASS")
        self.assertIn("source", " ".join(item["reasons"]))
        self.assertFalse(marker.exists())

    def test_missing_raw_does_not_turn_submitted_pass_into_current_pass(self) -> None:
        self.make_raw()
        self.make_plan(
            {"id": "save-flow", "expected": "entered price survives save and reload"},
            raw_for=self.raw,
        )
        self.make_capture()
        self.make_assessment()
        self.make_observation()
        self.raw.unlink()
        self.make_current()

        result, payload = self.check()

        self.assertEqual(result.returncode, 2, payload)
        item = payload["items"][0]
        self.assertEqual(item["historical_status"], "PASS")
        self.assertEqual(item["current_reuse"], "UNKNOWN")
        self.assertEqual(item["current_status"], "UNKNOWN")
        self.assertIn("raw", " ".join(item["reasons"]))

    def test_observed_json_can_supply_its_own_hashed_raw_assertion(self) -> None:
        self.write(self.observation, {"status": "PASS", "checks": [{"name": "saved price", "actual": 3500}]})
        self.make_plan(
            {"id": "save-flow", "expected": "entered price survives save and reload"},
            raw_for=self.observation,
        )
        self.make_capture()
        self.make_current()

        command = [
            sys.executable,
            str(VIEWER),
            "--plan",
            str(self.plan),
            "--record",
            str(self.record),
            "--observation",
            str(self.observation),
            "--current-context",
            str(self.current),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertTrue(result.stdout.strip(), result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2, payload)
        self.assertEqual(payload["items"][0]["historical_source"], "observation")
        self.assertEqual(payload["items"][0]["current_reuse"], "UNKNOWN")
        self.assertEqual(payload["items"][0]["raw"][0]["path"], str(self.observation.resolve()))
        self.assertIn("condition_missing:observed.criteria", payload["items"][0]["reasons"])

    def test_required_skip_and_issues_and_blocked_remain_separate(self) -> None:
        self.make_raw(status="failed")
        issue = {"id": "save-flow", "expected": "entered price survives save and reload"}
        blocked = {"id": "readback-flow", "expected": "saved value is visible after reload"}
        self.make_plan(issue, blocked, raw_for=self.raw)
        self.write(
            self.plan,
            {
                "schema_version": 1,
                "plan_id": "plan-1",
                "checks": [
                    {
                        **issue,
                        "feature_id": "product-save",
                        "criteria_revision": "criteria-1",
                        "required": True,
                        "selection": {"status": "selected", "reason": "changed behavior"},
                        "conditions": self.conditions,
                        "raw_observations": [{"path": str(self.raw), "sha256": digest(self.raw), "pointer": "$.checks[0]",
                                               "producer": {"run_id": "run-1", "capture_path": str(self.record),
                                                             "argv": self.conditions["command"]["argv"]}}],
                    },
                    {
                        **blocked,
                        "feature_id": "product-save",
                        "criteria_revision": "criteria-1",
                        "required": True,
                        "selection": {"status": "selected", "reason": "changed behavior"},
                        "conditions": self.conditions,
                        "raw_observations": [{"path": str(self.raw), "sha256": digest(self.raw), "pointer": "$.checks[0]",
                                               "producer": {"run_id": "run-2", "capture_path": str(self.root / "blocked-capture.json"),
                                                             "argv": self.conditions["command"]["argv"]}}],
                        "run_id": "run-2",
                    },
                ],
            },
        )
        self.make_capture(check="save-flow")
        self.make_assessment(status="ISSUES", check="save-flow")
        self.make_observation(status="ISSUES", check="save-flow")
        blocked_record = self.root / "blocked-capture.json"
        blocked_assessment = self.root / "blocked-assessment.json"
        blocked_observation = self.root / "blocked-observation.json"
        self.write(
            blocked_record,
            {"run_id": "run-2", "feature": "product-save", "check": "readback-flow",
             "argv": self.conditions["command"]["argv"], "cwd": self.cwd, "execution": "timeout",
             "exit_code": None, "conditions": self.conditions},
        )
        self.write(blocked_assessment, {"status": "BLOCKED", "run_id": "run-2", "feature": "product-save",
                                        "check": "readback-flow", "conditions": self.conditions})
        self.write(blocked_observation, {"status": "BLOCKED", "run_id": "run-2", "feature": "product-save",
                                         "check": "readback-flow", "conditions": self.conditions})
        self.make_current()

        command = [sys.executable, str(VIEWER), "--plan", str(self.plan),
                   "--record", str(self.record), "--record", str(blocked_record),
                   "--assessment", str(self.assessment), "--assessment", str(blocked_assessment),
                   "--observation", str(self.observation), "--observation", str(blocked_observation),
                   "--current-context", str(self.current)]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertTrue(result.stdout.strip(), result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2, payload)
        self.assertEqual(payload["historical"]["counts"]["ISSUES"], 1)
        self.assertEqual(payload["historical"]["counts"]["BLOCKED"], 1)
        self.assertIn("ISSUES", payload["current"]["statuses"])
        self.assertIn("BLOCKED", payload["current"]["statuses"])

    def test_unknown_error_and_mismatched_run_are_not_current_pass(self) -> None:
        self.make_raw()
        self.make_plan(
            {"id": "save-flow", "expected": "entered price survives save and reload", "run_id": "run-1"},
            raw_for=self.raw,
        )
        self.make_capture(run_id="run-2")
        self.make_assessment(status="ERROR", run_id="run-2")
        self.make_current()

        result, payload = self.check()

        self.assertEqual(result.returncode, 2, payload)
        item = payload["items"][0]
        self.assertEqual(item["historical_status"], "NOT_RUN")
        self.assertEqual(item["current_status"], "UNKNOWN")
        self.assertIn("capture_run_mismatch", item["reasons"])
        self.assertNotIn("PASS", payload["current"]["statuses"])

    def test_conflicting_adapter_and_raw_statuses_keep_issue_visible(self) -> None:
        self.make_raw()
        self.make_plan({"id": "save-flow", "expected": "entered price survives save and reload"}, raw_for=self.raw)
        self.make_capture()
        self.make_assessment(status="PASS")
        self.make_observation(status="ISSUES")
        self.make_current()

        result, payload = self.check()

        self.assertEqual(result.returncode, 1, payload)
        item = payload["items"][0]
        self.assertEqual(item["historical_status"], "ISSUES")
        self.assertEqual(item["historical_statuses"], ["PASS", "ISSUES"])
        self.assertEqual(item["current_status"], "ISSUES")
        self.assertEqual(payload["current"]["statuses"], ["ISSUES"])

    def test_raw_pointer_hash_without_explicit_producer_is_unknown(self) -> None:
        self.make_raw()
        self.make_plan({"id": "save-flow", "expected": "entered price survives save and reload"}, raw_for=self.raw)
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        plan["checks"][0]["raw_observations"][0].pop("producer")
        self.write(self.plan, plan)
        self.make_capture()
        self.make_assessment()
        self.make_observation()
        self.make_current()

        result, payload = self.check()

        self.assertEqual(result.returncode, 2, payload)
        self.assertEqual(payload["items"][0]["historical_status"], "PASS")
        self.assertEqual(payload["items"][0]["current_reuse"], "UNKNOWN")
        self.assertIn("raw_producer_missing", payload["items"][0]["reasons"])

    def test_assessment_evidence_path_and_hash_must_match_capture(self) -> None:
        self.make_raw()
        self.make_plan({"id": "save-flow", "expected": "entered price survives save and reload"}, raw_for=self.raw)
        self.make_capture()
        wrong = self.root / "wrong-capture.json"
        self.write(wrong, {"run_id": "run-1", "feature": "product-save", "check": "save-flow"})
        self.make_assessment()
        assessment = json.loads(self.assessment.read_text(encoding="utf-8"))
        assessment["evidence"] = str(wrong)
        assessment["sha256"] = digest(wrong)
        self.write(self.assessment, assessment)
        self.make_current()

        result, payload = self.check()

        self.assertEqual(result.returncode, 2, payload)
        self.assertIn("assessment_evidence_path_mismatch", payload["items"][0]["reasons"])
        self.assertIn("assessment_evidence_hash_mismatch", payload["items"][0]["reasons"])
        self.assertNotEqual(payload["items"][0]["current_status"], "PASS")

    def test_native_execution_and_raw_assertions_gate_a_submitted_pass(self) -> None:
        for mutation in ({"execution": "timeout"}, {"exit_code": 1}, {"cleanup_incomplete": True}, {"behavior_verdict": "PASS"}):
            with self.subTest(mutation=mutation):
                self.make_raw(); self.make_plan({"id": "save-flow", "expected": "saved price"}, raw_for=self.raw)
                self.make_capture(); self.make_assessment(); self.make_current()
                record = json.loads(self.record.read_text()); record.update(mutation); self.write(self.record, record)
                result, payload = self.check()
                self.assertEqual(result.returncode, 2, payload)
        for value in ({"checks": []}, {"checks": [{"actual": 3501}]}):
            with self.subTest(raw=value):
                self.write(self.raw, value); self.make_plan({"id": "save-flow", "expected": "saved price"}, raw_for=self.raw)
                self.make_capture(); self.make_assessment(); self.make_current()
                result, payload = self.check()
                self.assertEqual(result.returncode, 2, payload)

    def test_unattested_conditions_cannot_be_excluded_to_get_pass(self) -> None:
        self.conditions['fixture'] = {'status': 'not_applicable', 'reason': 'not independently attested'}
        self.make_raw(); self.make_plan({"id": "save-flow", "expected": "saved price"}, raw_for=self.raw)
        self.make_capture(); self.make_assessment(); self.make_current()
        result, payload = self.check()
        self.assertEqual(result.returncode, 2, payload)

    def test_live_source_change_cannot_reuse_copied_historical_current_context(self) -> None:
        self.make_raw(); self.make_plan({"id": "save-flow", "expected": "saved price"}, raw_for=self.raw)
        self.make_capture(); self.make_assessment(); self.make_current()
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--allow-empty', '-qm', 'changed'], cwd=self.cwd, check=True, capture_output=True)
        result, payload = self.check()
        self.assertEqual(result.returncode, 2, payload)
        self.assertEqual(payload['items'][0]['current_reuse'], 'STALE')

    def test_same_check_issue_and_blocked_are_both_preserved(self) -> None:
        self.make_raw(); self.make_plan({"id": "save-flow", "expected": "saved price"}, raw_for=self.raw)
        self.make_capture(); self.make_assessment(status='ISSUES'); self.make_observation(status='BLOCKED'); self.make_current()
        result, payload = self.check()
        self.assertEqual(result.returncode, 2, payload)
        self.assertIn('ISSUES', payload['current']['statuses'])
        self.assertIn('BLOCKED', payload['current']['statuses'])

    def test_required_exclusion_cannot_hide_an_unrun_check(self) -> None:
        self.make_raw()
        self.make_plan(
            {'id': 'save-flow', 'expected': 'saved price'},
            {'id': 'reload-flow', 'expected': 'fresh read', 'selection': {'status': 'excluded', 'reason': 'not executed'}},
            raw_for=self.raw,
        )
        self.make_capture(); self.make_assessment(); self.make_current()
        result, payload = self.check()
        self.assertEqual(result.returncode, 2, payload)

    def test_raw_issues_cannot_be_hidden_by_omitting_observation_argument(self) -> None:
        self.write(self.raw, {'status': 'ISSUES', 'checks': [{'actual': 3500}]})
        self.make_plan({'id': 'save-flow', 'expected': 'saved price'}, raw_for=self.raw)
        self.make_capture(); self.make_assessment(); self.make_current()
        result, payload = self.check()
        self.assertEqual(result.returncode, 1, payload)
        self.assertIn('ISSUES', payload['current']['statuses'])

    def test_changed_criterion_identity_cannot_reuse_old_conditions(self) -> None:
        self.make_raw()
        self.make_plan({'id': 'save-flow', 'expected': 'saved price', 'criteria_revision': 'criteria-2'}, raw_for=self.raw)
        self.make_capture(); self.make_assessment(); self.make_current()
        result, payload = self.check()
        self.assertEqual(result.returncode, 2, payload)

    def test_duplicate_logical_checks_cannot_count_the_same_result_twice(self) -> None:
        self.make_raw()
        self.make_plan({'id': 'save-flow', 'expected': 'saved price'}, {'id': 'save-flow', 'expected': 'saved price again'}, raw_for=self.raw)
        self.make_capture(); self.make_assessment(); self.make_current()
        result, payload = self.check()
        self.assertEqual(result.returncode, 2, payload)

    def test_selection_requires_an_explanation_for_every_disposition(self) -> None:
        for status in ('selected', 'excluded', 'not_required'):
            for reason in (None, '', '  ', 42):
                with self.subTest(status=status, reason=reason):
                    self.make_raw()
                    self.make_plan({'id': 'save-flow', 'expected': 'saved price',
                                    'selection': {'status': status, 'reason': reason}}, raw_for=self.raw)
                    self.make_capture(); self.make_assessment(); self.make_current()
                    result, payload = self.check()
                    self.assertEqual(result.returncode, 2, payload)
                    self.assertIn('selection.reason', ' '.join(payload['remaining']))


if __name__ == "__main__":
    unittest.main()
