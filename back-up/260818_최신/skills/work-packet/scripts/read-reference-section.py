#!/usr/bin/env python3
"""Print one section from work-packet REFERENCE.md by heading or anchor."""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Force UTF-8 stdout so non-ASCII section content (em-dashes, Korean, etc.) prints on
# consoles with a legacy code page (e.g. cp949 on Korean Windows) instead of crashing.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "REFERENCE.md"


def slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def section_for(anchor: str, text: str) -> str | None:
    wanted = slug(anchor.lstrip("#"))
    lines = text.splitlines()
    start: int | None = None
    start_level: int | None = None

    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        if slug(title) == wanted:
            start = index
            start_level = level
            break

    if start is None or start_level is None:
        return None

    end = len(lines)
    for index in range(start + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s+", lines[index])
        if match and len(match.group(1)) <= start_level:
            end = index
            break
    return "\n".join(lines[start:end]).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: read-reference-section.py <heading-or-anchor>", file=sys.stderr)
        return 2
    text = REFERENCE.read_text(encoding="utf-8")
    section = section_for(argv[1], text)
    if section is None:
        print(f"Section not found: {argv[1]}", file=sys.stderr)
        return 1
    print(section, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
