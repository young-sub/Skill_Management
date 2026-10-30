"""Replay the UserPromptSubmit router of given plugin revisions on every recorded real prompt.

Reads real_sessions.json from scan.py, loads `request_route` from each revision with `git show` (no
plugin import side effects), and writes routes.json: one row per prompt with the recorded hook route
and each replayed route. Labels are joined from --labels when present (human-checkable judgments).
"""
import argparse
import json
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOK = 'plugins/agentic-coding/hooks/workflow_context.py'


def router(rev):
    source = subprocess.run(['git', '-C', str(ROOT), 'show', f'{rev}:{HOOK}'], capture_output=True,
                            text=True, encoding='utf-8', check=True).stdout
    module = types.ModuleType(f'route_{rev}')
    exec(compile(source, f'{rev}:{HOOK}', 'exec'), module.__dict__)
    if not hasattr(module, 'request_route'):
        return lambda prompt: 'n/a'
    return lambda prompt: (module.request_route(prompt) or {}).get('skill')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--rev', action='append', default=[])
    parser.add_argument('--labels')
    parser.add_argument('--extra', help='JSON list of {id, text, recorded} prompts outside the scan (e.g. in-progress session)')
    args = parser.parse_args(argv)
    out = Path(args.output)
    sessions = json.loads((out / 'real_sessions.json').read_text(encoding='utf-8'))['sessions']
    routers = {rev: router(rev) for rev in args.rev}
    labels = json.loads(Path(args.labels).read_text(encoding='utf-8')) if args.labels else {}
    rows = []
    for s in sessions:
        recorded = {p['uuid']: p for p in s['prompts']}
        for i, p in enumerate(s['asked']):
            if p['kind'] not in ('user', 'task-notification'):
                continue
            hook = recorded.get(p['uuid'])
            rows.append({'id': f"{s['session'][:8]}#{i}", 'session': s['session'], 'project': s['project'], 'ts': p['ts'],
                         'kind': p['kind'], 'text': p['text'],
                         'recorded': (hook or {}).get('route') if hook else 'no-hook-record',
                         'recorded_context_bytes': (hook or {}).get('context_bytes'),
                         **{f'route@{rev}': routers[rev](p['text']) for rev in routers}})
    for p in json.loads(Path(args.extra).read_text(encoding='utf-8')) if args.extra else []:
        rows.append({'id': p['id'], 'session': p.get('session'), 'project': p.get('project'), 'ts': p.get('ts'),
                     'kind': 'user', 'text': p['text'], 'recorded': p.get('recorded'), 'recorded_context_bytes': None,
                     **{f'route@{rev}': routers[rev](p['text']) for rev in routers}})
    for row in rows:
        row['label'] = labels.get(row['id'], {}).get('label')
        row['label_note'] = labels.get(row['id'], {}).get('note')
    (out / 'routes.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    for rev in routers:
        print(rev, Counter((r['kind'], r[f'route@{rev}']) for r in rows))
    print('recorded', Counter((r['kind'], r['recorded']) for r in rows))


if __name__ == '__main__':
    sys.exit(main())
