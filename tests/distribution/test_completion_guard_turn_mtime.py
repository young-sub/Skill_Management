"""Independent final-round check of the Stop guard's turn-start attribution (prompt timestamp and file
mtimes), run as the hook runs, with realistic ISO `Z` transcript timestamps."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / 'authoring/scripts/completion_guard.py'
BODY = ''.join(f'line{i} = {i}\n' for i in range(10))  # 10 code lines
UNCHECKED = 'not handed to an independent verifier'


def iso(moment):
    return moment.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def prompt(text, started):
    return {'type': 'user', 'message': {'role': 'user', 'content': text}, 'timestamp': iso(started)}


def tool(name, **arguments):
    return {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
        {'type': 'tool_use', 'id': 'x', 'name': name, 'input': arguments}]}}


def result():
    return {'type': 'user', 'message': {'role': 'user', 'content': [
        {'type': 'tool_result', 'tool_use_id': 'x', 'content': 'ok'}]}}


RUN = tool('Bash', command='python -m unittest')
# Paths built at run time, which the guard cannot read from the script text.
FSTRING_ONE_LINE = "python - <<'EOF'\nfrom pathlib import Path\nfor n in ['app']:\n    Path(f'src/{n}.py').write_text('x = 2\\n')\nEOF"
FSTRING_BODY = "python - <<'EOF'\nfrom pathlib import Path\nfor n in ['app']:\n    Path(f'src/{n}.py').write_text(BODY)\nEOF"


class TurnStartAttribution(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.now = datetime.now(timezone.utc)
        self.started = self.now - timedelta(minutes=1)
        self.git('init', '-q')
        for name, text in {'.gitignore': 'transcript.jsonl\n', 'src/app.py': 'x = 1\n', 'src/other.py': 'y = 1\n'}.items():
            self.write(name, text)
        self.git('add', '-A')
        self.git('commit', '-qm', 'base', at=self.now - timedelta(days=1))

    def git(self, *args, at=None):
        env = os.environ.copy()
        if at:
            env |= {'GIT_COMMITTER_DATE': iso(at), 'GIT_AUTHOR_DATE': iso(at)}
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=t@e.invalid', '-c', 'user.name=t', *args],
                       check=True, capture_output=True, env=env)

    def write(self, name, text, at=None):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        if at:
            os.utime(path, (at.timestamp(), at.timestamp()))

    def earlier_turn_change(self):
        """src/other.py: 10 uncommitted lines written an hour before this turn."""
        self.write('src/other.py', BODY, at=self.now - timedelta(hours=1))

    def stop(self, entries):
        transcript = self.root / 'transcript.jsonl'
        transcript.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.root),
                   'transcript_path': str(transcript), 'stop_hook_active': False}
        process = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload), capture_output=True,
                                 text=True, encoding='utf-8', timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout).get('reason', '')

    def test_this_turns_runtime_path_edit_is_held_and_earlier_turn_lines_are_not_added(self):
        self.earlier_turn_change()
        self.write('src/app.py', BODY)  # this turn: 11 changed lines
        reason = self.stop([prompt('fix', self.started), tool('Bash', command=FSTRING_BODY), result(), RUN, result()])
        self.assertIn(f'11 changed code line(s) were {UNCHECKED}', reason)

    def test_small_runtime_path_edit_ignores_an_earlier_turns_change(self):
        self.earlier_turn_change()
        self.write('src/app.py', 'x = 2\n')
        reason = self.stop([prompt('fix', self.started), tool('Bash', command=FSTRING_ONE_LINE), result(), RUN, result()])
        self.assertNotIn(UNCHECKED, reason)

    def test_committing_an_earlier_turns_change_in_this_turn_does_not_count_it(self):
        self.earlier_turn_change()
        self.write('src/app.py', 'x = 2\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'fix')  # committed now, inside the turn
        entries = [prompt('fix', self.started), tool('Bash', command=FSTRING_ONE_LINE), result(), RUN, result(),
                   tool('Bash', command='git add -A && git commit -m fix'), result()]
        self.assertNotIn(UNCHECKED, self.stop(entries))

    def test_an_earlier_turns_commit_is_not_measured_as_this_turns_change(self):
        self.write('src/app.py', BODY, at=self.now - timedelta(minutes=30))
        self.git('commit', '-qam', 'earlier turn', at=self.now - timedelta(minutes=30))
        self.write('src/app.py', BODY.replace('line0 = 0', 'line0 = 1'))  # this turn: 2 changed lines
        self.git('commit', '-qam', 'this turn')
        entries = [prompt('fix', self.started), tool('Bash', command="sed -i 's/line0 = 0/line0 = 1/' src/app.py"),
                   result(), RUN, result(), tool('Bash', command='git commit -am fix'), result()]
        self.assertNotIn(UNCHECKED, self.stop(entries))

    def test_edit_tool_turn_still_held_with_a_timestamp(self):
        self.earlier_turn_change()
        edit = tool('Edit', file_path=str(self.root / 'src/app.py'), old_string='x = 1', new_string=BODY)
        self.write('src/app.py', BODY)
        self.assertIn(UNCHECKED, self.stop([prompt('fix', self.started), edit, result(), RUN, result()]))

    def test_no_edit_turn_with_timestamp_passes(self):
        self.write('src/app.py', BODY)  # dirty, but modified during this turn by nothing the guard sees as an edit
        reading = "python - <<'EOF'\nprint(open('src/app.py').read())\nEOF"
        self.assertEqual(self.stop([prompt('look', self.started), tool('Bash', command=reading), result()]), '')


if __name__ == '__main__':
    unittest.main()
