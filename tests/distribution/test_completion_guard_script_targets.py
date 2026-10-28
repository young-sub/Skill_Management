"""Independent third-round check of the Stop guard: verification scripts that write reports, and
write calls whose target is not a plain literal. Run as the hook runs."""
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
UNCHECKED = 'not handed to an independent verifier'
UNOBSERVED = 'after the last executed command'


def prompt(text):
    return {'type': 'user', 'message': {'role': 'user', 'content': text}}


def tool(name, **arguments):
    return {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
        {'type': 'tool_use', 'id': 'x', 'name': name, 'input': arguments}]}}


def result():
    return {'type': 'user', 'message': {'role': 'user', 'content': [
        {'type': 'tool_result', 'tool_use_id': 'x', 'content': 'ok'}]}}


RUN = tool('Bash', command='python -m unittest')


class ScriptTargets(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        subprocess.run(['git', '-C', str(self.root), 'init', '-q'], check=True, capture_output=True)
        for name, text in {'.gitignore': 'transcript.jsonl\n.work/\n', 'src/app.py': 'x = 1\n'}.items():
            self.write(name, text)
        subprocess.run(['git', '-C', str(self.root), 'add', '-A'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=t@e.invalid', '-c', 'user.name=t',
                        'commit', '-qm', 'base'], check=True, capture_output=True, env=os.environ | OLD)

    def write(self, name, text):
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        (self.root / name).write_text(text, encoding='utf-8')

    def stop(self, entries):
        transcript = self.root / 'transcript.jsonl'
        transcript.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')
        payload = {'hook_event_name': 'Stop', 'cwd': str(self.root),
                   'transcript_path': str(transcript), 'stop_hook_active': False}
        process = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload), capture_output=True,
                                 text=True, encoding='utf-8', timeout=60)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    # --- a verification run that writes a report still counts as having run ---------------------

    def test_verification_script_writing_a_report_clears_the_unobserved_edit_check(self):
        edit = tool('Edit', file_path=str(self.root / 'src/app.py'), old_string='x = 1', new_string='x = 2')
        for command in ("python - <<'EOF'\nimport json, app\nopen('.work/report.json', 'w').write("
                        "json.dumps({'ok': app.main()}))\nEOF",
                        'python -c "import json, app; open(\'.work/report.json\', \'w\').write(json.dumps(app.main()))"'):
            with self.subTest(command=command[:30]):
                decision = self.stop([prompt('fix'), edit, result(), tool('Bash', command=command), result()])
                self.assertNotIn(UNOBSERVED, decision.get('reason', ''), decision)

    # --- write calls whose targets are not plain literals are still edits of their files --------

    def assert_held(self, script):
        self.write('src/app.py', BODY)  # the effect the script had: 11 changed lines
        decision = self.stop([prompt('fix'), tool('Bash', command=f"python - <<'EOF'\n{script}\nEOF"), result(),
                              RUN, result()])
        self.assertIn(UNCHECKED, decision.get('reason', ''), decision)

    def test_glob_rewrite_script_is_held(self):
        self.assert_held("from pathlib import Path\nfor p in Path('src').glob('*.py'):\n"
                         "    p.write_text(p.read_text().replace('x', 'line'))")

    def test_f_string_target_is_held(self):
        self.assert_held("from pathlib import Path\nfor name in ['app']:\n"
                         "    Path(f'src/{name}.py').write_text(BODY)")

    def test_joined_path_write_next_to_a_literal_write_is_held(self):
        self.assert_held("import json\nfrom pathlib import Path\n(Path('src') / 'app.py').write_text(BODY)\n"
                         "open('.work/progress.json', 'w').write(json.dumps({'done': 1}))")


if __name__ == '__main__':
    unittest.main()
