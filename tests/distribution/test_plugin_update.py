"""Update guard exercises real files and a destructive native-command stand-in."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts/update_plugin.py'


def package(path, version):
    path.mkdir(parents=True)
    (path / 'plugin.json').write_text(json.dumps({'name': 'agentic-coding', 'version': version}))
    (path / 'tool.py').write_text('print(42)\n')
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in path.iterdir()}
    (path / 'package-files.json').write_text(json.dumps({'files': files}))


class PluginUpdateTests(unittest.TestCase):
    def test_refuses_overlapping_backup_and_directory_alias(self):
        api = runpy.run_path(str(SCRIPT))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home, marketplace = root / 'home', root / 'marketplace'
            home.mkdir()
            marketplace.mkdir()
            with self.assertRaisesRegex(ValueError, 'separate trees'):
                api['update'](home, marketplace, home / 'backup')
            outside = root / 'outside'
            outside.mkdir()
            (outside / 'auth.json').write_text('test sentinel, not credentials')
            alias = marketplace / 'linked'
            if os.name == 'nt':
                def quoted(path):
                    return "'" + str(path).replace("'", "''") + "'"
                subprocess.run(['powershell', '-NoProfile', '-Command',
                                'New-Item -ItemType Junction -Path ' + quoted(alias) +
                                ' -Target ' + quoted(outside) + ' | Out-Null'], check=True)
            else:
                alias.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'Aliased|escapes'):
                api['files'](marketplace)
            self.assertEqual((outside / 'auth.json').read_text(), 'test sentinel, not credentials')

    def test_guard_preserves_changes_and_recovers_after_destructive_failure(self):
        self.assertTrue(SCRIPT.exists(), 'Missing user-change-preserving plugin update command')
        api = runpy.run_path(str(SCRIPT))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'home'
            cache = home / 'plugins/cache/local/agentic-coding'
            old = cache / '1.0'
            package(old, '1.0')
            marketplace = root / 'marketplace'
            candidate = marketplace / 'plugins/agentic-coding'
            package(candidate, '2.0')
            descriptor = marketplace / '.agents/plugins/marketplace.json'
            descriptor.parent.mkdir(parents=True)
            descriptor.write_text(json.dumps({'name': 'local', 'plugins': [
                {'name': 'agentic-coding', 'source': {'source': 'local', 'path': './plugins/agentic-coding'}}]}))
            calls = []

            def native(argv, **kwargs):
                calls.append(argv)
                self.assertEqual(kwargs['env']['CODEX_HOME'], str(home))
                shutil.rmtree(cache)
                raise subprocess.CalledProcessError(17, argv)

            note = old / 'user-note.txt'
            note.write_text('keep my changes')
            with self.assertRaisesRegex(ValueError, 'user-note'):
                api['update'](home, marketplace, root / 'blocked', native)
            self.assertEqual(note.read_text(), 'keep my changes')
            self.assertEqual(calls, [])
            note.unlink()
            (old / 'tool.py').write_text('customized')
            with self.assertRaisesRegex(ValueError, 'tool.py'):
                api['update'](home, marketplace, root / 'changed', native)
            self.assertEqual(calls, [])
            (old / 'tool.py').write_text('print(42)\n')
            bytecode = old / '__pycache__/tool.cpython-313.pyc'
            bytecode.parent.mkdir()
            bytecode.write_bytes(b'cache also preserved')
            expected = {p.relative_to(cache).as_posix(): p.read_bytes() for p in cache.rglob('*') if p.is_file()}
            backup = root / 'backup'
            with self.assertRaises(subprocess.CalledProcessError):
                api['update'](home, marketplace, backup, native)
            self.assertFalse(cache.exists())
            with self.assertRaisesRegex(ValueError, 'separate from installation home'):
                api['recover'](backup, cache)
            self.assertFalse(cache.exists(), 'export recovery must not recreate the active cache')
            recovered = root / 'recovered'
            api['recover'](backup, recovered)
            self.assertEqual(expected, {p.relative_to(recovered).as_posix(): p.read_bytes()
                                       for p in recovered.rglob('*') if p.is_file()})
            with self.assertRaises(FileExistsError):
                api['recover'](backup, recovered)
            self.assertEqual(len(calls), 1)
            self.assertFalse((backup / 'auth.json').exists())

    def test_normal_update_noop_and_corrupt_backup(self):
        self.assertTrue(SCRIPT.exists(), 'Missing update command')
        api = runpy.run_path(str(SCRIPT))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'home'
            cache = home / 'plugins/cache/local/agentic-coding'
            package(cache / '1.0', '1.0')
            marketplace = root / 'marketplace'
            candidate = marketplace / 'plugins/agentic-coding'
            package(candidate, '2.0')
            descriptor = marketplace / '.agents/plugins/marketplace.json'
            descriptor.parent.mkdir(parents=True)
            descriptor.write_text(json.dumps({'name': 'local', 'plugins': [
                {'name': 'agentic-coding', 'source': {'source': 'local', 'path': './plugins/agentic-coding'}}]}))
            calls = []
            wrong_receipt = False

            def native(argv, **kwargs):
                calls.append(argv)
                with self.assertRaises(OSError):
                    api['update'](home, marketplace, root / 'concurrent', native)
                shutil.rmtree(cache)
                shutil.copytree(candidate, cache / '2.0')
                receipt = {'pluginId': 'agentic-coding@local', 'version': '2.0',
                           'installedPath': str(cache / '2.0')}
                if wrong_receipt:
                    receipt['pluginId'] = 'unrelated@local'
                return subprocess.CompletedProcess(argv, 0, json.dumps(receipt).encode(), b'')

            self.assertEqual(api['update'](home, marketplace, root / 'backup', native)['status'], 'UPDATED')
            self.assertEqual(api['update'](home, marketplace, root / 'unused', native)['status'], 'UNCHANGED')
            self.assertEqual(len(calls), 1)
            self.assertFalse((root / 'unused').exists())
            self.assertFalse((root / 'concurrent').exists())
            (root / 'backup/previous/1.0/tool.py').write_text('broken')
            with self.assertRaisesRegex(ValueError, 'snapshot'):
                api['recover'](root / 'backup', root / 'recovery')
            self.assertFalse((root / 'recovery').exists())
            wrong_receipt = True
            # Recreate the exact old test fixture to exercise a second update.
            shutil.rmtree(cache)
            package(cache / '1.0', '1.0')
            with self.assertRaisesRegex(ValueError, 'Native installation identity'):
                api['update'](home, marketplace, root / 'wrong-receipt', native)
            self.assertFalse((root / 'wrong-receipt/completed.json').exists())


if __name__ == '__main__':
    unittest.main()
