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


if __name__ == '__main__':
    unittest.main()
