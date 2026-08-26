# Validation

Status: COMPLETE

- focused preprocessing tests: 8/8;
- DPREP/DPCA/DEXEC/DSTAB/base adjacency: 62/62;
- chain plus dimensionless and ledger: 171/171;
- dimensionless checks: 105/105;
- source compilation and exact eight-file bundle;
- final gate: `OK final`.

Fixtures cover exact means/scales, zero normalized sums, same held-out transform,
large-shift non-recentering, raw scale covariance, invalid scales, downstream
training failure, and external-byte ceilings.
