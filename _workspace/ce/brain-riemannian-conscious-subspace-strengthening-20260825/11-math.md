# Mathematics lane — history edge metric and variable-rank subspace

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

Independent definition-to-proof audit. These are conditional mathematical results and L0 fixtures only; they do not validate brain geometry, consciousness, or a preferred dimension.

## Definitions, regularity, and units

For finite/countable $V,E$, finite $p_v,q_e$, and positive weights $\rho_e$,

$$
\mathcal H=\bigoplus_{v\in V}\mathbb R^{p_v}\oplus\bigoplus_{e\in E}L^2_{\rho_e}(( -\infty,0],\mathbb R^{q_e}).
$$

Assume $A_{0,x}=A_{0,x}^*$, $m_0I\preceq A_{0,x}\preceq M_0I$ with $m_0>0$, bounded $D_e$, and $K_e(x)=K_e(x)^*\succeq0$. Define

$$
A_x(b)=A_{0,x}+\sum_e b_eD_e^*K_e(x)D_e,\qquad g_x^{(b)}(u,v)=\langle u,A_x(b)v\rangle.
$$

The necessary local condition is $\sum_e\sup_{x\in B}\|D_e\|^2\|K_e(x)\|<\infty$. A $C^r$ claim also needs $A_0,K_e$ and their derivative series through order $r$ locally uniformly convergent in operator norm. Otherwise the sum can be only a quadratic form. Coordinates must be standardized: $A$, $D^*KD$, $b$, resolvent $z$, $\bar\Delta=\Delta/t_0$, $\lambda$, $c_d^\perp$, and $d_{\rm eff}$ are dimensionless. In physical coordinates, $A^{-1}\nabla\mathcal V$ needs an explicit mobility/time scale; this record is P2.

## Proof checks

**Theorem 1 — strong metric.** The assumptions give bounded self-adjoint $A_x(b)$ and

$$
m_0I\preceq A_x(b)\preceq\left(M_0+\sum_e\|D_e\|^2\|K_e(x)\|\right)I.
$$

Every edge term is self-adjoint PSD; norm summability gives a bounded PSD sum and $A_0$ supplies the lower frame bound. Hence $g^{(b)}$ is a strong Riemannian metric under the stated smoothness; $A^{-1}$ is bounded and $D(A^{-1})[H]=-A^{-1}HA^{-1}$. This is not an identified biological metric.

**Theorem 2 — weakening/removal.**

$$
\|A_x(b')-A_x(b)\|\le\epsilon_x:=\sum_e|b'_e-b_e|\|D_e\|^2\|K_e(x)\|,
$$

and $|g_x^{(b')}(u,u)-g_x^{(b)}(u,u)|\le\epsilon_x\|u\|^2$. If $\epsilon_x\le\epsilon<m_0$ on a curve, then

$$
(1-\epsilon/m_0)g^{(b)}\preceq g^{(b')}\preceq(1+\epsilon/m_0)g^{(b)}.
$$

The square-root factors bound length and distance. This concerns metric cost. Setting $b_e=0$ separately changes graph reachability; it is not smooth curvature across deletion.

**P0-A — baseline-free degeneracy.** In $\mathbb R^2$, $A_0=0$, $D=(1,-1)$, $K=1$ gives $D^*KD=\begin{pmatrix}1&-1\\-1&1\end{pmatrix}$, with kernel $(1,1)$; deletion gives zero. PSD edges/connectivity do not prove a strong metric.

**Proposition 3 — directed drift.** For

$$
\dot x=-A_x^{-1}\nabla\mathcal V+S_xx+R_x(h),
$$

$$
\frac{d\mathcal V}{dt}=-\langle\nabla\mathcal V,A_x^{-1}\nabla\mathcal V\rangle+\langle\nabla\mathcal V,S_xx\rangle+\langle\nabla\mathcal V,R_x\rangle.
$$

**P0-B — skew is not zero-work.** With $S=\begin{pmatrix}0&-1\\1&0\end{pmatrix}$, $x=(1,0)$, and $\mathcal V(x)=x_2$, $S^*=-S$ but $\langle\nabla\mathcal V,Sx\rangle=1$. Zero work requires $D\mathcal V(x)[Sx]=0$, for example $Sx=J\nabla\mathcal V$ with $J^*=-J$. Directed transport and the symmetric metric are distinct.

**Theorem 4 — Riesz subspace.** In the complexification, if bounded $U$ has a resolvent contour $\Gamma$ isolating finite algebraic multiplicity $d$,

$$
P=\frac{1}{2\pi i}\oint_\Gamma(zI-U)^{-1}dz
$$

satisfies $P^2=P$, $PU=UP$, and $\operatorname{rank}P=d$. With $R=\sup_{z\in\Gamma}\|(zI-U)^{-1}\|$, if $R\|E\|<1$, the same contour for $U+E$ has the same rank and

$$
\|P(U+E)-P(U)\|\le\frac{\operatorname{len}(\Gamma)}{2\pi}\frac{R^2\|E\|}{1-R\|E\|}.
$$

This is resolvent identity plus Neumann series. A nonlinear slow manifold needs uniform dichotomy or normal hyperbolicity (P1).

**P0-C — loops do not select 4–6.** Repeated recurrent blocks $\dot a_n=-a_n+b_n$, $\dot b_n=-b_n+a_n$ on $\ell^2(\mathbb N;\mathbb R^2)$ have $0,-2$ at infinite multiplicity and no isolated finite-rank cluster. A diagonal system can have any rank $d$ center subspace without a loop. Thus neither loops nor edge geometry forces $d=4$ or $4\le d\le6$.

**P0-D — concentration repair (now applied in the revised contract).** A Riesz projection need not be orthogonal. For

$$
P=\begin{pmatrix}1&2\\0&0\end{pmatrix},\qquad C=\begin{pmatrix}1&1\\1&1\end{pmatrix}\succeq0,
$$

$P^2=P$ but $\operatorname{tr}(PCP)/\operatorname{tr}C=3/2>1$. Thus the retired, unorthogonalized universal concentration claim is false. The revised contract correctly uses

$$
c_d^\perp=\frac{\operatorname{tr}(Q_dCQ_d)}{\operatorname{tr}C},
$$

where $Q_d$ is the orthogonal projection onto $\operatorname{Ran}P_d$. For trace-class $C\succeq0$ with $\operatorname{tr}C>0$, $0\le c_d^\perp\le1$. This removes only the retired universal-boundedness parent, not spectral-subspace existence.

**Theorem 5 — effective dimension.** For trace-class $\widetilde G\succeq0$ and $\lambda>0$,

$$
d_{\rm eff}(\lambda)=\sum_j\frac{\mu_j}{\mu_j+\lambda},\qquad0\le d_{\rm eff}(\lambda)\le\operatorname{rank}\widetilde G.
$$

Finiteness follows from $\mu_j/(\mu_j+\lambda)\le\mu_j/\lambda$; it decreases with $\lambda$ and tends to hard rank as $\lambda\downarrow0$. It is not ambient/manifold dimension. The observed pullback $J^*WJ$ remains subject to the passive quotient no-go.

**Theorem 6 — lossless no-go.** A differentiable lossless local chart $f:O\subset\mathcal H\to\mathbb R^d$ with local inverse needs injective $Df_x$, impossible by rank-nullity for infinite-dimensional $\mathcal H$ or finite dimension greater than $d$. A homeomorphic chart also contradicts local topological dimension. A many-to-one quotient is permitted but not lossless. This preserves the predecessor no-gos and is consistent with finite-family/complete-active escape routes because those add restrictions/interventions.

**Convention 7 — real rank of a real return operator.** Let $U$ be real-linear and $U_{\mathbb C}$ its complexification. A real eigenvalue contributes its complex algebraic multiplicity unchanged to real dimension. A nonreal eigenvalue $\lambda$ must be paired with $\bar\lambda$; if one representative has multiplicity $m$, the pair contributes $2m$ real dimensions. Therefore

$$
d_{\mathbb R}=\sum_{\lambda\in\mathbb R}m_{\rm alg}(\lambda)+2\sum_{\operatorname{Im}\lambda>0}m_{\rm alg}(\lambda).
$$

Complex conjugation maps the generalized eigenspace of $\lambda$ onto that of $\bar\lambda$, whose fixed real form has dimension $2m$; a real generalized eigenspace has dimension $m$. Freeze this convention before menu comparison. It does not turn a complex rank count or observed hard rank into consciousness dimension.

**Proposition 8 — physical nondimensionalization.** Let $x=X_0\widetilde x$, $\mathcal V=V_0\widetilde{\mathcal V}$, and $t=t_0\widetilde t$, with positive reference scales. For $\dot x=-\mu_0A^{-1}\nabla_x\mathcal V+\cdots$, choose

$$
\mu_0=\frac{X_0^2}{V_0t_0}.
$$

Since $\nabla_x\mathcal V=(V_0/X_0)\nabla_{\widetilde x}\widetilde{\mathcal V}$,

$$
\frac{d\widetilde x}{d\widetilde t}=-A^{-1}\nabla_{\widetilde x}\widetilde{\mathcal V}+\cdots.
$$

This is dimensional algebra, not biological calibration. Identifying $X_0,V_0,t_0$, physical mobility, and measurement mapping remains P2.

**Theorem 9 — conditional nonlinear local slow-manifold candidate.** Let a $C^r$ flow ($r\ge2$) near a reference trajectory have a $C^{r-1}$ invariant splitting $E^s_t\oplus E^c_t\oplus E^u_t$ for its variational cocycle, uniformly bounded projections, and a uniform exponential dichotomy/normal-hyperbolicity gap: stable/unstable rates dominate center rate by a positive margin. If the nonlinear derivative in a fixed tube is sufficiently small after removing the linear part, then a locally invariant $C^{r-1}$ graph tangent to $E^c_t$ exists and has real dimension $d_{\mathbb R}$.

Proof sketch: write a nearby state as $(\xi_c,\xi_{su})$, propagate Lipschitz graphs $\xi_{su}=h_t(\xi_c)$ across one normalized window, and use the gap plus nonlinear Lipschitz bound to make graph transform contractive. Its fixed graph is invariant; standard graph-transform bootstrap gives regularity. A closed gap, unbounded projections, or a large remainder invalidates this conclusion. No premise is asserted for a brain recording; Riesz isolation alone is insufficient.

**Theorem 10 — finite nonnormal contour-Riesz route (conditional).** Let $U\in\mathbb R^{n\times n}$, let $\Gamma=\{c+re^{i\theta}:0\le\theta<2\pi\}$ avoid $\sigma(U)$, and let its interior select an isolated eigenvalue cluster. The exact complex Riesz projector is

$$
P=\frac{1}{2\pi i}\oint_\Gamma(zI-U)^{-1}dz
=\frac{1}{2\pi}\int_0^{2\pi}re^{i\theta}(z(\theta)I-U)^{-1}d\theta.
$$

For nodes $\theta_k=2\pi k/N$, its circle-trapezoidal approximation is

$$
P_N=\frac1N\sum_{k=0}^{N-1}re^{i\theta_k}(z_kI-U)^{-1},\qquad z_k=c+re^{i\theta_k}.
$$

Exact $P$, not $P_N$, is idempotent and commutes with $U$. If $c,r$ are real and the selected cluster is closed under conjugation, then $P$ has a real range. Nonreal eigenvalues must be selected with their conjugates; their real range dimension follows Convention 7. A finite floating computation should report the residual $\|\operatorname{Im}P_N\|$, and obtain the orthogonal range projector $Q$ from a realified numerical range basis. It must not substitute $Q$ for oblique $P$ in the Riesz identity, nor substitute $P$ for $Q$ in concentration.

For implementation the following are certificates with explicitly different force: sampled separation $\min_{k,j}|z_k-\lambda_j|$, sampled maximum resolvent norm $\max_k\|(z_kI-U)^{-1}\|$, $\|P_{2N}-P_N\|$, idempotence $\|P_N^2-P_N\|$, commutator $\|UP_N-P_NU\|$, singular-value/rank conditioning of realification, and imaginary residual. They are finite numerical evidence only. A sampled separation is not an all-contour separation unless accompanied by an analytic enclosure; for a circle with certified eigenvalues an exact geometric margin is $\min_j\big||\lambda_j-c|-r\big$. Likewise, $N$ versus $2N$ agreement does not itself bound $\|P_N-P\|$.

One sufficient quadrature upgrade is an analytic strip certificate. If the periodic integrand $g(\theta)=re^{i\theta}(z(\theta)I-U)^{-1}$ extends analytically to $|\operatorname{Im}\theta|<a$ and obeys $\|g\|\le M$ there, then

$$
\|P_N-P\|\le\frac{2M}{e^{aN}-1}.
$$

This follows by bounding the Fourier coefficients of $g$ and summing the aliases at nonzero multiples of $N$. Without a certified $a,M$, the inequality may not be claimed.

For perturbation $E$, define $R_\Gamma=\sup_{z\in\Gamma}\|(zI-U)^{-1}\|$. If $R_\Gamma\|E\|<1$, then $\Gamma\subset\rho(U+E)$, the exact selected rank is unchanged, and

$$
\|P(U+E)-P(U)\|\le r\frac{R_\Gamma^2\|E\|}{1-R_\Gamma\|E\|}.
$$

The condition is on the full-contour resolvent, not eigenvalue distance alone.

**Nonnormal diagonalizable fixture.** Set

$$
V=\begin{pmatrix}1&0&10\\0&1&0\\0&0&1\end{pmatrix},\quad
U=V\operatorname{diag}(0.2,0.8,1.4)V^{-1}
=\begin{pmatrix}0.2&0&12\\0&0.8&0\\0&0&1.4\end{pmatrix}.
$$

The real circle $c=0.5,r=0.4$ encloses $0.2,0.8$ and has geometric eigenvalue margin $0.1$. Its exact Riesz projector is

$$
P=V\operatorname{diag}(1,1,0)V^{-1}
=\begin{pmatrix}1&0&-10\\0&1&0\\0&0&0\end{pmatrix},
$$

which is idempotent but oblique; its orthogonal range projector is $Q=\operatorname{diag}(1,1,0)$. This is a sound finite fixture for a future implementation, not an empirical model.

**Counterexamples retained before implementation.** A contour crossing an eigenvalue makes the resolvent and $P_N$ undefined. For $U=\begin{pmatrix}0&M\\0&1\end{pmatrix}$, a circle around zero can have a positive eigenvalue margin while $\|(zI-U)^{-1}\|$ grows with $M$; a perturbation far smaller than that margin can move eigenvalues across the contour. Thus eigenvalue distance does not control pseudospectral stability. Finally, for scalar $U=(0.9)$ and unit circle, exact $P=1$ but $P_N=(1-0.9^N)^{-1}$, so coarse quadrature can be badly non-idempotent despite no contour crossing. These kill any route that promotes sampled gap, sampled rank, or a single coarse $P_N$ to exact Riesz/rank evidence.

## Reproducibility and findings

The dependency-free PowerShell fixture `artifacts/spot_checks.ps1` ran twice with identical JSON and exit code 0: **POWERSHELL_L0_PASS**. The policy-allowed Python 3.14.2 NumPy fixture `artifacts/spot_checks.py` subsequently also ran twice with identical JSON and exit code 0: **PYTHON_NUMPY_PARITY_PASS**. Both confirm baseline coercivity 1, local squared-length difference 0.247, baseline-free degeneracy, rank 2 before/after, oblique concentration 1.5, corrected orthogonal concentration 0.5, and effective dimension 1.5. PowerShell reports the rigorous operator-norm upper bound 1.8; NumPy reports the actual spectral perturbation norm 1.5244997998398395 and perturbed minimum eigenvalue 1.2554396639452299. The historical unavailable-interpreter attempt and successful rerun are both retained in `artifacts/spot-check-attempt.md`. These are deterministic L0 algebra witnesses only, not mathematical proofs or empirical brain/consciousness validation.

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-riemannian-conscious-subspace-strengthening-20260825\artifacts\spot_checks.py
```

```powershell
& .\_workspace\ce\brain-riemannian-conscious-subspace-strengthening-20260825\artifacts\spot_checks.ps1
```

P0: baseline requirement, skew-drift requirement, no fixed rank from loops, and corrected concentration. P1: nonlinear-manifold and real/complex rank conventions. P2: physical scale and mobility record.
