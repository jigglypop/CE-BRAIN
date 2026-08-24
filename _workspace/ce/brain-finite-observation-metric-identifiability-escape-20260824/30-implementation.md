# BA-OBS-ID1 implementation — deterministic metric-identifiability witness

Status: COMPLETE

`artifacts/validate_metric_escape.py` implements only the frozen protocol in
`00-contract.md`: the dimensionless two-state invariant subsystem, the three
fixed inputs, constant-input RK4, the fixed grid/golden trajectory fit, and
the central-difference train Gramian.  It writes the deterministic machine
receipt `artifacts/metric_escape_receipt.json` and exits nonzero whenever a
contract gate fails.

The final receipt SHA-256 is
`9adc50dac7df5ba87a75a357c2414dd0575a1777621eef59ffeb76075dd54b49`;
the generating script SHA-256 is
`5e6f5f71dffdb3a2d0be84a4b614ec1518a167b1440721e245b98d4e3b061d8b`.

The first execution STOPped because the implementation evaluated the
negative-control loss against the active TRAIN schedules.  This was an
implementation-only mismatch with the already frozen `NEGATIVE-ZERO`
contract, not a failure of the model, thresholds, data, or formula.  The
repair changed only that loss evaluation to the zero-input schedule; it made
no change to the protocol, truths, thresholds, integrator, or estimator.  The
final code comment at that calculation records the same distinction.

The implementation does not estimate $y''(0)$ from finite samples.  W1 uses
that derivative analytically; this artifact instead supplies a separate,
trajectory-fitting reproducibility witness under the preregistered split.

Machine PASS means that this exact synthetic program met its frozen numerical
gates.  It is not a proof of T3/W1 and is not empirical evidence about brains,
consciousness, self, or AGI.
