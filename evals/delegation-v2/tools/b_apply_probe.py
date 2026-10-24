import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 5 or sys.argv[1] not in {"apply", "restore"}:
        raise SystemExit("usage: b_apply_probe.py apply|restore CLONE SCENARIO PROBE")
    action, clone, scenario_id, probe_name = sys.argv[1:]
    suite = Path(__file__).resolve().parents[1]
    scenarios = json.loads((suite / "scenarios-labeler-b.json").read_text(encoding="utf-8"))
    scenario = next(item for item in scenarios["scenarios"] if item["id"] == scenario_id)
    probe = next(item for item in scenario["probes"] if item["name"] == probe_name)
    path = Path(clone) / probe["file"]
    raw = path.read_bytes()
    find = probe["find"].encode("utf-8")
    replace = probe["replace"].encode("utf-8")
    old, new = (find, replace) if action == "apply" else (replace, find)
    count = raw.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one target in {path}, found {count}")
    path.write_bytes(raw.replace(old, new, 1))
    print(f"{action} {scenario_id}/{probe_name}: exact_match_count={count}")


if __name__ == "__main__":
    main()
