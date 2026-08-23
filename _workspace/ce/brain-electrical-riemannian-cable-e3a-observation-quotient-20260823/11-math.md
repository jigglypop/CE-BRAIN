# BA-ERC1-E3a mathematics — visible and quotiented branch modes

Status: COMPLETE

## 1. Observation decomposition

`[Definition]` In branch space, let $q=\mathbf1/\sqrt3$ and $\Pi=qq^T$. Then $\Pi^T=\Pi$, $\Pi^2=\Pi$, and $\operatorname{rank}\Pi=1$. It is the orthogonal projection onto every branch-shared point-neuron output.

The E2 antisymmetric coefficient $c=(1,-1,0)^T/\sqrt2$ satisfies $q^Tc=0$, hence $\Pi c=0$.

## 2. Exact panel consequences

At fixed $s_0=0.6$, write

$$
a(t)=\cos(\pi s_0)e^{-r_St},\qquad
b(t)=\sin(\pi s_0/2)e^{-r_At},
$$

where $r_S=0.2\pi^2+0.3$ and $r_A=0.2(\pi/2)^2+0.3$.

`[Theorem]` S1 has $Y(t)=a(t)\mathbf1$, so $(I-\Pi)Y=0$ and $\eta_\perp=0$.

`[Theorem]` A0 has $Y(t)=b(t)c$, so $\Pi Y=0$, $\eta_\perp=1$, and its branch mean is exactly zero.

`[Derived prediction]` M1 has $Y(t)=0.7a(t)\mathbf1+0.3b(t)c$. Orthogonality gives

$$
\eta_\perp^{M1}=
\frac{\sum_t0.3^2b(t)^2}
{\sum_t[3(0.7)^2a(t)^2+0.3^2b(t)^2]}.
$$

The frozen $0.2$ gate is evaluated only after the formula, sensor, and time grid are sealed.

## 3. Oracle strength and no-go

`[Conditional theorem]` For each time, $\Pi Y$ uniquely minimizes $\|Y-z\mathbf1\|_2$ over every scalar $z$. Allowing a different $z$ at every time is at least as flexible as any scalar point-neuron ODE with a fixed observation identity. Therefore nonzero orthogonal energy cannot be repaired by changing scalar dynamics.

`[No-go]` The mean map $m(Y)=\mathbf1^TY/3$ has the entire two-dimensional antisymmetric branch subspace in its kernel. A mean-only observation cannot distinguish A0 from zero, regardless of temporal resolution.

`[Boundary]` Sensor-specific gains or offsets would change the observation family and are not identified here. Real-data use requires typed calibration and a new measurement contract.

## 4. Formal status

- Projection identities and S1/A0 consequences: `[theorem]`.
- M1 threshold: `[frozen synthetic prediction]`.
- Machine result: `[unrun]` at freeze.
- Biological observability and state-space dimension: `[unfinished/unopened]`.
