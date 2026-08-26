# Contract: complete exact Q polynomial factorization

Status: COMPLETE

## Objective

Replace the degree-two/three residual shortcut with a proof-carrying exact
factorization of any supplied finite-degree polynomial over Q whose complete
Kronecker search fits a predeclared candidate-value budget.  Connect the
resulting primary factors to characteristic spectral split discovery.

## Frozen acceptance conditions

1. Exact `int`/`Fraction` coefficients only; constants and the zero polynomial
   are refused.
2. Monic normalization, primitive integer lift, Gauss-lemma reduction, and every
   exact division are exposed.
3. Every irreducibility claim exhausts the finite Kronecker search for degrees
   one through half the current factor degree.
4. Budget exhaustion fails closed before the unexhausted search and produces no
   completeness flag.
5. Equal irreducible factors are grouped into primary powers and their exact
   product reconstructs the normalized input.
6. The characteristic discovery successor must split two irreducible quartic
   atoms and construct the exact projector/rank through the existing strict gate.

## Claim ceiling

This contract does not cover complex/interval coefficients, continuous contour
optimization, empirical matrix provenance, consciousness, or dimension 4--6.
