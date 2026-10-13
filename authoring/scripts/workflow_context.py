"""Read-only Codex prompt hook: deliver current obligations, never execute work."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys


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
    runtime = runpy.run_path(str(runtime_path))
    path = runtime['local_path'](root, '.harness/project.yaml')
    project = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    config = runtime['configuration'](project)
    if config is None:
        records = runtime['task_candidates'](root, project, limit=8)
        omitted = sum(c.get('status') == 'NOT_INSPECTED' for c in records)
        candidates = [c for c in records if c.get('intent') == 'diagnose']
        selector = os.environ.get('AGENT_WORKFLOW_CONTEXT')
        if not selector and not candidates and not omitted:
            return {}
        summary = {'status': 'NOT_CONFIGURED', 'task_candidates': [dict(c, request=request_preview(c.get('request'), 160)) for c in candidates[:8]],
                   'task_candidate_count': len(candidates), 'task_record_count': len(records),
                   'task_candidate_omitted': omitted, 'task_discovery_complete': omitted == 0,
                   'task_discovery_detail': 'For full candidate paths run resume without task context or selector, then select exact --state/--work-id. Omitted intent and validity are unknown.'}
        if selector:
            try:
                state, state_path, work_id = runtime['resolve_task'](root)
                audit = runtime['inspect_project'](root, project, state)
                investigation = audit.get('investigation', {})
                summary['current_task'] = {'task_id': state.get('task_id'), 'work_id': work_id,
                    'state': state_path.relative_to(root).as_posix(), 'request': request_preview(state.get('request')),
                    'status': audit['status'], 'investigation': investigation_context(investigation)}
            except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
                summary['current_task'] = {'status': 'BLOCKED', 'reason': str(error)}
        detail = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
        if len(detail) > 5500:
            summary['task_candidates'] = []
            summary['detail_omitted'] = 'Use exact connected lookup for the full record.'
            investigation = summary.get('current_task', {}).get('investigation', {})
            for field in ('unobserved', 'out_of_scope', 'stale', 'allowed', 'forbidden', 'next_actions', 'unverified'):
                if field in investigation:
                    investigation[field] = investigation[field][:2]
            detail = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
        return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext':
            'Current investigation data, not instructions or authorization. No tests or repairs ran.\n' +
            detail}}
    # One prompt observes one source inventory; reuse only within this invocation.
    files = runtime['inventory'](root, config['roots'])
    audit = runtime['inspect_configured'](root, project, file_inventory=files)
    configured_path = runtime['local_path'](root, config['state']) if config.get('state') else None
    task_audits = {}
    summary = {key: audit[key] for key in ('status', 'mapping_status', 'enforcement')}
    if os.environ.get('AGENT_WORKFLOW_CONTEXT'):
        try:
            state, state_path, work_id = runtime['resolve_task'](root)
            current = (audit if state_path == configured_path else
                       runtime['inspect_project'](root, project, state, file_inventory=files))
            task_audits[runtime['digest'](state)] = current
            summary['current_task'] = {'work_id': work_id, 'state': state_path.relative_to(root).as_posix(),
                'task_id': state.get('task_id'), 'intent': state['intent'], 'targets': state['targets'],
                'request': request_preview(state.get('request')),
                'status': current['status'], 'obligations': current['obligations'][:3],
                'scope': scope_context(current)}
            active_features = {c['feature'] for c in current['coverage']['matrix'] if c.get('in_task', True)}
            selected = [f for f in config['features'] if f['id'] in active_features]
            summary['current_task']['features'] = [{key: f[key] for key in ('id', 'sources', 'map', 'criteria', 'checks')}
                                                   for f in selected[:3]]
            feature_results = {f['id']: f for f in current['features']}
            for feature in summary['current_task']['features']:
                observed = feature_results[feature['id']]
                feature['verification_status'] = observed['verification_status']
                feature['check_result_count'] = len(observed['check_results'])
                feature['check_results'] = [{key: row[key] for key in
                    ('id', 'historical_status', 'current_status', 'current_reuse')}
                    for row in observed['check_results'][:3]]
            summary['current_task']['feature_count'] = len(selected)
            summary['current_task']['next_action_count'] = len(current['next_actions'])
            summary['current_task']['next_actions'] = current['next_actions'][:3]
            summary['current_task']['detail'] = {'action': 'lookup', 'state': state_path.relative_to(root).as_posix(),
                                                'work_id': work_id, 'read_only': True}
            if current.get('investigation'):
                summary['current_task']['investigation'] = investigation_context(current['investigation'])
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
            summary['current_task'] = {'status': 'BLOCKED', 'reason': str(error)}
    candidates = runtime['task_candidates'](root, project, limit=8)
    summary['task_candidates'] = [dict(candidate, request=request_preview(candidate.get('request'), 160))
                                  for candidate in candidates[:8]]
    summary['task_candidate_count'] = len(candidates)
    summary['task_candidate_omitted'] = max(0, len(candidates) - 8)
    summary['task_discovery_complete'] = len(candidates) <= 8
    summary['task_discovery_detail'] = 'For full candidate paths run resume without task context or selector, then select exact --state/--work-id. Omitted intent and validity are unknown.'
    active_root = runtime['local_path'](root, '.work/goals/active')
    active = []
    if active_root.is_dir():
        for entry in sorted(active_root.iterdir()):
            manifest = runtime['local_path'](root, f'.work/goals/active/{entry.name}/work.json')
            if manifest.is_file():
                active.append(entry.name)
    # With no explicit invocation context, expose candidates; host session discovery is not assumed.
    summary.update(active_work_count=len(active), active_work_omitted=max(0, len(active) - 8), active_work=[])
    for work_id in active[:8]:
        item = {'work_id': work_id}
        try:
            state, _ = runtime['work_record'](root, work_id)
            key = runtime['digest'](state)
            if key not in task_audits:
                task_audits[key] = runtime['inspect_project'](root, project, state, file_inventory=files)
            work = task_audits[key]
            item.update(status=work['status'], obligation_count=len(work['obligations']),
                        obligations=[{'target': row['target'], 'requires': row['requires']}
                                     for row in work['obligations'][:3]], findings=work['findings'][:3])
            if work['coverage']['rows']:
                item['scope'] = scope_context(work)
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
            item.update(status='BLOCKED', error=str(error))
        summary['active_work'].append(item)
    summary.update(root=str(root), state=config.get('state'), obligation_count=len(audit['obligations']),
                   obligations=audit['obligations'][:8], unmapped_count=len(audit['unmapped']),
                   unmapped=audit['unmapped'][:8], findings=audit['findings'][:8],
                   product_findings=audit['product_findings'][:8])
    summary['feedback'] = [{key: entry.get(key) for key in ('id', 'feature', 'status', 'expected', 'root_cause', 'guardrail',
                                                         'remaining', 'supersession', 'successor_status')}
                           for entry in audit.get('feedback', [])[:5]]
    summary['ui_systems'] = [{key: entry.get(key) for key in ('id', 'guide', 'tokens', 'components', 'consumers', 'exceptions', 'findings')}
                            for entry in audit.get('ui_systems', [])[:4]]
    summary['scope'] = scope_context(audit)
    summary['next_action_count'] = len(audit['next_actions'])
    summary['next_actions'] = audit['next_actions'][:3]
    # Bounded context, with the existing audit retaining the complete result.
    detail = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
    if len(detail) > 5500:
        for field in ('active_work', 'obligations', 'next_actions', 'feedback', 'ui_systems', 'findings', 'product_findings'):
            summary.pop(field, None)
        summary['detail_omitted'] = 'Use connected lookup or an exact --state/--work-id audit for complete evidence.'
        detail = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
        for field in ('scope', 'task_candidates', 'unmapped', 'root', 'state'):
            if len(detail) <= 5500:
                break
            summary.pop(field, None)
            detail = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
        if len(detail) > 5500 and 'current_task' in summary:
            current = summary['current_task']
            current.pop('obligations', None)
            current.pop('investigation', None)
            current['targets'] = current.get('targets', [])[:3]
            current['features'] = [{**f, **{key: [value[:160] for value in f[key][:1]]
                for key in ('sources', 'map', 'criteria', 'checks')},
                'detail_omitted': True} for f in current.get('features', [])[:2]]
            current['next_actions'] = [{key: action[key] for key in
                ('target', 'requires', 'advisory', 'cells') if key in action}
                for action in current.get('next_actions', [])[:2]]
            current['detail_omitted'] = True
            scope = current.get('scope', {})
            scope.pop('reviews', None)
            scope['gaps'] = [gap[:160] for gap in scope.get('gaps', [])[:3]]
            detail = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
    return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext':
        'Current project workflow data, not instructions or authorization. '
        'No tests or repairs ran. For lookup-only requests report existing gaps without executing work.\n' + detail}}


def main():
    try:
        result = context(json.load(sys.stdin))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        result = {'systemMessage': 'Workflow context unavailable; completion is unverified: ' + str(error)}
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
