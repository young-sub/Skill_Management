"""Render the lean-audit tables from scan/routes/latency/provenance outputs. No model calls.

Token sizes use R tokens per UTF-8 byte, the median context jump per byte over every recorded Skill-body
injection (scan.py `skill_jumps`). Per-session consumption is `token_requests`: tokens an element added to the
context times the requests that re-read them (input + cache reads), the element's share of the session total.
"""
import argparse
import json
import math
import random
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / 'plugins/agentic-coding/skills'
IDEAL = {'IMPL': {'agent-workflow'}, 'BUG': {'diagnose'}, 'RESUME': {'recall', 'agent-workflow'},
         'IMPL-GO': {'agent-workflow', None}, 'FEEDBACK': {None, 'diagnose'}}
CODE_FACT = 'code-fact'
JUDGMENT = 'judgment'
ENVIRONMENT = 'environment'


def load(out, name):
    return json.loads((out / name).read_text(encoding='utf-8'))


def ratio(cells):
    rows = [j['tokens'] / j['body_bytes'] for c in cells for j in c.get('skill_jumps') or [] if j['body_bytes']]
    return st.median(rows), len(rows)


def skill_rows(r):
    rows = []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        text = (d / 'SKILL.md').read_text(encoding='utf-8')
        m = re.match(r'---\n(.*?)\n---\n', text, re.S)
        front, body = m.group(1), text[m.end():]
        desc = re.search(r'^description:\s*(.+)$', front, re.M).group(1)
        explicit = 'disable-model-invocation: true' in front
        refs = [p for p in d.rglob('*') if p.is_file() and p.name != 'SKILL.md']
        ref_bytes = sum(p.stat().st_size for p in refs)
        listing = len(f'- agentic-coding:{d.name}: {desc}'.encode('utf-8'))
        rows.append({'skill': d.name, 'explicit_only': explicit,
                     'listing_bytes': 0 if explicit else listing, 'listing_tokens': 0 if explicit else round(listing * r),
                     'body_bytes': len(body.encode('utf-8')), 'body_tokens': round(len(body.encode('utf-8')) * r),
                     'reference_files': len(refs), 'reference_bytes': ref_bytes, 'reference_tokens': round(ref_bytes * r)})
    return rows


def eval_consumption(cells):
    """Mean per cell, by dataset and arm."""
    out = {}
    groups = defaultdict(list)
    for c in cells:
        groups[(c['dataset'], c['arm'])].append(c)
    for (ds, arm), rows in sorted(groups.items()):
        n = len(rows)
        classes = Counter()
        for c in rows:
            for k, v in (c.get('process') or {}).items():
                classes[k] += v['token_requests']
        out[f'{ds}/{arm}'] = {
            'cells': n, 'success': sum(c['verified_success'] for c in rows), 'false': sum(c['false_completion'] for c in rows),
            'admitted': sum(c['admitted_incomplete'] for c in rows),
            'tokens_mean': round(sum(c['tokens'] for c in rows) / n), 'cost_mean': round(sum(c['cost_usd'] for c in rows) / n, 3),
            'requests_mean': round(sum(c['requests'] for c in rows) / n, 1),
            'first_ctx_median': st.median(c['first_ctx'] for c in rows),
            'tokens_per_success': round(sum(c['tokens'] for c in rows) / max(1, sum(c['verified_success'] for c in rows))),
            'process_token_requests_mean': {k: round(v / n) for k, v in classes.items()},
            'hook_context_chars_mean': round(sum(c['hook_context_chars'] or 0 for c in rows) / n),
            'stop_blocks': sum(c['stop_blocks'] or 0 for c in rows),
            'unexercised_final_edit': sum(c.get('unexercised_final_edit') or 0 for c in rows),
            'skill_invocations': sum(len(c.get('plugin_skills') or []) for c in rows),
        }
    return out


def real_consumption(sessions, r, global_tokens, project_tokens):
    rows = []
    for s in sessions:
        if not s['requests']:
            continue
        listing = (s['listing'] or {}).get('agentic_bytes') or 0
        hook = sum(p['context_bytes'] * r * (1 + p.get('requests_after', 0)) for p in s['prompts'])
        in_repo = 'Skill-Management' in s['project']
        rows.append({
            'session': s['session'][:8], 'project': s['project'].split('-python-')[-1], 'start': s['start'][:10],
            'requests': s['requests'], 'subagent_requests': s['subagent_requests'],
            'total_input_tokens': s['sum_ctx'] + s['subagent_sum_ctx'],
            'global_agents_md': round(global_tokens * s['requests']),
            'project_claude_md': round(project_tokens * s['requests']) if in_repo else 0,
            'plugin_listing': round(listing * r * s['requests']),
            'prompt_hook_context': round(hook), 'prompts_with_hook_context': len(s['prompts']),
            'skill_bodies': (s['process'].get('skill') or {}).get('token_requests', 0),
            'plugin_scripts': (s['process'].get('plugin-script') or {}).get('token_requests', 0),
            'plugin_doc_reads': (s['process'].get('plugin-doc-read') or {}).get('token_requests', 0),
            'harness_writes': (s['process'].get('harness-write') or {}).get('token_requests', 0),
            'stop_guard_runs': len(s['stops']), 'stop_blocks': sum(1 for x in s['stops'] if x['block']),
        })
    return rows


def confusion(routes, column):
    rows = [x for x in routes if x['kind'] == 'user' and x['label'] not in (None, 'DUPLICATE')]
    matrix = Counter((x['label'], x[column]) for x in rows)
    correct = sum(1 for x in rows if x[column] in IDEAL.get(x['label'], {None}))
    wrong = [x for x in rows if x[column] not in IDEAL.get(x['label'], {None})]
    notes = [x for x in routes if x['kind'] == 'task-notification' and x[column]]
    return {'n': len(rows), 'correct': correct, 'matrix': {f'{a}|{b}': v for (a, b), v in sorted(matrix.items(), key=str)},
            'misroutes': [{'id': x['id'], 'label': x['label'], 'route': x[column], 'recorded': x['recorded'],
                           'text': re.sub(r'\s+', ' ', x['text'])[:160]} for x in wrong],
            'task_notifications_routed': len(notes),
            'task_notifications_total': sum(1 for x in routes if x['kind'] == 'task-notification')}


def discordant(cells):
    out = []
    for ds in sorted({c['dataset'] for c in cells}):
        index = {(c['scenario'], c['rep'], c['arm']): c for c in cells if c['dataset'] == ds}
        pairs = [(index[(s, r, 'on')], index[(s, r, 'off')]) for (s, r, a) in index if a == 'on' and (s, r, 'off') in index]
        if not pairs:
            continue
        b = [(on, off) for on, off in pairs if off['verified_success'] and not on['verified_success']]
        c = [(on, off) for on, off in pairs if on['verified_success'] and not off['verified_success']]
        out.append({'dataset': ds, 'pairs': len(pairs), 'on_fail_off_success': len(b), 'on_success_off_fail': len(c),
                    'mcnemar_exact_p': mcnemar(len(b), len(c)),
                    'false_on_only': sum(1 for on, off in pairs if on['false_completion'] and not off['false_completion']),
                    'false_off_only': sum(1 for on, off in pairs if off['false_completion'] and not on['false_completion']),
                    'cells': [{'scenario': on['scenario'], 'rep': on['rep'], 'winner': 'off' if off['verified_success'] else 'on',
                               'on_regression': on['regression_passed'], 'on_hidden_failed': on['hidden_failed'],
                               'off_regression': off['regression_passed'], 'off_hidden_failed': off['hidden_failed']}
                              for on, off in b + c]})
    return out


def mcnemar(b, c):
    n = b + c
    if not n:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return round(min(1.0, 2 * tail), 4)


def mde(discordance, pairs, alpha=0.05, power=0.8):
    """Smallest non-inferiority margin (success-rate points) testable at one-sided alpha with the given power,
    when the true paired difference is 0 and a fraction `discordance` of pairs disagree."""
    z = {0.05: 1.6449, 0.025: 1.96}[alpha] + 0.8416
    return round(z * math.sqrt(discordance / pairs), 3)


def bootstrap_diff(cells, ds, key, draws=10000, seed=7):
    index = {(c['scenario'], c['rep'], c['arm']): c for c in cells if c['dataset'] == ds}
    pairs = [(index[(s, r, 'on')][key], index[(s, r, 'off')][key]) for (s, r, a) in index if a == 'on' and (s, r, 'off') in index]
    rng = random.Random(seed)
    diffs = sorted(sum(int(a) - int(b) for a, b in (rng.choice(pairs) for _ in pairs)) / len(pairs) for _ in range(draws))
    return {'point': round(sum(int(a) - int(b) for a, b in pairs) / len(pairs), 3),
            'ci95': [round(diffs[int(.025 * draws)], 3), round(diffs[int(.975 * draws)], 3)]}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    out = Path(args.output)
    cells = load(out, 'eval_cells.json')
    sessions = load(out, 'real_sessions.json')['sessions']
    routes = load(out, 'routes.json')
    latency = load(out, 'latency.json')['summary']
    r, n_jumps = ratio(cells)
    global_bytes = (ROOT / 'authoring/global/AGENTS.md').stat().st_size
    project_bytes = (ROOT / 'CLAUDE.md').stat().st_size
    skills = skill_rows(r)
    first = defaultdict(list)
    for c in cells:
        first[(c['dataset'], c['arm'])].append(c['first_ctx'])
    always_on = {ds: round(st.median(first[(ds, 'on')]) - st.median(first[(ds, 'off')]))
                 for ds in ('v1-0.1.88', 'v2-0.1.89')}
    pairs_total = sum(d['pairs'] for d in discordant(cells))
    disc_total = sum(d['on_fail_off_success'] + d['on_success_off_fail'] for d in discordant(cells))
    stops = [x for s in sessions for x in s['stops']]
    result = {
        'tokens_per_byte': {'r': round(r, 4), 'skill_body_injections': n_jumps},
        'always_on_measured_on_minus_off_first_request': always_on,
        'static': {'global_agents_md': {'bytes': global_bytes, 'tokens': round(global_bytes * r)},
                   'project_claude_md': {'bytes': project_bytes, 'tokens': round(project_bytes * r)},
                   'listing_current_bytes': sum(x['listing_bytes'] for x in skills),
                   'listing_current_tokens': sum(x['listing_tokens'] for x in skills),
                   'skills': skills},
        'latency': latency,
        'stop_hook_host_ms': {'n': sum(1 for x in stops if x['ms'] is not None),
                              'p50': st.median([x['ms'] for x in stops if x['ms'] is not None]),
                              'p95': sorted(x['ms'] for x in stops if x['ms'] is not None)[int(.95 * sum(1 for x in stops if x['ms'] is not None))]},
        'eval': eval_consumption(cells),
        'real': real_consumption(sessions, r, global_bytes * r, project_bytes * r),
        'stop_blocks': {'eval_cells': sum(c['stop_blocks'] or 0 for c in cells), 'eval_cell_count': len(cells),
                        'real_guard_runs': len(stops), 'real_blocks': [x for x in stops if x['block']]},
        'routes': {'current': confusion(routes, 'route@4bc7595'), 'v0.1.89': confusion(routes, 'route@987dba7')},
        'discordant': discordant(cells),
        'bootstrap': {ds: {k: bootstrap_diff(cells, ds, k) for k in ('verified_success', 'false_completion')}
                      for ds in ('v1-0.1.88', 'v2-0.1.89')},
        'power': {'observed_discordance': round(disc_total / pairs_total, 3), 'pairs_observed': pairs_total,
                  'mde_ni_margin': {n: mde(max(disc_total / pairs_total, 0.05), n) for n in (24, 36, 48, 72, 96)}},
    }
    (out / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('tokens_per_byte', 'always_on_measured_on_minus_off_first_request', 'stop_blocks',
                                              'bootstrap', 'power', 'stop_hook_host_ms')}, ensure_ascii=False, indent=1))
    for k in ('current', 'v0.1.89'):
        x = result['routes'][k]
        print(k, x['n'], 'correct', x['correct'], 'tn routed', x['task_notifications_routed'], '/', x['task_notifications_total'])


if __name__ == '__main__':
    sys.exit(main())
