# Generated file. Do not edit directly.
# Source: authoring/scripts/render_design_review.py
# Source-SHA256: f36ecc12ada7182001cd0148907d463f4fd5ac753d58ad50b2288d7c8357090f

#!/usr/bin/env python3
"""Render a scriptless, escaped Design Review from a validated contract."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
import sys

from contract_engine import contract_paths, load_contract, validate_documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()
    documents, errors = load_contract(root)
    validation_errors, _ = validate_documents(documents, root, None)
    errors.extend(validation_errors)
    if errors:
        print(";".join(sorted(set(errors))), file=sys.stderr)
        return 2
    cards = []
    for path in contract_paths(root):
        if path.is_file() and path.name not in {"RESULT.md", "BLOCKED.md"}:
            relative = path.relative_to(root).as_posix()
            source = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
            cards.append(
                '<section class="contract"><h2>'
                + html.escape(relative)
                + "</h2><pre>"
                + html.escape(source)
                + "</pre></section>"
            )
    template_path = Path(__file__).resolve().parents[1] / "templates" / "design-review.html"
    template = template_path.read_text(encoding="utf-8")
    page = template.replace("{{WORK_ID}}", html.escape(documents[0].metadata["work_id"]))
    page = page.replace("{{CONTRACT_CONTENT}}", "\n".join(cards))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
