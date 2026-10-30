# Agentic Coding Plugin

이 저장소는 기존 Skill을 `agentic-coding` 플러그인으로 묶어 업무 위임 → 실제 검증 → 결과 조회 → 피드백 수리와 기준 재사용을 연결합니다. `agent-workflow`가 단일 진입점이며, 프로젝트의 요구사항·코드·검증 명령을 사용합니다. 공개 Skill과 canonical source도 계속 관리합니다.

## Marketplace 설치

패키지를 직접 빌드할 필요 없이 GitHub marketplace에서 설치합니다. Python과 Git, 플러그인 기능을 지원하는 호스트가 필요합니다. 비공개 저장소라면 GitHub 접근 권한도 필요합니다.

**Codex — 터미널에서:**

```powershell
codex plugin marketplace add young-sub/Skill_Management --sparse .agents --sparse plugins
codex plugin add agentic-coding@agentic-coding
```

**Claude Code — 터미널에서:**

```powershell
claude plugin marketplace add young-sub/Skill_Management --sparse .claude-plugin plugins
claude plugin install agentic-coding@agentic-coding
```

### SSH 설치

Codex:

```powershell
codex plugin marketplace add git@github.com:young-sub/Skill_Management.git --sparse .agents --sparse plugins
codex plugin add agentic-coding@agentic-coding
```

Claude Code:

```powershell
claude plugin marketplace add git@github.com:young-sub/Skill_Management.git --sparse .claude-plugin plugins
claude plugin install agentic-coding@agentic-coding
```

`--sparse`는 설치에 필요한 marketplace 목록과 `plugins/`만 받습니다. 평가·문서·백업 파일은 설치 경로에 내려받지 않습니다. 이미 sparse 없이 등록했다면 같은 이름을 지운 뒤 다시 등록하거나, Codex는 `config.toml`의 해당 marketplace에 `sparse_paths = [".agents", "plugins"]`를, Claude Code는 marketplace source에 `sparsePaths`를 추가한 뒤 새로고침합니다.

GitHub SSH 키가 필요합니다. SSH에 `ys` 별칭을 설정했다면 주소의 `git@github.com:`을 `git@ys:`로 바꿀 수 있습니다. 이미 같은 marketplace를 등록했다면 중복 등록할 필요는 없습니다.

설치 후 새 세션을 시작합니다. Codex에서는 `agentic-coding:agent-workflow`를 선택하고, Claude Code에서는 `/agentic-coding:agent-workflow`로 요청합니다. hook 신뢰 검토가 필요한 호스트에서는 별도로 내용을 확인합니다. 설치 성공과 실제 업무 성공은 별도로 확인합니다.

Codex가 `plugin add`를 지원하지 않으면 등록 후 데스크톱 앱의 Plugins Directory에서 `agentic-coding` 소스를 선택해 설치합니다. 기존 `agentic-coding-local` 개발 설치나 개별 스킬은 자동 삭제하지 않습니다. 중복 설치가 있으면 사용할 플러그인을 선택하고 실제 로드 경로를 확인합니다.

업데이트는 호스트의 marketplace 새로고침과 플러그인 업데이트 기능을 사용합니다. 설치 캐시는 직접 수정하지 않습니다. 로컬 캐시 수정이 있다면 먼저 보존합니다. 저장소의 `update_plugin.py`는 별도 로컬 marketplace 전용이며 Git 원격 marketplace를 교체하는 도구가 아닙니다.

### 선택 설치 — 외부 플러그인

같은 marketplace에 외부 저장소의 플러그인 두 개를 선택 항목으로 등록했습니다. `agentic-coding`과 별개로 필요한 것만 설치합니다. 항목은 커밋을 고정하지 않고 각 저장소의 기본 브랜치를 따르므로, 원작자가 업데이트해도 아래 명령은 그대로입니다. 내용은 원작자가 관리하며 이 저장소에서 검토하거나 수정하지 않습니다.

| 플러그인 | 원본 | Claude Code | Codex |
|---|---|---|---|
| `diagram-design` | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) (MIT) | `claude plugin install diagram-design@agentic-coding` | `codex plugin add diagram-design@agentic-coding` |
| `humanize-korean` | [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) (MIT) | `claude plugin install humanize-korean@agentic-coding` | `codex plugin add humanize-korean@agentic-coding` |

최신 버전 받기: Claude Code는 `claude plugin marketplace update agentic-coding` 후 `claude plugin update <이름>@agentic-coding`을 실행하거나, `/plugin` → Marketplaces에서 이 marketplace의 auto-update를 켭니다(외부 marketplace는 기본값이 꺼짐). 두 플러그인은 자체 `plugin.json`에 `version`을 적어 두므로, 원작자가 버전 번호를 올린 커밋부터 업데이트로 인식됩니다. Codex의 `diagram-design`은 `codex plugin marketplace upgrade agentic-coding` 후 `codex plugin add diagram-design@agentic-coding`을 다시 실행합니다.

#### Codex의 `humanize-korean`

im-not-ai의 Codex용 폴더는 저장소 루트의 스크립트와 심볼릭 링크에 의존하므로, 원본을 marketplace 항목으로 직접 받으면 동작하지 않습니다. Codex에는 이 저장소의 `plugins/humanize-korean-codex` 실행기를 설치합니다. 실행기에는 윤문 규칙이 없고, 스킬을 사용할 때 `scripts/sync_upstream.py`가 원본을 받아 둔 사본으로 원본 Codex 스킬을 그대로 실행합니다.

- 처음 사용할 때 원본 저장소를 `CODEX_HOME`(없으면 `~/.codex`)의 `vendor/im-not-ai/`에 받고, 심볼릭 링크를 실제 폴더로 바꾼 사본을 만듭니다. Git, Python, github.com 접속이 필요합니다.
- 받은 지 24시간이 지났거나 최신으로 받아 달라고 요청하면(`--refresh`) 원본의 기본 브랜치를 다시 받습니다. 실행기 설치 명령은 바꾸지 않습니다.
- Codex 샌드박스가 네트워크를 막으면 받기 단계에서 권한 승인을 요청합니다. 거부하거나 오프라인이면 이미 받은 사본으로 계속 실행하고, 사본이 없으면 원인을 알리고 멈춥니다.
- 받은 원본이 Codex 스킬 구성을 잃으면 새 사본을 쓰지 않고 이전 사본을 유지합니다. `vendor/im-not-ai/repo`가 원본 저장소의 checkout이 아니면 건드리지 않고 멈춥니다.
- 원본 코드는 이 저장소에서 검토하지 않은 상태로 실행됩니다.

실행기 자체는 이 저장소가 바뀔 때만 `codex plugin marketplace upgrade agentic-coding` 후 `codex plugin add humanize-korean@agentic-coding`으로 다시 설치합니다. `codex plugin remove humanize-korean@agentic-coding`은 받아 둔 원본을 지우지 않으므로 `vendor/im-not-ai/` 폴더를 직접 삭제합니다.

설치 형식: [OpenAI marketplace 안내](https://developers.openai.com/plugins/build/plugins), [Claude Code marketplace 안내](https://code.claude.com/docs/en/plugin-marketplaces).

## 전역 지침 선택 설치 — 저장소 clone 필요

플러그인 설치만으로 전역 지침이 바뀌지는 않습니다. 설치 도구는 이 저장소의 `scripts/install_global_guidance.py`, 지침 원본은 `authoring/global/AGENTS.md`입니다. Python이 필요하며, 아래는 원하는 작업 폴더에서 처음 한 번 실행합니다.

```powershell
git clone --branch main git@github.com:young-sub/Skill_Management.git
Set-Location Skill_Management
```

이미 clone했다면 해당 폴더로 이동해 사용자 변경을 먼저 확인한 뒤 `git pull --ff-only`로 최신 main을 받습니다. 플러그인 캐시 내부에서 실행할 명령이 아닙니다.

**Codex — 변경 내용 확인 후 적용:**

```powershell
python scripts/install_global_guidance.py --host codex
python scripts/install_global_guidance.py --host codex --apply
```

**Claude Code — 변경 내용 확인 후 적용:**

```powershell
python scripts/install_global_guidance.py --host claude
python scripts/install_global_guidance.py --host claude --apply
```

사용하는 호스트의 명령만 선택합니다. 기본 명령은 대상 경로와 diff를 보여주며 파일을 쓰지 않습니다. `--apply`를 붙여야 적용합니다. Codex는 `CODEX_HOME`(없으면 `~/.codex`)의 `AGENTS.md`, Claude Code는 `CLAUDE_CONFIG_DIR`(없으면 `~/.claude`)의 `CLAUDE.md`를 사용합니다. 앱이 계정별 home을 쓰면 실제 경로를 확인하고 두 명령 모두 `--home "실제 home 경로"`를 추가합니다.

기존 사용자 문구는 유지하고 표시된 관리 구역만 갱신합니다. 기존 파일과 메타데이터는 선택한 home의 `back-up/global-guidance/`에 보존하며, 같은 내용을 다시 적용해도 중복 추가하지 않습니다. Codex의 `AGENTS.override.md`가 있거나 관리 구역이 모호하면 자동 덮어쓰기 대신 중단합니다. 기존 규칙과 새 지침의 의미 충돌은 미리보기에서 직접 확인해야 합니다. 적용 후 새 세션을 시작합니다.

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

개별 스킬도 현재 main의 최신 배포본을 사용합니다. `@latest`는 설치 도구 버전이며, 스킬 내용은 저장소 main에서 받습니다. 기존 설치본은 main 갱신만으로 자동 변경되지 않으므로 같은 설치 명령으로 원하는 스킬과 범위를 다시 선택합니다.

검증 실행에 필요한 capture 도구는 해당 스킬 안에 포함되어 `--run-check`나 플러그인 설치가 필요하지 않습니다. 프로젝트 자체의 테스트 명령과 실행 환경은 여전히 필요합니다. Harness 전체 흐름의 여섯 스킬은 기존 안내대로 함께 설치하고, 플러그인 사용자는 같은 스킬을 별도로 설치할 필요가 없습니다.


대상 프로젝트 루트에서 실행한 뒤 설치할 Skill과 적용 범위를 선택합니다. 전체 흐름에는 `setup-agent-harness`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, `maintain-agent-harness`를 선택하고, 아이디어 탐색이 필요하면 `explore-idea`를 추가합니다. 적용 범위는 사용할 에이전트와 Project를 선택합니다. `-g`를 사용하지 않으므로 프로젝트 로컬에 설치됩니다.

```powershell
npx skills@latest add git@github.com:young-sub/Skill_Management.git
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
