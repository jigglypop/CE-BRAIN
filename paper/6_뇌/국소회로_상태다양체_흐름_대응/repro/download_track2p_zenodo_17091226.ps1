param(
    [Parameter(Mandatory = $true)]
    [string]$DestinationRoot,
    [ValidateRange(1, 32)]
    [int]$MaxParallel = 16,
    [ValidateRange(8, 512)]
    [int]$PartMiB = 160
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$sourceUrl = 'https://zenodo.org/api/records/17091226/files/data.zip/content'
$expectedBytes = [int64]9863306433
$expectedMd5 = '8d12ff6b93a26e28609c5a20b11f3d88'
$curlPath = Join-Path $env:SystemRoot 'System32\curl.exe'

if (-not (Test-Path -LiteralPath $curlPath -PathType Leaf)) {
    throw "curl.exe is missing: $curlPath"
}

$root = [IO.Path]::GetFullPath($DestinationRoot)
if ([IO.Path]::GetFileName($root.TrimEnd('\')) -ne 'track2p_zenodo_17091226') {
    throw "DestinationRoot must end with track2p_zenodo_17091226: $root"
}
New-Item -ItemType Directory -Force -Path $root | Out-Null

$partsRoot = Join-Path $root 'data.zip.parts'
New-Item -ItemType Directory -Force -Path $partsRoot | Out-Null
$destination = Join-Path $root 'data.zip'
$assembled = Join-Path $root 'data.zip.assembled'
$partBytes = [int64]$PartMiB * 1MB
$partCount = [int][Math]::Ceiling($expectedBytes / [double]$partBytes)

$parts = @()
for ($index = 0; $index -lt $partCount; $index++) {
    $start = [int64]$index * $partBytes
    $end = [Math]::Min($expectedBytes - 1, $start + $partBytes - 1)
    $path = Join-Path $partsRoot ('part_{0:D3}.bin' -f $index)
    $parts += [pscustomobject]@{
        Index = $index
        Start = $start
        End = $end
        Bytes = $end - $start + 1
        Path = $path
    }
}

$missing = @($parts | Where-Object {
    -not (Test-Path -LiteralPath $_.Path -PathType Leaf) -or
    (Get-Item -LiteralPath $_.Path).Length -ne $_.Bytes
})

if ($missing.Count -gt 0) {
    $arguments = [Collections.Generic.List[string]]::new()
    $arguments.Add('--parallel')
    $arguments.Add('--parallel-immediate')
    $arguments.Add('--parallel-max')
    $arguments.Add($MaxParallel.ToString())

    $first = $true
    foreach ($part in $missing) {
        if (-not $first) {
            $arguments.Add('--next')
        }
        $first = $false
        $arguments.Add('--location')
        $arguments.Add('--fail')
        $arguments.Add('--retry')
        $arguments.Add('5')
        $arguments.Add('--retry-all-errors')
        $arguments.Add('--silent')
        $arguments.Add('--show-error')
        $arguments.Add('--range')
        $arguments.Add(('{0}-{1}' -f $part.Start, $part.End))
        $arguments.Add('--output')
        $arguments.Add($part.Path)
        $arguments.Add($sourceUrl)
    }

    Write-Output ("Downloading {0}/{1} parts with parallelism {2}" -f $missing.Count, $partCount, $MaxParallel)
    & $curlPath @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "parallel curl failed with exit code $LASTEXITCODE"
    }
}

foreach ($part in $parts) {
    if (-not (Test-Path -LiteralPath $part.Path -PathType Leaf)) {
        throw "missing part: $($part.Path)"
    }
    $actual = (Get-Item -LiteralPath $part.Path).Length
    if ($actual -ne $part.Bytes) {
        throw "part length mismatch: $($part.Path), expected=$($part.Bytes), actual=$actual"
    }
}

if (Test-Path -LiteralPath $assembled) {
    $assembledInfo = Get-Item -LiteralPath $assembled
    if ($assembledInfo.Length -ne $expectedBytes) {
        throw "unexpected pre-existing assembled file: $assembled ($($assembledInfo.Length) bytes)"
    }
} else {
    Write-Output ("Assembling {0} parts" -f $partCount)
    $output = [IO.File]::Open($assembled, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        foreach ($part in $parts) {
            $input = [IO.File]::OpenRead($part.Path)
            try {
                $input.CopyTo($output, 8MB)
            } finally {
                $input.Dispose()
            }
        }
    } finally {
        $output.Dispose()
    }
}

$assembledBytes = (Get-Item -LiteralPath $assembled).Length
if ($assembledBytes -ne $expectedBytes) {
    throw "assembled length mismatch: expected=$expectedBytes, actual=$assembledBytes"
}

Write-Output 'Computing final MD5'
$actualMd5 = (Get-FileHash -LiteralPath $assembled -Algorithm MD5).Hash.ToLowerInvariant()
if ($actualMd5 -ne $expectedMd5) {
    throw "assembled MD5 mismatch: expected=$expectedMd5, actual=$actualMd5"
}

if (Test-Path -LiteralPath $destination) {
    $superseded = Join-Path $root ('data.zip.superseded.{0:yyyyMMddTHHmmss}.partial' -f (Get-Date))
    Move-Item -LiteralPath $destination -Destination $superseded
    Write-Output "Preserved prior partial download: $superseded"
}
Move-Item -LiteralPath $assembled -Destination $destination

[pscustomobject]@{
    decision = 'TRACK2P_SOURCE_DOWNLOAD_PASS'
    path = $destination
    bytes = (Get-Item -LiteralPath $destination).Length
    md5 = $actualMd5
    part_count = $partCount
    max_parallel = $MaxParallel
} | ConvertTo-Json -Depth 3
