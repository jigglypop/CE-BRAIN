param(
    [Parameter(Mandatory = $false)]
    [string]$ManifestPath,

    [Parameter(Mandatory = $true)]
    [string]$ReceiptPath,

    [Parameter(Mandatory = $false)]
    [string]$DataPath,

    [Parameter(Mandatory = $false)]
    [string]$DictionaryPath
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ManifestPath = Join-Path $scriptDirectory 'loewenstein_2015_spine_source_lock.tsv'
}

$Expected = [ordered]@{
    manifest_sha256 = '8209A09886B9322A02308F1DCEFF8D3805462C715135F79E28E1AB1E166B0630'
    data_url = 'https://decision-making-lab.com/data/spines/publication_data.csv'
    data_bytes = 569938
    data_sha256 = '2F6343606F62ABB07B82491A71F0E4A4A898923D2BCF86AA4BE8D596276D0062'
    dictionary_url = 'https://decision-making-lab.com/data/spines/spines.html'
    dictionary_bytes = 4850
    dictionary_sha256 = '995BDB601F6FF71CD5877486DFDD0576DB576C15EFFCC8C52DB560EB523D9657'
    schema_sha256 = '5F695DB3EE5F4818E1E580D447E5D5BF1AC6F5FE64D3D3A16338CF91012BD718'
    rows = 8699
    columns = 13
    cells = 8
    dendrites = 48
    spines = 3688
    sessions = 6
    session_interval_days = 4
    dendrite_session_combinations = 288
    duplicate_keys = 0
    noncontiguous_presence_histories = 0
    first_session_prevalent_spines = 1420
    incident_spines = 2268
    final_session_visible_spines = 1388
    at_risk_intervals = 7311
    visible_survival_intervals = 5011
    visible_disappearance_intervals = 2300
}

$Columns = @(
    'cell_id',
    'dendrite_id',
    'spine_id',
    'session_id',
    'relative_intensity',
    'lambda1',
    'lambda2',
    'spine_dendrite_distance_px',
    'spine_x_px',
    'spine_y_px',
    'dendrite_x_px',
    'dendrite_y_px',
    'z_slice_offset'
)

# This commitment freezes source columns and the upstream author's terminology only.
# Biological endpoint semantics are locked separately in state_semantics and biological_scope.
$CanonicalSchemaLines = @(
    'cell_id:int:composite_postsynaptic_cell_index',
    'dendrite_id:int:cell_local_dendrite_index',
    'spine_id:int:dendrite_local_spine_index',
    'session_id:int:1_to_6',
    'relative_intensity:float:arbitrary_unit_volume_proxy',
    'lambda1:float:brightness_weighted_pca_eigenvalue_1',
    'lambda2:float:brightness_weighted_pca_eigenvalue_2',
    'spine_dendrite_distance_px:float:pixels',
    'spine_x_px:float:session_relative_pixels',
    'spine_y_px:float:session_relative_pixels',
    'dendrite_x_px:float:session_relative_pixels',
    'dendrite_y_px:float:session_relative_pixels',
    'z_slice_offset:float:0.5_micrometer_slice_difference',
    'session_time_days:float:4_times_session_id_minus_1',
    'row_semantics:author_catalogued_visible_spine_at_session'
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

function Get-SourceBytes {
    param(
        [string]$LocalPath,
        [string]$Url
    )

    if (-not [string]::IsNullOrWhiteSpace($LocalPath)) {
        return [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $LocalPath).Path)
    }

    $client = New-Object System.Net.WebClient
    try {
        return $client.DownloadData($Url)
    }
    finally {
        $client.Dispose()
    }
}

function Convert-ToInvariantDouble {
    param([string]$Value)

    [double]$parsed = 0.0
    $ok = [double]::TryParse(
        $Value,
        [System.Globalization.NumberStyles]::Float,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$parsed
    )
    if (-not $ok -or [double]::IsNaN($parsed) -or [double]::IsInfinity($parsed)) {
        throw "NONFINITE_OR_INVALID_FLOAT: $Value"
    }
    return $parsed
}

function Convert-ToPositiveInteger {
    param([string]$Value)

    [int]$parsed = 0
    $ok = [int]::TryParse(
        $Value,
        [System.Globalization.NumberStyles]::Integer,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$parsed
    )
    if (-not $ok -or $parsed -le 0) {
        throw "INVALID_POSITIVE_INTEGER: $Value"
    }
    return $parsed
}

function Get-CountMap {
    param([int[]]$Values)

    $map = [ordered]@{}
    foreach ($value in ($Values | Sort-Object -Unique)) {
        $map[[string]$value] = @($Values | Where-Object { $_ -eq $value }).Count
    }
    return $map
}

$resolvedManifest = (Resolve-Path -LiteralPath $ManifestPath).Path
$manifestBytes = [System.IO.File]::ReadAllBytes($resolvedManifest)
$manifestRows = @(
    Import-Csv -LiteralPath $resolvedManifest -Delimiter "`t" -Encoding UTF8
)

if ($manifestRows.Count -ne 2) {
    throw "SOURCE_LOCK_ROW_COUNT_MISMATCH: $($manifestRows.Count)"
}

$dataLock = @(
    $manifestRows | Where-Object { $_.source_id -eq 'loewenstein_2015_publication_data' }
)
$dictionaryLock = @(
    $manifestRows | Where-Object { $_.source_id -eq 'loewenstein_2015_data_dictionary' }
)
if ($dataLock.Count -ne 1 -or $dictionaryLock.Count -ne 1) {
    throw 'SOURCE_LOCK_ROLE_MISSING_OR_DUPLICATED'
}
$dataLock = $dataLock[0]
$dictionaryLock = $dictionaryLock[0]

$manifestDefinitionPass = (
    (Get-Sha256HexFromBytes $manifestBytes) -ceq $Expected.manifest_sha256 -and
    $dataLock.table_role -ceq 'raw_longitudinal_table' -and
    $dataLock.uri -ceq $Expected.data_url -and
    $dataLock.version_id -ceq 'unversioned_author_host_content_lock_2026-08-31' -and
    [int64]$dataLock.bytes -eq $Expected.data_bytes -and
    $dataLock.sha256.ToUpperInvariant() -ceq $Expected.data_sha256 -and
    $dataLock.etag -ceq '8b252-5cb8b404a82eb' -and
    $dataLock.last_modified_utc -ceq '2021-09-09T07:50:23Z' -and
    $dataLock.retrieved_utc -ceq '2026-08-31T08:31:16Z' -and
    $dataLock.schema_sha256.ToUpperInvariant() -ceq $Expected.schema_sha256 -and
    $dataLock.license_status -ceq 'not_stated' -and
    $dataLock.redistribution_policy -ceq 'metadata_and_hash_only_no_raw_vendoring' -and
    $dictionaryLock.table_role -ceq 'schema_dictionary' -and
    $dictionaryLock.uri -ceq $Expected.dictionary_url -and
    $dictionaryLock.version_id -ceq 'unversioned_author_host_content_lock_2026-08-31' -and
    [int64]$dictionaryLock.bytes -eq $Expected.dictionary_bytes -and
    $dictionaryLock.sha256.ToUpperInvariant() -ceq $Expected.dictionary_sha256 -and
    [string]::IsNullOrWhiteSpace($dictionaryLock.etag) -and
    [string]::IsNullOrWhiteSpace($dictionaryLock.last_modified_utc) -and
    $dictionaryLock.retrieved_utc -ceq '2026-08-31T08:31:16Z' -and
    $dictionaryLock.schema_sha256.ToUpperInvariant() -ceq $Expected.schema_sha256 -and
    $dictionaryLock.license_status -ceq 'not_stated' -and
    $dictionaryLock.redistribution_policy -ceq 'metadata_and_hash_only_no_raw_vendoring'
)

$canonicalSchema = ($CanonicalSchemaLines -join "`n") + "`n"
$schemaHash = Get-Sha256HexFromString $canonicalSchema
$schemaDefinitionPass = ($schemaHash -ceq $Expected.schema_sha256)

$dataBytes = Get-SourceBytes -LocalPath $DataPath -Url $Expected.data_url
$dictionaryBytes = Get-SourceBytes -LocalPath $DictionaryPath -Url $Expected.dictionary_url
$dataHash = Get-Sha256HexFromBytes $dataBytes
$dictionaryHash = Get-Sha256HexFromBytes $dictionaryBytes
$sourceContentPass = (
    $dataBytes.LongLength -eq $Expected.data_bytes -and
    $dataHash -ceq $Expected.data_sha256 -and
    $dictionaryBytes.LongLength -eq $Expected.dictionary_bytes -and
    $dictionaryHash -ceq $Expected.dictionary_sha256
)

if (-not $manifestDefinitionPass -or -not $schemaDefinitionPass -or -not $sourceContentPass) {
    $sourceStop = [ordered]@{
        schema_version = 'ce_npf_loewenstein_spine_preflight_v1'
        decision = 'STOP_SOURCE_LOCK_MISMATCH'
        endpoint_fit_executed = $false
        biological_hypothesis_tested = $false
        claim_ceiling = 'INPUT_ELIGIBILITY_ONLY_BIO_EVIDENCE_L0'
        failure_codes = @('STOP_UNFROZEN_SOURCE')
        manifest_definition_pass = $manifestDefinitionPass
        schema_definition_pass = $schemaDefinitionPass
        source_content_pass = $sourceContentPass
        observed = [ordered]@{
            manifest_sha256 = Get-Sha256HexFromBytes $manifestBytes
            data_bytes = $dataBytes.LongLength
            data_sha256 = $dataHash
            dictionary_bytes = $dictionaryBytes.LongLength
            dictionary_sha256 = $dictionaryHash
            schema_sha256 = $schemaHash
        }
    }
    $receiptDirectory = [System.IO.Path]::GetDirectoryName(
        [System.IO.Path]::GetFullPath($ReceiptPath)
    )
    if (-not [System.IO.Directory]::Exists($receiptDirectory)) {
        [System.IO.Directory]::CreateDirectory($receiptDirectory) | Out-Null
    }
    $stopJson = ($sourceStop | ConvertTo-Json -Depth 8) + "`n"
    [System.IO.File]::WriteAllText(
        [System.IO.Path]::GetFullPath($ReceiptPath),
        $stopJson,
        (New-Object System.Text.UTF8Encoding($false))
    )
    throw 'STOP_UNFROZEN_SOURCE'
}

$dataText = [System.Text.Encoding]::UTF8.GetString($dataBytes)
$nonemptyLines = @(
    ($dataText -split "`r?`n") | Where-Object { $_.Length -gt 0 }
)
$wrongColumnLineCount = @(
    $nonemptyLines | Where-Object { @($_ -split ',', -1).Count -ne $Expected.columns }
).Count
if ($wrongColumnLineCount -ne 0) {
    throw "CSV_COLUMN_COUNT_MISMATCH_LINES: $wrongColumnLineCount"
}

$rawRows = @(ConvertFrom-Csv -InputObject $dataText -Header $Columns)
$parsedRows = New-Object System.Collections.Generic.List[object]
$keySet = New-Object 'System.Collections.Generic.HashSet[string]'
$cellSet = New-Object 'System.Collections.Generic.HashSet[int]'
$dendriteSet = New-Object 'System.Collections.Generic.HashSet[string]'
$dendriteSessionSet = New-Object 'System.Collections.Generic.HashSet[string]'
$spineSessions = @{}
$spineRows = @{}
$duplicateKeyCount = 0
$lambdaOrderViolationCount = 0
$shapeOutsideUnitCount = 0

foreach ($row in $rawRows) {
    $cell = Convert-ToPositiveInteger $row.cell_id
    $dendrite = Convert-ToPositiveInteger $row.dendrite_id
    $spine = Convert-ToPositiveInteger $row.spine_id
    $session = Convert-ToPositiveInteger $row.session_id
    if ($session -gt $Expected.sessions) {
        throw "SESSION_OUT_OF_RANGE: $session"
    }

    $intensity = Convert-ToInvariantDouble $row.relative_intensity
    $lambda1 = Convert-ToInvariantDouble $row.lambda1
    $lambda2 = Convert-ToInvariantDouble $row.lambda2
    $distance = Convert-ToInvariantDouble $row.spine_dendrite_distance_px
    $spineX = Convert-ToInvariantDouble $row.spine_x_px
    $spineY = Convert-ToInvariantDouble $row.spine_y_px
    $dendriteX = Convert-ToInvariantDouble $row.dendrite_x_px
    $dendriteY = Convert-ToInvariantDouble $row.dendrite_y_px
    $zOffset = Convert-ToInvariantDouble $row.z_slice_offset
    if ($intensity -le 0.0 -or $lambda1 -le 0.0 -or $lambda2 -le 0.0 -or $distance -le 0.0) {
        throw 'NONPOSITIVE_MORPHOLOGY_MARK'
    }
    if ($lambda1 -lt $lambda2) {
        $lambdaOrderViolationCount += 1
    }
    $shape = ($lambda1 - $lambda2) / ($lambda1 + $lambda2)
    if ($shape -lt -1.0 -or $shape -gt 1.0) {
        $shapeOutsideUnitCount += 1
    }

    $rowKey = '{0}|{1}|{2}|{3}' -f $cell, $dendrite, $spine, $session
    if (-not $keySet.Add($rowKey)) {
        $duplicateKeyCount += 1
    }
    $spineKey = '{0}|{1}|{2}' -f $cell, $dendrite, $spine
    $dendriteKey = '{0}|{1}' -f $cell, $dendrite
    $dendriteSessionKey = '{0}|{1}|{2}' -f $cell, $dendrite, $session
    [void]$cellSet.Add($cell)
    [void]$dendriteSet.Add($dendriteKey)
    [void]$dendriteSessionSet.Add($dendriteSessionKey)
    if (-not $spineSessions.ContainsKey($spineKey)) {
        $spineSessions[$spineKey] = New-Object System.Collections.Generic.List[int]
        $spineRows[$spineKey] = New-Object System.Collections.Generic.List[object]
    }
    $spineSessions[$spineKey].Add($session)

    $parsed = [pscustomobject]@{
        cell = $cell
        dendrite = $dendrite
        spine = $spine
        session = $session
        intensity = $intensity
        lambda1 = $lambda1
        lambda2 = $lambda2
        shape = $shape
        distance = $distance
        spine_x = $spineX
        spine_y = $spineY
        dendrite_x = $dendriteX
        dendrite_y = $dendriteY
        z_offset = $zOffset
        spine_key = $spineKey
    }
    $parsedRows.Add($parsed)
    $spineRows[$spineKey].Add($parsed)
}

$spineSummary = @{}
$noncontiguousCount = 0
$firstSessions = New-Object System.Collections.Generic.List[int]
$lastSessions = New-Object System.Collections.Generic.List[int]
foreach ($spineKey in ($spineSessions.Keys | Sort-Object)) {
    $sessions = @($spineSessions[$spineKey] | Sort-Object)
    for ($index = 1; $index -lt $sessions.Count; $index += 1) {
        if ($sessions[$index] -ne ($sessions[$index - 1] + 1)) {
            $noncontiguousCount += 1
            break
        }
    }
    $first = [int]$sessions[0]
    $last = [int]$sessions[$sessions.Count - 1]
    $firstSessions.Add($first)
    $lastSessions.Add($last)
    $spineSummary[$spineKey] = [pscustomobject]@{
        first = $first
        last = $last
        present_sessions = $sessions.Count
        pattern = ($sessions -join '')
    }
}

$atRiskRows = @($parsedRows | Where-Object { $_.session -lt $Expected.sessions })
$visibleDisappearanceIntervals = @(
    $atRiskRows | Where-Object {
        $_.session -eq $spineSummary[$_.spine_key].last
    }
).Count
$visibleSurvivalIntervals = $atRiskRows.Count - $visibleDisappearanceIntervals
$incidentSpines = @(
    $spineSummary.Values | Where-Object { $_.first -gt 1 }
).Count
$prevalentSpines = @(
    $spineSummary.Values | Where-Object { $_.first -eq 1 }
).Count
$finalSessionVisibleSpines = @(
    $spineSummary.Values | Where-Object { $_.last -eq $Expected.sessions }
).Count

$comparisonRows = @(
    $atRiskRows | Where-Object {
        $spineSummary[$_.spine_key].first -gt 1
    } | Sort-Object cell, dendrite, spine, session
)
$comparisonCanonicalLines = @(
    foreach ($row in $comparisonRows) {
        $event = [int]($row.session -eq $spineSummary[$row.spine_key].last)
        '{0}|{1}|{2}|{3}|{4}' -f (
            $row.cell,
            $row.dendrite,
            $row.spine,
            $row.session,
            $event
        )
    }
)
$comparisonRowsHash = Get-Sha256HexFromString (
    ($comparisonCanonicalLines -join "`n") + "`n"
)
$comparisonEventCount = @(
    $comparisonRows | Where-Object {
        $_.session -eq $spineSummary[$_.spine_key].last
    }
).Count

$transitionSupport = @(
    foreach ($session in 1..5) {
        $sessionRows = @($parsedRows | Where-Object { $_.session -eq $session })
        $disappeared = @(
            $sessionRows | Where-Object {
                $spineSummary[$_.spine_key].last -eq $session
            }
        ).Count
        $survived = $sessionRows.Count - $disappeared
        $newAtNextSession = @(
            $spineSummary.Values | Where-Object { $_.first -eq ($session + 1) }
        ).Count
        [ordered]@{
            from_session = $session
            to_session = $session + 1
            interval_days = $Expected.session_interval_days
            visible_at_risk = $sessionRows.Count
            visible_next_session = $survived
            not_visible_next_session = $disappeared
            first_catalogued_next_session = $newAtNextSession
            conditional_visible_survival_fraction = $survived / $sessionRows.Count
        }
    }
)

$presencePatterns = [ordered]@{}
foreach ($group in @(
    $spineSummary.Values | Group-Object pattern | Sort-Object Name
)) {
    $presencePatterns[$group.Name] = $group.Count
}
$trackObservationCountDistribution = Get-CountMap (
    [int[]]@($spineSummary.Values.present_sessions)
)

$intensityValues = [double[]]@($parsedRows.intensity)
$shapeValues = [double[]]@($parsedRows.shape)
$distanceValues = [double[]]@($parsedRows.distance)
$zOffsetValues = [double[]]@($parsedRows.z_offset)
$markRanges = [ordered]@{
    relative_intensity = [ordered]@{
        minimum = ($intensityValues | Measure-Object -Minimum).Minimum
        maximum = ($intensityValues | Measure-Object -Maximum).Maximum
    }
    shape = [ordered]@{
        minimum = ($shapeValues | Measure-Object -Minimum).Minimum
        maximum = ($shapeValues | Measure-Object -Maximum).Maximum
    }
    spine_dendrite_distance_px = [ordered]@{
        minimum = ($distanceValues | Measure-Object -Minimum).Minimum
        maximum = ($distanceValues | Measure-Object -Maximum).Maximum
    }
    z_slice_offset = [ordered]@{
        minimum = ($zOffsetValues | Measure-Object -Minimum).Minimum
        maximum = ($zOffsetValues | Measure-Object -Maximum).Maximum
    }
}

$cellSupport = @(
    foreach ($cell in ($cellSet | Sort-Object)) {
        $cellRows = @($parsedRows | Where-Object { $_.cell -eq $cell })
        $cellSpineKeys = @($cellRows.spine_key | Sort-Object -Unique)
        $cellComparison = @($comparisonRows | Where-Object { $_.cell -eq $cell })
        $cellComparisonEvents = @(
            $cellComparison | Where-Object {
                $_.session -eq $spineSummary[$_.spine_key].last
            }
        ).Count
        [ordered]@{
            cell_id = $cell
            rows = $cellRows.Count
            dendrites = @(
                $cellRows | ForEach-Object { '{0}|{1}' -f $_.cell, $_.dendrite } |
                    Sort-Object -Unique
            ).Count
            spines = $cellSpineKeys.Count
            common_comparison_intervals = $cellComparison.Count
            common_comparison_events = $cellComparisonEvents
        }
    }
)

$schemaChecks = [ordered]@{
    row_count_pass = ($parsedRows.Count -eq $Expected.rows)
    column_count_pass = ($wrongColumnLineCount -eq 0)
    cell_count_pass = ($cellSet.Count -eq $Expected.cells)
    dendrite_count_pass = ($dendriteSet.Count -eq $Expected.dendrites)
    spine_count_pass = ($spineSummary.Count -eq $Expected.spines)
    session_domain_pass = (
        @($parsedRows.session | Sort-Object -Unique).Count -eq $Expected.sessions -and
        (@($parsedRows.session | Sort-Object -Unique) -join ',') -ceq '1,2,3,4,5,6'
    )
    dendrite_session_nonempty_pass = (
        $dendriteSessionSet.Count -eq $Expected.dendrite_session_combinations
    )
    duplicate_key_pass = ($duplicateKeyCount -eq $Expected.duplicate_keys)
    contiguous_presence_pass = (
        $noncontiguousCount -eq $Expected.noncontiguous_presence_histories
    )
    morphology_numeric_support_pass = (
        $lambdaOrderViolationCount -eq 0 -and $shapeOutsideUnitCount -eq 0
    )
    prevalent_count_pass = ($prevalentSpines -eq $Expected.first_session_prevalent_spines)
    incident_count_pass = ($incidentSpines -eq $Expected.incident_spines)
    final_session_count_pass = (
        $finalSessionVisibleSpines -eq $Expected.final_session_visible_spines
    )
    at_risk_interval_count_pass = ($atRiskRows.Count -eq $Expected.at_risk_intervals)
    survival_interval_count_pass = (
        $visibleSurvivalIntervals -eq $Expected.visible_survival_intervals
    )
    disappearance_interval_count_pass = (
        $visibleDisappearanceIntervals -eq $Expected.visible_disappearance_intervals
    )
    all_cells_have_common_intervals_and_events = (
        @($cellSupport | Where-Object {
            $_.common_comparison_intervals -le 0 -or $_.common_comparison_events -le 0
        }).Count -eq 0
    )
}
$schemaPass = @(
    $schemaChecks.GetEnumerator() | Where-Object { -not [bool]$_.Value }
).Count -eq 0
if (-not $schemaPass) {
    throw 'STOP_SCHEMA_OR_EXPECTED_COUNT_MISMATCH'
}

$failureCodes = @(
    'COMMON_SUPPORT_NOT_ESTABLISHED',
    'NI_FILOPODIA_SEPARATION',
    'NI_ANIMAL_HELDOUT_FRAILTY',
    'NI_BIPARENT_CONTACT',
    'NI_BIRTH_DENOMINATOR',
    'NI_CONDUCTING_STATE',
    'NI_DETECTION_TURNOVER_CONFOUNDING',
    'NI_EXACT_ACQUISITION_TIMESTAMPS',
    'NI_LEFT_TRUNCATED_AGE',
    'NI_MARK_SCALE_ERROR',
    'NI_SPATIAL_REGISTRATION_EXPOSURE',
    'NI_VISIT_COVERAGE_QC'
)
$ascertainmentCodes = @(
    'ASCERTAINMENT_ADULT_MALE_GFP_M_AUDITORY_L5_APICAL_TUFT',
    'ASCERTAINMENT_LATERAL_ORIENTATION_SELECTION',
    'FILOPODIA_NOT_SEPARATED_FROM_SPINES'
)
$governanceStopCodes = @(
    'DATASET_LICENSE_UNSPECIFIED',
    'LONG_TERM_AVAILABILITY_NOT_LOCKED'
)

$sourceScriptPath = $MyInvocation.MyCommand.Path
$sourceScriptHash = if ([string]::IsNullOrWhiteSpace($sourceScriptPath)) {
    $null
}
else {
    Get-Sha256HexFromBytes ([System.IO.File]::ReadAllBytes($sourceScriptPath))
}

$receipt = [ordered]@{
    schema_version = 'ce_npf_loewenstein_spine_preflight_v1'
    decision = 'PARTIAL_MODEL_ELIGIBILITY'
    endpoint_fit_executed = $false
    biological_hypothesis_tested = $false
    claim_ceiling = 'INPUT_ELIGIBILITY_ONLY_BIO_EVIDENCE_L0'
    source_lock_pass = $true
    content_identity_pass = $true
    source_lock_semantics = 'live_unversioned_host_content_identity_only'
    long_term_availability_locked = $false
    schema_preflight_pass = $true
    source_script_sha256 = $sourceScriptHash
    source_manifest_sha256 = Get-Sha256HexFromBytes $manifestBytes
    source_locks = @(
        [ordered]@{
            source_id = $dataLock.source_id
            uri = $dataLock.uri
            upstream_versioned = $false
            bytes = $dataBytes.LongLength
            sha256 = $dataHash
            etag = $dataLock.etag
            last_modified_utc = $dataLock.last_modified_utc
            raw_vendored = $false
        },
        [ordered]@{
            source_id = $dictionaryLock.source_id
            uri = $dictionaryLock.uri
            upstream_versioned = $false
            bytes = $dictionaryBytes.LongLength
            sha256 = $dictionaryHash
            raw_vendored = $false
        }
    )
    source_rights = [ordered]@{
        license_status = 'not_stated'
        redistribution_policy = 'metadata_and_hash_only_no_raw_vendoring'
        analysis_download_only = $true
        governance_release_status = 'GOVERNANCE_RELEASE_STOP_DATASET_LICENSE_UNSPECIFIED'
    }
    canonical_source_column_schema_sha256 = $schemaHash
    canonical_source_schema_uses_upstream_spine_terminology = $true
    state_semantics = [ordered]@{
        row_present = 'author_catalogued_lateral_dendritic_protrusion_at_session_filopodia_not_separated'
        row_absent = 'not_catalogued_at_session_under_unverified_branch_coverage'
        latent_synaptic_contact_truth_observed = $false
        conducting_state_observed = $false
        presynaptic_parent_observed = $false
        postsynaptic_cell_index_observed = $true
    }
    biological_scope = [ordered]@{
        paper_doi = '10.1523/JNEUROSCI.2917-14.2015'
        preparation = 'approximately_six_month_adult_male_GFP_M_mice'
        paper_reported_mouse_count = 6
        region = 'auditory_cortex'
        cell_class = 'layer_5_pyramidal_neuron'
        compartment = 'apical_tuft'
        filopodia_separated_from_spines = $false
        lateral_orientation_selected = $true
        axial_resolution_orientation_confound = $true
        paper_describes_cross_session_tracking_procedure = $true
        quantitative_detection_or_reidentification_error_calibration_available = $false
        allowed_endpoint = 'next_session_recataloguing_of_author_catalogued_lateral_protrusion_with_filopodia_not_separated'
    }
    clock = [ordered]@{
        session_ids = @(1, 2, 3, 4, 5, 6)
        protocol_interval_days = $Expected.session_interval_days
        derived_session_times_days = @(0, 4, 8, 12, 16, 20)
        exact_acquisition_timestamps_available = $false
        allowed_time_claim = 'scheduled_four_day_interval_scale_only'
    }
    entity_counts = [ordered]@{
        animals = $null
        cells = $cellSet.Count
        dendrites = $dendriteSet.Count
        spines = $spineSummary.Count
        biparent_contacts = $null
    }
    observation_counts = [ordered]@{
        rows = $parsedRows.Count
        dendrite_session_nonempty_combinations = $dendriteSessionSet.Count
        duplicate_entity_session_keys = $duplicateKeyCount
        noncontiguous_presence_histories = $noncontiguousCount
        rows_per_session = Get-CountMap ([int[]]$parsedRows.session)
        presence_patterns = $presencePatterns
        track_observation_count_distribution = $trackObservationCountDistribution
    }
    interval_support = [ordered]@{
        observed_visible_at_risk_intervals = $atRiskRows.Count
        observed_visible_survival_intervals = $visibleSurvivalIntervals
        observed_visible_disappearance_intervals = $visibleDisappearanceIntervals
        interval_width_days = $Expected.session_interval_days
        exact_event_times_observed = $false
        midpoint_or_one_jump_imputation_authorized = $false
        transitions_by_interval = $transitionSupport
    }
    left_truncation = [ordered]@{
        first_session_prevalent_spines = $prevalentSpines
        prevalent_true_age_known = $false
        initial_age_law_available = $false
        first_catalogued_after_session_1_spines = $incidentSpines
        first_catalog_session_observed = $true
        biological_birth_time_interval_censored = $false
        biological_birth_time_bounds_available = $false
        allowed_age_covariate = 'elapsed_since_first_catalog_not_true_biological_age'
    }
    right_censoring = [ordered]@{
        final_session_visible_spines = $finalSessionVisibleSpines
        administrative_horizon_session = $Expected.sessions
        administrative_horizon_day = 20
        row_level_censor_reason_available = $false
        last_positive_without_later_visit_counted_as_death = $false
    }
    coverage_and_detection = [ordered]@{
        all_composite_dendrites_have_at_least_one_row_each_session = $true
        explicit_branch_coverage_mask_available = $false
        covered_branch_length_time_available = $false
        finite_absent_candidate_risk_set_available = $false
        detection_calibration_available = $false
        registration_qc_per_row_available = $false
        tracking_procedure_described_in_paper = $true
        quantitative_detection_or_reidentification_calibration_available = $false
        xy_origin_stable_across_sessions = $false
    }
    mark_support = @(
        [ordered]@{
            name = 'relative_intensity'
            role = 'volume_proxy'
            unit = 'arbitrary_unit'
            observed_rows = $parsedRows.Count
            pre_next_visit_rows = $atRiskRows.Count
            measurement_error_calibration = $false
        },
        [ordered]@{
            name = 'shape'
            formula = '(lambda1-lambda2)/(lambda1+lambda2)'
            unit = 'dimensionless'
            observed_rows = $parsedRows.Count
            pre_next_visit_rows = $atRiskRows.Count
            measurement_error_calibration = $false
        },
        [ordered]@{
            name = 'spine_dendrite_distance'
            role = 'length_proxy'
            unit = 'pixel'
            observed_rows = $parsedRows.Count
            pre_next_visit_rows = $atRiskRows.Count
            measurement_error_calibration = $false
        }
    )
    mark_ranges = $markRanges
    biological_model_eligibility = [ordered]@{
        M0_constant_contact_ctmc = [ordered]@{
            eligible = $false
            failure_codes = @(
                'NI_DETECTION_TURNOVER_CONFOUNDING',
                'NI_BIRTH_DENOMINATOR'
            )
        }
        M1_age_only_semi_markov = [ordered]@{
            eligible = $false
            failure_codes = @(
                'NI_DETECTION_TURNOVER_CONFOUNDING',
                'NI_LEFT_TRUNCATED_AGE'
            )
        }
        M2_age_mark_pdmp = [ordered]@{
            eligible = $false
            failure_codes = @(
                'NI_DETECTION_TURNOVER_CONFOUNDING',
                'NI_LEFT_TRUNCATED_AGE',
                'NI_MARK_SCALE_ERROR'
            )
        }
        three_way_biological_likelihood_comparison = [ordered]@{
            eligible = $false
            failure_codes = @('INVALID_THREE_MODEL_COMPARISON_FOR_LATENT_BIOLOGICAL_STATES')
        }
    }
    catalogued_lateral_protrusion_predictive_eligibility = [ordered]@{
        V0_constant_interval_recataloguing = [ordered]@{
            input_eligible = $true
            allowed_claim = 'cell_heldout_prediction_of_next_session_recataloguing_within_this_sample_and_pipeline'
        }
        V1_elapsed_since_first_catalog = [ordered]@{
            input_eligible = $true
            allowed_claim = 'baseline_after_first_catalog_prediction_using_catalog_elapsed_time_not_biological_birth_or_true_age'
        }
        V2_current_morphology_plus_orientation_nuisance = [ordered]@{
            input_eligible = $true
            allowed_claim = 'pre_next_visit_morphology_association_with_z_offset_as_orientation_detection_nuisance_not_pdmp_mark_dynamics'
        }
        common_comparison = [ordered]@{
            input_eligible = $true
            unit = 'cell_not_animal'
            split_contract_locked = $false
            fit_executed = $false
            baseline_after_first_catalog_intervals = $comparisonRows.Count
            next_session_not_recatalogued_events = $comparisonEventCount
            comparison_rowset_sha256 = $comparisonRowsHash
            common_state_semantics = 'author_catalogued_lateral_protrusion_filopodia_not_separated'
            common_horizon_days = 4
        }
    }
    cell_support = $cellSupport
    schema_checks = $schemaChecks
    failure_codes = $failureCodes
    ascertainment_codes = $ascertainmentCodes
    governance_stop_codes = $governanceStopCodes
    forbidden_claims = @(
        'absolute_spine_birth_intensity',
        'animal_heldout_generalization_or_animal_frailty',
        'exact_event_time_hazard',
        'true_biological_spine_age_for_prevalent_or_first_catalogued_protrusions',
        'conducting_synapse_state_or_transition',
        'presynaptic_parent_identified_contact_process',
        'source_calibrated_mark_flow_or_jump_kernel',
        'mature_excitatory_spine_or_filopodia_separated_endpoint',
        'generalization_beyond_adult_male_GFP_M_auditory_L5_apical_tuft_lateral_protrusions',
        'neural_riemannian_metric_or_functional_folding',
        'behavioral_or_causal_mediation'
    )
    next_gate = [ordered]@{
        predictive_path = 'lock_cell_heldout_common_rowset_contract_before_any_fit'
        biological_upgrade_path = 'obtain_cell_animal_crosswalk_branch_exposure_visit_detection_censor_qc_initial_age_law_and_filopodia_separation'
        conducting_upgrade_path = 'obtain_biparent_identity_and_repeated_same_contact_functional_assay'
        governance_release_path = 'obtain_explicit_dataset_reuse_license_and_archive_a_versioned_snapshot_before_redistribution_or_release'
    }
    runtime = [ordered]@{
        powershell_version = $PSVersionTable.PSVersion.ToString()
        dotnet_runtime_version = [System.Environment]::Version.ToString()
        os_version = [System.Environment]::OSVersion.VersionString
        is_64_bit_process = [System.Environment]::Is64BitProcess
    }
}

$receiptDirectory = [System.IO.Path]::GetDirectoryName(
    [System.IO.Path]::GetFullPath($ReceiptPath)
)
if (-not [System.IO.Directory]::Exists($receiptDirectory)) {
    [System.IO.Directory]::CreateDirectory($receiptDirectory) | Out-Null
}
$json = ($receipt | ConvertTo-Json -Depth 12) + "`n"
[System.IO.File]::WriteAllText(
    [System.IO.Path]::GetFullPath($ReceiptPath),
    $json,
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Output "decision=$($receipt.decision)"
Write-Output "source_lock_pass=$($receipt.source_lock_pass)"
Write-Output "schema_preflight_pass=$($receipt.schema_preflight_pass)"
Write-Output "rows=$($receipt.observation_counts.rows)"
Write-Output "spines=$($receipt.entity_counts.spines)"
Write-Output "at_risk_intervals=$($receipt.interval_support.observed_visible_at_risk_intervals)"
Write-Output "disappearance_intervals=$($receipt.interval_support.observed_visible_disappearance_intervals)"
Write-Output "comparison_rowset_sha256=$comparisonRowsHash"
