"""Rebuild a past attempt's final diff by re-running its file-changing tool calls on a fresh clone.

Edit/Write/MultiEdit calls are applied directly. Shell calls that may write are re-run in order with
`npm`/`npx` replaced by no-ops, so test runs do not execute; edits made by Python or sed scripts replay
against the same file state they originally saw. The result is a patch against the pinned ref (commits the
attempt made are folded back into the working tree). Fidelity is judged afterwards by `replay.py precheck`:
the rebuilt diff must reproduce the recorded regression and hidden outcome.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'evals/path-check-offline/tools'))
import run as offline  # noqa: E402  (reuses the delegation runner's clone and cleanup helpers)

runner = offline.runner
WORK_ROOT = Path('C:/e/w')
SHELLS = {'Bash', 'PowerShell'}
EDITS = {'Edit', 'Write', 'MultiEdit'}
# Shell calls that can change files. Others (reads, test runs) are skipped.
MAY_WRITE = re.compile(r"sed\s+-i|perl\s+-\w*i|(?<![0-9&])>>?\s*[^&|\s]|Set-Content|Out-File|Add-Content|writeFile|"
                       r"write_text|write_bytes|open\([^)]*['\"][wa]b?['\"]|\.write\(|\bgit\s+(apply|checkout|restore|"
                       r"stash|reset|rm|mv|switch)\b|\b(cp|mv|rm|mkdir|touch)\s|Copy-Item|Move-Item|Remove-Item|"
                       r"New-Item|unlink|rmdir")
SKIP = re.compile(r'/tmp/|cygpath')  # the attempt's own scratch outside the repository
SHIM = '#!/bin/sh\nexit 0\n'
# The attempts ran in Git Bash; a bare `bash` on Windows resolves to WSL first.
BASH = 'C:/Program Files/Git/usr/bin/bash.exe' if os.name == 'nt' else 'bash'


def calls(transcript):
    """Ordered tool_use blocks with their tool_result error flag, and the session cwd."""
    uses, errors, cwd = [], {}, None
    for line in Path(transcript).read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        cwd = cwd or (event.get('cwd') if event.get('type') == 'system' else None)
        message = event.get('message')
        content = message.get('content') if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                uses.append(block)
            elif isinstance(block, dict) and block.get('type') == 'tool_result':
                errors[block.get('tool_use_id')] = bool(block.get('is_error'))
    return [(u, errors.get(u.get('id'))) for u in uses], cwd


def spellings(path):
    forward = path.replace('\\', '/')
    drive, rest = forward[0], forward[2:]
    return sorted({forward, forward.replace('/', '\\'), f'/{drive.lower()}{rest}', f'/{drive.upper()}{rest}',
                   drive.lower() + forward[1:], drive.upper() + forward[1:]}, key=len, reverse=True)


def rebase(text, old, new):
    for spelling in spellings(old):
        text = text.replace(spelling, new.replace('\\', '/') if '/' in spelling else new.replace('/', '\\'))
    return text


def apply_edit(repo, old_root, block, log):
    name, args = block['name'], block.get('input') or {}
    target = Path(rebase(str(args.get('file_path') or ''), old_root, str(repo)))
    if not target.resolve().is_relative_to(repo.resolve()):
        log.append(f'skip outside repo: {target}')
        return
    if name == 'Write':
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(str(args.get('content') or '').encode('utf-8'))
        return
    text = target.read_bytes().decode('utf-8')
    edits = args.get('edits') if name == 'MultiEdit' else [args]
    for edit in edits:
        old, new = edit['old_string'], edit['new_string']
        if old not in text and '\r\n' in text:  # the host matches LF edits against CRLF files
            old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
        if old not in text:
            log.append(f'EDIT MISS {target.name}: {old[:80]!r}')
            continue
        text = text.replace(old, new) if edit.get('replace_all') else text.replace(old, new, 1)
    target.write_bytes(text.encode('utf-8'))


def run_shell(repo, old_root, block, shim, log):
    command = rebase(str((block.get('input') or {}).get('command') or ''), old_root, str(repo))
    if block['name'] != 'Bash' or not MAY_WRITE.search(command) or SKIP.search(command):
        return False
    env = dict(os.environ, PATH=f'{shim}{os.pathsep}{os.environ["PATH"]}')
    try:
        done = subprocess.run([BASH, '-c', command], cwd=repo, env=env, capture_output=True, timeout=180)
        log.append(f'shell exit {done.returncode}: {command[:120]!r}')
    except subprocess.TimeoutExpired:
        log.append(f'shell TIMEOUT: {command[:120]!r}')
    return True


def reconstruct(attempt, out_dir):
    config = runner.load_scenarios(ROOT / attempt['suite'])
    scenario = next(s for s in config['scenarios'] if s['id'] == attempt['scenario'])
    cell = WORK_ROOT / hashlib.sha256(f'reconstruct/{attempt["id"]}'.encode()).hexdigest()[:8]
    if cell.exists():
        raise SystemExit(f'workspace exists: {cell}')
    repo, shim = cell / 'r', cell / 'shim'
    log = []
    try:
        cell.mkdir(parents=True)
        shim.mkdir()
        for tool in ('npm', 'npx'):
            (shim / tool).write_text(SHIM, newline='\n')
        runner.clone(Path(scenario['project']), repo, ref=scenario['ref'], link_modules=False, log_dir=cell)
        base = offline.git(repo, 'rev-parse', 'HEAD').stdout.decode().strip()
        shell_runs = edits = 0
        for transcript in attempt['transcripts']:
            blocks, old_root = calls(ROOT / transcript if not Path(transcript).is_absolute() else transcript)
            for block, _ in blocks:
                if block.get('name') in EDITS:
                    apply_edit(repo, old_root, block, log)
                    edits += 1
                elif block.get('name') in SHELLS:
                    shell_runs += run_shell(repo, old_root, block, shim, log)
        offline.git(repo, 'reset', '-q', '--soft', base)
        offline.git(repo, 'add', '-A')
        patch = offline.git(repo, 'diff', '--cached', '--binary', base).stdout
        stat = offline.git(repo, 'diff', '--cached', '--stat', base).stdout.decode(errors='replace')
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f'{attempt["id"]}.patch').write_bytes(patch)
        summary = {'id': attempt['id'], 'base': base, 'edits': edits, 'shell_runs': shell_runs,
                   'misses': [line for line in log if 'MISS' in line or 'TIMEOUT' in line], 'stat': stat.splitlines()[-1:]}
        (out_dir / f'{attempt["id"]}.log').write_text('\n'.join(log), encoding='utf-8')
        return summary
    finally:
        if not os.environ.get('RECONSTRUCT_KEEP'):
            runner.kill_owned(cell)
            runner.remove_tree(cell, WORK_ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    attempts = json.loads((SUITE / 'attempts.json').read_text(encoding='utf-8'))['attempts']
    for attempt in attempts:
        if args.only and attempt['id'] not in args.only:
            continue
        print(json.dumps(reconstruct(attempt, SUITE / 'attempts'), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
