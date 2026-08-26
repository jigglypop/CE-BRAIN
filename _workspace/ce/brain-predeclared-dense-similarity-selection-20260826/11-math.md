# Mathematics

Status: COMPLETE

## DSEL.1 Canonical finite menu

Let `T_1,...,T_J in Q(i)^(n x n)`, `J>=2`, be exact invertible similarities fixed
before development evaluation.  Since `T` and `aT`, `a!=0`, induce the same
similarity, divide every matrix by its first row-major nonzero entry.  Proportional
duplicates are rejected.  Canonical IDs, normalized entries, and a SHA-256 digest
freeze the menu.

## DSEL.2 Candidate-specific score

For candidate `j`, the dense predecessor supplies condition-translated node lowers
`ell_jk^(D)` and the original chord.  Define
\[
 \delta_j^{(D)}=\min_k\ell_{jk}^{(D)}-\chi_D^+.
\tag{DSEL-1}
\]
Only the dense-only positive margin is eligible.  The common untransformed fallback
is not a selection score.

## DSEL.3 Strict selection and heldout theorem

Require a unique development winner `j_*`, a unique runner-up, and
\[
 \delta_{j_*}^{(D)}-\delta_{j_(2)}^{(D)}>\gamma
\tag{DSEL-2}
\]
for exact preregistered `gamma>=0`.  Equality and order tie-breaking fail.  Evaluate
only `T_(j_*)` on heldout inputs and require its own
\[
 \delta_{j_*}^{(H)}>0.
\tag{DSEL-3}
\]
Then the selected dense geometry conditionally certifies the development and
heldout interval families through the predecessor contour/Riesz theorem.

Proof.  Each score is already an original-coordinate strict full-circle margin by
the dense theorem.  Finite exact comparison proves (DSEL-2); a single heldout call
proves (DSEL-3) without a second search.  The conclusion is their conjunction and
creates no empirical provenance.  QED.

## DSEL.4 Refusal completeness

No eligible candidate, only one eligible candidate, winner tie, runner tie,
advantage equality, changed/forged menu, and selected-candidate heldout failure all
stop before promotion.
