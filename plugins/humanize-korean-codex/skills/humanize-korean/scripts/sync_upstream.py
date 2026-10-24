"""Keep a runnable copy of the upstream im-not-ai Codex skill under CODEX_HOME.

The upstream codex/ folder resolves its scripts from the repository root and its
references through a symlink, so it only works from a full checkout with real
directories. This script maintains that checkout (`repo/`) and a materialized copy
(`runtime/`), then prints JSON with the `skill_root` to follow. Exit 0 means a
usable copy exists (possibly stale); exit 2 means there is none, with a reason.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

UPSTREAM = 'https://github.com/epoko77-ai/im-not-ai.git'
SKILL = Path('codex/skills/humanize-korean')
STAMP = '.sync.json'


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def read_stamp(runtime):
    try:
        return json.loads((runtime / STAMP).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def materialize(repo, target):
    """Copy the checkout without .git and replace symlink entries with real content."""
    shutil.copytree(repo, target, ignore=shutil.ignore_patterns('.git'), symlinks=False)
    listed = git('ls-files', '-s', '-z', cwd=repo)
    if listed.returncode:
        raise RuntimeError('git ls-files failed: ' + listed.stderr.strip())
    root = repo.resolve()
    for record in filter(None, listed.stdout.split('\0')):
        meta, path = record.split('\t', 1)
        if not meta.startswith('120000 '):
            continue
        link = target / path
        if link.is_dir() and not link.is_symlink():
            continue  # copytree already followed a real symlink
        # Without symlink support git checks the link out as a file holding its target.
        source = repo / path
        destination = os.readlink(source) if source.is_symlink() else source.read_text(encoding='utf-8').strip()
        resolved = (source.parent / destination).resolve()
        if root not in resolved.parents:
            raise RuntimeError(f'symlink {path} points outside the repository')
        if link.is_symlink() or link.exists():
            link.unlink()
        if resolved.is_dir():
            shutil.copytree(resolved, link, symlinks=False)
        elif resolved.is_file():
            shutil.copy2(resolved, link)
        else:
            raise RuntimeError(f'symlink {path} target is missing')


def usable(runtime):
    skill = runtime / SKILL
    return (skill / 'SKILL.md').is_file() and (skill / 'references').is_dir() and (runtime / 'scripts').is_dir()


def result(status, runtime, message='', code=0):
    stamp = read_stamp(runtime) or {}
    print(json.dumps({'status': status, 'skill_root': str((runtime / SKILL).resolve()) if code == 0 else None,
                      'commit': stamp.get('commit'), 'synced_at': stamp.get('synced_at'),
                      'message': message}, ensure_ascii=False))
    return code


def sync(home, source, max_age_hours, refresh):
    base = home / 'vendor' / 'im-not-ai'
    repo, runtime = base / 'repo', base / 'runtime'
    stamp = read_stamp(runtime)
    have = stamp is not None and usable(runtime)
    if have and not refresh:
        synced = datetime.datetime.fromisoformat(stamp['synced_at'])
        if now() - synced < datetime.timedelta(hours=max_age_hours):
            return result('current', runtime)

    def fail(message):
        if have:
            return result('stale', runtime, message + ' Using the copy from ' + stamp['synced_at'] + '.')
        return result('unavailable', runtime, message, code=2)

    if shutil.which('git') is None:
        return fail('git is not installed or not on PATH.')
    if (repo / '.git').exists():
        origin = git('remote', 'get-url', 'origin', cwd=repo)
        if origin.returncode or origin.stdout.strip() != source:
            return fail(f'{repo} is not a checkout of {source}; leaving it untouched.')
        fetched = git('fetch', '--depth', '1', 'origin', 'HEAD', cwd=repo)
        if fetched.returncode:
            return fail('Could not fetch ' + source + ' (network access is required): ' + fetched.stderr.strip())
        reset = git('reset', '--hard', 'FETCH_HEAD', cwd=repo)
        if reset.returncode:
            return fail('Could not update the checkout: ' + reset.stderr.strip())
    else:
        if repo.exists():
            return fail(f'{repo} exists but is not a Git checkout; leaving it untouched.')
        base.mkdir(parents=True, exist_ok=True)
        partial = base / 'repo.partial'
        shutil.rmtree(partial, ignore_errors=True)
        cloned = git('clone', '--depth', '1', source, str(partial))
        if cloned.returncode:
            shutil.rmtree(partial, ignore_errors=True)
            return fail('Could not clone ' + source + ' (network access is required): ' + cloned.stderr.strip())
        partial.rename(repo)
    commit = git('rev-parse', 'HEAD', cwd=repo).stdout.strip()
    stamp_data = {'source': source, 'commit': commit, 'synced_at': now().isoformat()}
    if have and stamp.get('commit') == commit:
        (runtime / STAMP).write_text(json.dumps(stamp_data), encoding='utf-8')
        return result('current', runtime)

    fresh, old = base / 'runtime.new', base / 'runtime.old'
    for leftover in (fresh, old):
        shutil.rmtree(leftover, ignore_errors=True)
    try:
        materialize(repo, fresh)
    except (OSError, RuntimeError) as error:
        shutil.rmtree(fresh, ignore_errors=True)
        return fail(f'Could not prepare commit {commit[:12]}: {error}')
    if not usable(fresh):
        shutil.rmtree(fresh, ignore_errors=True)
        return fail(f'Upstream commit {commit[:12]} no longer has a complete {SKILL.as_posix()} skill.')
    (fresh / STAMP).write_text(json.dumps(stamp_data), encoding='utf-8')
    if runtime.exists():
        runtime.rename(old)
    fresh.rename(runtime)
    shutil.rmtree(old, ignore_errors=True)
    return result('updated' if have else 'installed', runtime)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--home', help='Codex home (default: CODEX_HOME or ~/.codex)')
    parser.add_argument('--source', default=UPSTREAM, help=argparse.SUPPRESS)
    parser.add_argument('--max-age-hours', type=float, default=24.0)
    parser.add_argument('--refresh', action='store_true', help='fetch now regardless of age')
    args = parser.parse_args(argv)
    home = Path(args.home or os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    return sync(home, args.source, args.max_age_hours, args.refresh)


if __name__ == '__main__':
    sys.exit(main())
