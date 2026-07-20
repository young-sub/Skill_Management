"""Deterministic project bootstrap planner, applier, and validator."""

from __future__ import annotations

import argparse
import base64
import difflib
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
import uuid


CLASSIFICATIONS = {
    "NEW_UNCONFIGURED",
    "EXISTING_PARTIAL",
    "EXISTING_OVERGROWN",
    "DRIFT_REPAIR",
}
PLAN_SCHEMA_VERSION = 1
TEXT_EVIDENCE_SUFFIXES = {
    ".md",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
}
DISCOVERY_EXCLUDED_PARTS = {".git", ".work", "node_modules", "vendor", "dist", "build"}
REQUIRED_PROJECT_KEYS = (
    "version: 2",
    "authoritative: AGENTS.md",
    "- CLAUDE.md",
    "root: .work",
    "retention_days: 90",
    "trash_grace_days: 30",
    "targeted_max_seconds: 30",
    "feature_max_seconds: 120",
    "fast_suite_max_seconds: 300",
    "full_suite_runs_per_goal: 1",
    "integration_default: impacted",
    "live_default: false",
    "eval_default: false",
)


def _template_root() -> Path:
    return Path(__file__).resolve().parent.parent / "templates" / "project"


def _load_template(name: str) -> str:
    content = (_template_root() / name).read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    if lines and (
        lines[0].startswith("<!-- Generated file.")
        or lines[0].startswith("# Generated file.")
    ):
        for index, line in enumerate(lines):
            if not line.strip():
                return "".join(lines[index + 1 :])
    return content


def _read_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def instruction_hash(content: bytes) -> str:
    return sha256(content).hexdigest()


def _instruction_content(root: Path) -> bytes:
    for name in ("AGENTS.md", "CLAUDE.md"):
        content = _read_bytes(root / name)
        if content is not None:
            return content
    return _load_template("AGENTS.md").encode("utf-8")


def _is_overgrown(root: Path) -> bool:
    for instruction in root.rglob("AGENTS.md"):
        try:
            if len(instruction.read_text(encoding="utf-8").splitlines()) > 100:
                return True
        except UnicodeDecodeError:
            return True
    return False


def _config_sha(config: str) -> str | None:
    match = re.search(r"(?m)^\s*sha256:\s*([0-9a-f]{64})\s*$", config)
    return match.group(1) if match else None


def _has_drift(root: Path) -> bool:
    config_path = root / ".harness" / "project.yaml"
    if not config_path.is_file():
        return False
    agents = _read_bytes(root / "AGENTS.md")
    claude = _read_bytes(root / "CLAUDE.md")
    if agents is None or claude is None or agents != claude:
        return True
    config = config_path.read_text(encoding="utf-8")
    return _config_sha(config) != instruction_hash(agents)


def classify(root: Path) -> str:
    if _has_drift(root):
        return "DRIFT_REPAIR"
    if _is_overgrown(root):
        return "EXISTING_OVERGROWN"
    evidence_names = (
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        ".github",
        "docs",
        "src",
        "tests",
    )
    if any((root / name).exists() for name in evidence_names):
        return "EXISTING_PARTIAL"
    return "NEW_UNCONFIGURED"


def _path_is_reparse(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if is_junction is not None and is_junction():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        reparse_flag = getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & reparse_flag)
    except OSError:
        return False


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _existing_components(root: Path, target: Path) -> list[Path]:
    components = [root]
    relative = target.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            components.append(current)
        else:
            break
    return components


def _unsafe_write_target(root: Path, target: Path) -> str | None:
    root = root.absolute()
    target = target.absolute()
    if not _within(target, root):
        return "target_outside_root"
    for component in _existing_components(root, target):
        if _path_is_reparse(component):
            return f"reparse_component:{component}"
    resolved_root = root.resolve()
    existing_parent = target.parent
    while not existing_parent.exists() and existing_parent != root:
        existing_parent = existing_parent.parent
    try:
        resolved_parent = existing_parent.resolve(strict=True)
    except OSError:
        return f"unresolvable_parent:{existing_parent}"
    if not _within(resolved_parent, resolved_root):
        return f"resolved_parent_outside_root:{existing_parent}"
    return None


def _write_targets(root: Path) -> list[Path]:
    relative_paths = (
        "AGENTS.md",
        "CLAUDE.md",
        "TESTING.md",
        ".harness/project.yaml",
        ".gitignore",
        ".work/active",
        ".work/archive",
        ".work/trash",
    )
    return [root / relative for relative in relative_paths]


def _unsafe_targets(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for target in _write_targets(root):
        reason = _unsafe_write_target(root, target)
        if reason:
            findings.append(
                {"path": target.relative_to(root).as_posix(), "reason": reason}
            )
    return findings


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _git_head(root: Path) -> str | None:
    result = _git(root, "rev-parse", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def _git_tree(root: Path) -> str | None:
    result = _git(root, "rev-parse", "HEAD^{tree}")
    return result.stdout.strip() if result.returncode == 0 else None


def _git_state(root: Path, relative_path: str) -> str:
    tracked = _git(root, "ls-files", "--error-unmatch", "--", relative_path)
    if tracked.returncode == 0:
        return "tracked"
    ignored = _git(root, "check-ignore", "-q", "--no-index", "--", relative_path)
    if ignored.returncode == 0:
        return "ignored"
    return "untracked" if (root / relative_path).exists() else "absent"


def _ignore_source(root: Path, relative_path: str) -> str | None:
    result = _git(root, "check-ignore", "-v", "--no-index", "--", relative_path)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or "git-ignore-source-unavailable"


def _repository_boundaries(root: Path) -> list[dict[str, str]]:
    boundaries: list[dict[str, str]] = []
    for current, directories, _files in os.walk(root, followlinks=False):
        current_path = Path(current)
        relative = current_path.relative_to(root)
        if relative.parts and relative.parts[0] in {".git", ".work"}:
            directories[:] = []
            continue
        if current_path != root and (current_path / ".git").exists():
            boundaries.append({"kind": "nested_repository", "path": relative.as_posix()})
            directories[:] = []
            continue
        retained: list[str] = []
        for name in directories:
            candidate = current_path / name
            candidate_relative = candidate.relative_to(root)
            if name in {".git", ".work", "node_modules", "dist", "build"}:
                continue
            if _path_is_reparse(candidate):
                boundaries.append(
                    {"kind": "reparse_boundary", "path": candidate_relative.as_posix()}
                )
                continue
            retained.append(name)
        directories[:] = retained
    submodules = _git(root, "submodule", "status", "--recursive")
    if submodules.returncode == 0:
        for line in submodules.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                boundaries.append({"kind": "submodule", "path": parts[1]})
    return sorted(boundaries, key=lambda item: (item["path"], item["kind"]))


def _discovery_files(root: Path, boundaries: list[dict[str, str]]) -> list[Path]:
    excluded_roots = {item["path"] for item in boundaries}
    discovered: list[Path] = []
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        relative_dir = current_path.relative_to(root).as_posix()
        if relative_dir in excluded_roots:
            directories[:] = []
            continue
        directories[:] = [
            name
            for name in directories
            if name not in DISCOVERY_EXCLUDED_PARTS
            and (current_path / name).relative_to(root).as_posix() not in excluded_roots
            and not _path_is_reparse(current_path / name)
        ]
        for name in files:
            path = current_path / name
            relative = path.relative_to(root)
            if any(part in DISCOVERY_EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.suffix.lower() in TEXT_EVIDENCE_SUFFIXES or name in {"Makefile", "go.mod"}:
                discovered.append(path)
    return sorted(discovered, key=lambda path: _relative(root, path))


def _read_text_untrusted(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeDecodeError) as error:
        return None, f"read_failed:{type(error).__name__}"


def _evidence_kind(relative_path: str) -> str | None:
    name = Path(relative_path).name
    lower = relative_path.lower()
    if name in {"AGENTS.md", "CLAUDE.md", "copilot-instructions.md"} or name.startswith(".cursorrules"):
        return "instructions"
    if lower.startswith(".github/workflows/") or name in {".gitlab-ci.yml", "azure-pipelines.yml"}:
        return "ci"
    if name in {"pyproject.toml", "package.json", "Cargo.toml", "go.mod", "Makefile"} or name.endswith((".sln", ".csproj")):
        return "manifest"
    if name in {"TESTING.md", "CONTRIBUTING.md", "README.md", "CONTEXT.md"}:
        return "documentation"
    if lower.startswith("docs/architecture") or lower.startswith("docs/adr/") or lower == "docs/agents/domain.md":
        return "architecture"
    return None


def _discover_commands(relative_path: str, text: str) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []

    def add(command: str, locator: str, confidence: str) -> None:
        normalized = " ".join(command.strip().split())
        if not normalized or normalized.startswith(("#", "<!--")):
            return
        if not re.match(r"^(python|python3|pytest|npm|pnpm|yarn|cargo|go|dotnet|make|powershell|pwsh)\b", normalized, re.I):
            return
        commands.append(
            {
                "command": normalized,
                "source_pointer": f"{relative_path}:{locator}",
                "confidence": confidence,
                "state": "discovered",
            }
        )

    if Path(relative_path).name == "package.json":
        try:
            package = json.loads(text)
        except json.JSONDecodeError:
            package = {}
        scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
        if isinstance(scripts, dict):
            for name, value in sorted(scripts.items()):
                if isinstance(value, str) and (name == "test" or name.startswith(("test:", "lint", "type", "build"))):
                    add("npm test" if name == "test" else f"npm run {name}", f"scripts.{name}", "high")
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        run_match = re.match(r"^-?\s*run:\s*[|>]?-?\s*(.+)$", stripped)
        if run_match and run_match.group(1):
            add(run_match.group(1), str(number), "high")
        for inline in re.findall(r"`([^`\r\n]+)`", line):
            add(inline, str(number), "medium")
        if stripped and not stripped.startswith(("#", "```", "- `")):
            add(stripped, str(number), "medium")
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for command in commands:
        unique[(command["command"], command["source_pointer"])] = command
    return list(unique.values())


def _explicit_references(text: str, known_paths: set[str]) -> list[str]:
    referenced: set[str] = set()
    for candidate in known_paths:
        if candidate in text:
            referenced.add(candidate)
    return sorted(referenced)


def _input_record(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    content = _read_bytes(path)
    record: dict[str, Any] = {
        "path": relative_path,
        "existence": content is not None,
        "content_sha256": sha256(content).hexdigest() if content is not None else None,
        "git_state": _git_state(root, relative_path),
        "ignore_source": _ignore_source(root, relative_path),
    }
    if content is not None:
        try:
            record["content_utf8"] = content.decode("utf-8")
        except UnicodeDecodeError:
            record["content_base64"] = base64.b64encode(content).decode("ascii")
    return record


def _path_policy_entry(root: Path, path: str, desired_state: str) -> dict[str, Any]:
    probe = path.replace("**", "probe").replace("*", "fixture")
    current_state = _git_state(root, probe)
    ignore_source = _ignore_source(root, probe)
    approval_required = desired_state == "local-only"
    proposed_action = "none"
    if desired_state == "tracked" and current_state == "ignored":
        proposed_action = "resolve_ignore_conflict"
    elif desired_state == "tracked" and current_state in {"absent", "untracked"}:
        proposed_action = "create_or_review_tracked"
    elif desired_state == "local-only" and current_state != "ignored":
        proposed_action = "propose_ignore_rule"
    return {
        "path": path,
        "desired_state": desired_state,
        "current_state": current_state,
        "ignore_source": ignore_source,
        "evidence": [f"git_state:{current_state}"] + ([ignore_source] if ignore_source else []),
        "proposed_action": proposed_action,
        "approval_required": approval_required,
    }


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _plan_digest(plan: dict[str, Any]) -> str:
    return sha256(_canonical_json({key: value for key, value in plan.items() if key != "plan_sha256"})).hexdigest()


def _file_mutation(
    root: Path,
    relative_path: str,
    after: bytes,
    *,
    desired_state: str,
    approval_class: str,
    additional_approval_classes: list[str] | None = None,
) -> dict[str, Any] | None:
    before = _read_bytes(root / relative_path)
    if before == after:
        return None
    mutation: dict[str, Any] = {
        "path": relative_path,
        "operation": "create" if before is None else "replace",
        "before_sha256": sha256(before).hexdigest() if before is not None else None,
        "after_sha256": sha256(after).hexdigest(),
        "after_content_base64": base64.b64encode(after).decode("ascii"),
        "desired_state": desired_state,
        "approval_class": approval_class,
    }
    if additional_approval_classes:
        mutation["additional_approval_classes"] = additional_approval_classes
    return mutation


def build_reconciliation_plan(root: Path) -> dict[str, Any]:
    root = root.absolute()
    boundaries = _repository_boundaries(root)
    files = _discovery_files(root, boundaries)
    known_paths = {_relative(root, path) for path in files}
    evidence: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    commands: list[dict[str, Any]] = []
    contents: dict[str, str] = {}
    for path in files:
        relative_path = _relative(root, path)
        kind = _evidence_kind(relative_path)
        if kind is None:
            continue
        text, warning = _read_text_untrusted(path)
        if warning:
            warnings.append({"path": relative_path, "warning": warning})
            continue
        assert text is not None
        contents[relative_path] = text
        evidence.append(
            {
                "path": relative_path,
                "evidence_kind": kind,
                "detector": "conservative-text-inventory",
                "locator": relative_path,
                "confidence": "high" if kind in {"instructions", "ci", "manifest"} else "medium",
                "notes": "content treated as untrusted and was not executed",
            }
        )
        if kind in {"ci", "manifest", "documentation"}:
            commands.extend(_discover_commands(relative_path, text))
    commands = sorted(
        {(_item["command"], _item["source_pointer"]): _item for _item in commands}.values(),
        key=lambda item: (item["command"], item["source_pointer"]),
    )

    authorities: list[dict[str, Any]] = []
    instruction_paths = [path for path in ("AGENTS.md", "CLAUDE.md") if path in contents]
    for index, path in enumerate(instruction_paths):
        authorities.append(
            {
                "authority_kind": "instructions",
                "path": path,
                "precedence_basis": "root repository instruction surface",
                "precedence_rank": index + 1,
                "confidence": "high",
                "conflicts": [],
            }
        )
    for path in sorted(contents):
        if path in {"TESTING.md", "CONTRIBUTING.md", "README.md"}:
            authorities.append(
                {
                    "authority_kind": "verification",
                    "path": path,
                    "precedence_basis": "dedicated current documentation" if path == "TESTING.md" else "repository guidance",
                    "precedence_rank": 3 if path == "TESTING.md" else 4,
                    "confidence": "high" if path == "TESTING.md" else "medium",
                    "conflicts": [],
                }
            )
        elif _evidence_kind(path) == "architecture":
            authorities.append(
                {
                    "authority_kind": "architecture",
                    "path": path,
                    "precedence_basis": "dedicated architecture document",
                    "precedence_rank": 3,
                    "confidence": "high",
                    "conflicts": [],
                }
            )

    instruction_references: set[str] = set()
    for path in instruction_paths:
        instruction_references.update(_explicit_references(contents[path], known_paths))
    for authority in authorities:
        if authority["path"] in instruction_references:
            authority["precedence_basis"] = "explicitly referenced by repository instruction"
            authority["precedence_rank"] = 1
            authority["confidence"] = "high"

    blockers: list[dict[str, Any]] = []
    if len(instruction_paths) > 1 and contents[instruction_paths[0]].encode("utf-8") != contents[instruction_paths[1]].encode("utf-8"):
        conflict = {
            "kind": "conflicting_instruction_authority",
            "severity": "high",
            "paths": instruction_paths,
            "reason": "root instruction surfaces differ",
        }
        blockers.append(conflict)
        for authority in authorities:
            if authority["authority_kind"] == "instructions":
                authority["conflicts"].append("root instruction bytes differ")

    command_values = sorted({item["command"] for item in commands})
    conflicting_commands = command_values if len(command_values) > 1 else []
    if conflicting_commands:
        blockers.append(
            {
                "kind": "conflicting_verification_commands",
                "severity": "medium",
                "commands": conflicting_commands,
                "reason": "multiple candidate commands require intent classification",
            }
        )

    agents_content = contents.get("AGENTS.md") or contents.get("CLAUDE.md")
    referenced = _explicit_references(agents_content or "", known_paths)
    if agents_content is None:
        pointer_lines = ["# AGENTS.md", "", "## Repository Sources"]
        for path in sorted(
            item["path"]
            for item in authorities
            if item["authority_kind"] in {"architecture", "verification"}
        ):
            pointer_lines.append(f"- `{path}`")
        if command_values:
            pointer_lines.extend(["", "## Verification", *[f"- `{command}`" for command in command_values]])
        agents_content = "\n".join(pointer_lines).rstrip() + "\n"
        referenced = sorted(
            item["path"]
            for item in authorities
            if item["authority_kind"] in {"architecture", "verification"}
        )
    router_proposals = [
        {
            "path": "AGENTS.md",
            "preserved": instruction_paths,
            "referenced": referenced,
            "new_router_lines": [] if "AGENTS.md" in contents else agents_content.splitlines(),
            "unresolved": [item["kind"] for item in blockers if "instruction" in item["kind"]],
            "proposed_content": agents_content,
        }
    ]
    for nested_path in sorted(path for path in contents if path.endswith("/AGENTS.md")):
        router_proposals.append(
            {
                "path": nested_path,
                "preserved": [nested_path],
                "referenced": _explicit_references(contents[nested_path], known_paths),
                "new_router_lines": [],
                "unresolved": [],
                "proposed_content": contents[nested_path],
            }
        )

    testing_existing = contents.get("TESTING.md", "")
    additions = [item for item in commands if item["command"] not in testing_existing]
    proposed_testing = testing_existing
    if additions:
        separator = "" if not proposed_testing or proposed_testing.endswith("\n") else "\n"
        proposed_testing += separator + "\n## Discovered verification candidates\n\n"
        proposed_testing += "\n".join(f"- `{item['command']}` ({item['source_pointer']})" for item in additions) + "\n"
    testing_merge = {
        "preserved_sections": ["existing TESTING.md bytes"] if testing_existing else [],
        "preserved_content_utf8": testing_existing,
        "detected_commands": commands,
        "command_evidence": [{"command": item["command"], "source_pointer": item["source_pointer"], "confidence": item["confidence"]} for item in commands],
        "proposed_additions": additions,
        "conflicting_commands": conflicting_commands,
        "human_decisions_required": ["classify conflicting verification commands"] if conflicting_commands else [],
        "unified_diff_preview": _text_diff("TESTING.md", testing_existing.encode("utf-8"), proposed_testing.encode("utf-8")) if proposed_testing != testing_existing else "",
        "proposed_content_utf8": proposed_testing,
    }
    if not proposed_testing:
        proposed_testing = "# Testing\n\nNo verification command has been accepted.\n"
        testing_merge["proposed_content_utf8"] = proposed_testing
        testing_merge["unified_diff_preview"] = _text_diff(
            "TESTING.md", b"", proposed_testing.encode("utf-8")
        )

    path_policy = [
        _path_policy_entry(root, "AGENTS.md", "tracked"),
        _path_policy_entry(root, "CLAUDE.md", "tracked"),
        _path_policy_entry(root, "TESTING.md", "tracked"),
        _path_policy_entry(root, ".harness/project.yaml", "tracked"),
        _path_policy_entry(root, ".harness/**", "prohibited"),
        _path_policy_entry(root, ".work/**", "local-only"),
        _path_policy_entry(root, "agent-env.*.md", "local-only"),
    ]
    harness_entry = next(item for item in path_policy if item["path"] == ".harness/project.yaml")
    if harness_entry["current_state"] == "ignored":
        blockers.append(
            {
                "kind": "tracked_path_ignored",
                "severity": "high",
                "path": ".harness/project.yaml",
                "ignore_source": harness_entry["ignore_source"],
                "reason": ".harness/project.yaml must remain tracked",
            }
        )
    for boundary in boundaries:
        blockers.append(
            {
                "kind": "repository_boundary",
                "severity": "high",
                "path": boundary["path"],
                "boundary_kind": boundary["kind"],
                "reason": "excluded from automatic migration",
            }
        )

    input_paths = sorted(
        known_paths
        | {"AGENTS.md", "CLAUDE.md", "TESTING.md", ".harness/project.yaml", ".gitignore"}
    )
    inputs = [_input_record(root, path) for path in input_paths]
    fingerprint_material = {
        "inputs": [{key: value for key, value in item.items() if key not in {"content_utf8", "content_base64"}} for item in inputs],
        "head": _git_head(root),
        "tree": _git_tree(root),
        "boundaries": boundaries,
    }
    discovery_fingerprint = sha256(_canonical_json(fingerprint_material)).hexdigest()
    instruction_bytes = agents_content.encode("utf-8")
    project_config = (
        "version: 2\n"
        "project:\n"
        f"  name: {json.dumps(root.name, ensure_ascii=False)}\n"
        "  classification: existing_brownfield\n"
        "instructions:\n"
        "  authoritative: AGENTS.md\n"
        "  mirrors:\n"
        "    - CLAUDE.md\n"
        f"  sha256: {instruction_hash(instruction_bytes)}\n"
        "work:\n"
        "  root: .work\n"
        "  retention_days: 90\n"
        "  trash_grace_days: 30\n"
        "verification:\n"
        "  targeted_max_seconds: 30\n"
        "  feature_max_seconds: 120\n"
        "  fast_suite_max_seconds: 300\n"
        "  full_suite_runs_per_goal: 1\n"
        "  integration_default: impacted\n"
        "  live_default: false\n"
        "  eval_default: false\n"
        "  commands: []\n"
    ).encode("utf-8")
    mutations: list[dict[str, Any]] = []
    for relative_path, content in (
        ("AGENTS.md", instruction_bytes),
        ("CLAUDE.md", instruction_bytes),
        ("TESTING.md", proposed_testing.encode("utf-8")),
        (".harness/project.yaml", project_config),
    ):
        mutation = _file_mutation(
            root,
            relative_path,
            content,
            desired_state="tracked",
            approval_class="plan",
        )
        if mutation:
            mutations.append(mutation)
    gitignore_path = root / ".gitignore"
    gitignore_before = _read_bytes(gitignore_path) or b""
    try:
        gitignore_text = gitignore_before.decode("utf-8")
    except UnicodeDecodeError:
        gitignore_text = ""
        blockers.append(
            {
                "kind": "unsupported_gitignore_encoding",
                "severity": "high",
                "path": ".gitignore",
                "reason": "safe byte-preserving append requires UTF-8",
            }
        )
    missing_rules = [
        rule for rule in (".work/", "agent-env.*.md") if rule not in gitignore_text.splitlines()
    ]
    if missing_rules and not any(item["kind"] == "unsupported_gitignore_encoding" for item in blockers):
        newline = b"\r\n" if b"\r\n" in gitignore_before else b"\n"
        separator = b"" if not gitignore_before or gitignore_before.endswith((b"\n", b"\r")) else newline
        gitignore_after = gitignore_before + separator + newline.join(rule.encode("utf-8") for rule in missing_rules) + newline
        mutation = _file_mutation(
            root,
            ".gitignore",
            gitignore_after,
            desired_state="tracked",
            approval_class="local-only:.work/",
            additional_approval_classes=["local-only:agent-env.*.md"],
        )
        if mutation:
            mutations.append(mutation)
    for directory in (".work/active", ".work/archive", ".work/trash"):
        if not (root / directory).is_dir():
            mutations.append(
                {
                    "path": directory,
                    "operation": "create_directory",
                    "before_sha256": None,
                    "after_sha256": None,
                    "desired_state": "local-only",
                    "approval_class": "local-only:.work/",
                }
            )

    plan: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "mode": "brownfield-reconcile",
        "plan_id": discovery_fingerprint[:16],
        "repository_identity": {
            "root": root.as_posix(),
            "name": root.name,
            "git_head": _git_head(root),
            "git_tree": _git_tree(root),
        },
        "repository_root_fingerprint": discovery_fingerprint,
        "created_from_git_head": _git_head(root),
        "discovery_fingerprint": discovery_fingerprint,
        "inputs": inputs,
        "discovery": {
            "evidence": evidence,
            "warnings": warnings,
            "repository_boundaries": boundaries,
        },
        "proposal": {
            "authority_candidates": authorities,
            "router_proposals": router_proposals,
            "testing_merge_proposal": testing_merge,
            "path_policy": path_policy,
            "blocking_decisions": blockers,
            "warnings": warnings,
        },
        "mutations": sorted(mutations, key=lambda item: item["path"]),
        "blocking_decisions": blockers,
        "warnings": warnings,
    }
    plan["plan_sha256"] = _plan_digest(plan)
    return plan


def _transaction_root(root: Path) -> Path:
    return root / ".work" / "bootstrap-transactions"


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_journal(path: Path, journal: dict[str, Any]) -> None:
    _atomic_write_bytes(
        path,
        (json.dumps(journal, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )


def _load_journal(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("invalid_transaction_journal")
    return value


def _incomplete_transactions(root: Path) -> list[str]:
    transaction_root = _transaction_root(root)
    if not transaction_root.is_dir():
        return []
    incomplete: list[str] = []
    for journal_path in sorted(transaction_root.glob("*/journal.json")):
        try:
            status = _load_journal(journal_path).get("status")
        except (OSError, ValueError, json.JSONDecodeError):
            status = "recovery_required"
        if status in {"prepared", "committing", "recovery_required"}:
            incomplete.append(journal_path.parent.name)
    return incomplete


def _mutation_is_applied(root: Path, mutation: dict[str, Any]) -> bool:
    target = root / mutation["path"]
    if mutation["operation"] == "create_directory":
        return target.is_dir()
    content = _read_bytes(target)
    return content is not None and sha256(content).hexdigest() == mutation["after_sha256"]


def _required_local_approvals(plan: dict[str, Any]) -> set[str]:
    approvals: set[str] = set()
    for mutation in plan.get("mutations", []):
        classes = [mutation.get("approval_class"), *mutation.get("additional_approval_classes", [])]
        for approval_class in classes:
            if isinstance(approval_class, str) and approval_class.startswith("local-only:"):
                approvals.add(approval_class.removeprefix("local-only:"))
    return approvals


def _validate_plan_mutations(root: Path, plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    mutations = plan.get("mutations")
    if not isinstance(mutations, list):
        return ["mutations_not_array"]
    for index, mutation in enumerate(mutations):
        if not isinstance(mutation, dict):
            errors.append(f"mutation_not_object:{index}")
            continue
        relative_path = mutation.get("path")
        if not isinstance(relative_path, str) or not relative_path:
            errors.append(f"mutation_path_invalid:{index}")
            continue
        if relative_path in seen:
            errors.append(f"mutation_path_duplicate:{relative_path}")
        seen.add(relative_path)
        target = root / relative_path
        reason = _unsafe_write_target(root, target)
        if reason:
            errors.append(f"mutation_path_unsafe:{relative_path}:{reason}")
        operation = mutation.get("operation")
        if operation not in {"create", "replace", "create_directory"}:
            errors.append(f"mutation_operation_invalid:{relative_path}")
        if operation != "create_directory":
            if not isinstance(mutation.get("after_content_base64"), str):
                errors.append(f"mutation_content_missing:{relative_path}")
            if not re.fullmatch(r"[0-9a-f]{64}", str(mutation.get("after_sha256", ""))):
                errors.append(f"mutation_after_hash_invalid:{relative_path}")
    return errors


def _prepare_transaction(root: Path, plan: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    transaction_id = uuid.uuid4().hex
    transaction_dir = _transaction_root(root) / transaction_id
    staging_dir = transaction_dir / "staging"
    try:
        staging_dir.mkdir(parents=True, exist_ok=False)
        operations: list[dict[str, Any]] = []
        for index, mutation in enumerate(plan["mutations"]):
            operation = dict(mutation)
            operation["state"] = "pending"
            target = root / mutation["path"]
            before = _read_bytes(target)
            operation["before_content_base64"] = (
                base64.b64encode(before).decode("ascii") if before is not None else None
            )
            if mutation["operation"] != "create_directory":
                content = base64.b64decode(mutation["after_content_base64"], validate=True)
                if sha256(content).hexdigest() != mutation["after_sha256"]:
                    raise ValueError(f"staged_hash_mismatch:{mutation['path']}")
                stage_path = staging_dir / f"{index:04d}.bin"
                _atomic_write_bytes(stage_path, content)
                operation["staging_path"] = stage_path.relative_to(transaction_dir).as_posix()
            operations.append(operation)
        journal = {
            "schema_version": 1,
            "transaction_id": transaction_id,
            "root": root.as_posix(),
            "plan_sha256": plan["plan_sha256"],
            "status": "prepared",
            "operations": operations,
        }
        journal_path = transaction_dir / "journal.json"
        _write_journal(journal_path, journal)
        return journal_path, journal
    except Exception:
        shutil.rmtree(transaction_dir, ignore_errors=True)
        raise


def _restore_transaction(
    root: Path,
    journal_path: Path,
    journal: dict[str, Any],
    *,
    inject_failure: bool = False,
) -> None:
    if inject_failure:
        raise RuntimeError("injected_rollback_failure")
    for operation in reversed(journal["operations"]):
        if operation.get("state") != "applied":
            continue
        target = root / operation["path"]
        if operation["operation"] == "create_directory":
            if target.is_dir():
                try:
                    target.rmdir()
                except OSError as error:
                    raise RuntimeError(f"rollback_directory_not_empty:{operation['path']}") from error
            operation["state"] = "rolled_back"
            _write_journal(journal_path, journal)
            continue
        current = _read_bytes(target)
        current_hash = sha256(current).hexdigest() if current is not None else None
        before_hash = operation["before_sha256"]
        after_hash = operation["after_sha256"]
        if current_hash == before_hash:
            operation["state"] = "rolled_back"
            _write_journal(journal_path, journal)
            continue
        if current_hash != after_hash:
            raise RuntimeError(f"rollback_ambiguous:{operation['path']}")
        before_base64 = operation.get("before_content_base64")
        if before_base64 is None:
            target.unlink(missing_ok=True)
        else:
            _atomic_write_bytes(target, base64.b64decode(before_base64, validate=True))
        operation["state"] = "rolled_back"
        _write_journal(journal_path, journal)
    journal["status"] = "rolled_back"
    _write_journal(journal_path, journal)


def _commit_transaction(
    root: Path,
    journal_path: Path,
    journal: dict[str, Any],
    *,
    fault_after_operation: int | None = None,
    fault_during_rollback: bool = False,
) -> str:
    transaction_dir = journal_path.parent
    journal["status"] = "committing"
    _write_journal(journal_path, journal)
    applied_count = 0
    try:
        for operation in journal["operations"]:
            target = root / operation["path"]
            reason = _unsafe_write_target(root, target)
            if reason:
                raise RuntimeError(f"unsafe_transaction_target:{operation['path']}:{reason}")
            if operation["operation"] == "create_directory":
                target.mkdir(parents=True, exist_ok=True)
            else:
                stage_path = transaction_dir / operation["staging_path"]
                content = stage_path.read_bytes()
                if sha256(content).hexdigest() != operation["after_sha256"]:
                    raise RuntimeError(f"staged_hash_drift:{operation['path']}")
                _atomic_write_bytes(target, content)
            operation["state"] = "applied"
            applied_count += 1
            _write_journal(journal_path, journal)
            if fault_after_operation is not None and applied_count == fault_after_operation:
                journal["failure_operation_index"] = applied_count
                _write_journal(journal_path, journal)
                raise RuntimeError(f"injected_failure_after_operation:{applied_count}")
    except Exception as error:
        journal["failure"] = str(error)
        try:
            _restore_transaction(
                root,
                journal_path,
                journal,
                inject_failure=fault_during_rollback,
            )
        except Exception as rollback_error:
            journal["status"] = "recovery_required"
            journal["rollback_failure"] = str(rollback_error)
            _write_journal(journal_path, journal)
            return "recovery_required"
        shutil.rmtree(transaction_dir / "staging", ignore_errors=True)
        return "rolled_back"
    journal["status"] = "committed"
    _write_journal(journal_path, journal)
    shutil.rmtree(transaction_dir / "staging", ignore_errors=True)
    return "committed"


def _must_be_committed(root: Path, plan: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for mutation in plan["mutations"]:
        if mutation["desired_state"] != "tracked":
            continue
        result = _git(root, "status", "--porcelain", "--", mutation["path"])
        if result.returncode == 0 and result.stdout.strip():
            paths.append(mutation["path"])
    return sorted(set(paths))


def apply_reconciliation_plan(
    root: Path,
    plan: dict[str, Any],
    approved_digest: str,
    approved_local_only: set[str],
) -> tuple[int, dict[str, Any]]:
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION or plan.get("mode") != "brownfield-reconcile":
        return 2, {"status": "unsupported_plan_schema"}
    actual_digest = _plan_digest(plan)
    if plan.get("plan_sha256") != actual_digest or approved_digest != actual_digest:
        return 3, {
            "status": "plan_digest_mismatch",
            "approved": approved_digest,
            "actual": actual_digest,
        }
    if plan.get("repository_identity", {}).get("root") != root.as_posix():
        return 2, {"status": "repository_identity_mismatch"}
    mutation_errors = _validate_plan_mutations(root, plan)
    if mutation_errors:
        return 2, {"status": "invalid_plan", "errors": mutation_errors}
    blockers = plan.get("blocking_decisions", [])
    if blockers:
        return 2, {"status": "blocking_decisions", "blocking_decisions": blockers}
    missing_approvals = sorted(_required_local_approvals(plan) - approved_local_only)
    if missing_approvals:
        return 3, {
            "status": "path_approval_required",
            "missing_local_only_approvals": missing_approvals,
        }
    incomplete = _incomplete_transactions(root)
    if incomplete:
        return 4, {"status": "incomplete_transaction", "transactions": incomplete}
    if all(_mutation_is_applied(root, mutation) for mutation in plan.get("mutations", [])):
        return 0, {
            "status": "already_applied",
            "plan_sha256": actual_digest,
            "mutation_count": 0,
        }
    current = build_reconciliation_plan(root)
    failed_preconditions: list[str] = []
    if current["discovery_fingerprint"] != plan.get("discovery_fingerprint"):
        failed_preconditions.append("discovery_fingerprint")
    if current["repository_identity"]["git_head"] != plan["repository_identity"].get("git_head"):
        failed_preconditions.append("git_head")
    if current["repository_identity"]["git_tree"] != plan["repository_identity"].get("git_tree"):
        failed_preconditions.append("git_tree")
    if failed_preconditions:
        return 2, {
            "status": "precondition_failed",
            "failed_preconditions": failed_preconditions,
        }
    try:
        journal_path, journal = _prepare_transaction(root, plan)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return 4, {"status": "transaction_prepare_failed", "error": str(error)}
    fault_value = os.environ.get("HARNESS_FAULT_AFTER_OPERATION")
    try:
        fault_after = int(fault_value) if fault_value else None
    except ValueError:
        fault_after = None
    transaction_status = _commit_transaction(
        root,
        journal_path,
        journal,
        fault_after_operation=fault_after,
        fault_during_rollback=os.environ.get("HARNESS_FAULT_DURING_ROLLBACK") == "1",
    )
    transaction_id = journal["transaction_id"]
    if transaction_status != "committed":
        return 4, {
            "status": transaction_status,
            "transaction_id": transaction_id,
            "plan_sha256": actual_digest,
        }
    verification_errors = validate(root)
    harness_ignore = _ignore_source(root, ".harness/project.yaml")
    if harness_ignore:
        verification_errors.append("tracked_harness_path_ignored")
    report = {
        "status": "applied" if not verification_errors else "applied_validation_failed",
        "transaction_id": transaction_id,
        "plan_sha256": actual_digest,
        "mutation_count": len(plan["mutations"]),
        "must_be_committed": _must_be_committed(root, plan),
        "verification": {"errors": list(dict.fromkeys(verification_errors))},
    }
    return (0 if not verification_errors else 5), report


def recover_transaction(root: Path, transaction_id: str) -> tuple[int, dict[str, Any]]:
    if not re.fullmatch(r"[0-9a-f]{32}", transaction_id):
        return 2, {"status": "invalid_transaction_id"}
    journal_path = _transaction_root(root) / transaction_id / "journal.json"
    try:
        journal = _load_journal(journal_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return 2, {"status": "transaction_not_found", "error": str(error)}
    if journal.get("root") != root.as_posix():
        return 2, {"status": "repository_identity_mismatch"}
    if journal.get("status") == "rolled_back":
        return 0, {"status": "rolled_back", "transaction_id": transaction_id}
    if journal.get("status") == "committed":
        return 2, {"status": "transaction_already_committed", "transaction_id": transaction_id}
    try:
        _restore_transaction(root, journal_path, journal)
    except Exception as error:
        journal["status"] = "recovery_required"
        journal["rollback_failure"] = str(error)
        _write_journal(journal_path, journal)
        return 4, {
            "status": "recovery_required",
            "transaction_id": transaction_id,
            "error": str(error),
        }
    shutil.rmtree(journal_path.parent / "staging", ignore_errors=True)
    return 0, {"status": "rolled_back", "transaction_id": transaction_id}


def _command_exists(root: Path, command: list[str]) -> bool:
    if not command or not all(isinstance(part, str) and part for part in command):
        return False
    executable = command[0]
    executable_path = Path(executable)
    if executable_path.is_absolute():
        return executable_path.is_file()
    if os.sep in executable or "/" in executable or "\\" in executable:
        candidate = (root / executable_path).absolute()
        try:
            resolved_root = root.resolve(strict=True)
            resolved = candidate.resolve(strict=True)
        except OSError:
            return False
        return (
            _within(resolved, resolved_root)
            and candidate.is_file()
            and _unsafe_write_target(root, candidate) is None
        )
    return shutil.which(executable) is not None


def _execution_command(root: Path, command: list[str]) -> list[str]:
    executable = Path(command[0])
    if executable.is_absolute() or not (
        os.sep in command[0] or "/" in command[0] or "\\" in command[0]
    ):
        return command
    resolved = str((root / executable).resolve(strict=True))
    normalized = [resolved, *command[1:]]
    if os.name == "nt" and Path(resolved).suffix.lower() in {".bat", ".cmd"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", *normalized]
    return normalized


def verify_commands(root: Path, encoded_commands: list[str]) -> dict[str, list[dict[str, Any]]]:
    recorded: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for encoded in encoded_commands:
        try:
            value = json.loads(encoded)
        except json.JSONDecodeError:
            rejected.append({"input": encoded, "reason": "invalid_json"})
            continue
        if not isinstance(value, list) or not _command_exists(root, value):
            rejected.append({"command": value, "reason": "command_not_found"})
            continue
        try:
            result = subprocess.run(
                _execution_command(root, value),
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            rejected.append({"command": value, "reason": "timeout"})
            continue
        evidence = {
            "command": value,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        if result.returncode == 0:
            recorded.append(evidence)
        else:
            evidence["reason"] = "nonzero_exit"
            rejected.append(evidence)
    return {"recorded": recorded, "rejected": rejected}


def _command_arrays(verification: dict[str, list[dict[str, Any]]]) -> list[list[str]]:
    return [item["command"] for item in verification["recorded"]]


def _render_commands_markdown(commands: list[list[str]]) -> str:
    if not commands:
        return "No verification command has been recorded."
    return "\n".join(f"- `{' '.join(command)}`" for command in commands)


def _render_commands_yaml(commands: list[list[str]]) -> str:
    if not commands:
        return "  commands: []"
    normalized = [[part.replace("\\", "/") for part in command] for command in commands]
    entries = "\n".join(
        f"    - {json.dumps(command, ensure_ascii=False)}" for command in normalized
    )
    return f"  commands:\n{entries}"


def desired_files(
    root: Path,
    classification: str,
    verification: dict[str, list[dict[str, Any]]],
) -> dict[str, bytes]:
    instruction = _instruction_content(root)
    commands = _command_arrays(verification)
    testing = _load_template("TESTING.md").replace(
        "{{VERIFICATION_COMMANDS}}", _render_commands_markdown(commands)
    )
    project = (
        _load_template("project.yaml")
        .replace("{{PROJECT_NAME}}", json.dumps(root.name, ensure_ascii=False))
        .replace("{{CLASSIFICATION}}", classification.lower())
        .replace("{{INSTRUCTION_SHA256}}", instruction_hash(instruction))
        .replace("{{VERIFICATION_COMMANDS}}", _render_commands_yaml(commands))
    )
    return {
        "AGENTS.md": instruction,
        "CLAUDE.md": instruction,
        "TESTING.md": testing.encode("utf-8"),
        ".harness/project.yaml": project.encode("utf-8"),
    }


def _text_diff(path: str, existing: bytes, proposed: bytes) -> str:
    old = existing.decode("utf-8", errors="replace").splitlines()
    new = proposed.decode("utf-8", errors="replace").splitlines()
    return "\n".join(
        difflib.unified_diff(
            old,
            new,
            fromfile=f"{path} (existing)",
            tofile=f"{path} (proposed)",
            lineterm="",
        )
    )


def build_plan(
    root: Path,
    verification: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    classification = classify(root)
    verification = verification or {"recorded": [], "rejected": []}
    desired = desired_files(root, classification, verification)
    changes: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    for relative_path, proposed in desired.items():
        existing = _read_bytes(root / relative_path)
        if existing is None:
            changes.append({"path": relative_path, "action": "create"})
        elif existing != proposed:
            conflicts.append(
                {
                    "path": relative_path,
                    "diff": _text_diff(relative_path, existing, proposed),
                }
            )
    gitignore = root / ".gitignore"
    ignored = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.is_file() else []
    if ".work/" not in ignored:
        changes.append(
            {"path": ".gitignore", "action": "append" if gitignore.is_file() else "create"}
        )
    for directory in (".work/active", ".work/archive", ".work/trash"):
        if not (root / directory).is_dir():
            changes.append({"path": directory, "action": "create_directory"})
    return {
        "classification": classification,
        "changes": changes,
        "conflicts": conflicts,
        "verification": verification,
        "desired": desired,
    }


def _public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in plan.items() if key != "desired"}


def apply_plan(root: Path, plan: dict[str, Any], *, containment_check: Any = _unsafe_targets) -> None:
    unsafe_targets = containment_check(root)
    if unsafe_targets:
        raise ValueError("unsafe_target_after_verification:" + json.dumps(unsafe_targets, sort_keys=True))
    for relative_path, content in plan["desired"].items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    gitignore = root / ".gitignore"
    current = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    if ".work/" not in current.splitlines():
        separator = "" if not current or current.endswith("\n") else "\n"
        gitignore.write_text(f"{current}{separator}.work/\n", encoding="utf-8", newline="\n")
    for directory in (".work/active", ".work/archive", ".work/trash"):
        (root / directory).mkdir(parents=True, exist_ok=True)


def _recorded_commands(config: str) -> list[list[str]]:
    commands: list[list[str]] = []
    in_commands = False
    for line in config.splitlines():
        if line.strip() == "commands:":
            in_commands = True
            continue
        if not in_commands:
            continue
        match = re.match(r"^\s{4}-\s+(\[.*\])\s*$", line)
        if match:
            try:
                value = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if isinstance(value, list):
                commands.append(value)
        elif line and not line.startswith("    "):
            break
    return commands


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    agents = _read_bytes(root / "AGENTS.md")
    claude = _read_bytes(root / "CLAUDE.md")
    config_path = root / ".harness/project.yaml"
    if agents is None:
        errors.append("missing_authoritative_instruction")
    if agents is None or claude is None or agents != claude:
        errors.append("instruction_mirror_drift")
    if not config_path.is_file():
        errors.append("missing_project_config")
        return errors
    config = config_path.read_text(encoding="utf-8")
    for key in REQUIRED_PROJECT_KEYS:
        if key not in config:
            errors.append(f"missing_project_key:{key}")
    if agents is not None and _config_sha(config) != instruction_hash(agents):
        errors.append("instruction_hash_drift")
    for command in _recorded_commands(config):
        if not _command_exists(root, command):
            errors.append("recorded_command_not_found")
    return list(dict.fromkeys(errors))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("plan", "validate"):
        command = subparsers.add_parser(action)
        command.add_argument("--root", type=Path, required=True)
    apply_command = subparsers.add_parser("apply")
    apply_command.add_argument("--root", type=Path, required=True)
    apply_command.add_argument("--approve", action="store_true")
    apply_command.add_argument("--verify-command-json", action="append", default=[])
    hash_command = subparsers.add_parser("hash")
    hash_command.add_argument("--root", type=Path, required=True)
    reconcile_command = subparsers.add_parser("reconcile")
    reconcile_command.add_argument("--root", type=Path, required=True)
    reconcile_command.add_argument("--report", type=Path)
    apply_plan_command = subparsers.add_parser("apply-plan")
    apply_plan_command.add_argument("--root", type=Path, required=True)
    apply_plan_command.add_argument("--plan", type=Path, required=True)
    apply_plan_command.add_argument("--approve-plan-sha256", required=True)
    apply_plan_command.add_argument("--approve-local-only", action="append", default=[])
    recover_command = subparsers.add_parser("recover-apply")
    recover_command.add_argument("--root", type=Path, required=True)
    recover_command.add_argument("--transaction", required=True)
    recover_command.add_argument("--approve-recovery", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.root.absolute()
    if args.action == "apply-plan":
        try:
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(json.dumps({"status": "invalid_plan", "error": str(error)}))
            return 2
        if not isinstance(plan, dict):
            print(json.dumps({"status": "invalid_plan"}))
            return 2
        code, payload = apply_reconciliation_plan(
            root,
            plan,
            args.approve_plan_sha256,
            set(args.approve_local_only),
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        return code
    if args.action == "recover-apply":
        if not args.approve_recovery:
            print(json.dumps({"status": "recovery_approval_required"}))
            return 3
        code, payload = recover_transaction(root, args.transaction)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        return code
    if args.action == "reconcile":
        if not root.is_dir():
            print(json.dumps({"status": "invalid_root", "root": str(root)}))
            return 2
        plan = build_reconciliation_plan(root)
        rendered = json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.report is not None:
            report = args.report.absolute()
            if not _within(report, root) or _unsafe_write_target(root, report):
                print(json.dumps({"status": "unsafe_report_path", "path": str(report)}))
                return 4
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(rendered, encoding="utf-8", newline="\n")
        print(rendered, end="")
        return 0
    if args.action == "hash":
        content = _read_bytes(root / "AGENTS.md")
        if content is None:
            print(json.dumps({"status": "missing", "path": "AGENTS.md"}))
            return 1
        print(json.dumps({"sha256": instruction_hash(content)}))
        return 0
    if args.action == "validate":
        errors = validate(root)
        print(json.dumps({"status": "valid" if not errors else "invalid", "errors": errors}))
        return 0 if not errors else 1
    if args.action == "plan":
        print(json.dumps(_public_plan(build_plan(root)), indent=2))
        return 0
    if not args.approve:
        print(json.dumps({"status": "approval_required"}))
        return 3
    unsafe_targets = _unsafe_targets(root)
    if unsafe_targets:
        print(
            json.dumps(
                {"status": "unsafe_target", "unsafe_targets": unsafe_targets},
                indent=2,
            )
        )
        return 4
    preliminary = build_plan(root)
    if preliminary["conflicts"]:
        payload = _public_plan(preliminary)
        payload["status"] = "conflict"
        print(json.dumps(payload, indent=2))
        return 2
    verification = verify_commands(root, args.verify_command_json)
    unsafe_targets = _unsafe_targets(root)
    if unsafe_targets:
        print(json.dumps({"status": "unsafe_target", "unsafe_targets": unsafe_targets}, indent=2))
        return 4
    plan = build_plan(root, verification)
    if plan["conflicts"]:
        payload = _public_plan(plan)
        payload["status"] = "conflict"
        print(json.dumps(payload, indent=2))
        return 2
    try:
        apply_plan(root, plan)
    except ValueError as error:
        print(json.dumps({"status": "unsafe_target", "errors": [str(error)]}, indent=2))
        return 4
    payload = _public_plan(plan)
    payload["status"] = "applied"
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
