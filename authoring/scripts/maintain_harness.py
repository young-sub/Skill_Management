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


def _tracked(source_root: Path) -> list[Path] | None:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=source_root, capture_output=True, check=False)
    if result.returncode:
        return None
    return [source_root / raw.decode("utf-8", errors="surrogateescape") for raw in result.stdout.split(b"\0") if raw]


def _instruction_findings(root: Path) -> list[dict[str, str]]:
    agents, claude = root / "AGENTS.md", root / "CLAUDE.md"
    if agents.is_file() and claude.is_file() and agents.read_bytes() != claude.read_bytes():
        return [_finding("instruction_drift", "AGENTS.md|CLAUDE.md", "instruction bytes differ")]
    return []


def _document_findings(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    tracked = _tracked(root)
    if tracked is None:
        return [{"kind": "git_ls_files_failed", "path": ".git", "detail": "unable to enumerate tracked files", "severity": "High"}]
    for path in tracked:
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


def _bundled_manifest() -> Path:
    return Path(__file__).resolve().parent.parent / "resources" / "public-resource-manifest.json"


def _installed_resource_findings(
    installed_roots: list[Path], manifest_path: Path
) -> list[dict[str, str]]:
    if not installed_roots:
        return []
    value: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("unsupported_resource_manifest_schema")
    if value.get("algorithm") != "sha256" or value.get("root") != "skills":
        raise ValueError("invalid_resource_manifest_identity")
    files = value.get("files")
    if not isinstance(files, dict) or not all(
        isinstance(path, str)
        and isinstance(digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", digest)
        for path, digest in files.items()
    ):
        raise ValueError("invalid_resource_manifest_files")
    findings: list[dict[str, str]] = []
    for installed_root in installed_roots:
        installed_root = installed_root.resolve()
        content_root = installed_root / "skills" if (installed_root / "skills").is_dir() else installed_root
        for relative, expected_digest in sorted(files.items()):
            path = content_root / relative
            detail_root = installed_root.as_posix()
            if not path.is_file():
                findings.append(
                    _finding("missing_installed_resource", relative, f"installed root: {detail_root}")
                )
                continue
            actual_digest = sha256(path.read_bytes()).hexdigest()
            if actual_digest != expected_digest:
                findings.append(
                    _finding(
                        "installed_resource_drift",
                        relative,
                        f"installed root: {detail_root}; expected {expected_digest}; actual {actual_digest}",
                    )
                )
    return findings


def _verification_budgets(root: Path) -> dict[str, float]:
    project = root / ".harness" / "project.yaml"
    if not project.is_file():
        return {}
    content = project.read_text(encoding="utf-8")
    budgets: dict[str, float] = {}
    for suite, key in (
        ("targeted", "targeted_max_seconds"),
        ("feature", "feature_max_seconds"),
        ("fast_suite", "fast_suite_max_seconds"),
    ):
        match = re.search(rf"(?m)^\s*{key}:\s*([0-9]+(?:\.[0-9]+)?)\s*$", content)
        if match:
            budgets[suite] = float(match.group(1))
    return budgets


def _test_history_findings(
    root: Path, history_path: Path | None, today: date, stale_days: int
) -> list[dict[str, str]]:
    if history_path is None:
        return []
    value: Any = json.loads(history_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("test_history_must_be_object")
    tests = value.get("tests", [])
    runs = value.get("runs", [])
    if not isinstance(tests, list) or not isinstance(runs, list):
        raise ValueError("test_history_arrays_required")
    findings: list[dict[str, str]] = []

    identifiers: dict[str, int] = {}
    fingerprints: dict[str, set[str]] = {}
    for item in tests:
        if not isinstance(item, dict):
            raise ValueError("test_history_test_must_be_object")
        test_id = item.get("id")
        if not isinstance(test_id, str) or not test_id:
            raise ValueError("test_history_test_id_required")
        identifiers[test_id] = identifiers.get(test_id, 0) + 1
        fingerprint = item.get("fingerprint")
        if isinstance(fingerprint, str) and fingerprint:
            fingerprints.setdefault(fingerprint, set()).add(test_id)
        last_run = item.get("last_run")
        if isinstance(last_run, str):
            last_date = date.fromisoformat(last_run)
            age = (today - last_date).days
            if age >= stale_days:
                findings.append(
                    _finding("stale_test", test_id, f"last run {age} days ago; threshold {stale_days}")
                )
    for test_id, count in sorted(identifiers.items()):
        if count > 1:
            findings.append(_finding("duplicate_test_id", test_id, f"appears {count} times"))
    for fingerprint, ids in sorted(fingerprints.items()):
        if len(ids) > 1:
            findings.append(
                _finding(
                    "duplicate_test_candidate",
                    "|".join(sorted(ids)),
                    f"shared fingerprint: {fingerprint}",
                )
            )

    budgets = _verification_budgets(root)
    durations: dict[str, list[tuple[date, float]]] = {}
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("test_history_run_must_be_object")
        suite = run.get("suite")
        duration = run.get("duration_seconds")
        recorded_at = run.get("recorded_at")
        if not isinstance(suite, str) or not isinstance(duration, (int, float)) or not isinstance(recorded_at, str):
            raise ValueError("test_history_run_fields_required")
        durations.setdefault(suite, []).append((date.fromisoformat(recorded_at), float(duration)))
    for suite, samples in sorted(durations.items()):
        samples.sort()
        budget = budgets.get(suite)
        latest = samples[-1][1]
        if budget is not None and latest > budget:
            findings.append(
                _finding(
                    "test_duration_budget_exceeded",
                    suite,
                    f"latest {latest:g}s exceeds {budget:g}s budget",
                )
            )
        recent = [duration for _, duration in samples[-3:]]
        if len(recent) == 3 and recent[0] < recent[1] < recent[2]:
            findings.append(
                _finding(
                    "test_duration_regression_trend",
                    suite,
                    "last three durations increased: " + ", ".join(f"{item:g}s" for item in recent),
                )
            )
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
    parser.add_argument("--installed-root", type=Path, action="append", default=[])
    parser.add_argument("--resource-manifest", type=Path)
    parser.add_argument("--test-history", type=Path)
    parser.add_argument("--stale-test-days", type=int, default=30)
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
        manifest = args.resource_manifest or _bundled_manifest()
        findings.extend(_installed_resource_findings(args.installed_root, manifest))
        findings.extend(_test_history_findings(root, args.test_history, today, args.stale_test_days))
        findings.extend(_worktree_findings(args.worktrees))
        findings.sort(key=lambda item: (item["kind"], item["path"], item["detail"]))
        actions = [
            {"kind": item["kind"], "path": item["path"], "action": "review", "applied": False}
            for item in findings
        ]
        blocked = any(item.get("severity") == "High" for item in findings)
        print(json.dumps({"mode": "report-only", "status": "blocked" if blocked else "complete", "findings": findings, "actions": actions}, ensure_ascii=False, sort_keys=True))
        return 2 if blocked else 0
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"mode": "report-only", "errors": [str(error)], "actions": []}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
