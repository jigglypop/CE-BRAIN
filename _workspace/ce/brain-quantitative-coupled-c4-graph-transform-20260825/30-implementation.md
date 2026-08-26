# Implementation

Status: COMPLETE

Added `quantitative_coupled_c4_graph_transform.py`. It implements the exact
modified fourth tensor through size, point-modulus, and coefficient-vector
layers. The vector order is frozen as `(fourth, third, hessian, derivative,
value)`, and products are composed with exact rational nonnegative arithmetic.
The module exposes C4/C4,1 margins, the four cross coefficients, bypass status,
dimension, stable failure order, and exact five-layer iteration.

Added a focused test file and one dimensionless test. The first focused run had
one test-only failure: a deliberately zero third-derivative graph radius fails
the C2,1 predecessor before the C3 class, so the expected primary status was
corrected to preserve the existing gate order. No formula, fixture threshold,
predecessor source, dependency, environment, or Git state was changed.
