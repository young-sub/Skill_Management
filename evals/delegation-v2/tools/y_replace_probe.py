"""Apply or reverse one exact scenario probe, requiring a unique match."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario_file", type=Path)
    parser.add_argument("scenario_id")
    parser.add_argument("probe_name", nargs="?")
    parser.add_argument("repository", type=Path)
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--fault", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.scenario_file.read_text(encoding="utf-8"))
    scenario = next(item for item in data["scenarios"] if item["id"] == args.scenario_id)
    if args.fault:
        probe = scenario["fault"]
    else:
        if not args.probe_name:
            parser.error("probe_name is required unless --fault is used")
        probe = next(item for item in scenario["probes"] if item["name"] == args.probe_name)
    target = args.repository / probe["file"]
    original, replacement = probe["find"], probe["replace"]
    before, after = (replacement, original) if args.reverse else (original, replacement)
    content = target.read_text(encoding="utf-8")
    count = content.count(before)
    print(f"{probe.get('name', 'fault')}: exact matches={count} file={probe['file']}")
    if count != 1:
        raise SystemExit(f"expected exactly one match; found {count}")
    target.write_text(content.replace(before, after, 1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
