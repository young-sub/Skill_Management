---
name: multi-agent-review
description: Coordinate a main-agent decision frame, research subagents, more challenger subagents than researchers, evidence synthesis, objection adjudication, and a concise final conclusion. Use when the user asks for multi-agent review, adversarial critique, several agents to research and rebut a task or plan, or passes --subagents allowed.
---

# Multi-Agent Review

Use this skill to review a task, plan, design, architecture decision, implementation strategy, PRD, or proposal through structured research and rebuttal.

`--subagents allowed` means the user explicitly authorizes real subagent delegation for this workflow.

## Quality And Model Routing

Quality comes first. When a frontier/high-quality model such as `gpt-5.5` is available and cost or latency is not a material constraint, default researchers, challengers, and the main adjudicator to that model and tune reasoning by role instead of downgrading model class. Use `medium` reasoning for bounded research, `high` for challenger lenses, and `high` or `xhigh` for main adjudication depending on risk and complexity.

Use fast/small models only for bounded, checkable support tasks. A downgrade needs a task-shape reason such as source/file reference checking, duplicate-objection compression, mechanical evidence gathering, or formatting a draft final report only after main/high-quality adjudication supplies exact content boundaries. Do not downgrade merely because a task seems probably easy.

Before spawning subagents, apply a ROI gate. Use real subagents only when lenses are separable, each handoff can stay compact, the main agent can verify material claims by spot-checking rather than redoing the whole task, and coordination/context cost is lower than a main-only pass. If the gate fails, state that and perform a compressed single-agent multi-lens review. A longer handoff is acceptable only when it remains tightly scoped, pointer-rich, and easier to verify than the raw evidence.

Use main/high-quality for the decision frame, high-risk lens selection, canonical claim ledger, objection adjudication, final verdict, and evidence sufficiency decisions.

Never use fast/small models for resolving contradictions, deciding sustained/reserved/overruled status, materiality judgments, security/privacy/architecture/API/persistence-sensitive review, or final user-facing recommendations except formatting already-adjudicated content. `No final verdict` does not by itself make a challenger low-stakes; if the lens touches material contradictions or high-risk judgment, keep it on main/high-quality.
## Counts

- Small review path: use `N = 2`, `M = 3`, keep the canonical claim ledger to 150-250 words, skip full evidence cards unless a claim is material, disputed, or final-verdict-relevant, and stop early when outputs are duplicative.
- Normal task: use `N = 3`, `M = 4`.
- High-risk task: use `N = 4`, `M = 5` or more if justified.
- If the user provides counts and `M <= N`, raise `M` to `N + 1` unless they explicitly override the invariant.
- Do not spawn the requested maximum by reflex; stop when strongest objections are represented, findings are duplicative, or agent/thread limits require staged execution.

## Default Flow

1. Frame the task and write a compact provisional decision frame.
2. Spawn the researcher wave with distinct evidence lenses.
3. Wait for the researcher wave and close completed researcher agents when the host supports it.
4. Main compresses research into a 300-500 word canonical claim ledger. Use 150-250 words for the small review path.
5. Spawn the challenger wave using only the canonical claim ledger, not raw research outputs.
6. Wait for the challenger wave and close completed challenger agents when the host supports it.
7. Deduplicate objections, build capped evidence cards, and adjudicate canonical objections.
8. Present a concise final conclusion to the user.

If the host cannot close agents, keep only the canonical ledger and material objection summary in active context.

## Decision Frame

Before delegation, write a compact internal frame: decision/task, provisional direction, key claims and assumptions, constraints and non-goals, evidence that would change the conclusion, research lenses, and challenger lenses. Avoid anchoring on the provisional direction.

## Subagent Contracts

Use `templates/brief.md` for researcher and challenger assignments.

Every brief must include `Suggested model class`, `Reason`, and `Forbidden decisions`. If explicit model-class selection is unavailable, record intended model class and forbidden decisions without pretending enforcement exists.

Research subagents gather evidence for and against assigned claims. Challenger subagents attack assigned claims through one critique lens. Subagents return compact capsules only. The main agent owns synthesis, conflict resolution, final judgment, and user-facing reporting.

## Lens Selection

Pick non-overlapping lenses that fit the task.

Research examples: source/code evidence, product or user workflow, architecture and maintainability, testing and verification, security/privacy, operations/performance, documentation and prior decisions.

Challenger examples: factual correctness, hidden assumptions, failure modes, scope and simplicity, testability, security/privacy, operability, user impact, migration or compatibility.

## Synthesis

Build evidence cards only for deduplicated canonical claims, not for every subagent bullet.

Default caps: max 7 research finding cards, max 7 objection cards, and max 5 final adjudicated objections in the user-facing report. Merge duplicates and keep the strongest version by materiality and evidence quality. Do not drop a material minority objection merely because the cap is reached.

Subagent capsules and compressed ledgers are indexes, not conclusions. The main agent must inspect raw evidence directly when a claim is central to the final verdict, disputed by another agent, security/privacy sensitive, architecture/API/persistence/migration related, based on stale/generated/archived/indirect evidence, or likely to change the recommended action if wrong.

## Adjudication

Classify each canonical objection:

- `sustained`: valid, in scope, evidence-backed, and materially changes the conclusion or required action.
- `reserved`: plausible and material, but unresolved because evidence is missing or user/product judgment is required.
- `overruled`: unsupported, immaterial, duplicate, already addressed, outside scope, or contradicted by stronger evidence.

Overall verdict: `approve`, `approve-with-conditions`, `hold`, or `reject`. Never count agents as votes; count claims.

## Stop And Fallback

Stop and ask the user if the decision frame is unclear, the task requires external approval, or material evidence cannot be obtained.

If real subagents are unavailable after `--subagents allowed`, state that limitation and either perform a compressed single-agent lens review or ask whether to proceed without real subagents.

## Final Output

Use `templates/final-report.md` as the user-facing shape. Keep it concise and in the user's language. Do not paste raw subagent outputs unless asked.
