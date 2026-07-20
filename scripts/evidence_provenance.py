"""Build revision-bound local verification evidence context."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


def _git(root: Path, *arguments: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _file_digest(path: Path) -> str | None:
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _dirty_paths(root: Path) -> list[str]:
    output = _git(root, "status", "--porcelain=v1", "--untracked-files=all") or ""
    paths: list[str] = []
    for line in output.splitlines():
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value.replace("\\", "/"))
    return sorted(paths)


def build_provenance(
    root: Path,
    *,
    command: list[str],
    source_type: str,
    source_package: str,
    result: str,
    unverified_checks: list[str] | None = None,
    providers: list[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    catalog = root / "distribution" / "catalog.json"
    resource_manifest = root / "authoring" / "public-resource-manifest.json"
    try:
        catalog_value = json.loads(catalog.read_text(encoding="utf-8"))
        public_skill_count = len(catalog_value.get("public_skills", []))
    except (OSError, json.JSONDecodeError, AttributeError):
        public_skill_count = None
    dirty_paths = _dirty_paths(root)
    git_version = subprocess.run(
        ["git", "--version"], capture_output=True, text=True, check=False
    ).stdout.strip()
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": root.name,
        "git_commit": _git(root, "rev-parse", "HEAD"),
        "git_tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "git_dirty": bool(dirty_paths),
        "dirty_paths": dirty_paths,
        "branch": _git(root, "branch", "--show-current"),
        "command": command,
        "cwd": root.as_posix(),
        "tool_versions": {
            "python": sys.version.split()[0],
            "git": git_version,
        },
        "source_type": source_type,
        "source_package": source_package,
        "providers": providers or [],
        "public_skill_count": public_skill_count,
        "catalog_sha256": _file_digest(catalog),
        "resource_manifest_sha256": _file_digest(resource_manifest),
        "result": result,
        "unverified_checks": unverified_checks or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--command-json")
    parser.add_argument("--command-part", action="append", default=[])
    parser.add_argument("--command-part-base64", action="append", default=[])
    parser.add_argument("--source-type", required=True)
    parser.add_argument("--source-package", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--unverified-check", action="append", default=[])
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()
    encoded_command = [
        base64.b64decode(item, validate=True).decode("utf-8")
        for item in args.command_part_base64
    ]
    command = encoded_command or args.command_part or (
        json.loads(args.command_json) if args.command_json is not None else None
    )
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise SystemExit("--command-json must encode an array of strings")
    print(
        json.dumps(
            build_provenance(
                args.repository_root,
                command=command,
                source_type=args.source_type,
                source_package=args.source_package,
                result=args.result,
                unverified_checks=args.unverified_check,
                providers=args.provider,
            ),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
