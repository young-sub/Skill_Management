"""Host-only result publication for an already protected verifier installation.

The host must protect this module, policy, snapshots and result directory from
the candidate. Call finish only with observations collected by that host, never
with a candidate's submitted report. This module does not create that authority,
launch processes, or prove that descendants have stopped.
"""
import hashlib
import json
from pathlib import Path
import uuid


def _file(root, name):
    root = Path(root).absolute()
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('host_path_escape')
    if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
           for p in (path, *path.parents)):
        raise ValueError('host_path_alias')
    return path


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _case(case):
    if (not isinstance(case, dict) or set(case) != {'id', 'exit', 'saved_hex'}
            or not isinstance(case['id'], str) or not case['id']
            or type(case['exit']) is not int or not isinstance(case['saved_hex'], str)):
        raise ValueError('invalid_case')
    raw = bytes.fromhex(case['saved_hex'])
    return {'id': case['id'], 'exit': case['exit'], 'saved_hex': raw.hex()}


def _basis(root):
    raw = _file(root, 'policy.json').read_bytes()
    policy = json.loads(raw)
    if (not isinstance(policy, dict) or set(policy) != {'task', 'snapshot', 'cases'}
            or not isinstance(policy['task'], str) or not policy['task']
            or not isinstance(policy['snapshot'], list) or not policy['snapshot']
            or not all(isinstance(p, str) and p for p in policy['snapshot'])
            or len(set(policy['snapshot'])) != len(policy['snapshot'])
            or not isinstance(policy['cases'], list) or not policy['cases']):
        raise ValueError('invalid_host_policy')
    cases = [_case(case) for case in policy['cases']]
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('duplicate_policy_case')
    return {'task': policy['task'], 'policy_sha256': _sha(raw),
            'publisher_sha256': _sha(Path(__file__).read_bytes()),
            'snapshot': {p: _sha(_file(root, p).read_bytes()) for p in policy['snapshot']}}, cases


def _path(root, run_id, suffix):
    if str(uuid.UUID(run_id)) != run_id:
        raise ValueError('invalid_run_id')
    return _file(root, 'runs/' + run_id + suffix)


def begin(root):
    basis, _ = _basis(root)
    record = {'run_id': str(uuid.uuid4()), 'basis': basis, 'status': 'PENDING'}
    path = _path(root, record['run_id'], '.pending.json')
    path.parent.mkdir(exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, sort_keys=True)
    return record


def _verdict(cases, observations):
    try:
        if not isinstance(observations, list):
            raise ValueError('observations_required')
        facts = [_case(fact) for fact in observations]
        if (len(facts) != len(cases) or len({f['id'] for f in facts}) != len(facts)
                or {f['id'] for f in facts} != {c['id'] for c in cases}):
            return 'BLOCKED'
    except (ValueError, TypeError):
        return 'BLOCKED'
    return 'ACCEPTED' if sorted(facts, key=lambda x: x['id']) == sorted(cases, key=lambda x: x['id']) else 'REJECTED'


def lookup(root, run_id, task):
    basis, cases = _basis(root)
    pending = json.loads(_path(root, run_id, '.pending.json').read_bytes())
    if pending != {'run_id': run_id, 'basis': basis, 'status': 'PENDING'} or basis['task'] != task:
        raise ValueError('stale_or_wrong_host_run')
    path = _path(root, run_id, '.result.json')
    if not path.exists():
        return pending
    result = json.loads(path.read_bytes())
    if (result.get('run_id') != run_id or result.get('basis') != basis
            or result.get('status') != _verdict(cases, result.get('observations'))):
        raise ValueError('invalid_host_result')
    return result


def finish(root, run_id, observations):
    basis, cases = _basis(root)
    pending = lookup(root, run_id, basis['task'])
    if pending['status'] != 'PENDING':
        raise ValueError('host_run_already_finished')
    result = dict(pending, status=_verdict(cases, observations), observations=observations)
    # Exclusive terminal publication: interruption leaves unreadable/absent data,
    # never an older accepted record. The host owns serialization of each run.
    with _path(root, run_id, '.result.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, sort_keys=True)
    return result
