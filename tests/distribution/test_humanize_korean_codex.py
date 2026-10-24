"""The Codex humanize-korean launcher keeps a runnable upstream copy and fails safely."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'plugins/humanize-korean-codex/skills/humanize-korean/scripts/sync_upstream.py'
# Git without symlink support (the Windows default) checks a link out as a text file.
NO_SYMLINKS = {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.symlinks', 'GIT_CONFIG_VALUE_0': 'false'}
LAUNCHER = ('from pathlib import Path\nimport runpy\n'
            'runpy.run_path(str(Path(__file__).resolve().parents[4] / "scripts" / Path(__file__).name), run_name="__main__")\n')


def git(*args, cwd):
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', *args], cwd=cwd, check=True,
                   capture_output=True, input=None)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


class HumanizeKoreanCodexTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.upstream = self.root / 'upstream'
        self.publish('v1', initial=True)

    def publish(self, marker, initial=False):
        """Commit an upstream with the real layout: root scripts, launcher, symlinked references."""
        up = self.upstream
        if initial:
            up.mkdir()
            git('init', '-q', cwd=up)
        write(up / 'scripts/tool.py', f'print("root tool {marker}")\n')
        write(up / 'skills/humanize-korean/references/quick-rules.md', marker)
        write(up / 'codex/skills/humanize-korean/SKILL.md', f'---\nname: humanize-korean\n---\n{marker}\n')
        write(up / 'codex/skills/humanize-korean/scripts/tool.py', LAUNCHER)
        # Explicit paths: the symlink entry lives only in the index, so `add -A` would stage its deletion.
        git('add', 'scripts', 'skills', 'codex/skills/humanize-korean/SKILL.md', 'codex/skills/humanize-korean/scripts', cwd=up)
        if initial:
            blob = subprocess.run(['git', 'hash-object', '-w', '--stdin'], cwd=up, check=True, capture_output=True,
                                  input=b'../../../skills/humanize-korean/references').stdout.decode().strip()
            git('update-index', '--add', '--cacheinfo', f'120000,{blob},codex/skills/humanize-korean/references', cwd=up)
        git('commit', '-q', '-m', marker, cwd=up)

    def sync(self, *extra, source=None):
        run = subprocess.run([sys.executable, '-I', str(SCRIPT), '--home', str(self.home),
                              '--source', str(source or self.upstream), *extra],
                             capture_output=True, text=True, encoding='utf-8', env={**os.environ, **NO_SYMLINKS})
        return run.returncode, json.loads(run.stdout)

    def assert_runs(self, report, marker):
        skill = Path(report['skill_root'])
        self.assertEqual((skill / 'references/quick-rules.md').read_text(encoding='utf-8'), marker)
        self.assertIn(marker, (skill / 'SKILL.md').read_text(encoding='utf-8'))
        tool = subprocess.run([sys.executable, '-I', str(skill / 'scripts/tool.py')], capture_output=True, text=True)
        self.assertEqual(tool.stdout.strip(), f'root tool {marker}', tool.stderr)

    def test_first_run_installs_a_runnable_copy(self):
        code, report = self.sync()
        self.assertEqual((code, report['status']), (0, 'installed'), report)
        self.assert_runs(report, 'v1')
        self.assertEqual(sorted(p.name for p in (self.home / 'vendor/im-not-ai').iterdir()), ['repo', 'runtime'])

    def test_recent_copy_is_used_without_network(self):
        self.sync()
        self.upstream.rename(self.root / 'gone')
        code, report = self.sync()
        self.assertEqual((code, report['status']), (0, 'current'), report)
        self.assert_runs(report, 'v1')

    def test_refresh_takes_new_upstream_and_keeps_it_offline(self):
        self.sync()
        self.publish('v2')
        code, report = self.sync('--refresh')
        self.assertEqual((code, report['status']), (0, 'updated'), report)
        self.assert_runs(report, 'v2')
        self.upstream.rename(self.root / 'gone')
        code, report = self.sync('--refresh')
        self.assertEqual((code, report['status']), (0, 'stale'), report)
        self.assertIn('network access is required', report['message'])
        self.assert_runs(report, 'v2')

    def test_expired_copy_fetches_without_refresh_flag(self):
        self.sync()
        self.publish('v2')
        code, report = self.sync('--max-age-hours', '0')
        self.assertEqual((code, report['status']), (0, 'updated'), report)
        self.assert_runs(report, 'v2')

    def test_no_copy_and_no_network_fails_without_leftovers(self):
        code, report = self.sync(source=self.root / 'missing')
        self.assertEqual((code, report['status'], report['skill_root']), (2, 'unavailable', None), report)
        self.assertIn('network access is required', report['message'])
        self.assertEqual(list((self.home / 'vendor/im-not-ai').iterdir()), [])

    def test_incomplete_upstream_keeps_the_previous_copy(self):
        self.sync()
        git('rm', '-r', '-q', '--cached', 'codex', cwd=self.upstream)
        git('commit', '-q', '-m', 'drop codex', cwd=self.upstream)
        code, report = self.sync('--refresh')
        self.assertEqual((code, report['status']), (0, 'stale'), report)
        self.assertIn('no longer has a complete', report['message'])
        self.assert_runs(report, 'v1')

    def test_foreign_directory_is_left_untouched(self):
        foreign = self.home / 'vendor/im-not-ai/repo/keep.txt'
        write(foreign, 'mine')
        code, report = self.sync()
        self.assertEqual((code, report['status']), (2, 'unavailable'), report)
        self.assertEqual(foreign.read_text(encoding='utf-8'), 'mine')
        self.assertEqual(sorted(p.name for p in foreign.parent.iterdir()), ['keep.txt'])


if __name__ == '__main__':
    unittest.main()
