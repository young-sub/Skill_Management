# OFF에서 다시 쌓는 lean 감사 (2026-10-30)

시작 기준은 `wp-20261026-independent-path-check@4bc7595`(0.1.95, 깨끗한 working tree)다. 모든 수치는 결정적 도구로 원자료에서 다시 셌다
(`evals/lean-audit/tools/`, LLM 호출 없음). 예외는 두 가지다. 실제 요청 172개의 작업 유형 라벨(3b)과 플랫폼 중복 판정(4)은 Claude의
판단이며 그렇게 표시했다. 사전 등록과 판정 규칙은 [lean audit README](../../evals/lean-audit/README.md)가 소유한다.
**관찰**은 도구가 센 값, **추론**은 그 값에서 끌어낸 해석이다.

## 원자료

| 원천 | 내용 | 경로 |
| --- | --- | --- |
| 평가 셀 112개 | v1 0.1.88 ON/OFF 각 24, v2 0.1.89 ON/OFF 각 24, v1 0.1.87 ON 16. 셀마다 `result.json` 채점과 stream-json 전사본 | `%TEMP%/claude/delegation-eval-run3`(1–2회차), `-run4-rep3`, `-run5-v087`, `.work/delegation-eval/v2-0189-20261025-resume2` |
| 실제 작업 세션 30개 | `entrypoint: cli`. Skill_Management 15, yeondu-page 10, labeler 2, 기타 3. 하위 에이전트 전사본 포함 | `~/.claude/projects/*/*.jsonl` |
| 평가·탐침 세션 229개 | `entrypoint: sdk-cli`. 실제 작업 집계에서 뺐다 | 같은 위치 |
| 출처 | `git log -S`(현재 문구 도입 커밋) | `provenance.py` |

산출 JSON은 `.work/lean-audit/20261030/`(만료 대상)에 있다. 재생성 명령은 README에 있다.

**관찰: 실제 세션은 모두 설치본 0.1.89로 돌았다.** `~/.claude/plugins/installed_plugins.json`의 마지막 갱신은 2026-10-24다.
0.1.90–0.1.95(L5 독립 검증, LSP 지시 포함)는 실사용 기록이 0건이다.

## 1. 비용 장부

토큰 환산값은 **0.375 token/byte**다. 평가 전사본에서 Skill 본문이 주입될 때마다 생긴 문맥 증가량 44건의 중앙값(관찰)이다.
*세션당 소비*는 요소가 문맥에 더한 토큰 × 그 뒤로 그것을 다시 읽은 요청 수다. 즉 세션 입력 토큰(입력 + 캐시 읽기) 가운데 그 요소의 몫이다.

### 정적 크기와 로드 조건

| 요소 | 로드 조건 | 바이트 | 토큰 |
| --- | --- | ---: | ---: |
| 전역 `authoring/global/AGENTS.md`(= `~/.claude/CLAUDE.md`, 바이트 동일) | 상시. **평가 OFF에도 로드된다** | 4,184 | 1,569 |
| 프로젝트 `CLAUDE.md`(`AGENTS.md`와 동일, Codex용) | 상시. 이 저장소에서만 | 2,853 | 1,070 |
| Skill 목록: model-invocable 5개의 description | 플러그인 ON이면 상시 | 1,626 | 609 |
| 같은 목록, 0.1.88 이전(22개 모두 노출) | 상시 | 7,212 | 2,705 |
| UserPromptSubmit route 문맥 | 라우트가 걸린 매 프롬프트. task-notification 포함 | 338 | 127 |
| Stop guard 차단 사유 | 차단 시 | 약 300–600 | 약 110–225 |
| L5 검증 템플릿 `independent-check.md` | 차단 사유가 가리켜 Read할 때 | 5,830 | 2,186 |
| L5 검증자 하위 에이전트 | guard가 요구해 실행할 때 | 별도 문맥 | 회당 약 $0.89(failure replay 9회 $8.02) |

| Skill | 노출 | 목록 토큰 | 본문 B / 토큰 | references 파일 / B | 평가 호출 | 실사용 호출 | 첫 커밋 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `agent-workflow` | **model** | 148 | 3,712 / 1,392 | 17 / 547,131 | 44 | 2 | c7c064a 2026-10-05 |
| `diagnose` | **model** | 154 | 5,287 / 1,983 | 6 / 52,754 | 7 | 0 | 6eda4f4 2026-06-18 |
| `fixing-accessibility` | **model** | 96 | 4,926 / 1,847 | 1 / 1,093 | 0 | 1 | c77b4d0 2026-09-06 |
| `recall` | **model** | 108 | 2,622 / 983 | 0 / 0 | 0 | 0 | 298743d 2026-10-18 |
| `setup-project-verification` | **model** | 103 | 7,122 / 2,671 | 14 / 534,505 | 0 | 0 | c7c064a 2026-10-05 |
| `architect` | explicit | 0 | 2,692 / 1,010 | 2 / 4,207 | 0 | 0 | 66c3cee 2026-10-18 |
| `close-goal` | explicit | 0 | 2,538 / 952 | 11 / 600,806 | 0 | 0 | 9d73977 2026-07-20 |
| `design-goal` | explicit | 0 | 2,874 / 1,078 | 3 / 198,266 | 0 | 0 | 9f033b0 2026-07-19 |
| `execute-codex-goal` | explicit | 0 | 4,883 / 1,831 | 11 / 602,764 | 0 | 0 | 94f5fa7 2026-07-19 |
| `explore-idea` | explicit | 0 | 1,198 / 449 | 1 / 45 | 0 | 0 | 9f033b0 2026-07-19 |
| `finance-research` | explicit | 0 | 12,118 / 4,544 | 18 / 90,131 | 0 | 0 | 6eda4f4 2026-06-18 |
| `hwp-form-fill` | explicit | 0 | 4,761 / 1,785 | 6 / 41,410 | 0 | 0 | e191343 2026-09-22 |
| `impeccable` | explicit | 0 | 11,229 / 4,211 | 57 / 2,166,969 | 0 | 2 | c77b4d0 2026-09-06 |
| `maintain-agent-harness` | explicit | 0 | 1,515 / 568 | 11 / 635,219 | 0 | 0 | 9d73977 2026-07-20 |
| `maintain-project-verification` | explicit | 0 | 5,740 / 2,152 | 15 / 534,550 | 0 | 0 | c7c064a 2026-10-05 |
| `multi-agent-review` | explicit | 0 | 4,673 / 1,752 | 5 / 6,860 | 0 | 0 | 6eda4f4 2026-06-18 |
| `prototype` | explicit | 0 | 2,892 / 1,084 | 3 / 3,776 | 0 | 0 | 6eda4f4 2026-06-18 |
| `setup-agent-harness` | explicit | 0 | 2,758 / 1,034 | 8 / 206,928 | 0 | 1 | be87141 2026-07-19 |
| `swarm` | explicit | 0 | 6,114 / 2,293 | 1 / 45 | 0 | 0 | ca4d7b7 2026-10-18 |
| `teach` | explicit | 0 | 7,606 / 2,852 | 5 / 8,576 | 0 | 0 | 6eda4f4 2026-06-18 |
| `vercel-react-best-practices` | explicit | 0 | 7,299 / 2,737 | 75 / 229,884 | 0 | 0 | c77b4d0 2026-09-06 |
| `zoom-out` | explicit | 0 | 1,534 / 575 | 1 / 45 | 0 | 0 | 6eda4f4 2026-06-18 |

references 바이트에는 실행만 하고 읽지 않는 스크립트(`agent-workflow/scripts/*.py` 등)도 들어 있다.
관찰: explicit-only 17개는 모델 목록에 나오지 않는다. 실제 `skill_listing` 첨부에서 agentic-coding 줄이 5개다.

### 실측 상시 비용

관찰: ON 첫 요청 문맥 − OFF 첫 요청 문맥의 중앙값은 **v1 0.1.88 650 토큰, v2 0.1.89 586 토큰**이다. 목록 609 토큰 + 첫 route 127 토큰과 맞는다.

### 평가 세션 (셀 평균)

| 데이터 | 조건 | 성공 | 거짓 완료 | 토큰 | 성공당 토큰 | 요청 수 | 비용 | Skill 본문 | 플러그인 스크립트 | 플러그인 문서 Read |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 0.1.88 | OFF | 18/24 | 6 | 1,606,760 | 2,142,346 | 26.5 | $1.28 | 0 | 0 | 0 |
| v1 0.1.88 | ON | 19/24 | 5 | 1,984,005 | 2,506,111 (×1.17) | 32.7 | $1.58 | 87,216 | 24,374 | 12,350 |
| v2 0.1.89 | OFF | 22/24 | 2 | 2,514,273 | 2,742,843 | 29.3 | $1.72 | 0 | 0 | 0 |
| v2 0.1.89 | ON | 21/24 | 3 | 2,920,126 | 3,337,287 (×1.22) | 32.2 | $1.80 | 71,690 | 6,426 | 0 |

관찰: ON−OFF 토큰 차이는 셀당 377k(v1)와 406k(v2)다. 그중 플러그인 산출물에 직접 귀속되는 부분은 204k(54%)와 111k(27%)다.
Skill 본문, 스크립트, 문서 Read와 `.work/.harness` 읽기·쓰기 증가분을 합한 값이다. 상시 문맥(약 600토큰 × 약 30요청)은 약 18k(5% 안팎)다.
**추론:** 나머지 절반 안팎은 요청 수 증가(+6.2, +2.9)로 생긴 긴 세션이다. 정적 문맥을 줄이는 것만으로는 차이가 거의 줄지 않는다.

### 실제 작업 세션 (입력 토큰 중 몫, 진행 중인 이 세션 제외 23개)

| 묶음 | 세션 | 입력 토큰 | 전역 AGENTS.md | 프로젝트 CLAUDE.md | Skill 목록 | route 문맥 | Skill 본문 | 플러그인 스크립트 | `.work/.harness` 쓰기 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 제품 저장소(yeondu-page, labeler) | 10 | 322.1M | 0.54% | 0 | 0.94% | 0.72% | 0.27% | 0 | 7.09% |
| Skill_Management(플러그인 개발) | 11 | 589.8M | 0.46% | 0.32% | 0.46% | 1.36% | 0.42% | 10.75% | 9.89% |

Skill_Management의 스크립트·`.work` 몫은 플러그인 개발 작업 자체(테스트, 평가 실행)라 플러그인 비용이 아니다.
제품 저장소의 `.work` 쓰기 대상은 사진 brief, Codex 입력, 검증 로그 등이다. 관찰상 OFF 평가에도 비슷한 쓰기가 있어 플러그인 귀속은 정하지 못했다.

### 훅 지연

| 훅 | 측정 | p50 | p95 | n |
| --- | --- | ---: | ---: | ---: |
| Stop (`completion_guard.py`, 0.1.89) | 호스트 기록 `durationMs` | 261 ms | 565 ms | 279 |
| Stop (현재 0.1.95, 실제 전사본 30개 재생) | 로컬 `latency.py` | 117 ms | 393 ms | 30 |
| UserPromptSubmit (현재, 실제 프롬프트 172개 재생) | 로컬 | 92 ms | 105 ms | 172 |
| Python 시작만 | 로컬 | 90 ms | 98 ms | 20 |

**추론:** 지연은 비용이 아니다. UserPromptSubmit의 92 ms는 Python 시작 시간과 거의 같다.

## 2. 출처

현재 문구를 처음 넣은 커밋은 `git log -S`로 찾았다(`.work/lean-audit/20261030/provenance.json`). 근거 등급은 셋 중 하나다.
*짝지은 ON/OFF*는 요소가 들어간 플러그인을 같은 과제의 OFF와 짝지어 잰 경우다. 지금까지는 모두 **묶음 단위**였고, 요소 하나만 뺀 측정은 없다.

| 요소 | 현재 문구 도입 | 대응한 실패 기록 | 근거 등급 | 측정 결과 |
| --- | --- | --- | --- | --- |
| 전역 AGENTS.md 12조항(B4) | 3e85fe5 2026-10-18 | [B4 채택](global-guidance-b4-adoption.md): A의 전역 커밋 의무가 불필요한 Git 쓰기 유발 | **근거 없음(OFF 대비)** | A↔B4만 짝지어 쟀다(5과제, 품질 동일, 입력 −21.7%). 전역 없음과 비교한 적은 없다. 플러그인 평가의 OFF에도 항상 들어 있었다 |
| 프로젝트 CLAUDE.md | 4c6351b 2026-07-19 ~ 651f81e 2026-10-04 | 저장소 운영 규칙 | 근거 없음 | 이 저장소 개발에만 로드. 평가 대상이 아니다 |
| `agent-workflow` 본문 | c7c064a 2026-10-05(53회 수정, 0.1.93·0.1.95 재작성) | [failure replay](failure-replay-20261030.md) 경로 누락 6 | 짝지은 ON/OFF(묶음, 이전 문구) | 0.1.88: 19 대 18, 0.1.89: 21 대 22. 이득 없음, 토큰 +16–23%. 현재 문구는 미측정 |
| `diagnose` 본문 | 6eda4f4 2026-06-18(25회 수정) | 같은 기록 | 짝지은 ON/OFF(묶음, 이전 문구) | 같은 묶음 |
| L4 모든 쓰기 경로 지시(`LSP findReferences` 포함) | 0.1.95 4bc7595 | 경로 누락 6 | 짝지은 ON/OFF(묶음, 이전 문구) | 0.1.88·0.1.89에서 Skill이 호출된 경로 누락 4/4에 로드됐는데 0건을 막았다 |
| UserPromptSubmit router | 64fe661 2026-10-24(0.1.88) | 없음(Skill 자동 호출 보조) | 짝지은 ON/OFF(묶음) | 같은 묶음. 3b의 오분류 측정 |
| Stop: 마지막 실행 뒤 편집 | 298f9bd 2026-10-22(0.1.84) | 미실행 편집 완료 보고 | 짝지은 ON/OFF(묶음) | 평가 차단 0/112, 실사용 1/280 |
| Stop: 독립 검증 요구(L5) | 634207e 2026-10-27(0.1.91) | 경로 누락 6 | **오프라인 replay만** | 6건 중 5건 변화(경로를 위반으로 지목 2건, 질문 2건). 대조 3건 중 2건 표시(1건은 실제 결함) |
| Stop: shell/interpreter 편집 크기 | a10f894 2026-10-29(0.1.94) | 편집 61줄에 guard 침묵(실제 세션) | 근거 없음(단건 재현) | — |
| Stop: probe 등록 요구 | c3f733c 2026-10-28(0.1.92) | 없음 | 근거 없음 | — |
| `recall`, `fixing-accessibility`, `setup-project-verification` | 표 1 참조 | 없음 | 근거 없음 | — |
| explicit-only 17개 | 표 1 참조 | 없음 | 근거 없음 | 런타임 상시 비용 0 |

## 3. 해악 증거

### (a) Stop guard 차단 뒤 코드 변화

| 범위 | guard 실행 | 차단 | 차단 뒤 다음 Stop까지 파일 변경 0 |
| --- | ---: | ---: | --- |
| 평가 셀(0.1.87–0.1.89) | 112 세션 | 0 | — |
| 실제 세션(0.1.89) | 280 | 1 (`4b3921da`, `.gitignore`) | **1/1**. 읽기 전용 명령 1회(`git check-ignore`)와 설명 1회. 요청 2회가 늘었다 |

관찰: guard가 막으려는 상태, 즉 마지막 코드 편집 뒤 실행이 없는 경우는 OFF 48셀 중 3셀에서 났다. 그 3셀은 모두 검증된 성공이었다.
OFF 거짓 완료 8건 중 이 상태였던 것은 0건이다(`unexercised_final_edit`, Edit/Write의 코드 파일 기준. heredoc 편집은 세지 않는다).
현재 guard를 실제 전사본 30개의 마지막 지점에 재생하면 1건이 차단된다.
**추론:** 표본이 작다. 그래도 이 규칙이 실패를 막았다는 관찰은 0건이다.

### (b) UserPromptSubmit route 혼동 행렬

실제 사용자 프롬프트 172개 중 중복 10개를 뺀 162개다. 현재 router(4bc7595)와 0.1.89 router(987dba7)는 결정적으로 재생했고 결과가 같았다.
**라벨은 Claude의 판단이다.** 확인용 전체 목록(요청 원문 앞부분 포함)은 `.work/lean-audit/20261030/route-labels.md`에 있다.
요청 원문에 전화번호·검증 토큰이 있어 로컬에만 둔다. 커밋한 것은 id·라벨·메모뿐이다(`evals/lean-audit/labels/real-prompts.json`).
라벨별 기대 route: IMPL→agent-workflow, BUG→diagnose, RESUME→recall 또는 agent-workflow, IMPL-GO(구현 승인)→agent-workflow 또는 없음,
FEEDBACK→없음 또는 diagnose, 나머지→없음.

| 실제 유형 \ route | agent-workflow | diagnose | recall | 없음 |
| --- | ---: | ---: | ---: | ---: |
| IMPL 구현 요청 | **28** | 1 | 0 | 1 |
| IMPL-GO 구현 승인 | 10 | 0 | 0 | 2 |
| BUG 결함 신고 | 0 | **1** | 0 | 3 |
| RESUME 재개 | 1 | 0 | 0 | 0 |
| ANALYSIS 검토·분석 | 19 | 4 | 0 | 13 |
| PROMPT 프롬프트 작성·rewrite | 5 | 3 | 0 | 1 |
| QUESTION 질문 | 4 | 3 | 0 | 19 |
| OPS git·배포·설치 | 13 | 0 | 0 | 6 |
| CONT 이어가기·답변 | 3 | 0 | 0 | 6 |
| SYS-CONT 압축 요약 | 2 | 0 | 4 | 0 |
| SLASH 명시 slash 명령 | 4 | 0 | 0 | 0 |
| TRIVIAL 한 값 수정 | 2 | 0 | 0 | 0 |
| FEEDBACK 방향 교정 | 1 | 0 | 0 | 0 |
| OTHER | 0 | 0 | 0 | 3 |

- 맞음 **90/162(56%)**. 항상 "없음"을 내는 router는 127/162(78%)다.
- agent-workflow 정밀도는 39/92(구현·승인·재개)다. diagnose 정밀도는 **1/12**, 재현율은 BUG 1/4다.
- 백그라운드 `<task-notification>` 145개 중 130개에 route가 붙었다. 사용자 요청이 아니므로 모두 오분류다.
- 사용자가 말한 사례: `b47aef9f#2`("…덜어낼 수 있을지… 검토해줘" + "rewrite my prompt" 접미사)는 기록상·재생상 모두 **diagnose**다.
  이번 요청 `1dc71010#1`도 diagnose로 갔다. `deeper … rewrite` 접미사가 붙은 6건 중 5건이 오분류다(agent-workflow 4, diagnose 1).
- 원인(코드 사실): diagnose 오분류 11건 중 6건은 SYMPTOM의 한국어 연결어미 패턴 `(했|됐|인|는)데도?\s`("하고 있**는데** 그에 반해")에서 왔다.
  2건은 `원인`이다. 이번 요청은 "…셀 전부와 **원인**"에 걸렸다. 2건은 `이상해/이상한`, 1건은 `오류가 `다.
  agent-workflow 오분류 53건 중 44건은 "질문이 아니면 위임" 기본값, 9건은 표 패턴에서 왔다.

### (c) 프로세스 산출물에 쓴 턴과 토큰

| 범위 | Skill 본문 | 플러그인 스크립트(`probe_check`·`run_check`·`project_workflow`·`unittest_evidence`) | 플러그인 문서 Read | `.work/.harness` 쓰기·읽기 증가(ON−OFF) |
| --- | --- | --- | --- | --- |
| v1 0.1.88 ON, 24셀 | 24회 호출, 셀당 87k | 58회, 셀당 24k | 2회, 셀당 12k | 셀당 +80k |
| v2 0.1.89 ON, 24셀 | 20회, 셀당 72k | 15회, 셀당 6k | 0 | 셀당 +33k |
| 제품 실세션 10개 | 0.27% | 0 | 0.05% | 7.09%(귀속 불명) |

요청 수 기준으로는 ON이 셀당 +6.2(v1), +2.9(v2) 요청을 더 썼다. result card는 최종 답변 안에 있어 따로 세지 않았다.
관찰: 최종 답변 바이트 중앙값은 v1 OFF 2,500 / ON 2,911, v2 OFF 2,927 / ON 2,958이다(`answer_bytes`).

### (d) ON 실패 / OFF 성공 셀 전부 (짝지은 48쌍)

| 데이터 | 시나리오·회차 | ON 실패 내용 | 원인 | 분류 |
| --- | --- | --- | --- | --- |
| v1 0.1.88 | `api-contract-change` r1 | hidden 통과, 기존 회귀만 실패. 무관한 `fieldTranslations`·`translationCredits` 테스트의 5초 timeout | 실행 부하로 생긴 무관 테스트 timeout. 같은 테스트가 다른 셀에서는 통과 | **코드 사실(평가 기반시설)**: 러너가 timeout 회귀를 1회 재실행해 둘 다 기록하면 된다. 플러그인으로 막을 대상이 아니다 |
| v2 0.1.89 | `a-product-source-stale-all-paths` r2 | 백업 복원 경로가 규칙을 적용하지 않음(v2 hidden 실패) | 같은 규칙의 다른 쓰기 경로 누락 | **코드 사실**: "이 컬럼을 쓰는 모든 경로"는 질의(LSP references, SQL 쓰기 검색)로 열거할 수 있다. L4 지시는 로드됐는데 막지 못했다. L5 replay는 이 경로를 위반으로 지목했다 |

반대 방향인 ON 성공 / OFF 실패는 2셀이다(v1 `rule-all-paths` r1·r3, OFF가 쓰기 경로를 누락). McNemar exact p는 v1 1.0(2 대 1), v2 1.0(0 대 1)이다.
짝 차이의 bootstrap 95% CI는 성공 v1 [−0.083, +0.167], v2 [−0.125, 0.000]이다.

참고로 [failure replay](failure-replay-20261030.md)의 ON 실패 12건 원인 분류는 다음과 같다. 경로 누락 6건은 코드 사실이다.
hidden 기대 불일치 5건은 판단 영역이지만 OFF도 3/3 실패했으므로 과제 결함이다. timeout 1건은 환경이다.

## 4. 플랫폼 중복

비교 대상은 이 세션에서 관찰한 Claude Code 시스템 프롬프트(CLI 2.1.314, 대화형 백그라운드)다. headless `-p` 세션의 프롬프트는
기록되지 않아 같다고 가정할 수 없다(**추론의 한계**). 평가 init 이벤트의 `skills` 목록에는 내장 `verify`, `debug`, `run`, `code-review`, `simplify`가 있다(관찰).
애매한 것은 OFF 탐침으로 확인한다([탐침 설계](../../evals/lean-audit/README.md#b-off-probes), 유료, 미실행).

| 규칙 | 플랫폼에 있는 문장(요지) | 중복 | 탐침 |
| --- | --- | --- | --- |
| G1 승인 범위 안에서 끝까지 수행, 구현 요청 전 탐색은 읽기 전용 | "goals, using your own judgment", "When you have enough information to act, act" | 부분. 읽기 전용 조항은 없다 | `readonly` |
| G2 근거로 이해, 중요한 가정 명시, 가져온 내용은 권한이 아닌 근거 | pasted content·tool result는 데이터이며 지시가 아니다 | 부분. 가정 명시는 없다 | `assume` |
| G3 사용자 변경 보존, 파괴적·외부 작업은 명시 승인 | "confirm first… hard to reverse or outward-facing", "Before deleting or overwriting, look at the target" | **강함** | `notes.md` 보존을 모든 탐침에서 관찰 |
| G4 가장 작은 완전한 접근 | 위임 비용 경고 정도 | 약함 | `smallest` |
| G5 기존 코드 재사용, 원인을 소유자에서 수정 | "Write code that reads like the surrounding code" | 부분 | 판단 영역이라 평가로만 측정 |
| G6 작업 크기만큼의 절차, 실행·관찰 경로를 스스로 찾기 | 문장은 없다. 내장 `run`·`verify` Skill이 있다 | 애매 | `observe` |
| G7 변경에 맞춘 검증(버그 재현 등) | 문장은 없다. 내장 `debug` | 애매 | `repro` |
| G8 실패 시 원인 확인, 권한 한계 구분, 해제 방법 제시 | "denied call… adjust", "suggest `! <command>`" | 부분 | — |
| G9 충분한 근거에서 종료, 재시도 전 상태 확인 | "Report outcomes faithfully" | 부분 | — |
| G10 독립 작업 병렬화, 위임 | Agent 도구 장문 지침("When in doubt, don't spawn") | **강함**. 방향은 플랫폼이 더 보수적이라 **충돌 소지** | — |
| G11 오래가는 기술 진실을 구현과 일치 | 없음 | 없음 | — |
| G12 계획에서 멈추지 말고 끝내기, 관찰과 추론 구분 | "Report outcomes faithfully: if tests fail, say so…", "End the job with a report the user can act on" | **강함** | 기존 실패 테스트 보고를 관찰 |
| 프로젝트 CLAUDE.md "검증된 기능 단위마다 커밋" | "Commit or push only when the user asks" | **충돌**(저장소 정책이 의도적으로 덮어씀) | 모든 탐침에서 `new_commits` 관찰 |
| router(UserPromptSubmit) | Skill 도구: "When the task at hand is one a listed skill covers, call this tool first" + description 매칭 | **강함**. 플랫폼의 Skill 선택을 정규식으로 다시 구현했다 | 3b가 측정 |
| `agent-workflow`·`diagnose` 본문 | 내장 `verify`·`run`·`debug`·`code-review` | 기능 중복 | 3-arm에서 측정 |
| Stop guard | 없음 | 없음 | — |

## 5. 분류와 lean 후보

| 요소 | 분류 | 근거 |
| --- | --- | --- |
| Stop: 독립 검증 요구(L5)와 템플릿, 편집 크기 계산 | **lean에 포함(측정 대상)** | 등급은 replay뿐이지만 기록된 실패 원인 1위(경로 누락 6건)에서 5/6 변화. 3-arm이 판정한다 |
| Stop: 마지막 실행 뒤 편집 | 삭제 | 차단 0/112, 1/280. 대상 상태 3/48은 모두 성공 |
| Stop: probe 등록 요구 | 삭제 | 근거 없음. 프로세스 산출물 |
| UserPromptSubmit router | 삭제 | 맞음 56%, 무라우터는 78%. diagnose 정밀도 1/12. task-notification 130/145 오라우팅. 플랫폼 Skill 선택과 중복 |
| `agent-workflow`, `diagnose` | explicit-only 전환 | 묶음 ON/OFF 2회 이득 없음, 성공당 토큰 ×1.17·×1.22 |
| L4 모든 쓰기 경로 지시 | 결정적 도구로 대체 | 로드된 4/4에서 막지 못함. 원인이 코드 사실이므로 "쓰는 곳 목록"을 돌려주는 질의 도구(LSP references, 컬럼 쓰기 검색)를 검증자에게 준다 |
| `fixing-accessibility`, `recall`, `setup-project-verification` | explicit-only 전환 | 근거 없음. recall은 압축 요약 4건에 오라우팅됐다 |
| 플러그인 스크립트 `probe_check`·`run_check`·`unittest_evidence`·`project_workflow` | explicit-only(Skill 안에서만) | 근거 없음. v1 ON 셀당 24k |
| `finance-research`, `hwp-form-fill`, `teach` | 플러그인 밖으로 분리 | 코딩과 무관 |
| `impeccable`, `vercel-react-best-practices` | explicit-only 유지 | FE 지식. 상시 비용 0, 근거 없음 |
| Goal 계열 `setup-agent-harness`·`maintain-agent-harness`·`design-goal`·`close-goal`·`execute-codex-goal`·`maintain-project-verification` | explicit-only 유지, 일몰 대상 | 실사용 1회. 상시 비용 0 |
| `architect`, `swarm`, `multi-agent-review`, `prototype`, `explore-idea`, `zoom-out` | explicit-only 유지, 일몰 대상 | 실사용 0회 |
| 전역 G3·G10·G12 | 삭제 후보(플랫폼 중복) | 확정하려면 탐침이 필요하다. 플러그인 3-arm 밖이다 |
| 전역 G1·G2·G4·G6·G7 | 탐침 결과로 결정 | bare 기본 동작이 같으면 삭제, 다르면 탐침이 측정된 이득이 된다 |
| 전역 G5·G8·G9·G11 | 삭제 후보(근거 없음) | 판단 영역이라 탐침으로 잴 수 없다. 선택 사항인 `bare` 평가군으로만 확정할 수 있다 |
| 프로젝트 CLAUDE.md | 범위 밖(저장소 개발 규칙) | 평가 저장소에 로드되지 않는다. 커밋 조항은 플랫폼 기본값을 의도적으로 덮어쓴다 |

**lean = OFF + L5**다. 그 밖의 플러그인 요소는 위 분류대로 빼거나 explicit-only로 둔다.
패키지는 `evals/lean-audit/tools/run.py build`가 커밋된 플러그인에서 정확한 텍스트 편집으로 만든다(플러그인 원본은 바꾸지 않는다).

**상시 로드 토큰 예산(lean)**

| 항목 | 현재 0.1.95 | lean 예산 | 측정 방법 |
| --- | ---: | ---: | --- |
| 플러그인 Skill 목록 | 609 | **0** | 같은 시나리오 짝에서 lean 첫 요청 − OFF 첫 요청 ≤ **50** 토큰 |
| 프롬프트당 route 문맥 | 127(라우트 시) | **0** | UserPromptSubmit 훅 없음 |
| 전역 AGENTS.md | 1,569 | **≤ 1,569**(증가 금지). 탐침 뒤 중복 조항 삭제 시 목표 ≤ 1,000 | 바이트 × 0.375 |
| 트리거 시(L5 차단 사유 + 템플릿 Read) | 약 2,300 | ≤ 2,500 | 차단 1회당 |

### 빠진 요소

실패 증거는 있는데 대응 장치가 없는 것:

1. **쓰기 경로 질의 도구**: 경로 누락 6건의 원인은 코드 사실인데, 지금은 지시(L4)와 검증자(L5)만 있다. "컬럼 X를 쓰는 함수 목록"을 돌려주는 질의 도구가 없다.
   이전 인벤토리 B는 전체 덤프(211–246줄)라 실패했다.
2. **평가 러너의 timeout 재실행**: ON 실패 / OFF 성공 2건 중 1건, ON 실패 12건 중 1건이 무관 테스트 timeout이다.
3. **과제 결함 검출**: `fe-logic-feature`는 OFF도 3/3 같은 해석으로 실패했다. 과제 채택 전에 OFF 전원 실패를 검출하는 규칙이 없다.
4. **task-notification 제외**: router를 남긴다면 시스템 알림을 걸러야 한다(130/145 오라우팅).
5. **진짜 OFF**: 모든 평가 OFF에 전역 AGENTS.md, 사용자 훅(orca), codex 플러그인이 들어 있다. `--bare`는 API key가 필요하다(현재 OAuth뿐). `--setting-sources project,local` 격리는 미검증이다.

측정 인프라의 빈틈:

| 빈틈 | 현재 | 필요한 것 |
| --- | --- | --- |
| hold-out 세트 | 없음. v3 추가 hidden은 L5 계열 검증자가 찾은 결함이라 L5에 유리하다 | README의 구성안(yeondu-page 실제 작업) |
| 라우터 평가 | 합성 fixture(`tests/distribution/fixtures/route_*.json`)뿐 | 실제 프롬프트 라벨 세트(이번 162개, 라벨러 1명. 사용자 검토 필요) |
| 실사용 telemetry | 설치본 0.1.89 고정. 0.1.90–0.1.95 실사용 0건. 세션별 "어떤 장치가 발동했고 결과가 어땠는지" 기록이 없다 | 세션 종료 시 발동 장치·차단·사용자 교정 여부를 남기는 로컬 기록 |
| 모델·CLI 재측정 | 평가는 claude-opus-5-5, CLI 2.1.309–2.1.310. 현재 2.1.314 | 모델·CLI가 바뀌면 off/on/lean 24셀을 다시 재는 규칙 |
| 규칙 일몰 | 없음. 근거 없는 요소가 계속 남는다 | 요소마다 근거 등급과 만료일. 만료까지 측정 이득이 없으면 삭제 |
| 검정력 | 지난 ON/OFF는 24쌍. 불일치율 8.3%에서 80% 검정력의 비열등 마진은 14.7%p | 48쌍 이상(v3 24 + hold-out 24) |
| 라벨 신뢰도 | 1명(Claude) | 사용자 표본 검토 또는 두 번째 라벨러와의 일치도 |

## 한계

- 평가 셀은 Labeler·yeondoo-link 두 프로젝트, 같은 모델이다. 실제 세션 30개 중 15개는 플러그인 개발 자체다.
- `token_requests`는 문맥이 늘기만 한다고 가정한다. 압축(compaction) 뒤에는 과대평가된다.
- 0.375 token/byte는 영어 위주 Skill 본문에서 잰 값이다. 한국어 문맥에는 다른 값이 맞을 수 있다.
- 플랫폼 중복 판정은 이 세션의 시스템 프롬프트 기준이다. headless 프롬프트가 다를 수 있다.
- `unexercised_final_edit`은 Edit/Write의 코드 파일만 센다. heredoc·스크립트 편집은 빠진다.
