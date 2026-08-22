import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "authoring" / "scripts" / "core_harness.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_harness", CORE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class CoreFirstSchemaTests(unittest.TestCase):
    def test_current_project_config_rejects_missing_and_unknown_fields(self) -> None:
        core = load_core()

        normalized = core.normalize_project_config({"schema_version": 3, "unexpected": True})

        self.assertEqual(normalized["status"], "invalid", normalized)
        self.assertIn("project_config:unknown_field:unexpected", normalized["errors"])
        self.assertIn("project_config:missing:project", normalized["errors"])

    def test_legacy_project_preview_is_deterministic_and_has_no_runtime_version_branding(self) -> None:
        core = load_core()
        legacy = {
            "version": 2,
            "project": {"name": "brownfield", "classification": "partial"},
            "work": {"root": ".work", "retention_days": 90, "trash_grace_days": 30},
            "verification": {"full_suite_runs_per_goal": 1},
        }

        first = core.preview_project_config(legacy)
        second = core.preview_project_config(legacy)

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], 3)
        self.assertNotIn("harness", first)
        self.assertNotIn("migration", first)
        self.assertEqual(first["work"]["retention"]["completed_days"], 90)
        self.assertEqual(first["work"]["retention"]["trash_days"], 30)
        self.assertEqual(legacy["version"], 2)

    def test_project_normalization_is_read_only_and_rejects_unknown_legacy_matrices(self) -> None:
        core = load_core()
        old = json.loads(
            (ROOT / "authoring" / "templates" / "project" / "project.yaml").read_text(encoding="utf-8")
        )
        old["project"] = {"name": "sample", "classification": "mapped"}
        old["harness"] = {
            "active_cohort": "v3", "contract_version": 3, "runtime_version": 3,
            "dormant_cohorts": [],
            "components": {
                name: {"supports": [3]}
                for name in ("project", "design", "execute", "close", "maintain", "diagnose")
            },
        }
        original = json.loads(json.dumps(old))

        normalized = core.normalize_project_config(old)

        self.assertEqual(normalized["status"], "migration_required")
        self.assertEqual(old, original)
        self.assertNotIn("harness", normalized["project"])
        self.assertEqual(normalized["project"]["schema_version"], 3)
        current = core.normalize_project_config(normalized["project"])
        self.assertEqual(current["status"], "current")
        self.assertEqual(current["project"], normalized["project"])

        mixed = json.loads(json.dumps(old))
        mixed["harness"]["components"]["close"] = {"supports": [2]}
        rejected = core.normalize_project_config(mixed)
        self.assertEqual(rejected["status"], "invalid")
        self.assertIn("unknown_legacy_harness_configuration", rejected["errors"])

    def test_item_contract_requires_reviewable_behavior_fields(self) -> None:
        core = load_core()
        contract = {
            "schema_version": 3,
            "work_id": "W-20260802-001",
            "goal": "Deliver observable behavior",
            "scope": "One capability",
            "non_goals": ["Unrelated cleanup"],
            "items": [{
                "id": "I-01", "title": "Core behavior", "behavior_type": "tool",
                "what": "Implement the capability", "steps": ["input", "process", "output"],
                "terms": [{"term": "Impact rule", "explanation": "A mapping from change to checks."}],
                "tests": [{"id": "T-01", "target": "output", "method": "run check", "expected": "observable", "selector": "tests.output"}],
                "done": [{"id": "D-01", "criterion": "The relevant check passes"}],
                "depends_on": [], "non_goals": [], "decision": {"state": "resolved"},
                "material_risks": [], "priority": "core",
            }, {
                "id": "I-02", "title": "Result behavior", "behavior_type": "tool",
                "what": "Report the result", "steps": ["read", "report"], "terms": [],
                "tests": [{"id": "T-01", "target": "result", "method": "run check", "expected": "reported", "selector": "tests.result"}],
                "done": [{"id": "D-01", "criterion": "The result is reported"}],
                "depends_on": ["I-01"], "non_goals": [], "decision": {"state": "resolved"},
                "material_risks": [], "priority": "core",
            }],
        }
        self.assertEqual(core.validate_contract_v3(contract), [])
        broken = json.loads(json.dumps(contract))
        del broken["items"][0]["done"]
        self.assertIn("item:I-01:missing:done", core.validate_contract_v3(broken))
        one_item = json.loads(json.dumps(contract))
        one_item["items"] = one_item["items"][:1]
        self.assertEqual(core.validate_contract_v3(one_item), [])

    def test_runtime_validator_rejects_schema_invalid_item_values_and_dependency_cycles(self) -> None:
        core = load_core()
        source = {
            "schema_version": 3, "work_id": "W-valid", "goal": "deliver", "scope": "feature",
            "non_goals": [], "items": [],
        }
        for item_id, dependency in (("I-01", "I-02"), ("I-02", "I-01")):
            source["items"].append({
                "id": item_id, "title": item_id, "behavior_type": "tool", "what": "deliver",
                "steps": ["input", "output"], "terms": [],
                "tests": [{"id": "T-01", "target": "output", "method": "run", "expected": "pass", "selector": ""}],
                "done": [{"id": "D-01", "criterion": "delivered"}],
                "depends_on": [dependency], "non_goals": [], "decision": {"state": "resolved"},
                "material_risks": [], "priority": "core",
            })
        self.assertIn("items:dependency_cycle", core.validate_contract_v3(source))

        invalid = json.loads(json.dumps(source))
        invalid["items"][0].update({
            "behavior_type": "nonsense", "priority": "urgent", "terms": ["not-an-object"],
            "non_goals": [42], "material_risks": ["보안 변경"],
        })
        errors = core.validate_contract_v3(invalid)
        for expected in (
            "item:I-01:invalid_behavior_type", "item:I-01:invalid_priority",
            "item:I-01:term:0:expected_object", "item:I-01:non_goals:0:expected_string",
            "item:I-01:invalid_material_risk:보안 변경",
        ):
            self.assertIn(expected, errors)

    def test_authorization_record_binds_contract_without_review_digest(self) -> None:
        core = load_core()
        contract = {"schema_version": 3, "work_id": "W-1", "items": [{"id": "I-01"}, {"id": "I-02"}]}
        authorization = core._authorization_record(
            contract, mode="default", actor="policy",
            authorized_at="2026-08-02T12:00:00+09:00",
        )
        self.assertEqual(authorization["item_ids"], ["I-01", "I-02"])
        self.assertTrue(authorization["contract_digest"].startswith("sha256:"))
        self.assertNotIn("review_digest", authorization)

    def test_versioned_schema_and_active_policy_assets_exist(self) -> None:
        for name in ("project.schema.json", "work.schema.json", "contract.schema.json"):
            payload = json.loads((ROOT / "authoring" / "schemas" / "v3" / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
        for relative in (
            "authoring/templates/project/AGENTS.md", "authoring/templates/project/CLAUDE.md", "authoring/templates/project/project.yaml",
            "authoring/references/documentation-policy.md", "authoring/references/testing-policy.md",
            "authoring/references/goal-execution-policy.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)
        for skill in ("setup-agent-harness", "design-goal", "execute-codex-goal", "close-goal", "maintain-agent-harness"):
            self.assertTrue((ROOT / "skills" / skill / "scripts" / "core_harness.py").is_file(), skill)

    def test_work_schema_keeps_only_path_level_dirty_baseline_data(self) -> None:
        work = json.loads(
            (ROOT / "authoring" / "schemas" / "v3" / "work.schema.json").read_text(encoding="utf-8")
        )

        self.assertIn("dirty_baseline", work["required"])
        self.assertIn("integrity_digest", work["required"])
        self.assertIn("integrity_digest", work["properties"])
        baseline = work["properties"]["dirty_baseline"]
        self.assertEqual(set(baseline["required"]), {"base_revision", "entries"})
        self.assertFalse(baseline["additionalProperties"])
        entry = baseline["properties"]["entries"]["items"]
        self.assertEqual(
            set(entry["required"]),
            {"path", "identity", "states"},
        )
        self.assertFalse(entry["additionalProperties"])

    def test_json_schemas_close_normative_objects_and_require_command_contract(self) -> None:
        project = json.loads((ROOT / "authoring" / "schemas" / "v3" / "project.schema.json").read_text(encoding="utf-8"))
        self.assertNotIn("harness", project["required"])
        self.assertNotIn("harness", project["properties"])
        self.assertNotIn("migration", project["properties"])
        self.assertNotIn("component", project["$defs"])
        for section in ("paths", "impact", "commands", "documents", "work", "git", "baseline"):
            self.assertFalse(project["properties"][section]["additionalProperties"], section)
        self.assertEqual(set(project["properties"]["commands"]["required"]), {"targeted", "feature", "lint", "type", "build", "full", "live", "eval"})
        descriptor = project["$defs"]["command"]
        self.assertFalse(descriptor["additionalProperties"])
        self.assertEqual(set(descriptor["required"]), {"id", "argv", "working_directory", "platform", "runtime", "capability"})
        contract_schema = json.loads((ROOT / "authoring" / "schemas" / "v3" / "contract.schema.json").read_text(encoding="utf-8"))
        item = contract_schema["$defs"]["item"]
        self.assertIn("testCase", contract_schema["$defs"])
        test_case = contract_schema["$defs"]["testCase"]
        self.assertEqual(set(test_case["required"]), {"id", "target", "method", "expected", "selector"})
        self.assertFalse(test_case["additionalProperties"])
        self.assertEqual(item["properties"]["tests"]["items"]["$ref"], "#/$defs/testCase")
        self.assertFalse(contract_schema["$defs"]["term"]["additionalProperties"])
        self.assertFalse(contract_schema["$defs"]["decision"]["additionalProperties"])
        self.assertFalse(contract_schema["$defs"]["authorization"]["additionalProperties"])
        self.assertNotIn("review_digest", contract_schema["$defs"]["authorization"]["required"])
        self.assertFalse(contract_schema["$defs"]["amendment"]["additionalProperties"])
        for field in ("terms", "tests", "done"):
            self.assertIn("items", item["properties"][field], field)
        self.assertEqual(item["properties"]["non_goals"]["$ref"], "#/$defs/stringList")
        self.assertEqual(item["properties"]["material_risks"]["$ref"], "#/$defs/riskList")
        self.assertEqual(item["properties"]["decision"]["$ref"], "#/$defs/decision")


if __name__ == "__main__":
    unittest.main()
