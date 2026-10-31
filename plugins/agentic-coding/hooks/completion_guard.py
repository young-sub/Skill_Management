"""Stop hook: block one completion when a behavior change was never handed to an independent verifier.

It reads the host transcript and, for the size of a change, read-only `git diff --numstat`;
it never runs project commands. Passing it is not verification; it only prevents finishing on
an unchecked change without a stated reason.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import posixpath
import re
import subprocess
import sys

EDIT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}
EXEC_TOOLS = {'Bash', 'PowerShell'}
AGENT_TOOLS = {'Agent', 'Task'}
VERIFIER_MARKER = 'INDEPENDENT VERIFIER'  # first words of the independent-check template
# Below this many changed code lines in a turn, the edit counts as trivial for the independent check.
CHECK_MIN_LINES = 5
# The packaged hook lives in <plugin>/hooks/; name the template by its installed path when it exists.
_installed = Path(__file__).resolve().parent.parent / 'skills/agent-workflow/references/independent-check.md'
REFERENCE = str(_installed) if _installed.is_file() else 'agent-workflow references/independent-check.md'
DOC_SUFFIXES = {'.md', '.markdown', '.mdx', '.txt', '.rst', '.adoc'}
OUTPUT_SUFFIXES = {'.log', '.out'}  # captured command output, not code
EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
# Segments that inspect or record but do not exercise behavior.
INSPECTION = re.compile(r'^\s*(?:git\s+(?:status|diff|log|show|add|commit|branch|rev-parse|restore|stash|checkout)\b'
                        r'|(?:ls|dir|cat|type|head|tail|grep|rg|find|echo|pwd|cd|wc|sed\s+-n|Get-Content|'
                        r'Get-ChildItem|Set-Location|Select-String|Write-Output)\b|$)', re.IGNORECASE)
# The body may be empty; the lazy optional keeps one heredoc from swallowing the next.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n(?:.*?\n)??[ \t]*\2[ \t]*(?=\n|$)", re.DOTALL)
TARGET = r"""['"]?([^\s'";&|<>]+)['"]?"""
# Shell segments that change files: they are edits, never evidence that behavior ran.
SHELL_WRITES = [re.compile(pattern, re.IGNORECASE) for pattern in (
    r'^\s*(?:cat|echo|printf)\b[^>]*>>?\s*' + TARGET,
    r'^\s*(?:sed|perl)\s+(?:-\w*i\w*|--in-place)\b.*\s' + TARGET + r'\s*$',
    r'^\s*tee\s+(?:-a\s+)?' + TARGET,
)]
PS_WRITE = re.compile(r'^\s*(?:Set-Content|Add-Content|Out-File)\b(.*)$', re.IGNORECASE | re.DOTALL)
PS_PATH = re.compile(r'-(?:Literal)?(?:File)?Path\s+' + TARGET, re.IGNORECASE)
PS_SWITCHES = {'force', 'nonewline', 'append', 'noclobber', 'passthru', 'whatif', 'confirm'}
CD = re.compile(r'^\s*(?:cd|Set-Location)\s+(?:-Path\s+)?' + TARGET + r'\s*$', re.IGNORECASE)
REDIRECT = re.compile(r'(?<![0-9&>])>>?\s*' + TARGET)
# An interpreter script (heredoc, -c or -e) runs code, and one with a write call also changes files. With a
# turn-start timestamp, changed files are attributed by modification time. Without one, the targets are the
# paths its write calls name, directly or through one variable assignment; a script whose targets cannot be
# read keeps its text so that changed files it names as string literals are attributed to it.
INTERPRETER = re.compile(r'(?:^|[\s(])(?:python3?|py|node|ruby|perl)(?:\.exe)?\s', re.IGNORECASE)
INLINE = re.compile(r'''((?:^|[\s(;&|])(?:python3?|py|node|ruby|perl)(?:\.exe)?\s+(?:-[^\sce-]\S*\s+)*-[ce]\s+)'''
                    r'''(["'])(.*?)(?<!\\)\2''', re.IGNORECASE | re.DOTALL)
WRITE_CALL = re.compile(r'write_text|write_bytes|\.write\(|writeFileSync|appendFileSync|'
                        r'open\([^)]*,\s*(?:mode\s*=\s*)?[\'"][wax]')
LITERAL = r'''[rRbBuUfF]{0,2}(['"])([^'"\n]+?)\1'''
ARGUMENT = r'(?:' + LITERAL + r'|([A-Za-z_]\w*))'
WRITE_TARGETS = [re.compile(pattern) for pattern in (
    r'open\(\s*' + ARGUMENT + r'''\s*,\s*(?:mode\s*=\s*)?[rRbBuU]?['"][rbt+]*[wax]''',
    r'Path\(\s*' + ARGUMENT + r'\s*\)\s*\.\s*write_(?:text|bytes)\(',
    r'(?<![\w.])' + ARGUMENT + r'\s*\.\s*write_(?:text|bytes)\(',
    r'(?:writeFileSync|appendFileSync|writeFile|appendFile|File\.write)\(\s*' + ARGUMENT,
)]
# Paths built at run time (f-strings, globs, joins) cannot be read from the script text.
COMPUTED_PATH = re.compile(r'''[fF][rR]?['"][^'"\n]*\{|\.r?glob\(|\bglob\.|os\.path\.join|\bwalk\(|\)\s*/\s*[\w'"]''')


def script_targets(script):
    """Paths a writing script's write calls name, or None when one of them cannot be resolved."""
    if COMPUTED_PATH.search(script):
        return None
    targets = []
    for pattern in WRITE_TARGETS:
        for match in pattern.finditer(script):
            literal, name = match.group(2), match.group(3)
            if name and name != 'Path':
                assigned = re.findall(r'(?<![\w.])' + re.escape(name) + r'\s*=\s*(?:[\w.]*Path\(\s*)?' + LITERAL, script)
                if not assigned:
                    return None
                literal = assigned[-1][1]
            if literal:
                targets.append(literal)
    return targets or None


def ps_target(arguments):
    """Target of Set-Content/Add-Content/Out-File: -Path anywhere, else the first positional argument."""
    explicit = PS_PATH.search(arguments)
    if explicit:
        return explicit.group(1)
    tokens = arguments.split()
    index = 0
    while index < len(tokens):
        if tokens[index].startswith('-'):
            index += 1 if tokens[index].lstrip('-').lower() in PS_SWITCHES else 2
            continue
        return tokens[index].strip('\'"')
    return None


def within(cwd, target):
    """Join a target to the directory a `cd` earlier in the same command moved to."""
    if os.name == 'nt' and re.match(r'^/[a-zA-Z]/', target):
        target = target[1] + ':' + target[2:]  # MSYS-style /c/... on Windows
    return target if not cwd or Path(target).is_absolute() else posixpath.normpath(posixpath.join(cwd, target))


def shell_events(command):
    """Ordered (kind, value, lines) events of one shell command; heredoc and inline script bodies are
    data, not commands. A heredoc written to a file counts its body lines. A script is an execution; the
    files it writes, including redirected output, are ('output', path) events that are sized but are not
    unobserved edits, or one ('script', text) event when its targets cannot be read."""
    held = {}  # placeholder -> (body, body lines, interpreter script?)

    def hold(body, lines, script):
        key = f'\0{len(held)}\0'
        held[key] = (body, lines, script)
        return key

    def heredoc(match):
        line = command[:match.start()].rsplit('\n', 1)[-1]
        return hold(match.group(0), match.group(0).count('\n') - 1, bool(INTERPRETER.search(' ' + line))) + match.group(3)

    text = INLINE.sub(lambda match: match.group(1) + hold(match.group(3), 1, True), HEREDOC.sub(heredoc, command))
    events, cwd = [], ''
    for part in re.split(r'&&|\|\||;|\||\n', text):
        keys = [key for key in held if key in part]
        for key in keys:
            part = part.replace(key, ' ')
        moved = CD.match(part)
        if moved:
            cwd = within(cwd, moved.group(1))
            continue
        scripts = [held[key][0] for key in keys if held[key][2]]
        target = next((match.group(1) for pattern in SHELL_WRITES for match in [pattern.search(part)] if match), None)
        powershell = PS_WRITE.match(part)
        if target is None and powershell:
            target = ps_target(powershell.group(1))
        if target:
            events.append(('edit', within(cwd, target), max([held[key][1] for key in keys if not held[key][2]] or [1])))
            continue
        if not INSPECTION.match(part):
            events.append(('exec', part.strip(), 1))
            if scripts and REDIRECT.search(part):
                events.append(('output', within(cwd, REDIRECT.search(part).group(1)), 1))
        for script in (script for script in scripts if WRITE_CALL.search(script)):
            targets = script_targets(script)
            events.extend([('output', within(cwd, path), 0) for path in targets] if targets else [('script', script, 0)])
    return events


def changed_lines(name, arguments):
    if name == 'MultiEdit':
        return sum(str(e.get('new_string') or '').count('\n') + 1 for e in arguments.get('edits') or [] if isinstance(e, dict))
    text = arguments.get('new_string') if name == 'Edit' else arguments.get('content', arguments.get('new_source'))
    return str(text or '').count('\n') + 1


def turn_events(transcript):
    """Edits (with changed line counts), executions, writing scripts and verifier launches after the
    latest human prompt, which opens with a ('start', timestamp) event."""
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
            events = [('start', str(entry.get('timestamp') or ''), 0)]
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
                events.extend(shell_events(str(arguments.get('command') or '')))
            elif block.get('name') in AGENT_TOOLS and VERIFIER_MARKER in str(arguments.get('prompt') or ''):
                events.append(('verify', '', 0))
    return events


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
    return None if path.suffix.lower() in DOC_SUFFIXES | OUTPUT_SUFFIXES else relative.as_posix()


def git_changed_lines(root, files, scripts, since):
    """Changed lines per Git in the code files this turn changed, so other turns' changes do not count:
    tracked files against the commit before the turn's own commits (the empty tree before the first
    commit), untracked text files whole. A file belongs to the turn when the turn named it or, with a
    turn-start timestamp, was modified after it. Without a timestamp, a script with unreadable targets
    claims the changed files it names as string literals, or every changed file when it names none.
    0 outside a repository or without Git."""
    def git(*args, check=True):
        result = subprocess.run(['git', '-C', str(root), *args],  # -z output keeps non-ASCII paths verbatim
                                capture_output=True, timeout=5, check=check)
        return [item for item in result.stdout.decode('utf-8', errors='replace').split('\0') if item]

    try:
        started = datetime.fromisoformat(since.replace('Z', '+00:00')).timestamp() if since else None
    except ValueError:
        started = None
    literals = {posixpath.normpath(match[1].replace('\\', '/')) for script in scripts
                for match in re.findall(LITERAL, script)}

    def named(name):
        return any(name == literal or literal.endswith('/' + name) or name.endswith('/' + literal) for literal in literals)

    def touched(name, changed):
        if name in files:
            return True
        if started is not None:
            try:
                return (root / name).stat().st_mtime >= started - 2  # tolerate coarse file-system clocks
            except OSError:
                return False
        return bool(scripts) and (named(name) or not any(named(other) for other in changed))

    try:
        head = git('rev-parse', '--verify', '--quiet', 'HEAD', check=False)
        base = head[0].strip() if head else EMPTY_TREE
        commits = git('rev-list', '-z', '--reverse', f'--since={since}', 'HEAD') if since and head else []
        if commits:  # The turn committed: measure from the commit before its first one.
            parent = git('rev-parse', '--verify', '--quiet', commits[0] + '^', check=False)
            base = parent[0].strip() if parent else EMPTY_TREE
        counts, items = {}, git('diff', '--numstat', '-z', '--relative', base, '--')
        while items:
            added, removed, name = (items.pop(0).split('\t', 2) + ['', ''])[:3]
            if not name and len(items) >= 2:  # a rename: old and new paths follow
                name = items[1]
                del items[:2]
            counts[name] = int(added) + int(removed) if added.isdigit() and removed.isdigit() else 1
        for name in git('ls-files', '-z', '--others', '--exclude-standard'):
            try:
                data = (root / name).read_bytes()[:1_000_000]
            except OSError:
                continue
            if b'\0' not in data[:8000]:  # Binary output such as a built bundle is not a code change.
                counts[name] = data.count(b'\n') + 1
    except (OSError, subprocess.SubprocessError):
        return 0
    changed = {code_file(name, root): n for name, n in counts.items() if code_file(name, root)}
    return sum(n for name, n in changed.items() if touched(name, changed))


def unchecked_lines(events, root):
    """Changed code lines in the turn when no independent verifier ran after the first code edit.
    The count is the larger of the transcript's (edit tools, heredoc bodies) and Git's for the files
    the turn wrote, since shell writes and scripts do not always show their size."""
    lines, files, scripts, since, edited, verified = 0, set(), [], '', False, False
    for kind, value, count in events:
        if kind == 'start':
            since = value
        elif kind in ('edit', 'output') and code_file(value, root):
            edited = True
            lines += count
            files.add(code_file(value, root))
        elif kind == 'script':
            edited = True
            scripts.append(value)
        elif kind == 'verify' and edited:
            verified = True
    if verified or not edited:
        return 0
    return max(lines, git_changed_lines(root, files, scripts, since))


def guard(payload):
    if payload.get('stop_hook_active') or os.environ.get('AGENT_COMPLETION_GUARD', '').lower() == 'off':
        return {}
    transcript, cwd = payload.get('transcript_path'), payload.get('cwd')
    if not transcript or not cwd or not Path(transcript).is_file():
        return {}
    events, root = turn_events(Path(transcript)), Path(cwd).resolve()
    lines = unchecked_lines(events, root)
    if lines < CHECK_MIN_LINES:
        return {}
    return {'decision': 'block', 'reason': (
        f'Completion guard: {lines} changed code line(s) were not handed to an independent verifier. Launch one '
        f"with only the user's request verbatim and the diff, using the template in {REFERENCE}, "
        'or state on the card why the change is trivial. This guard blocks once.')}


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
