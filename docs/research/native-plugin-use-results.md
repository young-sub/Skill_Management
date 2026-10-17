# Native plugin use — 2026-10-17

Codex and Claude Code are the intended product hosts. This run separates native
loading/use from the optional protected verifier; a protected driver is not
required to query or invoke the plugin.

## Initial 0.1.72 observation and repair

Base: clean `main@b16ccfd`, package 0.1.71. Codex CLI 0.160.0 and Claude Code
2.1.186 were available. The ordinary Codex account's native `plugin list --json`
did **not** contain `agentic-coding`. Existing installations/settings were preserved.

The 0.1.71 package installed and appeared enabled in an isolated Codex home.
Actual `skills/list` discovered its 19 namespaced Skills; `hooks/list` found one
prompt hook, enabled but **untrusted**. Discovery is not hook execution.

Claude's validator rejected the same package directory because it lacked a
Claude manifest. Session loading nevertheless found 19 Skills and one hook by
default layout, using the directory name as the plugin identity. The hook also
failed under Claude's root environment variable (`KeyError: PLUGIN_ROOT`).

0.1.72 derives a `.claude-plugin/plugin.json` from the existing identity source
and lets the shared hook resolve `CLAUDE_PLUGIN_ROOT` or `PLUGIN_ROOT`. It does
not duplicate the hook declaration or introduce another runner. The package
regression first failed on missing identity, then on the root variable; both
host environments now execute the packaged hook. Existing package/update/hook
tests passed (10 tests). Native Claude validation passed with an optional missing
author warning; native details showed `agentic-coding 0.1.72`, 19 Skills, one hook.

## Native consumption and limits

Claude's real prompt event executed the candidate hook with exit 0 and handed
project status to the session. A loopback receiver observed the explicitly invoked
`agent-workflow` body, its lookup-only rule and hook context in the host's model
request. Codex's native explicit Skill invocation also delivered the body and
lookup rule to loopback; its untrusted hook did not deliver context. These are
native loading/prompt-assembly observations, **not model reasoning or task success**.
The receiver returns a deliberate error and never performs inference.

Evidence: `.work/native-plugin-use-20261017/`. Raw native lists, stream captures,
transport observations, candidate/frozen packages and delivery results remain
there. Initial Claude probes timed out while retrying the deliberately unavailable
or rejecting local endpoint. The capture recorded cleanup denial; subsequent
scoped host process checks found no owned probe processes remaining. Preserve
the timeout records, not only successful loading observations. The first ad-hoc
probe also failed to serialize its timeout; it is not counted as acceptance.

In that initial loading-only run, no real model task was performed, no external paid inference was requested, and
no ordinary installation, credential or hook trust setting was changed. Current
session adoption needs installation in the intended account, then a fresh session.
Automatic Codex hook delivery additionally needs that host's explicit hook review;
changing protected-host trust was outside existing authorization. A real authenticated
task is still needed to establish model use of the guide/CLI and correct reporting.
Neither prerequisite requires the optional protected verifier.

The bounded repair improves native identity and Claude hook delivery. It does not
establish all six design outcomes or general reductions in user intervention.

## Authenticated Codex follow-up, 0.1.73

The retained `native-plugin-use-20261017/codex-final-home` is now authenticated.
The user configured project/hook trust and the Windows sandbox; this follow-up
did not change those security settings or the global installation. The original
login/daemon failures, blocked lookup and later successful read-only lookup stay
in their separate raw records. A successful lookup can return task BLOCKED when
historical evidence is stale; that is not a host invocation failure.

0.1.73 repairs repeated summary payloads in the existing runtime. The same real
task lookup fell from 110,163 to 56,865 JSON characters (48.4%). Handoff, action
scopes, all criterion/cell IDs, check validity/reasons and run identities matched.
No product command ran for this comparison. The summary has no fixed byte ceiling;
this is a measured reduction, not proof of generally lower token cost. Full detail
and original evidence remain accessible. Seventy-one workflow tests and sixty-five
related runtime/store/refinement/hook/package/update/docs tests passed; one added
large-summary assertion and the affected documentation checks also passed. Resource
drift and distribution validation passed. Full was not required for presentation-only
logic; no execution/acceptance rule was weakened.

Actual Codex request assembly delivered `Current project workflow data` from the
trusted hook, both before and after the update. A local receiver recorded presence
and hashes, not credentials, and intentionally rejected the request without model
inference. Hook delivery is established separately from model task success. The
[official UserPromptSubmit contract](https://learn.chatgpt.com/docs/hooks#userpromptsubmit)
describes this additional developer context.

Real tasks use fresh native `gpt-6.1-sol / low` sessions, ordinary requests, the
same isolated Yeondoo Link checkout and the installed candidate. No Skill name,
answer patch, token name or CLI sequence is supplied in those requests. Existing
project documentation, installed Skill catalog and automatic hook are normal
discovery surfaces. Process-scoped Git safe.directory for the exact trusted copy
is infrastructure assistance. Native sandbox subprocess failures and parent-host
repairs/execution are recorded as assistance, not autonomous completion.

Evidence is retained under `.work/native-consumption-20261017/`; the original
product and global resources are untouched. The tested candidate's exact bytes
are frozen in `.work/native-plugin-use-20261017/frozen-0.1.73/` and match the
test installation. Its build origin honestly records the dirty pre-commit
observation at `a368df7`; functional commit `8fbed09` retains the source change.
The inventory, not a claimed clean build, pins these tested bytes.

### Actual discovery and reuse

| Fresh task | Observed native behavior | Limit / intervention |
| --- | --- | --- |
| Wrong staff PIN recovery | Chose `agent-workflow` and `fixing-accessibility`, read the shared UI/verification guide, added error association and keyboard focus recovery at `StaffGate`, extended the existing browser check and guide. | Native domain/type checks ran, but browser/build subprocesses hit EPERM. Parent execution exposed an incorrect new pointer-focus assertion. |
| Browser port collision feedback | Chose `diagnose` and `maintain-project-verification`; traced the fixed port through runner, seven suite callers, source checks and request guard; added one port option to the same runner and preserved external/ownership guards. | Native selected tests ran; subprocess cases failed. Parent ran all 12 runner regressions successfully and repaired encoding-damaged added guide prose, preserving the damaged version. |
| Product backup error recovery | Chose `agent-workflow` and `fixing-accessibility`; reused StaffGate's error association/focus pattern and the shared guide in `CatalogImport`; separated file error from storage error; used the new port option from the guide without a supplied CLI sequence. | Native domain/type checks ran; actual browser execution still required the parent host. This is unaided guide discovery, not unaided end-to-end delivery. |

The pointer assertion incorrectly required a disabled submit button to retain
focus. The baseline browser did not do so. The corrected oracle checks that
pointer rejection does not grab the PIN input, while keyboard rejection must
restore input focus and allow typing without a manual focus operation. With the
corrected oracle, the original StaffGate failed `Missing invalid state`; the
repair passed all seven existing browser suites on the alternate port with stable
served source and clean owned-resource shutdown. The screenshot also showed the
existing shared focus ring. This is browser/DOM evidence, not a real screen-reader
speech test or final user visual approval.

No useful existing check was deleted: there was no equivalent coverage proof for
removal. The incorrect added oracle was corrected against baseline behavior,
while valid rejection, nearby normal behavior, required suites, source binding,
report no-overwrite and foreign-server protections remain. Test counts are not an
effectiveness score. These trials expose remaining human intervention and do not
establish reduced cost or a comparative pstack/model benchmark. Actual model usage
and failures are retained in `native-trials.json`; currency cost is unknown.

The original CatalogImport then failed the new actual-browser check with
`Invalid backup is not linked to the focused input with recovery instructions`.
The final repair passed all seven browser suites, including valid replacement,
preview/apply, storage-failure distinction, staff access and existing normal flows.
The 16 relevant native PIN/backup/runner tests and final product build passed on
the parent host. The final run served unchanged source, closed both owned browsers
and its server, and released port 11106. The unrelated 5173 listener remained.
All 1,669 pre-existing product evidence files kept their hashes; only the 13
intended isolated product source/test/guide files changed. The patch, before
snapshot, failures and final raw are retained. Product originals were not edited.

### Six design outcomes and remaining boundaries

| Outcome | Current bounded evidence | Not established by this run |
| --- | --- | --- |
| Explain delegated verification | Real summary retains current/historical distinction and next-action scope; native answers identify tests, reasons and EPERM limits. | Smaller output is not a fixed context budget or proof of general cost reduction. |
| Business rules / architecture | PIN rejection, throttling, normal entry and backup validation/storage-failure preservation; FE owners and runner/caller boundaries exercised. | No changed API/DB path in these tasks; no new full-stack API/storage acceptance claim. |
| Feedback / prevention | Actual fixed-port failure traced to shared runner and seven callers; regression checks preserve occupied-listener and external-request boundaries. | Native workflow feedback-record/task-binding roundtrip was not exercised; these small tasks used direct development and retained reports. |
| UI guide reuse | A fresh unrelated import task reused the StaffGate error/focus pattern and updated shared criterion without a patch/token hint. | No actual screen-reader speech test or final user visual approval. |
| Executable verification guide | The next task discovered alternate-port usage; the same runner was actually executed with source checks and cleanup. | Native subprocess execution remains blocked; parent-host success does not erase it. |
| Useful checks / less waste | Duplicate summary payloads removed; incorrect new oracle repaired against baseline; valid regression and ownership protections retained. | No automatic check-retirement decision or general decrease in rework/intervention demonstrated. |

Resume native end-to-end acceptance only when the same authorized host can run
its required child processes. Do not recreate home/login or relax trust silently.
Then execute the affected guide in a fresh task and verify current bindings and
cleanup. Claude's earlier loading/hook result remains separate; these three real
model tasks are Codex evidence only. Model-created oracle assumptions and Windows
text encoding still require review: their repairs here are not a universal
prevention mechanism. The plugin is useful in this bounded flow, not fully
autonomous or wholly verified.
