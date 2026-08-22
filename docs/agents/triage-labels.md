# Triage Labels And States

No remote labels were inspected or changed during bootstrap. Work Packet records use these local states until publication:

| Work Packet state | Meaning |
| --- | --- |
| `needs-triage` | Scope or actionability is unclear. |
| `draft` | Blocking decisions remain. |
| `ready-for-agent` | Acceptance criteria and verification are explicit. |
| `in-progress` | Implementation is active. |
| `verification` | Implementation is complete and checks are running. |
| `approval_required` | An explicitly high-risk action awaits focused approval; ordinary work never enters this state. |
| `vetoed` | The human explicitly rejected the unchanged contract or action. |
| `verification_unavailable` | An environment limitation prevented a check; use and report the recorded fallback. |
| `execution_blocked` | An environment/runtime limitation prevented execution. |
| `blocked` | A non-approval external dependency prevents progress. |
| `done` | Close evidence is recorded. |

Suggested types are `feature`, `bug`, `architecture`, `docs`, `diagnostics`, `test/eval`, and `refactor`. Do not create or rename GitHub labels without explicit approval.
