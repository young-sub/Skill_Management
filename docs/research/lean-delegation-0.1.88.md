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

| 프롬프트 세트 | 0.1.87 | 0.1.88 |
| --- | --- | --- |
| 기존 관찰 13개 (`route_prompts.json`, 0.1.87 튜닝에 사용) | 13/13 | 13/13 |
| held-out 48개 (`route_heldout.json`, 0.1.87 측정 후 작성) | 26/48, 다른 Skill 오분류 4 | 48/48 (이 세트로 튜닝함) |
| 새 문맥 agent 40개 (`route_fresh.json`, router 비공개) | 14/40, 오분류 4 | 첫 측정 25/40, 일반 신호 보완 후 40/40 (튜닝함) |

튜닝 전 일반화 수치는 새 문맥 세트의 25/40이다. 세 세트 모두 이제 회귀 테스트이며 일반화 근거가 아니다.
실제 일반화는 평가 과제에서 관찰한 Skill 호출로 판단한다.

## 평가

평가 결과는 측정 후 이 절에 기록한다. 기준을 넘기 전에는 위임 결과 개선을 주장하지 않는다.
