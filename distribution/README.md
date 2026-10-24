# Agentic Coding plugin

이 패키지는 업무 위임, 실제 검증 결과 조회, 피드백 수리, UI·검증 기준 개선을 하나의 진입점으로 연결합니다. 버전은 [plugin.json](plugin.json), 원본 커밋은 [build-origin.json](build-origin.json), 배포 파일 해시는 [package-files.json](package-files.json)이 소유합니다.

## 시작

호스트에서 이 패키지를 등록하고 활성화한 뒤 [agent-workflow](skills/agent-workflow/SKILL.md)를 선택하여 실제 업무를 요청합니다. 플러그인 생성만으로 호스트 등록·인증·hook 신뢰가 설정되지는 않습니다. 개별 스킬을 따로 다시 설치할 필요는 없습니다.

```text
상품 저장 기능을 구현하고, 화면 입력부터 저장 후 재조회까지 검증해줘.
검사한 이유와 실제 결과, 아직 확인하지 못한 부분을 보여줘.
```

모델이 스스로 고르는 Skill은 `agent-workflow`, `diagnose`, `recall`, `setup-project-verification`, `fixing-accessibility` 다섯 개입니다. 나머지는 명시 호출 전용이라 평소 컨텍스트에 설명이 실리지 않습니다. 사용자가 직접 부르거나 `agent-workflow`가 필요할 때 형제 Skill의 `SKILL.md`를 읽어 사용합니다. 프롬프트 hook은 선택된 작업이나 명확한 요청 유형이 있을 때만 한 줄을 남기고, 그 외에는 아무것도 주입하지 않습니다.

위임한 작업은 요청에서 도출한 수락 검사, 변경 없이 새 테스트가 실패하는지 보는 증명(`probe_check.py prove`), 영향받는 기존 검사, 결과 카드로 끝납니다. 프로젝트의 `.harness/probes.json`에 등록한 인공 결함은 `probe_check.py probes`로 실행해 Feature × 업무/아키텍처/UI × 계층별로 몇 개를 잡는지 보여 줍니다.

프로젝트의 기존 AGENTS·기능 지도·요구사항·실행 명령을 먼저 사용합니다. 작은 수정에는 전체 프로젝트 설정이나 여섯 영역의 전수 검사를 요구하지 않습니다. 검증 연결이 없는 경로는 [setup-project-verification](skills/setup-project-verification/SKILL.md)으로 연결합니다.

| 목적 | 요청 예시 | 포함된 기준 |
| --- | --- | --- |
| 병렬 구현 | 독립 작업을 나눠 구현하고 통합 후 동작까지 확인해줘. | [swarm](skills/swarm/SKILL.md); 소유권·의존성·기존 실행 대조와 통합 책임. 독립 검토는 multi-agent-review |
| 위임·결과 조회 | 기존 업무의 결과와 남은 일만 보여줘. 검사는 다시 실행하지 마. | [상태·요청 연결](skills/agent-workflow/references/workflow-obligations.md) |
| 업무·아키텍처 검증 | 이 변경의 업무 규칙과 FE/API/Domain 연결을 검증해줘. | [검증 책임](skills/agent-workflow/references/project-verification.md) |
| 이전 작업 회상·재개 | 어디까지 했는지 알려줘. / 남은 작업을 이어서 해줘. | [회상](skills/recall/SKILL.md); 회상은 읽기 전용, 실제 재개는 기존 실행 흐름 |
| 현재 동작·설계 이유 | 이 흐름은 어떻게 동작하고 왜 이렇게 정했어? | [설명](skills/zoom-out/SKILL.md); 확인된 이유·추론·미확인 구분 |
| 설계·변경 영향 | 호출자와 저장 책임을 유지하면서 복잡한 변경을 설계하고 구현·회귀로 확인해줘. | [설계 판단](skills/architect/SKILL.md), [공통 영향 분석](skills/agent-workflow/references/change-impact.md); 작업 계약은 design-goal |
| 피드백·재발 방지 | 저장 후 값이 돌아오는 원인을 추적하고 우회 경로까지 막아줘. | [원인 수리·재사용](skills/agent-workflow/references/repair-and-reuse.md) |
| 인간의 교정·성공 절차 | 이 방향을 교정해줘. / 이 결과를 다음에도 재현할 절차로 남겨줘. | [교정·성공 재사용](skills/agent-workflow/references/feedback-and-success.md), [절차 템플릿](skills/agent-workflow/templates/reusable-procedure.md) |
| UI 기준 | 기존 화면의 스타일과 상태별 동작을 정리하고 공유 컴포넌트에 연결해줘. | [UI 설계](skills/impeccable/SKILL.md) |
| 검증 가이드 개선 | 이 가이드대로 실행하고, 틀린 명령과 관찰 방법을 고쳐줘. | [검증 유지보수](skills/maintain-project-verification/SKILL.md) |
| 불필요한 검사 정리 | 중복 검사를 찾아 같은 결함 검출과 정상 허용을 보존할 때만 통합해줘. | [검사 유지·통합 기준](skills/agent-workflow/references/project-verification.md#detection-value-and-measured-maintenance) |

사업 모델의 가치·수익 가설은 프로젝트의 실제 관찰 지표로 판단합니다. 소프트웨어 업무 규칙 테스트가 통과했다고 사업성이 검증된 것은 아닙니다. 업무 규칙/아키텍처 × FE/API/Domain은 영향 판단에 사용하며 미선언 영역은 검증 완료로 취급하지 않습니다.

## 결과 읽기와 재개

결과는 요청 → 검사 선택 이유 → 실제 관찰·근거 → 현재 유효성 → 미확인·다음 행동 순서로 확인합니다. 기존 업무의 정확한 state/context를 사용하며 여러 후보 중 임의로 고르지 않습니다.

```text
python <plugin>/skills/agent-workflow/scripts/project_workflow.py lookup --root <project> --state <existing-task-path> --summary
```

조회와 task `resume`은 검사를 실행하지 않습니다. 새 실행은 `prepare`와 명시적 `execute`로 구분합니다. 세부 입력은 [실행·결과 계약](skills/agent-workflow/references/result-viewer.md)에 있습니다. 오래된 PASS, skip, 실행하지 않은 검사와 환경 차단은 현재 성공이 아닙니다.

패키지 실행, 실제 제품 검증, 호스트의 Skill/hook 전달, 모델의 무도움 업무 완료는 별도 증거입니다. 기록과 해시는 일관성을 확인하는 수단이며 독립적인 성공 인증이 아닙니다. 실제 자격증명·외부 서비스·배포·전역 설정에는 해당 작업의 별도 권한이 필요합니다.
