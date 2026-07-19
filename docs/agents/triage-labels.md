# Triage Labels And States

No remote labels were inspected or changed during bootstrap. Work Packet records use these local states until publication:

| Work Packet state | Meaning |
| --- | --- |
| `needs-triage` | Scope or actionability is unclear. |
| `draft` | Blocking decisions remain. |
| `ready-for-agent` | Acceptance criteria and verification are explicit. |
| `in-progress` | Implementation is active. |
| `verification` | Implementation is complete and checks are running. |
| `blocked` | Human input, dependency, or approval is required. |
| `done` | Close evidence is recorded. |

Suggested types are `feature`, `bug`, `architecture`, `docs`, `diagnostics`, `test/eval`, and `refactor`. Do not create or rename GitHub labels without explicit approval.
