# Agent Coding 기반 구현 상태와 다음 연결

2026-10-04에 이 문서의 실행 프롬프트를 수행했다. 설계와 역사적 비교는 [수정 방향](agent-coding-system-direction.md), 현재 직접 명령은 [Testing](../testing.md), 단일 기능 지도는 [Feature Map](../feature-map.md)에 있다. 완료된 작업을 다시 수행하는 프롬프트로 사용하지 않는다.

## 완료된 로컬 범위

- `git fetch origin main`으로 `e19134358141f901bb22c4af1aea17d7a9e2898c`를 재확인했다. 준비된 `wp-20261004-agent-coding-foundation`의 문서 base `1cc09ac6468573c1a020742f2f7540bdf92d4432` 위에서 기능 단위로 작업했다. 주 작업 폴더에서 진행했고 공통 .git 삭제나 다른 checkout의 reset을 수행하지 않았다.
- 최신 배포에서 `write-a-skill`만 제거했다. 공개 catalog·allowlist·inventory·manifest를 정렬하고 HWP와 기존 runtime을 보존했다. 일반 설치본 삭제는 수행하지 않았다.
- 후보 `b40396a`의 실행 캡처를 [독립 CLI](../../scripts/run_check.py)로 선별 이식했다. 새 출력 부모 경로, 덮어쓰기 방지, native exit·timeout·Git 상태와 raw stdout/stderr를 기록한다. Feature/check와 고유 run ID를 추가했고 nonfinite timeout은 실행 전에 거절한다.
- [Repository adapter](../../scripts/verify_product.py)는 Feature Map에서 프로젝트 명령 선택 → 캡처 → check 범위 판정을 연결한다. native 실패, 0건·skip·미실행, 다른 대상·run ID·argv/cwd, 실행 중 변경과 stale 결과를 PASS로 받아들이지 않는다. 원본 실행 record의 제품 판정은 null로 남는다.
- 후보 `9d2139f`의 Windows cmd/Git Bash 전송 fallback과 실패 진단만 이식했다. 기존 hash 거절·공유 version cache를 유지하고 loopback fixture와 임시 cache로 정상·실패 경로를 검사했다.
- 실제 cached Skills CLI로 임시 Codex/Claude 프로젝트에 16개 공개 Skill을 설치·갱신하고 resource 트리를 비교했다. 일반 설치·전역 설정·push/publish·protected main 통합은 수행하지 않았다.

## 채택·보류

| 후보 | 결정 | 이유 |
| --- | --- | --- |
| 실행 캡처 | 채택 | 직접 실행되는 repository 검증 adapter가 소비하며 native 정상/실패·timeout·기록 재사용 거절을 검증 가능 |
| Windows launcher | 필요한 부분 채택 | 전송 fallback 부재와 오류 은폐를 재현했고 native cmd/Git Bash fixture로 수정 효과 확인 |
| Agent eval supervisor와 file-change 계수 | 보류 | 이번 native 검증에 모델 평가 consumer가 없고 과거 CLI filesystem 격리 실패의 해결도 확인하지 않음 |
| 신규 5개 Skill, 다단계 router | 불필요 | 현재 Agent와 native 명령으로 구현·검증을 끝낼 수 있음 |
| UI framework, MCP, 빈 plugin manifest | 보류 | 실제 제품 UI·외부 자원·설치 consumer가 아직 없음 |
| 테스트 대량 정리 | 보류 | 같은 의미의 결함 검출을 보존하며 삭제할 구체적 근거가 없음 |

## 검증과 한계

캡처·adapter 회귀 검사는 실제 Python/Git subprocess의 성공·결함·timeout·잘못된 대상·stale 대조를 사용한다. Windows launcher 검사는 컴파일한 fixture 엔진과 실패 curl, loopback HTTP를 사용하며 공개 release 다운로드 성공을 증명하지 않는다. 설치-script unit 검사의 mocked CLI와 실제 cached Skills CLI 설치 smoke는 별도 증거다. 임시 실행 자료는 `.work/agent-coding-foundation/` 및 기존 보존 정책 아래에 둔다.

샌드박스의 `taskkill /T`는 Access denied를 반환했다. 같은 소유 process/child와 무관한 process 대조는 허용된 native 도구 권한에서 검증했다. 제한 환경의 timeout 기록은 cleanup 실패·미완료를 그대로 남기고 BLOCKED로 판정한다. detached child까지 강제 정리하는 process sandbox는 제공하지 않는다.

`PASS`는 선택한 unittest assertions에 한정한다. 기록 정합성 검사는 editable evidence의 진위를 인증하지 않는다. untracked 내용·dependencies·fixture/runtime·server identity, Agent 품질·전체 skill 우월성, 외부 제품 UI/API/DB, 실제 plugin 설치/로딩/hook 동작은 미검증이다. 환경과 설치 root가 바뀌면 새 evidence가 필요하다.

## 다음 실제 plugin 연결용 프롬프트

```text
저장소: C:\Users\YS\Desktop\python\Skill_Management

현재 AGENTS.md, docs/index.md, docs/feature-map.md, docs/testing.md와 docs/research/agent-coding-system-direction.md의 구현 상태부터 읽어라. branch/HEAD/dirty baseline과 실제 최신 origin/main을 확인하고 완료된 기반 구현을 과거 후보 branch 전체로 덮어쓰지 마라.

다음 작업은 실제 대상 프로젝트와 plugin host의 설치 목적·경로가 정해졌을 때만 시작한다. 먼저 기존 CLI를 그 프로젝트에서 직접 실행하고 프로젝트가 소유하는 Feature Map·argv·업무 기준으로 성공/결함 대조를 확인해라. repository용 verify_product adapter를 외부 제품 검증으로 일반화하지 마라.

공통 실행 캡처와 필요한 adapter만 한 canonical source에서 얇게 package로 생성해라. 현재 공식 OpenAI plugin/hook 문서와 실제 host/CLI를 다시 확인하고, 임시 설치·새 세션 로딩·실제 command 실행·standalone/plugin 중복 버전 충돌을 각각 검증해라. Optional hook의 오류·timeout·trust 미부여·미지원 동작은 PASS로 취급하지 않고 직접 CLI/CI 경로를 유지해라.

일반 설치본·전역 설정 변경, 외부 publish/push, protected main 통합, provider 비용은 기존 명시 권한의 범위만 따른다. 새 승인이 필요한 행위는 review 가능한 package와 임시 검증까지 준비한 뒤 묻는다. 실제 설치 consumer가 없으면 빈 manifest·MCP·router를 만들지 말고 현재 CLI와 그 한계를 유지해라.
```
