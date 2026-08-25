# Exact physical scale and mobility map

Status: COMPLETE

Date: 2026-08-25

## Abstract

The predecessor proved an exact per-window contraction bound but could not translate window count into physical time. This run fixes positive state, model-energy, and time reference scales and retains an arbitrary declared scalar physical mobility. Chain-rule normalization yields a dimensionless mobility, physical speed and power scales, and conditional speed/dissipation bounds. A positive-term atanh series gives exact rational lower and upper bounds for the physical decay rate $-\log q/\Delta t$. The apparatus passes 23 focused, 25 dimensionless, and 74 adjacent tests. These are conditional algebraic theorems and software outputs, not a calibration of neural time, mobility, energy, consciousness, or dimension.

## 1. Definitions and normalization

Let $x=X_0\widetilde x$, $\mathcal V=V_0\widetilde{\mathcal V}$, and $t=t_0\tau$ with positive reference scales. In the homogeneous scalar-coordinate model, $\mu_{\rm phys}$ has unit $[x]^2/([\mathcal V][t])$. Substitution into the metric-gradient term gives the dimensionless coefficient

$$
\widetilde\mu=\frac{\mu_{\rm phys}V_0t_0}{X_0^2},
\qquad
\frac{d\widetilde x}{d\tau}
=-\widetilde\mu A^{-1}\nabla\widetilde{\mathcal V}.
$$

The earlier formula $\mu_0=X_0^2/(V_0t_0)$ is precisely the special slice $\widetilde\mu=1$. It is a convenient normalization, not an estimate of a biological mobility.

## 2. Conditional physical outputs

For a supplied dimensionless window $\Delta\tau>0$,

$$
\Delta t=t_0\Delta\tau,\qquad
v_0=X_0/t_0,\qquad P_0=V_0/t_0.
$$

If $\|A^{-1}\nabla\widetilde{\mathcal V}\|\le G$, then
$\|dx/dt\|\le v_0\widetilde\mu G$. In the Euclidean $A=I$ subcase,

$$
-\frac{d\mathcal V}{dt}
=P_0\widetilde\mu\|\nabla\widetilde{\mathcal V}\|^2
\le P_0\widetilde\mu G^2.
$$

For general $A$, the squared norm is replaced by the $A^{-1}$ quadratic form. The executable Euclidean bound is therefore deliberately narrower than the general metric-gradient identity.

## 3. Exact contraction-to-rate theorem

Suppose the predecessor supplies $0<q<1$ and distance after $n$ equal windows is at most $q^n$ times its initial value. Set $z=(1-q)/(1+q)$ and, for $N\ge1$,

$$
L_N=2\sum_{k=0}^{N-1}\frac{z^{2k+1}}{2k+1},\qquad
U_N=L_N+\frac{2z^{2N+1}}{(2N+1)(1-z^2)}.
$$

The identity $-\log q=2\operatorname{artanh}z$ and positivity of its series give

$$
\frac{L_N}{\Delta t}
\le -\frac{\log q}{\Delta t}
\le\frac{U_N}{\Delta t}.
$$

Thus $q^n=e^{-\gamma n\Delta t}$ with a certified rational enclosure of $\gamma$. At $q=0$, the discrete bound reaches zero after one window and no finite logarithmic rate is reported. At $q=1$, the identity sequence is a complete counterexample to any positive-rate extension.

## 4. Identifiability limit

Changing $t_0$ to $ct_0$ leaves $q$ intact and divides the physical rate by $c$. Hence no observation of $q$ alone identifies seconds. Similar compensating rescalings leave $\widetilde\mu$ invariant while changing the separate energy scale and physical mobility. The run therefore closes the conversion formula but not the empirical values needed to instantiate it.

Mixed-unit neural state vectors require a diagonal scale map and dimension-aware mobility tensor. A general Riemannian dissipation upper additionally needs an exact $A^{-1}$ quadratic-form or operator bound. Those are recorded as open extensions rather than hidden inside this scalar result.

## 5. Reproducibility and strict ceiling

The implementation is `physical_scale_mobility.py`; its focused test is `test_physical_scale_mobility.py`. Focused validation passed 23/23, the dimensionless registry passed 25/25, and graph-transform plus scale-map integration passed 74/74.

No number in the fixture is a measured neural constant. The model potential is not identified with metabolic energy; no physical brain speed, decay time, mobility, consciousness state, or preferred dimension is inferred. Actual calibration still requires a source-locked state/measurement model and empirical scales.

