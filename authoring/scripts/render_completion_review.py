#!/usr/bin/env python3
"""Render an escaped, scriptless Completion Review."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import sys
from typing import Any


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected_object")
    return value


def template_path() -> Path:
    root = Path(__file__).resolve().parents[1] / "templates"
    canonical = root / "review" / "completion-review.html"
    return canonical if canonical.is_file() else root / "completion-review.html"


def render_review(
    *, work_id: str, objective: str, result_markdown: str,
    findings: list[dict[str, Any]], checks: list[dict[str, Any]], template: Path,
) -> str:
    finding_rows = "".join(
        "<tr><td>" + html.escape(str(item.get("severity", "Unknown"))) + "</td><td>"
        + html.escape(str(item.get("title", item.get("message", "")))) + "</td></tr>"
        for item in findings
    ) or '<tr><td colspan="2">None</td></tr>'
    check_rows = "".join(
        "<tr><td>" + html.escape(str(item.get("kind", "Unknown"))) + "</td><td>"
        + html.escape(str(item.get("status", "unknown"))) + "</td></tr>"
        for item in checks
    )
    replacements = {
        "{{WORK_ID}}": html.escape(work_id),
        "{{OBJECTIVE}}": html.escape(objective),
        "{{FINDINGS}}": finding_rows,
        "{{VERIFICATION}}": check_rows,
        "{{RESULT_MARKDOWN}}": html.escape(result_markdown),
    }
    page = template.read_text(encoding="utf-8")
    for marker, value in replacements.items():
        page = page.replace(marker, value)
    return page.rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-id", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        findings = _object(args.findings).get("findings", [])
        checks = _object(args.verification).get("checks", [])
        if not isinstance(findings, list) or not isinstance(checks, list):
            raise ValueError("expected_lists")
        template = template_path()
        page = render_review(
            work_id=args.work_id, objective=args.objective,
            result_markdown=args.result.read_text(encoding="utf-8"),
            findings=findings, checks=checks, template=template,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(page, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
