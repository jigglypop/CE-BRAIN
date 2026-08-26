# Validation

Status: COMPLETE

- focused manifest tests: 8/8;
- DMAN/DPREP/DPCA/DEXEC/DSTAB/base adjacency: 70/70;
- chain plus dimensionless and ledger: 180/180;
- dimensionless checks: 106/106;
- source compilation and exact eight-file bundle;
- final gate: `OK final`.

Fixtures cover full-chain success, rational and mapping canonicalization, float/bool
refusal, expected-hash mismatch, payload mutation, ID-shape mismatch, cross-split ID
overlap, and the external-signature ceiling.
