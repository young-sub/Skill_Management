# Agent Coding 설계·실행 프롬프트 아카이브

2026-10-05 이후 사용자 논의로 대체된 방향 또는 수행 완료 지시를 보존한다. 아래 문서는 역사적 근거이며 현재 구현 지시가 아니다. 현재 결정은 [업무 위임·검증·지속 개선 체계](../agent-coding-system-direction.md), 다음 작업은 [현재 실행 프롬프트](../agent-workflow-next-session.md)를 따른다.

2026-10-09 G1–G6 실행 프롬프트는 Git `95c4f9e:docs/research/agent-workflow-next-session.md`에 원문이 보존돼 있다. 현재 프롬프트는 [0.1.44 이후 보완 검토](../agent-workflow-refinement-review.md)를 반영한 R0–R4와 최신 main 동기화·로컬 통합 요청이며, 이전 완료 과업을 다시 구현하라는 지시가 아니다.

| 보존 문서 | 아카이브 이유 |
| --- | --- |
| [2026-10-04 설계와 배포 비교](agent-coding-system-direction.md) | 직접 명령 중심·새 Router 보류 판단을 보존. 이후 단일 업무 진입점·두 검증 Skill 도입 합의가 대체 |
| [기반 구현 상태·Labeler 파일럿 프롬프트](agent-coding-next-session.md) | 해당 기반과 파일럿은 이미 수행됨. 다음 세션이 완료 과업을 다시 구현하지 않도록 분리 |

이동에 따른 상대 링크와 아카이브 표시만 보완했다. 변경 전 바이트는 Git 이력에 남는다. [PStack 고정 조사](../pstack-analysis.md)와 [Labeler 실제 결과](../labeler-verification-pilot.md)는 현재 결론의 근거로 유지한다. 결과의 제한을 제거하거나 새 설계가 이미 효과를 입증한 것처럼 수정하지 않는다.

후속 [요구사항 검토](../agent-coding-requirements-review.md)는 Router 보류 결론을 되살리지 않고, 압축 과정에서 약해진 domain/boundary 책임과 Feature lifecycle을 현재 설계 §11에 복구했다. 이전 설계 전체를 현재 지침으로 재적용하지 않는다. 2026-10-05 검토 전 방향/프롬프트의 정확한 비교본은 Git `53865b0`에 보존되므로 동일 문서를 다시 복제하거나 삭제하지 않는다.
