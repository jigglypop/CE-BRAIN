# Validation

Status: COMPLETE

- focused source-byte receipt tests: 9/9;
- DBYTE/DMAN/DPREP/DPCA/DEXEC/DSTAB/base adjacency: 79/79;
- chain plus dimensionless and ledger: 190/190;
- dimensionless checks: 107/107;
- both modified runtime modules compile;
- exact eight-file bundle;
- final gate: `OK final`.

The initial focused run exposed that exact rational decoding produced
`Fraction(k,1)` for integer-only bootstrap indices. The final implementation adds
schema-aware denominator-one refinement; no rounding or permissive coercion occurs.
