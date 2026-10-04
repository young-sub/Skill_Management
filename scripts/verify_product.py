"""Run or assess one repository-owned unittest check from the Feature Map.

This adapter understands unittest summaries only. It does not authenticate
editable evidence, attest untracked contents, or verify external products.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

from run_check import git_identity


def feature_checks(root, commands):
    """Consume the first and last columns of the canonical Markdown table."""
    features = {}
    for line in (root / 'docs/feature-map.md').read_text(encoding='utf-8').splitlines():
        if not line.startswith('|'):
            continue
        cells = [cell.strip().strip('`') for cell in line.strip('|').split('|')]
        if cells[0] == 'Feature ID' or cells[0].startswith('---'):
            continue
        if len(cells) != 7 or not re.fullmatch(r'[a-z][a-z0-9.-]*', cells[0]):
            raise ValueError('Malformed Feature Map row')
        checks = [check.strip() for check in cells[-1].split(',')]
        if cells[0] in features or not checks or any(check not in commands for check in checks):
            raise ValueError('Duplicate Feature ID or missing command in Feature Map')
        features[cells[0]] = checks
    if not features:
        raise ValueError('Feature Map contains no features')
    return features


def check_target(root, feature, check):
    project = json.loads((root / '.harness/project.yaml').read_text(encoding='utf-8'))
    commands = dict(project['commands'])
    for name, tokens in project.get('impact', {}).get('feature_selectors', {}).items():
        commands.setdefault(name, {'id': name, 'argv': tokens,
                                   'working_directory': '.', 'runtime': 'python'})
    features = feature_checks(root, commands)
    if feature not in features or check not in features[feature]:
        raise ValueError('Unknown Feature ID or command outside this Feature')
    descriptor = commands[check]
    argv = descriptor['argv']
    if (descriptor['id'] != check or not isinstance(argv, list) or len(argv) < 4
            or not all(isinstance(token, str) and token for token in argv)
            or argv[1:3] != ['-m', 'unittest']
            or descriptor['runtime'] != 'python'):
        raise ValueError('This adapter requires a configured Python unittest command')
    argv = [sys.executable, *argv[1:]]
    cwd = (root / descriptor['working_directory']).resolve()
    if not cwd.is_relative_to(root) or not cwd.is_dir():
        raise ValueError('Command working directory must exist inside the project')
    return argv, cwd


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
               'remaining': 'Untracked contents, dependencies, runtime/server identity, '
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--feature', required=True)
    parser.add_argument('--check', required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--output', type=Path, help='New evidence file; execute the selected check')
    source.add_argument('--evidence', type=Path, help='Existing evidence; assess without execution')
    parser.add_argument('--run-id', help='Required when assessing an existing run')
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError('Timeout must be finite and positive')
        root = args.root.resolve()
        argv, cwd = check_target(root, args.feature, args.check)
        run_id = args.run_id
        if args.output:
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('run_check.py')),
                                     '--cwd', str(cwd), '--output', str(args.output),
                                     '--feature', args.feature, '--check', args.check,
                                     '--timeout', str(args.timeout), '--', *argv],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace')
            if not result.stdout.strip():
                raise ValueError('Capture did not produce a new run; inspect path/permissions')
            run_id = json.loads(result.stdout)['run_id']
        elif not run_id:
            raise ValueError('Existing evidence requires an explicit run ID')
        verdict = assess(args.output or args.evidence, run_id, args.feature, args.check, argv, cwd)
    except (OSError, ValueError, KeyError, TypeError) as error:
        verdict = {'status': 'BLOCKED', 'feature': args.feature, 'check': args.check,
                   'reason': str(error), 'scope': 'repository/harness; selected check only'}
    print(json.dumps(verdict, ensure_ascii=False))
    return {'PASS': 0, 'ISSUES': 1, 'BLOCKED': 2}[verdict['status']]


if __name__ == '__main__':
    raise SystemExit(main())
