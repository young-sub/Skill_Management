"""Guard a local Agentic Coding plugin update; recover backups to a new directory.

Explicit homes only. Stop other plugin installers before updating. The native
host still owns installation; this is local preservation, not a security boundary.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib


def checked_path(value):
    path = Path(value).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError(f'Aliased path refused: {part}')
    return path.resolve()


def files(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if not checked_path(path).is_relative_to(root):
            raise ValueError(f'Path escapes package root: {path}')
        name = path.relative_to(root).as_posix()
        if any(p.lower().startswith(('.env', '.dev.vars')) or p.lower() in
               {'auth.json', 'credentials', 'secrets'} for p in path.relative_to(root).parts):
            raise ValueError(f'Private path refused without reading: {name}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f'Non-file refused: {name}')
        result[name] = path
    return result


def hashes(paths):
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}


def package(root, allow_bytecode=False):
    paths = files(root)
    inventory = json.loads((root / 'package-files.json').read_text(encoding='utf-8'))['files']
    expected = set(inventory) | {'package-files.json'}
    extra = set(paths) - expected
    if allow_bytecode:
        # Only interpreter cache beside an existing source; still backed up.
        extra = {name for name in extra if not (
            Path(name).parent.name == '__pycache__' and
            re.fullmatch(r'.+\.cpython-\d+(?:\.opt-\d+)?\.pyc', Path(name).name) and
            (Path(name).parent.parent / (Path(name).name.split('.cpython-')[0] + '.py')).as_posix() in inventory)}
    changed = sorted(extra | (expected - set(paths)))
    if changed:
        raise ValueError('Unrecognized or missing package files: ' + ', '.join(changed))
    actual = hashes(paths)
    changed = [name for name, value in inventory.items() if actual.get(name) != value]
    if changed:
        raise ValueError('Modified package files: ' + ', '.join(changed))
    manifest = json.loads((root / 'plugin.json').read_text(encoding='utf-8'))
    if manifest['name'] != 'agentic-coding' or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', manifest['version']):
        raise ValueError('Invalid plugin identity')
    return manifest, actual


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def copy_new(paths, destination):
    destination.mkdir(parents=True, exist_ok=False)
    for name, source in paths.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(source.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())


@contextmanager
def update_lock(home):
    path = home / 'plugins/.agentic-coding-update.lock'
    checked_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Closing releases the OS lock, including on wrapper termination.
        yield


def update(home, marketplace, backup, run=subprocess.run, *, resume_from=None):
    home, marketplace, backup = map(checked_path, (home, marketplace, backup))
    if not home.is_dir():
        raise ValueError('An existing explicit home is required')
    if any(a.is_relative_to(b) or b.is_relative_to(a) for a, b in
           ((backup, home), (backup, marketplace), (home, marketplace))):
        raise ValueError('Home, marketplace and backup must be separate trees')
    descriptor_path = checked_path(marketplace / '.agents/plugins/marketplace.json')
    descriptor = json.loads(descriptor_path.read_text(encoding='utf-8'))
    name = descriptor['name']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', name):
        raise ValueError('Invalid marketplace name')
    matches = [item for item in descriptor['plugins'] if item['name'] == 'agentic-coding']
    if len(matches) != 1 or matches[0]['source'] != {'source': 'local', 'path': './plugins/agentic-coding'}:
        raise ValueError('Expected one local plugins/agentic-coding source')
    candidate = checked_path(marketplace / 'plugins/agentic-coding')
    identity, expected = package(candidate)
    cache = checked_path(home / 'plugins/cache' / name / 'agentic-coding')
    with update_lock(home):
        if resume_from is not None:
            resume_from = checked_path(resume_from)
            if backup.is_relative_to(resume_from) or resume_from.is_relative_to(backup):
                raise ValueError('Resume backup must be separate from original backup')
            snapshot_path = checked_path(resume_from / 'snapshot.json')
            snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
            if ((resume_from / 'completed.json').exists() or
                    snapshot.get('home') != str(home) or snapshot.get('marketplace') != name or
                    snapshot.get('candidate') != identity or snapshot.get('candidate_files') != expected):
                raise ValueError('Resume requires the original interrupted update and identical candidate bytes')
            previous_hashes = hashes(files(checked_path(resume_from / 'previous')))
            if previous_hashes != snapshot.get('files'):
                raise ValueError('Invalid resume snapshot')
            candidate_hashes = {identity['version'] + '/' + key: value for key, value in expected.items()}
            if any(value not in (previous_hashes.get(key), candidate_hashes.get(key))
                   for key, value in hashes(files(cache)).items()):
                raise ValueError('Resume refuses unattributed or modified cache files')
        elif not cache.is_dir():
            raise ValueError('No installed plugin to update; use native installation first')
        for version in (() if resume_from is not None else cache.iterdir()):
            if not version.is_dir():
                raise ValueError(f'Unrecognized cache entry: {version.name}')
            installed, _ = package(checked_path(version), allow_bytecode=True)
            if installed['version'] != version.name:
                raise ValueError('Installed version directory mismatch')
        target = cache / identity['version']
        same_version = False
        if target.exists():
            try:
                _, actual = package(target, allow_bytecode=True)
                if all(actual.get(key) == value for key, value in expected.items()):
                    same_version = True
                else:
                    raise ValueError('Same version has different bytes; build a new version')
            except (ValueError, FileNotFoundError):
                if resume_from is None:
                    raise
        config_path = checked_path(home / 'config.toml')

        def registration():
            config = tomllib.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
            return config.get('marketplaces', {}).get(name)

        registered = registration()
        if registered is not None and registered.get('source_type') != 'local':
            raise ValueError('Replacing a non-local marketplace is outside this local update scope')

        def matches_source(value):
            if value is None or value.get('source_type') != 'local':
                return False
            source = checked_path(value['source'])
            return source.exists() and source.samefile(marketplace)

        bound = matches_source(registered)
        if same_version and bound:
            return {'status': 'UNCHANGED', 'installed': str(target)}
        previous = files(cache)
        before = hashes(previous)
        backup.mkdir(parents=True, exist_ok=False)
        copy_new(previous, backup / 'previous')
        if hashes(files(backup / 'previous')) != before or hashes(files(cache)) != before:
            raise ValueError('Cache changed during snapshot; native update not started')
        write_json(backup / 'snapshot.json', {'files': before, 'home': str(home),
                   'marketplace': name, 'candidate': identity,
                   'candidate_files': expected,
                   'previous_source': registered})
        # Native commands preserve unrelated config; never copy home/auth/config.
        env = dict(os.environ, CODEX_HOME=str(home))
        def native(arguments):
            argv = ['codex', 'plugin', *arguments, '--json']
            result = run(argv, env=env, cwd=home, check=True, capture_output=True)
            if result.returncode:
                raise subprocess.CalledProcessError(result.returncode, argv)
            return result

        if hashes(files(cache)) != before:
            raise ValueError('Cache changed before native update; snapshot retained')
        if not bound:
            if registered is not None:
                native(['marketplace', 'remove', name])
            native(['marketplace', 'add', str(marketplace)])
            current = registration()
            if not matches_source(current):
                raise ValueError('Native marketplace registration mismatch; snapshot retained')
        if same_version:
            if hashes(files(cache)) != before:
                raise ValueError('Cache changed during source binding; snapshot retained')
            write_json(backup / 'completed.json', {'installed': str(target), 'source': str(marketplace)})
            return {'status': 'REBOUND', 'installed': str(target), 'backup': str(backup)}
        result = native(['add', f'agentic-coding@{name}'])
        receipt = json.loads(result.stdout)
        if (receipt.get('pluginId') != f'agentic-coding@{name}' or
                receipt.get('version') != identity['version'] or
                checked_path(receipt.get('installedPath', '')) != target):
            raise ValueError('Native installation identity mismatch; snapshot retained')
        _, actual = package(checked_path(target), allow_bytecode=True)
        if any(actual.get(key) != value for key, value in expected.items()):
            raise ValueError('Installed bytes differ from inspected candidate; backup retained')
        write_json(backup / 'completed.json', {'installed': str(target), 'native': receipt})
        return {'status': 'UPDATED', 'installed': str(target), 'backup': str(backup)}


def recover(backup, output):
    backup, output = map(checked_path, (backup, output))
    if output.exists():
        raise FileExistsError(output)
    if output.is_relative_to(backup) or backup.is_relative_to(output):
        raise ValueError('Recovery output must be separate from backup')
    checked_path(backup / 'snapshot.json')
    snapshot = json.loads((backup / 'snapshot.json').read_text(encoding='utf-8'))
    home = checked_path(snapshot['home'])
    if output.is_relative_to(home) or home.is_relative_to(output):
        raise ValueError('Recovery output must be separate from installation home')
    expected = snapshot['files']
    previous = files(checked_path(backup / 'previous'))
    if not expected or hashes(previous) != expected:
        raise ValueError('Invalid snapshot; nothing restored')
    copy_new(previous, output)
    if hashes(files(output)) != expected:
        raise ValueError('Recovery bytes differ; original backup retained')
    return {'status': 'RECOVERED', 'output': str(output), 'scope': 'export only; active cache unchanged'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    update_parser = actions.add_parser('update')
    for option in ('home', 'marketplace', 'backup'):
        update_parser.add_argument('--' + option, type=Path, required=True)
    update_parser.add_argument('--resume-from', type=Path, help='Verified backup of an interrupted update with identical candidate bytes')
    recovery_parser = actions.add_parser('recover')
    for option in ('backup', 'output'):
        recovery_parser.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (update(args.home, args.marketplace, args.backup, resume_from=args.resume_from) if args.action == 'update'
                  else recover(args.backup, args.output))
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
