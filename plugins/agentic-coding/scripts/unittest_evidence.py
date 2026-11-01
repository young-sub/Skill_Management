"""Reassess native unittest captures; no test execution or stored-verdict trust.

This adapter establishes scoped unittest results, not authenticated host or
product proof. Scoped reuse is opt-in and always includes the active registry,
Feature owners, test modules, configuration and criteria.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


def _repository_root(cwd):
    try:
        result = subprocess.run(['git', '-C', str(cwd), 'rev-parse', '--show-toplevel'],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
    except OSError:
        return None
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 and result.stdout.strip() else None


repository_root = _repository_root


def _is_link(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def _git_input_paths(root):
    try:
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others',
                                 '--exclude-standard', '-z'], capture_output=True)
    except OSError as error:
        raise ValueError(f'Cannot enumerate declared project inputs: {error}') from error
    if result.returncode != 0:
        raise ValueError('Cannot enumerate declared project inputs')
    return set(filter(None, result.stdout.decode('utf-8', errors='strict').split('\0')))


def _sensitive_input(name):
    return any(part.lower().startswith(('.env', '.dev.vars')) or part.lower() in
               {'auth.json', 'credentials', 'secrets'} for part in PurePosixPath(name).parts)


def _relative_file(root, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Input paths must be nonempty project-relative strings')
    name = value.replace('\\', '/')
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(part in {'', '.', '..'} for part in relative.parts):
        raise ValueError(f'Input path must stay inside the project: {value}')
    if _sensitive_input(name):
        raise ValueError(f'Sensitive paths cannot be verification inputs: {value}')
    candidate = root.joinpath(*relative.parts)
    if _is_link(candidate):
        raise ValueError(f'Input path cannot be a symlink or junction: {value}')
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f'Input path must resolve to a project file: {value}')
    parent = candidate.parent
    while parent != root:
        if _is_link(parent):
            raise ValueError(f'Input path traverses a symlink or junction: {value}')
        parent = parent.parent
    return resolved.relative_to(root).as_posix()


def normalize_input_scope(root, inputs):
    """Validate concrete file paths used for a captured input scope."""
    root = Path(root).resolve()
    if not isinstance(inputs, (list, tuple)) or not inputs:
        raise ValueError('A scoped capture requires at least one declared input file')
    normalized = [_relative_file(root, value) for value in inputs]
    if len(normalized) != len(set(normalized)):
        raise ValueError('Scoped input files must be unique')
    inventory = _git_input_paths(root)
    if not set(normalized).issubset(inventory):
        raise ValueError('Scoped input files must be tracked or nonignored project files')
    return sorted(normalized)


def _expand_inputs(root, patterns, label):
    if not isinstance(patterns, (list, tuple)) or any(not isinstance(item, str) or not item.strip()
                                                       for item in patterns):
        raise ValueError(f'{label} must be a list of project-relative paths or patterns')
    inventory = _git_input_paths(root)
    result = set()
    for value in patterns:
        name = value.replace('\\', '/')
        relative = PurePosixPath(name)
        if relative.is_absolute() or any(part in {'', '.', '..'} for part in relative.parts):
            raise ValueError(f'{label} must stay inside the project: {value}')
        matches = list(root.glob(name))
        if not matches:
            raise ValueError(f'{label} has no matching files: {value}')
        matched_files = set()
        for match in matches:
            if _is_link(match):
                raise ValueError(f'{label} matches a symlink or junction: {value}')
            resolved = match.resolve(strict=True)
            if not resolved.is_relative_to(root):
                raise ValueError(f'{label} escapes the project: {value}')
            if resolved.is_dir():
                prefix = resolved.relative_to(root).as_posix().rstrip('/') + '/'
                matched_files.update(path for path in inventory if path.startswith(prefix))
            else:
                relative = resolved.relative_to(root).as_posix()
                if relative in inventory:
                    matched_files.add(relative)
        if not matched_files:
            raise ValueError(f'{label} has no tracked or nonignored files: {value}')
        result.update(matched_files)
    if patterns and not result:
        raise ValueError(f'{label} has no matching files')
    for path in result:
        _relative_file(root, path)
    return result


def _module_files(root, working_directory, name):
    """Resolve a unittest module/class target to its containing Python module."""
    direct = Path(name.replace('\\', '/'))
    candidates = []
    if direct.suffix == '.py':
        candidates.append(working_directory / direct)
    parts = name.replace('/', '.').split('.')
    for end in range(len(parts), 0, -1):
        base = working_directory.joinpath(*parts[:end])
        candidates.extend((base.with_suffix('.py'), base / '__init__.py'))
        base = root.joinpath(*parts[:end])
        candidates.extend((base.with_suffix('.py'), base / '__init__.py'))
    module = next((candidate.resolve() for candidate in candidates
                   if candidate.is_file() and candidate.resolve().is_relative_to(root)), None)
    if module is None:
        raise ValueError(f'Cannot resolve registered unittest module: {name}')
    if _is_link(module):
        raise ValueError(f'Unittest module cannot be a symlink or junction: {name}')
    files = {module.relative_to(root).as_posix()}
    parent = module.parent
    while parent != root:
        init = parent / '__init__.py'
        if init.is_file():
            if _is_link(init):
                raise ValueError(f'Unittest package cannot be a symlink or junction: {init}')
            files.add(init.relative_to(root).as_posix())
        parent = parent.parent
    return files


def _unittest_inputs(root, working_directory, argv):
    if len(argv) < 3 or argv[1:3] != ['-m', 'unittest']:
        raise ValueError('Scoped verification requires a registered python -m unittest command')
    arguments = argv[3:]
    result = set()
    if not arguments:
        relative = working_directory.relative_to(root).as_posix()
        pattern = f'{relative}/**/test*.py' if relative != '.' else '**/test*.py'
        return _expand_inputs(root, [pattern], 'unittest discovery')
    index = 0
    while index < len(arguments):
        item = arguments[index]
        if item == 'discover':
            start, pattern = '.', 'test*.py'
            index += 1
            while index < len(arguments) and arguments[index].startswith('-'):
                option = arguments[index]
                index += 1
                if option in {'-s', '--start-directory', '-p', '--pattern', '-t', '--top-level-directory'}:
                    if index >= len(arguments):
                        raise ValueError(f'Missing value for unittest option: {option}')
                    value = arguments[index]
                    index += 1
                    if option in {'-s', '--start-directory'}:
                        start = value
                    elif option in {'-p', '--pattern'}:
                        pattern = value
            base = Path(start)
            if not base.is_absolute():
                base = working_directory / base
            if not base.resolve().is_relative_to(root):
                raise ValueError('Unittest discovery directory must stay inside the project')
            relative = base.resolve().relative_to(root).as_posix()
            glob = f'{relative}/**/{pattern}' if relative != '.' else f'**/{pattern}'
            result.update(_expand_inputs(root, [glob], 'unittest discovery'))
            continue
        if item in {'-k', '--locals'}:
            index += 2 if item == '-k' else 1
            continue
        if item.startswith('-'):
            index += 1
            continue
        result.update(_module_files(root, working_directory, item))
        index += 1
    if not result:
        raise ValueError('Registered unittest command selects no test modules')
    return result


def verification_inputs(root, feature, check, argv, evidence_inputs):
    """Return the active minimum registry/test scope plus declared dependencies.

    ``None`` is the backwards-compatible whole-Git fallback. The explicit
    command-level ``evidence_inputs`` list only adds to this minimum; it can
    never replace registered sources, maps, criteria, tests, or configuration.
    """
    if evidence_inputs is None:
        return None
    root = Path(root).resolve()
    if not isinstance(evidence_inputs, list) or any(not isinstance(item, str) or not item.strip()
                                                    for item in evidence_inputs):
        raise ValueError('commands.<id>.evidence_inputs must be a list of nonempty paths or patterns')
    try:
        project = json.loads((root / '.harness/project.yaml').read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise ValueError(f'Cannot read the registered project configuration: {error}') from error
    workflow = project.get('extensions', {}).get('workflow', {})
    features = workflow.get('features') if isinstance(workflow, dict) else None
    if not isinstance(features, list):
        raise ValueError('Scoped reuse requires the registered workflow Feature map')
    matches = [entry for entry in features if isinstance(entry, dict) and entry.get('id') == feature]
    if len(matches) != 1:
        raise ValueError(f'Scoped reuse requires one registered Feature: {feature}')
    entry = matches[0]
    if check not in entry.get('checks', []):
        raise ValueError(f'Check is not registered for Feature {feature}: {check}')
    owners = []
    for key in ('sources', 'map', 'criteria'):
        values = entry.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value.strip()
                                                              for value in values):
            raise ValueError(f'Registered Feature {feature} requires explicit {key}')
        owners.extend(values)
    command = project.get('commands', {}).get(check)
    if command is None:
        command = project.get('impact', {}).get('feature_selectors', {}).get(check)
    if not isinstance(command, dict) or not isinstance(command.get('working_directory', '.'), str):
        raise ValueError(f'Registered command metadata is unavailable: {check}')
    working_directory = (root / command.get('working_directory', '.')).resolve()
    if not working_directory.is_relative_to(root) or not working_directory.is_dir():
        raise ValueError(f'Registered command directory must stay inside the project: {check}')
    configuration = ['.harness/project.yaml', 'docs/feature-map.md']
    test_files = _unittest_inputs(root, working_directory, argv)
    inputs = _expand_inputs(root, [*configuration, *owners, *evidence_inputs],
                            'Registered verification input')
    inputs.update(test_files)
    return sorted(inputs)


def validate_captured_scope(cwd, record, minimum=None, feature=None):
    """Validate a captured scope against the current command and Feature registry."""
    root = _repository_root(cwd)
    if root is None:
        raise ValueError('Scoped evidence requires a current repository root')
    project = json.loads((root / '.harness/project.yaml').read_text(encoding='utf-8'))
    check = record.get('check')
    descriptor = project.get('commands', {}).get(check)
    if descriptor is None:
        descriptor = project.get('impact', {}).get('feature_selectors', {}).get(check)
    declared = descriptor.get('evidence_inputs') if isinstance(descriptor, dict) else None
    consumers = record.get('shared_features', [record.get('feature')])
    if (not isinstance(consumers, list) or not consumers or record.get('feature') not in consumers
            or len(consumers) != len(set(consumers))):
        raise ValueError('Captured Feature consumers are invalid')
    required = set()
    for consumer in consumers:
        current = verification_inputs(root, consumer, check, record.get('argv'), declared)
        if current is None:
            raise ValueError('Captured scoped reuse is not declared by every active command consumer')
        required.update(current)
    required = sorted(required)
    captured = normalize_input_scope(root, record.get('input_scope'))
    if not set(required).issubset(captured):
        raise ValueError('Captured verification scope omits active registry, test, configuration, or criteria inputs')
    if minimum is not None:
        supplied = normalize_input_scope(root, minimum)
        selected_feature = feature or record.get('feature')
        missing = set(verification_inputs(root, selected_feature, check,
                                          record.get('argv'), declared)) - set(supplied)
        if missing:
            raise ValueError('Supplied verification scope omits active inputs for the selected Feature: ' +
                             ', '.join(sorted(missing)))
    if record.get('input_scope') != captured:
        raise ValueError('Captured verification scope is not canonical')
    return captured


def git_identity(cwd, inputs=None):
    if inputs is not None:
        root = _repository_root(cwd)
        if root is None:
            return None
        try:
            paths = normalize_input_scope(root, inputs)
            hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in paths}
        except (OSError, ValueError):
            return None
        return {'input_scope': paths, 'input_sha256': hashes,
                'limit': 'Only declared verification inputs are attested; runtime dependencies, generated state, and server identity are not.'}

    def git(*args):
        try:
            result = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True)
        except OSError:
            return None
        return result.stdout if result.returncode == 0 else None
    head = git('rev-parse', 'HEAD')
    if head is None:
        return None
    diff = git('diff', 'HEAD', '--binary')
    status = git('status', '--porcelain')
    untracked = git('ls-files', '--others', '--exclude-standard', '-z')
    if diff is None or status is None or untracked is None:
        return None
    untracked_hashes = {}
    root = Path(cwd).resolve()
    for name in filter(None, untracked.decode('utf-8').split('\0')):
        relative = Path(name)
        path = root / relative
        if (any(part.lower().startswith(('.env', '.dev.vars')) or part.lower() in
                {'auth.json', 'credentials', 'secrets'} for part in relative.parts) or
                not path.resolve().is_relative_to(root) or
                any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
                    for p in (path, *path.parents) if p != root.parent)):
            return None
        try:
            untracked_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None
    return {
        'head': head.decode().strip(),
        'tracked_diff_sha256': hashlib.sha256(diff).hexdigest() if diff is not None else None,
        'status': status.decode('utf-8', errors='replace'),
        'untracked_sha256': untracked_hashes,
        'limit': 'Ignored inputs, dependencies, runtime data and server identity are not attested.',
    }


def assess(path, run_id, feature, check, argv, cwd, input_scope=None):
    raw = path.read_bytes()
    record = json.loads(raw)
    if not isinstance(record, dict):
        raise ValueError('Evidence must be a capture record')
    binding = {'run_id': run_id, 'feature': feature, 'check': check,
               'argv': argv, 'cwd': str(cwd)}
    consumers = record.get('shared_features', [record.get('feature')])
    if (not isinstance(consumers, list) or not consumers
            or any(not isinstance(name, str) or not name.strip() for name in consumers)
            or len(consumers) != len(set(consumers)) or record.get('feature') not in consumers):
        raise ValueError('Invalid preselected Feature consumers')
    if feature not in consumers or any(record.get(key) != value for key, value in binding.items() if key != 'feature'):
        raise ValueError('Evidence does not match the selected run, Feature, command or cwd')

    captured_scope = record.get('input_scope')
    if captured_scope is not None:
        captured_scope = validate_captured_scope(cwd, record, input_scope, feature)
        current = git_identity(cwd, captured_scope)
    elif input_scope is not None:
        raise ValueError('Scoped verification was declared after this capture; recapture is required')
    else:
        current = git_identity(cwd)
    if current is None or record.get('before') != current or record.get('after') != current:
        raise ValueError('Git identity unavailable, changed during execution or stale')
    verdict = {**binding, 'evidence': str(path.resolve()),
               'evidence_sha256': hashlib.sha256(raw).hexdigest(),
               'scope': 'repository/harness; selected unittest command only',
               'remaining': 'Ignored inputs, dependencies, runtime/server identity, '
                            'agent quality and external products are not attested.'}
    if record.get('execution') != 'exited' or type(record.get('exit_code')) is not int:
        raise ValueError('Command did not exit normally; not_run/unavailable/timeout is not PASS')
    if record.get('cleanup_incomplete') or record.get('behavior_verdict') is not None:
        raise ValueError('Incomplete cleanup or submitted behavior verdict cannot establish PASS')
    output = record['stdout'] + '\n' + record['stderr']
    counts = re.findall(r'^Ran (\d+) tests? in [^\r\n]+$', output, re.MULTILINE)
    if len(counts) == 1 and int(counts[0]) == 0:
        raise ValueError('No tests ran; not_run is not PASS')
    if record['exit_code'] != 0:
        if re.search(r'_FailedTest|Failed to import test module', output):
            return {**verdict, 'status': 'BLOCKED', 'reason': 'Unittest discovery/import unavailable; inspect raw error',
                    'exit_code': record['exit_code']}
        return {**verdict, 'status': 'ISSUES', 'reason': 'Native command failed',
                'exit_code': record['exit_code']}
    # This project owns these unittest commands. Output strings are not
    # signatures; this parser is deliberately not a generic runner framework.
    if len(counts) != 1 or int(counts[0]) == 0 or not re.search(r'^OK\s*$', output, re.MULTILINE):
        raise ValueError('No unambiguous, nonempty unittest success summary')
    if re.search(r'^FAILED\b|^OK \(|^.*skipped=\d+', output, re.MULTILINE):
        raise ValueError('Skipped, expected-failure or contradictory results require scoped review')
    return {**verdict, 'status': 'PASS', 'reason': 'Selected unittest assertions passed',
            'tests_run': int(counts[0]), 'exit_code': 0}
