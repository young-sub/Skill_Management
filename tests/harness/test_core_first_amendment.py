import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from tests.harness.test_core_first_design_execution import contract, load_core, v3_project


class AmendmentTests(unittest.TestCase):
    def test_contract_item_count_follows_review_boundaries(self):
        core = load_core()
        source = contract()
        source["items"] = [dict(source["items"][0], id=f"I-{i}", depends_on=[]) for i in range(6)]
        self.assertEqual(core.validate_contract_v3(source), [])
        source["items"] = []
        self.assertIn("items:count_out_of_range", core.validate_contract_v3(source))

    def amendment(self, core, source, **changes):
        return core.apply_amendment(source, item_id="I-01", field="title", value="Clearer title",
                                    message_id="revision-1", actor="human",
                                    approved_at="2026-09-06T15:00:00+09:00", risk="low", **changes)

    def test_title_change_reuses_valid_explicit_authorization_but_rejects_drift(self):
        core = load_core()
        source = contract()
        source["items"][0]["material_risks"] = ["external_cost"]
        source = core.authorize_design(source, intent="explicit_approve", actor="human",
                                       authorized_at="2026-09-06T14:00:00+09:00")["contract"]
        amended = self.amendment(core, source)
        self.assertEqual(amended["status"], "applied", amended)
        self.assertEqual(amended["contract"]["authorization"]["mode"], "explicit")
        self.assertTrue(core.execution_authorized(amended["contract"])["authorized"])
        self.assertEqual(amended["contract"]["amendments"][-1], amended["event"])
        source["scope"] = "unapproved additional work"
        self.assertEqual(self.amendment(core, source)["status"], "invalid_amendment")

    def test_covered_selector_revision_uses_supplied_permission(self):
        core = load_core()
        source = contract()
        tests = [dict(source["items"][0]["tests"][0], selector="python -m unittest renamed_test")]
        amended = core.apply_amendment(
            source, item_id="I-01", field="tests", value=tests, message_id="selector-move",
            actor="human", approved_at="2026-09-06T15:00:00+09:00", risk="low",
            intent="explicit_approve",
        )
        self.assertEqual(amended["status"], "applied", amended)
        self.assertEqual(amended["contract"]["items"][0]["tests"], tests)

    def test_active_amendment_persists_without_resetting_baseline_and_rolls_back_on_failure(self):
        core = load_core()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
            git("init", "-q")
            git("config", "user.email", "agent@example.com")
            git("config", "user.name", "Agent")
            (root / ".harness").mkdir()
            (root / ".harness/project.yaml").write_text(json.dumps(v3_project()), encoding="utf-8")
            (root / ".gitignore").write_text(".work/\n", encoding="utf-8")
            (root / "user.txt").write_text("base\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-qm", "base")
            (root / "user.txt").write_text("preserve user edit\n", encoding="utf-8")
            source = core.authorize_design(contract(), actor="policy",
                                           authorized_at="2026-09-06T14:00:00+09:00")["contract"]
            work = root / ".work/goals/active" / source["work_id"]
            work.mkdir(parents=True)
            (work / "contract.json").write_text(json.dumps(source), encoding="utf-8")
            kwargs = dict(item_id="I-01", field="title", value="Clearer title", message_id="revision-1",
                          actor="human", approved_at="2026-09-06T15:00:00+09:00", risk="low")
            classify = core._classify_start_root
            calls = 0
            def amend_during_start(*args, **options):
                nonlocal calls
                calls += 1
                classified = classify(*args, **options)
                if calls == 2:
                    raced = core.amend_work(root, source, **kwargs)
                    self.assertEqual(raced["status"], "precondition_failed", raced)
                return classified
            with mock.patch.object(core, "_classify_start_root", side_effect=amend_during_start):
                started = core.start_work(root, source["work_id"], "amend", source)
            self.assertEqual(started["status"], "started", started)
            before = (work / "work.json").read_bytes()
            amended = core.amend_work(root, source, **kwargs)
            self.assertEqual(amended["status"], "applied", amended)
            saved = json.loads((work / "contract.json").read_text(encoding="utf-8"))
            resumed = core.start_work(root, source["work_id"], "amend", saved)
            self.assertEqual(resumed["status"], "already_started", resumed)
            manifest = json.loads((work / "work.json").read_text(encoding="utf-8"))
            for field in ("source_commit", "dirty_baseline", "base_branch", "created_at"):
                self.assertEqual(manifest[field], json.loads(before)[field])
            self.assertEqual(core.amend_work(root, source, **kwargs)["status"], "invalid_work")
            originals = {name: (work / name).read_bytes() for name in ("contract.json", "work.json")}
            write = core._durable_write_bytes
            failed = False
            def fail_manifest(path, content):
                nonlocal failed
                if path == work / "work.json" and not failed:
                    failed = True
                    raise OSError("interrupted amendment")
                return write(path, content)
            with mock.patch.object(core, "_durable_write_bytes", side_effect=fail_manifest):
                outcome = core.amend_work(root, saved, **dict(kwargs, value="Another title"))
            self.assertEqual(outcome["status"], "rolled_back", outcome)
            for name, content in originals.items():
                self.assertEqual((work / name).read_bytes(), content)
            self.assertEqual((root / "user.txt").read_text(encoding="utf-8"), "preserve user edit\n")
            impact = core.select_impacted_checks(["user.txt"], v3_project(), logic_impact={
                "scope": "none", "changed_logic": [], "affected_behaviors": [], "tests": [],
                "reason": "Only the user's existing text edit is present; no behavior changed.",
            })
            result = {"items": [{"id": item["id"], "checks": [
                {"check_id": check["id"], "status": "passed"} for check in item["tests"]
            ], "criteria": [{"criterion_id": done["id"], "criterion": done["criterion"],
                             "status": "satisfied", "evidence": "fixture check"} for done in item["done"]]
            } for item in saved["items"]]}
            evaluate = core.evaluate_result
            def amend_during_close(*args):
                evaluated = evaluate(*args)
                raced = core.amend_work(root, saved, **dict(kwargs, value="Raced title"))
                self.assertEqual(raced["status"], "precondition_failed", raced)
                return evaluated
            with mock.patch.object(core, "evaluate_result", side_effect=amend_during_close):
                closed = core.close_work(root, source["work_id"], contract=saved, result=result, impact=impact,
                                         completed_at="2026-09-06T16:00:00+09:00", completed_days=30, trash_days=7)
            self.assertEqual(closed["status"], "completed", closed)

    def test_document_review_needs_no_artificial_tests_but_still_needs_done_evidence(self):
        core = load_core()
        source = contract()
        for item in source["items"]:
            item["tests"] = []
        self.assertEqual(core.validate_contract_v3(source), [])
        impact = core.select_impacted_checks(["docs/guide.md"], v3_project(), logic_impact={
            "changed_logic": [], "affected_behaviors": [], "scope": "none",
            "reason": "Only explanatory wording changed; the affected instructions were reviewed.", "tests": [],
        })
        self.assertEqual(impact["status"], "selected", impact)
        self.assertFalse(impact["full_required"])
        result = {"items": [{"id": item["id"], "checks": [], "criteria": [
            {"criterion_id": done["id"], "criterion": done["criterion"], "status": "satisfied",
             "evidence": "Reviewed the affected instructions and references."} for done in item["done"]
        ]} for item in source["items"]]}
        self.assertEqual(core.evaluate_result(source, result, impact)["status"], "complete")
        result["items"][0]["criteria"][0]["evidence"] = ""
        self.assertEqual(core.evaluate_result(source, result, impact)["status"], "incomplete")
