# Generated file. Do not edit directly.
# Source: authoring/scripts/bootstrap_project.py
# Source-SHA256: 7780227d20c7657ef230363daf188309d3a1f81c5ef94d1f15368bbb75a9d96e

"""Deterministic project bootstrap planner, applier, and validator."""

from __future__ import annotations

import argparse
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


CLASSIFICATIONS = {
    "NEW_UNCONFIGURED",
    "EXISTING_PARTIAL",
    "EXISTING_OVERGROWN",
    "DRIFT_REPAIR",
}
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


def _command_exists(command: list[str]) -> bool:
    if not command or not all(isinstance(part, str) and part for part in command):
        return False
    executable = command[0]
    if Path(executable).is_absolute() or os.sep in executable or "/" in executable:
        return Path(executable).is_file()
    return shutil.which(executable) is not None


def verify_commands(root: Path, encoded_commands: list[str]) -> dict[str, list[dict[str, Any]]]:
    recorded: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for encoded in encoded_commands:
        try:
            value = json.loads(encoded)
        except json.JSONDecodeError:
            rejected.append({"input": encoded, "reason": "invalid_json"})
            continue
        if not isinstance(value, list) or not _command_exists(value):
            rejected.append({"command": value, "reason": "command_not_found"})
            continue
        try:
            result = subprocess.run(
                value,
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


def apply_plan(root: Path, plan: dict[str, Any]) -> None:
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
        if not _command_exists(command):
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
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.root.resolve()
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
    preliminary = build_plan(root)
    if preliminary["conflicts"]:
        payload = _public_plan(preliminary)
        payload["status"] = "conflict"
        print(json.dumps(payload, indent=2))
        return 2
    verification = verify_commands(root, args.verify_command_json)
    plan = build_plan(root, verification)
    if plan["conflicts"]:
        payload = _public_plan(plan)
        payload["status"] = "conflict"
        print(json.dumps(payload, indent=2))
        return 2
    apply_plan(root, plan)
    payload = _public_plan(plan)
    payload["status"] = "applied"
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
