[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $scriptDirectory 'hash-utils.ps1')

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
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

function ConvertTo-StableText([string]$Content) {
    if ($null -eq $Content) {
        return $null
    }
    return $Content.Replace("`r`n", "`n").Replace("`r", "`n")
}

function Get-StableTextHash([string]$Content) {
    $bytes = $utf8WithoutBom.GetBytes((ConvertTo-StableText $Content))
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha256.Dispose()
    }
}

function Get-StableFileHash([System.IO.FileInfo]$File) {
    $textExtensions = @('.json', '.md', '.html', '.py', '.ps1', '.txt', '.yaml', '.yml')
    if ($File.Extension.ToLowerInvariant() -in $textExtensions) {
        return Get-StableTextHash ([System.IO.File]::ReadAllText($File.FullName))
    }
    return Get-Sha256Hex -LiteralPath $File.FullName
}

function ConvertTo-StableJsonString([string]$Value) {
    $builder = [System.Text.StringBuilder]::new()
    foreach ($character in $Value.ToCharArray()) {
        $codePoint = [int]$character
        switch ($codePoint) {
            8 { [void]$builder.Append('\b'); continue }
            9 { [void]$builder.Append('\t'); continue }
            10 { [void]$builder.Append('\n'); continue }
            12 { [void]$builder.Append('\f'); continue }
            13 { [void]$builder.Append('\r'); continue }
            34 { [void]$builder.Append('\"'); continue }
            92 { [void]$builder.Append('\\'); continue }
        }
        if ($codePoint -lt 32) {
            [void]$builder.Append(('\u{0:x4}' -f $codePoint))
        } else {
            [void]$builder.Append($character)
        }
    }
    return '"' + $builder.ToString() + '"'
}

function ConvertTo-StableManifestJson($Files) {
    $entries = [System.Collections.Generic.List[string]]::new()
    foreach ($entry in $Files.GetEnumerator()) {
        $entries.Add(
            (ConvertTo-StableJsonString ([string]$entry.Key)) + ':' +
            (ConvertTo-StableJsonString ([string]$entry.Value))
        )
    }
    return '{"schema_version":1,"algorithm":"sha256","root":"skills",' +
        '"excludes":["maintain-agent-harness/resources/public-resource-manifest.json"],' +
        '"files":{' + ($entries -join ',') + '}}'
}

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
    $sourceContent = ConvertTo-StableText (Get-Content -LiteralPath $sourcePath -Raw -Encoding utf8)
    $sourceHash = Get-StableTextHash $sourceContent

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
            $isSkillEntrypoint = [System.IO.Path]::GetFileName($targetPath) -eq 'SKILL.md'
            if ($isSkillEntrypoint) {
                $frontmatterMatch = [Regex]::Match(
                    $sourceContent,
                    '\A(?<frontmatter>---\n.*?\n---)(?:\n)?',
                    [System.Text.RegularExpressions.RegexOptions]::Singleline
                )
                if (-not $frontmatterMatch.Success) {
                    Write-Output "ERROR canonical SKILL.md frontmatter missing: '$($resource.source)'"
                    exit 1
                }
                $body = $sourceContent.Substring($frontmatterMatch.Length)
                $generatedContent = @(
                    $frontmatterMatch.Groups['frontmatter'].Value
                    $header
                    ''
                    $body
                ) -join "`n"
            } elseif ($extension -eq '.html') {
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
                ConvertTo-StableText ([System.IO.File]::ReadAllText($targetPath))
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

    $manifestFiles = [System.Collections.Generic.SortedDictionary[string, string]]::new(
        [System.StringComparer]::Ordinal
    )
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
            $manifestFiles[$relative] = Get-StableFileHash $file
        }
    }
    # Avoid ConvertTo-Json because Windows PowerShell and PowerShell 7 serialize
    # ordered dictionaries differently. The fixed schema and explicit escaping
    # keep generated bytes stable across both local and CI hosts.
    $manifestContent = (ConvertTo-StableManifestJson $manifestFiles) + "`n"

    if ($Check) {
        $sourceContent = if (Test-Path -LiteralPath $manifestSourcePath -PathType Leaf) {
            ConvertTo-StableText ([System.IO.File]::ReadAllText($manifestSourcePath))
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
                ConvertTo-StableText ([System.IO.File]::ReadAllText($targetPath))
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
