"""Replay candidate devices on rebuilt plugin-ON attempts. See ../README.md for the counting rules.

precheck: rebuild each attempt, replay the Stop guards, list inventory candidates (candidate B), judge.
verify:   candidate A, the shipped independent-check verifier, on each attempt that passed precheck.
retest:   run each verifier's saved tests on a fresh reference build (no hidden files).
report:   count changed attempts per candidate.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'evals/path-check-offline/tools'))
import run as offline  # noqa: E402
import inventory  # noqa: E402

runner = offline.runner
JUDGE_SUITE = ROOT / 'evals/delegation-v3'
# The plugin commit each attempt ran, and the current one, for the Stop guard replay.
GUARDS = {'0.1.87': '9f89615', '0.1.88': 'c9b6a56', '0.1.89': '987dba7', 'current': 'HEAD'}
GUARD_PATH = 'plugins/agentic-coding/hooks/completion_guard.py'


def attempts():
    return json.loads((SUITE / 'attempts.json').read_text(encoding='utf-8'))['attempts']


def scenario_for(attempt):
    config = runner.load_scenarios(JUDGE_SUITE / 'scenarios.json')
    return config, next(s for s in config['scenarios'] if s['id'] == attempt['scenario'])


def item_for(attempt, variant='attempt'):
    if variant == 'reference':
        return {'id': attempt['id'], 'variant': 'reference'}
    return {'id': attempt['id'], 'variant': 'partial', 'recipe': 'patch', 'on': 'base',
            'patch': f'evals/failure-replay/attempts/{attempt["id"]}.patch'}


def build(item, scenario, cell_dir, log_dir):
    """The offline suite's build, with the v3 reference when the attempt is replaced by its reference."""
    if item['variant'] != 'reference':
        return offline.build(item, scenario, cell_dir, log_dir)
    repo = cell_dir / 'r'
    runner.clone(Path(scenario['project']), repo, ref=scenario['ref'], link_modules=False, log_dir=log_dir)
    offline.git(repo, 'apply', str(ROOT / scenario['reference_patch']))
    for name in scenario.get('links', []):
        private = cell_dir / 'd' / name
        private.parent.mkdir(parents=True, exist_ok=True)
        runner.copy_tree(offline.DEPS_ROOT / Path(scenario['project']).name / name, private, log_dir=log_dir)
        runner.link_directory(repo / name, private)
    return repo, offline.git(repo, 'diff', '--binary', 'HEAD').stdout


def judge(scenario, repo, log_dir):
    """Existing regression, then every v3 hidden check (v2 and v3 origins reported apart)."""
    regression = runner.judged_command(scenario['regression'], repo, offline.JUDGE_TIMEOUT, log_dir / 'regression.log')
    hidden = []
    for index, check in enumerate(scenario['hidden']):
        for dest, source in check['files'].items():
            target = runner.destination(repo, dest)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(JUDGE_SUITE / source, target)
        result = runner.judged_command(check['command'], repo, offline.JUDGE_TIMEOUT, log_dir / f'hidden{index}.log')
        hidden.append({'name': check['name'], 'origin': check.get('origin'), 'passed': result['passed'],
                       'failed': failing_names(log_dir / f'hidden{index}.log', result)})
    return {'regression_passed': regression['passed'],
            'hidden_v2_passed': all(h['passed'] for h in hidden if h['origin'] == 'v2'),
            'hidden_v3_passed': all(h['passed'] for h in hidden), 'hidden': hidden}


def failing_names(log, result):
    if result['passed']:
        return []
    names = []
    for path in (log, log.with_name(log.stem + '-retry' + log.suffix)):
        if path.exists():
            text = re.sub(r'\x1b\[[0-9;]*m', '', path.read_text(encoding='utf-8', errors='replace'))
            names = [m.strip() for m in re.findall(r'^\s*(?:×|not ok \d+ -)\s*(.+?)(?:\s+\d+ms)?$', text, re.M)]
    return names


def rewritten_transcript(attempt, repo, out):
    """The attempt's transcript with its workspace paths pointing at the rebuilt repository."""
    sys.path.insert(0, str(Path(__file__).parent))
    import reconstruct
    text = ''
    for transcript in attempt['transcripts']:
        _, old_root = reconstruct.calls(transcript)
        text += reconstruct.rebase(Path(transcript).read_text(encoding='utf-8', errors='replace'), old_root, str(repo))
    out.write_text(text, encoding='utf-8')
    return out


def replay_guards(attempt, repo, log_dir):
    transcript = rewritten_transcript(attempt, repo, log_dir / 'transcript-rebased.jsonl')
    payload = json.dumps({'transcript_path': str(transcript), 'cwd': str(repo), 'stop_hook_active': False})
    results = {}
    for label in (attempt['plugin'], 'current'):
        source = offline.git(ROOT, 'show', f'{GUARDS[label]}:{GUARD_PATH}').stdout
        with tempfile.TemporaryDirectory() as folder:
            guard = Path(folder) / 'completion_guard.py'
            guard.write_bytes(source)
            done = subprocess.run([sys.executable, '-I', str(guard)], input=payload.encode('utf-8'),
                                  capture_output=True, timeout=120)
        output = json.loads(done.stdout.decode('utf-8') or '{}')
        results[label] = {'blocks': output.get('decision') == 'block', 'reason': output.get('reason', '')[:600]}
    return results


def inventory_hit(attempt, found):
    """Candidate B counts only when a listed path reaches the attempt's pre-registered missed symbol."""
    markers = attempt.get('missed_markers', [])
    paths = [' '.join(path) for c in found['candidates'] for path in c['paths']]
    return any(marker in path for marker in markers for path in paths)


def workspace(key):
    return offline.WORK_ROOT / hashlib.sha256(key.encode()).hexdigest()[:8]


def precheck(attempt, output):
    config, scenario = scenario_for(attempt)
    log_dir = output / 'precheck' / attempt['id']
    log_dir.mkdir(parents=True, exist_ok=True)
    cell = workspace(f'{output.name}/precheck/{attempt["id"]}')
    result = {'id': attempt['id'], 'kind': attempt['kind'], 'errors': []}
    try:
        cell.mkdir(parents=True)
        repo, _ = build(item_for(attempt), scenario, cell, log_dir)
        result['guards'] = replay_guards(attempt, repo, log_dir)
        found = inventory.inventory(repo)
        runner.write_json(log_dir / 'inventory.json', found)
        result['inventory'] = {'applicable': found['applicable'], 'candidates': len(found['candidates']),
                               'paths': sum(len(c['paths']) for c in found['candidates']),
                               'hit': inventory_hit(attempt, found)}
        result['truth'] = judge(scenario, repo, log_dir)
        recorded = attempt['recorded']
        result['faithful'] = (result['truth']['regression_passed'] == recorded['regression']
                              and result['truth']['hidden_v2_passed'] == recorded['hidden'])
    except Exception as error:
        result['errors'].append(f'{type(error).__name__}: {error}')
    finally:
        runner.kill_owned(cell)
        runner.remove_tree(cell, offline.WORK_ROOT)
    runner.write_json(log_dir / 'result.json', result)
    return result


def verifier_prompt(scenario, base):
    reference = (ROOT / 'authoring/references/independent-check.md').read_text(encoding='utf-8')
    template = re.search(r'```\n(INDEPENDENT VERIFIER.*?)\n```', reference, re.S).group(1)
    requests = scenario.get('prompts', [scenario.get('prompt')])
    return template.replace('<base>', base).replace('<request>', '\n\n'.join(requests))


def verify(attempt, output, state, max_cost):
    config, scenario = scenario_for(attempt)
    log_dir = output / 'verify' / attempt['id']
    log_dir.mkdir(parents=True, exist_ok=True)
    result = {'id': attempt['id'], 'kind': attempt['kind'], 'errors': []}
    if state['cost'] > max_cost:
        result['errors'].append(f'skipped: cost {state["cost"]:.2f} > {max_cost}')
        return result
    cell = workspace(f'{output.name}/verify/{attempt["id"]}')
    try:
        cell.mkdir(parents=True)
        repo, diff = build(item_for(attempt), scenario, cell, log_dir)
        base = offline.git(repo, 'rev-parse', 'HEAD').stdout.decode().strip()
        prompt = verifier_prompt(scenario, base)
        (log_dir / 'prompt.md').write_text(prompt, encoding='utf-8')
        session = offline.claude_session(prompt, repo, log_dir, config)
        runner.kill_owned(cell)
        text = Path(session.pop('transcript')).read_text(encoding='utf-8', errors='replace')
        result['contamination'] = sorted(m for m in offline.LEAK_MARKERS if m in text)
        result['session'] = {k: v for k, v in session.items() if k != 'final'}
        state['cost'] += session.get('cost_usd') or 0
        result['final'] = session['final'][-3000:]
        result['verdict'] = offline.verdict_from(session['final'])
        result['verifier_edited'] = offline.restore_product(repo, diff, log_dir)
        added = offline.git(repo, 'ls-files', '--others', '--exclude-standard').stdout.decode().split()
        result['verifier_added'] = added
        for name in added:
            target = log_dir / 'added' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / name, target)
        result['on_attempt'] = run_tests(scenario, repo, added, log_dir / 'tests-on-attempt.log')
        result['truth'] = judge(scenario, repo, log_dir)
    except Exception as error:
        result['errors'].append(f'{type(error).__name__}: {error}')
    finally:
        runner.kill_owned(cell)
        runner.remove_tree(cell, offline.WORK_ROOT)
    runner.write_json(log_dir / 'result.json', result)
    return result


def run_tests(scenario, repo, tests, log):
    tests = [t for t in tests if re.search(r'\.(test|spec)\.[cm]?[jt]sx?$', t)]
    if not tests:
        return {'tests': [], 'passed': None}
    prefix = scenario['regression'].split(' tests/')[0].split(' src/')[0]
    result = runner.check_command(f'{prefix} {" ".join(tests)}', repo, offline.JUDGE_TIMEOUT, log)
    return {'tests': tests, 'passed': result['passed'], 'failed': failing_names(log, result)}


def retest(attempt, output):
    """Do the verifier's tests pass on the reference? A test failing there encodes a reading the reference rejects."""
    config, scenario = scenario_for(attempt)
    added = output / 'verify' / attempt['id'] / 'added'
    tests = sorted(p.relative_to(added).as_posix() for p in added.rglob('*') if p.is_file()) if added.exists() else []
    log_dir = output / 'retest' / attempt['id']
    log_dir.mkdir(parents=True, exist_ok=True)
    cell = workspace(f'{output.name}/retest/{attempt["id"]}')
    result = {'id': attempt['id'], 'errors': []}
    try:
        cell.mkdir(parents=True)
        repo, _ = build(item_for(attempt, 'reference'), scenario, cell, log_dir)
        for name in tests:
            (repo / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(added / name, repo / name)
        result['on_reference'] = run_tests(scenario, repo, tests, log_dir / 'tests-on-reference.log')
    except Exception as error:
        result['errors'].append(f'{type(error).__name__}: {error}')
    finally:
        runner.kill_owned(cell)
        runner.remove_tree(cell, offline.WORK_ROOT)
    runner.write_json(log_dir / 'result.json', result)
    return result


def load(output, stage, attempt):
    path = output / stage / attempt['id'] / 'result.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def report(output):
    rows = []
    for attempt in attempts():
        pre, ver, ret = (load(output, s, attempt) for s in ('precheck', 'verify', 'retest'))
        flagged = (ver.get('verdict') or {}).get('verdict') == 'incomplete'
        on_attempt = (ver.get('on_attempt') or {}).get('passed')
        on_reference = (ret.get('on_reference') or {}).get('passed')
        failing_attempt = set((ver.get('on_attempt') or {}).get('failed') or [])
        failing_reference = set((ret.get('on_reference') or {}).get('failed') or [])
        rows.append({
            'id': attempt['id'], 'kind': attempt['kind'], 'faithful': pre.get('faithful'),
            'guard_then': (pre.get('guards') or {}).get(attempt['plugin'], {}).get('blocks'),
            'guard_current': (pre.get('guards') or {}).get('current', {}).get('blocks'),
            'inventory_hit': (pre.get('inventory') or {}).get('hit'),
            'inventory_paths': (pre.get('inventory') or {}).get('paths'),
            'verdict': (ver.get('verdict') or {}).get('verdict'),
            'violations': [v.get('path') for v in (ver.get('verdict') or {}).get('violations', [])],
            'questions': len((ver.get('verdict') or {}).get('questions', [])),
            # A: flagged with a verifier test that fails on the attempt and that the reference passes.
            'a_changed': bool(flagged and on_attempt is False and bool(failing_attempt - failing_reference)),
            'a_tests_attempt_failed': sorted(failing_attempt), 'a_tests_reference_failed': sorted(failing_reference),
            'a_reference_passed': on_reference, 'cost_usd': (ver.get('session') or {}).get('cost_usd'),
            'contamination': ver.get('contamination'), 'errors': pre.get('errors', []) + ver.get('errors', []),
        })
    valid = [r for r in rows if r['faithful']]
    summary = {}
    for kind in ('failure', 'control'):
        group = [r for r in valid if r['kind'] == kind]
        summary[kind] = {'n': len(group),
                         'guard_then_blocked': sum(bool(r['guard_then']) for r in group),
                         'guard_current_blocked': sum(bool(r['guard_current']) for r in group),
                         'b_inventory_hit': sum(bool(r['inventory_hit']) for r in group),
                         'a_flagged': sum(r['verdict'] == 'incomplete' for r in group),
                         'a_changed': sum(r['a_changed'] for r in group),
                         'a_changed_and_guard_current': sum(r['a_changed'] and bool(r['guard_current']) for r in group)}
    costs = [r['cost_usd'] for r in rows if r['cost_usd'] is not None]
    out = {'summary': summary, 'unfaithful': [r['id'] for r in rows if not r['faithful']],
           'verifier_cost_usd': round(sum(costs), 4) if costs else None, 'rows': rows}
    runner.write_json(output / 'report.json', out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['precheck', 'verify', 'retest', 'report'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--max-cost', type=float, default=30.0)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    selected = [a for a in attempts() if not args.only or a['id'] in args.only]
    state = {'cost': 0.0}
    for attempt in selected:
        if args.action == 'precheck':
            row = precheck(attempt, output)
        elif args.action == 'verify':
            if not load(output, 'precheck', attempt).get('faithful'):
                print(attempt['id'], 'skipped: precheck not faithful', flush=True)
                continue
            if load(output, 'verify', attempt).get('session'):
                print(attempt['id'], 'skipped: already verified (paid cells are never rerun)', flush=True)
                continue
            row = verify(attempt, output, state, args.max_cost)
        elif args.action == 'retest':
            row = retest(attempt, output)
        else:
            break
        print(json.dumps({k: v for k, v in row.items() if k in ('id', 'faithful', 'guards', 'inventory', 'truth',
                                                                   'verdict', 'on_attempt', 'on_reference', 'errors')},
                         ensure_ascii=False), flush=True)
    if args.action == 'report':
        print(json.dumps(report(output)['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
