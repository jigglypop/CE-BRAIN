# Quantitative triangular nonlinear graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The predecessor's general conditional slow-manifold theorem used the phrase
`sufficiently small nonlinear remainder`. This successor replaces that phrase
with exact inequalities for a nonautonomous triangular Lipschitz chart. The
conditions prove a unique invariant attracting graph, its declared real base
dimension, exact robustness margins, and $q^n$ tracking. Focused validation
passed 26 tests, adjacent finite-subspace validation 43, and the dimensionless
gate 24. The result certifies declared constants, not a brain flow, smooth
manifold, consciousness, or dimension 4--6.

## 1. Chart and normalized constants

Consider

$$
x_{t+1}=\phi_t(x_t),\qquad
y_{t+1}=B_ty_t+g_t(x_t,y_t),
$$

with $\operatorname{Lip}(\phi_t^{-1})\le\mu$, $\|B_t\|\le b$,
$\|g_t(x,0)\|\le G$, and

$$
\|g_t(x,y)-g_t(x',y')\|
\le L_x\|x-x'\|+L_y\|y-y'\|.
$$

Base and fiber scales $X_*,Y_*$ normalize raw radius, forcing, cross-slope,
and graph slope as

$$
R=R_{\rm raw}/Y_*,\qquad
G=G_{\rm raw}/Y_*,\qquad
L_x=L_{x,\rm raw}X_*/Y_*,\qquad
\kappa=\kappa_{\rm raw}X_*/Y_*.
$$

Every subsequent quantity is dimensionless and invariant under independent
base/fiber coordinate rescaling.

## 2. Explicit sufficient conditions

Set $q=b+L_y$. The complete certificate is

$$
q<1,
$$

$$
qR+G\le R,
$$

$$
\mu(q\kappa+L_x)\le\kappa.
$$

It exposes

$$
m_q=1-q,\qquad
m_R=R-(qR+G),\qquad
m_\kappa=\kappa-\mu(q\kappa+L_x).
$$

Contraction must be strict. Tube and slope equality still prove invariance of
the closed graph class but are labelled `robust_interior=False`.

## 3. Proof and tracking

For graph families $h_t$ with $\|h_t\|_\infty\le R$ and
$\operatorname{Lip}h_t\le\kappa$, define

$$
(\mathcal Th)_{t+1}(x')=
B_th_t(\phi_t^{-1}x')+
g_t(\phi_t^{-1}x',h_t(\phi_t^{-1}x')).
$$

The tube inequality bounds its sup norm. The slope inequality follows from
the inverse-base Lipschitz factor. For two graphs,

$$
\|\mathcal Th-\mathcal Tk\|_\infty
\le q\|h-k\|_\infty.
$$

Banach's theorem gives a unique invariant Lipschitz graph family. Its graph is
bi-Lipschitz to the declared $d$-dimensional base chart and therefore has real
dimension $d$. Along a common base orbit,

$$
\|y_{t+n}-h_{t+n}(x_{t+n})\|
\le q^n\|y_t-h_t(x_t)\|.
$$

For $q=1$, identity fiber dynamics has every constant graph invariant, so
uniqueness and attraction fail. This proves strictness is necessary.

## 4. Implementation and evidence

`quantitative_graph_transform.py` accepts exact rational constants, rejects
invalid scales/types/bounds, reports all normalized quantities and margins,
distinguishes contraction/tube/slope failures, and computes exact tracking
bounds only from a passing certificate.

- focused behavior: 26/26;
- adjacent finite-subspace/graph-transform behavior: 43/43;
- dimensionless gate: 24/24;
- exact theorem fixture: PASS;
- research final gate: pending this report, checked next.

The executable dimension menu passes $d=1,4,5,6,100$ under the same constants.
It therefore demonstrates nonselection: the theorem preserves a supplied base
dimension and cannot explain why consciousness should be 4--6-dimensional.

## 5. Strict ceiling

The result is a precise triangular Lipschitz subcase. If base dynamics depends
on fiber state, the same-base contraction proof is unavailable and the full
normal-hyperbolicity/cone conditions are needed. Higher smoothness requires
derivative bunching. No uniform constants have been estimated from neural
data, and $q^n$ cannot be converted to seconds without a physical time map.

Thus the run strengthens the candidate equation but supplies no nonlinear
brain-manifold observation, consciousness identification, or preferred rank.

## Reproducibility record

- Contract: `00-contract.md`
- Proof and counterexamples: `11-math.md`
- General/smooth/empirical routes: `12-routes.md`
- Stable audit: `20-audit.md`
- Implementation: `30-implementation.md`
- Validation: `31-validation.md`
