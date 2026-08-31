[CmdletBinding()]
param(
    [ValidateSet('SelfTest', 'Fit')]
    [string]$Mode = 'SelfTest',
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [string]$DataPath = '',
    [string]$DictionaryPath = '',
    [string]$ExecutionLockPath = '',
    [string]$ExpectedExecutionLockSha256 = '',
    [string]$ComparisonContractPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedRustcVersion = 'rustc 1.95.0 (59807616e 2026-04-14)'
$expectedRustcHost = 'x86_64-pc-windows-msvc'
$expectedCompileFlags = '--edition=2021 -C opt-level=3 -C debuginfo=0 -C overflow-checks=yes -C target-feature=-fma -C codegen-units=1'
$expectedDataSha256 = '2f6343606f62abb07b82491a71f0e4a4a898923d2bcf86aa4be8d596276d0062'
$expectedDataBytes = '569938'
$expectedDictionarySha256 = '995bdb601f6ff71cd5877486dfdd0576db576c15effcc8c52db560eb523d9657'
$expectedDictionaryBytes = '4850'
$expectedSourceManifestSha256 = '8209a09886b9322a02308f1dceff8d3805462c715135f79e28e1ab1e166b0630'
$expectedPreflightAuditorSha256 = 'a1b68ad6820055ba305058d7b5f646626df2842dd628a2401a95f785b4f600cc'
$expectedPreflightReceiptSha256 = '2ce71a85cd25c5da3d26c74f14aeb6c2d23daafa7fe3485b77567ddce619f517'
$expectedRowsetSha256 = '127bf184fe88cd04c727f39c719e7ee0931c6bd1264338bb1b9b30dfff38fcd4'
$expectedModelFeatureOrder = 'V0:intercept;V1:intercept,age_4d,age_8d,age_12d;V1Z:intercept,age_4d,age_8d,age_12d,z_offset_standardized;V2:intercept,age_4d,age_8d,age_12d,z_offset_standardized,log_intensity_standardized,shape_standardized,log_distance_standardized'
$expectedToleranceProfile = 'mode_score=1e-10;mode_step=1e-10;mode_iters=50;optimizer_internal_gradient=1e-8;optimizer_gate_gradient=1e-6;optimizer_iters=400;optimizer_evals=5000;armijo=1e-4;line_shrink=0.5;multistart_objective=1e-8;boundary_gain=1e-8;parameter_order=1e-3;cv_order=1e-5;cell_quadrature=1e-6;hessian_condition=1e10;beta_guard=20;sigma=[1e-6,10];sign_zero=1e-12;gain_epsilon=ln1.01;cell_guard=ln1.05;synthetic=C2015.21'
$lockKeys = @(
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

function Get-LowerSha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $LiteralPath).Hash.ToLowerInvariant()
}

function Get-BytesSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $algorithm.ComputeHash($Bytes)
        return ([System.BitConverter]::ToString($hash) -replace '-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
}

function Read-ExactBytes {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$ReadStopCode
    )
    try {
        $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    }
    catch {
        throw ($ReadStopCode + ':read')
    }
    return [pscustomobject]@{
        Bytes = [byte[]]$bytes
        Sha256 = Get-BytesSha256 -Bytes $bytes
        Length = $bytes.Length
    }
}

function New-GuardedSnapshot {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][byte[]]$Bytes
    )
    $stream = [System.IO.FileStream]::new(
        $LiteralPath,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::Read
    )
    try {
        $stream.Write($Bytes, 0, $Bytes.Length)
        $stream.Flush($true)
        $stream.Position = 0
        return $stream
    }
    catch {
        $stream.Dispose()
        throw
    }
}

function Open-HashedReadGuard {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$StopCode
    )
    $stream = $null
    try {
        $item = Get-Item -LiteralPath $LiteralPath -Force
        if ($item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'not_regular_file'
        }
        $stream = [System.IO.FileStream]::new(
            $item.FullName,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read
        )
    }
    catch {
        if ($null -ne $stream) {
            $stream.Dispose()
        }
        throw ($StopCode + ':guard_open')
    }
    try {
        $algorithm = [System.Security.Cryptography.SHA256]::Create()
        try {
            $stream.Position = 0
            $hash = $algorithm.ComputeHash($stream)
            $stream.Position = 0
        }
        finally {
            $algorithm.Dispose()
        }
        return [pscustomobject]@{
            Path = $item.FullName
            Stream = $stream
            Sha256 = ([System.BitConverter]::ToString($hash) -replace '-', '').ToLowerInvariant()
            Length = $stream.Length
        }
    }
    catch {
        $stream.Dispose()
        throw ($StopCode + ':guard_hash')
    }
}

function Test-ExactFitStartMarker {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) {
        return $false
    }
    $snapshot = Read-ExactBytes -LiteralPath $LiteralPath -ReadStopCode 'STOP_RUNNER_EXIT:fit_marker'
    $encoding = [System.Text.UTF8Encoding]::new($false)
    $expectedBytes = $encoding.GetBytes("ce_npf_loewenstein_2015_fit_started_v1`n")
    $expectedHash = Get-BytesSha256 -Bytes $expectedBytes
    if ($snapshot.Length -ne $expectedBytes.Length -or $snapshot.Sha256 -cne $expectedHash) {
        throw 'STOP_RUNNER_EXIT:fit_marker:expected=exact_committed_marker:observed=invalid_marker_bytes'
    }
    return $true
}

function Write-NewUtf8 {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$Text
    )
    $encoding = [System.Text.UTF8Encoding]::new($false)
    $stream = [System.IO.FileStream]::new(
        $LiteralPath,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $writer = [System.IO.StreamWriter]::new($stream, $encoding)
        try {
            $writer.Write($Text)
            $writer.Flush()
            $stream.Flush($true)
        }
        finally {
            $writer.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function ConvertTo-JsonString {
    param([AllowEmptyString()][string]$Value)
    return ConvertTo-Json -InputObject $Value -Compress
}

function Get-StopReceiptText {
    param(
        [Parameter(Mandatory = $true)][string]$Detail,
        [Parameter(Mandatory = $true)][bool]$FitStarted
    )
    $stopCode = ($Detail -split ':', 2)[0]
    if ($stopCode -cnotmatch '^STOP_[A-Z0-9_]+$') {
        $stopCode = 'STOP_WRAPPER_FAILURE'
    }
    if ($stopCode -ceq 'STOP_REAL_DATA_NOT_AUTHORIZED') {
        $expected = 'real_data_fit_authorized=true'
        $observed = 'real_data_fit_authorized=false'
    }
    elseif (
        $Detail.IndexOf(':expected=', [System.StringComparison]::Ordinal) -ge 0 -and
        $Detail.LastIndexOf(':observed=', [System.StringComparison]::Ordinal) -gt
            $Detail.IndexOf(':expected=', [System.StringComparison]::Ordinal)
    ) {
        $expectedMarker = ':expected='
        $observedMarker = ':observed='
        $expectedStart = $Detail.IndexOf($expectedMarker, [System.StringComparison]::Ordinal) + $expectedMarker.Length
        $observedStart = $Detail.LastIndexOf($observedMarker, [System.StringComparison]::Ordinal)
        $expected = $Detail.Substring($expectedStart, $observedStart - $expectedStart)
        $observed = $Detail.Substring($observedStart + $observedMarker.Length)
    }
    else {
        $expected = 'all_locked_gates_pass'
        $observed = $stopCode
    }
    $lf = [char]10
    return (
        '{' + $lf +
        '  "schema_version":"ce_npf_loewenstein_2015_v0_v2_stop_receipt_v1",' + $lf +
        '  "stop_code":' + (ConvertTo-JsonString -Value $stopCode) + ',' + $lf +
        '  "expected":' + (ConvertTo-JsonString -Value $expected) + ',' + $lf +
        '  "observed":' + (ConvertTo-JsonString -Value $observed) + ',' + $lf +
        '  "fit_started":' + $FitStarted.ToString().ToLowerInvariant() + $lf +
        '}' + $lf
    )
}

function Read-StrictLock {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256
    )
    if ($ExpectedSha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'STOP_EXECUTION_CONTRACT_HASH_MISMATCH:expected_sha_format'
    }
    $snapshot = Read-ExactBytes -LiteralPath $LiteralPath -ReadStopCode 'STOP_EXECUTION_CONTRACT_HASH_MISMATCH:lock'
    $observedHash = $snapshot.Sha256
    if ($observedHash -cne $ExpectedSha256) {
        throw ('STOP_EXECUTION_CONTRACT_HASH_MISMATCH:expected={0}:observed={1}' -f $ExpectedSha256, $observedHash)
    }
    $bytes = $snapshot.Bytes
    if (
        ($bytes.Length -ge 3 -and $bytes[0] -eq 0xef -and $bytes[1] -eq 0xbb -and $bytes[2] -eq 0xbf) -or
        ($bytes -contains 13) -or
        $bytes.Length -eq 0 -or
        $bytes[$bytes.Length - 1] -ne 10 -or
        ($bytes.Length -ge 2 -and $bytes[$bytes.Length - 2] -eq 10)
    ) {
        throw 'STOP_CONTRACT_SCHEMA_MISMATCH:encoding_or_newline'
    }
    $utf8 = [System.Text.UTF8Encoding]::new($false, $true)
    try {
        $text = $utf8.GetString($bytes)
    }
    catch {
        throw 'STOP_CONTRACT_SCHEMA_MISMATCH:utf8'
    }
    $lines = $text.Substring(0, $text.Length - 1).Split([char]10)
    $expectedHeader = 'key' + [char]9 + 'value'
    if ($lines.Count -ne ($lockKeys.Count + 1) -or $lines[0] -cne $expectedHeader) {
        throw 'STOP_CONTRACT_SCHEMA_MISMATCH:header_or_row_count'
    }
    $values = [ordered]@{}
    for ($index = 0; $index -lt $lockKeys.Count; $index += 1) {
        $fields = $lines[$index + 1].Split([char]9)
        if (
            $fields.Count -ne 2 -or
            $fields[0] -cne $lockKeys[$index] -or
            [string]::IsNullOrEmpty($fields[1]) -or
            $values.Contains($fields[0])
        ) {
            throw ('STOP_CONTRACT_SCHEMA_MISMATCH:row={0}:expected={1}' -f ($index + 2), $lockKeys[$index])
        }
        $values[$fields[0]] = $fields[1]
    }
    return [pscustomobject]@{
        Bytes = [byte[]]$bytes
        Sha256 = $observedHash
        Values = $values
    }
}

function Assert-LockValue {
    param(
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Lock,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Expected
    )
    if ([string]$Lock[$Key] -cne $Expected) {
        throw ('STOP_CONTRACT_SCHEMA_MISMATCH:{0}:expected={1}:observed={2}' -f $Key, $Expected, [string]$Lock[$Key])
    }
}

function Assert-LowerShaValue {
    param(
        [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Lock,
        [Parameter(Mandatory = $true)][string]$Key
    )
    if ([string]$Lock[$Key] -cnotmatch '^[0-9a-f]{64}$') {
        throw ('STOP_CONTRACT_SCHEMA_MISMATCH:{0}:sha256' -f $Key)
    }
}

function Assert-Hash {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )
    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) {
        throw ($Context + ':missing')
    }
    $observed = Get-LowerSha256 -LiteralPath $LiteralPath
    if ($observed -cne $Expected) {
        throw ('{0}:expected={1}:observed={2}' -f $Context, $Expected, $observed)
    }
}

function Get-RustcIdentity {
    param([Parameter(Mandatory = $true)][string]$RustcPath)
    $versionLines = @(& $RustcPath -V)
    if ($LASTEXITCODE -ne 0 -or $versionLines.Count -ne 1) {
        throw 'STOP_TOOLCHAIN_MISMATCH:rustc_version_command'
    }
    $verboseLines = @(& $RustcPath -Vv)
    if ($LASTEXITCODE -ne 0 -or $verboseLines.Count -eq 0) {
        throw 'STOP_TOOLCHAIN_MISMATCH:rustc_verbose_command'
    }
    $hostLines = @($verboseLines | Where-Object { $_ -cmatch '^host: ' })
    if ($hostLines.Count -ne 1) {
        throw 'STOP_TOOLCHAIN_MISMATCH:rustc_host_line'
    }
    $canonicalText = ($verboseLines -join [char]10) + [char]10
    $encoding = [System.Text.UTF8Encoding]::new($false)
    $canonicalBytes = $encoding.GetBytes($canonicalText)
    return [pscustomobject]@{
        version = [string]$versionLines[0]
        verbose_sha256 = Get-BytesSha256 -Bytes $canonicalBytes
        verbose_bytes = $canonicalBytes.Length
        host = ([string]$hostLines[0]).Substring(6)
    }
}

$sourcePath = Join-Path $PSScriptRoot 'fit_loewenstein_2015_protrusion_v0_v2.rs'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
$sourceManifestPath = Join-Path $PSScriptRoot 'loewenstein_2015_spine_source_lock.tsv'
$preflightAuditorPath = Join-Path $PSScriptRoot 'audit_loewenstein_2015_spine_preflight.ps1'
$preflightReceiptPath = Join-Path $repositoryRoot 'artifacts/brain/ce_npf_loewenstein_spine_preflight_v1/receipt.json'

if (-not (Test-Path -LiteralPath $OutputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}
$resolvedOutput = (Resolve-Path -LiteralPath $OutputDirectory).Path
$coreName = if ($Mode -eq 'SelfTest') { 'self_test_core.json' } else { 'core_receipt.json' }
$corePath = Join-Path $resolvedOutput $coreName
$environmentPath = Join-Path $resolvedOutput 'environment_receipt.json'
foreach ($candidate in @($corePath, $environmentPath)) {
    if (Test-Path -LiteralPath $candidate) {
        throw ('STOP_OUTPUT_EXISTS:{0}' -f $candidate)
    }
}

$status = 'STOP'
$firstErrorDetail = ''
$runnerMessage = ''
$binarySha256 = ''
$coreSha256 = ''
$rustcVersion = ''
$rustcVerboseSha256 = ''
$rustcVerboseBytes = 0
$rustcHost = ''
$rustcSha256 = ''
$rustSourceSha256 = ''
$wrapperSha256 = ''
$resolvedTaskTemp = ''
$cleanupPass = $true
$fitStarted = $false
$lockSnapshot = $null
$sourceSnapshot = $null
$wrapperSnapshot = $null
$sourceGuard = $null
$lockGuard = $null
$rustcGuard = $null
$binaryGuard = $null
$verifiedSourcePath = ''
$verifiedLockPath = ''
$fitStartedMarkerPath = ''
$originalThreadEnvironment = [ordered]@{
    RAYON_NUM_THREADS = [Environment]::GetEnvironmentVariable('RAYON_NUM_THREADS', 'Process')
    OMP_NUM_THREADS = [Environment]::GetEnvironmentVariable('OMP_NUM_THREADS', 'Process')
    OPENBLAS_NUM_THREADS = [Environment]::GetEnvironmentVariable('OPENBLAS_NUM_THREADS', 'Process')
    MKL_NUM_THREADS = [Environment]::GetEnvironmentVariable('MKL_NUM_THREADS', 'Process')
}

try {
    if ($Mode -eq 'SelfTest') {
        if (-not [string]::IsNullOrEmpty($DataPath) -or -not [string]::IsNullOrEmpty($DictionaryPath)) {
            throw 'STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST'
        }
    }
    else {
        foreach ($required in @($ExecutionLockPath, $ExpectedExecutionLockSha256)) {
            if ([string]::IsNullOrEmpty($required)) {
                throw 'STOP_CONTRACT_SCHEMA_MISMATCH:missing_lock_argument'
            }
        }
    }

    $lock = $null
    if ($Mode -eq 'Fit') {
        $lockSnapshot = Read-StrictLock -LiteralPath $ExecutionLockPath -ExpectedSha256 $ExpectedExecutionLockSha256
        $lock = $lockSnapshot.Values
        Assert-LockValue -Lock $lock -Key 'schema_version' -Expected 'ce_npf_loewenstein_2015_v0_v2_execution_lock_v1'
        Assert-LockValue -Lock $lock -Key 'source_manifest_sha256' -Expected $expectedSourceManifestSha256
        Assert-LockValue -Lock $lock -Key 'preflight_auditor_sha256' -Expected $expectedPreflightAuditorSha256
        Assert-LockValue -Lock $lock -Key 'preflight_receipt_sha256' -Expected $expectedPreflightReceiptSha256
        Assert-LockValue -Lock $lock -Key 'preflight_decision' -Expected 'PARTIAL_MODEL_ELIGIBILITY'
        Assert-LockValue -Lock $lock -Key 'raw_csv_sha256' -Expected $expectedDataSha256
        Assert-LockValue -Lock $lock -Key 'raw_csv_bytes' -Expected $expectedDataBytes
        Assert-LockValue -Lock $lock -Key 'dictionary_sha256' -Expected $expectedDictionarySha256
        Assert-LockValue -Lock $lock -Key 'dictionary_bytes' -Expected $expectedDictionaryBytes
        Assert-LockValue -Lock $lock -Key 'rowset_sha256' -Expected $expectedRowsetSha256
        Assert-LockValue -Lock $lock -Key 'comparison_rows' -Expected '2723'
        Assert-LockValue -Lock $lock -Key 'comparison_events' -Expected '1459'
        Assert-LockValue -Lock $lock -Key 'age_rows' -Expected '1861,557,219,86'
        Assert-LockValue -Lock $lock -Key 'age_events' -Expected '1122,249,66,22'
        Assert-LockValue -Lock $lock -Key 'cell_rows' -Expected '529,151,404,433,419,401,353,33'
        Assert-LockValue -Lock $lock -Key 'cell_events' -Expected '321,72,201,231,229,202,185,18'
        Assert-LockValue -Lock $lock -Key 'model_feature_order' -Expected $expectedModelFeatureOrder
        Assert-LockValue -Lock $lock -Key 'numerical_tolerance_profile' -Expected $expectedToleranceProfile
        Assert-LockValue -Lock $lock -Key 'rustc_version' -Expected $expectedRustcVersion
        Assert-LockValue -Lock $lock -Key 'rustc_host' -Expected $expectedRustcHost
        Assert-LockValue -Lock $lock -Key 'compile_flags' -Expected $expectedCompileFlags
        Assert-LockValue -Lock $lock -Key 'runtime_threads' -Expected '1'
        foreach ($shaKey in @('comparison_contract_sha256', 'rust_source_sha256', 'wrapper_sha256', 'self_test_core_sha256', 'rustc_verbose_sha256', 'rustc_executable_sha256')) {
            Assert-LowerShaValue -Lock $lock -Key $shaKey
        }
        if ([string]$lock['real_data_fit_authorized'] -cnotin @('true', 'false')) {
            throw 'STOP_CONTRACT_SCHEMA_MISMATCH:authorization_boolean'
        }
        if ([string]$lock['real_data_fit_authorized'] -cne 'true') {
            throw 'STOP_REAL_DATA_NOT_AUTHORIZED:execution_lock_false'
        }
        foreach ($required in @($DataPath, $DictionaryPath, $ComparisonContractPath)) {
            if ([string]::IsNullOrEmpty($required)) {
                throw 'STOP_CONTRACT_SCHEMA_MISMATCH:missing_fit_argument_after_authorization'
            }
        }
    }

    $sourceSnapshot = Read-ExactBytes -LiteralPath $sourcePath -ReadStopCode 'STOP_IMPLEMENTATION_HASH_MISMATCH:rust_source'
    $wrapperSnapshot = Read-ExactBytes -LiteralPath $PSCommandPath -ReadStopCode 'STOP_IMPLEMENTATION_HASH_MISMATCH:wrapper'
    $rustSourceSha256 = $sourceSnapshot.Sha256
    $wrapperSha256 = $wrapperSnapshot.Sha256

    $rustcDiscoveredPath = (Get-Command rustc -CommandType Application -ErrorAction Stop).Source
    $rustcGuard = Open-HashedReadGuard -LiteralPath $rustcDiscoveredPath -StopCode 'STOP_TOOLCHAIN_MISMATCH:rustc'
    $rustcPath = $rustcGuard.Path
    $rustcSha256 = $rustcGuard.Sha256
    $rustcIdentity = Get-RustcIdentity -RustcPath $rustcPath
    $rustcVersion = $rustcIdentity.version
    $rustcVerboseSha256 = $rustcIdentity.verbose_sha256
    $rustcVerboseBytes = $rustcIdentity.verbose_bytes
    $rustcHost = $rustcIdentity.host
    if ($rustcVersion -cne $expectedRustcVersion -or $rustcHost -cne $expectedRustcHost) {
        throw ('STOP_TOOLCHAIN_MISMATCH:version={0}:host={1}' -f $rustcVersion, $rustcHost)
    }

    if ($Mode -eq 'Fit') {
        Assert-LockValue -Lock $lock -Key 'rustc_verbose_sha256' -Expected $rustcVerboseSha256
        Assert-LockValue -Lock $lock -Key 'rustc_executable_sha256' -Expected $rustcSha256
        if ($rustSourceSha256 -cne [string]$lock['rust_source_sha256']) {
            throw ('STOP_IMPLEMENTATION_HASH_MISMATCH:rust_source:expected={0}:observed={1}' -f [string]$lock['rust_source_sha256'], $rustSourceSha256)
        }
        if ($wrapperSha256 -cne [string]$lock['wrapper_sha256']) {
            throw ('STOP_IMPLEMENTATION_HASH_MISMATCH:wrapper:expected={0}:observed={1}' -f [string]$lock['wrapper_sha256'], $wrapperSha256)
        }
        Assert-Hash -LiteralPath $ComparisonContractPath -Expected $lock['comparison_contract_sha256'] -Context 'STOP_IMPLEMENTATION_HASH_MISMATCH:comparison_contract'
        Assert-Hash -LiteralPath $sourceManifestPath -Expected $lock['source_manifest_sha256'] -Context 'STOP_SOURCE_CONTENT_MISMATCH:source_manifest'
        Assert-Hash -LiteralPath $preflightAuditorPath -Expected $lock['preflight_auditor_sha256'] -Context 'STOP_PREREQUISITE_RECEIPT_MISMATCH:auditor'
        Assert-Hash -LiteralPath $preflightReceiptPath -Expected $lock['preflight_receipt_sha256'] -Context 'STOP_PREREQUISITE_RECEIPT_MISMATCH:receipt'
    }

    $taskTempDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ('ce-loewenstein-runner-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $taskTempDirectory | Out-Null
    $resolvedTaskTemp = (Resolve-Path -LiteralPath $taskTempDirectory).Path
    $binaryPath = Join-Path $resolvedTaskTemp 'fit_loewenstein_2015_protrusion_v0_v2.exe'
    $verifiedSourcePath = Join-Path $resolvedTaskTemp 'verified_fit_loewenstein_2015_protrusion_v0_v2.rs'
    $sourceGuard = New-GuardedSnapshot -LiteralPath $verifiedSourcePath -Bytes $sourceSnapshot.Bytes
    if ($Mode -eq 'Fit') {
        $verifiedLockPath = Join-Path $resolvedTaskTemp 'verified_execution_lock.tsv'
        $lockGuard = New-GuardedSnapshot -LiteralPath $verifiedLockPath -Bytes $lockSnapshot.Bytes
    }
    $compileArguments = @(
        '--edition=2021',
        '-C', 'opt-level=3',
        '-C', 'debuginfo=0',
        '-C', 'overflow-checks=yes',
        '-C', 'target-feature=-fma',
        '-C', 'codegen-units=1',
        $verifiedSourcePath,
        '-o', $binaryPath
    )
    $compileOutput = @(& $rustcGuard.Path @compileArguments 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw ('STOP_TOOLCHAIN_MISMATCH:compile_exit={0}:detail={1}' -f $LASTEXITCODE, ($compileOutput -join ' '))
    }
    $binaryGuard = Open-HashedReadGuard -LiteralPath $binaryPath -StopCode 'STOP_IMPLEMENTATION_HASH_MISMATCH:compiled_binary'
    $binarySha256 = $binaryGuard.Sha256
    foreach ($threadVariable in $originalThreadEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($threadVariable, '1', 'Process')
    }

    if ($Mode -eq 'SelfTest') {
        $runnerOutput = @(& $binaryGuard.Path --self-test --core-receipt $corePath 2>&1)
        $runnerExit = $LASTEXITCODE
    }
    else {
        $temporarySelfTestPath = Join-Path $resolvedTaskTemp 'self_test_core.json'
        $selfTestOutput = @(& $binaryGuard.Path --self-test --core-receipt $temporarySelfTestPath 2>&1)
        if ($LASTEXITCODE -ne 0) {
            $selfTestDetail = [string]($selfTestOutput | Select-Object -First 1)
            if ($selfTestDetail -cnotmatch '^STOP_[A-Z0-9_]+') {
                $selfTestDetail = 'STOP_GH_SELF_TEST:runner_exit'
            }
            throw $selfTestDetail
        }
        $observedSelfTestSha256 = Get-LowerSha256 -LiteralPath $temporarySelfTestPath
        if ($observedSelfTestSha256 -cne [string]$lock['self_test_core_sha256']) {
            throw ('STOP_SELF_TEST_CORE_HASH_MISMATCH:expected={0}:observed={1}' -f [string]$lock['self_test_core_sha256'], $observedSelfTestSha256)
        }
        Assert-Hash -LiteralPath $DictionaryPath -Expected $lock['dictionary_sha256'] -Context 'STOP_SOURCE_CONTENT_MISMATCH:dictionary'
        if ([string](Get-Item -LiteralPath $DictionaryPath).Length -cne [string]$lock['dictionary_bytes']) {
            throw 'STOP_SOURCE_CONTENT_MISMATCH:dictionary_bytes'
        }
        Assert-Hash -LiteralPath $DataPath -Expected $lock['raw_csv_sha256'] -Context 'STOP_SOURCE_CONTENT_MISMATCH:raw_csv'
        if ([string](Get-Item -LiteralPath $DataPath).Length -cne [string]$lock['raw_csv_bytes']) {
            throw 'STOP_SOURCE_CONTENT_MISMATCH:raw_csv_bytes'
        }
        $fitStartedMarkerPath = Join-Path $resolvedTaskTemp 'fit_started.marker'
        $runnerArguments = @(
            '--fit',
            '--data', $DataPath,
            '--dictionary', $DictionaryPath,
            '--execution-lock', $verifiedLockPath,
            '--expected-lock-sha256', $lockSnapshot.Sha256,
            '--core-receipt', $corePath,
            '--fit-started-marker', $fitStartedMarkerPath
        )
        $runnerOutput = @(& $binaryGuard.Path @runnerArguments 2>&1)
        $runnerExit = $LASTEXITCODE
        $fitStarted = Test-ExactFitStartMarker -LiteralPath $fitStartedMarkerPath
    }
    if ($runnerExit -ne 0) {
        $runnerDetail = [string]($runnerOutput | Select-Object -First 1)
        if ($runnerDetail -cnotmatch '^STOP_[A-Z0-9_]+') {
            $runnerDetail = 'STOP_RUNNER_EXIT:{0}:{1}' -f $runnerExit, ($runnerOutput -join ' ')
        }
        throw $runnerDetail
    }
    if ($Mode -eq 'Fit' -and -not $fitStarted) {
        throw 'STOP_RUNNER_EXIT:fit_marker:expected=exact_committed_marker:observed=missing_after_success'
    }
    $runnerMessage = $runnerOutput -join [char]10
    $coreSha256 = Get-LowerSha256 -LiteralPath $corePath
}
catch {
    $firstErrorDetail = $_.Exception.Message
}
finally {
    foreach ($threadVariable in $originalThreadEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($threadVariable, $originalThreadEnvironment[$threadVariable], 'Process')
    }
    $guardStreams = @()
    if ($null -ne $binaryGuard) { $guardStreams += $binaryGuard.Stream }
    if ($null -ne $lockGuard) { $guardStreams += $lockGuard }
    if ($null -ne $sourceGuard) { $guardStreams += $sourceGuard }
    if ($null -ne $rustcGuard) { $guardStreams += $rustcGuard.Stream }
    foreach ($guardStream in $guardStreams) {
        try {
            $guardStream.Dispose()
        }
        catch {
            $cleanupPass = $false
            if ([string]::IsNullOrEmpty($firstErrorDetail)) {
                $firstErrorDetail = 'STOP_TEMP_CLEANUP_SCOPE:guard_dispose'
            }
        }
    }
    if (-not [string]::IsNullOrEmpty($resolvedTaskTemp) -and (Test-Path -LiteralPath $resolvedTaskTemp -PathType Container)) {
        try {
            $resolvedTempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd([char]92)
            $resolvedCandidate = [System.IO.Path]::GetFullPath($resolvedTaskTemp).TrimEnd([char]92)
            $expectedPrefix = $resolvedTempRoot + [char]92 + 'ce-loewenstein-runner-'
            if (-not $resolvedCandidate.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw 'STOP_TEMP_CLEANUP_SCOPE'
            }
            $tempEntries = @(Get-ChildItem -LiteralPath $resolvedCandidate -Force)
            if (@($tempEntries | Where-Object { $_.PSIsContainer }).Count -ne 0) {
                throw 'STOP_TEMP_CLEANUP_SCOPE:unexpected_directory'
            }
            foreach ($tempEntry in $tempEntries) {
                Remove-Item -LiteralPath $tempEntry.FullName -Force
            }
            Remove-Item -LiteralPath $resolvedCandidate -Force
            if (Test-Path -LiteralPath $resolvedCandidate) {
                throw 'STOP_TEMP_CLEANUP_SCOPE:residual'
            }
        }
        catch {
            $cleanupPass = $false
            if ([string]::IsNullOrEmpty($firstErrorDetail)) {
                $firstErrorDetail = $_.Exception.Message
            }
        }
    }
    if (-not $cleanupPass -and [string]::IsNullOrEmpty($firstErrorDetail)) {
        $firstErrorDetail = 'STOP_TEMP_CLEANUP_SCOPE:residual'
    }
    if (-not [string]::IsNullOrEmpty($firstErrorDetail) -and -not (Test-Path -LiteralPath $corePath)) {
        try {
            $stopReceipt = Get-StopReceiptText -Detail $firstErrorDetail -FitStarted $fitStarted
            Write-NewUtf8 -LiteralPath $corePath -Text $stopReceipt
        }
        catch {
            if ([string]::IsNullOrEmpty($firstErrorDetail)) {
                $firstErrorDetail = $_.Exception.Message
            }
        }
    }
    if (Test-Path -LiteralPath $corePath -PathType Leaf) {
        $coreSha256 = Get-LowerSha256 -LiteralPath $corePath
    }
    if ([string]::IsNullOrEmpty($firstErrorDetail) -and $cleanupPass) {
        $status = 'PASS'
    }
    else {
        $status = 'STOP'
    }
    $environment = [ordered]@{
        schema_version = 'ce_npf_loewenstein_2015_v0_v2_environment_receipt_v2'
        mode = $Mode
        status = $status
        timestamp_utc = [DateTime]::UtcNow.ToString('o')
        os_version = [Environment]::OSVersion.VersionString
        rustc_version = $rustcVersion
        rustc_verbose_sha256 = $rustcVerboseSha256
        rustc_verbose_bytes = $rustcVerboseBytes
        rustc_host = $rustcHost
        rustc_executable_sha256 = $rustcSha256
        compile_flags = $expectedCompileFlags
        rust_source_sha256 = $rustSourceSha256
        wrapper_sha256 = $wrapperSha256
        binary_sha256 = $binarySha256
        core_receipt_sha256 = $coreSha256
        temporary_cleanup_pass = $cleanupPass
        runner_message = $runnerMessage
        stop_detail = $firstErrorDetail
    }
    $environmentText = ($environment | ConvertTo-Json -Depth 4).Replace("`r`n", "`n").Replace("`r", "`n").TrimEnd([char]10) + [char]10
    Write-NewUtf8 -LiteralPath $environmentPath -Text $environmentText
}

if (-not [string]::IsNullOrEmpty($firstErrorDetail)) {
    throw $firstErrorDetail
}
Write-Output $runnerMessage
