"""Run one verification command and retain its combined output and timing."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 4:
        raise SystemExit("usage: y_run.py REPOSITORY LOG COMMAND [ARG ...]")
    repository = Path(sys.argv[1]).resolve()
    log = Path(sys.argv[2]).resolve()
    command = sys.argv[3:]
    log.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.perf_counter() - started
    log.write_text(
        "$ " + subprocess.list2cmdline(command) + "\n"
        + result.stdout
        + f"\nEXIT_CODE={result.returncode}\nRUNTIME_SECONDS={elapsed:.3f}\n",
        encoding="utf-8",
    )
    print(f"{log} exit={result.returncode} runtime={elapsed:.3f}s")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
