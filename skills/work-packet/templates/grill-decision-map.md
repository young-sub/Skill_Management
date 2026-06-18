# Grill Decision Scaffold

Use this scaffold when `full_grill_with_docs` or a blocking preflight question
is still open. Do not use the full Work Packet, issue body, PRD, roadmap, or
Implementation Confirmation templates until direct grill questions are closed
or auto-closed from repo evidence.

## Status

- Intake mode:
- Alignment status: open
- Evidence inspected:

## Auto-closed decisions

- <decision and evidence>

## Open direct questions

- <question label and why it needs the user>

## Decision Map

Decision Map may be written in Korean for Korean grill sessions. Keep it compact for `targeted_grill`, use a mini map for `docs_grill_preflight`, and use the full map plus internal branch tracking for `full_grill_with_docs`.

| Category | Why it matters | Estimated questions | Direct questions |
|---|---|---:|---|
| <category or Korean category> | <short business/product reason in Korean or English> | <min-max> | <question labels> |

- Total estimated questions: <x-y>
- Questions to ask directly now: <count>
- Decisions likely auto-closed from repo evidence: <count>

For `full_grill_with_docs`, also keep an internal branch list for terminology, actor/user outcome, workflow/lifecycle/state, abstraction/data shape, permissions/failure/persistence, verification/eval, and docs/ADR impact when relevant. Do not expand the user-facing question block with this internal list.

## Deferred until alignment closes

- Implementation Contract
- roadmap
- PRD summary
- vertical slices
- acceptance criteria
- Codex goal
- Implementation Confirmation Brief

## Next question

## Fixed question format

```md
Progress: [category n/m, question z of estimated x-y]

## Q. [question in Korean]
Question intent:
- <Explain in Korean which business/product decision this question resolves and why the recommended answer is reasonable. Do not repeat the Decision Map.>

Recommended answer:
- <State the recommended option first, then briefly explain repo evidence, product intent, reversibility, and verification basis.>
```
