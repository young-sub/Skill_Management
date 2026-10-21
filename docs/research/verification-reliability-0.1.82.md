# Verification reliability follow-up

This local follow-up addresses five observed gaps in 0.1.81: close/lookup
acceptance disagreement, overly broad unittest invalidation, insufficient check
timeouts, screenshot access and repetitive individual review submissions.

- Close uses the current task verdict, including unmapped changes and prepared
  execution blockers. Unrelated project debt does not block a valid scoped task.
- Native unittest reuse is opt-in through complete declared inputs plus mandatory
  registry, Feature and test inputs. Undeclared checks remain conservative.
- Check timeouts use descriptor metadata with explicit CLI override. Running and
  timeout-cleanup stages retain owned PID and failures.
- The browser fixture preflights an explicit artifact directory and distinguishes
  capture/readability from actual image observation.
- A review array validates each Feature against one audit and writes atomically;
  a bad entry rejects the batch without partial progress.

The implementation reuses existing workflow, capture and fixture owners. It adds
no dependency, daemon or global setting. Generated outputs have explicit package
ownership rather than an unmapped-change exemption.

## Evidence boundaries

Working evidence is retained under `.work/verification-reliability-20261021`.
The controlled browser scenario is a local fixture, not Yeondoo or production
acceptance. Main-agent image inspection is separate from runner file readability.
Installed-plugin adoption, unaided native-host behavior and external services
remain outside this local change.

The initial real browser run passed 16/16 checks. A deliberately injected desktop
focus fault failed 1/16; restoring the copied CSS returned 16/16 with no errors
or skips. Main opened the mobile image and desktop before/after pair directly:
the repaired image visibly restores the orange keyboard-focus outline. Both
controlled runs retained five readable screenshots and clean service shutdown.
The helper injected/restored the fixture; this is assisted verification, not
unaided model discovery. Raw reports and image hashes remain under the work path.

The source-level controls cover task readiness, all-or-nothing review writes,
related/unrelated input changes, shared-check consumers, positive timeouts and
retained cleanup errors. Full and registered Feature results are retained with
the work evidence; no earlier version's PASS is counted as this run.
