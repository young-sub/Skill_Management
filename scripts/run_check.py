"""Capture a finite, foreground check. Output is evidence to inspect, never a verdict."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import signal
from pathlib import Path
import subprocess
import time
import uuid


from unittest_evidence import git_identity


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Use argv after --. Do not pass secrets or launch background services. Inspect runner counts/skips and behavior independently. Output must be a new file.')
    parser.add_argument('--cwd', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--feature', help='Optional project-owned Feature ID')
    parser.add_argument('--also-feature', action='append', default=[], help='Additional preselected consumer of this same check')
    parser.add_argument('--check', help='Optional project-owned command ID')
    parser.add_argument('--json-report', type=Path, help='New native JSON report path (relative to cwd); embed after execution, without assigning a verdict. Must contain no secrets.')
    parser.add_argument('--timeout', type=float, default=300, help='Seconds before stopping the owned process tree (default: 300)')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not argv or not args.cwd.is_dir() or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('A command and existing working directory are required')
    if args.also_feature and (not args.feature or not args.check or any(not name.strip() for name in args.also_feature)):
        parser.error('Shared capture requires nonempty Feature and check IDs')
    cwd = args.cwd.resolve()
    report = (cwd / args.json_report).absolute() if args.json_report else None
    if report:
        if report.exists() or report.is_symlink() or report == args.output.resolve():
            parser.error('Native JSON report must be a new path distinct from evidence')
        report.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve first: an old result can neither be overwritten nor mistaken for this run.
    with args.output.open('x', encoding='utf-8') as stream:
        record = {'run_id': str(uuid.uuid4()), 'feature': args.feature, 'check': args.check,
                  'argv': argv, 'cwd': str(cwd), 'started_at': datetime.now(timezone.utc).isoformat(),
                  'before': git_identity(cwd), 'behavior_verdict': None}
        if args.also_feature:
            record['shared_features'] = list(dict.fromkeys([args.feature, *args.also_feature]))
        start = time.monotonic()
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', start_new_session=os.name != 'nt')
            try:
                stdout, stderr = process.communicate(timeout=args.timeout)
                record.update(execution='exited', exit_code=process.returncode, stdout=stdout, stderr=stderr)
                code = process.returncode
            except subprocess.TimeoutExpired:
                cleanup_exit = None
                if process.poll() is None:
                    if os.name == 'nt':
                        cleanup_exit = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True).returncode
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                        cleanup_exit = 0
                    if process.poll() is None:
                        process.kill()
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired as error:
                    # A detached descendant may still hold a pipe; never wait forever or claim cleanup.
                    stdout = error.output or b''
                    stderr = error.stderr or b''
                    stdout = stdout.decode('utf-8', errors='replace') if isinstance(stdout, bytes) else stdout
                    stderr = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else stderr
                    record['cleanup_incomplete'] = True
                record.update(execution='timeout', exit_code=None, stdout=stdout, stderr=stderr, timeout_tree_cleanup_exit=cleanup_exit)
                code = 124
        except OSError as error:
            record.update(execution='unavailable', exit_code=None, stdout='', stderr=str(error))
            code = 127
        record.update(elapsed_seconds=time.monotonic() - start, after=git_identity(cwd))
        if report:
            captured = {'path': str(report.resolve()), 'sha256': None, 'data': None, 'error': None}
            try:
                if report.is_symlink():
                    raise ValueError('Native report became a symlink')
                raw = report.read_bytes()
                captured['sha256'] = hashlib.sha256(raw).hexdigest()
                captured['data'] = json.loads(raw)
            except (OSError, ValueError) as error:
                captured['error'] = str(error)
            record['json_report'] = captured
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'run_id': record['run_id'], 'execution': record['execution'], 'exit_code': record['exit_code'], 'evidence': str(args.output.resolve()), 'behavior_verdict': None}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
