"""Three-arm comparison off / on / lean. Criteria and decisions: ../README.md (committed before the first paid cell).

build:  derive the lean package from the committed plugin by exact edits (each must match once) and smoke-test it.
run:    start the delegation runner with off, on and lean (resumable; paid cells are never replayed).
report: score the pre-registered criteria from the runner's state and transcripts.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import math
import random
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
sys.dont_write_bytecode = True
PLUGIN_REF = '4bc7595'  # 0.1.95, the plugin this pre-registration measures as `on`
SCENARIOS = {'v3': ROOT / 'evals/delegation-v3/scenarios.json'}
DEPS_ROOT = Path('C:/e/deps')
REPS = 2
JOBS = 2
LEAN = 'lean'
# Skills the model can invoke on its own in 0.1.95; lean makes every Skill explicit-only.
MODEL_INVOCABLE = ('agent-workflow', 'diagnose', 'fixing-accessibility', 'recall', 'setup-project-verification')
# Stop guard: keep only the independent-check rule (and the edit sizing it uses).
GUARD_EDITS = [
    ('    pending, lines = unobserved_edits(events, root), unchecked_lines(events, root)\n',
     '    pending, lines = [], unchecked_lines(events, root)\n'),
    ('    violations = unregistered_violations(events, root)\n', '    violations = 0\n'),
    ("'or state on the card why the change is trivial.')", "'or state in the final answer why the change is trivial.')"),
]
NI_MARGIN = 0.10      # success and false-completion rate points
TOKEN_RATIO = 0.90    # lean tokens per success <= 0.90 x on
MIN_VALID = 22
ALWAYS_ON_BUDGET = 50  # tokens: median paired first-request context, lean - off
DRAWS, SEED = 10000, 7


def sha256_tree(root):
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts):
        digest.update(path.relative_to(root).as_posix().encode() + b'\0' + path.read_bytes())
    return digest.hexdigest()


def pinned_plugin(output):
    """The plugin tree at PLUGIN_REF, extracted once under output; later working-copy releases do not change it."""
    target = output / 'packages' / f'on-{PLUGIN_REF}'
    if not (target / 'agentic-coding/plugin.json').is_file():
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        archive = subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar', PLUGIN_REF, 'plugins/agentic-coding'],
                                 capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(target, filter='data')
        shutil.move(str(target / 'plugins/agentic-coding'), str(target / 'agentic-coding'))
        shutil.rmtree(target / 'plugins')
    return target / 'agentic-coding'


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


def edit_once(path, old, new):
    raw = path.read_bytes().decode('utf-8')
    crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n')
    if text.count(old) != 1:
        raise SystemExit(f'{path}: edit text matched {text.count(old)} times, expected 1')
    text = text.replace(old, new)
    path.write_bytes((text.replace('\n', '\r\n') if crlf else text).encode('utf-8'))


def build_lean(output):
    target = output / 'packages' / LEAN / 'agentic-coding'
    record_path = target.parent / 'lean.json'
    if record_path.is_file():
        return target, json.loads(record_path.read_text(encoding='utf-8'))
    if target.parent.exists():
        shutil.rmtree(target.parent)
    source = pinned_plugin(output)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__'))
    hooks_path = target / 'hooks/hooks.json'
    hooks = json.loads(hooks_path.read_text(encoding='utf-8'))
    removed_hooks = sorted(set(hooks['hooks']) - {'Stop'})
    hooks['hooks'] = {'Stop': hooks['hooks']['Stop']}
    hooks_path.write_text(json.dumps(hooks, indent=2) + '\n', encoding='utf-8')
    (target / 'hooks/workflow_context.py').unlink()
    for skill in MODEL_INVOCABLE:
        path = target / 'skills' / skill / 'SKILL.md'
        text = path.read_text(encoding='utf-8')
        description = next(line for line in text.splitlines() if line.startswith('description:'))
        edit_once(path, description + '\n', description + '\ndisable-model-invocation: true\n')
    for old, new in GUARD_EDITS:
        edit_once(target / 'hooks/completion_guard.py', old, new)
    record = {'arm': LEAN, 'source_commit': git('rev-parse', PLUGIN_REF), 'source_sha256': sha256_tree(source),
              'package_sha256': sha256_tree(target), 'removed_hooks': removed_hooks,
              'explicit_only': list(MODEL_INVOCABLE), 'guard_edits': GUARD_EDITS}
    smoke(target)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return target, record


def smoke(target):
    """The lean guard must still demand the independent check and nothing else on a synthetic edit turn."""
    work = target.parents[2] / 'smoke'
    if work.exists():
        shutil.rmtree(work)
    (work / 'repo/src').mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(work / 'repo')], check=True)
    edit = {'type': 'tool_use', 'id': 't1', 'name': 'Write',
            'input': {'file_path': str(work / 'repo/src/app.py'), 'content': ''.join(f'x{i} = {i}\n' for i in range(8))}}
    (work / 'repo/src/app.py').write_text(edit['input']['content'], encoding='utf-8')
    lines = [{'type': 'user', 'message': {'role': 'user', 'content': 'add constants'}},
             {'type': 'assistant', 'message': {'role': 'assistant', 'content': [edit]}},
             {'type': 'user', 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 't1', 'content': 'ok'}]}}]
    transcript = work / 't.jsonl'
    transcript.write_text(''.join(json.dumps(x) + '\n' for x in lines), encoding='utf-8')
    payload = {'hook_event_name': 'Stop', 'cwd': str(work / 'repo'), 'transcript_path': str(transcript), 'stop_hook_active': False}
    done = subprocess.run([sys.executable, str(target / 'hooks/completion_guard.py')], input=json.dumps(payload),
                          capture_output=True, text=True, encoding='utf-8', check=True)
    reason = json.loads(done.stdout).get('reason', '')
    if 'independent verifier' not in reason or 'after the last executed command' in reason:
        raise SystemExit(f'lean guard smoke failed: {done.stdout}')


def run(output, suite, dry_run):
    output.mkdir(parents=True, exist_ok=True)
    package, record = build_lean(output)
    argv = [sys.executable, '-B', str(ROOT / 'scripts/run_delegation_eval.py'), '--scenarios', str(SCENARIOS[suite]),
            '--output', str(output / 'runs' / suite), '--condition', 'off=off', '--condition', f'on=plugin:{pinned_plugin(output)}',
            '--condition', f'{LEAN}=plugin:{package}', '--reps', str(REPS), '--jobs', str(JOBS),
            '--deps-root', str(DEPS_ROOT), '--copy-deps', '--prune-clones']
    print(json.dumps({'lean': record, 'argv': argv}, ensure_ascii=False, indent=2), flush=True)
    return subprocess.call(argv + (['--dry-run'] if dry_run else []), cwd=ROOT)


def l5_tools():
    spec = importlib.util.spec_from_file_location('l5_run', ROOT / 'evals/l5-on-off/tools/run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def paired(cells, a, b, key):
    index = {(c['scenario'], c['rep'], c['arm']): c for c in cells}
    return [(index[(s, r, a)][key], index[(s, r, b)][key]) for (s, r, arm) in index if arm == a and (s, r, b) in index]


def mcnemar(pairs):
    b = sum(1 for x, y in pairs if y and not x)   # b: second arm only
    c = sum(1 for x, y in pairs if x and not y)   # c: first arm only
    n, k = b + c, min(b, c)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return {'first_only': c, 'second_only': b, 'exact_p': round(p, 4)}


def bootstrap(pairs, stat, draws=DRAWS, seed=SEED):
    rng = random.Random(seed)
    values = sorted(stat([rng.choice(pairs) for _ in pairs]) for _ in range(draws))
    return values[int(0.05 * draws)], values[int(0.95 * draws) - 1], values[int(0.025 * draws)], values[int(0.975 * draws) - 1]


def first_context(work):
    for path in sorted(work.glob('session[0-9]*.jsonl')):
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            usage = (event.get('message') or {}).get('usage') if isinstance(event, dict) and event.get('type') == 'assistant' else None
            if usage:
                return sum(usage.get(k) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
    return None


def report(output, suites):
    tools = l5_tools()
    cells, spent = [], 0.0
    for suite in suites:
        runs = output / 'runs' / suite
        state = json.loads((runs / 'state.json').read_text(encoding='utf-8'))
        spent += state.get('spent_usd') or 0
        for row in state['valid']:
            facts = tools.cell_facts(row, runs)
            work = runs / row['scenario'] / row['condition'] / f"rep{row['rep']}"
            cells.append(dict(facts, scenario=f"{suite}:{row['scenario']}", arm=row['condition'], rep=row['rep'],
                              first_ctx=first_context(work)))
    arms = {arm: tools.summarize([c for c in cells if c['arm'] == arm]) for arm in ('off', 'on', LEAN)}
    if not all(arms[a]['valid'] for a in arms):
        raise SystemExit('off, on and lean results are required')
    gaps = sorted(x - y for x, y in paired(cells, LEAN, 'off', 'first_ctx') if x is not None and y is not None)
    always_on = gaps[len(gaps) // 2] if gaps else None
    diff = lambda pairs: sum(int(x) - int(y) for x, y in pairs) / len(pairs)
    s_pairs, f_pairs = paired(cells, LEAN, 'on', 'success'), paired(cells, LEAN, 'on', 'false_completion')
    s_lo, _, s_lo95, s_hi95 = bootstrap(s_pairs, diff)
    _, f_hi, f_lo95, f_hi95 = bootstrap(f_pairs, diff)
    measure = 'cost' if any(arms[a]['missing_subagent_usage'] for a in arms) else 'tokens'
    t_pairs = paired(cells, LEAN, 'on', measure)
    w_pairs = paired(cells, LEAN, 'on', 'success')
    def ratio(sample_idx):
        lean = sum(t_pairs[i][0] for i in sample_idx) / max(1, sum(w_pairs[i][0] for i in sample_idx))
        on = sum(t_pairs[i][1] for i in sample_idx) / max(1, sum(w_pairs[i][1] for i in sample_idx))
        return lean / on if on else math.inf
    rng = random.Random(SEED)
    ratios = sorted(ratio([rng.randrange(len(t_pairs)) for _ in t_pairs]) for _ in range(DRAWS))
    point = ratio(range(len(t_pairs)))
    criteria = {
        'V': all(arms[a]['valid'] >= MIN_VALID for a in arms),
        'NI-S': s_lo > -NI_MARGIN,
        'NI-F': f_hi < NI_MARGIN,
        'T': point <= TOKEN_RATIO and ratios[int(0.95 * DRAWS) - 1] < 1.0,
        'B': always_on is not None and always_on <= ALWAYS_ON_BUDGET,
    }
    valid_per_arm = len(suites) * MIN_VALID
    criteria['V'] = all(arms[a]['valid'] >= valid_per_arm for a in arms)
    if not criteria['V']:
        decision = 'no decision: repair the cause and rerun only the invalid cells'
    elif criteria['NI-S'] and criteria['NI-F'] and criteria['T'] and criteria['B']:
        decision = ('adopt lean as the default package' if 'h' in suites
                    else 'interim: build lean as a candidate; ship only after H confirms')
    elif s_hi95 < -NI_MARGIN:
        decision = 'lean is inferior: stop; do not spend on H for this lean'
    elif criteria['NI-S'] and criteria['NI-F'] and criteria['B']:
        decision = 'adopt lean only if its per-success ratio <= 1.00 (simpler at no extra cost); otherwise keep on'
    else:
        decision = ('keep on; attribute each discordant pair to a removed element before changing anything'
                    if 'h' in suites else 'inconclusive on v3 alone by power: run H')
    out = {
        'suites': suites, 'always_on_lean_minus_off_tokens': always_on, 'arms': arms, 'measure_per_success': measure, 'criteria': criteria, 'decision': decision,
        'lean_vs_on': {'success': {'diff': diff(s_pairs), 'one_sided_95_lower': s_lo, 'ci95': [s_lo95, s_hi95],
                                   **mcnemar(s_pairs)},
                       'false_completion': {'diff': diff(f_pairs), 'one_sided_95_upper': f_hi, 'ci95': [f_lo95, f_hi95],
                                            **mcnemar(f_pairs)},
                       'per_success_ratio': {'point': point, 'one_sided_95_upper': ratios[int(0.95 * DRAWS) - 1]}},
        'secondary': {'lean_vs_off_success': mcnemar(paired(cells, LEAN, 'off', 'success')),
                      'on_vs_off_success': mcnemar(paired(cells, 'on', 'off', 'success')),
                      'discordant_lean_on': [c for c in cells if c['arm'] == LEAN and
                                             any(o['scenario'] == c['scenario'] and o['rep'] == c['rep'] and
                                                 o['arm'] == 'on' and o['success'] != c['success'] for o in cells)]},
        'spent_usd': spent,
    }
    (output / f"criteria-report-{'+'.join(suites)}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=['build', 'run', 'report'], default='run')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--suite', choices=sorted(SCENARIOS), default='v3', help='suite to run')
    parser.add_argument('--pool', nargs='+', choices=sorted(SCENARIOS), help='suites to score together (report)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if args.action == 'build':
        print(json.dumps(build_lean(output)[1], ensure_ascii=False, indent=2))
        return 0
    if args.action == 'report':
        report(output, args.pool or [args.suite])
        return 0
    return run(output, args.suite, args.dry_run)


if __name__ == '__main__':
    raise SystemExit(main())
