---
owner_display: <Display Name, e.g. Jane Doe>
owner_slug: <lowercase-alphanumeric, e.g. jane>
schema_version: 1
generated_at: <yyyy-mm-dd>
---

# Agent Environment Profile (local, gitignored)

Machine-/identity-/access-path facts for agent-driven Work Packet flow on THIS checkout.
This file is local-only and must stay out of git (root `.gitignore` excludes `agent-env.*.md`).
Repo-shared facts belong in tracked docs; only put environment and access-routing facts here.

This profile is the single source of truth for **tracker-channel routing**. It is read once at
the start of every tracker-touching mode. Routing is **declared, never probed**: the skill never
"tries gh/connector and sees if it fails". If the profile is missing in a non-init mode, STOP.

## Scope of this profile

- Governs only the **tracker channel**: GitHub Issue/PR query + create/update.
- Does NOT govern the **code channel** (git push/pull/fetch over SSH). The code channel works
  for every repo and every orchestrator tool and is never gated by this skill.

## Owner

- Display name: <Display Name>
- Slug: <slug>   # lowercase alphanumeric only; used solely for branch prefixes and the
                 # gitignored filename `agent-env.<slug>.md`. Not a display name.

## Orchestrator

- This profile is read by whichever tool is the **orchestrator** for the session (Claude or Codex).
  Both can be an orchestrator. The orchestrator owns all tracker operations; subagents do not.
- The skill detects the current orchestrator tool and reads the matching column below.

## Repo identification

Identify the repo from its git remote (`git remote -v`), then match a binding row:

- SSH remote `git@<alias>:<org>/<repo>(.git)`  -> `remote_match` is the **`<alias>` token** before the colon.
- HTTPS remote `https://<host>/<org>/<repo>(.git)` -> `remote_match` is **`<host>/<org>`**.
- If the remote is neither form, or no row matches, **STOP** and ask the owner to add a binding.
- If the matched row's `expected_remote_match` differs from the actual remote, **STOP** (drift).

## Tracker-channel bindings

| remote_match | network | orchestrator=claude | orchestrator=codex |
|---|---|---|---|
| acme     | internal | gh | gh |
| personal | external | mcp_pat | mcp_pat |

Channel meanings:

- `gh`        : `gh` CLI. Requires explicit `--repo <org>/<repo>`. Use sandbox escalation when the
                local keyring is not visible to the sandbox (treat a sandboxed 401 as a sandbox
                artifact, not an auth failure).
- `mcp_pat`   : GitHub MCP server authenticated by a static PAT, configured in that repo's
                `.mcp.json`. Independent of `gh` login expiry. Used by a Claude orchestrator on an
                external account where `gh` login is unreliable.
- `connector` : Codex git connector. A Codex orchestrator can use it for Issue/PR on an external
                account. Codex CLI 0.140+ can instead use the same PAT-backed GitHub MCP server
                (`codex mcp add <name> --url <url> --bearer-token-env-var <ENV>`); when configured,
                record `mcp_pat` for the codex column so both orchestrators share one channel.
- `handoff`   : No direct tracker channel for this (repo, orchestrator). The skill produces the
                exact payload + command and hands off; it never retries a live call.
- `none`      : Tracker disabled / local-only repo. Manage Issue/PR purely as local documents.

## Per-repo settings

Add one block per repo. `remote_match` links it to a binding row above.

### <org>/<repo>

- remote_match: <alias-or-host/org>
- expected_remote_match: <same as actual remote; STOP if the live remote differs>
- repo_flag: <e.g. --repo acme-corp/internal-service>   # for the `gh` channel
- integration_branch: <base/integration branch for this work stream, e.g. main or develop>
- protected_branches: [main]   # never auto-merge or auto-shuttle into these
- sandbox_escalation: <true|false>
- mcp_server_name: <name in .mcp.json, when channel is mcp_pat; else blank>

## Defaults (when a repo has no explicit per-repo block)

- integration_branch: auto = `git symbolic-ref --quiet refs/remotes/origin/HEAD`; if unset, STOP and ask.
- protected_branches: [main, master]
- sandbox_escalation: false

## Notes

- This profile records facts; it does not perform setup. Configuring `gh` auth, a repo `.mcp.json`
  PAT, or the Codex connector is owner infrastructure work outside this skill.
- Code push/pull is intentionally absent here: it is not gated.
