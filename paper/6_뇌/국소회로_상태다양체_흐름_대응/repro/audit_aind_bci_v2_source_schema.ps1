param(
    [Parameter(Mandatory = $false)]
    [string]$ManifestPath = (Join-Path $PSScriptRoot 'aind_bci_v2_source_lock.tsv'),

    [Parameter(Mandatory = $true)]
    [string]$ReceiptPath
)

$ErrorActionPreference = 'Stop'
$BucketHttpRoot = 'https://aind-open-data.s3.us-west-2.amazonaws.com'
$ExpectedAssetCount = 22
$ExpectedSubjectCount = 5
$ExpectedCanonicalManifestRowsHash = '2F6247EA984EFF10FD45DB717C98ED256AAF5E73D15F63AEEC577BBD0576AA66'
$ExpectedInventoryObjectCount = 88186
$ExpectedInventoryTotalBytes = 160509574918
$ExpectedInventorySummaryHash = 'CDDA8CBB9DF5442299E73D0BF20ED23359EA8965781E275D9D3457E9D639CD27'
$ExpectedProviderInvalidCount = 22

$RequiredMetadataKeys = @(
    'intervals/epochs/.zattrs',
    'intervals/epochs/id/.zarray',
    'intervals/epochs/stimulus_name/.zarray',
    'intervals/epochs/start_frame/.zarray',
    'intervals/epochs/stop_frame/.zarray',
    'intervals/epochs/start_time/.zarray',
    'intervals/epochs/stop_time/.zarray',
    'stimulus/presentation/PhotostimTrials/id/.zarray',
    'stimulus/presentation/PhotostimTrials/.zattrs',
    'stimulus/presentation/PhotostimTrials/start_time/.zarray',
    'stimulus/presentation/PhotostimTrials/stop_time/.zarray',
    'stimulus/presentation/PhotostimTrials/start_frame/.zarray',
    'stimulus/presentation/PhotostimTrials/stop_frame/.zarray',
    'stimulus/presentation/PhotostimTrials/group_index/.zarray',
    'stimulus/presentation/PhotostimTrials/closest_roi/.zarray',
    'stimulus/presentation/PhotostimTrials/laser_x/.zarray',
    'stimulus/presentation/PhotostimTrials/laser_y/.zarray',
    'stimulus/presentation/PhotostimTrials/power/.zarray',
    'stimulus/presentation/PhotostimTrials/duration/.zarray',
    'stimulus/presentation/PhotostimTrials/stimulus_name/.zarray',
    'stimulus/presentation/PhotostimTrials/stimulus_function/.zarray',
    'stimulus/presentation/PhotostimTrials/tiff_file/.zarray',
    'stimulus/presentation/Trials/.zattrs',
    'stimulus/presentation/Trials/id/.zarray',
    'stimulus/presentation/Trials/start_time/.zarray',
    'stimulus/presentation/Trials/stop_time/.zarray',
    'stimulus/presentation/Trials/start_frame/.zarray',
    'stimulus/presentation/Trials/stop_frame/.zarray',
    'stimulus/presentation/Trials/reward_time/.zarray',
    'stimulus/presentation/Trials/threshold_crossing_times/.zarray',
    'stimulus/presentation/Trials/conditioned_neuron_x/.zarray',
    'stimulus/presentation/Trials/conditioned_neuron_y/.zarray',
    'stimulus/presentation/Trials/closest_roi/.zarray',
    'stimulus/presentation/Trials/go_cue/.zarray',
    'stimulus/presentation/Trials/hit/.zarray',
    'stimulus/presentation/Trials/lick_L/.zarray',
    'stimulus/presentation/Trials/zaber_step_times/.zarray',
    'stimulus/presentation/Trials/tiff_file/.zarray',
    'processing/processed/dff/dff/.zattrs',
    'processing/processed/dff/dff/data/.zarray',
    'processing/processed/dff/dff/data/.zattrs',
    'processing/processed/dff/dff/starting_time/.zarray',
    'processing/processed/dff/dff/starting_time/.zattrs',
    'processing/processed/dff/dff/rois/.zarray',
    'processing/processed/dff/dff/rois/.zattrs',
    'processing/processed/image_segmentation/roi_table/.zattrs',
    'processing/processed/image_segmentation/roi_table/id/.zarray',
    'processing/processed/image_segmentation/roi_table/is_soma/.zarray',
    'processing/processed/image_segmentation/roi_table/soma_probability/.zarray',
    'processing/processed/image_segmentation/roi_table/image_mask/.zarray',
    'general/optophysiology/processed/imaging_rate/.zarray',
    'general/optophysiology/processed/imaging_rate/.zattrs',
    'session_start_time/.zarray',
    'session_start_time/.zattrs',
    'timestamps_reference_time/.zarray',
    'timestamps_reference_time/.zattrs'
)

$RequiredTableColumns = [ordered]@{
    'intervals/epochs/.zattrs' = @(
        'stimulus_name', 'start_frame', 'stop_frame', 'start_time', 'stop_time'
    )
    'stimulus/presentation/PhotostimTrials/.zattrs' = @(
        'start_time', 'stop_time', 'start_frame', 'stop_frame', 'tiff_file',
        'stimulus_name', 'laser_x', 'laser_y', 'power', 'duration',
        'stimulus_function', 'group_index', 'closest_roi'
    )
    'stimulus/presentation/Trials/.zattrs' = @(
        'start_time', 'stop_time', 'go_cue', 'hit', 'lick_L', 'reward_time',
        'threshold_crossing_times', 'zaber_step_times', 'tiff_file',
        'start_frame', 'stop_frame', 'conditioned_neuron_x',
        'conditioned_neuron_y', 'closest_roi'
    )
    'processing/processed/image_segmentation/roi_table/.zattrs' = @(
        'is_soma', 'soma_probability', 'is_dendrite',
        'dendrite_probability', 'image_mask'
    )
}

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

function Get-RemoteObject {
    param([string]$Url)
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url
    return [pscustomobject]@{
        bytes = [byte[]]$response.Content
        length = [int64]$response.RawContentLength
        etag = ([string]$response.Headers['ETag']).Trim('"')
        content_sha256 = Get-Sha256HexFromBytes ([byte[]]$response.Content)
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

function Get-MissingTableColumns {
    param(
        [object]$Metadata,
        [string]$Key,
        [string[]]$RequiredColumns
    )
    $attributes = Get-ZarrMetadataValue $Metadata $Key
    if ($null -eq $attributes -or $null -eq $attributes.colnames) {
        return @($RequiredColumns)
    }
    $actual = @($attributes.colnames | ForEach-Object { [string]$_ })
    return @($RequiredColumns | Where-Object { $_ -notin $actual })
}

function Get-BehaviorInventory {
    param([string]$Prefix)

    $incremental = [System.Security.Cryptography.IncrementalHash]::CreateHash(
        [System.Security.Cryptography.HashAlgorithmName]::SHA256
    )
    $continuationToken = $null
    [int64]$objectCount = 0
    [int64]$totalBytes = 0
    $firstKey = $null
    $lastKey = $null
    $previousKey = $null
    $lexicographicOrderStrict = $true

    try {
        do {
            $url = $BucketHttpRoot + '/?list-type=2&prefix=' + [System.Uri]::EscapeDataString($Prefix)
            if ($null -ne $continuationToken -and $continuationToken.Length -gt 0) {
                $url += '&continuation-token=' + [System.Uri]::EscapeDataString($continuationToken)
            }

            [xml]$listing = (Invoke-WebRequest -UseBasicParsing -Uri $url).Content
            $objects = @($listing.ListBucketResult.Contents)
            foreach ($object in $objects) {
                $key = [string]$object.Key
                $size = [int64]$object.Size
                $etag = ([string]$object.ETag).Trim('"')
                $lastModified = [string]$object.LastModified
                if ($null -eq $firstKey) {
                    $firstKey = $key
                }
                if ($null -ne $previousKey -and
                    [string]::CompareOrdinal($previousKey, $key) -ge 0) {
                    $lexicographicOrderStrict = $false
                }
                $previousKey = $key
                $lastKey = $key
                $line = $key + '|' + $size + '|' + $etag + '|' + $lastModified + "`n"
                $incremental.AppendData([System.Text.Encoding]::UTF8.GetBytes($line))
                $objectCount += 1
                $totalBytes += $size
            }

            $isTruncated = [System.Convert]::ToBoolean([string]$listing.ListBucketResult.IsTruncated)
            $continuationToken = [string]$listing.ListBucketResult.NextContinuationToken
        }
        while ($isTruncated)

        return [ordered]@{
            prefix = $Prefix
            object_count = $objectCount
            total_bytes = $totalBytes
            canonical_key_size_etag_last_modified_sha256 = (
                [System.BitConverter]::ToString($incremental.GetHashAndReset())
            ).Replace('-', '')
            first_key = $firstKey
            last_key = $lastKey
            lexicographic_order_strict = $lexicographicOrderStrict
        }
    }
    finally {
        $incremental.Dispose()
    }
}

$resolvedManifest = (Resolve-Path -LiteralPath $ManifestPath).Path
$rows = @(Import-Csv -LiteralPath $resolvedManifest -Delimiter "`t" -Encoding UTF8)
$subjectCount = @($rows.subject_id | Sort-Object -Unique).Count

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
$canonicalManifestRowsHash = Get-Sha256HexFromString (($canonicalManifestRows -join "`n") + "`n")

$assetResults = @()
[int64]$totalInventoryObjects = 0
[int64]$totalInventoryBytes = 0
$metadataStatusCounts = [ordered]@{}
$allMetadataLocksMatch = $true
$allZmetadataLocksMatch = $true
$allRequiredKeysPresent = $true
$allDffRoiAxesMatch = $true
$allRatesPositive = $true
$allManifestLocationsMatch = $true
$allProviderIdentitiesMatch = $true
$allTableColumnsMatch = $true
$allInventoryOrdersStrict = $true
$assetsWithLocomotionKeys = 0

foreach ($row in $rows) {
    $stem = $row.asset_name -replace '_processed_.*$', ''
    $expectedS3Location = 's3://aind-open-data/' + $row.asset_name
    $manifestLocationMatches = ([string]$row.s3_location -ceq $expectedS3Location)
    $metadataKey = $row.asset_name + '/metadata.nd.json'
    $behaviorPrefix = $row.asset_name + '/' + $stem + '_behavior_nwb/'
    $zmetadataKey = $behaviorPrefix + '.zmetadata'

    $metadataObject = Get-RemoteObject ($BucketHttpRoot + '/' + $metadataKey)
    $zmetadataObject = Get-RemoteObject ($BucketHttpRoot + '/' + $zmetadataKey)
    $metadataJson = ConvertFrom-Json -InputObject (
        [System.Text.Encoding]::UTF8.GetString($metadataObject.bytes)
    )
    $zmetadataJson = ConvertFrom-Json -InputObject (
        [System.Text.Encoding]::UTF8.GetString($zmetadataObject.bytes)
    )
    $zarrMetadata = $zmetadataJson.metadata
    $zarrKeys = @($zarrMetadata.PSObject.Properties.Name)
    $missingKeys = @($RequiredMetadataKeys | Where-Object { $_ -notin $zarrKeys })
    $missingTableColumns = [ordered]@{}
    foreach ($entry in $RequiredTableColumns.GetEnumerator()) {
        $missingTableColumns[$entry.Key] = @(
            Get-MissingTableColumns $zarrMetadata $entry.Key $entry.Value
        )
    }
    $tableColumnsMatch = (@(
        $missingTableColumns.Values | ForEach-Object { @($_) } | Where-Object { $_.Count -gt 0 }
    ).Count -eq 0)
    $locomotionKeyCount = @(
        $zarrKeys | Where-Object { $_ -match '(?i)(running|locomotion|speed|wheel)' }
    ).Count

    $dffArray = Get-ZarrMetadataValue $zarrMetadata 'processing/processed/dff/dff/data/.zarray'
    $dffRoisArray = Get-ZarrMetadataValue $zarrMetadata 'processing/processed/dff/dff/rois/.zarray'
    $roiArray = Get-ZarrMetadataValue $zarrMetadata 'processing/processed/image_segmentation/roi_table/id/.zarray'
    $photostimArray = Get-ZarrMetadataValue $zarrMetadata 'stimulus/presentation/PhotostimTrials/id/.zarray'
    $epochArray = Get-ZarrMetadataValue $zarrMetadata 'intervals/epochs/id/.zarray'
    $trialArray = Get-ZarrMetadataValue $zarrMetadata 'stimulus/presentation/Trials/id/.zarray'
    $startingTimeAttributes = Get-ZarrMetadataValue $zarrMetadata 'processing/processed/dff/dff/starting_time/.zattrs'

    $dffRoiAxisMatches = (
        $null -ne $dffArray -and
        $null -ne $dffRoisArray -and
        $null -ne $roiArray -and
        [int64]$dffArray.shape[1] -eq [int64]$dffRoisArray.shape[0] -and
        [int64]$dffRoisArray.shape[0] -eq [int64]$roiArray.shape[0]
    )
    $ratePositive = ($null -ne $startingTimeAttributes -and [double]$startingTimeAttributes.rate -gt 0.0)
    $metadataLockMatches = (
        $metadataObject.length -eq [int64]$row.metadata_bytes -and
        $metadataObject.etag -eq $row.metadata_etag
    )
    $zmetadataLockMatches = (
        $zmetadataObject.length -eq [int64]$row.nwb_zmetadata_bytes -and
        $zmetadataObject.etag -eq $row.nwb_zmetadata_etag
    )

    $metadataStatus = [string]$metadataJson.metadata_status
    $providerIdentityMatches = (
        [string]$metadataJson._id -ceq [string]$row.asset_id -and
        [string]$metadataJson.name -ceq [string]$row.asset_name -and
        [string]$metadataJson.location -ceq $expectedS3Location -and
        [string]$metadataJson.subject.subject_id -ceq [string]$row.subject_id -and
        [string]$metadataJson.data_description.subject_id -ceq [string]$row.subject_id
    )
    if (-not $metadataStatusCounts.Contains($metadataStatus)) {
        $metadataStatusCounts[$metadataStatus] = 0
    }
    $metadataStatusCounts[$metadataStatus] += 1

    $inventory = Get-BehaviorInventory $behaviorPrefix
    $totalInventoryObjects += [int64]$inventory.object_count
    $totalInventoryBytes += [int64]$inventory.total_bytes
    if ($locomotionKeyCount -gt 0) {
        $assetsWithLocomotionKeys += 1
    }

    $allMetadataLocksMatch = $allMetadataLocksMatch -and $metadataLockMatches
    $allZmetadataLocksMatch = $allZmetadataLocksMatch -and $zmetadataLockMatches
    $allRequiredKeysPresent = $allRequiredKeysPresent -and ($missingKeys.Count -eq 0)
    $allDffRoiAxesMatch = $allDffRoiAxesMatch -and $dffRoiAxisMatches
    $allRatesPositive = $allRatesPositive -and $ratePositive
    $allManifestLocationsMatch = $allManifestLocationsMatch -and $manifestLocationMatches
    $allProviderIdentitiesMatch = $allProviderIdentitiesMatch -and $providerIdentityMatches
    $allTableColumnsMatch = $allTableColumnsMatch -and $tableColumnsMatch
    $allInventoryOrdersStrict = (
        $allInventoryOrdersStrict -and [bool]$inventory.lexicographic_order_strict
    )

    [object[]]$fovSignatures = @(
        @(
            foreach ($stream in @($metadataJson.session.data_streams)) {
                foreach ($fov in @($stream.ophys_fovs)) {
                    if ($null -ne $fov) {
                        @(
                            [string]$fov.notes,
                            [string]$fov.targeted_structure,
                            [string]$fov.imaging_depth,
                            [string]$fov.imaging_depth_unit,
                            [string]$fov.frame_rate,
                            [string]$fov.frame_rate_unit
                        ) -join '|'
                    }
                }
            }
        ) | Sort-Object -Unique
    )
    [object[]]$sessionNumbers = @(
        @(
            $metadataJson.session.stimulus_epochs |
                ForEach-Object { $_.session_number } |
                Where-Object { $null -ne $_ -and [string]$_ -ne '' } |
                ForEach-Object { [int64]$_ }
        ) | Sort-Object -Unique
    )
    [object[]]$virusPreparations = @(
        foreach ($subjectProcedure in @($metadataJson.procedures.subject_procedures)) {
            foreach ($procedure in @($subjectProcedure.procedures)) {
                foreach ($material in @($procedure.injection_materials)) {
                    if ($null -ne $material -and [string]$material.material_type -eq 'Virus') {
                        [ordered]@{
                            name = [string]$material.name
                            virus_tars_id = [string]$material.tars_identifiers.virus_tars_id
                            prep_lot_number = [string]$material.tars_identifiers.prep_lot_number
                            prep_date = [string]$material.tars_identifiers.prep_date
                        }
                    }
                }
            }
        }
    )

    $assetResults += [ordered]@{
        asset_id = $row.asset_id
        subject_id = $row.subject_id
        asset_name = $row.asset_name
        manifest_s3_location = [string]$row.s3_location
        manifest_s3_location_matches = $manifestLocationMatches
        metadata_key = $metadataKey
        metadata_status = $metadataStatus
        genotype = [string]$metadataJson.subject.genotype
        provider_identity_matches = $providerIdentityMatches
        metadata_lock_matches = $metadataLockMatches
        metadata_content_sha256_observed = $metadataObject.content_sha256
        zmetadata_key = $zmetadataKey
        zmetadata_lock_matches = $zmetadataLockMatches
        zmetadata_content_sha256_observed = $zmetadataObject.content_sha256
        zmetadata_key_count = $zarrKeys.Count
        missing_required_keys = $missingKeys
        missing_required_table_columns = $missingTableColumns
        required_table_columns_match = $tableColumnsMatch
        dff_frame_count = [int64]$dffArray.shape[0]
        roi_count = [int64]$roiArray.shape[0]
        dff_roi_axis_matches = $dffRoiAxisMatches
        photostim_trial_rows = [int64]$photostimArray.shape[0]
        bci_trial_rows = [int64]$trialArray.shape[0]
        epoch_rows = [int64]$epochArray.shape[0]
        dff_rate_hz = [double]$startingTimeAttributes.rate
        locomotion_key_count = $locomotionKeyCount
        fov_signatures = $fovSignatures
        session_numbers = $sessionNumbers
        virus_preparations = $virusPreparations
        behavior_inventory = $inventory
    }
}

$inventorySummaryRows = @(
    $assetResults | ForEach-Object {
        @(
            $_.asset_id,
            $_.behavior_inventory.prefix,
            $_.behavior_inventory.object_count,
            $_.behavior_inventory.total_bytes,
            $_.behavior_inventory.canonical_key_size_etag_last_modified_sha256
        ) -join '|'
    }
)
$combinedInventoryHash = Get-Sha256HexFromString (($inventorySummaryRows -join "`n") + "`n")

$catalogShapePass = ($rows.Count -eq $ExpectedAssetCount -and $subjectCount -eq $ExpectedSubjectCount)
$canonicalManifestRowsPass = ($canonicalManifestRowsHash -eq $ExpectedCanonicalManifestRowsHash)
$inventorySnapshotPass = (
    $totalInventoryObjects -eq $ExpectedInventoryObjectCount -and
    $totalInventoryBytes -eq $ExpectedInventoryTotalBytes -and
    $combinedInventoryHash -eq $ExpectedInventorySummaryHash
)
$providerInvalidPass = (
    $metadataStatusCounts.Count -eq 1 -and
    $metadataStatusCounts.Contains('Invalid') -and
    [int64]$metadataStatusCounts['Invalid'] -eq $ExpectedProviderInvalidCount
)
$schemaPass = (
    $catalogShapePass -and
    $canonicalManifestRowsPass -and
    $allManifestLocationsMatch -and
    $allProviderIdentitiesMatch -and
    $allMetadataLocksMatch -and
    $allZmetadataLocksMatch -and
    $providerInvalidPass -and
    $allRequiredKeysPresent -and
    $allTableColumnsMatch -and
    $allDffRoiAxesMatch -and
    $allRatesPositive -and
    $allInventoryOrdersStrict -and
    $inventorySnapshotPass
)
$decision = if ($schemaPass) {
    'AIND_BCI_E1_SOURCE_SCHEMA_AUDIT_PASS_WITH_PROVIDER_METADATA_INVALID'
}
else {
    'AIND_BCI_E1_SOURCE_SCHEMA_AUDIT_FAIL'
}

$receipt = [ordered]@{
    schema_version = 'ce_npf_aind_bci_e1_source_schema_audit_v1'
    decision = $decision
    claim_ceiling = 'source and schema apparatus only; no Zarr array endpoint decoded'
    endpoint_opened = $false
    biological_hypothesis_tested = $false
    raw_chunk_content_sha256_locked = $false
    selected_chunk_version_id_locked = $false
    source_script_sha256 = Get-FileSha256Hex $PSCommandPath
    source_manifest_sha256 = Get-FileSha256Hex $resolvedManifest
    canonical_manifest_rows_sha256 = $canonicalManifestRowsHash
    canonical_manifest_rows_match_expected = $canonicalManifestRowsPass
    asset_count = $rows.Count
    subject_count = $subjectCount
    source_catalog_shape_pass = $catalogShapePass
    manifest_s3_locations_match_all = $allManifestLocationsMatch
    provider_identity_matches_all = $allProviderIdentitiesMatch
    metadata_lock_matches_all = $allMetadataLocksMatch
    zmetadata_lock_matches_all = $allZmetadataLocksMatch
    required_zmetadata_keys_present_all = $allRequiredKeysPresent
    required_zmetadata_key_count = $RequiredMetadataKeys.Count
    required_table_columns_match_all = $allTableColumnsMatch
    dff_roi_axes_match_all = $allDffRoiAxesMatch
    dff_rates_positive_all = $allRatesPositive
    provider_metadata_status_counts = $metadataStatusCounts
    provider_invalid_status_matches_expected = $providerInvalidPass
    assets_with_locomotion_keys = $assetsWithLocomotionKeys
    behavior_object_inventory = [ordered]@{
        canonical_asset_summary_sha256 = $combinedInventoryHash
        expected_canonical_asset_summary_sha256 = $ExpectedInventorySummaryHash
        object_count = $totalInventoryObjects
        expected_object_count = $ExpectedInventoryObjectCount
        total_bytes = $totalInventoryBytes
        expected_total_bytes = $ExpectedInventoryTotalBytes
        total_gib = [math]::Round($totalInventoryBytes / 1GB, 6)
        lexicographic_order_strict_all = $allInventoryOrdersStrict
        snapshot_matches_expected = $inventorySnapshotPass
        etag_semantics = 'opaque; not interpreted as MD5 or SHA-256'
    }
    input_content_gate = 'NOT_RUN'
    limits = @(
        'metadata.nd.json is provider-marked Invalid for this cohort and is not repaired or imputed',
        'no running/locomotion/speed/wheel Zarr key is available; zaber_step_times is not locomotion',
        'object inventory fail-closes against the preregistered key, size, opaque ETag, and LastModified digest but is not an atomic S3 snapshot',
        'every subsequently selected object must lock VersionId when available and content SHA-256 before value-level audit',
        'no epoch label, common-target count, ROI value, timestamp monotonicity, response, metric, or behavior endpoint was decoded'
    )
    required_zmetadata_keys = $RequiredMetadataKeys
    assets = $assetResults
}

$resolvedReceipt = [System.IO.Path]::GetFullPath($ReceiptPath)
$receiptDirectory = [System.IO.Path]::GetDirectoryName($resolvedReceipt)
[void][System.IO.Directory]::CreateDirectory($receiptDirectory)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$json = $receipt | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($resolvedReceipt, $json + "`n", $utf8NoBom)

Write-Output ('decision=' + $decision)
Write-Output ('assets=' + $rows.Count + ' subjects=' + $subjectCount)
Write-Output ('objects=' + $totalInventoryObjects + ' bytes=' + $totalInventoryBytes)
Write-Output ('inventory_sha256=' + $combinedInventoryHash)
Write-Output ('receipt=' + $resolvedReceipt)

if (-not $schemaPass) {
    exit 1
}
