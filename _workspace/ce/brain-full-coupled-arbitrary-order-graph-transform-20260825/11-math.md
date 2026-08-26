# Mathematics lane

Status: COMPLETE

## FCG.1 Exact same-version contacts

Write the normalized C0 constants as

$$
q=b+g_y,
\qquad
\alpha=\mu^{-1}-f_x-f_y\Lambda_1,
\qquad
r_x={f_y\over\alpha},
$$

$$
s=q\Lambda_1+g_x,
\qquad
q_0=q+{s f_y\over\alpha}<1.
$$

The derivative certificate must use the same base dimension, the same
`alpha`, the same first graph bound `Lambda_1`, and the same `r_x` in both raw
base and fiber envelopes.  Its first raw fiber composite must dominate `s`.
These are equalities between two records of one map version, not perturbative
margins; their robustness flag is therefore false even when all inequalities
inside both predecessors are strict.

## FCG.2 Full synchronous recurrence

Let `Delta_j^(m)` bound the distance between two graph iterates at derivative
order `j`.  The C0 theorem supplies

$$
\Delta_0^{(m+1)}\le q_0\Delta_0^{(m)}.
$$

For each `1<=j<=n`, the implicit finite-jet certificate supplies a complete
upper-triangular row `c_(jk)`:

$$
\Delta_j^{(m+1)}
\le\sum_{k=0}^{j}c_{jk}\Delta_k^{(m)},
\qquad c_{jj}<1.
$$

Every right-hand side is evaluated from the same old vector.  This matters:
preserving `Delta_0` would discard the C0 contraction, while updating higher
rows in place would no longer be the proved synchronous recurrence.

## FCG.3 Local and matched lift

The local lift requires exact identity with the derivative certificate and
the C0 base reference scale.  The matched lift additionally requires exact
identity with the local certificate and the C0 fiber reference scale.  Open
collar margins can be robust; exact constant and boundary contacts cannot.

## FCG.4 Consequence and boundary

The joined certificate proves conditional finite-Cn invariance and
convergence bounds for one supplied coupled map version.  It is order-generic
for every finite supplied `n>=2`.  Dimension is passed through as an input,
not inferred.  Neither a finite order nor an interface identity proves
C-infinity, analytic regularity, neural realizability, or consciousness.
