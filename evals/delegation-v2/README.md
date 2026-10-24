# Delegated coding evaluation v2

This suite targets omissions across write paths, sibling fixes, sequential requests, API authorization and existing consumers. Eleven new product requests accompany the byte-preserved v1 `rule-all-paths` anchor. Tasks were chosen from these failure classes before candidate-agent evaluation; no candidate sessions were run to select or tune tasks.

Authoring controls establish that the tasks are executable and distinguish a complete implementation from a documented plausible incomplete implementation. They do not establish a measured success rate or prove that strong agents will fail. See `VALIDATION.md` for current commands, exits, assertion evidence and timings.

## Failure-mode inventory

The inventory below records the authoring choices, rather than results from candidate-agent trials. The frozen v1 anchor is the explicit exception to the new prompt wording requirements.

| Scenario | Project | Intended omission |
| --- | --- | --- |
| a-offer-quantity-all-paths | Labeler | Ordinary saves enforce offer rules while restore accepts invalid quantities or list sizes |
| a-product-source-stale-all-paths | Labeler | Korean source changes leave translations falsely current on alternate saves |
| a-update-offer-list-complaint | Labeler | Repair the reported edit while spreadsheet updates still lose tiers |
| a-product-name-whitespace-complaint | Labeler | Repair ordinary spaces while tabs/newlines still fail across direct and spreadsheet entry |
| a-import-offer-sequence | Labeler | Adding blank-offer spreadsheet edits silently clears previously preserved offers or ignores invalid rows |
| b-sequence-category-branch-copy | Labeler | Adding branch duplication bypasses the depth limit established by the first request |
| b-entitlement-design-save-api | Labeler | The save API admits a free, expired, revoked, future or suspended paid period |
| b-contract-catalog-default-page | Labeler | Change the catalog page default while accidentally changing account-product pagination |
| b-cross-path-custom-unit-limit | Labeler | Repair direct custom-unit validation while import normalization still bypasses the length limit |
| cart-item-to-compare | yeondoo-link | Reusing comparison toggles removes an existing choice, exceeds five candidates or loses unrelated session state |
| medicine-catalog-classification-bypass | yeondoo-link | Patch only the reported purchase gate while the same medicine still exposes unreviewed details |
| rule-all-paths | Labeler | Unchanged v1 anchor: description limit across all writes |

## Candidate isolation and leakage

- Pin Labeler to `984e4f646e08b75a8dfc4b9c62913670960c1659` and yeondoo-link to `d17f0c2322056a4d804c911b83d6cc1b1738a083`. Clone the committed tree; never copy source working-tree changes.
- Candidate sessions receive only the product prompts, pinned project and configured synthetic fault. Keep this suite, hidden checks, references, partial implementations, authoring tools, validation records and results outside candidate workspaces and prompts. Do not reuse authoring clones for candidate runs.
- Preserve the runner's order: all sessions, probes with restoration, existing regression, hidden file installation, hidden commands. A probe's command must work before hidden installation. Probe relevance is demonstrated separately by mutating the reference and executing the hidden checks; this does not mean a candidate left tests that detect it.
- Regression commands name existing files explicitly and do not depend on Skill_Management assets. Hidden checks name only their installed destinations. Do not add broad discovery globs to regression commands.
- Freeze prompts and suite hashes before any candidate evaluation. Retain model/reasoning identity, runner/plugin versions, dependency identity, all failed/timed-out cells, cost/usage including unknowns, and raw results. Do not select tasks using observed candidate scores.
- Single-request budgets are 1,800 seconds; two-request sequences use 2,700 seconds. The current runner grants the sequence budget separately to each fresh session in the same clone. Judging commands retry a failure once; do not treat transient runtime/setup errors as behavioral evidence.

## Safety and reproduction

Repository authoring writes are confined to this directory; product writes use disposable clones under `C:/Users/YS/AppData/Local/Temp/claude/eval-authoring-v2/`. Dependencies are junctions only to the evaluation dependency copies under `C:/Users/YS/AppData/Local/Temp/claude/eval-deps/<project>/node_modules`. The Labeler copy unexpectedly lost packages during authoring; missing files were restored by copying from the read-only original after verifying identical dependency lock hashes, preserving existing destination files. The incident and copy command are retained in `evidence/dependency-incident.json` and `evidence/dependency-restore.json`. No dependency install/update, source-checkout write, commit, provider change or paid-agent session was performed.

The authoring clone procedure tries `git clone --local` and falls back to `git clone --local --no-hardlinks` when local hardlinks are denied. Labeler commands redirect Wrangler logs into the clone and use Vitest's runner config loader with cache disabled. Before deleting any clone, remove every contained junction with `cmd /c rmdir <junction-path>`; only then delete the clone directory. Never recursively remove a clone while its junctions remain.

Use the runner's dry run to validate configuration without invoking a candidate:

```powershell
python -B scripts/run_delegation_eval.py --scenarios evals/delegation-v2/scenarios.json --output C:/Users/YS/AppData/Local/Temp/claude/delegation-v2-dry-unused --condition off=off --condition plugin=plugin:plugins/agentic-coding --reps 1 --jobs 1 --timeout 300 --dry-run
```

Read `tools/audit.py` before using its `audit` action: it validates the runner schema, anchor identity, explicit regressions, budgets, fresh patch application and exact probe matches. It creates fresh disposable clones; resumption accepts an owned clone only at the same pin with the reference already applied. Selected new worker references also receive a compiler check. Run it with `python -B` to avoid bytecode writes outside this suite. The checked-in evidence contains the outcomes of authoring controls; it is not a candidate benchmark result.

Feature impact is confined to evaluation assets for delegated-work verification. Product changes exist only as reference patches in isolated clones. The repository Feature Map is preserved because this task authorizes writes only under this suite.
