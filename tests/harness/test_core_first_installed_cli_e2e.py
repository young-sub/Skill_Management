import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def cli(skill: str) -> Path:
    return ROOT / "skills" / skill / "scripts" / "core_harness.py"


def run_cli(skill: str, *args: str, cwd: Path | None = None) -> dict:
    completed = subprocess.run(
        ["python", str(cli(skill)), *args], cwd=cwd, text=True,
        capture_output=True, check=False,
    )
    if completed.returncode:
        raise AssertionError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def contract() -> dict:
    def item(item_id: str, depends_on: list[str]) -> dict:
        return {
            "id": item_id, "title": item_id, "behavior_type": "tool",
            "what": "deliver output", "steps": ["input", "output"], "terms": [],
            "tests": [{"id": "T-01", "target": "output", "method": "run", "expected": "pass", "selector": "python -m unittest sample"}],
            "done": [{"id": "D-01", "criterion": "output is delivered"}],
            "depends_on": depends_on, "non_goals": [], "decision": {"state": "resolved"},
            "material_risks": [], "priority": "core",
        }
    return {
        "schema_version": 3, "work_id": "W-e2e", "goal": "deliver",
        "scope": "one capability", "non_goals": [],
        "items": [item("I-01", []), item("I-02", ["I-01"])],
    }


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


class InstalledCliEndToEndTests(unittest.TestCase):
    def test_01_tiny_feature_default_authorizes_and_completes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "contract.json"
            write_json(source, contract())
            authorized = run_cli(
                "design-goal", "authorize", "--contract", str(source), "--intent", "default",
                "--actor", "policy", "--at", "2026-08-02T12:00:00+09:00",
            )
            authorized_path = root / "authorized.json"
            write_json(authorized_path, authorized["contract"])
            result = {
                "items": [{
                    "id": item_id, "checks": [{"check_id": "T-01", "status": "passed", "command": "python -m unittest sample"}],
                    "criteria": [{"criterion_id": "D-01", "criterion": "output is delivered", "status": "passed", "evidence": "observed"}],
                    "delta": {"material": False},
                } for item_id in ("I-01", "I-02")],
                "full": {"status": "not_required", "rule": "feature"},
            }
            impact = {"full_required": False, "unresolved": [], "not_required_rule_ids": ["feature"]}
            result_path, impact_path = root / "result.json", root / "impact.json"
            write_json(result_path, result)
            write_json(impact_path, impact)
            completed = run_cli(
                "close-goal", "complete", "--contract", str(authorized_path),
                "--result", str(result_path), "--impact", str(impact_path),
            )
            self.assertEqual(completed["status"], "complete")

    def test_02_brownfield_cleanup_uses_cli_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "notes").mkdir()
            (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "notes" / "guide.md").write_text("guide\n", encoding="utf-8")
            request = {
                "mode": "document-only", "source_roots": ["src"],
                "ownership": {"source_roots": ["src"], "durable_document_roots": ["docs", "notes"]},
                "operations": [{"action": "move", "source": "notes/guide.md", "target": "docs/guide.md"}],
            }
            request_path = root / "request.json"
            write_json(request_path, request)
            planned = run_cli("setup-agent-harness", "cleanup-plan", "--root", str(root), "--request", str(request_path))
            plan_path = root / "plan.json"
            write_json(plan_path, planned)
            applied = run_cli(
                "setup-agent-harness", "cleanup-apply", "--root", str(root), "--plan", str(plan_path),
                "--approval-digest", planned["plan"]["digest"],
            )
            self.assertEqual(applied["status"], "committed")
            self.assertTrue((root / "docs" / "guide.md").is_file())

    def test_03_large_suite_selects_one_cli_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rules = [{
                "id": f"cap-{index}", "source_prefixes": [f"src/cap_{index}/"],
                "tests": [f"tests/test_cap_{index}.py"], "feature": f"cap-{index}", "triggers": [],
            } for index in range(500)]
            selectors = {f"cap-{index}": ["python", "-m", "unittest", f"tests.test_cap_{index}"] for index in range(500)}
            project_path = root / "project.json"
            write_json(project_path, {"impact": {"rules": rules, "feature_selectors": selectors, "full_triggers": []}})
            selected = run_cli(
                "execute-codex-goal", "impacted", "--project", str(project_path),
                "--changed", "src/cap_347/feature.py",
            )
            self.assertEqual(selected["matched_rules"], ["cap-347"])
            self.assertEqual(len(selected["feature_commands"]), 1)

    def test_04_low_risk_amendment_rebinds_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "contract.json"
            write_json(source, contract())
            authorized = run_cli(
                "design-goal", "authorize", "--contract", str(source), "--intent", "default",
                "--actor", "policy", "--at", "2026-08-02T12:00:00+09:00",
            )
            write_json(source, authorized["contract"])
            value = root / "value.json"
            value.write_text(json.dumps("deliver safer output"), encoding="utf-8")
            amended = run_cli(
                "execute-codex-goal", "amend", "--contract", str(source), "--item-id", "I-01",
                "--field", "what", "--value", str(value), "--message-id", "m-1", "--actor", "human",
                "--at", "2026-08-02T12:30:00+09:00", "--risk", "low",
            )
            self.assertEqual(amended["status"], "applied")
            self.assertEqual(amended["contract"]["authorization"]["mode"], "default")

    def test_05_parallel_worktrees_create_commit_and_integrate_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            container = Path(temp_dir)
            root = container / "repo"
            root.mkdir()
            git(root, "init", "-q")
            git(root, "config", "user.email", "agent@example.com")
            git(root, "config", "user.name", "Agent")
            (root / "README.md").write_text("base\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-qm", "base")
            base = git(root, "branch", "--show-current")
            project = root / "project.json"
            write_json(project, {"git": {"protected_branches": []}})
            worktrees = [("item-a", container / "work-a", "a.txt"), ("item-b", container / "work-b", "b.txt")]
            for branch, path, filename in worktrees:
                created = run_cli(
                    "execute-codex-goal", "worktree-create", "--root", str(root), "--base", base,
                    "--branch", branch, "--path", str(path),
                )
                self.assertEqual(created["status"], "created")
                baseline = run_cli("execute-codex-goal", "baseline", "--root", str(path))
                baseline_path = container / f"{branch}-baseline.json"
                write_json(baseline_path, baseline)
                (path / filename).write_text(branch + "\n", encoding="utf-8")
                committed = run_cli(
                    "execute-codex-goal", "commit", "--root", str(path), "--item-id", branch,
                    "--path", filename, "--baseline", str(baseline_path),
                )
                self.assertEqual(committed["status"], "committed")
            for branch, path, _ in worktrees:
                integrated = run_cli(
                    "execute-codex-goal", "worktree-integrate", "--root", str(root), "--base", base,
                    "--branch", branch, "--path", str(path), "--project", str(project),
                    "--approved-exact-path", str(path),
                )
                self.assertEqual(integrated["status"], "integrated")
            self.assertTrue((root / "a.txt").is_file())
            self.assertTrue((root / "b.txt").is_file())
            self.assertFalse((container / "work-a").exists())
            self.assertFalse((container / "work-b").exists())


if __name__ == "__main__":
    unittest.main()
