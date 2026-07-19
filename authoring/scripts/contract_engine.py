#!/usr/bin/env python3
"""Validate and approve the generated Harness V2 Markdown contract schema."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Any


REQUIRED_SECTIONS = {
    "spec": (
        "Context",
        "Problem",
        "User Value",
        "Scope",
        "Non-Goals",
        "Constraints",
        "Acceptance Criteria",
    ),
    "goal": (
        "Objective",
        "Observable Outcomes",
        "Plans",
        "Hard Stops",
        "Verification",
        "Completion Criteria",
    ),
    "plan": ("Slice", "Outcomes", "Changes", "Tests", "Verification", "Evidence"),
    "result": ("Outcome", "Changes", "Verification", "Evidence", "Remaining Risks"),
    "blocked": ("Blocker", "Impact", "Evidence", "Attempts", "Resume Conditions"),
}

ALLOWED_FIELDS = {
    "spec": {
        "work_id",
        "kind",
        "approval.status",
        "approval.approved_at",
        "approval.approved_by",
        "approval.contract_hash",
    },
    "goal": {
        "work_id",
        "kind",
        "approval.status",
        "approval.approved_at",
        "approval.approved_by",
        "approval.contract_hash",
    },
    "plan": {"work_id", "kind", "plan_id", "status", "depends_on"},
    "result": {"work_id", "kind"},
    "blocked": {"work_id", "kind"},
}

PLAN_STATUSES = {"pending", "in_progress", "completed", "blocked"}
APPROVAL_STATUSES = {"pending", "approved"}


class Document:
    def __init__(self, path: Path, text: str, metadata: dict[str, str], body: str):
        self.path = path
        self.text = text
        self.metadata = metadata
        self.body = body
        self.kind = metadata.get("kind", "")
        self.sections = self._parse_sections(body)

    @staticmethod
    def _parse_sections(body: str) -> dict[str, str]:
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in body.splitlines():
            match = re.fullmatch(r"## ([^#].*?)\s*", line)
            if match:
                current = match.group(1)
                sections.setdefault(current, [])
            elif current is not None:
                sections[current].append(line)
        return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _normalise(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_document(path: Path) -> Document:
    text = _normalise(path.read_text(encoding="utf-8"))
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing_frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("unterminated_frontmatter") from error
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid_frontmatter_line:{line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or key in metadata:
            raise ValueError(f"invalid_frontmatter_key:{key}")
        metadata[key] = value.strip()
    body = "\n".join(lines[end + 1 :]).strip() + "\n"
    return Document(path, text, metadata, body)


def contract_paths(root: Path) -> list[Path]:
    paths = [root / "SPEC.md", root / "GOAL.md"]
    paths.extend(sorted((root / "plans").glob("*.md")) if (root / "plans").is_dir() else [])
    paths.extend(path for path in (root / "RESULT.md", root / "BLOCKED.md") if path.exists())
    return paths


def load_contract(root: Path) -> tuple[list[Document], list[str]]:
    errors: list[str] = []
    paths = contract_paths(root)
    has_spec = (root / "SPEC.md").is_file()
    has_goal = (root / "GOAL.md").is_file()
    has_plans = (root / "plans").is_dir() and bool(list((root / "plans").glob("*.md")))
    if not has_spec and not has_goal:
        errors.append("missing_contract")
    if has_spec and (has_goal or has_plans):
        errors.append("mixed_contract_shapes")
    if has_goal and not has_plans:
        errors.append("missing_plans")
    if has_plans and not has_goal:
        errors.append("missing_document:GOAL.md")
    documents: list[Document] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            documents.append(parse_document(path))
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"invalid_document:{path.name}:{error}")
    return documents, errors


def validate_documents(documents: list[Document], root: Path, work_root: Path | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    work_ids = {document.metadata.get("work_id", "") for document in documents}
    if "" in work_ids:
        errors.append("missing_work_id")
    nonempty_work_ids = work_ids - {""}
    if len(nonempty_work_ids) > 1:
        errors.append("work_id_mismatch")
    work_id = next(iter(nonempty_work_ids), "")
    plans: dict[str, Document] = {}
    dependencies: dict[str, list[str]] = {}

    approval_documents = [
        document for document in documents if "approval.status" in document.metadata
    ]
    if len(approval_documents) != 1:
        errors.append("invalid_approval_owner")

    for document in documents:
        kind = document.kind
        if kind not in REQUIRED_SECTIONS:
            errors.append(f"invalid_kind:{document.path.name}:{kind or 'missing'}")
            continue
        unexpected = sorted(set(document.metadata) - ALLOWED_FIELDS[kind])
        errors.extend(f"unexpected_field:{document.path.name}:{field}" for field in unexpected)
        for section in REQUIRED_SECTIONS[kind]:
            if section not in document.sections or not document.sections[section]:
                errors.append(f"missing_section:{document.path.name}:{section}")
        if "approval.status" in document.metadata:
            status = document.metadata.get("approval.status", "")
            if status not in APPROVAL_STATUSES:
                errors.append(f"invalid_approval_status:{status or 'missing'}")
        if kind == "plan":
            plan_id = document.metadata.get("plan_id", "")
            if not plan_id or plan_id in plans:
                errors.append(f"invalid_plan_id:{plan_id or 'missing'}")
                continue
            if document.metadata.get("status", "") not in PLAN_STATUSES:
                errors.append(f"invalid_plan_status:{plan_id}")
            try:
                parsed_dependencies = json.loads(document.metadata.get("depends_on", ""))
                if not isinstance(parsed_dependencies, list) or not all(
                    isinstance(item, str) for item in parsed_dependencies
                ):
                    raise ValueError
            except (json.JSONDecodeError, ValueError):
                errors.append(f"invalid_dependencies:{plan_id}")
                parsed_dependencies = []
            plans[plan_id] = document
            dependencies[plan_id] = parsed_dependencies

    for plan_id, required_ids in dependencies.items():
        for required_id in required_ids:
            if required_id not in plans:
                errors.append(f"missing_dependency:{plan_id}:{required_id}")
    order, cyclic = topological_order(dependencies)
    if cyclic:
        errors.append("dependency_cycle")
    if work_root is not None and work_id:
        contract_directories = set()
        for document_name in ("SPEC.md", "GOAL.md"):
            for contract_path in work_root.rglob(document_name):
                try:
                    if parse_document(contract_path).metadata.get("work_id") == work_id:
                        contract_directories.add(contract_path.parent.resolve())
                except (OSError, UnicodeError, ValueError):
                    continue
        if len(contract_directories) > 1:
            errors.append(f"duplicate_work_id:{work_id}")
    return sorted(set(errors)), order


def topological_order(dependencies: dict[str, list[str]]) -> tuple[list[str], bool]:
    indegree = {plan_id: 0 for plan_id in dependencies}
    dependents: dict[str, list[str]] = defaultdict(list)
    for plan_id, required_ids in dependencies.items():
        for required_id in required_ids:
            if required_id in indegree:
                indegree[plan_id] += 1
                dependents[required_id].append(plan_id)
    ready = sorted(plan_id for plan_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        plan_id = ready.pop(0)
        order.append(plan_id)
        for dependent in sorted(dependents[plan_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    return order, len(order) != len(indegree)


def canonical_contract(documents: list[Document]) -> dict[str, Any]:
    by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        if document.kind not in {"spec", "goal", "plan"}:
            continue
        section_names = [
            name for name in REQUIRED_SECTIONS[document.kind] if name != "Evidence"
        ]
        entry: dict[str, Any] = {
            "kind": document.kind,
            "work_id": document.metadata.get("work_id", ""),
            "sections": {name: document.sections.get(name, "") for name in section_names},
        }
        if document.kind == "plan":
            entry["plan_id"] = document.metadata.get("plan_id", "")
            entry["depends_on"] = json.loads(document.metadata.get("depends_on", "[]"))
        by_kind[document.kind].append(entry)
    return {
        "spec": sorted(by_kind["spec"], key=lambda item: item["work_id"]),
        "goal": sorted(by_kind["goal"], key=lambda item: item["work_id"]),
        "plans": sorted(by_kind["plan"], key=lambda item: item["plan_id"]),
    }


def contract_hash(documents: list[Document]) -> str:
    encoded = json.dumps(
        canonical_contract(documents), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def approval_document(documents: list[Document]) -> Document | None:
    return next(
        (document for document in documents if "approval.status" in document.metadata),
        None,
    )


def replace_approval(document: Document, values: dict[str, str]) -> None:
    lines = _normalise(document.path.read_text(encoding="utf-8")).splitlines()
    end = lines.index("---", 1)
    metadata = dict(document.metadata)
    metadata.update(values)
    ordered = [
        "work_id",
        "kind",
        "approval.status",
        "approval.approved_at",
        "approval.approved_by",
        "approval.contract_hash",
    ]
    frontmatter = ["---", *(f"{key}: {metadata.get(key, '')}" for key in ordered), "---"]
    document.path.write_text("\n".join(frontmatter + lines[end + 1 :]).rstrip() + "\n", encoding="utf-8", newline="\n")


def validate_contract(root: Path, work_root: Path | None) -> tuple[dict[str, Any], int, list[Document]]:
    documents, errors = load_contract(root)
    validation_errors, order = validate_documents(documents, root, work_root)
    errors.extend(validation_errors)
    approval = approval_document(documents)
    current_hash = contract_hash(documents) if not errors else ""
    approval_status = approval.metadata.get("approval.status", "") if approval else ""
    recorded_hash = approval.metadata.get("approval.contract_hash", "") if approval else ""
    drift = approval_status == "approved" and recorded_hash != current_hash
    if drift:
        errors.append("contract_hash_drift")
    payload = {
        "status": "valid" if not errors else "invalid",
        "work_id": approval.metadata.get("work_id", "") if approval else "",
        "approval_status": approval_status,
        "contract_hash": current_hash,
        "plan_order": order,
        "executable": approval_status == "approved" and not errors,
        "errors": sorted(set(errors)),
    }
    return payload, (4 if drift else 2 if errors else 0), documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "hash", "approve"):
        child = subparsers.add_parser(command)
        child.add_argument("--root", type=Path, required=True)
        child.add_argument("--work-root", type=Path)
        if command == "validate":
            child.add_argument("--require-approved", action="store_true")
        if command == "approve":
            child.add_argument("--approved-at", required=True)
            child.add_argument("--approved-by", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()
    payload, code, documents = validate_contract(root, args.work_root.resolve() if args.work_root else None)
    if args.command == "hash":
        print(json.dumps({"contract_hash": payload["contract_hash"], "errors": payload["errors"]}))
        return code
    if args.command == "approve":
        if code != 0:
            print(json.dumps(payload))
            return code
        try:
            datetime.fromisoformat(args.approved_at)
        except ValueError:
            payload["errors"] = ["invalid_approved_at"]
            print(json.dumps(payload))
            return 2
        approval = approval_document(documents)
        assert approval is not None
        replace_approval(
            approval,
            {
                "approval.status": "approved",
                "approval.approved_at": args.approved_at,
                "approval.approved_by": args.approved_by,
                "approval.contract_hash": payload["contract_hash"],
            },
        )
        payload["approval_status"] = "approved"
        payload["executable"] = True
        print(json.dumps(payload))
        return 0
    if args.require_approved and code == 0 and not payload["executable"]:
        payload["errors"] = ["approval_required"]
        payload["status"] = "invalid"
        print(json.dumps(payload))
        return 3
    print(json.dumps(payload))
    return code


if __name__ == "__main__":
    sys.exit(main())
