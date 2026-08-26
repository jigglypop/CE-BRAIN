# Implementation

Status: COMPLETE

`verified_interval_moving_knot_spline_spectral_rank_bridge.py` composes the
nominal MKRES receipt, normalizes the supplied raw uncertainty, checks the strict
Neumann margin, and emits perturbed-resolvent, contour-length, projector, and
rank receipts. Focused tests cover pass, equality/failure, oblique conditioning,
scale covariance, zero uncertainty, parser refusal, and honesty boundaries.
