"""Validate release-candidate evidence provenance and source revision binding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


REVISION = re.compile(r"^[0-9a-f]{40,64}$")
EVIDENCE_KINDS = {
    "pilot_execution",
    "local_source_install_refresh",
    "remote_github_update",
}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _finding(kind: str, evidence_key: str, message: str) -> dict[str, str]:
    return {"kind": kind, "evidence_key": evidence_key, "message": message}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    candidate_path = root / "distribution" / "release-candidate.json"
    findings: list[dict[str, str]] = []
    try:
        candidate = _load_json(candidate_path)
    except (OSError, json.JSONDecodeError) as error:
        return {
            "schema_version": 1,
            "status": "failed",
            "findings": [_finding("invalid_candidate", "release-candidate", str(error))],
        }
    if candidate.get("schema_version") != 2:
        findings.append(_finding("unsupported_candidate_schema", "release-candidate", "schema_version must be 2"))
    revision = candidate.get("source_revision", {})
    expected_commit = revision.get("git_commit")
    expected_tree = revision.get("git_tree")
    if not isinstance(expected_commit, str) or not REVISION.fullmatch(expected_commit):
        findings.append(_finding("invalid_source_revision", "release-candidate", "git_commit is invalid"))
    if not isinstance(expected_tree, str) or not REVISION.fullmatch(expected_tree):
        findings.append(_finding("invalid_source_revision", "release-candidate", "git_tree is invalid"))
    evidence_contract = candidate.get("evidence")
    if not isinstance(evidence_contract, dict):
        evidence_contract = {}
        findings.append(_finding("invalid_evidence_contract", "release-candidate", "evidence must be an object"))
    observed_kinds: set[str] = set()
    for key, contract in sorted(evidence_contract.items()):
        if not isinstance(contract, dict):
            findings.append(_finding("invalid_evidence_contract", key, "entry must be an object"))
            continue
        expected_kind = contract.get("evidence_kind")
        if expected_kind != key or expected_kind not in EVIDENCE_KINDS:
            findings.append(_finding("evidence_kind_mismatch", key, "contract key and evidence_kind differ"))
        if expected_kind in observed_kinds:
            findings.append(_finding("evidence_kind_mismatch", key, "evidence kind is duplicated"))
        observed_kinds.add(str(expected_kind))
        status = contract.get("status")
        if status == "not_verified":
            continue
        if status != "passed":
            findings.append(_finding("invalid_evidence_status", key, f"unsupported status: {status}"))
            continue
        relative_path = contract.get("path")
        if not isinstance(relative_path, str):
            findings.append(_finding("missing_evidence", key, "passed proof lacks a path"))
            continue
        evidence_path = (candidate_path.parent / relative_path).resolve(strict=False)
        if not _inside(evidence_path, root):
            findings.append(_finding("evidence_path_escape", key, relative_path))
            continue
        try:
            payload = _load_json(evidence_path)
        except (OSError, json.JSONDecodeError) as error:
            findings.append(_finding("missing_evidence", key, str(error)))
            continue
        record = payload.get("evidence") if key == "pilot_execution" else payload
        if not isinstance(record, dict):
            findings.append(_finding("invalid_evidence", key, "evidence record must be an object"))
            continue
        if record.get("evidence_kind") != expected_kind:
            findings.append(
                _finding(
                    "evidence_kind_mismatch",
                    key,
                    f"record kind {record.get('evidence_kind')!r} does not match {expected_kind!r}",
                )
            )
        if record.get("git_commit") != expected_commit or record.get("git_tree") != expected_tree:
            findings.append(_finding("stale_evidence", key, "commit/tree differs from candidate source revision"))
        if record.get("git_dirty") is not False or record.get("dirty_paths") not in ([], None):
            findings.append(_finding("dirty_evidence", key, "passed release evidence must come from a clean source tree"))
        if record.get("result") != "passed":
            findings.append(_finding("invalid_evidence_result", key, "passed contract points to non-passing evidence"))
    return {
        "schema_version": 1,
        "status": "passed" if not findings else "failed",
        "source_revision": {"git_commit": expected_commit, "git_tree": expected_tree},
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args()
    payload = validate(args.repository_root)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
