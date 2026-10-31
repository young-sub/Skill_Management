# Generated file. Do not edit directly.
# Source: authoring/scripts/risk_gate.py
# Source-SHA256: 21abeea6cd1a69139ffa67e2669ef32db60df8b3d5dd4f32b787e82d04cd2138

"""Decide how much human review a finished change needs, from rules the change cannot edit.

classify  LOW, MED or HIGH for the current tree against a base. The risk table is read from the
          base ref (`git show <base>:.harness/risk.yaml`), so a branch cannot loosen its own
          rules. LOW is positive only: every changed file belongs to a registered LOW class and
          that class's required evidence holds for the current tree and intact sealed tests.
          HIGH: a sensitive path, a modified, deleted or retyped existing test, fixture or
          expectation, a changed symbol referenced from a sensitive file (in the base or the work
          tree, symlinks followed), or a rename out of a sensitive path. Paths changed by a recent
          revert move up one tier. Everything else, including unknown paths, is MED.
recheck   For a committed candidate whose work tree is clean, merge it onto the integration tip in
          a disposable worktree, classify the merged change again (a new sensitive caller on the
          tip makes it HIGH), and run the sealed acceptance command plus any --regression
          commands there. Integrate only while the tip still equals the reported `onto`.
trailers  Commit trailers for traceability (Agent-Task, Risk, Acceptance). They do not measure
          human time or silent failures.
events    Reverts (`This reverts commit`) on the base become tasks: reproduce the reverted defect as an
          additive sealed regression. Other failure events enter the same loop by hand.
capacity  Whether another delegated task may start: open correctness questions and unmerged HIGH and
          MED branches each below a limit on the person's queue (exit 1 when one is full).

An LLM may raise a tier; nothing here lowers one. An agent's approval is never a human approval.
"""
import argparse
from fnmatch import fnmatch
import json
from pathlib import Path
import re
import subprocess
import sys

_here = Path(__file__).resolve().parent
for _candidate in (_here, _here.parent / 'scripts'):
    if (_candidate / 'acceptance_gate.py').is_file():
        sys.path.insert(0, str(_candidate))
        break
import acceptance_gate  # noqa: E402
import probe_check  # noqa: E402

TABLE = '.harness/risk.yaml'
ORDER = ['LOW', 'MED', 'HIGH']
TEST_PATH = acceptance_gate.TEST_PATH
FIXTURE_PATH = re.compile(r'(^|/)(fixtures?|snapshots?|__snapshots__|golden|expected|expectations?|baselines?)(/|$)|'
                          r'\.snap$', re.IGNORECASE)
# Declarations on changed lines (def/function/class/const/let/var/type, any indent) and module-level
# assignments (`LIMIT = 10`, unindented, so local variables do not make every change HIGH).
SYMBOL = re.compile(r'^[+-](?:\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?'
                    r'(?:def|function|class|const|let|var|interface|type|func|fn)\s+([A-Za-z_]\w+)|'
                    r'([A-Za-z_]\w+)\s*(?::[^=\n]*)?=(?!=))', re.MULTILINE)
# The enclosing declaration Git prints after a hunk header, including `const f = (...) =>`.
HUNK_SYMBOL = re.compile(r'^@@[^@]*@@\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?'
                         r'(?:(?:def|function|class|const|let|var|func|fn)\s+([A-Za-z_]\w+)|([A-Za-z_]\w+)\s*[=(:])',
                         re.MULTILINE)
EVIDENCE = {'acceptance-pass', 'no-untested', 'no-uncovered', 'sealed-additions'}


def git(root, *args, check=True):
    result = subprocess.run(['git', '-C', str(root), '-c', 'core.quotePath=false', *args], capture_output=True)
    if check and result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout.decode('utf-8', errors='replace')


def matches(path, patterns):
    return any(fnmatch(path, pattern) or fnmatch('/' + path, pattern) for pattern in patterns)


def load_table(root, base):
    """The risk table as committed on the base ref; a missing table makes every change MED or HIGH."""
    text = git(root, 'show', f'{base}:{TABLE}', check=False)
    if not text.strip():
        return {'schema_version': 1, 'low': [], 'high': {'paths': []}}
    table = json.loads(text)
    if table.get('schema_version') != 1 or not isinstance(table.get('low'), list) or not isinstance(table.get('high'), dict):
        raise ValueError(f'{TABLE} on {base} needs schema_version 1, a low list and a high object')
    for entry in table['low']:
        if not entry.get('id') or not entry.get('paths') or set(entry.get('requires', [])) - EVIDENCE:
            raise ValueError(f'LOW class needs id, paths and requires within {sorted(EVIDENCE)}: {entry}')
        if not isinstance(entry.get('additive_only', False), bool):
            raise ValueError(f'additive_only must be true or false: {entry}')
    return table


def changes(root, base, tree=None):
    """(status, old path, new path) for a tree (default: the current one) against base."""
    tree = tree or acceptance_gate.tree_id(root)
    rows = git(root, 'diff', '--name-status', '-z', '-M', base, tree).split('\0')
    result, index = [], 0
    while index < len(rows) - 1:
        status = rows[index]
        if status.startswith(('R', 'C')):
            result.append((status[0], rows[index + 1], rows[index + 2]))
            index += 3
        elif status:
            result.append((status[0], rows[index + 1], rows[index + 1]))
            index += 2
        else:
            index += 1
    return result, tree


def changed_symbols(root, base, tree, paths):
    patch = git(root, 'diff', '-U0', '--no-color', base, tree, '--', *paths) if paths else ''
    found = {name for pair in SYMBOL.findall(patch) + HUNK_SYMBOL.findall(patch) for name in pair if name}
    return sorted(found)


def sensitive_reference(root, base, symbols, high):
    """(symbol, file) when a sensitive file in the base or the work tree names a changed symbol."""
    if not symbols or not high:
        return None
    words = re.compile(r'\b(' + '|'.join(map(re.escape, symbols)) + r')\b')
    current = {line for line in git(root, 'ls-files', '-co', '--exclude-standard').splitlines() if matches(line, high)}
    for name in sorted(current):
        try:
            text = (root / name).read_text(encoding='utf-8', errors='replace')  # follows symlinks
        except OSError:
            continue
        hit = words.search(text)
        if hit:
            return hit.group(1), name
    for name in sorted(line for line in git(root, 'ls-tree', '-r', '--name-only', base).splitlines() if matches(line, high)):
        hit = words.search(git(root, 'show', f'{base}:{name}', check=False))
        if hit:
            return hit.group(1), name
    return None


def reverted_paths(root, base, days):
    """Paths changed by commits titled `Revert ...` on the base within the window."""
    log = git(root, 'log', base, f'--since={days}.days', '--format=%x00%s', '--name-only', check=False)
    paths = set()
    for record in log.split('\0'):
        lines = [line for line in record.splitlines() if line.strip()]
        if lines and lines[0].startswith('Revert'):
            paths.update(lines[1:])
    return paths


def evidence(root, added=()):
    """What the latest full sealed-acceptance result for the current tree establishes, with intact tests.
    `sealed-additions` holds when every file in `added` is byte-identical to a sealed test."""
    contract, directory, contract_hash = acceptance_gate.load_contract(root)
    if contract is None:
        return set(), None
    tests, changed = acceptance_gate.sealed_tests(contract, directory)
    if changed:
        return set(), {'verdict': 'TAMPERED', 'untested': [], 'uncovered': []}
    sealed = dict(tests)
    tree = acceptance_gate.tree_id(root)
    latest = next((r for r in reversed(acceptance_gate.results(directory))
                   if r.get('tree') == tree and r.get('contract') == contract_hash and r.get('ablated')), None)
    held = set()
    if latest and latest['verdict'] == 'PASS':
        held.add('acceptance-pass')
        if not latest['untested'] and not latest['unknown'] and not latest['skipped_hunks']:
            held.add('no-untested')
        if not latest['uncovered']:
            held.add('no-uncovered')
        if all(name in sealed and (root / name).is_file() and (root / name).read_bytes() == sealed[name] for name in added):
            held.add('sealed-additions')
    return held, latest


def high_reasons(root, base, rows, tree, high):
    reasons = []
    for status, old, new in rows:
        if matches(new, high) or matches(old, high):
            reasons.append(f'HIGH sensitive path: {new if matches(new, high) else old}')
        if status in 'MDRT' and (TEST_PATH.search(old) or FIXTURE_PATH.search(old)):
            reasons.append(f'HIGH existing test or fixture {"deleted" if status == "D" else "changed"}: {old}')
    symbols = changed_symbols(root, base, tree, [new for _, _, new in rows if not matches(new, high)])
    referenced = sensitive_reference(root, base, symbols, high)
    if referenced:
        reasons.append(f'HIGH changed symbol {referenced[0]} is referenced from a sensitive file: {referenced[1]}')
    return reasons


def commit(root, ref):
    """The commit a ref names; an unknown ref is an error, never an empty history."""
    return git(root, 'rev-parse', '--verify', '--quiet', ref + '^{commit}').strip() or None


def require(root, ref):
    found = commit(root, ref) if ref else None
    if not found:
        raise ValueError(f'unknown ref: {ref}')
    return found


def classify(root, base, revert_days=30, tree=None, with_evidence=True):
    require(root, base)
    table = load_table(root, base)
    rows, tree = changes(root, base, tree)
    if not rows:
        return {'tier': 'LOW', 'tree': tree, 'reasons': ['no change'], 'files': []}
    high = table['high'].get('paths', [])
    reasons, tier = high_reasons(root, base, rows, tree, high), 'MED'
    if reasons:
        tier = 'HIGH'
    else:
        classes = [next((c for c in table['low'] if matches(new, c['paths']) and (status != 'R' or matches(old, c['paths']))
                         and (status == 'A' or not c.get('additive_only'))), None) for status, old, new in rows]
        added = [new for (_, _, new), c in zip(rows, classes) if c and c.get('additive_only')]
        held = evidence(root, added)[0] if with_evidence else set()
        if all(classes):
            missing = sorted({need for c in classes for need in c.get('requires', [])} - held)
            if missing:
                reasons.append('MED LOW class evidence missing: ' + ', '.join(missing))
            else:
                tier = 'LOW'
                reasons.append('LOW classes: ' + ', '.join(sorted({c['id'] for c in classes})))
        else:
            unknown = [new for (_, _, new), c in zip(rows, classes) if not c]
            reasons.append('MED not in a registered LOW class: ' + ', '.join(unknown[:5]))
    reverted = reverted_paths(root, base, revert_days) & ({new for _, _, new in rows} | {old for _, old, _ in rows})
    if reverted and tier != 'HIGH':
        tier = ORDER[ORDER.index(tier) + 1]
        reasons.append(f'{tier} raised: reverted within {revert_days} days: ' + ', '.join(sorted(reverted)[:5]))
    return {'tier': tier, 'tree': tree, 'reasons': reasons, 'files': [new for _, _, new in rows]}


def recheck(root, candidate, onto, timeout, regressions=()):
    """Merge a committed candidate onto the integration tip; reclassify and rerun the sealed and regression checks."""
    contract, directory, _ = acceptance_gate.load_contract(root)
    if contract is None:
        raise ValueError('No sealed contract: LOW integration needs one')
    tests, changed = acceptance_gate.sealed_tests(contract, directory)
    if changed:
        return {'verdict': 'TAMPERED', 'reason': 'sealed tests changed: ' + ', '.join(changed)}
    candidate = git(root, 'rev-parse', '--verify', candidate + '^{commit}').strip()
    if candidate == git(root, 'rev-parse', 'HEAD').strip() and acceptance_gate.tree_id(root) != git(
            root, 'rev-parse', 'HEAD^{tree}').strip():
        raise ValueError('The work tree differs from the candidate commit: commit first, then recheck')
    onto = git(root, 'rev-parse', '--verify', onto + '^{commit}').strip()
    with probe_check.worktree(root, onto, links=contract.get('links', [])) as copy:
        merged = subprocess.run(['git', '-C', str(copy), '-c', 'user.name=risk-gate', '-c', 'user.email=risk-gate@invalid',
                                 'merge', '--no-ff', '--no-edit', candidate], capture_output=True)
        if merged.returncode:
            return {'verdict': 'CONFLICT', 'onto': onto, 'reason': merged.stdout.decode('utf-8', 'replace')[-400:]}
        tier = classify(copy, onto, tree=git(copy, 'rev-parse', 'HEAD^{tree}').strip(), with_evidence=False)
        result = {'onto': onto, 'candidate': candidate, 'merged_tier_reasons': tier['reasons']}
        if tier['tier'] == 'HIGH':
            return dict(result, verdict='HIGH', reason='on the integration tip the change is HIGH: ' + '; '.join(tier['reasons'][:3]))
        acceptance_gate.install(copy, tests)
        _, outcome = acceptance_gate.run(copy, contract, timeout)
        if outcome['verdict'] != 'pass':
            return dict(result, verdict='FAIL', reason=f'sealed tests: {outcome["reason"]}')
        for command in regressions:
            ran = probe_check.run_command(copy, command, timeout)
            if ran['timeout'] or ran['exit'] != 0:
                return dict(result, verdict='FAIL', reason=f'regression `{command}` exit {ran["exit"]}: {ran["tail"][-300:]}')
    return dict(result, verdict='PASS', reason='sealed and regression checks pass on the merged tree')


def task_trailers(root, sha):
    """Agent-Task values of a commit, or of every commit a merge brought in."""
    parents = git(root, 'rev-list', '--parents', '-n', '1', sha).split()[1:]
    span = [f'{parents[0]}..{parents[1]}'] if len(parents) > 1 else ['-1', sha]
    values = git(root, 'log', *span, '--format=%(trailers:key=Agent-Task,valueonly)').split()
    return sorted(set(values))


def events(root, base, days):
    """Reverts on the base within the window, as tasks: each needs an additive regression that fails on the
    reverted change. A revert is a commit whose message says `This reverts commit <sha>` (git revert), not a
    subject that starts with "Revert". Integration-check failures, repeated review findings and user
    corrections are not detected here; they enter the same loop by hand."""
    require(root, base)
    tasks = []
    for sha in git(root, 'log', base, f'--since={days}.days', '--format=%H').split():
        body = git(root, 'log', '-1', '--format=%B', sha)
        reverted = re.search(r'This reverts commit ([0-9a-f]{7,40})', body)
        if not reverted:
            continue
        source = commit(root, reverted.group(1))
        paths = [p for p in git(root, 'show', '--format=', '--name-only', '-m', '--first-parent', sha).splitlines() if p]
        tasks.append({'event': 'revert', 'commit': sha, 'reverted': source or reverted.group(1),
                      'agent_tasks': task_trailers(root, source) if source else [], 'paths': sorted(set(paths)),
                      'action': 'reproduce the reverted defect as a new acceptance test (it must fail on the reverted '
                                'change), seal it, then register a probe; an additive sealed test is LOW, editing existing '
                                'tests, probes, lint configuration, risk.yaml or rule files is HIGH'})
    return tasks


OPEN_ITEM = re.compile(r'^(?:[-*+]|\d+[.)])\s+(?!\[[xX]\])')


def capacity(root, onto, limits):
    """Whether another delegated task may start: open correctness questions and unmerged HIGH/MED work each stay
    below their limit. A limit bounds the person's queue; it does not remove the bottleneck."""
    require(root, onto)
    decisions = root / '.harness/decisions.md'
    questions, section = 0, None
    if decisions.is_file():
        for line in decisions.read_text(encoding='utf-8').splitlines():
            if line.startswith('#'):
                section = line.lstrip('#').strip().lower()
            elif section == 'open questions' and OPEN_ITEM.match(line):  # top-level, unchecked items only
                questions += 1
    tiers = {'HIGH': 0, 'MED': 0}
    for branch in git(root, 'for-each-ref', '--format=%(refname:short)', 'refs/heads').split():
        found = set(git(root, 'log', f'{onto}..{branch}', '--format=%(trailers:key=Risk,valueonly)').split())
        for tier in ('HIGH', 'MED'):  # a branch counts once, at its highest unmerged tier
            if tier in found:
                tiers[tier] += 1
                break
    counts = {'open_questions': questions, 'unmerged_high': tiers['HIGH'], 'unmerged_med': tiers['MED']}
    full = [name for name, value in counts.items() if value >= limits[name]]
    return {'start': not full, 'counts': counts, 'limits': limits, 'full': full}


def trailers(root, base, task):
    decided = classify(root, base)
    _, latest = evidence(root)
    acceptance = 'none' if latest is None else latest['verdict'].lower() + (
        f" untested={len(latest['untested'])} uncovered={len(latest['uncovered'])}" if latest['verdict'] == 'PASS' else '')
    return [f'Agent-Task: {task}', f"Risk: {decided['tier']}", f'Acceptance: {acceptance}']


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_subparsers(dest='mode', required=True)
    classifying = modes.add_parser('classify')
    classifying.add_argument('--revert-days', type=int, default=30)
    rechecking = modes.add_parser('recheck')
    rechecking.add_argument('--candidate', default='HEAD')
    rechecking.add_argument('--onto', required=True, help='integration branch tip, for example origin/main')
    rechecking.add_argument('--regression', action='append', default=[], help='affected check command; repeatable')
    rechecking.add_argument('--timeout', type=float, default=600)
    tagging = modes.add_parser('trailers')
    tagging.add_argument('--task', required=True)
    listing = modes.add_parser('events')
    listing.add_argument('--days', type=int, default=30)
    gating = modes.add_parser('capacity')
    gating.add_argument('--onto', required=True, help='integration branch, for example origin/main')
    gating.add_argument('--max-questions', type=int, default=3)
    gating.add_argument('--max-high', type=int, default=2)
    gating.add_argument('--max-med', type=int, default=5)
    for mode in (classifying, tagging, listing):
        mode.add_argument('--base', required=True, help='the ref the risk table is read from, for example origin/main')
    for mode in modes.choices.values():
        mode.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if Path(git(root, 'rev-parse', '--show-toplevel').strip()).resolve() != root:
            raise ValueError('--root must be the worktree root')
        if args.mode == 'classify':
            decided = classify(root, args.base, args.revert_days)
            print(json.dumps(decided, ensure_ascii=False, indent=2))
            return {'LOW': 0, 'MED': 10, 'HIGH': 20}[decided['tier']]
        if args.mode == 'recheck':
            outcome = recheck(root, args.candidate, args.onto, args.timeout, args.regression)
            print(json.dumps(outcome, ensure_ascii=False, indent=2))
            return 0 if outcome['verdict'] == 'PASS' else 1
        if args.mode == 'events':
            print(json.dumps(events(root, args.base, args.days), ensure_ascii=False, indent=2))
            return 0
        if args.mode == 'capacity':
            outcome = capacity(root, args.onto, {'open_questions': args.max_questions,
                                                 'unmerged_high': args.max_high, 'unmerged_med': args.max_med})
            print(json.dumps(outcome, ensure_ascii=False, indent=2))
            return 0 if outcome['start'] else 1
        print('\n'.join(trailers(root, args.base, args.task)))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
