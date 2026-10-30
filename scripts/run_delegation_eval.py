"""Paid delegated-coding evaluation. Invoke explicitly, never from unit tests.

Unit tests must supply a fake executable; --claude also accepts a JSON argv list.
Hidden checks are installed only after all fresh sessions and mutation probes.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import traceback


_spec = importlib.util.spec_from_file_location('skill_scenarios', Path(__file__).with_name('run_skill_scenarios.py'))
_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gate)
clone, replace_once = _gate.clone, _gate.replace_once
_probe_spec = importlib.util.spec_from_file_location(
    'probe_check', Path(__file__).resolve().parents[1] / 'authoring/scripts/probe_check.py')
_probe = importlib.util.module_from_spec(_probe_spec)
_probe_spec.loader.exec_module(_probe)
TOKEN_KEYS = ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')
DEFAULT_MARKERS = ['미완료', '완료하지 못', 'could not complete', 'unable to complete']
DEFAULT_WORK_ROOT = Path(__file__).resolve().parents[1] / '.work/e'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def relative_path(value):
    require(nonempty(value), 'expected relative file path')
    parts = value.replace('\\', '/').split('/')
    require(not Path(value).is_absolute() and not re.match(r'^[A-Za-z]:', value)
            and all(p not in ('', '.', '..', '.git') for p in parts), f'unsafe path: {value}')
    return Path(*parts)


def destination(repo, value):
    path = repo / relative_path(value)
    require(path.resolve().is_relative_to(repo.resolve()), f'path leaves clone: {value}')
    return path


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value),
            f'invalid identifier: {value!r}')


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def load_scenarios(path):
    """Validate the entire input before starting even the first paid session."""
    data = json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(data, dict) and type(data.get('schema_version')) is int
            and data['schema_version'] == 1, 'schema_version must be 1')
    for key, default in [('disable_plugins', ['agentic-coding@agentic-coding']),
                         ('incomplete_markers', DEFAULT_MARKERS)]:
        data.setdefault(key, default)
        require(isinstance(data[key], list) and all(nonempty(v) for v in data[key]), f'invalid {key}')
    scenarios = data.get('scenarios')
    require(isinstance(scenarios, list) and bool(scenarios), 'scenarios must be a nonempty list')
    ids = set()
    for s in scenarios:
        require(isinstance(s, dict), 'scenario must be an object')
        identifier(s.get('id'))
        require(s['id'].casefold() not in ids, 'duplicate scenario id')
        ids.add(s['id'].casefold())
        require(s.get('area') in ('FE', 'BE', 'Domain', 'Fullstack', 'Feedback', 'UI', 'Sequence'), 'invalid area')
        require(('prompt' in s) != ('prompts' in s), 'provide prompt OR prompts')
        prompts = [s['prompt']] if 'prompt' in s else s['prompts']
        require(isinstance(prompts, list) and bool(prompts) and all(nonempty(p) for p in prompts), 'invalid prompts')
        require(nonempty(s.get('project')), 'project is required')
        project = Path(s['project'])
        if not project.is_absolute():
            project = path.parent / project
        s['project'] = str(project.resolve())
        require(project.is_dir(), f'project missing: {project}')
        require(subprocess.run(['git', '-C', str(project), 'rev-parse', '--git-dir'],
                               capture_output=True).returncode == 0, f'not a git repository: {project}')
        if 'ref' in s:
            require(nonempty(s['ref']) and not s['ref'].startswith('-'), 'invalid ref')
            resolved = subprocess.run(['git', '-C', str(project), 'rev-parse', '--verify', s['ref'] + '^{commit}'],
                                      capture_output=True, text=True, encoding='utf-8')
            require(resolved.returncode == 0, 'ref does not name a commit')
            s['ref'] = resolved.stdout.strip()
        require('budget_seconds' not in s or positive(s['budget_seconds']), 'invalid budget_seconds')
        require('regression' not in s or nonempty(s['regression']), 'invalid regression')
        require(isinstance(s.get('links', []), list), 'links must be a list')
        for link in s.get('links', []):
            require(len(relative_path(link).parts) == 1, 'links must be directory names')
            require((project / link).is_dir(), f'link source missing: {link}')
        fault = s.get('fault')
        require('fault' not in s or isinstance(fault, dict), 'invalid fault')
        entries = ([fault] if fault else [])
        probes = s.get('probes', [])
        require(isinstance(probes, list), 'probes must be a list')
        for probe in probes:
            require(isinstance(probe, dict) and nonempty(probe.get('name'))
                    and nonempty(probe.get('command')), 'invalid probe')
        for entry in entries + probes:
            relative_path(entry.get('file'))
            require(nonempty(entry.get('find')) and isinstance(entry.get('replace'), str), 'invalid replacement')
        if fault is not None:
            require(nonempty(fault.get('commit_message')), 'fault needs commit_message')
        hidden = s.get('hidden')
        require(isinstance(hidden, list) and bool(hidden), 'hidden must be a nonempty list')
        for check in hidden:
            require(isinstance(check, dict) and nonempty(check.get('name'))
                    and nonempty(check.get('command')) and check.get('expect') == 'pass', 'invalid hidden check')
            require(isinstance(check.get('files'), dict), 'hidden files must be an object')
            for dest, source in check['files'].items():
                relative_path(dest)
                source = path.parent / relative_path(source)
                require(source.is_file(), f'hidden source missing: {source}')
        linked = set(s.get('links', [])) | {'node_modules'}
        for name in [e['file'] for e in entries + probes] + [d for h in hidden for d in h['files']]:
            require(relative_path(name).parts[0] not in linked, 'cannot write through linked directory')
    return data


def parse_conditions(values):
    conditions = []
    for value in values:
        require('=' in value, 'condition must be NAME=SPEC')
        name, spec = value.split('=', 1)
        identifier(name)
        require(name.casefold() not in {c['name'].casefold() for c in conditions}, 'duplicate condition')
        plugin = None
        if spec.startswith('plugin:'):
            require(bool(spec[7:]), 'plugin path is required')
            plugin = Path(spec[7:]).resolve()
            require(plugin.is_dir() and any((plugin / f).is_file() for f in
                    ('.claude-plugin/plugin.json', 'plugin.json')), 'plugin manifest missing')
        else:
            require(spec == 'off', 'condition spec must be off or plugin:<directory>')
        conditions.append({'name': name, 'plugin': str(plugin) if plugin else None})
    return conditions


def claude_command(value):
    command = json.loads(value) if value.lstrip().startswith('[') else [value]
    require(isinstance(command, list) and bool(command) and all(nonempty(v) for v in command), 'invalid --claude command')
    return command


def session_argv(command, prompt, condition, disable_plugins):
    args = command + ['-p', prompt, '--permission-mode', 'bypassPermissions', '--output-format',
                      'stream-json', '--verbose', '--include-hook-events', '--settings',
                      json.dumps({'enabledPlugins': {key: False for key in disable_plugins}})]
    return args + (['--plugin-dir', condition['plugin']] if condition['plugin'] else [])


def decoded(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def summarize_session(path, plugin=None):
    tools, skills, reads, contexts, blocks = Counter(), [], [], 0, 0
    fallback = Counter()
    result, model = {}, None
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        event = decoded(line)
        if not isinstance(event, dict):
            continue
        if event.get('type') == 'system' and event.get('subtype') == 'init':
            model = event.get('model')
        if event.get('type') == 'assistant':
            message = decoded(event.get('message'))
            for key in TOKEN_KEYS:
                value = decoded(message.get('usage')).get(key)
                if isinstance(value, (int, float)):
                    fallback[key] += value
            content = message.get('content', [])
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict) or block.get('type') != 'tool_use':
                    continue
                name = block.get('name')
                if not isinstance(name, str):
                    continue
                tools[name] += 1
                inputs = decoded(block.get('input'))
                skill, file = inputs.get('skill', ''), inputs.get('file_path', '')
                if name == 'Skill' and isinstance(skill, str) and skill.startswith('agentic-coding:'):
                    skills.append(skill)
                if name == 'Read' and isinstance(file, str) and ('agentic-coding' in file.casefold()
                        or (plugin and plugin.replace('\\', '/').casefold() in file.replace('\\', '/').casefold())):
                    reads.append(file)
        elif event.get('subtype') == 'hook_response':
            output = decoded(event.get('output'))
            specific = decoded(output.get('hookSpecificOutput'))
            hook = event.get('hook_name') or event.get('hook_event') or specific.get('hookEventName', '')
            if isinstance(hook, str) and hook.startswith('UserPromptSubmit'):
                context = specific.get('additionalContext', output.get('additionalContext', ''))
                if isinstance(context, str):
                    contexts += len(context)
            if isinstance(hook, str) and hook.startswith('Stop') and output.get('decision') == 'block':
                blocks += 1
        elif event.get('type') == 'result':
            result = event
    usage = decoded(result.get('usage')) if isinstance(result.get('usage'), dict) else fallback
    return {'model': model, 'cost_usd': result.get('total_cost_usd'), 'turns': result.get('num_turns'),
            'duration_s': result.get('duration_ms', 0) / 1000 if isinstance(result.get('duration_ms'), (int, float)) else None,
            'usage': {key: usage.get(key) for key in TOKEN_KEYS}, 'tools': dict(tools), 'plugin_skills': skills,
            'plugin_file_reads': reads, 'hook_context_chars': contexts, 'stop_blocks': blocks,
            'answer': str(result.get('result') or ''), 'result_received': bool(result),
            'is_error': bool(result.get('is_error'))}


def execute(command, repo, timeout, transcript, shell=False):
    """Bound the owned process tree too, so a timed-out agent cannot edit during judging."""
    started = time.monotonic()
    with transcript.open('wb') as stdout, transcript.with_suffix('.stderr').open('wb') as stderr:
        process = subprocess.Popen(command, cwd=repo, shell=shell, stdout=stdout, stderr=stderr,
                                   start_new_session=os.name != 'nt')
        transcript.with_suffix('.process.json').write_text(json.dumps({
            'pid': process.pid, 'cwd': str(repo), 'started_at': time.time()}), encoding='utf-8')
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            else:
                os.killpg(process.pid, signal.SIGKILL)
            if process.poll() is None:
                process.kill()
            process.wait()
    return {'exit': process.returncode, 'timed_out': timed_out, 'wall_seconds': time.monotonic() - started}


def check_command(command, repo, timeout, log):
    try:
        result = execute(command, repo, timeout, log, shell=True)
        result['passed'] = result['exit'] == 0 and not result['timed_out']
        result['tail'] = (log.read_text(encoding='utf-8', errors='replace') +
                          log.with_suffix('.stderr').read_text(encoding='utf-8', errors='replace'))[-1000:]
        return result
    except Exception as error:
        return {'exit': None, 'passed': False, 'tail': str(error)}


def judged_command(command, repo, timeout, log):
    """Judge once more after a failure: shared-machine load flakes affect every condition alike."""
    first = check_command(command, repo, timeout, log)
    if first['passed']:
        return first
    second = check_command(command, repo, timeout, log.with_name(log.stem + '-retry' + log.suffix))
    return dict(second, first_attempt={key: first.get(key) for key in ('exit', 'timed_out', 'tail')})


def known_sum(values):
    values = list(values)
    return sum(values) if values and all(isinstance(v, (int, float)) for v in values) else None


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def remove_tree(path, root):
    """Detach links, then remove only owned short-workspace descendants without recursion."""
    path, root = Path(os.path.abspath(path)), Path(os.path.abspath(root))
    require(root == root.resolve(), 'cleanup root contains a reparse point')
    require(path != root and path.is_relative_to(root), f'cleanup path leaves workspace root: {path}')
    for parent in path.parents:
        if parent == root:
            break
        require(not _probe.is_link(parent), f'cleanup ancestor is a link: {parent}')
    if not path.exists() and not _probe.is_link(path):
        return
    stack = [(path, False)]
    while stack:
        item, visited = stack.pop()
        if _probe.is_link(item):
            if os.name == 'nt' and item.is_dir():
                subprocess.run(['cmd', '/c', 'rmdir', str(item)], check=True, capture_output=True)
            else:
                item.unlink()
        elif item.is_dir():
            if visited:
                item.rmdir()
            else:
                stack.append((item, True))
                with os.scandir(item) as entries:
                    stack.extend((Path(entry.path), False) for entry in entries)
        else:
            os.chmod(item, 0o700)
            item.unlink()


def link_directory(link, source):
    if os.name == 'nt':
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(source)], check=True, capture_output=True)
    else:
        link.symlink_to(source, target_is_directory=True)


def kill_owned(work):
    """Stop servers an agent left running from this run's directory; they skew later runs and lock files."""
    marker = str(work.resolve())
    if os.name == 'nt':
        query = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and "
                 "$_.CommandLine.IndexOf($env:EVAL_WORK, [StringComparison]::OrdinalIgnoreCase) -ge 0 } | "
                 "ForEach-Object { $_.ProcessId }")
        found = subprocess.run(['powershell', '-NoProfile', '-Command', query], capture_output=True, text=True,
                               env=dict(os.environ, EVAL_WORK=marker))
        for pid in found.stdout.split():
            if pid.isdigit() and int(pid) != os.getpid():
                subprocess.run(['taskkill', '/PID', pid, '/T', '/F'], capture_output=True)
    else:
        subprocess.run(['pkill', '-f', marker], capture_output=True)


def path_extent(files, directories):
    return {'file': max(files, key=len, default=''), 'directory': max(directories, key=len, default='')}


@lru_cache(maxsize=None)
def tracked_extent(project, ref):
    names = subprocess.check_output(['git', '-C', str(project), 'ls-tree', '-r', '-z', '--name-only', ref])
    files = [name for name in names.decode('utf-8').split('\0') if name]
    directories = {str(p).replace('\\', '/') for name in files for p in Path(name).parents if str(p) != '.'}
    return path_extent(files, directories)


@lru_cache(maxsize=None)
def dependency_extent(source):
    source = Path(source)
    require(source.is_dir(), f'link source missing: {source}')
    files, directories = [], []
    for directory, names, filenames in os.walk(source, followlinks=False):
        # Match robocopy /XJ: a shared directory junction is never followed into a private copy.
        names[:] = [n for n in names if not _probe.is_link(Path(directory) / n)]
        directories.extend(str((Path(directory) / n).relative_to(source)) for n in names)
        files.extend(str((Path(directory) / n).relative_to(source)) for n in filenames)
    return path_extent(files, directories)


def budget_for(root, extent, limit):
    file = str(root / extent['file']) if extent['file'] else str(root)
    directory = str(root / extent['directory']) if extent['directory'] else str(root)
    return {'fits': len(file) <= min(limit, 259) and len(directory) <= min(limit, 248),
            'required_file_length': len(file), 'required_directory_length': len(directory),
            'cause_file': file, 'cause_directory': directory}


def fallback_work_root():
    return Path(os.environ.get('SystemDrive', 'C:') + '/e') if os.name == 'nt' else Path(tempfile.gettempdir()) / 'e'


def dependency_sources(scenario, deps_root):
    project = Path(scenario['project'])
    names = scenario.get('links', []) or (['node_modules'] if (project / 'node_modules').is_dir() else [])
    return {name: (Path(deps_root) / project.name / name if deps_root else project / name) for name in names}


def plan_workspace(scenario, condition, rep, output, deps_root=None, copy_deps=False,
                   work_root=None, path_limit=240):
    """Budget the pinned tree and dependencies before creating a clone or starting a session."""
    work = Path(output).resolve() / scenario['id'] / condition['name'] / f'rep{rep}'
    cell_id = hashlib.sha256(str(work).encode('utf-8')).hexdigest()[:8]
    extent = tracked_extent(str(Path(scenario['project']).resolve()), scenario.get('ref', 'HEAD'))
    sources = dependency_sources(scenario, deps_root)
    dependencies = {name: dependency_extent(str(source.resolve())) for name, source in sources.items()}
    candidates = []
    for root in dict.fromkeys((Path(work_root or DEFAULT_WORK_ROOT).resolve(), fallback_work_root().resolve())):
        cell = root / cell_id
        repo = cell / 'r'
        private = {name: str(cell / 'd' / name) for name in sources} if copy_deps else {}
        checks = [budget_for(repo, extent, path_limit)]
        for name, dep_extent in dependencies.items():
            # Tools also address dependencies through the node_modules link in the clone.
            checks.append(budget_for(repo / name, dep_extent, path_limit))
            if copy_deps:
                checks.append(budget_for(Path(private[name]), dep_extent, path_limit))
            else:
                checks.append(budget_for(sources[name].resolve(), dep_extent, path_limit))
        worst_file = max(checks, key=lambda x: x['required_file_length'])
        worst_dir = max(checks, key=lambda x: x['required_directory_length'])
        fits = all(c['fits'] for c in checks)
        budget = dict(worst_file, required_directory_length=worst_dir['required_directory_length'],
                      cause_directory=worst_dir['cause_directory'], fits=fits, limit=path_limit)
        candidates.append(dict(budget, root=str(root)))
        plan = {'cell_id': cell_id, 'cell': {'scenario': scenario['id'], 'condition': condition['name'], 'rep': rep},
                'result_directory': str(work), 'work_root': str(root), 'directory': str(cell),
                'repo': str(repo), 'dependencies': private, 'path_budget': dict(budget, candidates=list(candidates))}
        if fits:
            return plan
    return plan


def copy_tree(source, target, path_limit=240, log_dir=None):
    budget = budget_for(Path(target).resolve(), dependency_extent(str(Path(source).resolve())), path_limit)
    require(budget['fits'], 'path_budget_exceeded: ' + json.dumps(budget))
    if os.name == 'nt':  # robocopy is far faster for node_modules; exit codes below 8 mean success.
        result = subprocess.run(['robocopy', str(source), str(target), '/E', '/XJ', '/SL', '/256', '/MT:16', '/NFL', '/NDL', '/NJH', '/NJS', '/NP'],
                                capture_output=True)
        if log_dir is not None:
            Path(log_dir, f'copy-{target.name}.log').write_bytes(result.stdout + result.stderr)
        require(result.returncode < 8, f'dependency copy failed: robocopy exit {result.returncode}')
    else:
        shutil.copytree(source, target, symlinks=True,
                        ignore=lambda directory, names: [n for n in names if
                            (Path(directory) / n).is_dir() and _probe.is_link(Path(directory) / n)])


def run(scenario, condition, rep, output, command, config, timeout, source_dir, deps_root=None, prune=False,
        copy_deps=False, work_root=None, path_limit=240):
    started = time.monotonic()
    work = output / scenario['id'] / condition['name'] / f'rep{rep}'
    work.mkdir(parents=True)
    workspace, created = None, False
    result = {'scenario': scenario['id'], 'condition': condition['name'], 'rep': rep, 'area': scenario['area'],
              'exit': None, 'timed_out': False, 'sessions': [], 'hidden': [], 'regression': None,
              'probes': [], 'errors': [], 'infrastructure_errors': [], 'stage': 'preflight',
              'raw_path': str(work), 'session_started': False}
    (work / 'session.jsonl').touch()
    budget = scenario.get('budget_seconds', timeout)
    try:
        workspace = plan_workspace(scenario, condition, rep, output, deps_root, copy_deps, work_root, path_limit)
        (work / 'workspace.json').write_text(json.dumps(workspace, indent=2), encoding='utf-8')
        require(workspace['path_budget']['fits'], 'path_budget_exceeded: ' + json.dumps(workspace['path_budget']))
        cell, repo = Path(workspace['directory']), Path(workspace['repo'])
        cell.mkdir(parents=True, exist_ok=False)
        created = True
        result['stage'] = 'clone'
        clone(Path(scenario['project']), repo, ref=scenario.get('ref'), link_modules=False, log_dir=work)
        result['stage'] = 'dependencies'
        for name, source in dependency_sources(scenario, deps_root).items():
            link = repo / name
            # Shared dependencies come from an evaluation copy so an agent's install never touches the user's project.
            require(not link.exists(), f'link destination exists: {name}')
            require(source.is_dir(), f'link source missing: {source}')
            if copy_deps:  # Each run gets its own copy: one agent's install cannot break a concurrent run.
                private = Path(workspace['dependencies'][name])
                private.parent.mkdir(parents=True, exist_ok=True)
                copy_tree(source, private, path_limit, log_dir=work)
                source = private
            link_directory(link, source)
        if scenario.get('fault'):
            fault = scenario['fault']
            replace_once(destination(repo, fault['file']), fault['find'], fault['replace'])
            subprocess.run(['git', 'add', '--', fault['file']], cwd=repo, check=True, capture_output=True)
            subprocess.run(['git', '-c', 'user.name=evaluation', '-c', 'user.email=evaluation@invalid',
                            'commit', '-m', fault['commit_message']], cwd=repo, check=True, capture_output=True)
        prompts = scenario.get('prompts', [scenario.get('prompt')])
        for index, prompt in enumerate(prompts, 1):
            result['stage'] = f'session{index}'
            transcript = work / f'session{index}.jsonl'
            status = execute(session_argv(command, prompt, condition, config['disable_plugins']), repo, budget, transcript)
            result['exit'] = status['exit']
            result['timed_out'] |= status['timed_out']
            facts = summarize_session(transcript, condition['plugin'])
            facts.update(status)
            facts['admitted_incomplete'] = any(m.casefold() in facts['answer'].casefold() for m in config['incomplete_markers'])
            facts['answer'] = facts['answer'][:4000]
            result['sessions'].append(facts)
            with (work / 'session.jsonl').open('ab') as combined:
                combined.write(transcript.read_bytes())
                combined.write(b'\n')
            if status['exit'] != 0 or status['timed_out'] or not facts['result_received'] or facts['is_error']:
                result['errors'].append(f'session {index}: timeout' if status['timed_out'] else f'session {index}: failed or missing result')
                break
        kill_owned(cell)
        result['stage'] = 'probes'
        for index, probe in enumerate(scenario.get('probes', [])):
            record = {'name': probe['name'], 'detected': False}
            try:
                path = destination(repo, probe['file'])
                original = replace_once(path, probe['find'], probe['replace'])
                try:
                    outcome = check_command(probe['command'], repo, timeout, work / f'probe{index}.log')
                    record.update(outcome)
                    record['detected'] = outcome['exit'] is not None and outcome['exit'] != 0 and not outcome.get('timed_out')
                finally:
                    path.write_bytes(original)
            except Exception as error:
                record['error'] = str(error)
            result['probes'].append(record)
        # The existing suite runs before hidden files exist, so a glob never counts them twice.
        if scenario.get('regression'):
            result['stage'] = 'regression'
            result['regression'] = judged_command(scenario['regression'], repo, timeout, work / 'regression.log')
        # Install all hidden files together: no session or probe can read them beforehand.
        for check in scenario['hidden']:
            for dest, source in check['files'].items():
                target = destination(repo, dest)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_dir / relative_path(source), target)
        for index, check in enumerate(scenario['hidden']):
            result['stage'] = f'hidden{index}'
            result['hidden'].append({'name': check['name'], **judged_command(
                check['command'], repo, timeout, work / f'hidden{index}.log')})
    except Exception as error:
        result['errors'].append(f'{type(error).__name__}: {error}')
        result['infrastructure_errors'].append({'stage': result['stage'], 'message': str(error),
                                                'log': str(work / 'infrastructure.log')})
        (work / 'infrastructure.log').write_text(traceback.format_exc(), encoding='utf-8')
    result['session_started'] = any(work.glob('session[0-9]*.process.json'))
    if created:
        try:
            kill_owned(Path(workspace['directory']))
            if prune:
                remove_tree(Path(workspace['directory']), Path(workspace['work_root']))
        except Exception as error:
            result['errors'].append(f'cleanup failed: {error}')
            result['infrastructure_errors'].append({'stage': 'cleanup', 'message': str(error),
                                                    'log': str(work / 'cleanup.log')})
            (work / 'cleanup.log').write_text(traceback.format_exc(), encoding='utf-8')
    return finish_result(result, scenario, work, started)


def finish_result(result, scenario, work, started):
    checks = [('regression', result['regression'])] + [
        (f'hidden{index}', check) for index, check in enumerate(result['hidden'])] + [
        (f'probe{index}', check) for index, check in enumerate(result['probes']) if 'error' not in check]
    for stage, check in checks:
        if check and (check.get('exit') is None or check.get('timed_out')):
            message = f'{stage}: judging process unavailable or timed out'
            result['errors'].append(message)
            result['infrastructure_errors'].append({'stage': stage, 'message': message,
                                                    'log': str(work / f'{stage}.log')})
    sessions = result['sessions']
    for key in ('cost_usd', 'turns', 'duration_s', 'hook_context_chars', 'stop_blocks'):
        result[key] = known_sum(s.get(key) for s in sessions)
    result['usage'] = {key: known_sum(s['usage'][key] for s in sessions) for key in TOKEN_KEYS}
    result['tools'] = dict(sum((Counter(s['tools']) for s in sessions), Counter()))
    for key in ('plugin_skills', 'plugin_file_reads'):
        result[key] = [v for s in sessions for v in s[key]]
    result['answer'] = '\n'.join(s['answer'] for s in sessions)[:4000]
    result['admitted_incomplete'] = any(s['admitted_incomplete'] for s in sessions)
    result['models'] = sorted({s['model'] for s in sessions if s.get('model')})
    result['acceptance_passed'] = len(result['hidden']) == len(scenario['hidden']) and all(h['passed'] for h in result['hidden'])
    regression_ok = (result['regression'] is None and 'regression' not in scenario
                     or bool(result['regression'] and result['regression']['passed']))
    # A crashed or timed-out session never claimed completion; it counts against success only.
    result['false_completion'] = (not result['errors'] and not result['timed_out'] and not result['admitted_incomplete']
                                  and (not result['acceptance_passed'] or not regression_ok))
    result['verified_success'] = result['acceptance_passed'] and regression_ok and not result['errors'] and not result['timed_out']
    probes = result['probes']
    # A probe whose exact text is absent from the agent's own implementation is not applicable.
    applicable = [p for p in probes if 'error' not in p]
    result['probes_applicable'] = len(applicable)
    result['probe_kill_rate'] = sum(p['detected'] for p in applicable) / len(applicable) if applicable else None
    result['wall_seconds'] = time.monotonic() - started
    result['excluded'] = bool(result['infrastructure_errors'])
    for name in ('result.json', 'classified.json'):
        write_json(work / name, result)
    return result


def safe_run(scenario, condition, rep, output, *args):
    """A broken cell cannot abort the matrix; recover paid evidence rather than replaying it."""
    work = output / scenario['id'] / condition['name'] / f'rep{rep}'
    try:
        return run(scenario, condition, rep, output, *args)
    except Exception as error:
        work.mkdir(parents=True, exist_ok=True)
        log = work / f'runner-error-{time.time_ns()}.log'
        log.write_text(traceback.format_exc(), encoding='utf-8')
        mapping = work / 'workspace.json'
        cleanup_error = None
        if mapping.is_file():
            try:
                workspace = json.loads(mapping.read_text(encoding='utf-8'))
                expected_id = hashlib.sha256(str(work.resolve()).encode()).hexdigest()[:8]
                cell = Path(workspace['work_root']) / expected_id
                require(str(cell) == workspace['directory'], 'interrupted workspace mapping mismatch')
                kill_owned(cell)
                if args[5]:
                    remove_tree(cell, Path(workspace['work_root']))
            except Exception as failure:
                cleanup_error = str(failure)
        sessions = []
        for path in sorted(work.glob('session[0-9]*.jsonl')):
            facts = summarize_session(path, condition['plugin'])
            facts['admitted_incomplete'] = any(m.casefold() in facts['answer'].casefold()
                                             for m in args[1]['incomplete_markers'])
            sessions.append(facts)
        result = {'scenario': scenario['id'], 'condition': condition['name'], 'rep': rep,
                  'area': scenario['area'], 'raw_path': str(work), 'exit': None, 'timed_out': False,
                  'sessions': sessions, 'hidden': [], 'regression': None, 'probes': [],
                  'session_started': bool(sessions), 'stage': 'runner',
                  'errors': [str(error)], 'infrastructure_errors': [
                      {'stage': 'runner', 'message': str(error), 'log': str(log)}]}
        if cleanup_error:
            result['errors'].append('interrupted cleanup: ' + cleanup_error)
        return finish_result(result, scenario, work, time.monotonic())


def median(values):
    values = list(values)
    return statistics.median(values) if values and all(v is not None for v in values) else None


def aggregate(results):
    conditions, scenarios = {}, {}
    for name in dict.fromkeys(r['condition'] for r in results):
        rows = [r for r in results if r['condition'] == name]
        n, k = len(rows), sum(r['verified_success'] for r in rows)
        tokens = {key: known_sum(r['usage'][key] for r in rows) for key in TOKEN_KEYS}
        rates = [r['probe_kill_rate'] for r in rows if r['probe_kill_rate'] is not None]
        conditions[name] = {'runs': n, 'verified_success': {'k': k, 'n': n, 'rate': k / n},
                            'false_completion_rate': sum(r['false_completion'] for r in rows) / n,
                            'mean_probe_kill_rate': statistics.mean(rates) if rates else None,
                            'probes_applicable': sum(r.get('probes_applicable', 0) for r in rows),
                            'admitted_incomplete': sum(r['admitted_incomplete'] for r in rows),
                            'total_tokens': tokens,
                            'median_tokens': {key: median(r['usage'][key] for r in rows) for key in TOKEN_KEYS},
                            'total_cost_usd': known_sum(r['cost_usd'] for r in rows),
                            'median_wall_seconds': median(r['wall_seconds'] for r in rows),
                            'tokens_per_verified_success': (tokens['input_tokens'] + tokens['output_tokens']) / k
                                if k and tokens['input_tokens'] is not None and tokens['output_tokens'] is not None else None,
                            'plugin_skill_invocations': sum(len(r['plugin_skills']) for r in rows),
                            'mean_hook_context_chars': (known_sum(r['hook_context_chars'] for r in rows) / n
                                if all(r['hook_context_chars'] is not None for r in rows) else None)}
        for scenario in dict.fromkeys(r['scenario'] for r in rows):
            selected = [r for r in rows if r['scenario'] == scenario]
            scenarios.setdefault(scenario, {})[name] = {'k': sum(r['verified_success'] for r in selected), 'n': len(selected)}
    failures = []
    for r in results:
        if r['verified_success']:
            continue
        reasons = list(r['errors'])
        reasons += [f"hidden {h['name']} failed" for h in r['hidden'] if not h['passed']]
        if not r['acceptance_passed'] and not any(not h['passed'] for h in r['hidden']):
            reasons.append('hidden checks incomplete')
        if r['regression'] and not r['regression']['passed']:
            reasons.append('regression failed')
        if r['timed_out'] and not any('timeout' in reason for reason in reasons):
            reasons.append('timeout')
        failures.append({'scenario': r['scenario'], 'condition': r['condition'], 'rep': r['rep'], 'reasons': reasons})
    return {'conditions': conditions, 'scenarios': scenarios, 'failures': failures, 'results': results}


def markdown(report):
    def fmt(value):
        return '?' if value is None else f'{value:.3g}'
    lines = ['# Delegation evaluation', '',
             '| Condition | Runs | Success | False completion | Probe kill | Incomplete | Input med/total | Output med/total | Cost USD | Wall med s | Tokens/success | Skills | Hook chars mean |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for name, c in report['conditions'].items():
        success = c['verified_success']
        lines.append(f"| {name} | {c['runs']} | {success['k']}/{success['n']} | {fmt(c['false_completion_rate'])} | "
                     f"{fmt(c['mean_probe_kill_rate'])} | {c['admitted_incomplete']} | "
                     f"{fmt(c['median_tokens']['input_tokens'])}/{fmt(c['total_tokens']['input_tokens'])} | "
                     f"{fmt(c['median_tokens']['output_tokens'])}/{fmt(c['total_tokens']['output_tokens'])} | "
                     f"{fmt(c['total_cost_usd'])} | {fmt(c['median_wall_seconds'])} | "
                     f"{fmt(c['tokens_per_verified_success'])} | {c['plugin_skill_invocations']} | {fmt(c['mean_hook_context_chars'])} |")
    names = list(report['conditions'])
    lines += ['', '| Scenario | ' + ' | '.join(names) + ' |', '| --- | ' + ' | '.join('---' for _ in names) + ' |']
    for scenario, values in report['scenarios'].items():
        lines.append('| ' + scenario + ' | ' + ' | '.join(
            f"{values[n]['k']}/{values[n]['n']}" if n in values else '—' for n in names) + ' |')
    if report['failures']:
        lines += ['', 'Failed / timeout runs:']
        for f in report['failures']:
            lines.append(f"- {f['scenario']}/{f['condition']}/rep{f['rep']}: " + '; '.join(f['reasons']))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--condition', action='append', required=True)
    parser.add_argument('--reps', type=int, default=3)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--only', nargs='+', action='extend', default=[])
    parser.add_argument('--claude', default='claude')
    parser.add_argument('--timeout', type=float, default=2400)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--deps-root', type=Path, help='Directory holding <project-name>/<link> copies for clones')
    parser.add_argument('--prune-clones', action='store_true', help='Delete each clone after judging (links detached first)')
    parser.add_argument('--copy-deps', action='store_true', help='Give every run a private copy of each linked directory')
    parser.add_argument('--work-root', type=Path, default=DEFAULT_WORK_ROOT,
                        help='Short workspace root; logs remain under --output (default: .work/e)')
    parser.add_argument('--path-limit', type=int, default=240, help='Maximum planned file/directory length (default: 240)')
    parser.add_argument('--resume-from', type=Path, action='append', default=[],
                        help='Reuse valid/paid cells and costs from an earlier state.json; repeatable')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        require(args.reps > 0 and args.jobs > 0 and positive(args.timeout), 'reps, jobs and timeout must be positive')
        require(0 < args.path_limit <= 259, 'path-limit must be between 1 and 259')
        require(not args.output.exists() or (args.output / 'state.json').is_file(),
                'output directory must not exist without a resumable state.json')
        config = load_scenarios(args.scenarios.resolve())
        conditions = parse_conditions(args.condition)
        command = claude_command(args.claude)
        require(set(args.only) <= {s['id'] for s in config['scenarios']}, 'unknown --only scenario')
        scenarios = [s for s in config['scenarios'] if not args.only or s['id'] in args.only]
    except (ValueError, OSError, TypeError) as error:
        parser.error(str(error))
    matrix = [(s, c, rep) for rep in range(1, args.reps + 1) for s in scenarios for c in conditions]
    if args.dry_run:
        print(json.dumps({'runs': [{'scenario': s['id'], 'condition': c['name'], 'rep': rep} for s, c, rep in matrix],
                          'argv': {c['name']: session_argv(command, scenarios[0].get('prompt', scenarios[0].get('prompts', [''])[0]),
                                  c, config['disable_plugins']) for c in conditions}}, ensure_ascii=False, indent=2))
        return 0
    output = args.output.resolve()
    previous = [json.loads(p.read_text(encoding='utf-8')) for p in args.resume_from]
    current = json.loads((output / 'state.json').read_text(encoding='utf-8')) if output.exists() else None
    if current:
        previous.append(current)
    attempts, valid = {}, {}
    def cell_key(row):
        return row['scenario'], row['condition'], row['rep']
    def attempt_key(row):
        return row.get('raw_path') or json.dumps(row, sort_keys=True)
    for state in previous:
        for row in state['attempts']:
            attempts[attempt_key(row)] = row
        for row in state['valid']:
            key = cell_key(row)
            require(key not in valid or attempt_key(valid[key]) == attempt_key(row),
                    f'multiple valid results for cell: {key}')
            valid[key] = row
    def paid(row):
        return bool(row.get('session_started') or row.get('sessions') or row.get('cost_usd'))
    skip = set(valid) | {cell_key(r) for r in attempts.values() if paid(r)}
    if current:
        # Current-run infrastructure attempts are retained, not blindly retried after a process restart.
        skip |= {cell_key(r) for r in current['attempts']}
    expected = {(s['id'], c['name'], rep) for s, c, rep in matrix}
    matrix = [(s, c, rep) for s, c, rep in matrix if (s['id'], c['name'], rep) not in skip]
    output.mkdir(parents=True, exist_ok=True)
    def save_state(remaining):
        rows = list(attempts.values())
        excluded = [r for r in rows if cell_key(r) not in valid or attempt_key(valid[cell_key(r)]) != attempt_key(r)]
        unknown = [r for r in rows if paid(r) and r.get('cost_usd') is None]
        known = sum(r['cost_usd'] for r in rows if r.get('cost_usd') is not None)
        write_json(output / 'state.json', {
            'attempts': rows, 'valid': list(valid.values()), 'excluded': excluded,
            'spent_usd': None if unknown else known, 'reported_cost_known_usd': known,
            'unknown_cost_attempts': len(unknown), 'pending': remaining, 'remaining': remaining,
            'stopped': None, 'resume_from': [str(p.resolve()) for p in args.resume_from],
            'scenarios_sha256': hashlib.sha256(args.scenarios.read_bytes()).hexdigest(),
            'conditions': conditions, 'reps': args.reps, 'work_root': str(args.work_root.resolve()),
            'path_limit': args.path_limit})
    save_state(len(matrix))
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(safe_run, s, c, rep, output, command, config, args.timeout,
                               args.scenarios.resolve().parent, args.deps_root and args.deps_root.resolve(),
                               args.prune_clones, args.copy_deps, args.work_root, args.path_limit) for s, c, rep in matrix]
        for index, future in enumerate(as_completed(futures), 1):
            row = future.result()
            attempts[attempt_key(row)] = row
            if not row.get('excluded'):
                valid[cell_key(row)] = row
            save_state(len(futures) - index)
            print(f"CELL {row['scenario']}/{row['condition']}/rep{row['rep']} "
                  f"success={row['verified_success']} excluded={row.get('excluded', False)} "
                  f"cost={row['cost_usd']} valid={len(valid)}", flush=True)
    report = aggregate(list(valid.values()))
    report.update(attempts=list(attempts.values()), excluded=[r for r in attempts.values()
                  if cell_key(r) not in valid or attempt_key(valid[cell_key(r)]) != attempt_key(r)])
    rendered = markdown(report)
    (args.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (args.output / 'report.md').write_text(rendered, encoding='utf-8')
    print(rendered)
    return 0 if all(key in valid and valid[key]['verified_success'] for key in expected) else 1


if __name__ == '__main__':
    raise SystemExit(main())
