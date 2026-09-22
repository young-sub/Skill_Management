# 양식 작성 절차

## 입력 확인과 원본 보존

원본 양식 경로, 참고 자료 경로, 결과 파일명/디렉터리, 작성 기준일/대상 기간, 사용자 직접 값, 보존할 로고·서식·예시·페이지, HWP 필요 여부를 구분한다. 명시된 값은 재질문하지 않는다. 현재 날짜를 작성일로 추정하지 않는다.

HWPX는 항상 생성한다. HWP 필요 여부가 없어도 가능한 환경이면 함께 만들 수 있다. 불가능하면 HWPX만 주고 한 줄로 이유를 보고한다. HWP 가능 여부를 묻느라 작업을 중단하지 않는다. HWP 불필요 지시에는 `off`, 변환 성공을 명시적 필수로 요구한 경우만 `required`를 쓴다.

편집 전 원본 SHA256을 기록하고 결과를 새 경로에 쓴다. 참고 자료와 기존 결과도 변경하지 않는다. 나중에 계산한 hash를 baseline으로 대체하지 않는다.

```powershell
$sourceHash = (Get-FileHash -LiteralPath $templatePath -Algorithm SHA256).Hash
```

전용 작업 디렉터리에 매핑·검수 파일을 두고 스킬 패키지에는 사용자 문서/내용을 넣지 않는다. HWP 양식이면 로컬 한컴 `Open(..., 'HWP', '')`와 `SaveAs(..., 'HWPX', '')`로 별도 중간 HWPX를 만든 뒤 검증한다. core는 HWP 바이너리를 읽지 못한다. 한컴이 없으면 기존 로컬 HWP 읽기 도구로 참고 텍스트는 추출할 수 있으나 양식 보존을 보장하지 않는다. 양식을 변환할 방법이 없을 때만 HWPX 사본을 요청한다. 확장자 변경으로 우회하지 않는다.

## 참고 자료 읽기

정본이 지정되면 우선한다. 같은 사실이 중복된 경우 구조 손실이 적은 HWPX → DOCX → PDF → XLSX → CSV → Markdown → 일반 텍스트 순서로 읽되 관련 자료를 대조한다. 이 순서는 모순된 사실의 우선권이 아니다.

| 형식 | 로컬 읽기 우선 경로 | 근거 위치 |
|---|---|---|
| HWPX | 정상 MCP의 extract/text; 대안 `HwpxDocument.open`, `doc.text.plain()` | section·문단·표 논리 좌표·필드 |
| DOCX | 기존 ingest 또는 `python-docx.Document`의 본문·표·머리글·바닥글 | 제목·문단 번호·표 행/열 |
| PDF | 기존 로컬 추출기 또는 `pymupdf.open`, `page.get_text()` | 페이지·영역 |
| XLSX | 기존 ingest 또는 `openpyxl.load_workbook(read_only=True, data_only=True)` | 시트·셀 |
| CSV | 표준 `csv.DictReader`, `utf-8-sig`; 다른 인코딩은 확인 | 행·열 |
| Markdown/텍스트 | `Path.read_text(encoding='utf-8')` | 제목·줄 |
| HWP | 한컴에서 별도 HWPX 변환 또는 기존 로컬 추출기 | 원본과 중간 파일 위치 대응 |

PDF 스캔은 로컬 OCR/페이지 관찰이 필요하다. XLSX 수식 캐시는 누락·노후화 가능하므로 산식도 확인한다. DOCX 텍스트 상자·이미지·추적변경은 paragraphs에 빠질 수 있어 필요한 정보는 XML 읽기 또는 로컬 렌더로 보완한다.

사실과 에이전트 요약/해석을 구분한다. 진척률·담당자·작성일·완료일·상태·금액·승인 여부·기관명은 근거 없이 만들지 않는다. 문서 버전 날짜를 업무 완료일로 추정하지 않는다. 유일하고 명확하면 적용하고 여러 후보가 결과를 크게 바꿀 때만 질문한다. 기존 결과 예시의 값도 무조건 사실로 재사용하지 않는다.

## 양식 분석

표 개수, 각 표의 논리 행/열, 모든 논리 셀의 병합 anchor/span, 누름틀, 본문 placeholder, 빈 입력 영역을 조사한다. 예시 페이지·작성 안내·샘플 값·로고/이미지·머리글·바닥글·숨은 빈 문단·페이지 나눔도 확인한다. 뒤쪽 예시를 빠뜨리지 않는다.

**물리적 셀 개수와 화면의 논리 열 개수는 다를 수 있다.** core 6.5 예:

```python
from hwpx import HwpxDocument

with HwpxDocument.open(template_path) as doc:
    for table_index, table in enumerate(doc.tables):
        print(table_index, table.row_count, table.column_count)
        for position in table.iter_grid():
            print(position.row, position.column, position.anchor,
                  position.span, position.cell.text)
```

`doc.tables`는 iterable namespace다. 인덱스 접근은 `list(doc.tables)`로 한다. 여러 논리 위치가 같은 anchor를 가리키면 한 번만 쓴다. 구조 충돌을 물리 번호로 우회하지 않는다.

MCP에서는 `get_document_map`의 생략 여부까지 확인한다. 누름틀·라벨 셀·canonical path·body anchor 혼합 채움은 설치된 hwpx `workflows-forms.md`/generated contract의 `analyze_form_fill` → `apply_form_fill` → `verify_form_fill`을 재사용한다. 대상 모호성은 저장 전에 해결한다. 명확한 사용자 요청을 재승인받을 필요는 없다.

## 매핑과 작성

내부 매핑:

`대상 필드/논리 anchor | 값 | 근거 파일·위치 | 사실/요약·형식 변환 | 확정 여부 | 적용 방법 | 검증 방법`

정확한 셀/필드를 다시 읽어 검증한다. 문서 어딘가에 문자열이 있다는 것만으로 올바른 셀에 들어갔다고 볼 수 없다. 보존 영역의 값·구조·이미지 참조도 비교한다. 맞지 않는 기관 로고나 샘플은 제거 후보이며, 작성 영역과 명확히 구분되고 보존 지시가 없을 때만 제거한다. 불명확하면 유지하고 질문한다.

MCP 정상 시 canonical mixed-form 계획의 dry-run diff/대상/revision을 확인하고 한 트랜잭션으로 저장한다. commit 재시도 외에는 idempotency key를 재사용하지 않는다. 지원하지 않는 인자를 추측하지 않는다.

MCP가 없으면 로컬 python-hwpx를 쓴다. 설치된 automation이 있으면 canonical API를 재사용한다. core만 있으면 확인한 논리 셀과 본문/필드 API로 한 문서 객체에서 변경을 모으고 별도 임시 HWPX에 한 번 저장·검증한 뒤 새 결과로 확정한다. 복잡한 누름틀은 실제 `doc.fields` API/소스를 확인해 사용하고 XML 직접 패치 엔진을 만들지 않는다.

```python
from hwpx import HwpxDocument

# edits: 분석으로 확정한 (표 index, 논리 행, 논리 열, 값) 목록
# staging_path: 원본/기존 결과와 다른 새 임시 파일
with HwpxDocument.open(template_path) as doc:
    tables = list(doc.tables)
    for table_index, row, column, value in edits:
        tables[table_index].set_cell_text(
            row, column, value, logical=True, preserve_format=True)
    receipt = doc.save_to_path(staging_path, mode='patch', fallback='error', return_report=True)
    if not receipt.ok:
        raise RuntimeError('저장 검증 실패')
```

patch/error는 미수정 part 보존을 요구한다. 실패 시 무단 rebuild로 보존 수준을 낮추지 않는다. 전체 문단 text 설정은 여러 run 서식/필드를 합칠 수 있어 최소 API로 수정한다. 저장 receipt는 내용 충족이나 시각 검수를 대신하지 않는다.

## HWPX 필수 검증

검증 스크립트는 ZIP CRC, XML/HPF/RDF 파싱, core의 필수 part·관계 검사, `validate_editor_open_safety`, `HwpxDocument.open` 재열기, 양수 파일 크기를 확인한다. expected/forbidden은 반복 지정한다. 원본 hash는 편집 전 값과 비교한다.

```powershell
python scripts/convert_and_validate.py $resultPath --hwp off --expect $expectedText --forbid $exampleText --source $templatePath --source-sha256 $sourceHash
```

`hwpx.open_safety.validatePackage.ok`, `hwpx.open_safety.ok`, `hwpx.open_safety.reopen.ok`, `source_unchanged`, `input_unchanged`, `command_ok`를 확인한다. 필수 항목의 빈 값·누락과 정확한 대상 값은 별도로 대조한다. 문자열 검사에서 개행/공백 차이가 있으면 추출 결과를 조사한다. 조건을 빼서 실패를 숨기지 않는다. 미지정 항목의 SKIP을 PASS로 세지 않는다.

오류를 수정한 뒤 재검사하고 경고도 보고한다. **구조 통과는 페이지 배치 정상 판정이 아니다.**

## 선택 HWP 변환

기본 `auto`는 Windows·pywin32·COM 등록 확인 후 실제 한컴 시작·HWPX Open 성공 시 `SaveAs(..., 'HWP', '')`를 수행한다. 기본 240초 제한은 조정 가능하다.

```powershell
python scripts/convert_and_validate.py $resultPath --hwp auto --output-dir $newOutputDir --pdf --render-dir $newImageDir --expect $expectedText --source $templatePath --source-sha256 $sourceHash
```

HWP의 양수 크기/OLE 시그니처 `D0 CF 11 E0 A1 B1 1A E1`와 한컴 재열기를 확인한다. PDF는 원래 HWPX를 다시 열어 저장하므로 HWP 저장 실패와 독립적으로 시도한다. `off`는 이 스크립트의 COM/PDF도 끈다. 이 경우 별도 로컬 렌더러가 있으면 활용한다.

`auto` 실패는 `HWP 변환: SKIP`·이유·설치 조건을 남기고 HWPX 성공을 유지한다. `required`만 명령 전체를 실패시킨다. 기존 HWP/PDF가 있으면 새 출력 폴더를 사용한다. 원본과 정상 HWPX는 손상시키지 않는다. ZIP의 확장자만 바꾼 가짜 HWP는 만들지 않는다. 원인을 해결한 경우만 한 번 더 시도하며 무한 재시도하지 않는다.

임시는 tempfile 전용 디렉터리에만 만든다. 실패 partial만 정리하고 사용자 한컴 프로세스나 모든 `Hwp.exe`를 종료하지 않는다. 잠긴 잔여 임시는 경로를 보고하고 사용자 파일까지 정리 범위를 넓히지 않는다.

## 시각 검수와 전달

렌더러가 있으면 **모든 페이지 이미지**를 실제로 연다. PDF 페이지 수/렌더 성공과 다음 관찰을 구분한다:

- 잘린/겹친 텍스트, 셀 밖 내용, 불필요한 빈 페이지
- 예시 페이지·샘플 값 잔존, 잘못된 로고
- 부자연스러운 줄바꿈, 제목과 표 위치, 머리글과 바닥글

이미지별 관찰과 HWPX 해시를 검수 기록에 연결한다. 수정 후 재생성하면 모든 페이지를 다시 확인한다. hwpx 도구의 visual evidence 계약도 준수한다. renderer/폰트 충실도 한계가 있으면 보고한다. 렌더러가 없으면 구조·내용까지만 검증했다고 명시한다.

필수 전달: 별도 HWPX, 구조/open-safety/재열기/내용 검사, 원본 불변 확인, 수행/미수행 검증 구분. 환경이 지원할 때만 실제 HWP·검수 PDF·페이지 이미지를 추가한다. HWP/PDF 부재로 정상 HWPX를 폐기하지 않는다.
