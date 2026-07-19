[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$DestinationRoot,
    [string]$SkillsCommand = 'npx'
)

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepositoryRoot = Join-Path $scriptDirectory '..'
}

$resolvedRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$ownsDestination = [string]::IsNullOrWhiteSpace($DestinationRoot)
if ($ownsDestination) {
    $DestinationRoot = Join-Path (
        [System.IO.Path]::GetTempPath()
    ) "harness-install-$([Guid]::NewGuid().ToString('N'))"
}
$resolvedDestination = [System.IO.Path]::GetFullPath($DestinationRoot)
$expectedSkills = Get-ChildItem -LiteralPath (Join-Path $resolvedRoot 'skills') -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name

New-Item -ItemType Directory -Path $resolvedDestination -Force | Out-Null
$previousLocation = Get-Location

try {
    Set-Location -LiteralPath $resolvedDestination
    & $SkillsCommand skills add $resolvedRoot --skill '*' -a codex -a claude-code --copy -y
    if ($LASTEXITCODE -ne 0) {
        throw "skills CLI failed with exit code $LASTEXITCODE"
    }

    foreach ($skillName in $expectedSkills) {
        $codexEntrypoint = Join-Path $resolvedDestination ".agents\skills\$skillName\SKILL.md"
        $claudeEntrypoint = Join-Path $resolvedDestination ".claude\skills\$skillName\SKILL.md"
        if (-not (Test-Path -LiteralPath $codexEntrypoint -PathType Leaf)) {
            throw "Codex install missing skill: $skillName"
        }
        if (-not (Test-Path -LiteralPath $claudeEntrypoint -PathType Leaf)) {
            throw "Claude Code install missing skill: $skillName"
        }
    }

    Write-Output 'Install smoke test passed for codex and claude-code.'
} finally {
    Set-Location -LiteralPath $previousLocation
    if ($ownsDestination) {
        $tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
        if (-not $resolvedDestination.StartsWith(
            $tempRoot,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Refusing to clean non-temporary destination: $resolvedDestination"
        }
        Remove-Item -LiteralPath $resolvedDestination -Recurse -Force
    }
}
