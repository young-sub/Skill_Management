# Native plugin use — 2026-10-17

Codex and Claude Code are the intended product hosts. This run separates native
loading/use from the optional protected verifier; a protected driver is not
required to query or invoke the plugin.

## Observed failure and repair

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

No real model task was performed, no external paid inference was requested, and
no ordinary installation, credential or hook trust setting was changed. Current
session adoption needs installation in the intended account, then a fresh session.
Automatic Codex hook delivery additionally needs that host's explicit hook review;
changing protected-host trust was outside existing authorization. A real authenticated
task is still needed to establish model use of the guide/CLI and correct reporting.
Neither prerequisite requires the optional protected verifier.

The bounded repair improves native identity and Claude hook delivery. It does not
establish all six design outcomes or general reductions in user intervention.
