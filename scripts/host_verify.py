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


def workflow_audit(root, config, observations, executions):
    """Recompute obligations from host-approved files and host-collected cases.

    Never invoke candidate Git, import candidate code, or consume its bundles.
    The installation owner must review the frozen baseline and semantic reviews.
    """
    api = runpy.run_path(str(root / 'host_result.py'))
    basis, cases = api['_basis'](root)
    descriptor = config['workflow']
    if not isinstance(descriptor, dict) or set(descriptor) != {'root', 'state', 'checks'}:
        raise ValueError('invalid_host_workflow')
    project_root = api['_file'](root, descriptor['root'])
    if project_root == root or not project_root.is_dir():
        raise ValueError('workflow_snapshot_directory_required')
    for path in project_root.rglob('*'):
        relative = path.relative_to(root).as_posix()
        api['_file'](root, relative)
        if path.is_file() and relative not in basis['snapshot']:
            raise ValueError('unbound_workflow_file:' + relative)
    for name in ('project_workflow.py', descriptor['state'],
                 (project_root / '.harness/project.yaml').relative_to(root).as_posix()):
        if name not in basis['snapshot']:
            raise ValueError('unbound_workflow_file:' + name)
    workflow = runpy.run_path(str(root / 'project_workflow.py'))
    project = json.loads((project_root / '.harness/project.yaml').read_bytes())
    state = json.loads(api['_file'](root, descriptor['state']).read_bytes())
    if not isinstance(state, dict) or not state:
        raise ValueError('host_workflow_baseline_required')
    # Relocate the approved snapshot, preserving logical paths and all bases.
    state = dict(state, root=str(project_root.resolve()))
    configured = workflow['configuration'](project)
    if configured is None:
        raise ValueError('host_workflow_not_configured')
    mapping = descriptor['checks']
    known = {f['id']: set(f['checks']) for f in configured['features']}
    case_ids = {c['id'] for c in cases}
    if not isinstance(mapping, dict):
        raise ValueError('invalid_workflow_case_mapping')
    for feature, checks in mapping.items():
        if feature not in known or not isinstance(checks, dict):
            raise ValueError('unknown_workflow_feature')
        for check, ids in checks.items():
            if (check not in known[feature] or not isinstance(ids, list) or not ids
                    or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids)
                    or not set(ids).issubset(case_ids)):
                raise ValueError('invalid_workflow_case_mapping')
    inventory = {path.relative_to(project_root).as_posix(): workflow['file_hash'](
                    project_root, path.relative_to(project_root).as_posix())
                 for path in project_root.rglob('*') if path.is_file() and any(
                     path.relative_to(project_root).as_posix() == prefix or
                     path.relative_to(project_root).as_posix().startswith(prefix.rstrip('/') + '/')
                     for prefix in configured['roots'])}

    def resolve(_root, feature, _commands):
        findings = []
        for check in feature['checks']:
            ids = mapping.get(feature['id'], {}).get(check, [])
            verdict = api['_verdict']([c for c in cases if c['id'] in ids],
                [c for c in observations if c['id'] in ids],
                [c for c in executions if c['id'] in ids]) if ids else 'BLOCKED'
            if verdict != 'ACCEPTED':
                findings.append('protected_check_unverified:' + feature['id'] + ':' + check)
        if not feature['checks']:
            findings.append('protected_checks_missing:' + feature['id'])
        return {'status': 'BLOCKED' if findings else 'PASS', 'findings': findings}

    return workflow['inspect_project'](project_root, project, state,
                                      file_inventory=inventory, evidence_resolver=resolve)


def prepare(root):
    root = Path(root).resolve()
    result_api = runpy.run_path(str(root / 'host_result.py'))
    basis, expected = result_api['_basis'](root)
    required = {'host_verify.py', 'host_result.py', 'windows_job.py', 'execution.json'}
    if not required.issubset(basis['snapshot']):
        raise ValueError('host_runtime_not_bound')
    config = json.loads((root / 'execution.json').read_bytes())
    if (not isinstance(config, dict) or set(config) - {'workflow'} != {'workspace', 'home', 'codex', 'python',
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
    if 'workflow' in config:
        workflow_audit(root, config, [], [])  # Validate bindings before any launch.
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
        if 'workflow' in config:
            audit = workflow_audit(root, config, observations, executions)
            raw.append({'workflow': audit})
            if audit['status'] != 'READY_FOR_REVIEW':
                _, cases = result_api['_basis'](root)
                if result_api['_verdict'](cases, observations, executions) == 'ACCEPTED':
                    executions = []  # Pending review blocks success, not an observed rejection.
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
