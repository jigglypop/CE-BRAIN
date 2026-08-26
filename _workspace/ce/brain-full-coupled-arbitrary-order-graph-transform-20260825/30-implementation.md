# Implementation

Status: COMPLETE

Added:

- `quantitative_full_coupled_arbitrary_order_graph_transform.py`
- `test_quantitative_full_coupled_arbitrary_order_graph_transform.py`

The module defines global, local, and exact-matched full certificates.  It
checks five global numerical contacts, both local reference-scale/identity
contacts, both matched fiber-scale/identity contacts, and keeps exact-contact
robustness separate from strict differential/collar robustness.

The full iterator consumes exact nonnegative D0..Dn inputs.  It applies `q0`
to the old D0 and every derivative row to that same old vector at each step.
