# Validation

Status: COMPLETE

- focused signed-acquisition tests: 10/10;
- DSIGN/DBYTE/DMAN/DPREP/DPCA/DEXEC/DSTAB/base adjacency: 89/89;
- chain plus dimensionless and ledger: 201/201;
- dimensionless checks: 108/108;
- signed-receipt and predecessor runtime modules compile;
- exact eight-file bundle;
- final gate: `OK final`.

Coverage includes RFC 8032 vectors 1/2, altered message/signature, noncanonical
`S=L`, identity public key, complete-chain success, stale bundle root, wrong trusted
key fingerprint, changed signer ID, and the external-identity/device ceiling.
