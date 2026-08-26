# Mathematics lane

Status: COMPLETE

## Objects and assumptions

Let $H_h=(I,h)$, $J_h=DH_h=(I,Dh)$, and
$H_{k,h}=(0,D^kh)$ for $k=2,3,4$. Put
$S_h=Bh+g\circ H_h$. The passing C3 predecessor supplies $q,\mu,\kappa$,
$K_2,K_3,\Lambda_2,\Lambda_3$ and all lower recurrences. The new bounds are
$K_4\ge\|D^4g\|$, the fiber Lipschitz modulus $K_5$ of $D^4g$, and the graph
radius $\Lambda_4\ge\|D^4h\|$. Write $r=1+\kappa$.
The normalized graph tube contains every fiber segment between two admissible
graph values, so the stated fiber Lipschitz bounds apply by telescoping along
that segment.

## Exact fourth-order identity

The order-four set partitions have multiplicities $1,4,3,6,1$. Therefore

$$
\begin{aligned}
D^4S_h={}&(B+D_yg)H_{4,h}
+4D^2g[H_{3,h},J_h]
+3D^2g[H_{2,h},H_{2,h}]\\
&+6D^3g[H_{2,h},J_h,J_h]
+D^4g[J_h,J_h,J_h,J_h].
\end{aligned}
$$

The affine inverse contributes four factors bounded by $\mu$. Hence

$$
\Lambda_{4,\mathrm{out}}=\mu^4\left(
q\Lambda_4+4K_2\Lambda_3r+3K_2\Lambda_2^2
+6K_3\Lambda_2r^2+K_4r^4\right).
$$

Thus $\Lambda_{4,\mathrm{out}}\le\Lambda_4$ preserves the declared C4
class.

## Five-layer two-graph recurrence

Let $\delta,d,e,f,j$ denote the uniform distances of the graph value and its
first through fourth derivatives. Slotwise telescoping of the exact identity
gives

$$
j'\le\beta_4j+c_{43}f+c_{42}e+c_{41}d+c_{40}\delta,
$$

$$
\beta_4=q\mu^4,
\qquad
c_{43}=4\mu^4K_2r,
$$

$$
c_{42}=\mu^4(6K_2\Lambda_2+6K_3r^2),
$$

$$
c_{41}=\mu^4(4K_2\Lambda_3+12K_3\Lambda_2r+4K_4r^3),
$$

$$
\begin{aligned}
c_{40}=\mu^4(&K_2\Lambda_4+4K_3\Lambda_3r
+3K_3\Lambda_2^2\\
&+6K_4\Lambda_2r^2+K_5r^4).
\end{aligned}
$$

The $K_5$ term comes only from comparing $D^4g(x,h_1)$ and
$D^4g(x,h_2)$. A finite $K_4$ controls the size at one graph but cannot
control this increment. Together with the predecessor recurrences, strict
$q\mu^4<1$ makes the five-level nonnegative upper-triangular recurrence
converge and the unique invariant graph is C4.

## Boundary and exact fixture

At $q=1/16$ and $\mu=2$, all lower diagonal factors are strict but
$q\mu^4=1$. The family $h_c(x)=cx|x|^3$ satisfies
$h_c(x/2)=h_c(x)/16$. It is C3, while its fourth derivative has one-sided
values $-24c$ and $24c$ at zero. Equality therefore cannot force C4.

For the frozen exact fixture

$$
(q,\mu,r,K_2,K_3,K_4,K_5,\Lambda_2,\Lambda_3,\Lambda_4)
=\left(\frac12,1,2,\frac1{16},\frac1{16},\frac1{64},
\frac1{256},1,2,6\right),
$$

the output radius is $95/16$, its margin is $1/16$, and

$$
(\beta_4,c_{43},c_{42},c_{41},c_{40})
=\left(\frac12,\frac12,\frac{15}{8},\frac52,2\right).
$$

## Audit findings

- P0: none.
- P1: none under the declared C3 predecessor, $K_4$, and $K_5$ premises.
- P2: the symbol $K_4$ is both the one-graph fourth derivative bound and the
  C3 predecessor's fiber modulus for $D^3g$; the implementation passes it to
  both roles explicitly.
- The theorem is dimension-parametric and contains no biological input.

Reproduction:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-quantitative-triangular-c4-graph-transform-20260825\artifacts\triangular_c4_math_audit.py
```
