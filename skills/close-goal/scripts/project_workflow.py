# Generated file. Do not edit directly.
# Source: authoring/scripts/project_workflow.py
# Source-SHA256: 15ed9e5a4f837b1266127c31ec4d734ab0a274c0c07e15ddf72bae51e81d7fe8

"""Project-owned workflow obligations. Local consistency, not protected acceptance.

Reads the existing project extension and work record; does not infer business
meaning, execute project commands during audit, or authenticate an Agent review.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def local_path(root, name):
    path = root / name
    if not isinstance(name, str) or Path(name).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'path_outside_project:{name}')
    if any(parent.is_symlink() or (hasattr(parent, 'is_junction') and parent.is_junction())
           for parent in (path, *path.parents) if parent != root.parent):
        raise ValueError(f'aliased_path:{name}')
    if any(part.lower().startswith(('.env', '.dev.vars')) or part.lower() in
           {'credentials', 'secrets', 'auth.json'} for part in Path(name).parts):
        raise ValueError(f'private_path:{name}')
    return path


def file_hash(root, name):
    path = local_path(root, name)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)
    return result.stdout


def inventory(root, roots):
    """Names from Git; only explicitly scoped, non-private file bytes are read."""
    names = set(git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').decode('utf-8').split('\0')) - {''}
    result = {}
    for name in sorted(names):
        if any(name == prefix or name.startswith(prefix.rstrip('/') + '/') for prefix in roots):
            result[name] = file_hash(root, name)
    return result


def configuration(project):
    if not isinstance(project, dict):
        raise ValueError('project_must_be_object')
    config = project.get('extensions', {}).get('workflow')
    if config is None:
        return None
    if not isinstance(config, dict) or not config.get('roots') or not config.get('features'):
        raise ValueError('workflow_requires_roots_and_features')
    if not isinstance(config['roots'], list) or not isinstance(config['features'], list):
        raise ValueError('workflow_roots_and_features_must_be_lists')
    for prefix in config['roots']:
        if (not isinstance(prefix, str) or not prefix or Path(prefix).is_absolute()
                or any(part in {'.', '..', '.git', '.work'} for part in Path(prefix).parts)):
            raise ValueError('invalid_inventory_root')
    ids = []
    for feature in config['features']:
        if not isinstance(feature, dict):
            raise ValueError('feature_must_be_object')
        for field in ('id', 'partition'):
            if not isinstance(feature.get(field), str) or not feature[field].strip():
                raise ValueError(f'feature_requires:{field}')
        for field in ('sources', 'map', 'criteria', 'checks'):
            value = feature.get(field)
            if not isinstance(value, list) or (field != 'checks' and not value) or any(not isinstance(v, str) or not v for v in value):
                raise ValueError(f'feature_requires:{field}')
            if len(value) != len(set(value)):
                raise ValueError(f'duplicate:{feature["id"]}:{field}')
        ids.append(feature['id'])
        documents = feature.get('documentation_only', {})
        if not isinstance(documents, dict) or any(
                not isinstance(name, str) or not name or Path(name).is_absolute()
                or any(c in name for c in '*?[') or '..' in Path(name).parts
                or not isinstance(reason, str) or not reason.strip()
                for name, reason in documents.items()):
            raise ValueError('documentation_only_requires_exact_paths_and_reasons')
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate_feature_identity')
    return config


def begin(root, project, intent, targets=()):
    if intent not in {'init', 'change', 'feedback', 'ui', 'maintain'}:
        raise ValueError('unsupported_work_intent')
    if intent in {'feedback', 'ui'} and not targets:
        raise ValueError('target_required')
    config = configuration(project)
    if config is None:
        raise ValueError('workflow_not_configured')
    if set(targets) - {f['id'] for f in config['features']}:
        raise ValueError('unknown_target')
    return {'schema_version': 1, 'root': str(root.resolve()), 'intent': intent,
            'targets': sorted(set(targets)), 'base': git(root, 'rev-parse', 'HEAD').decode().strip(),
            'dirty_baseline': git(root, 'status', '--porcelain').decode('utf-8'),
            'baseline': inventory(root, config['roots']), 'reviews': {},
            'source_patterns': {f['id']: list(f['sources']) for f in config['features']},
            'documentation_only': {f['id']: dict(f.get('documentation_only', {})) for f in config['features']},
            'input_bases': {item['id']: item['basis'] for item in inspect_project(root, project)['features']}}


def begin_work(root, project):
    """Called by Harness start before mutation; reuse current semantic reviews."""
    state = begin(root, project, 'change')
    configured = configuration(project).get('state')
    if configured:
        path = local_path(root, configured)
        if not path.resolve().is_relative_to(root.resolve() / '.work'):
            raise ValueError('state_must_be_task_local_under_work')
        if path.is_file():
            previous = json.loads(path.read_text(encoding='utf-8'))
            current = inspect_project(root, project, previous)
            reusable = {item['id'] for item in current['features'] if item['reviewed']}
            state['reviews'] = {key: deepcopy(value) for key, value in previous.get('reviews', {}).items()
                                if key in reusable}
    return state


def work_record(root, work_id):
    """Use start's immutable baseline, even before an optional review file exists."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', work_id):
        raise ValueError('invalid_work_id')
    directory = local_path(root, f'.work/goals/active/{work_id}')
    manifest = json.loads(local_path(root, f'.work/goals/active/{work_id}/work.json').read_text(encoding='utf-8'))
    if manifest.get('work_id') != work_id or manifest.get('state') != 'active':
        raise ValueError('work_target_mismatch')
    baseline = manifest.get('workflow_baseline')
    if (not isinstance(baseline, dict) or baseline.get('schema_version') != 1
            or baseline.get('root') != str(root.resolve()) or baseline.get('base') != manifest.get('source_commit')
            or not isinstance(baseline.get('baseline'), dict) or not isinstance(baseline.get('input_bases'), dict)):
        raise ValueError('work_workflow_baseline_unavailable')
    path = local_path(root, f'.work/goals/active/{work_id}/workflow.json')
    state = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else deepcopy(baseline)
    if not isinstance(state, dict):
        raise ValueError('invalid_work_workflow_record')
    for key, value in baseline.items():
        if key not in {'reviews', 'retired_reviews'} and state.get(key) != value:
            raise ValueError(f'work_workflow_baseline_changed:{key}')
    return state, directory / 'workflow.json'


def inspect_project(root, project, state=None):
    root = root.resolve()
    config = configuration(project)
    result = {'status': 'NOT_CONFIGURED', 'mapping_status': 'NOT_CONFIGURED', 'enforcement': 'BLOCKED',
              'trust': 'editable local consistency; host-protected acceptance unavailable',
              'obligations': [], 'features': [], 'partitions': {}, 'unmapped': [],
              'unlinked': [], 'findings': [], 'product_findings': [], 'retired': []}
    if config is None:
        return result
    if state is not None and not isinstance(state, dict):
        raise ValueError('workflow_state_must_be_object')
    if state is not None and (state.get('schema_version') != 1 or state.get('root') != str(root)):
        raise ValueError('work_target_mismatch')
    if state is not None and not isinstance(state.get('baseline'), dict):
        raise ValueError('workflow_baseline_required')
    state = state or {}
    for field in ('reviews', 'retired_reviews', 'baseline', 'input_bases', 'source_patterns', 'documentation_only'):
        if not isinstance(state.get(field, {}), dict):
            raise ValueError(f'workflow_state_requires_object:{field}')
    if state.get('intent') in {'feedback', 'ui'} and not state.get('targets'):
        raise ValueError('target_required')
    files = inventory(root, config['roots'])
    commands = dict(project.get('commands', {}))
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    covered = set()
    old = state.get('baseline', {})
    changed = {name for name in files.keys() | old.keys() if files.get(name) != old.get(name)}
    if state and 'source_patterns' not in state:
        for name in sorted(changed):
            if old.get(name) is not None and files.get(name) is None and not any(
                    fnmatchcase(name, pattern) for f in config['features'] for pattern in f['sources']):
                result['findings'].append(f'baseline_source_ownership_unavailable:{name}')
    mapping_pending = bool(result['findings'])
    for feature in config['features']:
        identity = feature['id']
        sources = {name: value for name, value in files.items()
                   if any(fnmatchcase(name, pattern) for pattern in feature['sources'])}
        covered.update(sources)
        findings = []
        for pattern in feature['sources']:
            if not any(fnmatchcase(name, pattern) and value is not None for name, value in files.items()):
                findings.append(f'missing_source:{identity}:{pattern}')
        refs = {name: file_hash(root, name) for field in ('map', 'criteria', 'ui') for name in feature.get(field, [])}
        findings.extend(f'missing_reference:{identity}:{name}' for name, value in refs.items() if value is None)
        findings.extend(f'missing_command:{identity}:{name}' for name in feature['checks'] if name not in commands)
        for prevention in feature.get('prevention', []):
            if not all(prevention.get(key) for key in ('failure', 'check', 'normal_exception')):
                findings.append(f'incomplete_prevention:{identity}')
            if prevention.get('check') not in feature['checks']:
                findings.append(f'inactive_prevention:{identity}:{prevention.get("check")}')
        basis = digest({'feature': feature, 'sources': sources, 'references': refs,
                        'commands': {name: commands.get(name) for name in feature['checks']}})
        review = state.get('reviews', {}).get(identity, {})
        # A recorded analysis is a semantic-review input, never a success flag.
        reviewed = current_review(root, review, basis)
        product_findings = review.get('product_findings', []) if isinstance(review, dict) else []
        if isinstance(product_findings, list):
            result['product_findings'].extend({'feature': identity, 'finding': finding}
                for finding in product_findings if isinstance(finding, str) and finding.strip())
        # Preserve ownership across staged deletion and source-map reassignment.
        patterns = feature['sources'] + state.get('source_patterns', {}).get(identity, [])
        affected = sorted(name for name in changed
                          if any(fnmatchcase(name, pattern) for pattern in patterns))
        # Only a predeclared, still-existing document edit can avoid product execution.
        # Changing the declaration during work never retroactively exempts a path.
        documents = feature.get('documentation_only', {})
        original_documents = state.get('documentation_only', {}).get(identity, {})
        verification_changed = [name for name in affected if not (
            name in documents and name in original_documents
            and old.get(name) is not None and files.get(name) is not None)]
        requires = ['map_review']
        if verification_changed and state:
            requires.append('verification')
        if state.get('intent') == 'feedback' and identity in state.get('targets', []):
            requires.extend(['repair', 'regression', 'normal_case'])
        ui_requested = state.get('intent') == 'ui' and identity in state.get('targets', [])
        if ui_requested:
            requires.append('verification')
            if not feature.get('ui'):
                findings.append(f'missing_ui_standard:{identity}')
        if feature.get('ui') or ui_requested:
            requires.append('ui_review')
        mapping_ready = reviewed and not findings
        mapping_pending = mapping_pending or not mapping_ready
        if product_findings:
            requires.append('product_resolution')
        needs_behavior = any(requirement in requires for requirement in ('verification', 'repair', 'regression'))
        behavior = None
        if needs_behavior and reviewed and review.get('bundle'):
            behavior = inspect_evidence(root, feature, commands, review['bundle'])
            if behavior['status'] != 'PASS':
                findings.extend(behavior['findings'])
        if state.get('intent') == 'feedback' and identity in state.get('targets', []) and state.get('input_bases', {}).get(identity) == basis:
            findings.append(f'repair_not_observed:{identity}')
        pending = not reviewed or findings or product_findings or (needs_behavior and (not behavior or behavior['status'] != 'PASS'))
        if pending:
            result['obligations'].append({'id': f'feature:{identity}:{basis}', 'target': identity,
                'basis': basis, 'reason': 'initial_or_changed_inputs', 'changed': affected,
                'verification_changed': verification_changed,
                'requires': requires, 'references': sorted(refs)})
        result['features'].append({'id': identity, 'basis': basis, 'partition': feature['partition'],
                                   'verification_status': ('NOT_REQUIRED' if not needs_behavior else
                                       'PASS' if behavior and behavior['status'] == 'PASS' else 'REQUIRED'),
                                   'reviewed': reviewed, 'mapping_ready': bool(mapping_ready), 'source_count': len(sources)})
        partition = feature['partition']
        prior = result['partitions'].get(partition, 'READY_FOR_REVIEW')
        result['partitions'][partition] = 'PARTIAL' if pending else prior
        result['findings'].extend(findings)
        if not feature['checks']:
            result['unlinked'].append(identity)
    result['unmapped'] = sorted(name for name in files.keys() - covered if files[name] is not None)
    removed = (set(state.get('input_bases', {})) | set(state.get('reviews', {}))) - {f['id'] for f in config['features']}
    for name in sorted(removed):
        basis = digest({'removed': name, 'previous': state.get('input_bases', {}).get(name),
                        'features': config['features'], 'files': files})
        result['retired'].append({'id': name, 'basis': basis})
        review = state.get('retired_reviews', {}).get(name, {})
        if not current_review(root, review, basis):
            mapping_pending = True
            result['findings'].append(f'removed_feature_needs_reconciliation:{name}')
            result['obligations'].append({'id': f'removed:{name}:{basis}', 'target': name,
                'basis': basis, 'reason': 'removed_feature', 'changed': [],
                'requires': ['removal_review'], 'references': sorted({p for f in config['features'] for p in f['map']})})
    result['mapping_status'] = 'PARTIAL' if mapping_pending or result['unmapped'] else 'READY_FOR_REVIEW'
    result['status'] = 'PARTIAL' if result['obligations'] or result['unmapped'] or result['findings'] else 'READY_FOR_REVIEW'
    return result


def inspect_evidence(root, feature, commands, bundle):
    """Reinspect raw execution; submitted review/status strings cannot discharge checks."""
    try:
        path = local_path(root, bundle)
        binding = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(binding, dict) and binding.get('format') == 'unittest-captures-v1':
            return inspect_unittest_evidence(root, feature, commands, binding)
        viewer = runpy.run_path(str(Path(__file__).with_name('verification_results.py')))
        observed = viewer['view_bundle'](path)
        if observed['status'] != 'PASS':
            return {'status': 'BLOCKED', 'findings': observed.get('remaining', ['verification_incomplete'])}
        verified = set()
        for item in observed['items']:
            if item['feature'] != feature['id'] or item['current_status'] != 'PASS':
                continue
            descriptor = commands.get(item['id'])
            expected = descriptor.get('argv') if isinstance(descriptor, dict) else descriptor
            cwd = root / (descriptor.get('working_directory', '.') if isinstance(descriptor, dict) else '.')
            if item['capture']['argv'] == expected and Path(item['capture']['cwd']).resolve() == cwd.resolve():
                verified.add(item['id'])
        missing = set(feature['checks']) - verified
        if missing or not verified:
            return {'status': 'BLOCKED', 'findings': [f'verification_missing:{feature["id"]}:{name}' for name in sorted(missing or {'unconnected'})]}
        return {'status': 'PASS', 'findings': []}
    except (OSError, ValueError, TypeError, KeyError) as error:
        return {'status': 'BLOCKED', 'findings': [f'verification_unavailable:{error}']}


def inspect_unittest_evidence(root, feature, commands, binding):
    """Use the existing native adapter without loading or executing project code."""
    reader = runpy.run_path(str(Path(__file__).with_name('unittest_evidence.py')))
    if binding.get('feature') != feature['id']:
        raise ValueError('verification_feature_mismatch')
    records = binding.get('records')
    if not isinstance(records, list) or not records:
        raise ValueError('verification_records_required')
    verified = set()
    findings = []
    for record in records:
        check = record['check']
        if check not in feature['checks'] or check in verified:
            raise ValueError('duplicate_or_unselected_check')
        descriptor = commands.get(check)
        argv = descriptor.get('argv') if isinstance(descriptor, dict) else descriptor
        if not isinstance(argv, list) or len(argv) < 4 or argv[1:3] != ['-m', 'unittest']:
            raise ValueError('native_unittest_command_required')
        if isinstance(descriptor, dict) and descriptor.get('runtime', 'python') != 'python':
            raise ValueError('native_unittest_runtime_required')
        cwd = local_path(root, descriptor.get('working_directory', '.') if isinstance(descriptor, dict) else '.')
        observed = reader['assess'](local_path(root, record['path']), record['run_id'],
                                   feature['id'], check, [sys.executable, *argv[1:]], cwd.resolve())
        if observed['status'] == 'PASS':
            verified.add(check)
        else:
            findings.append(f'verification_failed:{feature["id"]}:{check}')
    findings.extend(f'verification_missing:{feature["id"]}:{check}'
                    for check in sorted(set(feature['checks']) - verified))
    return {'status': 'BLOCKED' if findings else 'PASS', 'findings': findings,
            'test_commands_executed': 0, 'scope': 'native unittest assertions; local consistency only'}


def inspect_configured(root, project):
    """Used by existing maintain/close boundaries, including when CLI is skipped."""
    config = configuration(project)
    state = None
    if config and config.get('state'):
        path = local_path(root, config['state'])
        if not path.resolve().is_relative_to(root.resolve() / '.work'):
            raise ValueError('state_must_be_task_local_under_work')
        if path.is_file():
            state = json.loads(path.read_text(encoding='utf-8'))
    return inspect_project(root, project, state)


def validate_review(root, review):
    if not isinstance(review, dict):
        raise ValueError('review_must_be_object')
    if not isinstance(review.get('analysis'), str) or not review['analysis'].strip():
        raise ValueError('review_analysis_required')
    product_findings = review.get('product_findings', [])
    if not isinstance(product_findings, list) or any(
            not isinstance(finding, str) or not finding.strip() for finding in product_findings):
        raise ValueError('review_product_findings_must_be_nonempty_strings')
    if (not isinstance(review.get('findings'), list) or not isinstance(review.get('references'), list)
            or not review['references']):
        raise ValueError('review_findings_and_references_required')
    for name in review['references']:
        if not isinstance(name, str) or not name or file_hash(root, name) is None:
            raise ValueError(f'review_reference_missing:{name}')


def current_review(root, review, basis):
    if not isinstance(review, dict) or review.get('basis') != basis:
        return False
    try:
        validate_review(root, review)
    except (OSError, ValueError, TypeError):
        return False
    return not review['findings']


def record_review(root, project, state, review):
    validate_review(root, review)
    result = inspect_project(root, project, state)
    feature = next((item for item in result['features'] + result['retired'] if item['id'] == review.get('feature')), None)
    if feature is None or feature['basis'] != review.get('basis'):
        raise ValueError('stale_or_unknown_review')
    updated = deepcopy(state)
    key = 'retired_reviews' if feature in result['retired'] else 'reviews'
    updated.setdefault(key, {})[review['feature']] = deepcopy(review)
    return updated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['begin', 'audit', 'review', 'accept'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--project', default='.harness/project.yaml')
    state_selection = parser.add_mutually_exclusive_group()
    state_selection.add_argument('--state', help='Task-owned record under .work; audit without it is read-only')
    state_selection.add_argument('--work-id', help='Use the workflow baseline captured by Harness start')
    parser.add_argument('--intent', choices=['init', 'change', 'feedback', 'ui', 'maintain'], default='init')
    parser.add_argument('--target', action='append', default=[])
    parser.add_argument('--review', type=Path)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        project = json.loads(local_path(root, args.project).read_text(encoding='utf-8'))
        state_path = local_path(root, args.state) if args.state else None
        if state_path and not state_path.resolve().is_relative_to(root / '.work'):
            raise ValueError('state_must_be_task_local_under_work')
        state = json.loads(state_path.read_text(encoding='utf-8')) if state_path and state_path.exists() else None
        if state_path and state_path.exists() and state is None:
            raise ValueError('workflow_state_must_be_object')
        if args.work_id:
            if args.action == 'begin':
                raise ValueError('Harness start owns this baseline; use audit or review with --work-id')
            state, state_path = work_record(root, args.work_id)
        if args.action in {'begin', 'review'}:
            if not state_path:
                raise ValueError('state_required')
            write_state = False
            if args.action == 'begin':
                if state is None:
                    state = begin(root, project, args.intent, args.target)
                    state_path.parent.mkdir(parents=True, exist_ok=True)
                    write_state = True
                elif state.get('intent') != args.intent or state.get('targets') != sorted(set(args.target)):
                    raise ValueError('resume_request_mismatch')
            else:
                if state is None or args.review is None:
                    raise ValueError('existing_state_and_review_required')
                state = record_review(root, project, state, json.loads(args.review.read_text(encoding='utf-8')))
                write_state = True
            if write_state:
                # An interrupted attempt must not block the next write or expose partial JSON.
                staging = root / '.work' if args.work_id else state_path.parent
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=staging,
                                                 prefix=state_path.name + '.', suffix='.pending', delete=False) as output:
                    json.dump(state, output, indent=2)
                    temporary = Path(output.name)
                temporary.replace(state_path)
        result = inspect_project(root, project, state)
        if args.action == 'accept':
            result['status'] = 'BLOCKED'
            result['findings'].append('host_protected_acceptance_unavailable')
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
        result = {'status': 'BLOCKED', 'findings': [str(error)]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['status'] in {'READY_FOR_REVIEW', 'NOT_CONFIGURED'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
