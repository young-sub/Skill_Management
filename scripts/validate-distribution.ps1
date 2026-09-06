[CmdletBinding()]
param(
    [string]$RepositoryRoot
)

$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDirectory 'hash-utils.ps1')
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Join-Path $scriptDirectory '..'
}

$resolvedRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$skillsRoot = Join-Path $resolvedRoot 'skills'
if (-not (Test-Path -LiteralPath $skillsRoot -PathType Container)) {
    Write-Output 'ERROR missing required distribution artifact: skills/'
    exit 1
}
$errors = [System.Collections.Generic.List[string]]::new()
$actualPublicSkills = [System.Collections.Generic.List[string]]::new()

foreach ($skillDirectory in Get-ChildItem -LiteralPath $skillsRoot -Directory) {
    $skillFile = Join-Path $skillDirectory.FullName 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        continue
    }
    $actualPublicSkills.Add($skillDirectory.Name)

    $lines = Get-Content -LiteralPath $skillFile -Encoding utf8
    $closingDelimiterIndex = -1
    if ($lines.Count -gt 1 -and $lines[0] -eq '---') {
        for ($index = 1; $index -lt $lines.Count; $index++) {
            if ($lines[$index] -eq '---') {
                $closingDelimiterIndex = $index
                break
            }
        }
    }
    if ($closingDelimiterIndex -lt 0) {
        $errors.Add("invalid frontmatter: '$($skillDirectory.Name)/SKILL.md'")
        continue
    }

    $frontmatter = [System.Collections.Generic.List[string]]::new()
    for ($index = 1; $index -lt $closingDelimiterIndex; $index++) {
        $frontmatter.Add($lines[$index])
    }

    $nameLine = $frontmatter |
        Where-Object { $_ -match '^name:\s*(.+?)\s*$' } |
        Select-Object -First 1

    $declaredName = if ($nameLine -match '^name:\s*["'']?(.+?)["'']?\s*$') {
        $Matches[1]
    } else {
        ''
    }

    if ($declaredName -ne $skillDirectory.Name) {
        $errors.Add(
            "directory/name mismatch: '$($skillDirectory.Name)' declares '$declaredName'"
        )
    }

    $allowedFields = @('name', 'description', 'license', 'metadata')
    $requiredFields = @('name', 'description')
    $parentField = ''
    foreach ($line in $frontmatter) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        if ($line -match '^\s+') {
            if ($parentField -ne 'metadata' -or $line -notmatch '^\s+[A-Za-z0-9_-]+:\s*.+$') {
                $errors.Add(
                    "invalid frontmatter line: '$line' in '$($skillDirectory.Name)'"
                )
            }
            continue
        }
        if ($line -notmatch '^([A-Za-z0-9_-]+):') {
            $errors.Add(
                "invalid frontmatter line: '$line' in '$($skillDirectory.Name)'"
            )
            continue
        }
        $field = $Matches[1]
        $parentField = $field
        if ($allowedFields -notcontains $field) {
            $errors.Add(
                "unsupported frontmatter field: '$field' in '$($skillDirectory.Name)'"
            )
        }
    }

    foreach ($requiredField in $requiredFields) {
        $hasField = $frontmatter | Where-Object {
            $_ -match "^$([Regex]::Escape($requiredField)):\s*.+$"
        }
        if (-not $hasField) {
            $errors.Add(
                "missing required frontmatter field: '$requiredField' in '$($skillDirectory.Name)'"
            )
        }
    }

}

$selfContainmentValidator = Join-Path $scriptDirectory 'validate_self_containment.py'
if (-not (Test-Path -LiteralPath $selfContainmentValidator -PathType Leaf)) {
    $errors.Add('missing self-containment rule validator')
} else {
    $scannerText = (& python $selfContainmentValidator --repository-root $resolvedRoot 2>&1) -join "`n"
    $scannerExitCode = $LASTEXITCODE
    try {
        $scannerPayload = $scannerText | ConvertFrom-Json
        foreach ($finding in @($scannerPayload.findings)) {
            $errors.Add(
                "[$($finding.rule_id)] $($finding.skill)/$($finding.source_path) $($finding.locator): $($finding.evidence) -> $($finding.normalized_target)"
            )
        }
        foreach ($allowlistError in @($scannerPayload.allowlist_errors)) {
            $errors.Add("self-containment allowlist error: $allowlistError")
        }
        if ($scannerExitCode -ne 0 -and @($scannerPayload.findings).Count -eq 0 -and @($scannerPayload.allowlist_errors).Count -eq 0) {
            $errors.Add("self-containment validator failed without findings: $scannerText")
        }
    } catch {
        $errors.Add("invalid self-containment validator output: $scannerText")
    }
}

$retiredLegacyRoot = Join-Path $resolvedRoot 'legacy-skills'
if (Test-Path -LiteralPath $retiredLegacyRoot -PathType Container) {
    $errors.Add('retired distribution artifact remains: legacy-skills/')
}

$catalogPath = Join-Path $resolvedRoot 'distribution\catalog.json'
if (Test-Path -LiteralPath $catalogPath -PathType Leaf) {
    $catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding utf8 |
        ConvertFrom-Json
    if ($catalog.schema_version -ne 1) {
        $errors.Add(
            "unsupported distribution catalog schema: '$($catalog.schema_version)'"
        )
    }
    $expectedPublicSkills = @($catalog.public_skills)
    foreach ($skillName in $actualPublicSkills) {
        if ($expectedPublicSkills -notcontains $skillName) {
            $errors.Add("unexpected public skill: '$skillName'")
        }
    }
    foreach ($skillName in $expectedPublicSkills) {
        if ($actualPublicSkills -notcontains $skillName) {
            $errors.Add("missing expected public skill: '$skillName'")
        }
    }
} else {
    $errors.Add(
        'missing required distribution artifact: distribution/catalog.json'
    )
}

$candidatePath = Join-Path $resolvedRoot 'distribution\release-candidate.json'
if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
    try {
        $candidate = Get-Content -LiteralPath $candidatePath -Raw -Encoding utf8 |
            ConvertFrom-Json
        if ($candidate.schema_version -ne 2) {
            $errors.Add("unsupported release candidate schema: '$($candidate.schema_version)'")
        }
        if ($candidate.version -ne '2.0.0') {
            $errors.Add('invalid release metadata version')
        }
        if ($candidate.stage -eq 'release-candidate') {
            if ($candidate.live_release -ne $false -or $null -ne $candidate.tag) {
                $errors.Add('release candidate must not claim a live release or tag')
            }
            if ($candidate.public_skill_count -ne $expectedPublicSkills.Count) {
                $errors.Add('release candidate public skill count does not match catalog')
            }
            if (@(Compare-Object @($candidate.public_skills) @($expectedPublicSkills)).Count -ne 0) {
                $errors.Add('release candidate public skills do not match catalog')
            }
        } elseif ($candidate.stage -eq 'stable') {
            if ($candidate.live_release -ne $true -or $candidate.tag -ne 'v2.0.0') {
                $errors.Add('stable release must claim the v2.0.0 live tag')
            }
            if ([string]$candidate.release_date -notmatch '^\d{4}-\d{2}-\d{2}$') {
                $errors.Add('stable release must declare a release date')
            }
            $releaseNotesPath = Join-Path (Split-Path -Parent $candidatePath) ([string]$candidate.release_notes).Replace('/', '\')
            if (-not (Test-Path -LiteralPath $releaseNotesPath -PathType Leaf)) {
                $errors.Add('stable release notes are missing')
            }
        } else {
            $errors.Add("unsupported release stage: '$($candidate.stage)'")
        }
        if (@($candidate.future_core_skills).Count -ne 0 -or @($catalog.future_core_skills).Count -ne 0) {
            $errors.Add('release candidate future Core Skill list must be empty')
        }
    } catch {
        $errors.Add("invalid release candidate metadata: $($_.Exception.Message)")
    }
} else {
    $errors.Add('missing required distribution artifact: distribution/release-candidate.json')
}

$evidenceValidator = Join-Path $resolvedRoot 'scripts\validate_evidence.py'
if (Test-Path -LiteralPath $evidenceValidator -PathType Leaf) {
    $evidenceOutput = & python $evidenceValidator --repository-root $resolvedRoot 2>&1
    if ($LASTEXITCODE -ne 0) {
        $errors.Add("release evidence validation failed: $($evidenceOutput -join ' ')")
    }
} else {
    $errors.Add('missing required distribution validator: scripts/validate_evidence.py')
}

$agentsPath = Join-Path $resolvedRoot 'AGENTS.md'
$claudePath = Join-Path $resolvedRoot 'CLAUDE.md'
$agentsExists = Test-Path -LiteralPath $agentsPath -PathType Leaf
$claudeExists = Test-Path -LiteralPath $claudePath -PathType Leaf
if (-not $agentsExists) {
    $errors.Add('missing required distribution artifact: AGENTS.md')
}
if (-not $claudeExists) {
    $errors.Add('missing required distribution artifact: CLAUDE.md')
}
if (
    $agentsExists -and
    $claudeExists
) {
    $agentsHash = Get-Sha256Hex -LiteralPath $agentsPath
    $claudeHash = Get-Sha256Hex -LiteralPath $claudePath
    if ($agentsHash -ne $claudeHash) {
        $errors.Add('instruction mirror drift: AGENTS.md and CLAUDE.md differ')
    }
    $instructionLineCount = (Get-Content -LiteralPath $agentsPath -Encoding utf8).Count
    if ($instructionLineCount -gt 100) {
        $errors.Add(
            "instruction router exceeds 100 lines: $instructionLineCount"
        )
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Output "ERROR $_" }
    exit 1
}

Write-Output 'Distribution validation passed.'
exit 0
