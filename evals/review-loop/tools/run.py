"""Paired review-loop evaluation (paid; invoke explicitly, never from unit tests).

One plugin-OFF implementation per cell, judged as `off`, then two follow-ups from the
same snapshot: `self` resumes the implementer with a re-verification request; `indep`
runs a fresh verifier on the diff, then resumes the implementer with its report.
Hidden checks are installed only for judging and removed before the next branch.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
SUITE = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('delegation_eval', ROOT / 'scripts/run_delegation_eval.py')
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)
BRANCHES = ('off', 'self', 'indep')
OFF = {'name': 'off', 'plugin': None}
SNAPSHOT_INDEX = 'review-snapshot-index'


def git(repo, *args, index=None):
    env = dict(os.environ, GIT_INDEX_FILE=str(Path(repo) / '.git' / index)) if index else None
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=True, env=env).stdout


def snapshot(repo, links):
    """Tree of the whole working state (tracked and untracked, not ignored), outside the real index."""
    (Path(repo) / '.git' / SNAPSHOT_INDEX).unlink(missing_ok=True)
    git(repo, 'add', '-A', '--', '.', *[f':(exclude){name}' for name in links], index=SNAPSHOT_INDEX)
    return git(repo, 'write-tree', index=SNAPSHOT_INDEX).decode().strip()


def restore(repo, tree, links):
    git(repo, 'reset', '-q')
    git(repo, 'checkout', '-q', '--', '.')
    git(repo, 'clean', '-fdq', *[arg for name in links for arg in ('-e', f'/{name}')])
    (Path(repo) / '.git' / SNAPSHOT_INDEX).unlink(missing_ok=True)
    git(repo, 'read-tree', tree, index=SNAPSHOT_INDEX)
    git(repo, 'checkout-index', '-a', '-f', index=SNAPSHOT_INDEX)
    for name in git(repo, 'diff-tree', '-r', '--name-only', '--diff-filter=D', 'HEAD', tree).decode().splitlines():
        (Path(repo) / name).unlink(missing_ok=True)
    runner.require(snapshot(repo, links) == tree, 'restore did not reproduce the snapshot')


def added_files(repo, tree):
    """Untracked files that are not part of the snapshot tree (for example verifier tests)."""
    known = set(git(repo, 'ls-tree', '-r', '--name-only', tree).decode().splitlines())
    current = git(repo, 'ls-files', '--others', '--exclude-standard').decode().splitlines()
    return sorted(set(current) - known)


def ignored(repo, links):
    """Ignored files outside dependency links, with size and modification time."""
    entries = git(repo, 'ls-files', '--others', '--ignored', '--exclude-standard', '--', '.',
                  *[f':(exclude){name}' for name in links]).decode().splitlines()
    found = {}
    for entry in entries:
        path = Path(repo) / entry
        if entry.split('/')[0] not in links and path.is_file():
            stat = path.stat()
            found[entry] = (stat.st_size, stat.st_mtime_ns)
    return found


def memory_dir(repo):
    key = re.sub(r'[:\\/]', '-', str(Path(repo).resolve()))
    return Path.home() / '.claude' / 'projects' / key / 'memory'


def session_id(transcript):
    for line in Path(transcript).read_text(encoding='utf-8', errors='replace').splitlines():
        event = runner.decoded(line)
        if event.get('type') == 'system' and event.get('subtype') == 'init' and event.get('session_id'):
            return event['session_id']
    return None


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


def prompt(name, **values):
    text = (SUITE / 'prompts' / f'{name}.md').read_text(encoding='utf-8')
    for key, value in values.items():
        text = text.replace('{' + key + '}', value)
    return text


def requests_text(scenario):
    requests = scenario.get('prompts', [scenario.get('prompt')])
    return '\n\n'.join(f'{i}. {r}' for i, r in enumerate(requests, 1)) if len(requests) > 1 else requests[0]


def session(argv, repo, budget, transcript, config):
    status = runner.execute(argv, repo, budget, transcript)
    facts = runner.summarize_session(transcript)
    facts.update(status)
    facts['session_id'] = session_id(transcript)
    facts['admitted_incomplete'] = any(m.casefold() in facts['answer'].casefold() for m in config['incomplete_markers'])
    facts['failed'] = status['exit'] != 0 or status['timed_out'] or not facts['result_received'] or facts['is_error']
    return facts


def judge(scenario, repo, links, timeout, log_dir, source_dir):
    """Regression, then hidden checks; afterwards remove ignored files judging created.

    Ignored files that already existed and changed (for example an agent-created log the
    judging commands append to) cannot be restored; they are returned for the record.
    """
    before = ignored(repo, links)
    regression = (runner.judged_command(scenario['regression'], repo, timeout, log_dir / 'regression.log')
                  if scenario.get('regression') else None)
    for check in scenario['hidden']:
        for dest, source in check['files'].items():
            target = runner.destination(repo, dest)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_dir / runner.relative_path(source), target)
    hidden = [{'name': c['name'], 'origin': c.get('origin', 'v2'),
               **runner.judged_command(c['command'], repo, timeout, log_dir / f'hidden{i}.log')}
              for i, c in enumerate(scenario['hidden'])]
    after = ignored(repo, links)
    for entry in sorted(set(after) - set(before)):  # e.g. runner logs that would name hidden tests
        (Path(repo) / entry).unlink(missing_ok=True)
    changed = sorted(e for e in set(after) & set(before) if after[e] != before[e])
    return regression, hidden, changed


def outcome(scenario, regression, hidden, answer_session, errors, timed_out):
    regression_ok = regression is None and 'regression' not in scenario or bool(regression and regression['passed'])
    passed = lambda origin=None: all(h['passed'] for h in hidden if origin is None or h['origin'] == origin)
    complete = len(hidden) == len(scenario['hidden'])
    success = complete and passed() and regression_ok and not errors and not timed_out
    admitted = bool(answer_session and answer_session['admitted_incomplete'])
    return {'regression_passed': regression_ok, 'hidden_passed': complete and passed(),
            'v2_hidden_passed': complete and passed('v2'), 'verified_success': success,
            'v2_verified_success': complete and passed('v2') and regression_ok and not errors and not timed_out,
            'false_completion': not errors and not timed_out and not admitted and not success,
            'admitted_incomplete': admitted}


def slim(facts):
    return {k: facts.get(k) for k in ('session_id', 'model', 'cost_usd', 'turns', 'duration_s', 'usage', 'exit',
                                      'timed_out', 'failed', 'admitted_incomplete', 'stop_blocks', 'plugin_skills')} | {
        'answer': facts.get('answer', '')[-4000:]}


def cost(sessions):
    return runner.known_sum(s.get('cost_usd') for s in sessions)


def cell_cost(rows):
    """One implementation plus every branch's follow-ups; unknown costs count as zero for the cap."""
    if not rows:
        return 0.0
    return (cost(rows[0]['implementer']) or 0) + sum(r['extra_cost_usd'] or 0 for r in rows)


def run_cell(scenario, rep, output, command, config, args, source_dir):
    cell_out = output / scenario['id'] / f'rep{rep}'
    cell_out.mkdir(parents=True, exist_ok=True)
    rows, errors = [], []
    workspace = runner.plan_workspace(scenario, {'name': 'paired'}, rep, output, args.deps_root, True,
                                      args.work_root, args.path_limit)
    runner.write_json(cell_out / 'workspace.json', workspace)
    cell, repo = Path(workspace['directory']), Path(workspace['repo'])
    links = list(runner.dependency_sources(scenario, args.deps_root))
    budget = scenario.get('budget_seconds', args.timeout)
    created = False
    try:
        runner.require(workspace['path_budget']['fits'], 'path_budget_exceeded')
        cell.mkdir(parents=True, exist_ok=False)
        created = True
        runner.clone(Path(scenario['project']), repo, ref=scenario.get('ref'), link_modules=False, log_dir=cell_out)
        for name, source in runner.dependency_sources(scenario, args.deps_root).items():
            private = Path(workspace['dependencies'][name])
            private.parent.mkdir(parents=True, exist_ok=True)
            runner.copy_tree(source, private, args.path_limit, log_dir=cell_out)
            runner.link_directory(repo / name, private)
        if scenario.get('fault'):
            fault = scenario['fault']
            runner.replace_once(runner.destination(repo, fault['file']), fault['find'], fault['replace'])
            git(repo, 'add', '--', fault['file'])
            git(repo, '-c', 'user.name=evaluation', '-c', 'user.email=evaluation@invalid', 'commit', '-qm',
                fault['commit_message'])
        implementer = []
        for index, text in enumerate(scenario.get('prompts', [scenario.get('prompt')]), 1):
            facts = session(runner.session_argv(command, text, OFF, config['disable_plugins']), repo, budget,
                            cell_out / f'implement{index}.jsonl', config)
            implementer.append(facts)
            if facts['failed']:
                raise RuntimeError(f'implementer session {index} failed or timed out')
        runner.kill_owned(cell)
        base = snapshot(repo, links)
        (cell_out / 'implementation.diff').write_bytes(git(repo, 'diff-tree', '-p', '--binary', 'HEAD', base))
        last = implementer[-1]['session_id']
        runner.require(last, 'implementer session id missing')
        for branch in BRANCHES:
            if branch in args.skip_branch:
                continue
            log_dir = cell_out / branch
            log_dir.mkdir(exist_ok=True)
            row = {'scenario': scenario['id'], 'area': scenario['area'], 'rep': rep, 'branch': branch, 'errors': [],
                   'implementer': [slim(s) for s in implementer], 'extra': [], 'verdict': None}
            try:
                restore(repo, base, links)
                resume = command + ['--resume', last, '--fork-session']
                answer = implementer[-1]
                if branch == 'self':
                    answer = session(runner.session_argv(resume, prompt('self'), OFF, config['disable_plugins']),
                                     repo, budget, log_dir / 'self.jsonl', config)
                    row['extra'].append(slim(answer))
                elif branch == 'indep':
                    memory, parked = memory_dir(repo), log_dir / 'implementer-memory'
                    if memory.is_dir() and any(memory.iterdir()):  # the verifier must not inherit implementer notes
                        shutil.move(str(memory), parked)
                        row['implementer_memory_parked'] = True
                    try:
                        verifier = session(runner.session_argv(command, prompt('verifier', requests=requests_text(scenario)),
                                                               OFF, config['disable_plugins']),
                                           repo, budget, log_dir / 'verifier.jsonl', config)
                    finally:
                        if parked.exists():
                            shutil.move(str(parked), memory)
                    row['extra'].append(slim(verifier))
                    runner.kill_owned(cell)
                    row['verdict'] = verdict_from(verifier['answer'])
                    # Keep the verifier's new tests; undo anything it changed in the implementation.
                    tests = {name: (repo / name).read_bytes() for name in added_files(repo, base)}
                    row['verifier_edited'] = sorted(git(repo, 'diff-tree', '-r', '--name-only', base,
                                                        snapshot(repo, links)).decode().split())
                    restore(repo, base, links)
                    for name, data in tests.items():
                        (repo / name).parent.mkdir(parents=True, exist_ok=True)
                        (repo / name).write_bytes(data)
                    row['verifier_tests'] = sorted(tests)
                    if verifier['failed']:
                        row['errors'].append('verifier session failed or timed out')
                    elif (row['verdict'] or {}).get('verdict') == 'incomplete':
                        answer = session(runner.session_argv(
                            resume, prompt('fix', report=verifier['answer'][-4000:]), OFF, config['disable_plugins']),
                            repo, budget, log_dir / 'fix.jsonl', config)
                        row['extra'].append(slim(answer))
                if any(s['failed'] for s in row['extra']):
                    row['errors'].append('follow-up session failed or timed out')
                runner.kill_owned(cell)
                final = snapshot(repo, links)
                (log_dir / 'final.diff').write_bytes(git(repo, 'diff-tree', '-p', '--binary', 'HEAD', final))
                row['final_tree'] = final
                regression, hidden, row['judge_changed_ignored'] = judge(scenario, repo, links, args.timeout,
                                                                         log_dir, source_dir)
                row['regression'] = regression and {k: regression.get(k) for k in ('passed', 'exit', 'timed_out')}
                row['hidden'] = [{k: h.get(k) for k in ('name', 'origin', 'passed', 'exit', 'timed_out')} for h in hidden]
                timed_out = any(s.get('timed_out') for s in row['extra'])
                row.update(outcome(scenario, regression, hidden, answer, row['errors'], timed_out))
            except Exception as error:
                row['errors'].append(f'{type(error).__name__}: {error}')
                (log_dir / 'error.log').write_text(traceback.format_exc(), encoding='utf-8')
            row['cost_usd'] = cost(implementer + row['extra'])
            row['extra_cost_usd'] = cost(row['extra']) if row['extra'] else 0
            row['excluded'] = bool(row['errors'])
            runner.write_json(log_dir / 'result.json', row)
            rows.append(row)
    except Exception as error:
        errors.append(f'{type(error).__name__}: {error}')
        (cell_out / 'error.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        if created:
            try:
                runner.kill_owned(cell)
                runner.remove_tree(cell, Path(workspace['work_root']))
            except Exception as error:
                errors.append(f'cleanup failed: {error}')
    cell_result = {'scenario': scenario['id'], 'rep': rep, 'errors': errors, 'branches': [r['branch'] for r in rows]}
    runner.write_json(cell_out / 'cell.json', cell_result)
    return rows, cell_result


def summarize(rows):
    valid = [r for r in rows if not r['excluded']]
    pairs = {}
    for r in valid:
        pairs.setdefault((r['scenario'], r['rep']), {})[r['branch']] = r
    complete = {k: v for k, v in pairs.items() if all(b in v for b in BRANCHES)}
    by = {}
    for branch in BRANCHES:
        chosen = [v[branch] for v in complete.values()]
        by[branch] = {'pairs': len(chosen),
                      'verified_success': sum(r['verified_success'] for r in chosen),
                      'v2_verified_success': sum(r['v2_verified_success'] for r in chosen),
                      'false_completion': sum(r['false_completion'] for r in chosen),
                      'admitted_incomplete': sum(r['admitted_incomplete'] for r in chosen),
                      'cost_usd': runner.known_sum(r['cost_usd'] for r in chosen),
                      'extra_cost_usd': runner.known_sum(r['extra_cost_usd'] for r in chosen)}
    flips = {}
    for a, b in (('off', 'self'), ('off', 'indep'), ('self', 'indep')):
        gained = sum(not v[a]['verified_success'] and v[b]['verified_success'] for v in complete.values())
        lost = sum(v[a]['verified_success'] and not v[b]['verified_success'] for v in complete.values())
        flips[f'{a}->{b}'] = {'gained': gained, 'lost': lost}
    verdicts = [v['indep'].get('verdict') for v in complete.values()]
    return {'branches': by, 'flips': flips, 'pairs': len(complete),
            'incomplete_pairs': sorted(f'{s}/rep{r}' for (s, r), v in pairs.items() if (s, r) not in complete),
            'excluded': sorted(f"{r['scenario']}/rep{r['rep']}/{r['branch']}" for r in rows if r['excluded']),
            'verifier_incomplete': sum((v or {}).get('verdict') == 'incomplete' for v in verdicts)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reps', type=int, default=2)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--only', nargs='+', default=[])
    parser.add_argument('--claude', default='claude')
    parser.add_argument('--timeout', type=float, default=2400)
    parser.add_argument('--deps-root', type=Path)
    parser.add_argument('--work-root', type=Path, default=Path('C:/e/w') if os.name == 'nt' else runner.DEFAULT_WORK_ROOT)
    parser.add_argument('--path-limit', type=int, default=240)
    parser.add_argument('--max-cost', type=float, default=120.0, help='Stop launching cells once recorded cost exceeds this')
    parser.add_argument('--skip-branch', nargs='*', default=[], choices=BRANCHES)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    config = runner.load_scenarios(args.scenarios.resolve())
    command = runner.claude_command(args.claude)
    scenarios = [s for s in config['scenarios'] if not args.only or s['id'] in args.only]
    runner.require(set(args.only) <= {s['id'] for s in config['scenarios']}, 'unknown --only scenario')
    matrix = [(s, rep) for rep in range(1, args.reps + 1) for s in scenarios]
    if args.dry_run:
        print(json.dumps([{'scenario': s['id'], 'rep': rep} for s, rep in matrix], indent=2))
        return 0
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    done = {(json.loads(p.read_text(encoding='utf-8'))['scenario'], json.loads(p.read_text(encoding='utf-8'))['rep'])
            for p in output.glob('*/rep*/cell.json')}
    matrix = [(s, rep) for s, rep in matrix if (s['id'], rep) not in done]  # paid cells are never replayed
    rows = [json.loads(p.read_text(encoding='utf-8')) for p in output.glob('*/rep*/*/result.json')]
    cells = {}
    for r in rows:
        cells.setdefault((r['scenario'], r['rep']), []).append(r)
    spent = sum(cell_cost(group) for group in cells.values())
    source_dir = args.scenarios.resolve().parent
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {}
        for s, rep in matrix:
            futures[pool.submit(lambda s=s, rep=rep: (run_cell(s, rep, output, command, config, args, source_dir)
                                                      if spent <= args.max_cost else ([], None)))] = (s['id'], rep)
        for future in as_completed(futures):
            cell_rows, cell = future.result()
            rows += cell_rows
            spent += cell_cost(cell_rows)
            print('CELL', futures[future], cell and cell['errors'],
                  {r['branch']: r.get('verified_success') for r in cell_rows}, f'spent={spent:.2f}', flush=True)
    report = summarize(rows)
    report['spent_usd'] = spent
    runner.write_json(output / 'report.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
