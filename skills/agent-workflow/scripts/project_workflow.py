# Generated file. Do not edit directly.
# Source: authoring/scripts/project_workflow.py
# Source-SHA256: 06a323edf2cd441794a112fc6e0d36f6ae4a74fd6f146705e6ab8327cec01900

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


def resolve_report_path(root, value, report_dir):
    """Expand only an explicit native-report path, never general command text."""
    if '{report_dir}' not in value:
        return value
    if not value.startswith('{report_dir}/') or not report_dir:
        raise ValueError('report_directory_required_for_path_template')
    suffix = value[len('{report_dir}/'):]
    if not suffix or '{report_dir}' in suffix or '..' in Path(suffix).parts:
        raise ValueError('invalid_report_path_template')
    directory = Path(report_dir)
    if directory.is_absolute():
        directory = directory.relative_to(root.resolve())
    directory = local_path(root, str(directory)).resolve()
    return str(local_path(directory, suffix))


def resolve_report_command(root, argv, report_dir=None):
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) for arg in argv):
        raise ValueError('registered_command_requires_argv')
    if '{report_dir}' in argv[0]:
        raise ValueError('report_template_cannot_select_executable')
    return [resolve_report_path(root, arg, report_dir) for arg in argv]


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
        coverage = feature.get('coverage', [])
        if not isinstance(coverage, list):
            raise ValueError('coverage_must_be_list')
        coverage_ids = []
        for row in coverage:
            if not isinstance(row, dict) or any(not isinstance(row.get(key), str) or not row[key].strip()
                    for key in ('id', 'requirement', 'outcome')):
                raise ValueError('coverage_requires_id_requirement_outcome')
            for axis, allowed in (('perspectives', {'business', 'architecture'}),
                                  ('areas', {'FE', 'BE/API', 'Domain'})):
                values = row.get(axis)
                if (not isinstance(values, list) or not values or any(not isinstance(v, str) or v not in allowed for v in values)
                        or len(values) != len(set(values))):
                    raise ValueError(f'invalid_coverage_axis:{axis}')
            if row.get('kind') not in {'test', 'review'} or row.get('method', 'direct') not in {'direct', 'cross-layer', 'e2e'}:
                raise ValueError('invalid_coverage_kind_or_method')
            if 'check' in row and (row['kind'] != 'test' or not isinstance(row['check'], str) or not row['check']):
                raise ValueError('invalid_coverage_check')
            coverage_ids.append(row['id'])
        if len(coverage_ids) != len(set(coverage_ids)):
            raise ValueError('duplicate_coverage_identity')
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


def coverage_rows(feature, review, basis, items=(), *, current_basis=None):
    """Declared scope only; the Agent decides which requirements/layers apply."""
    tests = {item['id']: item for item in items if item['feature'] == feature['id']}
    rows = []
    for declaration in feature.get('coverage', []):
        row = dict(declaration, feature=feature['id'], reasons=[], evidence=None)
        if row['kind'] == 'review':
            entry = review.get('scope_reviews', {}).get(row['id'], {})
            row['historical_status'] = entry.get('status', 'NOT_RUN')
            row['status'] = row['historical_status']
            if entry:
                row['evidence'] = {'analysis': entry.get('analysis'), 'references': entry.get('references', []),
                                   'reason': entry.get('reason'), 'kind': 'Agent semantic review'}
                if review.get('basis') != basis or (current_basis is not None and current_basis != basis):
                    row['status'] = 'STALE'
                    row['reasons'].append('semantic_review_basis_changed')
        else:
            item = tests.get(row.get('check'))
            row['historical_status'] = item['historical_status'] if item else 'NOT_RUN'
            if not row.get('check') or row['check'] not in feature['checks']:
                row['status'] = 'MISSING'
                row['reasons'].append('active_check_link_missing')
            elif not item:
                row['status'] = 'NOT_RUN'
                row['reasons'].append('check_not_in_result')
            else:
                row['status'] = ('NOT_REQUIRED' if not item['selected'] else
                                 'STALE' if item['current_reuse'] == 'STALE' else
                                 'NOT_RUN' if item['historical_status'] == 'NOT_RUN' else
                                 'BLOCKED' if item['current_status'] == 'UNKNOWN' else item['current_status'])
                row['reasons'] = item['reasons']
                row['evidence'] = {key: item[key] for key in ('run_id', 'capture', 'raw', 'selection', 'current_reuse')}
        rows.append(row)
    return rows


def coverage_summary(rows):
    return {'status': ('NOT_CONFIGURED' if not rows else
                       'COMPLETE' if all(row['status'] in {'PASS', 'NOT_REQUIRED'} for row in rows) else 'PARTIAL'),
            'rows': rows, 'gaps': [f"{row['feature']}/{row['id']}:{row['status']}" for row in rows
                                  if row['status'] not in {'PASS', 'NOT_REQUIRED'}],
            'perspectives': {axis: {status: sum(axis in row['perspectives'] and row['status'] == status for row in rows)
                                   for status in sorted({row['status'] for row in rows if axis in row['perspectives']})}
                             for axis in ('business', 'architecture')},
            'areas': {axis: {status: sum(axis in row['areas'] and row['status'] == status for row in rows)
                            for status in sorted({row['status'] for row in rows if axis in row['areas']})}
                      for axis in ('FE', 'BE/API', 'Domain')}}


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
    features = inspect_project(root, project)['features']
    feedback = {}
    if config.get('state'):
        prior = local_path(root, config['state'])
        if not prior.resolve().is_relative_to(root.resolve() / '.work'):
            raise ValueError('state_must_be_task_local_under_work')
        if prior.is_file():
            saved = json.loads(prior.read_text(encoding='utf-8'))
            if not isinstance(saved, dict) or saved.get('root') != str(root.resolve()) or saved.get('schema_version') != 1:
                raise ValueError('work_target_mismatch')
            feedback = deepcopy(saved.get('feedback', {}))
    return {'schema_version': 1, 'root': str(root.resolve()), 'intent': intent,
            'targets': sorted(set(targets)), 'base': git(root, 'rev-parse', 'HEAD').decode().strip(),
            'dirty_baseline': git(root, 'status', '--porcelain').decode('utf-8'),
            'baseline': inventory(root, config['roots']), 'reviews': {}, 'feedback': feedback,
            'source_patterns': {f['id']: list(f['sources']) for f in config['features']},
            'documentation_only': {f['id']: dict(f.get('documentation_only', {})) for f in config['features']},
            'input_bases': {item['id']: item['basis'] for item in features},
            'verification_bases': {item['id']: item['verification_basis'] for item in features}}


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
            state['feedback'] = deepcopy(previous.get('feedback', {}))
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
        if key not in {'reviews', 'retired_reviews', 'feedback'} and state.get(key) != value:
            raise ValueError(f'work_workflow_baseline_changed:{key}')
    return state, directory / 'workflow.json'


def inspect_project(root, project, state=None, *, file_inventory=None, evidence_resolver=None):
    """Host callers supply trusted inventory/evidence and a protected snapshot root.

    Reference and semantic-review reads still use root; injected inputs alone do
    not establish protected acceptance. Ordinary audit keeps its local adapters.
    """
    root = root.resolve()
    config = configuration(project)
    result = {'status': 'NOT_CONFIGURED', 'mapping_status': 'NOT_CONFIGURED', 'enforcement': 'BLOCKED',
              'trust': 'editable local consistency; host-protected acceptance unavailable',
              'obligations': [], 'features': [], 'partitions': {}, 'unmapped': [],
              'unlinked': [], 'findings': [], 'product_findings': [], 'retired': [], 'coverage': coverage_summary([]),
              'feedback': []}
    if config is None:
        return result
    if state is not None and not isinstance(state, dict):
        raise ValueError('workflow_state_must_be_object')
    if state is not None and (state.get('schema_version') != 1 or state.get('root') != str(root)):
        raise ValueError('work_target_mismatch')
    if state is not None and not isinstance(state.get('baseline'), dict):
        raise ValueError('workflow_baseline_required')
    state = state or {}
    for field in ('reviews', 'retired_reviews', 'baseline', 'input_bases', 'verification_bases', 'source_patterns', 'documentation_only'):
        if not isinstance(state.get(field, {}), dict):
            raise ValueError(f'workflow_state_requires_object:{field}')
    if state.get('intent') in {'feedback', 'ui'} and not state.get('targets'):
        raise ValueError('target_required')
    files = inventory(root, config['roots']) if file_inventory is None else file_inventory
    commands = dict(project.get('commands', {}))
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    result['feedback'] = inspect_feedback(root, config, state)
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
        refs.update({row['requirement']: file_hash(root, row['requirement']) for row in feature.get('coverage', [])})
        findings.extend(f'missing_reference:{identity}:{name}' for name, value in refs.items() if value is None)
        findings.extend(f'missing_command:{identity}:{name}' for name in feature['checks'] if name not in commands)
        for prevention in feature.get('prevention', []):
            if not all(prevention.get(key) for key in ('failure', 'check', 'normal_exception')):
                findings.append(f'incomplete_prevention:{identity}')
            if prevention.get('check') not in feature['checks']:
                findings.append(f'inactive_prevention:{identity}:{prevention.get("check")}')
        basis = digest({'feature': feature, 'sources': sources, 'references': refs,
                        'commands': {name: commands.get(name) for name in feature['checks']}})
        verification_basis = digest({
            'references': {field: {name: refs[name] for name in feature.get(field, [])}
                           for field in ('criteria', 'ui')},
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
        # Legacy records cannot distinguish reference changes from map-only edits.
        # Preserve their obligations conservatively; new baselines keep that distinction.
        verification_inputs_changed = (
            state['verification_bases'].get(identity) != verification_basis
            if 'verification_bases' in state else
            state.get('input_bases', {}).get(identity) != basis)
        if state and (verification_changed or verification_inputs_changed):
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
        unresolved_feedback = [item for item in result['feedback'] if item['feature'] == identity and item['status'] != 'RESOLVED']
        if unresolved_feedback:
            requires.extend(['repair', 'regression', 'normal_case'])
            findings.extend(f'feedback_pending:{item["id"]}:{part}' for item in unresolved_feedback for part in item['remaining'])
        needs_behavior = any(requirement in requires for requirement in ('verification', 'repair', 'regression'))
        behavior = None
        if needs_behavior and reviewed:
            if evidence_resolver is not None:
                behavior = evidence_resolver(root, feature, commands)
            elif review.get('bundle'):
                behavior = inspect_evidence(root, feature, commands, review['bundle'])
            if behavior is not None and behavior['status'] != 'PASS':
                findings.extend(behavior['findings'])
        if state.get('intent') == 'feedback' and identity in state.get('targets', []) and state.get('input_bases', {}).get(identity) == basis:
            findings.append(f'repair_not_observed:{identity}')
        pending = not reviewed or findings or product_findings or (needs_behavior and (not behavior or behavior['status'] != 'PASS'))
        rows = coverage_rows(feature, review, basis, behavior.get('items', []) if behavior else [])
        result['coverage']['rows'].extend(rows)
        scope_gaps = [row['id'] for row in rows if row['kind'] == 'review' and row['status'] not in {'PASS', 'NOT_REQUIRED'}
                      or row['status'] == 'MISSING']
        if scope_gaps:
            pending = True
            requires.append('scope_review_or_connection')
            findings.extend(f'coverage_gap:{identity}:{name}' for name in scope_gaps)
        if pending:
            result['obligations'].append({'id': f'feature:{identity}:{basis}', 'target': identity,
                'basis': basis, 'reason': 'initial_or_changed_inputs', 'changed': affected,
                'verification_changed': verification_changed,
                'verification_inputs_changed': bool(state and verification_inputs_changed),
                'requires': requires, 'references': sorted(refs)})
        result['features'].append({'id': identity, 'basis': basis, 'partition': feature['partition'],
                                   'verification_basis': verification_basis,
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
    removed |= {item['feature'] for item in result['feedback'] if item['feature'] not in {f['id'] for f in config['features']}}
    for name in sorted(removed):
        basis = digest({'removed': name, 'previous': state.get('input_bases', {}).get(name),
                        'features': config['features'], 'files': files})
        result['retired'].append({'id': name, 'basis': basis})
        review = state.get('retired_reviews', {}).get(name, {})
        reviewed = current_review(root, review, basis)
        prior_review = state.get('reviews', {}).get(name, {})
        for candidate in (prior_review, review):
            if not isinstance(candidate, dict):
                raise ValueError('workflow_review_must_be_object')
            gaps = candidate.get('product_findings', [])
            if not isinstance(gaps, list) or any(not isinstance(gap, str) or not gap.strip() for gap in gaps):
                raise ValueError('review_product_findings_must_be_nonempty_strings')
        previous = prior_review.get('product_findings', [])
        product_findings = review.get('product_findings', previous) if reviewed else (
            previous + review.get('product_findings', []))
        result['product_findings'].extend({'feature': name, 'finding': finding}
            for finding in dict.fromkeys(product_findings))
        if not reviewed:
            mapping_pending = True
            result['findings'].append(f'removed_feature_needs_reconciliation:{name}')
        if not reviewed or product_findings:
            result['obligations'].append({'id': f'removed:{name}:{basis}', 'target': name,
                'basis': basis, 'reason': 'removed_feature', 'changed': [],
                'requires': (['removal_review'] if not reviewed else []) +
                            (['product_resolution'] if product_findings else []),
                'references': sorted({p for f in config['features'] for p in f['map']})})
    result['mapping_status'] = 'PARTIAL' if mapping_pending or result['unmapped'] else 'READY_FOR_REVIEW'
    result['coverage'] = coverage_summary(result['coverage']['rows'])
    result['status'] = 'PARTIAL' if result['obligations'] or result['unmapped'] or result['findings'] else 'READY_FOR_REVIEW'
    if any(item['status'] != 'RESOLVED' for item in result['feedback']):
        result['status'] = 'PARTIAL'
    return result


def record_feedback(root, project, state, entry):
    if not isinstance(entry, dict) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', str(entry.get('id', ''))):
        raise ValueError('feedback_identity_required')
    feature = next((f for f in configuration(project)['features'] if f['id'] == entry.get('feature')), None)
    if feature is None:
        raise ValueError('feedback_feature_unknown')
    previous = state.get('feedback', {}).get(entry['id'], {})
    if previous and previous['feature'] != entry['feature']:
        raise ValueError('feedback_target_changed')
    updated = dict(previous, **deepcopy(entry))
    for field in ('expected', 'observed', 'reproduction'):
        if not isinstance(updated.get(field), str) or not updated[field].strip():
            raise ValueError(f'feedback_requires:{field}')
    for field in ('trace', 'root_cause', 'failed_prevention', 'red_bundle', 'green_bundle'):
        if field in updated and (not isinstance(updated[field], str) or not updated[field].strip()):
            raise ValueError(f'feedback_requires_text:{field}')
    if 'repair_paths' in updated and (not isinstance(updated['repair_paths'], list) or
            any(not isinstance(name, str) or not name for name in updated['repair_paths'])):
        raise ValueError('feedback_repair_paths_must_be_paths')
    # The captured work baseline, not caller-supplied hashes, owns repair identity.
    updated['source_before'] = previous.get('source_before', {
        name: value for name, value in state['baseline'].items()
        if any(fnmatchcase(name, pattern) for pattern in feature['sources'])})
    result = deepcopy(state)
    result.setdefault('feedback', {})[entry['id']] = updated
    return result


def feedback_evidence(root, feature, entry):
    """Fixed viewer/raw joins, never run a submitted reproduction or command."""
    viewer = runpy.run_path(str(Path(__file__).with_name('verification_results.py')))
    red = viewer['view_bundle'](local_path(root, entry['red_bundle']))
    green = viewer['view_bundle'](local_path(root, entry['green_bundle']))
    check = entry['guardrail']['check']
    before = next((i for i in red.get('items', []) if i['feature'] == feature['id'] and i['id'] == check), None)
    after = next((i for i in green.get('items', []) if i['feature'] == feature['id'] and i['id'] == check), None)
    reasons = []
    if not before or before['historical_status'] != 'ISSUES':
        reasons.append('original_failure_evidence_missing')
    if before and (before['capture']['execution'] != 'exited' or any(
            reason.startswith(('raw_producer', 'capture_feature', 'capture_check', 'capture_run', 'assessment_evidence'))
            for reason in before['reasons'])):
        reasons.append('original_failure_evidence_unbound')
    if not after or after['current_status'] != 'PASS':
        reasons.append('repair_revalidation_required')
    def assertions(item):
        return [obs for raw in (item or {}).get('raw', []) for obs in raw.get('observations', [])]
    regression = entry['guardrail']['regression_pointer']
    normal = entry['guardrail']['normal_pointer']
    failing = [obs['assertion'] for obs in assertions(before) if obs['assertion']['pointer'] == regression and not obs['matched']]
    passing = [obs['assertion'] for obs in assertions(after) if obs['assertion']['pointer'] == regression and obs['matched']]
    if not failing or not any(assertion in passing for assertion in failing):
        reasons.append('original_criterion_not_preserved')
    if normal == regression or not any(obs['assertion']['pointer'] == normal and obs['matched'] for obs in assertions(after)):
        reasons.append('nearby_normal_evidence_missing')
    if before and after:
        descriptor = green['bundle']
        bound = viewer['_read_json'](viewer['_bundle_file'](descriptor['plan'],
            base=local_path(root, entry['green_bundle']).parent, label='feedback plan'))[0]
        scope = bound.get('workflow_scope', {})
        if scope.get('root') != str(root.resolve()) or feature not in scope.get('features', []):
            reasons.append('prepared_project_binding_required')
    return reasons


def inspect_feedback(root, config, state):
    entries = state.get('feedback', {})
    if not isinstance(entries, dict):
        raise ValueError('feedback_must_be_object')
    features = {feature['id']: feature for feature in config['features']}
    result = []
    for identity, entry in entries.items():
        if not isinstance(entry, dict) or entry.get('id') != identity:
            raise ValueError('feedback_record_identity_mismatch')
        feature = features.get(entry.get('feature'))
        remaining = [key for key in ('trace', 'root_cause', 'failed_prevention', 'repair_paths', 'guardrail', 'red_bundle', 'green_bundle')
                     if not entry.get(key)]
        if feature is None:
            remaining.append('feature_removed_needs_reconciliation')
        else:
            paths = entry.get('repair_paths', [])
            refs = {name for field in ('map', 'criteria', 'ui') for name in feature.get(field, [])}
            if not isinstance(paths, list) or not paths or any(name in refs or not any(fnmatchcase(name, p) for p in feature['sources'])
                    or file_hash(root, name) == entry.get('source_before', {}).get(name) for name in paths):
                remaining.append('owner_repair_not_observed')
            guardrail = entry.get('guardrail', {})
            if not isinstance(guardrail, dict):
                raise ValueError('feedback_guardrail_must_be_object')
            required = ('failure', 'scope', 'check', 'normal_exception', 'reconsider', 'regression_pointer', 'normal_pointer')
            remaining.extend(f'guardrail.{key}' for key in required if not guardrail.get(key))
            if guardrail and (guardrail.get('check') not in feature['checks'] or not any(
                    all(p.get(key) == guardrail.get(key) for key in ('failure', 'check', 'normal_exception', 'scope', 'reconsider'))
                    for p in feature.get('prevention', []))):
                remaining.append('active_prevention_link_missing')
            if entry.get('red_bundle') and entry.get('green_bundle') and all(guardrail.get(key) for key in required):
                try:
                    remaining.extend(feedback_evidence(root, feature, entry))
                except (OSError, ValueError, TypeError, KeyError):
                    remaining.append('repair_evidence_unavailable')
        result.append(dict(entry, status='OPEN' if remaining else 'RESOLVED', remaining=sorted(set(remaining))))
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
            return {'status': 'BLOCKED', 'findings': observed.get('remaining', ['verification_incomplete']),
                    'items': observed.get('items', [])}
        verified = set()
        for item in observed['items']:
            if item['feature'] != feature['id'] or item['current_status'] != 'PASS':
                continue
            descriptor = commands.get(item['id'])
            expected = resolve_report_command(root,
                descriptor.get('argv') if isinstance(descriptor, dict) else descriptor,
                item['conditions']['expected']['command'].get('report_dir'))
            cwd = root / (descriptor.get('working_directory', '.') if isinstance(descriptor, dict) else '.')
            if item['capture']['argv'] == expected and Path(item['capture']['cwd']).resolve() == cwd.resolve():
                verified.add(item['id'])
        missing = set(feature['checks']) - verified
        if missing or not verified:
            return {'status': 'BLOCKED', 'findings': [f'verification_missing:{feature["id"]}:{name}' for name in sorted(missing or {'unconnected'})]}
        return {'status': 'PASS', 'findings': [], 'items': observed['items']}
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
            if state is None:
                raise ValueError('workflow_state_must_be_object')
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
    scopes = review.get('scope_reviews', {})
    if not isinstance(scopes, dict):
        raise ValueError('scope_reviews_must_be_object')
    for entry in scopes.values():
        if not isinstance(entry, dict) or entry.get('status') not in {'PASS', 'ISSUES', 'BLOCKED', 'NOT_REQUIRED'}:
            raise ValueError('invalid_scope_review_status')
        if not isinstance(entry.get('analysis'), str) or not entry['analysis'].strip():
            raise ValueError('scope_review_analysis_required')
        if entry['status'] == 'NOT_REQUIRED' and not entry.get('reason'):
            raise ValueError('scope_exclusion_reason_required')
        if not isinstance(entry.get('references'), list) or not entry['references']:
            raise ValueError('scope_review_references_required')
        for name in entry['references']:
            if file_hash(root, name) is None:
                raise ValueError(f'scope_review_reference_missing:{name}')


def current_review(root, review, basis):
    if not isinstance(review, dict) or review.get('basis') != basis:
        return False
    try:
        validate_review(root, review)
        if any(file_hash(root, name) != value for name, value in review.get('reference_hashes', {}).items()):
            return False
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
    updated[key][review['feature']]['reference_hashes'] = {
        name: file_hash(root, name) for name in dict.fromkeys(review['references'] +
        [name for entry in review.get('scope_reviews', {}).values() for name in entry['references']])}
    return updated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['begin', 'audit', 'review', 'feedback', 'accept'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--project', default='.harness/project.yaml')
    state_selection = parser.add_mutually_exclusive_group()
    state_selection.add_argument('--state', help='Task-owned record under .work; audit without it is read-only')
    state_selection.add_argument('--work-id', help='Use the workflow baseline captured by Harness start')
    parser.add_argument('--intent', choices=['init', 'change', 'feedback', 'ui', 'maintain'], default='init')
    parser.add_argument('--target', action='append', default=[])
    parser.add_argument('--review', type=Path)
    parser.add_argument('--feedback', type=Path, help='Register/update a complaint and repair chain in the existing work state')
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
        if args.action in {'begin', 'review', 'feedback'}:
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
            elif args.action == 'feedback':
                if state is None or args.feedback is None:
                    raise ValueError('existing_state_and_feedback_required')
                state = record_feedback(root, project, state, json.loads(args.feedback.read_text(encoding='utf-8')))
                write_state = True
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
