# Subagent Brief

Role: researcher | challenger

Suggested model and reasoning:
main/high required, e.g. `gpt-5.5 high` | main/high with `xhigh` if hardest-risk | fast/small allowed | inherit default

Reason:
<why this model/reasoning choice fits the task shape; if downgraded, name the bounded/checkable reason>
Forbidden decisions:
<decisions this subagent must not make>

Goal:
<specific question this subagent must answer>

Task:
<task, plan, design, or proposal under review>

Decision frame:
<main-agent provisional frame>

Canonical claim ledger:
<for challenger waves, pass the compressed ledger only; do not pass raw researcher outputs by default>

Lens:
<one distinct evidence or critique lens>

Scope:
- Work only within this lens.
- Return concise evidence-backed findings.
- Do not decide the final verdict.

Output limits:
- max 6 bullets
- max 45 words per bullet
- no raw excerpts unless one short quote is essential
- every claim must include an evidence pointer, or explicitly say "inference"
- include exactly one "Not checked" line
- include exactly one "Confidence basis" line

Output:
- For researchers: findings, evidence, confidence, contradictions, not checked, recommendation.
- For challengers: strongest objections only; failure mode, severity, likelihood, evidence or reasoning, suggested resolution, falsifier.

Challenger priority:
Prioritize only the strongest objections. Do not list low-materiality objections after the cap is reached.

Stop condition:
<when to stop searching or critiquing>
