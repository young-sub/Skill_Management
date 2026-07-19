[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [switch]$Check
)

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

foreach ($resource in $resourceMap.resources) {
    $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $authoringRoot $resource.source))
    if (-not $sourcePath.StartsWith(
        $authoringRootPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        Write-Output "ERROR source escapes authoring directory: '$($resource.source)'"
        exit 1
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
            $header = if ($extension -eq '.md') {
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
            $generatedContent = @($header; ''; $sourceContent) -join "`n"
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

if ($driftFound) {
    exit 1
}
