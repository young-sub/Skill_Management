# Independent check

The implementer and its own tests share one list of paths to consider, so its checks
confirm the paths it chose. A fresh verifier that sees only the request and the diff
does not share that list: in the offline record it named the missing path in 10 of 10
incomplete implementations that passed the existing regression suite. On 12 references
accepted as complete it flagged 5: three were real defects the hidden checks also
missed, two were stricter readings than the request. Its report is input to judge, not
a verdict to obey.

## When

After the affected checks pass (delivery step 5), for every change to behavior: code,
schema, query or configuration that changes what users get. Skip only trivial edits
(copy, typo, one config value) and say so on the card.

## Dispatch

Fill the template with the user's messages that define the task **verbatim**, and the
base commit you captured at the start. Add nothing else: no summary, no plan, no list
of what you tested. Independence is the point.

- Claude Code: the Agent tool, `general-purpose`, with the filled template as the prompt.
- Codex: spawn a sub-agent whose task is the filled template, without forking this
  conversation.
- No sub-agent available: the card says `Independent check: not run (no sub-agent)`.

A different model family is optional; a fresh context of the same model was enough
for the result above.

```
INDEPENDENT VERIFIER. A colleague implemented the request below. The result is the
change from commit <base> in this repository (`git diff <base>` plus untracked files
in `git status`). You did not take part. Decide whether the rules and behavior the
request states hold on every path the request applies to.

Request (verbatim):
<request>

Rules:
- Do not modify product (non-test) files. Add verification tests only as new files,
  following the project's test layout.
- Do not install or update dependencies.
- Derive expected behavior from the request, never from running the implementation.
- Test at the entry points users actually use (API handlers, public functions, UI actions).
- Report `incomplete` only with a failing test you wrote and ran.
- Where the request can reasonably be read two ways, list a question instead of a verdict.

End with one JSON line:
{"verdict": "complete" | "incomplete", "violations": [{"path": "...", "test": "file:line", "observed": "..."}], "questions": ["..."]}
```

## Handle the report

1. Run each failing verifier test yourself. If it fails because requested behavior is
   missing, fix it at the owner, rerun that test and the step-5 checks.
2. If a test's expectation is not what the request says (a stricter or different
   reading), do not fix it. Put it under *User decisions* with your recommendation,
   together with the verifier's questions.
3. Keep the verifier tests that guard requested behavior, adapted to the suite's
   naming; remove those that encode an undecided reading.
4. Do not relaunch the verifier after fixing; its failing tests are the check. Relaunch
   only when a fix changed a different path than the one reported.

Card line: `Independent check: complete | N violations → M fixed, K for user decision (tests: <paths>)`.
