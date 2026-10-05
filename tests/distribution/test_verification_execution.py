import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VIEWER = ROOT / "authoring" / "scripts" / "verification_results.py"
RUN_CHECK = ROOT / "scripts" / "run_check.py"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VerificationExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.evidence = self.root / "evidence"
        self._git("init", "-q")
        self._git("config", "user.name", "fixture")
        self._git("config", "user.email", "fixture@example.invalid")
        (self.project / "dependency.txt").write_text("dep-1\n", encoding="utf-8")
        (self.project / "fixture.json").write_text(
            json.dumps({"a": 2, "b": 3, "readback": "ok"}), encoding="utf-8"
        )
        (self.project / ".gitignore").write_text("result.json\n", encoding="utf-8")
        (self.project / "check.py").write_text(
            """import json\nfrom pathlib import Path\n\nfixture = json.loads(Path('fixture.json').read_text())\nPath('result.json').write_text(json.dumps({'checks': [{'sum': fixture['a'] + fixture['b'], 'readback': fixture['readback']}] }))\n""",
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-qm", "fixture")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.project), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def _plan(
        self,
        *,
        assertions=None,
        child=None,
        report="result.json",
        dependency_refs=None,
        fixture_refs=None,
    ) -> Path:
        head = self._git("rev-parse", "HEAD").strip()
        diff = _digest(self._git("diff", "HEAD", "--binary").encode())
        plan = {
            "schema_version": 1,
            "plan_id": "execution-fixture",
            "checks": [
                {
                    "id": "arithmetic-readback",
                    "feature_id": "fixture-product",
                    "expected": "arithmetic and readback facts are observed",
                    "criteria_revision": "criteria-1",
                    "required": True,
                    "selection": {"status": "selected", "reason": "focused execution"},
                    "conditions": {
                        "source": {"revision": head, "diff": diff},
                        "criteria": {"revision": "criteria-1"},
                        "command": {
                            "argv": [sys.executable, str(child or self.project / "check.py")],
                            "cwd": str(self.project),
                        },
                        "dependency": {"file_refs": dependency_refs or ["dependency.txt"]},
                        "fixture": {"file_refs": fixture_refs or ["fixture.json"]},
                        "runtime": {"id": "fixture-runtime"},
                    },
                    "raw_observations": [
                        {
                            "path": report,
                            "pointer": "$.checks[0]",
                            "assertions": assertions
                            if assertions is not None
                            else [
                                {"pointer": "$.checks[0].sum", "equals": 5},
                                {"pointer": "$.checks[0].readback", "equals": "ok"},
                            ],
                        }
                    ],
                }
            ],
        }
        path = self.root / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def _execute(
        self,
        plan: Path,
        *,
        timeout: str | None = None,
        evidence_dir: Path | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [
            sys.executable,
            str(VIEWER),
            "--execute",
            "--plan",
            str(plan),
            "--run-check",
            str(RUN_CHECK),
            "--evidence-dir",
            str(evidence_dir or self.evidence),
        ]
        if timeout is not None:
            command.extend(["--timeout", timeout])
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result, json.loads(result.stdout)

    def _viewer_module(self):
        spec = importlib.util.spec_from_file_location("verification_results_fixture", VIEWER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)
        return module

    def test_execute_child_report_binds_facts_and_current_passes(self) -> None:
        result, payload = self._execute(self._plan())

        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload["current"]["status"], "PASS")
        item = payload["items"][0]
        self.assertEqual(item["current_status"], "PASS")
        self.assertEqual([row["actual"] for row in item["raw"][0]["observations"]], [5, "ok"])
        self.assertEqual(item["capture"]["execution"], "exited")
        self.assertEqual(item["capture"]["exit_code"], 0)
        self.assertEqual(item["raw"][0]["producer"]["run_id"], item["run_id"])
        runtime = item["conditions"]["expected"]["runtime"]
        self.assertTrue(runtime["executable"])
        self.assertEqual(len(runtime["executable_sha256"]), 64)
        self.assertTrue(runtime["python_version"])

    def test_failed_explicit_assertion_is_not_pass(self) -> None:
        child = self.project / "bad.py"
        child.write_text(
            "from pathlib import Path\nPath('result.json').write_text('{\"checks\":[{\"sum\": 4, \"readback\": \"ok\"}]}')\n",
            encoding="utf-8",
        )
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload["current"]["status"], "PASS")
        self.assertTrue(any("raw_assertion_mismatch" in reason for reason in payload["remaining"]))

    def test_submitted_pass_string_cannot_hide_a_bad_fact(self) -> None:
        child = self.project / "misleading.py"
        child.write_text(
            "from pathlib import Path\n"
            "Path('result.json').write_text('{\"status\":\"PASS\",\"checks\":[{\"sum\": 4, \"readback\": \"ok\"}]}')\n",
            encoding="utf-8",
        )
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload["current"]["status"], "PASS")

    def test_missing_assertions_block_before_starting_a_child(self) -> None:
        marker = self.project / "preflight-marker"
        child = self.project / "should-not-start.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        plan = self._plan(child=child, assertions=[])

        result, payload = self._execute(plan)

        self.assertEqual(result.returncode, 2, payload)
        self.assertFalse(marker.exists())
        self.assertEqual(payload["test_commands_executed"], 0)

    def test_zero_and_skip_facts_are_rejected_by_explicit_assertions(self) -> None:
        for index, (body, assertion) in enumerate(
            (
                ('{"checks": []}', {"pointer": "$.checks", "min_count": 1}),
                ('{"checks": [{"skipped": true}]}', {"pointer": "$.checks[0].skipped", "equals": False}),
            )
        ):
            with self.subTest(body=body):
                child = self.project / "edge.py"
                (self.project / "result.json").unlink(missing_ok=True)
                child.write_text(
                    f"from pathlib import Path\nPath('result.json').write_text({body!r})\n",
                    encoding="utf-8",
                )
                result, payload = self._execute(
                    self._plan(child=child, assertions=[assertion]),
                    evidence_dir=self.root / f"evidence-{index}",
                )
                self.assertNotEqual(result.returncode, 0, payload)
                self.assertNotEqual(payload["current"]["status"], "PASS")
                self.assertTrue(
                    any(
                        "raw_assertion_mismatch" in reason or "raw_pointer_missing" in reason
                        for reason in payload["remaining"]
                    ),
                    payload,
                )

    def test_missing_native_report_is_blocked(self) -> None:
        child = self.project / "missing.py"
        child.write_text("pass\n", encoding="utf-8")
        result, payload = self._execute(self._plan(child=child))

        self.assertEqual(result.returncode, 2, payload)
        self.assertEqual(payload["current"]["status"], "BLOCKED")
        self.assertTrue(any("raw" in reason or "report" in reason for reason in payload["remaining"]))

    def test_existing_native_report_is_never_reused(self) -> None:
        marker = self.project / "executed"
        (self.project / "result.json").write_text(
            '{"checks":[{"sum":5,"readback":"ok"}]}', encoding="utf-8"
        )
        child = self.project / "should-not-run.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertFalse(marker.exists())

    def test_dependency_change_during_run_makes_result_stale(self) -> None:
        child = self.project / "mutate.py"
        child.write_text(
            "from pathlib import Path\nPath('dependency.txt').write_text('changed\\n')\n"
            "Path('result.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )
        result, payload = self._execute(self._plan(child=child))

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertIn(payload["items"][0]["current_reuse"], {"STALE", "UNKNOWN"})

    def test_lookup_without_execute_does_not_run_selected_command(self) -> None:
        marker = self.project / "lookup-ran"
        child = self.project / "lookup.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        plan = self._plan(child=child)
        result = subprocess.run(
            [sys.executable, str(VIEWER), "--plan", str(plan)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertFalse(marker.exists())
        self.assertEqual(json.loads(result.stdout)["test_commands_executed"], 0)

    def test_view_bundle_remeasures_current_files_without_execution_or_writes(self) -> None:
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bundle = payload["execution"]["bundle"]
        bound = Path(bundle["plan"])
        before = bound.read_bytes()
        (self.project / "fixture.json").write_text(
            json.dumps({"a": 9, "b": 3, "readback": "ok"}), encoding="utf-8"
        )

        viewed = self._viewer_module().view_bundle(bundle)
        persisted = Path(payload["execution"]["bundle_path"])
        persisted_before = persisted.read_bytes()
        viewed_from_path = self._viewer_module().view_bundle(persisted)

        self.assertNotEqual(viewed["status"], "PASS")
        self.assertEqual(viewed_from_path["status"], viewed["status"])
        self.assertEqual(viewed["test_commands_executed"], 0)
        self.assertEqual(bound.read_bytes(), before)
        self.assertEqual(persisted.read_bytes(), persisted_before)
        self.assertTrue(any("current.fixture" in reason for reason in viewed["remaining"]))

    def test_persisted_bundle_view_passes_current_without_execution(self) -> None:
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bundle_path = Path(payload["execution"]["bundle_path"])
        viewed = self._viewer_module().view_bundle(bundle_path)

        self.assertEqual(viewed["status"], "PASS")
        self.assertEqual(viewed["test_commands_executed"], 0)
        self.assertEqual(viewed["items"][0]["capture"]["argv"], [sys.executable, str(self.project / "check.py")])
        lookup = subprocess.run([sys.executable, str(VIEWER), '--bundle', str(bundle_path)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(lookup.stdout)['test_commands_executed'], 0)

    def test_bundle_without_measured_runtime_identity_is_blocked(self) -> None:
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bound = Path(payload["execution"]["bundle"]["plan"])
        plan = json.loads(bound.read_text(encoding="utf-8"))
        plan["checks"][0]["conditions"]["runtime"].pop("executable", None)
        plan["checks"][0]["conditions"]["runtime"].pop("executable_sha256", None)
        bound.write_text(json.dumps(plan), encoding="utf-8")

        viewed = self._viewer_module().view_bundle(Path(payload["execution"]["bundle_path"]))

        self.assertEqual(viewed["status"], "BLOCKED")
        self.assertIn("runtime_identity_missing", " ".join(viewed["remaining"]))

    def test_symlink_file_reference_and_native_report_are_blocked_before_child(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink support is unavailable")
        marker = self.project / "alias-marker"
        child = self.project / "alias-child.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        dependency_link = self.project / "dependency-link.txt"
        report_link = self.project / "report-link.json"
        try:
            os.symlink(self.project / "dependency.txt", dependency_link)
            os.symlink(self.root / "outside-report.json", report_link)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")
        for dependency_refs, report in ((["dependency-link.txt"], "result.json"), (["dependency.txt"], "report-link.json")):
            with self.subTest(dependency_refs=dependency_refs, report=report):
                marker.unlink(missing_ok=True)
                plan = self._plan(child=child, dependency_refs=dependency_refs, report=report)
                result, payload = self._execute(plan)
                self.assertEqual(result.returncode, 2, payload)
                self.assertFalse(marker.exists())

    def test_view_bundle_rejects_mutated_source_plan(self) -> None:
        _, payload = self._execute(self._plan())
        bundle = payload["execution"]["bundle"]
        source_plan = Path(bundle["source_plan"])
        source_plan.write_text(source_plan.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        viewed = self._viewer_module().view_bundle(bundle)

        self.assertEqual(viewed["status"], "BLOCKED")
        self.assertIn("source_plan_hash_mismatch", viewed["remaining"])

    def test_private_or_escaped_file_and_report_paths_block_before_child(self) -> None:
        marker = self.project / "blocked-marker"
        child = self.project / "marker.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
        outside = self.root / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        for dependency_refs, report in (([str(outside)], "result.json"), ([".env"], "result.json"), (["dependency.txt"], "../outside-report.json")):
            with self.subTest(dependency_refs=dependency_refs, report=report):
                if dependency_refs == [".env"]:
                    (self.project / ".env").write_text("secret", encoding="utf-8")
                plan = self._plan(child=child, dependency_refs=dependency_refs, report=report)
                result, payload = self._execute(plan)
                self.assertEqual(result.returncode, 2, payload)
                self.assertFalse(marker.exists())

    def test_nonfinite_timeout_blocks_before_child(self) -> None:
        marker = self.project / "timeout-marker"
        child = self.project / "timeout-check.py"
        child.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")

        result, payload = self._execute(self._plan(child=child), timeout="inf")

        self.assertEqual(result.returncode, 2, payload)
        self.assertFalse(marker.exists())

    def test_each_check_remeasures_files_before_starting_the_next_child(self) -> None:
        second_marker = self.project / "second-ran"
        first = self.project / "first.py"
        second = self.project / "second.py"
        first.write_text(
            "from pathlib import Path\n"
            "Path('dependency.txt').write_text('changed\\n')\n"
            "Path('result.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )
        second.write_text(
            f"from pathlib import Path\nPath({str(second_marker)!r}).touch()\n"
            "Path('result-2.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )
        plan = json.loads(self._plan(child=first, report="result.json").read_text(encoding="utf-8"))
        second_check = json.loads(json.dumps(plan["checks"][0]))
        second_check["id"] = "second-check"
        second_check["conditions"]["command"]["argv"] = [sys.executable, str(second)]
        second_check["raw_observations"][0]["path"] = "result-2.json"
        plan["checks"].append(second_check)
        plan_path = self.root / "multi-plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")

        result, payload = self._execute(plan_path)

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertFalse(second_marker.exists())
        self.assertTrue(any("precondition" in reason or "raw" in reason for reason in payload["remaining"]))

    def test_original_plan_mutation_during_child_invalidates_current_pass(self) -> None:
        child = self.project / "mutate-plan.py"
        plan = self._plan(child=child)
        child.write_text(
            f"from pathlib import Path\n"
            f"plan = Path({str(plan)!r})\n"
            "plan.write_text(plan.read_text() + '\\n')\n"
            "Path('result.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n",
            encoding="utf-8",
        )

        result, payload = self._execute(plan)

        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload["current"]["status"], "PASS")
        self.assertTrue(payload["execution"]["source_plan_changed_during_execution"])

    def test_bound_criteria_cannot_diverge_from_unchanged_original_plan(self) -> None:
        import runpy
        result, payload = self._execute(self._plan())
        self.assertEqual(result.returncode, 0, payload)
        bundle = payload['execution']['bundle']
        path = Path(bundle['plan'])
        bound = json.loads(path.read_text(encoding='utf-8'))
        bound['checks'][0]['expected'] = 'a different requirement never selected'
        path.write_text(json.dumps(bound), encoding='utf-8')
        viewed = runpy.run_path(str(VIEWER))['view_bundle'](bundle)
        self.assertEqual(viewed['status'], 'BLOCKED', viewed)

    def test_later_check_invalidates_earlier_ignored_fixture_before_return(self) -> None:
        (self.project / '.gitignore').write_text('result.json\nresult-2.json\nexternal.txt\n', encoding='utf-8')
        (self.project / 'external.txt').write_text('before', encoding='utf-8')
        second = self.project / 'second.py'
        second.write_text("from pathlib import Path\nPath('external.txt').write_text('after')\nPath('result-2.json').write_text('{\"checks\":[{\"sum\":5,\"readback\":\"ok\"}]}')\n", encoding='utf-8')
        path = self._plan()
        plan = json.loads(path.read_text(encoding='utf-8'))
        following = json.loads(json.dumps(plan['checks'][0]))
        plan['checks'][0]['conditions']['fixture'] = {'file_refs': ['external.txt']}
        following['id'] = 'later'
        following['conditions']['command']['argv'] = [sys.executable, str(second)]
        following['raw_observations'][0]['path'] = 'result-2.json'
        plan['checks'].append(following)
        path.write_text(json.dumps(plan), encoding='utf-8')
        result, payload = self._execute(path)
        self.assertNotEqual(result.returncode, 0, payload)
        self.assertNotEqual(payload['items'][0]['current_status'], 'PASS', payload)


if __name__ == "__main__":
    unittest.main()
