param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath,

    [Parameter(Mandatory = $true)]
    [string]$SourceReceiptPath,

    [Parameter(Mandatory = $true)]
    [string]$ContractPath,

    [Parameter(Mandatory = $true)]
    [string]$ReceiptPath
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$BucketHttpRoot = 'https://aind-open-data.s3.us-west-2.amazonaws.com'
$ExpectedAssetCount = 22
$ExpectedSubjectCount = 5
$ExpectedManifestSha256 = '80602529D57A673F58E0659344566FD0165080793E31F5CB106B5611D1F1EF38'
$ExpectedSourceAuditorSha256 = 'D07F02C386CF72AFEE9F101CDFD83B598F4AB888C1DFC60CA777F4066E2371B1'
$ExpectedSourceReceiptSha256 = 'CBC317F1C2173F364C7AEDE595BCCF6EC15D4C424E3482DAED52E8BEBDD26D17'
$ExpectedPreregisteredContractSha256 = '23FE688C9DBA568B8594509CD21CC28AE1DE9FCB16BAA60C6FBE53C641A4F22C'
$ExpectedCanonicalManifestRowsSha256 = '2F6247EA984EFF10FD45DB717C98ED256AAF5E73D15F63AEEC577BBD0576AA66'
$MinimumSessionsPerSubject = 2
$MinimumSessionsTotal = 15
$MaximumClockResidualFrames = 1.0

$SelectedArraySpecs = [ordered]@{
    'intervals/epochs/id' = [ordered]@{
        dtype = '<i8'; filter = $null; singleton = $false
    }
    'intervals/epochs/stimulus_name' = [ordered]@{
        dtype = '|O'; filter = 'vlen-utf8'; singleton = $false
    }
    'intervals/epochs/start_frame' = [ordered]@{
        dtype = '<i8'; filter = $null; singleton = $false
    }
    'intervals/epochs/stop_frame' = [ordered]@{
        dtype = '<i8'; filter = $null; singleton = $false
    }
    'intervals/epochs/start_time' = [ordered]@{
        dtype = '<f8'; filter = $null; singleton = $false
    }
    'intervals/epochs/stop_time' = [ordered]@{
        dtype = '<f8'; filter = $null; singleton = $false
    }
    'processing/processed/dff/dff/starting_time' = [ordered]@{
        dtype = '<f8'; filter = $null; singleton = $true
    }
    'general/optophysiology/processed/imaging_rate' = [ordered]@{
        dtype = '<f8'; filter = $null; singleton = $true
    }
}

$ForbiddenChunkPatterns = @(
    '/processing/processed/dff/dff/data/',
    '/stimulus/presentation/Trials/hit/',
    '/stimulus/presentation/Trials/lick_L/',
    '/stimulus/presentation/Trials/reward_time/',
    '/stimulus/presentation/Trials/threshold_crossing_times/',
    '/stimulus/presentation/Trials/zaber_step_times/',
    '/processing/processed/image_segmentation/roi_table/image_mask/'
)

function Get-Sha256HexFromBytes {
    param([byte[]]$Bytes)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($algorithm.ComputeHash($Bytes))).Replace('-', '')
    }
    finally {
        $algorithm.Dispose()
    }
}

function Get-Sha256HexFromString {
    param([string]$Value)
    return Get-Sha256HexFromBytes ([System.Text.Encoding]::UTF8.GetBytes($Value))
}

function Get-FileSha256Hex {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Get-UInt32LittleEndian {
    param(
        [byte[]]$Bytes,
        [int]$Offset
    )
    if ($Offset -lt 0 -or $Offset + 4 -gt $Bytes.Length) {
        throw "uint32 read exceeds buffer at offset $Offset"
    }
    return [uint32](
        [uint32]$Bytes[$Offset] -bor
        ([uint32]$Bytes[$Offset + 1] -shl 8) -bor
        ([uint32]$Bytes[$Offset + 2] -shl 16) -bor
        ([uint32]$Bytes[$Offset + 3] -shl 24)
    )
}

function Expand-Lz4RawBlock {
    param(
        [byte[]]$InputBytes,
        [int]$ExpectedLength
    )
    if ($ExpectedLength -lt 0) {
        throw 'negative LZ4 output length'
    }
    [byte[]]$output = New-Object byte[] $ExpectedLength
    [int]$source = 0
    [int]$target = 0

    while ($source -lt $InputBytes.Length) {
        [int]$token = $InputBytes[$source]
        $source += 1
        [int64]$literalLength = $token -shr 4
        if ($literalLength -eq 15) {
            do {
                if ($source -ge $InputBytes.Length) {
                    throw 'truncated LZ4 literal length'
                }
                [int]$extension = $InputBytes[$source]
                $source += 1
                $literalLength += $extension
            }
            while ($extension -eq 255)
        }
        if ($source + $literalLength -gt $InputBytes.Length -or
            $target + $literalLength -gt $ExpectedLength) {
            throw 'LZ4 literal exceeds input or output bounds'
        }
        if ($literalLength -gt 0) {
            [System.Array]::Copy($InputBytes, $source, $output, $target, [int]$literalLength)
            $source += [int]$literalLength
            $target += [int]$literalLength
        }
        if ($source -eq $InputBytes.Length) {
            break
        }
        if ($source + 2 -gt $InputBytes.Length) {
            throw 'truncated LZ4 match offset'
        }
        [int]$matchOffset = [int]$InputBytes[$source] -bor (
            [int]$InputBytes[$source + 1] -shl 8
        )
        $source += 2
        if ($matchOffset -le 0 -or $matchOffset -gt $target) {
            throw "invalid LZ4 match offset $matchOffset at output $target"
        }
        [int64]$matchLength = $token -band 15
        if ($matchLength -eq 15) {
            do {
                if ($source -ge $InputBytes.Length) {
                    throw 'truncated LZ4 match length'
                }
                [int]$extension = $InputBytes[$source]
                $source += 1
                $matchLength += $extension
            }
            while ($extension -eq 255)
        }
        $matchLength += 4
        if ($target + $matchLength -gt $ExpectedLength) {
            throw 'LZ4 match exceeds output bounds'
        }
        for ([int]$copy = 0; $copy -lt $matchLength; $copy += 1) {
            $output[$target] = $output[$target - $matchOffset]
            $target += 1
        }
    }
    if ($source -ne $InputBytes.Length -or $target -ne $ExpectedLength) {
        throw "LZ4 exact-length failure: source=$source/$($InputBytes.Length), target=$target/$ExpectedLength"
    }
    return ,$output
}

function Expand-BloscLz4Chunk {
    param(
        [byte[]]$ChunkBytes,
        [int]$ExpectedTypeSize
    )
    if (-not [System.BitConverter]::IsLittleEndian) {
        throw 'this decoder requires a little-endian .NET runtime'
    }
    if ($ChunkBytes.Length -lt 16) {
        throw 'Blosc chunk is shorter than its 16-byte header'
    }
    [int]$formatVersion = $ChunkBytes[0]
    [int]$codecVersion = $ChunkBytes[1]
    [int]$flags = $ChunkBytes[2]
    [int]$typeSize = $ChunkBytes[3]
    [int64]$nbytes = Get-UInt32LittleEndian $ChunkBytes 4
    [int64]$blockSize = Get-UInt32LittleEndian $ChunkBytes 8
    [int64]$cbytes = Get-UInt32LittleEndian $ChunkBytes 12
    if ($formatVersion -ne 2 -or $codecVersion -ne 1) {
        throw "unsupported Blosc/LZ4 versions $formatVersion/$codecVersion"
    }
    if (($flags -band 0x08) -ne 0 -or ($flags -band 0x04) -ne 0) {
        throw ('reserved or bitshuffle Blosc flag is set: 0x{0:X2}' -f $flags)
    }
    if (($flags -shr 5) -ne 1) {
        throw ('Blosc compressor enumeration is not LZ4: 0x{0:X2}' -f $flags)
    }
    if (($flags -band 0x01) -eq 0) {
        throw 'Blosc byte-shuffle flag differs from locked metadata'
    }
    if ($typeSize -ne $ExpectedTypeSize -or $typeSize -le 0) {
        throw "Blosc typesize $typeSize differs from expected $ExpectedTypeSize"
    }
    if ($cbytes -ne $ChunkBytes.Length) {
        throw "Blosc cbytes $cbytes differs from object length $($ChunkBytes.Length)"
    }
    if ($nbytes -gt [int]::MaxValue -or $blockSize -gt [int]::MaxValue) {
        throw 'Blosc chunk exceeds managed decoder bounds'
    }
    [byte[]]$output = New-Object byte[] ([int]$nbytes)
    $isMemcpy = (($flags -band 0x02) -ne 0)
    if ($isMemcpy) {
        if ($cbytes -ne 16 + $nbytes) {
            throw 'Blosc memcpy payload length is not header plus nbytes'
        }
        if ($nbytes -gt 0) {
            [System.Array]::Copy($ChunkBytes, 16, $output, 0, [int]$nbytes)
        }
        return ,$output
    }
    if ($nbytes -le 0 -or $blockSize -le 0) {
        throw 'compressed Blosc chunk has nonpositive nbytes or blocksize'
    }
    [int]$blockCount = [int][System.Math]::Ceiling($nbytes / [double]$blockSize)
    [int]$offsetTableEnd = 16 + 4 * $blockCount
    if ($offsetTableEnd -gt $ChunkBytes.Length) {
        throw 'Blosc block-offset table exceeds chunk'
    }
    [int[]]$blockStarts = New-Object int[] $blockCount
    for ([int]$block = 0; $block -lt $blockCount; $block += 1) {
        [int64]$start = Get-UInt32LittleEndian $ChunkBytes (16 + 4 * $block)
        if ($start -lt $offsetTableEnd -or $start -ge $cbytes) {
            throw "invalid Blosc block start $start"
        }
        if ($block -gt 0 -and $start -le $blockStarts[$block - 1]) {
            throw 'Blosc block starts are not strictly increasing'
        }
        $blockStarts[$block] = [int]$start
    }
    $doNotSplit = (($flags -band 0x10) -ne 0)
    [int]$outputOffset = 0
    for ([int]$block = 0; $block -lt $blockCount; $block += 1) {
        [int]$blockStart = $blockStarts[$block]
        [int]$blockEnd = if ($block + 1 -lt $blockCount) {
            $blockStarts[$block + 1]
        }
        else {
            [int]$cbytes
        }
        [int]$blockOutputLength = [int][System.Math]::Min(
            $blockSize,
            $nbytes - [int64]$outputOffset
        )
        $isLastBlock = ($block -eq $blockCount - 1)
        $isLeftoverBlock = (
            $isLastBlock -and
            ($nbytes % $blockSize) -ne 0
        )
        $splitEligible = (
            -not $doNotSplit -and
            -not $isLeftoverBlock -and
            $typeSize -le 16 -and
            [int]($blockOutputLength / $typeSize) -ge 128
        )
        [int]$splitCount = if ($splitEligible) { $typeSize } else { 1 }
        if ($splitCount -le 0 -or $blockOutputLength % $splitCount -ne 0) {
            throw 'Blosc split count does not divide block output length'
        }
        [int]$splitOutputLength = [int]($blockOutputLength / $splitCount)
        [byte[]]$shuffledBlock = New-Object byte[] $blockOutputLength
        [int]$cursor = $blockStart
        [int]$shuffledOffset = 0
        for ([int]$split = 0; $split -lt $splitCount; $split += 1) {
            if ($cursor + 4 -gt $blockEnd) {
                throw 'truncated Blosc split length'
            }
            [int64]$compressedLength = Get-UInt32LittleEndian $ChunkBytes $cursor
            $cursor += 4
            if ($compressedLength -le 0 -or
                $compressedLength -gt $splitOutputLength -or
                $cursor + $compressedLength -gt $blockEnd) {
                throw 'invalid Blosc split compressed length'
            }
            [byte[]]$splitBytes = New-Object byte[] ([int]$compressedLength)
            [System.Array]::Copy($ChunkBytes, $cursor, $splitBytes, 0, [int]$compressedLength)
            $cursor += [int]$compressedLength
            [byte[]]$expandedSplit = if ($compressedLength -eq $splitOutputLength) {
                $splitBytes
            }
            else {
                Expand-Lz4RawBlock $splitBytes $splitOutputLength
            }
            [System.Array]::Copy(
                $expandedSplit,
                0,
                $shuffledBlock,
                $shuffledOffset,
                $splitOutputLength
            )
            $shuffledOffset += $splitOutputLength
        }
        if ($cursor -ne $blockEnd -or $shuffledOffset -ne $blockOutputLength) {
            throw 'Blosc block has trailing bytes or incomplete output'
        }
        if ($typeSize -eq 1) {
            [System.Array]::Copy(
                $shuffledBlock,
                0,
                $output,
                $outputOffset,
                $blockOutputLength
            )
        }
        else {
            if ($blockOutputLength % $typeSize -ne 0) {
                throw 'byte unshuffle received partial atomic element'
            }
            [int]$elementCount = [int]($blockOutputLength / $typeSize)
            for ([int]$element = 0; $element -lt $elementCount; $element += 1) {
                for ([int]$byteIndex = 0; $byteIndex -lt $typeSize; $byteIndex += 1) {
                    $output[$outputOffset + $element * $typeSize + $byteIndex] = (
                        $shuffledBlock[$byteIndex * $elementCount + $element]
                    )
                }
            }
        }
        $outputOffset += $blockOutputLength
    }
    if ($outputOffset -ne $nbytes) {
        throw "Blosc output length $outputOffset differs from nbytes $nbytes"
    }
    return ,$output
}

function Decode-VLenUtf8 {
    param(
        [byte[]]$Bytes,
        [int]$ExpectedCount
    )
    if ($Bytes.Length -lt 4) {
        throw 'vlen-utf8 payload has no item count'
    }
    [int64]$count = Get-UInt32LittleEndian $Bytes 0
    if ($count -ne $ExpectedCount) {
        throw "vlen-utf8 count $count differs from shape $ExpectedCount"
    }
    $strictUtf8 = New-Object System.Text.UTF8Encoding($false, $true)
    [object[]]$values = New-Object object[] $ExpectedCount
    [int]$cursor = 4
    for ([int]$index = 0; $index -lt $ExpectedCount; $index += 1) {
        if ($cursor + 4 -gt $Bytes.Length) {
            throw 'truncated vlen-utf8 item length'
        }
        [int64]$length = Get-UInt32LittleEndian $Bytes $cursor
        $cursor += 4
        if ($length -gt [int]::MaxValue -or $cursor + $length -gt $Bytes.Length) {
            throw 'vlen-utf8 item exceeds payload bounds'
        }
        $values[$index] = $strictUtf8.GetString($Bytes, $cursor, [int]$length)
        $cursor += [int]$length
    }
    if ($cursor -ne $Bytes.Length) {
        throw 'vlen-utf8 payload has trailing bytes'
    }
    return ,$values
}

function Decode-NumericArray {
    param(
        [byte[]]$Bytes,
        [string]$Dtype,
        [int]$ExpectedCount
    )
    [int]$itemSize = switch ($Dtype) {
        '<i8' { 8; break }
        '<f8' { 8; break }
        '<f4' { 4; break }
        default { throw "unsupported numeric dtype $Dtype" }
    }
    if ($Bytes.Length -ne $ExpectedCount * $itemSize) {
        throw "numeric payload length $($Bytes.Length) differs from shape*dtype"
    }
    [object[]]$values = New-Object object[] $ExpectedCount
    for ([int]$index = 0; $index -lt $ExpectedCount; $index += 1) {
        [int]$offset = $index * $itemSize
        $values[$index] = switch ($Dtype) {
            '<i8' { [System.BitConverter]::ToInt64($Bytes, $offset); break }
            '<f8' { [System.BitConverter]::ToDouble($Bytes, $offset); break }
            '<f4' { [double][System.BitConverter]::ToSingle($Bytes, $offset); break }
        }
    }
    return ,$values
}

function Invoke-GetWithRetry {
    param([string]$Url)
    for ([int]$attempt = 1; $attempt -le 3; $attempt += 1) {
        try {
            return Invoke-WebRequest -UseBasicParsing -Uri $Url -Headers @{
                'Accept-Encoding' = 'identity'
            }
        }
        catch {
            if ($attempt -eq 3) {
                throw
            }
            Start-Sleep -Seconds $attempt
        }
    }
}

function Assert-IdentityHttpObject {
    param(
        [object]$Response,
        [byte[]]$Bytes,
        [string]$ObjectKey
    )
    $contentEncoding = [string]$Response.Headers['Content-Encoding']
    if (-not [string]::IsNullOrWhiteSpace($contentEncoding) -and
        $contentEncoding -cne 'identity') {
        throw "HTTP content encoding is not identity for $ObjectKey"
    }
    $contentLengthText = [string]$Response.Headers['Content-Length']
    [int64]$contentLength = -1
    if ([string]::IsNullOrWhiteSpace($contentLengthText) -or
        -not [int64]::TryParse($contentLengthText, [ref]$contentLength) -or
        $contentLength -ne $Bytes.Length) {
        throw "HTTP Content-Length differs from raw bytes for $ObjectKey"
    }
    if ([int64]$Response.RawContentLength -ne $Bytes.Length) {
        throw "Invoke-WebRequest raw length differs from bytes for $ObjectKey"
    }
}

function Get-VersionLockedRemoteObject {
    param(
        [string]$Url,
        [string]$ObjectKey,
        [string]$Kind
    )
    $discoveryResponse = Invoke-GetWithRetry $Url
    [byte[]]$discoveryBytes = [byte[]]$discoveryResponse.Content
    Assert-IdentityHttpObject $discoveryResponse $discoveryBytes $ObjectKey
    $versionId = [string]$discoveryResponse.Headers['x-amz-version-id']
    if ([string]::IsNullOrWhiteSpace($versionId)) {
        throw "S3 VersionId is absent for $ObjectKey"
    }
    $versionUrl = $Url + '?versionId=' + [System.Uri]::EscapeDataString($versionId)
    $lockedResponse = Invoke-GetWithRetry $versionUrl
    [byte[]]$lockedBytes = [byte[]]$lockedResponse.Content
    Assert-IdentityHttpObject $lockedResponse $lockedBytes $ObjectKey
    $lockedVersionId = [string]$lockedResponse.Headers['x-amz-version-id']
    $discoveryEtag = ([string]$discoveryResponse.Headers['ETag']).Trim('"')
    $lockedEtag = ([string]$lockedResponse.Headers['ETag']).Trim('"')
    $discoverySha = Get-Sha256HexFromBytes $discoveryBytes
    $lockedSha = Get-Sha256HexFromBytes $lockedBytes
    if ($lockedVersionId -cne $versionId -or
        $lockedEtag -cne $discoveryEtag -or
        $lockedBytes.Length -ne $discoveryBytes.Length -or
        $lockedSha -cne $discoverySha) {
        throw "bare and explicit-version GET differ for $ObjectKey"
    }
    return [pscustomobject]@{
        bytes = $lockedBytes
        record = [ordered]@{
            kind = $Kind
            key = $ObjectKey
            version_id = $lockedVersionId
            byte_length = $lockedBytes.Length
            etag = $lockedEtag
            last_modified = [string]$lockedResponse.Headers['Last-Modified']
            content_sha256 = $lockedSha
        }
    }
}

function Get-ZarrMetadataValue {
    param(
        [object]$Metadata,
        [string]$Key
    )
    $property = $Metadata.PSObject.Properties[$Key]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function Assert-SelectedZarrArrayMetadata {
    param(
        [object]$ArrayMetadata,
        [System.Collections.IDictionary]$Spec,
        [string]$Path
    )
    if ($null -eq $ArrayMetadata) {
        throw "missing consolidated array metadata for $Path"
    }
    if ([int]$ArrayMetadata.zarr_format -ne 2 -or [string]$ArrayMetadata.order -cne 'C') {
        throw "unexpected Zarr format or order for $Path"
    }
    if ($null -ne $ArrayMetadata.dimension_separator -and
        [string]$ArrayMetadata.dimension_separator -cne '.') {
        throw "unexpected dimension separator for $Path"
    }
    if ([string]$ArrayMetadata.dtype -cne [string]$Spec.dtype) {
        throw "dtype drift for $Path"
    }
    $compressor = $ArrayMetadata.compressor
    if ($null -eq $compressor -or
        [string]$compressor.id -cne 'blosc' -or
        [string]$compressor.cname -cne 'lz4' -or
        [int]$compressor.shuffle -ne 1 -or
        [int]$compressor.clevel -ne 5 -or
        [int]$compressor.blocksize -ne 0) {
        throw "compressor drift for $Path"
    }
    $shape = @($ArrayMetadata.shape)
    $chunks = @($ArrayMetadata.chunks)
    if ($shape.Count -ne 1 -or $chunks.Count -ne 1 -or
        [int64]$shape[0] -le 0 -or [int64]$chunks[0] -ne [int64]$shape[0]) {
        throw "selected preflight array is not one positive full 1D chunk: $Path"
    }
    if ([bool]$Spec.singleton -and [int64]$shape[0] -ne 1) {
        throw "singleton array shape drift for $Path"
    }
    $filters = @($ArrayMetadata.filters)
    if ($null -eq $Spec.filter) {
        if ($null -ne $ArrayMetadata.filters -and $filters.Count -ne 0) {
            throw "unexpected filter for $Path"
        }
    }
    else {
        if ($filters.Count -ne 1 -or [string]$filters[0].id -cne [string]$Spec.filter) {
            throw "object filter drift for $Path"
        }
    }
    if ([string]$Spec.dtype -ceq '|O') {
        if ([int64]$ArrayMetadata.fill_value -ne 0) {
            throw "object fill drift for $Path"
        }
    }
    elseif ([double]$ArrayMetadata.fill_value -ne 0.0) {
        throw "numeric fill drift for $Path"
    }
    return [int]$shape[0]
}

function Test-FiniteDouble {
    param([double]$Value)
    return -not (
        [double]::IsNaN($Value) -or
        [double]::IsInfinity($Value)
    )
}

$resolvedManifest = (Resolve-Path -LiteralPath $ManifestPath).Path
$resolvedSourceReceipt = (Resolve-Path -LiteralPath $SourceReceiptPath).Path
$resolvedContract = (Resolve-Path -LiteralPath $ContractPath).Path
$sourceAuditorPath = Join-Path $PSScriptRoot 'audit_aind_bci_v2_source_schema.ps1'
$resolvedSourceAuditor = (Resolve-Path -LiteralPath $sourceAuditorPath).Path

if ((Get-FileSha256Hex $resolvedManifest) -cne $ExpectedManifestSha256) {
    throw 'source manifest hash differs from preregistration'
}
if ((Get-FileSha256Hex $resolvedSourceAuditor) -cne $ExpectedSourceAuditorSha256) {
    throw 'source auditor hash differs from preregistration'
}
if ((Get-FileSha256Hex $resolvedSourceReceipt) -cne $ExpectedSourceReceiptSha256) {
    throw 'source receipt hash differs from preregistration'
}
if ((Get-FileSha256Hex $resolvedContract) -cne $ExpectedPreregisteredContractSha256) {
    throw 'selected-input contract hash differs from preregistration'
}

$sourceReceiptText = Get-Content -LiteralPath $resolvedSourceReceipt -Raw -Encoding UTF8
$sourceReceipt = ConvertFrom-Json -InputObject $sourceReceiptText
if ([string]$sourceReceipt.decision -cne
    'AIND_BCI_E1_SOURCE_SCHEMA_AUDIT_PASS_WITH_PROVIDER_METADATA_INVALID' -or
    [bool]$sourceReceipt.endpoint_opened -or
    [bool]$sourceReceipt.biological_hypothesis_tested -or
    [string]$sourceReceipt.canonical_manifest_rows_sha256 -cne
        $ExpectedCanonicalManifestRowsSha256) {
    throw 'source/schema receipt does not satisfy the selected-input prerequisite'
}

$sourceReceiptAssetById = @{}
foreach ($sourceAsset in @($sourceReceipt.assets)) {
    $sourceReceiptAssetById[[string]$sourceAsset.asset_id] = $sourceAsset
}

$rows = @(
    Import-Csv -LiteralPath $resolvedManifest -Delimiter ([char]9) -Encoding UTF8
)
$subjectCount = @($rows.subject_id | Sort-Object -Unique).Count
if ($rows.Count -ne $ExpectedAssetCount -or $subjectCount -ne $ExpectedSubjectCount) {
    throw 'manifest cohort shape differs from preregistration'
}

$canonicalManifestRows = @(
    $rows | ForEach-Object {
        @(
            $_.asset_id,
            $_.subject_id,
            $_.asset_name,
            $_.metadata_bytes,
            $_.metadata_etag,
            $_.nwb_zmetadata_bytes,
            $_.nwb_zmetadata_etag
        ) -join '|'
    }
)
$lineFeed = [string][char]10
$canonicalManifestRowsText = ($canonicalManifestRows -join $lineFeed) + $lineFeed
$canonicalManifestRowsHash = Get-Sha256HexFromString $canonicalManifestRowsText
if ($canonicalManifestRowsHash -cne $ExpectedCanonicalManifestRowsSha256) {
    throw 'canonical manifest row hash differs from preregistration'
}

$allObjectLocks = @()
$requestedChunkKeys = @()
$assetResults = @()

foreach ($row in $rows) {
    $assetId = [string]$row.asset_id
    $subjectId = [string]$row.subject_id
    $assetName = [string]$row.asset_name
    $stem = $assetName -replace '_processed_.*$', ''
    $behaviorPrefix = $assetName + '/' + $stem + '_behavior_nwb/'
    $zmetadataKey = $behaviorPrefix + '.zmetadata'
    $zmetadataUrl = $BucketHttpRoot + '/' + $zmetadataKey

    $zmetadataObject = Get-VersionLockedRemoteObject -Url $zmetadataUrl -ObjectKey $zmetadataKey -Kind 'consolidated_zmetadata'
    if ($zmetadataObject.record.byte_length -ne [int64]$row.nwb_zmetadata_bytes -or
        [string]$zmetadataObject.record.etag -cne [string]$row.nwb_zmetadata_etag) {
        throw "manifest zmetadata lock differs for $assetId"
    }
    $sourceAsset = $sourceReceiptAssetById[$assetId]
    if ($null -eq $sourceAsset -or
        [string]$zmetadataObject.record.content_sha256 -cne
            [string]$sourceAsset.zmetadata_content_sha256_observed) {
        throw "source receipt zmetadata content differs for $assetId"
    }
    $zmetadataRecord = [ordered]@{ asset_id = $assetId }
    foreach ($entry in $zmetadataObject.record.GetEnumerator()) {
        $zmetadataRecord[$entry.Key] = $entry.Value
    }
    $allObjectLocks += $zmetadataRecord

    $zmetadataText = [System.Text.Encoding]::UTF8.GetString(
        [byte[]]$zmetadataObject.bytes
    )
    $zmetadataJson = ConvertFrom-Json -InputObject $zmetadataText
    $metadata = $zmetadataJson.metadata
    $dffDataArray = Get-ZarrMetadataValue $metadata 'processing/processed/dff/dff/data/.zarray'
    if ($null -eq $dffDataArray -or
        @($dffDataArray.shape).Count -ne 2 -or
        [int64]$dffDataArray.shape[0] -le 0) {
        throw "dff data shape metadata is absent for $assetId"
    }
    [int64]$dffFrameCount = $dffDataArray.shape[0]

    $startingTimeAttributes = Get-ZarrMetadataValue $metadata 'processing/processed/dff/dff/starting_time/.zattrs'
    if ($null -eq $startingTimeAttributes -or
        -not (Test-FiniteDouble ([double]$startingTimeAttributes.rate)) -or
        [double]$startingTimeAttributes.rate -le 0.0) {
        throw "declared dff rate is invalid for $assetId"
    }
    [double]$declaredRate = $startingTimeAttributes.rate

    $decoded = @{}
    foreach ($specEntry in $SelectedArraySpecs.GetEnumerator()) {
        $arrayPath = [string]$specEntry.Key
        $spec = $specEntry.Value
        $arrayMetadata = Get-ZarrMetadataValue $metadata ($arrayPath + '/.zarray')
        [int]$elementCount = Assert-SelectedZarrArrayMetadata -ArrayMetadata $arrayMetadata -Spec $spec -Path $arrayPath

        $chunkKey = $behaviorPrefix + $arrayPath + '/0'
        foreach ($forbiddenPattern in $ForbiddenChunkPatterns) {
            if (('/' + $chunkKey + '/') -like ('*' + $forbiddenPattern + '*')) {
                throw "forbidden chunk request attempted: $chunkKey"
            }
        }
        $requestedChunkKeys += $chunkKey
        $chunkUrl = $BucketHttpRoot + '/' + $chunkKey
        $chunkObject = Get-VersionLockedRemoteObject -Url $chunkUrl -ObjectKey $chunkKey -Kind 'selected_input_chunk'

        [int]$typeSize = switch ([string]$spec.dtype) {
            '<i8' { 8; break }
            '<f8' { 8; break }
            '<f4' { 4; break }
            '|O' { 1; break }
            default { throw "unsupported selected dtype $($spec.dtype)" }
        }
        [byte[]]$uncompressed = Expand-BloscLz4Chunk -ChunkBytes ([byte[]]$chunkObject.bytes) -ExpectedTypeSize $typeSize
        [object[]]$values = if ([string]$spec.dtype -ceq '|O') {
            Decode-VLenUtf8 $uncompressed $elementCount
        }
        else {
            Decode-NumericArray $uncompressed ([string]$spec.dtype) $elementCount
        }
        $decoded[$arrayPath] = [pscustomobject]@{
            values = $values
            count = $elementCount
            dtype = [string]$spec.dtype
        }

        $chunkRecord = [ordered]@{ asset_id = $assetId }
        foreach ($entry in $chunkObject.record.GetEnumerator()) {
            $chunkRecord[$entry.Key] = $entry.Value
        }
        $chunkRecord.array_path = $arrayPath
        $chunkRecord.dtype = [string]$spec.dtype
        $chunkRecord.shape = @($arrayMetadata.shape)
        $chunkRecord.blosc_format_version = [int]$chunkObject.bytes[0]
        $chunkRecord.blosc_codec_version = [int]$chunkObject.bytes[1]
        $chunkRecord.blosc_header_flags = ('0x{0:X2}' -f [int]$chunkObject.bytes[2])
        $chunkRecord.blosc_typesize = [int]$chunkObject.bytes[3]
        $chunkRecord.decoded_payload_sha256 = Get-Sha256HexFromBytes $uncompressed
        $allObjectLocks += $chunkRecord
    }

    [object[]]$epochIds = $decoded['intervals/epochs/id'].values
    [object[]]$epochLabels = $decoded['intervals/epochs/stimulus_name'].values
    [object[]]$startFrames = $decoded['intervals/epochs/start_frame'].values
    [object[]]$stopFrames = $decoded['intervals/epochs/stop_frame'].values
    [object[]]$startTimes = $decoded['intervals/epochs/start_time'].values
    [object[]]$stopTimes = $decoded['intervals/epochs/stop_time'].values
    [double]$startingTime = $decoded[
        'processing/processed/dff/dff/starting_time'
    ].values[0]
    [double]$imagingRate = $decoded[
        'general/optophysiology/processed/imaging_rate'
    ].values[0]
    [int]$epochCount = $epochIds.Count

    $failureReasons = @()
    $lengthsMatch = (
        $epochLabels.Count -eq $epochCount -and
        $startFrames.Count -eq $epochCount -and
        $stopFrames.Count -eq $epochCount -and
        $startTimes.Count -eq $epochCount -and
        $stopTimes.Count -eq $epochCount
    )
    if (-not $lengthsMatch) {
        $failureReasons += 'EPOCH_COLUMN_LENGTH_MISMATCH'
    }
    $idsUnique = @($epochIds | Sort-Object -Unique).Count -eq $epochCount
    if (-not $idsUnique) {
        $failureReasons += 'EPOCH_ID_NOT_UNIQUE'
    }

    $preCount = @($epochLabels | Where-Object { [string]$_ -ceq 'photostim' }).Count
    $bciCount = @($epochLabels | Where-Object { [string]$_ -ceq 'BCI' }).Count
    $postCount = @(
        $epochLabels | Where-Object { [string]$_ -ceq 'photostim_post' }
    ).Count
    $epochLabelsPass = ($preCount -eq 1 -and $bciCount -ge 1 -and $postCount -eq 1)
    if ($preCount -ne 1) {
        $failureReasons += 'PRE_PHOTOSTIM_EPOCH_COUNT_NOT_ONE'
    }
    if ($bciCount -lt 1) {
        $failureReasons += 'BCI_EPOCH_ABSENT'
    }
    if ($postCount -ne 1) {
        $failureReasons += 'POST_PHOTOSTIM_EPOCH_COUNT_NOT_ONE'
    }

    $rateFinitePositive = (
        (Test-FiniteDouble $declaredRate) -and $declaredRate -gt 0.0 -and
        (Test-FiniteDouble $imagingRate) -and $imagingRate -gt 0.0 -and
        (Test-FiniteDouble $startingTime)
    )
    $rateAgreementTolerance = 1.0e-12 * [System.Math]::Max(1.0, $declaredRate)
    $rateValuesAgree = (
        $rateFinitePositive -and
        [System.Math]::Abs($declaredRate - $imagingRate) -le $rateAgreementTolerance
    )
    if (-not $rateFinitePositive) {
        $failureReasons += 'DFF_CLOCK_SCALAR_NOT_FINITE_POSITIVE'
    }
    if (-not $rateValuesAgree) {
        $failureReasons += 'DFF_RATE_FIELDS_DISAGREE'
    }

    $epochRows = @()
    [double]$maximumResidualSeconds = 0.0
    [bool]$rowClockPass = $true
    for ([int]$index = 0; $index -lt $epochCount; $index += 1) {
        [int64]$startFrame = $startFrames[$index]
        [int64]$stopFrame = $stopFrames[$index]
        [double]$startTime = $startTimes[$index]
        [double]$stopTime = $stopTimes[$index]
        $rowFinite = (
            (Test-FiniteDouble $startTime) -and
            (Test-FiniteDouble $stopTime)
        )
        $frameBounds = (
            $startFrame -ge 0 -and
            $stopFrame -gt $startFrame -and
            $stopFrame -lt $dffFrameCount
        )
        $timeOrder = ($rowFinite -and $stopTime -gt $startTime)
        $startResidual = $null
        $stopResidual = $null
        $residualPass = $false
        if ($rateFinitePositive -and $rowFinite) {
            [double]$startResidual = [System.Math]::Abs(
                $startTime - ($startingTime + $startFrame / $declaredRate)
            )
            [double]$stopResidual = [System.Math]::Abs(
                $stopTime - ($startingTime + $stopFrame / $declaredRate)
            )
            $maximumResidualSeconds = [System.Math]::Max(
                $maximumResidualSeconds,
                [System.Math]::Max($startResidual, $stopResidual)
            )
            $residualPass = (
                $startResidual * $declaredRate -le $MaximumClockResidualFrames -and
                $stopResidual * $declaredRate -le $MaximumClockResidualFrames
            )
        }
        $rowPass = (
            $rowFinite -and
            $frameBounds -and
            $timeOrder -and
            $residualPass
        )
        $rowClockPass = $rowClockPass -and $rowPass
        $epochRows += [ordered]@{
            id = [int64]$epochIds[$index]
            stimulus_name = [string]$epochLabels[$index]
            start_frame = $startFrame
            stop_frame = $stopFrame
            start_time = $startTime
            stop_time = $stopTime
            start_clock_residual_seconds = $startResidual
            stop_clock_residual_seconds = $stopResidual
            row_clock_pass = $rowPass
        }
    }

    $chronologicalPass = $true
    if ($epochCount -gt 1) {
        $chronologicalRows = @(
            0..($epochCount - 1) | ForEach-Object {
                [pscustomobject]@{
                    index = [int]$_
                    start_time = [double]$startTimes[$_]
                    id = [int64]$epochIds[$_]
                    start_frame = [int64]$startFrames[$_]
                }
            } | Sort-Object -Property start_time, id
        )
        for ([int]$position = 1; $position -lt $chronologicalRows.Count; $position += 1) {
            $previous = $chronologicalRows[$position - 1]
            $current = $chronologicalRows[$position]
            if ([double]$current.start_time -le [double]$previous.start_time -or
                [int64]$current.start_frame -lt [int64]$previous.start_frame) {
                $chronologicalPass = $false
            }
        }
    }
    if (-not $rowClockPass) {
        $failureReasons += 'EPOCH_FRAME_TIME_RESIDUAL_EXCEEDS_ONE_FRAME'
    }
    if (-not $chronologicalPass) {
        $failureReasons += 'EPOCH_CLOCK_ORDER_REVERSAL'
    }

    $clockPass = (
        $lengthsMatch -and
        $idsUnique -and
        $rateFinitePositive -and
        $rateValuesAgree -and
        $rowClockPass -and
        $chronologicalPass
    )
    $assetPass = ($epochLabelsPass -and $clockPass)
    $oneFrameSeconds = if ($declaredRate -gt 0.0) {
        1.0 / $declaredRate
    }
    else {
        $null
    }
    $assetResults += [ordered]@{
        asset_id = $assetId
        subject_id = $subjectId
        asset_name = $assetName
        dff_frame_count = $dffFrameCount
        dff_starting_time_seconds = $startingTime
        dff_declared_rate_hz = $declaredRate
        imaging_plane_rate_hz = $imagingRate
        rate_fields_agree = $rateValuesAgree
        one_frame_seconds = $oneFrameSeconds
        maximum_epoch_clock_residual_seconds = $maximumResidualSeconds
        maximum_epoch_clock_residual_frames = (
            $maximumResidualSeconds * $declaredRate
        )
        pre_epoch_count = $preCount
        bci_epoch_count = $bciCount
        post_epoch_count = $postCount
        epoch_labels_pass = $epochLabelsPass
        clock_pass = $clockPass
        selected_input_preflight_pass = $assetPass
        failure_reasons = @(
            $failureReasons | ForEach-Object { [string]$_ }
        )
        epochs = @($epochRows)
    }
}

$expectedChunkCount = $rows.Count * $SelectedArraySpecs.Count
if ($requestedChunkKeys.Count -ne $expectedChunkCount -or
    @($requestedChunkKeys | Sort-Object -Unique).Count -ne $expectedChunkCount) {
    throw 'selected chunk request count or uniqueness differs from preregistration'
}
foreach ($key in $requestedChunkKeys) {
    foreach ($forbiddenPattern in $ForbiddenChunkPatterns) {
        if (('/' + $key + '/') -like ('*' + $forbiddenPattern + '*')) {
            throw "forbidden chunk appeared in request log: $key"
        }
    }
}

$passingAssets = @(
    $assetResults | Where-Object {
        [bool]$_.selected_input_preflight_pass
    }
)
$passingSubjects = @($passingAssets.subject_id | Sort-Object -Unique)
$sessionsPerSubject = [ordered]@{}
foreach ($subjectId in @($rows.subject_id | Sort-Object -Unique)) {
    $subjectSessions = @(
        $passingAssets | Where-Object {
            [string]$_.subject_id -ceq [string]$subjectId
        }
    )
    $sessionsPerSubject[[string]$subjectId] = $subjectSessions.Count
}
$allSubjectsRetained = ($passingSubjects.Count -eq $ExpectedSubjectCount)
$minimumSessionsPerSubjectPass = $true
foreach ($entry in $sessionsPerSubject.GetEnumerator()) {
    if ([int]$entry.Value -lt $MinimumSessionsPerSubject) {
        $minimumSessionsPerSubjectPass = $false
    }
}
$minimumTotalSessionsPass = ($passingAssets.Count -ge $MinimumSessionsTotal)
$cohortGatePass = (
    $allSubjectsRetained -and
    $minimumSessionsPerSubjectPass -and
    $minimumTotalSessionsPass
)

$canonicalObjectRows = @(
    $allObjectLocks | ForEach-Object {
        @(
            $_.asset_id,
            $_.kind,
            $_.key,
            $_.version_id,
            $_.byte_length,
            $_.etag,
            $_.last_modified,
            $_.content_sha256,
            $_.decoded_payload_sha256
        ) -join '|'
    }
)
$canonicalObjectManifestText = ($canonicalObjectRows -join $lineFeed) + $lineFeed
$canonicalObjectManifestSha256 = Get-Sha256HexFromString $canonicalObjectManifestText

$decision = if ($cohortGatePass) {
    'AIND_BCI_E1_SELECTED_INPUT_PREFLIGHT_PASS'
}
else {
    'AIND_BCI_E1_SELECTED_INPUT_PREFLIGHT_FAIL'
}
$e1Status = if ($cohortGatePass) {
    'TARGET_ROI_JOIN_AUDIT_PENDING'
}
else {
    'E1_BLOCKED_INPUT'
}
$downstreamStatus = if ($cohortGatePass) {
    'PENDING'
}
else {
    'NOT_RUN_PREREQUISITE_FAILED'
}

$missingVersionLocks = @(
    $allObjectLocks | Where-Object {
        [string]$_.kind -ceq 'selected_input_chunk' -and
        [string]::IsNullOrWhiteSpace([string]$_.version_id)
    }
)
$missingContentLocks = @(
    $allObjectLocks | Where-Object {
        [string]$_.kind -ceq 'selected_input_chunk' -and
        [string]::IsNullOrWhiteSpace([string]$_.content_sha256)
    }
)
$observedBloscFlags = @(
    $allObjectLocks |
        Where-Object { [string]$_.kind -ceq 'selected_input_chunk' } |
        ForEach-Object { [string]$_['blosc_header_flags'] } |
        Select-Object -Unique |
        Sort-Object
)

$receipt = [ordered]@{
    schema_version = 'ce_npf_aind_bci_e1_selected_input_preflight_v1'
    decision = $decision
    e1_status = $e1Status
    claim_ceiling = 'input apparatus only; no dff response, behavior endpoint, metric, or biological hypothesis opened'
    endpoint_opened = $false
    biological_endpoint_opened = $false
    selected_input_value_chunks_decoded = $true
    biological_hypothesis_tested = $false
    biological_evidence_level = 'BIO_EVIDENCE_L0'
    biological_mediation_status = 'BIOLOGICAL_MEDIATION_UNTESTED'
    stage10_identified = $false
    stage10_status = 'STAGE10_INTEGRATED_MODEL_NOT_IDENTIFIABLE'
    dff_response_chunk_requested = $false
    behavior_endpoint_chunk_requested = $false
    roi_image_mask_chunk_requested = $false
    forbidden_chunk_request_count = 0
    gate_a_epoch_clock_preflight = $decision
    downstream_target_roi_join_audit = $downstreamStatus
    gate_c_endpoint_byte_lock = $downstreamStatus
    source_script_sha256 = Get-FileSha256Hex $PSCommandPath
    preregistered_contract_sha256 = Get-FileSha256Hex $resolvedContract
    source_manifest_sha256 = Get-FileSha256Hex $resolvedManifest
    source_auditor_sha256 = Get-FileSha256Hex $resolvedSourceAuditor
    source_receipt_sha256 = Get-FileSha256Hex $resolvedSourceReceipt
    runtime = [ordered]@{
        powershell_version = [string]$PSVersionTable.PSVersion
        dotnet_runtime_version = [string][System.Environment]::Version
        os_version = [string][System.Environment]::OSVersion.VersionString
        is_64_bit_process = [System.Environment]::Is64BitProcess
    }
    canonical_manifest_rows_sha256 = $canonicalManifestRowsHash
    asset_count = $rows.Count
    subject_count = $subjectCount
    selected_array_paths = @($SelectedArraySpecs.Keys)
    selected_chunk_count = $requestedChunkKeys.Count
    expected_selected_chunk_count = $expectedChunkCount
    consolidated_zmetadata_object_count = $rows.Count
    selected_chunk_version_id_locked_all = ($missingVersionLocks.Count -eq 0)
    selected_chunk_content_sha256_locked_all = ($missingContentLocks.Count -eq 0)
    collection_snapshot_atomic = $false
    latest_version_rechecked_after_collection = $false
    observed_selected_chunk_blosc_flags = $observedBloscFlags
    canonical_selected_object_manifest_sha256 = $canonicalObjectManifestSha256
    canonical_selected_object_manifest_order = (
        'manifest asset order; consolidated zmetadata first; selected array specification order'
    )
    asset_preflight_pass_count = $passingAssets.Count
    asset_preflight_fail_count = $rows.Count - $passingAssets.Count
    retained_subject_count = $passingSubjects.Count
    sessions_per_subject_after_preflight = $sessionsPerSubject
    all_subjects_retained = $allSubjectsRetained
    minimum_sessions_per_subject_required = $MinimumSessionsPerSubject
    minimum_sessions_per_subject_pass = $minimumSessionsPerSubjectPass
    minimum_sessions_total_required = $MinimumSessionsTotal
    minimum_sessions_total_pass = $minimumTotalSessionsPass
    cohort_gate_pass = $cohortGatePass
    maximum_clock_residual_frames_allowed = $MaximumClockResidualFrames
    forbidden_chunk_patterns = $ForbiddenChunkPatterns
    requested_chunk_keys = @($requestedChunkKeys)
    object_locks = @($allObjectLocks)
    assets = @($assetResults)
    limits = @(
        'the preflight opens only epoch labels/frame/time and two non-endpoint clock scalars',
        'dff data, PhotostimTrials values, Trials values, ROI values, image masks, and biological outputs remain unopened',
        'a source-declared rate is never re-estimated or replaced by provider metadata marked Invalid',
        'preflight failure is an apparatus/input failure, not a negative biological hypothesis result',
        '58 Hz calcium timing does not identify millisecond axonal conduction velocity',
        'per-object VersionIds define a non-atomic S3 collection snapshot; latest versions were not rechecked after collection',
        'only the Blosc flags listed in observed_selected_chunk_blosc_flags were exercised by this A preflight'
    )
}

$resolvedReceiptPath = [System.IO.Path]::GetFullPath($ReceiptPath)
$receiptDirectory = [System.IO.Path]::GetDirectoryName($resolvedReceiptPath)
[void][System.IO.Directory]::CreateDirectory($receiptDirectory)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$json = $receipt | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText(
    $resolvedReceiptPath,
    $json + $lineFeed,
    $utf8NoBom
)

Write-Output ('decision=' + $decision)
Write-Output ('e1_status=' + $e1Status)
Write-Output (
    'assets_pass=' + $passingAssets.Count +
    ' assets_fail=' + ($rows.Count - $passingAssets.Count)
)
$sessionSummary = (
    $sessionsPerSubject.GetEnumerator() | ForEach-Object {
        [string]$_.Key + ':' + [string]$_.Value
    }
) -join ','
Write-Output ('sessions_per_subject=' + $sessionSummary)
Write-Output ('selected_object_manifest_sha256=' + $canonicalObjectManifestSha256)
Write-Output ('receipt=' + $resolvedReceiptPath)

if (-not $cohortGatePass) {
    exit 1
}
