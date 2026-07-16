# Matt Skills v1.1 Candidate Evaluation

- Date: 2026-07-16
- Decision: do not install or adopt the candidate
- Archived experiment branch: `archive/rejected-matt-skills-v1.1-ab`
- Archived experiment commit: `471222e`

## Evidence Summary

The candidate did not improve completion rate and usually increased latency or context cost. In the
final local-planning A/B check, both variants hit the 390-second limit:

- A (existing skills): 394.548 seconds; produced an ignored local spec but no tickets.
- B (candidate skills): 394.516 seconds; produced no artifact.

Earlier representative runs found equivalent diagnosis and orchestration quality, while the
candidate generally used more input tokens and was slower. Small planning and TDD tasks repeatedly
failed to complete within the evaluation limit.

## Disposition

- Keep the existing installed skill set.
- Do not merge the candidate catalog replacements, renames, routing, or audit machinery.
- Ignore `/.scratch/` and `/docs/plans/` as local working surfaces.
- Raw evaluation evidence remains local under `.scratch/evals/matt-skills-ab/`.
