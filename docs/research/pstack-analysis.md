# pstack 구성과 자율 구현 검증 분석

pstack의 스킬, 작업 절차, 서브에이전트, 자동화 팩과 실행 도구를 정리하고, 에이전트가 구현부터 실제 환경 검증까지 수행해 작업을 마무리한다는 관점에서 평가한다. 외부 플러그인의 설계를 검토하거나 우리 작업 방식에 참고할 요소를 찾는 사람이 독자다.

이번 조사에서 가장 높게 평가한 부분은 검증 경로를 실제로 만들고 실행하는 절차, 변경과 분리된 측정 기준, 최종 코드에 연결된 검증 결과다. 그러나 대부분의 제품 검증 규칙은 에이전트가 따라야 하는 지침이다. 실행 도구가 모든 증거를 검사하거나 완료를 강제하는 구조는 확인되지 않았다.

이 문서는 외부 플러그인의 조사 기록이다. 이 저장소의 실행 지침은 [Agent workflow](../agents/workflow.md)와 기존 Harness 문서가 정한다.

현재 채택·제외 기준과 다음 개선 순서는 [Agent Coding 체계 방향](agent-coding-system-direction.md#next-improvements-0147), 실제 후속 구현은 [구현 결과](agent-workflow-implementation-results.md#d1d3-consumption-2026-10-09)에 정리했다. [과거 실행 프롬프트](agent-coding-next-session.md)는 수행 범위의 기록이며 새 실행 지시가 아니다. 이전 배포 비교·Router 보류 판단은 [아카이브](archive/index.md)에 보존한다. 이 문서는 2026-10-03에 고정한 외부 소스의 조사 기록이며, 후보 전체의 품질 효과나 현재 플러그인 호스트 지원을 보증하지 않는다.

## 조사 범위와 근거

2026-10-09의 현재 고도화 판단은 [0.1.47 설계 검토](agent-coding-system-direction.md#design-review-0147)를 따른다. [0.1.46 보완 검토](agent-workflow-refinement-review.md#post-0146-review)의 D1–D3는 후속 구현에서 해결됐다. 이 링크 갱신은 아래 고정 소스를 새로 조사하거나 pstack을 실행했다는 뜻이 아니다. 기존 기능 인수와 새 구현을 구분하고 고정된 기준의 실패/정상 반례·실제 기능 조작·원인별 개선을 재사용한다. 아래 pstack 고정 소스 조사 범위는 바뀌지 않았으며 동일 과업 실행 비교나 최신 버전 우월성을 확인한 것은 아니다.

우리 체계의 2026-10-07 실제 구현·사용과 이 고정 소스의 비교는 [현재 구현 결과](agent-workflow-implementation-results.md#pinned-pstack-comparison)에 있다. 같은 커밋의 주요 1차 소스를 다시 확인했으며, pstack 실행이나 양쪽의 동일 과제 비교 실험을 한 것은 아니다.

- 조사일은 2026-10-03이다.
- 요청받은 대상은 [cursor/plugins의 pstack](https://github.com/cursor/plugins/tree/main/pstack)이다.
- 조사 기준 커밋은 `23e4138daa01c42d4969f7a5465f82704e64f798`이다. 문서의 외부 소스 링크는 모두 이 커밋에 고정했다.
- [플러그인 manifest](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/.cursor-plugin/plugin.json)의 버전은 `0.15.6`, 제작자는 Lauren Tan, 라이선스는 MIT다.
- GitHub의 재귀 파일 목록을 기준으로 스킬 정의 52개를 확인했다. 일반 등록 경로 아래의 49개와 Benny 팩의 3개를 구분했다.
- 52개 스킬 정의, 내부 작업 절차 23개, 에이전트 정의 2개를 읽었다. 주요 실행 도구와 검토 기준도 확인했다.
- GitHub 페이지의 캐시된 README와 직접 조회한 소스 사이에 버전, 원칙 개수, 모델 기본값 차이가 있었다. 개수와 설정은 위 커밋의 실제 파일을 기준으로 확정했다.

| 근거 수준 | 이 문서에서 뜻하는 것 |
| --- | --- |
| 소스에서 확인 | 파일, 지침, 조건, 코드 분기와 저장 형식에서 직접 확인한 사실이다. |
| 평가 | 확인한 장치가 어떤 실패를 줄일 수 있는지에 대한 우리의 판단이다. 효과의 크기를 측정했다는 뜻은 아니다. |
| 미검증 | 플러그인 실행, 실제 앱 재현, 외부 서비스 연동, 비용과 완료율 비교는 이번 조사에서 수행하지 않았다. |

## 자율 구현과 검증에 대한 핵심 평가

### 검증 경로를 실행 가능한 결과물로 남긴다

소스에서 확인한 사실이다. [create-verification-skill](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/create-verification-skill/SKILL.md)은 저장소의 실제 시작 명령, 조작 방법, 관찰 방법, 격리 조건을 조사한다. 프로젝트 전용 검증 스킬에는 Launch, Doctor, Drive, Evidence, Cleanup과 기능 지도를 작성한다. 생성 후에는 그 절차로 한 기능을 실행하고, 정리 후에도 증거가 남아 있는지 확인해야 완성으로 인정한다.

[maintain-verification-skill](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/maintain-verification-skill/SKILL.md)은 소스가 정상처럼 보이는 경우에도 기능별 실제 조작을 요구한다. 검증 도구가 낡은 경우와 제품 자체가 고장 난 경우를 구분하며, 제품의 회귀를 설명 변경으로 덮지 않도록 범위를 제한한다.

Benny의 [기존 수정 검증 절차](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/automations/benny/skills/reproduce-and-fix-issues/references/verify-existing-fix.md)는 기준 버전에서 증상이 두 번 재현되고, 같은 환경의 수정 버전에서 기대 결과가 두 번 나타나야 성공으로 본다. 기준 버전에서 재현되지 않거나 어느 한쪽을 실행할 수 없으면 판정은 Inconclusive다.

우리의 평가다. 반복 작업을 맡기기 전에 관찰 수단을 산출물로 남기는 점이 유용하다. 수정 후 화면이 정상처럼 보이는 경우와 실제 결함을 해결한 경우를 구분할 근거도 있다. 이 장점은 해당 앱을 시작하고 조작할 수 있는 환경, 적절한 데이터와 관찰 가능한 성공 조건이 있을 때 성립한다. 도구가 없는 환경에서 지침만으로 같은 효과가 생기지는 않는다.

### 측정 기준과 개선 시도를 분리한다

소스에서 확인한 사실이다. [hillclimb](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/hillclimb.md)은 먼저 측정 도구가 서로 다른 현실적인 작업 조건을 구분하는지 확인하고, 그 도구를 고정한 뒤 실험한다. 한 변경마다 같은 방법으로 전후를 측정하고 회귀 검사를 실행한다. 잡음보다 큰 개선과 검사 통과를 함께 만족해야 채택하며, 실패한 변경은 되돌린다.

[benchmark-checklist](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/benchmark-checklist/SKILL.md)는 오류 수와 실제 작업량을 확인하고, 비교 대상의 실행 설정을 맞추며, 반복 측정과 사용자 경로 전체의 효과를 요구한다. 캐시로 생략된 작업, 빠른 오류 반환, 실행되지 않은 비동기 작업의 시간을 개선으로 오인하지 않도록 작성되어 있다.

우리의 평가다. 반복 수정이 목표 개선으로 이어졌는지를 판정하는 규칙이 구체적이다. 수정자가 결과에 맞춰 측정법이나 완료 조건을 바꾸는 위험을 줄일 수 있다. 다만 이는 절차상의 분리다. 고정한 도구가 처음부터 잘못된 요구를 측정하거나 에이전트가 도구를 바꾸는 것을 기술적으로 막지 못하면 잘못된 목표를 최적화할 수 있다.

### 검증 결과의 유효성을 전달 단계까지 추적한다

소스에서 확인한 사실이다. [shipping](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/shipping.md)은 작성자가 아닌 에이전트의 PR별 실제 검증을 요구한다. 판정에는 head SHA, base SHA와 `git patch-id`를 연결하고, 리베이스나 추가 변경 후 판정의 유효성을 다시 확인한다. 스택은 아래쪽부터 검증된 연속 구간만 병합하며, 병합 후 다음 PR의 상태를 다시 계산한다.

[autopilot-full](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/autopilot-full.md)은 구현 담당자의 코드 완성 보고와 별도의 검증 판정을 구분한다. 검토에서 입증된 결함은 구현 담당자에게 모아 전달하고, 패치가 바뀐 다음 회차에는 다시 검증한다. [interrogate](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/interrogate/SKILL.md)도 모델의 의견을 그대로 합산하지 않고 실행 경로와 실제 맥락을 통해 채택하거나 기각하도록 한다.

우리의 평가다. 코드 작성, 검토, 리베이스, 전달 사이에서 검증 대상이 바뀌는 문제를 다룬다. 에이전트 수 자체보다 무엇을 검증했고 그 결과가 지금도 유효한지를 관리하는 점이 중요하다.

한계도 있다. 같은 patch-id는 변경 내용의 동일성을 나타내지만 기반 코드, 의존성, 설정과 데이터의 동일성을 모두 증명하지는 않는다. Shipping의 판정 재사용 규칙은 환경 변화까지 포괄하는 완전한 실행 동등성 검사로 해석할 수 없다.

## 전체 구성

| 구성 | 수량 | 등록과 역할 |
| --- | --- | --- |
| 일반 스킬 | 25개 | 조사, 설계, 구현 지원, 검증, 기록과 개인화다. |
| 개발 원칙 스킬 | 24개 | 일반 스킬과 같은 skills 경로에 있는 판단 기준이다. |
| 일반 스킬 등록 대상 합계 | 49개 | manifest가 가리키는 skills 경로 아래의 SKILL.md 수다. |
| 내부 작업 절차 | 23개 | poteto-mode의 playbooks 파일이다. 별도의 독립 스킬 23개가 아니다. |
| 전용 서브에이전트 | 2개 | poteto-agent와 Comment Sicko다. |
| Benny 자동화용 정의 | 3개 | 일반 슬래시 스킬로 등록되지 않으며 두 자동화를 구성한다. |
| 실행 도구 | 주요 도구 5개와 bootstrap | PR 감시, 상태 관리, 계획 검사, worktree 조사, 결정 기록과 의존성 준비다. |

등록 대상 49개와 Benny 정의 3개를 합치면 SKILL.md는 52개다. 작업 절차와 에이전트, 스크립트는 이 숫자에 합산하지 않는다.

### 일반 스킬 25개

| 분류 | 스킬 원문 | 기능과 범위 |
| --- | --- | --- |
| 실행 | [poteto-mode](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/SKILL.md) | 요청을 작업 절차와 다른 스킬에 연결하는 중심 모드다. 후속 턴에도 유지되며 사용자가 해제할 수 있다. |
| 설정 | [setup-pstack](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/setup-pstack/SKILL.md) | 사용 가능한 모델과 추론 수준을 확인해 역할별 설정을 ~/.cursor/rules/pstack-models.mdc에 기록한다. |
| 실행 | [figure-it-out](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/figure-it-out/SKILL.md) | 기존 작업 절차가 맞지 않는 과제의 완료 조건, 실험 순서, 검증과 결정 기록 방법을 설계한다. |
| 기록 | [show-me-your-work](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/show-me-your-work/SKILL.md) | 결정, 이유, 증거와 결과를 TSV로 남기고 실제 대화 기록과 대조한다. |
| 조사 | [how](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/how/SKILL.md) | 현재 실행 흐름, 핵심 개념, 코드 위치와 책임을 설명한다. 넓은 범위는 병렬 탐색 후 합성한다. |
| 조사 | [why](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/why/SKILL.md) | 설계 이유와 이력을 Git, PR, 연결된 자료에서 조사한다. 확인 사실, 추론, 공백을 분리한다. |
| 맥락 복구 | [recall](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/recall/SKILL.md) | 현재 워크스페이스의 최근 대화와 공유 기록을 조사하고 Git과 PR의 현재 상태를 확인한다. |
| 설명 | [teach](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/teach/SKILL.md) | how와 why의 결과를 사람이 이해할 수 있는 설명으로 엮는다. 설명 깊이는 질문에 맞춘다. |
| 영향 조사 | [blast-radius](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/blast-radius/SKILL.md) | 변경의 안전성이 의존하는 핵심 전제를 찾고 실제 코드 실행으로 증명하도록 요구한다. |
| 설계 | [architect](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/architect/SKILL.md) | 호출자 사용법에서 타입, 서명과 모듈 경계를 도출한다. 후보 비교 후 기본적으로 구현까지 진행한다. |
| 후보 비교 | [arena](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/arena/SKILL.md) | 같은 과제의 여러 후보를 평가해 기준 후보를 선택하고 다른 후보의 유용한 부분을 통합한다. |
| 병렬 작업 | [swarm](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/swarm/SKILL.md) | 영역 분담, 동일 과제 경쟁이나 혼합 작업을 병렬로 수행하고 증거와 공백을 한 보고로 모은다. |
| 검토 | [interrogate](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/interrogate/SKILL.md) | 여러 모델이 동일 기준으로 변경을 검토한다. 주 에이전트가 채택, 고려, 참고, 기각으로 판정하며 자동 수정하지 않는다. |
| 버그 검증 | [tdd](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/tdd/SKILL.md) | 명시적 요청이나 저렴한 로컬 테스트 경로가 있을 때 실패하는 회귀 테스트부터 작성한다. 비실용적인 테스트는 강제하지 않는다. |
| 성능 검증 | [benchmark-checklist](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/benchmark-checklist/SKILL.md) | 병목, 비교 설정, 물리적 한계, 오류, 반복성, 사용자 경로의 효과와 실제 작업 수행을 검사한다. |
| 주석 정리 | [no-comments](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/no-comments/SKILL.md) | Comment Sicko의 주석 정리 결과를 검토하고 받아들인 구조 문제의 수정까지 수행할 수 있다. |
| TypeScript | [typescript-best-practices](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/typescript-best-practices/SKILL.md) | 판별 유니온, 브랜드 타입, 경계 검증, 스키마 유도와 누락 없는 분기 처리의 구체적 규칙이다. |
| 검증 기반 생성 | [create-verification-skill](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/create-verification-skill/SKILL.md) | 프로젝트 전용 검증 스킬과 기능 지도를 만든다. 실제 절차를 한번 실행해야 완성으로 본다. |
| 검증 기반 유지 | [maintain-verification-skill](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/maintain-verification-skill/SKILL.md) | 기능별 소스 조사와 실제 조작으로 검증 스킬의 낡은 내용을 수정한다. 제품 코드는 수정 범위에 넣지 않는다. |
| 문장 정리 | [unslop](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/unslop/SKILL.md) | AI 상투어, 과장, 군더더기, 형식적인 문장과 불필요한 전문 용어를 제거한다. |
| 쉬운 설명 | [bro](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/bro/SKILL.md) | 직전 답변을 더 쉽고 짧은 말로 다시 설명한다. |
| 기술 문서 | [technical-writing](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/technical-writing/SKILL.md) | Diátaxis로 문서 목적을 구분하고 Google 개발자 문체, STE와 Global English로 문장을 검토한다. |
| 개인화 | [automate-me](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/automate-me/SKILL.md) | 현재 워크스페이스의 반복된 작업 선호와 사용자 확인을 바탕으로 개인용 mode 스킬을 생성하거나 갱신한다. |
| 회고 | [reflect](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/reflect/SKILL.md) | 현재 대화를 세 관점에서 검토해 스킬 개선안을 만든다. Accepted 변경은 사용자의 명시적 승인 후 반영한다. |
| 봇 UI | [make-bot-ui](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/make-bot-ui/SKILL.md) | 서버가 웹훅으로 Grok Bot을 깨우는 UI를 구성한다. 송신 키 보관, 비밀 입력과 Tailscale 접근 설정을 다룬다. |

how는 현재 동작, why는 설계 이유, recall은 이전 작업 맥락, teach는 사람의 이해를 다룬다. arena의 결과는 후보를 통합한 산출물이고, swarm의 결과는 병렬 작업의 종합 보고다. interrogate는 현재 변경안에 대한 검토 판정이다.

### 개발 원칙 스킬 24개

모든 원칙의 실제 스킬 이름에는 principle- 접두사가 붙는다. poteto-mode는 필요한 원칙의 파일을 읽도록 요구하며, 사용자는 이름으로 작업 방향을 조정할 수 있다.

| 분류 | 원칙 원문 | 핵심 규칙 |
| --- | --- | --- |
| 기본 | [laziness-protocol](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-laziness-protocol/SKILL.md) | 삭제와 최소 변경을 우선하고 불필요한 계층과 추상화를 줄인다. |
| 기본 | [foundational-thinking](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-foundational-thinking/SKILL.md) | 로직보다 데이터 구조, 핵심 타입, 동시 작업의 공유 상태와 기반 작업의 순서를 먼저 정한다. |
| 기본 | [redesign-from-first-principles](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-redesign-from-first-principles/SKILL.md) | 새 요구가 처음부터 존재했다고 가정하고 전체 설계를 다시 생각한다. |
| 기본 | [attack-the-premise](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-attack-the-premise/SKILL.md) | 같은 전제에 기댄 수정이 반복 실패하면 관련 주체의 상태를 측정하고 전제를 검증한다. |
| 기본 | [subtract-before-you-add](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-subtract-before-you-add/SKILL.md) | 추가 전에 죽은 코드와 중복 검증, 불필요한 복잡성을 제거한다. |
| 기본 | [minimize-reader-load](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-minimize-reader-load/SKILL.md) | 읽는 사람이 추적할 계층과 기억할 상태를 줄인다. |
| 기본 | [outcome-oriented-execution](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-outcome-oriented-execution/SKILL.md) | 계획된 마이그레이션의 목표 구조를 우선한다. 중간 불안정은 범위와 검증 경계를 명시해야 한다. |
| 기본 | [experience-first](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-experience-first/SKILL.md) | 구현 편의보다 사용자와 유지보수자의 경험을 우선한다. |
| 기본 | [exhaust-the-design-space](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-exhaust-the-design-space/SKILL.md) | 선례 없는 설계는 구조적으로 다른 2~3개 대안을 비교한다. |
| 기본 | [build-the-lever](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-build-the-lever/SKILL.md) | 비단순 작업을 수행하거나 증명하는 재실행 가능한 스크립트, 생성기나 작업 스킬을 만든다. |
| 아키텍처 | [model-the-domain](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-model-the-domain/SKILL.md) | 흩어진 조건문 대신 상태 머신, 타입, 테이블 등의 구조로 도메인을 표현한다. |
| 아키텍처 | [boundary-discipline](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-boundary-discipline/SKILL.md) | 외부 입력 검증을 경계에 모으고 내부 타입과 순수 로직을 신뢰한다. |
| 아키텍처 | [type-system-discipline](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-type-system-discipline/SKILL.md) | 잘못된 상태를 표현할 수 없게 만들고 의미가 다른 값과 분기를 타입으로 구분한다. |
| 아키텍처 | [make-operations-idempotent](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-make-operations-idempotent/SKILL.md) | 재실행이나 중간 실패 후에도 같은 올바른 상태로 수렴하게 만든다. |
| 아키텍처 | [migrate-callers-then-delete-legacy-apis](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | 조정 가능한 내부 API는 호출자 이전과 기존 API 삭제를 함께 수행한다. |
| 아키텍처 | [separate-before-serializing-shared-state](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md) | 동시 작업의 쓰기 대상을 먼저 분리하고 실제 공유가 필요한 경우 구조적으로 직렬화한다. |
| 검증 | [prove-it-works](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-prove-it-works/SKILL.md) | 완료 선언 전에 실제 결과와 동작을 직접 확인한다. |
| 검증 | [fix-root-causes](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-fix-root-causes/SKILL.md) | 재현과 계측으로 근본 원인을 수정하고 증상을 숨기는 우회책을 경계한다. |
| 검증 | [sequence-verifiable-units](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-sequence-verifiable-units/SKILL.md) | 작은 단위를 검증한 뒤 다음 단위로 진행하며 전달 순서도 증거가 되도록 구성한다. |
| 검증 | [test-behavior-not-implementation](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-test-behavior-not-implementation/SKILL.md) | 내부 호출 방식이나 상수의 복사보다 사용자가 관찰할 결과를 검사한다. |
| 검증 | [explain-the-number](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-explain-the-number/SKILL.md) | 측정값의 병목과 의미를 설명하고 오류, 생략된 작업, 잡음 등의 대안을 확인한다. |
| 위임 | [guard-the-context-window](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-guard-the-context-window/SKILL.md) | 큰 자료는 분리 처리하고 주 대화에는 필요한 요약을 유지한다. |
| 위임 | [never-block-on-the-human](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-never-block-on-the-human/SKILL.md) | 되돌릴 수 있는 작업은 합리적으로 진행한다. 제품 방향과 비가역 행동은 확인한다. |
| 개선 | [encode-lessons-in-structure](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/principle-encode-lessons-in-structure/SKILL.md) | 반복 지침을 타입, 린트, 런타임 검사나 자동화로 구현한다. |

### poteto-mode의 내부 작업 절차 23개

| 작업 절차 원문 | 결과와 완료 경계 |
| --- | --- |
| [investigation](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/investigation.md) | 읽기 중심 조사와 근거 있는 설명 또는 추천이다. 코드 변경이나 PR 생성은 요구하지 않는다. |
| [bug-fix](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/bug-fix.md) | 실제 재현, 원인 규명, 수정, 동일 경로 검증을 수행한다. |
| [perf-issue](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/perf-issue.md) | 기준 성능과 트레이스를 수집하고 측정된 병목을 수정해 비교한다. |
| [hillclimb](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/hillclimb.md) | 고정된 지표와 측정법으로 실험을 반복하고 개선된 변경만 채택한다. |
| [runtime-forensics](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/runtime-forensics.md) | 실행 중 프로세스를 계측해 원인을 진단한다. 수정은 별도 요청의 범위다. |
| [trace-forensics](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/trace-forensics.md) | 이미 수집된 프로파일이나 트레이스를 분석한다. 짝이 되는 자료가 없으면 원인 확인의 한계를 표시한다. |
| [feature](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/feature.md) | 설계와 데이터 구조를 정한 뒤 기능을 구현하고 실제 동작을 검증한다. |
| [refactoring](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/refactoring.md) | 기존 동작을 고정한 검사를 유지하며 구조를 변경한다. |
| [prototype](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/prototype.md) | 설계 결정을 위한 빠른 실험이다. 결과물은 버릴 수 있는 시제품과 결정 근거다. |
| [visual-parity](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/visual-parity.md) | 변경 전 기준 이미지를 유지하고 이미지 차이로 시각적 동일성을 검사한다. |
| [authoring-a-skill](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/authoring-a-skill.md) | 스킬을 작성하거나 수정하고 frontmatter와 파일 참조를 확인한다. |
| [eval](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/eval.md) | 후보와 평가자를 눈가림해 스킬이나 프롬프트 변경의 효과를 조사한다. |
| [babysit](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/babysit.md) | PR의 리뷰와 CI를 관리해 병합 준비 상태까지 진행한다. 병합 권한을 뜻하지 않는다. |
| [shipping](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/shipping.md) | PR별 독립 검증 후 스택 아래쪽부터 검증된 연속 구간을 병합한다. |
| [autonomous-run](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/autonomous-run.md) | 확인 가능한 완료 조건까지 반복 작업을 수행한다. 진짜 막힘은 드러내며 기준을 낮춰 성공으로 만들지 않는다. |
| [orchestrate](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/orchestrate.md) | 단일 세션을 넘어서는 프로젝트를 작업 단위, 담당자, 상태, 검증 기록과 병합 순서로 조율한다. |
| [autopilot-full](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/autopilot-full.md) | 독립 PR별 담당자가 구현부터 병합까지 수행한다. 주 에이전트의 해당 패치에 대한 검증 판정이 필요하다. |
| [autopilot-stack](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/autopilot-stack.md) | 검증된 PR을 선형 스택으로 구성한다. 최종 병합은 사용자가 담당한다. |
| [session-pickup](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/session-pickup.md) | 이전 작업 기록과 현재 Git 상태를 복구해 남은 과제로 연결한다. |
| [pause-safely](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/pause-safely.md) | 안전한 작업 경계에서 멈추고 변경과 재개 정보를 보존한다. |
| [multi-phase-plan](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md) | 여러 단계와 PR의 의존 관계, 작업 항목과 검증 조건을 계획으로 작성한다. 실행은 별도 시작 요청을 기다린다. |
| [worktree-cleanup](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/worktree-cleanup.md) | 사용 여부와 미커밋 변경을 확인해 worktree와 시뮬레이터 등의 정리를 수행한다. |
| [opening-a-pr](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/opening-a-pr.md) | 작업 분리, 커밋 순서, PR 제목과 본문, 스택의 기준 브랜치와 공개 준비 상태를 정한다. |

Babysit은 병합 준비, Shipping은 실제 전달과 병합을 담당한다. Autopilot-full은 병합 권한이 주어진 독립 PR에, Autopilot-stack은 사람이 검토하고 병합할 스택에 맞춘다. Opening a PR을 모든 조사와 진단의 일률적 종료 단계로 해석해서는 안 된다. Investigation과 forensics에는 PR을 만들지 않는 별도 완료 경계가 있다.

### 전용 서브에이전트 2개

| 에이전트 원문 | 역할 |
| --- | --- |
| [poteto-agent](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/agents/poteto-agent.md) | poteto-mode 전체와 원칙 목록을 읽고 같은 실행 방식으로 작업하는 위임 대상이다. |
| [Comment Sicko](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/agents/comment-sicko.md) | 부모가 지정한 범위의 주석을 정리하고, 주석이 드러낸 구조 문제를 MUST KILL로 지적한다. 애플리케이션 코드 수정은 맡지 않는다. |

Comment Sicko는 법률과 라이선스, 변경할 수 없는 외부 제약, 공개 API 계약 등의 예외만 주석 보존 사유로 인정한다. 우리의 평가로는 이는 정확성 검증보다 강한 코드 취향 정책에 가깝다. 주석 삭제 자체를 구현 품질이나 문제 해결의 증거로 사용해서는 안 된다.

소스 표현에도 차이가 있다. README는 이 에이전트를 read-only reviewer로 소개하지만, 에이전트 지침과 no-comments 흐름은 주석 삭제와 그 diff의 검토를 전제한다. 따라서 read-only라는 소개만으로 실제 쓰기 범위를 판단할 수 없다.

### Benny 자동화 팩

Benny는 [별도 설정이 필요한 자동화 팩](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/automations/benny/README.md)이다. 일반 스킬 등록 경로에 포함되지 않는다. [설정 진입 문서](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/automations/benny/FOR_AGENTS.md)를 통해 대상 저장소의 .cursor/automations/benny에 팩을 배치하고, 공유 스킬을 사용할 수 있도록 pstack을 활성화한다.

| 자동화용 정의 원문 | 역할과 조건 |
| --- | --- |
| [setup-benny](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/automations/benny/skills/setup-benny/SKILL.md) | Slack, 저장소, 이슈 추적기, 모델, 조작 도구, 기능 지도와 예산을 설정한다. 자동화 생성과 활성화에는 별도 사용자 요청과 검토가 필요하다. |
| [triage-issue-reports](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/automations/benny/skills/triage-issue-reports/SKILL.md) | 보고와 첨부 자료를 읽고 원인을 제한적으로 조사해 분류한다. 중복을 검색하고 명확한 새 버그만 등록하며 원래 스레드에 판정한다. |
| [reproduce-and-fix-issues](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md) | 신뢰된 분류 결과를 받아 실제 UI에서 두 번 재현한다. 기존 수정안을 검증하거나 제한된 수정을 수행해 전후 증거가 있는 Draft PR을 만든다. |

두 자동화의 연결은 원래 스레드의 [benny:bug], [benny:performance], [benny:other] 표식으로 이뤄진다. 재현 자동화는 설정된 분류 담당자의 표식만 신뢰한다. 원래 채널과 스레드 좌표를 유지하며, 보고가 이미 다른 사람의 수정 대상이거나 기존 PR과 커밋이 있으면 경쟁 구현을 시작하지 않는다.

[앱 조작 도구의 계약](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/automations/benny/skills/reproduce-and-fix-issues/references/control-adapter.md)은 앱 시작, 사용자 조작, 읽기 전용 상태 확인, 화면 캡처, 녹화, 초기화와 정리를 요구한다. 내부 상태를 직접 조작해 증상을 만들 수 없다. 필수 기능이나 설정이 없으면 재현과 수정은 중단한다.

확인된 재현과 원인이 있어야 제한된 수정을 시작한다. 수정 전후 검증과 관련 동작 검사 후 Draft PR까지만 열며, 이 흐름은 병합과 배포를 수행하지 않는다. 소스 채널의 게시자는 조정자 한 명으로 제한하고, 위임한 작업자에게 Slack 쓰기 기능과 자격증명을 주지 않도록 한다. 실제 도구 격리 가능 여부는 이번 조사에서 확인하지 않았다.

### 실행 도구와 참고 자료

| 도구 원문 | 소스에서 확인한 기능 | 검증상의 경계 |
| --- | --- | --- |
| [watch-pr](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/scripts/watch-pr/cli.ts) | GitHub PR이나 스택의 CI, 리뷰, 충돌과 병합 상태를 조회하고 JSON 또는 표로 출력한다. | 외부 PR 상태를 관찰한다. 제품의 실제 기능을 검증하는 도구는 아니다. |
| [orch](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/scripts/orch/orch.ts) | 작업 단위, 검증 기록, 완료 알림, 승인 대기, 스택 상태와 진행 집계를 파일로 관리한다. | 상태 보존과 조회를 구현한다. 기록된 제품 검증의 진실성은 별도 확인이 필요하다. |
| [check-plan.mjs](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/scripts/check-plan.mjs) | 계획의 구조, PR별 항목, 10개 라이브 검증 경로와 문장 규칙을 검사한다. | 계획 형식을 확인한다. 적힌 검사가 실제 실행됐다는 증거가 아니다. |
| [worktree-audit.sh](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/scripts/worktree-audit.sh) | worktree의 용량, 변경, PR과 최근 대화 상태를 조사해 정리 후보를 분류한다. | 이 스크립트 자체는 worktree를 삭제하지 않는다. 후보 분류는 사용 여부의 최종 증명이 아니다. |
| [log.sh](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/show-me-your-work/scripts/log.sh) | 시간과 함께 TSV 결정을 추가하고 탭, 줄바꿈과 스프레드시트 수식으로 해석될 입력을 처리한다. | 행의 형식은 다룬다. 결정과 증거 내용의 정확성을 검사하지 않는다. |
| [bootstrap.ts](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/scripts/bootstrap.ts) | package.json과 bun.lock 기준으로 도구 의존성을 준비한다. | 도구 준비 기능이다. 이번 조사에서는 설치와 실행을 수행하지 않았다. |

orch의 [저장 구현](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/scripts/orch/store.ts)에는 파일 잠금, 죽은 PID의 잠금 복구, 원자적 파일 교체와 PR 및 SHA 기반 기록 조회가 있다. 이런 상태 관리의 일부는 코드로 구현된 장치다. 그러나 ledger.record는 판정과 증거 문자열을 입력받아 저장한다. 증거 파일이나 링크의 실재, 검사 실행 결과와 검토자 독립성을 확인하지 않으며, ledger.check도 해당 PR과 SHA의 행을 조회하는 기능이다.

참고 자료에는 설계 후보의 판단 기준, 검토 평가표, 조사자와 합성자 프롬프트, 증거 신뢰도 기준, TypeScript 예제와 기능 지도 예제가 있다. [사용자 가이드](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/docs/guide/README.md)는 설치, 모드 사용, 코드 이해, 설계, 구현과 정리, 검증과 전달, 야간 작업, 원칙, 개인화, 사용 예와 주의점의 10장으로 구성된다.

## 환경과 외부 의존성

소스에서 확인한 배포 범위다. [manifest](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/.cursor-plugin/plugin.json)는 skills와 agents 경로를 등록한다. MCP 서버와 외부 서비스 연결을 이 플러그인에 함께 제공하는 구성은 아니다.

| 구성요소 | 공급 위치 또는 조건 |
| --- | --- |
| deslop, control-ui, control-cli | pstack 밖의 cursor-team-kit 플러그인에서 제공한다. |
| create-skill, /loop, Benny 설정의 /automate | Cursor 내장 기능을 사용한다. |
| Task, 클라우드 에이전트, 대화 기록과 웹훅 자동화 | Cursor 환경의 기능과 경로를 전제로 한다. |
| 일반 PR 작업 | gh를 기본으로 하고 사용 가능한 Origin CLI를 선택할 수 있다. |
| orchestrate의 스택 상태 계산 | 이 작업 절차와 orch의 frontier 관리는 Graphite gt를 사용한다. |
| 실행 도구 | 도구에 따라 Bun, Node, Bash와 gh 등이 필요하다. OS별 명령의 실제 호환성은 미검증이다. |
| Benny | Slack과 이슈 추적기 접근, 실제 앱 조작 도구와 작성된 기능 지도가 필요하다. |

why는 사용 가능한 도구를 발견해 소스 관리, 이슈 추적기, 장문 문서, 팀 채팅, 인프라 관측, 오류 추적과 제품 분석 자료의 일곱 종류를 조사한다. 연결이 없는 종류는 조사 공백으로 표시한다. 발견할 수 있다는 지침은 그 연결이나 접근 권한을 제공한다는 뜻이 아니다.

조사 커밋의 setup-pstack 기본 설정은 코드에 grok-4.7-xhigh-fast, 어려운 판단과 글에 claude-opus-5-5-max를 사용한다. 비교와 검토 패널에는 이 두 모델과 gpt-5.6-sol-max가 들어간다. 역할별 설정은 바꿀 수 있고 auto와 inherit-parent는 부모 모델을 사용한다. unlimited, large, medium, small은 추론 수준 선택이다. 실제 비용의 상한을 보장하는 설정으로 해석할 수 없다.

poteto-mode의 외부 쓰기 자율성 지침, reflect의 일부 후속 처리, PR 공개 절차는 이 저장소의 사용자 권한과 Git 정책을 대신하지 않는다. 설치하거나 이식할 때 실제 도구 권한과 승인 범위를 별도로 맞춰야 한다.

## 비판적으로 봐야 할 한계

| 쟁점 | 소스에서 확인한 사실 | 우리의 평가 |
| --- | --- | --- |
| 제품 검증의 강제력 | 실제 경로 검증과 판정 무효화는 주로 스킬 지침이다. orch는 입력받은 기록을 저장한다. | 지침 준수가 무너지면 그럴듯한 증거 문자열만으로 완료를 주장할 여지가 있다. 기록과 실행 증명은 구분해야 한다. |
| 실행 환경의 준비 | 앱 조작 도구, 데이터, 계정과 관찰 방법이 필요하며 일부 기능은 다른 플러그인에 의존한다. | 설치만으로 어떤 앱에서도 정확한 검토를 수행한다는 기대는 근거가 부족하다. |
| 판정의 재사용 | Shipping은 patch-id와 일부 빌드 비교를 통해 기존 검증의 재사용을 허용한다. | 동일 패치라도 기반 코드, 의존성, 설정과 데이터가 바뀌면 의미가 달라질 수 있다. 환경 조건까지 연결된 증거가 더 강하다. |
| 검토의 독립성 | interrogate의 모델들은 같은 의도 설명과 평가 기준을 받는다. | 모델 다양성은 공통으로 잘못된 요구나 기준을 보완하지 못할 수 있다. 합의만으로 정확성을 증명할 수 없다. |
| 절차 비용 | multi-phase-plan은 PR별 10개 라이브 검증 경로와 성능 검증을 요구한다. | 고정된 수량은 실제 위험보다 절차 수를 우선할 수 있다. 완료율과 결함 검출의 이득 대비 비용은 미측정이다. |
| 코드 취향의 영향 | no-comments와 일부 설계 원칙은 강한 삭제, 재설계와 위임 규칙을 가진다. | 작은 변경에도 그대로 적용하면 문제 해결과 무관한 수정이나 조율을 늘릴 수 있다. 코드 취향과 정확성 근거를 분리해야 한다. |
| 복구와 장기 실행 | Orchestrate는 상태 저장과 재시작 복구를, 자율 작업 절차는 재시도와 막힘 보고를 규정한다. | 기록은 복구 가능성을 높이지만 실제 소유권, 살아 있는 프로세스와 검증의 유효성을 다시 확인해야 한다. 장기 무인 성공은 미검증이다. |

다단계 계획의 고정 검증 수량은 [multi-phase-plan](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md)과 [검사 코드](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/poteto-mode/scripts/check-plan.mjs)에서 확인했다. 검토의 판단 기준은 [review rubric](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/interrogate/references/rubric.md)과 [lead judgment](https://github.com/cursor/plugins/blob/23e4138daa01c42d4969f7a5465f82704e64f798/pstack/skills/interrogate/references/lead-judgment.md)에서 확인했다.

정확한 완료를 평가할 때는 구현 결과, 관찰 방법, 판정 기준과 전달 대상을 함께 봐야 한다. 구현자와 다른 모델이 검사했거나 형식 검사가 통과했다는 사실만으로 이 네 요소가 맞는다고 할 수 없다.

## 우리 작업 방식에 참고할 적용 후보

이 항목은 조사에서 도출한 제안이다. 현재 저장소의 구현 상태나 승인된 변경 계획을 뜻하지 않는다.

| 우선순위 | 적용 후보 | 도입 조건 |
| --- | --- | --- |
| 높음 | 프로젝트 전용 실행과 검증 경로를 만들고 실제로 한번 수행한다. | 기존 도구를 재사용하고 사용자 행동, 실제 부작용, 정리 후 증거 보존을 확인한다. |
| 높음 | 변경 전에 실패 또는 기준 동작을 관찰하고 동일 조건으로 수정 후를 비교한다. | 기준이 재현되지 않으면 성공 판정을 보류한다. 테스트 경로가 과도하면 적절한 실행 증거를 선택한다. |
| 높음 | 검증 기준과 측정 도구를 구현 변경과 분리한다. | 도구의 민감도를 먼저 확인한다. 실패한 변경을 되돌리고 관찰 기준을 낮춰 완료시키지 않는다. |
| 높음 | 검증 결과를 코드와 환경 조건에 연결한다. | 코드 버전 외에 중요한 의존성, 데이터, 설정과 실행 조건이 바뀌었는지 확인한다. |
| 중간 | 상태와 완료 알림을 파일과 외부 시스템의 실제 상태로 보존한다. | 기록 도구가 성공을 증명한다고 간주하지 않는다. 복구 시 소유권과 실제 산출물을 확인한다. |
| 선택적 | 별도 검토자와 병렬 탐색을 사용한다. | 위험이나 독립된 작업 범위가 조율 비용을 정당화할 때 사용한다. 모델 수를 완료 기준으로 삼지 않는다. |

고정된 10개 검증 경로, 모든 PR의 성능 검사, 일률적인 주석 제거는 우선 적용 후보로 평가하지 않았다. 구체적인 실패를 잡거나 실제 결정을 돕는 근거가 있는 경우에만 별도로 검토할 요소다.

## 이번 조사에서 검증하지 않은 범위

- Cursor에 pstack을 설치하고 전체 작업 절차를 실행하지 않았다.
- 프로젝트 전용 검증 스킬을 생성하거나 실제 앱의 수정 전후를 실행하지 않았다.
- Benny의 Slack, 이슈 추적기, 웹훅과 PR 생성 연동을 실행하지 않았다.
- 소스에 포함된 도구 테스트와 타입 검사를 실행하지 않았다.
- 장기 자율 실행의 완료율, 결함 검출률, 오탐률, 시간과 비용을 비교 측정하지 않았다.
- 조사 커밋 이후의 변경과 사용자 환경에서의 모델 사용 가능 여부는 확인하지 않았다.

따라서 이 문서는 구성과 구현 일부에 근거한 설계 평가다. pstack의 실제 운영 성과나 모든 환경에서의 동작 보증으로 인용해서는 안 된다.
