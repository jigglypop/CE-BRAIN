# BA-ERC1-E2 mathematics — exact star modes and two discretizations

Status: COMPLETE

## 1. Definitions

`[Definition]` Let Γ be a three-edge equilateral metric star. Each edge has outward coordinate (s\in[0,1]), with the common vertex at (s=0). The dimensionless passive generator is

$$
\mathcal L u=D_*u_{ss}-\kappa_*u,
\qquad D_*=0.2,\quad \kappa_*=0.3,
$$

on the domain with centre continuity, Kirchhoff condition ∑e (u'_e(0)=0), and distal Neumann condition (u'_e(1)=0).

`[Dimensionless audit]` If (s=x/L_0), θ=(t/T_0), (D_*=DT_0/L_0^2), and κ*=κ(T_0), then (D_*\lambda\theta) and (\kappa_*\theta) are dimensionless. No dimensional quantity enters an exponential, logarithm, probability, or fixed-point core at E2.

## 2. Exact modes

`[Theorem: symmetric sector]` For integer (n\ge0),

$$
\phi^{S,n}_e(s)=\cos(n\pi s)
$$

is a star eigenfunction with (\lambda_{S,n}=(n\pi)^2). All three centre values equal one; the centre derivatives vanish; and (\sin(n\pi)=0) makes each distal derivative vanish.

`[Theorem: antisymmetric sector]` For integer (n\ge0) and coefficients (c_e) satisfying ∑e (c_e=0),

$$
\phi^{A,n}_e(s)=c_e\sin((n+\tfrac12)\pi s)
$$

is an eigenfunction with $\lambda_{A,n}=((n+\tfrac12)\pi)^2$. All centre values are zero, hence continuous. The centre flux sum is $(n+\tfrac12)\pi\sum_e c_e=0$, and the distal derivative vanishes because $\cos((n+\tfrac12)\pi)=0$. For unequal conductance weights the correct constraint would be $\sum_e a_ec_e=0$; E2 deliberately freezes equal edges and equal weights.

`[Derived solution]` Every pure mode evolves as

$$
u(\theta)=\exp[-(D_*\lambda+\kappa_*)\theta]\phi.
$$

The M1 exact field is the linear superposition of the S1 and A0 fields with their distinct decay factors. No single-decay fit is applied to M1.

## 3. Passive dissipation

`[Conditional theorem]` For a sufficiently regular solution,

$$
\frac{d}{d\theta}\frac12\sum_e\int_0^1u_e^2\,ds
=-D_*\sum_e\int_0^1|u'_e|^2\,ds
-\kappa_*\sum_e\int_0^1u_e^2\,ds\le0.
$$

Integration by parts leaves distal terms zero. At the centre, continuity gives a common vertex value and Kirchhoff makes that value times the summed outward derivative zero. This theorem supplies the energy-direction gate; the numerical tolerance accounts only for floating arithmetic.

## 4. Conservative finite volume

`[Derivation]` With (h=1/N), centre cells (s_j=(j+1/2)h), and common vertex face value

$$
v=\frac13\sum_eu_{e,0},
$$

the centre-face gradients are (2(u_{e,0}-v)/h). Therefore their sum is identically zero. Integrating (u_{ss}) over the first control volume gives

$$
(L_hu)_{e,0}=\frac{(u_{e,1}-u_{e,0})/h-(u_{e,0}-v)/(h/2)}{h}.
$$

Interior cells use ((u_{j+1}-2u_j+u_{j-1})/h^2); the last cell uses ((u_{N-2}-u_{N-1})/h^2). With equal edges this operator is symmetric negative semidefinite in the cell-volume inner product. The reaction shifts its spectrum negatively. The frozen RK4 step is far inside the negative-real-axis stability interval; nevertheless monotone sampled energy is checked rather than assumed.

The normalized strong junction residual is

$$
r_{\rm KCL}=\frac{|\sum_e2(u_{e,0}-v)/h|}
{\max(1,\sum_e|2(u_{e,0}-v)/h|)}.
$$

## 5. Shared-node finite elements

`[Derivation]` Assemble one common centre degree of freedom and three chains of (N) linear elements. The weak equation is

$$
M\dot U+D_*KU+\kappa_*MU=0.
$$

The assembled (M) is symmetric positive definite and (K) is symmetric positive semidefinite. For generalized eigenpairs (KQ=MQ\Lambda) normalized by (Q^TMQ=I),

$$
U(\theta)=Qe^{-(D_*\Lambda+\kappa_*I)\theta}Q^TMU(0).
$$

This yields nonincreasing (M)-energy. A single shared degree of freedom enforces centre continuity exactly. At finite mesh width, raw one-sided element slopes need not sum to machine zero because the vertex row includes consistent-mass dynamics; the non-circular machine-precision check is instead the normalized weak residual

$$
r_{\rm weak}=\frac{\|M\dot U+D_*KU+\kappa_*MU\|_2}
{\|M\dot U\|_2+\|D_*KU\|_2+\|\kappa_*MU\|_2+\epsilon}.
$$

Pointwise flux convergence is indirectly tested by exact-field convergence, including the A0 sector that has nonzero branch derivatives but zero summed flux.

## 6. Common scoring

For vectors evaluated at the same cell centres,

$$
E(a,b)=\left(\frac{h\sum_{e,j}(a_{e,j}-b_{e,j})^2}
{h\sum_{e,j}b_{e,j}^2}\right)^{1/2}.
$$

The receipt records (E({\rm FV},{\rm exact})), (E({\rm FEM},{\rm exact})), and (E({\rm FV},{\rm FEM})). Exact-error refinement uses (E_{32}/E_{64}). Pure-mode decay is scored by projecting the terminal numerical field onto its exact initial spatial vector and comparing the amplitude with (e^{-(D_*\lambda+\kappa_*)\theta_f}).

`[Prediction]` Both consistent second-order spatial schemes should give refinement ratios near four and final errors below the frozen (10^{-3}) ceiling. This is a prediction, not yet a result.

## 7. Adverse control and closure boundary

`[Countermodel]` D0 replaces the common centre by an independent zero-flux face on each edge. Its domain is three disconnected Neumann intervals. The A0 sine field violates that centre condition, so its evolution is not the star-graph exact solution. E2 is discriminating only if the D0 relative error exceeds (2\times10^{-2}).

`[Unfinished]` Finite (N) does not establish the continuum equation as biological truth. Cross-solver agreement does not validate morphology, nonlinear channels, synaptic memory, an infinite-dimensional Riemannian metric, effective dimension, consciousness, hippocampal retrieval, or AGI.
