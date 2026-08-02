# Core-First Harness System

The Harness maps an existing repository before changing it, turns approved work into two to five observable Items, implements dependency-ready core behavior first, selects tests from explicit impact rules, and retains work evidence only for a configured period.

```text
static inventory -> mapped project v3 -> Item contract -> Korean Design Review -> natural approval
       -> core-first implementation -> Impacted checks -> per-Item commit
       -> Korean Result Review -> completed -> trash -> exact-approved deletion
```

Durable current knowledge is tracked under configured document roots. `contract.json`, Review HTML, evidence, logs, and transaction journals are ephemeral under `.work/`. Unknown legacy records enter `legacy-unclassified` and are never swept automatically.

The project, Design, Execute, Close, and Maintain consumers must all support the active cohort. Unsupported or mixed versions fail before mutation. A v2 migration first builds a dormant v3 cohort; activation changes every producer and consumer together only after legacy active, blocked, or incomplete transaction state is absent.
