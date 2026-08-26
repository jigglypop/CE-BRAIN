# Final report

Status: COMPLETE

Stored binary64 approximate inverse witnesses can now be reproduced exactly
as rational complex matrices and passed to the existing residual theorem.
This removes decimal-print ambiguity and makes a poor floating witness fail at
the same exact contraction gate as any rational witness.

The result is intentionally narrower than a full solver audit.  It verifies
the stored values and their residual certificate, not the algorithm,
operation rounding mode, hardware/BLAS, empirical matrix, or uncertainty
coverage.  Those provenance layers remain explicit external inputs.
