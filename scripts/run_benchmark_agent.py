"""Capture fresh Codex app-server threads under one enforced wall-clock budget.

Keep this controller outside the candidate's external sandbox. It records native discovery
and hook events; neither their presence nor a completed turn is task acceptance.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import tempfile

from evaluate_benchmark import InputError, _sha256


def _save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def _usage(phases):
    totals = [p.get('usage') for p in phases]
    keys = ('inputTokens', 'cachedInputTokens', 'outputTokens', 'reasoningOutputTokens', 'totalTokens')
    if not totals or any(not isinstance(t, dict) or any(
            isinstance(t.get(k), bool) or not isinstance(t.get(k), int) or t[k] < 0
            for k in keys) for t in totals):
        return None
    return {k: sum(t[k] for t in totals) for k in keys}


def _patch(cwd, base, destination):
    artifact = {'path': None, 'sha256': None, 'base_commit': base, 'error': None}
    if not base:
        artifact['error'] = 'candidate_not_git'
        return artifact
    try:
        with tempfile.TemporaryDirectory(prefix='benchmark-index-') as temporary:
            environment = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
            def git(*args):
                return subprocess.check_output(['git', '-C', str(cwd), *args], env=environment,
                                               stderr=subprocess.PIPE)
            git('read-tree', base)
            git('add', '--all', '--', '.')
            raw = git('diff', '--cached', '--binary', base, '--')
            with destination.open('xb') as stream:
                stream.write(raw)
        artifact.update(path=str(destination), sha256=_sha256(destination))
    except (OSError, subprocess.CalledProcessError) as error:
        artifact['error'] = str(error)
    return artifact


def _snapshot(cwd, base=None):
    try:
        head = subprocess.check_output(['git', '-C', str(cwd), 'rev-parse', 'HEAD'],
                                       stderr=subprocess.PIPE).decode().strip()
    except subprocess.CalledProcessError:
        head = None
    result = {'head': head, 'patch': None, 'error': None}
    if base:
        with tempfile.TemporaryDirectory(prefix='benchmark-patch-') as temporary:
            destination = Path(temporary) / 'candidate.diff'
            artifact = _patch(cwd, base, destination)
            result['error'] = artifact['error']
            if destination.is_file():
                result['patch'] = base64.b64encode(destination.read_bytes()).decode('ascii')
    return result


def _candidate_snapshot(manifest, base=None):
    if not manifest.get('snapshot_argv'):
        return _snapshot(Path(manifest['cwd']), base)
    # Transport and helper are controller-owned; all candidate Git executes inside its sandbox.
    argv = [*manifest['snapshot_argv'], '--snapshot', manifest.get('server_cwd', manifest['cwd'])]
    if base:
        argv += ['--base', base]
    return json.loads(subprocess.check_output(argv, cwd=Path(__file__).parent, timeout=30,
                                             stderr=subprocess.PIPE))


def _session(manifest_path, output):
    manifest = json.loads(manifest_path.read_bytes())
    record = json.loads(output.read_bytes())
    server_cwd = manifest.get('server_cwd', manifest['cwd'])
    process = None
    messages = queue.Queue()
    request_id = 0
    trace_path = Path(record['trace']['path'])
    stderr_path = output.with_name(output.name + '.server-stderr.txt')
    try:
        with trace_path.open('x', encoding='utf-8') as trace, stderr_path.open('x', encoding='utf-8') as stderr:
            environment = os.environ.copy()
            environment.update(manifest.get('environment', {}))
            process = subprocess.Popen(manifest['server_argv'], cwd=manifest['cwd'], env=environment,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                       text=True, encoding='utf-8', errors='replace')

            def receive():
                for line in process.stdout:
                    messages.put(line)
                messages.put(None)

            threading.Thread(target=receive, daemon=True).start()

            def log(direction, message):
                trace.write(json.dumps({'at': datetime.now(timezone.utc).isoformat(),
                                        'direction': direction, 'message': message}, ensure_ascii=False) + '\n')
                trace.flush()

            def send(method, params, notification=False):
                nonlocal request_id
                request_id += 1
                message = {'method': method, 'params': params}
                if not notification:
                    message['id'] = request_id
                log('send', message)
                process.stdin.write(json.dumps(message) + '\n')
                process.stdin.flush()
                return request_id

            def next_message():
                while True:
                    try:
                        line = messages.get(timeout=.1)
                        break
                    except queue.Empty:
                        phase = record['phases'][-1] if record['phases'] else {}
                        trigger = phase.get('interrupt_when_file')
                        if trigger and phase.get('turn_id') and not phase.get('interruption'):
                            path = (Path(manifest['cwd']) / trigger).resolve()
                            if not path.is_relative_to(Path(manifest['cwd']).resolve()):
                                raise InputError('interrupt trigger escaped candidate cwd')
                            if path.is_file():
                                phase['interruption'] = {'trigger': trigger, 'trigger_sha256': _sha256(path),
                                                         'requested_at': datetime.now(timezone.utc).isoformat()}
                                _save(output, record)
                                send('turn/interrupt', {'threadId': phase['thread_id'], 'turnId': phase['turn_id']})
                if line is None:
                    raise InputError(f'app_server_closed: {process.poll()}')
                message = json.loads(line)
                log('receive', message)
                if 'id' in message and 'method' in message:
                    raise InputError(f'unexpected_server_request: {message["method"]}')
                if message.get('method') == 'thread/tokenUsage/updated':
                    params = message['params']
                    for phase in record['phases']:
                        if phase.get('thread_id') == params.get('threadId'):
                            phase['usage'] = params.get('tokenUsage', {}).get('total')
                            _save(output, record)
                return message

            def request(method, params):
                identifier = send(method, params)
                while True:
                    message = next_message()
                    if message.get('id') == identifier:
                        if 'error' in message:
                            raise InputError(f'{method}: {message["error"]}')
                        return message['result']

            record['initialize'] = request('initialize', {
                'clientInfo': {'name': 'skill-benchmark', 'version': '1'},
                'capabilities': {'experimentalApi': True}})
            send('initialized', {}, notification=True)
            record['discovery'] = {
                'skills': request('skills/list', {'cwds': [server_cwd], 'forceReload': True}),
                'hooks': request('hooks/list', {'cwds': [server_cwd]}),
            }
            _save(output, record)
            for specification in manifest['phases']:
                phase = {'id': specification['id'], 'status': 'starting', 'usage': None,
                         'interrupt_when_file': specification.get('interrupt_when_file')}
                record['phases'].append(phase)
                _save(output, record)
                started = request('thread/start', {
                    'cwd': server_cwd, 'model': manifest['model'],
                    'approvalPolicy': 'never', 'sandbox': manifest.get('sandbox', 'read-only'),
                    'config': {'model_reasoning_effort': manifest['reasoning_effort'],
                               'features.multi_agent': False, 'features.memories': False},
                })
                phase.update(thread_id=started['thread']['id'], actual_model=started.get('model'),
                             actual_reasoning_effort=started.get('reasoningEffort'),
                             thread_start=started)
                _save(output, record)
                if (phase['actual_model'], phase['actual_reasoning_effort']) != (
                        manifest['model'], manifest['reasoning_effort']):
                    raise InputError('model_or_reasoning_mismatch')
                # Persist before sending: interruption leaves an unknown effect, never a safe retry.
                phase['status'] = 'unknown'
                _save(output, record)
                turn = request('turn/start', {
                    'threadId': phase['thread_id'], 'model': manifest['model'],
                    'effort': manifest['reasoning_effort'],
                    'input': [{'type': 'text', 'text': specification['prompt'], 'text_elements': []}],
                })
                phase['turn_id'] = turn['turn']['id']
                while True:
                    message = next_message()
                    if (message.get('method') == 'turn/completed' and
                            message.get('params', {}).get('threadId') == phase['thread_id']):
                        phase['turn'] = message['params']['turn']
                        phase['status'] = phase['turn']['status']
                        _save(output, record)
                        if phase['status'] != 'completed' and not (
                                phase['status'] == 'interrupted' and phase.get('interruption')):
                            raise InputError(f'turn_{phase["status"]}: {phase["turn"].get("error")}')
                        break
            record['execution'] = 'completed'
    except (OSError, ValueError, KeyError) as error:
        record.update(execution='failed', error=str(error))
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            record['server_exit_code'] = process.returncode
        record['usage'] = _usage(record['phases'])
        record['usage_complete'] = record['usage'] is not None and len(record['phases']) == len(manifest['phases'])
        _save(output, record)
    return 0 if record['execution'] == 'completed' else 2


def run(manifest_path, output):
    manifest_path = manifest_path.resolve()
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    if manifest.get('format') != 'codex-benchmark-agent-v1':
        raise InputError('invalid agent manifest format')
    if (manifest.get('model'), manifest.get('reasoning_effort')) != ('gpt-6-luna', 'medium'):
        raise InputError('benchmark requires gpt-6-luna / medium')
    if manifest.get('condition') not in ('A', 'B', 'C'):
        raise InputError('condition must be A, B or C')
    timeout = manifest.get('timeout_seconds')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise InputError('positive finite timeout_seconds required')
    phases = manifest.get('phases')
    if (not isinstance(phases, list) or not phases or any(
            not isinstance(p, dict) or not isinstance(p.get('id'), str) or not p['id'] or
            not isinstance(p.get('prompt'), str) or not p['prompt'].strip() for p in phases) or
            len({p['id'] for p in phases}) != len(phases)):
        raise InputError('unique phases with nonempty id and prompt required')
    argv = manifest.get('server_argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(v, str) or not v for v in argv):
        raise InputError('server_argv required')
    cwd = Path(manifest['cwd']).resolve()
    if not cwd.is_dir():
        raise InputError('candidate cwd missing')
    output = output.absolute()
    if manifest.get('server_cwd'):
        if not manifest.get('snapshot_argv'):
            raise InputError('remote execution requires sandboxed snapshot_argv; host Git is forbidden')
        if output.resolve().is_relative_to(cwd):
            raise InputError('remote evidence must stay outside candidate cwd')
    capture = output.with_name(output.name + '.run-check.json')
    trace = output.with_name(output.name + '.trace.jsonl')
    patch = output.with_name(output.name + '.patch.diff')
    for path in (output, capture, trace, patch, output.with_name(output.name + '.server-stderr.txt')):
        if path.exists() or path.is_symlink():
            raise InputError(f'result path already exists: {path}')
    record = {
        'format': 'codex-benchmark-agent-result-v1', 'task_id': manifest['task_id'],
        'condition': manifest['condition'], 'execution': 'launching', 'error': None,
        'manifest': {'path': str(manifest_path), 'sha256': hashlib.sha256(raw).hexdigest(), 'data': manifest},
        'started_at': datetime.now(timezone.utc).isoformat(), 'phases': [],
        'budget': {'enforced_wall_seconds': timeout, 'token_limit_enforced': False,
                   'scope': 'all phases and local descendant processes; run inside the external candidate sandbox'},
        'usage': None, 'usage_complete': False, 'cost_usd': None, 'credits': None,
        'behavior_verdict': None, 'trace': {'path': str(trace), 'sha256': None},
    }
    record['candidate_before'] = _candidate_snapshot(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(record, stream)
    command = [sys.executable, str(Path(__file__).with_name('run_check.py')), '--cwd', str(output.parent),
               '--output', str(capture), '--timeout', str(timeout), '--', sys.executable,
               str(Path(__file__).resolve()), '--session', '--manifest', str(manifest_path), '--output', str(output)]
    start = time.monotonic()
    subprocess.run(command, check=False, stdin=subprocess.DEVNULL)
    record = json.loads(output.read_bytes())
    captured = json.loads(capture.read_bytes())
    record['capture'] = {'path': str(capture), 'sha256': _sha256(capture), 'data': captured}
    if captured['execution'] != 'exited':
        record['execution'] = captured['execution']
        record['usage_complete'] = False
    elif captured['exit_code'] != 0 and record['execution'] == 'launching':
        record['execution'] = 'failed'
    record['elapsed_seconds'] = time.monotonic() - start
    record['usage'] = _usage(record['phases'])
    record['usage_complete'] = record['usage_complete'] and record['usage'] is not None
    if trace.is_file():
        record['trace']['sha256'] = _sha256(trace)
    base = record['candidate_before']['head']
    artifact = {'path': None, 'sha256': None, 'base_commit': base, 'error': None}
    try:
        snapshot = _candidate_snapshot(manifest, base)
        record['candidate_after'] = {k: v for k, v in snapshot.items() if k != 'patch'}
        artifact['error'] = snapshot.get('error')
        if snapshot.get('patch') is not None:
            patch.write_bytes(base64.b64decode(snapshot['patch'], validate=True))
            artifact.update(path=str(patch), sha256=_sha256(patch))
        elif base and not artifact['error']:
            artifact['error'] = 'missing_candidate_patch'
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        artifact['error'] = str(error)
    record['patch'] = artifact
    if record['patch']['base_commit'] and record['patch']['error']:
        record.update(execution='failed', error='patch_capture_failed: ' + record['patch']['error'])
    record['manifest_stable'] = _sha256(manifest_path) == record['manifest']['sha256']
    if not record['manifest_stable']:
        record.update(execution='failed', error='manifest_changed_during_run')
    _save(output, record)
    return 0 if record['execution'] == 'completed' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--snapshot', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--base', help=argparse.SUPPRESS)
    parser.add_argument('--session', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.snapshot:
            print(json.dumps(_snapshot(args.snapshot, args.base)))
            return 0
        if not args.manifest or not args.output:
            parser.error('--manifest and --output are required')
        return _session(args.manifest, args.output) if args.session else run(args.manifest, args.output)
    except (OSError, ValueError, KeyError) as error:
        print(f'agent capture refused: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
