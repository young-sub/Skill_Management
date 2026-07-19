# Authoring Sources

`authoring/` is the canonical source for policy and template resources shared by Harness V2 Core Skills.

Published skills must remain self-contained. They may not reference this directory at runtime. Add a source-to-target entry to `resource-map.json`, run `scripts/sync-skill-resources.ps1`, and commit the generated copy with its source SHA-256 header.

The map is intentionally empty during WP-01 because the seven Core Skill targets are implemented by WP-02 through WP-05. Those packets must add only the resource mappings they consume.
