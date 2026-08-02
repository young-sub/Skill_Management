import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_skill(skill: str, alias: str):
    path = ROOT / "skills" / skill / "scripts" / "core_harness.py"
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    return {
        "schema_version": 3, "work_id": "W-forward", "goal": "핵심 흐름 검증",
        "scope": "대표 구현 흐름 검증", "non_goals": ["외부 게시"],
        "items": [{
            "id": "I-01", "title": "핵심 구현", "behavior_type": "tool",
            "what": "공개 Skill이 Item 계약을 처리한다.", "steps": ["입력", "검증", "출력"],
            "terms": [{"term": "Item", "explanation": "독립 검증 가능한 구현 단위"}],
            "tests": ["관찰 가능한 결과 확인"], "done": ["관련 검증 통과"],
            "depends_on": [], "non_goals": [], "decision": {"state": "resolved"},
            "material_risks": [], "priority": "core",
        }],
    }


def result_payload() -> dict:
    return {
        "items": [{
            "id": "I-01", "actual": "공개 Skill이 계약을 처리했다.",
            "actual_steps": ["입력", "검증", "출력"],
            "checks": [{"kind": "Impacted", "status": "passed", "command": "python -m unittest test_feature"}],
            "done": [True], "delta": {"material": False},
        }],
        "full": {"status": "not_required", "rule": "independent-capability"},
    }


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)


def init_repository(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "agent@example.com")
    git(root, "config", "user.name", "Agent")


class CoreFirstForwardWorkflowTests(unittest.TestCase):
    def test_tiny_independent_feature_runs_design_execute_commit_and_close(self) -> None:
        design = load_skill("design-goal", "forward_design")
        execute = load_skill("execute-codex-goal", "forward_execute")
        close = load_skill("close-goal", "forward_close")
        source = contract()
        design_html = design.render_design_review_v3(source)
        approved = design.approve_review(
            source, design_html, utterance="approved", actor="human",
            approved_at="2026-08-02T12:00:00+09:00",
        )["contract"]
        self.assertTrue(execute.execution_authorized(approved, design_html, host_goal=None)["authorized"])
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            init_repository(repo)
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-qm", "base")
            (repo / "feature.py").write_text("VALUE = 1\n", encoding="utf-8")
            committed = execute.commit_item(repo, "I-01", ["feature.py"], dirty_baseline=[])
            self.assertEqual(committed["status"], "committed")
        impact = execute.select_impacted_checks(["feature.py"], {"impact": {"rules": [{
            "id": "feature", "source_prefixes": ["feature.py"], "tests": ["test_feature"],
            "feature": "tiny", "full": False,
        }]}})
        self.assertEqual(impact["tests"], ["test_feature"])
        evaluated = close.evaluate_result(approved, result_payload(), impact)
        self.assertEqual(evaluated["status"], "complete")
        self.assertIn('lang="ko"', close.render_result_review_v3(approved, result_payload()))

    def test_brownfield_mixed_document_reconciliation_preserves_production(self) -> None:
        setup = load_skill("setup-agent-harness", "forward_setup")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ("src", "docs", "handbook", "notes"):
                (root / relative).mkdir()
            (root / "src" / "app.py").write_bytes(b"VALUE = 1\r\n")
            (root / "docs" / "index.md").write_text("# Current\n", encoding="utf-8")
            (root / "handbook" / "operators.md").write_text("# Operators\n", encoding="utf-8")
            legacy_bytes = b"# Old guide\r\n"
            (root / "notes" / "guide.md").write_bytes(legacy_bytes)
            (root / "README.md").write_text("See notes/guide.md\n", encoding="utf-8")
            mapping = {
                "source_roots": ["src"], "test_roots": [], "fixture_roots": [],
                "generated_roots": [], "durable_document_roots": ["docs"],
                "human_guide_roots": ["handbook", "notes", "README.md"],
                "documentation_entrypoint": "docs/index.md",
            }
            self.assertEqual(setup.build_mapping_plan(root, mapping)["unresolved"], [])
            plan = setup.build_cleanup_plan(root, mode="document-only", source_roots=["src"], ownership=mapping, operations=[
                {"action": "move", "source": "notes/guide.md", "target": "docs/guide.md"},
                {"action": "replace", "path": "README.md", "old": "notes/guide.md", "new": "docs/guide.md"},
            ])
            applied = setup.apply_transaction(root, plan, approval_digest=plan["digest"])
            self.assertEqual(applied["status"], "committed")
            self.assertEqual(applied["production_hashes_before"], applied["production_hashes_after"])
            self.assertEqual((root / "docs" / "guide.md").read_bytes(), legacy_bytes)

    def test_large_suite_selects_only_impacted_capability(self) -> None:
        execute = load_skill("execute-codex-goal", "forward_large_suite")
        rules = [{
            "id": f"cap-{index}", "source_prefixes": [f"src/cap_{index}/"],
            "tests": [f"tests/test_cap_{index}.py"], "feature": f"cap-{index}", "full": False,
        } for index in range(500)]
        selected = execute.select_impacted_checks(["src/cap_347/feature.py"], {"impact": {"rules": rules}})
        self.assertEqual(selected["tests"], ["tests/test_cap_347.py"])
        self.assertEqual(selected["features"], ["cap-347"])
        self.assertFalse(selected["full_required"])
        self.assertEqual(selected["unresolved"], [])

    def test_mid_execution_low_risk_amendment_rebinds_and_continues(self) -> None:
        design = load_skill("design-goal", "forward_amend_design")
        execute = load_skill("execute-codex-goal", "forward_amend_execute")
        source = contract()
        original_review = design.render_design_review_v3(source)
        approved = design.approve_review(
            source, original_review, utterance="approved", actor="human",
            approved_at="2026-08-02T12:00:00+09:00",
        )["contract"]
        amendment = execute.apply_amendment(
            approved, item_id="I-01", field="what", value="공개 Skill이 계약을 안전하게 처리한다.",
            message_id="message-42", actor="human", approved_at="2026-08-02T12:30:00+09:00", risk="low",
        )
        self.assertEqual(amendment["status"], "applied")
        self.assertEqual(amendment["event"]["kind"], "approved_amendment")
        self.assertTrue(execute.execution_authorized(
            amendment["contract"], amendment["review_html"], host_goal=None,
        )["authorized"])

    def test_parallel_independent_worktrees_commit_and_integrate(self) -> None:
        execute = load_skill("execute-codex-goal", "forward_worktrees")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo, worktree_a, worktree_b = root / "repo", root / "item-a", root / "item-b"
            repo.mkdir()
            init_repository(repo)
            (repo / "a.txt").write_text("base a\n", encoding="utf-8")
            (repo / "b.txt").write_text("base b\n", encoding="utf-8")
            git(repo, "add", "a.txt", "b.txt")
            git(repo, "commit", "-qm", "base")
            git(repo, "worktree", "add", "-q", "-b", "item-a", str(worktree_a), "HEAD")
            git(repo, "worktree", "add", "-q", "-b", "item-b", str(worktree_b), "HEAD")
            (worktree_a / "a.txt").write_text("implemented a\n", encoding="utf-8")
            (worktree_b / "b.txt").write_text("implemented b\n", encoding="utf-8")
            self.assertEqual(execute.commit_item(worktree_a, "I-A", ["a.txt"], dirty_baseline=[])["status"], "committed")
            self.assertEqual(execute.commit_item(worktree_b, "I-B", ["b.txt"], dirty_baseline=[])["status"], "committed")
            git(repo, "merge", "--no-edit", "item-a")
            git(repo, "merge", "--no-edit", "item-b")
            self.assertEqual((repo / "a.txt").read_text(encoding="utf-8"), "implemented a\n")
            self.assertEqual((repo / "b.txt").read_text(encoding="utf-8"), "implemented b\n")
            git(repo, "worktree", "remove", "--force", str(worktree_a))
            git(repo, "worktree", "remove", "--force", str(worktree_b))


if __name__ == "__main__":
    unittest.main()
