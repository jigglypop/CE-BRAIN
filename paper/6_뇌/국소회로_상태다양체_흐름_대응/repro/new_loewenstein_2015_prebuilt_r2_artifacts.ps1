[CmdletBinding()]
param(
    [ValidateSet('Candidate', 'ProposeFinal', 'Finalize')]
    [string]$Mode = 'Candidate',
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [string]$SignedRunnerPath = '',
    [string]$RunId = 'PENDING-RUN-ID',
    [string]$EnterprisePolicyId = '{0283ac0f-fff1-49ae-ada1-8a933130cad6}',
    [string]$UserAuthorizationReceiptPath = '',
    [string]$ExpectedUserAuthorizationReceiptSha256 = '',
    [string]$EnterpriseApprovalReceiptPath = '',
    [string]$ExpectedEnterpriseApprovalReceiptSha256 = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedParentContractSha256 = 'a7fbc541b07bc47806ccba4836647826d4b125b2b4ff265387817cf09e78a93e'
$expectedParentFalseLockSha256 = '70171ba144416788891cd0e77ff390062ce8035eccdba6aa5a5af876485bc126'
$expectedParentWrapperSha256 = 'fd9e5c4ff094111f29431049ba2d9d267894237b218395634d40ad63165e998c'
$expectedR2ExecutionContractSha256 = '0272500218d9dbd3a0eedbaf5444c088cadc7d58711645da92483f3aa3ea569c'
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
$expectedCandidateRelativePath = 'signing_payload/fit_loewenstein_2015_protrusion_v0_v2.exe'
$expectedCandidateSha256 = '47fd90048d28c7bdceb0654cae218759c0aea12b7ce5593f9d90a3a62ee03b4e'
$expectedCandidateBytes = 732672
$expectedBuildManifestSha256 = '27deaa7964f0705b6fb8735c066d45a0b596aa0cd612140d598e41172517ac6a'
$expectedEnterprisePolicyId = '{0283ac0f-fff1-49ae-ada1-8a933130cad6}'

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

$proposalDigestKeys = @(
    'schema_version',
    'materialized',
    'scientific_lock_sha256',
    'parent_false_lock_sha256',
    'real_data_fit_authorized',
    'comparison_contract_sha256',
    'wrapper_sha256'
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

function Get-BytesSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    $algorithm = [Security.Cryptography.SHA256]::Create()
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

function Assert-NoReparsePath {
    param(
        [Parameter(Mandatory = $true)][IO.FileSystemInfo]$Item,
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

function Open-ReadGuard {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    try { $item = Get-Item -LiteralPath $LiteralPath -Force -ErrorAction Stop }
    catch { throw ($StopCode + ':missing') }
    if ($null -eq $item) { throw ($StopCode + ':null_item:' + $LiteralPath) }
    if (-not ($item -is [IO.FileInfo])) { throw ($StopCode + ':not_regular_file:' + $item.GetType().FullName) }
    Assert-NoReparsePath -Item $item -StopCode $StopCode
    $stream = [IO.FileStream]::new($item.FullName,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        if ($stream.Length -gt [int]::MaxValue) { throw ($StopCode + ':too_large') }
        $bytes = [byte[]]::new([int]$stream.Length)
        $offset = 0
        while ($offset -lt $bytes.Length) {
            $read = $stream.Read($bytes,$offset,$bytes.Length-$offset)
            if ($read -le 0) { throw ($StopCode + ':short_read') }
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

function Read-StrictTsv {
    param(
        [Parameter(Mandatory = $true)]$Guard,
        [Parameter(Mandatory = $true)][string[]]$Keys,
        [Parameter(Mandatory = $true)][string]$ExpectedSchema,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    $bytes = [byte[]]$Guard.Bytes
    if (($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) -or
        [Array]::IndexOf($bytes,[byte]13) -ge 0) {
        throw ($StopCode + ':encoding')
    }
    try { $text = [Text.UTF8Encoding]::new($false,$true).GetString($bytes) }
    catch { throw ($StopCode + ':utf8') }
    if (-not $text.EndsWith("`n",[StringComparison]::Ordinal) -or
        $text.EndsWith("`n`n",[StringComparison]::Ordinal)) {
        throw ($StopCode + ':newline')
    }
    $lines = $text.Substring(0,$text.Length-1).Split([char]10)
    if ($lines.Count -ne $Keys.Count+1 -or $lines[0] -cne "key`tvalue") {
        throw ($StopCode + ':header_or_count')
    }
    $values = [ordered]@{}
    for ($index=0; $index -lt $Keys.Count; $index++) {
        $fields = $lines[$index+1].Split([char]9)
        if ($fields.Count -ne 2 -or $fields[0] -cne $Keys[$index] -or
            [string]::IsNullOrEmpty($fields[1]) -or
            $fields[1] -cmatch '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]' -or
            $values.Contains($fields[0])) {
            throw ($StopCode + ':row_' + ($index+2))
        }
        $values[$fields[0]] = $fields[1]
    }
    if ([string]$values['schema_version'] -cne $ExpectedSchema) {
        throw ($StopCode + ':schema')
    }
    return $values
}

function Assert-Value {
    param(
        [Parameter(Mandatory = $true)]$Values,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    if ([string]$Values[$Key] -cne $Expected) { throw ($StopCode + ':' + $Key) }
}

function Assert-NoPendingApprovalValue {
    param(
        [Parameter(Mandatory = $true)]$Values,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    foreach ($key in @('run_id','issuer')) {
        if ([string]$Values[$key] -cmatch '^PENDING(?:-|$)') {
            throw ($StopCode + ':' + $key)
        }
    }
}

function Assert-ReceiptTimeWindow {
    param(
        [Parameter(Mandatory = $true)]$Values,
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

function ConvertTo-StrictTsvBytes {
    param(
        [Parameter(Mandatory = $true)]$Values,
        [Parameter(Mandatory = $true)][string[]]$Keys
    )
    if ($Values.Count -ne $Keys.Count) { throw 'STOP_GENERATOR_SCHEMA:value_count' }
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add("key`tvalue")
    foreach ($key in $Keys) {
        if (-not $Values.Contains($key) -or $key -cnotmatch '^[a-z0-9_]+$') {
            throw ('STOP_GENERATOR_SCHEMA:' + $key)
        }
        $value = [string]$Values[$key]
        if ([string]::IsNullOrEmpty($value) -or $value -cmatch '[\x00-\x1f\x7f]') {
            throw ('STOP_GENERATOR_VALUE:' + $key)
        }
        $lines.Add($key + [char]9 + $value)
    }
    return [Text.UTF8Encoding]::new($false).GetBytes(($lines -join [char]10) + [char]10)
}

function Write-NewBytes {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][byte[]]$Bytes
    )
    $stream = [IO.FileStream]::new($LiteralPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {
        $stream.Write($Bytes,0,$Bytes.Length)
        $stream.Flush($true)
        $stream.Position = 0
        $observed = [byte[]]::new($Bytes.Length)
        $offset = 0
        while ($offset -lt $observed.Length) {
            $read = $stream.Read($observed,$offset,$observed.Length-$offset)
            if ($read -le 0) { throw 'STOP_GENERATOR_WRITE_VERIFY:short_read' }
            $offset += $read
        }
        if ((Get-BytesSha256 -Bytes $observed) -cne (Get-BytesSha256 -Bytes $Bytes)) {
            throw 'STOP_GENERATOR_WRITE_VERIFY:hash'
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Get-PeContentIdentity {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][bool]$RequireEmbeddedCertificate,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    if ($Bytes.Length -lt 256) { throw ($StopCode + ':pe_too_short') }
    $peOffset = [BitConverter]::ToInt32($Bytes,0x3c)
    if ($peOffset -lt 0 -or $peOffset+24 -ge $Bytes.Length -or
        $Bytes[$peOffset] -ne 0x50 -or $Bytes[$peOffset+1] -ne 0x45 -or
        $Bytes[$peOffset+2] -ne 0 -or $Bytes[$peOffset+3] -ne 0) {
        throw ($StopCode + ':pe_header')
    }
    $optionalOffset = $peOffset+24
    $magic = [BitConverter]::ToUInt16($Bytes,$optionalOffset)
    if ($magic -eq 0x20b) { $directoryOffset=$optionalOffset+112 }
    elseif ($magic -eq 0x10b) { $directoryOffset=$optionalOffset+96 }
    else { throw ($StopCode + ':pe_magic') }
    $checksumOffset=$optionalOffset+64
    $securityOffset=$directoryOffset+32
    if ($securityOffset+8 -gt $Bytes.Length) { throw ($StopCode + ':pe_bounds') }
    $certificateOffset=[BitConverter]::ToUInt32($Bytes,$securityOffset)
    $certificateSize=[BitConverter]::ToUInt32($Bytes,$securityOffset+4)
    if ($RequireEmbeddedCertificate) {
        if ($certificateOffset -eq 0 -or $certificateSize -lt 8 -or
            ($certificateOffset % 8) -ne 0 -or
            ([uint64]$certificateOffset+[uint64]$certificateSize) -ne [uint64]$Bytes.Length) {
            throw ($StopCode + ':embedded_certificate_table')
        }
        $contentLength=[int]$certificateOffset
    }
    else {
        if ($certificateOffset -ne 0 -or $certificateSize -ne 0) {
            throw ($StopCode + ':unexpected_certificate_table')
        }
        $contentLength=$Bytes.Length
    }
    $normalized=[byte[]]$Bytes.Clone()
    for($index=0;$index -lt 4;$index++){$normalized[$checksumOffset+$index]=0}
    for($index=0;$index -lt 8;$index++){$normalized[$securityOffset+$index]=0}
    $algorithm=[Security.Cryptography.SHA256]::Create()
    try {
        $sha256=([BitConverter]::ToString($algorithm.ComputeHash($normalized,0,$contentLength)) -replace '-','').ToLowerInvariant()
    }
    finally { $algorithm.Dispose() }
    return [pscustomobject]@{Sha256=$sha256;ContentLength=$contentLength}
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
$contractMatches = @(Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'paper') -Recurse -File `
    -Filter 'CE_NPF_LOEWENSTEIN_2015_PREBUILT_R2_*.md')
if ($contractMatches.Count -ne 1) { throw 'STOP_GENERATOR_INPUT:r2_contract_discovery' }
$contractPath = $contractMatches[0].FullName
$wrapperPath = Join-Path $PSScriptRoot 'run_loewenstein_2015_protrusion_v0_v2_prebuilt_r2.ps1'
$sourcePath = Join-Path $PSScriptRoot 'fit_loewenstein_2015_protrusion_v0_v2.rs'
$parentLockPath = Join-Path $PSScriptRoot 'loewenstein_2015_v0_v2_execution_lock.tsv'
$buildManifestPath = Join-Path $repositoryRoot 'artifacts/brain/ce_npf_loewenstein_2015_runner_signing_candidate_v1/build_manifest.tsv'

$guards = [Collections.Generic.List[IDisposable]]::new()
try {
    if ($RunId -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$') { throw 'STOP_GENERATOR_VALUE:run_id' }
    if ($EnterprisePolicyId -cne $expectedEnterprisePolicyId) { throw 'STOP_GENERATOR_VALUE:enterprise_policy_id' }
    $approvalArguments = @(
        $UserAuthorizationReceiptPath,
        $ExpectedUserAuthorizationReceiptSha256,
        $EnterpriseApprovalReceiptPath,
        $ExpectedEnterpriseApprovalReceiptSha256
    )
    if ($Mode -eq 'Candidate') {
        if (-not [string]::IsNullOrEmpty($SignedRunnerPath)) {
            throw 'STOP_GENERATOR_VALUE:signed_runner_forbidden_in_candidate'
        }
        foreach ($value in $approvalArguments) {
            if (-not [string]::IsNullOrEmpty($value)) { throw 'STOP_GENERATOR_VALUE:approval_forbidden' }
        }
    }
    else {
        if ([string]::IsNullOrEmpty($SignedRunnerPath)) { throw 'STOP_GENERATOR_VALUE:signed_runner_required' }
        if ($RunId -cmatch '^PENDING(?:-|$)') { throw 'STOP_GENERATOR_VALUE:run_id_pending' }
        if ($Mode -eq 'ProposeFinal') {
            foreach ($value in $approvalArguments) {
                if (-not [string]::IsNullOrEmpty($value)) { throw 'STOP_GENERATOR_VALUE:approval_forbidden_in_proposal' }
            }
        }
        else {
            foreach ($value in $approvalArguments) {
                if ([string]::IsNullOrEmpty($value)) { throw 'STOP_GENERATOR_VALUE:approval_required_for_finalize' }
            }
            if (-not (Test-LowerSha256 -Value $ExpectedUserAuthorizationReceiptSha256) -or
                -not (Test-LowerSha256 -Value $ExpectedEnterpriseApprovalReceiptSha256)) {
                throw 'STOP_GENERATOR_APPROVAL:expected_hash'
            }
            if ([string]::Equals(
                [IO.Path]::GetFullPath($UserAuthorizationReceiptPath),
                [IO.Path]::GetFullPath($EnterpriseApprovalReceiptPath),
                [StringComparison]::OrdinalIgnoreCase
            )) {
                throw 'STOP_GENERATOR_APPROVAL:path_alias'
            }
        }
    }

    $generatorGuard = Open-ReadGuard -LiteralPath $PSCommandPath -StopCode 'STOP_GENERATOR_INPUT'
    $guards.Add($generatorGuard.Stream)
    $contractGuard = Open-ReadGuard -LiteralPath $contractPath -StopCode 'STOP_GENERATOR_INPUT'
    $guards.Add($contractGuard.Stream)
    if ($contractGuard.Sha256 -cne $expectedR2ExecutionContractSha256) { throw 'STOP_GENERATOR_INPUT:r2_contract' }
    $wrapperGuard = Open-ReadGuard -LiteralPath $wrapperPath -StopCode 'STOP_GENERATOR_INPUT'
    $guards.Add($wrapperGuard.Stream)
    $sourceGuard = Open-ReadGuard -LiteralPath $sourcePath -StopCode 'STOP_GENERATOR_INPUT'
    $guards.Add($sourceGuard.Stream)
    if ($sourceGuard.Sha256 -cne $expectedRustSourceSha256) { throw 'STOP_GENERATOR_INPUT:rust_source' }
    $parentLockGuard = Open-ReadGuard -LiteralPath $parentLockPath -StopCode 'STOP_GENERATOR_INPUT'
    $guards.Add($parentLockGuard.Stream)
    if ($parentLockGuard.Sha256 -cne $expectedParentFalseLockSha256) { throw 'STOP_GENERATOR_INPUT:parent_lock' }
    $parentLock = Read-StrictTsv -Guard $parentLockGuard -Keys $scientificLockKeys `
        -ExpectedSchema 'ce_npf_loewenstein_2015_v0_v2_execution_lock_v1' -StopCode 'STOP_GENERATOR_INPUT'
    Assert-Value -Values $parentLock -Key 'real_data_fit_authorized' -Expected 'false' -StopCode 'STOP_GENERATOR_INPUT'
    Assert-Value -Values $parentLock -Key 'comparison_contract_sha256' -Expected $expectedParentContractSha256 -StopCode 'STOP_GENERATOR_INPUT'
    Assert-Value -Values $parentLock -Key 'wrapper_sha256' -Expected $expectedParentWrapperSha256 -StopCode 'STOP_GENERATOR_INPUT'

    $manifestGuard = Open-ReadGuard -LiteralPath $buildManifestPath -StopCode 'STOP_GENERATOR_INPUT'
    $guards.Add($manifestGuard.Stream)
    if ($manifestGuard.Sha256 -cne $expectedBuildManifestSha256) { throw 'STOP_GENERATOR_INPUT:build_manifest_hash' }
    $manifest = Read-StrictTsv -Guard $manifestGuard -Keys $buildManifestKeys `
        -ExpectedSchema 'ce_npf_loewenstein_2015_runner_signing_candidate_v1' -StopCode 'STOP_GENERATOR_INPUT'
    foreach($binding in @(
        @('status','UNSIGNED_SIGNING_CANDIDATE_NOT_EXECUTED'),
        @('candidate_relative_path',$expectedCandidateRelativePath),
        @('candidate_sha256',$expectedCandidateSha256),
        @('candidate_bytes',[string]$expectedCandidateBytes),
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
        Assert-Value -Values $manifest -Key $binding[0] -Expected $binding[1] -StopCode 'STOP_GENERATOR_INPUT'
    }
    $candidatePath = Join-Path (Split-Path -Parent $manifestGuard.Path) $expectedCandidateRelativePath
    $candidateGuard = Open-ReadGuard -LiteralPath $candidatePath -StopCode 'STOP_GENERATOR_INPUT'
    $guards.Add($candidateGuard.Stream)
    if ($candidateGuard.Sha256 -cne $expectedCandidateSha256 -or $candidateGuard.Length -ne $expectedCandidateBytes) {
        throw 'STOP_GENERATOR_INPUT:unsigned_candidate'
    }
    $candidatePe = Get-PeContentIdentity -Bytes $candidateGuard.Bytes -RequireEmbeddedCertificate $false -StopCode 'STOP_GENERATOR_INPUT'
    if ($candidatePe.Sha256 -cne $expectedCandidateSha256 -or
        [string](Get-AuthenticodeSignature -LiteralPath $candidateGuard.Path).Status -cne 'NotSigned') {
        throw 'STOP_GENERATOR_INPUT:unsigned_candidate_identity'
    }

    $runnerSha256 = $expectedCandidateSha256
    $runnerBytes = $expectedCandidateBytes
    $certificateSha256 = '0000000000000000000000000000000000000000000000000000000000000000'
    $executionReady = 'false'
    if ($Mode -ne 'Candidate') {
        $runnerGuard = Open-ReadGuard -LiteralPath $SignedRunnerPath -StopCode 'STOP_GENERATOR_SIGNED_RUNNER'
        $guards.Add($runnerGuard.Stream)
        $signature = Get-AuthenticodeSignature -LiteralPath $runnerGuard.Path
        if ([string]$signature.Status -cne 'Valid' -or
            [string]$signature.SignatureType -cne 'Authenticode' -or
            $null -eq $signature.SignerCertificate) {
            throw 'STOP_GENERATOR_SIGNED_RUNNER:signature'
        }
        $signedPe = Get-PeContentIdentity -Bytes $runnerGuard.Bytes -RequireEmbeddedCertificate $true -StopCode 'STOP_GENERATOR_SIGNED_RUNNER'
        if ($signedPe.Sha256 -cne $expectedCandidateSha256) { throw 'STOP_GENERATOR_SIGNED_RUNNER:lineage' }
        $runnerSha256 = $runnerGuard.Sha256
        $runnerBytes = $runnerGuard.Length
        $certificateSha256 = Get-BytesSha256 -Bytes ([byte[]]$signature.SignerCertificate.RawData)
        $executionReady = 'true'
    }

    $lockValues = [ordered]@{}
    foreach($key in $scientificLockKeys){$lockValues[$key]=[string]$parentLock[$key]}
    $lockValues['real_data_fit_authorized'] = if ($Mode -eq 'Candidate') { 'false' } else { 'true' }
    $lockValues['wrapper_sha256'] = $wrapperGuard.Sha256
    $lockBytes = ConvertTo-StrictTsvBytes -Values $lockValues -Keys $scientificLockKeys
    $lockSha256 = Get-BytesSha256 -Bytes $lockBytes

    $runValues = [ordered]@{
        schema_version = 'ce_npf_loewenstein_2015_prebuilt_run_spec_r2'
        execution_ready = $executionReady
        parent_contract_sha256 = $expectedParentContractSha256
        parent_false_lock_sha256 = $expectedParentFalseLockSha256
        r2_execution_contract_sha256 = $contractGuard.Sha256
        r2_wrapper_sha256 = $wrapperGuard.Sha256
        artifact_generator_sha256 = $generatorGuard.Sha256
        rust_source_sha256 = $expectedRustSourceSha256
        scientific_execution_lock_sha256 = $lockSha256
        pre_sign_payload_sha256 = $expectedCandidateSha256
        signed_runner_sha256 = $runnerSha256
        signed_runner_bytes = [string]$runnerBytes
        signature_mode = 'authenticode'
        signer_certificate_sha256 = $certificateSha256
        enterprise_policy_id = $expectedEnterprisePolicyId
        build_manifest_sha256 = $manifestGuard.Sha256
        expected_self_test_core_sha256 = $expectedSelfTestCoreSha256
        rustc_version = $expectedBuildRustcVersion
        rustc_host = $expectedBuildRustcHost
        rustc_executable_sha256 = $expectedRustcExecutableSha256
        scientific_compile_flags = $expectedScientificCompileFlags
        packaging_link_flags = $expectedPackagingLinkFlags
        runtime_threads = '1'
        model_semantics_id = $expectedModelSemantics
        decision_scope = $expectedDecisionScope
        claim_ceiling = $expectedClaimCeiling
    }
    $runBytes = ConvertTo-StrictTsvBytes -Values $runValues -Keys $runSpecKeys
    $runSha256 = Get-BytesSha256 -Bytes $runBytes

    $proposalValues = [ordered]@{
        schema_version = 'ce_npf_loewenstein_2015_scientific_lock_digest_r2'
        materialized = 'false'
        scientific_lock_sha256 = $lockSha256
        parent_false_lock_sha256 = $expectedParentFalseLockSha256
        real_data_fit_authorized = [string]$lockValues['real_data_fit_authorized']
        comparison_contract_sha256 = [string]$lockValues['comparison_contract_sha256']
        wrapper_sha256 = [string]$lockValues['wrapper_sha256']
    }
    $proposalBytes = ConvertTo-StrictTsvBytes -Values $proposalValues -Keys $proposalDigestKeys
    $proposalSha256 = Get-BytesSha256 -Bytes $proposalBytes

    $userBytes = $null
    $enterpriseBytes = $null
    $userArtifactSha256 = ''
    $enterpriseArtifactSha256 = ''
    $approvalsVerified = $false
    if ($Mode -ne 'Finalize') {
        $userValues = [ordered]@{
            schema_version = 'ce_npf_loewenstein_2015_user_fit_authorization_r2'
            decision = 'PENDING'
            run_spec_sha256 = $runSha256
            scope = $expectedUserScope
            decision_scope = $expectedDecisionScope
            claim_ceiling = $expectedClaimCeiling
            run_id = $RunId
            issuer = 'PENDING'
            issued_at_utc = 'PENDING'
            expires_at_utc = 'PENDING'
        }
        $userBytes = ConvertTo-StrictTsvBytes -Values $userValues -Keys $userReceiptKeys
        $userArtifactSha256 = Get-BytesSha256 -Bytes $userBytes
        $enterpriseValues = [ordered]@{
            schema_version = 'ce_npf_loewenstein_2015_enterprise_execution_approval_r2'
            decision = 'PENDING'
            run_spec_sha256 = $runSha256
            signed_runner_sha256 = $runnerSha256
            signature_mode = 'authenticode'
            signer_certificate_sha256 = $certificateSha256
            enterprise_policy_id = $expectedEnterprisePolicyId
            allowed_host = [Environment]::MachineName
            allowed_architecture = $expectedBuildRustcHost
            run_id = $RunId
            issuer = 'PENDING'
            issued_at_utc = 'PENDING'
            expires_at_utc = 'PENDING'
        }
        $enterpriseBytes = ConvertTo-StrictTsvBytes -Values $enterpriseValues -Keys $enterpriseReceiptKeys
        $enterpriseArtifactSha256 = Get-BytesSha256 -Bytes $enterpriseBytes
    }
    else {
        $userGuard = Open-ReadGuard -LiteralPath $UserAuthorizationReceiptPath -StopCode 'STOP_GENERATOR_APPROVAL'
        $guards.Add($userGuard.Stream)
        if ($userGuard.Sha256 -cne $ExpectedUserAuthorizationReceiptSha256) { throw 'STOP_GENERATOR_APPROVAL:user_hash' }
        $userValues = Read-StrictTsv -Guard $userGuard -Keys $userReceiptKeys `
            -ExpectedSchema 'ce_npf_loewenstein_2015_user_fit_authorization_r2' -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $userValues -Key 'decision' -Expected 'AUTHORIZE' -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-NoPendingApprovalValue -Values $userValues -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $userValues -Key 'run_spec_sha256' -Expected $runSha256 -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $userValues -Key 'scope' -Expected $expectedUserScope -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $userValues -Key 'decision_scope' -Expected $expectedDecisionScope -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $userValues -Key 'claim_ceiling' -Expected $expectedClaimCeiling -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $userValues -Key 'run_id' -Expected $RunId -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-ReceiptTimeWindow -Values $userValues -StopCode 'STOP_GENERATOR_APPROVAL'

        $enterpriseGuard = Open-ReadGuard -LiteralPath $EnterpriseApprovalReceiptPath -StopCode 'STOP_GENERATOR_APPROVAL'
        $guards.Add($enterpriseGuard.Stream)
        if ($enterpriseGuard.Sha256 -cne $ExpectedEnterpriseApprovalReceiptSha256) { throw 'STOP_GENERATOR_APPROVAL:enterprise_hash' }
        $enterpriseValues = Read-StrictTsv -Guard $enterpriseGuard -Keys $enterpriseReceiptKeys `
            -ExpectedSchema 'ce_npf_loewenstein_2015_enterprise_execution_approval_r2' -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'decision' -Expected 'APPROVE_EXECUTION' -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-NoPendingApprovalValue -Values $enterpriseValues -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'run_spec_sha256' -Expected $runSha256 -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'signed_runner_sha256' -Expected $runnerSha256 -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'signature_mode' -Expected 'authenticode' -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'signer_certificate_sha256' -Expected $certificateSha256 -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'enterprise_policy_id' -Expected $expectedEnterprisePolicyId -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'allowed_host' -Expected ([Environment]::MachineName) -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'allowed_architecture' -Expected $expectedBuildRustcHost -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-Value -Values $enterpriseValues -Key 'run_id' -Expected $RunId -StopCode 'STOP_GENERATOR_APPROVAL'
        Assert-ReceiptTimeWindow -Values $enterpriseValues -StopCode 'STOP_GENERATOR_APPROVAL'
        $userBytes = [byte[]]$userGuard.Bytes
        $enterpriseBytes = [byte[]]$enterpriseGuard.Bytes
        $userArtifactSha256 = $userGuard.Sha256
        $enterpriseArtifactSha256 = $enterpriseGuard.Sha256
        $approvalsVerified = $true
    }

    $fullOutput = [IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $fullOutput) { throw 'STOP_GENERATOR_OUTPUT_EXISTS' }
    $outputParent = Get-Item -LiteralPath (Split-Path -Parent $fullOutput) -Force -ErrorAction Stop
    if (-not ($outputParent -is [IO.DirectoryInfo])) { throw 'STOP_GENERATOR_OUTPUT_PARENT' }
    Assert-NoReparsePath -Item $outputParent -StopCode 'STOP_GENERATOR_OUTPUT_PARENT'
    $outputItem = New-Item -ItemType Directory -Path $fullOutput -ErrorAction Stop
    Assert-NoReparsePath -Item $outputItem -StopCode 'STOP_GENERATOR_OUTPUT'

    $lockMaterialized = $false
    if ($Mode -eq 'Candidate') {
        $lockPath = Join-Path $fullOutput 'loewenstein_2015_v0_v2_scientific_lock_r2_candidate.tsv'
        $runPath = Join-Path $fullOutput 'loewenstein_2015_prebuilt_run_spec_r2_candidate.tsv'
        $userPath = Join-Path $fullOutput 'loewenstein_2015_user_authorization_r2_candidate.tsv'
        $enterprisePath = Join-Path $fullOutput 'loewenstein_2015_enterprise_approval_r2_candidate.tsv'
        Write-NewBytes -LiteralPath $lockPath -Bytes $lockBytes
        $lockMaterialized = $true
        Write-NewBytes -LiteralPath $runPath -Bytes $runBytes
        Write-NewBytes -LiteralPath $userPath -Bytes $userBytes
        Write-NewBytes -LiteralPath $enterprisePath -Bytes $enterpriseBytes
        $receiptStatus = 'PASS_CANDIDATE_NOT_EXECUTABLE'
    }
    elseif ($Mode -eq 'ProposeFinal') {
        $proposalPath = Join-Path $fullOutput 'loewenstein_2015_v0_v2_scientific_lock_r2_ready_proposal_digest.tsv'
        $runPath = Join-Path $fullOutput 'loewenstein_2015_prebuilt_run_spec_r2_ready_proposal.tsv'
        $userPath = Join-Path $fullOutput 'loewenstein_2015_user_authorization_r2_ready_proposal.tsv'
        $enterprisePath = Join-Path $fullOutput 'loewenstein_2015_enterprise_approval_r2_ready_proposal.tsv'
        Write-NewBytes -LiteralPath $proposalPath -Bytes $proposalBytes
        Write-NewBytes -LiteralPath $runPath -Bytes $runBytes
        Write-NewBytes -LiteralPath $userPath -Bytes $userBytes
        Write-NewBytes -LiteralPath $enterprisePath -Bytes $enterpriseBytes
        $receiptStatus = 'PASS_READY_PROPOSAL_PENDING_EXTERNAL_APPROVALS'
    }
    else {
        $runPath = Join-Path $fullOutput 'loewenstein_2015_prebuilt_run_spec_r2_final.tsv'
        $userPath = Join-Path $fullOutput 'loewenstein_2015_user_authorization_r2_verified.tsv'
        $enterprisePath = Join-Path $fullOutput 'loewenstein_2015_enterprise_approval_r2_verified.tsv'
        $manifestPath = Join-Path $fullOutput 'loewenstein_2015_prebuilt_r2_finalization_manifest.tsv'
        $lockPath = Join-Path $fullOutput 'loewenstein_2015_v0_v2_scientific_lock_r2_final.tsv'
        $finalizationValues = [ordered]@{
            schema_version = 'ce_npf_loewenstein_2015_prebuilt_r2_finalization_manifest_v1'
            status = 'APPROVALS_VERIFIED_LOCK_MATERIALIZATION_AUTHORIZED'
            run_id = $RunId
            artifact_generator_sha256 = $generatorGuard.Sha256
            r2_execution_contract_sha256 = $contractGuard.Sha256
            r2_wrapper_sha256 = $wrapperGuard.Sha256
            run_spec_sha256 = $runSha256
            scientific_execution_lock_sha256 = $lockSha256
            user_authorization_receipt_sha256 = $userArtifactSha256
            enterprise_approval_receipt_sha256 = $enterpriseArtifactSha256
            signed_runner_sha256 = $runnerSha256
            signer_certificate_sha256 = $certificateSha256
            enterprise_policy_id = $expectedEnterprisePolicyId
            scientific_lock_materialization_authorized = 'true'
            scientific_lock_must_be_last = 'true'
            data_opened = 'false'
            runner_executed = 'false'
        }
        $finalizationBytes = ConvertTo-StrictTsvBytes -Values $finalizationValues -Keys $finalizationManifestKeys
        Write-NewBytes -LiteralPath $runPath -Bytes $runBytes
        Write-NewBytes -LiteralPath $userPath -Bytes $userBytes
        Write-NewBytes -LiteralPath $enterprisePath -Bytes $enterpriseBytes
        Write-NewBytes -LiteralPath $manifestPath -Bytes $finalizationBytes
        Write-NewBytes -LiteralPath $lockPath -Bytes $lockBytes
        $lockMaterialized = $true
        $receiptStatus = 'PASS_APPROVALS_VERIFIED_LOCK_MATERIALIZED'
    }

    [ordered]@{
        schema_version = 'ce_npf_loewenstein_2015_prebuilt_r2_generator_receipt_v2'
        status = $receiptStatus
        mode = $Mode
        execution_ready = $executionReady
        scientific_lock_authorized = [string]$lockValues['real_data_fit_authorized']
        scientific_lock_materialized = $lockMaterialized
        scientific_lock_sha256 = $lockSha256
        proposal_digest_sha256 = $proposalSha256
        run_spec_sha256 = $runSha256
        user_artifact_sha256 = $userArtifactSha256
        enterprise_artifact_sha256 = $enterpriseArtifactSha256
        runner_sha256 = $runnerSha256
        signer_certificate_sha256 = $certificateSha256
        data_opened = $false
        runner_executed = $false
        approvals_verified = $approvalsVerified
    } | ConvertTo-Json -Compress
}
finally {
    foreach($guard in $guards){try{$guard.Dispose()}catch{}}
}
