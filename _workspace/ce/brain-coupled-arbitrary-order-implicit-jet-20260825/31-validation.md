# Validation

Status: COMPLETE

Focused evidence:

- Source compile: passed.
- Conditional implicit-jet tests: 19/19 passed.
- Exact C2--C4 numerator identities: passed (`B4=360` in the curved fixture).
- Linear-base C1--C6 reduction: passed.
- Strict diagonal boundary and invalid inputs: passed.
- Dimension preservation for 1, 4, 5, 6, 100: passed.

Final adjacent evidence:

- New implicit-jet module, nonaffine coupled C4, affine arbitrary order,
  common-inverse nonaffine arbitrary order, and dimensionless audit: 129/129.
- Dimensionless audit within that command: 50/50.

The repository-wide Python doctor is not a theorem failure: it currently stops
on the optional package import `torch`, while explicit source compile and
focused tests use the repository system-Python harness normally.
