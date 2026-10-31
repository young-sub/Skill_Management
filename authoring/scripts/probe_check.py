"""Exercise checks against synthetic faults in disposable Git worktrees.

Passing probes is evidence of detection for those synthetic faults only, not a
proof of correctness. Commands and explicitly linked dependency directories are trusted.

`prove` counts a test as proven only when it fails on the base by a failed assertion. An import,
setup or collection error, a timeout, or a nonzero exit without a readable test report proves
nothing about the behavior the test names.

In `probes`, a check that crashes (syntax or import error) did not reach an assertion and is an
ERROR, not a detection; `expect` names the failure output required instead.
"""
import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from xml.etree import ElementTree

# The first exception type named in a failure decides its kind; `Error` alone names none.
EXCEPTION_TYPE = re.compile(r'\b([A-Z]\w*(?:Error|Exception))\b')
# Without a type: pytest's rewritten `assert`, node's ERR_ASSERTION, jest/vitest expectation text.
ASSERTION_PHRASE = re.compile(r'(^|\n)\s*(E\s+)?assert\b|ERR_ASSERTION|\bexpect\(|\bexpected\b[^\n]*\b(to|but)\b',
                              re.IGNORECASE)
UNITTEST_RAN = re.compile(r'^Ran (\d+) tests? in ', re.MULTILINE)
UNITTEST_RESULT = re.compile(r'^(?:FAILED|OK) \(([^)]*)\)\s*$', re.MULTILINE)

# Output of a check that broke before any assertion ran: the fault, not the rule, failed it.
CRASH = re.compile(r'^(?:E\s+)?(?:SyntaxError|IndentationError|TabError|ModuleNotFoundError|ImportError)\b'
                   r'|error during collection|^ERROR collecting|Cannot find module|ERR_MODULE_NOT_FOUND',
                   re.M)


def git(root, *args, data=None):
    result = subprocess.run(['git', '-C', str(root), *args], input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


def relative_file(root, name, resolve=True):
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f'Expected a repository-relative path: {name!r}')
    name = name.replace('\\', '/')
    if (Path(name).is_absolute() or PureWindowsPath(name).root or PureWindowsPath(name).drive
            or '..' in Path(name).parts or name.split('/')[0].lower() == '.git'):
        raise ValueError(f'Expected a repository-relative path: {name!r}')
    path = root / name
    # A linked dependency directory may legitimately point outside; only its name must stay inside.
    if resolve and not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes repository: {name!r}')
    return path


def load_probes(root, registry):
    data = json.loads(registry.read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or set(data) != {'schema_version', 'probes'}
            or type(data['schema_version']) is not int or data['schema_version'] != 1
            or not isinstance(data['probes'], list)):
        raise ValueError('Registry requires schema_version: 1 and a probes list')
    required = {'id', 'feature', 'perspective', 'layer', 'file', 'find', 'replace', 'command'}
    seen = set()
    for probe in data['probes']:
        if not isinstance(probe, dict) or not required <= probe.keys():
            raise ValueError('Probe missing required fields: ' + ', '.join(sorted(required)))
        if probe.keys() - (required | {'rule', 'origin', 'expect_detected', 'expect'}):
            raise ValueError('Unknown probe fields')
        for key in required - {'command'} | (probe.keys() & {'rule', 'origin', 'expect'}):
            if not isinstance(probe[key], str) or (key != 'replace' and not probe[key].strip()):
                raise ValueError(f'Probe {key} must be a nonempty string (replace may be empty)')
        if probe['id'] in seen:
            raise ValueError(f'Duplicate probe id: {probe["id"]}')
        seen.add(probe['id'])
        if probe['perspective'] not in {'business', 'architecture', 'ui'}:
            raise ValueError(f'Unknown perspective: {probe["perspective"]}')
        if type(probe.get('expect_detected', True)) is not bool:
            raise ValueError('expect_detected must be boolean')
        compile_expect(probe.get('expect'))
        command = probe['command']
        if not ((isinstance(command, str) and command.strip()) or
                (isinstance(command, list) and command and
                 all(isinstance(arg, str) and arg for arg in command))):
            raise ValueError('command must be a nonempty string or argv list')
        relative_file(root, probe['file'])
    return data['probes']


def compile_expect(expect):
    try:
        return expect and re.compile(expect, re.M)
    except re.error as error:
        raise ValueError(f'expect is not a valid regular expression: {error}') from None


def failure(run, expect):
    """Return (detected, error): a nonzero exit counts only when it failed for the intended reason."""
    if run['timeout'] or run['exit'] == 0:
        return False, None
    if expect:
        if compile_expect(expect).search(run['output']):
            return True, None
        return False, f'exit {run["exit"]} without output matching expect {expect!r}'
    crash = CRASH.search(run['output'])
    if crash:
        line = run['output'][crash.start():].splitlines()[0].strip()
        return False, f'exit {run["exit"]} crashed before an assertion: {line[:200]}'
    return True, None


def add_links(root, copy, names, created):
    for name in names:
        source, target = relative_file(root, name, False), relative_file(copy, name, False)
        if not source.is_dir():
            continue
        if target.exists() or target.is_symlink():
            raise ValueError(f'Link destination already exists: {name}')
        target.parent.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(target), str(source)],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode:
                raise ValueError(result.stdout.decode('utf-8', errors='replace'))
        else:
            target.symlink_to(source, target_is_directory=True)
        created.append(target)


def is_link(path):
    if os.path.islink(path) or (hasattr(os.path, 'isjunction') and os.path.isjunction(path)):
        return True
    try:  # Junctions and other reparse points on Pythons without isjunction.
        return bool(os.lstat(path).st_file_attributes & 0x400)
    except (AttributeError, OSError):
        return False


def unlink_all_links(copy):
    """Detach every link in the copy, whoever created it, so deletion never reaches its target."""
    for directory, names, files in os.walk(copy, topdown=True, followlinks=False):
        for name in list(names) + files:
            path = os.path.join(directory, name)
            if is_link(path):
                if os.path.isdir(path) and os.name == 'nt':
                    os.rmdir(path)
                else:
                    os.unlink(path)
                if name in names:
                    names.remove(name)


@contextmanager
def worktree(root, ref, current=False, links=()):
    linked_paths = [relative_file(root, name, False).relative_to(root) for name in links]
    with tempfile.TemporaryDirectory(prefix='probe-check-') as temporary:
        copy = Path(temporary) / 'repo'
        created = []
        try:
            git(root, 'worktree', 'add', '--detach', str(copy), ref)
            if current:
                patch = git(root, 'diff', 'HEAD', '--binary', '--no-ext-diff', '--no-textconv')
                if patch:
                    git(copy, 'apply', '--binary', data=patch)
                for raw in git(root, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0'):
                    if raw:
                        name = os.fsdecode(raw)
                        if any(Path(name).is_relative_to(link) for link in linked_paths):
                            continue  # Explicit dependencies are attached by add_links, never copied.
                        source, target = relative_file(root, name), relative_file(copy, name)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
            add_links(root, copy, links, created)
            yield copy
        finally:
            try:
                # Git's force removal and rmtree can traverse Windows junctions into their targets,
                # including links a checked command created itself.
                if copy.exists():
                    unlink_all_links(copy)
                    git(root, 'worktree', 'remove', '--force', str(copy))
            finally:
                git(root, 'worktree', 'prune')


def run_command(copy, command, timeout):
    start = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    process = subprocess.Popen(command, cwd=copy, shell=isinstance(command, str),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=env, start_new_session=os.name != 'nt')
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            else:
                os.killpg(process.pid, signal.SIGKILL)
        finally:
            if process.poll() is None:
                process.kill()
        output, _ = process.communicate(timeout=5)
    text = output.decode('utf-8', errors='replace')
    return {'exit': None if timed_out else process.returncode,
            'seconds': round(time.monotonic() - start, 3),
            'output': text, 'tail': text[-800:], 'timeout': timed_out}


def is_assertion(text):
    """Whether a failure's type, message and body name a failed assertion rather than another error.

    The first exception type decides (AssertionError); without one, an assertion phrase must appear
    (pytest `assert`, node ERR_ASSERTION, jest `expect(`, `expected ... to`)."""
    text = text[:4000]
    kinds = EXCEPTION_TYPE.findall(text)
    if kinds:
        return kinds[0] == 'AssertionError'
    return bool(ASSERTION_PHRASE.search(text))


def new_counts():
    return {'tests': 0, 'skipped': 0, 'assertions': 0, 'other_failures': 0, 'errors': 0}


def junit_counts(path):
    """Tests, skipped tests, assertion failures, other failures and errors in a JUnit XML report."""
    root = ElementTree.parse(path).getroot()
    counts = new_counts()
    for case in root.iter('testcase'):
        counts['tests'] += 1
        counts['skipped'] += case.find('skipped') is not None
        for failure in case.findall('failure'):
            text = f"{failure.get('type') or ''} {failure.get('message') or ''}\n{failure.text or ''}"
            counts['assertions' if is_assertion(text) else 'other_failures'] += 1
        counts['errors'] += len(case.findall('error'))
    # A file that failed to import can appear only as an error count on its suite.
    suites = [suite for suite in root.iter('testsuite') if suite.find('testsuite') is None]
    declared = sum(int(suite.get('errors') or 0) for suite in suites if (suite.get('errors') or '0').isdigit())
    counts['errors'] = max(counts['errors'], declared)
    return counts


def jest_counts(data):
    """The same counts from a Jest-format JSON report (vitest `--reporter=json`, jest `--json`)."""
    counts = new_counts()
    for suite in data.get('testResults') or []:
        cases = suite.get('assertionResults') or []
        counts['tests'] += len(cases)
        counts['skipped'] += sum(case.get('status') in ('pending', 'skipped', 'todo', 'disabled') for case in cases)
        failed = [case for case in cases if case.get('status') == 'failed']
        for case in failed:
            counts['assertions' if is_assertion('\n'.join(map(str, case.get('failureMessages') or [])))
                   else 'other_failures'] += 1
        # A suite-level message is an import, setup or hook error unless it only repeats assertion failures.
        message = str(suite.get('message') or '').strip()
        if suite.get('status') == 'failed' and (not failed or (message and not is_assertion(message))):
            counts['errors'] += 1
    counts['errors'] = max(counts['errors'], int(data.get('numRuntimeErrorTestSuites') or 0))
    return counts


def report_counts(path):
    if path.suffix.lower() == '.json':
        return jest_counts(json.loads(path.read_text(encoding='utf-8')))
    return junit_counts(path)


def unittest_counts(output):
    """Counts from Python unittest's closing summary, or None when the output has none."""
    ran = UNITTEST_RAN.findall(output)
    if not ran:
        return None
    counts = dict(new_counts(), tests=int(ran[-1]))
    summary = UNITTEST_RESULT.findall(output)
    for part in (summary[-1].split(',') if summary else []):
        key, _, value = part.strip().partition('=')
        if value.isdigit() and key in ('failures', 'errors', 'skipped'):
            counts[{'failures': 'assertions'}.get(key, key)] = int(value)
    return counts


def run_outcome(copy, run, report=None):
    """Classify one run as pass, assertion_failure, error, timeout or unclassified.

    `report` is the JUnit XML or Jest-format JSON file the command writes, relative to the
    checkout; without it only Python unittest's own summary is read. A pass needs at least one
    executed test, and a proof needs every failure to be a failed assertion."""
    if run['timeout']:
        return {'verdict': 'timeout', 'reason': 'command timed out'}
    counts = None
    if report:
        path = relative_file(copy, report)
        if path.is_file():
            try:
                counts = report_counts(path)
            except (ElementTree.ParseError, OSError, ValueError, AttributeError) as error:
                return {'verdict': 'unclassified', 'reason': f'unreadable report {report}: {error}'}
        elif run['exit'] != 0:
            return {'verdict': 'error', 'reason': f'exit {run["exit"]} and no report {report}: setup or collection failed'}
        else:
            return {'verdict': 'unclassified', 'reason': f'exit 0 but no report {report}'}
    else:
        counts = unittest_counts(run.get('output', run['tail']))
    if counts is None:
        return {'verdict': 'unclassified', 'exit': run['exit'],
                'reason': f'exit {run["exit"]} without a test report; pass --report <junit.xml|jest.json>'}
    outcome = dict(counts, exit=run['exit'])
    failed = counts['assertions'] + counts['other_failures'] + counts['errors']
    if counts['tests'] - counts['skipped'] <= 0:
        return dict(outcome, verdict='unclassified', reason='no test executed')
    if run['exit'] == 0:
        return dict(outcome, verdict='unclassified' if failed else 'pass',
                    reason='exit 0 with failures in the report' if failed else 'passed')
    if counts['errors'] or counts['other_failures']:
        return dict(outcome, verdict='error', reason=f'{counts["errors"]} error(s) and {counts["other_failures"]} '
                    'non-assertion failure(s) such as import, setup or collection')
    if counts['assertions']:
        return dict(outcome, verdict='assertion_failure', reason=f'{counts["assertions"]} assertion failure(s)')
    return dict(outcome, verdict='error', reason=f'exit {run["exit"]} without a failed test in the report')


def prove_input(root, value):
    """`NAME` copies the repository file NAME; `SOURCE=NAME` copies SOURCE, which may be outside the repository."""
    source, separator, name = value.partition('=')
    if not separator:
        return value, relative_file(root, value).read_bytes()
    relative_file(root, name, False)
    return name, Path(source).read_bytes()


def probe_result(copy, probe, timeout, baseline=None):
    """Apply one fault and run its command; `baseline(command)` runs the command without the fault first."""
    result = {key: probe.get(key, '') for key in ('id', 'feature', 'rule', 'perspective', 'layer', 'origin')}
    result.update(detected=False, expected=probe.get('expect_detected', True),
                  status='INVALID', exit=None, seconds=0, tail='')
    path = relative_file(copy, probe['file'])
    try:
        original = path.read_bytes()
    except OSError as error:
        result['reason'] = str(error)
        return result
    find = probe['find'].encode('utf-8')
    count = original.count(find)
    if count != 1:
        result['reason'] = f'find text occurs {count} times; expected exactly once'
        return result
    clean = baseline(probe['command']) if baseline else None
    if clean and (clean['timeout'] or clean['exit'] != 0):
        result.update({key: clean[key] for key in ('exit', 'seconds', 'tail')})
        result['status'] = 'TIMEOUT' if clean['timeout'] else 'INVALID'
        result['reason'] = ('command timed out without the fault' if clean['timeout'] else
                            f'command fails without the fault (exit {clean["exit"]})')
        return result
    try:
        path.write_bytes(original.replace(find, probe['replace'].encode('utf-8'), 1))
        run = run_command(copy, probe['command'], timeout)
    finally:
        path.write_bytes(original)
    result.update({key: run[key] for key in ('exit', 'seconds', 'tail')})
    result['detected'], error = failure(run, probe.get('expect'))
    result['status'] = ('TIMEOUT' if run['timeout'] else 'ERROR' if error else
                        'UNEXPECTED_KILL' if result['detected'] and not result['expected'] else
                        'KILLED' if result['detected'] else 'SURVIVED')
    result['reason'] = ('command timed out' if run['timeout'] else error or
                        f'exit {run["exit"]}; expected detection: {result["expected"]}')
    return result


def cell(value):
    return str(value).replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')


def report(probes):
    lines = ['# Probe checks', '']
    for feature in dict.fromkeys(probe['feature'] for probe in probes):
        group = [probe for probe in probes if probe['feature'] == feature]
        layers = list(dict.fromkeys(probe['layer'] for probe in group))
        lines += [f'## {cell(feature)}', '', '| Perspective | ' + ' | '.join(map(cell, layers)) + ' |',
                  '| --- | ' + ' | '.join('---' for _ in layers) + ' |']
        for perspective in ('business', 'architecture', 'ui'):
            cells = []
            for layer in layers:
                items = [p for p in group if p['perspective'] == perspective and p['layer'] == layer]
                cells.append(f'{sum(p["detected"] for p in items)}/{len(items)}')
            lines.append('| ' + perspective + ' | ' + ' | '.join(cells) + ' |')
        lines.append('')
    # The origin's first word (independent-check, feedback, ...) shows which guardrails grew from findings.
    origins = {}
    for probe in probes:
        origins.setdefault(probe['origin'].split()[0] if probe['origin'].strip() else 'unrecorded', []).append(probe)
    lines += ['Origins: ' + ', '.join(f'{cell(origin)} {sum(p["detected"] for p in group)}/{len(group)}'
                                      for origin, group in origins.items()), '']
    for probe in probes:
        if probe['status'] != 'KILLED':
            lines.append(f'- {cell(probe["id"])} ({cell(probe["rule"])}): '
                         f'{probe["status"]} — {cell(probe["reason"])}')
            if probe['status'] == 'SURVIVED' and probe['tail']:
                lines.append('  ' + cell(probe['tail'][-300:]))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    probes = modes.add_parser('probes')
    probes.add_argument('--registry', type=Path, default=Path('.harness/probes.json'))
    probes.add_argument('--only', nargs='+', default=[])
    probes.add_argument('--output', type=Path)
    prove = modes.add_parser('prove')
    prove.add_argument('--base', required=True)
    prove.add_argument('--tests', nargs='+', required=True,
                       help='NAME (repository file) or SOURCE=NAME (SOURCE may be outside the repository)')
    prove.add_argument('--command', required=True)
    prove.add_argument('--report', help='JUnit XML or Jest-format JSON the command writes, relative to the checkout')
    prove.add_argument('--preserve', action='store_true',
                       help='behavior-preserving change: the tests must pass on the base and now')
    prove.add_argument('--skip-current', action='store_true')
    prove.add_argument('--expect', help='regex the base failure output must match')
    for mode in (probes, prove):
        mode.add_argument('--root', type=Path, required=True)
        mode.add_argument('--link', nargs='+', action='extend', default=[])
        mode.add_argument('--timeout', type=float, default=600)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError('--timeout must be positive and finite')
        for name in args.link:
            relative_file(root, name, False)
        if args.mode == 'probes':
            registry = args.registry if args.registry.is_absolute() else root / args.registry
            selected = load_probes(root, registry)
            unknown = set(args.only) - {p['id'] for p in selected}
            if unknown:
                raise ValueError('Unknown probe IDs: ' + ', '.join(sorted(unknown)))
            selected = [p for p in selected if not args.only or p['id'] in args.only]
            if args.output and (args.output.exists() or args.output.is_symlink()):
                raise ValueError('--output must not exist')
        else:
            if not args.command.strip():
                raise ValueError('--command must not be empty')
            compile_expect(args.expect)
            tests = [prove_input(root, value) for value in args.tests]
            if args.report:
                relative_file(root, args.report, False)
            if args.preserve and args.skip_current:
                raise ValueError('--preserve needs the current run; drop --skip-current')
        actual_root = Path(os.fsdecode(git(root, 'rev-parse', '--show-toplevel')).strip()).resolve()
        if actual_root != root:
            raise ValueError('--root must be the Git repository root')
        if args.mode == 'probes':
            with worktree(root, 'HEAD', current=True, links=args.link) as copy:
                clean = {}

                def baseline(command):
                    key = json.dumps(command)
                    if key not in clean:
                        clean[key] = run_command(copy, command, args.timeout)
                    return clean[key]
                results = [probe_result(copy, probe, args.timeout, baseline) for probe in selected]
            markdown = report(results)
            if args.output:
                args.output.mkdir(parents=True, exist_ok=False)
                (args.output / 'report.json').write_text(
                    json.dumps({'schema_version': 1, 'probes': results}, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')
                (args.output / 'report.md').write_text(markdown, encoding='utf-8')
            print(markdown, end='')
            return int(any(p['status'] in {'INVALID', 'TIMEOUT', 'ERROR'} or
                           p['detected'] != p['expected'] for p in results))
        def run_tests(ref, current=False):
            with worktree(root, ref, current=current, links=args.link) as copy:
                for name, raw in tests:
                    target = relative_file(copy, name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                if args.report:
                    relative_file(copy, args.report).unlink(missing_ok=True)  # never read a stale report
                run = run_command(copy, args.command, args.timeout)
                return run, run_outcome(copy, run, args.report)

        base, outcome = run_tests(args.base)
        # Preservation (refactoring): the tests must already pass on the base and still pass now.
        proven = outcome['verdict'] == ('pass' if args.preserve else 'assertion_failure')
        if proven and args.expect and not args.preserve and not compile_expect(args.expect).search(base['output']):
            proven = False
            outcome = dict(outcome, reason=f'no output matching expect {args.expect!r}')
        label = ('PRESERVED' if proven else 'NOT_PRESERVED') if args.preserve else ('PROVEN' if proven else 'NOT_PROVEN')
        print(f'# Test change proof\n\n- Base exit {base["exit"]}: {label} ({outcome["verdict"]}: {outcome["reason"]})')
        if not proven:
            print(cell(base['tail']))
        passed = True
        if not args.skip_current:
            current, now = run_tests('HEAD', current=True)
            passed = now['verdict'] == 'pass'
            print(f'- Current exit {current["exit"]}: ' + ('PASS' if passed else f'FAIL ({now["verdict"]}: {now["reason"]})'))
            if not passed:
                print(cell(current['tail']))
        return int(not (proven and passed))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
