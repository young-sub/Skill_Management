# Generated file. Do not edit directly.
# Source: authoring/scripts/blast_radius_check.py
# Source-SHA256: c3a5843348c74fd394b60de0fd65101888daed601c129ce8f3f63aa8d5f9dba3

"""Read-only check that delegated agents run inside a boundary instead of behind per-action approvals.

It reports, and changes nothing:
- worktree   the checkout is a linked Git worktree, so a task's changes stay in their own tree;
- deny       the project's Claude Code `Bash(...)` deny rules actually match sample force pushes,
             remote branch deletions and the given deploy commands, and writes outside the working
             directories are blocked;
- secrets    no environment variable that looks like a credential is set (names only).

Deny rules are a backstop: branch protection on the server and the absence of credentials are what
make a force push or deploy impossible. Applying settings or removing credentials is the person's
decision; this script never does it.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# Spellings a deny list must stop; each is matched against the Bash rules as Claude Code does.
SAMPLES = ('git push --force', 'git push origin --force main', 'git push -f origin main', 'git push --force-with-lease',
           'git push origin --delete feature', 'git push upstream --delete feature', 'git push origin :feature')
SECRET_NAME = re.compile(r'(^|_)(PROD|PRODUCTION|LIVE|TOKEN|SECRET|PASSWORD|PASSWD|APIKEY)(_|$)|PRIVATE_KEY|API_KEY|'
                         r'ACCESS_KEY|DATABASE_URL|CREDENTIAL', re.IGNORECASE)


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def bash_rule(rule):
    """A compiled matcher for a `Bash(<pattern>)` rule: `*` is any text and a trailing `:*` any suffix."""
    match = re.fullmatch(r'\s*Bash\((.*)\)\s*', rule)
    if not match:
        return None
    pattern = match.group(1).strip()
    if pattern.endswith(':*'):
        pattern = pattern[:-2] + '*'
    return re.compile('^' + '.*'.join(map(re.escape, pattern.split('*'))) + ('' if pattern.endswith('*') else '$'))


def settings(root):
    merged = {'deny': [], 'block_outside': False, 'files': []}
    for name in ('.claude/settings.json', '.claude/settings.local.json'):
        path = root / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            continue
        permissions = data.get('permissions') or {}
        merged['files'].append(name)
        merged['deny'] += [str(rule) for rule in permissions.get('deny') or []]
        merged['block_outside'] |= permissions.get('blockWritesOutsideWorkingDirectories') is True
    return merged


def check(root, deploy, environment):
    findings = []
    git_dir, common = git(root, 'rev-parse', '--absolute-git-dir'), git(root, 'rev-parse', '--git-common-dir')
    if git_dir is None:
        findings.append({'check': 'worktree', 'status': 'MISSING', 'detail': 'not a Git checkout'})
    else:
        common_path = (root / common).resolve() if common and not Path(common).is_absolute() else Path(common or '')
        linked = Path(git_dir).resolve() != common_path.resolve()
        findings.append({'check': 'worktree', 'status': 'OK' if linked else 'MISSING',
                         'detail': 'linked worktree' if linked else 'main checkout: run delegated tasks in `git worktree add` trees'})
    configured = settings(root)
    matchers = [m for m in map(bash_rule, configured['deny']) if m]
    unmatched = [command for command in (*SAMPLES, *deploy) if not any(m.search(command) for m in matchers)]
    findings.append({'check': 'deny', 'status': 'OK' if not unmatched and configured['block_outside'] else 'MISSING',
                     'detail': ('commands no Bash deny rule stops: ' + ', '.join(unmatched) if unmatched else 'deny rules match') +
                               ('' if configured['block_outside'] else '; blockWritesOutsideWorkingDirectories is not true'),
                     'files': configured['files']})
    exposed = sorted(name for name, value in environment.items() if value and SECRET_NAME.search(name))
    findings.append({'check': 'secrets', 'status': 'OK' if not exposed else 'MISSING',
                     'detail': 'credential-like variables set: ' + ', '.join(exposed) if exposed else 'none set'})
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--deploy', nargs='*', default=[], help='deploy or production commands that must be denied')
    args = parser.parse_args(argv)
    findings = check(args.root.resolve(), args.deploy, dict(os.environ))
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    return int(any(f['status'] != 'OK' for f in findings))


if __name__ == '__main__':
    sys.exit(main())
