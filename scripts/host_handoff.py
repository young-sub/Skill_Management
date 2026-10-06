"""Task-bound entrypoint installed inside an already protected verifier.

The host reviews handoff.json and includes it and this module in policy.snapshot.
Callers select only the fixed task and optionally a retained run, never paths,
commands, criteria or submitted success. This does not provision a sandbox.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy


def _candidate(api, root, basis):
    if not {'host_handoff.py', 'handoff.json'}.issubset(basis['snapshot']):
        raise ValueError('unbound_handoff')
    config = json.loads(api['_file'](root, 'handoff.json').read_bytes())
    if (not isinstance(config, dict) or set(config) != {'candidate', 'files'}
            or not isinstance(config['candidate'], str)
            or not isinstance(config['files'], dict) or not config['files']):
        raise ValueError('invalid_handoff')
    candidate = Path(config['candidate'])
    if not candidate.is_absolute() or not candidate.is_dir():
        raise ValueError('candidate_directory_required')
    api['_file'](candidate, '.')
    if root.resolve().is_relative_to(candidate.resolve()):
        raise ValueError('authority_inside_candidate_workspace')
    for name, snapshot in config['files'].items():
        if not isinstance(snapshot, str) or snapshot not in basis['snapshot']:
            raise ValueError('unbound_candidate_snapshot')
        actual = hashlib.sha256(api['_file'](candidate, name).read_bytes()).hexdigest()
        if actual != basis['snapshot'][snapshot]:
            raise ValueError('candidate_snapshot_changed:' + name)


def handoff(root, task, *, run_id=None):
    root = Path(root).absolute()
    api = runpy.run_path(str(root / 'host_result.py'))
    basis, _ = api['_basis'](root)
    if task != basis['task']:
        raise ValueError('task_mismatch')
    _candidate(api, root, basis)
    result = (api['lookup'](root, run_id, task) if run_id is not None else
              runpy.run_path(str(root / 'host_verify.py'))['execute'](root))
    try:
        _candidate(api, root, basis)
    except (OSError, ValueError) as error:
        return {'status': 'BLOCKED', 'task': task, 'run_id': result.get('run_id'),
                'error': str(error), 'verification': result}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--run-id', help='Read-only lookup; never execute or resume a check')
    args = parser.parse_args()
    try:
        result = handoff(Path(__file__).resolve().parent, args.task, run_id=args.run_id)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        result = {'status': 'BLOCKED', 'error': str(error)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'ACCEPTED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
