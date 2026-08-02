# Testing Policy v3 (Dormant)

- Select exact TDD/regression tests first, then path/dependency/cross-cutting mappings, then the configured Feature selector.
- An Item completes on Impacted tests plus relevant fast checks. Full is required only by an explicit cumulative-impact trigger or human request.
- Unclassified relevant impact blocks completion until mapped or explicitly broadened; it cannot silently become `not_required`.
- Behavior-preserving test relocation uses baseline GREEN, structural change, equivalent GREEN, and unchanged production hashes.
