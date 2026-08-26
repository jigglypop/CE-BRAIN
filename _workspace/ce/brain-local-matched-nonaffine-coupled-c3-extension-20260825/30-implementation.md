# Implementation

Status: COMPLETE

Added `quantitative_local_nonaffine_coupled_c3_graph_transform.py` and
`quantitative_matched_local_nonaffine_coupled_c3_graph_transform.py`. The local
certificate composes the unchanged global C3 certificate with core inverse
coverage and a separately normalized two-sided extension-collar gate. The
matched certificate adds exact contacts and boundary preservation while
reporting differential/collar robustness separately from zero-margin domain
contact.

Added one focused test file and two dimensionless tests. The exact cubic
witness recomputes the minimum expansion and Hessian bound on the enlarged
input collar instead of reusing core-only constants. No existing recurrence,
threshold, dependency, environment, or Git state was changed.
