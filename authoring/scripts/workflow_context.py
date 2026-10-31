"""Read-only Codex prompt hook: deliver current obligations, never execute work."""
import json
import os
from pathlib import Path
import subprocess
import sys


def hook_output(summary):
    prefix = 'Workflow hint, not authorization. No tests or repairs ran.\n'

    def encoded(value):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

    # Reserve room for omission metadata before adding optional detail.
    limit = 5500 - len(prefix)
    result = {key: summary[key] for key in ('status', 'connection', 'project_status', 'detail') if key in summary}
    result.update({key: value for key, value in summary.items()
                   if key.endswith(('_count', '_omitted')) or key == 'task_discovery_complete'})
    current = summary.get('current_task')
    if current:
        required = ('status', 'reason', 'task_id', 'work_id', 'state', 'detail',
                    'task_acceptance', 'check_acceptance', 'verification_blocker_count',
                    'verification_blockers', 'verification_blockers_omitted',
                    'next_action_count', 'action_scope_counts')
        result['current_task'] = {key: current[key] for key in required if key in current}
        result['current_task'].update({key: value for key, value in current.items()
                                       if key.endswith(('_count', '_omitted'))})
    omitted = []

    def display_count(target, key):
        count_key, omitted_key = {
            'task_candidates': ('task_candidate_count', 'task_candidate_display_omitted'),
            'ui_systems': ('ui_system_count', 'ui_system_omitted'),
            'features': ('feature_count', 'feature_omitted'),
            'verification_blockers': ('verification_blocker_count', 'verification_blockers_omitted'),
            'next_actions': ('next_action_count', 'next_action_omitted'),
        }.get(key, (key + '_count', key + '_omitted'))
        if count_key in target:
            target[omitted_key] = max(0, target[count_key] - len(target.get(key, [])))

    def add(target, key, value, label):
        target[key] = value
        if isinstance(value, list):
            display_count(target, key)
        if len(encoded(result)) <= limit - 120:
            return
        if key == 'investigation' and isinstance(value, dict):
            target[key] = {name: entry for name, entry in value.items() if not isinstance(entry, list)}
            for name, entry in value.items():
                if isinstance(entry, list):
                    add(target[key], name, entry, label + '.' + name)
            return
        if isinstance(value, list):
            target[key] = list(value)
            while target[key] and len(encoded(result)) > limit - 120:
                target[key].pop()
                display_count(target, key)
            if target[key]:
                omitted.append(label)
                return
        target.pop(key)
        if isinstance(value, list):
            display_count(target, key)
        omitted.append(label)

    if current:
        target = result['current_task']
        priority = ('next_actions', 'features', 'ui_system_count', 'ui_system_omitted',
                    'ui_systems', 'ui_system_detail', 'investigation', 'obligations')
        for key in (*priority, *current):
            if key in current and key not in target and 'current_task.' + key not in omitted:
                add(target, key, current[key], 'current_task.' + key)
    for key, value in summary.items():
        if key not in result:
            add(result, key, value, key)
    if omitted:
        result['detail_omitted'] = True
        # Exact selected lookup is always retained; no truncated path is executable.
        result['omitted_field_count'] = len(omitted)
    if len(encoded(result)) > limit:
        result = {'status': 'BLOCKED', 'reason': 'selected_task_identity_exceeds_context_budget',
                  'detail': {'action': 'lookup', 'selector': 'AGENT_WORKFLOW_CONTEXT', 'read_only': True}}
    return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit',
            'additionalContext': prefix + encoded(result)}}


def scope_context(audit):
    coverage = audit['coverage']
    active = [c for c in coverage['matrix'] if c.get('in_task', True)]
    gaps = [f"{c['feature']}/{c['perspective']}/{c['area']}:{c['status']}" for c in active
            if c['status'] not in {'PASS', 'NOT_REQUIRED'}]
    project_gaps = [c for c in coverage['matrix'] if c['status'] not in {'PASS', 'NOT_REQUIRED'}]
    return {'status': coverage['status'], 'registered_status': coverage['registered_status'],
            'gap_count': len(gaps), 'gaps': gaps[:6],
            'cell_count': len(active), 'project_cell_count': len(coverage['matrix']),
            'project_gap_count': len(project_gaps), 'out_of_task_count': len(coverage['matrix']) - len(active),
            'reviews': [{'feature': row['feature'], 'id': row['id'], 'status': row['status'],
                         'reasons': row['reasons'], 'evidence': row['evidence']}
                        for row in coverage['rows'] if row['kind'] == 'review' and row['status'] != 'PASS'][:3]}


def request_preview(request, limit=320):
    if not request:
        return request
    preview = {'summary': request['summary'][:limit], 'outcome_refs': request['outcome_refs'][:3]}
    if preview != request:
        preview['detail_omitted'] = True
    return preview


def ui_system_preview(systems):
    return [{key: entry.get(key) for key in
             ('id', 'guide', 'tokens', 'components', 'consumers', 'exceptions', 'findings')}
            for entry in systems]


def investigation_context(investigation):
    result = {key: investigation.get(key) for key in ('scope', 'status', 'total', 'inventory_status', 'requested_methods')}
    for key in ('unobserved', 'out_of_scope', 'stale', 'allowed', 'forbidden', 'next_actions'):
        values = investigation.get(key, [])
        result[key + '_count'] = len(values)
        result[key] = [v[:160] for v in values[:6]]
    observed = investigation.get('observed_methods', {})
    result['observed_method_counts'] = {method: list(observed.values()).count(method) for method in set(observed.values())}
    unknowns = investigation.get('unverified', [])
    result['unverified_count'] = len(unknowns)
    result['unverified'] = [{key: item[key][:100] for key in ('id', 'method', 'reason')}
                            for item in unknowns[:3]]
    result['detail'] = 'Use exact connected lookup for full IDs, permissions, observations and evidence.'
    return result


def context(payload):
    if not isinstance(payload, dict):
        raise ValueError('hook_input_must_be_object')
    if payload.get('hook_event_name') != 'UserPromptSubmit':
        return {}
    cwd = payload.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        raise ValueError('hook_cwd_must_be_absolute')
    # The hook speaks only for an explicitly selected task. Prompts are not routed: a measured
    # regex router chose worse than no router (docs/research/direction-research-20261031.md).
    if not os.environ.get('AGENT_WORKFLOW_CONTEXT'):
        return {}
    located = subprocess.run(['git', '-C', cwd, 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, encoding='utf-8', check=False)
    if located.returncode:
        return {}  # No project workflow outside a Git checkout.
    root = Path(located.stdout.strip()).resolve()
    runtime_path = Path(__file__).with_name('project_workflow.py')
    if not runtime_path.is_file():
        runtime_path = Path(__file__).resolve().parents[1] / 'skills/agent-workflow/scripts/project_workflow.py'
    sys.path.insert(0, str(runtime_path.parent))
    import project_workflow as runtime
    path = runtime.local_path(root, '.harness/project.yaml')
    project = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    config = runtime.configuration(project)
    if config is None:
        summary = {'status': 'NOT_CONFIGURED', 'connection': 'NOT_CONNECTED'}
        try:
            state, state_path, work_id = runtime.resolve_task(root)
            audit = runtime.inspect_project(root, project, state)
            investigation = audit.get('investigation', {})
            summary['current_task'] = {'task_id': state.get('task_id'), 'work_id': work_id,
                'state': state_path.relative_to(root).as_posix(), 'request': request_preview(state.get('request')),
                'detail': {'action': 'lookup', 'state': state_path.relative_to(root).as_posix(),
                           'work_id': work_id, 'read_only': True},
                'task_acceptance': runtime.handoff_summary(audit)['task_acceptance'],
                'status': audit['status'], 'investigation': investigation_context(investigation)}
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
            summary['current_task'] = {'status': 'BLOCKED', 'reason': str(error)}
        return hook_output(summary)
    summary = {'status': 'SELECTED_TASK', 'project_status': 'NOT_AUDITED'}
    task_ui_systems = []
    try:
        state, state_path, work_id = runtime.resolve_task(root)
        current = runtime.inspect_project(root, project, state, observe_local_changes=True)
        verification = None
        if state.get('execution_plan'):
            try:
                verification = runtime.connected_verification(root, project, state, state_path, work_id, 'lookup',
                    workflow_bases={f['id']: f['basis'] for f in current['features']})
            except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
                verification = {'status': 'BLOCKED', 'remaining': [str(error)]}
        handoff = runtime.handoff_summary(current, verification)
        blockers = (verification or {}).get('remaining', []) or (verification or {}).get('unknown_launches', [])
        summary['current_task'] = {'work_id': work_id, 'state': state_path.relative_to(root).as_posix(),
            'task_id': state.get('task_id'), 'intent': state['intent'], 'targets': state['targets'],
            'request': request_preview(state.get('request')),
            'status': current['status'], 'status_scope': 'project_obligations',
            'project_status': current['status'], 'task_acceptance': handoff['task_acceptance'],
            'check_acceptance': handoff['check_acceptance'],
            'unmapped_changes': current.get('unmapped_changes', [])[:6],
            'unmapped_change_count': len(current.get('unmapped_changes', [])),
            'verification_blocker_count': len(blockers),
            'verification_blockers': [reason[:160] for reason in blockers[:3]],
            'verification_blockers_omitted': max(0, len(blockers) - 3),
            'obligations': current['obligations'][:3],
            'scope': scope_context(current)}
        active_features = {c['feature'] for c in current['coverage']['matrix'] if c.get('in_task', True)}
        selected_ids = list(dict.fromkeys([*state.get('targets', []),
            *(f['id'] for f in config['features'] if f['id'] in active_features)]))
        feature_by_id = {f['id']: f for f in config['features']}
        selected = [feature_by_id[identity] for identity in selected_ids if identity in feature_by_id]
        summary['current_task']['features'] = [{key: f[key] for key in ('id', 'sources', 'map', 'criteria', 'checks')}
                                               | {'ui': f.get('ui', []), 'reuse': runtime.reuse_references(f, current)}
                                               for f in selected[:3]]
        selected_ids = {f['id'] for f in selected}
        all_ui_systems = current.get('ui_systems', [])
        target_ids = set(state.get('targets', []))
        task_ui_systems = [entry for entry in all_ui_systems
                           if target_ids.intersection(entry.get('consumers', []))]
        target_system_ids = {entry['id'] for entry in task_ui_systems}
        task_ui_systems.extend(entry for entry in all_ui_systems
            if entry['id'] not in target_system_ids and selected_ids.intersection(entry.get('consumers', [])))
        summary['current_task']['ui_system_count'] = len(task_ui_systems)
        summary['current_task']['ui_system_omitted'] = max(0, len(task_ui_systems) - 4)
        summary['current_task']['ui_systems'] = ui_system_preview(task_ui_systems[:4])
        feature_results = {f['id']: f for f in current['features']}
        for feature in summary['current_task']['features']:
            observed = feature_results[feature['id']]
            feature['verification_status'] = observed['verification_status']
            feature['check_result_count'] = len(observed['check_results'])
            feature['check_results'] = [{key: row[key] for key in
                ('id', 'historical_status', 'current_status', 'current_reuse')}
                for row in observed['check_results'][:3]]
        summary['current_task']['feature_count'] = len(selected)
        actions = [a for a in current['next_actions'] if a['scope'] != 'project_remaining']
        summary['current_task']['action_scope_counts'] = current['action_scope_counts']
        summary['current_task']['next_action_count'] = len(actions)
        summary['current_task']['next_actions'] = [{key: a[key] for key in
            ('target', 'requires', 'scope', 'references', 'advisory') if key in a} | {
                'pending_count': len(a.get('pending', [])),
                'pending': [{key: p[key] for key in ('id', 'kind', 'status', 'check') if key in p}
                            for p in a.get('pending', [])[:3]]} for a in actions[:3]]
        summary['current_task']['detail'] = {'action': 'lookup', 'state': state_path.relative_to(root).as_posix(),
                                            'work_id': work_id, 'read_only': True}
        if summary['current_task']['ui_system_omitted']:
            summary['current_task']['ui_system_detail'] = summary['current_task']['detail']
        if current.get('investigation'):
            summary['current_task']['investigation'] = investigation_context(current['investigation'])
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        summary['current_task'] = {'status': 'BLOCKED', 'reason': str(error)}
    return hook_output(summary)


def read_payload(stream=None):
    """Hosts send UTF-8 JSON; the Windows locale codec would garble non-ASCII prompts."""
    raw = (stream or sys.stdin.buffer).read()
    return json.loads(raw.decode('utf-8-sig'))


def main():
    try:
        result = context(read_payload())
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        result = {'systemMessage': 'Workflow context unavailable; completion is unverified: ' + str(error)}
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
