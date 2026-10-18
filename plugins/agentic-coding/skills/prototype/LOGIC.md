# Logic Prototype

Expose a state or data question through the smallest runnable experiment in the host project's language. Use a script, REPL, or existing interface; add a TUI only when repeated interactive manipulation helps.

1. Name the state, actions, and uncertain behavior in one sentence or short code comment. Use plain data and existing conventions; separate effects from transitions enough to observe them, without inventing a reusable architecture.
2. Keep state in memory. Use a clearly disposable store only for a persistence experiment. Do not connect exploratory mutations to a real database or external service by default.
3. Expose the initial state, available actions, resulting state, and rejected transitions. A rejected action should explain why and leave valid state intact. Show only the state relevant to the question.
4. Add the smallest repeatable check for the uncertain rule: for example, one successful transition and one invalid transition that preserves state. Existing tests or a script self-check are sufficient. Do not add a framework or full regression suite for the interaction shell.
5. Run the decisive scenario and its failure case. For interactive use, support reset/quit and plain line input when enough; screen clearing, ANSI styling, keyboard shortcuts, and a separate module are optional.
6. Provide one working command, such as `python path/to/prototype.py`. Reuse an existing task command if useful, but do not edit a task runner merely to hide a file path.

Report what was learned and the remaining decision in chat. Keep the experiment runnable until the user has tried it or authorized cleanup. If its behavior is adopted, reuse useful logic after the relevant production verification; discard unnecessary shell code.
