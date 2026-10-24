# Refactoring

Use when changing structure while preserving observable behavior. A new behavior
needs separate feature criteria; do not silently include it in a refactor.

1. Identify public/direct callers, input/output and error contracts, state/data
   ownership and side effects to preserve. Reuse [change impact](../references/change-impact.md)
   for shared boundaries; a local edit needs only its owner and consumers.
2. Obtain an equivalent baseline from existing checks or still-valid observations.
   Without behavior coverage, first add characterization checks of the current
   behavior; type checks and lint are not a behavior baseline. Move/simplify within
   existing architecture, retaining validation and error handling.
3. Compare candidate and baseline for affected behavior, errors and side effects;
   inspect callers/imports/config, string references, docs and reverse references
   for missed consumers. Do not broaden checks merely because code moved. Preserve
   user data and unrelated changes.

Completion evidence shows behavior preservation, not reduced line count. Use
[project verification](../references/project-verification.md) for impact/currentness.
If the baseline fails, distinguish the pre-existing defect and do not claim GREEN
preservation. Resolve relevant uncertainty or report it; no mandatory design
document, task, contract, fixed delegation or whole-project test run is implied.
