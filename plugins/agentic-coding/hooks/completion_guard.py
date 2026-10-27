"""Stop hook: block one completion when code was edited after the turn's last executed command,
or when a behavior change was never handed to an independent verifier.

It reads only the host transcript and never runs project commands. Passing it is not
verification; it only prevents finishing on an unobserved final edit, or on an unchecked
change, without a stated reason.
"""
import json
import os
from pathlib import Path
import re
import sys

EDIT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}
EXEC_TOOLS = {'Bash', 'PowerShell'}
AGENT_TOOLS = {'Agent', 'Task'}
VERIFIER_MARKER = 'INDEPENDENT VERIFIER'  # first words of the independent-check template
# Below this many changed code lines in a turn, the edit counts as trivial for the independent check.
CHECK_MIN_LINES = 5
DOC_SUFFIXES = {'.md', '.markdown', '.mdx', '.txt', '.rst', '.adoc'}
# Segments that inspect or record but do not exercise behavior.
INSPECTION = re.compile(r'^\s*(?:git\s+(?:status|diff|log|show|add|commit|branch|rev-parse|restore|stash|checkout)\b'
                        r'|(?:ls|dir|cat|type|head|tail|grep|rg|find|echo|pwd|cd|wc|sed\s+-n|Get-Content|'
                        r'Get-ChildItem|Set-Location|Select-String|Write-Output)\b|$)', re.IGNORECASE)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?\n\s*\2[ \t]*(?=\n|$)", re.DOTALL)
TARGET = r"""['"]?([^\s'";&|<>]+)['"]?"""
# Shell segments that change files: they are edits, never evidence that behavior ran.
SHELL_WRITES = [re.compile(pattern, re.IGNORECASE) for pattern in (
    r'^\s*(?:cat|echo|printf)\b[^>]*>>?\s*' + TARGET,
    r'^\s*(?:sed|perl)\s+(?:-\w*i\w*|--in-place)\b.*\s' + TARGET + r'\s*$',
    r'^\s*tee\s+(?:-a\s+)?' + TARGET,
    r'^\s*(?:Set-Content|Add-Content|Out-File)\b.*?(?:-(?:Literal)?(?:File)?Path\s+)?' + TARGET,
)]


def shell_events(command):
    """Ordered edit/exec events of one shell command; heredoc bodies are data, not commands."""
    events = []
    for part in re.split(r'&&|\|\||;|\||\n', HEREDOC.sub(lambda match: match.group(3), command)):
        target = next((match.group(1) for pattern in SHELL_WRITES for match in [pattern.search(part)] if match), None)
        if target:
            events.append(('edit', target))
        elif not INSPECTION.match(part):
            events.append(('exec', part.strip()))
    return events


def changed_lines(name, arguments):
    if name == 'MultiEdit':
        return sum(str(e.get('new_string') or '').count('\n') + 1 for e in arguments.get('edits') or [] if isinstance(e, dict))
    text = arguments.get('new_string') if name == 'Edit' else arguments.get('content', arguments.get('new_source'))
    return str(text or '').count('\n') + 1


def turn_events(transcript):
    """Edits (with changed line counts), executions and verifier launches after the latest human prompt."""
    events = []
    for line in transcript.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get('message') if isinstance(entry, dict) else None
        if not isinstance(message, dict):
            continue
        content = message.get('content')
        if entry.get('type') == 'user' and not entry.get('isMeta') and (
                isinstance(content, str) or isinstance(content, list) and any(
                    isinstance(block, dict) and block.get('type') == 'text' for block in content)):
            events = []
            continue
        if entry.get('type') != 'assistant' or not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get('type') != 'tool_use':
                continue
            arguments = block.get('input') or {}
            if block.get('name') in EDIT_TOOLS:
                events.append(('edit', str(arguments.get('file_path') or arguments.get('notebook_path') or ''),
                               changed_lines(block['name'], arguments)))
            elif block.get('name') in EXEC_TOOLS:
                # A shell write's size is unknown; it counts as one line.
                events.extend((kind, value, 1) for kind, value in shell_events(str(arguments.get('command') or '')))
            elif block.get('name') in AGENT_TOOLS and VERIFIER_MARKER in str(arguments.get('prompt') or ''):
                events.append(('verify', '', 0))
    return events


def exercises_behavior(command):
    return any(kind == 'exec' for kind, _ in shell_events(command))


def code_file(value, root):
    """Project-relative path of a code file, or None for documentation and files outside the project."""
    if not value:
        return None
    path = Path(value)
    path = path if path.is_absolute() else root / path
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        return None  # Scratch or other-project files are outside this guard.
    return None if path.suffix.lower() in DOC_SUFFIXES else relative.as_posix()


def unobserved_edits(events, root):
    pending = []
    for kind, value, _ in events:
        if kind == 'exec':
            pending = []
        elif kind == 'edit' and code_file(value, root) and code_file(value, root) not in pending:
            pending.append(code_file(value, root))
    return pending


def unchecked_lines(events, root):
    """Changed code lines in the turn when no independent verifier ran after the first code edit."""
    lines, verified = 0, False
    for kind, value, count in events:
        if kind == 'edit' and code_file(value, root):
            lines += count
        elif kind == 'verify' and lines:
            verified = True
    return 0 if verified else lines


def guard(payload):
    if payload.get('stop_hook_active') or os.environ.get('AGENT_COMPLETION_GUARD', '').lower() == 'off':
        return {}
    transcript, cwd = payload.get('transcript_path'), payload.get('cwd')
    if not transcript or not cwd or not Path(transcript).is_file():
        return {}
    events, root = turn_events(Path(transcript)), Path(cwd).resolve()
    pending, lines = unobserved_edits(events, root), unchecked_lines(events, root)
    reasons = []
    if pending:
        shown = ', '.join(pending[:5]) + (f' (+{len(pending) - 5} more)' if len(pending) > 5 else '')
        reasons.append(f'{len(pending)} code file(s) changed after the last executed command in this turn: {shown}. '
                       'Run the affected check or flow against the final edit and report the observation, or state '
                       'explicitly why no execution applies (for example descriptive-only change or unavailable runner).')
    if lines >= CHECK_MIN_LINES:
        reasons.append(f'{lines} changed code line(s) were not handed to an independent verifier. Launch one with only '
                       "the user's request verbatim and the diff (agent-workflow references/independent-check.md), "
                       'or state on the card why the change is trivial.')
    if not reasons:
        return {}
    return {'decision': 'block', 'reason': 'Completion guard: ' + ' '.join(reasons) + ' This guard blocks once.'}


def main():
    try:
        # Hosts send UTF-8 JSON; the Windows locale codec would garble non-ASCII paths.
        result = guard(json.loads(sys.stdin.buffer.read().decode('utf-8-sig')))
    except (OSError, ValueError, TypeError, AttributeError):
        result = {}  # A guard failure must not trap the session.
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
