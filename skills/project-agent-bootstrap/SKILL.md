---
name: project-agent-bootstrap
description: Compatibility alias that routes legacy bootstrap requests to setup-agent-harness.
---

# Project Agent Bootstrap compatibility alias

Immediately use `$setup-agent-harness` for the requested repository setup. This alias performs no independent mutation and has no separate contract.

Compatibility policy: install it alongside `setup-agent-harness`, keep behavior identical through routing, and remove the alias after 2026-12-31 once global instructions use the canonical name.
