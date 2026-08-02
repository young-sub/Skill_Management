# Generated file. Do not edit directly.
# Source: authoring/scripts/render_result_review.py
# Source-SHA256: e9d615c7a85d6b0ac5dabb5b3066663c1fa58ef352801b41bc931f1a78686736

#!/usr/bin/env python3
"""Render the Korean Item-based Result Review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from core_harness import render_result_review_v3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        result = json.loads(args.result.read_text(encoding="utf-8"))
        page = render_result_review_v3(contract, result)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(page, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
