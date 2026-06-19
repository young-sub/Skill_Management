---
name: codex-delegation
description: Prepare and launch delegated Codex work from Claude with an explicit context capsule and detached background execution. Use when Claude is asked to hand work to Codex, spawn a Codex worker, or avoid foreground codex-rescue/background timeout failures.
---

# Codex Delegation

## Scope

Use this skill only when Claude is delegating work to Codex. Standalone Codex sessions should not load or follow this skill unless the user explicitly asks for delegated execution.

## Rule

Delegated Codex work must receive a self-contained prompt and run detached from Claude's foreground shell. Never use foreground `codex:codex-rescue` for long-running work; host shell timeouts can kill it mid-task.

## Workflow

1. Confirm delegation is useful: the task is separable, has clear scope, and Codex can verify or report progress independently.
2. Build a Delegation Capsule and put it at the top of the Codex prompt.
3. Run preflight and record failures in Claude's report:

```powershell
Get-Command codex -ErrorAction Stop
Get-Command codex-companion.mjs -ErrorAction SilentlyContinue
codex doctor
```

4. If `codex-companion.mjs` exists, prefer it:

```powershell
codex-companion.mjs task --background --write
codex-companion.mjs status <jobId> --wait
```

5. If no companion exists, start `codex exec` as an OS-detached job and poll `.scratch/codex-jobs/<jobId>/`.
6. Claude owns orchestration: read Codex's final report, verify central claims before acting on them, and preserve remaining risks.

## Delegation Capsule

Use this shape at the top of every delegated Codex prompt:

```md
# Delegation Capsule

## Caller

- Orchestrator: Claude
- Repository: <absolute repo path>
- Branch and dirty state: <branch, relevant changed files, files to avoid>
- Reason for delegation: <why Codex is being asked to do this>

## Current Situation

- User request: <latest user intent in one or two sentences>
- Decisions already made: <facts Codex should not re-litigate>
- Evidence already gathered: <key files, commands, outputs, links>
- Constraints: <sandbox, approvals, no-touch paths, style or docs rules>

## Codex Task

- Objective: <single concrete objective>
- Scope: <allowed files or modules>
- Out of scope: <explicit non-goals>
- Required approach: <TDD, diagnose loop, read-only review, implementation, etc.>
- Verification: <commands Codex should run or explain if unrun>
- Stop conditions: <when Codex must stop and report back>
- Final report: <expected concise output format>
```

## PowerShell Fallback

Use this only when `codex-companion.mjs` is unavailable:

```powershell
$jobId = "codex-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$jobDir = Join-Path ".scratch\codex-jobs" $jobId
New-Item -ItemType Directory -Force -Path $jobDir | Out-Null
Set-Content -Path (Join-Path $jobDir "prompt.md") -Encoding UTF8 -Value @"
<paste the full Delegation Capsule and task prompt here>
"@

$promptPath = (Resolve-Path (Join-Path $jobDir "prompt.md")).Path
$lastMessage = (Join-Path (Resolve-Path $jobDir).Path "last-message.md")
$stdout = (Join-Path (Resolve-Path $jobDir).Path "stdout.log")
$stderr = (Join-Path (Resolve-Path $jobDir).Path "stderr.log")
$command = "Get-Content -Raw '$promptPath' | codex exec --cd '$PWD' --sandbox workspace-write --output-last-message '$lastMessage' - > '$stdout' 2> '$stderr'"

$process = Start-Process -WindowStyle Hidden -FilePath powershell -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command) -PassThru
Set-Content -Path (Join-Path $jobDir "pid.txt") -Encoding ASCII -Value $process.Id
```

Poll with:

```powershell
Get-Content .scratch\codex-jobs\<jobId>\stdout.log -Tail 40
Get-Content .scratch\codex-jobs\<jobId>\stderr.log -Tail 40
Get-Content .scratch\codex-jobs\<jobId>\last-message.md -ErrorAction SilentlyContinue
```
