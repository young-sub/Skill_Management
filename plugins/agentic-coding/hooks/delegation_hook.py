"""Hooks that hold delegated work to its stages; `delegate.py` owns the state.

PreToolUse    While a delegated task is active: refuse edits to a task worktree before its tests are
              sealed and the implementer starts; refuse reading the author's output, the sealed tests or
              the delegation state (only the acceptance author may write its own output); refuse
              `git push`, configured deploy commands and the person's own commands (`clear`, `resume`).
              Three refusals in a row, or twenty in all, stop the task for a person.
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
PERSON_ONLY = re.compile(r'acceptance_gate\.py["\']?\s+clear\b|delegate\.py["\']?\s+resume\b')
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
    agent = str(payload.get('agent_type') or '')
    author = agent.endswith('acceptance-author')
    paths, command = tool_paths(data), command_text(data)
    running = [t for t in delegate.tasks(root) if t['stage'] not in delegate.TERMINAL | {'queued'}]
    if not running:
        return {}
    owner = next((t for p in paths for t in [delegate.find_task(root, path=p)] if t), None)
    owner = owner or (running[0] if len(running) == 1 else None)

    def refuse(reason):
        if owner:
            stopped = delegate.record_denial(root, delegate.load(root, owner['id']))
            if stopped['stage'] == 'stopped':
                reason += f' Task {owner["id"]} is now stopped for a person (`delegate.py resume`).'
        return deny(reason)

    state = str(common / STATE).replace('\\', '/').lower()
    for path in paths:
        normalized = str(Path(path)).replace('\\', '/').lower() if path else ''
        if not any(marker in normalized for marker in PROTECTED):
            continue
        writing_own_output = (tool in EDIT_TOOLS and normalized.startswith(f'{state}/authors/') and any(
            t['stage'] == 'authoring' and normalized.startswith(f'{state}/authors/{t["id"].lower()}/') for t in running))
        if writing_own_output and (author or not agent):
            continue
        if author and tool in READ_TOOLS and normalized.startswith(f'{state}/authors/'):
            continue
        return refuse(f'{path} holds sealed acceptance or delegation state; the implementer and orchestrator do not '
                      'read or change it (the author writes only its own output).')
    if command:
        if PERSON_ONLY.search(command):
            return refuse('clearing a sealed contract or resuming a stopped task is the person\'s decision.')
        if any(marker in command.replace('\\', '/') for marker in PROTECTED) and not author:
            return refuse('the command touches sealed acceptance or delegation state, which stays with the gate.')
        for pattern in deny_patterns(delegate, root):
            if pattern.search(command):
                return refuse(f'`{pattern.pattern}` is refused during delegated work: pushing and deploying stay '
                              'with the person or CI.')
    if tool in EDIT_TOOLS:
        for path in paths:
            task = delegate.find_task(root, path=path)
            if task is None:
                continue
            if task['stage'] == 'stopped':
                return refuse(f'task {task["id"]} is stopped; a person resumes it.')
            if task['stage'] not in delegate.EDITABLE:
                return refuse(f'task {task["id"]} is {task["stage"]}: its worktree is edited only after the tests '
                              f'are sealed and `delegate.py implement` starts the implementer. Next: {delegate.next_step(task)}.')
    if owner and owner['denials']['consecutive']:
        delegate.clear_denials(root, delegate.load(root, owner['id']))  # an allowed call ends a run of refusals
    return {}


def role_of(payload, delegate, root):
    """(task id, role) from the sub-agent's prompt marker, or from its plugin agent type."""
    text = str(payload.get('last_assistant_message') or '')
    transcript = payload.get('agent_transcript_path')
    if transcript:
        try:
            with open(os.path.expanduser(transcript), encoding='utf-8', errors='replace') as stream:
                text = stream.read(400_000) + text
        except OSError:
            pass
    found = delegate.ROLE_MARK.search(text)
    if found:
        return found.group(1), found.group(2)
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
