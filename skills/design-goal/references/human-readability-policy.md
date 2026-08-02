<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/human-readability-policy.md -->
<!-- Source-SHA256: 72c1bacc5c5263f32734ed657f73a4b28ccc0072f67635201cc5677a65f14820 -->

# Human Readability Policy

- Agent contracts and durable technical documents are English. Design and Result surfaces are Korean by default.
- A Review is a decision document, not a status-card summary. Preserve the canonical contract's behavioral meaning and enough detail for a human to decide without reading agent-only sources.
- Design uses stable Item IDs/order and a deliberate reading sequence: changed outcome, behavior design, verification scenarios, completion criteria, then material dependencies, boundaries, and risks. Avoid naive question headings and keyword-only prose.
- Result uses the same Item identity and visual grammar. It shows implemented change, observable outcomes, behavior-level check summaries, criterion-by-criterion evidence, and a concrete planned-versus-actual statement.
- Use behavior-matched tool/API, UI, bug-fix, state, or migration visuals. A visual node is a plain-language action or state, not an internal noun label.
- Explain unfamiliar terms on first use. Keep exact commands subordinate to the behavior they prove.
- Do not expose raw Markdown, frontmatter, hashes, detailed logs, or audit appendices.
- Status always has text and an icon in addition to color.
