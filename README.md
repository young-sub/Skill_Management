# Agentic Coding Plugin

이 저장소는 기존 Skill을 `agentic-coding` 플러그인으로 묶어 업무 위임 → 실제 검증 → 결과 조회 → 피드백 수리와 기준 재사용을 연결합니다. `agent-workflow`가 단일 진입점이며, 프로젝트의 요구사항·코드·검증 명령을 사용합니다. 공개 Skill과 canonical source도 계속 관리합니다.

## 시작하기

플러그인 사용은 [패키지 시작 안내](distribution/README.md), 빌드·호스트 연결은 [플러그인 가이드](docs/plugins.md)를 따릅니다. 패키지의 안내 링크는 배포 내부 기준입니다. 현재 기능의 검증 범위와 한계는 [완성도 평가](docs/research/agent-coding-system-direction.md#현재-완성도--2026-10-18)에 있습니다.

- 에이전트 구현 문서: [`docs/index.md`](docs/index.md)
- 기계 판독 설정: [`.harness/project.yaml`](.harness/project.yaml)
- 공개 Skill: `skills/`
- 로컬 플러그인 생성·검증: [`docs/plugins.md`](docs/plugins.md)
- canonical source와 생성 매핑: `authoring/`

독립 구현의 병렬 분담·재개·통합은 [`swarm`](skills/swarm/SKILL.md)이 담당합니다. 독립 검토는 `multi-agent-review`에 남기며, 각 Agent의 완료 보고 뒤 통합된 실제 동작을 확인합니다.

설계 판단은 [`architect`](skills/architect/SKILL.md)가 호출자·타입·상태·데이터 소유권·모듈 경계를 따라 담당합니다. 작업 계약은 `design-goal`이 관리하며 작은 수정에는 설계 문서나 계약을 강제하지 않습니다.

공개 Harness Skill은 `setup-agent-harness`, `explore-idea`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, `maintain-agent-harness`입니다. 기존 v2.0.0 배포 사실은 [`docs/releases/v2.0.0.md`](docs/releases/v2.0.0.md)에 역사적 릴리스 증거로 남아 있으며, 현재 workflow authority는 아닙니다.

업무 조정에는 `agent-workflow`, 최초 제품 검증 연결에는 `setup-project-verification`, Feature·검증 가이드·UI 기준의 drift 수리에는 `maintain-project-verification`을 제공합니다. 프로젝트 로컬에 설치한 새 세션에서 “상품 저장 기능을 검증하고 무엇을 확인했는지 보여줘”, “개발 체계를 점검하고 필요한 부분을 개선해줘”처럼 업무를 요청합니다. 필요한 능력을 선택하고 기존 프로젝트 명령을 사용하며, “기존 결과만 보여줘”는 재실행하지 않습니다. 실제 사용 가능 범위는 프로젝트의 실행 환경과 검증 근거에 달려 있습니다.

“그 방향을 교정해줘”, “이 결과를 다음에도 재현할 절차로 남겨줘”는 [교정·성공 재사용](authoring/references/feedback-and-success.md)으로 연결하며 기존 소유자·발견 개선을 우선합니다.

프론트엔드 작업에는 `impeccable`(화면 설계·UX), `vercel-react-best-practices`(React/Next.js 구현·성능), `fixing-accessibility`(키보드·포커스·폼 접근성) 중 필요한 역할만 선택합니다. 기존 기술 스택과 컴포넌트를 우선하며 실제 브라우저 검증은 별도로 수행합니다.

한글 양식 작성·채움·검증 작업에는 독립 공개 Skill인 `hwp-form-fill`을 선택합니다.

## 개별 Skill 설치가 필요한 경우

대상 프로젝트 루트에서 실행한 뒤 설치할 Skill과 적용 범위를 선택합니다. 전체 흐름에는 `setup-agent-harness`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, `maintain-agent-harness`를 선택하고, 아이디어 탐색이 필요하면 `explore-idea`를 추가합니다. 적용 범위는 사용할 에이전트와 Project를 선택합니다. `-g`를 사용하지 않으므로 프로젝트 로컬에 설치됩니다.

```powershell
npx skills add git@github.com:young-sub/Skill_Management.git
```

설치 후 새 에이전트 세션을 시작하고 프로젝트 상태에 맞게 적용합니다.

### 새 프로젝트

프로젝트 디렉터리와 Git 저장소를 먼저 만든 뒤 위 명령으로 Skill을 설치합니다.

```text
$setup-agent-harness로 이 새 저장소에 Agent Harness를 설정해줘.
```

### 기존 프로젝트 — Harness 미적용

위 명령으로 Skill을 설치한 뒤 기존 구조를 보존하는 brownfield 설정을 요청합니다. Skill은 코드, 테스트, 문서와 명령을 먼저 조사하고 필요한 Harness 파일을 제안합니다.

```text
$setup-agent-harness로 기존 구조를 먼저 조사하고 이 저장소에 Agent Harness를 설정해줘.
```

### 기존 프로젝트 — 이전 Harness 설정 적용

위 명령으로 같은 이름의 Harness Skill을 최신 배포본으로 다시 설치한 뒤 마이그레이션을 요청합니다. 선택하지 않은 기존 Skill은 자동 삭제되지 않으며, 폐기된 `project-agent-bootstrap` 별칭이나 기존 구조의 삭제·이동은 조사 결과와 승인 후 정리합니다.

```text
$setup-agent-harness로 기존 설정을 조사하고 현재 Agent Harness 구성으로 마이그레이션해줘. 삭제나 이동은 적용 전에 계획을 보여줘.
```

## 검증

```powershell
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

외부 설치 smoke는 네트워크에서 코드를 내려받아 실행하므로 별도 명시적 승인이 필요합니다. 저장소 변경만으로 push, publish, release, protected branch merge를 수행하지 않습니다.

## 외부 Skill 출처

- [Impeccable](https://github.com/pbakaus/impeccable) — Apache-2.0
- [Vercel React Best Practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) — MIT
- [fixing-accessibility](https://github.com/ibelick/ui-skills/tree/main/skills/fixing-accessibility) — MIT
