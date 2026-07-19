[CmdletBinding()]
param(
    [string]$RepositoryRoot
)

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
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

    $allowedFields = @('name', 'description')
    foreach ($line in $frontmatter) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        if ($line -notmatch '^([A-Za-z0-9_-]+):') {
            $errors.Add(
                "invalid frontmatter line: '$line' in '$($skillDirectory.Name)'"
            )
            continue
        }
        $field = $Matches[1]
        if ($allowedFields -notcontains $field) {
            $errors.Add(
                "unsupported frontmatter field: '$field' in '$($skillDirectory.Name)'"
            )
        }
    }

    foreach ($requiredField in $allowedFields) {
        $hasField = $frontmatter | Where-Object {
            $_ -match "^$([Regex]::Escape($requiredField)):\s*.+$"
        }
        if (-not $hasField) {
            $errors.Add(
                "missing required frontmatter field: '$requiredField' in '$($skillDirectory.Name)'"
            )
        }
    }

    $skillRootPath = [System.IO.Path]::GetFullPath($skillDirectory.FullName)
    $skillRootPrefix = $skillRootPath.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $textExtensions = @('.json', '.md', '.ps1', '.py', '.sh', '.txt', '.yaml', '.yml')
    foreach ($resourceFile in Get-ChildItem -LiteralPath $skillDirectory.FullName -File -Recurse) {
        if ($textExtensions -notcontains $resourceFile.Extension.ToLowerInvariant()) {
            continue
        }
        $resourceText = Get-Content -LiteralPath $resourceFile.FullName -Raw -Encoding utf8
        $relativeReferences = [Regex]::Matches(
            $resourceText,
            '(?<path>(?:\.\.[/\\])+[A-Za-z0-9._/\\-]+)'
        )
        foreach ($relativeReference in $relativeReferences) {
            $targetPath = [System.IO.Path]::GetFullPath(
                (Join-Path $resourceFile.DirectoryName $relativeReference.Groups['path'].Value)
            )
            $isInsideSkill = $targetPath.Equals(
                $skillRootPath,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -or $targetPath.StartsWith(
                $skillRootPrefix,
                [System.StringComparison]::OrdinalIgnoreCase
            )
            if (-not $isInsideSkill) {
                $errors.Add(
                    "resource reference escapes skill directory: '$($resourceFile.FullName)' -> '$($relativeReference.Groups['path'].Value)'"
                )
            }
        }
    }
}

$legacyRoot = Join-Path $resolvedRoot 'legacy-skills'
if (Test-Path -LiteralPath $legacyRoot -PathType Container) {
    foreach ($legacyEntrypoint in Get-ChildItem -LiteralPath $legacyRoot -Filter 'SKILL.md' -File -Recurse) {
        $errors.Add(
            "legacy skill remains discoverable: '$($legacyEntrypoint.FullName)'"
        )
    }
} else {
    $errors.Add('missing required distribution artifact: legacy-skills/')
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
    foreach ($skillName in @($catalog.legacy_skills)) {
        $legacyEntrypoint = Join-Path $legacyRoot "$skillName\SKILL.legacy.md"
        if (-not (Test-Path -LiteralPath $legacyEntrypoint -PathType Leaf)) {
            $errors.Add("missing preserved legacy skill: '$skillName'")
        }
    }
} else {
    $errors.Add(
        'missing required distribution artifact: distribution/catalog.json'
    )
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
    $agentsHash = (Get-FileHash -LiteralPath $agentsPath -Algorithm SHA256).Hash
    $claudeHash = (Get-FileHash -LiteralPath $claudePath -Algorithm SHA256).Hash
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
