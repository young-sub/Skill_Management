# 0.1.81 실행·관찰 연결 개선

시작점은 clean `a3d1b96`, 작업 branch는 `wp-20261020-luna-0178-results`다.
[현재 설계](agent-coding-system-direction.md)의 V1–V6 중 실제 구현·관찰한 범위만 기록한다.
원본은 `.work/runtime-verification-20261021/`에 보존하며 이전 실패·패키지를 덮어쓰지 않았다.

## 구현과 시나리오

| 항목 | 변경 / 재사용 | 실제 관찰과 한계 |
| --- | --- | --- |
| V1 | 예제의 브라우저 패키지를 프로젝트 경로에서 먼저 찾고 부재일 때만 기존 전역 npm을 사용. 공통 setup 가이드에 실행·관찰 도구, 대상, 역할/데이터, 근거와 정리를 연결. | 수정 전 프로젝트 패키지가 있어도 npm 부재로 실패. 수정 후 npm 없이 Node의 실제 로컬 모듈 해석 성공. Node 부재는 서비스 실행 없이 BLOCKED. |
| V2 | 예제 readiness에서 소유 process, checkout, 시작 시 소스 해시와 DB 경로를 대조하고 재시작 후 재확인. 공통 가이드에는 같은 책임을 프로젝트 launch/doctor에 연결. | 다른 정상 서버를 수용하던 RED 재현. 수정 후 다른 서버·위조 launch PID·다른 DB·시작 후 소스 변경 거부, 정상 복원 허용. |
| V3 | 기존 fixture의 FE/API/Domain/SQLite 흐름을 실제 실행. 실제 제품은 아직 지정되지 않음. | 양수/0 저장, 음수 거부·무변경, 재시작 후 fresh read, API 검사가 놓치는 FE 전송 결함 검출. 실제 제품·운영 권한 검증 완료가 아님. |
| V4 | 기존 공유 UI 기준과 실제 화면·키보드 관측을 재사용. | 정상 token 변경 허용, History 포커스 결함 검출. 새 문맥의 패키지 소비는 아래 별도 범위로 기록. |
| V5 | 기존 유지보수 기능을 재사용하고 새 검사 삭제 기능을 추가하지 않음. | 중복 실행 통합 허용, 근거 변조/약화·입력 누락·오래된 기준 차단, 요구 폐기와 남은 호출자 영향 확인, 보존 근거 없는 삭제 차단. 이번 제품 검사 삭제는 없음. |
| V6 | clean `75fde80`에서 0.1.81 284개 파일을 동결하고 로컬 배포 트리 갱신. 기존 0.1.80은 evidence 폴더에 보존. | package/update/catalog 검사 11개 통과. 설치본·전역 설정·native host·유료 모델 호출·게시를 수행하지 않음. |

`v1-red.json`과 `v2-red.json`은 수정 전 반례이며 통과로 바꾸지 않는다.
`v1-connected.json` 5건, `v2-connected.json` 7건은 실제 Chromium 실행을 필수로 했다.
후자는 전자의 기능을 포함한 후속 회귀이며 합산해 서로 다른 12개 검사로 주장하지 않는다.
각 단계의 리소스/문서 검사 30건과 sync/배포 검사도 통과했다.
`v5-maintenance.json`은 정상·거부 분기를 포함한 기존 유지보수 회귀 4건,
`v6-package.json`은 패키지와 문서 검사 11건이다.

V2 브라우저 raw는
`.work/connected-product-artifacts/69a9b804-ef8e-46fe-bc91-5542ba36c711/`에 있다.
모바일 재시작 후 screenshot을 직접 열어 History의 수량 2와 0, 표시 배치를 확인했다.
서버 identity는 loopback 테스트 앱의 관찰 장치이며 공개 운영 endpoint에 추가한 기능이 아니다.
실행 도중 파일 교체에 대한 지속 감시나 서명된 실행 증명도 아니다.

## 후속 소비와 남은 범위

새 문맥 소비에는 격리 제품과 패키지 Skill 진입점, 사용자 증상만 제공한다.
정답 패치·수정 위치·이전 실행 결과는 전달하지 않는다. 명시적 Skill 경로를 제공하므로
패키지 도움받은 소비이며 native host의 무도움 발견과 구분한다.
소비 Agent는 `agent-workflow`와 bug-fix playbook, 프로젝트 index/Feature Map,
acceptance/UI guide 및 등록 assertion을 읽었다고 보고했다. 없는 `docs/testing.md`를
읽으려던 시도도 남기며, 실제 실행법은 acceptance guide에서 찾았다.

History에서 Tab 위치가 안 보인다는 요청으로 실제 브라우저 15/16 실패를 재현하고
`shared.css`의 History 전용 outline 억제 규칙 한 줄을 제거했다. 동일 검사 16/16,
skip/error 0, 두 서비스 종료와 cleanup 오류 0을 raw에서 확인했다.
부모 검토에서 기준 프로젝트와 대조해 변경 파일이 `shared.css`뿐이고 runner/assertion은
그대로임을 확인했다. 이전 답이나 정답 코드는 소비 범위 밖에 두었다.
`consumer-evaluator.json`, `consumer-observed.json`, `consumer-artifacts/`가
평가 기준·대조 결과·복사 보존한 원본을 소유한다.

소비 Agent의 screenshot 열람은 OS access denied로 실패했다. 부모가 원본을 보존한 채
작업 evidence 폴더에 복사한 이미지를 직접 열어 History 포커스 윤곽선을 확인했다.
따라서 구현·브라우저 검사 소비는 성공했으나 소비 Agent 혼자서 이미지 육안 검토까지
완료한 사례는 아니다. 일반적인 자율 완료율이나 native 설치 성공으로 확대하지 않는다.

실제 제품/Feature 지정 전에는 다른 제품 체크아웃을 수정하지 않는다.
사업 가치 지표와 운영 외부 연동, 무감독 일반 성공률·비용 절감은 미측정이다.
현재 플러그인의 기능 검증과 다른 프로젝트의 실행 경로 연결 완료는 별도다.
