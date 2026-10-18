import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
SPEC = importlib.util.spec_from_file_location('install_global_guidance', SCRIPTS / 'install_global_guidance.py')
GUIDANCE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUIDANCE
SPEC.loader.exec_module(GUIDANCE)


class InstallGlobalGuidanceTests(unittest.TestCase):
    def test_preview_does_not_create_or_change_host_files(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'new-codex-home'
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(GUIDANCE.main(['--host', 'codex', '--home', str(home)]), 0)
            record = json.loads(output.getvalue())
            self.assertEqual(record['status'], 'PREVIEW')
            self.assertTrue(record['changed'])
            self.assertIn('--- /dev/null\n', record['diff'])
            self.assertIn('+++ ' + str(home / 'AGENTS.md') + '\n', record['diff'])
            self.assertIn('+' + GUIDANCE.START.decode('ascii'), record['diff'])
            self.assertFalse(home.exists())

    def test_apply_preserves_user_text_backups_original_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            original = b'# My instructions\r\nKeep this line.\r\n'
            target.write_bytes(original)
            os_mode = stat.S_IMODE(target.stat().st_mode)
            plan = GUIDANCE.prepare('codex', home=home)
            result = GUIDANCE.apply(plan)
            installed = target.read_bytes()
            self.assertEqual(result['status'], 'UPDATED')
            self.assertIn(original, installed)
            self.assertEqual(installed.count(GUIDANCE.START), 1)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), os_mode)
            backup = Path(result['backup'])
            self.assertEqual(backup.read_bytes(), original)
            metadata = json.loads((backup.parent / 'metadata.json').read_text(encoding='utf-8'))
            self.assertEqual(metadata['sha256'], hashlib.sha256(original).hexdigest())
            self.assertEqual(stat.S_IMODE(backup.stat().st_mode), os_mode)
            self.assertEqual(backup.stat().st_mtime_ns, metadata['mtime_ns'])

            again = GUIDANCE.apply(GUIDANCE.prepare('codex', home=home))
            self.assertEqual(again['status'], 'CURRENT')
            self.assertEqual(len(list((home / 'back-up/global-guidance').iterdir())), 1)

    def test_exact_canonical_file_is_wrapped_once_without_duplicate_text(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'claude'
            home.mkdir()
            target = home / 'CLAUDE.md'
            source = (SCRIPTS.parent / 'authoring/global/AGENTS.md').read_bytes()
            target.write_bytes(source)
            plan = GUIDANCE.prepare('claude', home=home)
            self.assertEqual(plan.after.count(source), 1)
            self.assertEqual(plan.after.count(GUIDANCE.START), 1)

    def test_utf8_bom_is_preserved_and_backed_up_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            original = b'\xef\xbb\xbf# User text\r\n'
            target.write_bytes(original)
            result = GUIDANCE.apply(GUIDANCE.prepare('codex', home=home))
            self.assertTrue(target.read_bytes().startswith(b'\xef\xbb\xbf'))
            self.assertEqual(Path(result['backup']).read_bytes(), original)

    def test_preview_diff_marks_missing_final_newline(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            target.write_bytes(b'legacy')
            diff = GUIDANCE.preview_diff(GUIDANCE.prepare('codex', home=home))
            self.assertIn('\\ No newline at end of file\n', diff)

    def test_invalid_utf8_source_or_target_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            source = home / 'source.md'
            source.write_bytes(b'\xff')
            with self.assertRaisesRegex(GUIDANCE.UnsafeTarget, 'source_is_not_utf8'):
                GUIDANCE.prepare('codex', source_path=source, home=home)
            source.write_bytes(b'# Valid UTF-8\n')
            target = home / 'AGENTS.md'
            target.write_bytes(b'\xff')
            with self.assertRaisesRegex(GUIDANCE.UnsafeTarget, 'target_is_not_utf8'):
                GUIDANCE.prepare('codex', source_path=source, home=home)

    def test_claude_uses_config_dir_and_replaces_only_managed_block(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'claude-config'
            target = home / 'CLAUDE.md'
            target.parent.mkdir()
            source = b'# New guidance\n'
            prefix, suffix = b'# User text\r\n', b'# Tail\r\n'
            target.write_bytes(prefix + GUIDANCE.START + b'\r\n# Old guidance\r\n'
                               + GUIDANCE.END + b'\r\n' + suffix)
            plan = GUIDANCE.prepare('claude', source_path=self.write_source(home, source),
                                    env={'CLAUDE_CONFIG_DIR': str(home)})
            GUIDANCE.apply(plan)
            updated = target.read_bytes()
            self.assertTrue(updated.startswith(prefix))
            self.assertIn(b'# New guidance\n', updated)
            self.assertTrue(updated.endswith(suffix))
            self.assertEqual(updated.count(GUIDANCE.START), 1)
            self.assertEqual(GUIDANCE.apply(GUIDANCE.prepare('claude', source_path=home / 'source.md',
                                                             home=home))['status'], 'CURRENT')

    @unittest.skipUnless(os.name == 'nt', 'Windows DACL preservation applies only on Windows')
    def test_windows_target_dacl_can_be_copied_to_backup_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / 'source.md', root / 'backup.md'
            source.write_bytes(b'original')
            destination.write_bytes(b'copy')
            GUIDANCE._copy_windows_dacl(source, destination)

    def test_codex_override_and_ambiguous_markers_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            (home / 'AGENTS.override.md').write_text('overrides global', encoding='utf-8')
            with self.assertRaisesRegex(GUIDANCE.UnsafeTarget, 'shadows'):
                GUIDANCE.prepare('codex', home=home)
            (home / 'AGENTS.override.md').unlink()
            target = home / 'AGENTS.md'
            target.write_bytes(GUIDANCE.START + b'\nfirst\n' + GUIDANCE.START + b'\nsecond\n' + GUIDANCE.END)
            with self.assertRaisesRegex(GUIDANCE.UnsafeTarget, 'ambiguous'):
                GUIDANCE.prepare('codex', home=home)

    def test_symlink_target_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            target.write_text('user instructions', encoding='utf-8')
            is_symlink = Path.is_symlink
            with mock.patch.object(Path, 'is_symlink', autospec=True,
                                   side_effect=lambda path: path == target or is_symlink(path)):
                with self.assertRaisesRegex(GUIDANCE.UnsafeTarget, 'symlink'):
                    GUIDANCE.prepare('codex', home=home)

    def test_changed_target_after_preview_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            target.write_bytes(b'user original\n')
            plan = GUIDANCE.prepare('codex', home=home)
            target.write_bytes(b'user concurrent edit\n')
            with self.assertRaisesRegex(GUIDANCE.ConcurrentChange, 'since_preview'):
                GUIDANCE.apply(plan)
            self.assertEqual(target.read_bytes(), b'user concurrent edit\n')

    def test_new_codex_override_after_preview_blocks_write(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            target.write_bytes(b'user instructions\n')
            plan = GUIDANCE.prepare('codex', home=home)
            (home / 'AGENTS.override.md').write_bytes(b'override')
            with self.assertRaisesRegex(GUIDANCE.UnsafeTarget, 'shadows'):
                GUIDANCE.apply(plan)
            self.assertEqual(target.read_bytes(), b'user instructions\n')

    def test_changed_target_during_backup_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / 'codex'
            home.mkdir()
            target = home / 'AGENTS.md'
            target.write_bytes(b'user original\n')
            plan = GUIDANCE.prepare('codex', home=home)
            backup_impl = GUIDANCE._backup

            def backup_then_edit(current):
                backup = backup_impl(current)
                target.write_bytes(b'user concurrent edit\n')
                return backup

            with mock.patch.object(GUIDANCE, '_backup', side_effect=backup_then_edit):
                with self.assertRaisesRegex(GUIDANCE.ConcurrentChange, 'before_write'):
                    GUIDANCE.apply(plan)
            self.assertEqual(target.read_bytes(), b'user concurrent edit\n')

    @staticmethod
    def write_source(home, source):
        path = home / 'source.md'
        path.write_bytes(source)
        return path


if __name__ == '__main__':
    unittest.main()
