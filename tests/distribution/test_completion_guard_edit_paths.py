"""Independent check of the Stop guard's independent-check rule across edit paths, run as the hook runs."""
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


def prompt(text):
    return {'type': 'user', 'message': {'role': 'user', 'content': text}}


def tool(name, **arguments):
    return {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
        {'type': 'tool_use', 'id': 'x', 'name': name, 'input': arguments}]}}


def result():
    return {'type': 'user', 'message': {'role': 'user', 'content': [
        {'type': 'tool_result', 'tool_use_id': 'x', 'content': 'ok'}]}}


RUN = tool('Bash', command='python -m unittest')


class IndependentCheckPaths(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=t@e.invalid', '-c', 'user.name=t', *args],
                       check=True, capture_output=True)

    def repo(self, files):
        self.git('init', '-q')
        files = {'.gitignore': 'transcript.jsonl\n', **files}
        for name, text in files.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text, encoding='utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'base')

    def write(self, name, text):
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        (self.root / name).write_text(text, encoding='utf-8')

    def stop(self, entries, env=None):
        transcript = self.root / 'transcript.jsonl'
        transcript.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.root),
                   'transcript_path': str(transcript), 'stop_hook_active': False}
        process = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload), capture_output=True,
                                 text=True, encoding='utf-8', env=env, timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def assert_check_required(self, decision):
        self.assertIn('not handed to an independent verifier', decision.get('reason', ''), decision)

    def assert_no_check_required(self, decision):
        self.assertNotIn('not handed to an independent verifier', decision.get('reason', ''), decision)

    # --- edits of >= 5 code lines are held to the rule, however they were made -----------------

    def test_python_c_script_with_semicolons_is_an_edit(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', BODY)  # the effect the command had
        command = 'python -c "import pathlib; pathlib.Path(\'src/app.py\').write_text(BODY)"'
        self.assert_check_required(self.stop([prompt('fix'), tool('Bash', command=command), result(), RUN, result()]))

    def test_set_content_with_encoding_before_path_is_an_edit(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', BODY)
        for command in ('$code | Set-Content -Encoding utf8 -Path src/app.py',
                        'Set-Content -Value $code -Path src/app.py'):
            with self.subTest(command=command):
                self.assert_check_required(self.stop([prompt('fix'), tool('PowerShell', command=command), result(),
                                                      RUN, result()]))

    def test_interpreter_heredoc_redirected_into_a_code_file_is_an_edit(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', BODY)
        command = "python - <<'EOF' > src/app.py\nfor i in range(10):\n    print(f'line{i} = {i}')\nEOF"
        self.assert_check_required(self.stop([prompt('fix'), tool('Bash', command=command), result(), RUN, result()]))

    def test_heredoc_edit_committed_in_the_same_turn_still_counts(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', BODY)
        self.git('commit', '-qam', 'fix')  # the agent committed within the turn
        entries = [prompt('fix'), tool('Bash', command=f"cat > src/app.py <<'EOF'\n{BODY}EOF"), result(), RUN, result(),
                   tool('Bash', command='git add -A && git commit -m fix'), result()]
        self.assert_check_required(self.stop(entries))

    def test_shell_heredoc_after_cd_is_sized(self):
        self.repo({'shop/store.py': 'x = 1\n'})
        self.write('shop/store.py', BODY)
        command = f"cd shop && cat > store.py <<'EOF'\n{BODY}EOF"
        self.assert_check_required(self.stop([prompt('fix'), tool('Bash', command=command), result(), RUN, result()]))

    def test_heredoc_to_non_ascii_file_name_is_sized(self):
        self.repo({'shop/상점.py': 'x = 1\n'})
        self.write('shop/상점.py', BODY)
        command = f"cat > shop/상점.py <<'EOF'\n{BODY}EOF"
        self.assert_check_required(self.stop([prompt('fix'), tool('Bash', command=command), result(), RUN, result()]))

    def test_incident_shape_is_blocked(self):
        self.repo({'shop/store.py': 'x = 1\n', 'tests/test_store.py': 'y = 1\n'})
        self.write('shop/store.py', BODY)
        self.write('tests/test_store.py', 'y = 1\nz = 2\nw = 3\n')
        script = ("python - <<'EOF'\np = 'tests/test_store.py'\ns = open(p).read() + 'z = 2\\nw = 3\\n'\n"
                  "open(p,'w').write(s)\nEOF")
        entries = [prompt('fix'), tool('Bash', command=f"cat > shop/store.py <<'EOF'\n{BODY}EOF"), result(),
                   tool('Bash', command=script), result(), RUN, result()]
        self.assert_check_required(self.stop(entries))

    # --- earlier-turn changes, no-edit turns, docs and binaries are not counted ------------------

    def test_script_that_writes_only_a_scratch_file_does_not_count_earlier_turn_changes(self):
        self.repo({'src/app.py': 'x = 1\n', 'src/other.py': 'y = 1\n'})
        self.write('src/other.py', BODY)  # uncommitted change from an earlier turn
        scratch = Path(tempfile.gettempdir()) / 'guard-scratch.json'
        command = f"python - <<'EOF'\nimport json\nopen(r'{scratch}', 'w').write(json.dumps({{}}))\nEOF"
        self.assert_no_check_required(self.stop([prompt('look'), tool('Bash', command=command), result()]))

    def test_small_script_edit_does_not_count_earlier_turn_changes_in_other_files(self):
        self.repo({'src/app.py': 'x = 1\n', 'src/other.py': 'y = 1\n'})
        self.write('src/other.py', BODY)  # uncommitted change from an earlier turn
        self.write('src/app.py', 'x = 2\n')  # this turn: one line
        command = "python - <<'EOF'\nopen('src/app.py', 'w').write('x = 2\\n')\nEOF"
        self.assert_no_check_required(self.stop([prompt('fix'), tool('Bash', command=command), result(),
                                                 RUN, result()]))

    def test_no_edit_turn_with_dirty_tree_passes(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', BODY)
        reading = "python - <<'EOF'\nprint(open('src/app.py').read())\nEOF"
        self.assertEqual(self.stop([prompt('look'), tool('Bash', command=reading), result(), RUN, result()]), {})

    def test_documentation_and_binary_output_are_not_counted(self):
        self.repo({'src/app.py': 'x = 1\n', 'docs/guide.md': 'a\n'})
        self.write('docs/guide.md', BODY * 5)
        self.write('src/app.py', 'x = 2\n')
        (self.root / 'build').mkdir()
        (self.root / 'build/app.bin').write_bytes(b'\0\x01\n' * 500)
        command = ("python - <<'EOF'\nopen('docs/guide.md','w').write('...')\nopen('src/app.py','w').write('x = 2\\n')"
                   "\nEOF")
        self.assert_no_check_required(self.stop([prompt('fix'), tool('Bash', command=command), result(),
                                                 RUN, result()]))

    # --- Git unavailable never traps -------------------------------------------------------------

    def test_git_unavailable_does_not_trap(self):
        self.repo({'src/app.py': 'x = 1\n'})
        self.write('src/app.py', BODY)
        env = {k: v for k, v in os.environ.items() if k.upper() != 'PATH'}
        env['PATH'] = os.path.dirname(sys.executable)
        command = "python - <<'EOF'\nopen('src/app.py','w').write('x')\nEOF"
        decision = self.stop([prompt('fix'), tool('Bash', command=command), result(), RUN, result()], env=env)
        self.assertIsInstance(decision, dict)  # exit 0 with a JSON decision: no trap, no crash
        # Stop-hook-active must always release.
        transcript = self.root / 'transcript.jsonl'
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.root), 'transcript_path': str(transcript),
                   'stop_hook_active': True}
        process = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload), capture_output=True,
                                 text=True, env=env, timeout=60)
        self.assertEqual((process.returncode, json.loads(process.stdout)), (0, {}))


if __name__ == '__main__':
    unittest.main()
