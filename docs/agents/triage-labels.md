# Triage Labels And States

These values are local Work Packet metadata, not remote tracker labels.

| State | Meaning |
|---|---|
| `needs-triage` | Goal or evidence is not yet actionable |
| `draft` | Blocking decisions remain |
| `needs-confirmation` | Implementation intent awaits owner confirmation |
| `ready-for-agent` | Scope and verification are sufficient for implementation |
| `in-progress` | Implementation has started |
| `verification` | Changes exist and completion checks are running |
| `blocked` | Human approval or external state is required |
| `done` | Closed with verification and archive evidence |

Type labels: `bug`, `feature`, `architecture`, `docs`, `test-eval`, `refactor`, `skill-maintenance`.
Risk labels: `high-risk`, `approval-required`. State follows evidence and blocking decisions rather
than labels alone.
