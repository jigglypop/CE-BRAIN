# Mathematics lane

Status: COMPLETE

## T1. Tensor normalization

From $x=S\widetilde x$ and $\mathcal V=V_0\widetilde{\mathcal V}$,

$$
\dot x=\frac{S}{t_0}\frac{d\widetilde x}{d\tau},
\qquad
\nabla_x\mathcal V=V_0S^{-T}\nabla_{\widetilde x}\widetilde{\mathcal V}.
$$

Substitution in (T1) and multiplication by $t_0S^{-1}$ prove (T2)--(T3). Entry $ij$ has factor $V_0t_0/(X_iX_j)$, exactly cancelling the declared unit of $M_{ij}$.

## T2. PSD preservation and dissipation

$\widetilde M$ is a positive scalar multiple of a congruence of $M_{\rm phys}$. Congruence by invertible $S^{-1}$ preserves symmetry, PSD, PD, and rank. For the pure gradient term,

$$
\frac{d\mathcal V}{dt}
=\nabla_x\mathcal V^T\dot x
=-\nabla_x\mathcal V^TM_{\rm phys}\nabla_x\mathcal V,
$$

and substitution proves (T5). PSD gives nonnegative dissipation; singular PSD permits equality for nonzero gradients in its kernel.

## T3. Exact finite gate and counterexamples

For real symmetric matrices, nonnegativity of every principal minor is equivalent to PSD. Strict positivity of every nonempty principal minor is equivalent to PD. Thus exact rational determinants provide a complete finite gate without floating eigenvalue tolerances.

$\begin{pmatrix}1&2\\2&1\end{pmatrix}$ is symmetric but has determinant $-3$, so a negative dissipation direction exists and the energy inequality cannot be asserted. A nonsymmetric matrix has an antisymmetric component that contributes no quadratic dissipation but changes velocity; it is excluded from this symmetric mobility theorem rather than silently symmetrized.

Verdict: mixed-unit tensor normalization, exact PSD status, pointwise velocity, and pure-gradient dissipation are conditional theorems. Biological calibration remains open.

