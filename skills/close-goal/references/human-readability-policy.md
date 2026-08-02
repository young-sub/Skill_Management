<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/human-readability-policy.md -->
<!-- Source-SHA256: cb91ee67eefeb492c9989c0554dbabcc41c3eb44e52454830b267cadbe9e54ab -->

# Human Readability Policy

- Agent contracts and durable technical documents are English. Design and Result surfaces are Korean by default.
- A Review is a human decision surface. Show only the purpose, process, tests, and expected or actual result needed to judge the work without reading agent-only sources.
- Design and Result preserve stable Item IDs/order and use exactly four primary blocks per Item: `핵심 목적`, `핵심 프로세스`, `핵심 테스트`, and `예상 결과` or `핵심 결과`.
- Design test tables show the verification target, test method, and observable pass condition. Result test tables show the verification target, performed test, and observed result.
- Use a short plain-language process visual. Explain unfamiliar terms at first use and show non-goals or structured risks only when they materially change the human decision. Keep internal priority and routine dependency mechanics agent-only.
- Keep exact selectors, commands, criterion-level evidence, and non-material plan deltas in agent records; do not render them in the human Review.
- Do not expose raw Markdown, frontmatter, hashes, detailed logs, or audit appendices.
- Status always has text and an icon in addition to color.
