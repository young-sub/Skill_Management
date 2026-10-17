"""State ownership and OS lock recovery; no thread-only CAS simulation."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2] / 'authoring/scripts'
sys.path.insert(0, str(SOURCE))
from task_store import TaskStore


class TaskStoreTests(unittest.TestCase):
    def test_lock_directory_alias_is_rejected_without_external_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'project/.work/tasks/current/state.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"results": ["successful-effect"]}')
            external = root / 'outside'
            external.mkdir()
            alias = root / 'project/.work/locks'
            if os.name == 'nt':
                import _winapi
                _winapi.CreateJunction(str(external), str(alias))
            else:
                alias.symlink_to(external, target_is_directory=True)
            store = TaskStore(path)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'task_state_lock_alias'):
                store.commit(store.load())
            self.assertEqual(list(external.iterdir()), [])
            self.assertEqual(path.read_bytes(), before)

    @unittest.skipUnless(os.name == 'nt', 'Windows paths are case insensitive')
    def test_windows_case_alias_uses_the_same_writer_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / '.work/tasks/current/state.json'
            self.assertEqual(TaskStore(path).lock_path, TaskStore(Path(str(path).upper())).lock_path)

    def test_existing_bytes_require_the_original_snapshot_and_matching_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'state.json'
            legacy = b'{ "schema_version": 1, "reviews": {} }\n'
            path.write_bytes(legacy)
            store = TaskStore(path)
            first, stale = store.load(), store.load()
            self.assertEqual(path.read_bytes(), legacy, 'Loading legacy data must not migrate it')
            first['reviews']['api'] = 'reviewed'
            store.commit(first)
            saved = path.read_bytes()
            for attempt, error in ((lambda: store.create(dict(stale)), 'revision_conflict'),
                                   (lambda: store.commit(dict(stale)), 'snapshot_required'),
                                   (lambda: store.commit(stale), 'revision_conflict'),
                                   (lambda: TaskStore(path.with_name('other.json')).commit(first), 'snapshot_required')):
                with self.assertRaisesRegex(ValueError, error):
                    attempt()
                self.assertEqual(path.read_bytes(), saved)
            updated = copy.deepcopy(store.load())
            updated['reviews']['cli'] = 'reviewed'
            store.commit(updated)
            self.assertEqual(set(json.loads(path.read_bytes())['reviews']), {'api', 'cli'})
            self.assertNotIn('revision', json.loads(path.read_bytes()))

    def test_competing_process_writer_is_rejected_and_exit_releases_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'state.json'
            store = TaskStore(path)
            store.create({'results': ['successful-effect']})
            state = store.load()
            child = subprocess.Popen([sys.executable, '-u', '-c',
                "import sys,time; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
                "from task_store import writer_lock; "
                "lock=writer_lock(Path(sys.argv[2])); lock.__enter__(); print('locked',flush=True); time.sleep(30)",
                str(SOURCE), str(path.with_name('state.json.lock'))], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), 'locked')
                with self.assertRaisesRegex(ValueError, 'task_state_writer_busy'):
                    store.commit(state)
            finally:
                child.kill()
                child.communicate(timeout=10)
            state['reviews'] = {'api': 'reviewed'}
            store.commit(state)
            self.assertEqual(store.load()['results'], ['successful-effect'])
