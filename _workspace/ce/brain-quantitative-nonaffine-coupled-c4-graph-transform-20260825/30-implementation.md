# Implementation

Status: COMPLETE

Added `quantitative_nonaffine_coupled_c4_graph_transform.py` with the generic
nonaffine modified-tensor path, D4/D5 base-map separation, conditional C4,1,
full coefficient vectors, a sharp common-inverse bypass, exact iteration,
stable failures, sine forward bounds, and dimension preservation.

Added focused tests and a dimensionless registration. The first focused run
found two test-level issues and one substantive route issue: the common-inverse
fixture first failed a predecessor radius, an invalid string fixture was
actually accepted exact syntax, and the generic envelope did not reduce
sharply. The radii/string were corrected and the mathematically required
direct common-inverse bypass was implemented.
