"""Run delegated work as a deterministic state machine; the models run inside the host session.

Nothing here calls a model or starts an agent session. The orchestrating Claude Code or Codex
session launches the sub-agents whose prompts this prints (Claude Code: the plugin's
`acceptance-author` and `implementer` agents; Codex: sub-agents given the same prompt), and the
packaged hooks advance the state when those sub-agents stop and refuse tool calls the current
stage does not allow. The order is decided here, not by the model.

queue add   Put a task in the repository's queue: request text, optional Feature and path globs.
next        When capacity allows (risk_gate capacity, open correctness questions, no running task on
            the same Feature or overlapping paths), create the task's worktree on `agent/<id>` from the
            integration ref and print the acceptance author's prompt.
author-done Read the author's result (the SubagentStop hook calls this): queue correctness questions,
            or seal the tests in the task worktree. A refused test returns to the author.
answer      Record a person's answer to a correctness question. With every one answered the task
            returns to authoring with the decided readings.
implement   Print the implementer's prompt: the request and scenario text, never the sealed tests
            or the author's write-path list, which stay where the hooks refuse to read them.
finish      Run the sealed check, classify the tier under the integration ref's table and commit the
            work with trailers (the SubagentStop hook calls this when the implementer stops).
integrate   LOW only: recheck on the integration tip, then merge into the local branch named by
            --into while it is checked out and clean. Nothing is pushed.
status      Every task's stage without tests or write paths. digest: the person's batch (MED and
            HIGH work, open correctness questions, preference defaults taken).
event       Failure events become queued tasks: `event scan` reads reverts (risk_gate events);
            `event add` records an integration-check failure or a user correction; `event finding`
            counts a review finding and queues a task on its third occurrence.
resume      A person returns a stopped task to its previous stage.

State lives in the Git common directory (`agentic-delegation/`), outside every work tree. Without
OS-level isolation the hooks detect and refuse; they cannot prevent a determined process.
"""
import argparse
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

_here = Path(__file__).resolve().parent
for _candidate in (_here, _here.parent / 'scripts'):
    if (_candidate / 'acceptance_gate.py').is_file():
        sys.path.insert(0, str(_candidate))
        break
import acceptance_gate  # noqa: E402
import risk_gate  # noqa: E402

STATE = 'agentic-delegation'
ACTIVE = 'active'  # marker file: present while any task is between `next` and a terminal stage
TERMINAL = {'integrated', 'closed'}
WAITING = {'queued', 'questions', 'review', 'stopped'}  # nothing for the orchestrator to do
EDITABLE = {'implementing', 'ready', 'review'}  # stages whose worktree the implementer may edit
MAX_SEAL_ATTEMPTS = 3
DENY_CONSECUTIVE, DENY_TOTAL = 3, 20
ROLE_MARK = re.compile(r'DELEGATED TASK (\S+) ROLE (acceptance-author|implementer)')
TASK_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')
DEFAULT_DENY = (r'\bgit\s+push\b',)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def git(root, *args, check=True):
    result = subprocess.run(['git', '-C', str(root), '-c', 'core.quotePath=false', *args], capture_output=True)
    if check and result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout.decode('utf-8', errors='replace')


def common_dir(root):
    directory = Path(git(root, 'rev-parse', '--git-common-dir').strip())
    return (directory if directory.is_absolute() else Path(root) / directory).resolve()


def main_root(root):
    """The main checkout of the repository (the common directory's work tree)."""
    return common_dir(root).parent


def state(root):
    return common_dir(root) / STATE


def task_path(root, task_id):
    if not TASK_ID.match(task_id or ''):
        raise ValueError(f'task id must match {TASK_ID.pattern}: {task_id!r}')
    return state(root) / 'tasks' / f'{task_id}.json'


def load(root, task_id):
    path = task_path(root, task_id)
    if not path.is_file():
        raise ValueError(f'unknown task: {task_id}')
    return json.loads(path.read_text(encoding='utf-8'))


def save(root, task):
    path = task_path(root, task['id'])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(task, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)
    refresh_marker(root)
    return task


def tasks(root):
    directory = state(root) / 'tasks'
    if not directory.is_dir():
        return []
    found = [json.loads(path.read_text(encoding='utf-8')) for path in sorted(directory.glob('*.json'))]
    return sorted(found, key=lambda task: task.get('queued_at', ''))


def refresh_marker(root):
    marker = state(root) / ACTIVE
    live = [t['id'] for t in tasks(root) if t['stage'] not in TERMINAL | {'queued'}]
    if live:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text('\n'.join(live) + '\n', encoding='utf-8')
    elif marker.exists():
        marker.unlink()


def advance(task, stage, note=''):
    task['history'] = task.get('history', []) + [{'at': now(), 'from': task['stage'], 'to': stage, 'note': note[:300]}]
    task['previous_stage'], task['stage'] = task['stage'], stage
    return task


def author_dir(root, task_id):
    return state(root) / 'authors' / task_id


# --- queue ------------------------------------------------------------------------------------------

def queue_add(root, task_id, request, feature=None, paths=(), links=(), preserve=False, origin=None):
    if task_path(root, task_id).exists():
        raise ValueError(f'task {task_id} already exists')
    if not request.strip():
        raise ValueError('the request text is empty')
    task = {'schema_version': 1, 'id': task_id, 'request': request, 'feature': feature, 'paths': list(paths),
            'links': list(links), 'preserve': preserve, 'origin': origin, 'stage': 'queued', 'queued_at': now(),
            'questions': [], 'answers': [], 'seal_attempts': 0, 'denials': {'consecutive': 0, 'total': 0},
            'history': []}
    return save(root, task)


def overlaps(left, right):
    """Whether two tasks may touch the same files. A task without path globs may touch anything."""
    if not left.get('paths') or not right.get('paths'):
        return True
    for a in left['paths']:
        for b in right['paths']:
            a_low, b_low = a.lower(), b.lower()
            if fnmatchcase(a_low, b_low) or fnmatchcase(b_low, a_low) or \
                    a_low.split('*')[0].startswith(b_low.split('*')[0]) or b_low.split('*')[0].startswith(a_low.split('*')[0]):
                return True
    return False


def open_correctness(task):
    answered = {a['question'] for a in task.get('answers', [])}
    return [q for q in task.get('questions', []) if q.get('kind') == 'correctness' and q['id'] not in answered]


def integration(root, onto=None):
    ref = onto or acceptance_gate.default_integration(root)
    if ref:
        return ref, git(root, 'rev-parse', '--verify', ref + '^{commit}').strip()
    return None, git(root, 'rev-parse', '--verify', 'HEAD^{commit}').strip()


def blocked_reason(root, candidate, everything, onto, limits):
    running = [t for t in everything if t['stage'] not in TERMINAL | {'queued'} and t['id'] != candidate['id']]
    for other in running:
        if candidate.get('feature') and candidate.get('feature') == other.get('feature'):
            return f'Feature {candidate["feature"]} already has running task {other["id"]}'
        if overlaps(candidate, other):
            return f'paths may overlap running task {other["id"]}'
    for other in everything:
        if candidate.get('feature') and other.get('feature') == candidate['feature'] and open_correctness(other):
            return f'Feature {candidate["feature"]} has open correctness questions (task {other["id"]})'
    gate = risk_gate.capacity(main_root(root), onto, limits)
    questions = sum(len(open_correctness(t)) for t in everything)
    if questions + gate['counts']['open_questions'] >= limits['open_questions']:
        return f'{questions + gate["counts"]["open_questions"]} open correctness questions reach the limit'
    full = [name for name in gate['full'] if name != 'open_questions']
    review = {'unmerged_high': sum(t.get('tier') == 'HIGH' and t['stage'] == 'review' for t in everything),
              'unmerged_med': sum(t.get('tier') == 'MED' and t['stage'] == 'review' for t in everything)}
    full += [name for name, value in review.items() if value + gate['counts'][name] >= limits[name] and name not in full]
    if full:
        return 'the person\'s queue is full: ' + ', '.join(sorted(set(full)))
    return None


def next_task(root, onto=None, limits=None, worktrees=None):
    """Start the first queued task that may run now; returns its author prompt, or why none starts."""
    limits = limits or {'open_questions': 3, 'unmerged_high': 2, 'unmerged_med': 5}
    ref, tip = integration(root, onto)
    everything = tasks(root)
    waiting = [t for t in everything if t['stage'] == 'queued']
    reasons = {}
    for task in waiting:
        reason = blocked_reason(root, task, everything, ref or tip, limits)
        if reason:
            reasons[task['id']] = reason
            continue
        return start(root, task, ref, tip, worktrees)
    return {'started': None, 'waiting': reasons or 'the queue is empty'}


def start(root, task, ref, tip, worktrees=None):
    home = main_root(root)
    base = Path(worktrees) if worktrees else home / '.claude' / 'worktrees'
    tree = (base / task['id']).resolve()
    branch = f'agent/{task["id"]}'
    git(home, 'worktree', 'add', '-q', '-b', branch, str(tree), tip)
    exclude = common_dir(root) / 'info' / 'exclude'
    rule = '/.claude/worktrees/\n'
    if tree.is_relative_to(home) and rule.strip() not in (exclude.read_text(encoding='utf-8') if exclude.is_file() else ''):
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open('a', encoding='utf-8') as stream:
            stream.write(rule)
    output = author_dir(root, task['id'])
    if output.exists():
        shutil.rmtree(output)
    (output / 'files').mkdir(parents=True)
    task.update(worktree=str(tree), branch=branch, base=tip, integration=ref, started_at=now())
    save(root, advance(task, 'authoring', f'worktree {tree} from {ref or tip[:12]}'))
    return {'started': task['id'], 'worktree': str(tree), 'base': tip, 'stage': 'authoring',
            'launch': {'claude_code': 'Agent tool, subagent_type agentic-coding:acceptance-author',
                       'codex': 'a sub-agent given the prompt verbatim, without forking this conversation'},
            'prompt': author_prompt(root, task)}


# --- prompts ----------------------------------------------------------------------------------------

def decided_readings(task):
    lines = []
    for answer in task.get('answers', []):
        question = next((q['question'] for q in task['questions'] if q['id'] == answer['question']), answer['question'])
        lines.append(f'- {question} -> {answer["answer"]}')
    return '\n'.join(lines) or '- none'


def author_prompt(root, task):
    output = author_dir(root, task['id'])
    refused = task.get('refused')
    return f"""ACCEPTANCE AUTHOR. DELEGATED TASK {task['id']} ROLE acceptance-author
Someone else will implement the request below starting from commit {task['base']} of the repository
checked out at {task['worktree']}. You write the acceptance checks that will judge their work. You
will not see the implementation and must not change that repository.

Request (verbatim):
{task['request']}

Decided readings (part of the request):
{decided_readings(task)}
Also read `.harness/decisions.md` in the repository if it exists.

Write each test file under {output / 'files'}, at the path it will have in the repository (for example
{output / 'files' / 'tests' / 'test_acceptance.py'} for tests/test_acceptance.py). Rules:
- Test through entry points that already exist at the base (API handlers, CLI commands, public functions,
  UI actions through the project's live or e2e runner). A test that cannot import something the base
  lacks proves nothing and will be refused.
- Each test must fail on the base by a failed assertion about the requested behavior and pass once the
  request is implemented.{' For this behavior-preserving request, write tests that pass on the base and must keep passing.' if task.get('preserve') else ''}
- Expected values come from the request and decided readings, never from running code.
- Find every path the request's rule applies to: run `LSP findReferences` on the writing function (text
  search without an LSP tool) and search table and column writes (SQL INSERT/UPDATE, ORM calls, import
  and restore jobs, background jobs). Cover each with a test.
- One assertion per observable outcome; include the nearest valid case that must keep working.
- Questions: `correctness` when the observable result depends on the answer (do not guess and write no
  test for it), `preference` when any reasonable answer works (state the default and test it).
{f'- The previous tests were refused: {refused}. Fix the tests; never weaken what they check.' if refused else ''}
Then write {output / 'result.json'}:
{{"files": ["<repository path>", ...], "command": "<runner command from the repository root>",
 "report": "<JUnit XML or Jest JSON path the command writes, or null for Python unittest>",
 "scenarios": [{{"scenario": "<input -> expected result>", "covered_by": ["<repository path>"]}}],
 "questions": [{{"question": "...", "kind": "correctness" | "preference", "default": "..."}}],
 "write_paths": ["<file:function the rule applies to>", ...]}}
Reply with the single word `done`. Do not repeat the tests, scenarios or write paths in your reply:
the implementer must not see them.
"""


def implementer_prompt(task):
    scenarios = '\n'.join(f'- {s["scenario"]}' for s in task.get('scenarios', [])) or '- none'
    return f"""IMPLEMENTER. DELEGATED TASK {task['id']} ROLE implementer
Implement the request below in the Git worktree {task['worktree']} (branch {task['branch']}). Work only
there. Sealed acceptance checks you cannot see will judge the result when you stop.

Request (verbatim):
{task['request']}

Decided readings:
{decided_readings(task)}

Scenarios the checks cover:
{scenarios}

Rules: fix behavior at its owner. Enforce a rule on stored data at one boundary every writer crosses (a
database constraint or a single owner) and search for writes that bypass it (SQL, ORM, import and restore
jobs, background jobs; `LSP findReferences` when available). Run the affected existing checks after your
last edit. Do not create or edit acceptance tests for these scenarios, do not commit, push or deploy.
When you stop, the hook runs the sealed checks; if they fail you get the reason and continue.
"""


# --- transitions ------------------------------------------------------------------------------------

def author_done(root, task_id):
    """Read the author's result. Returns {'ok': bool, 'stage', 'reason'}; a refusal goes back to the author."""
    task = load(root, task_id)
    if task['stage'] != 'authoring':
        return {'ok': False, 'stage': task['stage'], 'reason': f'task {task_id} is {task["stage"]}, not authoring'}
    output = author_dir(root, task_id)

    def refuse(reason):
        task['seal_attempts'] = task.get('seal_attempts', 0) + 1
        task['refused'] = reason
        if task['seal_attempts'] >= MAX_SEAL_ATTEMPTS:
            save(root, advance(task, 'stopped', f'{MAX_SEAL_ATTEMPTS} refused results: {reason}'))
            return {'ok': False, 'stage': 'stopped', 'reason': f'{MAX_SEAL_ATTEMPTS} results refused; a person '
                    f'decides (`delegate.py resume` after changing the request). Last: {reason}'}
        save(root, task)
        return {'ok': False, 'stage': 'authoring', 'reason': reason}

    try:
        result = json.loads((output / 'result.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        return refuse(f'no readable {output / "result.json"}: {error}')
    files, command = result.get('files'), result.get('command')
    if not isinstance(files, list) or not files or not all(isinstance(f, str) for f in files):
        return refuse('result.json needs a nonempty `files` list')
    if not isinstance(command, str) or not command.strip():
        return refuse('result.json needs the runner `command`')
    missing = [name for name in files if not (output / 'files' / name).is_file()]
    if missing:
        return refuse('test files missing under the output directory: ' + ', '.join(missing))
    scenarios = result.get('scenarios') or []
    questions = result.get('questions') or []
    if not isinstance(scenarios, list) or not all(isinstance(s, dict) and isinstance(s.get('scenario'), str)
                                                  for s in scenarios):
        return refuse('`scenarios` must be a list of {"scenario": text, "covered_by": [paths]}')
    if not isinstance(questions, list) or not all(isinstance(q, dict) and q.get('kind') in ('correctness', 'preference')
                                                  and isinstance(q.get('question'), str) for q in questions):
        return refuse('`questions` must be a list of {"question", "kind": correctness|preference, "default"}')
    asked = {q['question'] for q in task['questions']}
    for question in questions:
        if question['question'] not in asked:
            task['questions'].append({'id': f'Q{len(task["questions"]) + 1}', 'question': question['question'],
                                      'kind': question['kind'], 'default': question.get('default')})
    task.update(command=command, report=result.get('report'), files=files,
                scenarios=[{'scenario': s['scenario'], 'covered_by': [c for c in s.get('covered_by') or [] if c in files]}
                           for s in scenarios],
                write_paths=len(result.get('write_paths') or []))
    if open_correctness(task):
        save(root, advance(task, 'questions', f'{len(open_correctness(task))} correctness question(s)'))
        return {'ok': True, 'stage': 'questions', 'questions': open_correctness(task)}
    scenario_file = output / 'scenarios.json'
    scenario_file.write_text(json.dumps(task['scenarios'], ensure_ascii=False), encoding='utf-8')
    tree = Path(task['worktree'])
    try:
        sealed = acceptance_gate.seal(tree, task['base'], [f'{output / "files" / name}={name}' for name in files],
                                      command, task.get('report'), task.get('preserve', False), task['scenarios'],
                                      600, task.get('links', []), task.get('integration'))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return refuse(f'seal failed: {error}')
    if not sealed['sealed']:
        return refuse(f'the tests do not {"pass" if task.get("preserve") else "fail by assertion"} on the base '
                      f'({sealed.get("verdict")}: {sealed.get("reason")})')
    task.update(contract=sealed['contract'], refused=None)
    save(root, advance(task, 'sealed', f'contract {sealed["contract"][:12]}'))
    return {'ok': True, 'stage': 'sealed', 'contract': sealed['contract']}


def answer(root, task_id, question_id, text):
    task = load(root, task_id)
    if not any(q['id'] == question_id for q in task['questions']):
        raise ValueError(f'task {task_id} has no question {question_id}')
    task['answers'] = [a for a in task['answers'] if a['question'] != question_id] + [
        {'question': question_id, 'answer': text, 'at': now()}]
    if task['stage'] == 'questions' and not open_correctness(task):
        task['refused'] = None
        save(root, advance(task, 'authoring', 'correctness questions answered'))
        return {'stage': 'authoring', 'prompt': author_prompt(root, task)}
    save(root, task)
    return {'stage': task['stage'], 'open': open_correctness(task)}


def implement(root, task_id):
    task = load(root, task_id)
    if task['stage'] not in ('sealed', 'implementing'):
        raise ValueError(f'task {task_id} is {task["stage"]}: it implements only after sealing')
    if task['stage'] == 'sealed':
        save(root, advance(task, 'implementing'))
    return {'stage': 'implementing', 'worktree': task['worktree'],
            'launch': {'claude_code': 'Agent tool, subagent_type agentic-coding:implementer',
                       'codex': 'a sub-agent given the prompt verbatim'},
            'prompt': implementer_prompt(task)}


def finish(root, task_id, timeout=600, deadline=1000):
    """Check, classify and commit. Returns {'ok', 'stage', 'reason', ...}."""
    task = load(root, task_id)
    if task['stage'] != 'implementing':
        return {'ok': False, 'stage': task['stage'], 'reason': f'task {task_id} is {task["stage"]}, not implementing'}
    tree = Path(task['worktree'])
    result = acceptance_gate.check(tree, timeout, True, 40, deadline)
    task['check'] = {key: result.get(key) for key in ('verdict', 'reason', 'tree', 'untested', 'unknown', 'uncovered')}
    if result['verdict'] == 'STOPPED':
        save(root, advance(task, 'stopped', result['reason']))
        return {'ok': False, 'stage': 'stopped', 'reason': acceptance_gate.summary(result)}
    if result['verdict'] != 'PASS':
        save(root, task)
        return {'ok': False, 'stage': 'implementing', 'reason': acceptance_gate.summary(result) +
                ' Fix the implementation, not the sealed tests, then stop again.'}
    # The integration ref's current tip supplies the table; without one, the base does.
    policy = acceptance_gate.integration_ref(tree, {'integration': task.get('integration')})
    decided = risk_gate.classify(tree, task['base'], policy=policy)
    task.update(tier=decided['tier'], tier_reasons=decided['reasons'])
    lines = risk_gate.trailers(tree, task['base'], task_id, policy=decided['policy'])
    if git(tree, 'status', '--porcelain').strip():
        git(tree, 'add', '-A')
        subject = task['request'].strip().splitlines()[0][:60]
        git(tree, '-c', 'user.name=' + (git(tree, 'config', 'user.name', check=False).strip() or 'delegate'),
            '-c', 'user.email=' + (git(tree, 'config', 'user.email', check=False).strip() or 'delegate@invalid'),
            'commit', '-q', '-m', f'{task_id}: {subject}', '-m', '\n'.join(lines))
    task['commit'] = git(tree, 'rev-parse', 'HEAD').strip()
    stage = 'ready' if decided['tier'] == 'LOW' else 'review'
    save(root, advance(task, stage, f'{decided["tier"]}: ' + '; '.join(decided['reasons'][:2])))
    return {'ok': True, 'stage': stage, 'tier': decided['tier'], 'card': card(task, result)}


def card(task, result=None):
    check = task.get('check') or {}
    lines = [f'Task {task["id"]} ({task["stage"]})',
             f'Request -> {task["request"].strip().splitlines()[0][:100]}',
             f'Acceptance: {check.get("verdict", "not checked")} (contract {str(task.get("contract", ""))[:12]})',
             f'Risk: {task.get("tier", "-")}: ' + '; '.join(task.get('tier_reasons', [])[:3]),
             'Untested changes: ' + ('; '.join(f'{u["file"]} {u["hunk"]}' for u in check.get('untested') or []) or 'none'),
             'Not judged: ' + ('; '.join(f'{u["file"]} {u["hunk"]}' for u in check.get('unknown') or []) or 'none'),
             'Uncovered requirements: ' + ('; '.join(check.get('uncovered') or []) or 'none'),
             'Assumptions: ' + ('; '.join(f'{q["question"]} -> {q.get("default")}' for q in task.get('questions', [])
                                         if q['kind'] == 'preference') or 'none')]
    if task.get('tier') == 'HIGH':
        lines.append('Independent check: required (HIGH): dispatch the verifier with the request and the diff')
    return '\n'.join(lines)


def integrate(root, task_id, into=None, timeout=600, regressions=()):
    task = load(root, task_id)
    if task['stage'] != 'ready' or task.get('tier') != 'LOW':
        raise ValueError(f'task {task_id} is {task["stage"]} ({task.get("tier")}): only LOW work integrates without a person')
    tree = Path(task['worktree'])
    onto = task.get('integration') or task['base']
    outcome = risk_gate.recheck(tree, 'HEAD', onto, timeout, regressions)
    task['recheck'] = {key: outcome.get(key) for key in ('verdict', 'reason', 'onto', 'tests_pass')}
    if outcome['verdict'] != 'PASS':
        save(root, advance(task, 'review', f'recheck {outcome["verdict"]}: {outcome.get("reason", "")}'))
        return {'integrated': False, 'stage': 'review', 'recheck': task['recheck']}
    if not into:
        save(root, task)
        return {'integrated': False, 'stage': 'ready', 'recheck': task['recheck'],
                'next': f'merge {task["branch"]} into the integration branch while its tip is {outcome["onto"][:12]}'}
    home = main_root(root)
    current = git(home, 'rev-parse', '--abbrev-ref', 'HEAD').strip()
    if current != into or git(home, 'status', '--porcelain', '--untracked-files=no').strip():
        raise ValueError(f'--into {into} must be checked out and clean in {home} (it has {current})')
    if git(home, 'rev-parse', 'HEAD').strip() != outcome['onto'] and git(home, 'rev-parse', onto).strip() != outcome['onto']:
        raise ValueError('the integration tip moved since the recheck; run integrate again')
    git(home, 'merge', '--no-ff', '--no-edit', task['branch'])
    task['integrated_commit'] = git(home, 'rev-parse', 'HEAD').strip()
    save(root, advance(task, 'integrated', f'merged into {into}'))
    return {'integrated': True, 'stage': 'integrated', 'commit': task['integrated_commit']}


def resume(root, task_id):
    task = load(root, task_id)
    if task['stage'] != 'stopped':
        raise ValueError(f'task {task_id} is {task["stage"]}, not stopped')
    previous = task.get('previous_stage') or 'authoring'
    task['denials'] = {'consecutive': 0, 'total': 0}
    task['seal_attempts'] = 0
    if previous == 'implementing':
        directory = acceptance_gate.state_dir(Path(task['worktree']))
        (directory / 'results.jsonl').unlink(missing_ok=True)
        (directory / 'blocks.json').unlink(missing_ok=True)
    save(root, advance(task, previous, 'resumed by a person'))
    return {'stage': previous}


# --- events ----------------------------------------------------------------------------------------

def event_scan(root, base, days=30):
    queued = []
    for item in risk_gate.events(main_root(root), base, days):
        task_id = f'revert-{item["commit"][:10]}'
        if task_path(root, task_id).exists():
            continue
        request = (f'Commit {item["reverted"]} was reverted by {item["commit"]} (paths: {", ".join(item["paths"])}). '
                   'Reproduce the reverted defect and its alternate paths as new acceptance tests that fail on the '
                   'reverted change, with the nearest valid case, then register a probe that restores the defect.')
        queue_add(root, task_id, request, paths=item['paths'], origin={'event': 'revert', **item})
        queued.append(task_id)
    return queued


def event_add(root, kind, detail, paths=()):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    task_id = f'{kind}-{stamp}'
    request = {'check-failure': 'The integration branch check failed: {detail}. Reproduce the failure as an additive '
                                'acceptance test and fix its cause.',
               'correction': 'A user corrected delegated work: {detail}. Reproduce the corrected behavior as an '
                             'additive acceptance test and fix the cause.'}[kind].format(detail=detail)
    queue_add(root, task_id, request, paths=paths, origin={'event': kind, 'detail': detail})
    return task_id


def event_finding(root, key, detail):
    path = state(root) / 'findings.json'
    counts = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    entry = counts.get(key) or {'count': 0, 'details': [], 'task': None}
    entry['count'] += 1
    entry['details'] = (entry['details'] + [detail])[-5:]
    if entry['count'] >= 3 and not entry['task']:
        task_id = 'finding-' + re.sub(r'[^A-Za-z0-9._-]', '-', key)[:40]
        if not task_path(root, task_id).exists():
            queue_add(root, task_id, f'The review finding "{key}" occurred {entry["count"]} times ({"; ".join(entry["details"])}). '
                      'Express the rule as an executable check (lint rule, type or test) that rejects a violation '
                      'while nearby valid code passes.', origin={'event': 'finding', 'key': key})
        entry['task'] = task_id
    counts[key] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding='utf-8')
    return entry


# --- views -----------------------------------------------------------------------------------------

def public(task):
    """A task without the author's test bytes or write paths."""
    return {key: task.get(key) for key in ('id', 'stage', 'feature', 'paths', 'worktree', 'branch', 'base', 'integration',
                                           'tier', 'contract', 'commit', 'refused', 'seal_attempts', 'denials', 'origin')} | {
        'open_questions': open_correctness(task), 'scenarios': len(task.get('scenarios') or []),
        'write_paths': task.get('write_paths')}


def next_step(task):
    return {'queued': 'delegate.py next', 'authoring': 'launch the acceptance author with the printed prompt '
            '(`delegate.py status --id` shows it again via `prompt`)', 'questions': 'a person answers: delegate.py answer',
            'sealed': 'delegate.py implement, then launch the implementer', 'implementing': 'the implementer works; '
            'its stop runs `finish`', 'ready': 'delegate.py integrate (LOW)', 'review': 'the person reviews the card '
            '(HIGH also needs the independent verifier)', 'stopped': 'a person decides: delegate.py resume',
            'integrated': 'none', 'closed': 'none'}[task['stage']]


def digest(root):
    everything = tasks(root)
    return {'review': [{'id': t['id'], 'tier': t.get('tier'), 'card': card(t)} for t in everything if t['stage'] == 'review'],
            'open_questions': [{'task': t['id'], **q} for t in everything for q in open_correctness(t)],
            'preference_defaults': [{'task': t['id'], 'question': q['question'], 'default': q.get('default')}
                                    for t in everything for q in t.get('questions', []) if q['kind'] == 'preference'
                                    and not any(a['question'] == q['id'] for a in t.get('answers', []))],
            'stopped': [{'id': t['id'], 'last': (t.get('history') or [{}])[-1].get('note')} for t in everything
                        if t['stage'] == 'stopped']}


# --- hook support ------------------------------------------------------------------------------------

def find_task(root, path=None, task_id=None):
    for task in tasks(root):
        if task_id and task['id'] == task_id:
            return task
        if path and task.get('worktree') and task['stage'] not in TERMINAL:
            try:
                if Path(path).resolve().is_relative_to(Path(task['worktree'])):
                    return task
            except (OSError, ValueError):
                continue
    return None


def record_denial(root, task):
    task['denials']['consecutive'] += 1
    task['denials']['total'] += 1
    if task['stage'] not in ('stopped',) and (task['denials']['consecutive'] >= DENY_CONSECUTIVE
                                              or task['denials']['total'] >= DENY_TOTAL):
        advance(task, 'stopped', f'{task["denials"]["consecutive"]} consecutive or {task["denials"]["total"]} '
                                 'refused tool calls')
    save(root, task)
    return task


def clear_denials(root, task):
    if task['denials']['consecutive']:
        task['denials']['consecutive'] = 0
        save(root, task)


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_subparsers(dest='mode', required=True)
    queue = modes.add_parser('queue').add_subparsers(dest='action', required=True).add_parser('add')
    queue.add_argument('--id', required=True)
    source = queue.add_mutually_exclusive_group(required=True)
    source.add_argument('--request')
    source.add_argument('--request-file', type=Path)
    queue.add_argument('--feature')
    queue.add_argument('--paths', nargs='*', default=[])
    queue.add_argument('--link', nargs='*', default=[])
    queue.add_argument('--preserve', action='store_true')
    starting = modes.add_parser('next')
    starting.add_argument('--onto')
    starting.add_argument('--worktrees', type=Path)
    starting.add_argument('--max-questions', type=int, default=3)
    starting.add_argument('--max-high', type=int, default=2)
    starting.add_argument('--max-med', type=int, default=5)
    simple = [modes.add_parser(name) for name in ('author-done', 'implement', 'finish', 'resume')]
    for mode in simple:
        mode.add_argument('--id', required=True)
    answering = modes.add_parser('answer')
    answering.add_argument('--id', required=True)
    answering.add_argument('--question', required=True)
    answering.add_argument('--text', required=True)
    integrating = modes.add_parser('integrate')
    integrating.add_argument('--id', required=True)
    integrating.add_argument('--into')
    integrating.add_argument('--regression', action='append', default=[])
    showing = modes.add_parser('status')
    showing.add_argument('--id')
    digesting = modes.add_parser('digest')
    events = modes.add_parser('event').add_subparsers(dest='action', required=True)
    scanning = events.add_parser('scan')
    scanning.add_argument('--base', required=True)
    scanning.add_argument('--days', type=int, default=30)
    adding = events.add_parser('add')
    adding.add_argument('--kind', choices=('check-failure', 'correction'), required=True)
    adding.add_argument('--detail', required=True)
    adding.add_argument('--paths', nargs='*', default=[])
    finding = events.add_parser('finding')
    finding.add_argument('--key', required=True)
    finding.add_argument('--detail', required=True)
    for mode in (queue, starting, *simple, answering, integrating, showing, digesting, scanning, adding, finding):
        mode.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.mode == 'queue':
            request = args.request if args.request is not None else args.request_file.read_text(encoding='utf-8')
            out = public(queue_add(root, args.id, request, args.feature, args.paths, args.link, args.preserve))
        elif args.mode == 'next':
            out = next_task(root, args.onto, {'open_questions': args.max_questions, 'unmerged_high': args.max_high,
                                              'unmerged_med': args.max_med}, args.worktrees)
        elif args.mode == 'author-done':
            out = author_done(root, args.id)
        elif args.mode == 'answer':
            out = answer(root, args.id, args.question, args.text)
        elif args.mode == 'implement':
            out = implement(root, args.id)
        elif args.mode == 'finish':
            out = finish(root, args.id)
        elif args.mode == 'integrate':
            out = integrate(root, args.id, args.into, regressions=args.regression)
        elif args.mode == 'resume':
            out = resume(root, args.id)
        elif args.mode == 'status':
            if args.id:
                task = load(root, args.id)
                out = dict(public(task), next=next_step(task), card=card(task),
                           prompt=author_prompt(root, task) if task['stage'] == 'authoring' else
                           implementer_prompt(task) if task['stage'] == 'implementing' else None)
            else:
                out = [dict(public(t), next=next_step(t)) for t in tasks(root)]
        elif args.mode == 'digest':
            out = digest(root)
        elif args.action == 'scan':
            out = {'queued': event_scan(root, args.base, args.days)}
        elif args.action == 'add':
            out = {'queued': event_add(root, args.kind, args.detail, args.paths)}
        else:
            out = event_finding(root, args.key, args.detail)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        failed = isinstance(out, dict) and (out.get('ok') is False or out.get('integrated') is False and out.get('stage') == 'review')
        return 1 if failed else 0
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
