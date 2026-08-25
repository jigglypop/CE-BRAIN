# Quantitative nonlinear routes and falsifiers

Status: COMPLETE

## Admitted triangular route

Normalize declared chart constants, compute all margins without tolerances,
and distinguish theorem boundary from robust interior. The certificate checks
uniform constants; it does not sample or fit a nonlinear map.

## General coupled-base route

For $x'=Ax+f(x,y)$, the inverse base map depends on the graph. A general graph
transform needs conorm bounds for $A+D_xf$, cross-coupling bounds, projection
conditioning, and a full cone/bunching inequality. This remains under the
predecessor normal-hyperbolicity theorem and cannot reuse G1's status.

## Smoothness route

Lipschitz invariance does not automatically give $C^{r-1}$. Derivative graph
transforms need higher-derivative bounds and spectral bunching at each order.
No smooth-conscious-manifold wording is admitted from the current apparatus.

## Empirical route

A future data contract must define the state, chart, time window, estimator for
all uniform constants, simultaneous uncertainty, held-out falsifier, and
failure behavior. Point estimates of a Jacobian do not prove uniform tube
bounds.

## Falsifiers

- nonpositive reference scales/radius or invalid dimension;
- dimensional constants used without normalization;
- contraction margin nonpositive;
- tube or slope margin negative;
- hidden fiber dependence in the base map;
- interpreting boundary pass as robust interior;
- converting $q^n$ to seconds without a time-scale map;
- reading declared graph dimension as observed neural or consciousness rank.
