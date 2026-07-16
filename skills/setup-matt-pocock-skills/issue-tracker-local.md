# Issue tracker: Local Markdown

Issues and specs for this repo live as agent-local markdown files under
`docs/plans/<owner-slug>/`. The entire `/docs/plans/` tree is gitignored so parallel agents do not
compete over personal planning files. `.scratch/` remains ephemeral.

## Conventions

- One feature per directory: `docs/plans/<owner-slug>/<feature-slug>/`
- The Work Packet is `docs/plans/<owner-slug>/<feature-slug>/work-packet.md`
- The spec is `docs/plans/<owner-slug>/<feature-slug>/spec.md`
- The slice set is `docs/plans/<owner-slug>/<feature-slug>/tickets.md`; optional child issue
  records live under `issues/<NN>-<slug>.md`, numbered from `01`
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create or update the matching durable file under
`docs/plans/<owner-slug>/<feature-slug>/` (creating the directory if needed). Do not call a
remote tracker. Resolve `<owner-slug>` from the gitignored `agent-env.<slug>.md` profile and verify
the whole `/docs/plans/` tree is ignored. Mirror settled decisions into tracked source-of-truth docs
before close or cross-clone handoff.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `docs/plans/<owner-slug>/<effort>/map.md` — the Notes / Decisions-so-far / Fog body.
- **Child ticket**: `docs/plans/<owner-slug>/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan the effort's durable `issues/` directory for files that are open, unblocked,
  and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.
