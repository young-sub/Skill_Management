# Luna / plugin 0.1.78 실제 비교 결과 — 2026-10-20

10개 과제 × 플러그인 OFF/ON × 3회, **60건을 실행하고 기록했다**.
공개 코딩 과제 성공은 양쪽 모두 **11/18(61.1%)**였다. 이 표본에서는
플러그인의 전반적인 해결률 향상을 입증하지 못했다. 설치·발견·훅 실행은
확인됐으며, 연속 작업의 실제 기능은 양쪽 모두 작동했다. 엄격한 연속 작업
점수 OFF 7/12, ON 6/12에는 문서 문구와 파일 읽기 인식 규칙이 영향을 줬다.

Feature: `benchmark-evaluation`. 플러그인 구현이나 평가 기준은 변경하지 않았다.
이전 [0.1.61/0.1.62 실험](luna-benchmark-execution.md)의 결과와 합산하지 않는다.

## 조건과 실행 범위

| 항목 | 이번 실행 |
| --- | --- |
| 모델 / reasoning | `gpt-6-luna` / `medium`; 78개 서로 다른 native thread의 선택 확인 |
| 호스트 | Codex CLI 0.160.0, 전용 WSL/Docker 및 ABC 후보 VM |
| 조건 | A=OFF, B=ON 0.1.78; 매번 새 격리 홈, 과제·반복별 AB/BA 교대, 직렬 실행 |
| 입력 | 고정한 자연어 과제; 후보에게 특정 Skill 호출을 강제하지 않음 |
| 제한 | 단위당 1,200초: 준비·전체 단계·중간 확인·산출물 수집 포함; 공식 채점은 별도 |
| 표본 | 공개 과제 6개와 내부 연속 작업 4개를 각각 3회 반복; 무작위·미사용 표본 아님 |
| 후보 격리 | private oracle, 자격 증명, 호스트 드라이브, Docker socket, 직접 외부 통신 미제공 |
| 기존 대조군 | 과거 24개 공식 positive/unchanged/defect control의 해시 재확인; 이번에 다시 실행한 24건이 아님 |

저장소 시작점은 clean `main@c9458bbe8362a429d55640632e4282655ba881bb`이다.
동결한 0.1.78 배포물의 `build-origin.json`은 별도로
`7ea0862769a04fbbec8bc1cde4c022378ca98e91`을 기록한다. 실행 저장소 커밋과
배포물 빌드 출처를 같은 것으로 취급하지 않는다. ZIP SHA256은
`336439c06d9ad0bf097d92846459339861b0a403b67080885f2cc52c9a4b767f`이다.
283개 내용 파일의 inventory가 원본 배포물과 일치했고, 완료된 ON 실행의
설치 후 해시도 동결본과 일치했다. 시간 초과 건의 사용 후 검증은 미완료다.
계획·실행 지원 파일 9개의 해시와 60건의 원본 증거 참조에 불일치는 없었다.

사용자는 격리 벤치마크 홈의 `UserPromptSubmit` 훅 신뢰를 명시적으로 승인했다.
실제 사용자 홈이나 전역 설정은 변경하지 않았다. 후보 모델의 대체 선택은 없었다.
기록된 성공 broker 요청 725개 중 723개에는 응답 모델 식별자도 있었고 모두
Luna였다. 나머지 2개의 응답 식별자는 미확정이며, 요청 모델과 native 선택은
Luna/medium이었다. 조정·준비 작업 사용량은 후보 사용량과 별도다.

## 공개 과제: 공식 평가 결과

각 셀의 분모는 3회다. 성공은 공식 평가기의 `resolved` 결과만 인정했다.

| 영역 | 과제 | OFF | ON 0.1.78 |
| --- | --- | ---: | ---: |
| FE / SWE-bench Multimodal | Carbon Dropdown 선택 항목 렌더링 | 0/3 | 0/3 |
| FE / SWE-bench Multimodal | Grommet UI 수정 | 3/3 | 3/3 |
| 일반 / FeatureBench | Metaflow stub generator | 2/3 | 3/3 |
| 일반 / FeatureBench | Astropy RGB mapping | 0/3 | 0/3 |
| BE / ABC-Bench | Express utility endpoints | 3/3 | 2/3 + 환경 시간 초과 1 |
| BE / ABC-Bench | Users API | 3/3 | 3/3 |
| 합계 | 18회/조건 | **11/18** | **11/18** |

OFF는 성공 11, 정상 채점 미해결 7이다. ON은 성공 11, 정상 채점 미해결 6,
미채점 시간 초과 1이다. 시간 초과를 분모에서 제거하지 않았다. 환경 영향을
받은 Azat 2회차 쌍을 양쪽에서 제외하는 보조 비교는 OFF 10/17, ON 11/17이다.
원래 점수를 대체하지 않으며, 이 작은 차이로 일반적 인과 효과를 주장하지 않는다.

Metaflow 2회차만 공식 결과가 ON 성공/OFF 미해결로 달랐다. 해당 ON 실행에는
인식된 Skill 본문 읽기가 없었다. Carbon은 6회 모두 자체 Dropdown 테스트
18개 통과를 보고했지만, 공식 `PublicAPI-test.js`와 `Dropdown-test.js`는 실패했다.
공식 보고서의 `infra_failure`는 모두 false다. 따라서 좁은 자체 검증과 실제
수락 기준 사이의 공백은 플러그인 ON에서도 남았다. Astropy의 일부 응답은
pytest 미실행 또는 남은 실패를 명시했다. 이를 전부 허위 통과 주장으로 묶지 않는다.

## 연속 작업: 엄격한 점수와 실제 동작

| 시나리오 | OFF 엄격 기준 | ON 엄격 기준 | 별도 실제 관측 |
| --- | ---: | ---: | --- |
| 상태·다음 행동 인계 | 2/3 | 3/3 | 첫 OFF의 차이는 다음 행동 enum; 양쪽 설명은 선행 browser flow 후 restart check |
| 중단 후 ledger 재개 | 3/3 | 3/3 | 모든 실행에서 1회 저장 후 실제 중단, 최종 2개 효과, 중복 시도 0 |
| UI 가이드·공유 소유자 재사용 | 1/3 | 0/3 | 양쪽 3/3, 총 12단계에서 UI runtime 기준 통과 및 실제 navigation 어두워짐 |
| 제품 연결 흐름·후속 변경 | 1/3 | 0/3 | 양쪽 3/3, 입력→API→Domain→SQLite→재시작→새 API·브라우저 조회 통과 |
| 합계 | **7/12** | **6/12** | 내부 fixture 결과이며 공개 벤치마크 점수와 합산하지 않음 |

UI 관측에는 두 화면의 공유 48px token, 실제 조작 영역, 링크 대비, 키보드
포커스와 navigation 일치가 포함됐다. 연결 흐름에서는 수량 2와 후속 수량 0을
저장하고 같은 ID·값을 재시작 후 다시 읽었다. 기존 guard 재사용·실행과 음수
거부도 모든 연결 과제에서 확인했다.

고정된 평가기의 한계는 원점수를 유지한 채 부가 분석으로 분리했다.

- 첫 인계 OFF의 `resolve-prerequisite-then-check`와 정답의 `run-registered-check`
  차이는 실제 다음 단계 설명과 구분해야 한다. 이 1건으로 인계 능력 개선을 주장하기 어렵다.
- UI 5건은 필수 파일 읽기를 인식하지 못했다. 첫 반복의 원본 명령에서는
  pipeline 뒤 `cat`이나 `rg` 내용 검색을 했는데 단순 shell parser가 누락한 사례를 확인했다.
  읽기 인식 실패 전체를 실제 미독으로 단정하지 않는다.
- ON UI 2회차는 공유 token·stylesheet·AppNav 소유자를 정확히 문서화했지만,
  코드의 `48px` 값을 가이드에 반복하지 않았다. 평가기는 literal `48px`도 요구해
  소유자 기준을 실패 처리했다. 실제 UI runtime은 두 단계 모두 통과했다.
- 연결 과제의 `project_evidence_reused`는 이전 증거 파일 자체의 재사용 여부가
  아니라, UI guide를 포함한 6개 파일 읽기와 두 명령의 인식을 요구한다.
  마지막 OFF만 이 기준을 충족했다. 나머지 5건도 실제 저장·재조회·guard는 통과했다.

## 플러그인 작동과 효율

OFF의 plugin Skill 발견은 0개, ON은 22개였다. ON native 39단계의 훅이 모두
완료됐고 훅 실패는 0이었다. 본문 읽기로 인식된 사용은 ON **5/30건**이었다:
Carbon 2회차, UI 2회차, 연결 흐름 3회. UI 2회차에서는 `agent-workflow`,
`impeccable`, `fixing-accessibility`를 읽었다. 공개 ON에서는 1/18건이다.
이는 읽기 명령 인식 휴리스틱이므로 나머지를 모든 형태의 미사용으로 확정하지 않는다.
발견·훅 실행·본문 사용·기능 성공은 서로 다른 증거다.

| 측정치 | OFF | ON |
| --- | ---: | ---: |
| 30건 agent unit 누적 시간: 준비·실행·내부 확인 포함 | 106.6분 | 122.6분 |
| agent unit 중앙값 | 127.5초 | 140.3초 |
| 별도 공식 채점 누적 시간 | 86.5분 / 18건 | 79.6분 / 17건 |
| 전체 단위 누적 시간: 채점·수집 포함 | 193.4분 | 202.5분 |
| 기록된 입력 토큰 | 8,500,738 | 8,680,433 + 미확정 1단계 |
| 입력 중 cache 토큰 | 3,168,384 | 3,343,232 + 미확정 1단계 |
| 기록된 출력 토큰 | 108,673 | 150,851 + 미확정 1단계 |
| 사용량 확인 단계 | 39/39 | 38/39 |
| 실제 비용·크레딧 | 미확정 | 미확정 |

cache 토큰은 입력에 이미 포함된다. 준비·조정·preflight 사용량을 위 숫자에
포함하지 않았다. ON의 관측 agent unit 누적 시간은 약 15% 길지만 환경 중단과
과제별 편차가 있어 플러그인 고유 지연으로 볼 수 없다. ABC 공식 평가에는
이미지 다운로드, npm/yarn/apt, 앱 준비가 포함돼 외부 의존성과 시간은 완전 고정되지
않았다. ON Astropy 3회차 하나의 입력만 약 126만 토큰이었다. 비용을 0으로 추정하거나
이 기록으로 청구 금액을 환산하지 않았다.

## 실패·복원·남은 한계

29번 ON Azat은 약 1,195초 후 시간 초과됐다. 다음 OFF 실행 중 전용 Docker
parent와 원래 broker cgroup이 다시 동결된 것을 발견했다. 동결 주체·정확한 시작
시각은 모른다. 소유권 확인 후 해당 broker만 재개했고 30번 OFF는 이어서 성공했다.
29번 재시도는 하지 않았으며, 두 건은 환경 영향 표시를 남겼다.

29번 상위 기록의 빈 phase 배열 때문에 activation이 `NO_PLUGIN_SKILLS_DISCOVERED`,
broker 수집이 `UNKNOWN_CANDIDATE_NOT_CONFIRMED_STOPPED`로 표시됐다. 원본 native
결과에는 22개 발견·Luna/medium 선택·훅 완료가 있고, unit에는 VM 종료 및
`candidate_containment_stopped=true`가 있다. 부가 감사는 이를 대조하지만
원본 실패 기록과 알 수 없는 사용량을 수정하지 않는다.

준비 중 package inventory 자기 포함 오류와 preflight 시간 초과도 별도 보존했다.
성공한 OFF/ON preflight 후 본 실험을 시작했으며, 실패 preflight를 성공으로
계산하지 않았다. 계획 설명의 선택 방식·승인 상태 오기는 별도 정정 기록으로 남겼고
과제 ID·프롬프트·실행 순서·제한은 중간에 바꾸지 않았다.

60건 종료 후 후보 VM·컨테이너와 matrix가 멈춘 것을 확인했다. 원래 broker만
남은 상태에서 시작 전 parent/broker 동결값을 복원했고, 기존 Docker·broker·private
grader 프로세스를 보존했다. 원본 자료는 삭제하지 않았다. 사용자 설치본·전역 설정·
다른 제품·기존 readiness Goal·보호된 main 통합·push는 이 작업의 변경 대상이 아니다.

다음 비교 전에는 읽기 인식과 문서 literal을 기능 기준과 분리한 평가기를 별도로
검증하고 새 버전으로 동결하는 것이 우선이다. 이후 자연어 발견과 명시적 Skill
호출을 분리하고, 독립적인 새 과제로 검증해야 한다. 이번 실행만으로 모든 Skill,
실서비스 배포 품질, 일반적인 성능 향상이나 비용 절감을 주장할 수 없다.

## 재현·증거 위치

원본은 `.work/luna-0178-20261019/`에 보존했다. 저장소의 임시 증거 보존 정책을
따르며, 문서의 수치는 아래 실행별 기록에서 집계했다.

- `plan.json`, `support-manifest.json`, `hook-authorization.json`: 입력·패키지·승인 고정.
- `main/trials/*/run-record.json`, `unit/result.json` 또는 `unit/phase-*/result.json`,
  native trace, `official/capture.json` 및 원본 evaluator report: 실행별 증거.
- `summary.json`, `audit.json`, `audit-results.py`: 60개 고유 셀, 78개 고유 thread,
  모델·제공자 metadata·패키지·원본 해시 대조 및 시간·사용량 집계.
- `diagnose-ui.py`, `ui-diagnostics.jsonl`, `continuous-phase-*.json`: 원점수를
  변경하지 않은 UI·연속 작업 해석.
- `refreeze-recovery.json`, `freezer-restored.json`: 환경 중단과 최종 복원.

보고서 연결·소유권 검사 `python -m unittest tests.distribution.test_repository_docs`의
4개 테스트와 `git diff --check`가 통과했다. 배포 코드 변경이 없어 전체 런타임
회귀 검사는 이번 보고서 작업에서 다시 실행하지 않았다.
