<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/result-viewer.md -->
<!-- Source-SHA256: 8ddd2e750a7ef301b43d8a9052de35e163aedf9a33af45b10731808976a1d57e -->

# Existing-result lookup

Use the bundled `scripts/verification_results.py` for compatible project records. It reads files and runs fixed read-only Git identity queries; it never executes captured argv, tests or services, or writes inputs. Direct CLI/CI remains independent of Skills.

```
python <agent-workflow>/scripts/verification_results.py --plan plan.json --record capture.json --assessment assessment.json --observation observed.json --current-context current.json --pretty
```

Repeat record/assessment/observation arguments for multiple checks. Exit 0 means all required checks are currently reusable PASS, 1 means issues, 2 means blocked/incomplete. Always inspect `items`, `historical`, `current`, `remaining`; ISSUES and BLOCKED can coexist.

## Project-owned input

Create the plan while selecting checks, before execution. Add actual run/raw bindings after execution without rewriting criteria. Each check requires:

- `id`, `feature_id`, `expected`, `criteria_revision`, `required` (boolean), and `selection: {status: selected|excluded|not_required, reason: ...}`. Every disposition requires a nonblank string reason. Each Feature/check pair is unique. `criteria_revision` must equal `conditions.criteria.revision`; inconsistent identities are blocked. Required exclusions prevent overall PASS. Optional exclusions remain distinct from PASS.
- `conditions` with nonempty `source`, `criteria`, `command`, `dependency`, `fixture`, `runtime` objects. Source uses `revision` and `diff` (HEAD and binary tracked-diff SHA-256); command uses exact `argv` and absolute `cwd`. Other identities are project-specific, observed values, not invented labels. Missing identity remains unknown; do not replace it with `not_applicable` to get PASS.
- Optional `run_id` to disambiguate repeated runs. Ambiguous records are unavailable, never picked by timestamp.
- `raw_observations` with `path`, `sha256`, `pointer`, `producer` and `assertions`. Producer requires the actual `run_id`, `capture_path` and exact `argv`, or matching `json_report_path`/`json_report_sha256` for a capture's embedded native report. Include `capture_sha256` when retaining the binding. Pointers use JSON Pointer or `$.checks[0]` notation.

Assertions are project-selected raw facts, not a generic runner parser. Each has a pointer into the raw document and exactly the applicable comparison: `equals` (strict type/value), `min_count` (positive array length), or `min` (positive numeric threshold). For example, a Vitest plan can require `$.numPassedTests` min 1, `$.numPendingTests` equals 0 and `$.numFailedTests` equals 0; a browser plan must assert actual entered/saved/reloaded values and expected cases, not merely `status: PASS`. Check the project's actual report shape and mandatory cases before selecting pointers. A zero count, missing pointer or mismatch cannot establish current PASS.

Captures use the existing `run_check.py` format. Assessments bind `feature`, `check`, `run_id`, `status`, and observed `conditions`; if `evidence` is supplied its `sha256` must match the capture. A project raw observation without identity fields may be joined only through an explicit raw descriptor. These are editable consistency records, not authenticated attestation.

`current.json` supplies independently checked current conditions under `conditions`, or per-check overrides under `checks: {"feature/check": {conditions: ...}}`. The viewer independently compares live Git HEAD/diff/status to the capture. It cannot independently attest an external runtime, dependencies, fixture, or the completeness of project criteria. Recheck those identities through the project guide; copied historical values are not current evidence. Without a current context, show historical observations and keep current reuse unavailable.

The output preserves capture path/hash/argv/exit, raw paths/hashes/pointers/producer, assertion values, original judgments, current reuse reasons and conditions. A raw document's top-level `status`, when present, participates in judgment even without `--observation`; an ISSUES/BLOCKED report cannot be hidden by selecting only its successful sub-observations. Unknown status vocabulary remains UNKNOWN for project interpretation. A historical PASS can be STALE or UNKNOWN today. Native nonzero exit, timeout, cleanup failure, required skip/not-run, missing raw or changed conditions prevent current PASS. Read-only requests never backfill missing evidence by rerunning or changing source.
