"""Host-owned process lifetime around a trusted native sandbox launcher.

Install this file outside candidate writes. The sandbox starts its gated child;
the host assigns that child to an unnamed job BEFORE permitting candidate code.
The job handle stays exclusively in the host. This is process lifetime control,
not a replacement for the native sandbox or protected verification policy.
"""
import ctypes
from ctypes import wintypes as w
import math
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time


class Limits(ctypes.Structure):
    _fields_ = [('times', ctypes.c_longlong * 2), ('flags', w.DWORD),
                ('minimum', ctypes.c_size_t), ('maximum', ctypes.c_size_t),
                ('active', w.DWORD), ('affinity', ctypes.c_size_t),
                ('priority', w.DWORD), ('scheduling', w.DWORD)]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', Limits), ('io', ctypes.c_ulonglong * 6),
                ('memory', ctypes.c_size_t * 4)]


class Accounting(ctypes.Structure):
    _fields_ = [('times', ctypes.c_longlong * 4), ('faults', w.DWORD),
                ('total', w.DWORD), ('active', w.DWORD), ('terminated', w.DWORD)]


def _api():
    if os.name != 'nt':
        raise OSError('Windows job support required')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
        'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
        'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
        'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
        'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
        'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
        'CloseHandle': ([w.HANDLE], w.BOOL),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = arguments, result
    return api


def _ok(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def run(launcher, command, *, cwd, timeout, env=None):
    """Return observed lifecycle, not a verification verdict.

    launcher is the host-selected sandbox argv ending in '--', or [] for tests.
    The host must pin this module/interpreter/launcher before invoking it.
    """
    if not command or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('command_and_positive_timeout_required')
    api = _api()
    job = _ok(api.CreateJobObjectW(None, None))
    process = None
    deadline = time.monotonic() + timeout
    def count():
        info = Accounting()
        _ok(api.QueryInformationJobObject(job, 1, ctypes.byref(info), ctypes.sizeof(info), None))
        return info.active
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        _ok(api.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        argv = [*launcher, sys.executable, '-I', str(Path(__file__).resolve()), '--child', *command]
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        handshake = queue.Queue()
        threading.Thread(target=lambda: handshake.put(process.stdout.readline()), daemon=True).start()
        header = handshake.get(timeout=max(.01, deadline - time.monotonic()))
        if not header.startswith(b'HOST_JOB_PID='):
            raise ValueError('missing_trusted_child_handshake')
        pid = int(header.removeprefix(b'HOST_JOB_PID=').strip())
        handle = _ok(api.OpenProcess(0x101, False, pid))  # SET_QUOTA | TERMINATE
        try:
            _ok(api.AssignProcessToJobObject(job, handle))
        finally:
            api.CloseHandle(handle)
        timed_out = False
        try:
            stdout, stderr = process.communicate(b'GO\n', timeout=max(.01, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
            _ok(api.TerminateJobObject(job, 124))
            stdout, stderr = process.communicate(timeout=5)
        remaining = count()
        descendants_killed = bool(remaining) and not timed_out
        if remaining:
            _ok(api.TerminateJobObject(job, 124))
        until = time.monotonic() + 5
        while count() and time.monotonic() < until:
            time.sleep(.01)
        remaining = count()
        if remaining:
            raise RuntimeError('job_cleanup_incomplete')
        return {'exit': process.returncode, 'stdout': stdout.decode('utf-8', 'replace'),
                'stderr': stderr.decode('utf-8', 'replace'), 'timed_out': timed_out,
                'descendants_killed': descendants_killed, 'remaining': remaining}
    finally:
        # The candidate never inherits this handle or permission to change limits.
        api.TerminateJobObject(job, 124)
        api.CloseHandle(job)
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


if __name__ == '__main__':
    if sys.argv[1:2] != ['--child'] or len(sys.argv) < 3:
        raise SystemExit('host module; child gate requires a command')
    print('HOST_JOB_PID=' + str(os.getpid()), flush=True)
    if sys.stdin.buffer.readline() != b'GO\n':
        raise SystemExit('host gate closed')
    raise SystemExit(subprocess.call(sys.argv[2:], stdin=subprocess.DEVNULL))
