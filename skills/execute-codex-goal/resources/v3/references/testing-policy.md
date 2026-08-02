<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/cohorts/v3/references/testing-policy.md -->
<!-- Source-SHA256: 209ae40d637c3987acf6e1eb227be21209adfbb40a30b50a17f9a72790d1c185 -->

# Testing Policy v3 (Dormant)

- Select exact TDD/regression tests first, then path/dependency/cross-cutting mappings, then the configured Feature selector.
- An Item completes on Impacted tests plus relevant fast checks. Full is required only by an explicit cumulative-impact trigger or human request.
- Unclassified relevant impact blocks completion until mapped or explicitly broadened; it cannot silently become `not_required`.
- Behavior-preserving test relocation uses baseline GREEN, structural change, equivalent GREEN, and unchanged production hashes.
