"""Install a reviewed host bundle below an already provisioned protected parent.

Does not create accounts, change ACLs, update an existing installation or activate
an ordinary plugin. The host owns review of policy, execution config and drivers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import uuid


HELPERS = ('host_verify.py', 'host_result.py', 'windows_job.py')
PROBE = r'''
import ctypes,json,os,pathlib,re,subprocess,sys
from ctypes import wintypes as w
root=pathlib.Path(sys.argv[1]);marker=pathlib.Path(sys.argv[2]);canary=root/'install-canary'
marker.write_text('workspace-write')
assert canary.read_bytes()==b'host-canary'
allowed={}
for name,operation in [('overwrite',lambda:canary.write_bytes(b'changed')),('delete',canary.unlink),('create',lambda:(root/'candidate-created').write_text('changed')),('rename',lambda:root.rename(root.with_name(root.name+'.moved')))]:
 try:operation();allowed[name]=True
 except PermissionError:allowed[name]=False
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.CloseHandle.argtypes=[w.HANDLE]
for path in [root,canary]:
 for name,mask in [('write_dac',0x40000),('write_owner',0x80000)]:
  h=k.CreateFileW(str(path),mask,7,None,3,0x02000000,None)
  allowed[path.name+':'+name]=h!=ctypes.c_void_p(-1).value
  if allowed[path.name+':'+name]:k.CloseHandle(h)
who=subprocess.check_output([str(pathlib.Path(os.environ['SYSTEMROOT'])/'System32/whoami.exe'),'/user','/fo','csv','/nh'])
print(json.dumps({'allowed':allowed,'sid':re.search(rb'S-1-5-[0-9-]+',who).group().decode()}))
'''


def _probe(target, config):
    verifier = runpy.run_path(str(Path(__file__).with_name('host_verify.py')))
    verifier['_identities'](config)
    if Path(config['codex']).resolve() != Path(shutil.which('codex') or '').resolve():
        raise ValueError('native_codex_path_mismatch')
    workspace = Path(config['workspace']).resolve()
    if target.is_relative_to(workspace) or not workspace.is_dir():
        raise ValueError('authority_inside_candidate_workspace')
    marker = workspace / ('host-install-probe-' + str(uuid.uuid4()))
    env = verifier['sandbox_env'](config)
    argv = [config['codex'], 'sandbox', '-P', ':workspace', '-c', 'windows.sandbox="elevated"',
            '-C', str(workspace), '--', config['python'], '-I', str(Path(__file__).resolve()),
            '--probe-child', str(target), str(marker)]
    process = subprocess.run(argv, cwd=workspace, env=env, capture_output=True, timeout=60)
    record = {'exit': process.returncode, 'stdout': process.stdout.decode('utf-8', 'replace'),
              'stderr': process.stderr.decode('utf-8', 'replace')}
    # Retain failed probes in the configured workspace too; a failed rename probe
    # may have moved the disposable target before any helper was installed.
    marker.with_suffix('.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    if process.returncode:
        raise ValueError('host_boundary_probe_failed:' + str(marker.with_suffix('.json')))
    observed = json.loads(process.stdout)
    host = subprocess.check_output([str(Path(os.environ['SYSTEMROOT']) / 'System32/whoami.exe'), '/user', '/fo', 'csv', '/nh'])
    host_sid = re.search(rb'S-1-5-[0-9-]+', host).group().decode()
    if (observed['sid'] == host_sid or any(observed['allowed'].values())
            or marker.read_text() != 'workspace-write'
            or (target / 'install-canary').read_bytes() != b'host-canary'):
        raise ValueError('host_boundary_not_protected')
    return {'verified': True, 'candidate_sid': observed['sid'], 'probe': record}


def install(bundle, target):
    bundle, target = Path(bundle).absolute(), Path(target).absolute()
    helper_root = Path(__file__).resolve().parent
    api = runpy.run_path(str(helper_root / 'host_result.py'))
    api['_file'](bundle, '.')
    api['_file'](target.parent, target.name)
    if not target.parent.is_dir() or target.exists():
        raise FileExistsError('new_target_under_existing_protected_parent_required')
    policy_bytes = api['_file'](bundle, 'policy.json').read_bytes()
    policy = json.loads(policy_bytes)
    if not isinstance(policy.get('snapshot'), list):
        raise ValueError('snapshot_required')
    # Freeze bytes before creating an installation. Never import bundle helpers.
    payload = {'policy.json': policy_bytes}
    for name in policy['snapshot']:
        payload[name] = (helper_root / name).read_bytes() if name in HELPERS else api['_file'](bundle, name).read_bytes()
    if not set(HELPERS + ('execution.json',)).issubset(payload):
        raise ValueError('host_runtime_not_bound')
    config = json.loads(payload['execution.json'])
    runpy.run_path(str(helper_root / 'host_verify.py'))['require_sandbox_ready'](config)
    target.mkdir()
    (target / 'install-canary').write_bytes(b'host-canary')
    probe = _probe(target, config)
    for name, raw in payload.items():
        path = api['_file'](target, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    runpy.run_path(str(target / 'host_verify.py'))['prepare'](target)
    hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in payload.items()}
    if any(hashlib.sha256(api['_file'](target, name).read_bytes()).hexdigest() != sha for name, sha in hashes.items()):
        raise ValueError('host_install_changed')
    record = {'status': 'INSTALLED', 'target': str(target), 'sha256': hashes, 'boundary': probe}
    with (target / 'installation.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    args = parser.parse_args()
    try:
        record = install(args.bundle, args.target)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        record = {'status': 'BLOCKED', 'error': str(error)}
    print(json.dumps(record, sort_keys=True))
    return 0 if record['status'] == 'INSTALLED' else 2


if __name__ == '__main__':
    if sys.argv[1:2] == ['--probe-child']:
        sys.argv = sys.argv[1:]
        exec(PROBE)
        raise SystemExit(0)
    raise SystemExit(main())
