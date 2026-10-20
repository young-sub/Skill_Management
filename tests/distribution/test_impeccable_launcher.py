"""Exercise the distributed Windows launchers with native processes and local HTTP."""
import functools
import hashlib
import http.server
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest


SCRIPTS = Path(__file__).resolve().parents[2] / 'skills/impeccable/scripts'
WINDOWS = Path(os.environ.get('SystemRoot', 'C:/Windows'))
CSC = WINDOWS / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
SH = shutil.which('sh')
if os.name == 'nt' and SH:
    # Git's bin/sh.exe wrapper prepends its own curl ahead of the injected fixture.
    direct_shell = Path(SH).parent.parent / 'usr/bin/sh.exe'
    if direct_shell.is_file():
        SH = str(direct_shell)


@unittest.skipUnless(os.name == 'nt' and CSC.is_file(), 'Native Windows launcher regression')
class ImpeccableLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = tempfile.TemporaryDirectory()
        root = Path(cls.compiled.name)
        source = root / 'Fixture.cs'
        source.write_text('''using System;
using System.IO;
class Fixture {
  static int Main(string[] args) {
    if (Path.GetFileName(Environment.GetCommandLineArgs()[0]) == "curl.exe") {
      File.AppendAllText(Environment.GetEnvironmentVariable("TEST_CURL_LOG"), String.Join(" ", args) + "\\n");
      Console.Error.WriteLine("curl: (60) schannel: CRYPT_E_NO_REVOCATION_CHECK");
      return 60;
    }
    File.AppendAllText(Environment.GetEnvironmentVariable("TEST_ENGINE_MARKER"), "executed\\n");
    Console.WriteLine("impeccable-engine fixture");
    return 0;
  }
}''', encoding='utf-8')
        cls.binary = root / 'fixture.exe'
        subprocess.run([str(CSC), '/nologo', '/target:exe', '/out:' + str(cls.binary), str(source)], capture_output=True, check=True)

    @classmethod
    def tearDownClass(cls):
        cls.compiled.cleanup()

    def exercise(self, launcher, *, curl_failure, bad_hash=False, missing=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts = root / 'installed skill' / 'scripts'
            scripts.mkdir(parents=True)
            for name in ('impeccable', 'impeccable.cmd', 'VERSION'):
                # Git Bash must receive LF even with a CRLF repository checkout.
                (scripts / name).write_text((SCRIPTS / name).read_text(), encoding='utf-8', newline='')
            version = (scripts / 'VERSION').read_text().strip()
            release = root / 'http' / ('engine-v' + version)
            release.mkdir(parents=True)
            asset = release / 'impeccable-windows-x64.exe'
            shutil.copyfile(self.binary, asset)
            checksum = ('0' * 64 if bad_hash else hashlib.sha256(asset.read_bytes()).hexdigest())
            asset.with_suffix('.exe.sha256').write_text(checksum + '  ' + asset.name + '\n')
            if missing == 'binary':
                asset.unlink()
            elif missing == 'sidecar':
                asset.with_suffix('.exe.sha256').unlink()
            requests = []

            class Handler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    requests.append(self.path)
                    super().do_GET()

                def log_message(self, *args):
                    pass

            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(root / 'http')))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                env = dict(os.environ)
                for key in list(env):
                    if key.startswith('IMPECCABLE_'):
                        del env[key]
                cache = root / 'shared cache !'  # Exercise quoting without delayed expansion.
                env.update(IMPECCABLE_HOME=cache.as_posix(), USERPROFILE=str(root / 'profile'),
                           IMPECCABLE_DOWNLOAD_BASE=f'http://127.0.0.1:{server.server_port}',
                           TEST_ENGINE_MARKER=str(root / 'engine-ran'), TEST_CURL_LOG=str(root / 'curl.log'),
                           PROCESSOR_ARCHITECTURE='AMD64')
                path = [str(WINDOWS / 'System32'), str(WINDOWS / 'System32/WindowsPowerShell/v1.0')]
                if SH:
                    path.append(str(Path(SH).parent))
                if curl_failure:
                    fake = root / 'fake-bin'
                    fake.mkdir()
                    shutil.copyfile(self.binary, fake / 'curl.exe')
                    path.insert(0, str(fake))
                env['PATH'] = os.pathsep.join(path)
                command = ([str(WINDOWS / 'System32/cmd.exe'), '/d', '/c', str(scripts / 'impeccable.cmd')]
                           if launcher == 'cmd' else [SH, str(scripts / 'impeccable')])
                result = subprocess.run([*command, 'engine-probe'], cwd=root, env=env, capture_output=True, text=True, errors='replace', timeout=40)
                installed = cache / 'bin' / version / 'impeccable.exe'
                diagnostics = result.stdout + result.stderr
                if bad_hash or missing:
                    self.assertEqual(result.returncode, 127, diagnostics)
                    self.assertFalse(installed.exists(), diagnostics)
                    self.assertFalse((root / 'engine-ran').exists(), diagnostics)
                    self.assertEqual(list(cache.rglob('*.part*')), [], diagnostics)
                    if bad_hash:
                        self.assertIn('checksum mismatch', diagnostics)
                    else:
                        self.assertIn('CRYPT_E_NO_REVOCATION_CHECK', diagnostics)
                        self.assertIn('404', diagnostics)
                        self.assertIn('proxy', diagnostics.lower())
                    return
                self.assertEqual(result.returncode, 0, diagnostics)
                self.assertIn('impeccable-engine fixture', result.stdout)
                self.assertEqual(installed.read_bytes(), self.binary.read_bytes())
                self.assertEqual(len(requests), 2, requests)
                if curl_failure:
                    self.assertIn('CRYPT_E_NO_REVOCATION_CHECK', result.stderr)
                    self.assertEqual(len((root / 'curl.log').read_text().splitlines()), 2)
                # A second project shares the same versioned cache, even with an unreachable URL.
                other = root / 'second-project'
                other.mkdir()
                env['IMPECCABLE_DOWNLOAD_BASE'] = 'http://127.0.0.1:9'
                reused = subprocess.run([*command, 'engine-probe'], cwd=other, env=env, capture_output=True, text=True, errors='replace', timeout=10)
                self.assertEqual(reused.returncode, 0, reused.stdout + reused.stderr)
                self.assertEqual(len(requests), 2)
                if curl_failure:
                    self.assertEqual(len((root / 'curl.log').read_text().splitlines()), 2)
                self.assertEqual((root / 'engine-ran').read_text().splitlines(), ['executed', 'executed'])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def launchers(self):
        return ('cmd', 'sh') if SH else ('cmd',)

    def test_first_install_and_shared_version_cache_reuse(self):
        for launcher in self.launchers():
            with self.subTest(launcher=launcher):
                self.exercise(launcher, curl_failure=False)

    def test_curl_failure_falls_back_for_binary_and_checksum(self):
        for launcher in self.launchers():
            with self.subTest(launcher=launcher):
                self.exercise(launcher, curl_failure=True)

    def test_hash_mismatch_never_installs_or_executes(self):
        for launcher in self.launchers():
            with self.subTest(launcher=launcher):
                self.exercise(launcher, curl_failure=True, bad_hash=True)

    def test_both_transports_fail_with_cause_and_recovery(self):
        for launcher in self.launchers():
            for missing in ('binary', 'sidecar'):
                with self.subTest(launcher=launcher, missing=missing):
                    self.exercise(launcher, curl_failure=True, missing=missing)


if __name__ == '__main__':
    unittest.main()
