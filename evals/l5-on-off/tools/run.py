"""Independent check ON/OFF with one ablation. Criteria and decisions: ../README.md.

run:    build the ablation package by exact-text removals, then start the delegation runner with
        off, on and the ablation (resumable; paid cells are never replayed).
report: score the pre-registered criteria from the runner's state and transcripts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
sys.dont_write_bytecode = True
SCENARIOS = ROOT / 'evals/delegation-v3/scenarios.json'
PLUGIN = ROOT / 'plugins/agentic-coding'
DEPS_ROOT = Path('C:/e/deps')
REPS = 2
JOBS = 2
VERIFIER_MARKER = 'INDEPENDENT VERIFIER'
# The ablated device: every instruction that carries it, removed by exact text (each must match once).
ABLATION = 'on-no-l4'
REMOVALS = {
    'skills/agent-workflow/SKILL.md': [(
        '3. **Fix at the owner, on every path.** List every place that writes or enforces the\n'
        '   same rule (callers, other endpoints, triggers, imports, background jobs) and cover\n'
        '   each with a check. A rule stated for all saves or all users applies to every such\n'
        '   path; exempting one (for example restore or import) is the user\'s decision, so ask\n'
        '   instead of deciding it. A guard is a fix only when that state can\n',
        '3. **Fix at the owner.** A guard is a fix only when that state can\n')],
    'skills/agent-workflow/playbooks/feature.md': [(
        '   tests, config and docs. Use existing tools and validation at trust boundaries.\n'
        '   Every entry point that creates or changes the same data obeys the same rule.\n',
        '   tests, config and docs. Use existing tools and validation at trust boundaries.\n')],
    'skills/diagnose/SKILL.md': [(
        '5. Enumerate alternate paths to the same failure class (other callers,\n'
        '   settlement/refund/retry/import paths, sibling queries repeating the rule). Prove each\n'
        '   is blocked by the regression, or record why none exists with the inspected owner\n'
        '   files (`guardrail.bypass_absence`). Register the original fault and each alternate\n'
        '   path as probes in `.harness/probes.json` (a guardrail that covers only the reported\n'
        '   path is not prevention) and run\n',
        '5. Register the original fault as a probe in `.harness/probes.json` and run\n')],
}


def sha256_tree(root):
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode() + b'\0' + path.read_bytes())
    return digest.hexdigest()


def build_ablation(output):
    target = output / 'packages' / ABLATION / 'agentic-coding'
    if target.exists():
        return target, json.loads((target.parent / 'ablation.json').read_text(encoding='utf-8'))
    shutil.copytree(PLUGIN, target)
    for name, edits in REMOVALS.items():
        path = target / name
        text = path.read_bytes().decode('utf-8')
        crlf = '\r\n' in text
        text = text.replace('\r\n', '\n')
        for old, new in edits:
            if text.count(old) != 1:
                shutil.rmtree(target.parent)
                raise SystemExit(f'{name}: removal text matched {text.count(old)} times, expected 1')
            text = text.replace(old, new)
        path.write_bytes((text.replace('\n', '\r\n') if crlf else text).encode('utf-8'))
    record = {'ablation': ABLATION, 'source': str(PLUGIN), 'source_commit': git('rev-parse', 'HEAD'),
              'source_sha256': sha256_tree(PLUGIN), 'package_sha256': sha256_tree(target),
              'removed': {name: [old for old, _ in edits] for name, edits in REMOVALS.items()}}
    (target.parent / 'ablation.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return target, record


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


def run(output, dry_run):
    output.mkdir(parents=True, exist_ok=True)
    package, record = build_ablation(output)
    argv = [sys.executable, '-B', str(ROOT / 'scripts/run_delegation_eval.py'), '--scenarios', str(SCENARIOS),
            '--output', str(output / 'runs'), '--condition', 'off=off', '--condition', f'on=plugin:{PLUGIN}',
            '--condition', f'{ABLATION}=plugin:{package}', '--reps', str(REPS), '--jobs', str(JOBS),
            '--deps-root', str(DEPS_ROOT), '--copy-deps', '--prune-clones']
    print(json.dumps({'ablation': record, 'argv': argv}, ensure_ascii=False, indent=2), flush=True)
    return subprocess.call(argv + (['--dry-run'] if dry_run else []), cwd=ROOT)


def session_facts(transcript):
    tokens = cost = model_cost = 0.0
    spawned, verifier = 0, False
    for line in Path(transcript).read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if VERIFIER_MARKER in line and event.get('type') == 'assistant':
            verifier = True
        if event.get('type') == 'result':
            usage = event.get('modelUsage') or {}
            for model in usage.values():
                tokens += sum(model.get(k) or 0 for k in ('inputTokens', 'outputTokens', 'cacheReadInputTokens',
                                                            'cacheCreationInputTokens'))
                model_cost += model.get('costUSD') or 0
            cost += event.get('total_cost_usd') or 0
            spawned += (event.get('subagent_stats') or {}).get('spawned') or 0
    return {'tokens': tokens, 'cost': cost, 'model_cost': model_cost, 'spawned': spawned, 'verifier': verifier}


def cell_facts(row, runs):
    work = runs / row['scenario'] / row['condition'] / f'rep{row["rep"]}'
    facts = [session_facts(p) for p in sorted(work.glob('session[0-9]*.jsonl'))]
    hidden = row.get('hidden') or []
    v2 = [h for h in hidden if h.get('origin', 'v2') == 'v2'] or hidden
    regression = (row.get('regression') or {}).get('passed')
    return {'scenario': row['scenario'], 'success': bool(row.get('verified_success')),
            'success_v2': bool(regression and v2 and all(h.get('passed') for h in v2)),
            'false_completion': bool(row.get('false_completion')),
            'tokens': sum(f['tokens'] for f in facts), 'cost': sum(f['cost'] for f in facts),
            'missing_subagent_usage': any(f['spawned'] and f['model_cost'] + 1e-6 < f['cost'] for f in facts),
            'l5_ran': any(f['spawned'] and f['verifier'] for f in facts)}


def summarize(cells):
    successes = sum(c['success'] for c in cells)
    tokens, cost = sum(c['tokens'] for c in cells), sum(c['cost'] for c in cells)
    return {'valid': len(cells), 'success': successes, 'success_v2': sum(c['success_v2'] for c in cells),
            'false_completion': sum(c['false_completion'] for c in cells),
            'tokens_per_success': tokens / successes if successes else None,
            'cost_per_success': cost / successes if successes else None,
            'missing_subagent_usage': any(c['missing_subagent_usage'] for c in cells),
            'l5_ran': sum(c['l5_ran'] for c in cells)}


def report(output):
    runs = output / 'runs'
    state = json.loads((runs / 'state.json').read_text(encoding='utf-8'))
    hidden_origin = {s['id']: {h['name']: h.get('origin', 'v2') for h in s['hidden']}
                     for s in json.loads(SCENARIOS.read_text(encoding='utf-8'))['scenarios']}
    by = {}
    for row in state['valid']:
        for check in row.get('hidden') or []:
            check.setdefault('origin', hidden_origin[row['scenario']].get(check.get('name'), 'v2'))
        by.setdefault(row['condition'], []).append(cell_facts(row, runs))
    s = {name: summarize(cells) for name, cells in by.items()}
    off, on, ablated = s.get('off'), s.get('on'), s.get(ABLATION)
    if not (off and on):
        raise SystemExit('off and on results are required')
    per = 'cost_per_success' if (off['missing_subagent_usage'] or on['missing_subagent_usage']) else 'tokens_per_success'
    criteria = {
        'V': all(x['valid'] >= 22 for x in (off, on) + ((ablated,) if ablated else ())),
        'H': on['success'] >= off['success'] + 3,
        'H-v2': on['success_v2'] >= off['success_v2'],
        'F': on['false_completion'] <= off['false_completion'] // 2,
        'T': bool(on[per] is not None and off[per] is not None and on[per] <= 1.20 * off[per]),
    }
    # The v3 additions came from defects a verifier found: a gain that vanishes on v2-origin checks is unconfirmed.
    v2_gain = on['success_v2'] - off['success_v2']
    guard = {'v2_origin_gain': v2_gain, 'unconfirmed': criteria['H'] and v2_gain < 3}
    if not criteria['V']:
        decision = 'no decision: repair the cause and rerun only the invalid cells'
    elif criteria['H'] and criteria['H-v2'] and criteria['F']:
        decision = ('keep L5 as the default path' if criteria['T']
                    else 'keep L5 only for requests stating a rule over all saves/users/paths; re-measure T there')
    else:
        decision = 'remove L5 from the default path; keep the reference as an explicit-only check'
    ablation = None
    if ablated:
        remove = ablated['success'] >= on['success'] - 1 and ablated['false_completion'] <= on['false_completion']
        ablation = {'name': ABLATION, 'remove_device': remove}
    out = {'conditions': s, 'measure': per, 'criteria': criteria, 'interpretation_guard': guard,
           'decision': decision, 'ablation': ablation, 'spent_usd': state.get('spent_usd')}
    (output / 'criteria-report.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=['run', 'report'], default='run')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if args.action == 'report':
        report(output)
        return 0
    return run(output, args.dry_run)


if __name__ == '__main__':
    raise SystemExit(main())
