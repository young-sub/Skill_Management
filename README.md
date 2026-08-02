# Personal Agent Harness Skills

이 저장소는 여러 에이전트 환경에 설치할 수 있는 공개 Skill 배포본과 그 canonical authoring source를 관리합니다. 현재 Agent Harness v3는 기존 저장소 구조를 먼저 매핑하고, 승인된 핵심 Item을 우선 구현하며, 변경 영향에 해당하는 테스트만 선택하고, 작업 상태를 `.work/`에서 보존 기간에 따라 관리합니다.

## 시작하기

- 에이전트 구현 문서: [`docs/index.md`](docs/index.md)
- 기계 판독 설정: [`.harness/project.yaml`](.harness/project.yaml)
- 공개 Skill: `skills/`
- canonical source와 생성 매핑: `authoring/`

공개 Harness Skill은 `setup-agent-harness`, `explore-idea`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, `maintain-agent-harness`입니다. 기존 v2.0.0 배포 사실은 [`docs/releases/v2.0.0.md`](docs/releases/v2.0.0.md)에 역사적 릴리스 증거로 남아 있으며, 현재 workflow authority는 아닙니다.

## 프로젝트에 설치

대상 프로젝트 루트에서 실행한 뒤 설치할 Skill과 적용 범위를 선택합니다. `-g`를 사용하지 않으므로 프로젝트 로컬에 설치됩니다.

```powershell
npx skills add git@github.com:young-sub/Skill_Management.git
```

## 검증

```powershell
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

외부 설치 smoke는 네트워크에서 코드를 내려받아 실행하므로 별도 명시적 승인이 필요합니다. 저장소 변경만으로 push, publish, release, protected branch merge를 수행하지 않습니다.
