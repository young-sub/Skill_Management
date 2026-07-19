[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$DestinationRoot,
    [string]$SkillsCommand = 'npx',
    [switch]$VerifyUpdate
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
$catalogPath = Join-Path $resolvedRoot 'distribution\catalog.json'
if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
    throw "Distribution catalog is missing: $catalogPath"
}
$catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding utf8 | ConvertFrom-Json
$expectedSkills = @($catalog.public_skills)

New-Item -ItemType Directory -Path $resolvedDestination -Force | Out-Null
$previousLocation = Get-Location

try {
    Set-Location -LiteralPath $resolvedDestination
    $installArguments = @(
        'skills', 'add', $resolvedRoot, '--skill', '*',
        '-a', 'codex', '-a', 'claude-code', '--copy', '-y'
    )
    & $SkillsCommand @installArguments
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

    if ($VerifyUpdate) {
        foreach ($skillName in $expectedSkills) {
            foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
                $installed = Join-Path $resolvedDestination "$providerRoot\$skillName\SKILL.md"
                Set-Content -LiteralPath $installed -Value '# stale install' -Encoding utf8
            }
        }

        $updateArguments = @('skills', 'update', '-p', '-y')
        & $SkillsCommand @updateArguments
        if ($LASTEXITCODE -ne 0) {
            throw "skills CLI update failed with exit code $LASTEXITCODE"
        }

        foreach ($skillName in $expectedSkills) {
            $source = Join-Path $resolvedRoot "skills\$skillName\SKILL.md"
            foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
                $installed = Join-Path $resolvedDestination "$providerRoot\$skillName\SKILL.md"
                if (-not (Test-Path -LiteralPath $installed -PathType Leaf)) {
                    throw "Update missing skill for $providerRoot`: $skillName"
                }
                $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
                $installedHash = (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash
                if ($sourceHash -ne $installedHash) {
                    throw "Update did not refresh $providerRoot skill: $skillName"
                }
            }
        }
        Write-Output "Install and update smoke test passed for $($expectedSkills.Count) public skills across codex and claude-code."
    } else {
        Write-Output "Install smoke test passed for codex and claude-code."
    }
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
