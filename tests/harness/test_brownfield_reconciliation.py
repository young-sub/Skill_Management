from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = REPO_ROOT / "skills" / "setup-agent-harness" / "scripts" / "bootstrap_project.py"


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, capture_output=True, text=True, check=False
    )


def bootstrap(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return run(sys.executable, str(BOOTSTRAP), "reconcile", "--root", str(root), *extra)


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


class BrownfieldReconciliationTests(unittest.TestCase):
    def _init_git(self, root: Path) -> None:
        self.assertEqual(run("git", "init", "-q", cwd=root).returncode, 0)
        self.assertEqual(run("git", "config", "user.email", "fixture@example.test", cwd=root).returncode, 0)
        self.assertEqual(run("git", "config", "user.name", "Fixture", cwd=root).returncode, 0)

    def test_reconcile_discovers_evidence_without_mutating_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_git(root)
            (root / ".github/workflows").mkdir(parents=True)
            (root / "docs/architecture").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "AGENTS.md").write_text(
                "# Router\n\n- Architecture: `docs/architecture/system.md`\n- Verification: `TESTING.md`\n",
                encoding="utf-8",
            )
            (root / "CLAUDE.md").write_bytes((root / "AGENTS.md").read_bytes())
            testing = "# Testing\n\nKeep this prose exactly.\n\n```powershell\npython -m unittest\n```\n"
            (root / "TESTING.md").write_text(testing, encoding="utf-8", newline="\n")
            (root / "docs/architecture/system.md").write_text("# System\n\nDomain truth.\n", encoding="utf-8")
            (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\ntestpaths = ['tests']\n", encoding="utf-8")
            (root / "package.json").write_text(
                json.dumps({"scripts": {"test": "node --test"}}), encoding="utf-8"
            )
            (root / ".github/workflows/ci.yml").write_text(
                "jobs:\n  test:\n    steps:\n      - run: python -m unittest\n      - run: npm test\n",
                encoding="utf-8",
            )
            run("git", "add", ".", cwd=root)
            run("git", "commit", "-qm", "fixture", cwd=root)
            before = snapshot(root)

            first = bootstrap(root)
            middle = snapshot(root)
            second = bootstrap(root)
            after = snapshot(root)

            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertEqual(before, middle)
            self.assertEqual(before, after)
            one = json.loads(first.stdout)
            two = json.loads(second.stdout)
            self.assertEqual(one, two)
            self.assertEqual(one["mode"], "brownfield-reconcile")
            self.assertEqual(one["schema_version"], 1)
            self.assertEqual(one["discovery_fingerprint"], two["discovery_fingerprint"])
            evidence = one["discovery"]["evidence"]
            self.assertTrue(any(item["evidence_kind"] == "ci" for item in evidence))
            self.assertTrue(any(item["evidence_kind"] == "manifest" for item in evidence))
            commands = one["proposal"]["testing_merge_proposal"]["detected_commands"]
            self.assertTrue(all(item["source_pointer"] and item["confidence"] for item in commands))
            testing_input = next(item for item in one["inputs"] if item["path"] == "TESTING.md")
            self.assertEqual(testing_input["content_utf8"], testing)
            router = one["proposal"]["router_proposals"][0]
            self.assertIn("docs/architecture/system.md", router["referenced"])
            self.assertNotIn("Domain truth.", router["proposed_content"])
            architecture_authority = next(
                item
                for item in one["proposal"]["authority_candidates"]
                if item["path"] == "docs/architecture/system.md"
            )
            self.assertEqual(architecture_authority["precedence_rank"], 1)
            self.assertEqual(
                architecture_authority["precedence_basis"],
                "explicitly referenced by repository instruction",
            )

    def test_conflicting_authorities_and_commands_require_human_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_git(root)
            (root / ".github/workflows").mkdir(parents=True)
            (root / "AGENTS.md").write_text("Use `TESTING.md`.\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text("Use `CONTRIBUTING.md`.\n", encoding="utf-8")
            (root / "TESTING.md").write_text("# Testing\n\n`python -m unittest`\n", encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text("# Checks\n\n`python -m pytest`\n", encoding="utf-8")
            (root / ".github/workflows/ci.yml").write_text(
                "steps:\n  - run: python -m pytest\n", encoding="utf-8"
            )

            result = bootstrap(root)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            plan = json.loads(result.stdout)
            blocker_kinds = {item["kind"] for item in plan["proposal"]["blocking_decisions"]}
            self.assertIn("conflicting_instruction_authority", blocker_kinds)
            self.assertIn("conflicting_verification_commands", blocker_kinds)
            authorities = plan["proposal"]["authority_candidates"]
            self.assertGreaterEqual(len([a for a in authorities if a["authority_kind"] == "instructions"]), 2)
            merge = plan["proposal"]["testing_merge_proposal"]
            self.assertEqual(merge["preserved_content_utf8"], "# Testing\n\n`python -m unittest`\n")
            self.assertTrue(merge["human_decisions_required"])

    def test_git_path_policy_is_evidence_backed_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_git(root)
            (root / ".gitignore").write_text(".harness/\n.work/\nagent-env.*.md\n", encoding="utf-8")
            (root / "README.md").write_text("# Existing\n", encoding="utf-8")
            nested = root / "vendor/nested"
            nested.mkdir(parents=True)
            self._init_git(nested)
            run("git", "add", ".gitignore", "README.md", cwd=root)
            run("git", "commit", "-qm", "fixture", cwd=root)

            result = bootstrap(root)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            plan = json.loads(result.stdout)
            policy = {item["path"]: item for item in plan["proposal"]["path_policy"]}
            self.assertEqual(policy[".harness/project.yaml"]["desired_state"], "tracked")
            self.assertEqual(policy[".harness/project.yaml"]["current_state"], "ignored")
            self.assertTrue(policy[".harness/project.yaml"]["ignore_source"])
            self.assertEqual(policy[".work/**"]["desired_state"], "local-only")
            self.assertTrue(policy[".work/**"]["approval_required"])
            self.assertIn(".harness/**", policy)
            self.assertEqual(policy[".harness/**"]["desired_state"], "prohibited")
            blockers = plan["proposal"]["blocking_decisions"]
            self.assertTrue(any(item["severity"] == "high" and item["path"] == ".harness/project.yaml" for item in blockers))
            boundaries = plan["discovery"]["repository_boundaries"]
            self.assertTrue(any(item["kind"] == "nested_repository" and item["path"] == "vendor/nested" for item in boundaries))

    def test_report_path_is_explicit_and_does_not_change_plan_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            root.mkdir()
            self._init_git(root)
            report = root / ".work/reports/plan.json"

            stdout_result = bootstrap(root)
            report_result = bootstrap(root, "--report", str(report))

            self.assertEqual(report_result.returncode, 0, report_result.stderr + report_result.stdout)
            from_stdout = json.loads(stdout_result.stdout)
            from_report = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(from_stdout, from_report)
            self.assertEqual(from_stdout["plan_sha256"], json.loads(report_result.stdout)["plan_sha256"])
            outside = bootstrap(root, "--report", str(root.parent / "outside.json"))
            self.assertNotEqual(outside.returncode, 0)
            self.assertFalse((root.parent / "outside.json").exists())

    def test_plan_artifact_contains_digest_bound_apply_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._init_git(root)
            (root / "README.md").write_text("# Existing project\n", encoding="utf-8")

            result = bootstrap(root)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            plan = json.loads(result.stdout)
            self.assertRegex(plan["plan_sha256"], r"^[0-9a-f]{64}$")
            mutations = {item["path"]: item for item in plan["mutations"]}
            for path in ("AGENTS.md", "CLAUDE.md", "TESTING.md", ".harness/project.yaml"):
                self.assertIn(path, mutations)
                mutation = mutations[path]
                self.assertEqual(mutation["operation"], "create")
                self.assertIsNone(mutation["before_sha256"])
                self.assertRegex(mutation["after_sha256"], r"^[0-9a-f]{64}$")
                self.assertEqual(mutation["desired_state"], "tracked")
                self.assertEqual(mutation["approval_class"], "plan")
                self.assertTrue(mutation["after_content_base64"])
            local = mutations[".gitignore"]
            self.assertEqual(local["approval_class"], "local-only:.work/")
            self.assertEqual(local["desired_state"], "tracked")
            required_input_fields = {
                "path", "existence", "content_sha256", "git_state", "ignore_source"
            }
            self.assertTrue(all(required_input_fields <= item.keys() for item in plan["inputs"]))


if __name__ == "__main__":
    unittest.main()
