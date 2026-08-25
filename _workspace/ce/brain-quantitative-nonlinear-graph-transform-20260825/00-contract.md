# Quantitative nonlinear graph-transform contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

## 1. Objective and exact boundary

The predecessor states a conditional normal-hyperbolicity theorem but leaves
`sufficiently small nonlinear remainder` qualitative. This successor gives an
explicit, executable sufficient condition for a nonautonomous triangular
chart. It is a rigorous subcase and diagnostic seam, not a replacement for the
general normal-hyperbolicity theorem.

No brain trajectory, nonlinear vector field, or consciousness observable is
supplied. A positive output certifies declared uniform constants only.

## 2. Frozen nonlinear chart

For integer windows $t$, let $K_t$ be a complete $d$-dimensional base chart
and $Y$ a complete normed fiber. Consider

$$
x_{t+1}=\phi_t(x_t),\qquad
y_{t+1}=B_ty_t+g_t(x_t,y_t),
$$

where each $\phi_t:K_t\to K_{t+1}$ is a bijection with
$\operatorname{Lip}(\phi_t^{-1})\le\mu$ and $\|B_t\|\le b$. Uniformly on the
declared tube,

$$
\|g_t(x,0)\|\le G,\qquad
\|g_t(x,y)-g_t(x',y')\|
\le L_x\|x-x'\|+L_y\|y-y'\|.
$$

The triangular base independence from $y$ is mandatory. A general coupled
base requires the predecessor's full graph-transform/normal-hyperbolicity
hypotheses and is outside this executable subcase.

## 3. Normalize chart scales first

Require positive base and fiber reference scales $X_*,Y_*$. Raw inputs have

- fiber radius $R_{\rm raw}$ and forcing $G_{\rm raw}$ in fiber unit;
- base-to-fiber Lipschitz $L_{x,\rm raw}$ and graph slope
  $\kappa_{\rm raw}$ in fiber/base unit;
- $\mu,b,L_y$ dimensionless.

Form

$$
R=R_{\rm raw}/Y_*,\qquad
G=G_{\rm raw}/Y_*,\qquad
L_x=L_{x,\rm raw}X_*/Y_*,\qquad
\kappa=\kappa_{\rm raw}X_*/Y_*.
$$

All graph-transform inequalities use only these dimensionless quantities.
Common independent rescaling of base and fiber coordinates must leave status
and every normalized margin invariant.

## 4. G1 candidate: explicit invariant graph conditions

Define

$$
q=b+L_y,
$$

and require

$$
q<1,
\tag{G1a}
$$

$$
qR+G\le R,
\tag{G1b}
$$

$$
\mu(q\kappa+L_x)\le\kappa.
\tag{G1c}
$$

The implementation must expose contraction, tube, and slope margins

$$
m_q=1-q,\qquad
m_R=R-(qR+G),\qquad
m_\kappa=\kappa-\mu(q\kappa+L_x).
$$

Only $m_q>0$, $m_R\ge0$, and $m_\kappa\ge0$ may pass. Zero tube or slope
margin proves the theorem but is labelled non-robust; contraction equality is
a non-certificate.

## 5. G2 candidate: graph existence, uniqueness, and tracking

Let $\mathcal G$ be the complete space of graph families
$h_t:K_t\to\overline B_Y(0,R)$ with uniform Lipschitz constant at most
$\kappa$, under the uniform sup metric. Define

$$
(\mathcal Th)_{t+1}(x')=
B_th_t(\phi_t^{-1}x')+
g_t(\phi_t^{-1}x',h_t(\phi_t^{-1}x')).
$$

Under G1, $\mathcal T$ maps $\mathcal G$ into itself and is a contraction with
factor at most $q$. Therefore a unique invariant Lipschitz graph family exists.
Its real graph dimension is the declared base dimension $d$.

For any fiber trajectory over the same base orbit,

$$
\|y_{t+n}-h_{t+n}(x_{t+n})\|
\le q^n\|y_t-h_t(x_t)\|.
$$

This is discrete-window attraction. No physical decay rate is claimed without
a source-locked map from one model window to biological time.

## 6. Required executable outputs

Accept exact built-in integers, `Fraction`, or canonical rational strings;
reject Boolean, float, negative bounds, nonpositive scales/radius, and
nonpositive built-in base dimension. Expose raw inputs, normalized constants,
$q$, all three margins, theorem status, robust-interior Boolean, declared graph
dimension, and an exact tracking-bound function for built-in nonnegative step
counts and exact nonnegative initial distance.

Positive status:
`VERIFIED_QUANTITATIVE_TRIANGULAR_GRAPH_TRANSFORM`.
Named non-certificates distinguish contraction, tube, and slope failures.

## 7. Required controls

- strict positive interior pass;
- exact tube and slope boundary pass with `robust_interior=False`;
- $q=1$ and $q>1$ failures;
- tube and slope failures with $q<1$;
- $q=1$ complete counterexample with nonunique constant invariant graphs;
- exact $q^n$ tracking values, zero steps, invalid steps/distance;
- zero $L_x$, zero slope, and zero forcing cases;
- independent base/fiber unit rescaling invariance;
- invalid dimension, scale, Boolean, float, negative and noncanonical inputs;
- a declared $d=4,5,6$ menu check showing the theorem accepts any positive
  $d$ and therefore does not select those values.

## 8. Claim ceiling

G1--G2 may reach a conditional exact theorem/apparatus status for the declared
triangular chart. They do not prove that a brain flow admits this chart or the
uniform constants, provide $C^{r-1}$ smoothness, handle a base depending on
fiber state, identify a neural manifold, identify consciousness, or select
dimension 4--6. General normal hyperbolicity remains conditional on the
predecessor theorem and empirical premises.

## 9. Execution order

Prove mapping, slope, contraction, uniqueness and tracking; audit boundaries
and units; implement one dependency-free certificate; run focused and
dimensionless checks; promote only after the final gate.
