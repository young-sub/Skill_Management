[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$DestinationRoot,
    [string]$SkillsCommand = 'npx',
    [string]$SourcePackage,
    [ValidateSet('local', 'github')]
    [string]$SourceType = 'local',
    [string]$EvidencePath,
    [switch]$VerifyUpdate,
    [switch]$ApproveRemoteEvidence
)

$ErrorActionPreference = 'Stop'

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Join-Path $scriptDirectory '..'
}

$resolvedRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
if ([string]::IsNullOrWhiteSpace($SourcePackage)) {
    $SourcePackage = $resolvedRoot
}
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

function Get-SkillTreeDrift {
    param(
        [string]$SourceRoot,
        [string]$InstallRoot,
        [string[]]$SkillNames
    )
    $drift = [System.Collections.Generic.List[string]]::new()
    foreach ($skillName in $SkillNames) {
        $sourceSkill = Join-Path $SourceRoot "skills\$skillName"
        $sourceFiles = @{}
        foreach ($sourceFile in Get-ChildItem -LiteralPath $sourceSkill -Recurse -File) {
            if ($sourceFile.Extension -eq '.pyc' -or $sourceFile.FullName -match '[\\/]__pycache__[\\/]') { continue }
            $relative = $sourceFile.FullName.Substring($sourceSkill.Length).TrimStart('\').Replace('\', '/')
            $sourceFiles[$relative] = (Get-FileHash -LiteralPath $sourceFile.FullName -Algorithm SHA256).Hash
        }
        foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
            $installedSkill = Join-Path $InstallRoot "$providerRoot\$skillName"
            if (-not (Test-Path -LiteralPath $installedSkill -PathType Container)) {
                $drift.Add("$providerRoot/$skillName:missing")
                continue
            }
            $installedFiles = @{}
            foreach ($installedFile in Get-ChildItem -LiteralPath $installedSkill -Recurse -File) {
                if ($installedFile.Extension -eq '.pyc' -or $installedFile.FullName -match '[\\/]__pycache__[\\/]') { continue }
                $relative = $installedFile.FullName.Substring($installedSkill.Length).TrimStart('\').Replace('\', '/')
                $installedFiles[$relative] = (Get-FileHash -LiteralPath $installedFile.FullName -Algorithm SHA256).Hash
            }
            foreach ($relative in $sourceFiles.Keys) {
                if (-not $installedFiles.ContainsKey($relative)) {
                    $drift.Add("$providerRoot/$skillName/${relative}:missing")
                } elseif ($sourceFiles[$relative] -ne $installedFiles[$relative]) {
                    $drift.Add("$providerRoot/$skillName/${relative}:hash_mismatch")
                }
            }
            foreach ($relative in $installedFiles.Keys) {
                if (-not $sourceFiles.ContainsKey($relative)) {
                    $drift.Add("$providerRoot/$skillName/${relative}:extra")
                }
            }
        }
    }
    return @($drift | Sort-Object)
}

function Write-SmokeEvidence {
    param([string]$Path, [hashtable]$Payload)
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    $resolvedEvidence = [System.IO.Path]::GetFullPath($Path)
    $parent = Split-Path -Parent $resolvedEvidence
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $Payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resolvedEvidence -Encoding utf8
}

New-Item -ItemType Directory -Path $resolvedDestination -Force | Out-Null
$previousLocation = Get-Location

try {
    Set-Location -LiteralPath $resolvedDestination
    $installArguments = @(
        'skills', 'add', $SourcePackage, '--skill', '*',
        '-a', 'codex', '-a', 'claude-code', '--copy', '-y'
    )
    & $SkillsCommand @installArguments
    if ($LASTEXITCODE -ne 0) {
        throw "skills CLI failed with exit code $LASTEXITCODE"
    }

    $installDrift = @(Get-SkillTreeDrift -SourceRoot $resolvedRoot -InstallRoot $resolvedDestination -SkillNames $expectedSkills)
    if ($installDrift.Count -gt 0) {
        throw "Installed public Skill trees differ from source: $($installDrift -join ', ')"
    }

    $nativeUpdateStatus = 'not_run'
    $localRefreshStatus = 'not_run'
    if ($VerifyUpdate) {
        foreach ($skillName in $expectedSkills) {
            foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
                $installedSkill = Join-Path $resolvedDestination "$providerRoot\$skillName"
                foreach ($installed in Get-ChildItem -LiteralPath $installedSkill -Recurse -File) {
                    Set-Content -LiteralPath $installed.FullName -Value '# stale install' -Encoding utf8
                }
            }
        }

        $updateArguments = @('skills', 'update', '-p', '-y')
        & $SkillsCommand @updateArguments
        if ($LASTEXITCODE -ne 0) {
            throw "skills CLI update failed with exit code $LASTEXITCODE"
        }

        $treeDrift = @(Get-SkillTreeDrift `
            -SourceRoot $resolvedRoot `
            -InstallRoot $resolvedDestination `
            -SkillNames $expectedSkills)
        if ($treeDrift.Count -gt 0 -and $SourceType -eq 'github') {
            throw "Remote GitHub update left stale public Skill trees: $($treeDrift -join ', ')"
        }
        if ($treeDrift.Count -gt 0) {
            $nativeUpdateStatus = 'unsupported_for_local_source'
            Write-Output 'Native update unsupported/no-op for local source; running local source refresh.'
            & $SkillsCommand @installArguments
            if ($LASTEXITCODE -ne 0) {
                throw "skills CLI local source refresh failed with exit code $LASTEXITCODE"
            }
            $treeDrift = @(Get-SkillTreeDrift `
                -SourceRoot $resolvedRoot `
                -InstallRoot $resolvedDestination `
                -SkillNames $expectedSkills)
            if ($treeDrift.Count -gt 0) {
                throw "Local source refresh left stale public Skill trees: $($treeDrift -join ', ')"
            }
            $localRefreshStatus = 'passed'
            Write-Output "Local source refresh passed for $($expectedSkills.Count) public skills across codex and claude-code."
        } else {
            $nativeUpdateStatus = 'passed'
        }
        Write-Output "Install and update smoke test passed for $($expectedSkills.Count) public skills across codex and claude-code."
    } else {
        Write-Output "Install smoke test passed for codex and claude-code."
    }
    $remoteSourceMatch = [regex]::Match(
        $SourcePackage,
        '^https://github\.com/[^/]+/[^/]+/(?:tree|commit)/(?<commit>[0-9a-fA-F]{40})$'
    )
    $remoteEvidenceApproved = (
        $ApproveRemoteEvidence -and
        $SourceType -eq 'github' -and
        $VerifyUpdate -and
        $remoteSourceMatch.Success
    )
    $unverifiedChecks = @()
    if (-not $remoteEvidenceApproved) {
        $unverifiedChecks += 'remote_github_update'
    }
    $provenanceScript = Join-Path $scriptDirectory 'evidence_provenance.py'
    $evidenceCommand = @(
        'powershell', '-NoProfile', '-File', $MyInvocation.MyCommand.Path,
        '-RepositoryRoot', $resolvedRoot, '-SourcePackage', $SourcePackage,
        '-SourceType', $SourceType
    )
    if ($VerifyUpdate) { $evidenceCommand += '-VerifyUpdate' }
    if ($ApproveRemoteEvidence) { $evidenceCommand += '-ApproveRemoteEvidence' }
    $provenanceArguments = @(
        $provenanceScript,
        '--repository-root', $resolvedRoot,
        '--source-type', $SourceType,
        '--source-package', $SourcePackage,
        '--result', 'passed'
    )
    foreach ($commandPart in $evidenceCommand) {
        $encodedPart = [Convert]::ToBase64String(
            [Text.Encoding]::UTF8.GetBytes([string]$commandPart)
        )
        $provenanceArguments += @('--command-part-base64', $encodedPart)
    }
    foreach ($check in $unverifiedChecks) {
        $provenanceArguments += @('--unverified-check', $check)
    }
    foreach ($provider in @('codex', 'claude-code')) {
        $provenanceArguments += @('--provider', $provider)
    }
    $provenanceText = (& python @provenanceArguments 2>&1) -join "`n"
    if ($LASTEXITCODE -ne 0) {
        throw "Evidence provenance failed: $provenanceText"
    }
    $provenance = $provenanceText | ConvertFrom-Json
    if (
        $remoteEvidenceApproved -and
        $provenance.git_commit.ToLowerInvariant() -ne
            $remoteSourceMatch.Groups['commit'].Value.ToLowerInvariant()
    ) {
        throw 'Remote evidence source commit does not match the local source revision.'
    }
    Write-SmokeEvidence -Path $EvidencePath -Payload ([ordered]@{
        schema_version = 2
        evidence_kind = $(
            if ($remoteEvidenceApproved) { 'remote_github_update' }
            elseif ($localRefreshStatus -eq 'passed') { 'local_source_install_refresh' }
            else { 'install_and_update_smoke' }
        )
        generated_at = $provenance.generated_at
        repository = $provenance.repository
        git_commit = $provenance.git_commit
        git_tree = $provenance.git_tree
        git_dirty = $provenance.git_dirty
        dirty_paths = @($provenance.dirty_paths)
        branch = $provenance.branch
        command = @($provenance.command)
        cwd = $provenance.cwd
        tool_versions = [ordered]@{
            python = $provenance.tool_versions.python
            git = $provenance.tool_versions.git
            powershell = $PSVersionTable.PSVersion.ToString()
            skills_command = $SkillsCommand
        }
        source_package = $SourcePackage
        source_type = $SourceType
        verification_mode = $(if ($VerifyUpdate) { 'install_and_update' } else { 'install' })
        public_skill_count = $expectedSkills.Count
        providers = @('codex', 'claude-code')
        catalog_sha256 = $provenance.catalog_sha256
        resource_manifest_sha256 = $provenance.resource_manifest_sha256
        result = 'passed'
        unverified_checks = $unverifiedChecks
        complete_skill_tree_comparison = @{ status = 'passed'; algorithm = 'SHA256' }
        native_update = @{ status = $nativeUpdateStatus }
        local_source_refresh = @{ status = $localRefreshStatus }
        remote_github_update = @{
            status = $(if ($remoteEvidenceApproved) { 'passed' } else { 'not_verified' })
            evidence_kind = 'remote_github_update'
        }
    })
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
