---
name: prototype
description: Build a runnable experiment to answer a concrete design, state, data-model, or UI question before production implementation. Match the requested artifact and number of options; reuse the existing stack.
---

# Prototype

State the question the user will be able to answer by trying the prototype. Infer a reasonable shape from the request and repository; ask only when the choice materially changes the experiment.

- For state, business logic, or data shape, read [LOGIC.md](LOGIC.md). A small script, REPL, or existing app surface is enough; a terminal UI is optional.
- For layout or interaction, read [UI.md](UI.md). Build one requested design, or a few distinct variants when comparison is the question.

1. Use the existing language, component system, and runtime. Put clearly named prototype code in the repository's existing experimental area or a suitable dev-only location. Do not create a new app, task runner, dependency, or worktree unless the experiment needs it.
2. Keep state in memory or use a disposable scratch store when persistence is the question. Real mutations, paid APIs, and production data require matching authorization; fixtures must be identified as fixtures.
3. Build only enough behavior and visual fidelity to answer the question. Keep basic input validation, failure feedback, and accessibility. Add a small runnable check only for consequential logic or invalid transitions; do not build a comprehensive test suite for throwaway scaffolding.
4. Run it and exercise the decisive scenario, including the relevant failure case. Show the relevant state and provide one working command or URL. Do not claim it was observed if the environment prevented execution.
5. Summarize what the experiment demonstrates and what it leaves open. Keep the artifact available for the user to try. Once a direction is chosen and implementation/cleanup is authorized, remove unused scaffolding or reuse validated code with appropriate production checks; a rewrite is not required merely because it began as a prototype.

Chat is enough to record the finding unless it changes durable project knowledge. A prototype request alone does not authorize production rollout or automatic deletion of the user's experiment.
