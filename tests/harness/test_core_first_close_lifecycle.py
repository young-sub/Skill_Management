import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tests.harness.test_core_first_design_execution import contract


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_close", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def result_payload() -> dict:
    return {
        "items": [
            {"id": "I-01", "actual": "요청 검증과 응답 생성 경계를 분리해 공개 응답을 유지했다.", "actual_steps": ["요청 수신", "입력 검증", "응답 반환"], "actual_outcomes": ["정상 요청은 기존 응답 형식을 유지한다", "잘못된 요청은 명시적인 오류를 반환한다"], "checks": [{"kind": "Targeted", "summary": "정상·거부 요청의 공개 응답을 검증", "command": "python -m unittest auth", "status": "passed"}], "criteria": [{"criterion": "관련 공개 동작이 통과한다", "status": "passed", "evidence": "정상·거부 요청 회귀 테스트 통과"}], "done": [True], "delta": {"material": False, "summary": "승인된 설계와 동일", "impact": "추가 승인 불필요"}},
            {"id": "I-02", "actual": "선택 기능을 제공한다", "actual_steps": ["입력", "처리", "출력"], "checks": [{"kind": "Feature", "command": "python -m unittest optional", "status": "passed"}], "done": [True], "delta": {"material": False}},
        ],
        "full": {"status": "not_required", "rule": "independent_capability"},
    }


class CoreFirstCloseLifecycleTests(unittest.TestCase):
    def test_close_is_item_based_and_full_is_conditional(self) -> None:
        core = load_core()
        independent = core.evaluate_result(contract(), result_payload(), {"full_required": False, "unresolved": []})
        self.assertEqual(independent["status"], "complete")
        self.assertEqual(independent["full"], "not_required")
        shared = core.evaluate_result(contract(), result_payload(), {"full_required": True, "unresolved": []})
        self.assertEqual(shared["status"], "incomplete")
        self.assertIn("full_required_but_unrun", shared["errors"])
        failed = result_payload()
        failed["items"][0]["checks"][0]["status"] = "failed"
        evaluated = core.evaluate_result(contract(), failed, {"full_required": False, "unresolved": []})
        self.assertEqual(evaluated["items"][0]["status"], "incomplete")
        self.assertEqual(evaluated["items"][1]["status"], "complete")

    def test_korean_result_review_matches_design_identity_and_shows_actual_visual(self) -> None:
        core = load_core()
        page = core.render_result_review_v3(contract(), result_payload())
        self.assertIn('lang="ko"', page)
        self.assertLess(page.index('data-item-id="I-01"'), page.index('data-item-id="I-02"'))
        for label in ("핵심 목적", "핵심 프로세스", "핵심 테스트", "핵심 결과"):
            self.assertIn(label, page)
        for table_label in ("검증 대상", "수행한 테스트", "확인 결과"):
            self.assertIn(table_label, page)
        self.assertIn("정상 요청은 기존 응답 형식을 유지한다", page)
        self.assertIn("정상·거부 요청의 공개 응답을 검증", page)
        self.assertEqual(page.count('class="section-body"'), 8)
        self.assertIn('<section class="review-section result-section"><h3>핵심 결과</h3><div class="section-body">', page)
        self.assertIn("✓ 완료", page)
        for removed in ("구현된 변화", "실제 동작과 관찰 결과", "검증 근거", "완료 기준별 판정", "계획 대비 변경", "criteria-table", "review-facts", "기술 세부 정보", "python -m unittest auth", "관련 공개 동작이 통과한다", "정상·거부 요청 회귀 테스트 통과", "승인된 설계와 동일", "추가 승인 불필요"):
            self.assertNotIn(removed, page)
        for forbidden in ("sha256:", "<pre", "frontmatter", "감사 부록", "```"):
            self.assertNotIn(forbidden, page)
        self.assertNotIn("source-sha256", page.casefold())
        material = result_payload()
        material["items"][0]["delta"] = {"material": True, "summary": "공개 응답 변경", "approval": "required"}
        changed = core.render_result_review_v3(contract(), material)
        self.assertIn("승인 필요", changed)
        self.assertIn("공개 응답 변경", changed)

    def test_close_moves_active_work_and_writes_manifest_retention_dates(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / ".work" / "goals" / "active" / "W-1"
            active.mkdir(parents=True)
            (active / "contract.json").write_text("{}", encoding="utf-8")
            (active / "work.json").write_text(json.dumps({
                "schema_version": 3, "work_id": "W-1", "state": "active", "created_at": "2026-08-01T00:00:00+09:00",
                "source_commit": "abc", "base_branch": "develop", "feature_branch": "wp-1", "contract_version": 3,
                "integrity_digest": "internal", "owned_paths": [".work/goals/active/W-1"],
            }), encoding="utf-8")
            closed = core.close_work(root, "W-1", completed_at="2026-08-02T12:00:00+09:00", completed_days=30, trash_days=7)
            self.assertEqual(closed["status"], "completed")
            destination = root / ".work" / "goals" / "completed" / "2026-08" / "W-1"
            manifest = json.loads((destination / "work.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["retain_until"], "2026-09-01T12:00:00+09:00")
            self.assertEqual(manifest["delete_after"], "2026-09-08T12:00:00+09:00")
            self.assertEqual(manifest["owned_paths"], [".work/goals/completed/2026-08/W-1"])
            self.assertFalse(active.exists())

    def test_close_and_sweep_roll_back_interrupted_manifest_and_move(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / ".work" / "goals" / "active" / "W-fault"
            active.mkdir(parents=True)
            manifest = {"schema_version":3,"work_id":"W-fault","state":"active","created_at":"2026-08-01T00:00:00+09:00","source_commit":"a","base_branch":"develop","feature_branch":"wp","contract_version":3,"integrity_digest":"x","owned_paths":[".work/goals/active/W-fault"]}
            original = json.dumps(manifest)
            (active / "work.json").write_text(original, encoding="utf-8")
            failed = core.close_work(root, "W-fault", completed_at="2026-08-02T12:00:00+09:00", completed_days=30, trash_days=7, fault_after="move")
            self.assertEqual(failed["status"], "rolled_back")
            self.assertTrue(active.is_dir())
            self.assertEqual(json.loads((active / "work.json").read_text(encoding="utf-8"))["state"], "active")

            completed = root / ".work" / "goals" / "completed" / "2026-07" / "W-sweep"
            completed.mkdir(parents=True)
            (completed / "work.json").write_text(json.dumps({"schema_version":3,"work_id":"W-sweep","state":"completed","retain_until":"2026-08-01T00:00:00+09:00"}), encoding="utf-8")
            swept = core.sweep_lifecycle(root, now="2026-08-02T00:00:00+09:00", fault_after="move")
            self.assertEqual(swept["status"], "rolled_back")
            self.assertTrue(completed.is_dir())
            self.assertEqual(json.loads((completed / "work.json").read_text(encoding="utf-8"))["state"], "completed")

    def test_lifecycle_sweep_is_recoverable_idempotent_and_legacy_safe(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            completed = root / ".work" / "goals" / "completed" / "2026-07" / "W-old"
            completed.mkdir(parents=True)
            (completed / "work.json").write_text(json.dumps({"schema_version": 3, "work_id": "W-old", "state": "completed", "retain_until": "2026-08-01T00:00:00+09:00", "delete_after": "2026-08-08T00:00:00+09:00"}), encoding="utf-8")
            legacy = root / ".work" / "archive" / "unknown"
            legacy.mkdir(parents=True)
            (legacy / "RESULT.md").write_text("no trustworthy date\n", encoding="utf-8")
            first = core.sweep_lifecycle(root, now="2026-08-02T00:00:00+09:00")
            second = core.sweep_lifecycle(root, now="2026-08-02T00:00:00+09:00")
            self.assertEqual(first["moved_to_trash"], ["W-old"])
            self.assertEqual(second["moved_to_trash"], [])
            self.assertTrue((root / ".work" / "goals" / "trash" / "2026-08-02" / "W-old").is_dir())
            migrated = core.classify_legacy_work(root)
            self.assertEqual(migrated["unclassified"], ["unknown"])
            self.assertTrue((root / ".work" / "goals" / "legacy-unclassified" / "unknown").is_dir())

    def test_baseline_aware_maintenance_reports_only_new_or_worsened(self) -> None:
        core = load_core()
        baseline = [{"rule_id": "docs.orphan", "location": "docs/a.md", "severity": "medium", "fingerprint": "same", "review_until": "2026-08-31"}]
        findings = [dict(baseline[0]), {"rule_id": "tests.unmapped", "location": "src/new.py", "severity": "high", "fingerprint": "new", "review_until": "2026-08-31"}]
        report = core.compare_findings_to_baseline(baseline, findings, today="2026-08-02")
        self.assertEqual([item["rule_id"] for item in report["blocking"]], ["tests.unmapped"])
        self.assertEqual([item["rule_id"] for item in report["baselined"]], ["docs.orphan"])

    def test_lifecycle_audit_detects_orphans_duplicates_and_delete_is_exact_approval(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            orphan = root / ".work" / "goals" / "active" / "orphan"
            orphan.mkdir(parents=True)
            for state, suffix in (("active", "one"), ("completed", "two")):
                directory = root / ".work" / "goals" / state / suffix / "W-dup"
                directory.mkdir(parents=True)
                (directory / "work.json").write_text(json.dumps({"work_id": "W-dup", "state": state}), encoding="utf-8")
            audit = core.audit_work_lifecycle(root)
            rules = [item["rule_id"] for item in audit["findings"]]
            self.assertIn("work.orphan", rules)
            self.assertIn("work.duplicate_id", rules)

            trash = root / ".work" / "goals" / "trash" / "2026-08-02" / "W-delete"
            trash.mkdir(parents=True)
            denied = core.delete_trash(root, ".work/goals/trash/2026-08-02/W-delete", approved_exact_target=None)
            self.assertEqual(denied["status"], "approval_required")
            self.assertTrue(trash.exists())
            deleted = core.delete_trash(root, ".work/goals/trash/2026-08-02/W-delete", approved_exact_target=".work/goals/trash/2026-08-02/W-delete")
            self.assertEqual(deleted["status"], "deleted")
            self.assertFalse(trash.exists())

    def test_owned_review_directory_is_not_an_orphan(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work = root / ".work" / "goals" / "completed" / "2026-08" / "W-1"
            (work / "review").mkdir(parents=True)
            (work / "review" / "result.html").write_text("ok", encoding="utf-8")
            (work / "work.json").write_text(json.dumps({"work_id":"W-1","state":"completed"}), encoding="utf-8")
            self.assertNotIn("work.orphan", [finding["rule_id"] for finding in core.audit_work_lifecycle(root)["findings"]])


if __name__ == "__main__":
    unittest.main()
