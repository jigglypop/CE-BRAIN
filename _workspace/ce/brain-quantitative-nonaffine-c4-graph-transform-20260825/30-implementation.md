# Implementation

Status: COMPLETE

Added `quantitative_nonaffine_c4_graph_transform.py` with exact rational
common-inverse C4 class and recurrence certificates, the scalar sine inverse
bound, fail-closed statuses, exact iteration, and dimension preservation.

Added a focused test module and a dimensionless-core registration. The first
focused execution exposed one stale expected fixture value after increasing
`Lambda4` from 40 to 100; the expected `c40` was corrected. No derivation or
implementation coefficient changed.
