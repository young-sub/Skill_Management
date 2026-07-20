---
name: execute-codex-goal
description: Execute an approved Harness V2 contract inside an already active human-declared Codex Goal.
---

# Execute Codex Goal

Run only inside the active Goal declared by the human. Never create or start `/goal`, invoke a Goal wrapper, or silently broaden the approved contract.

## Inactive Goal

If the host does not expose an active Goal, do not mutate source or contract files. Return the Goal declaration payload with Work ID, resolved Contract path, and approved contract hash, then stop.

## Preflight

Use `scripts/goal_runtime.py preflight` with `--contract-root`, `--source-root`, and the host-provided `--goal-state` JSON file. The state must be a fresh serialization of the host `get_goal` result, never inferred or invented: it includes `active: true`, a nonempty `goal_id`, `retrieved_at`, a host marker, and the exact objective Work ID/path/hash. Continue only when those fields, the approved contract and DAG, and byte hashes for `AGENTS.md` and `CLAUDE.md` all match. The first successful preflight atomically persists the dirty baseline beside that Goal state, keyed by Goal ID and objective fingerprint; every later command reuses and verifies it.

## Slice Loop

1. Use `next`, then `start`, to select the first dependency-ready `pending` Plan in stable order and atomically transition it to `in_progress`.
2. Follow TDD. Verification order is always `targeted -> feature -> fast`.
3. Live and Eval are disabled by default. Run either only when the approved Test Envelope explicitly enables it; an unrun Live/Eval check is unverified, not failed.
4. On a failure, invoke `diagnose`, record structured `failure`, `diagnose`, `regression`, and `retry` evidence, and retry only after root cause and a regression test are known.
5. Use `complete` only after the Plan evidence is sufficient. It atomically transitions `in_progress` to `completed`.
6. Preserve existing dirty files and never perform broad cleanup.

Only one Plan may be `in_progress`. A blocked Plan can return to `pending` only with `resume --approve-resume --resolution-evidence <evidence>` after the exact Goal and Contract preflight succeeds; resolved blocker evidence is retained under `resolved-blocks/`.

## Hard Stop

For a contract Hard Stop, stop implementation immediately. Use `block` to durably create a transaction marker and `BLOCKED.md` before marking the active Plan `blocked`, so a blocked state can never exist without its report. An incomplete marker fails closed; use `recover-block --approve-recovery` to finish that exact transaction. Ask no broad follow-up questions beyond the approved Hard Stop boundary.

## Evidence

Use `evidence` for structured JSON records. Evidence stays beside the ephemeral contract as `evidence.jsonl`; never write a tracked source artifact or claim an existing dirty change as this Goal's work.
