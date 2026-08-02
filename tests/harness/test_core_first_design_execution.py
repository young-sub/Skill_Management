import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import os


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_design", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _legacy_contract() -> dict:
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


def contract() -> dict:
    payload = _legacy_contract()
    for candidate in payload["items"]:
        candidate["tests"] = [{
            "id": "T-01", "target": "normal request response",
            "method": "python -m unittest auth", "expected": "the relevant check passes",
            "selector": "python -m unittest auth",
        }]
        candidate["done"] = [{"id": "D-01", "criterion": "the relevant check passes"}]
    return payload


def v3_project() -> dict:
    return {
        "harness": {
            "active_cohort": "v3",
            "components": {
                name: {"supports": [3]}
                for name in ("project", "design", "execute", "close", "maintain", "diagnose")
            },
        }
    }


class CoreFirstDesignExecutionTests(unittest.TestCase):
    def test_korean_design_review_is_item_bound_visual_and_human_readable(self) -> None:
        core = load_core()
        source = contract()
        source["non_goals"] = ["No public API changes"]
        source["items"][0].update({
            "behavior_type": "migration",
            "what": "기존 API 계약을 유지하면서 새 검증 경로로 안전하게 전환하고, 실패하면 이전 상태를 보존한다.",
            "steps": ["기존 요청 경로와 기준선을 확인한다", "새 검증 경로를 활성화한다", "대표 요청의 응답을 비교한다", "오류가 나면 기존 경로로 복구한다"],
            "tests": [
                {"target": "기존 응답 유지", "method": "전환 전후 대표 요청을 비교한다", "expected": "응답 형식과 값이 같다", "selector": "tests.api.test_contract"},
                {"target": "실패 복구", "method": "새 경로에서 오류를 발생시킨다", "expected": "기존 경로로 복구된다", "selector": "tests.api.test_rollback"},
            ],
            "non_goals": ["No public response changes"],
            "material_risks": ["irreversible_migration"],
        })
        source["items"][1]["depends_on"] = ["I-01"]
        for index, test in enumerate(source["items"][0]["tests"], 1):
            test["id"] = f"T-{index:02d}"
        page = core.render_design_review_v3(source)
        self.assertIn('lang="ko"', page)
        self.assertLess(page.index('data-item-id="I-01"'), page.index('data-item-id="I-02"'))
        for label in ("핵심 목적", "핵심 프로세스", "핵심 테스트", "예상 결과"):
            self.assertIn(label, page)
        for table_label in ("검증 대상", "수행할 테스트", "통과 기준"):
            self.assertIn(table_label, page)
        self.assertIn("기존 응답 유지", page)
        self.assertIn("전환 전후 대표 요청을 비교한다", page)
        self.assertIn("응답 형식과 값이 같다", page)
        self.assertEqual(page.count('class="section-body"'), 8)
        self.assertIn('data-visual="migration"', page)
        self.assertIn("복구", page)
        self.assertIn("review-masthead", page)
        self.assertIn("Impact rule", page)
        self.assertIn("변경과 검사를 연결하는 규칙", page)
        self.assertIn("No public API changes", page)
        self.assertIn("No public response changes", page)
        self.assertIn("비가역 마이그레이션", page)
        self.assertIn("우선순위", page)
        self.assertIn("핵심", page)
        self.assertIn("선택", page)
        self.assertIn("선행 Item", page)
        self.assertIn("I-01 이후", page)
        for removed in ("검토 요청", "변경 후 달라지는 점", "동작 설계", "완료 판정 기준", "의존성과 작업 경계", "리스크와 검토 포인트", "review-facts", "기술 세부 정보", "tests.api.test_contract"):
            self.assertNotIn(removed, page)
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

    def test_valid_design_is_default_authorized_without_affirmative_text(self) -> None:
        core = load_core()
        authorized = core.authorize_design(
            contract(), intent="default", actor="policy",
            authorized_at="2026-08-02T12:00:00+09:00",
        )
        self.assertEqual(authorized["status"], "default_authorized")
        self.assertEqual(authorized["contract"]["authorization"]["mode"], "default")
        self.assertNotIn("utterance", authorized["contract"]["authorization"])
        self.assertTrue(core.execution_authorized(
            authorized["contract"], project=v3_project(), host_goal=None,
        )["authorized"])

    def test_veto_invalid_contract_and_high_risk_design_fail_closed(self) -> None:
        core = load_core()
        vetoed = core.authorize_design(
            contract(), intent="veto", actor="human",
            authorized_at="2026-08-02T12:00:00+09:00",
        )
        self.assertEqual(vetoed["status"], "vetoed")
        self.assertFalse(core.execution_authorized(
            vetoed["contract"], project=v3_project(), host_goal=None,
        )["authorized"])

        invalid = contract()
        invalid["schema_version"] = 4
        invalid["unknown"] = True
        self.assertEqual(core.authorize_design(
            invalid, intent="default", actor="policy",
            authorized_at="2026-08-02T12:00:00+09:00",
        )["status"], "invalid_contract")

        high = contract()
        high["items"][0]["material_risks"] = ["security_privacy"]
        self.assertEqual(core.authorize_design(
            high, intent="default", actor="policy",
            authorized_at="2026-08-02T12:00:00+09:00",
        )["status"], "explicit_approval_required")
        explicit = core.authorize_design(
            high, intent="explicit_approve", actor="human",
            authorized_at="2026-08-02T12:01:00+09:00",
        )
        self.assertEqual(explicit["status"], "explicit_authorized")
        self.assertTrue(core.execution_authorized(
            explicit["contract"], project=v3_project(), host_goal=None,
        )["authorized"])

        repeated = core.authorize_design(
            vetoed["contract"], intent="default", actor="policy",
            authorized_at="2026-08-02T12:02:00+09:00",
        )
        self.assertEqual(repeated["status"], "vetoed")
        self.assertEqual(repeated["contract"]["authorization"]["mode"], "vetoed")

    def test_legacy_pending_conversion_is_lossless_but_active_work_blocks(self) -> None:
        core = load_core()
        legacy = {"work_id": "W-old", "status": "pending", "objective": "deliver", "requirements": ["A", "B"], "non_goals": ["C"]}
        converted = core.convert_legacy_contract(legacy)
        self.assertEqual(converted["status"], "converted")
        self.assertEqual(core.validate_contract_v3(converted["contract"]), [])
        serialized = json.dumps(converted["contract"], ensure_ascii=False)
        for value in ("deliver", "A", "B", "C"):
            self.assertIn(value, serialized)
        self.assertTrue(converted["unresolved_fields"])
        active = dict(legacy, status="in_progress")
        self.assertEqual(core.convert_legacy_contract(active)["status"], "cutover_blocked")

    def test_start_revalidates_the_actual_project_cohort_before_git_mutation(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-b", "develop"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "README.md").write_text("baseline\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
            source = contract()
            source["work_id"] = "W-start"
            authorized = core.authorize_design(
                source, intent="default", actor="policy",
                authorized_at="2026-08-02T12:00:00+09:00",
            )["contract"]
            mixed = v3_project()
            mixed["harness"]["components"]["close"] = {"supports": [2]}

            result = core.start_work(root, "W-start", "feature", authorized, project=mixed)

            self.assertEqual(result["status"], "authorization_failed")
            self.assertIn("mixed_cohort:close:3", result["errors"])
            branch = subprocess.run(
                ["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True,
            ).stdout.strip()
            self.assertEqual(branch, "develop")

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

    def test_every_canonical_material_risk_blocks_default_amendment_rebinding(self) -> None:
        core = load_core()
        source = contract()

        for risk in sorted(core.MATERIAL_RISK_FLAGS):
            with self.subTest(risk=risk):
                outcome = core.apply_amendment(
                    source, item_id="I-01", field="what", value="changed",
                    message_id=f"risk-{risk}", actor="human",
                    approved_at="2026-08-02T13:00:00+09:00", risk=risk,
                )
                self.assertEqual(outcome["status"], "focused_approval_required")

        low = core.apply_amendment(
            source, item_id="I-01", field="what", value="safe change",
            message_id="risk-low", actor="human",
            approved_at="2026-08-02T13:00:00+09:00", risk="low",
        )
        self.assertEqual(low["status"], "applied")

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

    def test_git_baseline_classifies_dirty_paths_without_ignored_files(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / ".gitignore").write_text("ignored.bin\n.venv/\n", encoding="utf-8")
            for name in ("staged.txt", "unstaged.txt", "deleted.txt"):
                (root / name).write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            (root / "staged.txt").write_text("staged\n", encoding="utf-8")
            subprocess.run(["git", "add", "staged.txt"], cwd=root, check=True)
            (root / "unstaged.txt").write_text("unstaged\n", encoding="utf-8")
            (root / "deleted.txt").unlink()
            (root / "untracked.txt").write_text("untracked\n", encoding="utf-8")
            (root / "ignored.bin").write_bytes(b"x" * 1024)
            (root / ".venv").mkdir()
            (root / ".venv" / "locked.bin").write_bytes(b"ignored")

            baseline = core.collect_git_baseline(root)

            self.assertEqual(baseline["base_revision"], subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip())
            by_path = {entry["path"]: entry for entry in baseline["entries"]}
            self.assertEqual(set(by_path), {"deleted.txt", "staged.txt", "unstaged.txt", "untracked.txt"})
            self.assertIn("staged", by_path["staged.txt"]["states"])
            self.assertIn("unstaged", by_path["unstaged.txt"]["states"])
            self.assertIn("deleted", by_path["deleted.txt"]["states"])
            self.assertIn("untracked", by_path["untracked.txt"]["states"])

    def test_item_commit_rejects_dot_alias_and_directory_dirty_overlap(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            (root / "docs" / "guide.md").write_text("user change\n", encoding="utf-8")
            baseline = core.collect_git_baseline(root)

            alias = core.commit_item(root, "I-01", ["./docs/guide.md"], dirty_baseline=baseline)
            directory = core.commit_item(root, "I-01", ["docs"], dirty_baseline=baseline)

            self.assertEqual(alias["status"], "dirty_baseline_conflict")
            self.assertEqual(directory["status"], "dirty_baseline_conflict")

    def test_canonical_repo_identity_rejects_filesystem_aliases(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            real = root / "real"
            real.mkdir()
            (real / "file.txt").write_text("data\n", encoding="utf-8")
            alias = root / "alias"
            try:
                os.symlink(real, alias, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")

            with self.assertRaisesRegex(ValueError, "path_alias"):
                core.canonical_repo_identity(root, "alias/file.txt")

    def test_canonical_repo_identity_normalizes_case_and_unicode_by_platform_policy(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            composed = "café.txt"
            decomposed = "cafe\u0301.txt"
            (root / composed).write_text("data\n", encoding="utf-8")

            _, upper_identity = core.canonical_repo_identity(root, composed.upper(), case_sensitive=False)
            _, decomposed_identity = core.canonical_repo_identity(root, decomposed, case_sensitive=False)
            _, composed_identity = core.canonical_repo_identity(root, composed, case_sensitive=False)

            self.assertEqual(upper_identity, composed_identity)
            self.assertEqual(decomposed_identity, composed_identity)

    def test_impacted_selection_requires_mapping_and_promotes_shared_changes(self) -> None:
        core = load_core()
        project = {"impact": {
            "rules": [
                {"id": "auth", "source_prefixes": ["src/auth/"], "tests": ["tests/auth"], "feature": "auth", "triggers": []},
                {"id": "shared", "source_prefixes": ["src/core/"], "tests": ["tests/core"], "feature": "core", "triggers": ["shared_policy"]},
            ],
            "feature_selectors": {"auth": ["python", "-m", "unittest", "tests.auth"], "core": ["python", "-m", "unittest", "tests.core"]},
            "full_triggers": ["shared_policy"],
        }}
        selected = core.select_impacted_checks(["src/auth/service.py"], project)
        self.assertEqual(selected["tests"], ["tests/auth"])
        self.assertEqual(selected["feature_commands"], [{"feature": "auth", "argv": ["python", "-m", "unittest", "tests.auth"]}])
        self.assertFalse(selected["full_required"])
        self.assertEqual(selected["not_required_rule_ids"], ["auth"])
        self.assertEqual(selected["unresolved"], [])
        shared = core.select_impacted_checks(["src/core/state.py"], project)
        self.assertTrue(shared["full_required"])
        self.assertEqual(shared["full_trigger_ids"], ["shared_policy"])
        self.assertEqual(core.select_impacted_checks(["src/unknown.py"], project)["unresolved"], ["src/unknown.py"])


if __name__ == "__main__":
    unittest.main()
