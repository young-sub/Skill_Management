"""The Stop guard blocks once on a behavior change no independent verifier saw and otherwise stays silent."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / 'authoring/scripts/completion_guard.py'


def prompt(text):
    return {'type': 'user', 'message': {'role': 'user', 'content': text}}


def tool(name, **arguments):
    return {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
        {'type': 'text', 'text': 'working'}, {'type': 'tool_use', 'id': 'x', 'name': name, 'input': arguments}]}}


def result():
    return {'type': 'user', 'message': {'role': 'user', 'content': [
        {'type': 'tool_result', 'tool_use_id': 'x', 'content': 'ok'}]}}


class CompletionGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def stop(self, entries, **payload):
        transcript = self.root / 'transcript.jsonl'
        transcript.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.root),
                   'transcript_path': str(transcript), 'stop_hook_active': False} | payload
        process = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload),
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def code_edit(self, name='src/app.py'):
        return tool('Edit', file_path=str(self.root / name), old_string='a', new_string='b')

    def test_small_edits_after_the_last_execution_and_shell_writes_do_not_block(self):
        # Removed rule: a final edit after the last command no longer blocks (0/112 eval, 1/280 real blocks).
        run = tool('Bash', command='python -m unittest')
        for entries in ([run, result(), self.code_edit(), result(), tool('Write', file_path='src/new.py', content='x'), result()],
                        [self.code_edit(), result(), tool('Bash', command='git diff --check && git add -A'), result()],
                        [run, result(), tool('Bash', command="sed -i 's/a - b/a + b/' src/app.py"), result()]):
            with self.subTest(entries=len(entries)):
                self.assertEqual(self.stop([prompt('fix'), *entries]), {})

    def test_documentation_outside_project_and_previous_turn_edits_are_ignored(self):
        self.assertEqual(self.stop([prompt('docs'), self.code_edit('docs/guide.md'), result()]), {})
        outside = tool('Write', file_path=str(Path(tempfile.gettempdir()) / 'scratch.py'), content='x')
        self.assertEqual(self.stop([prompt('scratch'), outside, result()]), {})
        # The same large edit blocks in its own turn and is forgotten once the next human prompt arrives.
        edited = [prompt('fix'), self.large_edit(), result()]
        self.assertEqual(self.stop(edited)['decision'], 'block')
        self.assertEqual(self.stop([*edited, prompt('thanks, what changed?')]), {})

    def large_edit(self, name='src/app.py', lines=5):
        return tool('Edit', file_path=str(self.root / name), old_string='a', new_string='\n'.join(['b'] * lines))

    def verifier(self, prompt_text='INDEPENDENT VERIFIER. A colleague implemented the request below.'):
        return tool('Agent', subagent_type='general-purpose', description='verify', prompt=prompt_text)

    def test_a_behavior_change_needs_an_independent_verifier_after_the_first_code_edit(self):
        run = tool('Bash', command='python -m unittest')
        decision = self.stop([prompt('fix'), self.large_edit(), result(), run, result()])
        self.assertEqual(decision['decision'], 'block')
        self.assertIn('5 changed code line(s) were not handed to an independent verifier', decision['reason'])
        self.assertNotIn('after the last executed command', decision['reason'])
        complete = {'verdict': 'complete', 'violations': [], 'questions': []}
        self.assertEqual(self.stop([prompt('fix'), self.large_edit(), result(), *self.verifier_report(complete),
                                    self.code_edit(), result(), run, result()]), {})
        for entries in ([*self.verifier_report(complete), self.large_edit(), result()],
                        [self.large_edit(), result(), self.verifier('Review this change'), result()]):
            with self.subTest(entries=entries[0]['message']['content'][1]['name']):
                self.assertIn('independent verifier', self.stop([prompt('fix'), *entries, run, result()])['reason'])

    def test_a_verifier_counts_only_when_its_verdict_arrives(self):
        run = tool('Bash', command='python -m unittest')
        before = [prompt('fix'), self.large_edit(), result(), run, result()]
        # Launched but its answer never came back with a verdict line: nothing was verified.
        for answer in ('Async agent launched successfully.', 'Looks fine to me.'):
            with self.subTest(answer=answer):
                self.assertIn('not handed to an independent verifier',
                              self.stop([*before, *self.verifier_report(answer)])['reason'])
        # A background verifier reports through a task notification, which is not a new human prompt.
        launch, _ = self.verifier_report('')
        verdict = json.dumps({'verdict': 'complete', 'violations': [], 'questions': []})
        self.assertEqual(self.stop([*before, launch, self.notification('v', 'Checked.\n' + verdict)]), {})
        self.assertIn('not handed to an independent verifier',
                      self.stop([*before, launch, self.notification('other', 'done')])['reason'])

    def test_a_task_notification_does_not_start_a_new_turn(self):
        decision = self.stop([prompt('fix'), self.large_edit(), result(), self.notification('other', 'done')])
        self.assertEqual(decision['decision'], 'block', 'the edit before the notification still belongs to the turn')
        self.assertIn('not handed to an independent verifier', decision['reason'])

    def notification(self, tool_use_id, text):
        return {'type': 'user', 'origin': {'kind': 'task-notification'}, 'message': {'role': 'user', 'content':
                f'<task-notification>\n<tool-use-id>{tool_use_id}</tool-use-id>\n<result>{text}</result>\n'
                '</task-notification>'}}

    def test_small_documentation_and_outside_changes_skip_the_independent_check(self):
        run = tool('Bash', command='python -m unittest')
        self.assertEqual(self.stop([prompt('fix'), self.large_edit(lines=4), result(), run, result()]), {})
        self.assertEqual(self.stop([prompt('docs'), self.large_edit('docs/guide.md', 50), result()]), {})
        outside = tool('Write', file_path=str(Path(tempfile.gettempdir()) / 'scratch.py'), content='x\n' * 50)
        self.assertEqual(self.stop([prompt('scratch'), outside, result(), run, result()]), {})

    def git_repo(self, **files):
        def git(*args):
            # The base commit predates the turn, as it would in a real session.
            env = os.environ | {'GIT_COMMITTER_DATE': '2026-01-01T00:00:00Z', 'GIT_AUTHOR_DATE': '2026-01-01T00:00:00Z'}
            subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True, env=env)
        git('init', '-q')
        for name, text in files.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text, encoding='utf-8')
        git('add', '-A')
        git('-c', 'user.email=t@e.invalid', '-c', 'user.name=t', 'commit', '-qm', 'base')

    def test_shell_and_script_edits_are_sized_by_git(self):
        self.git_repo(**{'.gitignore': 'transcript.jsonl\n', 'src/app.py':'x = 1\n', 'src/other.py': 'y = 1\n'})
        body = ''.join(f'line{i} = {i}\n' for i in range(10))
        (self.root / 'src/app.py').write_text(body, encoding='utf-8')
        (self.root / 'src/__pycache__').mkdir()
        (self.root / 'src/__pycache__/app.pyc').write_bytes(b'\0\x01\n' * 50)
        run =tool('Bash', command='python -m unittest')
        for command in (f"cat > src/app.py <<'EOF'\n{body}EOF",
                        "python - <<'EOF'\nfrom pathlib import Path\nPath('src/app.py').write_text(body)\nEOF",
                        "cat >> x.tmp <<'EOF'\nEOF\nrm x.tmp\npython - <<'EOF'\nopen('src/app.py', 'w').write(body)\nEOF",
                        "cd src && python3 -c \"open('app.py', 'w').write(body)\""):
            with self.subTest(command=command[:20]):
                decision = self.stop([prompt('fix'), tool('Bash', command=command), result(), run, result()])
                self.assertIn('11 changed code line(s) were not handed', decision.get('reason', ''))
        # A one-line shell write is sized by Git, through a cd and under a non-ASCII name.
        (self.root / 'src/상점.py').write_text(body, encoding='utf-8')
        for command in ("cd src && sed -i 's/x/y/' app.py", "sed -i 's/x/y/' src/상점.py"):
            with self.subTest(command=command):
                decision = self.stop([prompt('fix'), tool('Bash', command=command), result(), run, result()])
                self.assertIn('changed code line(s) were not handed', decision.get('reason', ''))
        (self.root / 'src/상점.py').unlink()
        reading = "python - <<'EOF'\nprint(open('src/app.py').read())\nEOF"
        self.assertEqual(self.stop([prompt('look'), tool('Bash', command=reading), result()]), {})
        # Uncommitted lines from earlier turns in other files do not count toward this turn's edit.
        self.assertEqual(self.stop([prompt('fix'), self.code_edit('src/other.py'), result(), run, result()]), {})

    def test_script_writes_are_attributed_to_their_targets_not_to_files_they_read(self):
        self.git_repo(**{'.gitignore': 'transcript.jsonl\n', 'src/app.py': 'x = 1\n', 'tests/test_app.py': 't = 1\n'})
        (self.root / 'src/app.py').write_text('x = 1\n' * 10, encoding='utf-8')  # an earlier turn's change
        (self.root / 'tests/test_app.py').write_text('t = 2\n', encoding='utf-8')
        run = tool('Bash', command='python -m unittest')
        for script in ("p = 'tests/test_app.py'\ns = open('src/app.py').read()\nopen(p, 'w').write('t = 2')",
                       "for p in ['tests/test_app.py']:\n    open(p, 'w').write('t = 2')"):
            with self.subTest(script=script[:12]):
                command = f"python - <<'EOF'\n{script}\nEOF"
                self.assertEqual(self.stop([prompt('fix'), tool('Bash', command=command), result(), run, result()]), {})
        # A script's captured output is not code, however long.
        (self.root / 'run.log').write_text('ok\n' * 50, encoding='utf-8')
        logged = tool('Bash', command="python - <<'EOF' > run.log\nimport app\nEOF")
        self.assertEqual(self.stop([prompt('fix'), self.code_edit('tests/test_app.py'), result(), logged, result()]), {})

    def test_with_a_turn_start_files_modified_since_belong_to_the_turn_however_written(self):
        self.git_repo(**{'.gitignore': 'transcript.jsonl\n', 'src/app.py': 'x = 1\n', 'src/other.py': 'y = 1\n'})
        (self.root / 'src/other.py').write_text('y = 2\n' * 20, encoding='utf-8')
        os.utime(self.root / 'src/other.py', (1_700_000_000, 1_700_000_000))  # an earlier turn's change
        (self.root / 'src/app.py').write_text('x = 2\n' * 10, encoding='utf-8')  # this turn's rewrite
        started = prompt('fix') | {'timestamp': '2026-06-01T00:00:00.000Z'}
        glob = tool('Bash', command="python - <<'EOF'\nfrom pathlib import Path\n"
                                    "for p in Path('src').glob('a*.py'):\n    p.write_text('x = 2\\n' * 10)\nEOF")
        decision = self.stop([started, glob, result()])
        self.assertIn('11 changed code line(s)', decision.get('reason', ''))
        self.assertNotIn('after the last executed command', decision['reason'])  # a script is an execution

    def test_a_script_edit_committed_within_the_turn_is_sized_from_the_turn_start(self):
        self.git_repo(**{'.gitignore': 'transcript.jsonl\n', 'src/app.py': 'x = 1\n'})
        (self.root / 'src/app.py').write_text(''.join(f'line{i} = {i}\n' for i in range(10)), encoding='utf-8')
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=t@e.invalid', '-c', 'user.name=t',
                        'commit', '-qam', 'fix'], check=True, capture_output=True)
        started = prompt('fix') | {'timestamp': '2026-06-01T00:00:00.000Z'}
        script = tool('Bash', command="python - <<'EOF'\nopen('src/app.py', 'w').write(body)\nEOF")
        entries = [started, script, result(), tool('Bash', command='python -m unittest'), result(),
                   tool('Bash', command='git commit -am fix'), result()]
        self.assertIn('11 changed code line(s)', self.stop(entries).get('reason', ''))
        # Without the turn start, the commit hides the script's change.
        self.assertEqual(self.stop([prompt('fix'), *entries[1:]]), {})

    def verifier_report(self, report):
        launch = tool('Agent', subagent_type='general-purpose', description='verify',
                      prompt='INDEPENDENT VERIFIER. A colleague implemented the request below.')
        launch['message']['content'][1]['id'] = 'v'
        reply = {'type': 'user', 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'v', 'content': [
            {'type': 'text', 'text': 'Import skips the check.\n' + json.dumps(report)}]}]}}
        return [launch, reply]

    def test_reported_violations_without_a_probe_do_not_block(self):
        # Removed rule: probe registration after verifier violations is left to the event loop.
        incomplete = {'verdict': 'incomplete', 'violations': [{'path': 'import', 'test': 't.py:3', 'observed': 'saved'}],
                      'questions': []}
        self.assertEqual(self.stop([prompt('fix'), self.large_edit(), result(), *self.verifier_report(incomplete),
                                    self.code_edit(), result(), tool('Bash', command='python -m unittest'), result()]), {})

    def test_blocks_only_once_and_honors_opt_out_and_unreadable_input(self):
        entries = [prompt('fix'), self.large_edit(), result()]
        self.assertEqual(self.stop(entries)['decision'], 'block')
        self.assertEqual(self.stop(entries, stop_hook_active=True), {})
        self.assertEqual(self.stop(entries, transcript_path=str(self.root / 'missing.jsonl')), {})
        process = subprocess.run([sys.executable, str(GUARD)], input='not json',
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual((process.returncode, json.loads(process.stdout)), (0, {}))


if __name__ == '__main__':
    unittest.main()
