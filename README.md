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

For GitHub-backed installations with update hashes, the CLI supports `npx skills update -p -y`. Review the detected scope before using a non-interactive update in a workspace containing unrelated skills. With `skills@1.5.19`, a project installation from a local repository is recorded as `sourceType=local`; native update can exit successfully without refreshing those copies. The smoke wrapper detects that no-op by comparing the complete relative file set and SHA256 for every public Skill tree, then falls back to the same local `skills add ... --copy -y` command as the supported local-source refresh path. This does not verify remote GitHub update behavior.

The repository's offline smoke wrapper can verify both install and update using a supplied local fake CLI:

```powershell
powershell -NoProfile -File scripts/test-install.ps1 `
  -SkillsCommand <fake-cli.ps1> `
  -VerifyUpdate
```

This path verifies all 18 catalog Skills in project-local Codex and Claude Code targets without network access. It rejects missing, extra, or stale nested resources as well as stale entrypoints. Output distinguishes a working native update from an unsupported/no-op local update followed by a successful local-source refresh. The default command still invokes `npx` and therefore requires explicit approval.

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
4. Run `setup-agent-harness` once per target repository. For an existing repository, start with `python scripts/bootstrap_project.py reconcile --root <repository-root>` and review the read-only PlanArtifact, authority decisions, router/TESTING proposals, Git path policy, blockers, and `plan_sha256`. Apply only that artifact with `apply-plan`, the exact digest, and explicit approvals for `.work/` and `agent-env.*.md`; interrupted transactions block new apply until explicit `recover-apply`. Greenfield repositories retain the `plan` then explicit `apply --approve` flow.

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

Run the three isolated Harness V2 pilots with raw evidence in a temporary directory:

```powershell
python scripts/run-v2-pilots.py
```

The default command does not modify tracked files. Use `--update-baseline` only when intentionally refreshing the normalized tracked reports under `docs/pilots/`. The recorded pilots are real temporary implementation cycles through a repo-local host adapter. They start from assertion-failing source and unittest fixtures, apply one explicit source change per Plan, execute measured Targeted, Feature, and Fast subprocess checks per Plan and exactly one Full suite per Goal, then use the real Contract approval, runtime state transition, evidence, close, and archive helpers. They are not live host `/goal` sessions. See `docs/pilots/harness-v2-pilots.md`.

Release evidence is accepted only when `distribution/release-candidate.json` and the proof record name the same clean Git commit and tree. Pilot, local-source install/refresh, and remote GitHub update are separate evidence kinds; one cannot substitute for another. Run `python scripts/validate_evidence.py --repository-root .` to verify that binding.

The install wrapper uses an isolated temporary destination but downloads and executes the current third-party `skills` package through `npx`; it requires explicit approval after reviewing that external execution:

```powershell
powershell -NoProfile -File scripts/test-install.ps1 -VerifyUpdate
```

The automated install-wrapper tests substitute a local fake CLI and cover a working native update, an exit-0/no-op local update, nested-resource tampering, missing resources, named-ref mismatch, and default-branch mismatch. They do not by themselves prove remote GitHub behavior. The normal repository source is `-SourcePackage young-sub/Skill_Management`; an approved release-candidate check uses a non-moving `release-smoke-<commit>` tag plus `-ExpectedSourceCommit`. The wrapper resolves both that tag and the remote default branch to the expected commit before accepting update evidence, and records complete installed-tree digests before and after update. The current candidate's passed proof is stored separately under `distribution/evidence/`:

```powershell
powershell -NoProfile -File scripts/test-install.ps1 `
  -RepositoryRoot . `
  -SourcePackage https://github.com/young-sub/Skill_Management/tree/release-smoke-<40-character-commit-sha> `
  -ExpectedSourceCommit <40-character-commit-sha> `
  -SourceType github `
  -VerifyUpdate `
  -ApproveRemoteEvidence `
  -EvidencePath distribution/evidence/remote-github-update.json
```
