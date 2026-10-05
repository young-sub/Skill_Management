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

from unittest_evidence import assess


def capture_check(argv, cwd, output, feature, check, timeout):
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('run_check.py')),
                             '--cwd', str(cwd), '--output', str(output),
                             '--feature', feature, '--check', check,
                             '--timeout', str(timeout), '--', *argv],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    if not result.stdout.strip():
        raise ValueError('Capture did not produce a new run; inspect path/permissions')
    return json.loads(result.stdout)['run_id']


def execute_feature(root, feature, output, timeout):
    """Run each registered check once, then recheck all captures at the final state."""
    project = json.loads((root / '.harness/project.yaml').read_text(encoding='utf-8'))
    commands = dict(project['commands'])
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    checks = feature_checks(root, commands).get(feature)
    if not checks:
        raise ValueError('Feature has no connected checks')
    selected = [(check, *check_target(root, feature, check)) for check in dict.fromkeys(checks)]
    output = output.resolve()
    if not output.is_relative_to(root):
        raise ValueError('Workflow evidence must be inside the project')
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for index, (check, argv, cwd) in enumerate(selected):
        path = output / f'{index}.json'
        run_id = capture_check(argv, cwd, path, feature, check, timeout)
        records.append({'check': check, 'run_id': run_id, 'path': path.relative_to(root).as_posix()})
    bundle = output / 'bundle.json'
    bundle.write_text(json.dumps({'format': 'unittest-captures-v1', 'feature': feature,
                                 'records': records}), encoding='utf-8')
    results = []
    for record, (check, argv, cwd) in zip(records, selected):
        try:
            results.append(assess(root / record['path'], record['run_id'], feature, check, argv, cwd))
        except (OSError, ValueError, KeyError, TypeError) as error:
            results.append({'check': check, 'status': 'BLOCKED', 'reason': str(error)})
    statuses = {item['status'] for item in results}
    return {'status': 'BLOCKED' if 'BLOCKED' in statuses else 'ISSUES' if 'ISSUES' in statuses else 'PASS',
            'feature': feature, 'bundle': str(bundle), 'results': results}


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



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--feature', required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--check')
    selection.add_argument('--all-checks', action='store_true', help='Run all checks registered for this Feature into a new output directory')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--output', type=Path, help='New evidence file; execute the selected check')
    source.add_argument('--evidence', type=Path, help='Existing evidence; assess without execution')
    parser.add_argument('--run-id', help='Required when assessing an existing run')
    parser.add_argument('--bundle-output', type=Path, help='New workflow binding for this native capture; no test rerun')
    parser.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args()
    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError('Timeout must be finite and positive')
        root = args.root.resolve()
        if args.all_checks:
            if not args.output or args.bundle_output or args.run_id:
                raise ValueError('--all-checks requires a new --output directory only')
            verdict = execute_feature(root, args.feature, args.output, args.timeout)
            print(json.dumps(verdict, ensure_ascii=False))
            return {'PASS': 0, 'ISSUES': 1, 'BLOCKED': 2}[verdict['status']]
        if args.bundle_output and args.bundle_output.exists():
            raise ValueError('Bundle output already exists')
        argv, cwd = check_target(root, args.feature, args.check)
        run_id = args.run_id
        if args.output:
            run_id = capture_check(argv, cwd, args.output, args.feature, args.check, args.timeout)
        elif not run_id:
            raise ValueError('Existing evidence requires an explicit run ID')
        verdict = assess(args.output or args.evidence, run_id, args.feature, args.check, argv, cwd)
        if args.bundle_output:
            capture = (args.output or args.evidence).resolve()
            if not capture.is_relative_to(root):
                raise ValueError('Workflow capture must be inside the project')
            args.bundle_output.parent.mkdir(parents=True, exist_ok=True)
            with args.bundle_output.open('x', encoding='utf-8') as stream:
                json.dump({'format': 'unittest-captures-v1', 'feature': args.feature,
                           'records': [{'check': args.check, 'run_id': run_id,
                                        'path': capture.relative_to(root).as_posix()}]}, stream)
    except (OSError, ValueError, KeyError, TypeError) as error:
        verdict = {'status': 'BLOCKED', 'feature': args.feature, 'check': args.check,
                   'reason': str(error), 'scope': 'repository/harness; selected check only'}
    print(json.dumps(verdict, ensure_ascii=False))
    return {'PASS': 0, 'ISSUES': 1, 'BLOCKED': 2}[verdict['status']]


if __name__ == '__main__':
    raise SystemExit(main())
