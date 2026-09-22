# 설치와 환경 단계

## 지원 버전

Python 3.10 이상. 2026-09-22 확인한 hwpx-plugin 2.3.0의 지원 범위는 core `>=6.5.0,<7`, automation `>=7.2.0,<8`이다. 본 스킬은 `python-hwpx==6.5.0`으로 검증했다. 공개 패키지와 설치된 스킬의 `references/api.md`를 확인했으며 최신 버전을 추측하지 않았다.

- [python-hwpx 6.5.0 공개 패키지](https://pypi.org/project/python-hwpx/6.5.0/)
- [공식 소스와 API](https://github.com/airmang/python-hwpx)
- [automation 7.2.0 공개 패키지](https://pypi.org/project/python-hwpx-automation/7.2.0/)

추가 라이브러리는 이 환경에서 검증한 `python-docx==1.2.0`, `pywin32==312`, `PyMuPDF==1.28.2`로 고정한다. 다른 Python/OS용 배포본이 없으면 공식 지원 범위에 맞춰 호환 버전을 검증한다. core만으로 기본 작업을 끝낼 수 있다. 추가 형식 라이브러리는 해당 입력에 필요할 때만 설치한다.

## 스킬 설치

공유받은 `hwp-form-fill` 폴더의 **상위 디렉터리**에서 실행한다. 동일 이름이 있으면 중단하고 내용을 비교한다. 사용자 변경을 덮어쓰지 않는다.

Windows PowerShell:

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex/skills' }
$skillTarget = Join-Path $skillRoot 'hwp-form-fill'
if (Test-Path -LiteralPath $skillTarget) { throw '기존 스킬을 먼저 비교하세요.' }
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -LiteralPath ./hwp-form-fill -Destination $skillTarget -Recurse
```

macOS/Linux:

```sh
skill_root="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skill_root"
test ! -e "$skill_root/hwp-form-fill" && cp -R ./hwp-form-fill "$skill_root/"
```

호스트가 새 스킬을 발견하지 못하면 새 세션에서 `$hwp-form-fill`로 호출한다.

## Level 1 — 필수 HWPX 기본 작업

HWPX 읽기·구조 분석·편집·생성·구조 검증이 가능하다. Python과 프로젝트 가상환경, python-hwpx만 필수다. DOCX를 읽을 때 python-docx를 추가한다. 정상 가상환경은 재생성하지 않는다. 아래 명령은 **스킬 폴더 안**에서 실행한다. `.hwp-form-work`는 전용 작업 디렉터리이며 배포에 넣지 않는다.

Windows PowerShell:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
$OutputEncoding=[System.Text.UTF8Encoding]::new()
python -m venv .hwp-form-work/.venv
& ./.hwp-form-work/.venv/Scripts/python.exe -m pip install 'python-hwpx==6.5.0' 'python-docx==1.2.0'
& ./.hwp-form-work/.venv/Scripts/python.exe scripts/doctor.py
```

macOS/Linux:

```sh
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
python3 -m venv .hwp-form-work/.venv
.hwp-form-work/.venv/bin/python -m pip install 'python-hwpx==6.5.0' 'python-docx==1.2.0'
.hwp-form-work/.venv/bin/python scripts/doctor.py
```

DOCX가 없으면 python-docx는 생략 가능하다. XLSX가 필요할 때만 해당 가상환경에서 `python -m pip install openpyxl`을 실행하고 설치 버전을 기록한다. CSV/Markdown/텍스트는 표준 라이브러리로 읽는다. PDF는 Level 3의 PyMuPDF를 재사용한다.

## Level 2 — 선택 HWP 변환

Windows, 한컴오피스 설치, `HWPFrame.HwpObject` COM 등록, pywin32가 필요하다. 실제 HWP 저장과 한컴 재열기가 추가된다. 실행 파일 전체 검색보다 **COM ProgID/레지스트리부터** 확인한다.

```powershell
& ./.hwp-form-work/.venv/Scripts/python.exe -m pip install 'pywin32==312'
& ./.hwp-form-work/.venv/Scripts/python.exe -c "import winreg; k=winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,r'HWPFrame.HwpObject\CLSID'); print(winreg.QueryValueEx(k,None)[0])"
& ./.hwp-form-work/.venv/Scripts/python.exe scripts/doctor.py --smoke-test --require-hwp --timeout 240
```

미등록이면 정상 한컴오피스 설치/복구로 자동화 구성요소를 준비한다. 임의 CLSID나 검증되지 않은 레지스트리 수정을 하지 않는다. COM 등록만으로 변환 가능 판정을 하지 않는다. 파일 접근 확인 창은 정상 제품 절차로 처리하고 보안 설정을 임의로 해제하지 않는다.

최초 실행은 수십 초 이상 출력 없이 대기할 수 있다. 기본 제한은 **240초**이며 짧은 무응답으로 중단하지 않는다. 실패 시 원인을 기록하고 무한 재시도하지 않는다. 전용 DispatchEx 인스턴스만 Quit한다. 제한 초과 시 Python worker만 종료하며 모든 `Hwp.exe`를 종료하지 않는다. 남은 COM 서버는 사용자 세션과 구별되지 않은 상태로 종료하지 않는다.

doctor 기본 실행은 한컴을 시작하지 않는다. `--require-hwp`는 실제 PASS를 요구하므로 `--smoke-test --require-hwp`를 함께 쓴다. HWP 환경이 없는 OS에서도 Level 1은 성공한다.

## Level 3 — 선택 시각 검수

한컴 PDF 저장 기능 또는 **로컬** HWPX 렌더러, PDF 페이지 렌더링 라이브러리가 필요하다. PDF 라이브러리 설치만으로 HWPX→PDF가 가능해지는 것은 아니다.

```powershell
& ./.hwp-form-work/.venv/Scripts/python.exe -m pip install 'PyMuPDF==1.28.2'
& ./.hwp-form-work/.venv/Scripts/python.exe scripts/doctor.py --smoke-test
```

macOS/Linux: `.hwp-form-work/.venv/bin/python -m pip install 'PyMuPDF==1.28.2'`. 다른 렌더러는 실제 로컬 동작과 충실도를 확인한 경우만 사용한다. PDF·이미지는 전용 임시 디렉터리에 저장한다. 생성/렌더 PASS는 실제 페이지 관찰 PASS와 다르다.

## 플러그인과 MCP 상태

설치된 hwpx 스킬과 참조를 읽고 **현재 세션 도구 목록**에서 health/capabilities를 찾는다. 노출되면 `mcp_server_health`의 `pythonHwpxVersion`, `toolSurface.status`, `missingKeyTools` 및 `describe_capabilities` 응답을 확인한다. 폴더·설정 파일 존재만으로 성공이라고 기록하지 않는다.

MCP 미노출·오류이면 로컬 core로 진행한다. canonical mixed-form API가 필요한 경우 설치된 automation을 재사용한다. 없다면 다음은 선택 설치이며 호스트 세션에 MCP를 노출시키는 명령은 아니다:

```text
python -m pip install "python-hwpx==6.5.0" "python-hwpx-automation==7.2.0"
```

플러그인 연결/복구는 설치된 플러그인 안내를 따른다. 이 스킬은 전역 설정을 자동 변경하지 않는다.

## 종료 코드와 자체 검사

기본 환경 정상 → 0. 선택 HWP 부재 → SKIP와 0. 기본 환경 실패 또는 `--require-hwp`의 HWP 미검증/실패 → 1. 기본 출력은 표+JSON, `--format json`은 JSON만이다.

```text
python scripts/test_workflow.py
python scripts/convert_and_validate.py --help
```

자체 검사는 COM 불가와 SaveAs 실패를 모의하여 세 모드와 원본 보존을 검사한다. 실제 Windows 변환 증거를 대신하지 않는다.

스킬 제작자가 메타데이터도 재검증할 때는 skill-creator의 `quick_validate.py`를 사용한다. 해당 검사에만 PyYAML이 필요하며 문서 작업 런타임 의존성은 아니다. Windows에서는 `python -X utf8 <skill-creator>/scripts/quick_validate.py <hwp-form-fill>`처럼 UTF-8 모드로 실행한다.
