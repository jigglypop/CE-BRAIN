# Mixed-unit tensor mobility scale map

Status: COMPLETE

Date: 2026-08-25

## Abstract

The scalar mobility map assumed one homogeneous state unit. This successor allows every finite coordinate to have its own positive reference scale and normalizes a symmetric physical mobility tensor by diagonal congruence. Exact principal minors provide a tolerance-free PSD/PD gate. For a supplied dimensionless gradient, the apparatus returns coordinate velocities and pure-gradient model-potential dissipation only after the PSD gate. Focused validation passed 21 tests, scalar regression 44, dimensionless checks 29, and graph/scale integration 145. The theorem closes the mixed-unit algebra but supplies no neural coordinate units, fitted tensor, metabolic-energy identification, or consciousness result.

## 1. Tensor normalization theorem

Let $S=\operatorname{diag}(X_1,\ldots,X_n)$, $x=S\widetilde x$, $\mathcal V=V_0\widetilde{\mathcal V}$, and $t=t_0\tau$. If

$$
\dot x=-M_{\rm phys}\nabla_x\mathcal V,
$$

then

$$
\frac{d\widetilde x}{d\tau}
=-\widetilde M\nabla_{\widetilde x}\widetilde{\mathcal V},
\qquad
\widetilde M=V_0t_0S^{-1}M_{\rm phys}S^{-T}.
$$

Entry $M_{ij}$ has unit $[x_i][x_j]/([\mathcal V][t])$, so every entry of $\widetilde M$ is dimensionless. At $n=1$ this reduces exactly to the predecessor's scalar formula.

## 2. Exact PSD and dissipation theorem

The congruence by invertible $S^{-1}$ preserves symmetry, PSD, PD, and rank. In finite real dimension, a symmetric matrix is PSD exactly when all principal minors are nonnegative. The apparatus therefore computes all nonempty principal minors over the rationals and reports the first negative subset without floating tolerances.

For dimensionless gradient $g$,

$$
\widetilde v=-\widetilde Mg,
\qquad
\dot x_i=\frac{X_i}{t_0}\widetilde v_i,
$$

and the pure-gradient potential dissipation is

$$
-\frac{d\mathcal V}{dt}
=\frac{V_0}{t_0}g^T\widetilde Mg\ge0.
$$

A singular PSD tensor can have zero dissipation for a nonzero kernel gradient and is not labelled positive definite. The symmetric matrix
$\begin{pmatrix}1&2\\2&1\end{pmatrix}$ has determinant $-3$ and is rejected. Nonsymmetric input is also rejected rather than silently projected onto its symmetric part.

## 3. Evidence and ceiling

The exact certificate passed 21/21 focused tests, 44/44 scalar/tensor regression tests, 29/29 dimensionless tests, and 145/145 graph/scale integration tests. Identity tensors in dimensions 1, 4, 5, and 6 all pass, demonstrating again that the apparatus checks a supplied dimension rather than selecting one.

This result closes finite mixed-unit tensor normalization and pure-gradient dissipation. It does not identify which neural observables are coordinates, estimate their scales or mobility, prove physical reciprocity, include nonsymmetric drift work, identify the model potential with metabolic energy, analyze a brain, identify consciousness, or prefer 4--6 dimensions.

