"""Capture a finite, foreground check. Output is evidence to inspect, never a verdict."""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import signal
from pathlib import Path
import subprocess
import tempfile
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
    parser.add_argument('--stdin-file', type=Path, help='Non-secret UTF-8 input file, relative to cwd; pass exact bytes without shell text transcoding')
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
    input_bytes = None
    if args.stdin_file:
        input_path = (cwd / args.stdin_file).resolve()
        try:
            input_bytes = input_path.read_bytes()
            input_bytes.decode('utf-8', errors='strict')
        except (OSError, UnicodeError) as error:
            parser.error(f'Cannot read UTF-8 stdin file: {error}')
    report = (cwd / args.json_report).absolute() if args.json_report else None
    if report:
        if report.exists() or report.is_symlink() or report == args.output.resolve():
            parser.error('Native JSON report must be a new path distinct from evidence')
        report.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve first: an old result can neither be overwritten nor mistaken for this run.
    with args.output.open('x', encoding='utf-8') as stream, \
            (tempfile.TemporaryFile() if input_bytes is not None else nullcontext()) as input_stream:
        record = {'run_id': str(uuid.uuid4()), 'feature': args.feature, 'check': args.check,
                  'argv': argv, 'cwd': str(cwd), 'started_at': datetime.now(timezone.utc).isoformat(),
                  'behavior_verdict': None}
        if input_stream is not None:
            # Snapshot bytes before launch; ambient PowerShell encoding cannot alter this input.
            input_stream.write(input_bytes)
            input_stream.seek(0)
            record['stdin_file'] = {'path': str(input_path), 'bytes': len(input_bytes),
                                    'sha256': hashlib.sha256(input_bytes).hexdigest()}
        if args.also_feature:
            record['shared_features'] = list(dict.fromkeys([args.feature, *args.also_feature]))
        record.update(execution='running', exit_code=None, capture_pid=os.getpid(),
                      progress='Wait for this capture to finish; do not launch the command again. '
                               'If the owner exited, the outcome is unknown until reconciled.')
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
        record['before'] = git_identity(cwd)
        start = time.monotonic()
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=input_stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', start_new_session=os.name != 'nt')
            try:
                stdout, stderr = process.communicate(timeout=args.timeout)
                record.update(execution='exited', exit_code=process.returncode, stdout=stdout, stderr=stderr)
                code = process.returncode
            except subprocess.TimeoutExpired:
                cleanup = {'command': None, 'status': 'not_attempted', 'exit_code': None,
                           'stdout': '', 'stderr': ''}
                if process.poll() is None:
                    cleanup['command'] = (['taskkill', '/PID', str(process.pid), '/T', '/F']
                                          if os.name == 'nt' else
                                          ['os.killpg', str(process.pid), 'SIGKILL'])
                    try:
                        if os.name == 'nt':
                            result = subprocess.run(
                                cleanup['command'], capture_output=True, text=True,
                                encoding='utf-8', errors='replace',
                            )
                            cleanup.update(
                                status='succeeded' if result.returncode == 0 else 'failed',
                                exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
                            )
                        else:
                            os.killpg(process.pid, signal.SIGKILL)
                            cleanup.update(status='succeeded', exit_code=0)
                    except OSError as error:
                        cleanup.update(status='failed', error=str(error))
                    if process.poll() is None:
                        try:
                            process.kill()
                        except OSError as error:
                            cleanup['status'] = 'failed'
                            cleanup['error'] = '; '.join(filter(None, (
                                cleanup.get('error'), f'process.kill: {error}')))
                    if cleanup['status'] == 'failed':
                        record['cleanup_incomplete'] = True
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired as error:
                    # A detached descendant may still hold a pipe; never wait forever or claim cleanup.
                    stdout = error.output or b''
                    stderr = error.stderr or b''
                    stdout = stdout.decode('utf-8', errors='replace') if isinstance(stdout, bytes) else stdout
                    stderr = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else stderr
                    record['cleanup_incomplete'] = True
                except OSError as error:
                    stdout, stderr = '', ''
                    cleanup['pipe_drain_error'] = str(error)
                    record['cleanup_incomplete'] = True
                record.update(
                    execution='timeout', exit_code=None, stdout=stdout, stderr=stderr,
                    timeout_tree_cleanup_exit=cleanup['exit_code'], timeout_tree_cleanup=cleanup,
                )
                code = 124
        except OSError as error:
            record.update(execution='unavailable', exit_code=None, stdout='', stderr=str(error))
            code = 127
        record.pop('progress', None)
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
        # Publish completion atomically: readers see either progress or the whole result.
        stream.close()
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=args.output.parent,
                    prefix=args.output.name + '.', suffix='.pending', delete=False) as final:
                temporary = Path(final.name)
                json.dump(record, final, ensure_ascii=False, indent=2)
                final.write('\n')
                final.flush()
                os.fsync(final.fileno())
            temporary.replace(args.output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    print(json.dumps({'run_id': record['run_id'], 'execution': record['execution'], 'exit_code': record['exit_code'], 'evidence': str(args.output.resolve()), 'behavior_verdict': None}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
