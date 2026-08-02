import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_design", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    item = {
        "id": "I-01", "title": "핵심 API", "behavior_type": "api",
        "what": "요청을 처리한다", "steps": ["요청", "검증", "응답"],
        "terms": [{"term": "Impact rule", "explanation": "변경과 검사를 연결하는 규칙"}],
        "tests": ["정상 요청이 응답을 만든다"], "done": ["관련 검사가 통과한다"],
        "depends_on": [], "non_goals": ["추가 최적화"],
        "decision": {"state": "resolved"}, "material_risks": [], "priority": "core",
    }
    optional = dict(item, id="I-02", title="선택 기능", priority="optional", depends_on=[])
    return {
        "schema_version": 3, "work_id": "W-20260802-003", "goal": "핵심 흐름을 전달한다",
        "scope": "승인된 API 흐름", "non_goals": ["무관한 정리"], "items": [item, optional],
    }


class CoreFirstDesignExecutionTests(unittest.TestCase):
    def test_korean_design_review_is_item_bound_visual_and_human_readable(self) -> None:
        core = load_core()
        page = core.render_design_review_v3(contract())
        self.assertIn('lang="ko"', page)
        self.assertLess(page.index('data-item-id="I-01"'), page.index('data-item-id="I-02"'))
        for label in ("무엇을 구현하나요", "어떻게 동작하나요", "어떻게 테스트하나요", "완료 기준"):
            self.assertIn(label, page)
        self.assertIn("Impact rule", page)
        self.assertIn("변경과 검사를 연결하는 규칙", page)
        self.assertIn("flow-step", page)
        self.assertIn("✓ 결정 완료", page)
        for forbidden in ("sha256:", "<pre", "frontmatter", "감사 부록", "```"):
            self.assertNotIn(forbidden, page)
        self.assertNotIn("source-sha256", page.casefold())

    def test_natural_approval_authorizes_without_host_goal_or_pasted_hash(self) -> None:
        core = load_core()
        source = contract()
        review = core.render_design_review_v3(source)
        approved = core.approve_review(source, review, utterance="승인합니다", actor="human", approved_at="2026-08-02T12:00:00+09:00")
        self.assertEqual(approved["status"], "approved")
        self.assertTrue(core.execution_authorized(approved["contract"], review, host_goal=None)["authorized"])
        unresolved = contract()
        unresolved["items"][0]["decision"]["state"] = "unresolved"
        blocked = core.approve_review(unresolved, core.render_design_review_v3(unresolved), utterance="승인", actor="human", approved_at="2026-08-02T12:00:00+09:00")
        self.assertEqual(blocked["status"], "unresolved_decisions")

    def test_legacy_pending_conversion_is_lossless_but_active_work_blocks(self) -> None:
        core = load_core()
        legacy = {"work_id": "W-old", "status": "pending", "objective": "deliver", "requirements": ["A", "B"], "non_goals": ["C"]}
        converted = core.convert_legacy_contract(legacy)
        self.assertEqual(converted["status"], "converted")
        serialized = json.dumps(converted["contract"], ensure_ascii=False)
        for value in ("deliver", "A", "B", "C"):
            self.assertIn(value, serialized)
        self.assertTrue(converted["unresolved_fields"])
        active = dict(legacy, status="in_progress")
        self.assertEqual(core.convert_legacy_contract(active)["status"], "cutover_blocked")

    def test_core_item_precedes_optional_and_amendments_are_risk_based(self) -> None:
        core = load_core()
        source = contract()
        self.assertEqual(core.next_item(source, {})["id"], "I-01")
        state = {"I-01": "completed"}
        self.assertEqual(core.next_item(source, state)["id"], "I-02")
        low = core.apply_amendment(source, item_id="I-01", field="what", value="요청을 안전하게 처리한다", message_id="m1", actor="human", approved_at="2026-08-02T13:00:00+09:00", risk="low")
        self.assertEqual(low["status"], "applied")
        self.assertEqual(low["event"]["kind"], "approved_amendment")
        high = core.apply_amendment(source, item_id="I-01", field="what", value="공개 API를 파괴한다", message_id="m2", actor="human", approved_at="2026-08-02T13:00:00+09:00", risk="public_contract")
        self.assertEqual(high["status"], "focused_approval_required")

    def test_item_commit_excludes_preexisting_dirty_baseline(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "dirty.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "dirty.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            (root / "dirty.txt").write_text("user change\n", encoding="utf-8")
            (root / "staged.txt").write_text("preserve staged\n", encoding="utf-8")
            subprocess.run(["git", "add", "staged.txt"], cwd=root, check=True)
            (root / "item.txt").write_text("implementation\n", encoding="utf-8")
            result = core.commit_item(root, "I-01", ["item.txt"], dirty_baseline=["dirty.txt"])
            self.assertEqual(result["status"], "committed")
            changed = subprocess.run(["git", "show", "--pretty=", "--name-only", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
            self.assertEqual(changed, ["item.txt"])
            self.assertIn("dirty.txt", subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True, check=True).stdout)
            self.assertEqual(subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines(), ["staged.txt"])

    def test_impacted_selection_requires_mapping_and_promotes_shared_changes(self) -> None:
        core = load_core()
        project = {"impact": {"rules": [
            {"id": "auth", "source_prefixes": ["src/auth/"], "tests": ["tests/auth"], "feature": "auth", "full": False},
            {"id": "shared", "source_prefixes": ["src/core/"], "tests": ["tests/core"], "feature": "core", "full": True},
        ]}}
        selected = core.select_impacted_checks(["src/auth/service.py"], project)
        self.assertEqual(selected["tests"], ["tests/auth"])
        self.assertFalse(selected["full_required"])
        self.assertEqual(selected["unresolved"], [])
        self.assertTrue(core.select_impacted_checks(["src/core/state.py"], project)["full_required"])
        self.assertEqual(core.select_impacted_checks(["src/unknown.py"], project)["unresolved"], ["src/unknown.py"])


if __name__ == "__main__":
    unittest.main()
