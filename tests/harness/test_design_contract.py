import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE = REPO_ROOT / "skills" / "design-goal" / "scripts" / "contract_engine.py"
RENDERER = REPO_ROOT / "skills" / "design-goal" / "scripts" / "render_design_review.py"
FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def run_engine(root: Path, command: str = "validate", *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), command, "--root", str(root), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def copy_fixture(name: str, destination: Path) -> None:
    shutil.copytree(FIXTURES / name, destination, dirs_exist_ok=True)


class DesignContractTests(unittest.TestCase):
    def test_approve_requires_work_root_and_rechecks_duplicate_work_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            first = work_root / "first"
            second = work_root / "second"
            copy_fixture("small", first)

            missing_scope = run_engine(
                first, "approve", "--approved-at", "2026-07-19T18:00:00+09:00",
                "--approved-by", "human",
            )
            self.assertNotEqual(missing_scope.returncode, 0)
            self.assertIn("--work-root", missing_scope.stderr)

            # A duplicate created after design validation must still block approval.
            self.assertEqual(run_engine(first, "validate", "--work-root", str(work_root)).returncode, 0)
            copy_fixture("small", second)
            duplicate = run_engine(
                first, "approve", "--work-root", str(work_root),
                "--approved-at", "2026-07-19T18:00:00+09:00", "--approved-by", "human",
            )
            self.assertEqual(duplicate.returncode, 2, duplicate.stdout)
            self.assertIn("duplicate_work_id:W-20260719-101", json.loads(duplicate.stdout)["errors"])

    def test_small_contract_validates_but_pending_approval_cannot_execute(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_fixture("small", root)

            valid = run_engine(root)
            executable = run_engine(root, "validate", "--require-approved")

            self.assertEqual(valid.returncode, 0, valid.stderr)
            payload = json.loads(valid.stdout)
            self.assertEqual(payload["work_id"], "W-20260719-101")
            self.assertEqual(payload["plan_order"], [])
            self.assertEqual(payload["approval_status"], "pending")
            self.assertFalse(payload["executable"])
            self.assertFalse((root / "GOAL.md").exists())
            self.assertEqual(list((root / "plans").glob("*.md")), [])
            self.assertEqual(executable.returncode, 3, executable.stderr)
            self.assertIn("approval_required", json.loads(executable.stdout)["errors"])

    def test_approval_records_hash_and_contract_mutation_causes_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_fixture("small", root)

            approved = run_engine(
                root,
                "approve",
                "--work-root",
                str(root.parent),
                "--approved-at",
                "2026-07-19T18:00:00+09:00",
                "--approved-by",
                "human",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr)
            approved_hash = json.loads(approved.stdout)["contract_hash"]
            self.assertTrue(approved_hash.startswith("sha256:"))
            self.assertEqual(run_engine(root, "validate", "--require-approved").returncode, 0)

            spec = root / "SPEC.md"
            spec.write_text(
                spec.read_text(encoding="utf-8").replace(
                    "Deliver a verified greeting.", "Deliver a mutated greeting."
                ),
                encoding="utf-8",
                newline="\n",
            )

            drifted = run_engine(root, "validate", "--require-approved")
            self.assertEqual(drifted.returncode, 4, drifted.stderr)
            self.assertIn("contract_hash_drift", json.loads(drifted.stdout)["errors"])

    def test_multi_plan_contract_has_stable_topological_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_fixture("multi", root)

            first_result = run_engine(root)
            second_result = run_engine(root)
            self.assertEqual(first_result.returncode, 0, first_result.stdout)
            self.assertEqual(second_result.returncode, 0, second_result.stdout)
            first = json.loads(first_result.stdout)["plan_order"]
            second = json.loads(second_result.stdout)["plan_order"]

            self.assertEqual(first, ["P-01", "P-02", "P-03"])
            self.assertEqual(second, first)
            self.assertFalse((root / "SPEC.md").exists())

    def test_missing_dependency_and_cycle_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_fixture("multi", root)
            p3 = root / "plans" / "P-03.md"
            p3.write_text(
                p3.read_text(encoding="utf-8").replace('["P-01"]', '["P-99"]'),
                encoding="utf-8",
                newline="\n",
            )
            missing = run_engine(root)
            self.assertEqual(missing.returncode, 2, missing.stderr)
            self.assertIn("missing_dependency:P-03:P-99", json.loads(missing.stdout)["errors"])

            copy_fixture("multi", root)
            p1 = root / "plans" / "P-01.md"
            p1.write_text(
                p1.read_text(encoding="utf-8").replace("depends_on: []", 'depends_on: ["P-02"]'),
                encoding="utf-8",
                newline="\n",
            )
            cycle = run_engine(root)
            self.assertEqual(cycle.returncode, 2, cycle.stderr)
            self.assertIn("dependency_cycle", json.loads(cycle.stdout)["errors"])

    def test_required_sections_and_unique_work_id_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            first = work_root / "first"
            second = work_root / "second"
            copy_fixture("small", first)
            copy_fixture("small", second)
            spec = second / "SPEC.md"
            spec.write_text(
                spec.read_text(encoding="utf-8").replace(
                    "## Acceptance Criteria", "## Omitted Acceptance Criteria"
                ),
                encoding="utf-8",
                newline="\n",
            )

            invalid = run_engine(second, "validate", "--work-root", str(work_root))

            self.assertEqual(invalid.returncode, 2, invalid.stderr)
            errors = json.loads(invalid.stdout)["errors"]
            self.assertIn("missing_section:SPEC.md:Acceptance Criteria", errors)
            self.assertIn("duplicate_work_id:W-20260719-101", errors)

    def test_approval_requirements_and_dependencies_are_hashed_but_runtime_status_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_fixture("multi", root)
            baseline = json.loads(run_engine(root, "hash").stdout)["contract_hash"]
            p2 = root / "plans" / "P-02.md"
            p2.write_text(
                p2.read_text(encoding="utf-8").replace("status: pending", "status: completed"),
                encoding="utf-8",
                newline="\n",
            )
            self.assertEqual(json.loads(run_engine(root, "hash").stdout)["contract_hash"], baseline)

            p2.write_text(
                p2.read_text(encoding="utf-8").replace('["P-01"]', "[]"),
                encoding="utf-8",
                newline="\n",
            )
            self.assertNotEqual(json.loads(run_engine(root, "hash").stdout)["contract_hash"], baseline)

    def test_design_review_is_scriptless_escaped_and_contains_all_contract_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_fixture("small", root)
            marker = '<script>alert("contract")</script>'
            spec = root / "SPEC.md"
            spec.write_text(spec.read_text(encoding="utf-8") + "\n" + marker + "\n", encoding="utf-8")
            output = root / "design-review.html"

            rendered = subprocess.run(
                [sys.executable, str(RENDERER), "--root", str(root), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            page = output.read_text(encoding="utf-8")
            self.assertNotIn("<script", page.lower())
            self.assertIn(html.escape(marker), page)
            contract_files = [path for path in (root / "SPEC.md", root / "GOAL.md") if path.exists()]
            contract_files.extend((root / "plans").glob("*.md"))
            for contract_file in contract_files:
                self.assertIn(html.escape(contract_file.read_text(encoding="utf-8")), page)

    def test_skill_contracts_prevent_automatic_chaining_and_exploration_writes(self) -> None:
        explore = (REPO_ROOT / "skills" / "explore-idea" / "SKILL.md").read_text(encoding="utf-8")
        design = (REPO_ROOT / "skills" / "design-goal" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("read-only", explore)
        self.assertIn("Do not create or modify files", explore)
        self.assertIn("Do not invoke `design-goal`", explore)
        self.assertIn("Do not invoke `execute-codex-goal`", design)
        self.assertIn("Goal declaration payload", design)
        self.assertIn("stop", design.lower())

    def test_design_skill_uses_adaptive_bounded_interview(self) -> None:
        design = (REPO_ROOT / "skills" / "design-goal" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("bounded interview", design)
        self.assertIn("Repeat decision rounds", design)
        self.assertIn("Do not ask questions when no material decision remains", design)
        self.assertIn("human intent", design)
        self.assertNotIn("Ask one grouped decision question only", design)


if __name__ == "__main__":
    unittest.main()
