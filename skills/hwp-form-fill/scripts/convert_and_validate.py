"""Read-only HWPX validation and isolated, optional Hancom SaveAs.

No document data leaves this machine. Exit 0 means HWPX passed; inspect the
separate hwp/pdf/visual statuses. Existing output files are never replaced.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

OLE = bytes.fromhex("D0 CF 11 E0 A1 B1 1A E1")
HWP_SETUP = "Windows + 한컴오피스 COM 등록 필요; python -m pip install pywin32==312"


def utf8():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def sha256(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else _hash(stream)


def _hash(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def com_registered():
    if sys.platform != "win32":
        return False
    import winreg
    for view in (0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"HWPFrame.HwpObject\CLSID", 0, winreg.KEY_READ | view) as key:
                if winreg.QueryValueEx(key, None)[0]:
                    return True
        except OSError:
            pass
    return False


def hwp_environment():
    if sys.platform != "win32":
        return False, "Windows가 아님"
    if not importlib.util.find_spec("win32com"):
        return False, "pywin32 없음"
    if not com_registered():
        return False, "HWPFrame.HwpObject COM 미등록"
    return True, "COM 등록 확인; 실제 변환은 아직 미검증"


def validate(path, expected=(), forbidden=()):
    from hwpx import HwpxDocument
    from hwpx.tools.package_validator import validate_editor_open_safety
    from hwpx.opc.security import guard_zip_file, parse_xml_stdlib, read_member

    if path.suffix.lower() != ".hwpx" or path.stat().st_size == 0:
        raise ValueError("0바이트 또는 HWPX가 아닌 입력")
    with zipfile.ZipFile(path) as archive:
        guard_zip_file(archive)
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC 오류")
        # Core validates required parts and manifest/spine relationships.
        for name in archive.namelist():
            if name.lower().endswith((".xml", ".hpf", ".rdf")):
                parse_xml_stdlib(read_member(archive, name))
    safety = validate_editor_open_safety(path)
    with HwpxDocument.open(path) as doc:
        content = doc.text.plain()
    missing = [value for value in expected if value not in content]
    residue = [value for value in forbidden if value in content]
    ok = safety.ok and safety.validate_package.ok and not missing and not residue
    return {"ok": ok, "zip_crc": True, "xml_parse": True,
            "open_safety": safety.to_dict(), "missing": missing, "forbidden_found": residue,
            "content_check": "PASS" if expected or forbidden else "SKIP: 문자열 조건 미지정"}


def _worker(source, directory, pdf):
    """Only this child owns the DispatchEx instance; never attach to user ROT."""
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    app = None
    result = {"status": "SKIP", "reason": "자동화 시작 실패", "pdf": {"status": "SKIP"}}
    try:
        app = win32com.client.DispatchEx("HWPFrame.HwpObject")
        app.XHwpWindows.Item(0).Visible = False
        if not app.Open(str(source), "HWPX", ""):
            raise RuntimeError("HWPX Open 실패")
        try:
            target = directory / "converted.hwp"
            if not app.SaveAs(str(target), "HWP", ""):
                raise RuntimeError("HWP SaveAs 실패")
            with target.open("rb") as stream:
                if stream.read(8) != OLE:
                    raise RuntimeError("HWP OLE 시그니처 불일치")
            app.Clear(1)
            if not app.Open(str(target), "HWP", ""):
                raise RuntimeError("HWP 재열기 실패")
            result.update(status="PASS", reason="실제 SaveAs + OLE + 한컴 재열기 통과", reopen=True)
        except Exception as exc:
            result["reason"] = str(exc)
        if pdf:
            try:
                app.Clear(1)
                if not app.Open(str(source), "HWPX", ""):
                    raise RuntimeError("PDF용 HWPX 재열기 실패")
                target = directory / "review.pdf"
                if not app.SaveAs(str(target), "PDF", ""):
                    raise RuntimeError("PDF SaveAs 실패")
                with target.open("rb") as stream:
                    if stream.read(5) != b"%PDF-":
                        raise RuntimeError("PDF 시그니처 불일치")
                result["pdf"] = {"status": "PASS"}
            except Exception as exc:
                result["pdf"] = {"status": "SKIP", "reason": str(exc)}
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        # Write evidence before Quit, which itself can stall on some installs.
        (directory / "worker.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        try:
            if app is not None:
                app.Quit()
        finally:
            pythoncom.CoUninitialize()


def copy_new(source, target):
    # Exclusive creation also protects hardlinks/symlinks and output races.
    with target.open("xb") as out:
        try:
            with source.open("rb") as src:
                shutil.copyfileobj(src, out)
        except Exception:
            out.close()
            target.unlink(missing_ok=True)
            raise


def run_conversion(source, output_dir, pdf=False, render_dir=None, timeout=240):
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / (source.stem + ".hwp")
    pdf_target = output_dir / (source.stem + ".pdf")
    if target.exists() or (pdf and pdf_target.exists()):
        return {"status": "SKIP", "reason": "출력 파일 존재: 덮어쓰기 거부; 새 --output-dir 사용"}
    # All COM partial files are confined to a unique local staging directory.
    with tempfile.TemporaryDirectory(prefix="hwp-form-convert-") as tmp:
        stage = Path(tmp)
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", str(source), str(stage), str(int(pdf))]
        try:
            subprocess.run(command, timeout=timeout, check=True, capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired:
            # subprocess kills only its Python child, never Hwp.exe/user processes.
            return {"status": "SKIP", "reason": f"한컴 자동화 {timeout}초 제한 초과; 한컴 프로세스는 강제 종료하지 않음"}
        except subprocess.CalledProcessError as exc:
            return {"status": "SKIP", "reason": "COM worker 실패: " + exc.stderr.decode("utf-8", "replace")[-1000:]}
        result = json.loads((stage / "worker.json").read_text(encoding="utf-8"))
        if result["status"] == "PASS":
            copy_new(stage / "converted.hwp", target)
            result["path"] = str(target)
            result["sha256"] = sha256(target)
        if result.get("pdf", {}).get("status") == "PASS":
            try:
                copy_new(stage / "review.pdf", pdf_target)
                result["pdf"]["path"] = str(pdf_target)
                import pymupdf
                with pymupdf.open(pdf_target) as document:
                    if document.page_count == 0:
                        raise ValueError("빈 PDF")
                    result["pdf"]["pages"] = document.page_count
                    images = []
                    if render_dir:
                        render_dir.mkdir(parents=True, exist_ok=False)
                    for index, page in enumerate(document):
                        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
                        if render_dir:
                            image = render_dir / f"page-{index + 1}.png"
                            pixmap.save(image)
                            images.append(str(image))
                    result["pdf"].update(render="PASS", images=images, visual_review="UNREVIEWED")
            except Exception as exc:
                result["pdf"].update(render="SKIP", reason=str(exc))
        return result


def emit(result, mode="both"):
    if mode != "json":
        print("검사 | 상태 | 설명")
        print("HWPX 검증 |", "PASS" if result["ok"] else "FAIL")
        print("명령 결과 |", "PASS" if result["command_ok"] else "FAIL")
        print("HWP 변환:", result["hwp"]["status"], result["hwp"].get("reason", ""))
        if result["hwp"]["status"] != "PASS":
            print("HWP 환경 안내:", HWP_SETUP)
        print("시각 검수 | UNREVIEWED | 페이지 이미지는 에이전트가 전부 확인해야 함")
    if mode != "text":
        print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv=None):
    utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="완성된 HWPX; 수정하지 않음")
    parser.add_argument("--hwp", choices=("auto", "off", "required"), default="auto")
    parser.add_argument("--output-dir", type=Path, help="HWP/PDF 출력 폴더; 기존 파일 거부")
    parser.add_argument("--expect", action="append", default=[], help="필수 문자열; 반복 가능")
    parser.add_argument("--forbid", action="append", default=[], help="금지 문자열; 반복 가능")
    parser.add_argument("--source", type=Path, help="보존할 원본 양식")
    parser.add_argument("--source-sha256", help="편집 전에 기록한 원본 SHA256; --source와 함께 사용")
    parser.add_argument("--pdf", action="store_true", help="한컴 PDF 저장도 시도")
    parser.add_argument("--render-dir", type=Path, help="새 이미지 디렉터리; --pdf 필요")
    parser.add_argument("--timeout", type=int, default=240, help="COM worker 제한 초 (기본 240)")
    parser.add_argument("--format", choices=("both", "json", "text"), default="both")
    args = parser.parse_args(argv)
    if bool(args.source) != bool(args.source_sha256):
        parser.error("--source와 --source-sha256를 함께 지정하세요")
    if args.render_dir and not args.pdf:
        parser.error("--render-dir에는 --pdf가 필요합니다")
    if args.timeout <= 0:
        parser.error("--timeout은 양수여야 합니다")
    result = {"ok": False, "hwp": {"status": "SKIP", "reason": "HWPX 검증 전"}}
    try:
        source = args.input.resolve(strict=True)
        before = sha256(source)
        if args.source and args.source.resolve() == source:
            raise ValueError("원본 양식과 결과 HWPX 경로가 같음")
        result["hwpx"] = validate(source, args.expect, args.forbid)
        result["ok"] = result["hwpx"]["ok"]
        result["source_unchanged"] = "SKIP: 원본 해시 미지정"
        if args.source:
            result["source_unchanged"] = sha256(args.source) == args.source_sha256.lower()
            result["ok"] &= result["source_unchanged"]
        if result["ok"]:
            available, reason = hwp_environment() if args.hwp != "off" else (False, "off 모드")
            if available:
                try:
                    result["hwp"] = run_conversion(source, (args.output_dir or source.parent).resolve(), args.pdf,
                                                   args.render_dir.resolve() if args.render_dir else None, args.timeout)
                except Exception as exc:
                    result["hwp"] = {"status": "SKIP", "reason": f"변환 실패: {exc}"}
            else:
                result["hwp"] = {"status": "SKIP", "reason": reason}
        result["input_unchanged"] = sha256(source) == before
        result["input_sha256"] = before
        result["ok"] &= result["input_unchanged"]
        if args.source:
            result["source_unchanged"] = sha256(args.source) == args.source_sha256.lower()
            result["ok"] &= result["source_unchanged"]
    except Exception as exc:
        result.update(ok=False, error=f"{type(exc).__name__}: {exc}")
    result["command_ok"] = result["ok"] and (args.hwp != "required" or result["hwp"]["status"] == "PASS")
    if result["hwp"]["status"] != "PASS":
        result["hwp"]["setup"] = HWP_SETUP
    emit(result, args.format)
    return 0 if result["command_ok"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        _worker(Path(sys.argv[2]), Path(sys.argv[3]), bool(int(sys.argv[4])))
    else:
        raise SystemExit(main())
