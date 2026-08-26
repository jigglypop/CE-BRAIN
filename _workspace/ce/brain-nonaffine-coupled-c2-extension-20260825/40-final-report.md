# Quantitative nonaffine coupled-base C2 graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The global coupled C2 graph-transform theorem is extended from an affine base
to a graph-independent nonaffine base. A bound $H_\phi$ controls base curvature
and a separate modulus $T_\phi$ controls its variation. Both contributions are
propagated through the modified Hessian, inverse reparameterization, C2,1
class, and three-level recurrence. This is conditional differential geometry,
not evidence that a measured brain field or consciousness realizes the model.

## 1. One-graph class

For $F_h=\phi_t+f_t(\cdot,h)$, the predecessor gives

$$
C_F^{\rm na}=H_\phi+H_f(1+\kappa)^2+L_{fy}\Lambda,
\qquad N=C_Y+\rho C_F^{\rm na}.
$$

If $\operatorname{Lip}(D^2\phi_t)\le T_\phi$, then

$$
C_P^{\rm na}=T_\phi+T_f(1+\kappa)^3
+3H_f(1+\kappa)\Lambda+L_{fy}\Xi.
$$

Together with $C_R$ and
$C_T=C_Y/\alpha+sC_F^{\rm na}/\alpha^2$, this yields

$$
C_N^{\rm na}=C_R+C_TC_F^{\rm na}+\rho C_P^{\rm na},
\qquad
\Xi_{\rm out}^{\rm na}
=\frac{C_N^{\rm na}}{\alpha^3}
+\frac{2NC_F^{\rm na}}{\alpha^4}.
$$

The $\Xi$ gate is required when $L_{fy}>0$ and is bypassed when preimages are
graph-independent.

## 2. Two-graph recurrence

The new base-Hessian comparison is

$$
P_\delta^{\rm na}=T_\phi r_x+L_{fy}\Xi r_x+H_fZ\Lambda
+2H_f(1+\kappa)\Lambda r_x+T_fZ(1+\kappa)^2.
$$

Putting

$$
N_d^{\rm na}=R_d+C_F^{\rm na}\beta_1+\rho P_d,
\qquad
N_\delta^{\rm na}=R_\delta+C_F^{\rm na}c_{10}^{\rm na}
+\rho P_\delta^{\rm na},
$$

gives the exact upper-triangular Hessian recurrence

$$
e_{n+1}\le\frac Q{\alpha^2}e_n
+\left(\frac{N_d^{\rm na}}{\alpha^2}
+\frac{2NL_{fy}}{\alpha^3}\right)d_n
+\left(\frac{N_\delta^{\rm na}}{\alpha^2}
+\frac{2NA_\delta^{\rm na}}{\alpha^3}\right)\delta_n.
$$

Passing C1 gates, C2,1 class invariance, and strict $Q/\alpha^2<1$ imply a
unique C2 invariant graph.

## 3. Exact witness and reductions

For $\phi_{\lambda,a}(x)=\lambda x+a\sin x$ with
$(\lambda,a)=(1001/1000,1/1000)$,
$\mu=1$ and $H_\phi=T_\phi=1/1000$. The exact fixture gives

$$
\Xi_{\rm out}^{\rm na}=\frac{701739032}{1733598925},
\quad
\beta_{2,c}=\frac{12320}{50653},
\quad
c_{21,c}^{\rm na}=\frac{840496}{9370805},
\quad
c_{20,c}^{\rm na}=\frac{410712208}{8667994625}.
$$

$H_\phi=T_\phi=0$ reproduces affine coupled C2 term by term. With $f\equiv0$,
the certificate reproduces graph-independent nonaffine triangular C2, using
$\nu=H_\phi\mu^3$. Equality $Q/\alpha^2=1$ is rejected by the embedded
C1/non-C2 counterexample.

## 4. Evidence ceiling

This closes the conditional global nonaffine coupled C2 apparatus. It does not
compose local domain gates, prove C3 or higher regularity, identify a concrete
brain vector field, select dimension 4--6, or establish consciousness.
Validation counts are recorded in `31-validation.md`; no external source or
empirical input was used.

## References

Formal dependencies are the final-gated nonaffine coupled C1 and affine
coupled C2 repository runs.
