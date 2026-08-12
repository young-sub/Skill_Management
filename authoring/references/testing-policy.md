# Testing Policy

- Select exact TDD/regression tests first, then path/dependency/cross-cutting mappings, then the configured Feature selector.
- An Item completes on observable Done evidence plus Impacted tests and relevant fast checks. Test command or selector changes are implementation details unless they change acceptance. Full is required only by a cumulative executable-impact trigger or explicit request.
- Unclassified relevant impact blocks completion until mapped or explicitly broadened; it cannot silently become `not_required`.
- Behavior-preserving test relocation uses baseline GREEN, ownership-confined structural change, equivalent GREEN, and unchanged public behavior.
