"""Fixed-installation host verification entrypoint; never run from candidate writes.

The trusted host installs this file, its two helpers, execution.json, policy.json
and frozen inputs together under its protected directory. The CLI cannot select
another authority, policy, command or evidence file. It accepts only that policy's
declared cases; full project obligations require their own protected criteria.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import queue
import subprocess
import sys


def _identities(config):
    for name in ['codex', 'python']:
        path = Path(config[name])
        if not path.is_absolute() or hashlib.sha256(path.read_bytes()).hexdigest() != config[name + '_sha256']:
            raise ValueError('host_executable_changed:' + name)
    if Path(config['python']).resolve() != Path(sys.executable).resolve():
        raise ValueError('host_interpreter_mismatch')


def require_sandbox_ready(config):
    # Presence only: never read/copy credential material or automatically re-run
    # administrator setup. The native launcher still validates existing state.
    for name in ['.sandbox/setup_marker.json', '.sandbox-secrets/sandbox_users.json']:
        if not (Path(config['home']) / name).is_file():
            raise ValueError('sandbox_setup_incomplete:' + name)


def sandbox_env(config):
    # Windows known-folder and user-account resolution needs these standard OS
    # variables too. Dropping SYSTEMDRIVE/PROGRAMDATA creates literal fallback
    # cache paths; dropping identity fields can break native setup resolution.
    names = ['SYSTEMROOT', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP', 'USERPROFILE',
             'LOCALAPPDATA', 'APPDATA', 'PATH', 'SYSTEMDRIVE', 'PROGRAMDATA',
             'USERNAME', 'USERDOMAIN', 'USERDOMAIN_ROAMINGPROFILE', 'HOMEDRIVE',
             'HOMEPATH', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMW6432',
             'COMMONPROGRAMFILES', 'COMMONPROGRAMFILES(X86)', 'COMMONPROGRAMW6432',
             'PUBLIC', 'ALLUSERSPROFILE', 'COMPUTERNAME', 'PATHEXT']
    env = {name: os.environ[name] for name in names if name in os.environ}
    env['CODEX_HOME'] = config['home']
    return env


def prepare(root):
    root = Path(root).resolve()
    result_api = runpy.run_path(str(root / 'host_result.py'))
    basis, expected = result_api['_basis'](root)
    required = {'host_verify.py', 'host_result.py', 'windows_job.py', 'execution.json'}
    if not required.issubset(basis['snapshot']):
        raise ValueError('host_runtime_not_bound')
    config = json.loads((root / 'execution.json').read_bytes())
    if (not isinstance(config, dict) or set(config) != {'workspace', 'home', 'codex', 'python',
            'codex_sha256', 'python_sha256', 'timeout', 'cases'}
            or not isinstance(config['cases'], list)
            or type(config['timeout']) not in (int, float)
            or not math.isfinite(config['timeout']) or config['timeout'] <= 0):
        raise ValueError('invalid_host_execution')
    for name in ['workspace', 'home']:
        path = Path(config[name])
        if not path.is_absolute() or not path.is_dir():
            raise ValueError('host_directory_required:' + name)
        result_api['_file'](path, '.')
    workspace = Path(config['workspace']).resolve()
    if root.is_relative_to(workspace):
        raise ValueError('authority_inside_candidate_workspace')
    selected = []
    for case in config['cases']:
        if (not isinstance(case, dict) or set(case) != {'id', 'argv', 'saved', 'initial_hex'}
                or not isinstance(case['id'], str) or not isinstance(case['argv'], list)
                or not case['argv'] or not all(isinstance(arg, str) and arg for arg in case['argv'])
                or not isinstance(case['saved'], str) or not case['saved']):
            raise ValueError('invalid_host_case')
        if case['argv'][:2] != [config['python'], '-I']:
            raise ValueError('case_requires_pinned_isolated_python_driver')
        if len(case['argv']) < 3 or not case['argv'][2].startswith('{authority}/'):
            raise ValueError('protected_driver_required')
        for arg in case['argv'][2:]:
            if not arg.startswith('{authority}/'):
                continue
            path = result_api['_file'](root, arg.removeprefix('{authority}/'))
            files = list(path.rglob('*')) if path.is_dir() else [path]
            for file in files:
                relative = file.relative_to(root).as_posix()
                result_api['_file'](root, relative)
                if file.is_file() and relative not in basis['snapshot']:
                    raise ValueError('unbound_host_input:' + relative)
            if not path.exists():
                raise ValueError('missing_host_input')
        result_api['_file'](workspace, case['saved'])
        bytes.fromhex(case['initial_hex'])
        selected.append(case['id'])
    if len(selected) != len(set(selected)) or set(selected) != {c['id'] for c in expected}:
        raise ValueError('host_case_coverage_mismatch')
    _identities(config)
    require_sandbox_ready(config)
    return result_api, config


def execute(root):
    root = Path(root).resolve()
    result_api, config = prepare(root)
    workspace = Path(config['workspace']).resolve()
    job = runpy.run_path(str(root / 'windows_job.py'))
    run = result_api['begin'](root)
    runtime = workspace / ('host-run-' + run['run_id'])
    runtime.mkdir(exist_ok=False)
    # Do not pass provider credentials or arbitrary host environment to candidates.
    env = sandbox_env(config)
    launcher = [config['codex'], 'sandbox', '-P', ':workspace', '-c',
                'windows.sandbox="elevated"', '-C', str(workspace), '--']
    observations, executions, raw = [], [], []
    try:
        for index, case in enumerate(config['cases']):
            work = runtime / str(index)
            work.mkdir()
            saved = result_api['_file'](work, case['saved'])
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(bytes.fromhex(case['initial_hex']))
            argv = [arg.replace('{authority}', str(root)).replace('{runtime}', str(work)) for arg in case['argv']]
            execution = job['run'](launcher, argv, cwd=root, env=env, timeout=config['timeout'])
            raw.append({'id': case['id'], 'argv': argv, 'execution': execution})
            executions.append(dict(id=case['id'], **{key: execution[key] for key in
                              ['exit', 'timed_out', 'descendants_killed', 'remaining']}))
            # All job members are stopped before reading candidate-produced bytes.
            saved = result_api['_file'](work, case['saved'])
            if saved.stat().st_nlink != 1:
                raise ValueError('aliased_saved_output')
            observations.append({'id': case['id'], 'exit': execution['exit'],
                                 'saved_hex': saved.read_bytes().hex()})
            if execution['timed_out'] or execution['descendants_killed'] or execution['remaining']:
                break
        _identities(config)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, queue.Empty) as error:
        raw.append({'error': str(error)})
        # No partial observations can satisfy a full host policy.
        executions = []
    with (root / 'runs' / (run['run_id'] + '.raw.json')).open('x', encoding='utf-8') as stream:
        json.dump(raw, stream, indent=2)
    return result_api['finish'](root, run['run_id'], observations, executions=executions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'lookup'])
    parser.add_argument('--run-id')
    parser.add_argument('--task')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        if args.action == 'run':
            if args.run_id or args.task:
                raise ValueError('run_uses_fixed_host_policy')
            result = execute(root)
        else:
            if not args.run_id or not args.task:
                raise ValueError('lookup_requires_run_and_task')
            result = runpy.run_path(str(root / 'host_result.py'))['lookup'](root, args.run_id, args.task)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        result = {'status': 'BLOCKED', 'error': str(error)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'ACCEPTED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
