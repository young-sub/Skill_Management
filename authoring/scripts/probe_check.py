"""Exercise checks against synthetic faults in disposable Git worktrees.

Passing probes is evidence of detection for those synthetic faults only, not a
proof of correctness. Commands and explicitly linked dependency directories are trusted.
"""
import argparse
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path, PureWindowsPath
import shutil
import signal
import subprocess
import sys
import tempfile
import time


def git(root, *args, data=None):
    result = subprocess.run(['git', '-C', str(root), *args], input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


def relative_file(root, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f'Expected a repository-relative path: {name!r}')
    name = name.replace('\\', '/')
    if (Path(name).is_absolute() or PureWindowsPath(name).root or PureWindowsPath(name).drive
            or '..' in Path(name).parts or name.split('/')[0].lower() == '.git'):
        raise ValueError(f'Expected a repository-relative path: {name!r}')
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
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
        if probe.keys() - (required | {'rule', 'origin', 'expect_detected'}):
            raise ValueError('Unknown probe fields')
        for key in required - {'command'} | (probe.keys() & {'rule', 'origin'}):
            if not isinstance(probe[key], str) or (key != 'replace' and not probe[key].strip()):
                raise ValueError(f'Probe {key} must be a nonempty string (replace may be empty)')
        if probe['id'] in seen:
            raise ValueError(f'Duplicate probe id: {probe["id"]}')
        seen.add(probe['id'])
        if probe['perspective'] not in {'business', 'architecture', 'ui'}:
            raise ValueError(f'Unknown perspective: {probe["perspective"]}')
        if type(probe.get('expect_detected', True)) is not bool:
            raise ValueError('expect_detected must be boolean')
        command = probe['command']
        if not ((isinstance(command, str) and command.strip()) or
                (isinstance(command, list) and command and
                 all(isinstance(arg, str) and arg for arg in command))):
            raise ValueError('command must be a nonempty string or argv list')
        relative_file(root, probe['file'])
    return data['probes']


def add_links(root, copy, names, created):
    for name in names:
        source, target = relative_file(root, name), relative_file(copy, name)
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
    return {'exit': None if timed_out else process.returncode,
            'seconds': round(time.monotonic() - start, 3),
            'tail': output.decode('utf-8', errors='replace')[-800:], 'timeout': timed_out}


def probe_result(copy, probe, timeout):
    result = {key: probe.get(key, '') for key in ('id', 'feature', 'rule', 'perspective', 'layer')}
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
    try:
        path.write_bytes(original.replace(find, probe['replace'].encode('utf-8'), 1))
        run = run_command(copy, probe['command'], timeout)
    finally:
        path.write_bytes(original)
    result.update({key: run[key] for key in ('exit', 'seconds', 'tail')})
    result['detected'] = not run['timeout'] and run['exit'] != 0
    result['status'] = ('TIMEOUT' if run['timeout'] else
                        'UNEXPECTED_KILL' if result['detected'] and not result['expected'] else
                        'KILLED' if result['detected'] else 'SURVIVED')
    result['reason'] = ('command timed out' if run['timeout'] else
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
    prove.add_argument('--tests', nargs='+', required=True)
    prove.add_argument('--command', required=True)
    prove.add_argument('--skip-current', action='store_true')
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
            relative_file(root, name)
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
            tests = [(name, relative_file(root, name).read_bytes()) for name in args.tests]
        actual_root = Path(os.fsdecode(git(root, 'rev-parse', '--show-toplevel')).strip()).resolve()
        if actual_root != root:
            raise ValueError('--root must be the Git repository root')
        if args.mode == 'probes':
            with worktree(root, 'HEAD', current=True, links=args.link) as copy:
                results = [probe_result(copy, probe, args.timeout) for probe in selected]
            markdown = report(results)
            if args.output:
                args.output.mkdir(parents=True, exist_ok=False)
                (args.output / 'report.json').write_text(
                    json.dumps({'schema_version': 1, 'probes': results}, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')
                (args.output / 'report.md').write_text(markdown, encoding='utf-8')
            print(markdown, end='')
            return int(any(p['status'] in {'INVALID', 'TIMEOUT'} or
                           p['detected'] != p['expected'] for p in results))
        with worktree(root, args.base, links=args.link) as copy:
            for name, raw in tests:
                target = relative_file(copy, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            base = run_command(copy, args.command, args.timeout)
        proven = not base['timeout'] and base['exit'] != 0
        print(f'# Test change proof\n\n- Base exit {base["exit"]}: ' +
              ('PROVEN' if proven else 'NOT_PROVEN'))
        if not proven:
            print(cell(base['tail']))
        passed = True
        if not args.skip_current:
            with worktree(root, 'HEAD', current=True, links=args.link) as copy:
                current = run_command(copy, args.command, args.timeout)
            passed = not current['timeout'] and current['exit'] == 0
            print(f'- Current exit {current["exit"]}: ' + ('PASS' if passed else 'FAIL'))
            if not passed:
                print(cell(current['tail']))
        return int(not (proven and passed))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
