# Implementation

Status: COMPLETE

`verified_interval_residual.py` now exposes `exact_nominal_node_inverse_witnesses`. It normalizes the rational nominal contour problem, constructs the ordered four node matrices, uses the existing exact $\mathbb Q(i)$ Gauss--Jordan inverse, verifies both inverse identities, and reports the first singular node without producing partial witnesses.

`verified_componentwise_residual_circle_with_exact_witnesses` composes that receipt with the unchanged residual-family certificate. It preserves construction and family statuses separately: an exact construction pass cannot override contraction or full-circle failure.

