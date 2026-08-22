import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.harness.test_core_first_design_execution import (
    authorized_contract,
    contract,
    init_git_repository,
    project_policy,
    write_design_only,
)


ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness_close", CORE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _legacy_result_payload() -> dict:
    return {
        "items": [
            {"id": "I-01", "actual": "요청 검증과 응답 생성 경계를 분리해 공개 응답을 유지했다.", "actual_steps": ["요청 수신", "입력 검증", "응답 반환"], "actual_outcomes": ["정상 요청은 기존 응답 형식을 유지한다", "잘못된 요청은 명시적인 오류를 반환한다"], "checks": [{"kind": "Targeted", "summary": "정상·거부 요청의 공개 응답을 검증", "command": "python -m unittest auth", "status": "passed"}], "criteria": [{"criterion": "관련 공개 동작이 통과한다", "status": "passed", "evidence": "정상·거부 요청 회귀 테스트 통과"}], "done": [True], "delta": {"material": False, "summary": "승인된 설계와 동일", "impact": "추가 승인 불필요"}},
            {"id": "I-02", "actual": "선택 기능을 제공한다", "actual_steps": ["입력", "처리", "출력"], "checks": [{"kind": "Feature", "command": "python -m unittest optional", "status": "passed"}], "done": [True], "delta": {"material": False}},
        ],
        "full": {"status": "not_required", "rule": "independent_capability"},
    }


def result_payload() -> dict:
    payload = _legacy_result_payload()
    for item in payload["items"]:
        for check in item.get("checks", []):
            check["check_id"] = "T-01"
            check["command"] = "python -m unittest auth"
        criteria = item.get("criteria")
        if criteria is None:
            criteria = [{
                "criterion_id": "D-01", "criterion": "the relevant check passes",
                "status": "passed", "evidence": "observed",
            }]
            item["criteria"] = criteria
        for criterion in criteria:
            criterion["criterion_id"] = "D-01"
            criterion["criterion"] = "the relevant check passes"
    return payload


def started_work(core, root: Path, work_id: str) -> tuple[Path, dict]:
    init_git_repository(root)
    source = authorized_contract(core, work_id)
    active, _, _ = write_design_only(root, core, source)
    started = core.start_work(
        root, work_id, "close", source,
        project=project_policy(protected=()),
    )
    if started["status"] != "started":
        raise AssertionError(started)
    return active, source


def close_impact(core, scope: str = "local") -> tuple[dict, dict]:
    project = project_policy(protected=())
    project["impact"] = {"rules": [], "feature_selectors": {}, "full_triggers": []}
    impact = core.select_impacted_checks(
        [], project,
        logic_impact={
            "changed_logic": ["completed work result"],
            "affected_behaviors": ["goal completion evidence"],
            "scope": scope, "reason": "The fixture records the assessed logic scope.",
            "tests": ["tests/test_goal_result.py"],
        },
    )
    return project, impact


class CoreFirstCloseLifecycleTests(unittest.TestCase):
    def test_close_blocks_when_cumulative_changed_paths_outgrow_logic_assessment(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active, source = started_work(core, root, "W-cumulative-impact")
            project = project_policy(protected=())
            project["impact"] = {
                "rules": [{
                    "id": "app", "source_prefixes": ["src/"],
                    "tests": ["tests/test_app.py"], "feature": "app", "triggers": [],
                }],
                "feature_selectors": {"app": ["python", "-m", "unittest", "tests.test_app"]},
                "full_triggers": [],
            }
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/app.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "app"], cwd=root, check=True, capture_output=True)
            impact = core.select_impacted_checks(
                ["src/app.py"], project,
                logic_impact={
                    "changed_logic": ["app.VALUE"],
                    "affected_behaviors": ["app output"],
                    "scope": "local", "reason": "One app value changed.",
                    "tests": ["tests/test_app_value.py"],
                },
            )
            (root / "src" / "bootstrap.py").write_text("ENABLED = True\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/bootstrap.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "bootstrap"], cwd=root, check=True, capture_output=True)
            result = result_payload()
            result["full"]["rule"] = "app"

            closed = core.close_work(
                root, "W-cumulative-impact", contract=source, result=result,
                impact=impact, project=project,
                completed_at="2026-08-22T14:00:00+09:00",
                completed_days=30, trash_days=7,
            )

            self.assertEqual(closed["status"], "incomplete", closed)
            self.assertIn("cumulative_logic_impact_stale", closed["errors"])
            self.assertTrue(active.is_dir())

    def test_json_only_design_closes_with_result_json_and_maintains_cleanly(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root)
            source = contract()
            source["work_id"] = "W-json-close"
            created = core.design_create(
                root, source, slug="json-close", work_id="W-json-close",
                intent="default", actor="policy",
                authorized_at="2026-08-22T12:00:00+09:00",
            )
            self.assertEqual(created["status"], "created", created)
            stored = created["contract"]
            started = core.start_work(
                root, "W-json-close", "json-close", stored,
                project=project_policy(protected=("main",)),
            )
            self.assertEqual(started["status"], "started", started)
            project, impact = close_impact(core)
            result = result_payload()
            result["full"]["rule"] = impact["not_required_rule_ids"][0]

            closed = core.close_work(
                root, "W-json-close", contract=stored, result=result,
                impact=impact, project=project,
                completed_at="2026-08-22T12:30:00+09:00",
                completed_days=30, trash_days=7,
            )

            self.assertEqual(closed["status"], "completed", closed)
            destination = root / ".work" / "goals" / "completed" / "2026-08" / "W-json-close"
            self.assertTrue((destination / "result.json").is_file())
            self.assertFalse((destination / "review").exists())
            self.assertEqual(
                core.audit_work_lifecycle(root)["findings"], [],
            )

    def test_legacy_html_digest_work_continues_without_new_result_html(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root)
            source = contract()
            source["work_id"] = "W-legacy-html"
            legacy_review = "<html lang='ko'>legacy design</html>\n"
            source["authorization"] = {
                "schema_version": 3,
                "mode": "default",
                "contract_digest": core.canonical_digest(core._contract_payload(source)),
                "review_digest": core.canonical_digest(legacy_review),
                "item_ids": [item["id"] for item in source["items"]],
                "actor": "legacy-policy",
                "authorized_at": "2026-08-01T12:00:00+09:00",
            }
            active = root / ".work" / "goals" / "active" / "W-legacy-html"
            (active / "review").mkdir(parents=True)
            (active / "contract.json").write_text(json.dumps(source), encoding="utf-8")
            (active / "review" / "design.html").write_text(legacy_review, encoding="utf-8")

            started = core.start_work(
                root, "W-legacy-html", "legacy-html", source,
                project=project_policy(protected=("main",)),
            )
            self.assertEqual(started["status"], "started", started)
            closed = core.close_work(
                root, "W-legacy-html", contract=source, result=result_payload(),
                impact={
                    "full_required": False, "unresolved": [],
                    "not_required_rule_ids": ["independent_capability"],
                },
                completed_at="2026-08-22T13:00:00+09:00",
                completed_days=30, trash_days=7,
            )

            self.assertEqual(closed["status"], "completed", closed)
            destination = root / ".work" / "goals" / "completed" / "2026-08" / "W-legacy-html"
            self.assertEqual(
                (destination / "review" / "design.html").read_text(encoding="utf-8"),
                legacy_review,
            )
            self.assertFalse((destination / "review" / "result.html").exists())
    def test_close_is_item_based_and_full_is_conditional(self) -> None:
        core = load_core()
        _, local = close_impact(core)
        local_result = result_payload()
        local_result["full"]["rule"] = local["not_required_rule_ids"][0]
        independent = core.evaluate_result(contract(), local_result, local)
        self.assertEqual(independent["status"], "complete")
        self.assertEqual(independent["full"], "not_required")
        _, cross_cutting = close_impact(core, "cross-cutting")
        shared = core.evaluate_result(contract(), result_payload(), cross_cutting)
        self.assertEqual(shared["status"], "incomplete")
        self.assertIn("full_required_but_unrun", shared["errors"])
        failed = result_payload()
        failed["items"][0]["checks"][0]["status"] = "failed"
        failed["full"]["rule"] = local["not_required_rule_ids"][0]
        evaluated = core.evaluate_result(contract(), failed, local)
        self.assertEqual(evaluated["items"][0]["status"], "incomplete")
        self.assertEqual(evaluated["items"][1]["status"], "complete")

    def test_close_requires_exact_planned_test_and_done_evidence(self) -> None:
        core = load_core()
        impact = close_impact(core)[1]
        unrelated = result_payload()
        unrelated["full"]["rule"] = impact["not_required_rule_ids"][0]
        unrelated["items"][0]["checks"] = [{
            "check_id": "T-other", "kind": "Targeted", "command": "python -m unittest unrelated",
            "status": "passed",
        }]
        unrelated["items"][0]["criteria"] = [{
            "criterion_id": "D-other", "criterion": "different", "status": "passed", "evidence": "unrelated",
        }]

        evaluated = core.evaluate_result(
            contract(), unrelated, impact,
        )

        self.assertEqual(evaluated["items"][0]["status"], "incomplete")
        self.assertIn("planned_check_evidence_mismatch", evaluated["items"][0]["errors"])
        self.assertIn("planned_done_evidence_mismatch", evaluated["items"][0]["errors"])

        changed_command = result_payload()
        changed_command["full"]["rule"] = impact["not_required_rule_ids"][0]
        changed_command["items"][0]["checks"][0]["command"] = "python -m unittest exact.runtime.case"
        proportional = core.evaluate_result(
            contract(), changed_command, impact,
        )
        self.assertEqual(proportional["items"][0]["status"], "complete")

    def test_close_rejects_a_different_goal_contract_before_writing_result_artifacts(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active, _ = started_work(core, root, "W-close-a")
            other = authorized_contract(core, "W-close-b")

            closed = core.close_work(
                root, "W-close-a", contract=other, result=result_payload(),
                impact={"full_required": False, "unresolved": [], "not_required_rule_ids": ["independent_capability"]},
                completed_at="2026-08-02T12:00:00+09:00", completed_days=30,
                trash_days=7,
            )

            self.assertEqual(closed["status"], "invalid_work", closed)
            self.assertIn("supplied_contract_identity_mismatch", closed["errors"])
            self.assertTrue(active.is_dir())
            self.assertFalse((active / "result.json").exists())
            self.assertFalse((root / ".work" / "goals" / "completed").exists())

    def test_close_prechecks_destination_and_restores_result_preimages_on_move_failure(self) -> None:
        core = load_core()
        project, impact = close_impact(core)
        result = result_payload()
        result["full"]["rule"] = impact["not_required_rule_ids"][0]
        with self.subTest("destination_conflict"), tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active, source = started_work(core, root, "W-close-conflict")
            result_path = active / "result.json"
            result_path.write_bytes(b"existing-result\r\n")
            destination = root / ".work" / "goals" / "completed" / "2026-08" / "W-close-conflict"
            destination.mkdir(parents=True)

            closed = core.close_work(
                root, "W-close-conflict", contract=source, result=result,
                impact=impact, project=project, completed_at="2026-08-02T12:00:00+09:00",
                completed_days=30, trash_days=7,
            )

            self.assertEqual(closed["status"], "conflict", closed)
            self.assertEqual(result_path.read_bytes(), b"existing-result\r\n")

        with self.subTest("move_failure"), tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active, source = started_work(core, root, "W-close-rollback")
            result_path = active / "result.json"
            result_path.write_bytes(b"result-preimage\r\n")

            closed = core.close_work(
                root, "W-close-rollback", contract=source, result=result,
                impact=impact, project=project, completed_at="2026-08-02T12:00:00+09:00",
                completed_days=30, trash_days=7, fault_after="move",
            )

            self.assertEqual(closed["status"], "rolled_back", closed)
            self.assertTrue(active.is_dir())
            self.assertEqual(result_path.read_bytes(), b"result-preimage\r\n")

    def test_close_moves_active_work_and_writes_manifest_retention_dates(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active, source = started_work(core, root, "W-1")
            project, impact = close_impact(core)
            result = result_payload()
            result["full"]["rule"] = impact["not_required_rule_ids"][0]
            closed = core.close_work(
                root, "W-1", contract=source, result=result,
                impact=impact, project=project,
                completed_at="2026-08-02T12:00:00+09:00", completed_days=30,
                trash_days=7,
            )
            self.assertEqual(closed["status"], "completed")
            destination = root / ".work" / "goals" / "completed" / "2026-08" / "W-1"
            manifest = json.loads((destination / "work.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["retain_until"], "2026-09-01T12:00:00+09:00")
            self.assertEqual(manifest["delete_after"], "2026-09-08T12:00:00+09:00")
            self.assertEqual(manifest["owned_paths"], [".work/goals/completed/2026-08/W-1"])
            self.assertTrue((destination / "result.json").is_file())
            self.assertFalse((destination / "review").exists())
            self.assertFalse(active.exists())
            journals = list((root / ".work" / "transactions").glob("*/journal.json"))
            self.assertEqual(len(journals), 1)
            self.assertNotIn("post_manifest_hash", json.loads(journals[0].read_text(encoding="utf-8")))

    def test_close_and_sweep_roll_back_interrupted_manifest_and_move(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / ".work" / "goals" / "active" / "W-fault"
            active.mkdir(parents=True)
            manifest = {"schema_version":3,"work_id":"W-fault","state":"active","created_at":"2026-08-01T00:00:00+09:00","source_commit":"a","base_branch":"develop","feature_branch":"wp","contract_version":3,"integrity_digest":"x","owned_paths":[".work/goals/active/W-fault"]}
            original = json.dumps(manifest)
            (active / "work.json").write_text(original, encoding="utf-8")
            failed = core._transition_work_to_completed(root, "W-fault", completed_at="2026-08-02T12:00:00+09:00", completed_days=30, trash_days=7, fault_after="move")
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

    def test_lifecycle_move_recovers_after_process_exit(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / ".work" / "goals" / "active" / "W-crash"
            active.mkdir(parents=True)
            original = {
                "schema_version": 3, "work_id": "W-crash", "state": "active",
                "created_at": "2026-08-01T00:00:00+09:00", "source_commit": "a",
                "base_branch": "develop", "feature_branch": "wp", "contract_version": 3,
                "integrity_digest": "x", "owned_paths": [".work/goals/active/W-crash"],
            }
            (active / "work.json").write_text(json.dumps(original), encoding="utf-8")
            child = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('core_lifecycle_crash', Path(sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module._transition_work_to_completed(Path(sys.argv[2]), 'W-crash', completed_at='2026-08-02T12:00:00+09:00', completed_days=30, trash_days=7, crash_after='move')
"""

            crashed = subprocess.run(
                [sys.executable, "-c", child, str(CORE_PATH), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(crashed.returncode, 92, crashed.stderr)
            self.assertFalse(active.exists())

            recovered = core.recover_transactions(root)

            self.assertEqual(recovered["status"], "recovered")
            self.assertTrue(active.is_dir())
            self.assertEqual(json.loads((active / "work.json").read_text(encoding="utf-8")), original)

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

    def test_lifecycle_sweep_rejects_manifest_work_id_escape_before_creating_paths(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            completed = root / ".work" / "goals" / "completed" / "2026-07" / "W-safe"
            completed.mkdir(parents=True)
            (completed / "work.json").write_text(json.dumps({
                "schema_version": 3,
                "work_id": "../../../../outside",
                "state": "completed",
                "retain_until": "2026-08-01T00:00:00+09:00",
                "delete_after": "2026-08-08T00:00:00+09:00",
            }), encoding="utf-8")

            result = core.sweep_lifecycle(root, now="2026-08-02T00:00:00+09:00")

            self.assertEqual(result["status"], "invalid_work")
            self.assertEqual(result["errors"], ["manifest_identity_or_state_invalid"])
            self.assertTrue(completed.is_dir())
            self.assertFalse((root / "outside").exists())
            self.assertFalse((root / ".work" / "transactions").exists())

    def test_legacy_classification_distinguishes_trustworthy_missing_and_contradictory_dates(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / ".work" / "archive"
            trustworthy = archive / "W-trust"
            missing = archive / "W-missing"
            contradictory = archive / "W-conflict"
            for directory in (trustworthy, missing, contradictory):
                directory.mkdir(parents=True)
            completed_at = "2026-07-01T10:00:00+09:00"
            (trustworthy / "work.json").write_text(json.dumps({"completed_at": completed_at}), encoding="utf-8")
            (trustworthy / "result.json").write_text(json.dumps({"completed_at": completed_at}), encoding="utf-8")
            (missing / "RESULT.md").write_text("no date evidence\n", encoding="utf-8")
            (contradictory / "work.json").write_text(json.dumps({"completed_at": completed_at}), encoding="utf-8")
            (contradictory / "result.json").write_text(
                json.dumps({"completed_at": "2026-07-02T10:00:00+09:00"}), encoding="utf-8",
            )

            classified = core.classify_legacy_work(root)

            self.assertEqual(classified["completed"], ["W-trust"])
            self.assertEqual(classified["unclassified"], ["W-missing"])
            self.assertEqual(classified["unresolved"], ["W-conflict"])
            self.assertTrue((root / ".work" / "goals" / "completed" / "2026-07" / "W-trust").is_dir())
            self.assertTrue((root / ".work" / "goals" / "legacy-unclassified" / "W-missing").is_dir())
            self.assertTrue(contradictory.is_dir())

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
            (trash / "work.json").write_text(json.dumps({
                "work_id": "W-delete", "state": "trash", "delete_after": "2026-08-08T00:00:00+09:00",
            }), encoding="utf-8")
            denied = core.delete_trash(root, ".work/goals/trash/2026-08-02/W-delete", approved_exact_target=None)
            self.assertEqual(denied["status"], "approval_required")
            self.assertTrue(trash.exists())
            deleted = core.delete_trash(
                root,
                ".work/goals/trash/2026-08-02/W-delete",
                approved_exact_target=".work/goals/trash/2026-08-02/W-delete",
                now="2026-08-08T00:00:00+09:00",
            )
            self.assertEqual(deleted["status"], "deleted")
            self.assertFalse(trash.exists())

    def test_lifecycle_audit_distinguishes_valid_design_only_from_malformed_orphan(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = contract()
            source["work_id"] = "W-design-only"
            source = core.authorize_design(
                source, intent="default", actor="policy",
                authorized_at="2026-08-09T12:00:00+09:00",
            )["contract"]
            design = root / ".work" / "goals" / "active" / "W-design-only"
            design.mkdir(parents=True)
            (design / "contract.json").write_text(
                json.dumps(source, ensure_ascii=False), encoding="utf-8",
            )
            malformed = root / ".work" / "goals" / "active" / "W-malformed"
            malformed.mkdir(parents=True)
            (malformed / "contract.json").write_text("{}", encoding="utf-8")

            before = core.audit_work_lifecycle(root)

            self.assertIn("W-design-only", before.get("design_only", []))
            orphan_locations = {
                finding["location"] for finding in before["findings"]
                if finding["rule_id"] == "work.orphan"
            }
            self.assertNotIn(".work/goals/active/W-design-only", orphan_locations)
            self.assertIn(".work/goals/active/W-malformed", orphan_locations)

    def test_delete_trash_rejects_traversal_even_when_the_alias_is_approved(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            active = root / ".work" / "goals" / "active" / "W-live"
            active.mkdir(parents=True)
            (active / "work.json").write_text(json.dumps({"work_id": "W-live", "state": "active"}), encoding="utf-8")
            alias = ".work/goals/trash/../active/W-live"

            result = core.delete_trash(
                root, alias, approved_exact_target=alias, now="2026-08-10T00:00:00+09:00",
            )

            self.assertEqual(result["status"], "invalid_target")
            self.assertTrue(active.is_dir())

    def test_delete_trash_rejects_a_date_bucket_target(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bucket = root / ".work" / "goals" / "trash" / "2026-08-02"
            work = bucket / "W-one"
            work.mkdir(parents=True)
            target = ".work/goals/trash/2026-08-02"

            result = core.delete_trash(
                root, target, approved_exact_target=target, now="2026-08-10T00:00:00+09:00",
            )

            self.assertEqual(result["status"], "invalid_target")
            self.assertTrue(work.is_dir())

    def test_delete_trash_requires_an_expired_matching_manifest(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            trash = root / ".work" / "goals" / "trash" / "2026-08-02" / "W-delete"
            trash.mkdir(parents=True)
            manifest_path = trash / "work.json"
            manifest_path.write_text(json.dumps({
                "work_id": "W-delete", "state": "trash", "delete_after": "2026-08-12T00:00:00+09:00",
            }), encoding="utf-8")
            target = ".work/goals/trash/2026-08-02/W-delete"

            early = core.delete_trash(
                root, target, approved_exact_target=target, now="2026-08-10T00:00:00+09:00",
            )
            self.assertEqual(early["status"], "retention_active")
            self.assertTrue(trash.is_dir())

            deleted = core.delete_trash(
                root, target, approved_exact_target=target, now="2026-08-12T00:00:00+09:00",
            )
            self.assertEqual(deleted["status"], "deleted")
            self.assertFalse(trash.exists())

    def test_owned_result_is_not_an_orphan(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            work = root / ".work" / "goals" / "completed" / "2026-08" / "W-1"
            work.mkdir(parents=True)
            (work / "result.json").write_text("{}", encoding="utf-8")
            (work / "work.json").write_text(json.dumps({"work_id":"W-1","state":"completed"}), encoding="utf-8")
            self.assertNotIn("work.orphan", [finding["rule_id"] for finding in core.audit_work_lifecycle(root)["findings"]])


if __name__ == "__main__":
    unittest.main()
