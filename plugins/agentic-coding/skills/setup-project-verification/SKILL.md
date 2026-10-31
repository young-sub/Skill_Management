---
name: setup-project-verification
description: Give a product repository one committed command that launches the app from the current worktree, drives an entry point and saves responses, logs and screenshots, so agents observe their own changes instead of a person testing by hand. Also maps the project's verification when a full map is requested.
disable-model-invocation: true
---
<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/skills/setup-project-verification/SKILL.md -->
<!-- Source-SHA256: 42adb58f5532f46aaddce54a11a8701c010da12160525e55887183b9f0b83d4f -->


# Setup Project Verification

Without a way to run the product, every other check falls back to a person clicking through
it. The goal is one command per product that an agent runs to see a change working:

```
<command> --report <new path> [--script <drive script>]
```

1. **Launch** the app from the current worktree with its own state: empty or seeded database,
   free port, no developer server, no production credentials or local secrets.
2. **Doctor:** wait until the served process belongs to this checkout.
3. **Drive** a script through a real entry point (UI action, API call, CLI). The default script
   exercises one flow end to end, including a fresh read after a write.
4. **Evidence:** the drive script's JSON result, server and browser logs and screenshots go under
   the report directory.
5. **Cleanup:** stop only what the command started. A failing drive script makes the command fail.

Wrap the project's existing runner (e2e harness, isolated worker, compose file) instead of building
one. Register the command as `commands.live` in `.harness/project.yaml` with `{report_dir}` in its
argv, document it in the project's guide, run it once and look at the screenshots, run it once
with a drive script that must fail, and commit it in the product repository. A copy, fixture or
plugin-side adapter is evidence, not a connection. Example: labeler
`node tests/live.mjs --report {report_dir}/live.json` over its `tests/isolatedWorker.mjs`.

Acceptance authors (`agent-workflow`) then write UI and API acceptance tests as drive scripts for
this command. Keeping it working when the environment changes is the remaining human cost.

When the person asks for a full verification map, a Feature map or a missing execution path
beyond this command, follow [full verification mapping](references/full-verification-mapping.md).
