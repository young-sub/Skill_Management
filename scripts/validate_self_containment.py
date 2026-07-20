"""Validate that public Skills are install-tree self-contained."""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit


TEXT_SUFFIXES = {".json", ".md", ".ps1", ".py", ".sh", ".txt", ".yaml", ".yml"}
RULES = {
    "SC_RELATIVE_ESCAPE",
    "SC_ABSOLUTE_PATH",
    "SC_FILE_URI",
    "SC_REPO_ROOT_REFERENCE",
    "SC_CROSS_SKILL_REFERENCE",
    "SC_MISSING_RESOURCE",
    "SC_REPARSE_ESCAPE",
}
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\((?P<target>[^)\s]+)(?:\s+[^)]*)?\)")
RELATIVE_ESCAPE = re.compile(r"(?P<target>(?:\.\.[/\\])+[A-Za-z0-9._/\\-]+)")
WINDOWS_ABSOLUTE = re.compile(r"(?<![A-Za-z0-9_])(?P<target>[A-Za-z]:[\\/][^\s`\"'<>|]*)")
FILE_URI = re.compile(r"(?P<target>file://[^\s`\"'<>)]*)", re.IGNORECASE)


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _normalize_target(target: str) -> str:
    if target.lower().startswith("file:"):
        parsed = urlsplit(target)
        normalized_path = unquote(parsed.path).replace("\\", "/")
        authority = f"//{parsed.netloc}" if parsed.netloc else "//"
        return f"file:{authority}{normalized_path}"
    return target.replace("\\", "/")


def _locator(text: str, offset: int) -> str:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    return f"line:{line}:column:{offset - line_start + 1}"


def _finding(
    rule_id: str,
    skill: str,
    source_path: str,
    locator: str,
    target: str,
    evidence: str,
    *,
    severity: str = "error",
) -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "skill": skill,
        "source_path": source_path,
        "locator": locator,
        "normalized_target": _normalize_target(target),
        "severity": severity,
        "evidence": evidence,
    }


def _link_findings(
    root: Path,
    skills_root: Path,
    skill_root: Path,
    source: Path,
    text: str,
    target: str,
    offset: int,
) -> list[dict[str, str]]:
    if target.startswith(("#", "http://", "https://", "mailto:")):
        return []
    skill = skill_root.name
    source_path = source.relative_to(skill_root).as_posix()
    locator = _locator(text, offset)
    if target.lower().startswith("file:"):
        return [_finding("SC_FILE_URI", skill, source_path, locator, target, target)]
    if re.match(r"^[A-Za-z]:[/\\]", target) or target.startswith(("/", "\\\\")):
        return [_finding("SC_ABSOLUTE_PATH", skill, source_path, locator, target, target)]
    clean_target = target.split("#", 1)[0].split("?", 1)[0]
    if not clean_target:
        return []
    lexical = source.parent / clean_target
    resolved = lexical.resolve(strict=False)
    resolved_skill = skill_root.resolve()
    findings: list[dict[str, str]] = []
    if not _inside(resolved, resolved_skill):
        findings.append(
            _finding(
                "SC_RELATIVE_ESCAPE",
                skill,
                source_path,
                locator,
                target,
                "resource reference escapes skill directory",
            )
        )
        resolved_root = root.resolve()
        resolved_skills = skills_root.resolve()
        if _inside(resolved, resolved_skills):
            relative_to_skills = resolved.relative_to(resolved_skills)
            target_skill = relative_to_skills.parts[0] if relative_to_skills.parts else ""
            if target_skill and target_skill != skill:
                findings.append(
                    _finding(
                        "SC_CROSS_SKILL_REFERENCE",
                        skill,
                        source_path,
                        locator,
                        target,
                        f"runtime dependency on public Skill '{target_skill}'",
                    )
                )
        elif _inside(resolved, resolved_root):
            findings.append(
                _finding(
                    "SC_REPO_ROOT_REFERENCE",
                    skill,
                    source_path,
                    locator,
                    target,
                    "reference depends on repository-root content absent from an installed Skill",
                )
            )
        return findings
    if not lexical.exists():
        findings.append(
            _finding(
                "SC_MISSING_RESOURCE",
                skill,
                source_path,
                locator,
                target,
                "referenced in-skill resource is missing",
            )
        )
    return findings


def _scan_text_file(
    root: Path, skills_root: Path, skill_root: Path, source: Path
) -> list[dict[str, str]]:
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [
            _finding(
                "SC_MISSING_RESOURCE",
                skill_root.name,
                source.relative_to(skill_root).as_posix(),
                "file",
                source.name,
                f"text resource could not be inspected: {type(error).__name__}",
            )
        ]
    findings: list[dict[str, str]] = []
    occupied: set[tuple[int, int]] = set()
    for match in MARKDOWN_LINK.finditer(text):
        target = match.group("target")
        occupied.add(match.span("target"))
        findings.extend(
            _link_findings(root, skills_root, skill_root, source, text, target, match.start("target"))
        )
    source_path = source.relative_to(skill_root).as_posix()
    for rule_id, pattern in (
        ("SC_FILE_URI", FILE_URI),
        ("SC_ABSOLUTE_PATH", WINDOWS_ABSOLUTE),
    ):
        for match in pattern.finditer(text):
            if any(start <= match.start("target") < end for start, end in occupied):
                continue
            target = match.group("target")
            findings.append(
                _finding(
                    rule_id,
                    skill_root.name,
                    source_path,
                    _locator(text, match.start("target")),
                    target,
                    target,
                )
            )
    for match in RELATIVE_ESCAPE.finditer(text):
        if any(start <= match.start("target") < end for start, end in occupied):
            continue
        findings.extend(
            _link_findings(
                root,
                skills_root,
                skill_root,
                source,
                text,
                match.group("target"),
                match.start("target"),
            )
        )
    return findings


def _is_reparse(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction and is_junction())
    except OSError:
        return True


def _scan_reparse(skill_root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    resolved_skill = skill_root.resolve()
    for current, directories, files in os.walk(skill_root, followlinks=False):
        current_path = Path(current)
        for name in [*directories, *files]:
            path = current_path / name
            if not _is_reparse(path):
                continue
            relative = path.relative_to(skill_root).as_posix()
            try:
                resolved = path.resolve(strict=True)
                escaped = not _inside(resolved, resolved_skill)
                evidence = f"reparse resolves to {resolved.as_posix()}"
            except OSError as error:
                escaped = True
                evidence = f"reparse target inspection failed: {type(error).__name__}"
            if escaped:
                findings.append(
                    _finding(
                        "SC_REPARSE_ESCAPE",
                        skill_root.name,
                        relative,
                        "filesystem-entry",
                        relative,
                        evidence,
                    )
                )
        directories[:] = [name for name in directories if not _is_reparse(current_path / name)]
    return findings


def _manifest_findings(root: Path, skills_root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    resource_map = root / "authoring" / "resource-map.json"
    if resource_map.is_file():
        try:
            mapping = json.loads(resource_map.read_text(encoding="utf-8"))
            resources = mapping.get("resources", [])
        except (OSError, json.JSONDecodeError, AttributeError):
            resources = []
        for item in resources:
            if not isinstance(item, dict):
                continue
            for target in item.get("targets", []):
                if not isinstance(target, str) or (skills_root / target).is_file():
                    continue
                skill = target.replace("\\", "/").split("/", 1)[0]
                findings.append(
                    _finding(
                        "SC_MISSING_RESOURCE",
                        skill,
                        "authoring/resource-map.json",
                        f"target:{target}",
                        target,
                        "declared generated resource target is missing",
                    )
                )
    public_manifest = root / "authoring" / "public-resource-manifest.json"
    if public_manifest.is_file():
        try:
            manifest = json.loads(public_manifest.read_text(encoding="utf-8"))
            declared = manifest.get("files", {})
        except (OSError, json.JSONDecodeError, AttributeError):
            declared = {}
        for target in declared:
            if isinstance(target, str) and not (skills_root / target).is_file():
                skill = target.replace("\\", "/").split("/", 1)[0]
                findings.append(
                    _finding(
                        "SC_MISSING_RESOURCE",
                        skill,
                        "authoring/public-resource-manifest.json",
                        f"files:{target}",
                        target,
                        "public resource manifest entry is missing from the complete tree",
                    )
                )
    return findings


def _load_allowlist(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    path = root / "distribution" / "self-containment-allowlist.json"
    if not path.is_file():
        return [], []
    errors: list[str] = []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [], [f"invalid allowlist JSON: {error}"]
    if value.get("schema_version") != 1 or not isinstance(value.get("entries"), list):
        return [], ["unsupported self-containment allowlist schema"]
    required = {
        "rule_id",
        "skill",
        "source_path",
        "normalized_target",
        "reason",
        "owner",
        "review_after",
    }
    entries: list[dict[str, str]] = []
    for index, entry in enumerate(value["entries"]):
        if not isinstance(entry, dict) or not required <= entry.keys():
            errors.append(f"allowlist entry {index} is missing governance fields")
            continue
        if entry["rule_id"] not in RULES or not all(str(entry[key]).strip() for key in required):
            errors.append(f"allowlist entry {index} has invalid values")
            continue
        try:
            date.fromisoformat(str(entry["review_after"]))
        except ValueError:
            errors.append(f"allowlist entry {index} has invalid review_after")
            continue
        entries.append({key: str(entry[key]) for key in required})
    return entries, errors


def _allowlisted(finding: dict[str, str], entries: Iterable[dict[str, str]]) -> bool:
    identity = ("rule_id", "skill", "source_path", "normalized_target")
    return any(all(entry[key] == finding[key] for key in identity) for entry in entries)


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    skills_root = root / "skills"
    findings: list[dict[str, str]] = []
    if skills_root.is_dir():
        for skill_root in sorted(skills_root.iterdir(), key=lambda path: path.name):
            if not skill_root.is_dir() or not (skill_root / "SKILL.md").is_file():
                continue
            findings.extend(_scan_reparse(skill_root))
            for current, directories, files in os.walk(skill_root, followlinks=False):
                current_path = Path(current)
                directories[:] = [
                    name for name in directories if not _is_reparse(current_path / name)
                ]
                for name in files:
                    source = current_path / name
                    if source.suffix.lower() in TEXT_SUFFIXES and not _is_reparse(source):
                        findings.extend(_scan_text_file(root, skills_root, skill_root, source))
    findings.extend(_manifest_findings(root, skills_root))
    unique = {
        (
            item["rule_id"],
            item["skill"],
            item["source_path"],
            item["locator"],
            item["normalized_target"],
        ): item
        for item in findings
    }
    ordered = sorted(unique.values(), key=lambda item: tuple(item[key] for key in ("skill", "source_path", "locator", "rule_id", "normalized_target")))
    allowlist, allowlist_errors = _load_allowlist(root)
    active = [item for item in ordered if not _allowlisted(item, allowlist)]
    suppressed = [item for item in ordered if _allowlisted(item, allowlist)]
    return {
        "schema_version": 1,
        "status": "passed" if not active and not allowlist_errors else "failed",
        "findings": active,
        "allowlisted_findings": suppressed,
        "allowlist_errors": allowlist_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args()
    payload = validate(args.repository_root)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
