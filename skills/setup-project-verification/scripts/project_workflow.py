# Generated file. Do not edit directly.
# Source: authoring/scripts/project_workflow.py
# Source-SHA256: d3400c2bbd32fb659389d9064206493fa84e092601bd5cf4b145f21891a95515

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
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

# Script and packaged Skill entrypoints share the adjacent canonical modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))


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


def source_patterns(config, feature):
    return list(dict.fromkeys(feature['sources'] + [pattern
        for system in config.get('ui_systems', {}).values() if feature['id'] in system['consumers']
        for field in ('tokens', 'components') for pattern in system[field]]))


def outside_inventory(root, config, base, previous=()):
    """Only changed, nonignored Git paths; never broaden the content inventory."""
    names = set(git(root, 'diff', '--name-only', '-z', base).decode('utf-8').split('\0'))
    names.update(git(root, 'ls-files', '-z', '--others', '--exclude-standard').decode('utf-8').split('\0'))
    names.update(previous)
    references = {name for feature in config['features'] for field in ('map', 'criteria', 'ui')
                  for name in feature.get(field, [])}
    references.update(row['requirement'] for feature in config['features'] for row in feature.get('coverage', []))
    references.update(system['guide'] for system in config.get('ui_systems', {}).values())
    references.add('.harness/project.yaml')
    result = {}
    for name in sorted(names - {''} - references):
        if name.startswith('.work/') or any(name == prefix or name.startswith(prefix.rstrip('/') + '/') for prefix in config['roots']):
            continue
        try:
            result[name] = file_hash(root, name) or 'DELETED'
        except ValueError:
            # Private or aliased paths remain visible without reading their bytes.
            result[name] = 'UNINSPECTED'
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
                or any(part in {'.', '..', '.git', '.work'} for part in prefix.replace(chr(92), '/').split('/'))):
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
    systems = config.get('ui_systems', {})
    if not isinstance(systems, dict):
        raise ValueError('ui_systems_must_be_object')
    for identity, system in systems.items():
        if not isinstance(identity, str) or not identity or not isinstance(system, dict) or not isinstance(system.get('guide'), str) or not system['guide']:
            raise ValueError('ui_system_requires_identity_and_guide')
        for field in ('tokens', 'components', 'consumers'):
            if not isinstance(system.get(field), list) or any(not isinstance(v, str) or not v for v in system[field]):
                raise ValueError(f'ui_system_requires:{field}')
        if not isinstance(system.get('exceptions', []), list):
            raise ValueError('ui_exceptions_must_be_list')
        for exception in system.get('exceptions', []):
            if not isinstance(exception, dict) or any(not isinstance(exception.get(key), str) or not exception[key].strip()
                    for key in ('feature', 'reason', 'reference', 'reconsider')):
                raise ValueError('ui_exception_requires_scope_reason_reference_reconsider')
    return config


def inspect_ui_systems(root, config, files):
    features = {f['id'] for f in config['features']}
    result = []
    for identity, system in config.get('ui_systems', {}).items():
        sources, findings = {}, []
        for field in ('tokens', 'components'):
            if not system[field]:
                findings.append(f'missing_ui_owner:{identity}:{field}')
            for pattern in system[field]:
                local_path(root, pattern)
                matched = {name: value for name, value in files.items() if fnmatchcase(name, pattern) and value is not None}
                if not matched:
                    findings.append(f'missing_ui_owner:{identity}:{pattern}')
                sources.update(matched)
        references = {name: file_hash(root, name) for name in [system['guide']] +
                      [entry['reference'] for entry in system.get('exceptions', [])]}
        if references[system['guide']] is None:
            findings.append(f'missing_ui_guide:{identity}:{system["guide"]}')
        findings.extend(f'missing_ui_exception_reference:{identity}:{entry["reference"]}' for entry in system.get('exceptions', [])
                        if references[entry['reference']] is None)
        findings.extend(f'removed_ui_consumer:{identity}:{name}' for name in system['consumers'] if name not in features)
        findings.extend(f'ui_exception_consumer_unlinked:{identity}:{entry["feature"]}' for entry in system.get('exceptions', [])
                        if entry['feature'] not in system['consumers'])
        result.append(dict(system, id=identity, source_hashes=sources, reference_hashes=references,
                           status='NEEDS_REPAIR' if findings else 'CONNECTED', findings=findings))
    return result


def coverage_rows(feature, review, basis, items=(), *, current_basis=None, semantic_valid=True, scope_states=None):
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
                                   'reason': entry.get('reason'), 'architecture': entry.get('architecture'),
                                   'kind': 'Agent semantic review', 'sufficiency': 'Agent judgment; structural evidence is not semantic proof'}
                if review.get('basis') != basis or (current_basis is not None and current_basis != basis):
                    row['status'] = 'STALE'
                    row['reasons'].append('semantic_review_basis_changed')
                elif (scope_states or {}).get(row['id']) == 'STALE':
                    row['status'] = 'STALE'
                    row['reasons'].append('scope_review_reference_changed')
                elif not semantic_valid or (scope_states or {}).get(row['id']) == 'BLOCKED':
                    row['status'] = 'BLOCKED'
                    row['reasons'].append('semantic_review_invalid_or_unbound')
                elif 'architecture' in row['perspectives'] and entry['status'] != 'NOT_REQUIRED' and not entry.get('architecture'):
                    row['status'] = 'BLOCKED'
                    row['reasons'].append('architecture_evidence_missing')
                elif any(finding['status'] == 'open' for finding in entry.get('architecture', {}).get('findings', [])):
                    row['status'] = 'ISSUES'
                    row['reasons'].append('architecture_findings_unresolved')
        else:
            item = tests.get(row.get('check'))
            row['historical_status'] = item['historical_status'] if item else 'NOT_RUN'
            decision = review.get('scope_reviews', {}).get(row['id'], {})
            if decision.get('status') == 'NOT_REQUIRED' and decision.get('reason') and review.get('basis') == basis:
                row['status'] = 'NOT_REQUIRED'
                row['evidence'] = {'kind': 'Agent scope exclusion', **decision}
                if (scope_states or {}).get(row['id']) in {'STALE', 'BLOCKED'}:
                    row['status'] = scope_states[row['id']]
                    row['reasons'].append('scope_exclusion_reference_changed_or_invalid')
            elif not row.get('check') or row['check'] not in feature['checks']:
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


def scope_matrix(feature, review, basis, rows, *, current_basis=None, scope_states=None):
    """Six projections of existing review decisions, never inferred test coverage."""
    indexed = {row['id']: row for row in rows}
    matrix = []
    for perspective in ('business', 'architecture'):
        for area in ('FE', 'BE/API', 'Domain'):
            key = perspective + ':' + area
            decision = review.get('scope_reviews', {}).get(key, {})
            applicability = decision.get('status', 'UNDECIDED')
            links = decision.get('coverage', [])
            reasons = []
            if decision and (review.get('basis') != basis or current_basis is not None and current_basis != basis):
                applicability = 'STALE'
                reasons.append('scope_decision_basis_changed')
            elif decision and (scope_states or {}).get(key) in {'STALE', 'BLOCKED'}:
                applicability = scope_states[key]
                reasons.append('scope_decision_reference_changed_or_invalid')
            linked = [indexed[name] for name in links if name in indexed
                      and perspective in indexed[name]['perspectives'] and area in indexed[name]['areas']]
            statuses = list(dict.fromkeys(row['status'] for row in linked))
            if applicability == 'REQUIRED':
                omitted = [row['id'] for row in rows if perspective in row['perspectives'] and area in row['areas']
                           and row['id'] not in links and row['status'] != 'NOT_REQUIRED']
                if omitted:
                    statuses.append('MISSING')
                    reasons.extend('scope_requirement_unaccounted:' + name for name in omitted)
                if len(linked) != len(links) or not links:
                    statuses.append('MISSING')
                    reasons.append('scope_requirement_connection_missing')
                status = next((s for s in ('ISSUES', 'BLOCKED', 'STALE', 'MISSING', 'NOT_RUN', 'UNKNOWN') if s in statuses), 'PASS')
                if 'NOT_REQUIRED' in statuses:
                    status = 'MISSING'
                    reasons.append('required_scope_has_excluded_evidence')
            else:
                status = applicability
            matrix.append({'feature': feature['id'], 'perspective': perspective, 'area': area,
                           'applicability': applicability, 'status': status, 'statuses': statuses,
                           'coverage': [row['id'] for row in linked], 'decision': deepcopy(decision), 'reasons': reasons})
    return matrix


def coverage_summary(rows, matrix=()):
    registered = ('NOT_CONFIGURED' if not rows else
                  'COMPLETE' if all(row['status'] in {'PASS', 'NOT_REQUIRED'} for row in rows) else 'PARTIAL')
    active = [cell for cell in matrix if cell.get('in_task', True)]
    targets = {cell['feature'] for cell in active}
    task_rows = [row for row in rows if row['feature'] in targets]
    return {'status': ('COMPLETE' if active and all(cell['status'] in {'PASS', 'NOT_REQUIRED'} for cell in active)
                       and all(row['status'] in {'PASS', 'NOT_REQUIRED'} for row in task_rows)
                       else 'NOT_REQUIRED' if matrix and not active
                       else 'PARTIAL' if rows or matrix else 'NOT_CONFIGURED'),
            'registered_status': registered, 'scope': 'Agent-declared task scope; completeness of discovery is not attested',
            'matrix': list(matrix),
            'rows': rows, 'gaps': [f"{row['feature']}/{row['id']}:{row['status']}" for row in rows
                                  if row['status'] not in {'PASS', 'NOT_REQUIRED'}],
            'perspectives': {axis: {status: sum(axis in row['perspectives'] and row['status'] == status for row in rows)
                                   for status in sorted({row['status'] for row in rows if axis in row['perspectives']})}
                             for axis in ('business', 'architecture')},
            'areas': {axis: {status: sum(axis in row['areas'] and row['status'] == status for row in rows)
                            for status in sorted({row['status'] for row in rows if axis in row['areas']})}
                      for axis in ('FE', 'BE/API', 'Domain')}}


def request_details(root, summary=None, outcome_refs=()):
    if summary is None and not outcome_refs:
        return None
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError('request_summary_required')
    references = list(dict.fromkeys(outcome_refs))
    for name in references:
        if not isinstance(name, str) or not name or file_hash(root, name) is None:
            raise ValueError('request_outcome_reference_missing')
    return {'summary': summary.strip(), 'outcome_refs': references}


def begin(root, project, intent, targets=(), *, prior_state=None, request_summary=None, outcome_refs=()):
    if intent not in {'init', 'change', 'feedback', 'ui', 'maintain', 'diagnose'}:
        raise ValueError('unsupported_work_intent')
    if intent in {'feedback', 'ui'} and not targets:
        raise ValueError('target_required')
    request = request_details(root, request_summary, outcome_refs)
    config = configuration(project)
    if config is None:
        if intent == 'diagnose' and request:
            if prior_state is not None and (prior_state.get('root') != str(root.resolve()) or prior_state.get('schema_version') != 1):
                raise ValueError('work_target_mismatch')
            return {'schema_version': 1, 'task_id': str(uuid.uuid4()), 'root': str(root.resolve()),
                    'intent': intent, 'request': request, 'targets': sorted(set(targets)),
                    'base': git(root, 'rev-parse', 'HEAD').decode().strip(),
                    'dirty_baseline': git(root, 'status', '--porcelain').decode('utf-8'),
                    'baseline': {}, 'reviews': {}, 'feedback': {}, 'results': {},
                    **({'investigation': deepcopy(prior_state['investigation'])}
                       if prior_state and prior_state.get('investigation') else {})}
        raise ValueError('workflow_not_configured')
    if set(targets) - {f['id'] for f in config['features']}:
        raise ValueError('unknown_target')
    files = inventory(root, config['roots'])
    features = inspect_project(root, project, file_inventory=files)['features']
    feedback = {}
    results = {}
    reviews = {}
    retired_reviews = {}
    investigation = {}
    check_links = {f['id']: {'checks': list(f['checks']), 'prevention': deepcopy(f.get('prevention', [])),
                            'criteria_before': {name: file_hash(root, name) for name in f['criteria']}}
                   for f in config['features']}
    if prior_state is not None or config.get('state'):
        prior = local_path(root, config['state']) if prior_state is None else None
        if prior is not None and not prior.resolve().is_relative_to(root.resolve() / '.work'):
            raise ValueError('state_must_be_task_local_under_work')
        if prior_state is not None or prior.is_file():
            saved = prior_state if prior_state is not None else json.loads(prior.read_text(encoding='utf-8'))
            if not isinstance(saved, dict) or saved.get('root') != str(root.resolve()) or saved.get('schema_version') != 1:
                raise ValueError('work_target_mismatch')
            feedback = deepcopy(saved.get('feedback', {}))
            observed = saved.get('investigation', {})
            if observed and (not targets or any(fnmatchcase(name, pattern) for name in observed['source_refs']
                    for feature in config['features'] if feature['id'] in targets for pattern in feature['sources'])):
                investigation = deepcopy(observed)
            current = inspect_project(root, project, saved, file_inventory=files)
            reusable = {item['id'] for item in current['features'] if item['reviewed']}
            for key, review in saved.get('reviews', {}).items():
                unresolved = [f for f in architecture_findings(review) if f['status'] == 'open']
                if key in reusable or review.get('product_findings') or unresolved:
                    reviews[key] = deepcopy(review)
                    reviews[key]['scope_reviews'] = {}
                    reviews[key]['inherited_architecture_findings'] = deepcopy(unresolved)
            retired_reviews = deepcopy(saved.get('retired_reviews', {}))
            results = deepcopy(saved.get('results', {}))
            for identity, review in saved.get('reviews', {}).items():
                if review.get('bundle'):
                    links = results.setdefault(identity, [])
                    if review['bundle'] not in links:
                        links.append(review['bundle'])
            for pending in current['check_retirements']:
                if pending['status'] == 'BLOCKED' and pending['feature'] in check_links:
                    links = check_links[pending['feature']]
                    prior_links = saved['check_links'][pending['feature']]
                    if pending['check'] not in links['checks']:
                        links['checks'].append(pending['check'])
                    links['prevention'].extend(p for p in prior_links.get('prevention', [])
                                               if p.get('check') == pending['check'] and p not in links['prevention'])
                    links['criteria_before'] = deepcopy(prior_links.get('criteria_before', {}))
    return {'schema_version': 1, 'task_id': str(uuid.uuid4()), 'root': str(root.resolve()), 'intent': intent, 'request': request,
            'targets': sorted(set(targets)), 'base': git(root, 'rev-parse', 'HEAD').decode().strip(),
            'dirty_baseline': git(root, 'status', '--porcelain').decode('utf-8'),
            'baseline': files, 'outside_baseline': outside_inventory(root, config, git(root, 'rev-parse', 'HEAD').decode().strip()),
            'reviews': reviews, 'retired_reviews': retired_reviews,
            'feedback': feedback, 'results': results,
            'source_patterns': {f['id']: source_patterns(config, f) for f in config['features']},
            'documentation_only': {f['id']: dict(f.get('documentation_only', {})) for f in config['features']},
            'input_bases': {item['id']: item['basis'] for item in features},
            'verification_bases': {item['id']: item['verification_basis'] for item in features},
            'check_links': check_links, **({'investigation': investigation} if investigation else {})}


def investigation_unknowns(investigation):
    result = []
    for entry in investigation['entries']:
        for unknown in entry.get('unverified', []):
            if isinstance(unknown, str):
                unknown = {'id': entry['id'] + ':unverified:' + digest(unknown)[:12],
                           'method': 'unspecified', 'reason': unknown}
            result.append(dict(unknown, entry_id=entry['id']))
    return result


def record_investigation(root, state, investigation):
    """Agent-owned observations in the existing task; no setup or execution."""
    if not isinstance(investigation, dict) or investigation.get('scope') not in {'whole-project', 'targeted'}:
        raise ValueError('investigation_scope_required')
    if investigation.get('inventory_status') not in {'partial', 'complete'}:
        raise ValueError('investigation_inventory_status_required')
    for field in ('inventory_refs', 'source_refs', 'allowed', 'forbidden', 'next_actions'):
        if not isinstance(investigation.get(field), list) or any(not isinstance(v, str) or not v.strip() for v in investigation[field]):
            raise ValueError(f'investigation_requires_list:{field}')
    previous = state.get('investigation', {})
    methods = investigation.get('requested_methods', ['unspecified'])
    if not isinstance(methods, list) or not methods or any(m not in {'source', 'runtime', 'retained_evidence', 'unspecified'} for m in methods):
        raise ValueError('investigation_requested_methods_invalid')
    if previous and previous.get('requested_methods', ['unspecified']) != methods:
        raise ValueError('investigation_scope_changed:requested_methods')
    for field in ('scope', 'allowed', 'forbidden'):
        if previous and previous[field] != investigation[field]:
            raise ValueError(f'investigation_scope_changed:{field}')
    prior_entries = {e['id']: e for e in previous.get('entries', [])}
    entries = investigation.get('entries')
    if not isinstance(entries, list) or not entries:
        raise ValueError('investigation_entries_required')
    ids = []
    for entry in entries:
        if not isinstance(entry, dict) or any(not isinstance(entry.get(k), str) or not entry[k].strip()
                for k in ('id', 'location', 'access', 'conditions', 'expected')):
            raise ValueError('investigation_entry_identity_and_conditions_required')
        ids.append(entry['id'])
        if entry.get('observation_method', 'unspecified') not in {'source', 'runtime', 'retained_evidence', 'unspecified'}:
            raise ValueError('investigation_observation_method_invalid')
        if not isinstance(entry.get('unverified', []), list) or any(
                not (isinstance(v, str) and v.strip() or isinstance(v, dict) and
                     all(isinstance(v.get(k), str) and v[k].strip() for k in ('id', 'method', 'reason')) and
                     v['method'] in {'source', 'runtime', 'retained_evidence', 'unspecified'}) for v in entry.get('unverified', [])):
            raise ValueError('investigation_unverified_invalid')
        if entry.get('status') not in {'observed', 'unobserved', 'blocked', 'not_applicable'}:
            raise ValueError('invalid_investigation_entry_status')
        if entry.get('owner') not in {'product', 'plugin', 'tool', 'environment', 'agent', 'unknown'}:
            raise ValueError('investigation_issue_owner_required')
        if not isinstance(entry.get('evidence'), list) or any(not isinstance(v, str) or not v for v in entry['evidence']):
            raise ValueError('investigation_evidence_paths_required')
        if entry['status'] == 'observed' and (not entry['evidence'] or not isinstance(entry.get('observed'), str) or not entry['observed'].strip()):
            raise ValueError('observed_entry_requires_evidence_and_observation')
        if entry['status'] in {'blocked', 'not_applicable'} and not entry.get('reason'):
            raise ValueError('investigation_entry_reason_required')
        if entry['id'] in prior_entries and any(entry[k] != prior_entries[entry['id']][k] for k in ('location', 'access', 'conditions', 'expected')):
            raise ValueError('investigation_entry_identity_changed')
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate_investigation_entry')
    if set(prior_entries) - set(ids):
        raise ValueError('investigation_entry_removed')
    unknowns = investigation_unknowns(investigation)
    by_id = {entry['id']: entry for entry in entries}
    if len({v['id'] for v in unknowns}) != len(unknowns):
        raise ValueError('duplicate_investigation_unverified')
    for unknown in unknowns:
        replacement = by_id.get(unknown['id'])
        if replacement is not None and (unknown['id'] == unknown['entry_id'] or
                replacement.get('observation_method', 'unspecified') != unknown['method']):
            raise ValueError('investigation_unverified_entry_collision')
    prior_unknowns = investigation_unknowns(previous) if previous else []
    if {v['id'] for v in prior_unknowns} - ({v['id'] for v in unknowns} | set(ids)):
        raise ValueError('investigation_unverified_removed_without_observation_entry')
    for unknown in prior_unknowns:
        current = next((v for v in unknowns if v['id'] == unknown['id']), None)
        if current is not None and current != unknown:
            raise ValueError('investigation_unverified_identity_changed')
        if current is None:
            method = by_id[unknown['id']].get('observation_method', 'unspecified')
            if method == 'unspecified' or unknown['method'] != 'unspecified' and method != unknown['method']:
                raise ValueError('investigation_unverified_observation_method_mismatch')
    if investigation['inventory_status'] == 'complete' and not investigation['inventory_refs']:
        raise ValueError('complete_inventory_requires_references')
    updated = deepcopy(investigation)
    references = list(dict.fromkeys(updated['inventory_refs'] + updated['source_refs'] +
                                   [name for e in entries for name in e['evidence']]))
    updated['reference_hashes'] = {name: file_hash(root, name) for name in references}
    if any(value is None for value in updated['reference_hashes'].values()):
        raise ValueError('investigation_reference_missing')
    for entry in updated['entries']:
        prior = prior_entries.get(entry['id'], {})
        if prior and all(prior.get(k) == entry.get(k) for k in ('status', 'observed', 'evidence')):
            entry['reference_hashes'] = deepcopy(prior['reference_hashes'])
        else:
            entry['reference_hashes'] = {name: updated['reference_hashes'][name] for name in
                dict.fromkeys(updated['source_refs'] + updated['inventory_refs'] + entry['evidence'])}
    result = deepcopy(state)
    result['investigation'] = updated
    return result


def inspect_investigation(root, state):
    investigation = state.get('investigation')
    if investigation is None:
        return None
    hashes = investigation['reference_hashes']
    changed = [name for name, value in hashes.items() if file_hash(root, name) != value]
    stale = [e['id'] for e in investigation['entries'] if e['status'] == 'observed' and any(
        file_hash(root, name) != value for name, value in e['reference_hashes'].items())]
    methods = investigation.get('requested_methods', ['unspecified'])
    def in_scope(method):
        return 'unspecified' in methods or method in methods
    unknowns = investigation_unknowns(investigation)
    entries = {e['id']: e for e in investigation['entries']}
    unknowns = [v for v in unknowns if v['id'] not in entries]
    unobserved = [e['id'] for e in entries.values() if e['status'] in {'unobserved', 'blocked'} and
                  in_scope(e.get('observation_method', 'unspecified'))]
    unobserved.extend(v['id'] for v in unknowns if in_scope(v['method']))
    out_of_scope = [e['id'] for e in entries.values() if not in_scope(e.get('observation_method', 'unspecified'))]
    out_of_scope.extend(v['id'] for v in unknowns if not in_scope(v['method']))
    return dict(investigation, total=len(entries), unobserved=unobserved, stale=stale,
                requested_methods=methods, unverified=unknowns, out_of_scope=out_of_scope,
                observed_methods={e['id']: e.get('observation_method', 'unspecified') for e in entries.values()
                                  if e['status'] == 'observed'},
                status='PARTIAL' if unobserved or stale or changed or investigation['inventory_status'] != 'complete' else 'READY_FOR_REVIEW',
                changed_references=changed, semantic_limit='Agent-declared inventory and observations; no automatic product verdict')


def begin_work(root, project):
    """Use the same follow-up rules for ordinary tasks and Harness start."""
    return begin(root, project, 'change')


def work_record(root, work_id):
    """Use start's immutable baseline, even before an optional review file exists."""
    from task_store import TaskStore
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
    state = TaskStore(path).load(default=deepcopy(baseline))
    if not isinstance(state, dict):
        raise ValueError('invalid_work_workflow_record')
    for key, value in baseline.items():
        if key not in {'reviews', 'retired_reviews', 'feedback', 'results', 'execution_plan', 'investigation'} and state.get(key) != value:
            raise ValueError(f'work_workflow_baseline_changed:{key}')
    return state, directory / 'workflow.json'


def task_state(root, state=None, work_id=None):
    from task_store import TaskStore
    if bool(state) == bool(work_id):
        raise ValueError('select_exactly_one_task_state_or_work_id')
    if work_id:
        return work_record(root, work_id)
    path = local_path(root, str(state))
    if not path.resolve().is_relative_to(root.resolve() / '.work') or not path.is_file():
        raise ValueError('existing_task_local_state_required')
    try:
        record = TaskStore(path).load()
    except ValueError as error:
        if str(error) == 'workflow_state_must_be_object':
            raise ValueError('work_target_mismatch') from error
        raise
    if (not isinstance(record, dict) or record.get('schema_version') != 1
            or record.get('root') != str(root.resolve()) or not isinstance(record.get('baseline'), dict)):
        raise ValueError('work_target_mismatch')
    return record, path


def task_candidates(root, project, *, limit=None):
    """Bounded discovery of existing owned records, without choosing a task."""
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError('invalid_candidate_preview_limit')
    paths = {p.relative_to(root).as_posix() for p in local_path(root, '.work/tasks').glob('*/state.json')}
    configured = (configuration(project) or {}).get('state')
    if configured and local_path(root, configured).is_file():
        paths.add(configured)
    selectors = [{'state': name} for name in sorted(paths)]
    selectors += [{'work_id': p.parent.name} for p in
                  sorted(local_path(root, '.work/goals/active').glob('*/work.json'))]
    candidates = []
    for index, selector in enumerate(selectors):
        if limit is not None and index >= limit:
            candidates.append({**selector, 'status': 'NOT_INSPECTED', 'reason': 'candidate_preview_limit'})
            continue
        try:
            state, path = task_state(root, **selector)
            candidates.append({**selector, 'state': path.relative_to(root).as_posix(),
                               'task_id': state.get('task_id'), 'intent': state['intent'], 'targets': state['targets'],
                               'request': state.get('request')})
        except (OSError, ValueError, TypeError, KeyError) as error:
            candidates.append({**selector, 'status': 'BLOCKED', 'reason': str(error)})
    return candidates


def task_context(root, state, path, work_id=None):
    return json.dumps({'root': str(root.resolve()), 'state': path.relative_to(root).as_posix(),
                       'work_id': work_id, 'identity': task_identity(state)}, separators=(',', ':'))


def resolve_task(root, state=None, work_id=None, context=None):
    """An explicit invocation context points to existing state, never a second ledger."""
    context = context if context is not None else os.environ.get('AGENT_WORKFLOW_CONTEXT')
    if not context:
        return task_state(root, state, work_id) + (work_id,)
    binding = json.loads(context)
    if not isinstance(binding, dict) or set(binding) != {'root', 'state', 'work_id', 'identity'}:
        raise ValueError('invalid_task_context')
    if binding['root'] != str(root.resolve()):
        raise ValueError('context_project_mismatch')
    bound_state = None if binding['work_id'] else binding['state']
    if state is not None or work_id is not None:
        if (work_id != binding['work_id'] or state is not None and
                local_path(root, str(state)).resolve() != local_path(root, binding['state']).resolve()):
            raise ValueError('context_selector_conflict')
    record, path = task_state(root, bound_state, binding['work_id'])
    if path.relative_to(root).as_posix() != binding['state'] or task_identity(record) != binding['identity']:
        raise ValueError('context_task_identity_changed')
    return record, path, binding['work_id']


def connected_verification(root, project, state, path, work_id, action, *, output=None, run_check=None,
                           timeout=300, resume=False, workflow_bases=None):
    """Compose the existing prepare/execute API, retaining only its plan pointer."""
    import verification_results as viewer
    if action == 'prepare':
        directory = local_path(root, output or f'.work/tasks/{state["task_id"]}/runs/{uuid.uuid4()}')
        if not directory.resolve().is_relative_to(root / '.work') or directory.exists():
            raise ValueError('new_task_local_output_required')
        result = viewer.prepare_plan(root, None, directory / 'plan.json', report_dir=directory / 'native',
            pending_state=None if work_id else path.relative_to(root), work_id=work_id)
        if result['status'] == 'PREPARED':
            current, _ = task_state(root, None if work_id else path.relative_to(root), work_id)
            if task_identity(current) != task_identity(state):
                raise ValueError('task_identity_changed')
            current['execution_plan'] = (directory / 'plan.json').relative_to(root).as_posix()
            write_state(path, current, staging=root / '.work' if work_id else None)
        return result
    name = state.get('execution_plan')
    if not isinstance(name, str) or not name:
        raise ValueError('task_requires_prepare')
    plan = local_path(root, name)
    prepared = json.loads(plan.read_text(encoding='utf-8'))
    if not isinstance(prepared, dict):
        raise ValueError('prepared_plan_must_be_object')
    scope = prepared.get('workflow_scope', {})
    if not isinstance(scope, dict):
        raise ValueError('prepared_plan_scope_must_be_object')
    if (scope.get('root') != str(root) or scope.get('state') != path.relative_to(root).as_posix()
            or scope.get('work_id') != work_id or scope.get('task_identity') != task_identity(state)):
        raise ValueError('prepared_plan_task_mismatch')
    if action in {'lookup', 'resume', 'audit'}:
        directory = plan.parent / 'evidence'
        final = directory / 'bundle.json'
        checkpoints = sorted(directory.glob('checkpoint-*-bundle.json'), key=lambda p: int(p.name.split('-')[1]))
        if final.is_file() or checkpoints:
            saved = final if final.is_file() else checkpoints[-1]
            result = viewer.view_bundle_with_context(saved, workflow_state=path.relative_to(root), workflow_bases=workflow_bases)
            try:
                descriptor = json.loads(saved.read_text(encoding='utf-8'))
                indices = descriptor.get('completed_indices') if isinstance(descriptor, dict) else None
                checks = prepared.get('checks')
                valid_indices = (isinstance(indices, list) and isinstance(checks, list)
                    and len(indices) == len(set(indices))
                    and all(type(index) is int and 0 <= index < len(checks) for index in indices))
            except (OSError, ValueError, TypeError):
                indices, valid_indices = None, False
            completed = set(indices) if valid_indices else set()
            unknown = []
            for marker in sorted(directory.glob('command-*-started.json')):
                match = re.fullmatch(r'command-(\d+)-started\.json', marker.name)
                if match is None or not valid_indices or int(match.group(1)) not in completed:
                    unknown.append(marker.name)
            result['unknown_launches'] = unknown
            result['test_commands_executed'] = 0
            if not valid_indices or unknown:
                reasons = (['checkpoint_completed_indices_invalid'] if not valid_indices else []) + [
                    f'unknown_launch_outcome:{name}' for name in unknown]
                result['status'] = 'BLOCKED'
                result['remaining'] = sorted(set(result.get('remaining', [])) | set(reasons))
                result['reason'] = ('Checkpoint completion indices are invalid; execution outcome remains unknown'
                    if not valid_indices else 'An external command may have started; explicit recovery is required')
            return result
        launches = [p.name for p in directory.glob('command-*-started.json')]
        return {'status': 'BLOCKED' if launches else 'NOT_RUN', 'plan': str(plan), 'unknown_launches': launches,
                'test_commands_executed': 0, 'reason': 'Explicit execute/resume required; lookup never launches a command'}
    capture = run_check or viewer.capture_tool()
    if capture is None:
        raise ValueError('project_capture_tool_required')
    return viewer.execute_plan(plan, run_check_path=capture, evidence_dir=plan.parent / 'evidence',
                                  timeout=timeout, resume=resume)


def pending_selection(audit):
    """One selector for project adapters and native assertion preparation."""
    if audit['status'] not in {'PARTIAL', 'READY_FOR_REVIEW'}:
        raise ValueError('workflow_selection_unavailable')
    decisions = []
    for feature in audit['features']:
        results = {item['id']: item for item in feature['check_results'] if item.get('selected')}
        for check in feature['checks']:
            result = results.get(check, {})
            excluded = feature.get('excluded_checks', {}).get(check)
            selected = (feature['verification_status'] == 'REQUIRED' and not excluded
                        and result.get('current_status') != 'PASS')
            decisions.append({'feature': feature['id'], 'check': check, 'selected': selected,
                              'reason': excluded or ('current_evidence_reusable' if result.get('current_status') == 'PASS'
                                        else 'task_verification_required' if selected else 'no_changed_behavior_obligation')})
    return {'selected_checks': [{'feature': d['feature'], 'check': d['check']} for d in decisions if d['selected']],
            'unconnected_features': [f['id'] for f in audit['features'] if f['verification_status'] == 'REQUIRED' and not f['checks']],
            'selection': decisions, 'workflow_status': audit['status'],
            'remaining_obligations': audit['obligations'], 'product_findings': audit['product_findings'],
            'coverage': audit['coverage'], 'feedback': audit['feedback'], 'ui_systems': audit['ui_systems'],
            'check_retirements': audit['check_retirements']}


def write_state(path: Path, state: dict, *, staging: Path | None = None) -> None:
    """Compatibility entrypoint: updates require a revision-bound task read."""
    from task_store import TaskState, TaskStore
    store = TaskStore(path)
    if isinstance(state, TaskState):
        store.commit(state, staging=staging)
    else:
        store.create(state, staging=staging)


def task_identity(state):
    return digest({key: value for key, value in state.items() if key not in {'reviews', 'retired_reviews', 'feedback', 'results', 'execution_plan', 'investigation'}})


def bind_results(root, state_path, bundles, *, work_id=None, expected_identity=None):
    """Store existing result pointers, independently of Agent semantic review."""
    state, path = task_state(root, state_path if not work_id else None, work_id)
    if expected_identity is not None and task_identity(state) != expected_identity:
        raise ValueError('task_identity_changed')
    updated = deepcopy(state)
    for feature, bundle in bundles.items():
        name = Path(bundle).resolve().relative_to(root.resolve()).as_posix()
        if not local_path(root, name).is_file():
            raise ValueError('result_bundle_missing')
        links = updated.setdefault('results', {}).setdefault(feature, [])
        if name not in links:
            links.append(name)
    if updated != state:
        write_state(path, updated, staging=root / '.work' if work_id else None)
    return updated


def inspect_result_links(root, feature, commands, links, required_checks=None, *, bundle_cache=None):
    items, findings = {}, []
    for link in links:
        observed = inspect_evidence(root, feature, commands, link, bundle_cache=bundle_cache)
        findings.extend(observed['findings'])
        for item in observed.get('items', []):
            if item.get('selected') and item.get('feature') == feature['id']:
                items[item['id']] = item
    missing = [name for name in (feature['checks'] if required_checks is None else required_checks)
               if items.get(name, {}).get('current_status') != 'PASS']
    return {'status': 'BLOCKED' if missing else 'PASS', 'items': list(items.values()),
            'findings': sorted(set(findings)) if missing else []}


def inspect_project(root, project, state=None, *, file_inventory=None, evidence_resolver=None, observe_local_changes=False):
    """Host callers supply trusted inventory/evidence and a protected snapshot root.

    Reference and semantic-review reads still use root; injected inputs alone do
    not establish protected acceptance. Ordinary audit keeps its local adapters.
    The local prompt hook explicitly opts into Git change observation when sharing inventory.
    """
    root = root.resolve()
    config = configuration(project)
    result = {'status': 'NOT_CONFIGURED', 'mapping_status': 'NOT_CONFIGURED', 'enforcement': 'BLOCKED',
              'trust': 'editable local consistency; host-protected acceptance unavailable',
              'obligations': [], 'features': [], 'partitions': {}, 'unmapped': [],
              'unlinked': [], 'findings': [], 'product_findings': [], 'retired': [], 'coverage': coverage_summary([]),
              'feedback': [], 'ui_systems': [], 'check_retirements': [], 'next_actions': []}
    if state is not None:
        if not isinstance(state, dict) or state.get('schema_version') != 1 or state.get('root') != str(root):
            raise ValueError('work_target_mismatch')
        investigation = inspect_investigation(root, state)
        if investigation is not None:
            result['investigation'] = investigation
    if config is None:
        if result.get('investigation'):
            result['status'] = result['investigation']['status']
        return result
    if state is not None and not isinstance(state, dict):
        raise ValueError('workflow_state_must_be_object')
    if state is not None and (state.get('schema_version') != 1 or state.get('root') != str(root)):
        raise ValueError('work_target_mismatch')
    if state is not None and not isinstance(state.get('baseline'), dict):
        raise ValueError('workflow_baseline_required')
    state = state or {}
    for field in ('reviews', 'retired_reviews', 'baseline', 'outside_baseline', 'input_bases', 'verification_bases', 'source_patterns', 'documentation_only', 'results'):
        if not isinstance(state.get(field, {}), dict):
            raise ValueError(f'workflow_state_requires_object:{field}')
    for links in state.get('results', {}).values():
        if not isinstance(links, list) or any(not isinstance(link, str) or not link for link in links):
            raise ValueError('workflow_results_require_bundle_paths')
    if state.get('intent') in {'feedback', 'ui'} and not state.get('targets'):
        raise ValueError('target_required')
    files = inventory(root, config['roots']) if file_inventory is None else file_inventory
    result['ui_systems'] = inspect_ui_systems(root, config, files)
    result['findings'].extend(finding for system in result['ui_systems'] for finding in system['findings'])
    commands = dict(project.get('commands', {}))
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    bundle_cache = {}
    assertion_path = local_path(root, config['assertions']) if isinstance(config.get('assertions'), str) else None
    assertion_hash = file_hash(root, config['assertions']) if assertion_path else None
    result['feedback'] = inspect_feedback(root, config, state, bundle_cache=bundle_cache)
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
        ui_systems = [system for system in result['ui_systems'] if identity in system['consumers']]
        for system in ui_systems:
            sources.update(system['source_hashes'])
        covered.update(sources)
        findings = []
        for pattern in feature['sources']:
            if not any(fnmatchcase(name, pattern) and value is not None for name, value in files.items()):
                findings.append(f'missing_source:{identity}:{pattern}')
        refs = {name: file_hash(root, name) for field in ('map', 'criteria', 'ui') for name in feature.get(field, [])}
        refs.update({row['requirement']: file_hash(root, row['requirement']) for row in feature.get('coverage', [])})
        for system in ui_systems:
            refs.update(system['reference_hashes'])
            findings.extend(system['findings'])
        findings.extend(f'missing_reference:{identity}:{name}' for name, value in refs.items() if value is None)
        findings.extend(f'missing_command:{identity}:{name}' for name in feature['checks'] if name not in commands)
        for prevention in feature.get('prevention', []):
            structural = prevention.get('mechanism') in {'structure', 'type_constraint'}
            fields = ('failure', 'scope', 'owner_refs', 'normal_exception', 'reconsider') if structural else ('failure', 'check', 'normal_exception')
            if not all(prevention.get(key) for key in fields):
                findings.append(f'incomplete_prevention:{identity}')
            if structural:
                owners = prevention.get('owner_refs', [])
                if not isinstance(owners, list) or not owners or any(name not in sources or sources[name] is None for name in owners):
                    findings.append(f'inactive_prevention_owner:{identity}')
            elif prevention.get('check') not in feature['checks']:
                findings.append(f'inactive_prevention:{identity}:{prevention.get("check")}')
        basis_inputs = {'feature': feature, 'sources': sources, 'references': refs,
                        'commands': {name: commands.get(name) for name in feature['checks']}}
        if ui_systems:
            basis_inputs['ui_systems'] = ui_systems
        basis = digest(basis_inputs)
        verification_basis = digest({
            'references': {field: {name: refs[name] for name in feature.get(field, [])}
                           for field in ('criteria', 'ui')},
            'commands': {name: commands.get(name) for name in feature['checks']}})
        if ui_systems:
            verification_basis = digest({'verification': verification_basis, 'ui_systems': ui_systems})
        review = state.get('reviews', {}).get(identity, {})
        # A recorded analysis is a semantic-review input, never a success flag.
        reviewed = current_review(root, review, basis)
        excluded = {}
        states = review_scope_states(root, review)
        if review.get('basis') == basis:
            for check in feature['checks']:
                declarations = [row for row in feature.get('coverage', []) if row.get('check') == check]
                decisions = [review.get('scope_reviews', {}).get(row['id'], {}) for row in declarations]
                if decisions and all(d.get('status') == 'NOT_REQUIRED' and d.get('reason')
                                     and states.get(row['id']) == 'CURRENT' for row, d in zip(declarations, decisions)):
                    excluded[check] = '; '.join(dict.fromkeys(d['reason'] for d in decisions))
        required_feature = dict(feature, checks=[c for c in feature['checks'] if c not in excluded])
        product_findings = review.get('product_findings', []) if isinstance(review, dict) else []
        if isinstance(product_findings, list):
            product_findings = list(product_findings)
            result['product_findings'].extend({'feature': identity, 'finding': finding}
                for finding in product_findings if isinstance(finding, str) and finding.strip())
        for finding in architecture_findings(review):
            if finding['status'] == 'open':
                product_findings.append(finding['problem'])
                result['product_findings'].append(dict(finding, feature=identity))
        # Preserve ownership across staged deletion and source-map reassignment.
        patterns = feature['sources'] + state.get('source_patterns', {}).get(identity, []) + [pattern
            for system in ui_systems for field in ('tokens', 'components') for pattern in system[field]]
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
        if identity in state.get('targets', []):
            requires.append('verification')
        feature_feedback = [item for item in result['feedback'] if item['feature'] == identity]
        repair_request = state.get('intent') == 'feedback' and identity in state.get('targets', []) and (
            not feature_feedback or any(item.get('kind', 'requirement_violation') in
                                       {'requirement_violation', 'oracle_tool_error'} and not item.get('supersession')
                                       for item in feature_feedback))
        if repair_request:
            requires.extend(['repair', 'regression', 'normal_case'])
        ui_requested = state.get('intent') == 'ui' and identity in state.get('targets', [])
        if ui_requested:
            requires.append('verification')
            if not feature.get('ui') and not ui_systems:
                findings.append(f'missing_ui_standard:{identity}')
        if feature.get('ui') or ui_requested or ui_systems:
            requires.append('ui_review')
        mapping_ready = reviewed and not findings
        mapping_pending = mapping_pending or not mapping_ready
        if product_findings:
            requires.append('product_resolution')
        unresolved_feedback = [item for item in result['feedback'] if item['feature'] == identity and item['status'] not in {'RESOLVED', 'ACCEPTED', 'SUPERSEDED'}]
        if unresolved_feedback:
            for item in unresolved_feedback:
                kind = item.get('kind', 'requirement_violation')
                requires.extend(['feedback_reconciliation'] if item.get('supersession') else
                                ['diagnosis'] if kind in {'environment_limit', 'unknown'} else
                                ['difference_review'] if kind == 'intentional_difference' else
                                ['criterion_revision', 'verification', 'normal_case'] if kind == 'requirement_change' else
                                ['repair', 'regression', 'normal_case'])
            findings.extend(f'feedback_pending:{item["id"]}:{part}' for item in unresolved_feedback for part in item['remaining'])
        retirements = inspect_check_retirements(root, project, feature, state, review, reviewed, bundle_cache=bundle_cache)
        result['check_retirements'].extend(retirements)
        if any(item['status'] != 'PRESERVED' for item in retirements):
            requires.append('check_preservation')
            findings.extend(f'check_retirement_pending:{identity}:{item["check"]}:{reason}'
                            for item in retirements for reason in item['remaining'])
        needs_behavior = any(requirement in requires for requirement in ('verification', 'repair', 'regression'))
        behavior = None
        structural_evidence = []
        current_repairs = [item for item in feature_feedback
            if item.get('prevention_binding', {}).get('task_identity') == task_identity(state)]
        current_structural_repair = (repair_request and current_repairs and not feature['checks']
            and all(item['status'] == 'RESOLVED' and item.get('guardrail', {}).get('mechanism') in {'structure', 'type_constraint'}
                    for item in current_repairs))
        links = list(state.get('results', {}).get(identity, []))
        if review.get('bundle') and review['bundle'] not in links:
            links.insert(0, review['bundle'])
        if needs_behavior or links:
            if evidence_resolver is not None:
                if reviewed:
                    behavior = evidence_resolver(root, required_feature, commands)
            elif links:
                behavior = inspect_result_links(root, feature, commands, links, required_feature['checks'], bundle_cache=bundle_cache)
            elif current_structural_repair:
                structural_evidence = sorted({name for item in current_repairs for name in item['prevention_review']['captures']})
                behavior = {'status': 'PASS', 'findings': [], 'items': []}
            elif not required_feature['checks'] and excluded:
                behavior = {'status': 'NOT_REQUIRED', 'findings': [], 'items': []}
            if needs_behavior and behavior is not None and behavior['status'] not in {'PASS', 'NOT_REQUIRED'}:
                findings.extend(behavior['findings'])
        if repair_request and state.get('input_bases', {}).get(identity) == basis:
            findings.append(f'repair_not_observed:{identity}')
        assertion_changed = []
        if assertion_path and behavior:
            for item in behavior.get('items', []):
                if item['id'] not in required_feature['checks'] or not item.get('selected'):
                    continue
                hashes = item.get('conditions', {}).get('expected', {}).get('fixture', {}).get('file_hashes', {})
                if any(Path(name) == assertion_path and value != assertion_hash for name, value in hashes.items()):
                    assertion_changed = [config['assertions']]
                    needs_behavior = True
                    requires.append('verification')
                    findings.extend(behavior.get('findings', []))
                    break
        pending = not reviewed or findings or product_findings or (needs_behavior and (not behavior or behavior['status'] not in {'PASS', 'NOT_REQUIRED'}))
        rows = coverage_rows(feature, review, basis, behavior.get('items', []) if behavior else [],
                             semantic_valid=reviewed, scope_states=states)
        result['coverage']['rows'].extend(rows)
        matrix = scope_matrix(feature, review, basis, rows, scope_states=states)
        in_task = not state or state.get('intent') == 'init' or bool(affected) or needs_behavior
        work_scope = ('request_required' if identity in state.get('targets', []) or state.get('intent') == 'init' else
                      'impact_required' if state and (affected or verification_inputs_changed or assertion_changed) else
                      'scope_undetermined' if not state.get('targets') or identity not in state.get('verification_bases', {})
                          or unresolved_feedback or any(r['status'] != 'PRESERVED' for r in retirements) else
                      'project_remaining')
        scope_basis = {'targets': state.get('targets', []), 'changed': affected,
                       'verification_inputs_changed': bool(state and verification_inputs_changed),
                       'assertion_contract_changed': assertion_changed,
                       'baseline_available': identity in state.get('verification_bases', {}),
                       'references': sorted(refs), 'current_basis': basis,
                       'request': state.get('request')}
        for cell in matrix:
            cell['in_task'] = in_task
            cell['work_scope'] = work_scope
        for row in rows:
            row['work_scope'] = work_scope
        result['coverage']['matrix'].extend(matrix)
        scope_gaps = [row['id'] for row in rows if row['kind'] == 'review' and row['status'] not in {'PASS', 'NOT_REQUIRED'}
                      or row['status'] == 'MISSING']
        if scope_gaps:
            pending = True
            requires.append('scope_review_or_connection')
            findings.extend(f'coverage_gap:{identity}:{name}' for name in scope_gaps)
        if in_task:
            if any(cell['decision'] and cell['status'] not in {'PASS', 'NOT_REQUIRED'} for cell in matrix):
                pending = True
                requires.append('scope_applicability_or_evidence')
        if pending:
            requires = list(dict.fromkeys(requires))
            result['obligations'].append({'id': f'feature:{identity}:{basis}', 'target': identity,
                'basis': basis, 'reason': 'initial_or_changed_inputs', 'changed': affected,
                'verification_changed': verification_changed,
                'verification_inputs_changed': bool(state and verification_inputs_changed),
                'requires': requires, 'references': sorted(refs),
                'ui_systems': [system['id'] for system in ui_systems],
                'prevention': feature.get('prevention', [])})
        result['features'].append({'id': identity, 'basis': basis, 'partition': feature['partition'],
                                   'work_scope': work_scope, 'scope_basis': scope_basis,
                                   'verification_basis': verification_basis,
                                   'verification_status': ('NOT_REQUIRED' if not needs_behavior or not required_feature['checks'] and excluded else
                                       'PASS' if behavior and behavior['status'] == 'PASS' else 'REQUIRED'),
                                   'checks': feature['checks'], 'excluded_checks': excluded,
                                   'structural_evidence': structural_evidence,
                                   'check_results': behavior.get('items', []) if behavior else [],
                                   'reviewed': reviewed, 'mapping_ready': bool(mapping_ready), 'source_count': len(sources)})
        partition = feature['partition']
        prior = result['partitions'].get(partition, 'READY_FOR_REVIEW')
        result['partitions'][partition] = 'PARTIAL' if pending else prior
        result['findings'].extend(findings)
        if not feature['checks']:
            result['unlinked'].append(identity)
    result['unmapped'] = sorted(name for name in files.keys() - covered if files[name] is not None)
    owned_patterns = [pattern for feature in config['features'] for pattern in feature['sources']]
    owned_patterns += [pattern for patterns in state.get('source_patterns', {}).values() for pattern in patterns]
    result['unmapped_changes'] = (result['unmapped'] if not state or state.get('intent') == 'init' or not state.get('targets')
        else sorted(name for name in changed if name not in covered and not any(fnmatchcase(name, pattern) for pattern in owned_patterns)))
    if state and (file_inventory is None or observe_local_changes):
        outside = outside_inventory(root, config, state['base'], state.get('outside_baseline', {}))
        result['unmapped_changes'] = sorted(set(result['unmapped_changes']) | {
            name for name, value in outside.items() if value != state.get('outside_baseline', {}).get(name)})
    removed = (set(state.get('input_bases', {})) | set(state.get('reviews', {})) | set(state.get('retired_reviews', {}))) - {f['id'] for f in config['features']}
    removed |= {item['feature'] for item in result['feedback'] if item['feature'] not in {f['id'] for f in config['features']}}
    for name in sorted(removed):
        basis = digest({'removed': name, 'previous': state.get('input_bases', {}).get(name),
                        'features': config['features'], 'files': files})
        result['retired'].append({'id': name, 'basis': basis})
        review = state.get('retired_reviews', {}).get(name, {})
        prior_review = state.get('reviews', {}).get(name, {})
        reviewed = current_review(root, review, basis) and review.get('active_findings_basis') == finding_basis(prior_review)
        for candidate in (prior_review, review):
            if not isinstance(candidate, dict):
                raise ValueError('workflow_review_must_be_object')
            gaps = candidate.get('product_findings', [])
            if not isinstance(gaps, list) or any(not isinstance(gap, str) or not gap.strip() for gap in gaps):
                raise ValueError('review_product_findings_must_be_nonempty_strings')
        previous = prior_review.get('product_findings', [])
        product_findings = list(review.get('product_findings', previous) if reviewed else (
            previous + review.get('product_findings', [])))
        result['product_findings'].extend({'feature': name, 'finding': finding}
            for finding in dict.fromkeys(product_findings))
        architecture = architecture_findings(review) if reviewed else (
            architecture_findings(prior_review) + architecture_findings(review))
        for finding in architecture:
            if finding['status'] == 'open':
                product_findings.append(finding['problem'])
                result['product_findings'].append(dict(finding, feature=name))
        if not reviewed:
            mapping_pending = True
            result['findings'].append(f'removed_feature_needs_reconciliation:{name}')
        pending_feedback = [item for item in result['feedback'] if item['feature'] == name
                            and item['status'] not in {'RESOLVED', 'ACCEPTED', 'SUPERSEDED'}]
        if not reviewed or product_findings or pending_feedback:
            result['obligations'].append({'id': f'removed:{name}:{basis}', 'target': name,
                'basis': basis, 'reason': 'removed_feature', 'changed': [],
                'requires': (['removal_review'] if not reviewed else []) +
                            (['product_resolution'] if product_findings else []) +
                            (['feedback_reconciliation'] if pending_feedback else []),
                'references': sorted({p for f in config['features'] for p in f['map']})})
    result['mapping_status'] = 'PARTIAL' if mapping_pending or result['unmapped'] else 'READY_FOR_REVIEW'
    result['coverage'] = coverage_summary(result['coverage']['rows'], result['coverage']['matrix'])
    result['status'] = 'PARTIAL' if result['obligations'] or result['unmapped'] or result['findings'] else 'READY_FOR_REVIEW'
    if any(item['status'] not in {'RESOLVED', 'ACCEPTED', 'SUPERSEDED'} for item in result['feedback']):
        result['status'] = 'PARTIAL'
    if result.get('investigation', {}).get('status') == 'PARTIAL':
        result['status'] = 'PARTIAL'
    result['next_actions'] = deepcopy(result['obligations'])
    connect_next_actions(root, project, state, result)
    return result


def connect_next_actions(root, project, state, result):
    """Connect existing obligations to project contracts, without deciding semantic scope."""
    config = configuration(project)
    features = {f['id']: f for f in config['features']}
    observed = {f['id']: f for f in result['features']}
    commands = dict(project.get('commands', {}))
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    assertions, assertion_error = {}, None
    if config.get('assertions'):
        try:
            spec = json.loads(local_path(root, config['assertions']).read_text(encoding='utf-8'))
            for check in spec['checks']:
                key = (check['feature_id'], check['id'])
                if key in assertions:
                    raise ValueError('duplicate_assertion_identity')
                assertions[key] = check
        except (OSError, ValueError, TypeError, KeyError) as error:
            assertions, assertion_error = {}, str(error)
    for action in result['next_actions']:
        identity = action['target']
        feature = features.get(identity, {})
        current = observed.get(identity, {})
        action['scope'] = current.get('work_scope', 'request_required' if identity in state.get('targets', []) else 'scope_undetermined')
        action['scope_basis'] = deepcopy(current.get('scope_basis', {'targets': state.get('targets', []), 'reason': 'removed_owner_needs_reconciliation'}))
        action['status'] = 'PENDING'
        action['current_validity'] = 'CURRENT_OBSERVATION'
        guides = [{key: system[key] for key in ('id', 'guide', 'tokens', 'components', 'status')}
                  for system in result['ui_systems'] if identity in system['consumers']]
        action['guides'] = guides
        action['bundles'] = state.get('results', {}).get(identity, [])
        action['pending'] = []
        checks = {item['id']: item for item in current.get('check_results', [])}
        rows = [r for r in result['coverage']['rows'] if r['feature'] == identity]
        declared_checks = {r.get('check') for r in rows if r['kind'] == 'test'}
        if current.get('verification_status') == 'REQUIRED':
            rows += [dict(id=check, check=check, kind='test', status='NOT_RUN',
                          requirement=None, outcome=None, reasons=['check_not_in_result'])
                     for check in current['checks'] if check not in declared_checks]
        for row in rows:
            if row['status'] in {'PASS', 'NOT_REQUIRED'}:
                continue
            item = checks.get(row.get('check'), {}) if row['kind'] == 'test' else {}
            status = row['status']
            if item and row['kind'] == 'test':
                status = ('STALE' if item.get('current_reuse') == 'STALE' else
                          'NOT_RUN' if item.get('historical_status') == 'NOT_RUN' else
                          'BLOCKED' if item.get('current_status') == 'UNKNOWN' else item.get('current_status', status))
            if status in {'PASS', 'NOT_REQUIRED'}:
                continue
            check = row.get('check')
            registered = check in feature.get('checks', []) and check in commands
            contract = assertions.get((identity, check), {}) if registered else {}
            pending = {'id': row['id'], 'kind': 'execution_check' if row['kind'] == 'test' else 'Agent_semantic_review',
                'status': status, 'historical_status': item.get('historical_status', row.get('historical_status', 'NOT_RUN')),
                'current_validity': item.get('current_reuse', status), 'reasons': row.get('reasons', []) or item.get('reasons', []),
                'requirement': row.get('requirement'), 'outcome': row.get('outcome'),
                'check': check, 'command': deepcopy(commands.get(check)) if registered else None,
                'expected': contract.get('expected') or item.get('expected') if registered else None,
                'raw_contract': deepcopy(contract.get('raw_observations', [])),
                'contract_reference': config.get('assertions') if contract else None,
                'contract_error': assertion_error if row['kind'] == 'test' else None,
                'guides': [g['guide'] for g in guides], 'references': feature.get('criteria', []),
                'evidence': deepcopy(item or row.get('evidence')),
                'next_action': ('Reconcile the active check/registered contract before explicit preparation.' if not registered else
                                'Inspect current conditions and raw, then explicitly prepare/execute the registered check if required.')
                               if row['kind'] == 'test' else
                               'Review the stated outcome against sources and guide; record analysis and references in scope_reviews. Execution PASS does not supply semantic judgment.'}
            action['pending'].append(pending)
        cells = [c for c in result['coverage']['matrix'] if c['feature'] == identity and c['in_task'] and c['decision']
                 and c['status'] not in {'PASS', 'NOT_REQUIRED'}]
        for cell in cells:
            action['pending'].append({'id': cell['perspective'] + ':' + cell['area'], 'kind': 'Agent_scope_decision',
                'status': cell['status'], 'applicability': cell['applicability'], 'current_validity': cell['status'],
                'coverage': cell['coverage'], 'evidence': cell['decision'], 'reasons': cell['reasons'],
                'references': feature.get('criteria', []), 'guides': [g['guide'] for g in guides],
                'command': None, 'next_action': 'Determine applicability from the request and changed owners/consumers; connect relevant coverage or justify exclusion. Undecided is not outside scope.'})
        action['next_action'] = 'Inspect pending criteria and their contracts; perform only authorized work in this scope. Retain project obligations and unresolved scope.'
    scopes = ('request_required', 'impact_required', 'project_remaining', 'scope_undetermined')
    result['action_scope_counts'] = {scope: sum(a['scope'] == scope for a in result['next_actions']) for scope in scopes}


def handoff_summary(result, verification=None):
    blocked = (verification or {}).get('status') == 'BLOCKED'
    limit = ('Current individual checks cover only their registered criteria. '
             'Individual checks do not replace required Agent judgments. '
             'Use task_acceptance and current_request_actions for this task; project remainder is separate. '
             'Scope labels never discharge obligations.')
    if blocked:
        reasons = verification.get('remaining', []) or verification.get('unknown_launches', [])
        limit += (' Task verification is BLOCKED: ' + json.dumps(reasons[:3])
                  + '. Inspect verification for all blockers before accepting this task.')
    return {'project_status': result['status'],
        'task_acceptance': 'BLOCKED' if blocked else 'INCOMPLETE' if result['status'] == 'NOT_CONFIGURED' or result.get('unmapped_changes', result['unmapped'])
            or result.get('investigation', {}).get('status', 'READY_FOR_REVIEW') != 'READY_FOR_REVIEW'
            or any(a['scope'] != 'project_remaining' for a in result['next_actions']) else 'READY_FOR_REVIEW',
        'check_acceptance': 'BLOCKED_BY_TASK_BINDING_OR_EFFECT' if blocked else 'CURRENT_CHECKS_ONLY',
        'reusable_checks': [] if blocked else [{'feature': f['id'], 'check': item['id']}
            for f in result['features'] for item in f['check_results']
            if item.get('current_status') == 'PASS' and item.get('current_reuse') == 'REUSABLE'],
        'current_request_actions': [a['target'] for a in result['next_actions']
            if a['scope'] in {'request_required', 'impact_required'}],
        'project_remaining': [a['target'] for a in result['next_actions'] if a['scope'] == 'project_remaining'],
        'scope_undetermined': [a['target'] for a in result['next_actions'] if a['scope'] == 'scope_undetermined'],
        'limit': limit}


def retirement_references(proof):
    return [name for field in ('authorization_refs', 'requirement_refs', 'references') for name in proof.get(field, [])] + [
        name for field in ('entrypoints', 'callers') for item in proof.get(field, []) for name in item.get('references', [])]


def check_decision_references(decision):
    references = retirement_references(decision.get('retirement', {}))
    if decision.get('action') in {'rebind', 'consolidate'}:
        proof = decision.get('rebind' if decision['action'] == 'rebind' else 'consolidation', {})
        references.extend(proof.get(name) for name in ('source_plan', 'target_bundle') if isinstance(proof.get(name), str))
    return references


def normalize_rebind_check(root, check, changed_metadata):
    """Mask only identity, clean source revision, explicit report paths and their metadata hashes."""
    root = Path(root).resolve()
    value = deepcopy(check)
    if not isinstance(value, dict) or not isinstance(value.get('conditions'), dict):
        raise ValueError('rebind_check_contract_invalid')
    outputs = []
    for raw in value.get('raw_observations', []):
        candidate = Path(raw.get('path', ''))
        output = (candidate if candidate.is_absolute() else root / candidate).resolve()
        if not output.is_relative_to(root / '.work') or output in outputs:
            raise ValueError('rebind_report_output_invalid')
        outputs.append(output)
        raw['path'] = '<explicit-report-output>'
    if not outputs:
        raise ValueError('rebind_explicit_report_output_required')
    command = value['conditions'].get('command', {})
    argv = command.get('argv')
    if not isinstance(argv, list):
        raise ValueError('rebind_command_registration_invalid')
    cwd = Path(command.get('cwd', root))
    cwd = (cwd if cwd.is_absolute() else root / cwd).resolve()
    for output in outputs:
        positions = [index for index, arg in enumerate(argv) if isinstance(arg, str) and
                    ((Path(arg) if Path(arg).is_absolute() else cwd / arg).resolve() == output)]
        if len(positions) != 1:
            raise ValueError('rebind_report_output_not_bound_to_command')
        argv[positions[0]] = '<explicit-report-output>'
    if 'report_dir' in command:
        report_dir = Path(command['report_dir'])
        report_dir = (report_dir if report_dir.is_absolute() else root / report_dir).resolve()
        if not report_dir.is_relative_to(root / '.work') or any(not output.is_relative_to(report_dir) for output in outputs):
            raise ValueError('rebind_report_directory_invalid')
        command['report_dir'] = '<explicit-report-directory>'
    source = value['conditions'].get('source', {})
    if not isinstance(source, dict):
        raise ValueError('rebind_source_condition_invalid')
    source['revision'] = '<source-revision>'
    hashes = value['conditions'].get('fixture', {}).get('file_hashes', {})
    if not isinstance(hashes, dict):
        raise ValueError('rebind_fixture_hashes_invalid')
    for absolute in hashes:
        path = Path(absolute).resolve()
        if path.is_relative_to(root) and path.relative_to(root).as_posix() in changed_metadata:
            hashes[absolute] = '<explicit-metadata-revision>'
    value['id'] = '<check-identity>'
    return value


def inspect_check_identity_rebind(root, project, feature, state, check, decision):
    """Preserve a renamed or consolidated binding from Git and current native evidence."""
    root = Path(root).resolve()
    consolidating = decision.get('action') == 'consolidate'
    proof = decision.get('consolidation' if consolidating else 'rebind', {})

    def need(value, reason):
        if not value:
            raise ValueError(reason)

    def work_file(name):
        need(isinstance(name, str) and name and not Path(name).is_absolute(), 'rebind_proof_path_invalid')
        path = local_path(root, name)
        need(path.resolve().is_relative_to(root / '.work') and path.is_file(), 'rebind_proof_path_invalid')
        return path.resolve()

    def resolve_bundle_file(name, base):
        need(isinstance(name, str) and name.strip(), 'rebind_bundle_reference_invalid')
        candidate = Path(name)
        candidate = candidate if candidate.is_absolute() else base / candidate
        candidate = candidate.resolve()
        need(candidate.is_relative_to(root), 'rebind_bundle_reference_outside_project')
        return work_file(candidate.relative_to(root).as_posix())

    def repo_name(name):
        need(isinstance(name, str) and name.strip(), 'rebind_repository_reference_invalid')
        path = Path(name.replace('\\', '/'))
        need(not path.is_absolute() and '..' not in path.parts and '.git' not in path.parts,
             'rebind_repository_reference_invalid')
        return path.as_posix()

    def git_bytes(revision, name):
        return git(root, 'show', f'{revision}:{repo_name(name)}')

    def git_json(revision, name):
        return json.loads(git_bytes(revision, name).decode('utf-8-sig'))

    def is_ancestor(older, newer):
        return subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', older, newer],
                              capture_output=True).returncode == 0

    def source_revision(item):
        source = item.get('conditions', {}).get('source', {})
        revision = source.get('revision')
        empty_diff = hashlib.sha256(b'').hexdigest()
        empty_untracked = hashlib.sha256(b'{}').hexdigest()
        need(isinstance(revision, str) and re.fullmatch(r'[0-9a-fA-F]{40,64}', revision)
             and source.get('diff') == empty_diff and source.get('status') == ''
             and source.get('untracked') == empty_untracked, 'rebind_source_preimage_not_clean')
        return revision

    def plan_check(plan, feature_id, identity, viewer):
        rows = [item for item in viewer.plan_checks(plan, allow_unbound=True)
                if item.get('feature_id') == feature_id and item.get('id') == identity]
        need(len(rows) == 1, 'rebind_plan_check_missing_or_ambiguous')
        return rows[0]

    def scope_feature(plan, feature_id):
        rows = [item for item in plan.get('workflow_scope', {}).get('features', [])
                if item.get('id') == feature_id]
        need(len(rows) == 1, 'rebind_plan_feature_missing_or_ambiguous')
        return rows[0]

    def feature_for(config, feature_id):
        rows = [item for item in config['features'] if item.get('id') == feature_id]
        need(len(rows) == 1, 'rebind_feature_registration_missing_or_ambiguous')
        return rows[0]

    def spec_check(spec, feature_id, identity):
        rows = [item for item in spec.get('checks', []) if isinstance(item, dict)
                and item.get('feature_id') == feature_id and item.get('id') == identity]
        need(len(rows) == 1, 'rebind_assertion_registration_missing_or_ambiguous')
        return rows[0]

    def command_entry(project, identity):
        locations = []
        commands = project.get('commands', {})
        selectors = project.get('impact', {}).get('feature_selectors', {})
        if isinstance(commands, dict) and identity in commands:
            locations.append(('commands', commands, commands[identity]))
        if isinstance(selectors, dict) and identity in selectors:
            locations.append(('impact.feature_selectors', selectors, selectors[identity]))
        need(len(locations) == 1, 'rebind_command_registration_missing_or_ambiguous')
        return locations[0]

    def normalized_command(descriptor, spec_row):
        value = deepcopy(descriptor)
        argv = value.get('argv') if isinstance(value, dict) else value
        need(isinstance(argv, list) and argv and all(isinstance(arg, str) for arg in argv),
             'rebind_command_registration_invalid')
        paths = [raw.get('path') for raw in spec_row.get('raw_observations', []) if isinstance(raw, dict)]
        need(paths and all(isinstance(path, str) and path.strip() for path in paths),
             'rebind_explicit_report_output_required')
        for path in paths:
            positions = [index for index, arg in enumerate(argv) if arg == path]
            need(len(positions) == 1, 'rebind_report_output_not_bound_to_command')
            argv[positions[0]] = '<explicit-report-output>'
        return value

    def bind_plan_check(project, identity, spec_row, item):
        _, _, descriptor = command_entry(project, identity)
        command = descriptor if isinstance(descriptor, dict) else {'argv': descriptor}
        conditions = item['conditions']['command']
        report_dir = conditions.get('report_dir')
        argv = resolve_report_command(root, command.get('argv'), report_dir)
        cwd = local_path(root, command.get('working_directory', '.')).resolve()
        need(conditions.get('argv') == argv and conditions.get('cwd') == str(cwd),
             'rebind_registered_command_mismatch')
        raw_rows, spec_rows = item.get('raw_observations', []), spec_row.get('raw_observations', [])
        need(len(raw_rows) == len(spec_rows) and raw_rows, 'rebind_raw_assertions_changed')
        for raw, declared in zip(raw_rows, spec_rows):
            need(isinstance(raw, dict) and isinstance(declared, dict)
                 and {k: v for k, v in raw.items() if k != 'path'}
                 == {k: v for k, v in declared.items() if k != 'path'}, 'rebind_raw_assertions_changed')
            expected = Path(resolve_report_path(root, declared.get('path'), report_dir))
            if not expected.is_absolute():
                expected = cwd / expected
            actual = Path(raw.get('path', ''))
            actual = actual if actual.is_absolute() else cwd / actual
            actual = actual.resolve()
            expected = expected.resolve()
            need(actual == expected and actual.is_relative_to(root / '.work'), 'rebind_report_output_mismatch')
            need(any((Path(arg) if Path(arg).is_absolute() else cwd / arg).resolve() == actual for arg in argv),
                 'rebind_report_output_not_bound_to_command')
        if report_dir:
            output_dir = Path(report_dir)
            output_dir = (output_dir if output_dir.is_absolute() else root / output_dir).resolve()
            need(output_dir.is_relative_to(root / '.work'), 'rebind_report_directory_invalid')
        return True

    def repository_hashes(item):
        fixture = item.get('conditions', {}).get('fixture', {})
        hashes = fixture.get('file_hashes')
        need(isinstance(hashes, dict) and hashes, 'rebind_fixture_hashes_missing')
        cwd = Path(item['conditions']['command']['cwd']).resolve()
        names = set()
        for ref in fixture.get('file_refs', []):
            name = ref.get('path') if isinstance(ref, dict) else ref
            need(isinstance(name, str) and not Path(name).is_absolute(), 'rebind_fixture_reference_invalid')
            path = (cwd / name).resolve()
            need(path.is_relative_to(root), 'rebind_fixture_reference_outside_project')
            names.add(path.relative_to(root).as_posix())
        for ref in fixture.get('repository_file_refs', []):
            name = repo_name(ref)
            local_path(root, name)
            names.add(name)
        result = {}
        for absolute, value in hashes.items():
            path = Path(absolute).resolve()
            need(path.is_relative_to(root), 'rebind_fixture_path_outside_project')
            name = path.relative_to(root).as_posix()
            need(name not in result and isinstance(value, str), 'rebind_fixture_hashes_invalid')
            result[name] = value
        need(names == set(result), 'rebind_fixture_references_changed')
        return result

    def matches_git_preimage(name, expected, revision):
        raw = git_bytes(revision, name)
        crlf = raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        return expected in {hashlib.sha256(raw).hexdigest(), hashlib.sha256(crlf).hexdigest()}

    def transformed_map(old_raw, feature_id, old_id, new_id):
        bom = old_raw.startswith(b'\xef\xbb\xbf')
        text = old_raw.decode('utf-8-sig')
        lines = text.splitlines(keepends=True)
        matches = []
        leading_identifier = re.compile(r'\s*(?P<quote>`?)(?P<id>[A-Za-z0-9][A-Za-z0-9._-]*)(?P=quote)(?P<suffix>\s.*)?')
        for index, line in enumerate(lines):
            body = line.rstrip('\r\n')
            parts = body.split('|')
            cells = parts[1:-1] if len(parts) >= 3 and not parts[0].strip() and not parts[-1].strip() else []
            feature_token = leading_identifier.fullmatch(cells[0]) if cells else None
            if feature_token and feature_token.group('id') == feature_id:
                command_text, separator, note = cells[-1].partition(';')
                entries, parsed, offset = command_text.split(','), [], 0
                for entry in entries:
                    token = leading_identifier.fullmatch(entry)
                    need(token is not None, 'rebind_feature_map_command_ids_invalid')
                    parsed.append((token.group('id'), offset + token.start('id')))
                    offset += len(entry) + 1
                positions = [start for name, start in parsed if name == old_id]
                if positions:
                    need(len(positions) == 1, 'rebind_feature_map_binding_missing_or_ambiguous')
                    matches.append((index, parts, command_text, separator, note, positions[0]))
        need(len(matches) == 1, 'rebind_feature_map_binding_missing_or_ambiguous')
        index, parts, command_text, separator, note, token_start = matches[0]
        command_text = command_text[:token_start] + new_id + command_text[token_start + len(old_id):]
        parts[-2] = command_text + separator + note
        ending = '\r\n' if lines[index].endswith('\r\n') else '\n' if lines[index].endswith('\n') else ''
        lines[index] = '|'.join(parts) + ending
        output = ('\ufeff' if bom else '') + ''.join(lines)
        return output.encode('utf-8')

    def consolidate(old_plan, old_check, bundle_path, target_id):
        # Reuse the original registered contract, even when it predates prevention labels.
        old_revision = source_revision(old_check)
        need(old_revision == state.get('base'), 'consolidation_source_not_task_baseline')

        def original_input(name, expected):
            current = local_path(root, name).read_bytes()
            # Clean Windows files can contain mixed line endings after a scoped edit.
            return (hashlib.sha256(current).hexdigest() == expected
                    and current.replace(b'\r\n', b'\n') == git_bytes(old_revision, name).replace(b'\r\n', b'\n'))

        old_project = git_json(old_revision, '.harness/project.yaml')
        old_config, new_config = configuration(old_project), configuration(project)
        old_feature = feature_for(old_config, feature['id'])
        prior = state.get('check_links', {}).get(feature['id'], {})
        need(Path(old_plan.get('workflow_scope', {}).get('root', '')).resolve() == root
             and scope_feature(old_plan, feature['id']) == old_feature
             and prior.get('checks') == old_feature['checks']
             and prior.get('prevention', []) == old_feature.get('prevention', []),
             'consolidation_source_binding_mismatch')
        need(target_id in {identity for row in old_config['features'] for identity in row['checks']}
             and target_id in feature['checks'], 'consolidation_existing_target_required')
        wrapper = json.loads(bundle_path.read_text(encoding='utf-8-sig'))
        bundle = wrapper.get('execution', {}).get('bundle', wrapper)
        new_plan_path = resolve_bundle_file(bundle.get('source_plan'), bundle_path.parent)
        new_plan = json.loads(new_plan_path.read_text(encoding='utf-8-sig'))
        new_check = plan_check(new_plan, feature['id'], target_id, viewer)
        scope = new_plan.get('workflow_scope', {})
        target_state_path = work_file(scope.get('state'))
        target_state = json.loads(target_state_path.read_text(encoding='utf-8-sig'))
        need(Path(scope.get('root', '')).resolve() == root
             and scope.get('task_identity') == task_identity(state)
             and task_identity(target_state) == task_identity(state)
             and scope_feature(new_plan, feature['id']) == feature, 'consolidation_target_binding_mismatch')
        for plan, item in ((old_plan, old_check), (new_plan, new_check)):
            need(item.get('required') is True and item.get('selection', {}).get('status') == 'selected'
                 and any(row.get('feature') == feature['id'] and row.get('check') == item['id']
                         and row.get('selected') is True for row in plan['workflow_scope'].get('selection', [])),
                 'consolidation_required_check_missing')
        for field in ('coverage', 'prevention'):
            for row in old_feature.get(field, []):
                if row.get('check') == check:
                    need(dict(row, check=target_id) in feature.get(field, []),
                         'consolidation_detection_scope_changed')
        spec_path = old_config.get('assertions')
        need(spec_path == new_config.get('assertions'), 'consolidation_assertion_source_changed')
        old_spec = spec_check(git_json(old_revision, spec_path), feature['id'], check)
        new_spec = spec_check(json.loads(local_path(root, spec_path).read_text(encoding='utf-8-sig')),
                              feature['id'], target_id)
        bind_plan_check(old_project, check, old_spec, old_check)
        bind_plan_check(project, target_id, new_spec, new_check)
        need(normalized_command(command_entry(old_project, check)[2], old_spec)
             == normalized_command(command_entry(project, target_id)[2], new_spec),
             'consolidation_registered_command_changed')
        observations = lambda item: [{k: v for k, v in row.items() if k != 'path'}
                                     for row in item['raw_observations']]
        need(observations(old_check) == observations(new_check), 'consolidation_raw_assertions_changed')
        before, after = old_check['conditions'], new_check['conditions']
        need(before['runtime'] == after['runtime'] and before['criteria'] == after['criteria']
             and old_feature.get('criteria') == feature.get('criteria'), 'consolidation_runtime_or_criteria_changed')
        metadata = {'.harness/project.yaml', repo_name(spec_path),
                    *(repo_name(name) for name in old_feature.get('map', []))}
        old_hashes = repository_hashes(old_check)
        required = metadata | set(old_feature.get('criteria', [])) | set(old_feature.get('ui', []))
        required.update(row['requirement'] for row in old_feature.get('coverage', []))
        need(required <= set(old_hashes), 'consolidation_original_inputs_missing')
        tracked = set(git(root, 'ls-tree', '-r', '--name-only', old_revision).decode('utf-8').splitlines())
        for arg in before['command']['argv']:
            path = Path(arg)
            path = (path if path.is_absolute() else Path(before['command']['cwd']) / path).resolve()
            if path.is_relative_to(root) and path.relative_to(root).as_posix() in tracked:
                name = path.relative_to(root).as_posix()
                need(original_input(name, file_hash(root, name)), 'consolidation_runner_input_changed')
        for group in ('dependency', 'fixture'):
            declared = old_spec.get(group, {})
            for key, value in declared.items():
                need(before[group].get(key) == value, 'consolidation_original_conditions_changed')
            for key, value in before[group].items():
                if key == 'file_hashes':
                    for absolute, digest in value.items():
                        path = Path(absolute).resolve()
                        name = path.relative_to(root).as_posix() if path.is_relative_to(root) else None
                        if name is not None and name not in metadata:
                            need(original_input(name, digest), 'consolidation_input_preimage_mismatch')
                        if name not in metadata:
                            need(after[group].get(key, {}).get(absolute) == digest, 'consolidation_runtime_inputs_changed')
                elif isinstance(value, list):
                    need(all(ref in after[group].get(key, []) for ref in value), 'consolidation_inputs_dropped')
                elif key != 'kind':
                    need(after[group].get(key) == value, 'consolidation_conditions_changed')
        viewed = viewer.view_bundle(bundle_path, workflow_state=target_state_path.relative_to(root))
        rows = [item for item in viewed.get('items', []) if item.get('feature') == feature['id'] and item.get('id') == target_id]
        need(viewed.get('test_commands_executed') == 0 and len(rows) == 1, 'consolidation_target_evidence_missing')
        item = rows[0]
        need(item.get('current_status') == 'PASS' and item.get('historical_status') == 'PASS'
             and item.get('current_reuse') == 'REUSABLE' and item.get('selected') is True
             and item.get('capture', {}).get('execution') == 'exited'
             and item.get('capture', {}).get('exit_code') == 0, 'consolidation_target_evidence_not_current_pass')
        return []

    try:
        target_id = proof.get('target_check')
        need(isinstance(target_id, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', target_id)
             and target_id != check,
             'rebind_target_check_invalid')
        source_path, bundle_path = work_file(proof.get('source_plan')), work_file(proof.get('target_bundle'))
        old_plan = json.loads(source_path.read_text(encoding='utf-8-sig'))
        import verification_results as viewer
        old_check = plan_check(old_plan, feature['id'], check, viewer)
        if consolidating:
            return consolidate(old_plan, old_check, bundle_path, target_id)
        old_scope = old_plan.get('workflow_scope', {})
        need(Path(old_scope.get('root', '')).resolve() == root
             and old_scope.get('task_identity') == task_identity(state), 'rebind_source_task_binding_mismatch')
        old_state_path = work_file(old_scope.get('state'))
        old_state = json.loads(old_state_path.read_text(encoding='utf-8-sig'))
        need(task_identity(old_state) == task_identity(state) and old_state.get('base') == state.get('base'),
             'rebind_source_task_preimage_mismatch')
        old_revision = source_revision(old_check)
        need(old_check.get('required') is True and old_check.get('selection', {}).get('status') == 'selected',
             'rebind_source_check_not_required')
        need(old_scope.get('selection') and any(row.get('feature') == feature['id']
             and row.get('check') == check and row.get('selected') is True for row in old_scope['selection']),
             'rebind_source_check_not_selected')
        base = state.get('base')
        need(isinstance(base, str) and is_ancestor(old_revision, base), 'rebind_source_not_based_on_task_baseline')
        old_project = git_json(old_revision, '.harness/project.yaml')
        old_config = configuration(old_project)
        old_feature = feature_for(old_config, feature['id'])
        need(scope_feature(old_plan, feature['id']) == old_feature, 'rebind_source_feature_preimage_mismatch')
        old_links = old_state.get('check_links', {}).get(feature['id'], {})
        current_links = state.get('check_links', {}).get(feature['id'], {})
        need(old_links == current_links and check in current_links.get('checks', [])
             and current_links.get('prevention', []) == old_feature.get('prevention', []),
             'rebind_task_check_links_mismatch')
        need(old_feature.get('checks', []).count(check) == 1, 'rebind_source_check_identity_missing')

        wrapper = json.loads(bundle_path.read_text(encoding='utf-8-sig'))
        bundle = wrapper.get('execution', {}).get('bundle', wrapper) if isinstance(wrapper, dict) else None
        need(isinstance(bundle, dict), 'rebind_target_bundle_invalid')
        new_plan_path = resolve_bundle_file(bundle.get('source_plan'), bundle_path.parent)
        bound_plan_path = resolve_bundle_file(bundle.get('plan'), bundle_path.parent)
        new_plan = json.loads(new_plan_path.read_text(encoding='utf-8-sig'))
        new_check = plan_check(new_plan, feature['id'], target_id, viewer)
        new_scope = new_plan.get('workflow_scope', {})
        need(Path(new_scope.get('root', '')).resolve() == root
             and new_scope.get('task_identity') == task_identity(state), 'rebind_target_task_binding_mismatch')
        target_state_path = work_file(new_scope.get('state'))
        target_state = json.loads(target_state_path.read_text(encoding='utf-8-sig'))
        need(task_identity(target_state) == task_identity(state), 'rebind_target_state_mismatch')
        target_revision = source_revision(new_check)
        head = git(root, 'rev-parse', 'HEAD').decode().strip()
        need(old_revision != target_revision and is_ancestor(old_revision, target_revision)
             and isinstance(base, str) and is_ancestor(base, target_revision)
             and target_revision == head and not git(root, 'status', '--porcelain').strip(),
             'rebind_target_source_not_current_clean_lineage')
        need(new_check.get('required') is True and new_check.get('selection', {}).get('status') == 'selected'
             and new_scope.get('selection') and any(row.get('feature') == feature['id']
                 and row.get('check') == target_id and row.get('selected') is True for row in new_scope['selection']),
             'rebind_target_check_not_required')

        new_project = git_json(target_revision, '.harness/project.yaml')
        need(new_project == project, 'rebind_current_project_differs_from_git')
        new_config = configuration(new_project)
        new_feature = feature_for(new_config, feature['id'])
        need(new_feature == feature and scope_feature(new_plan, feature['id']) == new_feature,
             'rebind_target_feature_preimage_mismatch')
        need(target_id not in old_project.get('commands', {})
             and target_id not in old_project.get('impact', {}).get('feature_selectors', {})
             and target_id not in {identity for item in old_config['features'] for identity in item.get('checks', [])}
             and target_id not in {item.get('id') for item in git_json(old_revision, old_config['assertions']).get('checks', [])},
             'rebind_target_check_collision')
        transformed_feature = deepcopy(old_feature)
        transformed_feature['checks'] = [target_id if value == check else value for value in transformed_feature['checks']]
        for field in ('coverage', 'prevention'):
            for row in transformed_feature.get(field, []) or []:
                if isinstance(row, dict) and row.get('check') == check:
                    row['check'] = target_id
        need(transformed_feature == new_feature, 'rebind_feature_consumers_or_prevention_changed')

        spec_path = old_config.get('assertions')
        need(isinstance(spec_path, str) and spec_path == new_config.get('assertions'),
             'rebind_assertion_source_changed')
        old_spec, new_spec = git_json(old_revision, spec_path), git_json(target_revision, spec_path)
        old_spec_row, new_spec_row = spec_check(old_spec, feature['id'], check), spec_check(new_spec, feature['id'], target_id)
        need(not any(row.get('id') == target_id for row in old_spec.get('checks', []) if isinstance(row, dict)),
             'rebind_target_assertion_collision')
        normalized_old_spec, normalized_new_spec = deepcopy(old_spec_row), deepcopy(new_spec_row)
        normalized_old_spec['id'] = normalized_new_spec['id'] = '<check-identity>'
        for before, after in zip(normalized_old_spec.get('raw_observations', []),
                                 normalized_new_spec.get('raw_observations', [])):
            need(isinstance(before.get('path'), str) and isinstance(after.get('path'), str),
                 'rebind_explicit_report_output_required')
            before['path'] = after['path'] = '<explicit-report-output>'
        need(len(old_spec_row.get('raw_observations', [])) == len(new_spec_row.get('raw_observations', []))
             and normalized_old_spec == normalized_new_spec, 'rebind_assertion_or_requirement_changed')
        transformed_spec = deepcopy(old_spec)
        old_rows = transformed_spec.get('checks', [])
        old_index = old_rows.index(old_spec_row)
        transformed_spec['checks'][old_index] = new_spec_row
        need(transformed_spec == new_spec, 'rebind_assertion_registry_changed')

        old_registry, old_mapping, old_descriptor = command_entry(old_project, check)
        new_registry, _, new_descriptor = command_entry(new_project, target_id)
        need(old_registry == new_registry
             and normalized_command(old_descriptor, old_spec_row) == normalized_command(new_descriptor, new_spec_row),
             'rebind_registered_command_changed')
        bind_plan_check(old_project, check, old_spec_row, old_check)
        bind_plan_check(new_project, target_id, new_spec_row, new_check)
        for item, spec_row in ((old_check, old_spec_row), (new_check, new_spec_row)):
            need(item.get('expected') == spec_row.get('expected'), 'rebind_expected_outcome_changed')

        expected_project = deepcopy(old_project)
        expected_config = configuration(expected_project)
        expected_feature = feature_for(expected_config, feature['id'])
        expected_feature['checks'] = [target_id if value == check else value for value in expected_feature['checks']]
        for field in ('coverage', 'prevention'):
            for row in expected_feature.get(field, []) or []:
                if isinstance(row, dict) and row.get('check') == check:
                    row['check'] = target_id
        if old_registry == 'commands':
            expected_project.setdefault('commands', {})[target_id] = deepcopy(new_descriptor)
        else:
            expected_project.setdefault('impact', {}).setdefault('feature_selectors', {})[target_id] = deepcopy(new_descriptor)
        need(expected_project == new_project, 'rebind_project_changed_beyond_identity')

        metadata = {'.harness/project.yaml', repo_name(spec_path),
                    *(repo_name(name) for name in old_feature.get('map', []))}
        for name in old_feature.get('map', []):
            old_map = git_bytes(old_revision, name)
            new_map = git_bytes(target_revision, name)
            need(transformed_map(old_map, feature['id'], check, target_id) == new_map,
                 'rebind_feature_map_changed_beyond_check_identity')
        old_fixture, new_fixture = repository_hashes(old_check), repository_hashes(new_check)
        need(set(old_fixture) == set(new_fixture) and metadata <= set(old_fixture),
             'rebind_fixture_references_changed')
        for name, value in old_fixture.items():
            need(matches_git_preimage(name, value, old_revision), 'rebind_fixture_preimage_mismatch')
            if name not in metadata:
                need(value == new_fixture[name], 'rebind_fixture_inputs_changed')
        changed = set(git(root, 'diff', '--name-only', '-z', old_revision, target_revision).decode('utf-8').split('\0')) - {''}
        source_paths = old_feature['sources'] + new_feature['sources']
        criteria_paths = set(old_feature.get('criteria', []))
        for name in changed:
            need(not any(fnmatchcase(name, pattern) for pattern in source_paths)
                 and name not in criteria_paths, 'rebind_source_or_criteria_changed')
            need(name in metadata or (name.startswith('docs/') and name.endswith('.md')),
                 'rebind_unrelated_source_change')

        need(normalize_rebind_check(root, old_check, metadata)
             == normalize_rebind_check(root, new_check, metadata), 'rebind_check_contract_changed')
        viewed = viewer.view_bundle(bundle_path, workflow_state=target_state_path.relative_to(root))
        matches = [item for item in viewed.get('items', [])
                   if item.get('feature') == feature['id'] and item.get('id') == target_id]
        need(viewed.get('test_commands_executed') == 0 and len(matches) == 1,
             'rebind_target_evidence_missing')
        item = matches[0]
        need(viewed.get('status') == 'PASS' and item.get('historical_status') == 'PASS'
             and item.get('current_status') == 'PASS' and item.get('current_reuse') == 'REUSABLE'
             and item.get('selected') is True and item.get('capture', {}).get('execution') == 'exited'
             and item.get('capture', {}).get('exit_code') == 0, 'rebind_target_evidence_not_current_pass')
        return []
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.CalledProcessError) as error:
        return [str(error) if isinstance(error, ValueError) and str(error) else 'rebind_evidence_unavailable']


def inspect_check_retirements(root, project, feature, state, review, reviewed, *, bundle_cache=None):
    prior = state.get('check_links', {}).get(feature['id'], {})
    result = []
    for check in sorted(set(prior.get('checks', [])) - set(feature['checks'])):
        decision = review.get('check_decisions', {}).get(check, {})
        remaining = []
        if not reviewed:
            remaining.append('current_semantic_review_required')
        if ((decision.get('action') == 'rebind' and decision.get('reason') == 'check_identity_migrated')
                or (decision.get('action') == 'consolidate' and decision.get('reason') == 'duplicate_execution'
                    and 'consolidation' in decision)):
            remaining.extend(inspect_check_identity_rebind(root, project, feature, state, check, decision))
            result.append({'feature': feature['id'], 'check': check, 'decision': decision,
                           'status': 'BLOCKED' if remaining else 'PRESERVED', 'remaining': sorted(set(remaining))})
            continue
        if decision.get('action') not in {'remove', 'consolidate'} or not decision.get('reason'):
            remaining.append('preservation_decision_missing')
        if decision.get('action') == 'remove' and decision.get('reason') == 'requirement_retired':
            proof = decision.get('retirement', {})
            for field in ('authorization_refs', 'requirement_refs', 'references'):
                if not isinstance(proof.get(field), list) or not proof[field] or any(
                        not isinstance(v, str) or not v.strip() for v in proof[field]):
                    remaining.append(f'retirement.{field}')
            detailed = 'entrypoints' in proof or 'callers' in proof
            for field in ('entrypoints', 'callers') if detailed else ('removed_entrypoints', 'removed_callers'):
                items = proof.get(field)
                if not isinstance(items, list) or not items:
                    remaining.append(f'retirement.{field}')
                    continue
                for item in items:
                    if detailed:
                        if (not isinstance(item, dict) or not isinstance(item.get('name'), str) or not item['name'].strip() or
                                item.get('disposition') not in {'removed', 'changed', 'retained', 'not_applicable'} or
                                not isinstance(item.get('reason'), str) or not item['reason'].strip() or
                                not isinstance(item.get('references'), list) or not item['references']):
                            remaining.append(f'retirement.{field}.disposition_required')
                        elif any(file_hash(root, name) is None for name in item['references']):
                            remaining.append('retirement_reference_missing')
                    elif not isinstance(item, str) or not item.strip():
                        remaining.append(f'retirement.{field}')
            if not isinstance(proof.get('remaining_impact'), str) or not proof['remaining_impact'].strip():
                remaining.append('retirement.remaining_impact')
            failures = prior.get('prevention', [])
            retired = proof.get('retired_failures', [])
            if not isinstance(retired, list) or not retired or any(not isinstance(p, dict) or any(
                    not isinstance(p.get(k), str) or not p[k].strip() for k in ('failure', 'scope')) for p in retired) or any(not any(isinstance(p, dict) and all(
                    p.get(k) == failure.get(k) for k in ('failure', 'scope')) for p in retired)
                    for failure in failures if failure.get('check') == check):
                remaining.append('retired_failure_scope_unaccounted')
            for field in ('authorization_refs', 'requirement_refs', 'references'):
                for name in proof.get(field, []) if isinstance(proof.get(field, []), list) else []:
                    if file_hash(root, name) is None:
                        remaining.append('retirement_reference_missing')
            requirements = proof.get('requirement_refs', [])
            if not isinstance(requirements, list) or not requirements or any(
                    name not in prior.get('criteria_before', {}) or
                    file_hash(root, name) == prior['criteria_before'][name] for name in requirements):
                remaining.append('requirement_change_not_observed')
            if any(row.get('check') == check for row in feature.get('coverage', []) + feature.get('prevention', [])):
                remaining.append('retired_check_still_linked')
            source_refs = {name for item in proof.get('entrypoints', []) if isinstance(item, dict)
                           for name in item.get('references', [])} if detailed else set(state.get('baseline', {}))
            if detailed:
                owners = [p.get('owner_refs', []) for p in failures if p.get('check') == check]
                if not owners or any(not isinstance(refs, list) or not refs or any(
                        not isinstance(name, str) or name not in state.get('baseline', {}) or
                        not any(fnmatchcase(name, pattern) for pattern in feature['sources']) for name in refs) for refs in owners):
                    remaining.append('retired_rule_owner_binding_required')
                    source_refs = set()
                else:
                    source_refs &= {name for refs in owners for name in refs}
            if not any(file_hash(root, name) != value for name, value in state.get('baseline', {}).items()
                       if name in source_refs and any(fnmatchcase(name, pattern) for pattern in feature['sources'])):
                remaining.append('retired_rule_source_change_not_observed' if detailed else 'entrypoint_removal_not_observed')
            result.append({'feature': feature['id'], 'check': check, 'decision': decision,
                           'status': 'BLOCKED' if remaining else 'PRESERVED', 'remaining': sorted(set(remaining))})
            continue
        failures = [p for p in prior.get('prevention', []) if p.get('check') == check]
        if not failures:
            remaining.append('prior_detection_scope_unknown')
        for failure in failures:
            proof = next((p for p in decision.get('preservation', []) if
                          all(p.get('guardrail', {}).get(key) == failure.get(key) for key in ('failure', 'scope'))), None)
            if not proof:
                remaining.append(f'detection_preservation_missing:{failure["failure"]}')
                continue
            guardrail = proof.get('guardrail', {})
            if guardrail.get('check') not in feature['checks'] or not any(
                    all(p.get(key) == guardrail.get(key) for key in ('failure', 'scope', 'check', 'normal_exception', 'reconsider'))
                    for p in feature.get('prevention', [])):
                remaining.append('replacement_prevention_inactive')
            try:
                remaining.extend(feedback_evidence(root, feature, proof, original_check=check, bundle_cache=bundle_cache))
            except (OSError, ValueError, KeyError, TypeError):
                remaining.append('replacement_evidence_unavailable')
        result.append({'feature': feature['id'], 'check': check, 'decision': decision,
                       'status': 'BLOCKED' if remaining else 'PRESERVED', 'remaining': sorted(set(remaining))})
    return result


def maintenance_summary(root, project, state=None, history=(), *, retirements=()):
    """Inspect explicitly connected runs, not all past work or speculative pruning."""
    config = configuration(project)
    state = state or {}
    commands = dict(project.get('commands', {}))
    commands.update(project.get('impact', {}).get('feature_selectors', {}))
    checks = {}
    for feature in config['features']:
        prior = state.get('check_links', {}).get(feature['id'], {})
        for check in dict.fromkeys(feature['checks'] + prior.get('checks', [])):
            row = checks.setdefault(check, {'id': check, 'features': [], 'failures': [], 'runs': [],
                'disposition': 'retain', 'retain_reason': 'No current detection-preservation evidence; semantic review required'})
            row['features'].append(feature['id'])
            for prevention in feature.get('prevention', []) + prior.get('prevention', []):
                if prevention.get('check') == check and prevention not in row['failures']:
                    row['failures'].append(prevention)
    paths = list(history) + [review['bundle'] for review in state.get('reviews', {}).values() if review.get('bundle')]
    paths += [path for links in state.get('results', {}).values() for path in links]
    paths += [entry[key] for entry in state.get('feedback', {}).values() for key in ('red_bundle', 'green_bundle') if entry.get(key)]
    paths += [proof[key] for review in state.get('reviews', {}).values()
              for decision in review.get('check_decisions', {}).values() for proof in decision.get('preservation', [])
              for key in ('original_bundle', 'red_bundle', 'green_bundle') if proof.get(key)]
    import verification_results as viewer
    findings, seen, variations = [], set(), {}
    for name in dict.fromkeys(paths):
        try:
            path = local_path(root, name)
            binding = json.loads(path.read_text(encoding='utf-8'))
            if binding.get('format') == 'unittest-captures-v1':
                feature = next(f for f in config['features'] if f['id'] == binding.get('feature'))
                items = inspect_unittest_evidence(root, feature, commands, binding).get('items', [])
            else:
                viewed = viewer.view_bundle(path)
                items = viewed.get('items', [])
                if not items:
                    findings.append(f'maintenance_bundle_unavailable:{name}')
            for item in items:
                if item['id'] not in checks or not item['capture'].get('path'):
                    continue
                record_path = local_path(root, str(Path(item['capture']['path']).resolve().relative_to(root.resolve())))
                record = json.loads(record_path.read_text(encoding='utf-8'))
                key = (item['id'], record.get('run_id'), digest(record))
                row = checks[item['id']]
                if key not in seen:
                    seen.add(key)
                    row['runs'].append({'run_id': record.get('run_id'), 'capture': str(record_path),
                        'capture_sha256': digest(record),
                        'execution': record.get('execution'), 'exit_code': record.get('exit_code'),
                        'elapsed_seconds': record.get('elapsed_seconds'),
                        'native_report_error': record.get('json_report', {}).get('error'),
                        'cleanup_incomplete': bool(record.get('cleanup_incomplete')), 'judgments': []})
                run = next(run for run in row['runs'] if run['run_id'] == record.get('run_id') and run['capture_sha256'] == digest(record))
                judgment = {key: item.get(key) for key in ('feature', 'historical_status', 'current_status', 'current_reuse', 'reasons')}
                judgment['raw'] = [{key: raw[key] for key in ('path', 'sha256', 'pointer')} | {
                    'assertions': [{'assertion': obs['assertion'], 'matched': obs['matched']}
                                   for obs in raw.get('observations', [])]} for raw in item.get('raw', [])]
                if judgment not in run['judgments']:
                    run['judgments'].append(judgment)
                conditions = dict(item.get('conditions', {}).get('expected', {}))
                conditions['command'] = commands.get(item['id'])
                assertions = [obs['assertion'] for raw in item.get('raw', []) for obs in raw.get('observations', [])]
                if item.get('conditions', {}).get('expected') and assertions:
                    signature = (item['id'], item['feature'], digest({'conditions': conditions, 'assertions': assertions}))
                    group = variations.setdefault(signature, {'runs': set(), 'statuses': set()})
                    group['runs'].add(record.get('run_id'))
                    group['statuses'].add(item['historical_status'])
        except (OSError, ValueError, TypeError, KeyError, StopIteration):
            findings.append(f'maintenance_evidence_unavailable:{name}')
    for row in checks.values():
        costs = [run['elapsed_seconds'] for run in row['runs'] if type(run['elapsed_seconds']) in (int, float)
                 and math.isfinite(run['elapsed_seconds']) and run['elapsed_seconds'] >= 0]
        row['cost'] = {'unique_runs': len(row['runs']), 'measured_runs': len(costs),
                       'elapsed_seconds': sum(costs) if costs else None,
                       'native_failures': sum(type(run['exit_code']) is int and run['exit_code'] != 0 for run in row['runs']),
                       'incomplete_runs': sum(run['execution'] != 'exited' or run['cleanup_incomplete'] for run in row['runs']),
                       'native_report_errors': sum(bool(run['native_report_error']) for run in row['runs'])}
        overlaps = sorted({other['id'] for other in checks.values() if other['id'] != row['id'] and any(
            (left['failure'], left.get('scope')) == (right['failure'], right.get('scope'))
            for left in row['failures'] for right in other['failures'])})
        row['declared_overlap'] = overlaps
        row['active_features'] = [f['id'] for f in config['features'] if row['id'] in f['checks']]
        active_checks = {check for f in config['features'] for check in f['checks']}
        row['candidate'] = 'review_overlap' if row['active_features'] and any(check in active_checks for check in overlaps) else 'retain'
        row['declared_unique_failures'] = [p for p in row['failures'] if not any(
            other['id'] != row['id'] and other['id'] in active_checks and any(
                (p['failure'], p.get('scope')) == (q['failure'], q.get('scope')) for q in other['failures']) for other in checks.values())]
        if row['active_features'] and row['runs'] and row['failures']:
            row['retain_reason'] = 'Active failure detector; retain unless equivalent replacement is demonstrated'
        row['registered_command'] = commands.get(row['id'])
        row['retirements'] = [item for item in retirements if item['check'] == row['id']]
        if row['retirements'] and all(item['status'] == 'PRESERVED' for item in row['retirements']) and not row['active_features']:
            row['disposition'] = ('removed_with_retired_requirement' if all(
                item['decision'].get('reason') == 'requirement_retired' for item in row['retirements']) else 'removed_with_preserved_detection')
            row['retain_reason'] = None
            row['candidate'] = 'completed_consolidation_or_removal'
        row['same_conditions_outcome_variation'] = [{'feature': feature, 'condition_id': signature,
            'runs': sorted(group['runs']), 'statuses': sorted(group['statuses'])}
            for (check, feature, signature), group in variations.items()
            if check == row['id'] and len(group['runs']) > 1 and len(group['statuses']) > 1]
    return {'read_only': True, 'test_commands_executed': 0, 'checks': list(checks.values()), 'findings': findings,
            'meaning': 'Declared overlap and outcome variation require Agent judgment; counts/cost never authorize deletion'}


def difference_subject(entry):
    return {key: entry.get(key) for key in ('id', 'candidate_id', 'feature', 'kind', 'scope', 'expected', 'observed')}


def difference_criteria(config, feature):
    return set(feature['criteria']) | {system['guide'] for system in config.get('ui_systems', {}).values()
                                       if feature['id'] in system['consumers']}


def difference_criteria_connections(config, feature):
    return {'feature': feature['id'], 'criteria': sorted(feature['criteria']),
            'ui_guides': {identity: system['guide'] for identity, system in config.get('ui_systems', {}).items()
                         if feature['id'] in system['consumers']}}


def difference_review_matches(entry, config, feature):
    review = entry.get('user_review', {})
    refs = review.get('criteria_refs')
    return (isinstance(review.get('id'), str) and bool(review['id'].strip()) and
            bool(entry.get('candidate_id')) and review.get('candidate_id') == entry['candidate_id'] and
            review.get('decision') in {'agree', 'intentional_difference'} and
            review.get('disposition') == 'intentional_difference' and review.get('scope') == entry.get('scope') and
            isinstance(refs, list) and bool(refs) and all(isinstance(name, str) and
                name in difference_criteria(config, feature) for name in refs) and
            difference_criteria(config, feature).issubset(refs))


def feedback_basis(entry):
    return digest({key: value for key, value in entry.items()
                   if key not in {'supersession', 'supersession_history'}})


def feedback_successor(root, config, state, identity, proof):
    if (not isinstance(proof, dict) or not isinstance(proof.get('feedback'), str)
            or not isinstance(proof.get('reason'), str) or not proof['reason'].strip()
            or not isinstance(proof.get('references'), list) or not proof['references']):
        raise ValueError('feedback_supersession_review_required')
    if any(not isinstance(item, dict) or item.get('id') != key
           for key, item in state.get('feedback', {}).items()):
        raise ValueError('feedback_record_identity_mismatch')
    successor = state.get('feedback', {}).get(proof['feedback'])
    if (proof['feedback'] == identity or not isinstance(successor, dict)
            or successor.get('id') != proof['feedback']
            or successor.get('feature') not in {feature['id'] for feature in config['features']}):
        raise ValueError('feedback_supersession_current_target_required')
    # One direct owner link keeps cycles and hidden chains out of the completion path.
    if successor.get('supersession') is not None or any(
            isinstance(item.get('supersession'), dict) and item['supersession'].get('feedback') == identity
            for item in state.get('feedback', {}).values()):
        raise ValueError('feedback_supersession_chain_not_supported')
    hashes = {}
    for name in proof['references']:
        if not isinstance(name, str) or not name or (value := file_hash(root, name)) is None:
            raise ValueError('feedback_supersession_reference_missing')
        hashes[name] = value
    return successor, hashes


def record_feedback(root, project, state, entry):
    if not isinstance(entry, dict) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', str(entry.get('id', ''))):
        raise ValueError('feedback_identity_required')
    previous = state.get('feedback', {}).get(entry['id'], {})
    if previous and previous['feature'] != entry['feature']:
        raise ValueError('feedback_target_changed')
    if 'supersession_history' in entry:
        raise ValueError('feedback_supersession_history_is_read_only')
    if 'supersession' in entry:
        if not previous or set(entry) != {'id', 'feature', 'supersession'}:
            raise ValueError('feedback_supersession_requires_existing_unchanged_record')
        proof = deepcopy(entry['supersession'])
        if proof is not None:
            if not isinstance(proof, dict) or set(proof) != {'feedback', 'reason', 'references'}:
                raise ValueError('feedback_supersession_review_required')
            successor, hashes = feedback_successor(root, configuration(project), state, entry['id'], proof)
            proof.update(source_basis=feedback_basis(previous), target_basis=feedback_basis(successor),
                         reference_hashes=hashes)
        result = deepcopy(state)
        updated = result['feedback'][entry['id']]
        if updated.get('supersession') and updated['supersession'] != proof:
            updated.setdefault('supersession_history', []).append(updated['supersession'])
        updated['supersession'] = proof
        return result
    feature = next((f for f in configuration(project)['features'] if f['id'] == entry.get('feature')), None)
    if feature is None:
        raise ValueError('feedback_feature_unknown')
    updated = dict(previous, **deepcopy(entry))
    for field in ('decision_hashes', 'decision_binding', 'decision_history', 'confirmation_hashes', 'recovery_hashes', 'environment_history', 'prevention_binding'):
        if field in entry:
            raise ValueError('feedback_decision_basis_is_read_only')
    kinds = {'requirement_violation', 'requirement_change', 'intentional_difference', 'oracle_tool_error',
             'environment_limit', 'unknown'}
    if updated.get('kind', 'requirement_violation') not in kinds:
        raise ValueError('feedback_kind_invalid')
    for field in ('evidence_refs', 'owner_refs', 'authorization_refs'):
        if field in updated and (not isinstance(updated[field], list) or not updated[field] or
                any(not isinstance(name, str) or file_hash(root, name) is None for name in updated[field])):
            raise ValueError(f'feedback_reference_missing:{field}')
    if 'user_review' in updated:
        review = updated['user_review']
        if not isinstance(review, dict) or review.get('decision') not in {'agree', 'intentional_difference', 'defer', 'opinion'}:
            raise ValueError('feedback_user_review_decision_invalid')
        if not isinstance(review.get('reference'), str) or not review['reference'] or file_hash(root, review['reference']) is None:
            raise ValueError('feedback_user_review_reference_missing')
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
        if any(fnmatchcase(name, pattern) for pattern in source_patterns(configuration(project), feature))})
    updated['criteria_before'] = previous.get('criteria_before', {name: file_hash(root, name) for name in feature['criteria']})
    references = [name for field in ('evidence_refs', 'owner_refs', 'authorization_refs') for name in updated.get(field, [])]
    if updated.get('user_review'):
        references.append(updated['user_review']['reference'])
    if updated.get('kind') == 'intentional_difference':
        old_review = previous.get('decision_binding', {}).get('review', previous.get('user_review', {}))
        new_review = entry.get('user_review', {})
        history = deepcopy(previous.get('decision_history', []))
        used = [item['user_review'].get('id') for item in history] + [old_review.get('id')]
        if new_review and new_review != old_review and new_review.get('id') in used and new_review.get('id'):
            raise ValueError('feedback_user_review_identity_reused')
        updated['decision_hashes'] = deepcopy(previous.get('decision_hashes', {}))
        updated['decision_binding'] = deepcopy(previous.get('decision_binding', {}))
        if new_review and new_review != old_review:
            if old_review:
                history.append({'user_review': deepcopy(old_review), **{key: deepcopy(previous.get(key, {})) for key in
                                ('decision_hashes', 'decision_binding')}})
            updated['decision_binding'] = {}
            if difference_review_matches(updated, configuration(project), feature):
                updated['decision_hashes'] = {name: file_hash(root, name) for name in references}
                updated['decision_binding'] = {'subject': difference_subject(updated), 'review': deepcopy(new_review),
                    'criteria': {name: file_hash(root, name) for name in new_review['criteria_refs']},
                    'criteria_connections': difference_criteria_connections(configuration(project), feature)}
        updated['decision_history'] = history
    else:
        # Classification confirmation cannot rewrite an existing exception decision.
        updated['confirmation_hashes'] = {name: file_hash(root, name) for name in references}
    if updated.get('kind') == 'environment_limit' and updated.get('environment_recovery'):
        if previous.get('red_bundle') and previous['red_bundle'] != updated.get('red_bundle'):
            raise ValueError('environment_original_failure_is_read_only')
        proof = updated['environment_recovery']
        if not isinstance(proof, dict):
            raise ValueError('environment_recovery_must_be_object')
        names = ['.harness/project.yaml', *feature['criteria'], *proof.get('configuration_refs', []), *proof.get('attempt_captures', [])]
        if not names or any(not isinstance(name, str) or file_hash(root, name) is None for name in names):
            raise ValueError('environment_recovery_references_required')
        updated['recovery_hashes'] = {name: file_hash(root, name) for name in names}
        updated['environment_history'] = deepcopy(previous.get('environment_history', []))
        if previous.get('environment_recovery') and previous['environment_recovery'] != proof:
            updated['environment_history'].append({key: deepcopy(previous.get(key)) for key in
                ('environment_recovery', 'recovery_hashes', 'green_bundle')})
    if 'prevention_review' in entry:
        proof = updated['prevention_review']
        references = prevention_review_references(root, proof)
        if proof != previous.get('prevention_review'):
            if proof['id'] == previous.get('prevention_review', {}).get('id'):
                raise ValueError('prevention_review_requires_new_identity')
            names = set(references + updated.get('repair_paths', []) +
                        updated.get('guardrail', {}).get('owner_refs', []) + feature['criteria'] + ['.harness/project.yaml'])
            updated['prevention_binding'] = {'subject': prevention_subject(updated), 'task_identity': task_identity(state),
                'references': {name: file_hash(root, name) for name in names}}
    result = deepcopy(state)
    result.setdefault('feedback', {})[entry['id']] = updated
    return result


def bundle_observation(viewer, path, *, include_scope=True, bundle_cache=None):
    if bundle_cache is None:
        return viewer.view_bundle(path, include_scope=include_scope)
    key = (path.resolve(), include_scope)
    if key not in bundle_cache:
        bundle_cache[key] = viewer.view_bundle(path, include_scope=include_scope)
    return deepcopy(bundle_cache[key])


def feedback_evidence(root, feature, entry, *, original_check=None, bundle_cache=None):
    """Fixed viewer/raw joins, never run a submitted reproduction or command."""
    import verification_results as viewer
    red = bundle_observation(viewer, local_path(root, entry['red_bundle']), bundle_cache=bundle_cache)
    green = bundle_observation(viewer, local_path(root, entry['green_bundle']), bundle_cache=bundle_cache)
    check = entry['guardrail']['check']
    before = next((i for i in red.get('items', []) if i['feature'] == feature['id'] and i['id'] == check), None)
    after = next((i for i in green.get('items', []) if i['feature'] == feature['id'] and i['id'] == check), None)
    reasons = []
    def unbound(item):
        return item['capture']['execution'] != 'exited' or any(reason == 'source_plan_hash_mismatch' or
            reason.startswith(('raw_producer', 'capture_feature', 'capture_check', 'capture_run',
                               'capture_source_changed', 'capture_invalid', 'assessment_')) for reason in item['reasons'])
    if not before or before['historical_status'] != 'ISSUES':
        reasons.append('original_failure_evidence_missing')
    if before and unbound(before):
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
    if original_check is not None:
        original_result = bundle_observation(viewer, local_path(root, entry.get('original_bundle', entry['red_bundle'])), bundle_cache=bundle_cache)
        original = next((i for i in original_result.get('items', []) if i['feature'] == feature['id'] and i['id'] == original_check), None)
        if (not original or original['historical_status'] != 'ISSUES' or unbound(original) or not any(
                not obs['matched'] and obs['assertion'] in failing for obs in assertions(original))):
            reasons.append('prior_detector_evidence_missing')
    if normal == regression or not any(obs['assertion']['pointer'] == normal and obs['matched'] for obs in assertions(after)):
        reasons.append('nearby_normal_evidence_missing')
    if before and after:
        descriptor = green['bundle']
        bound = viewer.read_json(viewer.resolve_bundle_file(descriptor['plan'],
            base=local_path(root, entry['green_bundle']).parent, label='feedback plan'))[0]
        scope = bound.get('workflow_scope', {})
        if scope.get('root') != str(root.resolve()) or feature not in scope.get('features', []):
            reasons.append('prepared_project_binding_required')
    return reasons


def environment_recovery_remaining(root, feature, entry, *, bundle_cache=None):
    """Validate a project-owned same-target recheck; no diagnostic or repair is executed."""
    proof = entry.get('environment_recovery', {})
    if not proof or not entry.get('red_bundle') or not entry.get('green_bundle') or not entry.get('root_cause'):
        return ['environment_resume_required']
    try:
        if proof.get('classification') not in {'command_missing', 'endpoint_missing', 'access_denied', 'os_mismatch', 'architecture_mismatch'}:
            return ['environment_cause_unconfirmed']
        if not proof.get('configuration_refs') or not proof.get('attempt_captures') or not isinstance(proof.get('target'), dict) or not proof['target']:
            return ['environment_recovery_contract_required']
        hashes = entry.get('recovery_hashes', {})
        names = ['.harness/project.yaml', *feature['criteria'], *proof['configuration_refs'], *proof['attempt_captures']]
        if any(name not in hashes or file_hash(root, name) != hashes[name] for name in names):
            return ['environment_recovery_configuration_or_attempt_stale']
        exceptions = local_path(root, '.harness/environment-exceptions.json')
        if exceptions.exists():
            document = json.loads(exceptions.read_text(encoding='utf-8'))
            if document.get('schema_version') != 1 or not isinstance(document.get('exceptions'), list):
                return ['environment_exception_document_invalid']
            if any(item.get('capability') == proof.get('capability') and item.get('retry') == 'skip_until_manual_reenable'
                   for item in document['exceptions']):
                return ['environment_manually_disabled']
        project = json.loads((root / '.harness/project.yaml').read_text(encoding='utf-8'))
        contract = configuration(project).get('environment_recovery', {}).get(proof.get('capability'), {})
        if (not contract or contract.get('check') != proof.get('check') or
                contract.get('recovery_command') != proof.get('recovery_command') or
                contract.get('target_pointer') != proof.get('target_pointer') or contract.get('target') != proof['target']):
            return ['environment_project_target_contract_required']
        commands = dict(project.get('commands', {}))
        commands.update(project.get('impact', {}).get('feature_selectors', {}))
        descriptor = commands.get(proof.get('check'))
        if (proof.get('check') not in feature['checks'] or not isinstance(descriptor, dict)
                or not proof.get('capability') or descriptor.get('capability') != proof['capability']):
            return ['environment_registered_capability_required']
        import verification_results as viewer
        red = bundle_observation(viewer, local_path(root, entry['red_bundle']), include_scope=False, bundle_cache=bundle_cache)
        green = inspect_evidence(root, feature, commands, entry['green_bundle'], bundle_cache=bundle_cache)
        old = next(i for i in red['items'] if i['feature'] == feature['id'] and i['id'] == proof['check'] and i['selected'])
        new = next(i for i in green['items'] if i['feature'] == feature['id'] and i['id'] == proof['check'] and i['selected'])
        if new['current_status'] != 'PASS' or new['current_reuse'] != 'REUSABLE' or old.get('run_id') == new.get('run_id'):
            return ['environment_current_recheck_required']
        if old['capture']['execution'] == 'exited' and old['capture']['exit_code'] == 0:
            return ['environment_original_failure_required']
        expected_cwd = local_path(root, descriptor.get('working_directory', '.')).resolve()
        for item in (old, new):
            condition = item['conditions']['expected']['command']
            if (Path(item['capture']['cwd']).resolve() != expected_cwd or item['capture']['argv'] !=
                    resolve_report_command(root, descriptor['argv'], condition.get('report_dir'))):
                return ['environment_recheck_target_changed']
            targets = []
            for raw in item['raw']:
                path = local_path(root, Path(raw['path']).relative_to(root).as_posix())
                data, content = viewer.read_json(path)
                if viewer.sha256(content) != raw['sha256']:
                    return ['environment_target_evidence_stale']
                if item is old and data.get('status') != 'BLOCKED':
                    return ['environment_original_failure_required']
                targets.append(viewer.json_pointer(data, proof['target_pointer']))
                if item is old and viewer.json_pointer(data, contract['failure_pointer']) != proof['classification']:
                    return ['environment_original_cause_mismatch']
                if item is new:
                    names = contract.get('environment_variables')
                    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
                        return ['environment_context_contract_required']
                    observed_environment = viewer.json_pointer(data, contract['environment_pointer'])
                    current_environment = {name: os.environ.get(name) for name in names}
                    if observed_environment != current_environment:
                        return ['environment_context_changed']
            if not targets or any(target != proof['target'] for target in targets):
                return ['environment_recheck_target_changed']
        for name in proof['attempt_captures']:
            capture = json.loads(local_path(root, name).read_text(encoding='utf-8'))
            recovery = commands.get(proof.get('recovery_command'), {})
            if (not isinstance(recovery, dict) or recovery.get('capability') != proof['capability'] or
                    not capture.get('run_id') or capture.get('argv') != recovery.get('argv') or
                    Path(capture.get('cwd', '')).resolve() != local_path(root, recovery.get('working_directory', '.')).resolve() or
                    capture.get('execution') not in {'exited', 'timeout', 'unavailable'}):
                return ['environment_attempt_capture_required']
        return []
    except (OSError, ValueError, KeyError, TypeError, StopIteration, AttributeError):
        return ['environment_recovery_evidence_unavailable']


def prevention_subject(entry):
    return digest({key: entry.get(key) for key in ('guardrail', 'prevention_review', 'repair_paths')})


def prevention_review_references(root, proof):
    if (not isinstance(proof, dict) or any(not isinstance(proof.get(key), str) or not proof[key].strip()
            for key in ('id', 'analysis')) or not isinstance(proof.get('captures'), list) or not proof['captures']):
        raise ValueError('prevention_review_requires_analysis_and_execution')
    references = list(proof['captures'])
    for key in ('original_failure', 'bypass', 'normal'):
        observation = proof.get(key, {})
        if (not isinstance(observation, dict) or not isinstance(observation.get('analysis'), str)
                or not observation['analysis'].strip() or not isinstance(observation.get('references'), list)
                or not observation['references']):
            raise ValueError(f'prevention_observation_required:{key}')
        if key != 'original_failure' and not any(name in proof['captures'] for name in observation['references']):
            raise ValueError(f'prevention_execution_reference_required:{key}')
        references.extend(observation['references'])
    if not any(name not in proof['captures'] for name in proof['original_failure']['references']):
        raise ValueError('prevention_original_observation_required')
    if any(not isinstance(name, str) or not name or file_hash(root, name) is None for name in references):
        raise ValueError('prevention_reference_missing')
    return references


def structural_prevention_remaining(root, feature, entry, *, bundle_cache):
    """Bind Agent-reviewed behavior to existing captures; exit zero alone is not a verdict."""
    import unittest_evidence as reader
    from datetime import datetime
    proof = entry.get('prevention_review', {})
    references = prevention_review_references(root, proof)
    binding = entry.get('prevention_binding', {})
    hashes = binding.get('references', {})
    remaining = []
    if (binding.get('subject') != prevention_subject(entry) or not hashes
            or any(name not in hashes for name in references)
            or any(value is None or file_hash(root, name) != value for name, value in hashes.items())):
        remaining.append('prevention_review_stale_or_unbound')
    key = ('structural_source', str(root))
    if key not in bundle_cache:
        bundle_cache[key] = reader.git_identity(root)
    current = bundle_cache[key]
    for name in proof['captures']:
        capture = json.loads(local_path(root, name).read_text(encoding='utf-8'))
        if not isinstance(capture, dict) or not isinstance(capture.get('run_id'), str):
            raise ValueError('prevention_capture_invalid')
        uuid.UUID(capture['run_id'])
        datetime.fromisoformat(capture.get('started_at', ''))
        observed = capture.get('before')
        source_key = ('structural_bound_source', digest(observed))
        if source_key not in bundle_cache:
            same_source = observed == current and current is not None
            if not same_source and isinstance(observed, dict) and current:
                original_untracked = observed.get('untracked_sha256', {})
                if (isinstance(original_untracked, dict)
                        and re.fullmatch(r'[0-9a-f]{40,64}', observed.get('head', ''))
                        and not set(current['untracked_sha256']) - set(original_untracked)
                        and all(file_hash(root, path) == value for path, value in original_untracked.items())):
                    # Compare effective bytes against the captured base, even after a commit/stage.
                    changes = git(root, 'diff', observed['head'], '--binary', '--', '.',
                                  *(':(exclude,literal)' + path for path in original_untracked))
                    same_source = hashlib.sha256(changes).hexdigest() == observed.get('tracked_diff_sha256')
            bundle_cache[source_key] = same_source
        consumers = capture.get('shared_features', [capture.get('feature')])
        selected = (isinstance(consumers, list) and bool(consumers)
                    and all(isinstance(name, str) and name.strip() for name in consumers)
                    and len(consumers) == len(set(consumers))
                    and capture.get('feature') in consumers and feature['id'] in consumers)
        if (not selected
                or type(capture.get('capture_pid')) is not int or capture['capture_pid'] <= 0
                or not isinstance(capture.get('elapsed_seconds'), (int, float))
                or not math.isfinite(capture['elapsed_seconds']) or capture['elapsed_seconds'] < 0
                or any(not isinstance(capture.get(key), str) for key in ('stdout', 'stderr'))
                or capture.get('cwd') != str(root.resolve()) or not capture.get('run_id')
                or not isinstance(capture.get('argv'), list) or not capture['argv']
                or capture.get('execution') != 'exited' or type(capture.get('exit_code')) is not int
                or capture['exit_code'] != 0 or capture.get('cleanup_incomplete')
                or capture.get('behavior_verdict') is not None or not current
                or capture.get('before') != capture.get('after') or not bundle_cache[source_key]):
            remaining.append('prevention_execution_stale_or_unbound')
        report = capture.get('json_report')
        if report:
            report_path = Path(report['path']).resolve().relative_to(root.resolve()).as_posix()
            if report.get('error') or file_hash(root, report_path) != report.get('sha256'):
                remaining.append('prevention_native_report_stale')
    return remaining


def inspect_feedback(root, config, state, *, bundle_cache=None):
    if bundle_cache is None:
        bundle_cache = {}
    entries = state.get('feedback', {})
    if not isinstance(entries, dict):
        raise ValueError('feedback_must_be_object')
    features = {feature['id']: feature for feature in config['features']}
    result = []
    for identity, entry in entries.items():
        if not isinstance(entry, dict) or entry.get('id') != identity:
            raise ValueError('feedback_record_identity_mismatch')
        feature = features.get(entry.get('feature'))
        kind = entry.get('kind', 'requirement_violation')
        if kind in {'intentional_difference', 'requirement_change', 'oracle_tool_error', 'environment_limit', 'unknown'}:
            remaining = []
            if feature is None:
                remaining.append('feature_removed_needs_reconciliation')
            for field in ('scope', 'reason', 'evidence_refs', 'owner_refs', 'reconsider'):
                if not entry.get(field):
                    remaining.append(field)
            hashes = (entry.get('decision_hashes', {}) if kind == 'intentional_difference' else
                      entry.get('confirmation_hashes', entry.get('decision_hashes', {})))
            if any(file_hash(root, name) != value for name, value in hashes.items()):
                remaining.append('decision_evidence_stale')
            if entry.get('user_review', {}).get('decision') == 'defer':
                remaining.append('user_review_deferred')
            if kind == 'intentional_difference':
                binding = entry.get('decision_binding', {})
                if not binding.get('criteria_connections'):
                    remaining.append('decision_criteria_connections_required')
                elif feature is None or binding['criteria_connections'] != difference_criteria_connections(config, feature):
                    remaining.append('decision_criteria_connections_changed')
                if (feature is None or not difference_review_matches(entry, config, feature) or
                        binding.get('subject') != difference_subject(entry) or
                        binding.get('review') != entry.get('user_review')):
                    remaining.append('user_difference_review_required')
                criteria = binding.get('criteria', {})
                if not criteria:
                    remaining.append('decision_criteria_binding_required')
                elif feature is None or any(name not in difference_criteria(config, feature) or value is None or
                        file_hash(root, name) != value for name, value in criteria.items()):
                    remaining.append('decision_criteria_stale')
            if kind in {'environment_limit', 'unknown'}:
                remaining.extend(environment_recovery_remaining(root, feature, entry, bundle_cache=bundle_cache)
                                 if kind == 'environment_limit' and feature is not None else ['cause_unconfirmed'])
            if kind in {'requirement_change', 'oracle_tool_error'} and feature is not None:
                if kind == 'requirement_change' and not entry.get('authorization_refs'):
                    remaining.append('requirement_change_authorization_required')
                changed = [name for name in feature['criteria'] if file_hash(root, name) != entry.get('criteria_before', {}).get(name)]
                if kind == 'requirement_change' and not changed:
                    remaining.append('criterion_revision_not_observed')
                if kind == 'oracle_tool_error':
                    for field in ('trace', 'root_cause', 'repair_paths'):
                        if not entry.get(field):
                            remaining.append(field)
                    before = dict(entry.get('source_before', {}), **entry.get('criteria_before', {}))
                    missing = [name for name in entry.get('repair_paths', []) if name not in before]
                    if missing and entry.get('red_bundle'):
                        try:
                            before.update(oracle_repair_preimages(root, feature, entry, missing, bundle_cache=bundle_cache))
                        except (OSError, ValueError, KeyError, TypeError):
                            pass
                    if not entry.get('repair_paths') or any(not isinstance(before.get(name), str)
                            or not re.fullmatch(r'[0-9a-f]{64}', before[name]) or file_hash(root, name) == before[name]
                            for name in entry.get('repair_paths', [])):
                        remaining.append('oracle_or_tool_repair_not_observed')
                proof = entry.get('confirmation', {})
                if proof.get('check') not in feature['checks'] or not proof.get('expected_pointer') or not proof.get('normal_pointer') or not entry.get('green_bundle'):
                    remaining.append('new_and_retained_contract_evidence_required')
                else:
                    try:
                        remaining.extend(feedback_confirmation(root, feature, entry, bundle_cache=bundle_cache))
                    except (OSError, ValueError, TypeError, KeyError):
                        remaining.append('confirmation_evidence_unavailable')
            result.append(dict(entry, status='OPEN' if remaining else 'ACCEPTED' if kind == 'intentional_difference' else 'RESOLVED',
                               remaining=sorted(set(remaining))))
            if kind == 'environment_limit':
                result[-1]['environment_status'] = 'BLOCKED' if remaining else 'AVAILABLE'
                result[-1]['next_action'] = ('Inspect original failure, project target/configuration and attempted recovery; explicitly recheck the same target.'
                    if remaining else 'Reuse only while target/configuration and current recheck remain valid; retain the original failure and recovery raw.')
            continue
        guardrail = entry.get('guardrail', {})
        if not isinstance(guardrail, dict):
            raise ValueError('feedback_guardrail_must_be_object')
        structural = guardrail.get('mechanism') in {'structure', 'type_constraint'}
        evidence_fields = ('prevention_review',) if structural else ('red_bundle', 'green_bundle')
        remaining = [key for key in ('trace', 'root_cause', 'failed_prevention', 'repair_paths', 'guardrail') + evidence_fields
                     if not entry.get(key)]
        if feature is None:
            remaining.append('feature_removed_needs_reconciliation')
        else:
            paths = entry.get('repair_paths', [])
            refs = {name for field in ('map', 'criteria', 'ui') for name in feature.get(field, [])}
            if not isinstance(paths, list) or not paths or any(name in refs or not any(fnmatchcase(name, p) for p in source_patterns(config, feature))
                    or file_hash(root, name) == entry.get('source_before', {}).get(name) for name in paths):
                remaining.append('owner_repair_not_observed')
            guardrail = entry.get('guardrail', {})
            if not isinstance(guardrail, dict):
                raise ValueError('feedback_guardrail_must_be_object')
            required = (('failure', 'scope', 'owner_refs', 'normal_exception', 'reconsider') if structural else
                        ('failure', 'scope', 'check', 'normal_exception', 'reconsider', 'regression_pointer', 'normal_pointer'))
            remaining.extend(f'guardrail.{key}' for key in required if not guardrail.get(key))
            link_keys = ('failure', 'normal_exception', 'scope', 'reconsider') + (('mechanism', 'owner_refs') if structural else ('check',))
            if guardrail and ((not structural and guardrail.get('check') not in feature['checks']) or not any(
                    all(p.get(key) == guardrail.get(key) for key in link_keys) for p in feature.get('prevention', []))):
                remaining.append('active_prevention_link_missing')
            if structural:
                proof = entry.get('prevention_review', {})
                observation = proof.get('original_failure', {}) if isinstance(proof, dict) else {}
                original = observation.get('references', []) if isinstance(observation, dict) else []
                if not isinstance(original, list) or not any(isinstance(name, str) and name not in refs and not any(fnmatchcase(name, p) for p in source_patterns(config, feature))
                           for name in original):
                    remaining.append('original_failure_observation_required')
                owners = guardrail.get('owner_refs', [])
                if not isinstance(owners, list) or not owners or any(not isinstance(name, str)
                        or not any(fnmatchcase(name, pattern) for pattern in source_patterns(config, feature))
                        or file_hash(root, name) is None for name in owners):
                    remaining.append('active_prevention_owner_missing')
                try:
                    remaining.extend(structural_prevention_remaining(root, feature, entry, bundle_cache=bundle_cache))
                except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
                    remaining.append('prevention_review_or_execution_unavailable')
            elif entry.get('red_bundle') and entry.get('green_bundle') and all(guardrail.get(key) for key in required):
                try:
                    remaining.extend(feedback_evidence(root, feature, entry, bundle_cache=bundle_cache))
                except (OSError, ValueError, TypeError, KeyError):
                    remaining.append('repair_evidence_unavailable')
        result.append(dict(entry, status='OPEN' if remaining else 'RESOLVED', remaining=sorted(set(remaining)),
            resolution_basis='Agent-reviewed structural prevention with current execution' if structural else 'fixed-oracle regression and normal evidence'))
    statuses = {item['id']: item['status'] for item in result}
    for item in result:
        entry = entries[item['id']]
        proof = entry.get('supersession')
        if proof is None:
            continue
        remaining = []
        try:
            successor, hashes = feedback_successor(root, config, state, item['id'], proof)
            if (proof.get('source_basis') != feedback_basis(entry)
                    or proof.get('target_basis') != feedback_basis(successor)
                    or proof.get('reference_hashes') != hashes):
                remaining.append('feedback_supersession_review_stale')
            if statuses[successor['id']] not in {'RESOLVED', 'ACCEPTED'}:
                remaining.append('feedback_successor_unresolved')
        except (OSError, ValueError, KeyError, TypeError) as error:
            remaining.append(str(error))
        item['original_remaining'] = item['remaining']
        successor_id = proof.get('feedback') if isinstance(proof, dict) else None
        item['successor_status'] = statuses.get(successor_id) if isinstance(successor_id, str) else None
        item['remaining'] = remaining
        item['status'] = 'OPEN' if remaining else 'SUPERSEDED'
    return result


def oracle_repair_preimages(root, feature, entry, paths, *, bundle_cache=None):
    """Use a bound failing capture for new tool owners; never rewrite task baseline."""
    import verification_results as viewer
    red = bundle_observation(viewer, local_path(root, entry['red_bundle']), include_scope=False, bundle_cache=bundle_cache)
    check = entry.get('confirmation', {}).get('check')
    items = [item for item in red.get('items', []) if item['feature'] == feature['id'] and item['id'] == check]
    if len(items) != 1:
        return {}
    item = items[0]
    allowed = ('raw_assertion_mismatch:', 'condition_mismatch:current.', 'condition_missing:current.')
    if (not item.get('selected') or item['historical_status'] != 'ISSUES'
            or any(reason not in {'capture_native_failure', 'capture_exit_nonzero', 'current_context_missing'}
                   and not reason.startswith(allowed) for reason in item['reasons'])):
        return {}
    pointer = entry.get('confirmation', {}).get('expected_pointer')
    if not any(obs['assertion']['pointer'] == pointer and not obs['matched']
               for raw in item.get('raw', []) for obs in raw.get('observations', [])):
        return {}
    plan_path = Path(red['bundle']['plan']).resolve()
    plan, _ = viewer.read_json(local_path(root, plan_path.relative_to(root).as_posix()))
    scope = plan.get('workflow_scope', {})
    old_feature = next((f for f in scope.get('features', []) if f['id'] == feature['id']), {})
    if scope.get('root') != str(root.resolve()):
        return {}
    record_path = Path(item['capture']['path']).resolve()
    record, raw = viewer.read_json(local_path(root, record_path.relative_to(root).as_posix()))
    if (hashlib.sha256(raw).hexdigest() != item['capture']['sha256']
            or Path(record['cwd']).resolve() != root.resolve()
            or record.get('before') != record.get('after')):
        return {}
    dependency = item['conditions']['expected']['dependency']
    measured = record.get('conditions', {}).get('dependency', {})
    captured = record.get('before', {}).get('untracked_sha256', {})
    before = record.get('before', {})
    head = before.get('head')
    source = item['conditions']['expected'].get('source', {})
    # shortcut: Dirty captures/custom filters stay OPEN; require retained bytes before supporting them.
    clean_tracked = (isinstance(head, str) and re.fullmatch(r'[0-9a-f]{40,64}', head)
        and before.get('status') == ''
        and before.get('tracked_diff_sha256') == hashlib.sha256(b'').hexdigest()
        and source.get('revision') == head and source.get('status') == ''
        and source.get('diff') == before['tracked_diff_sha256'])
    result = {}
    for name in paths:
        if (not any(fnmatchcase(name, pattern) for pattern in feature['sources'])
                or not any(fnmatchcase(name, pattern) for pattern in old_feature.get('sources', []))
                or name not in dependency.get('file_refs', [])):
            continue
        sha = dependency.get('file_hashes', {}).get(str(local_path(root, name)))
        if (not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha)
                or measured.get('file_hashes', {}).get(str(local_path(root, name))) != sha):
            continue
        if captured.get(name) == sha:
            result[name] = sha
        elif clean_tracked and name not in captured:
            try:
                blob = git(root, 'show', f'{head}:{name}')
            except (OSError, subprocess.CalledProcessError):
                continue
            # Git may store LF while a clean Windows checkout supplies CRLF.
            variants = (blob, blob.replace(b'\n', b'\r\n')) if b'\r\n' not in blob else (blob,)
            if any(hashlib.sha256(value).hexdigest() == sha for value in variants):
                result[name] = sha
    return result


def feedback_confirmation(root, feature, entry, *, bundle_cache=None):
    """A changed requirement needs fresh native evidence, not an old RED oracle."""
    import verification_results as viewer
    path = local_path(root, entry['green_bundle'])
    green = bundle_observation(viewer, path, bundle_cache=bundle_cache)
    proof = entry['confirmation']
    item = next((i for i in green.get('items', []) if i['feature'] == feature['id'] and i['id'] == proof['check']), None)
    remaining = []
    if not item or item['current_status'] != 'PASS':
        remaining.append('changed_requirement_revalidation_required')
    observations = [obs for raw in (item or {}).get('raw', []) for obs in raw.get('observations', [])]
    pointers = (proof['expected_pointer'], proof['normal_pointer'])
    if pointers[0] == pointers[1] or any(not any(obs['assertion']['pointer'] == pointer and obs['matched']
            for obs in observations) for pointer in pointers):
        remaining.append('new_and_retained_contract_evidence_required')
    bound = viewer.read_json(viewer.resolve_bundle_file(green['bundle']['plan'], base=path.parent, label='feedback plan'))[0]
    scope = bound.get('workflow_scope', {})
    if scope.get('root') != str(root.resolve()) or feature not in scope.get('features', []):
        remaining.append('prepared_project_binding_required')
    return remaining


def inspect_evidence(root, feature, commands, bundle, *, bundle_cache=None):
    """Reinspect raw execution; submitted review/status strings cannot discharge checks."""
    try:
        path = local_path(root, bundle)
        binding = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(binding, dict) and binding.get('format') == 'unittest-captures-v1':
            return inspect_unittest_evidence(root, feature, commands, binding)
        import verification_results as viewer
        observed = bundle_observation(viewer, path, include_scope=False, bundle_cache=bundle_cache)
        verified = set()
        for item in observed['items']:
            if item['feature'] != feature['id']:
                continue
            descriptor = commands.get(item['id'])
            if descriptor is None:
                item['current_status'] = 'BLOCKED'
                item['reasons'].append('active_command_missing')
                continue
            expected = resolve_report_command(root,
                descriptor.get('argv') if isinstance(descriptor, dict) else descriptor,
                item['conditions']['expected']['command'].get('report_dir'))
            cwd = root / (descriptor.get('working_directory', '.') if isinstance(descriptor, dict) else '.')
            if not item.get('selected'):
                continue
            if not item['capture'].get('argv') or not item['capture'].get('cwd'):
                continue
            if item['capture']['argv'] != expected or Path(item['capture']['cwd']).resolve() != cwd.resolve():
                item['current_status'] = 'BLOCKED'
                item['reasons'].append('registered_command_or_target_changed')
            elif item['current_status'] == 'PASS':
                verified.add(item['id'])
        missing = set(feature['checks']) - verified
        if missing or not verified:
            return {'status': 'BLOCKED', 'findings': [f'verification_missing:{feature["id"]}:{name}' for name in sorted(missing or {'unconnected'})],
                    'items': observed['items']}
        return {'status': 'PASS', 'findings': [], 'items': observed['items']}
    except (OSError, ValueError, TypeError, KeyError) as error:
        return {'status': 'BLOCKED', 'findings': [f'verification_unavailable:{error}']}


def inspect_unittest_evidence(root, feature, commands, binding):
    """Use the existing native adapter without loading or executing project code."""
    import unittest_evidence as reader
    if binding.get('feature') != feature['id']:
        raise ValueError('verification_feature_mismatch')
    records = binding.get('records')
    if not isinstance(records, list) or not records:
        raise ValueError('verification_records_required')
    verified = set()
    findings = []
    items = []
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
        path = local_path(root, record['path'])
        captured = json.loads(path.read_text(encoding='utf-8'))
        try:
            observed = reader.assess(path, record['run_id'], feature['id'], check, [sys.executable, *argv[1:]], cwd.resolve())
        except (OSError, ValueError) as error:
            observed = {'status': 'BLOCKED', 'reason': str(error)}
        items.append({'id': check, 'feature': feature['id'], 'historical_status': observed['status'],
            'current_status': observed['status'], 'current_reuse': 'REUSABLE' if observed['status'] == 'PASS' else 'UNKNOWN',
            'selected': True, 'selection': {'status': 'selected', 'reason': 'Feature native unittest binding'},
            'run_id': record['run_id'], 'raw': [], 'reasons': [] if observed['status'] == 'PASS' else [observed.get('reason', 'native_assertions_unavailable_or_failed')],
            'capture': {'path': str(path.resolve()), 'argv': captured.get('argv'), 'cwd': captured.get('cwd'),
                        'execution': captured.get('execution'), 'exit_code': captured.get('exit_code')}})
        if observed['status'] == 'PASS':
            verified.add(check)
        else:
            findings.append(f'verification_failed:{feature["id"]}:{check}')
    findings.extend(f'verification_missing:{feature["id"]}:{check}'
                    for check in sorted(set(feature['checks']) - verified))
    return {'status': 'BLOCKED' if findings else 'PASS', 'findings': findings,
            'items': items,
            'test_commands_executed': 0, 'scope': 'native unittest assertions; local consistency only'}


def inspect_configured(root, project, *, file_inventory=None, observe_local_changes=False):
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
    return inspect_project(root, project, state, file_inventory=file_inventory, observe_local_changes=observe_local_changes)


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
    cell_keys = {p + ':' + a for p in ('business', 'architecture') for a in ('FE', 'BE/API', 'Domain')}
    for key, entry in scopes.items():
        allowed = {'REQUIRED', 'NOT_REQUIRED'} if key in cell_keys else {'PASS', 'ISSUES', 'BLOCKED', 'NOT_REQUIRED'}
        if not isinstance(entry, dict) or entry.get('status') not in allowed:
            raise ValueError('invalid_scope_review_status')
        if key in cell_keys and entry['status'] == 'REQUIRED' and (not isinstance(entry.get('coverage'), list)
                or not entry['coverage'] or any(not isinstance(name, str) or not name for name in entry['coverage'])
                or len(entry['coverage']) != len(set(entry['coverage']))):
            raise ValueError('scope_decision_requires_coverage_links')
        if not isinstance(entry.get('analysis'), str) or not entry['analysis'].strip():
            raise ValueError('scope_review_analysis_required')
        if entry['status'] == 'NOT_REQUIRED' and not entry.get('reason'):
            raise ValueError('scope_exclusion_reason_required')
        if not isinstance(entry.get('references'), list) or not entry['references']:
            raise ValueError('scope_review_references_required')
        for name in entry['references']:
            if file_hash(root, name) is None:
                raise ValueError(f'scope_review_reference_missing:{name}')
        if 'architecture' in entry:
            validate_architecture(root, entry['architecture'])
    decisions = review.get('check_decisions', {})
    if not isinstance(decisions, dict):
        raise ValueError('check_decisions_must_be_object')
    for entry in decisions.values():
        if not isinstance(entry, dict) or entry.get('action') not in {'retain', 'remove', 'consolidate', 'rebind'} or not entry.get('reason'):
            raise ValueError('check_decision_requires_action_reason')
        if not isinstance(entry.get('preservation', []), list) or any(not isinstance(p, dict) for p in entry.get('preservation', [])):
            raise ValueError('check_preservation_must_be_list')
        if entry.get('action') == 'rebind' or 'consolidation' in entry:
            consolidating = 'consolidation' in entry
            proof = entry.get('consolidation' if consolidating else 'rebind')
            if (entry.get('action') != ('consolidate' if consolidating else 'rebind')
                    or entry.get('reason') != ('duplicate_execution' if consolidating else 'check_identity_migrated')
                    or (consolidating and 'rebind' in entry) or not isinstance(proof, dict)
                    or set(proof) != {'target_check', 'source_plan', 'target_bundle'}
                    or any(not isinstance(proof.get(field), str) or not proof[field].strip()
                           for field in ('target_check', 'source_plan', 'target_bundle'))
                    or entry.get('preservation', []) or 'retirement' in entry):
                raise ValueError('check_rebind_requires_identity_and_execution_proof')
            for field in ('source_plan', 'target_bundle'):
                try:
                    path = local_path(root, proof[field])
                except (OSError, ValueError):
                    raise ValueError('check_rebind_proof_path_invalid') from None
                if not path.resolve().is_relative_to((root / '.work').resolve()) or not path.is_file():
                    raise ValueError('check_rebind_proof_path_invalid')
        if 'retirement' in entry:
            proof = entry['retirement']
            if not isinstance(proof, dict):
                raise ValueError('check_retirement_must_be_object')
            for field in ('authorization_refs', 'requirement_refs', 'references'):
                if field in proof and (not isinstance(proof[field], list) or any(
                        not isinstance(name, str) or not name or file_hash(root, name) is None for name in proof[field])):
                    raise ValueError('check_retirement_reference_missing')
            for field in ('entrypoints', 'callers'):
                if field in proof and (not isinstance(proof[field], list) or any(not isinstance(item, dict) or
                        not isinstance(item.get('references', []), list) or any(not isinstance(name, str) or
                            file_hash(root, name) is None for name in item.get('references', [])) for item in proof[field])):
                    raise ValueError('check_retirement_disposition_reference_invalid')


def architecture_references(architecture):
    return list(dict.fromkeys(name for group in ('flows', 'boundaries', 'findings')
        for entry in architecture.get(group, []) for name in entry.get('references', []) +
        ([entry['owner']] if 'owner' in entry else [])))


def finding_basis(review):
    return digest({'product': review.get('product_findings', []),
                   'architecture': architecture_findings(review)})


def architecture_findings(review):
    current = [dict(finding, scope_review=key) for key, entry in review.get('scope_reviews', {}).items()
               for finding in entry.get('architecture', {}).get('findings', [])]
    identities = {finding['id'] for finding in current}
    return current + [finding for finding in review.get('inherited_architecture_findings', [])
                      if finding['id'] not in identities]


def validate_architecture(root, architecture):
    if (not isinstance(architecture, dict) or not isinstance(architecture.get('flows'), list) or not architecture['flows']
            or not isinstance(architecture.get('boundaries'), list) or not isinstance(architecture.get('findings'), list)):
        raise ValueError('architecture_evidence_requires_flows_boundaries_findings')
    for flow in architecture['flows']:
        if not isinstance(flow, dict) or any(not isinstance(flow.get(k), str) or not flow[k].strip()
                                              for k in ('owner', 'call', 'state', 'data')):
            raise ValueError('architecture_flow_requires_owner_call_state_data')
    kinds = {boundary.get('kind') for boundary in architecture['boundaries'] if isinstance(boundary, dict)}
    if kinds != {'contract', 'dependency', 'failure'}:
        raise ValueError('architecture_evidence_requires_contract_dependency_failure_boundaries')
    for boundary in architecture['boundaries']:
        if not isinstance(boundary, dict) or not isinstance(boundary.get('analysis'), str) or not boundary['analysis'].strip():
            raise ValueError('architecture_boundary_analysis_required')
    for finding in architecture['findings']:
        if (not isinstance(finding, dict) or any(not isinstance(finding.get(k), str) or not finding[k].strip()
                for k in ('id', 'problem', 'owner')) or finding.get('status') not in {'open', 'fixed', 'excluded'}):
            raise ValueError('architecture_finding_requires_problem_owner_disposition')
        if finding['status'] == 'excluded' and not finding.get('reason'):
            raise ValueError('architecture_finding_exclusion_reason_required')
        if finding['status'] == 'fixed':
            repair = finding.get('repair', {})
            if (repair.get('path') != finding['owner'] or not repair.get('before_sha256')
                    or repair.get('before_sha256') == repair.get('after_sha256')
                    or file_hash(root, finding['owner']) != repair.get('after_sha256')):
                raise ValueError('architecture_finding_owner_repair_evidence_required')
    for group in ('flows', 'boundaries', 'findings'):
        for entry in architecture[group]:
            if not isinstance(entry.get('references'), list) or not entry['references']:
                raise ValueError('architecture_evidence_references_required')
    for name in architecture_references(architecture):
        if not isinstance(name, str) or file_hash(root, name) is None:
            raise ValueError('architecture_evidence_reference_missing')


def review_scope_states(root, review):
    result = {}
    for key, entry in review.get('scope_reviews', {}).items():
        try:
            if any(file_hash(root, name) != value for name, value in entry.get('reference_hashes', {}).items()):
                result[key] = 'STALE'
                continue
            validate_review(root, dict(review, scope_reviews={key: entry}))
            result[key] = 'CURRENT'
        except (OSError, ValueError, TypeError, AttributeError):
            result[key] = 'BLOCKED'
    return result


def current_review(root, review, basis):
    if not isinstance(review, dict) or review.get('basis') != basis:
        return False
    try:
        validate_review(root, dict(review, scope_reviews={}))
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
    key = 'retired_reviews' if feature in result['retired'] else 'reviews'
    other_key = 'reviews' if key == 'retired_reviews' else 'retired_reviews'
    prior = state.get(key, {}).get(review['feature'], state.get(other_key, {}).get(review['feature'], {}))
    prior_records = [prior]
    if key == 'retired_reviews' and prior.get('active_findings_basis') != finding_basis(state.get('reviews', {}).get(review['feature'], {})):
        prior_records.append(state.get('reviews', {}).get(review['feature'], {}))
    if ('inherited_architecture_findings' in review and
            review['inherited_architecture_findings'] != prior.get('inherited_architecture_findings', [])):
        raise ValueError('inherited_architecture_findings_are_read_only; resolve through a current scope review')
    unresolved = {f['id'] for entry in prior_records for f in architecture_findings(entry) if f['status'] == 'open'}
    remaining = {f['id'] for f in architecture_findings(review)}
    if unresolved - remaining:
        raise ValueError(f'unresolved_architecture_finding_disposition_required:{sorted(unresolved - remaining)}')
    for entry in review.get('scope_reviews', {}).values():
        for finding in entry.get('architecture', {}).get('findings', []):
            if finding['status'] == 'fixed' and state['baseline'].get(finding['owner']) != finding['repair']['before_sha256']:
                raise ValueError('architecture_owner_repair_baseline_mismatch')
    declared = next((f for f in configuration(project)['features'] if f['id'] == review['feature']), {})
    for row in declared.get('coverage', []):
        entry = review.get('scope_reviews', {}).get(row['id'], {})
        if row['kind'] == 'review' and 'architecture' in row['perspectives'] and entry.get('status') in {'PASS', 'ISSUES', 'BLOCKED'}:
            if not entry.get('architecture'):
                raise ValueError('architecture_evidence_required')
    updated = deepcopy(state)
    if key == 'reviews':
        updated.get('retired_reviews', {}).pop(review['feature'], None)
    updated.setdefault(key, {})[review['feature']] = deepcopy(review)
    if key == 'retired_reviews':
        updated[key][review['feature']]['active_findings_basis'] = finding_basis(state.get('reviews', {}).get(review['feature'], {}))
    if 'product_findings' not in review:
        updated[key][review['feature']]['product_findings'] = list(dict.fromkeys(
            finding for entry in prior_records for finding in entry.get('product_findings', [])))
    updated[key][review['feature']]['reference_hashes'] = {
        name: file_hash(root, name) for name in dict.fromkeys(review['references'] + [name
            for decision in review.get('check_decisions', {}).values()
            for name in check_decision_references(decision)])}
    for entry in updated[key][review['feature']].get('scope_reviews', {}).values():
        entry['reference_hashes'] = {name: file_hash(root, name) for name in dict.fromkeys(
            entry['references'] + architecture_references(entry.get('architecture', {})))}
    return updated


def summarize_lookup(result, project, root):
    """Present already inspected facts; discovery never audits other task bundles."""
    summary = {key: deepcopy(result[key]) for key in ('handoff', 'status', 'mapping_status', 'read_only',
        'test_commands_executed', 'findings', 'product_findings', 'feedback', 'investigation',
        'task_context', 'action_scope_counts', 'unmapped_changes') if key in result}
    task = result.get('task', {})
    summary['task'] = {key: task.get(key) for key in ('state', 'work_id', 'task_id', 'intent', 'targets', 'request', 'base')}
    summary['detail_command'] = {'action': 'lookup', 'root': str(root),
        'state': task.get('state'), 'work_id': task.get('work_id'), 'summary': False}
    summary['feedback'] = [{key: deepcopy(entry[key]) for key in
        ('id', 'feature', 'kind', 'status', 'expected', 'root_cause', 'remaining',
         'owner_refs', 'repair_paths', 'evidence_refs', 'red_bundle', 'green_bundle',
         'supersession', 'successor_status') if key in entry} | {'detail_omitted': True}
        for entry in result.get('feedback', [])]
    import verification_results as viewer
    summary['coverage'] = deepcopy(result['coverage'])
    config = {f['id']: f for f in (configuration(project) or {}).get('features', [])}
    active = {c['feature'] for c in result.get('coverage', {}).get('matrix', []) if c.get('in_task', True)}
    summary['features'] = []
    for feature in result.get('features', []):
        row = {key: deepcopy(feature[key]) for key in ('id', 'partition', 'verification_status', 'checks', 'excluded_checks', 'reviewed')}
        row['work_scope'] = feature.get('work_scope', 'scope_undetermined')
        row.update({key: config[feature['id']][key] for key in ('sources', 'map', 'criteria')})
        row['in_task'] = feature['id'] in active
        row['bundles'] = task.get('results', {}).get(feature['id'], [])
        row['structural_evidence'] = feature.get('structural_evidence', [])
        row['evidence_status'] = ('AVAILABLE' if feature['check_results'] or row['structural_evidence'] else
            'UNAVAILABLE' if row['bundles'] else 'NOT_RUN' if feature['verification_status'] == 'REQUIRED' else 'NOT_REQUIRED')
        row['check_results'] = viewer.summarize_results({'items': feature['check_results']})['items']
        for item in row['check_results']:
            for key in ('historical_source', 'historical_statuses', 'assessment', 'observation', 'criteria_revision'):
                item.pop(key, None)
            for key in ('argv', 'cwd'):
                item.get('capture', {}).pop(key, None)
            for raw in item.get('raw', []):
                raw.pop('producer', None)
        summary['features'].append(row)
    evidence_ids = {f['id'] + '/' + item['id'] for f in summary['features'] for item in f['check_results']}

    def evidence_preview(item):
        identity = str(item.get('feature')) + '/' + str(item.get('id'))
        if identity not in evidence_ids:
            return viewer.summarize_results({'items': [item]})['items'][0]
        return dict({key: deepcopy(item[key]) for key in ('feature', 'id', 'historical_status',
            'current_status', 'current_reuse', 'selected') if key in item}, evidence_ref=identity)

    for row in summary['coverage'].get('rows', []):
        if row.get('evidence') and row.get('kind') == 'test':
            row['evidence'] = evidence_preview(dict(row['evidence'], feature=row['feature'], id=row['check']))
        elif row.get('evidence'):
            row.pop('evidence')
            row['evidence_omitted'] = True

    if 'verification' in result:
        summary['verification'] = {key: deepcopy(value) for key, value in result['verification'].items()
                                   if key not in {'items', 'coverage', 'bundle'}}
        if 'bundle' in result['verification']:
            summary['verification']['bundle_omitted'] = True
        summary['verification']['items'] = [evidence_preview(item) for item in result['verification'].get('items', [])]
        if 'coverage' in result['verification']:
            summary['verification']['coverage_ref'] = 'coverage'
            summary['verification']['coverage'] = {key: deepcopy(value) for key, value in result['verification']['coverage'].items()
                                                   if key not in {'rows', 'matrix', 'gaps'}}
            for key in ('rows', 'matrix', 'gaps'):
                values = result['verification']['coverage'].get(key, [])
                summary['verification']['coverage'][key + '_count'] = len(values)
                summary['verification']['coverage'][key + '_ids'] = [
                    {k: v[k] for k in ('feature', 'id', 'perspective', 'area', 'status') if k in v} for v in values]
    priority = {'request_required': 0, 'impact_required': 1, 'scope_undetermined': 2, 'project_remaining': 3}
    summary['next_actions'] = sorted(deepcopy(result['next_actions']), key=lambda a: priority.get(a.get('scope'), 2))
    preview_remaining = 6
    for action in summary['next_actions']:
        pending = action.get('pending', [])
        action['pending_count'] = len(pending)
        action['pending_ids'] = [{'id': p['id'], 'kind': p['kind'], 'status': p['status']} for p in pending]
        action['pending'] = pending[:min(2, preview_remaining)] if action.get('scope') != 'project_remaining' else []
        preview_remaining -= len(action['pending'])
        action['pending_omitted'] = len(pending) - len(action['pending'])
        action.pop('scope_basis', None)
        for key in ('basis', 'changed', 'verification_changed', 'verification_inputs_changed', 'ui_systems', 'prevention'):
            action.pop(key, None)
        if action.get('scope') == 'project_remaining':
            for key in ('guides', 'bundles', 'references', 'next_action'):
                action.pop(key, None)
        for entry in action['pending']:
            if entry.get('evidence') and entry['kind'] == 'execution_check':
                preview = evidence_preview(entry.pop('evidence'))
                entry.update({'evidence_ref': preview['evidence_ref']} if 'evidence_ref' in preview else {'evidence': preview})
            elif entry.get('evidence'):
                entry.pop('evidence')
                entry['evidence_omitted'] = True
            if entry.get('raw_contract'):
                entry['raw_contract'] = [{key: raw[key] for key in ('path', 'pointer') if key in raw} |
                    {'assertion_count': len(raw.get('assertions', []))} for raw in entry['raw_contract']]
    for coverage in (summary.get('coverage', {}), summary.get('verification', {}).get('coverage', {})):
        for key in ('rows', 'matrix', 'gaps'):
            if key in coverage:
                coverage[key + '_ids'] = [{name: value[name] for name in
                    ('feature', 'id', 'perspective', 'area', 'status') if name in value}
                    if isinstance(value, dict) else value for value in coverage[key]]
        for key, limit in (('rows', 8), ('matrix', 12)):
            if key not in coverage:
                continue
            values = coverage[key]
            coverage['row_count' if key == 'rows' else 'cell_count'] = len(values)
            coverage[key + '_omitted'] = max(0, len(values) - limit)
            if len(values) > limit:
                coverage[key] = sorted(values, key=lambda v: v.get('work_scope') == 'project_remaining'
                    or not v.get('in_task', True))[:limit]
    summary['detail_hint'] = 'Evidence refs name features/check_results by feature/check; coverage IDs retain denominators. Raw values, semantic review bodies, feedback bindings and bundle descriptors are omitted after validation. Follow bundles/raw path/pointer or repeat exact lookup without --summary. Check PASS is not task acceptance.'
    # Large projects need a decision view, not repeated previews of the same facts.
    if len(json.dumps(summary)) > 32000:
        summary['detail_omitted'] = True
        for coverage in (summary['coverage'], summary.get('verification', {}).get('coverage', {})):
            for key in ('rows', 'matrix'):
                if key in coverage:
                    coverage[key + '_omitted'] = coverage.get(key + '_omitted', 0) + len(coverage[key])
                    coverage[key] = []
        for action in summary['next_actions']:
            action['pending_omitted'] = action['pending_count']
            action['pending'] = []
            if action.get('scope') == 'project_remaining':
                for key in ('references', 'reason', 'requires', 'current_validity'):
                    action.pop(key, None)
        for feature in summary['features']:
            feature.pop('sources', None)
            feature['detail_omitted'] = True
            for item in feature['check_results']:
                item.pop('selection', None)
                item.get('capture', {}).pop('sha256', None)
                for raw in item.get('raw', []):
                    for key in ('sha256', 'origin'):
                        raw.pop(key, None)
    leading = ('handoff', 'task', 'status', 'action_scope_counts', 'next_actions', 'detail_command')
    return {key: summary[key] for key in leading if key in summary} | {key: value for key, value in summary.items() if key not in leading}


def main(argv=None):
    from task_store import TaskStore
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['begin', 'start', 'connect', 'resume', 'prepare', 'execute', 'lookup',
                                          'audit', 'maintain', 'review', 'feedback', 'investigate', 'accept'])
    parser.add_argument('--root', type=Path, help='Project root; connected calls may omit it')
    parser.add_argument('--project', default='.harness/project.yaml')
    state_selection = parser.add_mutually_exclusive_group()
    state_selection.add_argument('--state', help='Task-owned record under .work, relative to --root or absolute within it; audit without it is read-only')
    state_selection.add_argument('--work-id', help='Use the workflow baseline captured by Harness start')
    parser.add_argument('--context', help='Explicit context returned by start/connect; otherwise AGENT_WORKFLOW_CONTEXT')
    parser.add_argument('--output', help='New .work directory for prepare; default is a unique task run')
    parser.add_argument('--run-check', type=Path, help='Optional capture override; plugin and standalone Skill discover their bundled tool')
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--resume', action='store_true', help='Execute only never-started checks of this prepared run')
    parser.add_argument('--summary', action='store_true', help='Read-only lookup/resume/audit summary with criteria, current reuse and raw pointers')
    parser.add_argument('--intent', choices=['init', 'change', 'feedback', 'ui', 'maintain', 'diagnose'], default='init')
    parser.add_argument('--request-summary', help='Ordinary task request; Harness work keeps its existing contract reference')
    parser.add_argument('--outcome-ref', action='append', default=[], help='Existing project-relative expected-outcome document')
    parser.add_argument('--target', action='append', default=[])
    parser.add_argument('--review', type=Path)
    parser.add_argument('--investigation', type=Path, help='Agent observations and remaining scope in the existing task')
    parser.add_argument('--feedback', type=Path, help='Register/update a complaint and repair chain in the existing work state')
    parser.add_argument('--history-bundle', action='append', default=[], help='Project-relative retained bundle for read-only maintenance costs/detection review')
    args = parser.parse_args(argv)
    root, project = None, None
    try:
        context = args.context if args.context is not None else os.environ.get('AGENT_WORKFLOW_CONTEXT')
        root = (args.root.resolve() if args.root else Path(json.loads(context)['root']).resolve() if context else
                Path(git(Path.cwd(), 'rev-parse', '--show-toplevel').decode().strip()).resolve())
        project_path = local_path(root, args.project)
        project = json.loads(project_path.read_text(encoding='utf-8')) if project_path.is_file() else {}
        if not project_path.is_file() and args.project != '.harness/project.yaml':
            raise ValueError('explicit_project_file_missing')
        if args.resume and args.action != 'execute' or args.output and args.action != 'prepare':
            raise ValueError('execution_options_require_matching_action')
        if args.summary and args.action not in {'lookup', 'resume', 'audit'}:
            raise ValueError('summary_requires_read_only_lookup')
        if (args.request_summary is not None or args.outcome_ref) and args.action not in {'begin', 'start'}:
            raise ValueError('request_metadata_requires_task_start')
        if args.investigation and args.action not in {'start', 'begin', 'investigate'}:
            raise ValueError('investigation_requires_start_begin_or_investigate')
        if args.state and Path(args.state).is_absolute():
            try:
                # Keep lexical components so local_path still rejects aliases and escapes.
                args.state = Path(args.state).relative_to(root).as_posix()
            except ValueError:
                raise ValueError(f'path_outside_project:{args.state}') from None
        state_path = local_path(root, args.state) if args.state else None
        if state_path and not state_path.resolve().is_relative_to(root / '.work'):
            raise ValueError('state_must_be_task_local_under_work')
        state = TaskStore(state_path).load() if state_path and state_path.exists() else None
        if state_path and state_path.exists() and state is None:
            raise ValueError('workflow_state_must_be_object')
        if args.action == 'start':
            if args.state or args.work_id:
                raise ValueError('start_creates_a_new_task; use begin/connect for an existing record')
            prior = resolve_task(root, context=context)[0] if context else None
            state = begin(root, project, args.intent, args.target, prior_state=prior,
                          request_summary=args.request_summary, outcome_refs=args.outcome_ref)
            if args.investigation:
                state = record_investigation(root, state, json.loads(args.investigation.read_text(encoding='utf-8')))
            state_path = local_path(root, f'.work/tasks/{state["task_id"]}/state.json')
            write_state(state_path, state)
        elif args.action != 'begin' and (context or args.state or args.work_id) and not (
                args.action == 'connect' and (args.state or args.work_id)):
            state, state_path, args.work_id = resolve_task(root, args.state, args.work_id, context)
        elif args.work_id:
            if args.action == 'begin':
                raise ValueError('Harness start owns this baseline; use audit or review with --work-id')
            state, state_path = work_record(root, args.work_id)
        if args.action in {'connect', 'resume', 'lookup', 'prepare', 'execute'} and state is None:
            raise ValueError('explicit_task_selection_required; select --state/--work-id or use start/connect context')
        if args.action in {'prepare', 'execute', 'review', 'feedback'} and configuration(project) is None:
            raise ValueError('workflow_not_configured; diagnosis supports investigate/connect/lookup/resume only')
        if args.action in {'begin', 'review', 'feedback', 'investigate'}:
            if not state_path:
                raise ValueError('state_required')
            changed = False
            if args.action == 'begin':
                if state is None:
                    state = begin(root, project, args.intent, args.target,
                                  request_summary=args.request_summary, outcome_refs=args.outcome_ref)
                    state_path.parent.mkdir(parents=True, exist_ok=True)
                    changed = True
                elif ((args.request_summary is not None or args.outcome_ref) and
                      state.get('request') != request_details(root, args.request_summary, args.outcome_ref)):
                    raise ValueError('resume_request_mismatch')
                elif state.get('intent') != args.intent or state.get('targets') != sorted(set(args.target)):
                    raise ValueError('resume_request_mismatch')
                if args.investigation:
                    state = record_investigation(root, state, json.loads(args.investigation.read_text(encoding='utf-8')))
                    changed = True
            elif args.action == 'investigate':
                if state is None or args.investigation is None:
                    raise ValueError('existing_state_and_investigation_required')
                state = record_investigation(root, state, json.loads(args.investigation.read_text(encoding='utf-8')))
                changed = True
            elif args.action == 'feedback':
                if state is None or args.feedback is None:
                    raise ValueError('existing_state_and_feedback_required')
                state = record_feedback(root, project, state, json.loads(args.feedback.read_text(encoding='utf-8')))
                changed = True
            else:
                if state is None or args.review is None:
                    raise ValueError('existing_state_and_review_required')
                state = record_review(root, project, state, json.loads(args.review.read_text(encoding='utf-8')))
                changed = True
            if changed:
                write_state(state_path, state, staging=root / '.work' if args.work_id else None)
        verification = None
        result = None
        if args.action in {'lookup', 'resume', 'audit'}:
            result = inspect_project(root, project, state)
        if args.action in {'prepare', 'execute'} or args.action in {'lookup', 'resume', 'audit'} and state and state.get('execution_plan'):
            try:
                verification = connected_verification(root, project, state, state_path, args.work_id, args.action,
                    output=args.output, run_check=args.run_check, timeout=args.timeout, resume=args.resume,
                    workflow_bases={f['id']: f['basis'] for f in result['features']} if result is not None and
                        local_path(root, args.project) == local_path(root, '.harness/project.yaml') else None)
            except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
                if args.action not in {'lookup', 'resume', 'audit'}:
                    raise
                verification = {'status': 'BLOCKED', 'remaining': [str(error)],
                                'read_only': True, 'test_commands_executed': 0}
            state, state_path = task_state(root, None if args.work_id else state_path.relative_to(root), args.work_id)
        if result is None:
            result = inspect_project(root, project, state)
        result['test_commands_executed'] = (verification or {}).get('test_commands_executed', 0)
        result['read_only'] = args.action in {'connect', 'resume', 'lookup', 'audit', 'maintain', 'accept'}
        if verification is not None:
            result['verification'] = verification
        if args.action == 'maintain':
            result['maintenance'] = maintenance_summary(root, project, state, args.history_bundle,
                                                        retirements=result['check_retirements'])
        elif args.history_bundle:
            raise ValueError('history_bundle_requires_read_only_maintain')
        if args.action == 'accept':
            result['status'] = 'BLOCKED'
            result['findings'].append('host_protected_acceptance_unavailable')
        if state is not None:
            if configuration(project) is not None:
                selection = pending_selection(result)
                result['execution_selection'] = {key: selection[key] for key in ('selected_checks', 'selection', 'unconnected_features')}
            result['task_context'] = task_context(root, state, state_path, args.work_id)
            result['task'] = {'state': state_path.relative_to(root).as_posix(), 'work_id': args.work_id,
                              **{key: state.get(key) for key in ('task_id', 'intent', 'targets', 'request', 'base', 'dirty_baseline',
                                                               'reviews', 'feedback', 'results', 'execution_plan', 'investigation')}}
        if args.action in {'lookup', 'resume', 'audit'} and (verification or {}).get('status') == 'BLOCKED':
            result['status'] = 'BLOCKED'
            result['next_actions'].append({'target': state['task_id'],
                'scope': 'request_required', 'status': 'BLOCKED',
                'current_validity': 'BLOCKED', 'blockers': verification.get('remaining', []) or verification.get('unknown_launches', []),
                'plan': state.get('execution_plan'),
                'requires': ['execution_plan_reconciliation'],
                'reason': 'Inspect verification blockers and existing effects before explicit prepare/execute; lookup never retries.'})
            result['action_scope_counts']['request_required'] += 1
        if state is not None:
            result['handoff'] = handoff_summary(result, verification)
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
        result = {'status': 'BLOCKED', 'findings': [str(error)], 'test_commands_executed': 0}
        if root is not None and project is not None:
            try:
                result['task_candidates'] = task_candidates(root, project)
                result['selection_hint'] = 'Select an exact --state/--work-id. Other custom .work paths require their explicit --state.'
            except (OSError, ValueError, TypeError, KeyError):
                pass
    if args.summary and result.get('features') is not None:
        result = summarize_lookup(result, project, root)
    print(json.dumps(result, sort_keys=not args.summary))
    if args.action in {'prepare', 'execute'} and result.get('verification'):
        return {'PREPARED': 0, 'NOT_REQUIRED': 0, 'PASS': 0, 'ISSUES': 1}.get(result['verification']['status'], 2)
    return 0 if result['status'] in {'READY_FOR_REVIEW', 'NOT_CONFIGURED'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
