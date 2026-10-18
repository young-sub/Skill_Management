"""Preview or install this checkout's managed global guidance for Codex or Claude Code."""
import argparse
import ctypes
from dataclasses import dataclass
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import uuid
from ctypes import wintypes


START = b'<!-- BEGIN SKILL_MANAGEMENT_GLOBAL_GUIDANCE -->'
END = b'<!-- END SKILL_MANAGEMENT_GLOBAL_GUIDANCE -->'


class UnsafeTarget(ValueError):
    pass


class ConcurrentChange(RuntimeError):
    pass


@dataclass(frozen=True)
class Plan:
    host: str
    target: Path
    before: bytes | None
    identity: tuple | None
    metadata: tuple | None
    after: bytes
    backup_root: Path


def _check_shadow(host, root):
    override = root / 'AGENTS.override.md'
    if host == 'codex' and (override.exists() or override.is_symlink()):
        raise UnsafeTarget('codex_AGENTS.override.md_shadows_global_AGENTS.md')


def host_paths(host, home=None, env=None):
    env = os.environ if env is None else env
    if home is not None:
        root = Path(home)
    elif host == 'codex':
        root = Path(env.get('CODEX_HOME') or (Path.home() / '.codex'))
    elif host == 'claude':
        root = Path(env.get('CLAUDE_CONFIG_DIR') or (Path.home() / '.claude'))
    else:
        raise ValueError('host_must_be_codex_or_claude')
    root = root.expanduser().resolve()
    _check_shadow(host, root)
    return root / ('AGENTS.md' if host == 'codex' else 'CLAUDE.md'), root


def _identity(path):
    if path.is_symlink():
        raise UnsafeTarget('target_is_symlink')
    if not path.exists():
        return None
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise UnsafeTarget('target_is_not_a_regular_file')
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, stat.S_IMODE(info.st_mode)


def _managed_block(source):
    source = source if source.endswith(b'\n') else source + b'\n'
    return START + b'\n' + source + END + b'\n'


def _utf8(raw, label):
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError as error:
        raise UnsafeTarget(label + '_is_not_utf8') from error


def render(existing, source):
    if existing == source:
        return _managed_block(source)
    starts = [i for i in range(len(existing)) if existing.startswith(START, i)]
    ends = [i for i in range(len(existing)) if existing.startswith(END, i)]
    if not starts and not ends:
        prefix = existing
        if prefix and not prefix.endswith(b'\n'):
            prefix += b'\n'
        return prefix + _managed_block(source)
    if len(starts) != 1 or len(ends) != 1 or starts[0] > ends[0]:
        raise UnsafeTarget('managed_guidance_markers_are_ambiguous_or_incomplete')
    start, end = starts[0], ends[0] + len(END)
    block = _managed_block(source).removesuffix(b'\n')
    updated = existing[:start] + block + existing[end:]
    return updated


def prepare(host, source_path=None, home=None, env=None):
    source_path = (Path(source_path) if source_path else
                   Path(__file__).resolve().parents[1] / 'authoring' / 'global' / 'AGENTS.md')
    source = source_path.read_bytes()
    _utf8(source, 'source')
    target, root = host_paths(host, home, env)
    identity = _identity(target)
    info = target.stat() if identity is not None else None
    before = target.read_bytes() if identity is not None else None
    if before is not None:
        _utf8(before, 'target')
    after = render(before or b'', source)
    backup_root = root / 'back-up' / 'global-guidance'
    metadata = ((stat.S_IMODE(info.st_mode), info.st_atime_ns, info.st_mtime_ns)
                if info is not None else None)
    return Plan(host, target, before, identity, metadata, after, backup_root)


def preview_diff(plan):
    before = _utf8(plan.before or b'', 'target').splitlines(keepends=True)
    after = _utf8(plan.after, 'result').splitlines(keepends=True)
    old_name = str(plan.target) if plan.before is not None else '/dev/null'
    output = []
    for line in difflib.unified_diff(before, after, fromfile=old_name,
                                     tofile=str(plan.target)):
        output.append(line)
        if (not line.endswith(('\n', '\r')) and line[:1] in ('+', '-', ' ')):
            output.append('\n\\ No newline at end of file\n')
    return ''.join(output)


def _current_identity(path):
    return _identity(path)


def _copy_windows_dacl(source, destination):
    if os.name != 'nt':
        return
    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    pointer = ctypes.POINTER(ctypes.c_void_p)
    get_security = advapi.GetNamedSecurityInfoW
    get_security.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
                             pointer, pointer, pointer, pointer, pointer]
    get_security.restype = wintypes.DWORD
    set_security = advapi.SetNamedSecurityInfoW
    set_security.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
                             ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    set_security.restype = wintypes.DWORD
    local_free = kernel.LocalFree
    local_free.argtypes = [ctypes.c_void_p]
    local_free.restype = ctypes.c_void_p
    dacl, descriptor = ctypes.c_void_p(), ctypes.c_void_p()
    result = get_security(str(source), 1, 0x4, None, None, ctypes.byref(dacl), None,
                          ctypes.byref(descriptor))
    if result:
        raise OSError(result, 'could_not_read_global_guidance_dacl', str(source))
    try:
        result = set_security(str(destination), 1, 0x4, None, None, dacl, None)
        if result:
            raise OSError(result, 'could_not_preserve_global_guidance_dacl', str(destination))
    finally:
        if descriptor:
            local_free(descriptor)


def _backup(plan):
    if plan.before is None:
        return None
    plan.backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    folder = plan.backup_root / (stamp + '-' + uuid.uuid4().hex[:8])
    folder.mkdir()
    backup = folder / plan.target.name
    with backup.open('xb') as stream:
        stream.write(plan.before)
        stream.flush()
        os.fsync(stream.fileno())
    mode, atime_ns, mtime_ns = plan.metadata
    os.chmod(backup, mode)
    _copy_windows_dacl(plan.target, backup)
    os.utime(backup, ns=(atime_ns, mtime_ns))
    metadata = {
        'source': str(plan.target),
        'bytes': len(plan.before),
        'sha256': hashlib.sha256(plan.before).hexdigest(),
        'mode': mode,
        'atime_ns': atime_ns,
        'mtime_ns': mtime_ns,
    }
    (folder / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    saved = backup.stat()
    if (backup.read_bytes() != plan.before or stat.S_IMODE(saved.st_mode) != metadata['mode']
            or saved.st_mtime_ns != metadata['mtime_ns']):
        raise OSError('global_guidance_backup_verification_failed')
    return backup


def apply(plan):
    if plan.before == plan.after:
        return {'status': 'CURRENT', 'target': str(plan.target), 'backup': None}
    _check_shadow(plan.host, plan.target.parent)
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    if _current_identity(plan.target) != plan.identity:
        raise ConcurrentChange('global_guidance_changed_since_preview')
    backup = _backup(plan)
    if (_current_identity(plan.target) != plan.identity
            or (plan.before is not None and plan.target.read_bytes() != plan.before)):
        raise ConcurrentChange('global_guidance_changed_before_write')
    fd, temp_name = tempfile.mkstemp(prefix='.global-guidance-', dir=plan.target.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(plan.after)
            stream.flush()
            os.fsync(stream.fileno())
        if plan.metadata is not None:
            os.chmod(temp, plan.metadata[0])
            _copy_windows_dacl(plan.target, temp)
        _check_shadow(plan.host, plan.target.parent)
        if (_current_identity(plan.target) != plan.identity
                or (plan.before is not None and plan.target.read_bytes() != plan.before)):
            raise ConcurrentChange('global_guidance_changed_immediately_before_write')
        os.replace(temp, plan.target)
    finally:
        temp.unlink(missing_ok=True)
    if plan.target.read_bytes() != plan.after:
        raise OSError('global_guidance_write_verification_failed')
    return {'status': 'UPDATED', 'target': str(plan.target),
            'backup': str(backup) if backup else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('codex', 'claude'), required=True)
    parser.add_argument('--home', type=Path, help='Use this host configuration directory instead of the environment/default.')
    parser.add_argument('--apply', action='store_true', help='Write after previewing; default only prints the plan.')
    args = parser.parse_args(argv)
    try:
        plan = prepare(args.host, home=args.home)
        diff = preview_diff(plan)
        if not args.apply:
            print(json.dumps({'status': 'PREVIEW', 'host': plan.host, 'target': str(plan.target),
                              'changed': plan.before != plan.after,
                              'backup_root': str(plan.backup_root), 'diff': diff}, sort_keys=True))
            return 0
        result = apply(plan)
        result['diff'] = diff
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, UnsafeTarget, ConcurrentChange, ValueError) as error:
        print(json.dumps({'status': 'BLOCKED', 'error': str(error)}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
