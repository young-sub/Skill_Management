# 0.1.78 실험 후 로컬 개선

기준은 clean `wp-20261020-luna-0178-results@efa89a04ea8f81794d6b3b7312416d43363ed32e`다.
기존 [60건 실험](luna-0.1.78-benchmark-results.md)은 다시 실행하거나 재채점하지 않았다.
새 구현은 로컬 0.1.79 후보이며 설치·전역 설정·readiness Goal·main·원격을 변경하지 않는다.
Feature: `workflow-obligations`, `verification-results`, `agent-workflow`, `plugin-package`.

## 구현

- 훅은 명시 context를 먼저 검증한다. 미선택 요청은 최대 8개 후보의 메타데이터만 읽으며
  inventory와 다른 active work 감사를 실행하지 않는다. 전체 감사는 기존 명시 CLI에 남긴다.
  선택된 작업의 영향·freshness 판정은 기존 audit owner를 사용한다.
- 출력은 task acceptance, blocker, 다음 행동, 분모와 정확한 lookup 참조를 우선한다.
  선택되지 않은 프로젝트 상태는 `NOT_AUDITED`다. 큰 조사 결과를 줄여도 남은 항목 수를 유지한다.
  미설정 개발 요청에는 기존 AGENTS/프로젝트 가이드/호출부/테스트 탐색을 안내한다.
  새 미설정 비개발 요청에는 문맥을 추가하지 않는다. 문구 분류는 발견 힌트이며 작업 선택·권한이 아니다.
- assertion의 `source_scope: registered`는 검토된 소스/의존 범위에 대한 명시적 opt-in이다.
  기존 소스 pattern과 공유 UI owner를 바인딩하며 동일 check의 소비자는 소스 합집합을 사용한다.
  관련 변경·새 matching 파일·삭제는 해당 체크를 stale로 만들고 다음 prepare가 그 체크만 선택한다.
  오래된 current-context를 직접 제출해도 실제 소스를 다시 읽는다.
  기존 등록 정보는 의존 파일을 빠뜨릴 수 있으므로 미설정 체크의 전체 Git 보호는 유지한다.
- 선택 audit의 bases를 같은 호출의 connected lookup에 전달한다. 같은 조건 비교의 중복 호출을 제거한다.
  영속 캐시는 추가하지 않았다. Skill 진입점은 프로젝트 가이드→관련 코드→남은 필요에 대한 절차 순으로
  읽도록 바꾸고, 큰 보고서는 summary와 해당 관측부터 읽도록 연결했다.
  접근성·UI 기준·연결 흐름 검증을 생략하는 규칙은 추가하지 않았다.

## 훅 전후 측정

동일 Windows 호스트, 30개 Feature·12개 active work를 가진 임시 Git fixture,
각 조건 7회, 동일 측정 스크립트를 사용했다. 기준 훅은 변경 전 원문을 사용한다.
아래 시간은 이미 로드된 Python 프로세스 안의 `context()`이며 호스트 시작·모델 추론 시간을 제외한다.
p95는 7개 표본의 nearest-rank 값(최댓값)이다. OS 파일시스템 호출 전체가 아닌
Python `Path.read_text/read_bytes`와 subprocess Git 호출을 센다. 모든 조건에서 product 명령과 상태 변경은 0이다.

| 요청 | p50 ms 전→후 | p95 ms 전→후 | 파일 읽기 전→후 | Git 전→후 | 문맥 UTF-8 bytes 전→후 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 설정됨, 조회, 미선택 | 639.3→96.9 | 664.9→104.0 | 183→16 | 6→1 | 2,659→1,766 |
| 설정됨, 변경, 미선택 | 689.1→94.5 | 704.0→100.8 | 183→16 | 6→1 | 2,659→1,766 |
| 명시 task, 변경 | 471.5→287.6 | 487.8→292.8 | 124→92 | 4→4 | 5,261→2,804 |
| 새 미설정, 개발 | 24.2→24.5 | 25.0→26.4 | 1→1 | 1→1 | 0→451 |
| 새 미설정, 비개발 | 24.0→24.0 | 25.7→24.3 | 1→1 | 1→1 | 0→0 |

기존 후보가 남은 미설정 개발 요청은 417→753 bytes로 증가한다. 이전에 없던 fallback을
전달하는 비용이다. 모든 요청에서 문맥이 줄었다거나 일반적인 모델 성능/비용이 개선됐다는 결과가 아니다.
Skill 본문 반복 읽기와 모델 token 절감에 대한 새 유료 비교는 실행하지 않았다.

동일한 실제 실행 bundle을 변경 전/후 viewer에서 다시 읽은 로컬 소비에서는
현재 조건 비교가 2→1회(전체 조건 비교 3→2회)로 줄었다.
양쪽 모두 PASS였고 product 명령·파일 변경은 0이었다.
범위 바인딩용 Git 파일 목록 수집은 별도 비용이므로 모든 viewer 호출이 더 빨라졌다고 주장하지 않는다.

## 검증과 증거

새 증거는 `.work/luna-improvements-20261020/`에 보존한다.

- `measure.py`, `workflow_context-before.py`, `before-frozen.json`, `after-frozen.json`:
  fixture, 원문, 각 표본과 실제 출력. 앞선 측정도 덮어쓰지 않았다.
- `hook-first-tests.log`: 최초 관련 121개 검사. 바뀐 훅 계약의 기존 기대값 3개와
  긴 조사 결과의 분모 누락 1개를 발견했다. 기대값을 바꾸면서 기존 full audit의 검증은
  명시 경로에 남겼고, 분모 누락은 출력 owner에서 수정했다.
- `hook-regression-final.log`: 관련 출력 압박·요청 모드 10개 통과.
  `workflow-core-capture.json`: TaskStore/API/최종 훅 관련 14개 통과.
- `workflow-final-capture.json`: 기본 300초 capture 제한에 걸린 미완료 시도.
  timeout의 `taskkill`은 Access denied였으며 종료된 부모 PID를 확인하고
  남은 프로세스 소유권을 대조한 뒤 재실행을 분리했다. 이 시도를 PASS로 세지 않는다.
- `workflow-complete-capture.json`: 최종 소스의 훅/작업 흐름/TaskStore/API 130개 통과.
- `binding-complete-capture.json`: 최종 소스의 결과 조회/실행/standalone capture 79개 통과.
- `guidance-regression-capture.json`: 리소스 동기화/문서/설치 전환 24개 중 22개 통과,
  설치 전환 2개 실패. `base-cutover-capture.json`은 변경 전 `efa89a0`를 별도 추출하여
  같은 2개 실패를 재현한다. 기존 `run_check.py` 설치 허용 목록 불일치이며 이번 수정으로
  생긴 실패가 아니다. 설치 전환 owner는 변경하지 않았다.
- `binding-red.log`, `binding-green.log`, `binding-focused.log`, `binding-critical*.log`:
  관련 변경 binding의 재현, 수정, 기존 입력 보호의 발견 및 후속 검증.
  실패 시도는 성공으로 치환하지 않았다.
- `measure-reuse.py`, `reuse-measurements.json`, `condition-consumer/`:
  동일 실제 bundle의 전후 조건 비교 횟수와 원본 실행/capture.
- `package-consumption-capture.json`: 15개 검사 통과. 저장소 밖 패키지의 실제
  shell 훅에서 두 host-root 변수로 개발 fallback과 비개발 무출력을 소비하고
  입력 보존을 확인했다. 이는 native host 자동 호출이나 모델 준수 증거가 아니다.
- `connected-capture.json`: 실제 연결 제품 회귀 3개 통과.
  입력→API→Domain→SQLite→재시작→새 조회, FE payload 결함 검출,
  공유 UI 스타일/키보드 포커스와 실제 브라우저 산출물을 확인했다.
- `preservation-before.json`: 기존 실험 manifest의 67개 해시 확인 및
  readiness 파일 4개 보존 기준.
- `preservation-after.json`: 위 71개 파일 해시가 모두 같음을 재확인했다.
- `resource-drift-final.log`, `distribution-final.log`: 생성 리소스 및 배포 정적 검사 통과.

훅 첫 구현 커밋은 `6d4afea`, 검증 바인딩·읽기 지침·생성 리소스의 소스 커밋은
`91675aeae2ba4ee0c66b9f89b0496d0598d4bc6c`다.
해당 clean 소스에서 `frozen-package/`의 284개 파일을 생성했다.
기존 marketplace의 원본은 `previous-marketplace-0.1.78/`에 보존하고
`plugins/agentic-coding/`만 동일한 생성 바이트로 갱신했다.

- `frozen-package-capture.json`: plugin-package selector 20개 통과.
  두 catalog, 생성 패키지 일치, 격리된 update/global guidance fixture 및
  실제 패키지 실행/조회·shell 훅 소비를 포함한다. 실제 설치본에는 적용하지 않았다.
- `frozen-hook-consumption.json`: 동결 패키지 자체의 shell 훅을 두 root 변수로
  호출한 개발/비개발 4개 소비 통과. 소비 저장소와 패키지 바이트는 그대로다.
- `package-freeze.json`: 소스 커밋, 변경 파일 목록, inventory와 ZIP SHA-256.
  `agentic-coding-0.1.79-frozen.zip`의 SHA-256은
  `c6776fcb3c5154f2fa2be2599b8a152bd5246a351f4e3671895eefa315fce313`이다.

## 한계

미설정 개발 문구 인식은 영문/한국어의 작은 발견 휴리스틱이며 자연어 의도 판정기가 아니다.
소스 범위 opt-in은 등록 owner와 의존성이 완전하다는 프로젝트 검토를 필요로 한다.
일반 직접 작업에는 완료를 강제로 차단하는 호스트 기능을 추가하지 않았다.
브라우저 검증은 프로젝트의 Playwright 경로를 사용했고, 비활성 in-app browser는 재시도하지 않았다.
패키지 실행, native host의 자동 전달, 모델의 무도움 사용·해결률은 서로 다른 증거다.
전체 저장소 테스트는 실행하지 않았다. 추가 검사에서 확인한 기존 설치 전환 2개 실패는 남아 있다.
새 유료 비교, 설치본 업데이트, hook trust 변경, push/publish는 이 로컬 개선 범위에 없다.
