# Validation

Status: COMPLETE

Validation on the final implementation snapshot:

- focused selection tests: 23/23 passed;
- selection plus rational/interval/tightening/residual/weighted/witness/binary64
  contour adjacency and dimensionless suite: 186/186 passed;
- dimensionless suite separately: 60/60 passed;
- source compilation with `py_compile`: passed;
- exact run shape: eight numbered files, passed;
- final gate: `OK final`.

Required negative fixtures include top tie, runner tie, equality at the advantage
threshold, no eligible candidate, failed heldout selected weight, forged menu,
invalid exact inputs, and proof that only one heldout evaluation occurs.
