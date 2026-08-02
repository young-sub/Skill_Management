# Domain And Source Of Truth

- `authoring/` owns shared implementation, schemas, policies, and templates.
- `skills/` is the generated, self-contained public distribution surface.
- `.harness/project.yaml` owns project mapping, impact, commands, retention, Git policy, baseline debt, and active cohort.
- `docs/index.md` owns technical navigation; `docs/architecture/harness-v3.md` owns Harness boundaries; `docs/testing.md` owns verification semantics.
- `tests/harness/test_core_first_*.py` own behavior contracts. Distribution tests own generation, self-containment, catalog, and clean-install invariants.
- `.work/goals`, `.work/runtime`, and `.work/transactions` are typed ephemeral state and never tracked authority.

The v2.0.0 release record is durable historical evidence. Removed Work Packets and implementation plans are recoverable from Git history but are not current sources of truth.
