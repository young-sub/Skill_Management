import importlib.util
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import os
import threading
from unittest import mock


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
    return json.loads(
        (ROOT / "authoring" / "templates" / "project" / "project.yaml").read_text(encoding="utf-8")
    )


def init_git_repository(root: Path, *, branch: str = "develop") -> str:
    subprocess.run(["git", "init", "-b", branch], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    (root / ".gitignore").write_text(".work/\n/.worktree/\n", encoding="utf-8")
    (root / "README.md").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True,
    ).stdout.strip()


def authorized_contract(core, work_id: str) -> dict:
    source = contract()
    source["work_id"] = work_id
    outcome = core.authorize_design(
        source, intent="default", actor="policy",
        authorized_at="2026-08-09T12:00:00+09:00",
    )
    assert outcome["status"] == "default_authorized"
    return outcome["contract"]


def write_design_only(root: Path, core, source: dict) -> tuple[Path, bytes, bytes]:
    work_root = root / ".work" / "goals" / "active" / source["work_id"]
    review_root = work_root / "review"
    review_root.mkdir(parents=True)
    contract_bytes = (
        json.dumps(source, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    review_bytes = core.render_design_review_v3(core._contract_payload(source)).encode("utf-8")
    (work_root / "contract.json").write_bytes(contract_bytes)
    (review_root / "design.html").write_bytes(review_bytes)
    return work_root, contract_bytes, review_bytes


def git_branch(root: Path) -> str:
    return subprocess.run(
        ["git", "branch", "--show-current"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def git_reflog(root: Path) -> str:
    return subprocess.run(
        ["git", "reflog", "--format=%H:%gs"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout


def project_policy(*, protected: tuple[str, ...] = ("main",)) -> dict:
    project = v3_project()
    project["git"]["protected_branches"] = list(protected)
    project["git"]["branch_pattern"] = "wp-{work_id}-{slug}"
    return project


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

    def test_start_revalidates_project_configuration_before_git_mutation(self) -> None:
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
            invalid = v3_project()
            invalid["harness"] = {"active_cohort": "v4"}

            result = core.start_work(root, "W-start", "feature", authorized, project=invalid)

            self.assertEqual(result["status"], "authorization_failed")
            self.assertIn("unknown_legacy_harness_configuration", result["errors"])
            branch = subprocess.run(
                ["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True,
            ).stdout.strip()
            self.assertEqual(branch, "develop")

    def test_start_creates_missing_work_on_unprotected_current_branch_and_captures_baseline(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            revision = init_git_repository(root)
            (root / "README.md").write_text("dirty baseline\n", encoding="utf-8")
            (root / "untracked.txt").write_text("preserve\n", encoding="utf-8")
            source = authorized_contract(core, "W-new")

            result = core.start_work(
                root, "W-new", "feature", source,
                project=project_policy(protected=("main",)),
            )

            self.assertEqual(result["status"], "started", result)
            self.assertEqual(git_branch(root), "develop")
            manifest = result["manifest"]
            self.assertEqual(manifest["source_commit"], revision)
            self.assertEqual(manifest["base_branch"], "develop")
            self.assertEqual(manifest["feature_branch"], "develop")
            baseline_paths = {entry["path"] for entry in manifest["dirty_baseline"]["entries"]}
            self.assertEqual(baseline_paths, {"README.md", "untracked.txt"})
            self.assertTrue((root / ".work" / "goals" / "active" / "W-new" / "work.json").is_file())

    def test_start_promotes_valid_design_only_and_preserves_existing_bytes(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            revision = init_git_repository(root)
            source = authorized_contract(core, "W-design-only")
            work_root, contract_bytes, review_bytes = write_design_only(root, core, source)

            result = core.start_work(
                root, "W-design-only", "feature", source,
                project=project_policy(protected=("main",)),
            )

            self.assertEqual(result["status"], "started", result)
            self.assertEqual(git_branch(root), "develop")
            self.assertEqual((work_root / "contract.json").read_bytes(), contract_bytes)
            self.assertEqual((work_root / "review" / "design.html").read_bytes(), review_bytes)
            self.assertEqual(result["manifest"]["source_commit"], revision)
            self.assertTrue((work_root / "work.json").is_file())

    def test_start_rejects_stored_contract_mismatch_before_git_mutation(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root, branch="main")
            source = authorized_contract(core, "W-contract-drift")
            work_root, _, _ = write_design_only(root, core, source)
            stored = json.loads((work_root / "contract.json").read_text(encoding="utf-8"))
            stored["goal"] = "drifted"
            (work_root / "contract.json").write_text(json.dumps(stored), encoding="utf-8")
            before_reflog = git_reflog(root)

            result = core.start_work(
                root, "W-contract-drift", "feature", source,
                project=project_policy(protected=("main",)),
            )

            self.assertEqual(result["status"], "conflict", result)
            self.assertIn("stored_contract_mismatch", result["errors"])
            self.assertEqual(git_reflog(root), before_reflog)
            self.assertEqual(git_branch(root), "main")
            self.assertFalse((work_root / "work.json").exists())

    def test_start_rejects_canonical_review_mismatch_before_git_mutation(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root, branch="main")
            source = authorized_contract(core, "W-review-drift")
            work_root, _, _ = write_design_only(root, core, source)
            (work_root / "review" / "design.html").write_bytes(b"drift\n")
            before_reflog = git_reflog(root)

            result = core.start_work(
                root, "W-review-drift", "feature", source,
                project=project_policy(protected=("main",)),
            )

            self.assertEqual(result["status"], "conflict", result)
            self.assertIn("canonical_review_mismatch", result["errors"])
            self.assertEqual(git_reflog(root), before_reflog)
            self.assertFalse((work_root / "work.json").exists())

    def test_start_rejects_authorization_digest_mismatch_before_git_mutation(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root, branch="main")
            source = authorized_contract(core, "W-authorization-drift")
            source["authorization"]["contract_digest"] = "sha256:" + "0" * 64
            work_root, _, _ = write_design_only(root, core, source)
            before_reflog = git_reflog(root)

            result = core.start_work(
                root, "W-authorization-drift", "feature", source,
                project=project_policy(protected=("main",)),
            )

            self.assertEqual(result["status"], "authorization_failed", result)
            self.assertIn("authorization_bundle_drift", result["errors"])
            self.assertEqual(git_reflog(root), before_reflog)
            self.assertFalse((work_root / "work.json").exists())

    def test_start_returns_already_started_only_for_the_same_intact_goal(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root)
            source = authorized_contract(core, "W-idempotent")
            work_root, _, _ = write_design_only(root, core, source)
            first = core.start_work(
                root, "W-idempotent", "feature", source,
                project=project_policy(),
            )
            before_reflog = git_reflog(root)

            second = core.start_work(
                root, "W-idempotent", "feature", source,
                project=project_policy(),
            )

            self.assertEqual(first["status"], "started", first)
            self.assertEqual(second["status"], "already_started", second)
            self.assertEqual(second["manifest"], json.loads((work_root / "work.json").read_text(encoding="utf-8")))
            self.assertEqual(git_reflog(root), before_reflog)

    def test_start_rejects_wrong_identity_or_state_manifest_as_conflict(self) -> None:
        core = load_core()
        cases = (
            ("work_id", "W-other", "work_identity_conflict"),
            ("state", "completed", "work_state_conflict"),
            ("dirty_baseline", {}, "work_manifest_invalid:dirty_baseline"),
        )
        for field, value, expected_error in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                init_git_repository(root)
                source = authorized_contract(core, "W-manifest-conflict")
                work_root, _, _ = write_design_only(root, core, source)
                started = core.start_work(root, "W-manifest-conflict", "feature", source, project=project_policy())
                self.assertEqual(started["status"], "started", started)
                manifest_path = work_root / "work.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest[field] = value
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                result = core.start_work(root, "W-manifest-conflict", "feature", source, project=project_policy())

                self.assertEqual(result["status"], "conflict", result)
                self.assertIn(expected_error, result["errors"])

    def test_start_never_treats_a_corrupt_manifest_as_already_started(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root)
            source = authorized_contract(core, "W-corrupt")
            work_root, _, _ = write_design_only(root, core, source)
            (work_root / "work.json").write_bytes(b"{not-json")

            try:
                result = core.start_work(root, "W-corrupt", "feature", source, project=project_policy())
            except Exception as error:  # The public boundary must fail closed, not raise parser errors.
                self.fail(f"corrupt manifest escaped start_work: {error}")

            self.assertEqual(result["status"], "conflict", result)
            self.assertIn("work_manifest_corrupt", result["errors"])

    def test_start_rolls_back_created_branch_and_partial_manifest_on_write_failure(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root, branch="main")
            source = authorized_contract(core, "W-write-fault")
            work_root, contract_bytes, review_bytes = write_design_only(root, core, source)
            real_replace = os.replace

            def fail_manifest_replace(source_path, destination_path):
                if Path(destination_path).name == "work.json":
                    raise OSError("injected manifest write failure")
                return real_replace(source_path, destination_path)

            with mock.patch.object(core.os, "replace", side_effect=fail_manifest_replace):
                failed = core.start_work(
                    root, "W-write-fault", "feature", source,
                    project=project_policy(protected=("main",)),
                )

            self.assertEqual(failed["status"], "precondition_failed", failed)
            self.assertIn("injected manifest write failure", " ".join(failed["errors"]))
            self.assertEqual(git_branch(root), "main")
            branches = subprocess.run(
                ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"],
                cwd=root, check=True, capture_output=True, text=True,
            ).stdout.splitlines()
            self.assertEqual(branches, ["main"])
            self.assertEqual((work_root / "contract.json").read_bytes(), contract_bytes)
            self.assertEqual((work_root / "review" / "design.html").read_bytes(), review_bytes)
            self.assertFalse((work_root / "work.json").exists())
            self.assertFalse((work_root / "work.json.tmp").exists())

    def test_start_partial_write_failure_does_not_pollute_the_next_call(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root, branch="main")
            source = authorized_contract(core, "W-retry")
            work_root, _, _ = write_design_only(root, core, source)
            real_replace = os.replace

            def fail_once(source_path, destination_path):
                if Path(destination_path).name == "work.json":
                    raise OSError("retryable manifest failure")
                return real_replace(source_path, destination_path)

            with mock.patch.object(core.os, "replace", side_effect=fail_once):
                first = core.start_work(root, "W-retry", "feature", source, project=project_policy())
            second = core.start_work(root, "W-retry", "feature", source, project=project_policy())

            self.assertEqual(first["status"], "precondition_failed", first)
            self.assertEqual(second["status"], "started", second)
            self.assertTrue((work_root / "work.json").is_file())

    @unittest.skipUnless(os.name == "nt", "Windows directory regression")
    def test_windows_design_only_directory_promotes_without_winerror_183(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root)
            source = authorized_contract(core, "W-windows-existing")
            work_root, contract_bytes, review_bytes = write_design_only(root, core, source)

            result = core.start_work(root, "W-windows-existing", "feature", source, project=project_policy())

            self.assertEqual(result["status"], "started", result)
            self.assertNotIn("WinError 183", " ".join(result.get("errors", [])))
            self.assertEqual((work_root / "contract.json").read_bytes(), contract_bytes)
            self.assertEqual((work_root / "review" / "design.html").read_bytes(), review_bytes)

    def test_start_rejects_collision_artifacts_and_incomplete_transactions_before_git(self) -> None:
        core = load_core()
        cases = {
            "collision": "unexpected_work_artifact:unexpected.tmp",
            "applying": "incomplete_transaction:unfinished:applying",
            "rollback_failed": "incomplete_transaction:unfinished:rollback_failed",
            "missing_journal": "transaction_journal_missing:unfinished",
        }
        for case, expected_error in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                init_git_repository(root, branch="main")
                source = authorized_contract(core, f"W-{case}")
                work_root, _, _ = write_design_only(root, core, source)
                if case == "collision":
                    (work_root / "unexpected.tmp").write_text("collision", encoding="utf-8")
                elif case != "missing_journal":
                    journal = root / ".work" / "transactions" / "unfinished" / "journal.json"
                    journal.parent.mkdir(parents=True)
                    journal.write_text(json.dumps({"status": case, "kind": "lifecycle_move"}), encoding="utf-8")
                else:
                    (root / ".work" / "transactions" / "unfinished").mkdir(parents=True)
                before_reflog = git_reflog(root)

                result = core.start_work(
                    root, f"W-{case}", "feature", source,
                    project=project_policy(protected=("main",)),
                )

                self.assertIn(result["status"], {"conflict", "precondition_failed"}, result)
                self.assertIn(expected_error, result["errors"])
                self.assertEqual(git_reflog(root), before_reflog)
                self.assertFalse((work_root / "work.json").exists())

    def test_start_rejects_an_aliased_design_only_root_before_git(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root, branch="main")
            source = authorized_contract(core, "W-alias")
            external = root / "external-design"
            external.mkdir()
            active = root / ".work" / "goals" / "active"
            active.mkdir(parents=True)
            alias = active / "W-alias"
            try:
                os.symlink(external, alias, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            before_reflog = git_reflog(root)

            try:
                result = core.start_work(
                    root, "W-alias", "feature", source,
                    project=project_policy(protected=("main",)),
                )
            except Exception as error:
                self.fail(f"aliased work root escaped start_work: {error}")

            self.assertIn(result["status"], {"conflict", "precondition_failed"}, result)
            self.assertEqual(git_reflog(root), before_reflog)

    def test_parallel_design_create_with_the_same_slug_reserves_unique_work_roots(self) -> None:
        core = load_core()
        create = getattr(core, "design_create", None)
        self.assertIsNotNone(create, "design_create entrypoint is required")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = contract()
            source["work_id"] = ""
            observed_temporary_names: list[str] = []
            real_replace = os.replace

            def capture_replace(source_path, destination_path):
                observed_temporary_names.append(Path(source_path).name)
                return real_replace(source_path, destination_path)

            def invoke(_index: int) -> dict:
                return create(
                    root, source, slug="same-human-slug", work_id=None,
                    intent="default", actor="policy",
                    authorized_at="2026-08-09T12:00:00+09:00",
                )

            with mock.patch.object(core.os, "replace", side_effect=capture_replace):
                with ThreadPoolExecutor(max_workers=8) as executor:
                    outcomes = list(executor.map(invoke, range(8)))

            self.assertEqual([item["status"] for item in outcomes], ["created"] * 8, outcomes)
            work_ids = [item["work_id"] for item in outcomes]
            self.assertEqual(len(set(work_ids)), 8)
            self.assertEqual(len(observed_temporary_names), len(set(observed_temporary_names)))
            for work_id in work_ids:
                work_root = root / ".work" / "goals" / "active" / work_id
                files = {
                    path.relative_to(work_root).as_posix()
                    for path in work_root.rglob("*") if path.is_file()
                }
                self.assertEqual(files, {"contract.json", "review/design.html"})
                stored = json.loads((work_root / "contract.json").read_text(encoding="utf-8"))
                self.assertEqual(stored["work_id"], work_id)
                self.assertTrue(core.execution_authorized(stored)["authorized"])

    def test_parallel_design_create_with_one_explicit_id_has_one_owner_and_conflicts(self) -> None:
        core = load_core()
        create = getattr(core, "design_create", None)
        self.assertIsNotNone(create, "design_create entrypoint is required")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = contract()
            source["work_id"] = "W-explicit-owner"

            def invoke(_index: int) -> dict:
                return create(
                    root, source, slug="same", work_id="W-explicit-owner",
                    intent="default", actor="policy",
                    authorized_at="2026-08-09T12:00:00+09:00",
                )

            with ThreadPoolExecutor(max_workers=8) as executor:
                outcomes = list(executor.map(invoke, range(8)))

            statuses = [item["status"] for item in outcomes]
            self.assertEqual(statuses.count("created"), 1, outcomes)
            self.assertEqual(statuses.count("conflict"), 7, outcomes)
            work_root = root / ".work" / "goals" / "active" / "W-explicit-owner"
            self.assertEqual(
                {
                    path.relative_to(work_root).as_posix()
                    for path in work_root.rglob("*") if path.is_file()
                },
                {"contract.json", "review/design.html"},
            )

    def test_design_create_write_failure_rolls_back_only_its_reserved_root(self) -> None:
        core = load_core()
        create = getattr(core, "design_create", None)
        self.assertIsNotNone(create, "design_create entrypoint is required")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            kept = contract()
            kept["work_id"] = "W-kept"
            created = create(
                root, kept, slug="kept", work_id="W-kept", intent="default",
                actor="policy", authorized_at="2026-08-09T12:00:00+09:00",
            )
            self.assertEqual(created["status"], "created", created)
            failing = contract()
            failing["work_id"] = "W-failing"
            real_replace = os.replace

            def fail_review(source_path, destination_path):
                if Path(destination_path).name == "design.html":
                    raise OSError("injected design review write failure")
                return real_replace(source_path, destination_path)

            with mock.patch.object(core.os, "replace", side_effect=fail_review):
                result = create(
                    root, failing, slug="failing", work_id="W-failing", intent="default",
                    actor="policy", authorized_at="2026-08-09T12:00:00+09:00",
                )

            self.assertEqual(result["status"], "write_failed", result)
            self.assertTrue((root / ".work" / "goals" / "active" / "W-kept").is_dir())
            self.assertFalse((root / ".work" / "goals" / "active" / "W-failing").exists())
            self.assertEqual(list(root.rglob("*.tmp")), [])

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
            result = core.commit_item(
                root, "I-01", ["item.txt"], "feat(example): implement item",
                dirty_baseline=["dirty.txt"],
            )
            self.assertEqual(result["status"], "committed")
            changed = subprocess.run(["git", "show", "--pretty=", "--name-only", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
            self.assertEqual(changed, ["item.txt"])
            self.assertIn("dirty.txt", subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True, check=True).stdout)
            self.assertEqual(subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines(), ["staged.txt"])

    def test_worktree_lifecycle_uses_the_ignored_project_local_directory(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            init_git_repository(root)

            created = core.create_worktree(
                root, base="develop", branch="feature/item-a",
            )

            expected = root / ".worktree" / "wt-feature%2Fitem-a"
            self.assertEqual(created["status"], "created", created)
            self.assertEqual(Path(created["path"]), expected)
            self.assertTrue(expected.is_dir())
            self.assertFalse((root.parent / "feature-item-a").exists())

            project = v3_project()
            project["git"]["protected_branches"] = []
            integrated = core.integrate_worktree(
                root, base="develop", branch="feature/item-a",
                project=project, approved_exact_path=str(expected),
            )

            self.assertEqual(integrated["status"], "integrated", integrated)
            self.assertFalse(expected.exists())

    def test_worktree_creation_requires_a_real_ignored_local_root(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            init_git_repository(root)
            (root / ".gitignore").write_text(".work/\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "remove worktree ignore"], cwd=root, check=True, capture_output=True)

            result = core.create_worktree(
                root, base="develop", branch="feature-item",
            )

            self.assertEqual(result["status"], "precondition_failed", result)
            self.assertIn("worktree_root_not_ignored", result["errors"])
            self.assertFalse((root / ".worktree").exists())

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

            alias = core.commit_item(
                root, "I-01", ["./docs/guide.md"], "docs(example): update guide",
                dirty_baseline=baseline,
            )
            directory = core.commit_item(
                root, "I-01", ["docs"], "docs(example): update guide",
                dirty_baseline=baseline,
            )

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
        project = v3_project()
        project["impact"] = {
            "rules": [
                {"id": "auth", "source_prefixes": ["src/auth/"], "tests": ["tests/auth"], "feature": "auth", "triggers": []},
                {"id": "shared", "source_prefixes": ["src/core/"], "tests": ["tests/core"], "feature": "core", "triggers": ["shared_policy"]},
            ],
            "feature_selectors": {"auth": ["python", "-m", "unittest", "tests.auth"], "core": ["python", "-m", "unittest", "tests.core"]},
            "full_triggers": ["shared_policy"],
        }
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

    def test_project_consumers_fail_closed_before_git_or_impact_selection(self) -> None:
        core = load_core()
        invalid = {"schema_version": 3, "unexpected": True}

        impacted = core.select_impacted_checks(["src/auth/service.py"], invalid)

        self.assertEqual(impacted["status"], "invalid")
        self.assertTrue(impacted["unresolved"])
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(core.subprocess, "run") as run:
                integrated = core.integrate_worktree(
                    root, base="develop", branch="feature",
                    project=invalid,
                    approved_exact_path=str(root / ".worktree" / "wt-feature"),
                )

            self.assertEqual(integrated["status"], "precondition_failed", integrated)
            self.assertIn("project_config:unknown_field:unexpected", integrated["errors"])
            run.assert_not_called()

    def test_parallel_start_has_one_transition_owner_and_never_rolls_back_the_winner(self) -> None:
        core = load_core()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repository(root, branch="develop")
            source = authorized_contract(core, "W-parallel-start")
            work_root, _, _ = write_design_only(root, core, source)
            policy = project_policy(protected=("main",))
            barrier = threading.Barrier(8)
            thread_state = threading.local()
            classify = core._classify_start_root

            def synchronized_classify(*args, **kwargs):
                outcome = classify(*args, **kwargs)
                if (
                    outcome.get("classification") == "valid_design_only"
                    and not getattr(thread_state, "initial_classification_complete", False)
                ):
                    thread_state.initial_classification_complete = True
                    barrier.wait(timeout=10)
                return outcome

            def invoke(_):
                return core.start_work(
                    root, source["work_id"], "parallel", source, project=policy,
                )

            with mock.patch.object(core, "_classify_start_root", side_effect=synchronized_classify):
                with ThreadPoolExecutor(max_workers=8) as pool:
                    outcomes = list(pool.map(invoke, range(8)))

            statuses = [outcome["status"] for outcome in outcomes]
            self.assertEqual(statuses.count("started"), 1, outcomes)
            self.assertTrue(all(status in {"started", "already_started", "conflict"} for status in statuses))
            manifest = json.loads((work_root / "work.json").read_text(encoding="utf-8"))
            self.assertEqual(core._validate_active_manifest(manifest, source["work_id"], source), [])


if __name__ == "__main__":
    unittest.main()
