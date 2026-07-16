# Matt Skills v1.1 Candidate Evaluation

- Date: 2026-07-16
- Decision: rejected for local installation and mainline adoption
- Candidate source: Matt Pocock skills v1.1.0 adaptation

## Why

The candidate did not improve completion rate in controlled A/B runs and generally increased
latency or context cost. In the final local-planning check, both variants hit the 390-second limit:

- A (existing skills): 394.548 seconds; produced an ignored local spec but no tickets.
- B (candidate skills): 394.516 seconds; produced no artifact.

Earlier representative checks showed equivalent diagnosis and orchestration quality, while the
candidate used more input tokens and was usually slower. Small planning and TDD tasks repeatedly
failed to complete within the evaluation limit.

## Disposition

- Do not install the candidate into the user skill directory.
- Do not merge the upstream catalog replacements, renames, routing, or audit machinery into main.
- Retain only the repository policy that `/.scratch/` and `/docs/plans/` are ignored local working
  surfaces.
- Raw evaluation evidence remains local under `.scratch/evals/matt-skills-ab/` and is not a durable
  repository artifact.

