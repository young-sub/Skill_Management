"""Stdlib-first capability probe. Only --smoke-test launches Hancom."""
import argparse
import importlib
import importlib.metadata
import json
import platform
from pathlib import Path
import sys
import tempfile

from convert_and_validate import com_registered, hwp_environment, run_conversion, utf8, validate, HWP_SETUP


def main():
    original_encoding = sys.stdout.encoding
    utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", help="임시 HWPX를 실제 HWP/PDF로 저장 (최초 실행은 수십 초 이상)")
    parser.add_argument("--require-hwp", action="store_true", help="실제 변환 PASS 요구; --smoke-test와 함께 사용")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--format", choices=("both", "json", "text"), default="both")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout은 양수여야 합니다")
    checks = {}

    def record(name, status, detail="", repair=""):
        checks[name] = {"status": status, "detail": detail, "repair": repair}

    record("운영체제", "PASS", platform.platform())
    record("Python", "PASS", platform.python_version() + " " + sys.executable)
    record("가상환경", "PASS" if sys.prefix != sys.base_prefix else "SKIP", sys.prefix,
           "python -m venv .hwp-form-work/.venv" if sys.prefix == sys.base_prefix else "")
    record("UTF-8 출력", "PASS", f"초기={original_encoding}, 현재={sys.stdout.encoding}")
    modules = [("python-hwpx", "hwpx", "python-hwpx==6.5.0"),
               ("DOCX 읽기", "docx", "python-docx==1.2.0"),
               ("pywin32", "win32com.client", "pywin32==312"),
               ("PDF 렌더링", "pymupdf", "PyMuPDF==1.28.2")]
    for name, module, package in modules:
        try:
            imported = importlib.import_module(module)
            version = importlib.metadata.version(package.split("==")[0])
            if module == "hwpx" and not ((6, 5, 0) <= tuple(int(n) for n in version.split(".")[:3]) < (7, 0, 0)):
                raise RuntimeError(f"지원 범위 밖 python-hwpx: {version}; >=6.5.0,<7 필요")
            if module == "docx":
                import io
                stream = io.BytesIO()
                doc = imported.Document()
                doc.add_paragraph("probe")
                doc.save(stream)
                stream.seek(0)
                assert imported.Document(stream).paragraphs[0].text == "probe"
            elif module == "pymupdf":
                with imported.open() as doc:
                    doc.new_page().get_pixmap()
            record(name, "PASS", version)
        except Exception as exc:
            record(name, "FAIL" if module == "hwpx" else "SKIP", str(exc), f"python -m pip install {package}")
    record("HWP COM 등록", "PASS" if com_registered() else "SKIP", "HWPFrame.HwpObject", HWP_SETUP)
    available, reason = hwp_environment()
    record("한컴 자동화", "UNVERIFIED" if available else "SKIP", reason)
    record("HWP 변환", "UNVERIFIED" if available else "SKIP", reason, HWP_SETUP)
    record("PDF 시각 검수", "SKIP", "실제 문서 PDF 생성과 전체 페이지 관찰 필요")
    record("HWPX MCP", "UNVERIFIED", "이 스크립트는 호스트 세션 도구 노출을 알 수 없음; 에이전트가 health 호출로 확인")
    basic = False
    smoke = None
    with tempfile.TemporaryDirectory(prefix="hwp-form-doctor-") as tmp:
        try:
            from hwpx import HwpxDocument
            path = Path(tmp) / "probe.hwpx"
            with HwpxDocument.new() as doc:
                doc.add_paragraph("환경 검사")
                doc.save_to_path(path)
            with HwpxDocument.open(path) as doc:
                assert "환경 검사" in doc.text.plain()
                record("HWPX 읽기", "PASS")
                doc.add_paragraph("편집 검사")
                edited = Path(tmp) / "edited.hwpx"
                doc.save_to_path(edited)
            evidence = validate(edited, ["환경 검사", "편집 검사"])
            basic = evidence["ok"] and checks["python-hwpx"]["status"] == "PASS"
            record("HWPX 편집", "PASS" if basic else "FAIL", json.dumps(evidence, ensure_ascii=False) if not basic else "저장·재열기·open-safety 통과")
            if args.smoke_test and available and basic:
                try:
                    smoke = run_conversion(edited, Path(tmp), pdf=True, timeout=args.timeout)
                except Exception as exc:
                    smoke = {"status": "SKIP", "reason": str(exc)}
                record("HWP 변환", smoke["status"], smoke.get("reason", ""), HWP_SETUP if smoke["status"] != "PASS" else "")
                record("한컴 자동화", smoke["status"], "실제 임시 문서 검사")
                record("PDF 생성/렌더", smoke.get("pdf", {}).get("render", "SKIP"), str(smoke.get("pdf", {})))
        except Exception as exc:
            if "HWPX 읽기" not in checks:
                record("HWPX 읽기", "FAIL", str(exc), "python -m pip install python-hwpx==6.5.0")
            record("HWPX 편집", "FAIL", str(exc), "python -m pip install python-hwpx==6.5.0")
    hwp_pass = checks["HWP 변환"]["status"] == "PASS"
    level = 1 if basic else 0
    if basic and hwp_pass:
        level = 3 if smoke.get("pdf", {}).get("render") == "PASS" else 2
    result = {"ok": basic and (not args.require_hwp or hwp_pass), "level": level,
              "basic_output": "HWPX" if basic else None, "hwp_confirmed": hwp_pass,
              "additional_outputs": (["HWP"] if hwp_pass else []) + (["PDF"] if level == 3 else []),
              "checks": checks}
    if args.format != "json":
        print("검사 | 상태 | 설명 / 복구 명령")
        for name, value in checks.items():
            print(f"{name} | {value['status']} | {value['detail']}")
            if value["repair"] and value["status"] != "PASS":
                print("  ", value["repair"])
        print(f"기본 작업 가능: {result['basic_output']}; 현재 수준: Level {level}")
        print("추가 출력 가능:", " + ".join(result["additional_outputs"]) or "아직 미검증 또는 없음")
    if args.format != "text":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
