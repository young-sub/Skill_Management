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


def project_config(impact: dict) -> dict:
    project = json.loads(
        (ROOT / "authoring" / "templates" / "project" / "project.yaml").read_text(encoding="utf-8")
    )
    project["impact"] = impact
    return project


def contract() -> dict:
    return {
        "schema_version": 3, "work_id": "W-forward", "goal": "핵심 흐름 검증",
        "scope": "대표 구현 흐름 검증", "non_goals": ["외부 게시"],
        "items": [{
            "id": "I-01", "title": "핵심 구현", "behavior_type": "tool",
            "what": "공개 Skill이 Item 계약을 처리한다.", "steps": ["입력", "검증", "출력"],
            "terms": [{"term": "Item", "explanation": "독립 검증 가능한 구현 단위"}],
            "tests": [{"id": "T-01", "target": "observable result", "method": "python -m unittest test_feature", "expected": "pass", "selector": "python -m unittest test_feature"}],
            "done": [{"id": "D-01", "criterion": "relevant verification passes"}],
            "depends_on": [], "non_goals": [], "decision": {"state": "resolved"},
            "material_risks": [], "priority": "core",
        }, {
            "id": "I-02", "title": "결과 보고", "behavior_type": "tool",
            "what": "실행 결과를 보고한다.", "steps": ["수집", "보고"], "terms": [],
            "tests": [{"id": "T-01", "target": "result report", "method": "python -m unittest test_feature", "expected": "pass", "selector": "python -m unittest test_feature"}],
            "done": [{"id": "D-01", "criterion": "relevant verification passes"}],
            "depends_on": ["I-01"], "non_goals": [], "decision": {"state": "resolved"},
            "material_risks": [], "priority": "core",
        }],
    }


def result_payload() -> dict:
    return {
        "items": [{
            "id": "I-01", "actual": "공개 Skill이 계약을 처리했다.",
            "actual_steps": ["입력", "검증", "출력"],
            "checks": [{"check_id": "T-01", "kind": "Impacted", "status": "passed", "command": "python -m unittest test_feature"}],
            "criteria": [{"criterion_id": "D-01", "criterion": "relevant verification passes", "status": "passed", "evidence": "test passed"}],
            "delta": {"material": False},
        }, {
            "id": "I-02", "actual": "결과를 보고했다.", "actual_steps": ["수집", "보고"],
            "checks": [{"check_id": "T-01", "kind": "Impacted", "status": "passed", "command": "python -m unittest test_feature"}],
            "criteria": [{"criterion_id": "D-01", "criterion": "relevant verification passes", "status": "passed", "evidence": "test passed"}],
            "delta": {"material": False},
        }],
        "full": {"status": "not_required", "rule": "feature"},
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
        approved = design.authorize_design(
            source, intent="default", actor="policy",
            authorized_at="2026-08-02T12:00:00+09:00",
        )["contract"]
        self.assertTrue(execute.execution_authorized(approved, host_goal=None)["authorized"])
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            init_repository(repo)
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-qm", "base")
            (repo / "feature.py").write_text("VALUE = 1\n", encoding="utf-8")
            committed = execute.commit_item(
                repo, "I-01", ["feature.py"], "feat(example): add tiny feature",
                dirty_baseline=[],
            )
            self.assertEqual(committed["status"], "committed")
        impact = execute.select_impacted_checks(
            ["feature.py"],
            project_config({"rules": [{
                "id": "feature", "source_prefixes": ["feature.py"], "tests": ["test_feature"],
                "feature": "tiny", "triggers": [],
            }], "feature_selectors": {"tiny": ["python", "-m", "unittest", "test_feature"]}, "full_triggers": []}),
            logic_impact={
                "changed_logic": ["feature.VALUE"], "affected_behaviors": ["tiny feature output"],
                "scope": "local", "reason": "One independent feature changed.",
                "tests": ["test_feature"],
            },
        )
        self.assertEqual(impact["tests"], ["test_feature"])
        evaluated = close.evaluate_result(approved, result_payload(), impact)
        self.assertEqual(evaluated["status"], "complete")

    def test_brownfield_mixed_document_reconciliation_preserves_production(self) -> None:
        setup = load_skill("setup-agent-harness", "forward_setup")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in ("src", "docs", "handbook", "notes"):
                (root / relative).mkdir()
            production_bytes = b"VALUE = 1\r\n"
            (root / "src" / "app.py").write_bytes(production_bytes)
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
            self.assertNotIn("production_hashes_before", applied)
            self.assertNotIn("production_hashes_after", applied)
            self.assertEqual((root / "src" / "app.py").read_bytes(), production_bytes)
            self.assertEqual((root / "docs" / "guide.md").read_bytes(), legacy_bytes)

    def test_test_only_relocation_preserves_real_collection_outcome_and_production(self) -> None:
        cli = ROOT / "skills" / "setup-agent-harness" / "scripts" / "core_harness.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "tests" / "old").mkdir(parents=True)
            test_source = (
                "import unittest\n\n"
                "class FeatureTests(unittest.TestCase):\n"
                "    def test_behavior(self):\n"
                "        self.assertEqual(1, 1)\n"
            )
            (root / "tests" / "old" / "test_feature.py").write_text(test_source, encoding="utf-8")
            before_hash = (root / "src" / "app.py").read_bytes()
            before = subprocess.run(
                ["python", "-m", "unittest", "discover", "-v", "-s", "tests/old"],
                cwd=root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(before.returncode, 0, before.stderr)

            request = {
                "mode": "test-only", "source_roots": ["src"],
                "ownership": {"source_roots": ["src"], "test_roots": ["tests"]},
                "operations": [{"action": "move", "source": "tests/old/test_feature.py", "target": "tests/new/test_feature.py"}],
            }
            request_path = root / "request.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            planned = subprocess.run(
                ["python", str(cli), "cleanup-plan", "--root", str(root), "--request", str(request_path)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            plan_payload = json.loads(planned.stdout)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan_payload), encoding="utf-8")
            applied = subprocess.run(
                ["python", str(cli), "cleanup-apply", "--root", str(root), "--plan", str(plan_path),
                 "--approval-digest", plan_payload["plan"]["digest"]],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(json.loads(applied.stdout)["status"], "committed")

            after = subprocess.run(
                ["python", "-m", "unittest", "discover", "-v", "-s", "tests/new"],
                cwd=root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(after.returncode, 0, after.stderr)
            before_identity = [line for line in before.stderr.splitlines() if line.startswith("test_behavior")]
            after_identity = [line for line in after.stderr.splitlines() if line.startswith("test_behavior")]
            self.assertEqual(before_identity, after_identity)
            self.assertEqual((root / "src" / "app.py").read_bytes(), before_hash)
            local_selector = {"id": "local", "capability": "test-relocation", "argv": ["python", "-m", "unittest", "discover", "-s", "tests/new"]}
            ci_selector = {"id": "ci", "capability": "test-relocation", "argv": ["python", "-m", "unittest", "discover", "-v", "-s", "tests/new"]}
            self.assertEqual(local_selector["capability"], ci_selector["capability"])

    def test_large_suite_selects_only_impacted_capability(self) -> None:
        execute = load_skill("execute-codex-goal", "forward_large_suite")
        rules = [{
            "id": f"cap-{index}", "source_prefixes": [f"src/cap_{index}/"],
            "tests": [f"tests/test_cap_{index}.py"], "feature": f"cap-{index}", "triggers": [],
        } for index in range(500)]
        selectors = {f"cap-{index}": ["python", "-m", "unittest", f"tests.test_cap_{index}"] for index in range(500)}
        selected = execute.select_impacted_checks(
            ["src/cap_347/feature.py"],
            project_config({"rules": rules, "feature_selectors": selectors, "full_triggers": []}),
            logic_impact={
                "changed_logic": ["cap_347 feature branch"],
                "affected_behaviors": ["capability 347 output"],
                "scope": "local", "reason": "Only capability 347 changed.",
                "tests": ["tests/test_cap_347.py"],
            },
        )
        self.assertEqual(selected["tests"], ["tests/test_cap_347.py"])
        self.assertEqual(selected["features"], [])
        self.assertEqual(selected["candidate_features"], ["cap-347"])
        self.assertFalse(selected["full_required"])
        self.assertEqual(selected["unresolved"], [])

    def test_mid_execution_low_risk_amendment_rebinds_and_continues(self) -> None:
        design = load_skill("design-goal", "forward_amend_design")
        execute = load_skill("execute-codex-goal", "forward_amend_execute")
        source = contract()
        approved = design.authorize_design(
            source, intent="default", actor="policy",
            authorized_at="2026-08-02T12:00:00+09:00",
        )["contract"]
        amendment = execute.apply_amendment(
            approved, item_id="I-01", field="what", value="공개 Skill이 계약을 안전하게 처리한다.",
            message_id="message-42", actor="human", approved_at="2026-08-02T12:30:00+09:00", risk="low",
        )
        self.assertEqual(amendment["status"], "applied")
        self.assertEqual(amendment["event"]["kind"], "approved_amendment")
        self.assertTrue(execute.execution_authorized(
            amendment["contract"], host_goal=None,
        )["authorized"])

    def test_parallel_independent_worktrees_commit_and_integrate(self) -> None:
        execute = load_skill("execute-codex-goal", "forward_worktrees")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            worktree_a = repo / ".worktree" / "item-a"
            worktree_b = repo / ".worktree" / "item-b"
            repo.mkdir()
            init_repository(repo)
            (repo / ".gitignore").write_text("/.worktree/\n", encoding="utf-8")
            (repo / "a.txt").write_text("base a\n", encoding="utf-8")
            (repo / "b.txt").write_text("base b\n", encoding="utf-8")
            git(repo, "add", ".gitignore", "a.txt", "b.txt")
            git(repo, "commit", "-qm", "base")
            git(repo, "worktree", "add", "-q", "-b", "item-a", str(worktree_a), "HEAD")
            git(repo, "worktree", "add", "-q", "-b", "item-b", str(worktree_b), "HEAD")
            (worktree_a / "a.txt").write_text("implemented a\n", encoding="utf-8")
            (worktree_b / "b.txt").write_text("implemented b\n", encoding="utf-8")
            self.assertEqual(execute.commit_item(
                worktree_a, "I-A", ["a.txt"], "feat(example): implement item a",
                dirty_baseline=[],
            )["status"], "committed")
            self.assertEqual(execute.commit_item(
                worktree_b, "I-B", ["b.txt"], "feat(example): implement item b",
                dirty_baseline=[],
            )["status"], "committed")
            git(repo, "merge", "--no-edit", "item-a")
            git(repo, "merge", "--no-edit", "item-b")
            self.assertEqual((repo / "a.txt").read_text(encoding="utf-8"), "implemented a\n")
            self.assertEqual((repo / "b.txt").read_text(encoding="utf-8"), "implemented b\n")
            git(repo, "worktree", "remove", "--force", str(worktree_a))
            git(repo, "worktree", "remove", "--force", str(worktree_b))


if __name__ == "__main__":
    unittest.main()
