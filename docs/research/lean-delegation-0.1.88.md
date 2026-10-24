# 0.1.88 lean delegation

[설계 기준](agent-coding-system-direction.md)의 첫 구현이다. 출발점은 clean
`wp-20261020-luna-0178-results@46356b2`(0.1.87), 작업 branch는 `wp-20261024-lean-delegation`이다.

## 바꾼 것

| 영역 | 변경 | 근거 |
| --- | --- | --- |
| Skill 노출 | 17개 Skill을 명시 호출 전용으로 전환(Claude `disable-model-invocation: true`, Codex `agents/openai.yaml` `allow_implicit_invocation: false`). 자동 호출은 5개 | 설명 합계 6,544자 → 자동 호출 5개 약 1,700자 |
| 명시 호출 연결 | `agent-workflow` capability 표가 필요에 따라 형제 Skill의 `SKILL.md`를 읽는다. 경로 링크가 아닌 이름 기반 선택 의존이라 단독 설치를 유지한다 | 사용자 요청 |
| 프롬프트 hook | 선택된 task가 없으면 Git·runtime을 실행하지 않고 route가 있을 때만 한 줄. task 후보 목록·미설정 안내 제거 | 0.1.87은 설정된 프로젝트의 모든 프롬프트에 후보 목록 주입 |
| route | 증상 표현 중심으로 재작성. 일반 변경 요청도 `agent-workflow`로. 따옴표 문구 편집·질문은 제외 | 아래 측정 |
| 위임 장치 | `agent-workflow`를 L1–L5(수락 기준 먼저, 테스트 유효성 증명, 같은 규칙의 모든 경로, 영향받는 기존 검사, 결과 카드)로 재작성. 플레이북·`diagnose`·`swarm`에 pstack 원칙 반영 | 거짓 완료·검출 누락 기록 |
| probe 등록부 | `probe_check.py probes|prove`: 격리 worktree에서 인공 결함 적용, Feature × 관점 × 계층 killed/total, 새 테스트가 변경 없이 실패하는지 증명 | 실제 제품에서 효과가 측정된 유일한 장치(Labeler 4/11 → 9/11) |
| 평가 | `scripts/run_delegation_eval.py`, `evals/delegation-v1/` | 사용자 기준: OFF 대비 측정 가능한 이득 |

## route 측정

키워드 router는 처음 보는 표현에 약했다. 최종 구조는 명시 유형(결과 조회·재개·검증 연결·가드레일·UI)을 먼저 보고,
질문·방법 문의·리뷰·요약·추천·이름 변경·버전·따옴표 문구 편집·짧은 메시지는 직접 처리한다. 증상 표현은 `diagnose`,
나머지 메시지는 작업으로 보고 `agent-workflow`로 보낸다.

| 프롬프트 세트 | 0.1.87 | 키워드 0.1.88 (중간) | 최종 0.1.88 |
| --- | --- | --- | --- |
| 기존 관찰 13개 (0.1.87 튜닝에 사용) | 13/13 | 13/13 | 13/13 |
| held-out 48개 (0.1.87 측정 후 작성) | 26/48 | 48/48 (튜닝) | 48/48 |
| 새 문맥 agent 40개 (`route_fresh.json`) | 14/40 | 첫 측정 25/40 → 튜닝 후 40/40 | 40/40 |
| 두 번째 새 문맥 40개: 필요할 때 플러그인 로드 (`route_fresh2.json`) | 7/31 | 첫 측정 15/31 | 30/31, 단순 요청 로드 0/10 |
| 평가 과제 프롬프트 9개: route 부여 | 2/9 | 4/9 | 9/9 |

평가 과제에서 키워드 router가 5/9를 놓쳐 첫 유료 평가(5회, $7.44)를 중단하고 기본 작업 route로 바꿨다. 이 변경은
평가 프롬프트의 route 여부를 본 뒤 이뤄졌으므로 평가 프롬프트의 route 9/9는 일반화 근거가 아니다. 일반화 근거는
두 번째 새 문맥 세트의 30/31이다(이 구조로 처음 측정, 세트 내용은 앞선 키워드 측정 때 이미 봤음). 증상 서술형
버그 다수는 `diagnose` 대신 `agent-workflow`로 가며, 그 버그 수정 플레이북과 `diagnose` 연결이 처리한다.

## Host 확인 (Claude Code 2.1.309, `claude-opus-5-5`, 2026-10-24)

같은 사소한 프롬프트, 전역 `agentic-coding` 비활성(`--settings`), 패키지는 `--plugin-dir`로만 로드했다.
Git 저장소이지만 Harness 설정이 없는 빈 프로젝트다.

| 조건 | 첫 요청 입력 토큰 (cache 포함) | OFF 대비 | 모델이 본 `agentic-coding` Skill |
| --- | --- | --- | --- |
| OFF | 29,547 | — | 없음 |
| 0.1.87 | 31,931 | +2,384 | 22개 |
| 0.1.88 | 30,079 | +532 | 5개 (agent-workflow, diagnose, fixing-accessibility, recall, setup-project-verification) |

0.1.87은 설정된 프로젝트에서 매 프롬프트 task 후보 JSON(약 700자)을 추가로 주입했다. 0.1.88은 route가 없으면
주입하지 않는다. 명시 호출 연결 확인: 병렬 구현 요청에 모델이 `agent-workflow`를 호출한 뒤 capability 표에 따라
`skills/swarm/SKILL.md`를 직접 읽었다(Skill 이름을 프롬프트에 준 도움 받은 1회).

## 평가

평가 결과는 측정 후 이 절에 기록한다. 기준을 넘기 전에는 위임 결과 개선을 주장하지 않는다.
