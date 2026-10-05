"""Reassess native unittest captures; no test execution or stored-verdict trust.

This is the existing repository adapter, shared by the workflow evidence consumer.
It establishes scoped unittest results, not authenticated host or product proof.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def git_identity(cwd):
    def git(*args):
        try:
            result = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True)
        except OSError:
            return None
        return result.stdout if result.returncode == 0 else None
    head = git('rev-parse', 'HEAD')
    if head is None:
        return None
    diff = git('diff', 'HEAD', '--binary')
    status = git('status', '--porcelain')
    untracked = git('ls-files', '--others', '--exclude-standard', '-z')
    if diff is None or status is None or untracked is None:
        return None
    untracked_hashes = {}
    root = Path(cwd).resolve()
    for name in filter(None, untracked.decode('utf-8').split('\0')):
        relative = Path(name)
        path = root / relative
        if (any(part.lower().startswith(('.env', '.dev.vars')) or part.lower() in
                {'auth.json', 'credentials', 'secrets'} for part in relative.parts) or
                not path.resolve().is_relative_to(root) or
                any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
                    for p in (path, *path.parents) if p != root.parent)):
            return None
        try:
            untracked_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None
    return {
        'head': head.decode().strip(),
        'tracked_diff_sha256': hashlib.sha256(diff).hexdigest() if diff is not None else None,
        'status': status.decode('utf-8', errors='replace'),
        'untracked_sha256': untracked_hashes,
        'limit': 'Ignored inputs, dependencies, runtime data and server identity are not attested.',
    }


def assess(path, run_id, feature, check, argv, cwd):
    raw = path.read_bytes()
    record = json.loads(raw)
    if not isinstance(record, dict):
        raise ValueError('Evidence must be a capture record')
    binding = {'run_id': run_id, 'feature': feature, 'check': check,
               'argv': argv, 'cwd': str(cwd)}
    if any(record.get(key) != value for key, value in binding.items()):
        raise ValueError('Evidence does not match the selected run, Feature, command or cwd')
    current = git_identity(cwd)
    if current is None or record.get('before') != current or record.get('after') != current:
        raise ValueError('Git identity unavailable, changed during execution or stale')
    verdict = {**binding, 'evidence': str(path.resolve()),
               'evidence_sha256': hashlib.sha256(raw).hexdigest(),
               'scope': 'repository/harness; selected unittest command only',
               'remaining': 'Ignored inputs, dependencies, runtime/server identity, '
                            'agent quality and external products are not attested.'}
    if record.get('execution') != 'exited' or type(record.get('exit_code')) is not int:
        raise ValueError('Command did not exit normally; not_run/unavailable/timeout is not PASS')
    if record.get('cleanup_incomplete') or record.get('behavior_verdict') is not None:
        raise ValueError('Incomplete cleanup or submitted behavior verdict cannot establish PASS')
    output = record['stdout'] + '\n' + record['stderr']
    counts = re.findall(r'^Ran (\d+) tests? in [^\r\n]+$', output, re.MULTILINE)
    if len(counts) == 1 and int(counts[0]) == 0:
        raise ValueError('No tests ran; not_run is not PASS')
    if record['exit_code'] != 0:
        return {**verdict, 'status': 'ISSUES', 'reason': 'Native command failed',
                'exit_code': record['exit_code']}
    # This project owns these unittest commands. Output strings are not
    # signatures; this parser is deliberately not a generic runner framework.
    if len(counts) != 1 or int(counts[0]) == 0 or not re.search(r'^OK\s*$', output, re.MULTILINE):
        raise ValueError('No unambiguous, nonempty unittest success summary')
    if re.search(r'^FAILED\b|^OK \(|^.*skipped=\d+', output, re.MULTILINE):
        raise ValueError('Skipped, expected-failure or contradictory results require scoped review')
    return {**verdict, 'status': 'PASS', 'reason': 'Selected unittest assertions passed',
            'tests_run': int(counts[0]), 'exit_code': 0}
