<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/acceptance-author.md -->
<!-- Source-SHA256: 6e90f4e16e1ce065b3421afab4b7c6e4204ddb2342bf87812a3c69145c203d57 -->

# Acceptance author

An implementer's own tests confirm the paths it chose, and a verifier that reads the
diff afterwards leaves a person to judge each finding. Acceptance written before the
implementation, by an agent that never sees it, and sealed where the worker cannot
edit it, moves that judgement to the start: the person answers the questions that
decide the result once, and a check outside the session judges completion.

Generated tests are often weak (specification-derived suites that pass a reference
implementation still let many injected faults survive), so the gate does not stop at "they pass": every
changed hunk is reverted in turn and a hunk no test notices is reported as untested,
and scenarios without a test are reported as uncovered. A pass means "the stated
checks pass", never "the request is complete".

## Dispatch

`delegate.py next` (and `answer`, after a correctness question) prints the author's prompt
with the verbatim request, the decided readings, the base commit and an output directory in
the Git common directory. Launch it unchanged:

- Claude Code: the Agent tool with `subagent_type` `agentic-coding:acceptance-author`.
- Codex: a sub-agent whose task is the prompt, without forking this conversation.
- No sub-agent available: say so on the card; seal tests you wrote before implementing with
  `acceptance_gate.py seal` by hand.

The prompt starts with `DELEGATED TASK <id> ROLE acceptance-author`, which is how the
SubagentStop hook knows whose stop it is. It asks for tests through entry points that exist
at the base, failing there by a failed assertion; expected values from the request and
decisions, never from running code; every path the rule applies to (`LSP findReferences`, SQL
and ORM writes, import, restore and background jobs); the nearest valid case; and questions
split into `correctness` (no guess, no test) and `preference` (a stated, tested default).

## Handle the result

The author writes the test files and `result.json` (`files`, `command`, `report`,
`scenarios`, `questions`, `write_paths`) into its output directory and replies `done`, so
none of it enters the orchestrator's context. The PreToolUse hook refuses reads of that
directory and of the sealed tests to everyone but the author.

1. **Seal.** The author's stop runs `delegate.py author-done`: correctness questions put the
   task in `questions` for the person; otherwise the tests are sealed in the task worktree.
   A test that does not fail on the base by assertion (with `--preserve`, that does not pass
   on it) goes back to the author with the reason; three refusals stop the task.
2. **Questions.** `delegate.py answer` records each answer; the task returns to authoring
   with the decided readings in a new prompt. Preference defaults wait in `delegate.py digest`
   for the person's batch; an answer that overturns a default is a new task.
3. **Implement** from the request and scenario text only (`delegate.py implement`). The
   author's tests and write-path list stay with the gate: an implementer that shares the list
   confirms the same paths it chose, which is how path misses passed before.
4. **Check.** The implementer's stop runs the sealed check; fix the implementation, never the
   sealed tests. Three failed checks stop the contract until a person clears and re-seals it.
   The seal detects changed files but cannot prevent a worker from replacing the contract: the
   task record keeps the hash `seal` returned, outside the worktree.

Card lines:
`Acceptance: PASS (stated checks, contract <hash>) | FAIL | TAMPERED | STOPPED: <reason> | not sealed: <reason>`,
`Untested changes: <file hunk> ... or none`, `Uncovered requirements: <scenario> ... or none`.
