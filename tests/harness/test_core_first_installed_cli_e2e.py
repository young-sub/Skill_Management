import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = Path(os.environ.get("HARNESS_SKILLS_ROOT", str(ROOT / "skills")))


def cli(skill: str) -> Path:
    return SKILLS_ROOT / skill / "scripts" / "core_harness.py"


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


def project_config() -> dict:
    return json.loads(
        (ROOT / "authoring" / "templates" / "project" / "project.yaml").read_text(encoding="utf-8")
    )


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
            project = project_config()
            project["impact"] = {"rules": rules, "feature_selectors": selectors, "full_triggers": []}
            write_json(project_path, project)
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
            (root / ".gitignore").write_text("/.worktree/\n", encoding="utf-8")
            git(root, "add", "README.md", ".gitignore")
            git(root, "commit", "-qm", "base")
            base = git(root, "branch", "--show-current")
            project = root / "project.json"
            integration_project = project_config()
            integration_project["git"]["protected_branches"] = []
            write_json(project, integration_project)
            worktrees = [
                ("item-a", root / ".worktree" / "wt-item-a", "a.txt"),
                ("item-b", root / ".worktree" / "wt-item-b", "b.txt"),
            ]
            for branch, path, filename in worktrees:
                created = run_cli(
                    "execute-codex-goal", "worktree-create", "--root", str(root), "--base", base,
                    "--branch", branch,
                )
                self.assertEqual(created["status"], "created")
                self.assertEqual(Path(created["path"]), path)
                baseline = run_cli("execute-codex-goal", "baseline", "--root", str(path))
                baseline_path = container / f"{branch}-baseline.json"
                write_json(baseline_path, baseline)
                (path / filename).write_text(branch + "\n", encoding="utf-8")
                committed = run_cli(
                    "execute-codex-goal", "commit", "--root", str(path), "--item-id", branch,
                    "--path", filename, "--baseline", str(baseline_path),
                    "--message", f"feat(example): implement {branch}",
                )
                self.assertEqual(committed["status"], "committed")
            for branch, path, _ in worktrees:
                integrated = run_cli(
                    "execute-codex-goal", "worktree-integrate", "--root", str(root), "--base", base,
                    "--branch", branch, "--project", str(project),
                    "--approved-exact-path", str(path),
                )
                self.assertEqual(integrated["status"], "integrated")
            self.assertTrue((root / "a.txt").is_file())
            self.assertTrue((root / "b.txt").is_file())
            self.assertFalse((root / ".worktree" / "wt-item-a").exists())
            self.assertFalse((root / ".worktree" / "wt-item-b").exists())

    def test_06_windows_design_only_start_uses_the_bundled_execute_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            git(root, "init", "-b", "develop")
            git(root, "config", "user.email", "agent@example.com")
            git(root, "config", "user.name", "Agent")
            (root / ".gitignore").write_text(".work/\n", encoding="utf-8")
            (root / "README.md").write_text("base\n", encoding="utf-8")
            git(root, "add", ".gitignore", "README.md")
            git(root, "commit", "-m", "base")
            project_root = root / ".harness"
            project_root.mkdir()
            project = project_config()
            project["git"]["protected_branches"] = ["main"]
            project["git"]["branch_pattern"] = "wp-{work_id}-{slug}"
            write_json(project_root / "project.yaml", project)
            source = contract()
            source["work_id"] = "W-e2e-start"
            source_path = root / "source.json"
            write_json(source_path, source)
            authorized = run_cli(
                "design-goal", "authorize", "--contract", str(source_path), "--intent", "default",
                "--actor", "policy", "--at", "2026-08-09T12:00:00+09:00",
            )["contract"]
            work_root = root / ".work" / "goals" / "active" / "W-e2e-start"
            (work_root / "review").mkdir(parents=True)
            contract_path = work_root / "contract.json"
            write_json(contract_path, authorized)
            design_path = work_root / "review" / "design.html"
            run_cli(
                "design-goal", "render-design", "--contract", str(contract_path),
                "--output", str(design_path),
            )
            contract_bytes = contract_path.read_bytes()
            review_bytes = design_path.read_bytes()

            completed = subprocess.run(
                [
                    "python", str(cli("execute-codex-goal")), "start", "--root", str(root),
                    "--work-id", "W-e2e-start", "--slug", "feature", "--contract", str(contract_path),
                ],
                cwd=root, text=True, capture_output=True, check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            started = json.loads(completed.stdout)
            self.assertEqual(started["status"], "started", started)
            self.assertEqual(git(root, "branch", "--show-current"), "develop")
            self.assertEqual(contract_path.read_bytes(), contract_bytes)
            self.assertEqual(design_path.read_bytes(), review_bytes)
            self.assertTrue((work_root / "work.json").is_file())

    def test_07_parallel_design_create_is_isolated_and_explicit_collision_has_one_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_source = contract()
            generated_source["work_id"] = ""
            generated_path = root / "generated.json"
            write_json(generated_path, generated_source)

            def invoke_generated(_index: int) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        "python", str(cli("design-goal")), "design-create", "--root", str(root),
                        "--contract", str(generated_path), "--slug", "same-slug",
                        "--actor", "policy", "--at", "2026-08-09T12:00:00+09:00",
                    ],
                    text=True, capture_output=True, check=False,
                )

            with ThreadPoolExecutor(max_workers=4) as executor:
                generated_runs = list(executor.map(invoke_generated, range(4)))
            self.assertEqual(
                [run.returncode for run in generated_runs], [0] * 4,
                [run.stderr or run.stdout for run in generated_runs],
            )
            generated = [json.loads(run.stdout) for run in generated_runs]
            self.assertEqual(len({item["work_id"] for item in generated}), 4)

            explicit_source = contract()
            explicit_source["work_id"] = "W-cli-explicit"
            explicit_path = root / "explicit.json"
            write_json(explicit_path, explicit_source)

            def invoke_explicit(_index: int) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        "python", str(cli("design-goal")), "design-create", "--root", str(root),
                        "--contract", str(explicit_path), "--slug", "same-slug",
                        "--work-id", "W-cli-explicit", "--actor", "policy",
                        "--at", "2026-08-09T12:00:00+09:00",
                    ],
                    text=True, capture_output=True, check=False,
                )

            with ThreadPoolExecutor(max_workers=4) as executor:
                explicit_runs = list(executor.map(invoke_explicit, range(4)))
            explicit = [json.loads(run.stdout) for run in explicit_runs]
            statuses = [item["status"] for item in explicit]
            self.assertEqual(statuses.count("created"), 1, explicit)
            self.assertEqual(statuses.count("conflict"), 3, explicit)
            self.assertEqual(sorted(run.returncode for run in explicit_runs), [0, 2, 2, 2])

            invalid_root = subprocess.run(
                [
                    "python", str(cli("design-goal")), "design-create",
                    "--root", str(root / "missing"), "--contract", str(generated_path),
                    "--slug", "same-slug", "--actor", "policy",
                    "--at", "2026-08-09T12:00:00+09:00",
                ],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(invalid_root.returncode, 2, invalid_root.stderr or invalid_root.stdout)
            self.assertEqual(json.loads(invalid_root.stdout)["status"], "invalid_root")


if __name__ == "__main__":
    unittest.main()
