# Loewenstein V0--V2 runner signing request

Status: `UNSIGNED_SIGNING_CANDIDATE_NOT_EXECUTED / DATA_NOT_OPENED`

## Exact payload

The only payload proposed for enterprise signing is
[`signing_payload/fit_loewenstein_2015_protrusion_v0_v2.exe`](signing_payload/fit_loewenstein_2015_protrusion_v0_v2.exe).

- SHA-256: `47fd90048d28c7bdceb0654cae218759c0aea12b7ce5593f9d90a3a62ee03b4e`
- bytes: `732672`
- current Authenticode status: `NotSigned`
- execution status: **not executed**

The payload was built three times with the same basename and exact source,
toolchain, scientific flags, and packaging flag. All three payloads were
byte-identical. The first build pair without the packaging flag differed in PE
metadata, so byte reproducibility is claimed only for the `/Brepro` packaging
profile recorded in [`build_manifest.tsv`](build_manifest.tsv).

## Frozen scientific identity

- Rust source SHA-256:
  `23094cb23b3d14e9384b55270b0d887147d7dd7e8cbef9b85da6564796891e8e`
- comparison contract SHA-256:
  `a7fbc541b07bc47806ccba4836647826d4b125b2b4ff265387817cf09e78a93e`
- expected deterministic self-test core SHA-256:
  `ed13230bb3497a8a482e72ccd2acf40af09d2cd3c2078d9d43cabc31b7aec697`
- model semantics:
  `LOEWENSTEIN_V0_V1_V1Z_V2_C2015`
- R2 execution contract SHA-256:
  `0272500218d9dbd3a0eedbaf5444c088cadc7d58711645da92483f3aa3ea569c`
- R2 canonical generator SHA-256:
  `a1f7f96985ee6b100a5d52528611d7f0382d19725f608a83bcc2dc53a04cd13e`
- R2 wrapper SHA-256:
  `3a0b4c5d389db90d0582c2aebc6a6e2973c89eb7a8c1855ad3503d237e07ac0e`

`/Brepro` is a packaging/link reproducibility flag. It does not authorize a
scientific model, change the frozen model columns or tolerances, or replace the
required post-sign self-test. A signed payload is usable only if its own
`--self-test` receipt exactly matches the frozen self-test SHA above.

## Required enterprise action

For the current R2 path, an enterprise administrator must perform the following
without changing the unsigned payload before signing:

1. apply one embedded Authenticode signature chaining to a signer accepted by
   the active Windows Code Integrity policy;
2. preserve the pre-sign PE content lineage described below; and
3. return the complete post-sign binary and approval metadata.

The returned artifact must include the final post-sign binary bytes, SHA-256,
byte size, `SignatureType=Authenticode`, signer certificate identity, policy ID,
allowed host/architecture, and approval validity window.

The current R2 adapter supports only option 1: an **embedded Authenticode**
signature whose certificate table is 8-byte aligned and ends exactly at the end
of the PE file. It normalizes the PE checksum and certificate-table directory,
removes that trailing certificate table, and requires the remaining content SHA
to equal the unsigned payload SHA above. Catalog or Managed Installer return
artifacts require a separately implemented and audited later adapter revision;
they must not be labeled R2-ready.

## Fail-closed handoff

Signing or deployment approval is distinct from permission to fit biological
data. After the enterprise artifact is returned, the implementation owner must:

1. stabilize the R2 contract, canonical generator and wrapper, then verify the
   exact post-sign binary;
2. use `ProposeFinal` to calculate the
   `real_data_fit_authorized=true` lock bytes in memory and emit only their
   digest, never the true lock file;
3. freeze a versioned ready run specification binding that digest, the final
   binary, wrapper, generator, source, contract, toolchain, self-test,
   `decision_scope=WITHIN_PIPELINE_DESCRIPTIVE_PREDICTION_ONLY`, and
   `claim_ceiling=BIO_EVIDENCE_L0`;
4. obtain separate user and enterprise approval receipts bound to that exact
   run specification and the same non-PENDING `run_id`;
5. use `Finalize` to validate both exact receipt hashes, decisions and UTC time
   windows, then materialize the true lock as the final output file;
6. run the prebuilt binary in self-test mode before checking the CSV or data
   dictionary; and
7. begin the fit only after the self-test receipt is an exact hash match.

Until those gates pass, the correct status remains
`ENTERPRISE_EXECUTION_PREREQUISITE_UNMET / FIT_NOT_STARTED`.
