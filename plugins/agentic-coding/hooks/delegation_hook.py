"""Hooks that hold delegated work to its stages; `delegate.py` owns the state.

PreToolUse    While a delegated task is active: refuse edits to a task worktree before its tests are
              sealed and the implementer starts, by edit tools and by shell commands that name the
              worktree or run in it (only read-only commands and test runners pass); refuse reading or
              searching the author's output, the sealed tests or the delegation state (only the
              acceptance author writes its own task's output); refuse `git push` however optioned,
              configured deploy commands and the person's own commands (`clear`, `resume`, `close`).
              Paths are compared after resolving `..`, symlinks, case and extended (`//?/`) prefixes. A refusal
              is charged to the task it concerns; three in a row, or twenty in all, stop that task.
SubagentStop  The acceptance author's stop reads and seals its result; the implementer's stop runs the
              sealed check and classifies the tier. A refusal or a failing check keeps that sub-agent
              working with the reason. Roles come from the `DELEGATED TASK <id> ROLE <role>` line the
              prompts start with, or the plugin agent's type.
Stop          (called by the packaged Stop hook) blocks once when a task waits on the orchestrator:
              sealed but not implemented, or LOW and not integrated.

Without any active task every event returns at once, before Git or the state machine loads. Refusal
is detection with a reason, not isolation: a process can still read files the hooks do not see.
"""
import json
import os
from pathlib import Path
import re
import sys

STATE = 'agentic-delegation'
EDIT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit', 'apply_patch'}
READ_TOOLS = {'Read', 'Grep', 'Glob', 'NotebookRead'}
SHELL_TOOLS = {'Bash', 'PowerShell', 'shell', 'exec_command', 'local_shell'}
PROTECTED = ('agentic-delegation', 'agentic-acceptance')
PERSON_ONLY = re.compile(r'acceptance_gate\.py["\']?\s+clear\b|delegate\.py["\']?\s+(?:resume|close)\b', re.IGNORECASE)
SEGMENT = re.compile(r'&&|\|\||;|\||\n')
ARGUMENT =r'(?:"[^"]*"|\'[^\']*\'|\S+)'
PYTHON = r'(?:"[^"]*python[^"]*"|\'[^\']*python[^\']*\'|\S*python3?(?:\.exe)?|py(?:\.exe)?)'
# Shell segments that read, run tests or drive the delegation without changing the tree they name. The
# lifecycle scripts are allowed by name; their person-only subcommands are refused earlier.
READ_ONLY = re.compile(r'^\s*(?:'
                       r'["\']?\S*git(?:\.exe)?["\']?(?:\s+-[Cc]\s+' + ARGUMENT + r')*\s+(?:status|diff|log|show|rev-parse|'
                       r'ls-files|grep|blame|cat-file|branch\s+--show-current)\b'
                       r'|(?:ls|dir|cat|type|head|tail|grep|rg|find|wc|pwd|cd|echo|Get-Content|Get-ChildItem|'
                       r'Select-String|Test-Path|Set-Location)\b'
                       r'|' + PYTHON + r'\s+(?:-\w+\s+)*-m\s+(?:unittest|pytest)\b'
                       r'|' + PYTHON + r'\s+(?:"[^"]*?|\'[^\']*?|\S*?)(?:delegate|acceptance_gate|risk_gate|probe_check|run_check|'
                       r'blast_radius_check|project_workflow)\.py\b'
                       r'|(?:pytest|npx\s+vitest\s+run|npm\s+test|node\s+--test)\b'
                       r'|$)', re.IGNORECASE)
# What changes files from a shell: a redirect other than to a stream or the null device, Git's
# `--output`, deleting `find`, and the usual writing commands.
HARMLESS_REDIRECT = re.compile(r'\d*>&\d|\d*>\s*(?:/dev/null|nul|\$null)(?![\w.\-/\\])', re.IGNORECASE)
# Writes a read-only command can still make through its arguments. Writing commands themselves (cp, rm,
# Set-Content, git commit ...) never start a segment READ_ONLY accepts, so argument words such as
# `rg install` or `git show HEAD:chmod.md` are not writes.
WRITES = re.compile(r'>|--output\b|\s-delete\b|-exec(?:dir)?\s', re.IGNORECASE)
PATCH_FILE = re.compile(r'^\*\*\* (?:Add|Update|Delete) File: (.+?)\s*$', re.MULTILINE)


def common_dir(cwd):
    """The Git common directory above cwd, read from the file system without starting Git."""
    try:
        path = Path(cwd).resolve()
    except (OSError, ValueError):
        return None
    for directory in (path, *path.parents):
        dot = directory / '.git'
        if dot.is_dir():
            return dot
        if dot.is_file():
            text = dot.read_text(encoding='utf-8', errors='replace').strip()
            if not text.startswith('gitdir:'):
                return None
            gitdir = Path(text.split(':', 1)[1].strip())
            gitdir = gitdir if gitdir.is_absolute() else (directory / gitdir).resolve()
            pointer = gitdir / 'commondir'
            if pointer.is_file():
                shared = Path(pointer.read_text(encoding='utf-8').strip())
                return shared if shared.is_absolute() else (gitdir / shared).resolve()
            return gitdir
    return None


def active(payload):
    common = common_dir(payload.get('cwd') or os.getcwd())
    return common if common and (common / STATE / 'active').is_file() else None


def load_delegate():
    here = Path(__file__).resolve().parent
    for directory in (here, here.parent / 'skills/agent-workflow/scripts'):
        if (directory / 'delegate.py').is_file():
            if str(directory) not in sys.path:
                sys.path.insert(0, str(directory))
            import delegate
            return delegate
    raise ImportError('delegate.py not found beside the hook or in the agent-workflow Skill')


def canon(path, cwd):
    """A comparable absolute path: `\\\\?\\` and `//?/` prefixes dropped, relative paths joined to cwd, `..`
    and symlinks resolved, case folded where the file system folds it."""
    text = str(path).strip().strip('"\'')
    for prefix in ('\\\\?\\UNC\\', '//?/UNC/'):
        if text.upper().startswith(prefix.upper()):
            text = '\\\\' + text[len(prefix):]
    for prefix in ('\\\\?\\', '//?/', '\\\\.\\'):
        if text.startswith(prefix):
            text = text[len(prefix):]
    candidate = Path(os.path.expanduser(text))
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    try:
        candidate = candidate.resolve()
    except (OSError, RuntimeError):
        candidate = Path(os.path.abspath(candidate))
    return Path(os.path.normcase(str(candidate)))


def inside(path, root):
    try:
        return path == root or path.is_relative_to(root)
    except ValueError:
        return False


def spelled(command, path):
    """Whether a shell command names the path, in any slash direction or case."""
    text = command.replace('\\', '/').lower()
    target = str(path).replace('\\', '/').lower()
    spellings = {target}
    if re.match(r'^[a-z]:/', target):
        spellings.add('/' + target[0] + target[2:])  # MSYS and Git Bash: /c/...
    return any(spelling in text for spelling in spellings)


def deny(reason):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                   'permissionDecisionReason': reason}}


def tool_paths(data):
    paths = [data[key] for key in ('file_path', 'notebook_path', 'path') if isinstance(data.get(key), str)]
    for key in ('patch', 'input', 'command'):
        if isinstance(data.get(key), str):
            paths += PATCH_FILE.findall(data[key])
    return paths


def command_text(data):
    command = data.get('command') if isinstance(data, dict) else None
    if isinstance(command, list):
        return ' '.join(map(str, command))
    return command if isinstance(command, str) else ''


def deny_patterns(delegate, root):
    config = delegate.state(root) / 'config.json'
    extra = []
    if config.is_file():
        try:
            extra = json.loads(config.read_text(encoding='utf-8')).get('deny_commands', [])
        except ValueError:
            extra = []
    return [re.compile(pattern, re.IGNORECASE) for pattern in (*delegate.DEFAULT_DENY, *extra)]


def pre_tool(payload, common):
    delegate = load_delegate()
    root = common.parent
    tool, data = str(payload.get('tool_name') or ''), payload.get('tool_input') or {}
    agent, agent_id = str(payload.get('agent_type') or ''), payload.get('agent_id')
    cwd = payload.get('cwd') or os.getcwd()
    author = agent.endswith('acceptance-author')
    running = [t for t in delegate.tasks(root) if t['stage'] not in delegate.TERMINAL | {'queued'}]
    if not running:
        return {}
    command = command_text(data)
    paths = [canon(path, cwd) for path in tool_paths(data) if path]
    base = canon(common, cwd)
    state = canon(common / STATE, cwd)
    trees = {t['id']: canon(t['worktree'], cwd) for t in running if t.get('worktree')}
    here = canon(cwd, cwd)
    mine = delegate.assigned(root, agent_id) if agent_id else None
    if agent_id and not mine:  # a plugin agent's first call: its role names the one task in that stage
        for role, stage in (('acceptance-author', 'authoring'), ('implementer', 'implementing')):
            candidates = [t for t in running if t['stage'] == stage]
            if agent.endswith(role) and len(candidates) == 1:
                try:
                    delegate.assign(root, agent_id, candidates[0]['id'], role)
                    mine = {'task': candidates[0]['id'], 'role': role}
                except ValueError:
                    pass

    def responsible(path=None):
        for task in running:
            if path is not None and task['id'] in trees and inside(path, trees[task['id']]):
                return task['id']
        for task in running:
            if task['id'] in trees and (inside(here, trees[task['id']]) or (command and spelled(command, trees[task['id']]))):
                return task['id']
        if mine and any(t['id'] == mine['task'] for t in running):
            return mine['task']
        return running[0]['id'] if len(running) == 1 else None

    def refuse(reason, task_id):
        if task_id:
            try:
                if delegate.record_denial(root, task_id) == 'stopped':
                    reason += f' Task {task_id} is now stopped for a person (`delegate.py resume`).'
            except ValueError:
                pass  # the state is busy: refuse without counting rather than wait
        return deny(reason)

    def protected(path):
        return inside(path, base) and (inside(path, state) or 'agentic-acceptance' in path.parts)

    def own_output(path):
        return any(t['stage'] == 'authoring' and inside(path, canon(delegate.author_dir(root, t['id']), cwd))
                   and (not mine or mine['task'] == t['id']) for t in running)

    for path in paths:
        if tool in READ_TOOLS and inside(path, base) and (inside(state, path) or protected(path)) and not author:
            return refuse(f'{path} contains sealed acceptance or delegation state; searching or reading it is refused '
                          '(the author reads only its own output).', responsible())
        if not protected(path):
            continue
        if own_output(path) and (tool in EDIT_TOOLS and (author or not agent) or tool in READ_TOOLS and author):
            continue
        return refuse(f'{path} holds sealed acceptance or delegation state; the implementer and orchestrator do not '
                      'read or change it (the author writes only its own task\'s output).', responsible())
    if tool == 'Glob':
        pattern = str(data.get('pattern') or '').replace('\\', '/').lower()
        if (any(marker in pattern for marker in PROTECTED) or re.search(r'(^|/)\.git(/|$)', pattern)) and not author:
            return refuse('the glob reaches sealed acceptance or delegation state.', responsible())
    if command:
        lowered = command.replace('\\', '/').lower()
        if PERSON_ONLY.search(command):
            return refuse('clearing a sealed contract, resuming a stopped task or closing reviewed work is the '
                          'person\'s decision.', responsible())
        if any(marker in lowered for marker in PROTECTED) and not author:
            return refuse('the command touches sealed acceptance or delegation state, which stays with the gate.',
                          responsible())
        for pattern in deny_patterns(delegate, root):
            if pattern.search(command):
                return refuse(f'`{pattern.pattern}` is refused during delegated work: pushing and deploying stay '
                              'with the person or CI.', responsible())
        for task in running:
            if task['stage'] in delegate.EDITABLE or task['id'] not in trees:
                continue
            tree = trees[task['id']]
            if not (inside(here, tree) or spelled(command, tree)):
                continue
            own = [canon(delegate.author_dir(root, t['id']), cwd) for t in running
                   if t['stage'] == 'authoring' and (not mine or mine['task'] == t['id'])] if author else []

            def harmless(part):
                # The author may write its own output from a shell in the worktree; that segment only.
                if any(spelled(part, directory) for directory in own) and not spelled(part, tree):
                    return True
                return bool(READ_ONLY.match(part)) and not WRITES.search(HARMLESS_REDIRECT.sub(' ', part))
            if not all(harmless(part) for part in SEGMENT.split(command) if part.strip()):
                return refuse(f'task {task["id"]} is {task["stage"]}: only read-only commands and test runners may '
                              f'touch its worktree until `delegate.py implement`. Next: {delegate.next_step(task)}.',
                              task['id'])
    if tool in EDIT_TOOLS:
        for path in paths:
            task = next((t for t in running if t['id'] in trees and inside(path, trees[t['id']])), None)
            if task is None:
                continue
            if task['stage'] == 'stopped':
                return refuse(f'task {task["id"]} is stopped; a person resumes it.', task['id'])
            if task['stage'] not in delegate.EDITABLE:
                return refuse(f'task {task["id"]} is {task["stage"]}: its worktree is edited only after the tests '
                              f'are sealed and `delegate.py implement` starts the implementer. Next: {delegate.next_step(task)}.',
                              task['id'])
    owner = responsible(paths[0] if paths else None)
    if owner:
        try:
            delegate.clear_denials(root, owner)  # an allowed call ends a run of refusals
        except ValueError:
            pass
    return {}


def first_prompt(transcript):
    """The text of the first user message in a sub-agent transcript (its prompt), or ''."""
    try:
        with open(os.path.expanduser(transcript), encoding='utf-8', errors='replace') as stream:
            for line in stream:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = entry.get('message') if isinstance(entry, dict) else None
                if entry.get('type') == 'user' and isinstance(message, dict):
                    content = message.get('content')
                    if isinstance(content, list):
                        content = '\n'.join(str(b.get('text') or '') for b in content if isinstance(b, dict))
                    return str(content or '')
    except (OSError, TypeError):
        pass
    return ''


def role_of(payload, delegate, root):
    """(task id, role) from the `DELEGATED TASK` line that opens the sub-agent's own prompt (never from its
    later output), from an earlier assignment of its agent id, or from its plugin agent type."""
    transcript = payload.get('agent_transcript_path')
    found = delegate.ROLE_MARK.match(first_prompt(transcript).lstrip()) if transcript else None
    if found is None and transcript:
        head = first_prompt(transcript).lstrip().splitlines()
        found = delegate.ROLE_MARK.search(head[0]) if head else None
    if found:
        return found.group(1), found.group(2)
    known = delegate.assigned(root, payload.get('agent_id')) if payload.get('agent_id') else None
    if known:
        return known['task'], known['role']
    agent = str(payload.get('agent_type') or '')
    for role, stage in (('acceptance-author', 'authoring'), ('implementer', 'implementing')):
        if agent.endswith(role):
            candidates = [t for t in delegate.tasks(root) if t['stage'] == stage]
            if len(candidates) == 1:
                return candidates[0]['id'], role
    return None, None


def subagent_stop(payload, common):
    delegate = load_delegate()
    root = common.parent
    task_id, role = role_of(payload, delegate, root)
    if not task_id:
        return {}
    try:
        task = delegate.load(root, task_id)
        delegate.assign(root, payload.get('agent_id'), task_id, role)
    except ValueError:
        return {}
    if role == 'acceptance-author' and task['stage'] == 'authoring':
        outcome = delegate.author_done(root, task_id)
        if not outcome['ok'] and outcome['stage'] == 'authoring':
            return {'decision': 'block', 'reason': f'Your result for task {task_id} was refused: {outcome["reason"]} '
                    'Fix the tests or result.json (never weaken what a test checks), then reply `done`.'}
        return {'systemMessage': f'Task {task_id}: {outcome["stage"]}'}
    if role == 'implementer' and task['stage'] == 'implementing':
        outcome = delegate.finish(root, task_id)
        if not outcome['ok'] and outcome['stage'] == 'implementing':
            return {'decision': 'block', 'reason': f'Task {task_id}: {outcome["reason"]}'}
        return {'systemMessage': f'Task {task_id}: {outcome["stage"]}' + (f' ({outcome.get("tier")})' if outcome.get('tier') else '')}
    return {}


def stop(payload):
    """The main session's stop: block once while a task waits on the orchestrator."""
    common = active(payload)
    if not common:
        return {}
    delegate = load_delegate()
    root = common.parent
    pending = []
    for task in delegate.tasks(root):
        if task['stage'] == 'authoring' and (delegate.author_dir(root, task['id']) / 'result.json').is_file():
            outcome = delegate.author_done(root, task['id'])  # a host without SubagentStop
            task = delegate.load(root, task['id'])
            if not outcome['ok'] and task['stage'] == 'authoring':
                pending.append(f'{task["id"]}: the author result was refused ({outcome["reason"]}); relaunch the author')
                continue
        if task['stage'] in ('sealed', 'ready'):
            pending.append(f'{task["id"]} is {task["stage"]}: {delegate.next_step(task)}')
    waiting = [f'{t["id"]} {t["stage"]}' for t in delegate.tasks(root) if t['stage'] in ('questions', 'review', 'stopped')]
    note = ('Delegated tasks waiting on a person: ' + ', '.join(waiting)) if waiting else ''
    if pending and not payload.get('stop_hook_active'):
        return {'decision': 'block', 'reason': 'Delegated work waits on you: ' + '; '.join(pending) +
                '. Continue it, or say on the result card why it stays.'} | ({'systemMessage': note} if note else {})
    return {'systemMessage': note} if note else {}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        payload = json.loads(sys.stdin.buffer.read().decode('utf-8-sig'))
        common = active(payload) if isinstance(payload, dict) else None
        event = payload.get('hook_event_name') if common else None
        if event == 'PreToolUse':
            result = pre_tool(payload, common)
        elif event == 'SubagentStop':
            result = subagent_stop(payload, common)
        else:
            result = {}
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        result = {'systemMessage': f'Delegation hook unavailable: {error}'}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
