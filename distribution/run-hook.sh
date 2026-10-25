#!/bin/sh
# Probe the interpreter, not the hook: hook failures must never trigger a retry.
for python in python3 python; do
    if "$python" -c 'import sys; sys.exit(sys.version_info.major != 3)' >/dev/null 2>&1; then
        exec "$python" -c 'import os,runpy,sys; runpy.run_path(os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ["PLUGIN_ROOT"],"hooks",sys.argv[1]),run_name="__main__")' "$1"
    fi
done
printf '%s\n' 'agentic-coding: Python 3 is required (python3 or python on PATH).' >&2
exit 127
