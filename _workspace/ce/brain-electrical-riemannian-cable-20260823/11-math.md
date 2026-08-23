# BA-ERC1 mathematics — nonlinear electrical cable on a metric graph

Status: COMPLETE

## 1. Three geometries that must not be conflated

**[Definition]** The physical morphology is a metric graph $\Gamma=(\mathcal V,\mathcal E)$ whose edge $e$ is an interval with arclength $s\in(0,L_e)$. The graph distance comes from arclength. A branch vertex is not an ordinary point of a globally smooth one-dimensional manifold.

**[Definition]** The axial conductance coefficient is $a_e(s)=\sigma_{i,e}(s)A_e(s)$. It is a physical transport coefficient, not by itself a Riemannian metric.

**[Definition]** A metric $\mathsf G_X$ on the infinite-dimensional electrical state space measures tangent perturbations of states. It is distinct from both graph arclength and $a_e$.

These three objects may interact in one equation, but identifying them destroys units and obscures which quantity data can identify.

## 2. Axial current and charge conservation

Let $A_e$ be intracellular cross-sectional area, $P_e$ membrane area per arclength, $\sigma_{i,e}$ intracellular conductivity, $c_{m,e}$ membrane capacitance per area, and $V_e=\Phi_i-\Phi_e$ membrane voltage. Positive membrane current is outward and applied current density $i_{\rm ext}$ is positive inward. Their units are

| quantity | SI unit |
|---|---|
| $V,E_k$ | $\mathrm V$ |
| $I_\parallel$ | $\mathrm A$ |
| $s,L$ | $\mathrm m$ |
| $A$ | $\mathrm{m^2}$ |
| $P$ | $\mathrm m$ |
| $\sigma_i$ | $\mathrm{S\,m^{-1}}$ |
| $c_m$ | $\mathrm{F\,m^{-2}}$ |
| $i_m,i_{\rm ion},i_{\rm syn},i_{\rm ext}$ | $\mathrm{A\,m^{-2}}$ |
| conductance density $\bar g_k,g^{\rm syn}$ | $\mathrm{S\,m^{-2}}$ |

**[Derived]** Axial Ohm conduction gives

$$
I_{\parallel,e}(s,t)=-\sigma_{i,e}(s)A_e(s)\partial_sV_e(s,t).
\tag{1}
$$

Charge conservation on an infinitesimal segment is

$$
\partial_sI_{\parallel,e}+P_e i_{m,e}=0,
\qquad
i_m=c_m\partial_tV+i_{\rm ion}+i_{\rm syn}-i_{\rm ext}.
\tag{2}
$$

Substitution yields the primary electrical equation

$$
c_{m,e}\partial_tV_e
=\frac{1}{P_e}\partial_s\!\left(\sigma_{i,e}A_e\partial_sV_e\right)
-i_{{\rm ion},e}(V_e,w_e)
-i_{{\rm syn},e}(V_e,h_t)
+i_{{\rm ext},e}.
\tag{3}
$$

**[Derived: dimensional closure]** The diffusion term has unit $(1/\mathrm m)\partial_s(\mathrm A)=\mathrm{A\,m^{-2}}$, and $c_m\partial_tV$ has unit $\mathrm{F\,m^{-2}}\mathrm{V\,s^{-1}}=\mathrm{A\,m^{-2}}$. Every term in (3) therefore has the same unit.

If an arbitrary edge coordinate $x$ has line element $ds=\sqrt{g_e(x)}\,dx$, then (3) becomes

$$
c_m\partial_tV
=\frac{1}{P\sqrt g}\partial_x\!\left(
\frac{\sigma_iA}{\sqrt g}\partial_xV\right)
-i_{\rm ion}-i_{\rm syn}+i_{\rm ext}.
\tag{4}
$$

Equation (4) is a weighted Laplace--Beltrami/Sturm--Liouville operator. Replacing it by an unweighted $\Delta_g$ would lose taper, membrane-area, and conductivity factors.

For a constant cylinder of radius $r$, $A=\pi r^2$ and $P=2\pi r$, so

$$
c_m\partial_tV=\frac{\sigma_ir}{2}\partial_{ss}V-i_{\rm ion}-i_{\rm syn}+i_{\rm ext}.
\tag{5}
$$

## 3. Nonlinear membrane and synaptic electricity

**[Empirical formula]** A Hodgkin--Huxley-type current density is

$$
i_{\rm ion}
=\bar g_{\rm Na}m^3h(V-E_{\rm Na})
+\bar g_{\rm K}n^4(V-E_{\rm K})
+g_L(V-E_L),
\tag{6}
$$

$$
\partial_tq=\alpha_q(V)(1-q)-\beta_q(V)q,
\qquad q\in\{m,h,n\}.
\tag{7}
$$

The removable singularities in standard rate formulas are assigned their analytic limits. Every exponential uses a normalized voltage such as $(V-V_q)/V_{s,q}$, never a dimensional voltage directly.

**[Definition]** Conductance-based synaptic current is

$$
i_{\rm syn}(s,t)=\sum_r g_r(s,t)\bigl(V(s,t)-E_r\bigr).
\tag{8}
$$

**[Hypothesis: bounded causal-history conductance]** Use the directed convention $i\leftarrow j$: neuron $j$ is presynaptic and neuron $i$ is postsynaptic. Define a normalized strict-past history

$$
h_{ij,t}(a)=
\left(
\frac{V_j(t-a)-V_*}{V_0},
\frac{V_i(t-a)-V_*}{V_0},
\frac{i_{ij}(t-a)}{i_0},
q_j(t-a),q_i(t-a)
\right),\qquad a>0,
\tag{9}
$$

where $i_{ij}$ and $i_0$ are synaptic membrane-current densities in $\mathrm{A\,m^{-2}}$. Let $K_{ij}$ be a dimensionless Riesz representative in the normalized history Hilbert space. Its pairing uses an absolutely continuous history measure and admits neither endpoint evaluation nor a Dirac mass at $a=0$; this prevents an instantaneous algebraic loop through $i_{ij}(t)$. With $S(z)=(1+e^{-z})^{-1}$,

$$
g_{ij}^{\rm syn}(t)=g_{\min,ij}+(g_{\max,ij}-g_{\min,ij})
S\!\left(b_{ij}+\langle K_{ij},h_{ij,t}\rangle\right).
\tag{10}
$$

Equation (10) is causal, $C^\infty$ on its smooth function-space domain, positive, and bounded. Its postsynaptic contribution is $i_{ij}^{\rm syn}=g_{ij}^{\rm syn}(V_i-E_{ij})$, an electrical conductance density times a driving voltage. It is a testable model choice, not a theorem about all biological synapses.

A causal compactly supported smooth release kernel can be constructed from

$$
\phi(u)=
\begin{cases}
C\exp\!\left[-\dfrac{1}{u(1-u)}\right],&0<u<1,\\
0,&\text{otherwise},
\end{cases}
\qquad
K_\tau(a)=\tau^{-1}\phi(a/\tau).
\tag{11}
$$

The extension is $C^\infty$ and flat at both endpoints. A symmetric Gaussian spike kernel is not admitted because it has pre-event support.

## 4. Branch and soma laws

At a passive graph vertex $v$, all incident edges share voltage and conserve axial current:

$$
V_e(v,t)=V_{e'}(v,t),
\qquad
\sum_{e\sim v}\nu_{e,v}\sigma_{i,e}A_e\partial_sV_e(v,t)=I_v^{\rm node}(t),
\tag{12}
$$

where $\nu_{e,v}$ is the outward orientation. If a soma is represented by a point capacitance, its law is

$$
C_v\dot V_v+I_{{\rm ion},v}+I_{{\rm syn},v}
=\sum_{e\sim v}\nu_{e,v}\sigma_{i,e}A_e\partial_sV_e+I_v^{\rm app}.
\tag{13}
$$

Thus a branch is an electrical junction with continuity and Kirchhoff flux, not a smooth-manifold chart glued by assertion.

## 5. Passive energy identity

Set $u=V-E_L$ for one spatially constant reversal potential $E_L$ shared across the connected graph, use sealed-end or Kirchhoff boundary conditions, and retain only passive leak with no input. Define

$$
\mathcal E_C[u]=\frac12\sum_e\int_eP_ec_m u_e^2\,ds.
\tag{14}
$$

**[Theorem: conditional passive dissipation]** For sufficiently regular solutions of (3),

$$
\frac{d\mathcal E_C}{dt}
=-\sum_e\int_e\sigma_{i,e}A_e|\partial_su_e|^2\,ds
-\sum_e\int_eP_eg_Lu_e^2\,ds\le0.
\tag{15}
$$

**Proof.** Multiply the per-length form of (3) by $u$, integrate edgewise, and integrate the axial term by parts. Sealed endpoints vanish and paired vertex terms cancel by (12). Positivity of $\sigma_iA$ and $P g_L$ gives the sign. This identity is an L0 falsifier. It is not an energy law for the driven active HH system.

## 6. Infinite-dimensional state and regularity

**[Definition]** One energy-state realization, including optional point-capacitance soma vertices $\mathcal V_s$, is

$$
\mathcal X=\mathcal X_V
\oplus L^2(\Gamma;\mathbb R^{n_q})
\oplus L^2_\rho(\Gamma_{\rm syn}\times\mathbb R_+;\mathbb R^{n_h}),
\qquad
\mathcal X_V=
\left\{(V,(V_v)_{v\in\mathcal V_s}):
V\in H^1_{\rm cont}(\Gamma),\ V_v=\operatorname{tr}_vV\right\},
\tag{16}
$$

Here $\mathcal X_V$ is the trace-equality closed subspace: $H^1_{\rm cont}$ imposes vertex continuity and each finite soma voltage equals the corresponding edge trace. The measure $\rho(a)\,da$ is normalized and has no atom at zero. Even a finite graph has an infinite-dimensional voltage state because $V(\cdot,t)$ is a function on its edges. A general history field adds further infinite-dimensional coordinates.

**[Counterexample]** If every synaptic kernel is a finite sum of exponentials, auxiliary ODE variables give a finite-dimensional Markov realization of each synapse. Therefore “a synapse depends on history, so it must be infinite-dimensional” is false. The continuum cable state remains infinite-dimensional.

**[Conditional regularity]** Smooth positive edge coefficients, smooth forcing and channel vector fields, compatible initial/boundary/vertex data, and no impulse singularity permit parabolic smoothing in each open edge for $t>0$. A metric graph is not globally $C^\infty$ across a multi-edge vertex, and thresholded endogenous spikes can reduce temporal regularity. The defensible default is edgewise smooth or weak solutions plus continuity and Kirchhoff flux, not a global $C^\infty$ assertion.

## 7. State-space Riemannian metric and observation quotient

Choose energy $E_0>0$, time $T_0>0$, normalized history measure $\rho(a)da$, and gate/history energy densities $\kappa_q,\kappa_h$ in $\mathrm{J\,m^{-1}}$. Assume all metric weights have positive lower and finite upper bounds on their declared domains. A dimensionless reference metric on tangent perturbations is

$$
\begin{aligned}
\mathsf G_0(\delta X,\delta X)=\frac1{E_0}\Biggl\{\sum_e\int_e\Bigl[
&P_ec_m(\delta V)^2
+T_0\sigma_iA_e|\partial_s\delta V|^2\\
&+\sum_q\kappa_q(\delta q)^2
+\sum_h\kappa_h\int_0^\infty\rho(a)|\delta h(a)|^2\,da
\Bigr]ds
+\sum_{v\in\mathcal V_s}C_v(\delta V_v)^2\Biggr\}.
\end{aligned}
\tag{17}
$$

Every edge integral and soma term has energy units, so (17) is dimensionless and uniformly coercive relative to the declared weighted norm under the stated bounds. This is a chosen Sobolev/Hilbert reference metric, not an empirically identified unique geometry.

For normalized observation map $M:\mathcal X\to\mathbb R^p$ and positive noise covariance $R$, define

$$
\mathsf G_X^{\rm obs}(\delta X,\delta Y)
=\langle DM_X\delta X,R^{-1}DM_X\delta Y\rangle_{\mathbb R^p}.
\tag{18}
$$

**[Theorem: finite-observation no-go]** Equation (18) is positive semidefinite and vanishes on $\ker DM_X$. If $\mathcal X$ is infinite-dimensional and $p<\infty$, it cannot be positive definite on all of $T_X\mathcal X$. It defines a metric only on the observable quotient $T_X\mathcal X/\ker DM_X$, subject to closed-range/constant-rank regularity when a smooth quotient is required.

**Proof.** $\mathsf G_X^{\rm obs}(\delta X,\delta X)=\|R^{-1/2}DM_X\delta X\|^2\ge0$. A linear map from an infinite-dimensional space to finite-dimensional $\mathbb R^p$ has nontrivial kernel. Hence full-state positive definiteness is impossible without an added prior such as (17).

The regularized sum $\mathsf G_X=\mathsf G_0+\gamma\mathsf G_X^{\rm obs}$ with dimensionless $\gamma\ge0$ is a valid model metric, but its prior component is analyst-chosen.

## 8. Continuous effective dimension is a derived diagnostic

Let $Z(t)=T_0\dot X(t)$ be a dimensionless tangent velocity under (17), and let $W(a)da$ be a normalized causal window. If

$$
\mathcal C_t=\int_0^\infty W(a)\,Z(t-a)\otimes_{\mathsf G_X}Z(t-a)\,da
\tag{19}
$$

is positive trace class and nonzero, then either

$$
d_{\rm PR}(t)=\frac{(\operatorname{Tr}\mathcal C_t)^2}
{\operatorname{Tr}(\mathcal C_t^2)}
\tag{20}
$$

or, for frozen dimensionless $\lambda>0$,

$$
d_{\rm eff}(t;\lambda)=
\operatorname{Tr}\!\left[\mathcal C_t(\mathcal C_t+\lambda I)^{-1}\right]
\tag{21}
$$

can vary continuously and need not be an integer. These are effective numbers of active/observable modes. They are not the graph's topological dimension, a proof of a four-dimensional conscious slice, or an observer-independent property; they depend on metric, window, observation map, and regularization.

## 9. Nondimensional form

Let $v=(V-E_*)/V_0$, $\xi=s/L_0$, $\theta=t/T_0$, and $i_0=c_0V_0/T_0$. With $c_m=c_0\hat c$, $P=P_0\hat P$, $\sigma_i=\sigma_0\hat\sigma$, and $A=A_0\hat A$, (3) becomes

$$
\partial_\theta v
=D_0\frac1{\hat c\hat P}\partial_\xi
\left(\hat\sigma\hat A\partial_\xi v\right)
-\frac{\hat i_{\rm ion}+\hat i_{\rm syn}-\hat i_{\rm ext}}{\hat c},
\qquad
D_0=\frac{T_0\sigma_0A_0}{c_0P_0L_0^2}.
\tag{22}
$$

$D_0$ and every hatted current are dimensionless. For a constant passive cylinder, $\tau_m=c_m/g_L$ and $\lambda_c^2=\sigma_ir/(2g_L)$ give the familiar coefficient $(\lambda_c/L_0)^2$. All exponentials and fixed-point maps receive only ratios such as $(V-V_q)/V_{s,q}$ or $t/\tau$.

## 10. Higher-fidelity boundary

**[Axiom: upgrade model]** On an intra/extracellular Riemannian domain, ion species $c_k$ and potential $\Phi$ may instead obey

$$
\partial_tc_k+\operatorname{div}_gJ_k=0,
\qquad
J_k=-D_k\left(\nabla_gc_k+\frac{z_kF}{RT}c_k\nabla_g\Phi\right),
\tag{23}
$$

$$
-\operatorname{div}_g(\varepsilon\nabla_g\Phi)
=F\sum_kz_kc_k+\rho_{\rm fixed}.
\tag{24}
$$

PNP resolves concentration polarization and extracellular fields that a cable model omits. BA-ERC1 does not claim (23)--(24) were derived, solved, or reduced rigorously to (3); they define the boundary at which cable assumptions must later be challenged.

## 11. Claim boundary

Equations (1)--(18) formalize an electrical, nonlinear, infinite-dimensional state model under explicit assumptions. Equations (20)--(21) merely define continuous spectral diagnostics. No equation in this run derives consciousness, a preferred value four, a hippocampal hash mechanism, memory from curvature, or AGI.
