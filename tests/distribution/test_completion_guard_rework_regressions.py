"""Independent second-round check of the Stop guard after the shell-parsing rework, run as the hook runs."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / 'authoring/scripts/completion_guard.py'
BODY = ''.join(f'line{i} = {i}\n' for i in range(10))  # 10 code lines
OLD = {'GIT_COMMITTER_DATE': '2026-01-01T00:00:00Z', 'GIT_AUTHOR_DATE': '2026-01-01T00:00:00Z'}


def prompt(text, **extra):
    return {'type': 'user', 'message': {'role': 'user', 'content': text}, **extra}


def tool(name, **arguments):
    return {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
        {'type': 'tool_use', 'id': 'x', 'name': name, 'input': arguments}]}}


def result(content='ok', tool_use_id='x'):
    return {'type': 'user', 'message': {'role': 'user', 'content': [
        {'type': 'tool_result', 'tool_use_id': tool_use_id, 'content': content}]}}


RUN = tool('Bash', command='python -m unittest')
UNCHECKED = 'not handed to an independent verifier'
UNOBSERVED = 'after the last executed command'


class ReworkRegressions(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def git(self, *args, env=None):
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=t@e.invalid', '-c', 'user.name=t', *args],
                       check=True, capture_output=True, env=os.environ | (env or {}))

    def write(self, name, data):
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            (self.root / name).write_bytes(data)
        else:
            (self.root / name).write_text(data, encoding='utf-8')

    def repo(self, files, commit=True):
        self.git('init', '-q')
        for name, text in {'.gitignore': 'transcript.jsonl\n', **files}.items():
            self.write(name, text)
        if commit:
            self.git('add', '-A')
            self.git('commit', '-qm', 'base', env=OLD)  # the base predates the turn

    def stop(self, entries):
        transcript = self.root / 'transcript.jsonl'
        transcript.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.root),
                   'transcript_path': str(transcript), 'stop_hook_active': False}
        process = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload), capture_output=True,
                                 text=True, encoding='utf-8', timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def edit(self, name='src/app.py'):
        return tool('Edit', file_path=str(self.root / name), old_string='a', new_string='b')

    # --- executed commands must still clear the unobserved-edit check ---------------------------

    def test_running_an_interpreter_script_and_capturing_its_output_is_an_execution(self):
        self.repo({'src/app.py': 'x = 1\n'})
        for command in ("python - <<'EOF' > .work/run.log\nimport app\nprint(app.main())\nEOF",
                        'python -c "import app; print(app.main())" > .work/out.log',
                        'npm test > .work/test.log'):
            with self.subTest(command=command):
                decision = self.stop([prompt('fix'), self.edit(), result(), tool('Bash', command=command), result()])
                self.assertNotIn(UNOBSERVED, decision.get('reason', ''), decision)

    def test_inspection_only_commands_after_an_edit_still_block(self):
        self.repo({'src/app.py': 'x = 1\n'})
        decision = self.stop([prompt('fix'), self.edit(), result(),
                              tool('Bash', command='git diff --check && git add -A && git commit -m x'), result(),
                              tool('Bash', command="cat <<'EOF'\nnotes\nEOF"), result()])
        self.assertIn(UNOBSERVED, decision.get('reason', ''))

    # --- earlier-turn changes, scratch-only writes and binaries do not count ---------------------

    def test_script_editing_a_test_does_not_count_an_earlier_turns_change_to_a_similarly_named_file(self):
        self.repo({'src/app.py': 'x = 1\n', 'tests/test_app.py': 'y = 1\n'})
        self.write('src/app.py', BODY)  # uncommitted change from an earlier turn
        self.write('tests/test_app.py', 'y = 2\n')  # this turn: one line
        command = "python - <<'EOF'\nopen('tests/test_app.py', 'w').write('y = 2\\n')\nEOF"
        self.assertNotIn(UNCHECKED, self.stop([prompt('fix'), tool('Bash', command=command), result(),
                                               RUN, result()]).get('reason', ''))

    def test_script_that_reads_a_dirty_file_and_writes_only_scratch_makes_no_edit(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', BODY)  # uncommitted change from an earlier turn
        scratch = Path(tempfile.gettempdir()) / 'guard-scratch.txt'
        command = (f"python - <<'EOF'\ns = open('src/app.py').read()\n"
                   f"open(r'{scratch}', 'w').write(str(len(s)))\nEOF")
        self.assertNotIn(UNCHECKED, self.stop([prompt('look'), tool('Bash', command=command), result()])
                         .get('reason', ''))

    def test_binary_output_a_script_writes_is_not_counted(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', 'x = 2\n')
        self.write('dist/app.bin', b'\0\x01\n' * 500)
        command = ("python - <<'EOF'\nopen('src/app.py', 'w').write('x = 2\\n')\n"
                   "open('dist/app.bin', 'wb').write(b'\\0\\x01\\n' * 500)\nEOF")
        self.assertNotIn(UNCHECKED, self.stop([prompt('build'), tool('Bash', command=command), result(),
                                               RUN, result()]).get('reason', ''))

    # --- edits of >= 5 lines are still held to the rule ------------------------------------------

    def test_script_creating_code_in_a_repository_without_commits_is_held(self):
        self.repo({}, commit=False)
        self.write('src/app.py', BODY)
        command = "python - <<'EOF'\nopen('src/app.py', 'w').write(BODY)\nEOF"
        self.assertIn(UNCHECKED, self.stop([prompt('start'), tool('Bash', command=command), result(),
                                            RUN, result()]).get('reason', ''))

    def test_sed_edit_committed_within_a_turn_with_a_real_timestamp_is_held(self):
        self.repo({'src/app.py': 'x = 1\n'})
        started = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        self.write('src/app.py', BODY)
        self.git('commit', '-qam', 'fix')
        entries = [prompt('fix', timestamp=started), tool('Bash', command="sed -i 's/x/line/' src/app.py"), result(),
                   RUN, result(), tool('Bash', command='git add -A && git commit -m fix'), result()]
        self.assertIn(UNCHECKED, self.stop(entries).get('reason', ''))

    # --- the 0.1.92 verifier-violation / probe rule ----------------------------------------------

    def test_probe_rule_still_applies(self):
        self.repo({'src/app.py': 'x = 1\n', '.harness/probes.json': '{}\n'})
        launch = {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
            {'type': 'tool_use', 'id': 'v', 'name': 'Agent',
             'input': {'prompt': 'INDEPENDENT VERIFIER. A colleague implemented the request below.'}}]}}
        report = result('done\n{"verdict": "incomplete", "violations": [{"path": "a"}, {"path": "b"}], '
                        '"questions": []}', tool_use_id='v')
        base = [prompt('fix'), tool('Edit', file_path=str(self.root / 'src/app.py'), old_string='a',
                                    new_string='\n'.join('b' * 6)), result(), launch, report]
        self.assertIn('reported 2 violation(s)', self.stop(base + [RUN, result()]).get('reason', ''))
        probes = {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
            {'type': 'tool_use', 'id': 'p', 'name': 'Bash',
             'input': {'command': 'python probe_check.py probes --root .'}}]}}
        killed = result('# Probe checks\n\nOrigins: independent-check 2/2\n', tool_use_id='p')
        # Since 0.1.97 a registry edit alone is not evidence; a probe run that kills the probes is.
        for update in (tool('Edit', file_path=str(self.root / '.harness/probes.json'), old_string='{', new_string='{ '),
                       tool('Bash', command="cat > .harness/probes.json <<'EOF'\n{\"probes\": []}\nEOF")):
            with self.subTest(update=update['message']['content'][0]['name']):
                self.assertIn('reported 2 violation(s)',
                              self.stop(base + [update, result(), RUN, result()]).get('reason', ''))
                self.assertEqual(self.stop(base + [update, result(), probes, killed]), {})


if __name__ == '__main__':
    unittest.main()
