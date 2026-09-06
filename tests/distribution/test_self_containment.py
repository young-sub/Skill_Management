from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNER = REPO_ROOT / "scripts" / "validate_self_containment.py"


def scan(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), "--repository-root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


class SelfContainmentTests(unittest.TestCase):
    def _payload(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertTrue(result.stdout.strip(), result.stderr)
        return json.loads(result.stdout)

    def _skill(self, root: Path, name: str = "fixture-skill") -> Path:
        skill = root / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: fixture\n---\n",
            encoding="utf-8",
        )
        return skill

    def test_reports_structured_rule_ids_for_adversarial_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self._skill(root)
            self._skill(root, "other-skill")
            (root / "README.md").write_text("# Root\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[escape](../../outside.md)\n"
                + "[root](../../README.md)\n"
                + "[cross](../other-skill/SKILL.md)\n"
                + "[missing](references/missing.md)\n"
                + "Windows path: `C:\\Users\\fixture\\secret.md`\n"
                + "URI: `file:///tmp/secret.md`\n",
                encoding="utf-8",
            )

            result = scan(root)

            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = self._payload(result)
            rule_ids = {item["rule_id"] for item in payload["findings"]}
            self.assertTrue(
                {
                    "SC_RELATIVE_ESCAPE",
                    "SC_ABSOLUTE_PATH",
                    "SC_FILE_URI",
                    "SC_REPO_ROOT_REFERENCE",
                    "SC_CROSS_SKILL_REFERENCE",
                    "SC_MISSING_RESOURCE",
                }
                <= rule_ids
            )
            required = {"skill", "source_path", "locator", "normalized_target", "severity", "evidence"}
            self.assertTrue(all(required <= finding.keys() for finding in payload["findings"]))

    def test_allows_existing_in_skill_resources_and_exact_governed_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self._skill(root)
            (skill / "references").mkdir()
            (skill / "references/local.md").write_text("# Local\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[local](references/local.md)\n"
                + "Windows example: `C:\\documented\\example.md`\n",
                encoding="utf-8",
            )
            distribution = root / "distribution"
            distribution.mkdir()
            (distribution / "self-containment-allowlist.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "entries": [
                            {
                                "rule_id": "SC_ABSOLUTE_PATH",
                                "skill": "fixture-skill",
                                "source_path": "SKILL.md",
                                "normalized_target": "C:/documented/example.md",
                                "reason": "documentation-only platform example",
                                "owner": "fixture-owner",
                                "review_after": "2099-01-01",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = scan(root)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = self._payload(result)
            self.assertEqual(payload["findings"], [])
            self.assertEqual(len(payload["allowlisted_findings"]), 1)

    def test_ignores_paths_inside_fenced_code_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self._skill(root)
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n```js\nfetch('/api/example')\nconst local = 'file:///tmp/example'\n```\n",
                encoding="utf-8",
            )

            result = scan(root)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(self._payload(result)["findings"], [])

    def test_resource_map_missing_target_is_a_missing_resource(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._skill(root)
            authoring = root / "authoring"
            authoring.mkdir()
            (authoring / "source.md").write_text("source\n", encoding="utf-8")
            (authoring / "resource-map.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "resources": [
                            {"source": "source.md", "targets": ["fixture-skill/references/generated.md"]}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = scan(root)

            payload = self._payload(result)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertTrue(
                any(
                    item["rule_id"] == "SC_MISSING_RESOURCE"
                    and item["normalized_target"] == "fixture-skill/references/generated.md"
                    for item in payload["findings"]
                )
            )

    def test_reparse_escape_is_fail_closed_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self._skill(root)
            external = root / "external"
            external.mkdir()
            (external / "secret.md").write_text("secret\n", encoding="utf-8")
            try:
                os.symlink(external, skill / "linked", target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")

            result = scan(root)

            payload = self._payload(result)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertTrue(any(item["rule_id"] == "SC_REPARSE_ESCAPE" for item in payload["findings"]))

    def test_malformed_manifests_and_missing_skills_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "authoring").mkdir()
            (root / "authoring/resource-map.json").write_text("{broken", encoding="utf-8")

            result = scan(root)

            self.assertEqual(result.returncode, 1)
            payload = self._payload(result)
            evidence = " ".join(item["evidence"] for item in payload["findings"])
            self.assertIn("skills directory", evidence)
            self.assertIn("resource-map", evidence)

    def test_structured_unix_root_and_cross_skill_paths_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self._skill(root)
            self._skill(root, "other-skill")
            (skill / "config.json").write_text(
                json.dumps(
                    {
                        "absolute": "/tmp/private/config.json",
                        "repo": "authoring/references/policy.md",
                        "cross": "skills/other-skill/SKILL.md",
                    }
                ),
                encoding="utf-8",
            )

            result = scan(root)

            self.assertEqual(result.returncode, 1)
            rule_ids = {item["rule_id"] for item in self._payload(result)["findings"]}
            self.assertIn("SC_ABSOLUTE_PATH", rule_ids)
            self.assertIn("SC_REPO_ROOT_REFERENCE", rule_ids)
            self.assertIn("SC_CROSS_SKILL_REFERENCE", rule_ids)

    def test_expired_allowlist_entry_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self._skill(root)
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\nExample: `C:\\expired\\example.md`\n",
                encoding="utf-8",
            )
            (root / "distribution").mkdir()
            (root / "distribution/self-containment-allowlist.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "entries": [{
                            "rule_id": "SC_ABSOLUTE_PATH",
                            "skill": "fixture-skill",
                            "source_path": "SKILL.md",
                            "normalized_target": "C:/expired/example.md",
                            "reason": "expired fixture",
                            "owner": "fixture-owner",
                            "review_after": "2000-01-01",
                        }],
                    }
                ),
                encoding="utf-8",
            )

            result = scan(root)

            self.assertEqual(result.returncode, 1)
            self.assertTrue(self._payload(result)["allowlist_errors"])


if __name__ == "__main__":
    unittest.main()
