"""The delegation state machine and its hooks on real Git fixtures, with scripted sub-agents and no model calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[2] / 'authoring/scripts'
DELEGATE, HOOK, GUARD = SCRIPTS / 'delegate.py', SCRIPTS / 'delegation_hook.py', SCRIPTS / 'completion_guard.py'
SPEC = importlib.util.spec_from_file_location('delegate', DELEGATE)
delegate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delegate)

RULE = 'def allowed(amount):\n    return amount >= 10\n'
ACCEPTANCE = ('import unittest\nfrom rule import allowed\n\n\nclass Acceptance(unittest.TestCase):\n'
              '    def test_minimum_is_twenty(self):\n        self.assertFalse(allowed(10))\n        self.assertTrue(allowed(20))\n')
TABLE = {'schema_version': 1,
         'low': [{'id': 'logic', 'paths': ['*.py'], 'requires': ['acceptance-pass', 'no-untested', 'no-uncovered']}],
         'high': {'paths': ['auth/*', '.harness/*']}}
COMMAND = subprocess.list2cmdline([sys.executable, '-m', 'unittest', 'discover', '-s', 'acceptance'])


class DelegationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='delegate-tests-')
        self.addCleanup(temporary.cleanup)
        self.outside = Path(temporary.name)
        self.root = self.outside / 'repo'
        self.root.mkdir()
        for args in (('init', '-q', '-b', 'main'), ('config', 'user.email', 't@example.invalid'),
                     ('config', 'user.name', 'T'), ('config', 'core.autocrlf', 'false')):
            self.git(*args)
        self.write('.gitignore', '__pycache__/\n')
        self.write('rule.py', RULE)
        self.write('.harness/risk.yaml', json.dumps(TABLE))
        self.git('add', '-A')
        self.git('commit', '-qm', 'base')
        self.git('update-ref', 'refs/remotes/origin/main', 'main')
        self.addCleanup(self.remove_worktrees)

    def remove_worktrees(self):
        for task in delegate.tasks(self.root):
            if task.get('worktree'):
                subprocess.run(['git', '-C', str(self.root), 'worktree', 'remove', '--force', task['worktree']],
                               capture_output=True)

    def git(self, *args, cwd=None):
        return subprocess.run(['git', '-C', str(cwd or self.root), *args], check=True, capture_output=True).stdout.decode()

    def write(self, name, text, root=None):
        path = (root or self.root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(DELEGATE), *args, '--root', str(self.root)], capture_output=True,
                                timeout=300)
        self.assertEqual(result.returncode, expected, result.stdout.decode() + result.stderr.decode())
        return json.loads(result.stdout) if result.stdout.strip() else None

    def hook(self, script, payload):
        payload = {'cwd': str(self.root), 'session_id': 's', 'transcript_path': str(self.outside / 'main.jsonl')} | payload
        result = subprocess.run([sys.executable, str(script)], capture_output=True, timeout=600,
                                input=json.dumps(payload).encode('utf-8'))
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return json.loads(result.stdout)

    def tool(self, name, agent=None, agent_id=None, **arguments):
        payload = {'hook_event_name': 'PreToolUse', 'tool_name': name, 'tool_input': arguments}
        return self.hook(HOOK, payload | ({'agent_type': agent} if agent else {}) | ({'agent_id': agent_id} if agent_id else {}))

    def subagent_stop(self, prompt, agent):
        transcript = self.outside / f'{agent}.jsonl'
        transcript.write_text(json.dumps({'type': 'user', 'message': {'content': prompt}}) + '\n', encoding='utf-8')
        return self.hook(HOOK, {'hook_event_name': 'SubagentStop', 'agent_type': agent, 'agent_id': 'a1',
                                'agent_transcript_path': str(transcript), 'stop_hook_active': False,
                                'last_assistant_message': 'done'})

    def main_stop(self, active=False):
        (self.outside / 'main.jsonl').write_text('', encoding='utf-8')
        return self.hook(GUARD, {'hook_event_name': 'Stop', 'stop_hook_active': active})

    def author_writes(self, output, test=ACCEPTANCE, questions=(), write_paths=('rule.py:allowed',)):
        self.write('acceptance/test_acceptance.py', test, root=output / 'files')
        result = {'files': ['acceptance/test_acceptance.py'], 'command': COMMAND, 'report': None,
                  'scenarios': [{'scenario': 'amount 10 is refused, 20 is allowed',
                                 'covered_by': ['acceptance/test_acceptance.py']}],
                  'questions': list(questions), 'write_paths': list(write_paths)}
        self.write('result.json', json.dumps(result), root=output)

    def denied(self, outcome):
        return outcome.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny'

    def test_the_loop_runs_in_order_seals_before_implementing_and_integrates_low_work(self):
        self.cli('queue', 'add', '--id', 'T1', '--request', 'Raise the minimum amount to 20.', '--paths', 'rule.py')
        self.assertFalse((delegate.state(self.root) / 'active').exists(), 'a queued task is not active yet')
        started = self.cli('next')
        tree, output = Path(started['worktree']), delegate.author_dir(self.root, 'T1')
        self.assertTrue((tree / 'rule.py').is_file())
        self.assertIn('DELEGATED TASK T1 ROLE acceptance-author', started['prompt'])
        self.assertIn('Raise the minimum amount to 20.', started['prompt'])
        # Before sealing, nobody edits the task worktree; only the author writes its own output.
        self.assertTrue(self.denied(self.tool('Edit', file_path=str(tree / 'rule.py'), old_string='10', new_string='20')))
        self.assertEqual(self.tool('Write', agent='agentic-coding:acceptance-author',
                                   file_path=str(output / 'files/acceptance/test_acceptance.py'), content=ACCEPTANCE), {})
        self.assertTrue(self.denied(self.tool('Read', file_path=str(output / 'result.json'))), 'the orchestrator never reads it')
        self.assertTrue(self.denied(self.tool('Bash', command=f'cat "{output}/result.json"')))
        # A correctness question waits for the person; the main session may stop meanwhile.
        self.author_writes(output, questions=[{'question': 'Is 20 itself allowed?', 'kind': 'correctness'}])
        self.assertEqual(self.subagent_stop(started['prompt'], 'agentic-coding:acceptance-author'),
                         {'systemMessage': 'Task T1: questions'})
        self.assertNotIn('decision', self.main_stop())
        answered = self.cli('answer', '--id', 'T1', '--question', 'Q1', '--text', 'yes, 20 is allowed')
        self.assertEqual(answered['stage'], 'authoring')
        self.assertIn('Is 20 itself allowed? -> yes, 20 is allowed', answered['prompt'])
        # A test that passes on the base is refused back to the author, who keeps working.
        self.author_writes(output, test=ACCEPTANCE.replace('assertFalse(allowed(10))', 'assertTrue(allowed(10))')
                           .replace('assertTrue(allowed(20))', 'assertTrue(allowed(10))'))
        refused = self.subagent_stop(answered['prompt'], 'agentic-coding:acceptance-author')
        self.assertEqual(refused['decision'], 'block')
        self.assertIn('fail by assertion on the base', refused['reason'])
        self.author_writes(output)
        self.assertEqual(self.subagent_stop(answered['prompt'], 'agentic-coding:acceptance-author'),
                         {'systemMessage': 'Task T1: sealed'})
        # Sealed but not implemented: the orchestrator is told once, then may stop.
        blocked = self.main_stop()
        self.assertEqual(blocked['decision'], 'block')
        self.assertIn('T1 is sealed: delegate.py implement', blocked['reason'])
        self.assertNotIn('decision', self.main_stop(active=True))
        handed = self.cli('implement', '--id', 'T1')
        self.assertIn('amount 10 is refused, 20 is allowed', handed['prompt'])
        self.assertNotIn('assertFalse', handed['prompt'], 'the implementer never sees the sealed tests')
        self.assertNotIn('rule.py:allowed', handed['prompt'], 'nor the author\'s write paths')
        self.assertNotIn('rule.py:allowed', json.dumps(self.cli('status', '--id', 'T1')))
        self.assertEqual(self.tool('Edit', agent='agentic-coding:implementer', file_path=str(tree / 'rule.py'),
                                   old_string='10', new_string='30'), {})
        self.write('rule.py', RULE.replace('>= 10', '>= 30'), root=tree)
        failed = self.subagent_stop(handed['prompt'], 'agentic-coding:implementer')
        self.assertEqual(failed['decision'], 'block')
        self.assertIn('Fix the implementation, not the sealed tests', failed['reason'])
        self.write('rule.py', RULE.replace('>= 10', '>= 20'), root=tree)
        done = self.subagent_stop(handed['prompt'], 'agentic-coding:implementer')
        self.assertEqual(done, {'systemMessage': 'Task T1: ready (LOW)'})
        message = self.git('log', '-1', '--format=%B', cwd=tree)
        self.assertIn('Agent-Task: T1', message)
        self.assertIn('Risk: LOW', message)
        self.assertIn('T1 is ready: delegate.py integrate', self.main_stop()['reason'])
        merged = self.cli('integrate', '--id', 'T1', '--into', 'main')
        self.assertTrue(merged['integrated'])
        self.assertIn('>= 20', (self.root / 'rule.py').read_text(encoding='utf-8'))
        self.assertFalse((delegate.state(self.root) / 'active').exists(), 'no task is active after integration')
        self.assertEqual(self.main_stop(), {})

    def started(self, task_id='T1', paths=('rule.py',)):
        self.cli('queue', 'add', '--id', task_id, '--request', 'Raise the minimum amount to 20.', '--paths', *paths)
        return self.cli('next')

    def test_push_deploy_and_person_only_commands_are_refused_and_repeated_refusals_stop_the_task(self):
        delegate.state(self.root).mkdir(parents=True, exist_ok=True)
        (delegate.state(self.root) / 'config.json').write_text(json.dumps({'deny_commands': [r'\bwrangler\s+deploy\b']}),
                                                               encoding='utf-8')
        self.started()
        self.assertEqual(self.tool('Bash', command='git status'), {})
        self.assertTrue(self.denied(self.tool('Bash', command='python acceptance_gate.py clear --root .')))
        self.assertTrue(self.denied(self.tool('Bash', command='npx wrangler deploy')))
        refused = self.tool('Bash', command='git push origin main')
        self.assertTrue(self.denied(refused))
        self.assertIn('now stopped for a person', refused['hookSpecificOutput']['permissionDecisionReason'])
        self.assertEqual(delegate.load(self.root, 'T1')['stage'], 'stopped')
        self.assertEqual(self.cli('resume', '--id', 'T1')['stage'], 'authoring')

    def test_overlapping_paths_or_a_shared_feature_wait_for_the_running_task(self):
        self.started('T1', ('src/*',))
        self.cli('queue', 'add', '--id', 'T2', '--request', 'Change the parser.', '--paths', 'src/parser.py')
        self.cli('queue', 'add', '--id', 'T3', '--request', 'Change the docs.', '--paths', 'docs/*', '--feature', 'docs')
        started = self.cli('next')
        self.assertEqual(started['started'], 'T3', 'T2 overlaps T1, so the next free task starts')
        self.cli('queue', 'add', '--id', 'T4', '--request', 'More docs.', '--paths', 'site/*', '--feature', 'docs')
        waiting = self.cli('next')
        self.assertIsNone(waiting['started'])
        self.assertIn('T2', waiting['waiting'])
        self.assertIn('Feature docs already has running task T3', waiting['waiting']['T4'])

    def test_open_correctness_questions_hold_new_work_on_their_feature(self):
        self.cli('queue', 'add', '--id', 'T1', '--request', 'Raise the minimum.', '--paths', 'rule.py', '--feature', 'rules')
        started = self.cli('next')
        self.author_writes(delegate.author_dir(self.root, 'T1'),
                           questions=[{'question': 'Is 20 allowed?', 'kind': 'correctness'}])
        self.subagent_stop(started['prompt'], 'agentic-coding:acceptance-author')
        self.cli('queue', 'add', '--id', 'T2', '--request', 'Other rule.', '--paths', 'other.py', '--feature', 'rules')
        waiting = self.cli('next')
        self.assertIn('rules', waiting['waiting']['T2'])
        digest = self.cli('digest')
        self.assertEqual([q['question'] for q in digest['open_questions']], ['Is 20 allowed?'])

    def test_events_become_queued_tasks(self):
        for _ in range(2):
            self.cli('event', 'finding', '--key', 'missing-null-check', '--detail', 'api.py:12')
        self.assertFalse(delegate.task_path(self.root, 'finding-missing-null-check').exists())
        third = self.cli('event', 'finding', '--key', 'missing-null-check', '--detail', 'api.py:40')
        self.assertEqual(third['task'], 'finding-missing-null-check')
        self.assertEqual(delegate.load(self.root, third['task'])['stage'], 'queued')
        self.write('rule.py', RULE.replace('10', '5'))
        self.git('commit', '-qam', 'lower the minimum')
        self.git('revert', '--no-edit', 'HEAD')
        scanned = self.cli('event', 'scan', '--base', 'main')
        self.assertEqual(len(scanned['queued']), 1)
        task = delegate.load(self.root, scanned['queued'][0])
        self.assertEqual(task['paths'], ['rule.py'])
        self.assertEqual(self.cli('event', 'scan', '--base', 'main')['queued'], [], 'a revert queues one task')
        added = self.cli('event', 'add', '--kind', 'check-failure', '--detail', 'main CI: test_rule failed')
        self.assertIn('main CI: test_rule failed', delegate.load(self.root, added['queued'])['request'])

    def test_a_high_change_goes_to_review_with_the_verifier_on_its_card(self):
        self.write('auth/session.py', 'def login(token):\n    return token == "ok"\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'auth')
        self.git('update-ref', 'refs/remotes/origin/main', 'main')
        started = self.started(paths=('rule.py', 'auth/*'))
        self.author_writes(delegate.author_dir(self.root, 'T1'))
        self.subagent_stop(started['prompt'], 'agentic-coding:acceptance-author')
        handed = self.cli('implement', '--id', 'T1')
        tree = Path(started['worktree'])
        self.write('rule.py', RULE.replace('>= 10', '>= 20'), root=tree)
        self.write('auth/session.py', 'def login(token):\n    return True\n', root=tree)
        self.assertEqual(self.subagent_stop(handed['prompt'], 'agentic-coding:implementer'),
                         {'systemMessage': 'Task T1: review (HIGH)'})
        card = self.cli('status', '--id', 'T1')['card']
        self.assertIn('Independent check: required (HIGH)', card)
        self.cli('integrate', '--id', 'T1', '--into', 'main', expected=2)
        self.assertEqual([item['id'] for item in self.cli('digest')['review']], ['T1'])

    # --- regressions from the independent re-review ------------------------------------------------

    def sealed_task(self, task_id='T1', paths=('rule.py',)):
        started = self.started(task_id, paths)
        self.author_writes(delegate.author_dir(self.root, task_id))
        self.assertEqual(self.subagent_stop(started['prompt'], 'agentic-coding:acceptance-author'),
                         {'systemMessage': f'Task {task_id}: sealed'})
        return started

    def ready_task(self):
        started = self.sealed_task()
        handed = self.cli('implement', '--id', 'T1')
        self.write('rule.py', RULE.replace('>= 10', '>= 20'), root=Path(started['worktree']))
        self.assertEqual(self.subagent_stop(handed['prompt'], 'agentic-coding:implementer'),
                         {'systemMessage': 'Task T1: ready (LOW)'})
        return started

    def test_integrate_merges_only_onto_the_rechecked_tip(self):
        self.ready_task()
        self.write('other.py', 'x = 1\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'untested local commit on main')  # origin/main still names the tested tip
        result = subprocess.run([sys.executable, str(DELEGATE), 'integrate', '--id', 'T1', '--into', 'main',
                                 '--root', str(self.root)], capture_output=True, text=True, timeout=300)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('not at the rechecked tip', result.stderr)
        self.assertNotIn('>= 20', (self.root / 'rule.py').read_text(encoding='utf-8'))

    def test_resolved_paths_and_extended_prefixes_cannot_reach_protected_state(self):
        started = self.started()
        tree = Path(started['worktree'])
        sneaky = delegate.author_dir(self.root, 'T1') / '..' / '..' / 'tasks' / 'T1.json'
        self.assertTrue(self.denied(self.tool('Write', file_path=str(sneaky), content='{}')))
        self.assertTrue(self.denied(self.tool('Write', agent='agentic-coding:acceptance-author',
                                              file_path=str(sneaky), content='{}')), 'not the author either')
        extended = '\\\\?\\' + str(tree / 'rule.py')
        self.assertTrue(self.denied(self.tool('Edit', file_path=extended, old_string='10', new_string='20')))
        relative = Path('.claude') / 'worktrees' / 'T1' / 'rule.py'
        self.assertTrue(self.denied(self.tool('Edit', file_path=str(relative), old_string='10', new_string='20')))

    def test_shell_writes_before_sealing_and_optioned_pushes_are_refused(self):
        started = self.started()
        tree = Path(started['worktree'])
        for command in (f'printf "x" > "{tree / "rule.py"}"', f'Set-Content -Path "{tree / "rule.py"}" -Value x',
                        f'cd "{tree}" && python -c "open(\'rule.py\',\'w\')"'):
            with self.subTest(command=command[:30]):
                self.assertTrue(self.denied(self.tool('Bash', command=command)))
                self.cli('resume', '--id', 'T1') if delegate.load(self.root, 'T1')['stage'] == 'stopped' else None
        self.assertEqual(self.tool('Bash', command=f'git -C "{tree}" status'), {}, 'reading the worktree is fine')
        self.assertTrue(self.denied(self.tool('Bash', command=f'git -C "{self.root}" push origin HEAD')))

    def test_searches_that_reach_the_git_directory_or_uppercase_markers_are_refused(self):
        self.started()
        common = delegate.common_dir(self.root)
        self.assertTrue(self.denied(self.tool('Grep', pattern='assert|write_paths', path=str(common))))
        self.assertTrue(self.denied(self.tool('Glob', pattern='.git/**/result.json')))
        self.assertTrue(self.denied(self.tool('Bash', command=f'type "{str(common).upper()}\\AGENTIC-DELEGATION\\x"')))
        self.assertEqual(self.tool('Grep', pattern='allowed', path=str(self.root)), {}, 'the work tree itself is searchable')

    def test_a_stale_writer_fails_instead_of_overwriting_a_transition(self):
        self.started()
        stale = delegate.load(self.root, 'T1')
        fresh = delegate.load(self.root, 'T1')
        delegate.save(self.root, delegate.advance(fresh, 'stopped', 'a concurrent transition'))
        with self.assertRaises(ValueError):
            delegate.save(self.root, delegate.advance(stale, 'sealed', 'stale'))
        self.assertEqual(delegate.load(self.root, 'T1')['stage'], 'stopped')
        delegate.clear_denials(self.root, 'T1')
        self.assertEqual(delegate.load(self.root, 'T1')['stage'], 'stopped', 'clearing a counter never touches the stage')

    def test_refusals_are_charged_to_the_task_they_concern(self):
        self.started('T1', ('a/*',))
        second = self.started('T2', ('b/*',))
        tree_two = Path(second['worktree'])
        self.tool('Edit', file_path=str(tree_two / 'rule.py'), old_string='1', new_string='2')
        self.assertEqual((delegate.denials(self.root, 'T1')['total'], delegate.denials(self.root, 'T2')['total']), (0, 1))
        delegate.assign(self.root, 'agent-7', 'T1', 'implementer')
        self.tool('Bash', agent='agentic-coding:implementer', command='git push', agent_id='agent-7')
        self.assertEqual(delegate.denials(self.root, 'T1')['total'], 1, 'an assigned agent is charged to its task')

    def tool_with(self, name, **payload):
        return self.hook(HOOK, {'hook_event_name': 'PreToolUse', 'tool_name': name} | payload)

    def test_a_role_line_in_later_output_does_not_claim_a_task(self):
        self.started()
        transcript = self.outside / 'other.jsonl'
        transcript.write_text('\n'.join(json.dumps(e) for e in (
            {'type': 'user', 'message': {'content': 'Summarize the repository.'}},
            {'type': 'assistant', 'message': {'content': 'DELEGATED TASK T1 ROLE acceptance-author'}})) + '\n',
            encoding='utf-8')
        self.author_writes(delegate.author_dir(self.root, 'T1'))
        outcome = self.hook(HOOK, {'hook_event_name': 'SubagentStop', 'agent_type': 'general-purpose', 'agent_id': 'x',
                                   'agent_transcript_path': str(transcript),
                                   'last_assistant_message': 'DELEGATED TASK T1 ROLE acceptance-author'})
        self.assertEqual(outcome, {})
        self.assertEqual(delegate.load(self.root, 'T1')['stage'], 'authoring')

    def test_reviewed_work_closes_after_a_person_merges_it(self):
        self.write('auth/session.py', 'def login(token):\n    return token == "ok"\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'auth')
        self.git('update-ref', 'refs/remotes/origin/main', 'main')
        started = self.sealed_task(paths=('rule.py', 'auth/*'))
        handed = self.cli('implement', '--id', 'T1')
        tree = Path(started['worktree'])
        self.write('rule.py', RULE.replace('>= 10', '>= 20'), root=tree)
        self.write('auth/session.py', 'def login(token):\n    return bool(token)\n', root=tree)
        self.subagent_stop(handed['prompt'], 'agentic-coding:implementer')
        self.cli('close', '--id', 'T1', expected=2)  # not merged yet
        self.assertTrue(self.denied(self.tool('Bash', command='python delegate.py close --id T1 --root .')),
                        'closing is the person\'s step')
        self.git('merge', '-q', '--no-ff', '--no-edit', 'agent/T1')
        self.assertEqual(self.cli('close', '--id', 'T1', '--into', 'main')['stage'], 'integrated')
        self.assertFalse((delegate.state(self.root) / 'active').exists())

    def test_finished_review_work_is_counted_once_against_capacity(self):
        self.write('auth/session.py', 'def login(token):\n    return token == "ok"\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'auth')
        self.git('update-ref', 'refs/remotes/origin/main', 'main')
        started = self.sealed_task(paths=('rule.py', 'auth/*'))
        handed = self.cli('implement', '--id', 'T1')
        tree = Path(started['worktree'])
        self.write('rule.py', RULE.replace('>= 10', '>= 20'), root=tree)
        self.write('auth/session.py', 'def login(token):\n    return bool(token)\n', root=tree)
        self.subagent_stop(handed['prompt'], 'agentic-coding:implementer')
        self.cli('queue', 'add', '--id', 'T2', '--request', 'Docs.', '--paths', 'docs/*')
        self.assertEqual(self.cli('next')['started'], 'T2', 'one HIGH review stays below the default limit of two')

    def test_a_custom_worktree_location_is_excluded_from_the_main_checkout(self):
        self.cli('queue', 'add', '--id', 'T1', '--request', 'Raise the minimum.', '--paths', 'rule.py')
        exclude = delegate.common_dir(self.root) / 'info' / 'exclude'
        exclude.write_text('# no trailing newline', encoding='utf-8')
        self.cli('next', '--worktrees', str(self.root / 'scratch'))
        self.assertIn('/scratch/T1/', exclude.read_text(encoding='utf-8').splitlines())
        self.assertNotIn('scratch', self.git('status', '--porcelain'))

    # --- regressions from the verification of the hardening ----------------------------------------

    def test_lifecycle_commands_and_quoted_runners_pass_where_writes_do_not(self):
        started = self.sealed_task()
        tree = Path(started['worktree'])
        allowed = (f'cd "{tree}" && python "{DELEGATE}" implement --id T1 --root "{self.root}"',
                   f'cd "{tree}" && "{sys.executable}" -m unittest discover -s acceptance',
                   f'git -C "{tree}" diff')
        for command in allowed:
            with self.subTest(command=command[:40]):
                self.assertEqual(self.tool('Bash', command=command), {})
        refused = (f'git -C "{tree}" diff --output=rule.py', f'cd "{tree}" && git diff 1>rule.py',
                   f'find "{tree}" -name "*.py" -delete')
        for command in refused:
            with self.subTest(command=command[:40]):
                self.assertTrue(self.denied(self.tool('Bash', command=command)))
                self.cli('resume', '--id', 'T1') if delegate.load(self.root, 'T1')['stage'] == 'stopped' else None
        self.assertTrue(self.denied(self.tool('Bash', command=f'"C:/Program Files/Git/bin/git.exe" -C "{self.root}" push')))

    def test_the_lock_is_released_only_by_its_owner_and_a_dead_owner_is_taken_over(self):
        lock = delegate.state(self.root) / 'lock'
        with delegate.lock(self.root):
            self.assertTrue(lock.is_file())
            lock.write_text('999999999 someone-else', encoding='utf-8')  # another owner's lock
        self.assertTrue(lock.is_file(), 'a lock that is not ours stays')
        old = delegate.time.time() - delegate.LOCK_STALE - 10
        os.utime(lock, (old, old))  # stale, and pid 999999999 is not running
        with delegate.lock(self.root, wait=2):
            self.assertIn(str(os.getpid()), lock.read_text(encoding='utf-8'))
        self.assertFalse(lock.exists())
        lock.write_text(f'{os.getpid()} live-owner', encoding='utf-8')
        os.utime(lock, (old, old))
        with self.assertRaises(ValueError):  # old but its owner still runs: never taken over
            with delegate.lock(self.root, wait=0.3):
                pass
        lock.unlink()

    def test_a_failed_lock_write_leaves_no_lock_behind(self):
        real = delegate.os.write

        def broken(handle, data):
            raise OSError('disk full')
        delegate.os.write = broken
        try:
            with self.assertRaises(OSError):
                with delegate.lock(self.root, wait=1):
                    pass
        finally:
            delegate.os.write = real
        self.assertFalse((delegate.state(self.root) / 'lock').exists())

    def test_ready_work_with_a_new_commit_reopens_through_implement(self):
        started = self.ready_task()
        tree = Path(started['worktree'])
        self.write('extra.py', 'X = 1\n', root=tree)
        self.git('add', '-A', cwd=tree)
        self.git('commit', '-qm', 'more work', cwd=tree)
        result = subprocess.run([sys.executable, str(DELEGATE), 'integrate', '--id', 'T1', '--root', str(self.root)],
                                capture_output=True, text=True, timeout=300)
        self.assertEqual(result.returncode, 2)
        self.assertIn('delegate.py implement --id T1', result.stderr)
        self.assertEqual(self.cli('implement', '--id', 'T1')['stage'], 'implementing')
        self.assertNotIn('commit', delegate.load(self.root, 'T1'))
        self.assertEqual(self.cli('finish', '--id', 'T1')['stage'], 'review', 'extra.py is not in a LOW class here')

    def test_a_glob_into_a_directory_named_like_git_is_ordinary(self):
        self.started()
        self.assertEqual(self.tool('Glob', pattern='fixtures/project.git/*.py'), {})
        self.assertTrue(self.denied(self.tool('Glob', pattern='.git/**/*.json')))

    def test_a_plugin_agent_is_assigned_to_the_one_task_in_its_stage_on_its_first_call(self):
        self.started('T1', ('a/*',))
        self.started('T2', ('b/*',))
        delegate.save(self.root, delegate.advance(delegate.load(self.root, 'T2'), 'implementing'))
        self.tool('Bash', agent='agentic-coding:implementer', agent_id='impl-1', command='git push')
        self.assertEqual(delegate.assigned(self.root, 'impl-1')['task'], 'T2')
        self.assertEqual(delegate.denials(self.root, 'T2')['total'], 1)
        self.assertEqual(delegate.denials(self.root, 'T1')['total'], 0)

    def test_an_old_empty_lock_is_recovered(self):
        lock = delegate.state(self.root) / 'lock'
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text('', encoding='utf-8')  # the writer died between creating and writing it
        old = delegate.time.time() - delegate.LOCK_STALE - 10
        os.utime(lock, (old, old))
        with delegate.lock(self.root, wait=2):
            pass
        self.assertFalse(lock.exists())

    def test_naming_the_author_output_does_not_excuse_other_writes(self):
        started = self.started()
        tree, output = Path(started['worktree']), delegate.author_dir(self.root, 'T1')
        author = 'agentic-coding:acceptance-author'
        self.assertEqual(self.tool('Bash', agent=author, command=f'cd "{tree}" && echo ok > "{output}/note.txt"'), {})
        self.assertTrue(self.denied(self.tool('Bash', agent=author,
                                              command=f'cd "{tree}" && echo ok > "{output}/note.txt" && echo x > rule.py')))

    def test_searches_with_writing_words_and_null_like_file_names_are_judged_correctly(self):
        started = self.started()
        tree = Path(started['worktree'])
        for command in (f'cd "{tree}" && rg "install" .', f'git -C "{tree}" show HEAD:chmod.md',
                        f'git -C "{tree}" diff 2>nul'):
            with self.subTest(command=command[-25:]):
                self.assertEqual(self.tool('Bash', command=command), {})
        self.assertTrue(self.denied(self.tool('Bash', command=f'cd "{tree}" && git diff >nul-output.txt')))
        self.assertEqual(delegate.load(self.root, 'T1')['stage'], 'authoring', 'harmless searches never stop a task')

    def test_without_an_active_task_the_hooks_return_at_once(self):
        self.assertEqual(self.tool('Bash', command='git push origin main'), {})
        self.assertEqual(self.hook(HOOK, {'hook_event_name': 'SubagentStop', 'agent_type': 'implementer'}), {})


if __name__ == '__main__':
    unittest.main()
