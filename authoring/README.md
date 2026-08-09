# Canonical Authoring Resources

`authoring/` is the single source for Harness implementation, schemas, policies, and templates. `resource-map.json` maps each source to self-contained public Skill targets. Run `scripts/sync-skill-resources.ps1` after canonical changes and use `-Check` to detect drift.

Active shared implementation is `scripts/core_harness.py`. Review renderers use structured `contract.json`/Result JSON and Korean HTML templates. The public resource manifest covers the complete generated Skill tree; generated files carry canonical source hashes where supported.
