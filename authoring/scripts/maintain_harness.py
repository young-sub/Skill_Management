#!/usr/bin/env python3
"""Report Harness drift and retention candidates without applying changes."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


TEXT_DOCUMENT_SUFFIXES = {".md", ".txt", ".rst", ".adoc", ".html", ".json", ".yaml", ".yml"}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def _finding(kind: str, path: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "path": path, "detail": detail}


def _tracked(source_root: Path) -> list[Path]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=source_root, capture_output=True, check=False)
    if result.returncode:
        return []
    return [source_root / raw.decode("utf-8", errors="surrogateescape") for raw in result.stdout.split(b"\0") if raw]


def _instruction_findings(root: Path) -> list[dict[str, str]]:
    agents, claude = root / "AGENTS.md", root / "CLAUDE.md"
    if agents.is_file() and claude.is_file() and agents.read_bytes() != claude.read_bytes():
        return [_finding("instruction_drift", "AGENTS.md|CLAUDE.md", "instruction bytes differ")]
    return []


def _document_findings(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in _tracked(root):
        if path.suffix.lower() not in TEXT_DOCUMENT_SUFFIXES or not path.is_file():
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        relative = path.relative_to(root).as_posix()
        if ".work/" in source.replace("\\", "/"):
            findings.append(_finding("durable_work_reference", relative, "tracked document references .work/"))
        if path.suffix.lower() != ".md":
            continue
        for raw_target in MARKDOWN_LINK.findall(source):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("#", "http://", "https://", "mailto:", "/")):
                continue
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                continue
            if not candidate.exists():
                findings.append(_finding("broken_relative_path", relative, target))
    return findings


def _age_days(path: Path, today: date) -> int:
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date()
    return (today - modified).days


def _retention_findings(root: Path, today: date, active_days: int, archive_days: int, trash_days: int) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    active = root / ".work" / "active"
    if active.is_dir():
        for item in sorted(active.iterdir()):
            if item.is_dir() and _age_days(item, today) >= active_days:
                findings.append(_finding("active_retention_eligible", item.relative_to(root).as_posix(), f"age >= {active_days} days"))
    archive = root / ".work" / "archive"
    if archive.is_dir():
        for month in sorted(archive.iterdir()):
            try:
                month_date = datetime.strptime(month.name, "%Y-%m").date()
            except ValueError:
                continue
            if (today - month_date).days >= archive_days:
                for item in sorted(month.iterdir()):
                    if item.is_dir():
                        findings.append(_finding("archive_retention_eligible", item.relative_to(root).as_posix(), f"age >= {archive_days} days"))
    trash = root / ".work" / "trash"
    if trash.is_dir():
        for dated in sorted(trash.iterdir()):
            try:
                trash_date = datetime.strptime(dated.name, "%Y-%m-%d").date()
            except ValueError:
                continue
            if (today - trash_date).days >= trash_days:
                for item in sorted(dated.iterdir()):
                    if item.is_dir():
                        findings.append(_finding("trash_retention_eligible", item.relative_to(root).as_posix(), f"age >= {trash_days} days"))
    return findings


def _resource_findings(root: Path) -> list[dict[str, str]]:
    resource_map = root / "authoring" / "resource-map.json"
    if not resource_map.is_file():
        return []
    value = json.loads(resource_map.read_text(encoding="utf-8"))
    findings: list[dict[str, str]] = []
    for entry in value.get("resources", []):
        source = root / "authoring" / entry["source"]
        if not source.is_file():
            findings.append(_finding("missing_resource_source", source.relative_to(root).as_posix(), "mapped source missing"))
            continue
        digest = sha256(source.read_bytes()).hexdigest()
        for target_name in entry.get("targets", []):
            target = root / "skills" / target_name
            if not target.is_file():
                findings.append(_finding("missing_resource_target", target.relative_to(root).as_posix(), "mapped target missing"))
            else:
                content = target.read_bytes()
                if target.suffix.lower() == ".json":
                    matches = sha256(content).hexdigest() == digest
                else:
                    header = content[:1024].decode("utf-8", errors="replace")
                    match = re.search(r"Source-SHA256:\s*([0-9a-fA-F]{64})", header)
                    matches = match is not None and match.group(1).lower() == digest
                if not matches:
                    findings.append(_finding("resource_drift", target.relative_to(root).as_posix(), entry["source"]))
    return findings


def _worktree_findings(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("worktrees_must_be_object")
    registered = {str(Path(str(item)).resolve()) for item in value.get("registered", [])}
    observed = {str(Path(str(item)).resolve()) for item in value.get("observed", [])}
    findings = [_finding("unregistered_worktree", item, "observed path is not registered") for item in sorted(observed - registered)]
    findings.extend(
        _finding("residual_worktree_path", item, "registered path no longer exists")
        for item in sorted(registered) if not Path(item).exists()
    )
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--current-date", required=True)
    parser.add_argument("--worktrees", type=Path)
    parser.add_argument("--active-retention-days", type=int, default=30)
    parser.add_argument("--archive-retention-days", type=int, default=180)
    parser.add_argument("--trash-retention-days", type=int, default=30)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        root = args.source_root.resolve()
        today = date.fromisoformat(args.current_date)
        findings = _instruction_findings(root)
        findings.extend(_document_findings(root))
        findings.extend(_retention_findings(root, today, args.active_retention_days, args.archive_retention_days, args.trash_retention_days))
        findings.extend(_resource_findings(root))
        findings.extend(_worktree_findings(args.worktrees))
        findings.sort(key=lambda item: (item["kind"], item["path"], item["detail"]))
        actions = [
            {"kind": item["kind"], "path": item["path"], "action": "review", "applied": False}
            for item in findings
        ]
        print(json.dumps({"mode": "report-only", "findings": findings, "actions": actions}, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"mode": "report-only", "errors": [str(error)], "actions": []}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
