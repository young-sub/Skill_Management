"""Offline authoring audit; never invokes a delegated agent or makes a commit."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import time


SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
TEMP = Path('C:/Users/YS/AppData/Local/Temp/claude/eval-authoring-v2')
PROJECTS = [Path('C:/Users/YS/Desktop/python') / n for n in ('labeler', 'yeondoo-link')]


def git(repo, *args, check=True):
    result = subprocess.run(['git', '--no-optional-locks', '-c', f'safe.directory={repo.as_posix()}', '-C', str(repo), *args],
                            capture_output=True, check=check)
    return result.stdout.decode('utf-8', errors='replace').strip()


def snapshot():
    result = {}
    for repo in PROJECTS:
        status = git(repo, 'status', '--porcelain=v1', '--untracked-files=all')
        tracked = git(repo, 'diff', 'HEAD', '--binary')
        result[repo.name] = {'head': git(repo, 'rev-parse', 'HEAD'), 'status': status,
                             'tracked_diff_sha256': hashlib.sha256(tracked.encode()).hexdigest()}
    return result


def save(name, data):
    dest = SUITE / 'evidence' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def cleanup(delete=False):
    """Inventory without traversing reparse points; remove junctions before trees."""
    assert TEMP.absolute() == TEMP.resolve(), 'Authoring root or ancestor is a reparse point'
    links, ordinary_bytes, files = [], 0, 0
    pending = [TEMP]
    while pending:
        for entry in os.scandir(pending.pop()):
            path = Path(entry.path)
            assert path.absolute().is_relative_to(TEMP.absolute())
            info = entry.stat(follow_symlinks=False)
            if info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                links.append({'path': str(path), 'target': os.readlink(path)})
            elif entry.is_dir(follow_symlinks=False):
                pending.append(path)
            else:
                ordinary_bytes += info.st_size
                files += 1
    record = {'root': str(TEMP), 'files': files, 'ordinary_bytes': ordinary_bytes,
              'junctions': links, 'excluded': [str(DEPS_ROOT) for DEPS_ROOT in
                  (TEMP.parent / 'eval-deps', *PROJECTS)], 'deleted': False}
    save('cleanup-preview.json', record)
    if delete:
        for link in links:
            subprocess.run(['cmd', '/d', '/c', 'rmdir', link['path']], check=True, capture_output=True)
            assert not os.path.lexists(link['path'])
        # The traversal above found every reparse point without following one.
        assert TEMP.absolute() == TEMP.resolve()
        shutil.rmtree(TEMP, onerror=lambda func, path, exc: (os.chmod(path, stat.S_IWRITE), func(path)))
        assert not TEMP.exists()
        record['deleted'] = True
        record['dependency_copies_present'] = all((TEMP.parent / 'eval-deps' / p.name / 'node_modules').is_dir()
                                                  for p in PROJECTS)
        assert record['dependency_copies_present']
        save('cleanup-result.json', record)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def clone(project, target, ref):
    assert target.parent == TEMP and not target.exists(), target
    TEMP.mkdir(parents=True, exist_ok=True)
    command = ['git', '-c', f'safe.directory={project.as_posix()}',
               '-c', f'safe.directory={(project / ".git").as_posix()}', 'clone', '--local']
    first = subprocess.run(command + [str(project), str(target)], capture_output=True)
    if first.returncode:
        # A failed local-hardlink clone normally removes its own destination.
        # Preserve an unexpected remaining directory rather than deleting it.
        assert not target.exists(), first.stderr.decode(errors='replace')
        subprocess.run(command + ['--no-hardlinks', str(project), str(target)], check=True, capture_output=True)
    git(target, 'checkout', '--detach', ref)
    return {'first_clone_exit': first.returncode, 'head': git(target, 'rev-parse', 'HEAD')}


def replace_once(repo, entry):
    path = repo / entry['file']
    assert path.resolve().is_relative_to(repo.resolve()), path
    old = path.read_bytes()
    find, replacement = entry['find'].encode(), entry['replace'].encode()
    assert old.count(find) == 1, (entry['file'], old.count(find))
    path.write_bytes(old.replace(find, replacement, 1))
    return old


def audit():
    # Reuse the actual runner's schema without creating __pycache__ files.
    config_count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
    for index, project in enumerate(PROJECTS, config_count):
        os.environ[f'GIT_CONFIG_KEY_{index}'] = 'safe.directory'
        os.environ[f'GIT_CONFIG_VALUE_{index}'] = project.as_posix()
    os.environ['GIT_CONFIG_COUNT'] = str(config_count + len(PROJECTS))
    spec = importlib.util.spec_from_file_location('delegation_runner', ROOT / 'scripts/run_delegation_eval.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    config = runner.load_scenarios(SUITE / 'scenarios.json')
    scenarios = config['scenarios']
    assert len(scenarios) == 12
    assert config['incomplete_markers'] == ['미완료', '완료하지 못', '구현하지 못', '끝내지 못',
                                           '마치지 못', 'could not complete', 'unable to complete',
                                           'did not finish', 'not finished']
    v1 = json.loads((SUITE.parent / 'delegation-v1/scenarios.json').read_text(encoding='utf-8'))
    anchor = next(s for s in scenarios if s['id'] == 'rule-all-paths')
    old_anchor = next(s for s in v1['scenarios'] if s['id'] == 'rule-all-paths')
    # load_scenarios normalizes native Windows project spelling.
    old_anchor['project'] = str(Path(old_anchor['project']).resolve())
    assert anchor == old_anchor, 'anchor scenario changed'
    assert not ({s['id'] for s in scenarios if s is not anchor} & {s['id'] for s in v1['scenarios']})
    rows = []
    for scenario in scenarios:
        started = time.monotonic()
        ident = scenario['id']
        assert scenario['links'] == ['node_modules']
        assert scenario['budget_seconds'] == (2700 if 'prompts' in scenario else 1800)
        if 'prompts' in scenario:
            assert len(scenario['prompts']) == 2
        prompts = scenario.get('prompts', [scenario.get('prompt', '')])
        assert all('???' not in prompt and '\ufffd' not in prompt for prompt in prompts), 'Prompt text is corrupted'
        regression = scenario['regression']
        assert not any(t in regression for t in ('*', 'Skill_Management', 'delegation-v', '--changed'))
        assert 2 <= len(scenario['probes']) <= 3
        hidden_destinations = [p for h in scenario['hidden'] for p in h['files']]
        assert all(p not in regression for p in hidden_destinations)
        if Path(scenario['project']).name == 'labeler':
            assert regression.startswith('set "WRANGLER_LOG_PATH=.work\\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false')
        reference = SUITE / 'reference' / f'{ident}.patch'
        assert reference.is_file() and reference.stat().st_size > 0, reference
        target = TEMP / f'audit-final-{ident}'
        if target.exists():
            assert target.resolve().parent == TEMP.resolve()
            assert git(target, 'rev-parse', 'HEAD') == scenario['ref']
            # Resume only an already-applied reference in this audit's owned clone.
            subprocess.run(['git', '-C', str(target), 'apply', '--reverse', '--check', str(reference)],
                           check=True, capture_output=True)
            row = {'id': ident, 'head': scenario['ref'], 'reused_audit_clone': True}
        else:
            row = {'id': ident, **clone(Path(scenario['project']), target, scenario['ref'])}
            if scenario.get('fault'):
                replace_once(target, scenario['fault'])
            subprocess.run(['git', '-c', f'safe.directory={target.as_posix()}', '-C', str(target),
                            'apply', '--check', str(reference)], check=True, capture_output=True)
            subprocess.run(['git', '-c', f'safe.directory={target.as_posix()}', '-C', str(target),
                            'apply', str(reference)], check=True, capture_output=True)
        row['reference_applied'] = True
        if ident in ('a-offer-quantity-all-paths', 'a-product-source-stale-all-paths', 'a-import-offer-sequence'):
            dependency = TEMP.parent / 'eval-deps/labeler/node_modules'
            assert (dependency / 'typescript/bin/tsc').is_file()
            if not (target / 'node_modules').exists():
                subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(target / 'node_modules'), str(dependency)],
                               check=True, capture_output=True)
            assert (target / 'node_modules').resolve() == dependency.resolve()
            compile_started = time.monotonic()
            compiler = subprocess.run(['node', 'node_modules/typescript/bin/tsc', '-p', 'tsconfig.worker.json',
                                       '--noEmit', '--incremental', 'false', '--pretty', 'false'],
                                      cwd=target, capture_output=True, timeout=90)
            log = SUITE / 'evidence' / f'audit-{ident}-typecheck.log'
            log.write_bytes(compiler.stdout + compiler.stderr)
            row['typecheck'] = {'exit': compiler.returncode, 'seconds': round(time.monotonic() - compile_started, 3),
                                'command': 'node node_modules/typescript/bin/tsc -p tsconfig.worker.json --noEmit --incremental false --pretty false'}
            assert compiler.returncode == 0, log.read_text(encoding='utf-8', errors='replace')
        row['probes_exact_once'] = []
        for probe in scenario['probes']:
            original = replace_once(target, probe)
            (target / probe['file']).write_bytes(original)
            row['probes_exact_once'].append(probe['name'])
        for hidden in scenario['hidden']:
            for dest, source in hidden['files'].items():
                data = (SUITE / source).read_bytes()
                assert data
                if scenario is anchor:
                    assert data == (SUITE.parent / 'delegation-v1' / source).read_bytes()
        if scenario is anchor:
            assert reference.read_bytes() == (SUITE.parent / 'delegation-v1/reference/rule-all-paths.patch').read_bytes()
        row['seconds'] = round(time.monotonic() - started, 3)
        rows.append(row)
        save('asset-audit-progress.json', rows)
        print(ident, 'PASS', flush=True)
    save('asset-audit.json', rows)
    manifest = {p.relative_to(SUITE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(SUITE.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS.json'}
    save('../SHA256SUMS.json', manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'compare', 'audit', 'cleanup-preview', 'cleanup'])
    args = parser.parse_args()
    if args.action == 'snapshot':
        save('source-before.json', snapshot())
    elif args.action == 'compare':
        after = snapshot()
        before = json.loads((SUITE / 'evidence/source-before.json').read_text(encoding='utf-8'))
        save('source-after.json', after)
        assert before == after, 'Source checkout changed; inspect concurrent ownership before attributing it.'
        print('Source HEAD, status and tracked diff unchanged.')
    elif args.action == 'audit':
        audit()
    else:
        cleanup(delete=args.action == 'cleanup')
