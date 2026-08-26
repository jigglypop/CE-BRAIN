# Mathematics

Status: COMPLETE

## WSEL.1 Frozen menu

Let
\[
  \mathcal W=(W_1,\ldots,W_J),\qquad
  W_j=\operatorname{diag}(w_{j1},\ldots,w_{jn}),\quad w_{ji}>0,
\]
be fixed before development evaluation, with `J >= 2`.  Divide every vector by
its smallest component.  Proportional vectors are then identical and duplicates
are rejected.  Canonical candidate identifiers, sorted normalized rational
weights, and their SHA-256 digest identify the frozen menu; the digest is identity,
not empirical provenance.

## WSEL.2 Candidate-specific score

For development node `k`, the predecessor weighted theorem returns the translated
original-coordinate lower
\[
  \ell^{(D)}_{jk}=\frac{1}{\kappa_2(W_j)M'^{(D)}_{2,jk}}.
\]
Define the weight-specific full-circle margin
\[
  \delta^{(D)}_j=\min_k\ell^{(D)}_{jk}-\chi_D^+ .
\tag{WSEL-1}
\]
Candidate `j` is eligible only when every transformed node contracts and
`delta_j^(D) > 0` exactly.

The score must be (WSEL-1), not the predecessor's best-of-two margin
`min_k max(ell_uk, ell_jk)-chi`.  The latter retains a common unweighted fallback
and can make distinct weights tie identically even when their own certificates
differ.  Using it would make the declared selection rule degenerate.

## WSEL.3 Strict development selection

For a preregistered exact `gamma >= 0`, require
\[
 j_* = \operatorname*{arg\,max}_{j:\delta_j^{(D)}>0}\delta_j^{(D)}
\]
to be unique.  Require the runner-up to be unique as well and
\[
  \delta_{j_*}^{(D)}-\delta_{j_{(2)}}^{(D)}>\gamma.
\tag{WSEL-2}
\]
Equality fails.  Candidate order is never a tie breaker.

## WSEL.4 Selected-only heldout theorem

Using the independently supplied heldout interval family and witnesses, evaluate
only `W_(j_*)` and form
\[
  \delta_{j_*}^{(H)}=\min_k\ell^{(H)}_{j_*k}-\chi_H^+ .
\tag{WSEL-3}
\]
If (WSEL-1)--(WSEL-3) pass, then both development and heldout interval families
are contour-free under the selected diagonal geometry, with their predecessor
Riesz-rank conclusions.  In particular, heldout success requires
`delta_(j_*)^(H) > 0` for the selected weight itself.  An unweighted fallback may
not rescue a failed selected weight.

Proof.  Each positive margin is exactly the predecessor full-circle theorem after
the mandatory `kappa_2(W)` translation.  Finite exact comparison proves the unique
development maximizer and (WSEL-2).  Because no alternative is evaluated on the
heldout input, (WSEL-3) is a confirmation of the frozen selected candidate rather
than a second selection.  The conclusion is the conjunction of the two conditional
predecessor certificates.  No statistical independence or empirical provenance is
created by this deterministic argument.  QED.

## WSEL.5 Complete refusal cases

1. Equal maximum scores: no winner exists; ordering cannot repair it.
2. Equal runner-up scores: the preregistered comparison target is not unique.
3. Advantage equal to `gamma`: strict inequality (WSEL-2) fails.
4. No positive candidate margin: node success or a nonpositive circle margin is
   not a certificate.
5. Selected weight fails (WSEL-3): an unweighted heldout fallback and all untested
   alternatives are irrelevant.
