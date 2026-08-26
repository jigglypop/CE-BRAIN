# Implementation

Status: COMPLETE

`quantitative_coupled_c3_graph_transform.py` composes the exact coupled C2
predecessor, computes the one-graph $U,V,M$ and Lipschitz layers, exposes the
two-graph modified-tensor coefficients, preserves predecessor failures, marks
class equalities nonrobust, and iterates the exact four-level recurrence.

`test_quantitative_coupled_c3_graph_transform.py` covers 24 focused cases:
strict certification, recurrence, mandatory/optional C3,1 gates, class
equality, a nonzero scalar inverse-chain identity, exact triangular reduction,
bunching equality, the $|x|^3$ witness, predecessor failure, scale covariance,
dimensions, and fail-closed inputs.
