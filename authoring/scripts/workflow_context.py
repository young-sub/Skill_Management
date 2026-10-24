"""Read-only Codex prompt hook: deliver current obligations, never execute work."""
import json
import os
import re
from pathlib import Path
import subprocess
import sys


# Request routes, measured on tests/distribution/fixtures/route_*.json. In a code repository a message
# that is not a question, a trivial edit or chit-chat is a task, so it defaults to agent-workflow.
ROUTES = (
    ('agent-workflow', 'show what is verified: render lookup/audit --report and answer from it',
     r'(검증|테스트)\s?(결과|현황|상태)|어떤\s?(테스트|검증)|무엇이\s?검증|검증(되지|이 안|안 된)|테스트\s?(되어|돼)\s?있|'
     r'검증이?\s?(끝난|됐|된)\s?(거|건)|verification\s(status|results|coverage)|test coverage|been verified|'
     r'what\s(is|was|gets)\s(tested|verified)|not\scovered|show\s.{0,12}(results|verification)'),
    ('recall', 'resume prior work: reconcile the handoff with the checkout before acting',
     r'어디까지|이어서|이어\s?하|계속\s?하자|하던\s?작업|중단된\s.{0,12}작업|작업\s?계속|where (were|did) we|'
     r'continue (where|the previous)|left off|pick up .{0,40}(where|from)'),
    ('setup-project-verification', 'connect verification for a flow',
     r'검증\s?체계|검증.{0,12}연결|연결.{0,12}검증|테스트\s?환경\s?(붙|연결|구성)|테스트를?\s?붙여|(e2e|E2E)\s?테스트를?\s?(연결|붙)|'
     r'connect\s.{0,20}verification|set\s?up\s.{0,30}(verification|automated (checks?|tests?))'),
    ('agent-workflow', 'guardrail: express the rule in the existing linter/runner and prove it rejects a synthetic violation',
     r'가드레일|재발\s?방지|린트|다시\s?들어오지\s?못하게|막는\s?규칙|guardrail|\blint\b|boundary rule|CI check'),
    ('agent-workflow', 'UI standards: discover the project UI guide and shared token/component owners before editing',
     r'통일감?|일관되게|제각각|스타일\s?가이드|디자인\s?(기준|시스템)|\bUI\b.{0,12}(정리|맞춰|통일|개선)|design system|'
     r'design tokens?|style guide'),
)
SYMPTOM = (r'버그|고장|깨져|깨짐|잘려|사라졌|사라져|엉뚱|틀려|틀린|이상(해|하게|한|하다)|신고|원인|왜\s?그런지|빈\s?(파일|화면|값)|'
           r'안\s?(돼|되|나와|나오|열려|보여|늘어)|(는데|은데)\s?(안|못)\s|(돼|되어)\s?버(려|린)|다시는?\s?(이런|없|안)|'
           r'(오류|에러)(가|이)\s|고객.{0,12}(문의|불만|항의|화)|제보|항의|(했|됐|인|는)데도?\s|두\s?번\s?(차감|결제|청구)|'
           r'마이너스|음수로|하얀\s?화면|흰\s?화면|\bbug\b|\bbroken\b|\bwrong\b|\bfail(s|ing)\b|crash|complain|are seeing|'
           r'never (arrives|loads|shows)|doesn.?t work|not working|regress')
DIAGNOSE = ('diagnose', 'reported incorrect behavior: reproduce, find the cause owner, block the original and alternate paths')
DELEGATE = ('agent-workflow', 'delegated work: acceptance first, prove the checks catch the defect, run affected checks, result card')

# Direct work: quoted copy or label edits, renames, version bumps, questions, reviews, summaries and
# recommendations without a fix request, and very short messages.
QUOTE = '["\'‘’“”]'
TRIVIAL_EDIT = (QUOTE + r'.+' + QUOTE + r'.{0,30}(바꿔|추가|넣어|수정)|(문구|이름|제목|오타|한\s?줄|라벨|버전)\S*\s.{0,40}' + QUOTE
                + r'|버전을?\s.{0,15}(올려|바꿔)|(함수|변수|파일)\s?이름|\brename\b|\btypo\b|bump the version')
QUESTION = (r'설명해|무슨\s?의미|뭐야|어떻게\s?(읽|보)|알려\s?줘|방법|법을?\s|차이가|리뷰|요약|번역해|추천|recommend|'
            r'(커밋|로그|log)\S*\s?(만\s)?보여|explain|what does|how (do|does|to)|difference between|\breview\b|summari[sz]e|translate')
FIX_REQUEST = r'고쳐|수정해|막아|해결|\bfix\b'


def request_route(prompt):
    if not isinstance(prompt, str):
        return None

    def route(skill, reason):
        return {'skill': skill, 'plugin': 'agentic-coding', 'reason': reason,
                'instruction': f'Invoke the {skill} Skill before other work unless the request is a trivial edit.'}

    for skill, reason, pattern in ROUTES:
        if re.search(pattern, prompt, re.I):
            return route(skill, reason)
    if len(prompt.strip()) < 12 or re.search(TRIVIAL_EDIT, prompt, re.I) or (
            re.search(QUESTION, prompt, re.I) and not re.search(FIX_REQUEST, prompt, re.I)):
        return None
    if re.search(SYMPTOM, prompt, re.I):
        return route(*DIAGNOSE)
    if re.search(r'\?\s*$', prompt):
        return None  # A plain question without a reported symptom stays direct.
    return route(*DELEGATE)


def hook_output(summary):
    prefix = 'Workflow hint, not authorization. No tests or repairs ran.\n'

    def encoded(value):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

    # Reserve room for omission metadata before adding optional detail.
    limit = 5500 - len(prefix)
    result = {key: summary[key] for key in ('status', 'connection', 'route', 'project_status', 'detail') if key in summary}
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
    route = request_route(payload.get('prompt'))
    routed = lambda summary: hook_output(dict(summary, route=route) if route else summary)
    # Prior work is discovered by `recall`/resume on request, not projected into every prompt.
    if not os.environ.get('AGENT_WORKFLOW_CONTEXT'):
        return routed({}) if route else {}
    located = subprocess.run(['git', '-C', cwd, 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, encoding='utf-8', check=False)
    if located.returncode:
        return routed({}) if route else {}  # No project workflow outside a Git checkout.
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
        return routed(summary)
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
    return routed(summary)


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
