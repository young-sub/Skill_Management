from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parent
DRIVER = ROOT / "browser_drive.cjs"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_output(argv: list[str], *, timeout: int = 10, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
    if result.returncode:
        raise RuntimeError(
            "Command failed (%s): %s; stderr: %s"
            % (result.returncode, argv, result.stderr[-2000:])
        )
    return result.stdout.strip()


def browser_runtime() -> tuple[dict, dict[str, str]]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js executable is not available on PATH")
    environment = os.environ.copy()
    resolver = "const req=require('node:module').createRequire(%s);" % json.dumps(str(DRIVER))
    resolved = json.loads(command_output([node, "-e", resolver +
        "try{console.log(JSON.stringify(req.resolve('playwright')))}"
        "catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e;console.log('null')}"],
        timeout=15, env=environment))
    npm_root = None
    if resolved is None and os.name == "nt":
        npm_command = shutil.which("npm.cmd") or shutil.which("npm")
        if not npm_command:
            raise RuntimeError("npm is not available to locate the existing Playwright package")
        if npm_command.lower().endswith((".cmd", ".bat")):
            npm_root = command_output(["cmd.exe", "/d", "/s", "/c", "npm root -g"])
        else:
            npm_root = command_output([npm_command, "root", "-g"])
    elif resolved is None:
        npm_command = shutil.which("npm")
        if not npm_command:
            raise RuntimeError("npm is not available to locate the existing Playwright package")
        npm_root = command_output([npm_command, "root", "-g"])
    if npm_root is not None:
        previous_node_path = environment.get("NODE_PATH")
        environment["NODE_PATH"] = os.pathsep.join(value for value in (npm_root, previous_node_path) if value)
    inspect = resolver + (
        "const path=require('node:path');"
        "const playwright=req('playwright');"
        "const packagePath=req.resolve('playwright/package.json');"
        "const root=path.dirname(packagePath);"
        "const corePackage=req.resolve('playwright-core/package.json',{paths:[root]});"
        "const coreRoot=path.dirname(corePackage);"
        "console.log(JSON.stringify({node:process.execPath,node_version:process.version,"
        "playwright_package:packagePath,playwright_entry:req.resolve('playwright'),"
        "playwright_lib_entry:path.join(root,'lib/index.js'),"
        "core_package:corePackage,core_entry:req.resolve('playwright-core',{paths:[root]}),"
        "chromium_entry:path.join(coreRoot,'lib/server/chromium/chromium.js'),"
        "browser_metadata:path.join(coreRoot,'browsers.json'),"
        "playwright_version:req('playwright/package.json').version,"
        "chromium_executable:playwright.chromium.executablePath()}));"
    )
    details = json.loads(command_output([node, "-e", inspect], timeout=15, env=environment))
    files = {
        "node": Path(details["node"]),
        "playwright_package": Path(details["playwright_package"]),
        "playwright_entry": Path(details["playwright_entry"]),
        "playwright_lib_entry": Path(details["playwright_lib_entry"]),
        "core_package": Path(details["core_package"]),
        "core_entry": Path(details["core_entry"]),
        "chromium_entry": Path(details["chromium_entry"]),
        "browser_metadata": Path(details["browser_metadata"]),
        "chromium_executable": Path(details["chromium_executable"]),
    }
    missing = [str(path) for path in files.values() if not path.is_file()]
    if missing:
        raise RuntimeError("Required browser dependency files are missing: " + ", ".join(missing))
    details["external_files"] = {
        name: {"path": str(path), "sha256": sha256(path)} for name, path in files.items()
    }
    details["global_module_root"] = str(Path(npm_root).resolve()) if npm_root else None
    details["python_version"] = sys.version
    details["sqlite_version"] = sqlite3.sqlite_version
    details["python_executable"] = str(Path(sys.executable).resolve())
    return details, environment


def server_process(
    root: Path, database: Path, port_file: Path, log_path: Path, *, port: int = 0
) -> tuple[subprocess.Popen, object]:
    port_file.unlink(missing_ok=True)
    log = log_path.open("a", encoding="utf-8", buffering=1)
    argv = [
        sys.executable,
        str(root / "app.py"),
        "--database",
        str(database),
        "--port-file",
        str(port_file),
        "--port",
        str(port),
    ]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        argv,
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=flags,
    )
    return process, log


def stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def wait_for_server(process: subprocess.Popen, port_file: Path, timeout: float = 20.0) -> dict:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Application process exited before readiness: " + str(process.returncode))
        if port_file.is_file():
            try:
                address = json.loads(port_file.read_text(encoding="utf-8"))
                url = "http://%s:%s" % (address["host"], address["port"])
                with urllib.request.urlopen(url + "/health", timeout=2) as response:
                    health = json.loads(response.read().decode("utf-8"))
                if response.status == 200 and health.get("ready") is True:
                    return {"url": url, "address": address, "health": health}
            except (OSError, ValueError, KeyError, urllib.error.URLError) as error:
                last_error = str(error)
        time.sleep(0.1)
    raise TimeoutError("Application did not become ready: " + str(last_error))


def database_rows(database: Path) -> list[dict]:
    with closing(sqlite3.connect(database, timeout=5)) as connection:
        connection.row_factory = sqlite3.Row
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError("SQLite integrity check failed: " + str(integrity))
        return [dict(row) for row in connection.execute("SELECT id, quantity FROM items ORDER BY id")]


def add_check(checks: list[dict], identity: str, expected: object, observed: object) -> None:
    checks.append(
        {
            "id": identity,
            "expected": expected,
            "observed": observed,
            "passed": observed == expected,
        }
    )


def start_browser(project: Path, runtime_env: dict[str, str], url: str, report_dir: Path) -> subprocess.Popen:
    argv = [shutil.which("node"), str(DRIVER), url, str(report_dir)]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(
        argv,
        cwd=project,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=runtime_env,
        creationflags=flags,
    )


def read_line_with_timeout(process: subprocess.Popen, timeout: int = 90) -> str:
    lines: queue.Queue[str] = queue.Queue(maxsize=1)
    threading.Thread(target=lambda: lines.put(process.stdout.readline()), daemon=True).start()
    try:
        return lines.get(timeout=timeout)
    except queue.Empty as error:
        raise TimeoutError("Browser driver did not report its pre-restart observations") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the connected product acceptance path.")
    parser.add_argument("--report", type=Path, required=True, help="New raw JSON observation path")
    args = parser.parse_args()
    report_path = args.report.resolve()
    report_dir = report_path.parent / report_path.stem
    database = report_dir / "product.sqlite"
    port_file = report_dir / "server-port.json"
    log_path = report_dir / "server.log"
    if report_path.exists() or report_dir.exists():
        print("Refusing to overwrite existing report or database.", file=sys.stderr)
        return 2

    report_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.uuid4())
    started = time.monotonic()
    report = {
        "schema_version": 1,
        "status": "BLOCKED",
        "execution": {
            "id": run_id,
            "argv": [sys.executable, *sys.argv],
            "cwd": str(Path.cwd().resolve()),
            "project_root": str(ROOT),
            "report_path": str(report_path),
            "database_path": str(database),
            "started_at_utc": now(),
            "target": None,
            "executed": False,
            "phases": [],
        },
        "checks": [],
        "observed": {"services": [], "api_responses": [], "database": {}, "browser": {}},
        "skipped": [],
        "errors": [],
        "counts": {"assertions": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0},
        "cleanup": {"attempted": False, "removed_paths": [], "errors": []},
        "artifacts": [],
    }
    service = None
    server_log = None
    browser = None
    runtime = None
    runtime_env = None
    port = 0
    fatal_error = False
    phase = "doctor"
    try:
        phase = "launch"
        report["execution"]["phases"].append({"name": "launch", "started_at_utc": now()})
        runtime, runtime_env = browser_runtime()
        report["observed"]["browser"] = runtime
        service, server_log = server_process(ROOT, database, port_file, log_path)
        ready = wait_for_server(service, port_file)
        port = int(ready["address"]["port"])
        report["execution"]["target"] = ready["url"]
        report["observed"]["services"].append(
            {"pid": service.pid, "port": port, "launch": ready, "status": "running"}
        )
        report["execution"]["phases"][-1]["finished_at_utc"] = now()

        phase = "doctor"
        report["execution"]["phases"].append({"name": "doctor", "started_at_utc": now()})
        first_rows = database_rows(database)
        report["observed"]["database"]["initial"] = {
            "rows": first_rows,
            "integrity": "ok",
            "health": ready["health"],
        }
        add_check(report["checks"], "new_database_is_empty", [], first_rows)
        report["execution"]["phases"][-1]["finished_at_utc"] = now()

        phase = "drive"
        report["execution"]["phases"].append({"name": "drive", "started_at_utc": now()})
        browser = start_browser(ROOT, runtime_env, ready["url"], report_dir)
        report["execution"]["executed"] = True
        event_line = read_line_with_timeout(browser)
        if not event_line:
            raise RuntimeError("Browser driver exited without observations: " + str(browser.poll()))
        first_event = json.loads(event_line)
        if first_event.get("phase") != "restart_ready":
            if first_event.get("phase") == "error":
                report["errors"].append({"phase": "browser_drive", **first_event.get("error", {})})
            raise RuntimeError("Browser driver did not complete the pre-restart user flow")
        report["checks"].extend(first_event.get("checks", []))
        report["observed"]["api_responses"].extend(first_event.get("api_responses", []))
        report["observed"]["browser"].update(first_event.get("browser", {}))
        report["observed"]["browser"]["before_restart"] = first_event.get("observations", {})

        phase = "evidence"
        report["execution"]["phases"].append({"name": "evidence", "started_at_utc": now()})
        before_restart = database_rows(database)
        report["observed"]["database"]["before_restart"] = {
            "rows": before_restart,
            "integrity": "ok",
        }
        add_check(report["checks"], "sqlite_values_before_restart", [2, 0],
                  [row["quantity"] for row in before_restart])
        add_check(report["checks"], "negative_value_not_persisted_before_restart", 2, len(before_restart))
        report["execution"]["phases"][-1]["finished_at_utc"] = now()

        phase = "restart"
        report["execution"]["phases"].append({"name": "service_restart", "started_at_utc": now()})
        stop_process(service)
        report["observed"]["services"][-1].update(status="stopped", exit_code=service.returncode)
        if server_log is not None:
            server_log.close()
            server_log = None
        service, server_log = server_process(ROOT, database, port_file, log_path, port=port)
        restarted = wait_for_server(service, port_file)
        report["observed"]["services"].append(
            {"pid": service.pid, "port": port, "launch": restarted, "status": "running"}
        )
        report["observed"]["database"]["after_restart_doctor"] = {
            "health": restarted["health"],
            "rows": database_rows(database),
        }
        if browser.stdin is None:
            raise RuntimeError("Browser driver control channel is unavailable")
        browser.stdin.write("RESTARTED\n")
        browser.stdin.flush()
        browser.stdin = None
        remaining, browser_stderr = browser.communicate(timeout=90)
        final_lines = [line for line in remaining.splitlines() if line.strip()]
        if not final_lines:
            raise RuntimeError("Browser driver produced no final observation: " + browser_stderr[-2000:])
        final_event = json.loads(final_lines[-1])
        if browser.returncode != 0 or final_event.get("phase") != "complete":
            report["errors"].append(
                {
                    "phase": "browser_drive",
                    "exit_code": browser.returncode,
                    "stderr": browser_stderr[-2000:],
                    "event": final_event,
                }
            )
            raise RuntimeError("Browser driver could not complete the post-restart observation")
        report["checks"].extend(final_event.get("checks", []))
        report["observed"]["api_responses"].extend(final_event.get("api_responses", []))
        report["observed"]["browser"].update(final_event.get("browser", {}))
        report["observed"]["browser"]["after_restart"] = final_event.get("observations", {})
        after_restart = database_rows(database)
        report["observed"]["database"]["after_restart"] = {
            "rows": after_restart,
            "integrity": "ok",
        }
        add_check(report["checks"], "sqlite_values_after_restart", [2, 0],
                  [row["quantity"] for row in after_restart])
        add_check(report["checks"], "service_restart_preserved_storage", before_restart, after_restart)
        report["execution"]["phases"][-1]["finished_at_utc"] = now()
    except Exception as error:
        fatal_error = True
        report["errors"].append(
            {"phase": phase, "type": type(error).__name__, "message": str(error)}
        )
        if phase in {"doctor", "launch"}:
            report["skipped"].append({"phase": "browser_flow", "reason": str(error)})
        if browser is not None and browser.poll() is None:
            try:
                browser.kill()
                browser.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if browser is not None and browser.stderr is not None:
            try:
                report["observed"]["browser"]["driver_stderr"] = browser.stderr.read()[-2000:]
            except OSError:
                pass
    finally:
        report["cleanup"]["attempted"] = True
        report["execution"]["phases"].append({"name": "cleanup", "started_at_utc": now()})
        if browser is not None and browser.poll() is None:
            try:
                browser.kill()
                browser.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired) as error:
                report["cleanup"]["errors"].append(str(error))
        stop_process(service)
        if service is not None:
            for observed in report["observed"]["services"]:
                if observed["pid"] == service.pid:
                    observed.update(status="stopped" if service.poll() is not None else "running",
                                    exit_code=service.returncode)
        if server_log is not None:
            server_log.close()
        for path in (port_file, database, Path(str(database) + "-wal"), Path(str(database) + "-shm")):
            try:
                if path.exists():
                    path.unlink()
                    report["cleanup"]["removed_paths"].append(str(path))
            except OSError as error:
                report["cleanup"]["errors"].append({"path": str(path), "error": str(error)})
        if log_path.is_file():
            report["artifacts"].append(
                {"kind": "server_log", "path": str(log_path), "sha256": sha256(log_path)}
            )
        for name, path in (
            ("entry_desktop_screenshot", report_dir / "entry-1280.png"),
            ("entry_mobile_screenshot", report_dir / "entry-390.png"),
            ("history_desktop_screenshot", report_dir / "history-1280.png"),
            ("history_mobile_screenshot", report_dir / "history-390.png"),
            ("history_mobile_after_restart_screenshot", report_dir / "history-390-after-restart.png"),
            ("browser_trace", report_dir / "browser-trace.zip"),
        ):
            if path.is_file():
                report["artifacts"].append({"kind": name, "path": str(path), "sha256": sha256(path)})
        report["execution"]["phases"][-1]["finished_at_utc"] = now()
        if report["cleanup"]["errors"]:
            fatal_error = True
            report["errors"].append({"phase": "cleanup", "details": report["cleanup"]["errors"]})

    required_check_ids = {
        "new_database_is_empty",
        "history_empty_and_loading_states",
        "history_read_error_state",
        "accessible_entry_controls",
        "keyboard_submit",
        "positive_quantity_api_save",
        "negative_quantity_rejected_by_domain",
        "zero_quantity_api_save",
        "history_fresh_read_before_restart",
        "sqlite_values_before_restart",
        "negative_value_not_persisted_before_restart",
        "history_fresh_read_after_service_restart",
        "mobile_history_layout",
        "shared_ui_mobile_acceptance",
        "sqlite_values_after_restart",
        "service_restart_preserved_storage",
    }
    present_check_ids = {check.get("id") for check in report["checks"]}
    missing_check_ids = sorted(required_check_ids - present_check_ids)
    if missing_check_ids:
        fatal_error = True
        report["skipped"].append(
            {"phase": "drive", "checks": missing_check_ids, "reason": "required observation was not reached"}
        )
    passed = sum(check.get("passed") is True for check in report["checks"])
    failed = sum(check.get("passed") is not True for check in report["checks"])
    report["counts"] = {
        "assertions": len(report["checks"]),
        "passed": passed,
        "failed": failed,
        "skipped": len(report["skipped"]),
        "errors": len(report["errors"]),
    }
    report["observed"]["assertions_by_id"] = {
        check["id"]: {
            "expected": check.get("expected"),
            "observed": check.get("observed"),
            "passed": check.get("passed"),
        }
        for check in report["checks"]
        if isinstance(check.get("id"), str)
    }
    report["status"] = "BLOCKED" if fatal_error or report["skipped"] else ("ISSUES" if failed else "PASS")
    report["execution"]["finished_at_utc"] = now()
    report["execution"]["duration_ms"] = round((time.monotonic() - started) * 1000)
    try:
        with report_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError:
        print("Refusing to overwrite existing report: " + str(report_path), file=sys.stderr)
        return 2
    print(json.dumps({"report": str(report_path), "status": report["status"]}, ensure_ascii=False))
    return {"PASS": 0, "ISSUES": 1, "BLOCKED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
