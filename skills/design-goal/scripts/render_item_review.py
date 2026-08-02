# Generated file. Do not edit directly.
# Source: authoring/scripts/render_item_review.py
# Source-SHA256: 58ad47225af59cd1188e13a99142121167ab2ac083d68b98fb3e3d8ddf892028

#!/usr/bin/env python3
"""Render the Korean Item-based Design Review from contract.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from core_harness import render_design_review_v3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        page = render_design_review_v3(contract)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(page, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
