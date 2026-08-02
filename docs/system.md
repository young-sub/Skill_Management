# Core-First Harness System

The Harness maps an existing repository before changing it, turns authorized work into two to five observable Items, implements dependency-ready core behavior first, selects tests from explicit impact rules, and retains work evidence only for a configured period.

```text
static inventory -> mapped project v3 -> Item contract -> canonical Korean Design Review -> default authorization
       -> core-first implementation -> Impacted checks -> per-Item commit
       -> Korean Result Review -> completed -> trash -> exact-approved deletion
```

Durable current knowledge is tracked under configured document roots. `contract.json`, Review HTML, evidence, logs, and transaction journals are ephemeral under `.work/`. Unknown legacy records enter `legacy-unclassified` and are never swept automatically.

Valid ordinary designs continue without an affirmative phrase: the runtime renders the canonical Review and binds `default` authorization to its digest. A clear veto stops execution. Destructive, security/privacy, secret, irreversible, costly external, push, and publish risks require explicit approval.

Project, Design, Execute, Close, Maintain, and Diagnose must all support the active cohort. Unsupported or mixed versions fail before mutation. A v2 migration first builds a dormant v3 cohort; activation changes every producer and consumer together only after legacy active, blocked, or incomplete transaction state is absent.
