"""Bind a pinned benchmark invocation to its official JSON evaluator report.

This connector captures an evaluator command; it does not interpret a verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys


RUN_CHECK = Path(__file__).with_name('run_check.py')
_SHA256 = re.compile(r'^[0-9a-f]{64}$')


class InputError(ValueError):
    """The manifest or its pinned inputs cannot support a reproducible run."""


def _nonempty_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise InputError(f'{label} must be a nonempty string')
    return value


def _sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _artifact(root, value, label):
    if not isinstance(value, dict):
        raise InputError(f'{label} file reference is required')
    relative = _nonempty_text(value.get('path'), f'{label}.path')
    expected = _nonempty_text(value.get('sha256'), f'{label}.sha256')
    if not _SHA256.fullmatch(expected):
        raise InputError(f'{label}.sha256 must be a lowercase SHA-256 hex digest')
    candidate = root / relative
    if candidate.is_symlink():
        raise InputError(f'{label} file is missing or is a symlink: {relative}')
    path = candidate.resolve()
    if not path.is_file():
        raise InputError(f'{label} file is missing or is a symlink: {relative}')
    actual = _sha256(path)
    if actual != expected:
        raise InputError(f'{label} identity changed: expected {expected}, found {actual}')
    return {'path': str(path), 'sha256': expected, 'expected_sha256': expected, 'before_sha256': actual,
            'after_sha256': None, 'stable': None}


def _validate_manifest(manifest, manifest_path):
    if not isinstance(manifest, dict) or manifest.get('format') != 'benchmark-evaluation-manifest-v1':
        raise InputError('manifest format must be benchmark-evaluation-manifest-v1')
    root = manifest_path.parent
    benchmark = manifest.get('benchmark')
    if not isinstance(benchmark, dict):
        raise InputError('benchmark metadata is required')
    for key in ('id', 'task_id', 'data_revision', 'evaluator_revision'):
        _nonempty_text(benchmark.get(key), f'benchmark.{key}')
    image = _nonempty_text(benchmark.get('image_digest'), 'benchmark.image_digest')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise InputError('benchmark.image_digest must be pinned as sha256:<64 lowercase hex>')

    execution = manifest.get('execution')
    if not isinstance(execution, dict):
        raise InputError('execution metadata is required')
    argv = execution.get('argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(token, str) or not token for token in argv):
        raise InputError('execution.argv must be a nonempty array of nonempty strings')
    cwd_value = _nonempty_text(execution.get('cwd'), 'execution.cwd')
    cwd = (root / cwd_value).resolve()
    if not cwd.is_dir():
        raise InputError(f'execution.cwd must name an existing directory: {cwd_value}')
    timeout = execution.get('timeout_seconds')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise InputError('execution.timeout_seconds must be finite and greater than zero')
    report_value = _nonempty_text(execution.get('report_path'), 'execution.report_path')
    report = Path(os.path.abspath(cwd / report_value))
    pointer = execution.get('verdict_pointer')
    if not isinstance(pointer, str) or (pointer and not pointer.startswith('/')):
        raise InputError('execution.verdict_pointer must be an RFC 6901 JSON pointer (or empty for the root)')

    artifact_refs = manifest.get('artifacts')
    if not isinstance(artifact_refs, dict):
        raise InputError('artifacts.patch and artifacts.trace are required')
    artifacts = {
        'patch': _artifact(root, artifact_refs.get('patch'), 'artifacts.patch'),
        'trace': _artifact(root, artifact_refs.get('trace'), 'artifacts.trace'),
    }
    agent = manifest.get('agent')
    if not isinstance(agent, dict):
        raise InputError('agent metadata is required')
    for key in ('model', 'cli_revision'):
        _nonempty_text(agent.get(key), f'agent.{key}')
    if not isinstance(agent.get('budget'), dict) or not agent['budget']:
        raise InputError('agent.budget must be a nonempty object')
    if not isinstance(agent.get('permissions'), dict):
        raise InputError('agent.permissions must be an object')

    plugin = manifest.get('plugin')
    if not isinstance(plugin, dict):
        raise InputError('plugin condition and fixed-package identity are required')
    for key in ('condition', 'version', 'source_commit'):
        _nonempty_text(plugin.get(key), f'plugin.{key}')
    artifacts['plugin_package'] = _artifact(root, plugin.get('package'), 'plugin.package')
    if 'usage' not in manifest or 'cost' not in manifest:
        raise InputError('usage and cost must be explicit; use null when uncollected')

    return {
        'benchmark': benchmark,
        'execution': execution,
        'argv': argv,
        'cwd': cwd,
        'timeout': float(timeout),
        'report': report,
        'pointer': pointer,
        'artifacts': artifacts,
    }


def _pointer_value(document, pointer):
    if pointer == '':
        return True, document
    current = document
    for raw_part in pointer[1:].split('/'):
        if re.search(r'~(?![01])', raw_part):
            return False, None
        part = raw_part.replace('~1', '/').replace('~0', '~')
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdecimal():
            index = int(part)
            if index >= len(current):
                return False, None
            current = current[index]
        else:
            return False, None
    return True, current


def _write_record(stream, record):
    stream.seek(0)
    stream.truncate()
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
    stream.flush()


def run(manifest_path, output_path):
    manifest_path = Path(manifest_path).resolve()
    output = Path(os.path.abspath(output_path))
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    if not isinstance(manifest, dict):
        raise InputError('manifest root must be a JSON object')
    execution = manifest.get('execution')
    if not isinstance(execution, dict):
        raise InputError('execution metadata is required')
    capture = output.with_name(output.name + '.run-check.json')
    conditions = _validate_manifest(manifest, manifest_path)
    report = conditions['report']
    if not RUN_CHECK.is_file():
        raise InputError(f'run_check capture tool is unavailable: {RUN_CHECK}')
    if len({output, capture, report}) != 3:
        raise InputError('final output, run_check capture, and evaluator report must be distinct paths')
    for path, label in ((output, 'output'), (capture, 'run_check capture'), (report, 'evaluator report')):
        if path.exists() or path.is_symlink():
            raise InputError(f'{label} path already exists: {path}')

    record = {
        'format': 'official-benchmark-capture-v1',
        'capture_status': 'incomplete',
        'incomplete_reason': 'evaluation_not_finished',
        'manifest': {'path': str(manifest_path), 'sha256': hashlib.sha256(raw_manifest).hexdigest(),
                     'data': manifest},
        'benchmark': manifest['benchmark'],
        'plugin': manifest['plugin'],
        'agent': manifest['agent'],
        'usage': manifest['usage'],
        'cost': manifest['cost'],
        'artifacts': conditions['artifacts'],
        'runner': {'exit_code': None, 'execution': None, 'launcher_error': None},
        'execution_capture': {'path': str(capture), 'sha256': None, 'data': None, 'error': None},
        'evaluator_report': {'path': str(report), 'sha256': None, 'data': None, 'error': None},
        'external_verdict': None,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        _write_record(stream, record)
        argv = [sys.executable, str(RUN_CHECK), '--cwd', str(conditions['cwd']),
                '--output', str(capture), '--json-report', str(report),
                '--timeout', str(conditions['timeout']), '--', *conditions['argv']]
        try:
            launcher = subprocess.run(
                argv, cwd=manifest_path.parent, capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=max(conditions['timeout'] + 30, 60),
            )
            record['runner'] = {
                'exit_code': launcher.returncode,
                'execution': 'exited',
                'stdout': launcher.stdout,
                'stderr': launcher.stderr,
                'launcher_error': None,
            }
        except (OSError, subprocess.TimeoutExpired) as error:
            record['runner']['launcher_error'] = str(error)

        capture_record = None
        if capture.is_file() and not capture.is_symlink():
            capture_bytes = capture.read_bytes()
            record['execution_capture'].update(
                sha256=hashlib.sha256(capture_bytes).hexdigest(),
            )
            try:
                capture_record = json.loads(capture_bytes)
                record['execution_capture']['data'] = capture_record
                record['runner']['execution'] = capture_record.get('execution') if isinstance(capture_record, dict) else None
                record['runner']['exit_code'] = capture_record.get('exit_code') if isinstance(capture_record, dict) else None
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                record['execution_capture']['error'] = str(error)
        else:
            record['execution_capture']['error'] = 'run_check did not produce a fresh capture'

        report_info = capture_record.get('json_report') if isinstance(capture_record, dict) else None
        if isinstance(report_info, dict):
            record['evaluator_report']['sha256'] = report_info.get('sha256')
            record['evaluator_report']['data'] = report_info.get('data')
            record['evaluator_report']['error'] = report_info.get('error')
            if report_info.get('path') and Path(report_info['path']).resolve() != report.resolve():
                record['evaluator_report']['error'] = 'run_check report path did not match manifest'
        else:
            record['evaluator_report']['error'] = 'run_check did not capture a JSON report'

        found = False
        if record['evaluator_report']['error'] is None:
            found, value = _pointer_value(record['evaluator_report']['data'], conditions['pointer'])
            if found:
                record['external_verdict'] = {'pointer': conditions['pointer'], 'value': value}
            else:
                record['evaluator_report']['error'] = 'verdict_pointer_not_found_or_invalid'

        stable_artifacts = True
        for name, artifact in record['artifacts'].items():
            current = Path(artifact['path'])
            try:
                after = _sha256(current) if current.is_file() and not current.is_symlink() else None
            except OSError:
                after = None
            artifact['after_sha256'] = after
            artifact['stable'] = after == artifact['expected_sha256']
            stable_artifacts = stable_artifacts and artifact['stable']

        execution_complete = isinstance(capture_record, dict) and capture_record.get('execution') == 'exited'
        report_complete = record['evaluator_report']['error'] is None and found
        if execution_complete and report_complete and stable_artifacts:
            record['capture_status'] = 'complete'
            record['incomplete_reason'] = None
        else:
            reasons = []
            if not execution_complete:
                reasons.append('evaluator_execution_incomplete')
            if not report_complete:
                reasons.append('official_report_or_verdict_missing')
            if not stable_artifacts:
                reasons.append('pinned_artifact_changed_during_run')
            record['incomplete_reason'] = reasons
        _write_record(stream, record)

    print(json.dumps({'capture_status': record['capture_status'], 'output': str(output),
                      'external_verdict': record['external_verdict']}))
    return 0 if record['capture_status'] == 'complete' else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path,
                        help='new run result path; existing results are never overwritten')
    args = parser.parse_args(argv)
    try:
        return run(args.manifest, args.output)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, InputError) as error:
        print(f'benchmark capture refused: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
