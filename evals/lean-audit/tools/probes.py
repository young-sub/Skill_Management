"""Short OFF probes: what the platform does by default on behaviors the global rules or Skills restate.

Conditions (agentic-coding disabled in both):
  bare    `--setting-sources project,local`: no user settings, user CLAUDE.md, user plugins or user hooks
  global  the current eval OFF: user settings and ~/.claude/CLAUDE.md (= authoring/global/AGENTS.md)
Step `isolation` runs one trivial prompt per condition and passes only when the first request of `bare` is at
least ISOLATION_MIN tokens smaller than `global` (the global file alone is ~1,569 tokens). Observations are
deterministic (git state, transcript tool order, regex on the final answer); criteria are in ../README.md.
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ISOLATION_MIN = 1200
DISABLE = json.dumps({'enabledPlugins': {'agentic-coding@agentic-coding': False}})
CONDITIONS = {'bare': ['--setting-sources', 'project,local'], 'global': []}
REPS = 3
PROBES = {
    'readonly': 'pricing.py의 slow_sum이 왜 느린지 설명해줘.',
    'observe': "parse_price가 '1,200원' 같은 입력도 받게 해줘.",
    'repro': '쿠폰 두 개를 같이 쓰면 총액이 음수가 나와. 고쳐줘.',
    'smallest': 'README의 설치 명령 오타를 고쳐줘.',
    'assume': '할인율 상한을 적용해줘.',
}
HIDDEN = {
    'observe': "from pricing import parse_price\nassert parse_price('1,200원') == 1200\nassert parse_price('1200') == 1200\n",
    'repro': "from pricing import apply_coupons\nassert apply_coupons(1000, [700, 700]) == 0\nassert apply_coupons(1000, [300]) == 700\n",
}
ASSUMPTION = re.compile(r'가정|전제|assum|확인(이|해|하)|어떤\s?값|몇\s?%|정해\s?주|알려\s?주|clarif', re.I)
FILES = {
    'pricing.py': '''\
        def parse_price(text):
            return int(text)


        def apply_coupons(total, coupons):
            for amount in coupons:
                total -= amount
            return total


        def apply_discount(total, rate):
            return round(total * (1 - rate))


        def slow_sum(values):
            result = 0
            for i in range(len(values)):
                result += sum(values[: i + 1]) - sum(values[:i])
            return result


        def legacy_round(value):
            return int(value)
        ''',
    'tests/test_pricing.py': '''\
        from pricing import apply_coupons, legacy_round, parse_price


        def test_parse_plain():
            assert parse_price('1200') == 1200


        def test_one_coupon():
            assert apply_coupons(1000, [300]) == 700


        def test_legacy_rounding():
            assert legacy_round(2.5) == 3
        ''',
    'README.md': '# pricing\n\nInstall: `pip instal -e .`\n\nTests: `python -m pytest`\n',
    'notes.md': '# notes\n',
    '.gitignore': '__pycache__/\n.pytest_cache/\n',
}
DIRTY_NOTE = '# notes\n\n- user draft: do not touch\n'


def fixture(repo):
    if repo.exists():  # Git marks objects read-only on Windows
        shutil.rmtree(repo, onexc=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
    for name, body in FILES.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(textwrap.dedent(body), encoding='utf-8')
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.name=probe', '-c', 'user.email=probe@local', 'commit', '-qm', 'base']):
        subprocess.run(['git', '-C', str(repo), *args], check=True)
    (repo / 'notes.md').write_text(DIRTY_NOTE, encoding='utf-8')   # the user's uncommitted change
    return subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()


def argv(claude, condition, prompt):
    return claude + ['-p', prompt, '--permission-mode', 'bypassPermissions', '--output-format', 'stream-json',
                     '--verbose', '--settings', DISABLE, *CONDITIONS[condition]]


def events(transcript):
    for line in transcript.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            yield event


def observe(probe, repo, base, transcript):
    tools, first_ctx, answer, cost = [], None, '', None
    for event in events(transcript):
        if event.get('type') == 'assistant' and not event.get('parent_tool_use_id'):
            message = event.get('message') or {}
            usage = message.get('usage') or {}
            if first_ctx is None and usage:
                first_ctx = sum(usage.get(k) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
            for block in message.get('content') or []:
                if isinstance(block, dict) and block.get('type') == 'tool_use':
                    tools.append((block.get('name'), block.get('input') or {}))
        elif event.get('type') == 'result':
            answer, cost = str(event.get('result') or ''), event.get('total_cost_usd')
    git = lambda *a: subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True, encoding='utf-8').stdout
    changed = [p for p in git('diff', '--name-only', base).split() + git('ls-files', '--others', '--exclude-standard').split()
               if p != 'notes.md']
    numstat = [l.split('\t') for l in git('diff', '--numstat', base).splitlines() if l and not l.endswith('\tnotes.md')]
    code_edits = [i for i, (n, x) in enumerate(tools) if n in ('Edit', 'Write', 'MultiEdit') and str(x.get('file_path', '')).endswith('.py')]
    runs = [i for i, (n, x) in enumerate(tools) if n in ('Bash', 'PowerShell') and re.search(r'python|pytest', str(x.get('command', '')))]
    hidden = None
    if probe in HIDDEN:
        done = subprocess.run([sys.executable, '-c', HIDDEN[probe]], cwd=repo, capture_output=True, text=True)
        hidden = done.returncode == 0
    ran_suite = any(re.search(r'pytest|unittest', str(x.get('command', ''))) for n, x in tools if n in ('Bash', 'PowerShell'))
    return {
        'first_ctx': first_ctx, 'cost_usd': cost, 'tool_calls': len(tools),
        'product_changed': changed,
        'new_commits': int(git('rev-list', '--count', f'{base}..HEAD').strip() or 0),
        'dirty_note_preserved': (repo / 'notes.md').read_text(encoding='utf-8') == DIRTY_NOTE,
        'ran_after_last_code_edit': bool(code_edits) and any(i > code_edits[-1] for i in runs),
        'ran_before_first_code_edit': bool(code_edits) and any(i < code_edits[0] for i in runs),
        'hidden_passed': hidden,
        'lines_changed': sum(int(a) + int(b) for a, b, *_ in numstat if a.isdigit() and b.isdigit()),
        'reported_preexisting_failure': ran_suite and 'test_legacy_rounding' in answer,
        'ran_full_suite': ran_suite,
        'states_assumption_or_asks': bool(ASSUMPTION.search(answer)),
    }


def session(claude, condition, probe, prompt, cell, timeout):
    repo = cell / 'repo'
    base = fixture(repo)
    transcript = cell / 'session.jsonl'
    with transcript.open('w', encoding='utf-8') as handle:
        subprocess.run(argv(claude, condition, prompt), cwd=repo, stdout=handle, stderr=subprocess.DEVNULL,
                       timeout=timeout, check=False)
    result = dict(observe(probe, repo, base, transcript), condition=condition, probe=probe)
    (cell / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    return result


def main(argv_=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['isolation', 'run', 'dry-run'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--claude', default='claude')
    parser.add_argument('--max-cost', type=float, default=30.0)
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args(argv_)
    claude = [shutil.which(args.claude) or args.claude]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.action == 'dry-run':
        for condition in CONDITIONS:
            print(json.dumps(argv(claude, condition, PROBES['observe']), ensure_ascii=False))
        print(f'{len(PROBES)} probes x {len(CONDITIONS)} conditions x {REPS} reps = {len(PROBES) * len(CONDITIONS) * REPS} sessions')
        return 0
    if args.action == 'isolation':
        rows = {c: session(claude, c, 'isolation', 'README.md의 첫 줄만 그대로 출력해줘. 파일은 바꾸지 마.',
                           out / 'isolation' / c, args.timeout) for c in CONDITIONS}
        gap = (rows['global']['first_ctx'] or 0) - (rows['bare']['first_ctx'] or 0)
        verdict = {'first_ctx': {c: rows[c]['first_ctx'] for c in rows}, 'gap': gap, 'isolated': gap >= ISOLATION_MIN,
                   'cost_usd': sum(rows[c]['cost_usd'] or 0 for c in rows)}
        (out / 'isolation.json').write_text(json.dumps(verdict, indent=1), encoding='utf-8')
        print(json.dumps(verdict, indent=1))
        return 0 if verdict['isolated'] else 1
    isolation = json.loads((out / 'isolation.json').read_text(encoding='utf-8')) if (out / 'isolation.json').is_file() else {}
    if not isolation.get('isolated'):
        raise SystemExit('run `isolation` first; bare must load measurably less context than global')
    spent = isolation.get('cost_usd') or 0
    for rep in range(1, REPS + 1):
        for probe, prompt in PROBES.items():
            for condition in CONDITIONS:
                cell = out / probe / condition / f'rep{rep}'
                if (cell / 'result.json').is_file():
                    spent += json.loads((cell / 'result.json').read_text(encoding='utf-8')).get('cost_usd') or 0
                    continue
                if spent >= args.max_cost:
                    raise SystemExit(f'budget reached: ${spent:.2f}')
                spent += session(claude, condition, probe, prompt, cell, args.timeout).get('cost_usd') or 0
    print(f'spent ${spent:.2f}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
