[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepositoryRoot = Join-Path $scriptDirectory '..'
}

$resolvedRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$authoringRoot = Join-Path $resolvedRoot 'authoring'
$skillsRoot = Join-Path $resolvedRoot 'skills'
$authoringRootPath = [System.IO.Path]::GetFullPath($authoringRoot)
$authoringRootPrefix = $authoringRootPath.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
$skillsRootPath = [System.IO.Path]::GetFullPath($skillsRoot)
$skillsRootPrefix = $skillsRootPath.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
$resourceMapPath = Join-Path $authoringRoot 'resource-map.json'
$resourceMap = Get-Content -LiteralPath $resourceMapPath -Raw -Encoding utf8 |
    ConvertFrom-Json
if ($resourceMap.schema_version -ne 1) {
    Write-Output "ERROR unsupported resource map schema: '$($resourceMap.schema_version)'"
    exit 1
}
$utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
$driftFound = $false
$manifestResource = $null

foreach ($resource in $resourceMap.resources) {
    $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $authoringRoot $resource.source))
    if (-not $sourcePath.StartsWith(
        $authoringRootPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        Write-Output "ERROR source escapes authoring directory: '$($resource.source)'"
        exit 1
    }
    if ($resource.source -eq 'public-resource-manifest.json') {
        if ($null -ne $manifestResource) {
            Write-Output 'ERROR duplicate public resource manifest mapping'
            exit 1
        }
        $manifestResource = $resource
        continue
    }
    $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $sourceContent = Get-Content -LiteralPath $sourcePath -Raw -Encoding utf8

    foreach ($target in $resource.targets) {
        $targetPath = [System.IO.Path]::GetFullPath((Join-Path $skillsRoot $target))
        if (-not $targetPath.StartsWith(
            $skillsRootPrefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            Write-Output "ERROR target escapes skills directory: '$target'"
            exit 1
        }
        $extension = [System.IO.Path]::GetExtension($targetPath).ToLowerInvariant()
        if ($extension -eq '.json') {
            # JSON has no comment syntax. Preserve valid JSON byte-for-byte.
            $generatedContent = $sourceContent
        } else {
            $header = if ($extension -in @('.md', '.html')) {
                @(
                    '<!-- Generated file. Do not edit directly. -->'
                    "<!-- Source: authoring/$($resource.source) -->"
                    "<!-- Source-SHA256: $sourceHash -->"
                )
            } else {
                @(
                    '# Generated file. Do not edit directly.'
                    "# Source: authoring/$($resource.source)"
                    "# Source-SHA256: $sourceHash"
                )
            }
            if ($extension -eq '.html') {
                $doctypeMatch = [Regex]::Match(
                    $sourceContent,
                    '\A(?<doctype><!doctype[^>]*>)(?:\r?\n)?',
                    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
                )
                if ($doctypeMatch.Success) {
                    $body = $sourceContent.Substring($doctypeMatch.Length)
                    $generatedContent = @(
                        $doctypeMatch.Groups['doctype'].Value
                        $header
                        ''
                        $body
                    ) -join "`n"
                } else {
                    $generatedContent = @($header; ''; $sourceContent) -join "`n"
                }
            } else {
                $generatedContent = @($header; ''; $sourceContent) -join "`n"
            }
        }

        if ($Check) {
            $targetContent = if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
                [System.IO.File]::ReadAllText($targetPath)
            } else {
                $null
            }
            if ($targetContent -ne $generatedContent) {
                Write-Output "ERROR generated resource drift: '$target'"
                $driftFound = $true
            } else {
                Write-Output "Verified $target"
            }
            continue
        }

        $targetDirectory = Split-Path -Parent $targetPath
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null

        [System.IO.File]::WriteAllText(
            $targetPath,
            $generatedContent,
            $utf8WithoutBom
        )
        Write-Output "Synced $($resource.source) -> $target"
    }
}

if ($null -ne $manifestResource) {
    $manifestSourcePath = [System.IO.Path]::GetFullPath(
        (Join-Path $authoringRoot $manifestResource.source)
    )
    $manifestTargetPaths = [System.Collections.Generic.List[string]]::new()
    foreach ($target in $manifestResource.targets) {
        $targetPath = [System.IO.Path]::GetFullPath((Join-Path $skillsRoot $target))
        if (-not $targetPath.StartsWith(
            $skillsRootPrefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            Write-Output "ERROR target escapes skills directory: '$target'"
            exit 1
        }
        $manifestTargetPaths.Add($targetPath)
    }

    $manifestFiles = [ordered]@{}
    $publicSkillDirectories = Get-ChildItem -LiteralPath $skillsRoot -Directory |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') -PathType Leaf
        } |
        Sort-Object Name
    foreach ($skillDirectory in $publicSkillDirectories) {
        $files = Get-ChildItem -LiteralPath $skillDirectory.FullName -File -Recurse |
            Where-Object {
                $_.FullName -notmatch '[\\/]__pycache__[\\/]' -and
                $_.Extension -ne '.pyc' -and
                $manifestTargetPaths -notcontains $_.FullName
            } |
            Sort-Object FullName
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($skillsRootPrefix.Length).Replace('\', '/')
            $manifestFiles[$relative] = (
                Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
            ).Hash.ToLowerInvariant()
        }
    }
    $manifest = [ordered]@{
        schema_version = 1
        algorithm = 'sha256'
        root = 'skills'
        excludes = @('maintain-agent-harness/resources/public-resource-manifest.json')
        files = $manifestFiles
    }
    $manifestContent = ($manifest | ConvertTo-Json -Depth 5) + "`n"

    if ($Check) {
        $sourceContent = if (Test-Path -LiteralPath $manifestSourcePath -PathType Leaf) {
            [System.IO.File]::ReadAllText($manifestSourcePath)
        } else {
            $null
        }
        if ($sourceContent -ne $manifestContent) {
            Write-Output "ERROR generated resource drift: 'authoring/$($manifestResource.source)'"
            $driftFound = $true
        } else {
            Write-Output "Verified authoring/$($manifestResource.source)"
        }
        foreach ($index in 0..($manifestResource.targets.Count - 1)) {
            $target = $manifestResource.targets[$index]
            $targetPath = $manifestTargetPaths[$index]
            $targetContent = if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
                [System.IO.File]::ReadAllText($targetPath)
            } else {
                $null
            }
            if ($targetContent -ne $manifestContent) {
                Write-Output "ERROR generated resource drift: '$target'"
                $driftFound = $true
            } else {
                Write-Output "Verified $target"
            }
        }
    } else {
        [System.IO.File]::WriteAllText(
            $manifestSourcePath,
            $manifestContent,
            $utf8WithoutBom
        )
        foreach ($index in 0..($manifestResource.targets.Count - 1)) {
            $target = $manifestResource.targets[$index]
            $targetPath = $manifestTargetPaths[$index]
            New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force |
                Out-Null
            [System.IO.File]::WriteAllText(
                $targetPath,
                $manifestContent,
                $utf8WithoutBom
            )
            Write-Output "Synced $($manifestResource.source) -> $target"
        }
    }
}

if ($driftFound) {
    exit 1
}
