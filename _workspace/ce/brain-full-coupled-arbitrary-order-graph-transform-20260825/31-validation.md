# Validation

Status: COMPLETE

- Focused full-adapter tests: 27/27 passed.
- Adjacent full/local/raw/implicit plus dimensionless tests: 153/153 passed,
  including dimensionless 55/55.
- Exact fixture: `alpha=9/10`, `r_x=1/10`, `s=1/100`, `q0=11/1000`.
- Orders C2/C4/C6: passed.
- Global contact mismatches: dimension, conorm, slope, preimage coupling, and
  first fiber numerator all failed closed under their named codes.
- Local/matched identity and reference-scale mismatches: passed.
- Synchronous one/two-step recurrence and zero-step identity: passed.
- Dimensions 1/4/5/6/100 are preserved rather than selected: passed.

Source compile, repository whitespace check, and final run gate are recorded
after documentation integration.
