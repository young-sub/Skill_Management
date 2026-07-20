# Generated file. Do not edit directly.
# Source: authoring/scripts/close_goal.py
# Source-SHA256: 953851974ce86f18b1d6c0a5af6d8e52db2d73d36bb37edb73f17556833cb356

#!/usr/bin/env python3
"""Close an eligible Harness work item and archive it without deletion."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

from render_completion_review import render_review, template_path


TEXT_DOCUMENT_SUFFIXES = {".md", ".txt", ".rst", ".adoc", ".html", ".json", ".yaml", ".yml"}
REQUIRED_CHECKS = {"targeted", "feature", "fast", "full"}


def _load_engine() -> Any:
    path = Path(__file__).with_name("contract_engine.py")
    spec = importlib.util.spec_from_file_location("harness_close_contract_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("contract_engine_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENGINE = _load_engine()


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_object:{path}")
    return value


def _metadata(source: str) -> dict[str, str]:
    if not source.startswith("---\n") or "\n---\n" not in source[4:]:
        return {}
    header = source.split("\n---\n", 1)[0].splitlines()[1:]
    return {key.strip(): value.strip() for line in header if ":" in line for key, value in [line.split(":", 1)]}


def _contract_document(contract_root: Path) -> tuple[Path, str]:
    candidates = [path for name in ("GOAL.md", "SPEC.md") if (path := contract_root / name).is_file()]
    if len(candidates) != 1:
        raise ValueError("exactly_one_contract_document_required:GOAL.md|SPEC.md")
    path = candidates[0]
    return path, path.read_text(encoding="utf-8")


def _objective(source: str, document_name: str) -> str:
    preferred = ("Objective",) if document_name == "GOAL.md" else ("Problem", "User Value", "Objective")
    for heading in preferred:
        match = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n+(.+?)(?=\n## |\Z)", source)
        if match and match.group(1).strip():
            return match.group(1).strip()
    match = re.search(r"(?ms)^## [^\n]+\s*\n+(.+?)(?=\n## |\Z)", source)
    return match.group(1).strip() if match else "Completed approved work."


def _tracked_work_references(source_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=source_root, capture_output=True, check=False
    )
    if result.returncode:
        return ["git_ls_files_failed"]
    errors: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", errors="surrogateescape")
        path = source_root / relative
        if path.suffix.lower() not in TEXT_DOCUMENT_SUFFIXES or not path.is_file():
            continue
        try:
            if ".work/" in path.read_text(encoding="utf-8").replace("\\", "/"):
                errors.append(f"durable_work_reference:{Path(relative).as_posix()}")
        except UnicodeError:
            continue
    return errors


def _checks(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("checks_must_be_list")
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("check_must_be_object")
        kind = str(item.get("kind", "Unknown"))
        status = str(item.get("status", "unknown")).lower().replace("-", "_")
        if kind.lower() in {"live", "eval"} and status in {"not_run", "unrun", "skipped", "skip"}:
            status = "unverified"
        normalized.append({**{str(k): str(v) for k, v in item.items()}, "kind": kind, "status": status})
    return normalized


def _verification_errors(checks: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    by_kind: dict[str, list[dict[str, str]]] = {}
    for check in checks:
        by_kind.setdefault(check["kind"].lower(), []).append(check)
    for kind in sorted(REQUIRED_CHECKS):
        entries = by_kind.get(kind, [])
        if len(entries) != 1:
            errors.append(f"required_check_count:{kind}:{len(entries)}")
            continue
        check = entries[0]
        if check.get("status") != "passed":
            errors.append(f"required_check_not_passed:{kind}")
        if not check.get("command", "").strip():
            errors.append(f"required_check_missing_command:{kind}")
        if not check.get("evidence", "").strip():
            errors.append(f"required_check_missing_evidence:{kind}")
        if check.get("returncode") != "0":
            errors.append(f"required_check_returncode:{kind}")
    for kind in ("live", "eval"):
        for check in by_kind.get(kind, []):
            if check.get("status") not in {"passed", "failed", "unverified"}:
                errors.append(f"invalid_optional_check_status:{kind}")
    return errors


def _completion_errors(contract_root: Path, source_root: Path) -> tuple[list[str], list[Any], dict[str, Any]]:
    payload, _, documents = ENGINE.validate_contract(contract_root, source_root / ".work")
    errors = list(payload.get("errors", []))
    if payload.get("approval_status") != "approved":
        errors.append("approval_required")
    if not payload.get("executable"):
        errors.append("contract_not_executable")
    plans = [document for document in documents if document.kind == "plan"]
    if plans:
        errors.extend(
            f"plan_not_completed:{document.metadata.get('plan_id', 'missing')}"
            for document in plans if document.metadata.get("status") != "completed"
        )
    elif any(document.kind == "spec" for document in documents):
        state_path = contract_root / "runtime-state.json"
        try:
            state = _object(state_path)
            if state != {"SPEC": "completed"}:
                errors.append("spec_not_completed")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            errors.append("spec_not_completed")
    return errors, documents, payload


def _handoff_target(source_root: Path) -> str:
    path = source_root / ".harness" / "project.yaml"
    if not path.is_file():
        return "none"
    in_handoff = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "handoff:":
            in_handoff = True
        elif in_handoff and re.match(r"^\s+target\s*:", line):
            return line.split(":", 1)[1].strip().strip("'\"")
        elif line and not line[0].isspace():
            in_handoff = False
    return "none"


def _result_text(work_id: str, objective: str, findings: list[dict[str, Any]], checks: list[dict[str, str]]) -> str:
    finding_lines = [f"- {item.get('severity', 'Unknown')}: {item.get('title', item.get('message', ''))}" for item in findings]
    verification_lines = [f"- {item['kind']}: {item['status']}" for item in checks]
    return f"""---
work_id: {work_id}
kind: result
---

## Outcome

{objective}

## Changes

Approved work completed and reviewed across Spec, Standards, Maintainability, Architecture, and Diagnostics.

## Verification

{chr(10).join(verification_lines) if verification_lines else '- No checks recorded.'}

## Findings

{chr(10).join(finding_lines) if finding_lines else '- None'}

## Evidence

- `artifacts/completion-review.html`

## Remaining Risks

Unverified checks and non-High findings remain visible above.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--current-month", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.current_month):
            raise ValueError("invalid_current_month")
        contract_root, source_root = args.contract_root.resolve(), args.source_root.resolve()
        active_root = (source_root / ".work" / "active").resolve()
        if contract_root.parent != active_root:
            raise ValueError("contract_root_must_be_direct_active_work")
        contract_path, contract = _contract_document(contract_root)
        contract_errors, _, contract_payload = _completion_errors(contract_root, source_root)
        work_id = str(contract_payload.get("work_id") or _metadata(contract).get("work_id", contract_root.name))
        if work_id != contract_root.name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", work_id):
            raise ValueError("invalid_work_id")
        findings = _object(args.findings).get("findings", [])
        if not isinstance(findings, list) or any(not isinstance(item, dict) for item in findings):
            raise ValueError("findings_must_be_list")
        checks = _checks(_object(args.verification).get("checks", []))
        errors = contract_errors + _verification_errors(checks) + _tracked_work_references(source_root)
        if any(str(item.get("severity", "")).lower() == "high" for item in findings):
            errors.append("high_finding")
        archive = source_root / ".work" / "archive" / args.current_month / work_id
        if archive.exists():
            errors.append("archive_destination_exists")
        if errors:
            print(json.dumps({"status": "blocked", "errors": sorted(set(errors))}, sort_keys=True))
            return 3

        objective = _objective(contract, contract_path.name)
        result_text = _result_text(work_id, objective, findings, checks)
        result_path = contract_root / "RESULT.md"
        result_path.write_text(result_text, encoding="utf-8", newline="\n")
        template = template_path()
        review_path = contract_root / "artifacts" / "completion-review.html"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(render_review(
            work_id=work_id, objective=objective, result_markdown=result_text,
            findings=findings, checks=checks, template=template,
        ), encoding="utf-8", newline="\n")
        if _handoff_target(source_root) in {"local", "both"}:
            handoff = f"""---
work_id: {work_id}
kind: handoff
---

## Outcome

{objective}

## Verification

{chr(10).join(f'- {item["kind"]}: {item["status"]}' for item in checks)}

## Evidence

- `RESULT.md`
- `artifacts/completion-review.html`

## Remaining Work

Review unverified checks and non-High findings, if any.
"""
            (contract_root / "HANDOFF.md").write_text(handoff, encoding="utf-8", newline="\n")
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(contract_root), str(archive))
        print(json.dumps({"status": "complete", "work_id": work_id, "archive": str(archive)}, sort_keys=True))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"status": "rejected", "errors": [str(error)]}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
