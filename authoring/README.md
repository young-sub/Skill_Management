# Canonical Authoring Resources

`authoring/` is the single source for Harness implementation, schemas, policies, and templates. `resource-map.json` maps each source to self-contained public Skill targets. Run `scripts/sync-skill-resources.ps1` after canonical changes and use `-Check` to detect drift.

Active shared implementation is `scripts/core_harness.py`. Contracts and results use JSON; human summaries stay in chat. Retained legacy HTML is read only for compatibility. The public resource manifest covers the complete public Skill tree; mapped generated files carry canonical source hashes where supported. Independent skills without resource-map entries are maintained directly under `skills/`.

The latest global AGENTS source is separately maintained in `global/AGENTS.md`; its backup and update procedure is in `docs/agents/global-guidance.md` at the repository root.
