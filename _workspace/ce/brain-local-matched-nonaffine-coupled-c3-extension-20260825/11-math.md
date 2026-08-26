# Mathematics lane

Status: COMPLETE

## Domain composition

Let the core input and output balls have normalized radii $R_t,R_{t+1}$.
Let their open C3 extension collars have widths $\eta_t,\eta_{t+1}>0$.
For every admissible graph assume

$$
F_h^{-1}(B_{R_{t+1}})\subseteq B_{R_t},
$$

$$
F_h^{-1}(B_{R_{t+1}+\eta_{t+1}})
\subseteq B_{R_t+\eta_t}.
$$

The margins are

$$
m_0=R_t-R_{\rm pre},\qquad
m_3=R_t+\eta_t-R_{\rm pre,3}.
$$

The first closes core evaluation. The second supplies the open neighborhood
needed by the global C3 chain rule and inverse theorem at the core boundary.

## Local and matched theorems

Under the global nonaffine coupled C3 certificate, positive collars, and
$m_0,m_3\ge0$, restriction changes no differential coefficient. The same
four-layer recurrence proves a unique local C3 graph. Strict global margins
and $m_0,m_3>0$ give robust interior; equality is valid but nonrobust.

For the matched theorem add exact contacts $R_{\rm pre}=R_t$ and
$R_{\rm fwd}=R_{t+1}$, zero graph boundary values, and zero fiber boundary
forcing. The predecessor boundary argument gives full forward/backward
invariance, while the collar justifies C3 differentiation at the boundary.
Domain-contact robust interior is false, though differential-and-collar robust
interior may be true.

## Exact witness

For $F_h(x)=x+a x(1-x^2)+\varepsilon h(x)$ and $|h'|\le\kappa$ on
$|x|\le1+\eta_t$,

$$
F_h'(x)\ge1+a-3a(1+\eta_t)^2-\varepsilon\kappa
=:\alpha_{\rm collar}.
$$

At $a=\varepsilon=1/100$, $\kappa=1/2$, and $\eta_t=1/10$,

$$
\alpha_{\rm core}=\frac{39}{40},\qquad
\alpha_{\rm collar}=\frac{9687}{10000}.
$$

Choosing $\eta_{t+1}=\alpha_{\rm collar}\eta_t/2=9687/200000$
puts the expanded inverse image within radius $21/20$, leaving margin $1/20$.
The collar Hessian bound is $33/500$, its Lipschitz modulus is $3/50$, and the
third-derivative Lipschitz modulus is zero.

## Findings

- P0: none.
- P1: none under the explicit extension premises.
- P2: core and collar inverse Lipschitz constants must remain distinct.
- Removing either positive collar or expanded inverse coverage invalidates the
  closed-boundary C3 conclusion, not the global theorem.

Reproduction:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-local-matched-nonaffine-coupled-c3-extension-20260825\artifacts\local_matched_c3_math_audit.py
```
