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
    def test_v2_project_preview_is_deterministic_and_keeps_v2_active(self) -> None:
        core = load_core()
        legacy = {
            "version": 2,
            "project": {"name": "brownfield", "classification": "partial"},
            "work": {"root": ".work", "retention_days": 90, "trash_grace_days": 30},
            "verification": {"full_suite_runs_per_goal": 1},
        }

        first = core.preview_project_v3(legacy)
        second = core.preview_project_v3(legacy)

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], 3)
        self.assertEqual(first["harness"]["active_cohort"], "v2")
        self.assertEqual(first["harness"]["runtime_version"], 2)
        self.assertIn(3, first["harness"]["dormant_cohorts"])
        self.assertEqual(first["work"]["retention"]["completed_days"], 90)
        self.assertEqual(first["work"]["retention"]["trash_days"], 30)

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
                "tests": ["The output is observable"], "done": ["The relevant check passes"],
                "depends_on": [], "non_goals": [], "decision": {"state": "resolved"},
                "material_risks": [], "priority": "core",
            }],
        }
        self.assertEqual(core.validate_contract_v3(contract), [])
        broken = json.loads(json.dumps(contract))
        del broken["items"][0]["done"]
        self.assertIn("item:I-01:missing:done", core.validate_contract_v3(broken))

    def test_approval_bundle_binds_contract_review_and_visible_item_ids(self) -> None:
        core = load_core()
        contract = {"schema_version": 3, "work_id": "W-1", "items": [{"id": "I-01"}, {"id": "I-02"}]}
        bundle = core.build_approval_bundle(
            contract, "<html lang='ko'>review</html>", utterance="승인합니다",
            actor="human", approved_at="2026-08-02T12:00:00+09:00",
        )
        self.assertEqual(bundle["item_ids"], ["I-01", "I-02"])
        self.assertTrue(bundle["contract_digest"].startswith("sha256:"))
        self.assertTrue(bundle["review_digest"].startswith("sha256:"))
        changed = dict(contract, work_id="W-2")
        self.assertFalse(core.approval_bundle_matches(bundle, changed, "<html lang='ko'>review</html>"))

    def test_unsupported_or_mixed_cohort_fails_closed(self) -> None:
        core = load_core()
        compatible = {"project": [2, 3], "design": [2, 3], "execute": [2, 3], "close": [2, 3], "maintain": [2, 3]}
        self.assertEqual(core.validate_cohort(2, compatible), [])
        mixed = dict(compatible, close=[3])
        self.assertIn("mixed_cohort:close:2", core.validate_cohort(2, mixed))
        self.assertIn("unsupported_active_cohort:4", core.validate_cohort(4, compatible))

    def test_versioned_schema_and_active_policy_assets_exist(self) -> None:
        for name in ("project.schema.json", "work.schema.json", "contract.schema.json"):
            payload = json.loads((ROOT / "authoring" / "schemas" / "v3" / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
        for relative in (
            "authoring/templates/project/AGENTS.md", "authoring/templates/project/CLAUDE.md", "authoring/templates/project/project.yaml",
            "authoring/references/documentation-policy.md", "authoring/references/testing-policy.md",
            "authoring/references/human-readability-policy.md", "authoring/references/goal-execution-policy.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)
        for skill in ("setup-agent-harness", "design-goal", "execute-codex-goal", "close-goal", "maintain-agent-harness"):
            self.assertTrue((ROOT / "skills" / skill / "scripts" / "core_harness.py").is_file(), skill)

    def test_json_schemas_close_normative_objects_and_require_command_contract(self) -> None:
        project = json.loads((ROOT / "authoring" / "schemas" / "v3" / "project.schema.json").read_text(encoding="utf-8"))
        for section in ("harness", "paths", "impact", "commands", "documents", "work", "git", "baseline"):
            self.assertFalse(project["properties"][section]["additionalProperties"], section)
        self.assertEqual(set(project["properties"]["commands"]["required"]), {"targeted", "feature", "lint", "type", "build", "full", "live", "eval"})
        descriptor = project["$defs"]["command"]
        self.assertFalse(descriptor["additionalProperties"])
        self.assertEqual(set(descriptor["required"]), {"argv", "working_directory", "platform", "runtime", "env_keys", "capability"})
        contract_schema = json.loads((ROOT / "authoring" / "schemas" / "v3" / "contract.schema.json").read_text(encoding="utf-8"))
        item = contract_schema["$defs"]["item"]
        self.assertFalse(contract_schema["$defs"]["term"]["additionalProperties"])
        self.assertFalse(contract_schema["$defs"]["decision"]["additionalProperties"])
        self.assertFalse(contract_schema["$defs"]["approval"]["additionalProperties"])
        self.assertFalse(contract_schema["$defs"]["amendment"]["additionalProperties"])
        for field in ("terms", "tests", "done"):
            self.assertIn("items", item["properties"][field], field)
        for field in ("material_risks", "non_goals"):
            self.assertEqual(item["properties"][field]["$ref"], "#/$defs/stringList")
        self.assertEqual(item["properties"]["decision"]["$ref"], "#/$defs/decision")


if __name__ == "__main__":
    unittest.main()
