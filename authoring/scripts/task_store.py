"""Single writer for task JSON. Revisions are byte hashes, never persisted fields."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterator


class TaskState(dict[str, Any]):
    """A JSON object bound to the exact file revision that was read."""

    def __init__(self, data: dict[str, Any], path: Path, revision: str | None):
        super().__init__(data)
        self.path = path.resolve()
        self.revision = revision


@contextmanager
def writer_lock(path: Path) -> Iterator[None]:
    # Keep the inode: unlinking a lock lets another writer lock a different file.
    if any(part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction())
           for part in (path, *path.parents)):
        raise ValueError('task_state_lock_alias')
    with path.open('a+b') as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b'\0')
            lock.flush()
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError('task_state_writer_busy') from error
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_UN)


class TaskStore:
    def __init__(self, path: Path):
        self.path = path.resolve()
        work = next((parent for parent in self.path.parents if os.path.normcase(parent.name) == '.work'), None)
        self.lock_path = (work / 'locks' / ('task-state-' + hashlib.sha256(os.path.normcase(str(self.path)).encode()).hexdigest() + '.lock')
                          if work else self.path.with_name(self.path.name + '.lock'))

    def load(self, default: dict[str, Any] | None = None) -> TaskState:
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            if default is None:
                raise
            return TaskState(default, self.path, None)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('workflow_state_must_be_object')
        return TaskState(data, self.path, hashlib.sha256(raw).hexdigest())

    def commit(self, state: TaskState, *, staging: Path | None = None) -> None:
        if not isinstance(state, TaskState) or state.path != self.path:
            raise ValueError('task_state_snapshot_required')
        if any(part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction())
               for part in (self.lock_path, *self.lock_path.parents)):
            raise ValueError('task_state_lock_alias')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with writer_lock(self.lock_path):
            current = hashlib.sha256(self.path.read_bytes()).hexdigest() if self.path.exists() else None
            if current != state.revision:
                raise ValueError('task_state_revision_conflict')
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=staging or self.path.parent,
                        prefix=self.path.name + '.', suffix='.pending', delete=False) as output:
                    temporary = Path(output.name)
                    json.dump(state, output, indent=2)
                    output.flush()
                    os.fsync(output.fileno())
                revision = hashlib.sha256(temporary.read_bytes()).hexdigest()
                temporary.replace(self.path)
                state.revision = revision
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)

    def create(self, state: dict[str, Any], *, staging: Path | None = None) -> None:
        self.commit(TaskState(state, self.path, None), staging=staging)
