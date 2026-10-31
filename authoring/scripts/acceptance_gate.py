"""Judge delegated work with acceptance tests sealed before implementation.

seal   Prove the acceptance tests fail on the base by a failed assertion (or pass, with --preserve),
       then copy them into this worktree's Git directory with their hashes. The implementer gets the
       scenario text, not the tests.
check  In a disposable checkout of the current state, install the sealed tests and run them. Then,
       from a clean copy of that state each time, revert one changed hunk and run them again: a hunk
       whose reversal fails no test is an untested change. Scenarios without a test are uncovered
       requirements. The verdict is bound to the tree that was tested; any later change needs a new
       check. After three failed checks the contract stops accepting checks until a person re-seals.
hook   Claude Code Stop hook. Silent without a sealed contract or when the current tree already has a
       full passing check; otherwise runs check and blocks the stop on failure or gate error, at most
       three blocks per contract.

Without OS-level isolation the seal detects tampering; it does not prevent it, and every verdict
says so. A pass means the stated checks pass, not that the request is complete.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

_here = Path(__file__).resolve().parent
# Beside this file (Skill scripts), or the package's scripts/ when run from hooks/.
for _candidate in (_here, _here.parent / 'scripts'):
    if (_candidate / 'probe_check.py').is_file():
        sys.path.insert(0, str(_candidate))
        break
import probe_check  # noqa: E402

STATE = 'agentic-acceptance'
MAX_FAILURES = 3
INTEGRITY = 'tamper-detection-only'
DOC_SUFFIXES = {'.md', '.markdown', '.mdx', '.rst', '.adoc'}
DEV_NULL = '/'.join(('', 'dev', 'null'))  # what Git prints for the missing side of an added or deleted file
TEST_PATH = re.compile(r'(^|/)(tests?|__tests__|spec|e2e)/|(^|/)test_[^/]*$|_test\.\w+$|\.(test|spec)\.\w+$', re.IGNORECASE)


def git(root, *args, env=None, data=None):
    result = subprocess.run(['git', '-C', str(root), '-c', 'core.quotePath=false', *args],
                            capture_output=True, env=env, input=data)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout.decode('utf-8', errors='replace')


def state_dir(root):
    """Per-worktree Git directory: outside the work tree, never committed."""
    directory = Path(git(root, 'rev-parse', '--git-dir').strip())
    return (directory if directory.is_absolute() else root / directory).resolve() / STATE


def tree_id(root):
    """Tree of the index plus every tracked and unignored change, without touching the real index."""
    with tempfile.TemporaryDirectory(prefix='acceptance-index-') as temporary:
        index = Path(temporary) / 'index'
        real = Path(git(root, 'rev-parse', '--git-path', 'index').strip())
        real = real if real.is_absolute() else root / real
        if real.is_file():
            shutil.copyfile(real, index)  # keeps force-added files the next `add -A` would skip
        env = dict(os.environ, GIT_INDEX_FILE=str(index))
        git(root, 'add', '-A', env=env)
        return git(root, 'write-tree', env=env).strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_contract(root):
    """(contract, directory, hash); contract is None when nothing is sealed. A damaged contract raises."""
    directory = state_dir(root)
    path = directory / 'contract.json'
    if not path.is_file():
        if directory.exists():
            raise ValueError(f'{directory} exists without contract.json')
        return None, directory, None
    raw = path.read_bytes()
    contract = json.loads(raw.decode('utf-8'))
    if not isinstance(contract, dict) or contract.get('schema_version') != 1 or not contract.get('tests'):
        raise ValueError('contract.json is not a sealed contract')
    return contract, directory, digest(raw)


def results(directory):
    path = directory / 'results.jsonl'
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def record(directory, result):
    with (directory / 'results.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False) + '\n')
    return result


def failures(directory, contract_hash):
    return sum(r['verdict'] != 'PASS' for r in results(directory) if r.get('contract') == contract_hash)


def install(copy, tests):
    for name, raw in tests:
        target = probe_check.relative_file(copy, name)
        if target.is_dir():
            raise ValueError(f'a directory occupies the sealed test path {name}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


def run(copy, contract, timeout):
    if contract.get('report'):
        probe_check.relative_file(copy, contract['report']).unlink(missing_ok=True)
    outcome = probe_check.run_command(copy, contract['command'], timeout)
    return outcome, probe_check.run_outcome(copy, outcome, contract.get('report'))


def seal(root, base, tests, command, report, preserve, scenarios, timeout, links):
    contract, directory, _ = load_contract(root)
    if contract is not None:
        raise ValueError(f'A contract is already sealed in {directory}; a person runs `clear` first')
    base = git(root, 'rev-parse', '--verify', base + '^{commit}').strip()
    tests = [probe_check.prove_input(root, value) for value in tests]
    names = {name for name, _ in tests}
    unknown = sorted({name for s in scenarios for name in s.get('covered_by') or []} - names)
    if unknown:
        raise ValueError('scenarios name tests that are not sealed: ' + ', '.join(unknown))
    if report:
        probe_check.relative_file(root, report, False)
    draft = {'command': command, 'report': report}
    with probe_check.worktree(root, base, links=links) as copy:
        install(copy, tests)
        outcome, verdict = run(copy, draft, timeout)
    expected = 'pass' if preserve else 'assertion_failure'
    if verdict['verdict'] != expected:
        return {'sealed': False, 'base': base, 'expected': expected, **verdict, 'tail': outcome['tail']}
    (directory / 'tests').mkdir(parents=True)
    for name, raw in tests:
        (directory / 'tests' / digest(name.encode('utf-8'))).write_bytes(raw)
    contract = {'schema_version': 1, 'base': base, 'command': command, 'report': report, 'preserve': preserve,
                'links': links, 'tests': {name: digest(raw) for name, raw in tests},
                'scenarios': scenarios, 'sealed_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    raw = (json.dumps(contract, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    (directory / 'contract.json').write_bytes(raw)
    # Keep this hash outside the worktree's reach (task record, commit trailer): a later contract with
    # another hash was replaced, which the seal alone cannot prevent.
    return {'sealed': True, 'base': base, 'contract': digest(raw), 'integrity': INTEGRITY, 'state': str(directory), **verdict}


def sealed_tests(contract, directory):
    """The sealed files, and the names whose bytes no longer match the recorded hashes."""
    tests, changed = [], []
    for name, expected in contract['tests'].items():
        path = directory / 'tests' / digest(name.encode('utf-8'))
        raw = path.read_bytes() if path.is_file() else None
        if raw is not None and digest(raw) == expected:
            tests.append((name, raw))
        else:
            changed.append(name)
    return tests, changed


def snapshot(root, copy):
    """Make the copy's index hold exactly the tested state and return its tree."""
    git(copy, 'add', '-A')
    staged = git(root, 'diff', '--cached', '--name-only', '-z', '--diff-filter=A', 'HEAD').split('\0')
    forced = [name for name in staged if name and (copy / name).is_file()]
    if forced:  # force-added files that .gitignore hides from `add -A`
        git(copy, 'add', '-f', '--', *forced)
    return git(copy, 'write-tree').strip()


def code_hunks(copy, base, exclude):
    """(file, header lines, hunk lines) for each changed text hunk, and the binary files changed."""
    patch = git(copy, 'diff', '--cached', '-U0', '--no-color', '--no-ext-diff', '--no-renames', base, '--')
    hunks, binaries, header, name, body = [], [], [], None, None
    for line in patch.splitlines(keepends=True):
        if line.startswith('diff --git '):
            header, name, body = [line], None, None
        elif body is None and line.startswith(('--- ', '+++ ')):
            header.append(line)
            path = line[4:].rstrip('\n').rstrip('\t')  # Git ends names containing spaces with a tab
            if path != DEV_NULL and (line.startswith('+++ ') or name is None):
                name = path[2:]
        elif line.startswith('Binary files '):
            match = re.search(r' and (?:b/)?(.*) differ$', line.rstrip('\n'))
            binaries.append(match.group(1) if match else line.strip())
        elif line.startswith('@@'):
            body = [line]
            hunks.append((name, header, body))
        elif body is not None:
            body.append(line)  # +, - and "\ No newline" lines up to the next hunk or file
        else:
            header.append(line)  # index and mode lines before the ---/+++ pair

    def judged(path):
        return path and path not in exclude and Path(path).suffix.lower() not in DOC_SUFFIXES and not TEST_PATH.search(path)
    return [h for h in hunks if judged(h[0])], [b for b in binaries if judged(b)]


def reset(copy, links):
    """Return the copy's work tree to its index (the tested state), dropping generated files and caches."""
    git(copy, 'checkout', '--', '.')
    git(copy, 'clean', '-fdxq', *[arg for link in links for arg in ('-e', link)])


def ablate(copy, contract, hunks, deadline, timeout, limit):
    """Revert each hunk alone from a clean copy; a hunk whose reversal leaves every sealed test passing is untested."""
    untested, unknown, judged = [], [], 0
    links = contract.get('links', [])
    for name, header, body in hunks[:limit]:
        remaining = deadline - time.monotonic()
        if remaining < 5:
            break
        judged += 1
        label = {'file': name, 'hunk': body[0].strip()}
        reset(copy, links)
        try:
            git(copy, 'apply', '-R', '--unidiff-zero', '-', data=''.join(header + body).encode('utf-8'))
        except ValueError as error:
            unknown.append(dict(label, reason=f'could not revert alone: {error}'[:200]))
            continue
        _, verdict = run(copy, contract, min(timeout, remaining))
        if verdict['verdict'] == 'pass':
            untested.append(label)
        elif verdict['verdict'] in ('timeout', 'unclassified'):
            unknown.append(dict(label, reason=verdict['reason']))
    reset(copy, links)
    return untested, unknown, len(hunks) - judged


def check(root, timeout=600, ablation=True, limit=40, deadline_seconds=1000):
    deadline = time.monotonic() + deadline_seconds
    contract, directory, contract_hash = load_contract(root)
    if contract is None:
        raise ValueError('No sealed contract for this worktree; run `seal` first')
    result = {'contract': contract_hash, 'integrity': INTEGRITY, 'ablated': ablation,
              'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'untested': [], 'unknown': [], 'skipped_hunks': 0,
              'uncovered': [s['scenario'] for s in contract.get('scenarios', []) if not s.get('covered_by')]}
    if failures(directory, contract_hash) >= MAX_FAILURES:
        return dict(result, tree=tree_id(root), verdict='STOPPED',
                    reason=f'{MAX_FAILURES} failed checks: a person re-seals (`clear`, then `seal`) or takes over')
    tests, changed = sealed_tests(contract, directory)
    if changed:
        return record(directory, dict(result, tree=tree_id(root), verdict='TAMPERED',
                                      reason='sealed tests changed: ' + ', '.join(changed)))
    links = contract.get('links', [])
    with probe_check.worktree(root, 'HEAD', current=True, links=links) as copy:
        result['tree'] = snapshot(root, copy)  # what the worker left, the tree the hook compares against
        hunks, binaries = code_hunks(copy, contract['base'], set(contract['tests']))
        install(copy, tests)  # the sealed bytes replace any copy the worker left at the same path
        git(copy, 'add', '-f', '--', *[name for name, _ in tests])  # so a reset keeps them
        outcome, verdict = run(copy, contract, min(timeout, max(1, deadline - time.monotonic())))
        result.update(outcome=verdict, tail=outcome['tail'][-600:])
        if verdict['verdict'] != 'pass':
            result.update(verdict='FAIL', reason=f'sealed tests: {verdict["verdict"]}: {verdict["reason"]}')
        else:
            result['verdict'] = 'PASS'
            result['unknown'] = [{'file': name, 'hunk': 'binary', 'reason': 'binary change is not reverted'}
                                 for name in binaries]
            result['hunks'] = len(hunks)
            if ablation:
                untested, unknown, skipped = ablate(copy, contract, hunks, deadline, timeout, limit)
                result.update(untested=untested, unknown=result['unknown'] + unknown, skipped_hunks=skipped)
    return record(directory, result)


def summary(result):
    if result['verdict'] != 'PASS':
        return f"Acceptance {result['verdict']}: {result.get('reason', '')}"
    lines = [f"Acceptance PASS: the sealed checks pass on tree {result['tree'][:12]} "
             f"(stated checks only, not request completeness; seal is {INTEGRITY})."]
    if not result.get('ablated'):
        lines.append('Strength not checked (--no-ablate).')
    if result['untested']:
        lines.append(f"{len(result['untested'])} untested change(s): reverting each fails no sealed test: " +
                     '; '.join(f"{u['file']} {u['hunk']}" for u in result['untested'][:8]))
    if result['unknown'] or result['skipped_hunks']:
        lines.append(f"{len(result['unknown'])} change(s) not judged, {result['skipped_hunks']} beyond the limit or deadline.")
    if result['uncovered']:
        lines.append(f"{len(result['uncovered'])} uncovered requirement(s): " + '; '.join(result['uncovered'][:8]))
    return '\n'.join(lines)


def hook(payload):
    if os.environ.get('AGENT_ACCEPTANCE_GATE', '').lower() == 'off':
        return {}
    cwd = payload.get('cwd')
    if not cwd:
        return {}
    try:
        root = Path(git(Path(cwd), 'rev-parse', '--show-toplevel').strip()).resolve()
    except (OSError, ValueError):
        return {}  # not a Git checkout: no contract can exist
    directory = state_dir(root)
    if not directory.exists():
        return {}
    blocks = directory / 'blocks.json'
    try:
        contract, directory, contract_hash = load_contract(root)
        tests, changed = sealed_tests(contract, directory)
        tree = tree_id(root)
        previous = next((r for r in reversed(results(directory)) if r.get('contract') == contract_hash
                         and r.get('tree') == tree and r.get('ablated')), None)
        if changed:
            result = record(directory, {'contract': contract_hash, 'tree': tree, 'verdict': 'TAMPERED',
                                        'integrity': INTEGRITY, 'reason': 'sealed tests changed: ' + ', '.join(changed)})
        else:
            result = previous or check(root, float(os.environ.get('AGENT_ACCEPTANCE_TIMEOUT', 600)),
                                       deadline_seconds=float(os.environ.get('AGENT_ACCEPTANCE_DEADLINE', 1000)))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        contract_hash, result = None, {'verdict': 'ERROR', 'reason': f'acceptance gate error: {error}'}
    if result['verdict'] == 'PASS':
        notes = summary(result)
        return {} if notes.count('\n') == 0 else {'systemMessage': notes}
    try:
        counts = json.loads(blocks.read_text(encoding='utf-8')) if blocks.is_file() else {}
    except ValueError:
        counts = {}
    key = contract_hash or 'unreadable'
    if counts.get(key, 0) >= MAX_FAILURES or result['verdict'] == 'STOPPED':
        return {'systemMessage': summary(result) + f' Stop blocked {counts.get(key, 0)} times: stopping for a person.'}
    counts[key] = counts.get(key, 0) + 1
    blocks.write_text(json.dumps(counts), encoding='utf-8')
    tail = probe_check.cell(result.get('tail', ''))[-500:]
    return {'decision': 'block', 'reason': summary(result) + (f' Output: {tail}' if tail else '') +
            f' Fix the implementation, not the sealed tests, then stop again (block {counts[key]} of {MAX_FAILURES}).'}


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_subparsers(dest='mode', required=True)
    sealing = modes.add_parser('seal')
    sealing.add_argument('--base', default='HEAD')
    sealing.add_argument('--tests', nargs='+', required=True, help='SOURCE=NAME; keep SOURCE outside the worktree')
    sealing.add_argument('--command', required=True)
    sealing.add_argument('--report', help='JUnit XML or Jest-format JSON the command writes')
    sealing.add_argument('--preserve', action='store_true', help='behavior-preserving work: tests pass on the base')
    sealing.add_argument('--scenarios', type=Path, help='JSON list of {"scenario": text, "covered_by": [test names]}')
    sealing.add_argument('--link', nargs='+', action='extend', default=[])
    checking = modes.add_parser('check')
    checking.add_argument('--no-ablate', action='store_true')
    checking.add_argument('--max-hunks', type=int, default=40)
    checking.add_argument('--deadline', type=float, default=1000, help='seconds for the whole check')
    modes.add_parser('status')
    modes.add_parser('clear')
    modes.add_parser('hook')
    for mode in (sealing, checking):
        mode.add_argument('--timeout', type=float, default=600, help='seconds for one test run')
    for name, mode in modes.choices.items():
        if name != 'hook':
            mode.add_argument('--root', type=Path, required=True)
    if argv is None:
        # The packaged hook launcher runs this file by path with no mode (or only its own name).
        argv = [arg for arg in sys.argv[1:] if not arg.endswith('acceptance_gate.py')] or ['hook']
    args = parser.parse_args(argv)
    if args.mode == 'hook':
        try:
            result = hook(json.loads(sys.stdin.buffer.read().decode('utf-8-sig')))
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            result = {'systemMessage': f'Acceptance gate unavailable; completion is unchecked: {error}'}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    try:
        root = args.root.resolve()
        if Path(git(root, 'rev-parse', '--show-toplevel').strip()).resolve() != root:
            raise ValueError('--root must be the worktree root')
        if args.mode == 'seal':
            scenarios = json.loads(args.scenarios.read_text(encoding='utf-8')) if args.scenarios else []
            if not isinstance(scenarios, list) or not all(
                    isinstance(s, dict) and isinstance(s.get('scenario'), str) and isinstance(s.get('covered_by', []), list)
                    for s in scenarios):
                raise ValueError('--scenarios must be a list of {"scenario": text, "covered_by": [names]}')
            outcome = seal(root, args.base, args.tests, args.command, args.report, args.preserve,
                           scenarios, args.timeout, args.link)
            print(json.dumps(outcome, ensure_ascii=False, indent=2))
            return 0 if outcome['sealed'] else 1
        if args.mode == 'check':
            result = check(root, args.timeout, not args.no_ablate, args.max_hunks, args.deadline)
            print(summary(result))
            return 0 if result['verdict'] == 'PASS' else 1
        if args.mode == 'status':
            contract, directory, contract_hash = load_contract(root)
            print(json.dumps({'contract': contract, 'hash': contract_hash, 'results': results(directory)[-3:]},
                             ensure_ascii=False, indent=2))
            return 0 if contract else 3
        directory = state_dir(root)  # clear: a person's decision to drop or re-seal the contract
        if directory.exists():
            shutil.rmtree(directory)
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
