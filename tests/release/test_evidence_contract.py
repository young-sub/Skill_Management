from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_evidence.py"


class EvidenceContractTests(unittest.TestCase):
    def _write_fixture(
        self,
        root: Path,
        *,
        evidence_commit: str = "a" * 40,
        evidence_tree: str = "b" * 40,
        dirty: bool = False,
        local_kind: str = "local_source_install_refresh",
    ) -> None:
        distribution = root / "distribution/evidence"
        distribution.mkdir(parents=True)
        pilots = root / "docs/pilots"
        pilots.mkdir(parents=True)
        common = {
            "schema_version": 1,
            "generated_at": "2026-07-20T00:00:00+00:00",
            "repository": "fixture",
            "git_commit": evidence_commit,
            "git_tree": evidence_tree,
            "git_dirty": dirty,
            "dirty_paths": ["dirty.txt"] if dirty else [],
            "branch": "develop",
            "command": ["fixture", "verify"],
            "cwd": "<repository-root>",
            "tool_versions": {"python": "3.12"},
            "source_type": "local_checkout",
            "source_package": "<repository-root>",
            "providers": [],
            "public_skill_count": 1,
            "catalog_sha256": "c" * 64,
            "resource_manifest_sha256": "d" * 64,
            "result": "passed",
            "unverified_checks": [],
        }
        (pilots / "harness-v2-pilots.json").write_text(
            json.dumps({"schema_version": 1, "result": "passed", "evidence": common | {"evidence_kind": "pilot_execution"}}),
            encoding="utf-8",
        )
        (distribution / "local.json").write_text(
            json.dumps(common | {"schema_version": 2, "evidence_kind": local_kind}),
            encoding="utf-8",
        )
        (root / "distribution/release-candidate.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "source_revision": {"git_commit": "a" * 40, "git_tree": "b" * 40},
                    "evidence": {
                        "pilot_execution": {
                            "status": "passed",
                            "path": "../docs/pilots/harness-v2-pilots.json",
                            "evidence_kind": "pilot_execution",
                        },
                        "local_source_install_refresh": {
                            "status": "passed",
                            "path": "evidence/local.json",
                            "evidence_kind": "local_source_install_refresh",
                        },
                        "remote_github_update": {
                            "status": "not_verified",
                            "path": "evidence/remote.json",
                            "evidence_kind": "remote_github_update",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

    def _validate(self, root: Path) -> tuple[int, dict[str, object]]:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--repository-root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_matching_revision_bound_local_and_pilot_evidence_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_fixture(root)

            code, payload = self._validate(root)

            self.assertEqual(code, 0, payload)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["findings"], [])

    def test_stale_or_dirty_passed_evidence_fails(self) -> None:
        for kwargs, expected in (
            ({"evidence_commit": "c" * 40}, "stale_evidence"),
            ({"evidence_tree": "d" * 40}, "stale_evidence"),
            ({"dirty": True}, "dirty_evidence"),
        ):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                self._write_fixture(root, **kwargs)

                code, payload = self._validate(root)

                self.assertEqual(code, 1)
                self.assertTrue(any(item["kind"] == expected for item in payload["findings"]))

    def test_local_evidence_cannot_be_labeled_as_remote_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_fixture(root, local_kind="remote_github_update")

            code, payload = self._validate(root)

            self.assertEqual(code, 1)
            self.assertTrue(any(item["kind"] == "evidence_kind_mismatch" for item in payload["findings"]))
            candidate = json.loads((root / "distribution/release-candidate.json").read_text())
            self.assertEqual(candidate["evidence"]["remote_github_update"]["status"], "not_verified")

    def test_incomplete_passed_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_fixture(root)
            evidence_path = root / "distribution/evidence/local.json"
            evidence = json.loads(evidence_path.read_text())
            evidence.pop("command")
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            code, payload = self._validate(root)

            self.assertEqual(code, 1)
            self.assertTrue(any(item["kind"] == "incomplete_evidence" for item in payload["findings"]))


if __name__ == "__main__":
    unittest.main()
