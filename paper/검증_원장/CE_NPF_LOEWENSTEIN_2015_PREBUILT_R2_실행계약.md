# CE-NPF Loewenstein 2015 prebuilt R2 실행계약

Status: `PARENT_SNAPSHOT_FROZEN / REPRODUCIBLE_UNSIGNED_PAYLOAD_READY / ENTERPRISE_APPROVAL_PENDING / SCIENTIFIC_LOCK_FALSE / FIT_NOT_STARTED`

이 문서는 기존
[`V0,V1,V1Z,V2 비교계약`](CE_NPF_LOEWENSTEIN_2015_돌기재관측_V0_V2_비교계약.md)의
과학모형을 바꾸지 않고, Windows Code Integrity가 승인한 사전빌드 실행파일만
사용하기 위한 **실행 전달 R2**다. 기존 계약·Rust source·wrapper v1·false lock은
수정하거나 덮어쓰지 않는다.

## 1. 목표와 비목표

최종 목표는 동결된 공통 2,723구간·1,459사건·8-cell leave-one-cell-out
rowset에서 승인된 한 `run_id`에 대해 다음 세 비교를 실행하는 것이다.

\[
V_1-V_0,\qquad V_{1Z}-V_1,\qquad V_2-V_{1Z}.
\]

R2는 unsigned 임시 EXE를 만드는 wrapper v1의 전달 경로만 교체한다.
likelihood, nested frailty, variance face, AGHQ, optimizer, Hessian gate,
score, tolerance와 receipt renderer는 바꾸지 않는다. 기계 판정 필드는 부모와 같은
`decision_scope=WITHIN_PIPELINE_DESCRIPTIVE_PREDICTION_ONLY`,
`claim_ceiling=BIO_EVIDENCE_L0`다. 재카탈로그된 측방 돌기 endpoint는 별도 `scope`에만
기록하며 claim ceiling을 대신하지 않는다.

R2의 성공은 다음을 뜻하지 않는다.

- mature spine 또는 biological contact hazard를 식별했다.
- animal holdout이나 다른 성별·연령·구획으로 일반화했다.
- synaptic weight, conduction delay, Riemann metric 또는 행동 매개를 검증했다.

## 2. 부모 snapshot

| 객체 | SHA-256 |
|---|---|
| 비교계약 | `a7fbc541b07bc47806ccba4836647826d4b125b2b4ff265387817cf09e78a93e` |
| Rust source | `23094cb23b3d14e9384b55270b0d887147d7dd7e8cbef9b85da6564796891e8e` |
| wrapper v1 | `fd9e5c4ff094111f29431049ba2d9d267894237b218395634d40ad63165e998c` |
| authorization=false lock | `70171ba144416788891cd0e77ff390062ce8035eccdba6aa5a5af876485bc126` |
| deterministic self-test core | `ed13230bb3497a8a482e72ccd2acf40af09d2cd3c2078d9d43cabc31b7aec697` |

부모 false lock의 29-key schema와 과학 필드는 그대로 보존한다. signed runner가
반환되고 R2 wrapper와 이 계약이 안정화되면 `ProposeFinal`은 최종 lock의 결정적
bytes를 메모리에서 계산하되 **SHA-256 digest만** 파일로 쓴다. 실제
`real_data_fit_authorized=true` lock은 최종 run spec에 대한 두 승인을 `Finalize`가
검증한 뒤, 새 산출물 디렉터리의 마지막 파일로만 생성한다.

## 3. 현재 Code Integrity 사실

현재 host의 Smart App Control/UMCI는 강제 상태이고 활성 차단 정책은
`VerifiedAndReputableDesktop`, policy GUID
`{0283ac0f-fff1-49ae-ada1-8a933130cad6}`다. wrapper v1이 만든 EXE는
Code Integrity event 3033/3077에서 enterprise signing level 미충족으로
차단됐다. 고정 workspace 경로도 같은 이유로 차단됐으므로 경로 이동은 해결책이
아니다.

WSL, Docker, 다른 signed interpreter 또는 순수 PowerShell 재구현으로 경계를
피하지 않는다. 수치코어를 다른 언어로 옮기는 것도 R2가 아니라 새 과학 구현이다.

## 4. 서명 payload

서명 요청 정본은
[`build_manifest.tsv`](../../artifacts/brain/ce_npf_loewenstein_2015_runner_signing_candidate_v1/build_manifest.tsv)와
[`SIGNING_REQUEST.md`](../../artifacts/brain/ce_npf_loewenstein_2015_runner_signing_candidate_v1/SIGNING_REQUEST.md)다.

현재 unsigned payload는 같은 basename으로 세 번 빌드해 byte-identical이었다.

| 필드 | 값 |
|---|---|
| unsigned SHA-256 | `47fd90048d28c7bdceb0654cae218759c0aea12b7ce5593f9d90a3a62ee03b4e` |
| bytes | `732672` |
| source | 부모 Rust source exact bytes |
| scientific flags | `--edition=2021 -C opt-level=3 -C debuginfo=0 -C overflow-checks=yes -C target-feature=-fma -C codegen-units=1` |
| packaging flag | `-C link-arg=/Brepro` |
| current signature | `NotSigned` |

`/Brepro`는 PE packaging metadata의 재현성만 고정한다. post-sign binary는
signature bytes 때문에 새 SHA를 가지며 그 최종 SHA·크기·signer를 run spec에
다시 고정해야 한다. 또한 R2 adapter는 unsigned payload와 post-sign binary의
PE 내용을 직접 대조한다. PE checksum과 certificate-table directory를 0으로 만들고
파일 끝의 embedded certificate table을 제외한 내용 SHA가 unsigned payload의
`47fd9004...03b4e`와 exact match해야 한다. certificate table은 8-byte 정렬이고
파일 끝까지 정확히 차지해야 한다. 따라서 서명 전 payload가 아닌 다른 프로그램을
서명해 반환하는 signing-lineage 변경은 self-test 전에 닫힌다.

## 5. 두 독립 승인

실행 허가는 다음 AND다.

\[
\mathsf{GO}_{\rm fit}
=
\mathsf{UserScientificAuthorization}
\land
\mathsf{EnterpriseExecutionApproval}
\land
\mathsf{ExactBinding}.
\]

1. **사용자 과학 승인**은 이 고정 자료·rowset·비교·claim ceiling으로 실제 fit을
   수행해도 된다는 승인이다.
2. **enterprise 실행 승인**은 이 exact post-sign binary가 이 host 정책에서
   실행돼도 된다는 승인이다.

CLI boolean이나 파일 존재만으로 어느 승인도 대신하지 않는다. 두 approval
receipt는 최종 run spec SHA를 각각 가리켜야 하며, 서로를 대신할 수 없다.

## 6. strict prebuilt run spec

UTF-8 no-BOM, LF-only, final LF 하나인 2열 TSV를 쓴다. 키 순서는 다음과 같다.

```text
schema_version
execution_ready
parent_contract_sha256
parent_false_lock_sha256
r2_execution_contract_sha256
r2_wrapper_sha256
artifact_generator_sha256
rust_source_sha256
scientific_execution_lock_sha256
pre_sign_payload_sha256
signed_runner_sha256
signed_runner_bytes
signature_mode
signer_certificate_sha256
enterprise_policy_id
build_manifest_sha256
expected_self_test_core_sha256
rustc_version
rustc_host
rustc_executable_sha256
scientific_compile_flags
packaging_link_flags
runtime_threads
model_semantics_id
decision_scope
claim_ceiling
```

허용 `signature_mode`는 우선 `authenticode` 하나다. catalog/Managed Installer는
origin claim과 approval verifier가 별도로 구현·감사된 다음 새 run-spec revision에서
연다. 현재 adapter와 생성기는 literal path에 대해
`Get-AuthenticodeSignature.Status=Valid`와 `SignatureType=Authenticode`를 함께
요구한다. 따라서 catalog signature는 거부한다. exact certificate SHA-256, exact
post-sign binary SHA와 byte size, embedded PE certificate table과 pre-sign content
lineage도 모두 일치해야 한다.

run spec은 부모 비교계약, R2 실행계약, R2 wrapper와 canonical generator를 각각
별도 SHA-256으로 묶는다. adapter와 generator에는 R2 실행계약, unsigned payload
`47fd9004...03b4e`, build manifest
`27deaa7964f0705b6fb8735c066d45a0b596aa0cd612140d598e41172517ac6a`, 활성 정책 GUID가
trust anchor로 고정된다. 실제 OS가 그 정책으로 launch를 허용하는지는 최종 실행의
외부 관측 경계다.

`execution_ready=false` 또는 `PENDING` 값이 하나라도 있으면 runner를 실행하지
않는다.

## 7. approval receipt

두 receipt 모두 strict TSV이고 최종 run-spec SHA를 가리킨다.

사용자 receipt 키 순서:

```text
schema_version
decision
run_spec_sha256
scope
decision_scope
claim_ceiling
run_id
issuer
issued_at_utc
expires_at_utc
```

enterprise receipt 키 순서:

```text
schema_version
decision
run_spec_sha256
signed_runner_sha256
signature_mode
signer_certificate_sha256
enterprise_policy_id
allowed_host
allowed_architecture
run_id
issuer
issued_at_utc
expires_at_utc
```

R2 adapter는 receipt exact SHA를 CLI에서 받고 strict schema, `AUTHORIZE`와
`APPROVE_EXECUTION`, run-spec binding, 동일 `run_id`, 정확한
`yyyy-MM-ddTHH:mm:ssZ` UTC 유효기간을 검사한다. `run_id`는 두 결정을 같은 실행에
결합하는 식별자이지 소비 원장이 아니다. 이 revision은 다른 output directory에서
같은 receipt를 재사용하는 것을 기술적으로 막지 않으므로 `single_use`라고 부르지
않는다. 모든 값에서 C0 제어문자를 거부하고, `issuer`나 `run_id`가 `PENDING` 또는
`PENDING-...`이면 정지한다.

조직이 detached signature를 제공하면 그 signature verifier를 새 revision에
추가한다. 현재 revision의 plain TSV receipt와 caller-supplied hash는 **감사 결합**이지
issuer의 암호학적 인증이 아니다. binary의 embedded Authenticode, exact signer와 실제
OS Code Integrity enforcement가 enterprise 실행 신뢰의 강제점이다. 마찬가지로
서명된 runner를 wrapper 밖에서 직접 호출하는 것을 R2 자체가 보안 경계로 막지는
않는다. 따라서 이 계약은 협력적 연구 실행 하네스이며, 적대적 local-user 환경이나
일회성 소비 강제가 필요하면 detached approval signature와 broker/ACL 또는 코어 내부
approval 검증을 갖춘 후속 revision 없이는 production security 승인을 주장하지 않는다.

## 8. scientific execution lock

기존 Rust binary가 직접 읽으므로 부모와 같은 strict 29-key
`ce_npf_loewenstein_2015_v0_v2_execution_lock_v1` schema를 쓴다. 과학 비교계약을
뜻하는 `comparison_contract_sha256`는 부모 값
`a7fbc541b07bc47806ccba4836647826d4b125b2b4ff265387817cf09e78a93e`로 유지한다.

candidate false lock은 부모에서 다음 하나만 바꾼다.

- `wrapper_sha256=<안정 R2 adapter SHA-256>`

승인된 final true lock은 부모에서 다음 둘만 바꾼다.

- `real_data_fit_authorized=true`
- `wrapper_sha256=<안정 R2 adapter SHA-256>`

나머지 27개 값은 부모 false lock과 exact match여야 한다. R2 실행계약 SHA는
scientific lock의 비교계약 필드를 재목적화하지 않고 run spec이 별도로 묶는다. R2
adapter는 허용 차이를 명시적으로 검사한다. hash 순환과 승인 선행 생성을 피하는
발급 순서는 다음과 같다.

1. R2 contract를 안정화해 그 SHA를 generator와 wrapper에 고정한다.
2. generator를 안정화해 그 SHA를 wrapper에 고정하고, 최종 wrapper를 안정화한다.
3. signed runner의 embedded Authenticode와 PE-content lineage를 검증한다.
4. 부모 대비 두 허용 delta만 가진 true-lock bytes를 **메모리에서만** 계산한다.
5. `materialized=false`인 lock digest와 그 SHA를 묶은 ready run-spec을 제안한다.
6. 그 run-spec SHA를 가리키는 두 외부 approval receipt를 받는다.
7. `Finalize`가 exact receipt SHA, `AUTHORIZE`, `APPROVE_EXECUTION`, 동일 non-PENDING
   `run_id`, scope, machine field, signer, host, policy와 UTC 유효기간을 다시 검증한다.
8. final run spec, 검증된 receipt 사본, finalization manifest를 `CreateNew`로 쓴 뒤,
   authorization=true 29-key lock을 **항상 마지막 파일**로 `CreateNew`한다.

승인 전에는 실제 true lock 파일이 존재하지 않는다. 후보 false lock을 제자리에서
flip하지 않고, 어느 안정 입력이 바뀌면 digest, 제안 run spec과 두 receipt를 모두
폐기한다. 최종 true lock의 존재만으로 적대적 사용자의 direct invocation을 막는다는
뜻은 아니며, 그 보안 한계는 7절의 협력적 하네스 경계를 따른다.

이 순서의 canonical serializer는
[`new_loewenstein_2015_prebuilt_r2_artifacts.ps1`](../6_뇌/국소회로_상태다양체_흐름_대응/repro/new_loewenstein_2015_prebuilt_r2_artifacts.ps1)다.
`Candidate` mode는 authorization=false lock, execution-ready=false run spec과 두
`PENDING` template만 새 디렉터리에 쓴다. `ProposeFinal` mode는 exact
embedded-signed runner와 PE-content lineage를 검증한 뒤 authorization=true lock의
digest, execution-ready=true run-spec과 두 `PENDING` template을 쓴다. true lock
bytes는 쓰지 않는다. `Finalize` mode만 두 외부 receipt를 검증하고 final true lock을
마지막에 materialize한다. 생성기는 `AUTHORIZE`나 `APPROVE_EXECUTION`을 발급하지
않으며 runner 또는 자료를 실행·열람하지 않는다.

`ProposeFinal`의 strict digest key 순서는 다음과 같다.

```text
schema_version
materialized
scientific_lock_sha256
parent_false_lock_sha256
real_data_fit_authorized
comparison_contract_sha256
wrapper_sha256
```

여기서 `materialized=false`여야 한다. `Finalize`의 strict manifest key 순서는
다음과 같고, 이 manifest 자체는 lock보다 먼저 쓰이므로 완료를 가장하지 않고
`status=APPROVALS_VERIFIED_LOCK_MATERIALIZATION_AUTHORIZED`를 기록한다.

```text
schema_version
status
run_id
artifact_generator_sha256
r2_execution_contract_sha256
r2_wrapper_sha256
run_spec_sha256
scientific_execution_lock_sha256
user_authorization_receipt_sha256
enterprise_approval_receipt_sha256
signed_runner_sha256
signer_certificate_sha256
enterprise_policy_id
scientific_lock_materialization_authorized
scientific_lock_must_be_last
data_opened
runner_executed
```

## 9. 실행 순서

R2 adapter의 순서는 fail-closed로 고정한다.

0. 어떤 filesystem call보다 먼저 mode별 필수·금지 인수와 모든 명시·암묵 경로를
   lexical 정규화한다. `SelfTest`의 data/dictionary/lock/user/finalization 인수, 중복 경로,
   output과 input의 포함관계, UNC와 alternate data stream을 거부한다.
1. output directory를 non-reparse로 확인하고
   `execution_control_receipt.json`을 `CreateNew/ReadWrite/FileShare.None`으로 예약한다.
2. run spec exact hash·strict schema·`execution_ready=true`, 고정 contract/generator/
   payload/manifest/policy anchor와 machine decision/claim field를 검사한다.
3. enterprise receipt와, Fit이면 user receipt의 exact hash·schema·결정·run-spec·
   non-PENDING run-ID·issuer·UTC 유효기간을 검사한다.
4. Fit이면 scientific lock exact hash·29-key schema·authorization과 부모 대비 두 허용
   delta만 검사하고, finalization manifest exact hash·schema·run ID·두 receipt·lock·
   runner·signer·contract·wrapper·generator·policy 결합을 검사한다.
5. R2 contract, wrapper 자기 bytes, generator, Rust source, strict build manifest와
   선행 receipt hash를 검사한다.
6. unsigned candidate exact hash·bytes·`NotSigned`와 post-sign runner의 PE-content
   identity를 검사한다.
7. prebuilt runner regular-file·non-reparse, post-sign hash·bytes·embedded
   `SignatureType=Authenticode` signer를 검사한다.
8. fresh non-reparse temporary directory에 검증된 runner bytes를 `CreateNew` snapshot으로
   만들고 재해시·재서명 검사한 뒤, 원본과 snapshot의 read handle을 유지한 채
   `--self-test`를 실행한다.
9. self-test receipt SHA가 부모의 `ed13230...c697`과 exact match인지 검사한다.
10. 그 뒤에만 dictionary와 CSV를 열어 hash·bytes를 검사하고, lock·dictionary·CSV를
    같은 temporary directory에 snapshot한다. runner에는 snapshot 경로만 전달한다.
11. 같은 snapshot runner가 inner scientific lock을 다시 독립 검사하고 Rust input
    parse·rowset gate 뒤 exact fit-start marker를 commit한다.
12. runner가 nonzero여도 존재하는 core receipt를 먼저 해시한다. 모든 read handle을
    닫고, 원래 생성한 exact basename의 regular file만 비재귀적으로 지운 뒤 빈
    temporary directory만 지운다. 예상 밖 항목·reparse·부모/이름 불일치 또는 cleanup
    실패는 PASS를 STOP으로 바꾼다. thread 환경변수 복구도 항목별로 시도하며 실패는
    `STOP_ENVIRONMENT_RESTORE`다.
13. 예약된 control stream에
    `ce_npf_loewenstein_2015_prebuilt_r2_control_receipt_v2` JSON을 기록하고
    `Flush(true)`·동일 stream readback SHA 검증 후 stream을 성공적으로 닫고, 그 JSON SHA-256과
    final LF만 담은 `execution_control_receipt.sha256`를 `CreateNew`로 기록·검증한다.
    sidecar가 없거나 JSON SHA와 다르면 receipt는 미완성이다. commit 실패 시 JSON을
    가능한 경우 빈 예약 상태로 되돌리고 반드시 nonzero
    `STOP_CONTROL_RECEIPT_COMMIT`으로 끝낸다. 정상·정지 모두 유효한 JSON+sidecar
    조합 없이는 committed receipt가 아니다.

0--9단계의 어떤 실패도 CSV·dictionary의 존재 여부를 조회해서는 안 된다. 이 절대
no-touch는 정직하게 분리된 로컬 경로를 쓰는 협력적 실행 하네스 범위다. 공격자가
hardlink를 미리 만들거나 디렉터리 ACL/reparse 상태를 검사와 사용 사이에 바꿀 수 있는
환경까지 보장하려면 신뢰 루트 ACL 또는 handle broker가 필요하며 이 revision의
production 보안 범위가 아니다. adapter는 일반 path 재개방을 줄이기 위해 검증 bytes의
fresh snapshot만 실행·전달한다. OS 강제 종료나 전원 손실은 cleanup 코드를 실행하지
못해 `%TEMP%` snapshot을 남길 수 있다. 그런 경우 control sidecar가 없으므로 실행은
미완성으로 판정하고 운영자가 exact `ce-loewenstein-prebuilt-r2-<32 hex>` 경로를 별도
감사·정리해야 한다.

## 10. stop code

- `STOP_RUN_SPEC_HASH_OR_SCHEMA`
- `STOP_RUN_SPEC_NOT_READY`
- `STOP_PATH_ALIAS_OR_SCOPE`
- `STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST`
- `STOP_OUTPUT_EXISTS`
- `STOP_USER_DATA_FIT_NOT_AUTHORIZED`
- `STOP_ENTERPRISE_EXECUTION_NOT_APPROVED`
- `STOP_APPROVAL_BINDING_MISMATCH`
- `STOP_APPROVAL_EXPIRED_OR_RUN_ID_MISMATCH`
- `STOP_SCIENTIFIC_LOCK_MISMATCH`
- `STOP_FINALIZATION_MANIFEST_MISMATCH`
- `STOP_PREBUILT_RUNNER_HASH_OR_SIZE`
- `STOP_PREBUILT_RUNNER_SIGNATURE`
- `STOP_SELF_TEST_CORE_HASH_MISMATCH`
- `STOP_SOURCE_CONTENT_MISMATCH`
- `STOP_RUNNER_EXIT`
- `STOP_TEMP_CLEANUP_SCOPE`
- `STOP_ENVIRONMENT_RESTORE`
- `STOP_CONTROL_RECEIPT_COMMIT`
- 부모 계약의 모든 수치·자료·optimizer stop code

generator는 별도로 `STOP_GENERATOR_INPUT`, `STOP_GENERATOR_VALUE`,
`STOP_GENERATOR_SIGNED_RUNNER`, `STOP_GENERATOR_APPROVAL`,
`STOP_GENERATOR_OUTPUT_EXISTS`, `STOP_GENERATOR_WRITE_VERIFY`를 fail-closed로 쓴다.

## 11. 다음 gate

현재 허용되는 행동은 R2 source 독립 재감사, 서명 payload 전달과 enterprise가
반환한 post-sign artifact의 읽기 전용 감사뿐이다. 재감사 PASS 뒤 signed runner로
`ProposeFinal`을 만들고 두 승인을 받은 다음, `Finalize`가 final lock을 마지막에
materialize해야 한다. 실제 fit은 다음 일곱 값이 모두 관측된 뒤에만 시작한다.

```text
execution_ready=true
user decision=AUTHORIZE
enterprise decision=APPROVE_EXECUTION
scientific lock real_data_fit_authorized=true
finalization manifest status=APPROVALS_VERIFIED_LOCK_MATERIALIZATION_AUTHORIZED
post-sign PE content=47fd9004...03b4e
self-test core=ed13230b...c697
```

그 전 상태는 `FIT_NOT_STARTED`이며 `FIT_FAILED`가 아니다. 양성 fit이 나오더라도 이
R2의 결론 상한은 동일 저자 pipeline 내부 측방 돌기 재카탈로그 예측의
`BIO_EVIDENCE_L0`다. synaptic weight, 전도속도, Riemann metric, 공간 접힘,
행동·인과 매개로의 승격은 별도 biological mediation 자료와 사전 게이트 없이는
허용하지 않는다.
