<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/testing-policy.md -->
<!-- Source-SHA256: f046a01c3b0531887d8e9769637140f04cab4e7216fc277e0bf164d946a1fb45 -->

# Testing Policy

- Record `changed_logic`, `affected_behaviors`, `scope`, and `reason` from the diff plus direct-caller/public-behavior searches. Paths and names provide candidate tests, features, and Full warnings only.
- Local impact runs exact behavior tests. Capability impact adds only relevant contract/integration tests. Cross-cutting impact runs Full. Unknown or unexplained logic impact is `unresolved_logic_impact` and blocks completion without auto-expanding to Full.
- `feature_commands` are fallback candidates, not automatic selections. A configured `full_trigger` is a warning until the logic assessment is cross-cutting; an explicit human Full request is the only other way to require Full.
- Re-evaluate the cumulative Git change set before close so a stale per-Item assessment cannot complete the work.
- Behavior-preserving test relocation uses baseline GREEN, ownership-confined structural change, equivalent GREEN, and unchanged public behavior.
