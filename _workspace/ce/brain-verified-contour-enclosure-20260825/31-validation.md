# Verified rational contour enclosure -- focused validation

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-verified-contour-enclosure-20260825`

Command:

```powershell
.codex\hooks\python.cmd pytest tests\test_verified_rational_contour.py -vv -s --tb=short
```

Result: `11 passed in 0.07s` (Python 3.14.2, 2026-08-25).

The focused file covers exact parser rejection of binary and noncanonical
string inputs, dyadic enclosure self-checks and inadequate precision, a
positive exact circle with exposed chord-root inequalities, 
singular node, nonpositive lower bound, unsupported mesh, invalid matrix,
simultaneous unit rescaling, an oblique exactly diagonalizable nonnormal
witness, invalid/defective witnesses, and annulus inner-boundary,
outer-boundary, and interior eigenvalue controls.

No full test suite, empirical data access, or irreversible stage was run.
