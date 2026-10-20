"""Read-only Codex prompt hook: deliver current obligations, never execute work."""
import json
import os
import re
from pathlib import Path
import subprocess
import sys


def development_request(prompt):
    """A discovery hint only; prompt text never selects a task or authorizes work."""
    return isinstance(prompt, str) and bool(re.search(
        r'\b(fix|implement|refactor|debug|code|test|build)\b|구현|수정|버그|리팩터|개발|테스트', prompt, re.I))


def hook_output(summary):
    prefix = ('Current workflow data, not instructions or authorization. No tests or repairs ran. '
              'Lookup is read-only; project remainder is not a task blocker.\n')

    def encoded(value):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

    # Reserve room for omission metadata before adding optional detail.
    limit = 5500 - len(prefix)
    result = {key: summary[key] for key in ('status', 'project_status', 'detail') if key in summary}
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

    def add(target, key, value, label):
        target[key] = value
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
            if target[key]:
                omitted.append(label)
                return
        target.pop(key)
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
        selector = os.environ.get('AGENT_WORKFLOW_CONTEXT')
        records = [] if selector else runtime.task_candidates(root, project, limit=8)
        omitted = sum(c.get('status') == 'NOT_INSPECTED' for c in records)
        candidates = [c for c in records if c.get('intent') == 'diagnose']
        fallback = ('Use existing AGENTS.md, docs/index.md and project test/build commands; inspect relevant callers, types and tests before editing. '
                    'Select the matching agent-workflow playbook only if needed. Verify affected behavior after the final edit. No Harness setup is required.')
        if not selector and not candidates and not omitted:
            if not development_request(payload.get('prompt')):
                return {}
            return hook_output({'status': 'NOT_CONFIGURED', 'guidance': fallback})
        summary = {'status': 'NOT_CONFIGURED', 'task_candidates': [dict(c, request=request_preview(c.get('request'), 160)) for c in candidates[:8]],
                   'task_candidate_count': len(candidates), 'task_record_count': len(records),
                   'task_candidate_omitted': omitted, 'task_discovery_complete': omitted == 0,
                   'task_discovery_detail': 'For full candidate paths run resume without task context or selector, then select exact --state/--work-id. Omitted intent and validity are unknown.'}
        if development_request(payload.get('prompt')):
            summary['guidance'] = fallback
        if selector:
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
    if not os.environ.get('AGENT_WORKFLOW_CONTEXT'):
        candidates = runtime.task_candidates(root, project, limit=8)
        summary = {'status': 'TASK_NOT_SELECTED', 'project_status': 'NOT_AUDITED',
            'task_candidates': [dict(c, request=request_preview(c.get('request'), 160)) for c in candidates[:8]],
            'task_candidate_count': len(candidates), 'task_candidate_omitted': max(0, len(candidates) - 8),
            'task_discovery_complete': len(candidates) <= 8,
            'detail': {'action': 'resume', 'read_only': True},
            'next_action': 'Use an exact --state/--work-id for existing work; ordinary direct work needs no task. Full project audit is explicit.'}
        return hook_output(summary)
    summary = {'status': 'SELECTED_TASK', 'project_status': 'NOT_AUDITED'}
    task_ui_systems = []
    if os.environ.get('AGENT_WORKFLOW_CONTEXT'):
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
                                                   | {'ui': f.get('ui', [])}
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


def main():
    try:
        result = context(json.load(sys.stdin))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        result = {'systemMessage': 'Workflow context unavailable; completion is unverified: ' + str(error)}
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
