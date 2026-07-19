# Personal Agent Harness

Source repository for self-contained Agent Skills distributed through the open [`skills` CLI](https://github.com/vercel-labs/skills).

Harness V2 is available as a verified **v2.0.0 release candidate**. This repository metadata is not a live tag or GitHub Release. All seven project bootstrap, design, execution, close, and maintenance Core Skills are public while replaced workflows remain preserved under non-discoverable `legacy-skills/`.

## Public catalog

- Compatibility/support: `multi-agent-review`, `prototype`, `webapp-testing`, `zoom-out`
- Harness V2 Core: `setup-agent-harness`, `explore-idea`, `design-goal`, `execute-codex-goal`, `diagnose`, `close-goal`, `maintain-agent-harness`
- Professional/domain: `finance-research`, `find-skills`, `frontend-design`, `teach`, `theme-factory`, `web-artifacts-builder`, `write-a-skill`

Run a read-only catalog check before installation:

```powershell
npx skills@latest add young-sub/Skill_Management --list
```

## Interactive installation

Choose skills, Agent Providers, scope, and symlink/copy mode interactively:

```powershell
npx skills@latest add young-sub/Skill_Management
```

Project scope is the CLI default. Add `-g` only when you intentionally want a user-global installation.

## Non-interactive installation

Install every currently public skill for Codex and Claude Code into the current project using independent copies:

```powershell
npx skills@latest add young-sub/Skill_Management `
  --skill '*' `
  -a codex `
  -a claude-code `
  --copy `
  -y
```

To install selected skills, replace `--skill '*'` with repeated `--skill <name>` options. Add `-g` only after reviewing the global target paths.

## Update

Use the interactive updater and select only skills installed from this repository:

```powershell
npx skills update
```

For a known project-local installation, the CLI also supports `npx skills update -p -y`. Review the detected scope before using a non-interactive update in a workspace containing unrelated skills.

The repository's offline smoke wrapper can verify both install and update using a supplied local fake CLI:

```powershell
powershell -NoProfile -File scripts/test-install.ps1 `
  -SkillsCommand <fake-cli.ps1> `
  -VerifyUpdate
```

This path verifies all 18 catalog Skills in project-local Codex and Claude Code targets without network access. The default command still invokes `npx` and therefore requires explicit approval.

## Uninstall

Use the interactive remover and select only Harness skills:

```powershell
npx skills remove
```

For automation, pass explicit skill names and Agent Providers. Avoid `--all` in a shared Agent home because it can remove unrelated skills.

## Project setup

1. Run the interactive or non-interactive installation from the target project root without `-g`.
2. Confirm Codex skills under `.agents/skills/` and Claude Code skills under `.claude/skills/`.
3. Commit project-scoped copies or symlink metadata only when that target project's policy permits it.
4. Run `setup-agent-harness` once per target repository. Review its dry-run classification and conflict diffs, then explicitly approve apply to generate evidence-backed project instructions and verification configuration.

The CLI's official supported-agent table documents Codex and Claude Code paths and environment overrides: [Supported Agents](https://www.mintlify.com/vercel-labs/skills/guides/supported-agents).

## Repository boundaries

- `skills/`: installer-discoverable, self-contained public skills.
- `legacy-skills/`: preserved replacement candidates with `SKILL.legacy.md`, never public catalog entries.
- `authoring/`: canonical shared policies/templates; never referenced by an installed skill at runtime.
- `scripts/`: distribution sync, validation, and isolated install checks.
- `tests/distribution/`: behavior tests for catalog and packaging invariants.
- `docs/architecture/skill-inventory.md`: current public/legacy/future mapping.

## Verification

Run local checks from the repository root:

```powershell
python -m unittest discover -s tests -p "test_*.py"
powershell -NoProfile -File scripts/sync-skill-resources.ps1 -Check
powershell -NoProfile -File scripts/validate-distribution.ps1
git diff --check
```

Reproduce the three isolated Harness V2 pilots and their JSON, Markdown, and Completion Review artifacts:

```powershell
python scripts/run-v2-pilots.py
```

The recorded pilots are deterministic repo-local helper simulations. They execute the real Contract approval, runtime state transition, evidence, close, and archive helpers, but are not live host `/goal` sessions. Simulated timing fields are explicitly labeled; success and residual-state fields are measured from each temporary repository. See `docs/pilots/harness-v2-pilots.md`.

The install wrapper uses an isolated temporary destination but downloads and executes the current third-party `skills` package through `npx`; it requires explicit approval after reviewing that external execution:

```powershell
powershell -NoProfile -File scripts/test-install.ps1 -VerifyUpdate
```

The automated install-wrapper test substitutes a local fake CLI, so it does not prove the current upstream package's runtime behavior. Record a real `npx skills add . --list` and isolated Codex/Claude smoke result before a public release.
