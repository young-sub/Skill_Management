@echo off
setlocal
rem Impeccable launcher (Windows). Runs bin\windows-<arch>\impeccable.exe next
rem to this file, else a cached or freshly downloaded engine binary.
rem
rem Structure notes (native Windows cmd and Git Bash regressions live in
rem tests/distribution/test_impeccable_launcher.py in the distribution repo):
rem - No multi-line parenthesized blocks: cmd expands %var% at block parse
rem   time, which made the old download path read back empty %url%/%cached%.
rem   Linear goto flow keeps every expansion on its own line, and avoids
rem   delayed expansion eating ! characters in user arguments.
rem - The unversioned user binary and the PATH candidate are validated with
rem   the engine-probe handshake (see :probe) so the retired 3.x npm CLI,
rem   whose bin is also named impeccable, is never exec'd. IMPECCABLE_BIN,
rem   the sibling binary, and the version-pinned cache stay trusted.
rem - Downloads are verified against the .sha256 sidecar via certutil and
rem   fail closed: a missing sidecar or hash tool refuses the download. On
rem   ARM64 the arm64 asset is tried first and the x64 asset is the
rem   fallback (Windows on ARM runs x64 binaries).
if not defined IMPECCABLE_SKILL_DIR set "IMPECCABLE_SKILL_DIR=%~dp0.."
if not defined IMPECCABLE_SELF set "IMPECCABLE_SELF=%~f0"
set "arch=x64"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "arch=arm64"

if not defined IMPECCABLE_BIN goto no_env_bin
if not exist "%IMPECCABLE_BIN%" goto no_env_bin
set "run=%IMPECCABLE_BIN%"
goto run
:no_env_bin

set "bin=%~dp0bin\windows-%arch%\impeccable.exe"
if not exist "%bin%" goto no_sibling
set "run=%bin%"
goto run
:no_sibling

set "home_bin=%USERPROFILE%\.impeccable\bin\impeccable.exe"
if not exist "%home_bin%" goto no_home_bin
if defined IMPECCABLE_LAUNCHER_PROBE goto no_home_bin
call :probe "%home_bin%"
if not "%probe_ok%"=="1" goto no_home_bin
set "run=%home_bin%"
goto run
:no_home_bin

set "version="
if exist "%~dp0VERSION" set /p version=<"%~dp0VERSION"
if not defined IMPECCABLE_HOME set "IMPECCABLE_HOME=%USERPROFILE%\.impeccable"
set "cached=%IMPECCABLE_HOME%\bin\%version%\impeccable.exe"
if not defined version goto no_cache
if not exist "%cached%" goto no_cache
set "run=%cached%"
goto run
:no_cache

if defined IMPECCABLE_LAUNCHER_PROBE goto download
where impeccable >nul 2>nul
if errorlevel 1 goto download
call :probe impeccable
if not "%probe_ok%"=="1" goto download
impeccable %*
exit /b

:download
rem Last resort: fetch this version's binary from the release channel into
rem the version-pinned user cache, verify it, then run it. Never inside
rem another launcher's probe: fail fast and quiet instead.
if defined IMPECCABLE_LAUNCHER_PROBE exit /b 127
if not defined version goto fail
if not defined IMPECCABLE_DOWNLOAD_BASE set "IMPECCABLE_DOWNLOAD_BASE=https://github.com/pbakaus/impeccable/releases/download"
if not exist "%IMPECCABLE_HOME%\bin\%version%" mkdir "%IMPECCABLE_HOME%\bin\%version%" >nul 2>nul
set "asset=impeccable-windows-%arch%.exe"
set "url=%IMPECCABLE_DOWNLOAD_BASE%/engine-v%version%/%asset%"
call :fetch_url "%url%" "%cached%.part"
if not errorlevel 1 goto verify
if not "%arch%"=="arm64" goto fail
set "asset=impeccable-windows-x64.exe"
set "url=%IMPECCABLE_DOWNLOAD_BASE%/engine-v%version%/%asset%"
call :fetch_url "%url%" "%cached%.part"
if errorlevel 1 goto fail

:verify
call :check_download
if errorlevel 1 exit /b 127
rem Mirrors the sh launcher and fails closed: a freshly downloaded binary
rem runs only after verifying against its .sha256 sidecar. A sidecar that
rem cannot be fetched, or an empty certutil result, refuses the download
rem instead of running an unverified binary.
call :fetch_url "%url%.sha256" "%cached%.sha256"
if errorlevel 1 goto verify_refuse
set "expected="
set /p expected=<"%cached%.sha256"
for /f "tokens=1" %%h in ("%expected%") do set "expected=%%h"
call :check_download
if errorlevel 1 exit /b 127
set "actual="
rem Reuse the sidecar staging file after reading expected. Check certutil's
rem status before parsing: its error text on stdout is not a digest.
certutil -hashfile "%cached%.part" SHA256 >"%cached%.sha256"
if errorlevel 1 goto hash_failed
call :check_download
if errorlevel 1 exit /b 127
for /f "usebackq skip=1 delims=" %%h in ("%cached%.sha256") do if not defined actual set "actual=%%h"
del "%cached%.sha256" >nul 2>nul
if not defined expected goto verify_refuse
if not defined actual goto verify_refuse
set "actual=%actual: =%"
if /I "%actual%"=="%expected%" goto place
del "%cached%.part" >nul 2>nul
echo impeccable: checksum mismatch downloading %url% 1>&2
exit /b 127

:hash_failed
type "%cached%.sha256" 1>&2
goto verify_refuse

:verify_refuse
call :check_download
if errorlevel 1 exit /b 127
del "%cached%.part" >nul 2>nul
del "%cached%.sha256" >nul 2>nul
echo impeccable: cannot verify %url% against %url%.sha256; refusing the unverified download 1>&2
exit /b 127

:fetch_url
rem Pass data through the environment, not interpolated PowerShell code.
rem Both the executable and its checksum use this same verified-TLS path.
set "IMPECCABLE_FETCH_URL=%~1"
set "IMPECCABLE_FETCH_PATH=%~2"
where curl.exe >nul 2>nul
if errorlevel 1 goto fetch_powershell
curl.exe -fsSL --connect-timeout 15 --max-time 120 -o "%IMPECCABLE_FETCH_PATH%" "%IMPECCABLE_FETCH_URL%"
if not errorlevel 1 exit /b 0
:fetch_powershell
echo impeccable: curl failed or is unavailable; retrying %IMPECCABLE_FETCH_URL% with PowerShell. 1>&2
powershell.exe -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; try { Invoke-WebRequest -UseBasicParsing -Uri $env:IMPECCABLE_FETCH_URL -OutFile $env:IMPECCABLE_FETCH_PATH -TimeoutSec 120 } catch { [Console]::Error.WriteLine(('impeccable: PowerShell download failed: ' + $_.Exception.Message)); exit 1 }"
if not errorlevel 1 exit /b 0
echo impeccable: download failed: %IMPECCABLE_FETCH_URL%. Check network, proxy and certificate trust/revocation access, then retry; do not disable certificate validation. For offline recovery, download the engine and .sha256 on a trusted connection and verify SHA-256 before using IMPECCABLE_BIN. 1>&2
exit /b 1

:check_download
set "download_file=%~1"
if not defined download_file set "download_file=%cached%.part"
if not exist "%download_file%" goto download_missing
for %%f in ("%download_file%") do if %%~zf==0 goto download_empty
exit /b 0

:download_missing
del "%cached%.sha256" >nul 2>nul
echo impeccable: download completed but the file was removed before execution: %url%; check your antivirus quarantine or logs. Refusing to continue; do not disable protection. 1>&2
exit /b 127

:download_empty
del "%download_file%" >nul 2>nul
del "%cached%.sha256" >nul 2>nul
echo impeccable: downloaded file is empty: %url%; refusing the unverified download 1>&2
exit /b 127

:place
call :check_download
if errorlevel 1 exit /b 127
move /y "%cached%.part" "%cached%" >nul 2>nul
if errorlevel 1 goto place_failed
call :check_download "%cached%"
if errorlevel 1 exit /b 127
set "run=%cached%"
goto run

:place_failed
call :check_download
if errorlevel 1 exit /b 127
del "%cached%.part" >nul 2>nul
echo impeccable: could not cache the verified download: %url% 1>&2
exit /b 127

:run
"%run%" %*
exit /b

:probe
rem Sets probe_ok=1 when %1 answers the engine handshake: prints
rem "impeccable-engine <version>" and exits 0. The 3.x npm CLI answers any
rem unknown verb with "Unknown command", exit 1, so it never passes.
set "probe_ok="
set "probe_tmp=%TEMP%\impeccable-probe-%RANDOM%%RANDOM%.txt"
set "IMPECCABLE_LAUNCHER_PROBE=1"
"%~1" engine-probe >"%probe_tmp%" 2>nul
set "probe_err=%ERRORLEVEL%"
set "IMPECCABLE_LAUNCHER_PROBE="
if not "%probe_err%"=="0" goto probe_done
findstr /b /c:"impeccable-engine" "%probe_tmp%" >nul 2>nul
if not errorlevel 1 set "probe_ok=1"
:probe_done
del "%probe_tmp%" >nul 2>nul
exit /b 0

:fail
del "%cached%.part" >nul 2>nul
echo impeccable: no engine binary found (looked in %bin%, %cached%, PATH). 1>&2
echo Download impeccable-windows-%arch%.exe and its .sha256 from https://github.com/pbakaus/impeccable/releases (tag engine-v%version%). Verify SHA-256 before saving it as %cached% or using IMPECCABLE_BIN. Docs: https://impeccable.style 1>&2
exit /b 127
