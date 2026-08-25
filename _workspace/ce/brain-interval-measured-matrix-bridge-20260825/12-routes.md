# Interval bridge routes and falsifiers

Status: COMPLETE

## R1 -- admitted global norm-ball bridge

Use exact rectangular radii, normalize first, enclose the Frobenius radius,
and require strict margin positivity. This route is simple, dependency-free,
and covers the entire box. It may fail conservatively for large or sparse
matrices even when a sharper structured analysis would pass.

Positive status requires every exact check. Increasing square-root precision
after a conservative failure may be reported only as a new invocation with
the precision exposed; changing the uncertainty box after seeing the result
is a different claim.

## R2 -- induced row/column candidate

For $C_{ij}=\sqrt{a_{ij}^2+b_{ij}^2}$,

$$
\|\Delta\|_2\le\sqrt{\|C\|_1\|C\|_\infty}.
$$

With individually outward-rounded rational uppers $C_{ij}^+$, the same bound
is executable and can improve on Frobenius for structured boxes. It adds many
square-root enclosures and is retained as a candidate optimization, not as a
condition silently substituted after R1 fails.

## R3 -- residual/Krawczyk candidate

A verified approximate inverse or invariant-subspace residual can produce a
local certificate tighter than a global box norm. Such a route must expose
outward rounding, residuals, condition bounds, and its own existence/uniqueness
hypotheses. It cannot inherit the current status merely by reusing the word
`verified`.

## R4 -- empirical uncertainty calibration

To turn $a,b$ into measurement statements, a later contract must freeze the
estimator, sampling unit, preprocessing, dependence structure, missingness,
simultaneous-coverage target, confidence level, and held-out policy. Pointwise
standard errors do not automatically give simultaneous entrywise coverage,
and a deterministic interval theorem cannot supply statistical calibration.

## Falsifiers

- nominal full-circle certificate unavailable;
- normalized uncertainty upper greater than or equal to the nominal margin;
- any negative, nonexact, malformed, or shape-mismatched bound;
- raw-unit dyadic rounding that changes status under unit rescaling;
- reporting a non-certificate as contour crossing;
- reporting rank stability as small projector motion;
- dropping either uncertainty or nominal quadrature error in I3;
- interpreting a declared interval as measured coverage without R4.
