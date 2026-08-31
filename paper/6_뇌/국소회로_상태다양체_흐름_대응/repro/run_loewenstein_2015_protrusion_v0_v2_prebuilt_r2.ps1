[CmdletBinding()]
param(
    [ValidateSet('SelfTest', 'Fit')]
    [string]$Mode = 'SelfTest',
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [Parameter(Mandatory = $true)]
    [string]$PrebuiltRunnerPath,
    [Parameter(Mandatory = $true)]
    [string]$RunSpecPath,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedRunSpecSha256,
    [Parameter(Mandatory = $true)]
    [string]$EnterpriseApprovalReceiptPath,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedEnterpriseApprovalReceiptSha256,
    [string]$UserAuthorizationReceiptPath = '',
    [string]$ExpectedUserAuthorizationReceiptSha256 = '',
    [string]$ScientificExecutionLockPath = '',
    [string]$ExpectedScientificExecutionLockSha256 = '',
    [string]$FinalizationManifestPath = '',
    [string]$ExpectedFinalizationManifestSha256 = '',
    [string]$DataPath = '',
    [string]$DictionaryPath = '',
    [Parameter(Mandatory = $true)]
    [string]$R2ExecutionContractPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedParentContractSha256 = 'a7fbc541b07bc47806ccba4836647826d4b125b2b4ff265387817cf09e78a93e'
$expectedParentFalseLockSha256 = '70171ba144416788891cd0e77ff390062ce8035eccdba6aa5a5af876485bc126'
$expectedParentWrapperSha256 = 'fd9e5c4ff094111f29431049ba2d9d267894237b218395634d40ad63165e998c'
$expectedR2ExecutionContractSha256 = '0272500218d9dbd3a0eedbaf5444c088cadc7d58711645da92483f3aa3ea569c'
$expectedArtifactGeneratorSha256 = 'a1f7f96985ee6b100a5d52528611d7f0382d19725f608a83bcc2dc53a04cd13e'
$expectedRustSourceSha256 = '23094cb23b3d14e9384b55270b0d887147d7dd7e8cbef9b85da6564796891e8e'
$expectedSelfTestCoreSha256 = 'ed13230bb3497a8a482e72ccd2acf40af09d2cd3c2078d9d43cabc31b7aec697'
$expectedBuildRustcVersion = 'rustc 1.95.0 (59807616e 2026-04-14)'
$expectedBuildRustcHost = 'x86_64-pc-windows-msvc'
$expectedRustcExecutableSha256 = '86478e53f769379d7f0ebfa7c9aa97cb76ca92233f79aa2cc0dbee2efaac73c7'
$expectedRustcVerboseSha256 = '185aa337caf524a621d7b1ce7b21a4d6f92f3ea592d009e481fea0e00e0d0434'
$expectedScientificCompileFlags = '--edition=2021 -C opt-level=3 -C debuginfo=0 -C overflow-checks=yes -C target-feature=-fma -C codegen-units=1'
$expectedPackagingLinkFlags = '-C link-arg=/Brepro'
$expectedModelSemantics = 'LOEWENSTEIN_V0_V1_V1Z_V2_C2015'
$expectedDecisionScope = 'WITHIN_PIPELINE_DESCRIPTIVE_PREDICTION_ONLY'
$expectedClaimCeiling = 'BIO_EVIDENCE_L0'
$expectedUserScope = 'V0,V1,V1Z,V2/2723_rows/1459_events/8_cell_LOCO/recataloguing_prediction_only'
$expectedPreSignPayloadSha256 = '47fd90048d28c7bdceb0654cae218759c0aea12b7ce5593f9d90a3a62ee03b4e'
$expectedBuildManifestSha256 = '27deaa7964f0705b6fb8735c066d45a0b596aa0cd612140d598e41172517ac6a'
$expectedEnterprisePolicyId = '{0283ac0f-fff1-49ae-ada1-8a933130cad6}'
$expectedDataSha256 = '2f6343606f62abb07b82491a71f0e4a4a898923d2bcf86aa4be8d596276d0062'
$expectedDataBytes = 569938
$expectedDictionarySha256 = '995bdb601f6ff71cd5877486dfdd0576db576c15effcc8c52db560eb523d9657'
$expectedDictionaryBytes = 4850
$expectedSourceManifestSha256 = '8209a09886b9322a02308f1dceff8d3805462c715135f79e28e1ab1e166b0630'
$expectedPreflightAuditorSha256 = 'a1b68ad6820055ba305058d7b5f646626df2842dd628a2401a95f785b4f600cc'
$expectedPreflightReceiptSha256 = '2ce71a85cd25c5da3d26c74f14aeb6c2d23daafa7fe3485b77567ddce619f517'
$expectedSourceManifestName = 'loewenstein_2015_spine_source_lock.tsv'
$expectedPreflightAuditorName = 'audit_loewenstein_2015_spine_preflight.ps1'
$expectedParentFalseLockName = 'loewenstein_2015_v0_v2_execution_lock.tsv'
$fitMarkerBytes = [System.Text.UTF8Encoding]::new($false).GetBytes("ce_npf_loewenstein_2015_fit_started_v1`n")

$runSpecKeys = @(
    'schema_version',
    'execution_ready',
    'parent_contract_sha256',
    'parent_false_lock_sha256',
    'r2_execution_contract_sha256',
    'r2_wrapper_sha256',
    'artifact_generator_sha256',
    'rust_source_sha256',
    'scientific_execution_lock_sha256',
    'pre_sign_payload_sha256',
    'signed_runner_sha256',
    'signed_runner_bytes',
    'signature_mode',
    'signer_certificate_sha256',
    'enterprise_policy_id',
    'build_manifest_sha256',
    'expected_self_test_core_sha256',
    'rustc_version',
    'rustc_host',
    'rustc_executable_sha256',
    'scientific_compile_flags',
    'packaging_link_flags',
    'runtime_threads',
    'model_semantics_id',
    'decision_scope',
    'claim_ceiling'
)

$userReceiptKeys = @(
    'schema_version',
    'decision',
    'run_spec_sha256',
    'scope',
    'decision_scope',
    'claim_ceiling',
    'run_id',
    'issuer',
    'issued_at_utc',
    'expires_at_utc'
)

$enterpriseReceiptKeys = @(
    'schema_version',
    'decision',
    'run_spec_sha256',
    'signed_runner_sha256',
    'signature_mode',
    'signer_certificate_sha256',
    'enterprise_policy_id',
    'allowed_host',
    'allowed_architecture',
    'run_id',
    'issuer',
    'issued_at_utc',
    'expires_at_utc'
)

$finalizationManifestKeys = @(
    'schema_version',
    'status',
    'run_id',
    'artifact_generator_sha256',
    'r2_execution_contract_sha256',
    'r2_wrapper_sha256',
    'run_spec_sha256',
    'scientific_execution_lock_sha256',
    'user_authorization_receipt_sha256',
    'enterprise_approval_receipt_sha256',
    'signed_runner_sha256',
    'signer_certificate_sha256',
    'enterprise_policy_id',
    'scientific_lock_materialization_authorized',
    'scientific_lock_must_be_last',
    'data_opened',
    'runner_executed'
)

$buildManifestKeys = @(
    'schema_version',
    'status',
    'candidate_relative_path',
    'candidate_sha256',
    'candidate_bytes',
    'candidate_authenticode_status',
    'repro_build_count',
    'repro_byte_identical',
    'rust_source_sha256',
    'rustc_version',
    'rustc_host',
    'rustc_executable_sha256',
    'rustc_verbose_sha256',
    'scientific_compile_flags',
    'packaging_link_flags',
    'comparison_contract_sha256',
    'parent_wrapper_sha256',
    'parent_false_lock_sha256',
    'expected_self_test_core_sha256',
    'runtime_threads',
    'model_semantics_id',
    'data_opened',
    'runner_executed'
)

$scientificLockKeys = @(
    'schema_version',
    'real_data_fit_authorized',
    'comparison_contract_sha256',
    'rust_source_sha256',
    'wrapper_sha256',
    'source_manifest_sha256',
    'preflight_auditor_sha256',
    'preflight_receipt_sha256',
    'preflight_decision',
    'raw_csv_sha256',
    'raw_csv_bytes',
    'dictionary_sha256',
    'dictionary_bytes',
    'rowset_sha256',
    'comparison_rows',
    'comparison_events',
    'age_rows',
    'age_events',
    'cell_rows',
    'cell_events',
    'model_feature_order',
    'numerical_tolerance_profile',
    'self_test_core_sha256',
    'rustc_version',
    'rustc_verbose_sha256',
    'rustc_host',
    'rustc_executable_sha256',
    'compile_flags',
    'runtime_threads'
)

function Get-BytesSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($algorithm.ComputeHash($Bytes)) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
}

function Test-LowerSha256 {
    param([Parameter(Mandatory = $true)][string]$Value)
    return $Value -cmatch '^[0-9a-f]{64}$'
}

function Get-LexicallySeparatedPaths {
    param(
        [Parameter(Mandatory = $true)][string]$ExecutionMode,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$RawPaths,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string[]]$ForbiddenSelfTestValues,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string[]]$RequiredFitValues
    )
    if ($ExecutionMode -ceq 'SelfTest') {
        foreach ($value in $ForbiddenSelfTestValues) {
            if (-not [string]::IsNullOrEmpty($value)) {
                throw 'STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST'
            }
        }
    }
    else {
        foreach ($value in $RequiredFitValues) {
            if ([string]::IsNullOrEmpty($value)) {
                throw 'STOP_USER_DATA_FIT_NOT_AUTHORIZED:missing_fit_argument'
            }
        }
    }
    $normalized = [ordered]@{}
    $seen = @{}
    foreach ($name in $RawPaths.Keys) {
        $value = [string]$RawPaths[$name]
        if ([string]::IsNullOrEmpty($value)) {
            $normalized[$name] = ''
            continue
        }
        try { $full = [IO.Path]::GetFullPath($value) }
        catch { throw ('STOP_PATH_ALIAS_OR_SCOPE:' + $name) }
        if ($full.StartsWith('\\',[StringComparison]::Ordinal) -or
            [string]::IsNullOrEmpty([IO.Path]::GetPathRoot($full))) {
            throw ('STOP_PATH_ALIAS_OR_SCOPE:' + $name + ':nonlocal')
        }
        $root = [IO.Path]::GetPathRoot($full)
        if ($full.Substring($root.Length).Contains(':')) {
            throw ('STOP_PATH_ALIAS_OR_SCOPE:' + $name + ':alternate_stream')
        }
        $identity = $full.ToLowerInvariant()
        if ($seen.ContainsKey($identity)) {
            throw ('STOP_PATH_ALIAS_OR_SCOPE:' + $name + ':duplicate')
        }
        $seen[$identity] = $name
        $normalized[$name] = $full
    }
    $output = [string]$normalized['OutputDirectory']
    $outputPrefix = $output.TrimEnd([char]92,[char]47) + [IO.Path]::DirectorySeparatorChar
    foreach ($name in $normalized.Keys) {
        if ($name -ceq 'OutputDirectory' -or [string]::IsNullOrEmpty([string]$normalized[$name])) { continue }
        $full = [string]$normalized[$name]
        $inputPrefix = $full.TrimEnd([char]92,[char]47) + [IO.Path]::DirectorySeparatorChar
        if ($full.StartsWith($outputPrefix,[StringComparison]::OrdinalIgnoreCase) -or
            $output.StartsWith($inputPrefix,[StringComparison]::OrdinalIgnoreCase)) {
            throw ('STOP_PATH_ALIAS_OR_SCOPE:' + $name + ':output_overlap')
        }
    }
    return $normalized
}

function Assert-Exact {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    if ([string]$Values[$Key] -cne $Expected) {
        throw ($StopCode + ':' + $Key)
    }
}

function Assert-NoReparsePath {
    param(
        [Parameter(Mandatory = $true)][System.IO.FileSystemInfo]$Item,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw ($StopCode + ':reparse')
    }
    $cursor = if ($Item -is [IO.DirectoryInfo]) { $Item } else { $Item.Directory }
    while ($null -ne $cursor) {
        if (($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw ($StopCode + ':reparse')
        }
        $cursor = $cursor.Parent
    }
}

function Get-PeContentIdentity {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][bool]$RequireEmbeddedCertificate,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    if ($Bytes.Length -lt 256) { throw ($StopCode + ':pe_too_short') }
    $peOffset = [BitConverter]::ToInt32($Bytes, 0x3c)
    if ($peOffset -lt 0 -or $peOffset + 24 -ge $Bytes.Length -or
        $Bytes[$peOffset] -ne 0x50 -or $Bytes[$peOffset + 1] -ne 0x45 -or
        $Bytes[$peOffset + 2] -ne 0 -or $Bytes[$peOffset + 3] -ne 0) {
        throw ($StopCode + ':pe_header')
    }
    $optionalOffset = $peOffset + 24
    $magic = [BitConverter]::ToUInt16($Bytes, $optionalOffset)
    if ($magic -eq 0x20b) { $directoryOffset = $optionalOffset + 112 }
    elseif ($magic -eq 0x10b) { $directoryOffset = $optionalOffset + 96 }
    else { throw ($StopCode + ':pe_magic') }
    $checksumOffset = $optionalOffset + 64
    $securityOffset = $directoryOffset + 32
    if ($securityOffset + 8 -gt $Bytes.Length) { throw ($StopCode + ':pe_bounds') }
    $certificateOffset = [BitConverter]::ToUInt32($Bytes, $securityOffset)
    $certificateSize = [BitConverter]::ToUInt32($Bytes, $securityOffset + 4)
    if ($RequireEmbeddedCertificate) {
        if ($certificateOffset -eq 0 -or $certificateSize -lt 8 -or
            ($certificateOffset % 8) -ne 0 -or
            ([uint64]$certificateOffset + [uint64]$certificateSize) -ne [uint64]$Bytes.Length) {
            throw ($StopCode + ':embedded_certificate_table')
        }
        $contentLength = [int]$certificateOffset
    }
    else {
        if ($certificateOffset -ne 0 -or $certificateSize -ne 0) {
            throw ($StopCode + ':unexpected_certificate_table')
        }
        $contentLength = $Bytes.Length
    }
    $normalized = [byte[]]$Bytes.Clone()
    for ($index = 0; $index -lt 4; $index++) { $normalized[$checksumOffset + $index] = 0 }
    for ($index = 0; $index -lt 8; $index++) { $normalized[$securityOffset + $index] = 0 }
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $sha256 = ([BitConverter]::ToString($algorithm.ComputeHash($normalized, 0, $contentLength)) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
    return [pscustomobject]@{
        Sha256 = $sha256
        ContentLength = $contentLength
        CertificateOffset = [uint64]$certificateOffset
        CertificateSize = [uint64]$certificateSize
    }
}

function Open-ReadGuard {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    try {
        $item = Get-Item -LiteralPath $LiteralPath -Force -ErrorAction Stop
    }
    catch {
        throw ($StopCode + ':missing')
    }
    if (-not ($item -is [IO.FileInfo])) {
        throw ($StopCode + ':not_regular_file')
    }
    Assert-NoReparsePath -Item $item -StopCode $StopCode
    $stream = [IO.FileStream]::new(
        $item.FullName,
        [IO.FileMode]::Open,
        [IO.FileAccess]::Read,
        [IO.FileShare]::Read
    )
    try {
        if ($stream.Length -gt [int]::MaxValue) {
            throw ($StopCode + ':too_large')
        }
        $bytes = [byte[]]::new([int]$stream.Length)
        $offset = 0
        while ($offset -lt $bytes.Length) {
            $read = $stream.Read($bytes, $offset, $bytes.Length - $offset)
            if ($read -le 0) {
                throw ($StopCode + ':short_read')
            }
            $offset += $read
        }
        $stream.Position = 0
        return [pscustomobject]@{
            Path = $item.FullName
            Bytes = $bytes
            Length = $bytes.Length
            Sha256 = Get-BytesSha256 -Bytes $bytes
            Stream = $stream
        }
    }
    catch {
        $stream.Dispose()
        throw
    }
}

function New-GuardedSnapshot {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    $parent = Get-Item -LiteralPath (Split-Path -Parent $LiteralPath) -Force -ErrorAction Stop
    if (-not ($parent -is [IO.DirectoryInfo])) { throw ($StopCode + ':snapshot_parent') }
    Assert-NoReparsePath -Item $parent -StopCode $StopCode
    $stream = [IO.FileStream]::new(
        $LiteralPath,
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::Write,
        [IO.FileShare]::None
    )
    try {
        $stream.Write($Bytes,0,$Bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
    $guard = Open-ReadGuard -LiteralPath $LiteralPath -StopCode $StopCode
    if ($guard.Sha256 -cne (Get-BytesSha256 -Bytes $Bytes)) {
        $guard.Stream.Dispose()
        throw ($StopCode + ':snapshot_hash')
    }
    return $guard
}

function Read-StrictTsv {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256,
        [Parameter(Mandatory = $true)][string[]]$Keys,
        [Parameter(Mandatory = $true)][string]$ExpectedSchema,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    if (-not (Test-LowerSha256 -Value $ExpectedSha256)) {
        throw ($StopCode + ':expected_hash')
    }
    $guard = Open-ReadGuard -LiteralPath $LiteralPath -StopCode $StopCode
    try {
        if ($guard.Sha256 -cne $ExpectedSha256) {
            throw ($StopCode + ':hash')
        }
        $bytes = [byte[]]$guard.Bytes
        if (($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) -or
            [Array]::IndexOf($bytes, [byte]13) -ge 0) {
            throw ($StopCode + ':encoding')
        }
        try {
            $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes)
        }
        catch {
            throw ($StopCode + ':utf8')
        }
        if (-not $text.EndsWith("`n", [StringComparison]::Ordinal) -or
            $text.EndsWith("`n`n", [StringComparison]::Ordinal)) {
            throw ($StopCode + ':newline')
        }
        $lines = $text.Substring(0, $text.Length - 1).Split([char]10)
        if ($lines.Count -ne $Keys.Count + 1 -or $lines[0] -cne "key`tvalue") {
            throw ($StopCode + ':header_or_count')
        }
        $values = @{}
        for ($index = 0; $index -lt $Keys.Count; $index++) {
            $fields = $lines[$index + 1].Split([char]9)
            if ($fields.Count -ne 2 -or $fields[0] -cne $Keys[$index] -or
                [string]::IsNullOrEmpty($fields[1]) -or
                $fields[1] -cmatch '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]' -or
                $values.ContainsKey($fields[0])) {
                throw ($StopCode + ':row_' + ($index + 2))
            }
            $values[$fields[0]] = $fields[1]
        }
        if ([string]$values['schema_version'] -cne $ExpectedSchema) {
            throw ($StopCode + ':schema')
        }
        return [pscustomobject]@{
            Guard = $guard
            Sha256 = $guard.Sha256
            Values = $values
        }
    }
    catch {
        $guard.Stream.Dispose()
        throw
    }
}

function Assert-ReceiptTimeWindow {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    try {
        $issued = [DateTimeOffset]::ParseExact(
            [string]$Values['issued_at_utc'],
            'yyyy-MM-ddTHH:mm:ssZ',
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal
        ).ToUniversalTime()
        $expires = [DateTimeOffset]::ParseExact(
            [string]$Values['expires_at_utc'],
            'yyyy-MM-ddTHH:mm:ssZ',
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal
        ).ToUniversalTime()
    }
    catch {
        throw ($StopCode + ':time_parse')
    }
    $now = [DateTimeOffset]::UtcNow
    if ($issued -gt $now.AddMinutes(5) -or $expires -le $now -or $expires -le $issued) {
        throw ($StopCode + ':time_window')
    }
}

function Assert-NoPendingApprovalValue {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    foreach ($key in @('run_id','issuer')) {
        if ([string]$Values[$key] -cmatch '^PENDING(?:-|$)') {
            throw ($StopCode + ':' + $key)
        }
    }
}

function Test-ExactMarker {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) {
        return $false
    }
    $bytes = [IO.File]::ReadAllBytes($LiteralPath)
    if ($bytes.Length -ne $fitMarkerBytes.Length) {
        return $false
    }
    for ($index = 0; $index -lt $bytes.Length; $index++) {
        if ($bytes[$index] -ne $fitMarkerBytes[$index]) {
            return $false
        }
    }
    return $true
}

function Invoke-GuardedRunner {
    param(
        [Parameter(Mandatory = $true)][string]$RunnerPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    try {
        $output = @(& $RunnerPath @Arguments 2>&1)
        $exitCode = $LASTEXITCODE
    }
    catch {
        throw 'STOP_ENTERPRISE_EXECUTION_NOT_APPROVED:launch_denied'
    }
    return [pscustomobject]@{
        Output = $output
        ExitCode = $exitCode
    }
}

function Commit-ControlReceipt {
    param(
        [Parameter(Mandatory = $true)][IO.FileStream]$Stream,
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Value
    )
    $json = ($Value | ConvertTo-Json -Depth 6 -Compress) + [char]10
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($json)
    $expectedSha256 = Get-BytesSha256 -Bytes $bytes
    $Stream.SetLength(0)
    $Stream.Position = 0
    $Stream.Write($bytes,0,$bytes.Length)
    $Stream.Flush($true)
    $Stream.Position = 0
    $observed = [byte[]]::new($bytes.Length)
    $offset = 0
    while ($offset -lt $observed.Length) {
        $read = $Stream.Read($observed,$offset,$observed.Length-$offset)
        if ($read -le 0) { throw 'STOP_CONTROL_RECEIPT_COMMIT:short_read' }
        $offset += $read
    }
    if ((Get-BytesSha256 -Bytes $observed) -cne $expectedSha256) {
        throw 'STOP_CONTROL_RECEIPT_COMMIT:hash'
    }
    return $expectedSha256
}

function Write-ControlCommitMarker {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$ReceiptSha256
    )
    if (-not (Test-LowerSha256 -Value $ReceiptSha256)) {
        throw 'STOP_CONTROL_RECEIPT_COMMIT:marker_hash'
    }
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($ReceiptSha256 + [char]10)
    $stream = [IO.FileStream]::new(
        $LiteralPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None
    )
    try {
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush($true)
        $stream.Position = 0
        $observed = [byte[]]::new($bytes.Length)
        $offset = 0
        while ($offset -lt $observed.Length) {
            $read = $stream.Read($observed,$offset,$observed.Length-$offset)
            if ($read -le 0) { throw 'STOP_CONTROL_RECEIPT_COMMIT:marker_short_read' }
            $offset += $read
        }
        if ((Get-BytesSha256 -Bytes $observed) -cne (Get-BytesSha256 -Bytes $bytes)) {
            throw 'STOP_CONTROL_RECEIPT_COMMIT:marker_verify'
        }
    }
    finally {
        $stream.Dispose()
    }
}

try {
    $lexicalPaths = Get-LexicallySeparatedPaths -ExecutionMode $Mode -RawPaths ([ordered]@{
        OutputDirectory = $OutputDirectory
        PrebuiltRunnerPath = $PrebuiltRunnerPath
        RunSpecPath = $RunSpecPath
        EnterpriseApprovalReceiptPath = $EnterpriseApprovalReceiptPath
        UserAuthorizationReceiptPath = $UserAuthorizationReceiptPath
        ScientificExecutionLockPath = $ScientificExecutionLockPath
        FinalizationManifestPath = $FinalizationManifestPath
        DataPath = $DataPath
        DictionaryPath = $DictionaryPath
        R2ExecutionContractPath = $R2ExecutionContractPath
        WrapperPath = $PSCommandPath
        ArtifactGeneratorPath = (Join-Path $PSScriptRoot 'new_loewenstein_2015_prebuilt_r2_artifacts.ps1')
        RustSourcePath = (Join-Path $PSScriptRoot 'fit_loewenstein_2015_protrusion_v0_v2.rs')
        ParentFalseLockPath = (Join-Path $PSScriptRoot $expectedParentFalseLockName)
        SourceManifestPath = (Join-Path $PSScriptRoot $expectedSourceManifestName)
        PreflightAuditorPath = (Join-Path $PSScriptRoot $expectedPreflightAuditorName)
        PreflightReceiptPath = (Join-Path $PSScriptRoot '../../../../artifacts/brain/ce_npf_loewenstein_spine_preflight_v1/receipt.json')
        BuildManifestPath = (Join-Path $PSScriptRoot '../../../../artifacts/brain/ce_npf_loewenstein_2015_runner_signing_candidate_v1/build_manifest.tsv')
        UnsignedCandidatePath = (Join-Path $PSScriptRoot '../../../../artifacts/brain/ce_npf_loewenstein_2015_runner_signing_candidate_v1/signing_payload/fit_loewenstein_2015_protrusion_v0_v2.exe')
    }) -ForbiddenSelfTestValues @(
        $DataPath,$DictionaryPath,$ScientificExecutionLockPath,
        $ExpectedScientificExecutionLockSha256,$UserAuthorizationReceiptPath,
        $ExpectedUserAuthorizationReceiptSha256,$FinalizationManifestPath,
        $ExpectedFinalizationManifestSha256
    ) -RequiredFitValues @(
        $UserAuthorizationReceiptPath,$ExpectedUserAuthorizationReceiptSha256,
        $ScientificExecutionLockPath,$ExpectedScientificExecutionLockSha256,
        $FinalizationManifestPath,$ExpectedFinalizationManifestSha256,
        $DataPath,$DictionaryPath
    )
}
catch {
    [Console]::Error.WriteLine([string](($_.Exception.Message -split ':',2)[0]))
    exit 1
}
$OutputDirectory = [string]$lexicalPaths['OutputDirectory']
$PrebuiltRunnerPath = [string]$lexicalPaths['PrebuiltRunnerPath']
$RunSpecPath = [string]$lexicalPaths['RunSpecPath']
$EnterpriseApprovalReceiptPath = [string]$lexicalPaths['EnterpriseApprovalReceiptPath']
$UserAuthorizationReceiptPath = [string]$lexicalPaths['UserAuthorizationReceiptPath']
$ScientificExecutionLockPath = [string]$lexicalPaths['ScientificExecutionLockPath']
$FinalizationManifestPath = [string]$lexicalPaths['FinalizationManifestPath']
$DataPath = [string]$lexicalPaths['DataPath']
$DictionaryPath = [string]$lexicalPaths['DictionaryPath']
$R2ExecutionContractPath = [string]$lexicalPaths['R2ExecutionContractPath']

$sourcePath = Join-Path $PSScriptRoot 'fit_loewenstein_2015_protrusion_v0_v2.rs'
$artifactGeneratorPath = Join-Path $PSScriptRoot 'new_loewenstein_2015_prebuilt_r2_artifacts.ps1'
$sourceManifestPath = Join-Path $PSScriptRoot $expectedSourceManifestName
$preflightAuditorPath = Join-Path $PSScriptRoot $expectedPreflightAuditorName
$parentFalseLockPath = Join-Path $PSScriptRoot $expectedParentFalseLockName
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
$preflightReceiptPath = Join-Path $repositoryRoot 'artifacts/brain/ce_npf_loewenstein_spine_preflight_v1/receipt.json'
$buildManifestPath = Join-Path $repositoryRoot 'artifacts/brain/ce_npf_loewenstein_2015_runner_signing_candidate_v1/build_manifest.tsv'

$guards = [Collections.Generic.List[IDisposable]]::new()
$status = 'STOP'
$stopCode = ''
$runnerMessage = ''
$coreSha256 = ''
$selfTestSha256 = ''
$fitStarted = $false
$dataOpened = $false
$runnerSha256 = ''
$runnerCertificateSha256 = ''
$runnerPeContentSha256 = ''
$runSpecSha256 = ''
$scientificLockSha256 = ''
$finalizationManifestSha256 = ''
$userReceiptSha256 = ''
$enterpriseReceiptSha256 = ''
$runId = ''
$temporaryRoot = ''
$outputReady = $false
$controlStream = $null
$controlCommitPath = ''
$controlReceiptCommitted = $false
$cleanupPass = $true
$environmentRestorePass = $true
$originalThreads = [ordered]@{
    RAYON_NUM_THREADS = [Environment]::GetEnvironmentVariable('RAYON_NUM_THREADS', 'Process')
    OMP_NUM_THREADS = [Environment]::GetEnvironmentVariable('OMP_NUM_THREADS', 'Process')
    OPENBLAS_NUM_THREADS = [Environment]::GetEnvironmentVariable('OPENBLAS_NUM_THREADS', 'Process')
    MKL_NUM_THREADS = [Environment]::GetEnvironmentVariable('MKL_NUM_THREADS', 'Process')
}

try {
    if (Test-Path -LiteralPath $OutputDirectory) { throw 'STOP_OUTPUT_EXISTS' }
    $outputParent = Get-Item -LiteralPath (Split-Path -Parent $OutputDirectory) -Force -ErrorAction Stop
    if (-not ($outputParent -is [IO.DirectoryInfo])) { throw 'STOP_OUTPUT_EXISTS:parent_not_directory' }
    Assert-NoReparsePath -Item $outputParent -StopCode 'STOP_OUTPUT_EXISTS'
    New-Item -ItemType Directory -Path $OutputDirectory -ErrorAction Stop | Out-Null
    $outputItem = Get-Item -LiteralPath $OutputDirectory -Force -ErrorAction Stop
    if (-not ($outputItem -is [IO.DirectoryInfo])) { throw 'STOP_OUTPUT_EXISTS:not_directory' }
    Assert-NoReparsePath -Item $outputItem -StopCode 'STOP_OUTPUT_EXISTS'
    $resolvedOutput = $outputItem.FullName
    $corePath = Join-Path $resolvedOutput $(if ($Mode -eq 'SelfTest') { 'self_test_core.json' } else { 'core_receipt.json' })
    $controlPath = Join-Path $resolvedOutput 'execution_control_receipt.json'
    $controlCommitPath = Join-Path $resolvedOutput 'execution_control_receipt.sha256'
    if (Test-Path -LiteralPath $corePath) {
        throw ('STOP_OUTPUT_EXISTS:' + $corePath)
    }
    $controlStream = [IO.FileStream]::new(
        $controlPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None
    )
    $outputReady = $true

    $runSpec = Read-StrictTsv -LiteralPath $RunSpecPath -ExpectedSha256 $ExpectedRunSpecSha256 `
        -Keys $runSpecKeys -ExpectedSchema 'ce_npf_loewenstein_2015_prebuilt_run_spec_r2' `
        -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $guards.Add($runSpec.Guard.Stream)
    $runSpecSha256 = $runSpec.Sha256
    $run = $runSpec.Values
    if ([string]$run['execution_ready'] -cne 'true') {
        throw 'STOP_RUN_SPEC_NOT_READY'
    }
    foreach ($key in $runSpecKeys) {
        if ([string]$run[$key] -cmatch '^PENDING(?:-|$)') {
            throw ('STOP_RUN_SPEC_NOT_READY:' + $key)
        }
    }
    Assert-Exact -Values $run -Key 'parent_contract_sha256' -Expected $expectedParentContractSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'parent_false_lock_sha256' -Expected $expectedParentFalseLockSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'r2_execution_contract_sha256' -Expected $expectedR2ExecutionContractSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'artifact_generator_sha256' -Expected $expectedArtifactGeneratorSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'rust_source_sha256' -Expected $expectedRustSourceSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'pre_sign_payload_sha256' -Expected $expectedPreSignPayloadSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'build_manifest_sha256' -Expected $expectedBuildManifestSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'expected_self_test_core_sha256' -Expected $expectedSelfTestCoreSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'rustc_version' -Expected $expectedBuildRustcVersion -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'rustc_host' -Expected $expectedBuildRustcHost -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'rustc_executable_sha256' -Expected $expectedRustcExecutableSha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'scientific_compile_flags' -Expected $expectedScientificCompileFlags -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'packaging_link_flags' -Expected $expectedPackagingLinkFlags -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'runtime_threads' -Expected '1' -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'model_semantics_id' -Expected $expectedModelSemantics -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'decision_scope' -Expected $expectedDecisionScope -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'claim_ceiling' -Expected $expectedClaimCeiling -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'signature_mode' -Expected 'authenticode' -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    Assert-Exact -Values $run -Key 'enterprise_policy_id' -Expected $expectedEnterprisePolicyId -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    foreach ($shaKey in @('r2_execution_contract_sha256','r2_wrapper_sha256','artifact_generator_sha256','scientific_execution_lock_sha256','pre_sign_payload_sha256','signed_runner_sha256','signer_certificate_sha256','build_manifest_sha256')) {
        if (-not (Test-LowerSha256 -Value ([string]$run[$shaKey]))) {
            throw ('STOP_RUN_SPEC_HASH_OR_SCHEMA:' + $shaKey)
        }
    }
    if ([string]$run['enterprise_policy_id'] -cnotmatch '^\{[0-9A-Fa-f-]{36}\}$') {
        throw 'STOP_RUN_SPEC_HASH_OR_SCHEMA:enterprise_policy_id'
    }
    $signedRunnerBytes = 0L
    if (-not [long]::TryParse([string]$run['signed_runner_bytes'], [ref]$signedRunnerBytes) -or $signedRunnerBytes -le 0) {
        throw 'STOP_RUN_SPEC_HASH_OR_SCHEMA:signed_runner_bytes'
    }

    $enterpriseReceipt = Read-StrictTsv -LiteralPath $EnterpriseApprovalReceiptPath `
        -ExpectedSha256 $ExpectedEnterpriseApprovalReceiptSha256 -Keys $enterpriseReceiptKeys `
        -ExpectedSchema 'ce_npf_loewenstein_2015_enterprise_execution_approval_r2' `
        -StopCode 'STOP_ENTERPRISE_EXECUTION_NOT_APPROVED'
    $guards.Add($enterpriseReceipt.Guard.Stream)
    $enterpriseReceiptSha256 = $enterpriseReceipt.Sha256
    $enterprise = $enterpriseReceipt.Values
    Assert-Exact -Values $enterprise -Key 'decision' -Expected 'APPROVE_EXECUTION' -StopCode 'STOP_ENTERPRISE_EXECUTION_NOT_APPROVED'
    Assert-NoPendingApprovalValue -Values $enterprise -StopCode 'STOP_ENTERPRISE_EXECUTION_NOT_APPROVED'
    Assert-Exact -Values $enterprise -Key 'run_spec_sha256' -Expected $runSpecSha256 -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
    foreach ($key in @('signed_runner_sha256','signature_mode','signer_certificate_sha256','enterprise_policy_id')) {
        Assert-Exact -Values $enterprise -Key $key -Expected ([string]$run[$key]) -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
    }
    Assert-Exact -Values $enterprise -Key 'allowed_host' -Expected ([Environment]::MachineName) -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
    Assert-Exact -Values $enterprise -Key 'allowed_architecture' -Expected $expectedBuildRustcHost -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
    Assert-ReceiptTimeWindow -Values $enterprise -StopCode 'STOP_APPROVAL_EXPIRED_OR_RUN_ID_MISMATCH'
    $runId = [string]$enterprise['run_id']
    if ($runId -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$') {
        throw 'STOP_APPROVAL_EXPIRED_OR_RUN_ID_MISMATCH:run_id'
    }

    if ($Mode -eq 'Fit') {
        $userReceipt = Read-StrictTsv -LiteralPath $UserAuthorizationReceiptPath `
            -ExpectedSha256 $ExpectedUserAuthorizationReceiptSha256 -Keys $userReceiptKeys `
            -ExpectedSchema 'ce_npf_loewenstein_2015_user_fit_authorization_r2' `
            -StopCode 'STOP_USER_DATA_FIT_NOT_AUTHORIZED'
        $guards.Add($userReceipt.Guard.Stream)
        $userReceiptSha256 = $userReceipt.Sha256
        $user = $userReceipt.Values
        Assert-Exact -Values $user -Key 'decision' -Expected 'AUTHORIZE' -StopCode 'STOP_USER_DATA_FIT_NOT_AUTHORIZED'
        Assert-NoPendingApprovalValue -Values $user -StopCode 'STOP_USER_DATA_FIT_NOT_AUTHORIZED'
        Assert-Exact -Values $user -Key 'run_spec_sha256' -Expected $runSpecSha256 -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
        Assert-Exact -Values $user -Key 'scope' -Expected $expectedUserScope -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
        Assert-Exact -Values $user -Key 'decision_scope' -Expected $expectedDecisionScope -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
        Assert-Exact -Values $user -Key 'claim_ceiling' -Expected $expectedClaimCeiling -StopCode 'STOP_APPROVAL_BINDING_MISMATCH'
        Assert-Exact -Values $user -Key 'run_id' -Expected $runId -StopCode 'STOP_APPROVAL_EXPIRED_OR_RUN_ID_MISMATCH'
        Assert-ReceiptTimeWindow -Values $user -StopCode 'STOP_APPROVAL_EXPIRED_OR_RUN_ID_MISMATCH'

        $scientificLock = Read-StrictTsv -LiteralPath $ScientificExecutionLockPath `
            -ExpectedSha256 $ExpectedScientificExecutionLockSha256 -Keys $scientificLockKeys `
            -ExpectedSchema 'ce_npf_loewenstein_2015_v0_v2_execution_lock_v1' `
            -StopCode 'STOP_SCIENTIFIC_LOCK_MISMATCH'
        $guards.Add($scientificLock.Guard.Stream)
        $scientificLockSha256 = $scientificLock.Sha256
        Assert-Exact -Values $run -Key 'scientific_execution_lock_sha256' -Expected $scientificLockSha256 -StopCode 'STOP_SCIENTIFIC_LOCK_MISMATCH'
        $parentLock = Read-StrictTsv -LiteralPath $parentFalseLockPath `
            -ExpectedSha256 $expectedParentFalseLockSha256 -Keys $scientificLockKeys `
            -ExpectedSchema 'ce_npf_loewenstein_2015_v0_v2_execution_lock_v1' `
            -StopCode 'STOP_SCIENTIFIC_LOCK_MISMATCH'
        $guards.Add($parentLock.Guard.Stream)
        foreach ($key in $scientificLockKeys) {
            $expected = [string]$parentLock.Values[$key]
            if ($key -ceq 'real_data_fit_authorized') { $expected = 'true' }
            elseif ($key -ceq 'wrapper_sha256') { $expected = [string]$run['r2_wrapper_sha256'] }
            if ([string]$scientificLock.Values[$key] -cne $expected) {
                throw ('STOP_SCIENTIFIC_LOCK_MISMATCH:' + $key)
            }
        }

        $finalizationManifest = Read-StrictTsv -LiteralPath $FinalizationManifestPath `
            -ExpectedSha256 $ExpectedFinalizationManifestSha256 -Keys $finalizationManifestKeys `
            -ExpectedSchema 'ce_npf_loewenstein_2015_prebuilt_r2_finalization_manifest_v1' `
            -StopCode 'STOP_FINALIZATION_MANIFEST_MISMATCH'
        $guards.Add($finalizationManifest.Guard.Stream)
        $finalizationManifestSha256 = $finalizationManifest.Sha256
        $finalization = $finalizationManifest.Values
        foreach ($key in $finalizationManifestKeys) {
            if ([string]$finalization[$key] -cmatch '^PENDING(?:-|$)') {
                throw ('STOP_FINALIZATION_MANIFEST_MISMATCH:' + $key)
            }
        }
        foreach ($binding in @(
            @('status','APPROVALS_VERIFIED_LOCK_MATERIALIZATION_AUTHORIZED'),
            @('run_id',$runId),
            @('artifact_generator_sha256',[string]$run['artifact_generator_sha256']),
            @('r2_execution_contract_sha256',[string]$run['r2_execution_contract_sha256']),
            @('r2_wrapper_sha256',[string]$run['r2_wrapper_sha256']),
            @('run_spec_sha256',$runSpecSha256),
            @('scientific_execution_lock_sha256',$scientificLockSha256),
            @('user_authorization_receipt_sha256',$userReceiptSha256),
            @('enterprise_approval_receipt_sha256',$enterpriseReceiptSha256),
            @('signed_runner_sha256',[string]$run['signed_runner_sha256']),
            @('signer_certificate_sha256',[string]$run['signer_certificate_sha256']),
            @('enterprise_policy_id',$expectedEnterprisePolicyId),
            @('scientific_lock_materialization_authorized','true'),
            @('scientific_lock_must_be_last','true'),
            @('data_opened','false'),
            @('runner_executed','false')
        )) {
            Assert-Exact -Values $finalization -Key $binding[0] -Expected $binding[1] `
                -StopCode 'STOP_FINALIZATION_MANIFEST_MISMATCH'
        }
    }

    $wrapperGuard = Open-ReadGuard -LiteralPath $PSCommandPath -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $guards.Add($wrapperGuard.Stream)
    Assert-Exact -Values $run -Key 'r2_wrapper_sha256' -Expected $wrapperGuard.Sha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $generatorGuard = Open-ReadGuard -LiteralPath $artifactGeneratorPath -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $guards.Add($generatorGuard.Stream)
    if ($generatorGuard.Sha256 -cne $expectedArtifactGeneratorSha256) { throw 'STOP_RUN_SPEC_HASH_OR_SCHEMA:artifact_generator' }
    Assert-Exact -Values $run -Key 'artifact_generator_sha256' -Expected $generatorGuard.Sha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $sourceGuard = Open-ReadGuard -LiteralPath $sourcePath -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $guards.Add($sourceGuard.Stream)
    if ($sourceGuard.Sha256 -cne $expectedRustSourceSha256) { throw 'STOP_RUN_SPEC_HASH_OR_SCHEMA:rust_source' }
    $contractGuard = Open-ReadGuard -LiteralPath $R2ExecutionContractPath -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $guards.Add($contractGuard.Stream)
    if ($contractGuard.Sha256 -cne $expectedR2ExecutionContractSha256) { throw 'STOP_RUN_SPEC_HASH_OR_SCHEMA:r2_contract' }
    Assert-Exact -Values $run -Key 'r2_execution_contract_sha256' -Expected $contractGuard.Sha256 -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $buildManifest = Read-StrictTsv -LiteralPath $buildManifestPath `
        -ExpectedSha256 ([string]$run['build_manifest_sha256']) -Keys $buildManifestKeys `
        -ExpectedSchema 'ce_npf_loewenstein_2015_runner_signing_candidate_v1' `
        -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    $guards.Add($buildManifest.Guard.Stream)
    $manifest = $buildManifest.Values
    foreach ($binding in @(
        @('status','UNSIGNED_SIGNING_CANDIDATE_NOT_EXECUTED'),
        @('candidate_relative_path','signing_payload/fit_loewenstein_2015_protrusion_v0_v2.exe'),
        @('candidate_sha256',$expectedPreSignPayloadSha256),
        @('candidate_bytes','732672'),
        @('candidate_authenticode_status','NotSigned'),
        @('repro_build_count','3'),
        @('repro_byte_identical','true'),
        @('rust_source_sha256',$expectedRustSourceSha256),
        @('rustc_version',$expectedBuildRustcVersion),
        @('rustc_host',$expectedBuildRustcHost),
        @('rustc_executable_sha256',$expectedRustcExecutableSha256),
        @('rustc_verbose_sha256',$expectedRustcVerboseSha256),
        @('scientific_compile_flags',$expectedScientificCompileFlags),
        @('packaging_link_flags',$expectedPackagingLinkFlags),
        @('comparison_contract_sha256',$expectedParentContractSha256),
        @('parent_wrapper_sha256',$expectedParentWrapperSha256),
        @('parent_false_lock_sha256',$expectedParentFalseLockSha256),
        @('expected_self_test_core_sha256',$expectedSelfTestCoreSha256),
        @('runtime_threads','1'),
        @('model_semantics_id',$expectedModelSemantics),
        @('data_opened','false'),
        @('runner_executed','false')
    )) {
        Assert-Exact -Values $manifest -Key $binding[0] -Expected $binding[1] -StopCode 'STOP_RUN_SPEC_HASH_OR_SCHEMA'
    }
    $candidatePath = Join-Path (Split-Path -Parent $buildManifest.Guard.Path) ([string]$manifest['candidate_relative_path'])
    $candidateGuard = Open-ReadGuard -LiteralPath $candidatePath -StopCode 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE'
    $guards.Add($candidateGuard.Stream)
    if ($candidateGuard.Sha256 -cne [string]$run['pre_sign_payload_sha256'] -or
        $candidateGuard.Length -ne [int][string]$manifest['candidate_bytes']) {
        throw 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE:pre_sign_payload'
    }
    $candidatePeIdentity = Get-PeContentIdentity -Bytes $candidateGuard.Bytes -RequireEmbeddedCertificate $false -StopCode 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE'
    if ($candidatePeIdentity.Sha256 -cne $candidateGuard.Sha256 -or
        [string](Get-AuthenticodeSignature -LiteralPath $candidateGuard.Path).Status -cne 'NotSigned') {
        throw 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE:pre_sign_identity'
    }
    if ($Mode -eq 'Fit') {
        foreach ($pair in @(
            @($sourceManifestPath,$expectedSourceManifestSha256),
            @($preflightAuditorPath,$expectedPreflightAuditorSha256),
            @($preflightReceiptPath,$expectedPreflightReceiptSha256)
        )) {
            $guard = Open-ReadGuard -LiteralPath $pair[0] -StopCode 'STOP_SCIENTIFIC_LOCK_MISMATCH'
            $guards.Add($guard.Stream)
            if ($guard.Sha256 -cne $pair[1]) { throw 'STOP_SCIENTIFIC_LOCK_MISMATCH:prerequisite' }
        }
    }

    $runnerGuard = Open-ReadGuard -LiteralPath $PrebuiltRunnerPath -StopCode 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE'
    $guards.Add($runnerGuard.Stream)
    $runnerSha256 = $runnerGuard.Sha256
    if ($runnerSha256 -cne [string]$run['signed_runner_sha256'] -or $runnerGuard.Length -ne $signedRunnerBytes) {
        throw 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE'
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $runnerGuard.Path
    if ([string]$signature.Status -cne 'Valid' -or
        [string]$signature.SignatureType -cne 'Authenticode' -or
        $null -eq $signature.SignerCertificate) {
        throw 'STOP_PREBUILT_RUNNER_SIGNATURE:status'
    }
    $runnerCertificateSha256 = Get-BytesSha256 -Bytes ([byte[]]$signature.SignerCertificate.RawData)
    Assert-Exact -Values $run -Key 'signer_certificate_sha256' -Expected $runnerCertificateSha256 -StopCode 'STOP_PREBUILT_RUNNER_SIGNATURE'
    $runnerPeIdentity = Get-PeContentIdentity -Bytes $runnerGuard.Bytes -RequireEmbeddedCertificate $true -StopCode 'STOP_PREBUILT_RUNNER_SIGNATURE'
    $runnerPeContentSha256 = $runnerPeIdentity.Sha256
    Assert-Exact -Values $run -Key 'pre_sign_payload_sha256' -Expected $runnerPeContentSha256 -StopCode 'STOP_PREBUILT_RUNNER_SIGNATURE'

    foreach ($threadName in $originalThreads.Keys) {
        [Environment]::SetEnvironmentVariable($threadName, '1', 'Process')
    }
    $temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ('ce-loewenstein-prebuilt-r2-' + [guid]::NewGuid().ToString('N'))
    $temporaryItem = New-Item -ItemType Directory -Path $temporaryRoot -ErrorAction Stop
    if (-not ($temporaryItem -is [IO.DirectoryInfo])) { throw 'STOP_TEMP_CLEANUP_SCOPE:not_directory' }
    Assert-NoReparsePath -Item $temporaryItem -StopCode 'STOP_TEMP_CLEANUP_SCOPE'
    $runnerSnapshot = New-GuardedSnapshot -LiteralPath (Join-Path $temporaryRoot 'fit_loewenstein_2015_protrusion_v0_v2.exe') `
        -Bytes $runnerGuard.Bytes -StopCode 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE'
    $guards.Add($runnerSnapshot.Stream)
    if ($runnerSnapshot.Sha256 -cne $runnerSha256 -or $runnerSnapshot.Length -ne $signedRunnerBytes) {
        throw 'STOP_PREBUILT_RUNNER_HASH_OR_SIZE:snapshot'
    }
    $snapshotSignature = Get-AuthenticodeSignature -LiteralPath $runnerSnapshot.Path
    if ([string]$snapshotSignature.Status -cne 'Valid' -or
        [string]$snapshotSignature.SignatureType -cne 'Authenticode' -or
        $null -eq $snapshotSignature.SignerCertificate -or
        (Get-BytesSha256 -Bytes ([byte[]]$snapshotSignature.SignerCertificate.RawData)) -cne $runnerCertificateSha256) {
        throw 'STOP_PREBUILT_RUNNER_SIGNATURE:snapshot'
    }
    $snapshotPeIdentity = Get-PeContentIdentity -Bytes $runnerSnapshot.Bytes -RequireEmbeddedCertificate $true -StopCode 'STOP_PREBUILT_RUNNER_SIGNATURE'
    if ($snapshotPeIdentity.Sha256 -cne $expectedPreSignPayloadSha256) { throw 'STOP_PREBUILT_RUNNER_SIGNATURE:snapshot_lineage' }
    $selfTestPath = if ($Mode -eq 'SelfTest') { $corePath } else { Join-Path $temporaryRoot 'self_test_core.json' }
    $selfTestRun = Invoke-GuardedRunner -RunnerPath $runnerSnapshot.Path -Arguments @('--self-test','--core-receipt',$selfTestPath)
    if ($selfTestRun.ExitCode -ne 0) {
        throw 'STOP_SELF_TEST_CORE_HASH_MISMATCH:runner_exit'
    }
    $selfTestGuard = Open-ReadGuard -LiteralPath $selfTestPath -StopCode 'STOP_SELF_TEST_CORE_HASH_MISMATCH'
    $guards.Add($selfTestGuard.Stream)
    $selfTestSha256 = $selfTestGuard.Sha256
    if ($selfTestSha256 -cne $expectedSelfTestCoreSha256) {
        throw 'STOP_SELF_TEST_CORE_HASH_MISMATCH:receipt'
    }

    if ($Mode -eq 'Fit') {
        $lockSnapshot = New-GuardedSnapshot -LiteralPath (Join-Path $temporaryRoot 'scientific_execution_lock.tsv') `
            -Bytes $scientificLock.Guard.Bytes -StopCode 'STOP_SCIENTIFIC_LOCK_MISMATCH'
        $guards.Add($lockSnapshot.Stream)
        if ($lockSnapshot.Sha256 -cne $scientificLockSha256) { throw 'STOP_SCIENTIFIC_LOCK_MISMATCH:snapshot' }
        $dataOpened = $true
        $dictionaryGuard = Open-ReadGuard -LiteralPath $DictionaryPath -StopCode 'STOP_SOURCE_CONTENT_MISMATCH'
        $guards.Add($dictionaryGuard.Stream)
        if ($dictionaryGuard.Sha256 -cne $expectedDictionarySha256 -or $dictionaryGuard.Length -ne $expectedDictionaryBytes) {
            throw 'STOP_SOURCE_CONTENT_MISMATCH:dictionary'
        }
        $dictionarySnapshot = New-GuardedSnapshot -LiteralPath (Join-Path $temporaryRoot 'dictionary.csv') `
            -Bytes $dictionaryGuard.Bytes -StopCode 'STOP_SOURCE_CONTENT_MISMATCH'
        $guards.Add($dictionarySnapshot.Stream)
        $dataGuard = Open-ReadGuard -LiteralPath $DataPath -StopCode 'STOP_SOURCE_CONTENT_MISMATCH'
        $guards.Add($dataGuard.Stream)
        if ($dataGuard.Sha256 -cne $expectedDataSha256 -or $dataGuard.Length -ne $expectedDataBytes) {
            throw 'STOP_SOURCE_CONTENT_MISMATCH:raw_csv'
        }
        $dataSnapshot = New-GuardedSnapshot -LiteralPath (Join-Path $temporaryRoot 'loewenstein_2015_spines.csv') `
            -Bytes $dataGuard.Bytes -StopCode 'STOP_SOURCE_CONTENT_MISMATCH'
        $guards.Add($dataSnapshot.Stream)
        $fitMarkerPath = Join-Path $temporaryRoot 'fit_started.marker'
        $fitRun = Invoke-GuardedRunner -RunnerPath $runnerSnapshot.Path -Arguments @(
            '--fit',
            '--data',$dataSnapshot.Path,
            '--dictionary',$dictionarySnapshot.Path,
            '--execution-lock',$lockSnapshot.Path,
            '--expected-lock-sha256',$scientificLockSha256,
            '--core-receipt',$corePath,
            '--fit-started-marker',$fitMarkerPath
        )
        $fitStarted = Test-ExactMarker -LiteralPath $fitMarkerPath
        if (Test-Path -LiteralPath $corePath -PathType Leaf) {
            $coreGuard = Open-ReadGuard -LiteralPath $corePath -StopCode 'STOP_RUNNER_EXIT'
            $guards.Add($coreGuard.Stream)
            $coreSha256 = $coreGuard.Sha256
        }
        if ($fitRun.ExitCode -ne 0) {
            $detail = [string]($fitRun.Output | Select-Object -First 1)
            if ($detail -cnotmatch '^STOP_[A-Z0-9_]+') { $detail = 'STOP_RUNNER_EXIT' }
            throw $detail
        }
        if (-not $fitStarted) { throw 'STOP_RUNNER_EXIT:fit_marker' }
        $runnerMessage = $fitRun.Output -join [char]10
        if ([string]::IsNullOrEmpty($coreSha256)) { throw 'STOP_RUNNER_EXIT:missing_core_receipt' }
    }
    else {
        $runnerMessage = $selfTestRun.Output -join [char]10
        $coreSha256 = $selfTestSha256
    }
    $status = 'PASS'
}
catch {
    $detail = $_.Exception.Message
    $stopCode = [string](($detail -split ':',2)[0])
}
finally {
    foreach ($threadName in $originalThreads.Keys) {
        try {
            [Environment]::SetEnvironmentVariable($threadName, $originalThreads[$threadName], 'Process')
        }
        catch {
            $environmentRestorePass = $false
            if ($status -ceq 'PASS' -or [string]::IsNullOrEmpty($stopCode)) {
                $status = 'STOP'
                $stopCode = 'STOP_ENVIRONMENT_RESTORE'
            }
        }
    }
    foreach ($guard in $guards) {
        try { $guard.Dispose() } catch { }
    }
    if (-not [string]::IsNullOrEmpty($temporaryRoot) -and (Test-Path -LiteralPath $temporaryRoot)) {
        try {
            $temporaryItem = Get-Item -LiteralPath $temporaryRoot -Force -ErrorAction Stop
            if (-not ($temporaryItem -is [IO.DirectoryInfo])) { throw 'STOP_TEMP_CLEANUP_SCOPE:not_directory' }
            Assert-NoReparsePath -Item $temporaryItem -StopCode 'STOP_TEMP_CLEANUP_SCOPE'
            $resolvedTemporaryRoot = $temporaryItem.FullName.TrimEnd([char]92,[char]47)
            $expectedTemporaryRoot = [IO.Path]::GetFullPath($temporaryRoot).TrimEnd([char]92,[char]47)
            $expectedTemporaryParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([char]92,[char]47)
            if (-not [string]::Equals($resolvedTemporaryRoot,$expectedTemporaryRoot,[StringComparison]::OrdinalIgnoreCase) -or
                -not [string]::Equals($temporaryItem.Parent.FullName.TrimEnd([char]92,[char]47),$expectedTemporaryParent,[StringComparison]::OrdinalIgnoreCase) -or
                $temporaryItem.Name -cnotmatch '^ce-loewenstein-prebuilt-r2-[0-9a-f]{32}$') {
                throw 'STOP_TEMP_CLEANUP_SCOPE:identity'
            }
            foreach ($leafName in @(
                'fit_loewenstein_2015_protrusion_v0_v2.exe',
                'self_test_core.json',
                'scientific_execution_lock.tsv',
                'dictionary.csv',
                'loewenstein_2015_spines.csv',
                'fit_started.marker'
            )) {
                $leafPath = Join-Path $resolvedTemporaryRoot $leafName
                if (-not (Test-Path -LiteralPath $leafPath)) { continue }
                $leafItem = Get-Item -LiteralPath $leafPath -Force -ErrorAction Stop
                if (-not ($leafItem -is [IO.FileInfo]) -or
                    ($leafItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
                    -not [string]::Equals($leafItem.Directory.FullName,$resolvedTemporaryRoot,[StringComparison]::OrdinalIgnoreCase)) {
                    throw ('STOP_TEMP_CLEANUP_SCOPE:leaf:' + $leafName)
                }
                Remove-Item -LiteralPath $leafItem.FullName -Force -ErrorAction Stop
                if (Test-Path -LiteralPath $leafItem.FullName) { throw ('STOP_TEMP_CLEANUP_SCOPE:leaf_remains:' + $leafName) }
            }
            if (@(Get-ChildItem -LiteralPath $resolvedTemporaryRoot -Force -ErrorAction Stop).Count -ne 0) {
                throw 'STOP_TEMP_CLEANUP_SCOPE:unexpected_content'
            }
            Remove-Item -LiteralPath $resolvedTemporaryRoot -Force -ErrorAction Stop
            if (Test-Path -LiteralPath $resolvedTemporaryRoot) { throw 'STOP_TEMP_CLEANUP_SCOPE:remains' }
        }
        catch {
            $cleanupPass = $false
            if ($status -ceq 'PASS' -or [string]::IsNullOrEmpty($stopCode)) {
                $status = 'STOP'
                $stopCode = 'STOP_TEMP_CLEANUP_SCOPE'
            }
        }
    }
    if ($outputReady -and $null -ne $controlStream) {
        $receipt = [ordered]@{
            schema_version = 'ce_npf_loewenstein_2015_prebuilt_r2_control_receipt_v2'
            status = $status
            stop_code = $stopCode
            mode = $Mode
            run_spec_sha256 = $runSpecSha256
            scientific_lock_sha256 = $scientificLockSha256
            finalization_manifest_sha256 = $finalizationManifestSha256
            user_authorization_receipt_sha256 = $userReceiptSha256
            enterprise_approval_receipt_sha256 = $enterpriseReceiptSha256
            run_id = $runId
            runner_sha256 = $runnerSha256
            runner_certificate_sha256 = $runnerCertificateSha256
            runner_pe_content_sha256 = $runnerPeContentSha256
            self_test_core_sha256 = $selfTestSha256
            core_receipt_sha256 = $coreSha256
            fit_started = $fitStarted
            data_opened = $dataOpened
            temporary_cleanup_pass = $cleanupPass
            environment_restore_pass = $environmentRestorePass
            control_receipt_commit_marker = 'execution_control_receipt.sha256'
            runner_message = $runnerMessage
            control_receipt_committed = $true
        }
        try {
            $receiptSha256 = Commit-ControlReceipt -Stream $controlStream -Value $receipt
            $controlStream.Dispose()
            $controlStream = $null
            Write-ControlCommitMarker -LiteralPath $controlCommitPath -ReceiptSha256 $receiptSha256
            $controlReceiptCommitted = $true
        }
        catch {
            if ($null -ne $controlStream) {
                try {
                    $controlStream.SetLength(0)
                    $controlStream.Flush($true)
                }
                catch { }
                try { $controlStream.Dispose() } catch { }
                $controlStream = $null
            }
            $status = 'STOP'
            $stopCode = 'STOP_CONTROL_RECEIPT_COMMIT'
        }
    }
}

if ($status -cne 'PASS' -or -not $controlReceiptCommitted) {
    if ([string]::IsNullOrEmpty($stopCode)) { $stopCode = 'STOP_UNKNOWN' }
    [Console]::Error.WriteLine($stopCode)
    exit 1
}

Write-Output $runnerMessage
