# BA-ERC1-E3a route decision

Status: COMPLETE

| route | decision | reason |
|---|---|---|
| Equal-arclength three-branch observation versus branch-shared oracle projection | `SELECTED / E3A_AUTHORIZED` | Cheapest exact test of whether the measurement map preserves a cable-only antisymmetric mode. |
| Branch mean only | `NO-GO CONTROL` | Its kernel contains every antisymmetric branch vector; it cannot test cable versus point structure. |
| Fit a scalar ODE before checking observation rank | `REJECTED_AS_WEAKER` | The per-time oracle projection is already a stronger scalar baseline. |
| Add noise, filters, missing channels, or sensor gains | `DEFERRED_TO_E4` | These are measurement-stress variables, not needed for the analytic seam. |
| Finite-state versus history-kernel synapse | `LOCKED_TO_E3B` | Open only if E3a shows the necessary branch information survives observation. |
| Real data or consciousness/AGI interpretation | `PROHIBITED_HERE` | No empirical endpoint is opened.

Execution order: freeze hashes; machine-check projection algebra; score S1/A0/M1; require the collapsed A0 no-go; emit one fail-closed receipt; audit the stable result. PASS can only make E3b separately contractable.
