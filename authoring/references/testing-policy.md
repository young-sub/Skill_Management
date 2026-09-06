# Testing Policy

- Record `changed_logic`, `affected_behaviors`, `scope`, and `reason` from the diff plus direct-caller/public-behavior searches. `scope=none` is valid when no product behavior is affected; its logic and test lists may be empty, but its reason still explains the assessment. Paths and names provide candidate tests, features, and Full warnings only.
- Local impact runs exact behavior tests. Capability impact adds only relevant contract/integration tests. Cross-cutting impact runs Full. `scope=none` needs no behavior test when Done evidence is sufficient. Unknown or unexplained logic impact is `unresolved_logic_impact` and blocks completion without auto-expanding to Full.
- `feature_commands` are fallback candidates, not automatic selections. A configured `full_trigger` is a warning until the logic assessment is cross-cutting; an explicit human Full request is the only other way to require Full.
- Re-evaluate the cumulative Git change set before close so a stale per-Item assessment cannot complete the work.
- Reuse evidence while the relevant implementation, acceptance criteria, and execution conditions remain unchanged. Once required checks pass, repeat or broaden only for a concrete new concern. Documentation wording alone does not need a new behavior test, and an Item's `tests` field must not be populated with a duplicate manual review just to satisfy a schema.
- Run selected commands and inspect actual outcomes. `complete` and `close` validate submitted result consistency; neither runs the reported product checks. Never substitute a `passed` field or validator exit code for execution evidence.
- Selector and command `argv` are ordered tokens and may repeat an identical value when different flags require it. Set-like path, test, trigger, and Full-warning lists remain unique.
- Behavior-preserving test relocation compares the baseline and resulting inventory/public behavior; rerun only the checks needed to show the move preserved behavior.
