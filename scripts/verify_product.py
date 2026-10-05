"""Run or assess repository-owned unittest checks from the Feature Map.

This adapter understands unittest summaries only. It does not authenticate
editable evidence, attest ignored runtime inputs, or verify external products.
"""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys

from unittest_evidence import assess


def capture_check(argv, cwd, output, feature, check, timeout, also_features=()):
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('run_check.py')),
                             '--cwd', str(cwd), '--output', str(output),
                             '--feature', feature, '--check', check,
                             *[token for name in also_features for token in ('--also-feature', name)],
                             '--timeout', str(timeout), '--', *argv],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    if not result.stdout.strip():
        raise ValueError('Capture did not produce a new run; inspect path/permissions')
    return json.loads(result.stdout)['run_id']


def execute_feature(root, feature, output, timeout):
    outcome = execute_features(root, [feature], output, timeout)
    return {'status': outcome['status'], 'feature': feature,
            'bundle': outcome['bundles'][feature], 'results': outcome['results'][feature]}


def execute_features(root, features, output, timeout):
    """Share only the same registered check/argv/cwd within this execution batch."""
    project = json.loads((root / '.harness/project.yaml').read_text(encoding='utf-8'))
    commands = dict(project['commands'])
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    mapping = feature_checks(root, commands)
    features = list(dict.fromkeys(features))
    if not features or any(not mapping.get(feature) for feature in features):
        raise ValueError('Feature has no connected checks')
    selected = {}
    for feature in features:
        for check in dict.fromkeys(mapping[feature]):
            argv, cwd = check_target(root, feature, check)
            selected.setdefault((check, tuple(argv), cwd), []).append(feature)
    output = output.resolve()
    if not output.is_relative_to(root):
        raise ValueError('Workflow evidence must be inside the project')
    output.mkdir(parents=True, exist_ok=False)
    records = {feature: [] for feature in features}
    executed = []
    for index, ((check, argv, cwd), consumers) in enumerate(selected.items()):
        path = output / f'{index}.json'
        run_id = capture_check(argv, cwd, path, consumers[0], check, timeout, consumers[1:])
        record = {'check': check, 'run_id': run_id, 'path': path.relative_to(root).as_posix()}
        for feature in consumers:
            records[feature].append(record)
        executed.append((record, list(argv), cwd, consumers))
    bundles = {}
    for feature in features:
        bundle = output / ('bundle.json' if len(features) == 1 else feature + '.bundle.json')
        bundle.write_text(json.dumps({'format': 'unittest-captures-v1', 'feature': feature,
                                     'records': records[feature]}), encoding='utf-8')
        bundles[feature] = str(bundle)
    results = {feature: [] for feature in features}
    for record, argv, cwd, consumers in executed:
        for feature in consumers:
            try:
                results[feature].append(assess(root / record['path'], record['run_id'], feature, record['check'], argv, cwd))
            except (OSError, ValueError, KeyError, TypeError) as error:
                results[feature].append({'check': record['check'], 'status': 'BLOCKED', 'reason': str(error)})
    statuses = {item['status'] for values in results.values() for item in values}
    return {'status': 'BLOCKED' if 'BLOCKED' in statuses else 'ISSUES' if 'ISSUES' in statuses else 'PASS',
            'bundles': bundles, 'results': results, 'executed_checks': len(executed)}


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


def execute_pending(root, state, work_id, output, timeout):
    """Ask the existing runtime to recompute obligations, never trust a saved verdict."""
    if state:
        path = (root / state).resolve()
        if not path.is_relative_to(root / '.work') or not path.is_file():
            raise ValueError('Pending selection requires an existing task-local state')
    selection = ['--state', state] if state else ['--work-id', work_id]
    completed = subprocess.run([sys.executable, str(Path(__file__).with_name('project_workflow.py')),
        'audit', '--root', str(root), *selection], capture_output=True, text=True, encoding='utf-8')
    audit = json.loads(completed.stdout)
    if completed.returncode not in (0, 2) or audit.get('status') not in {'PARTIAL', 'READY_FOR_REVIEW'}:
        raise ValueError(f'Workflow selection unavailable: {audit.get("findings", [])}')
    selected = [feature['id'] for feature in audit['features'] if feature.get('verification_status') == 'REQUIRED']
    if any(feature.get('verification_status') not in {'PASS', 'REQUIRED', 'NOT_REQUIRED'} for feature in audit['features']):
        raise ValueError('Workflow runtime does not expose current verification requirements')
    context = {'selected_features': selected, 'workflow_status': audit['status'],
               'remaining_obligations': audit['obligations'], 'product_findings': audit['product_findings']}
    if not selected:
        return {'status': 'NOT_REQUIRED', 'executed_checks': 0, **context}
    project = json.loads((root / '.harness/project.yaml').read_text(encoding='utf-8'))
    commands = dict(project['commands'])
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    mapping = feature_checks(root, commands)
    configured = {f['id']: f['checks'] for f in project['extensions']['workflow']['features']}
    if any(set(mapping.get(feature, [])) != set(configured[feature]) for feature in selected):
        raise ValueError('Feature Map and workflow check selection disagree')
    return {**execute_features(root, selected, output, timeout), **context}


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
    features = parser.add_mutually_exclusive_group(required=True)
    features.add_argument('--feature')
    features.add_argument('--features', nargs='+', help='Share registered checks across these preselected Features')
    features.add_argument('--pending-state', help='Select outstanding verification from an existing .work record')
    features.add_argument('--work-id', help='Select outstanding verification from Harness start state')
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
        if (args.features or args.pending_state or args.work_id) and not args.all_checks:
            raise ValueError('Batch or pending selection requires --all-checks')
        if args.all_checks:
            if not args.output or args.bundle_output or args.run_id:
                raise ValueError('--all-checks requires a new --output directory only')
            if args.pending_state or args.work_id:
                verdict = execute_pending(root, args.pending_state, args.work_id, args.output, args.timeout)
            else:
                verdict = (execute_features(root, args.features, args.output, args.timeout) if args.features else
                           execute_feature(root, args.feature, args.output, args.timeout))
            print(json.dumps(verdict, ensure_ascii=False))
            return {'PASS': 0, 'NOT_REQUIRED': 0, 'ISSUES': 1, 'BLOCKED': 2}[verdict['status']]
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
