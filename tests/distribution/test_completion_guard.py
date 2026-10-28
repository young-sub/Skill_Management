"""The Stop guard blocks once on an unobserved final code edit and otherwise stays silent."""
import json
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

    def test_blocks_code_edited_after_last_execution(self):
        decision = self.stop([prompt('fix it'), tool('Bash', command='python -m unittest'), result(),
                              self.code_edit(), result(), tool('Write', file_path='src/new.py', content='x'), result()])
        self.assertEqual(decision['decision'], 'block')
        self.assertIn('2 code file(s)', decision['reason'])
        self.assertIn('src/app.py, src/new.py', decision['reason'])

    def test_execution_after_final_edit_allows_stop(self):
        for command in ('python -m unittest tests.test_app', 'cd web && npm test', 'git status; pytest -q'):
            with self.subTest(command=command):
                self.assertEqual(self.stop([prompt('fix'), self.code_edit(), result(),
                                            tool('PowerShell', command=command), result()]), {})

    def test_inspection_only_commands_do_not_count_as_verification(self):
        decision = self.stop([prompt('fix'), self.code_edit(), result(),
                              tool('Bash', command='git diff --check && git add -A && git commit -m x'), result(),
                              tool('Bash', command='cat src/app.py | head -5'), result()])
        self.assertEqual(decision['decision'], 'block')

    def test_shell_file_writes_are_edits_not_verification(self):
        for command in ("sed -i 's/a - b/a + b/' src/app.py",
                        "cat > src/app.py <<'EOF'\nimport os\nprint(os.getcwd())\nEOF",
                        "cd repo && printf 'x' > src/app.py",
                        'Set-Content -Path src/app.py -Value x'):
            with self.subTest(command=command):
                decision = self.stop([prompt('fix'), tool('Bash', command='python -m unittest'), result(),
                                      tool('Bash', command=command), result()])
                self.assertEqual(decision.get('decision'), 'block', decision)
                self.assertIn('src/app.py', decision['reason'])
        self.assertEqual(self.stop([prompt('fix'), tool('Bash', command="sed -i 's/a/b/' src/app.py && npm test"),
                                    result()]), {})
        self.assertEqual(self.stop([prompt('fix'), self.code_edit(), result(),
                                    tool('Bash', command='npm test > .work/test.log'), result()]), {})

    def test_documentation_outside_project_and_previous_turn_edits_are_ignored(self):
        self.assertEqual(self.stop([prompt('docs'), self.code_edit('docs/guide.md'), result()]), {})
        outside = tool('Write', file_path=str(Path(tempfile.gettempdir()) / 'scratch.py'), content='x')
        self.assertEqual(self.stop([prompt('scratch'), outside, result()]), {})
        self.assertEqual(self.stop([prompt('fix'), self.code_edit(), result(), prompt('thanks, what changed?')]), {})

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
        self.assertEqual(self.stop([prompt('fix'), self.large_edit(), result(), self.verifier(), result(),
                                    self.code_edit(), result(), run, result()]), {})
        for entries in ([self.verifier(), result(), self.large_edit(), result()],
                        [self.large_edit(), result(), self.verifier('Review this change'), result()]):
            with self.subTest(entries=entries[0]['message']['content'][1]['name']):
                self.assertIn('independent verifier', self.stop([prompt('fix'), *entries, run, result()])['reason'])

    def test_small_documentation_and_outside_changes_skip_the_independent_check(self):
        run = tool('Bash', command='python -m unittest')
        self.assertEqual(self.stop([prompt('fix'), self.large_edit(lines=4), result(), run, result()]), {})
        self.assertEqual(self.stop([prompt('docs'), self.large_edit('docs/guide.md', 50), result()]), {})
        outside = tool('Write', file_path=str(Path(tempfile.gettempdir()) / 'scratch.py'), content='x\n' * 50)
        self.assertEqual(self.stop([prompt('scratch'), outside, result(), run, result()]), {})

    def verifier_report(self, report):
        launch = tool('Agent', subagent_type='general-purpose', description='verify',
                      prompt='INDEPENDENT VERIFIER. A colleague implemented the request below.')
        launch['message']['content'][1]['id'] = 'v'
        reply = {'type': 'user', 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'v', 'content': [
            {'type': 'text', 'text': 'Import skips the check.\n' + json.dumps(report)}]}]}}
        return [launch, reply]

    def test_reported_violations_need_a_probe_registered_after_the_report(self):
        run = tool('Bash', command='python -m unittest')
        incomplete = {'verdict': 'incomplete', 'violations': [{'path': 'import', 'test': 't.py:3', 'observed': 'saved'}] * 2,
                      'questions': []}
        before = [prompt('fix'), self.large_edit(), result(), run, result()]
        decision = self.stop([*before, *self.verifier_report(incomplete), self.code_edit(), result(), run, result()])
        self.assertEqual(decision['decision'], 'block')
        self.assertIn('reported 2 violation(s) and .harness/probes.json was not updated', decision['reason'])
        self.assertNotIn('independent verifier.', decision['reason'])
        registry = tool('Write', file_path=str(self.root / '.harness/probes.json'), content='{}')
        probes = tool('Bash', command='python probe_check.py probes --root .')
        self.assertEqual(self.stop([*before, *self.verifier_report(incomplete), self.code_edit(), result(),
                                    registry, result(), probes, result()]), {})
        self.assertIn('violation(s)', self.stop([*before, registry, result(), *self.verifier_report(incomplete),
                                                  run, result()])['reason'])
        for report in ({'verdict': 'complete', 'violations': [], 'questions': ['import?']}, 'no json'):
            with self.subTest(report=report):
                self.assertEqual(self.stop([*before, *self.verifier_report(report)]), {})

    def test_blocks_only_once_and_honors_opt_out_and_unreadable_input(self):
        entries = [prompt('fix'), self.code_edit(), result()]
        self.assertEqual(self.stop(entries, stop_hook_active=True), {})
        self.assertEqual(self.stop(entries, transcript_path=str(self.root / 'missing.jsonl')), {})
        process = subprocess.run([sys.executable, str(GUARD)], input='not json',
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertEqual((process.returncode, json.loads(process.stdout)), (0, {}))


if __name__ == '__main__':
    unittest.main()
