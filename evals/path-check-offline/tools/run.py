"""Offline falsification of an independent verifier against known complete and partial diffs.

precheck: build every item, observe regression/hidden ground truth and the inventory, no model.
run:      for each valid item and verifier, build a fresh workspace, run the verifier, then judge.
report:   score against the criteria pre-registered in ../README.md.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import traceback

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location('delegation_runner', ROOT / 'scripts/run_delegation_eval.py')
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)
sys.path.insert(0, str(Path(__file__).parent))
import inventory  # noqa: E402

WORK_ROOT = Path('C:/e/w')
# Private copies of each project's node_modules, made from the read-only originals with robocopy.
# %TEMP%/claude/eval-deps/labeler lost package manifests and is not used.
DEPS_ROOT = Path('C:/e/deps')
SESSION_TIMEOUT = 1200
JUDGE_TIMEOUT = 600
MAX_CANDIDATE_LINES = 60
LEAK_MARKERS = ('delegation-v2', 'delegation-v1', 'Skill_Management', 'zz-eval', 'path-check-offline', 'hidden/',
                'agentic-coding/', 'memories/')
COST_LOCK = threading.Lock()


def git(repo, *args, check=True):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=check)


def load():
    items = json.loads((SUITE / 'items.json').read_text(encoding='utf-8'))
    config = runner.load_scenarios(ROOT / items['suite'])
    scenarios = {s['id']: s for s in config['scenarios']}
    cells = [{'id': f'{sid}--reference', 'scenario': sid, 'variant': 'reference'} for sid in scenarios]
    cells += [{'id': f'{sid}--partial', 'scenario': sid, 'variant': 'partial', **recipe}
              for sid, recipe in items['partials'].items()]
    return config, scenarios, sorted(cells, key=lambda c: c['id'])


def build(item, scenario, cell_dir, log_dir):
    """Clone at the pinned ref, commit any synthetic fault, leave the variant as an uncommitted diff."""
    repo = cell_dir / 'r'
    runner.clone(Path(scenario['project']), repo, ref=scenario['ref'], link_modules=False, log_dir=log_dir)
    if scenario.get('fault'):
        fault = scenario['fault']
        runner.replace_once(runner.destination(repo, fault['file']), fault['find'], fault['replace'])
        git(repo, 'add', '--', fault['file'])
        git(repo, '-c', 'user.name=dev', '-c', 'user.email=dev@invalid', 'commit', '-q', '-m', fault['commit_message'])
    reference = ROOT / 'evals/delegation-v2/reference' / f"{scenario['id']}.patch"
    if item['variant'] == 'reference' or item.get('recipe') == 'probe' or item.get('on') == 'reference':
        git(repo, 'apply', str(reference))
    if item.get('recipe') == 'patch':
        git(repo, 'apply', str(ROOT / item['patch']))
    elif item.get('recipe') == 'probe':
        probe = next(p for p in scenario['probes'] if p['name'] == item['probe'])
        runner.replace_once(runner.destination(repo, probe['file']), probe['find'], probe['replace'])
    for name in scenario.get('links', []):
        source = DEPS_ROOT / Path(scenario['project']).name / name
        private = cell_dir / 'd' / name
        private.parent.mkdir(parents=True, exist_ok=True)
        runner.copy_tree(source, private, log_dir=log_dir)
        runner.link_directory(repo / name, private)
    diff = git(repo, 'diff', '--binary', 'HEAD').stdout
    (log_dir / 'variant.diff').write_bytes(diff)
    return repo, diff


def judge(scenario, repo, log_dir):
    """Existing regression first, then hidden checks installed only now."""
    regression = runner.judged_command(scenario['regression'], repo, JUDGE_TIMEOUT, log_dir / 'regression.log')
    for check in scenario['hidden']:
        for dest, source in check['files'].items():
            target = runner.destination(repo, dest)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'evals/delegation-v2' / source, target)
    hidden = [{'name': c['name'], **runner.judged_command(c['command'], repo, JUDGE_TIMEOUT, log_dir / f'hidden{i}.log')}
              for i, c in enumerate(scenario['hidden'])]
    return {'regression_passed': regression['passed'], 'hidden_passed': all(h['passed'] for h in hidden),
            'regression': {k: regression.get(k) for k in ('exit', 'timed_out', 'wall_seconds')},
            'hidden': [{k: h.get(k) for k in ('name', 'exit', 'timed_out', 'wall_seconds')} for h in hidden]}


def valid(item, truth):
    if not truth['regression_passed']:
        return False
    return truth['hidden_passed'] if item['variant'] == 'reference' else not truth['hidden_passed']


def prompt_for(scenario, candidates):
    requests = scenario.get('prompts', [scenario.get('prompt')])
    text = '\n\n'.join(f'{i}. {r}' for i, r in enumerate(requests, 1)) if len(requests) > 1 else requests[0]
    lines = candidates.splitlines()
    if len(lines) > MAX_CANDIDATE_LINES:  # keeps the argv well below the Windows command-line limit
        candidates = '\n'.join(lines[:MAX_CANDIDATE_LINES] + [f'(이하 {len(lines) - MAX_CANDIDATE_LINES}줄 생략)'])
    template = (SUITE / 'verifier-prompt.md').read_text(encoding='utf-8')
    return template.replace('{requests}', text).replace('{candidates}', candidates)


def verdict_from(text):
    for line in reversed((text or '').strip().splitlines()):
        line = line.strip().strip('`')
        if line.startswith('{') and '"verdict"' in line:
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if data.get('verdict') in ('complete', 'incomplete'):
                return data
    return None


def claude_session(prompt, repo, log_dir, config):
    argv = runner.session_argv(['claude'], prompt, {'plugin': None}, config['disable_plugins'])
    transcript = log_dir / 'session.jsonl'
    status = runner.execute(argv, repo, SESSION_TIMEOUT, transcript)
    facts = runner.summarize_session(transcript)
    final = ''
    for line in transcript.read_text(encoding='utf-8', errors='replace').splitlines():
        event = runner.decoded(line)
        if event.get('type') == 'result':
            final = event.get('result') or ''
    return {**status, 'cost_usd': facts.get('cost_usd'), 'usage': facts.get('usage'), 'model': facts.get('model'),
            'final': final, 'transcript': transcript}


def codex_session(prompt, repo, log_dir):
    transcript, last = log_dir / 'session.jsonl', log_dir / 'last-message.txt'
    # Codex 0.160 `exec` ignores per-plugin `enabled=false` overrides (agentic-coding Skills stay listed),
    # so every plugin is disabled. Memories are off: they hold this repository's suite vocabulary.
    argv = [shutil.which('codex') or 'codex', 'exec', '--disable', 'plugins', '--disable', 'memories',
            '--sandbox', 'workspace-write', '--ephemeral',
            '--skip-git-repo-check', '--json', '-C', str(repo), '-o', str(last), '-']
    started = time.monotonic()
    with transcript.open('wb') as stdout, transcript.with_suffix('.stderr').open('wb') as stderr:
        process = subprocess.Popen(argv, cwd=repo, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
        process.stdin.write(prompt.encode('utf-8'))
        process.stdin.close()
        timed_out = False
        try:
            process.wait(timeout=SESSION_TIMEOUT)
        except subprocess.TimeoutExpired:
            timed_out = True
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            process.wait()
    final = last.read_text(encoding='utf-8', errors='replace') if last.exists() else ''
    return {'exit': process.returncode, 'timed_out': timed_out, 'wall_seconds': time.monotonic() - started,
            'cost_usd': None, 'final': final, 'transcript': transcript}


def restore_product(repo, diff, log_dir):
    """Undo verifier edits to tracked files; new (test) files stay in place."""
    if git(repo, 'diff', '--binary', 'HEAD').stdout == diff:
        return []
    changed = sorted(git(repo, 'diff', '--name-only', 'HEAD').stdout.decode().split())
    (log_dir / 'verifier-edits.diff').write_bytes(git(repo, 'diff', '--binary', 'HEAD').stdout)
    git(repo, 'checkout', '-q', 'HEAD', '--', '.')
    if diff:
        patch = log_dir / 'restore.patch'
        patch.write_bytes(diff)
        git(repo, 'apply', '--binary', str(patch))
    return changed


def cell_workspace(key):
    return WORK_ROOT / hashlib.sha256(key.encode()).hexdigest()[:8]


def run_cell(item, scenario, verifier, output, config, state):
    log_dir = output / 'cells' / item['id'] / verifier
    log_dir.mkdir(parents=True, exist_ok=True)
    cell_dir = cell_workspace(f'{output.name}/{item["id"]}/{verifier}')
    result = {'item': item['id'], 'variant': item['variant'], 'verifier': verifier, 'errors': []}
    try:
        if cell_dir.exists():
            raise RuntimeError(f'workspace exists: {cell_dir}')
        cell_dir.mkdir(parents=True)
        repo, diff = build(item, scenario, cell_dir, log_dir)
        found = inventory.inventory(repo)
        candidates = inventory.render(found)
        runner.write_json(log_dir / 'inventory.json', found)
        if verifier != 'inventory':
            prompt = prompt_for(scenario, candidates)
            (log_dir / 'prompt.md').write_text(prompt, encoding='utf-8')
            session = (claude_session(prompt, repo, log_dir, config) if verifier == 'claude'
                       else codex_session(prompt, repo, log_dir))
            runner.kill_owned(cell_dir)
            text = Path(session.pop('transcript')).read_text(encoding='utf-8', errors='replace')
            result['contamination'] = sorted(m for m in LEAK_MARKERS if m in text)
            result['session'] = {k: v for k, v in session.items() if k != 'final'}
            result['final'] = session['final'][-3000:]
            result['verdict'] = verdict_from(session['final'])
            if result['verdict'] is None and session['exit'] != 0 and not session['timed_out']:
                # A failed launch (for example HTTP 429) is not a verifier judgement; rerun it.
                result['errors'].append(f'session exited {session["exit"]} without a verdict')
            result['verifier_edited'] = restore_product(repo, diff, log_dir)
            added = git(repo, 'ls-files', '--others', '--exclude-standard').stdout.decode().split()
            result['verifier_added'] = added
            for name in added:  # keep the verifier's tests as evidence
                target = log_dir / 'added' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(repo / name, target)
            with COST_LOCK:
                state['claude_cost'] += session.get('cost_usd') or 0
        result['truth'] = judge(scenario, repo, log_dir)
        result['valid'] = valid(item, result['truth'])
        result['inventory'] = {'applicable': found['applicable'], 'candidates': len(found['candidates']),
                               'changed_symbols': found['changed_symbols'],
                               'paths': [p for c in found['candidates'] for p in c['paths']]}
    except Exception as error:
        result['errors'].append(f'{type(error).__name__}: {error}')
        (log_dir / 'error.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        if cell_dir.exists():
            try:
                runner.kill_owned(cell_dir)
                runner.remove_tree(cell_dir, WORK_ROOT)
            except Exception as error:
                result['errors'].append(f'cleanup failed: {error}')
    runner.write_json(log_dir / 'result.json', result)
    return result


def execute_matrix(cells, verifiers, output, jobs, max_cost):
    config, scenarios, _ = load()
    state = {'claude_cost': 0.0}
    results = []
    work = [(c, v) for v in verifiers for c in cells]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {}
        for cell, verifier in work:
            futures[pool.submit(guarded, cell, scenarios[cell['scenario']], verifier, output, config, state,
                                max_cost)] = (cell['id'], verifier)
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(result['item'], result['verifier'], (result.get('verdict') or {}).get('verdict'),
                  'valid' if result.get('valid') else 'INVALID', result['errors'] or '', flush=True)
    return results


def guarded(cell, scenario, verifier, output, config, state, max_cost):
    if verifier == 'claude' and state['claude_cost'] > max_cost:
        return {'item': cell['id'], 'variant': cell['variant'], 'verifier': verifier,
                'errors': [f'skipped: claude cost {state["claude_cost"]:.2f} > {max_cost}']}
    return run_cell(cell, scenario, verifier, output, config, state)


def score(results, verifier):
    rows = [r for r in results if r['verifier'] == verifier and r.get('valid') and not r['errors']]
    clean = [r for r in rows if not r.get('contamination')]
    partial = [r for r in clean if r['variant'] == 'partial']
    reference = [r for r in clean if r['variant'] == 'reference']
    flagged = lambda r: (r.get('verdict') or {}).get('verdict') == 'incomplete'
    detected, alarms = sum(map(flagged, partial)), sum(map(flagged, reference))
    need = math.ceil(0.75 * len(partial))
    costs = [r['session'].get('cost_usd') for r in rows if r.get('session', {}).get('cost_usd') is not None]
    walls = [r['session']['wall_seconds'] for r in rows if r.get('session')]
    return {'verifier': verifier, 'valid_partials': len(partial), 'detected': detected, 'needed': need,
            'valid_references': len(reference), 'false_alarms': alarms,
            'passes': bool(partial) and detected >= need and alarms <= 1,
            'contaminated': sorted(r['item'] for r in rows if r.get('contamination')),
            'missing_verdicts': sorted(r['item'] for r in clean if not r.get('verdict')),
            'verifier_edited_product': sorted(r['item'] for r in clean if r.get('verifier_edited')),
            'cost_usd': round(sum(costs), 4) if costs else None,
            'median_wall_seconds': round(sorted(walls)[len(walls) // 2], 1) if walls else None}


def inventory_recall(results):
    """Partial items whose candidate paths name a symbol the reference changed and the partial did not."""
    by_item = {r['item']: r for r in results if r['verifier'] == 'inventory' and r.get('inventory')}
    rows = []
    for item, partial in by_item.items():
        if not item.endswith('--partial'):
            continue
        reference = by_item.get(item.replace('--partial', '--reference'))
        if not reference:
            continue
        missing = set(reference['inventory']['changed_symbols']) - set(partial['inventory']['changed_symbols'])
        names = {m.split(' ')[-1] for m in missing}
        hit = any(k.split(' ')[-1] in names for path in partial['inventory']['paths'] for k in path)
        rows.append({'item': item, 'applicable': partial['inventory']['applicable'], 'missing': sorted(missing),
                     'candidates': partial['inventory']['candidates'], 'hit': hit,
                     'reference_candidates': reference['inventory']['candidates']})
    return rows


def replay(cell, scenario, verifier, output):
    """Run a verifier's saved tests on a fresh build of the same item, with no hidden files."""
    added = output / 'cells' / cell['id'] / verifier / 'added'
    tests = sorted(p.relative_to(added).as_posix() for p in added.rglob('*') if p.is_file())
    log_dir = output / 'replay' / verifier / cell['id']
    log_dir.mkdir(parents=True, exist_ok=True)
    cell_dir = cell_workspace(f'{output.name}/replay/{cell["id"]}/{verifier}')
    cell_dir.mkdir(parents=True)
    try:
        repo, _ = build(cell, scenario, cell_dir, log_dir)
        for name in tests:
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(added / name, repo / name)
        # The scenario's own runner prefix, pointed at the verifier's tests instead of its suite.
        prefix = scenario['regression'].split(' tests/')[0].split(' src/')[0]
        result = runner.check_command(f'{prefix} {" ".join(tests)}', repo, JUDGE_TIMEOUT, log_dir / 'replay.log')
        return {'item': cell['id'], 'verifier': verifier, 'tests': tests, 'passed': result['passed']}
    finally:
        runner.kill_owned(cell_dir)
        runner.remove_tree(cell_dir, WORK_ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['precheck', 'run', 'report', 'replay'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--verifier', action='append', choices=['claude', 'codex'], default=[])
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--max-cost', type=float, default=40.0)
    args = parser.parse_args()
    output = args.output.resolve()
    _, _, cells = load()
    if args.only:
        cells = [c for c in cells if c['id'] in args.only]
    if args.action == 'precheck':
        output.mkdir(parents=True, exist_ok=True)
        results = execute_matrix(cells, ['inventory'], output, args.jobs, args.max_cost)
        runner.write_json(output / 'precheck.json', results)
        bad = sorted(r['item'] for r in results if not r.get('valid'))
        print('precheck invalid:', bad or 'none')
    elif args.action == 'run':
        precheck = json.loads((output / 'precheck.json').read_text(encoding='utf-8'))
        ok = {r['item'] for r in precheck if r.get('valid') and not r['errors']}
        require = [c for c in cells if c['id'] in ok]
        if not require:
            raise SystemExit('no valid precheck items')
        results = execute_matrix(require, args.verifier, output, args.jobs, args.max_cost)
        previous = output / 'results.json'
        merged = (json.loads(previous.read_text(encoding='utf-8')) if previous.exists() else []) + results
        runner.write_json(previous, merged)
    elif args.action == 'replay':
        # Flagged reference items only: does the verifier's failing test reproduce on a fresh reference?
        config, scenarios, _ = load()
        rows = []
        for verifier in args.verifier:
            for cell in cells:
                path = output / 'cells' / cell['id'] / verifier / 'result.json'
                result = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
                if cell['variant'] == 'reference' and (result.get('verdict') or {}).get('verdict') == 'incomplete':
                    rows.append(replay(cell, scenarios[cell['scenario']], verifier, output))
                    print(json.dumps(rows[-1]), flush=True)
        runner.write_json(output / 'replay.json', rows)
    else:
        precheck = json.loads((output / 'precheck.json').read_text(encoding='utf-8'))
        # Per-cell results survive an interrupted matrix; the merged file is only written at the end.
        results = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((output / 'cells').glob('*/*/result.json'))
                   if p.parent.name != 'inventory']
        verifiers = sorted({r['verifier'] for r in results})
        report = {'precheck_invalid': sorted(r['item'] for r in precheck if not r.get('valid')),
                  'scores': [score(results, v) for v in verifiers],
                  'inventory_recall': inventory_recall(precheck),
                  'cells': [{k: r.get(k) for k in ('item', 'verifier', 'valid', 'errors', 'contamination',
                                                    'verifier_edited')} | {'verdict': r.get('verdict')}
                            for r in results]}
        runner.write_json(output / 'report.json', report)
        print(json.dumps(report['scores'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
