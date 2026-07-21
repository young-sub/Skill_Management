function Get-Sha256Hex {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath
    )

    $resolvedPath = [System.IO.Path]::GetFullPath($LiteralPath)
    $stream = [System.IO.File]::OpenRead($resolvedPath)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString(
            $sha256.ComputeHash($stream)
        )).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha256.Dispose()
        $stream.Dispose()
    }
}
