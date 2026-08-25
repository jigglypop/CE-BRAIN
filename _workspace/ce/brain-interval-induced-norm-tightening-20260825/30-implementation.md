# Induced-norm tightening implementation

Status: COMPLETE

Added `verified_interval_tightening.py` as a separate layer. The predecessor
Frobenius bridge is returned intact inside every result.

The module computes normalized outward dyadic magnitude brackets for every
rectangular entry, exact column/row maxima, an outward square-root enclosure
of their product, and both Frobenius and induced uncertainty uppers. It applies
the frozen minimum and `FROBENIUS` tie policy, then recomputes strict robust
separation, resolvent, family-wide rank status, projector perturbation, and
optional nominal-quadrature total error.

It can issue a positive new tightened status when the preserved predecessor
Frobenius status is negative but the simultaneously computed induced upper
passes the unchanged nominal margin. All brackets and the selected method are
exposed. No network, data, statistical, or scientific-endpoint path exists.
