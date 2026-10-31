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

Before any implementation, capture the base commit and pick an output directory
outside the worktree (for example under the system temp directory). Fill the
template with the user's messages that define the task **verbatim**; add nothing else.

- Claude Code: the Agent tool, `general-purpose`, with the filled template.
- Codex: a sub-agent whose task is the filled template, without forking this conversation.
- No sub-agent available: say so on the card and seal tests you wrote before implementing.

```
ACCEPTANCE AUTHOR. Someone else will implement the request below starting from commit
<base> of this repository. You write the acceptance checks that will judge their work.
You will not see the implementation and must not change the repository.

Request (verbatim):
<request>

Decided readings: if `.harness/decisions.md` exists, read it; decided questions are
part of the request.

Write test files only under <output directory>, named as they will sit in the
repository's test layout. Rules:
- Test through entry points that already exist at <base> (API handlers, CLI commands,
  public functions, UI actions through the project's live/e2e runner). A test that cannot
  import something the base lacks proves nothing and will be refused.
- Each test must fail on <base> by a failed assertion about the requested behavior, and
  should pass once the request is implemented. For a behavior-preserving request
  (refactoring), write tests that pass on <base> and must keep passing.
- Expected values come from the request and decisions, never from running code.
- Find every path the request's rule applies to: run `LSP findReferences` on the writing
  function (text search without an LSP tool) and text-search table/column writes (SQL
  INSERT/UPDATE, ORM calls, import/restore jobs, background jobs). Cover each with a test.
- Prefer one assertion per observable outcome; include the nearest valid case that must
  keep working.
- Questions: `correctness` when the observable result depends on the answer (do not
  guess; write no test for it), `preference` when any reasonable answer works (give the
  default you assumed and test that default).

End with one JSON object:
{"files": ["<repository path>", ...], "command": "<runner command from the repository root>",
 "report": "<JUnit XML or Jest JSON path the command writes, or null for Python unittest>",
 "scenarios": [{"scenario": "<input → expected result>", "covered_by": ["<repository path>"]}],
 "questions": [{"question": "...", "kind": "correctness" | "preference", "default": "..."}],
 "write_paths": ["<file:function that the rule applies to>", ...]}
```

## Handle the result

1. **Questions.** Correctness questions are answered before sealing: ask in an
   interactive session; headless, stop and list them under *User decisions*. Record each
   answer in `.harness/decisions.md` ([recorded decisions](independent-check.md#recorded-decisions))
   and re-run the author if the answer changes a scenario. Preference questions proceed
   with the stated default and go under a `## Pending` heading in `.harness/decisions.md`
   for the person to answer in a batch; an answer that overturns a default is a new task.
2. **Seal.** `acceptance_gate.py seal --root <worktree> --base <base> --tests
   <output>/<path>=<path> ... --command "<command>" [--report <path>] --scenarios <file>
   [--link node_modules] [--preserve]`. A refused test is re-authored, never weakened.
3. **Implement** from the scenario text only. The author's tests and write-path list stay
   with the gate: an implementer that shares the list confirms the same paths it chose,
   which is how path misses passed before. The test names and command are enough to run
   the gate.
4. **Check.** `acceptance_gate.py check --root <worktree>` (the Claude Code Stop hook runs
   it). Fix the implementation, never the sealed tests. Three failed checks stop the
   contract (`STOPPED`) until a person clears and re-seals it. Record the contract hash
   `seal` prints on the card: the seal detects changed files but cannot prevent a worker
   from replacing the contract, so only a hash kept elsewhere shows that.

Card lines:
`Acceptance: PASS (stated checks, contract <hash>) | FAIL | TAMPERED | STOPPED: <reason> | not sealed: <reason>`,
`Untested changes: <file hunk> ... or none`, `Uncovered requirements: <scenario> ... or none`.
