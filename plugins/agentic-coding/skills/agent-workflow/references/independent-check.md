<!-- Generated file. Do not edit directly. -->
<!-- Source: authoring/references/independent-check.md -->
<!-- Source-SHA256: 5ffc33fd033af95394b66c72340ac7091c6c8e0d8f5c6b5a53d7ceca9a51cde3 -->

# Independent check

The implementer and its own tests share one list of paths to consider, so its checks
confirm the paths it chose. A fresh verifier that sees only the request and the diff
does not share that list: in the offline record it named the missing path in 10 of 10
incomplete implementations that passed the existing regression suite. On 12 references
accepted as complete it flagged 5: three were real defects the hidden checks also
missed, two were stricter readings than the request. Its report is input to judge, not
a verdict to obey.

## When

After the affected checks pass (delivery step 3), for every change to behavior: code,
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

Decided readings: if `.harness/decisions.md` exists, read it. The user settled those
questions; behavior it decides counts as requested, and a settled question is not a question.

Rules:
- Do not modify product (non-test) files. Add verification tests only as new files,
  following the project's test layout.
- Do not install or update dependencies.
- Derive expected behavior from the request, never from running the implementation.
- Test at the entry points users actually use (API handlers, public functions, UI actions).
- Report `incomplete` only with a failing test you wrote and ran.
- A rule over all saves/users/paths applies to every such path: a path that does not
  apply it is a VIOLATION, not a question to the user. Report it with a failing test.
- Only genuinely ambiguous scope belongs in questions; do not invent exceptions.

Examples (after writing and running the failing test):
- Request: round every invoice total to cents, half up. Interactive entry rounds
  1.005 to 1.01; recurring invoice creation stores 1.005. VIOLATION: recurring
  creation misses the rule; report that path and test, not a rounding-scope question.
- Request: lowercase usernames on every save. Signup saves `alice`, but profile
  editing saves `ALICE`. VIOLATION: profile editing bypasses normalization; report
  its failing save test, not a question about whether existing users are exempt.

End with one JSON line:
{"verdict": "complete" | "incomplete", "violations": [{"path": "...", "test": "file:line", "observed": "..."}], "questions": ["..."]}
```

## Handle the report

1. Run each failing verifier test yourself. If it fails because requested behavior is
   missing, fix it at the owner, rerun that test and the affected checks.
2. If a test's expectation is not what the request says (a stricter or different
   reading), do not fix it. Put it under *User decisions* with your recommendation,
   together with the verifier's questions.
3. Keep the verifier tests that guard requested behavior, adapted to the suite's
   naming, and add them to the Feature's registered checks so later changes run them.
   Remove those that encode an undecided reading.
4. Turn each fixed violation into a guardrail: add a probe to `.harness/probes.json`
   that undoes the fix at its owner (`find` the fixed code, `replace` it with the
   original), with `command` running the kept test and `origin`
   `"independent-check <date>"`. Run `probe_check.py probes --root <project>`; the probe
   must be killed. The next change that reopens the same path then fails an existing
   check instead of waiting for another verifier. The Claude Code Stop guard asks once
   when the verifier reported violations and the registry was not updated afterwards.
5. Do not relaunch the verifier after fixing; its failing tests are the check. Relaunch
   only when a fix changed a different path than the one reported.

Card line: `Independent check: complete | N violations → M fixed (probes: <ids>), K for user decision (tests: <paths>)`.

## Recorded decisions

When the user answers a *User decision*, append one line to `.harness/decisions.md`
(create it if missing) before acting on the answer:

```
- 2026-10-28 product-name: Does the 50-character limit apply to bulk import? → Yes, reject the row. (asked by: independent check)
```

Date, Feature or area, the question, the answer, and where it came from. A later
answer to the same question replaces the line instead of adding one. Then:

- If the answer adopts the stricter reading, it is a new request: implement it through
  the delivery loop with a regression for it (the verifier's removed test is a starting
  point) and its probe.
- If the answer rejects it, the line alone stops the next verifier from asking again.

Read the file in acceptance step 1: a decision there is part of the
expected behavior for every later change in that area.
