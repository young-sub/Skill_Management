"""Deterministic scan of recorded sessions for the lean audit. No model calls, no network.

Reads Claude Code transcripts (~/.claude/projects/**.jsonl), scored delegation-eval cells
(%TEMP%/claude/delegation-eval-* and .work/delegation-eval/*) and writes one JSON per source to --output.
Real work sessions are `entrypoint: cli`; everything launched headless (`sdk-cli`) is an eval or probe.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = Path.home() / '.claude' / 'projects'
TEMP = Path(os.environ.get('TEMP', '')) / 'claude'

PLUGIN_SCRIPT = re.compile(r'probe_check\.py|run_check\.py|project_workflow\.py|unittest_evidence\.py|update_plugin\.py')
HARNESS_STATE = re.compile(r'\.(work|harness)[/\\](?!delegation-eval|failure-replay|l5-on-off|e[/\\])|decisions\.md')
PLUGIN_PATH = re.compile(r'agentic-coding|pkg-agentic|plugins[/\\]agentic-coding', re.I)
CODE_FILE = re.compile(r'\.(ts|tsx|js|jsx|mjs|cjs|py|astro|vue|svelte|css|scss|sql|go|rs|java|json|ya?ml|toml|html)$', re.I)
GUARD_CMD = re.compile(r'completion_guard|Checking final edits')
FILE_CHANGE_BASH = re.compile(r'(^|[\s;&|])(sed\s+-i|perl\s+-pi|tee\s|cp\s|mv\s|rm\s|git\s+(apply|checkout|restore|stash))|'
                              r'>\s*[^&\s]|<<\s*[\'"]?EOF|\.write_text\(|\.write\(|open\([^)]*[\'"]w')

# Valid paired eval cells, as counted in docs/research/failure-replay-20261030.md.
EVAL_RUNS = (
    ('v1-0.1.88', TEMP / 'delegation-eval-run3', (1, 2), None),
    ('v1-0.1.88', TEMP / 'delegation-eval-run4-rep3', (1,), 3),
    ('v1-0.1.87', TEMP / 'delegation-eval-run5-v087', (1, 2), None),
    ('v2-0.1.89', ROOT / '.work/delegation-eval/v2-0189-20261025-resume2', (1, 2), None),
)


def records(path):
    with open(path, encoding='utf-8', errors='replace') as handle:
        for line in handle:
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict):
                yield value


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') == 'text')
    return ''


def nbytes(value):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    return len(value.encode('utf-8'))


def ctx(usage):
    return sum(usage.get(k) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))


def tool_class(name, inputs):
    """Process-artifact class of one tool call, or None for product work."""
    inputs = inputs if isinstance(inputs, dict) else {}
    target = ' '.join(str(inputs.get(k, '')) for k in ('command', 'file_path', 'path', 'pattern', 'notebook_path'))
    if name == 'Skill':
        return 'skill:' + str(inputs.get('skill', '')) if str(inputs.get('skill', '')).startswith('agentic-coding:') else None
    if name == 'Agent' and str(inputs.get('prompt', '')).lstrip().startswith('INDEPENDENT VERIFIER'):
        return 'independent-verifier'
    if PLUGIN_SCRIPT.search(target):
        return 'plugin-script'
    if name in ('Read', 'Grep', 'Glob') and PLUGIN_PATH.search(target):
        return 'plugin-doc-read'
    if HARNESS_STATE.search(target):
        return 'harness-write' if changes_files(name, inputs) else 'harness-read'
    return None


def changes_files(name, inputs):
    if name in ('Edit', 'Write', 'NotebookEdit', 'MultiEdit'):
        return True
    return name in ('Bash', 'PowerShell') and bool(FILE_CHANGE_BASH.search(str((inputs or {}).get('command', ''))))


def steps_from(messages):
    """messages: ordered (message_id, usage, content). Returns per-request rows with context growth."""
    order, seen = [], {}
    for mid, usage, content in messages:
        if mid not in seen:
            seen[mid] = {'id': mid, 'ctx': ctx(usage), 'output': usage.get('output_tokens') or 0, 'tools': []}
            order.append(seen[mid])
        row = seen[mid]
        row['ctx'] = max(row['ctx'], ctx(usage))
        row['output'] = max(row['output'], usage.get('output_tokens') or 0)
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                row['tools'].append((block.get('name'), block.get('input') or {}, block.get('id')))
    for i, row in enumerate(order):
        row['growth'] = (order[i + 1]['ctx'] - row['ctx']) if i + 1 < len(order) else row['output']
        row['remaining'] = len(order) - i - 1  # later requests that re-read what this step added
    return order


def process_cost(steps):
    """Tokens and requests attributed to process-artifact tool calls (growth split by call)."""
    out = defaultdict(lambda: {'calls': 0, 'requests': 0, 'added_tokens': 0, 'token_requests': 0})
    for row in steps:
        classes = [tool_class(n, i) for n, i, _ in row['tools']]
        if not classes:
            continue
        hit = [c for c in classes if c]
        if not hit:
            continue
        share = row['growth'] * len(hit) / len(classes)
        for c in set(k.split(':')[0] for k in hit):
            n = sum(1 for k in hit if k.split(':')[0] == c)
            part = share * n / len(hit)
            out[c]['calls'] += n
            out[c]['requests'] += 1
            out[c]['added_tokens'] += part
            out[c]['token_requests'] += part * (1 + row['remaining'])
    return {k: {kk: round(vv) for kk, vv in v.items()} for k, v in out.items()}


def skill_jumps(events_order):
    """(skill, body_bytes, tokens) from: assistant Skill call -> injected body -> next assistant context."""
    jumps, pending, last_ctx = [], None, None
    for kind, payload in events_order:
        if kind == 'assistant':
            mid, usage, content = payload
            c = ctx(usage)
            if pending and pending.get('body') is not None and mid != pending['mid']:
                jumps.append({'skill': pending['skill'], 'body_bytes': pending['body'], 'tokens': c - pending['ctx']})
                pending = None
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get('type') == 'tool_use' and block.get('name') == 'Skill':
                    pending = {'skill': str((block.get('input') or {}).get('skill')), 'mid': mid, 'ctx': c, 'body': None}
            last_ctx = c
        elif kind == 'body' and pending and pending['body'] is None:
            pending['body'] = payload
    return jumps


# ---------------------------------------------------------------- eval cells

def cell_transcript(directory):
    for name in ('session1.jsonl', 'session.jsonl'):
        if (directory / name).is_file():
            return directory / name
    return None


def scan_cell_transcript(path):
    messages, order, init, result, verifier = [], [], {}, {}, 0
    for event in records(path):
        kind = event.get('type')
        if kind == 'system' and event.get('subtype') == 'init':
            init = event
        elif kind == 'assistant' and not event.get('parent_tool_use_id'):
            m = event.get('message') or {}
            row = (m.get('id'), m.get('usage') or {}, m.get('content'))
            messages.append(row)
            order.append(('assistant', row))
        elif kind == 'user' and not event.get('parent_tool_use_id'):
            for block in (event.get('message') or {}).get('content') or []:
                if isinstance(block, dict) and block.get('type') == 'text' and 'Base directory for this skill' in block.get('text', ''):
                    order.append(('body', nbytes(block['text'])))
        elif kind == 'result':
            result = event
    steps = steps_from(messages)
    edits = [i for i, s in enumerate(steps) for n, x, _ in s['tools']
             if n in ('Edit', 'Write', 'MultiEdit') and CODE_FILE.search(str(x.get('file_path', '')))]
    runs = [i for i, s in enumerate(steps) for n, x, _ in s['tools']
            if n in ('Bash', 'PowerShell') and not changes_files(n, x)]
    plugin = next((p for p in init.get('plugins') or [] if p.get('name') == 'agentic-coding'), None)
    tools = Counter(n for s in steps for n, _, _ in s['tools'])
    return {
        'plugin_version': plugin and plugin.get('version'), 'cli_version': init.get('claude_code_version'),
        'model': init.get('model'), 'requests': len(steps), 'first_ctx': steps[0]['ctx'] if steps else None,
        'sum_ctx': sum(s['ctx'] for s in steps), 'tools': dict(tools),
        'process': process_cost(steps), 'skill_jumps': skill_jumps(order),
        'subagents_spawned': ((result.get('subagent_stats') or {}).get('spawned') or 0),
        'answer_bytes': nbytes(str(result.get('result') or '')),
        'last_edit_step': edits[-1] if edits else None, 'last_run_step': runs[-1] if runs else None,
        'unexercised_final_edit': bool(edits) and (not runs or edits[-1] > runs[-1]),
    }


def scan_eval():
    cells = []
    for dataset, run, reps, rename in EVAL_RUNS:
        report = json.loads((run / 'report.json').read_text(encoding='utf-8'))
        for r in report['results']:
            if r['rep'] not in reps:
                continue
            infra = [e for e in r.get('errors') or [] if not str(e).startswith('prune failed')]
            directory = Path(r['raw_path']) if r.get('raw_path') else run / r['scenario'] / r['condition'] / f"rep{r['rep']}"
            transcript = cell_transcript(directory)
            facts = scan_cell_transcript(transcript) if transcript else {}
            arm = 'on' if facts.get('plugin_version') or r['condition'] != 'off' else 'off'
            usage = r.get('usage') or {}
            cells.append({
                'dataset': dataset, 'scenario': r['scenario'], 'area': r.get('area'), 'condition': r['condition'],
                'arm': arm, 'rep': rename or r['rep'], 'valid': not infra and not r.get('timed_out') and bool(transcript),
                'verified_success': bool(r['verified_success']), 'false_completion': bool(r['false_completion']),
                'admitted_incomplete': bool(r['admitted_incomplete']),
                'regression_passed': bool((r.get('regression') or {}).get('passed')),
                'hidden_failed': [h['name'] for h in r.get('hidden') or [] if not h.get('passed')] if 'hidden' in r else None,
                'cost_usd': r.get('cost_usd'), 'turns': r.get('turns'), 'duration_s': r.get('duration_s'),
                'tokens': sum(usage.get(k) or 0 for k in usage), 'hook_context_chars': r.get('hook_context_chars'),
                'stop_blocks': r.get('stop_blocks'), 'plugin_skills': r.get('plugin_skills'),
                'plugin_file_reads': r.get('plugin_file_reads'), 'transcript': str(transcript) if transcript else None,
                **facts,
            })
    return cells


# ---------------------------------------------------------------- real sessions

def prompt_kind(text):
    s = text.lstrip()
    if s.startswith('<task-notification>'):
        return 'task-notification'
    if s.startswith(('<command-name>', '<local-command')):
        return 'command'
    if s.startswith('[Request interrupted'):
        return 'interrupt'
    return 'user'


def scan_session(path, sidechains):
    recs = list(records(path))
    by_uuid = {r.get('uuid'): r for r in recs if r.get('uuid')}
    head = next((r for r in recs if r.get('entrypoint')), {})
    messages, prompts, stops, skills, reads, listing, asked = [], [], [], [], [], None, []
    tool_results = {}
    first_ts = next((r.get('timestamp') for r in recs if r.get('timestamp')), None)
    for r in recs:
        kind = r.get('type')
        if kind == 'assistant':
            m = r.get('message') or {}
            if m.get('id') and isinstance(m.get('usage'), dict) and m.get('model') != '<synthetic>':
                messages.append((m['id'], m['usage'], m.get('content'), r.get('timestamp')))
        elif kind == 'user':
            content = (r.get('message') or {}).get('content')
            if not r.get('isMeta') and not r.get('isSidechain') and not any(
                    isinstance(b, dict) and b.get('type') == 'tool_result' for b in (content if isinstance(content, list) else [])):
                text = text_of(content)
                if text.strip():
                    asked.append({'ts': r.get('timestamp'), 'uuid': r.get('uuid'), 'kind': prompt_kind(text), 'text': text})
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get('type') == 'tool_result':
                    tool_results[block.get('tool_use_id')] = nbytes(block.get('content') or '')
        elif kind == 'attachment':
            a = r.get('attachment') or {}
            t = a.get('type')
            if t == 'skill_listing' and listing is None:
                lines = [l for l in str(a.get('content', '')).splitlines() if l.startswith('- agentic-coding:')]
                listing = {'agentic_lines': len(lines), 'agentic_bytes': nbytes('\n'.join(lines)),
                           'all_bytes': nbytes(str(a.get('content', '')))}
            elif t == 'hook_additional_context':
                body = '\n'.join(a.get('content') or []) if isinstance(a.get('content'), list) else str(a.get('content'))
                if not body.startswith(('Workflow hint', 'Current workflow data', 'Current project workflow data')):
                    continue
                parent = by_uuid.get(r.get('parentUuid')) or {}
                while parent.get('type') == 'attachment':
                    parent = by_uuid.get(parent.get('parentUuid')) or {}
                text = text_of((parent.get('message') or {}).get('content')) if parent.get('type') == 'user' else ''
                match = re.search(r'"skill":\s*"([^"]+)"', body)
                prompts.append({'ts': r.get('timestamp'), 'uuid': parent.get('uuid'), 'kind': prompt_kind(text),
                                'text': text, 'route': match.group(1) if match else None, 'context_bytes': nbytes(body)})
            elif t == 'hook_success' and a.get('hookEvent') == 'Stop' and GUARD_CMD.search(str(a.get('command'))):
                stops.append({'ts': r.get('timestamp'), 'ms': a.get('durationMs'), 'block': False})
            elif t == 'hook_blocking_error' and a.get('hookEvent') == 'Stop':
                reason = str((a.get('blockingError') or {}).get('blockingError', ''))
                if reason.startswith(('Completion guard', 'Independent check')) or 'guard' in reason[:40].lower():
                    stops.append({'ts': r.get('timestamp'), 'ms': None, 'block': True, 'reason': reason})
    steps = steps_from([(m, u, c) for m, u, c, _ in messages])
    stamps = {}
    for m, _, _, ts in messages:
        stamps.setdefault(m, ts)
    for s in steps:
        s['ts'] = stamps.get(s['id'])
        for name, inputs, tid in s['tools']:
            if name == 'Skill' and str(inputs.get('skill', '')).startswith('agentic-coding:'):
                skills.append({'skill': inputs['skill'], 'ts': s['ts'], 'request': steps.index(s)})
            if name == 'Read' and PLUGIN_PATH.search(str(inputs.get('file_path', ''))):
                reads.append({'path': inputs.get('file_path'), 'bytes': tool_results.get(tid), 'request': steps.index(s)})
    for p in prompts:
        p['requests_after'] = sum(1 for s in steps if s['ts'] and p['ts'] and s['ts'] > p['ts'])
    # file-changing calls after each guard block until the next real user prompt
    user_ts = sorted(p['ts'] for p in asked if p['kind'] == 'user' and p['ts'])
    guard_ts = sorted(s['ts'] for s in stops if s['ts'])
    for stop in (s for s in stops if s['block']):
        end = min(next((t for t in user_ts if t > stop['ts']), '9999'), next((t for t in guard_ts if t > stop['ts']), '9999'))
        after = [s for s in steps if s['ts'] and stop['ts'] < s['ts'] < end]
        stop['requests_after'] = len(after)
        stop['file_changes_after'] = sum(1 for s in after for n, i, _ in s['tools'] if changes_files(n, i))
        stop['commands_after'] = sum(1 for s in after for n, i, _ in s['tools'] if n in ('Bash', 'PowerShell'))
    side = [scan_sidechain(p) for p in sidechains]
    return {
        'session': path.stem, 'project': path.parent.name, 'cwd': head.get('cwd'), 'entrypoint': head.get('entrypoint'),
        'cli_version': head.get('version'), 'start': first_ts, 'listing': listing,
        'plugin_listed': bool(listing and listing['agentic_lines']), 'requests': len(steps),
        'sum_ctx': sum(s['ctx'] for s in steps), 'output_tokens': sum(s['output'] for s in steps),
        'subagent_requests': sum(x['requests'] for x in side), 'subagent_sum_ctx': sum(x['sum_ctx'] for x in side),
        'prompts': prompts, 'asked': asked, 'stops': stops, 'skills': skills, 'plugin_reads': reads,
        'process': process_cost(steps),
        'user_prompts': sum(1 for r in recs if r.get('type') == 'user' and isinstance((r.get('message') or {}).get('content'), str)
                            and prompt_kind(r['message']['content']) == 'user' and not r.get('isMeta')),
    }


def scan_sidechain(path):
    messages = [(m['id'], m['usage'], m.get('content')) for r in records(path) if r.get('type') == 'assistant'
                for m in [r.get('message') or {}] if m.get('id') and isinstance(m.get('usage'), dict)]
    steps = steps_from(messages)
    return {'requests': len(steps), 'sum_ctx': sum(s['ctx'] for s in steps)}


def scan_real(exclude):
    sessions, eval_like = [], Counter()
    for path in sorted(PROJECTS.glob('*/*.jsonl')):
        head = next((r for r in records(path) if r.get('entrypoint')), {})
        if head.get('entrypoint') != 'cli':
            eval_like[head.get('entrypoint')] += 1
            continue
        if path.stem in exclude:
            continue
        sidechains = sorted((path.parent / path.stem / 'subagents').glob('*.jsonl'))
        sessions.append(scan_session(path, sidechains))
    return sessions, dict(eval_like)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--exclude-session', action='append', default=[], help='in-progress session ids')
    args = parser.parse_args(argv)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    cells = scan_eval()
    (out / 'eval_cells.json').write_text(json.dumps(cells, ensure_ascii=False, indent=1), encoding='utf-8')
    sessions, eval_like = scan_real(set(args.exclude_session))
    (out / 'real_sessions.json').write_text(json.dumps({'sessions': sessions, 'non_cli_session_files': eval_like},
                                                       ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'eval cells {len(cells)} (valid {sum(c["valid"] for c in cells)}); real sessions {len(sessions)}; '
          f'non-cli files {eval_like}')


if __name__ == '__main__':
    sys.exit(main())
