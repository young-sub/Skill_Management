[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$DestinationRoot,
    [string]$SkillsCommand = 'npx',
    [string]$GitCommand = 'git',
    [string]$SourcePackage,
    [string]$ExpectedSourceCommit,
    [ValidateSet('local', 'github')]
    [string]$SourceType = 'local',
    [string]$EvidencePath,
    [switch]$VerifyUpdate,
    [switch]$ApproveRemoteEvidence
)

$ErrorActionPreference = 'Stop'

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDirectory 'hash-utils.ps1')
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
$harnessCohortSkills = @(
    'setup-agent-harness',
    'design-goal',
    'execute-codex-goal',
    'close-goal',
    'maintain-agent-harness',
    'diagnose'
)
$hasCompleteHarnessCohort = @(
    $harnessCohortSkills | Where-Object { $expectedSkills -notcontains $_ }
).Count -eq 0
$remoteSourceMatch = [regex]::Match(
    $SourcePackage,
    '^https://github\.com/(?<owner>[^/]+)/(?<repo>[^/]+)/(?<kind>tree|commit)/(?<ref>[^/]+)$'
)
$boundSourceCommit = $ExpectedSourceCommit
if (
    [string]::IsNullOrWhiteSpace($boundSourceCommit) -and
    $remoteSourceMatch.Success -and
    $remoteSourceMatch.Groups['ref'].Value -match '^[0-9a-fA-F]{40}$'
) {
    $boundSourceCommit = $remoteSourceMatch.Groups['ref'].Value
}
$remoteEvidenceApproved = (
    $ApproveRemoteEvidence -and
    $SourceType -eq 'github' -and
    $VerifyUpdate -and
    $remoteSourceMatch.Success -and
    $boundSourceCommit -match '^[0-9a-fA-F]{40}$'
)
$resolvedRemoteCommits = @()
$remoteDefaultBranch = $null
$remoteDefaultCommit = $null
if ($remoteEvidenceApproved) {
    $remoteRepository = "https://github.com/$($remoteSourceMatch.Groups['owner'].Value)/$($remoteSourceMatch.Groups['repo'].Value).git"
    $remoteRef = $remoteSourceMatch.Groups['ref'].Value
    $resolutionOutput = @(& $GitCommand ls-remote --exit-code $remoteRepository "refs/heads/$remoteRef" "refs/tags/$remoteRef" "refs/tags/$remoteRef^{}" 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Remote source ref could not be resolved: $($resolutionOutput -join [Environment]::NewLine)"
    }
    $resolvedRemoteCommits = @(
        $resolutionOutput |
            ForEach-Object { ([string]$_ -split '\s+')[0] } |
            Where-Object { $_ -match '^[0-9a-fA-F]{40}$' } |
            Sort-Object -Unique
    )
    if ($resolvedRemoteCommits -notcontains $boundSourceCommit.ToLowerInvariant()) {
        throw "Remote source ref does not resolve to ExpectedSourceCommit: $remoteRef"
    }
    $defaultResolutionOutput = @(& $GitCommand ls-remote --symref --exit-code $remoteRepository HEAD 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Remote default branch could not be resolved: $($defaultResolutionOutput -join [Environment]::NewLine)"
    }
    foreach ($line in $defaultResolutionOutput) {
        if ([string]$line -match '^ref:\s+(?<branch>refs/heads/\S+)\s+HEAD$') {
            $remoteDefaultBranch = $Matches['branch']
        } elseif ([string]$line -match '^(?<commit>[0-9a-fA-F]{40})\s+HEAD$') {
            $remoteDefaultCommit = $Matches['commit'].ToLowerInvariant()
        }
    }
    if ($remoteDefaultCommit -ne $boundSourceCommit.ToLowerInvariant()) {
        throw "Remote default branch does not resolve to ExpectedSourceCommit: $remoteDefaultBranch"
    }
}

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
        $sourceDirectories = [System.Collections.Generic.HashSet[string]]::new(
            [System.StringComparer]::Ordinal
        )
        foreach ($sourceFile in Get-ChildItem -LiteralPath $sourceSkill -Recurse -File) {
            if ($sourceFile.Extension -eq '.pyc' -or $sourceFile.FullName -match '[\\/]__pycache__[\\/]') { continue }
            $relative = $sourceFile.FullName.Substring($sourceSkill.Length).TrimStart('\').Replace('\', '/')
            $sourceFiles[$relative] = Get-Sha256Hex -LiteralPath $sourceFile.FullName
            $parent = [System.IO.Path]::GetDirectoryName($relative).Replace('\', '/')
            while (-not [string]::IsNullOrWhiteSpace($parent)) {
                [void]$sourceDirectories.Add($parent)
                $parent = [System.IO.Path]::GetDirectoryName($parent).Replace('\', '/')
            }
        }
        foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
            $installedSkill = Join-Path $InstallRoot "$providerRoot\$skillName"
            if (-not (Test-Path -LiteralPath $installedSkill -PathType Container)) {
                $drift.Add("$providerRoot/$skillName:missing")
                continue
            }
            $installedFiles = @{}
            $installedDirectories = [System.Collections.Generic.HashSet[string]]::new(
                [System.StringComparer]::Ordinal
            )
            foreach ($installedDirectory in Get-ChildItem -LiteralPath $installedSkill -Recurse -Directory) {
                $relative = $installedDirectory.FullName.Substring($installedSkill.Length).TrimStart('\').Replace('\', '/')
                [void]$installedDirectories.Add($relative)
            }
            foreach ($installedFile in Get-ChildItem -LiteralPath $installedSkill -Recurse -File) {
                if ($installedFile.Extension -eq '.pyc' -or $installedFile.FullName -match '[\\/]__pycache__[\\/]') { continue }
                $relative = $installedFile.FullName.Substring($installedSkill.Length).TrimStart('\').Replace('\', '/')
                $installedFiles[$relative] = Get-Sha256Hex -LiteralPath $installedFile.FullName
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
            foreach ($relative in $sourceDirectories) {
                if (-not $installedDirectories.Contains($relative)) {
                    $drift.Add("$providerRoot/$skillName/${relative}:directory_missing")
                }
            }
            foreach ($relative in $installedDirectories) {
                if (-not $sourceDirectories.Contains($relative)) {
                    $drift.Add("$providerRoot/$skillName/${relative}:directory_extra")
                }
            }
        }
    }
    return @($drift | Sort-Object)
}

function Install-ExactHarnessCohort {
    param(
        [string]$SourceRoot,
        [string]$InstallRoot
    )
    $runtime = Join-Path $SourceRoot 'skills\setup-agent-harness\scripts\core_harness.py'
    $skillSource = Join-Path $SourceRoot 'skills'
    $manifest = Join-Path $SourceRoot 'authoring\public-resource-manifest.json'
    foreach ($required in @($runtime, $manifest)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Harness cohort installer resource is missing: $required"
        }
    }
    foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
        $installedRoot = Join-Path $InstallRoot $providerRoot
        $output = @(
            & python $runtime install-cohort `
                --source-root $skillSource `
                --install-root $installedRoot `
                --manifest $manifest `
                --approved-install-root $installedRoot 2>&1
        )
        if ($LASTEXITCODE -ne 0) {
            throw "Harness cohort replacement failed for ${providerRoot}: $($output -join [Environment]::NewLine)"
        }
        try {
            $payload = ($output -join "`n") | ConvertFrom-Json
        } catch {
            throw "Harness cohort replacement emitted invalid output for ${providerRoot}: $($output -join [Environment]::NewLine)"
        }
        if ($payload.status -ne 'installed') {
            throw "Harness cohort replacement did not complete for ${providerRoot}: $($output -join [Environment]::NewLine)"
        }
    }
}

function Get-PublicSkillTreeDigest {
    param([string]$InstallRoot, [string[]]$SkillNames)
    $entries = [System.Collections.Generic.List[string]]::new()
    foreach ($skillName in $SkillNames) {
        foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
            $installedSkill = Join-Path $InstallRoot "$providerRoot\$skillName"
            foreach ($installedDirectory in Get-ChildItem -LiteralPath $installedSkill -Recurse -Directory) {
                $relative = $installedDirectory.FullName.Substring($InstallRoot.Length).TrimStart('\').Replace('\', '/')
                $entries.Add("directory:$relative")
            }
            foreach ($installedFile in Get-ChildItem -LiteralPath $installedSkill -Recurse -File) {
                if ($installedFile.Extension -eq '.pyc' -or $installedFile.FullName -match '[\\/]__pycache__[\\/]') { continue }
                $relative = $installedFile.FullName.Substring($InstallRoot.Length).TrimStart('\').Replace('\', '/')
                $hash = Get-Sha256Hex -LiteralPath $installedFile.FullName
                $entries.Add("$relative=$hash")
            }
        }
    }
    $payload = [Text.Encoding]::UTF8.GetBytes((@($entries | Sort-Object) -join "`n"))
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($payload))).Replace('-', '')
    } finally {
        $sha.Dispose()
    }
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
    if ($hasCompleteHarnessCohort) {
        Install-ExactHarnessCohort -SourceRoot $resolvedRoot -InstallRoot $resolvedDestination
    }

    $installDrift = @(Get-SkillTreeDrift -SourceRoot $resolvedRoot -InstallRoot $resolvedDestination -SkillNames $expectedSkills)
    if ($installDrift.Count -gt 0) {
        throw "Installed public Skill trees differ from source: $($installDrift -join ', ')"
    }
    $installedTreeBeforeUpdate = Get-PublicSkillTreeDigest -InstallRoot $resolvedDestination -SkillNames $expectedSkills

    $nativeUpdateStatus = 'not_run'
    $localRefreshStatus = 'not_run'
    if ($VerifyUpdate) {
        if (-not $remoteEvidenceApproved) {
            foreach ($skillName in $expectedSkills) {
                foreach ($providerRoot in @('.agents\skills', '.claude\skills')) {
                    $installedSkill = Join-Path $resolvedDestination "$providerRoot\$skillName"
                    foreach ($installed in Get-ChildItem -LiteralPath $installedSkill -Recurse -File) {
                        Set-Content -LiteralPath $installed.FullName -Value '# stale install' -Encoding utf8
                    }
                }
            }
        }

        $updateArguments = @('skills', 'update', '-p', '-y')
        & $SkillsCommand @updateArguments
        if ($LASTEXITCODE -ne 0) {
            throw "skills CLI update failed with exit code $LASTEXITCODE"
        }
        if ($hasCompleteHarnessCohort) {
            Install-ExactHarnessCohort -SourceRoot $resolvedRoot -InstallRoot $resolvedDestination
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
            if ($hasCompleteHarnessCohort) {
                Install-ExactHarnessCohort -SourceRoot $resolvedRoot -InstallRoot $resolvedDestination
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
    $installedTreeAfterUpdate = Get-PublicSkillTreeDigest -InstallRoot $resolvedDestination -SkillNames $expectedSkills
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
    if (-not [string]::IsNullOrWhiteSpace($ExpectedSourceCommit)) {
        $evidenceCommand += @('-ExpectedSourceCommit', $ExpectedSourceCommit)
    }
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
            $boundSourceCommit.ToLowerInvariant()
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
        expected_source_commit = $boundSourceCommit
        installed_tree_before_update_sha256 = $installedTreeBeforeUpdate
        installed_tree_after_update_sha256 = $installedTreeAfterUpdate
        remote_source_resolution = @{
            status = $(if ($remoteEvidenceApproved) { 'passed' } else { 'not_verified' })
            resolved_commits = @($resolvedRemoteCommits)
        }
        remote_default_resolution = @{
            status = $(if ($remoteEvidenceApproved) { 'passed' } else { 'not_verified' })
            branch = $remoteDefaultBranch
            commit = $remoteDefaultCommit
        }
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
            verification_mode = $(if ($remoteEvidenceApproved) { 'idempotent_current_revision' } else { 'not_verified' })
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
