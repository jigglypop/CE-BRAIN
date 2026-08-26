# Mathematics lane

Status: COMPLETE

## L1. Why the actual graph-dependent inverse is required

For $h:U_t\to Y$, the local transform at $x'\in U_{t+1}$ evaluates

$$
(\mathcal Th)(x')=Y_h(F_h^{-1}(x')).
$$

Thus it is well-defined on all of $U_{t+1}$ precisely when the required
inverse branch exists there and returns to $U_t$. Coverage of
$\phi_t^{-1}(U_{t+1})$ alone cannot establish this because $F_h$ contains
$f_t(x,h(x))$.

## L2. Uniform local-domain theorem

Assume the global nonaffine coupled C2 hypotheses and constants hold uniformly
on open collars of $U_t$ and $U_{t+1}$. Assume additionally that every
admissible $F_{t,h}$ has the selected inverse branch on that collar and

$$
\sup_h\sup_{x'\in U_{t+1}}
\|F_{t,h}^{-1}(x')-c_t\|
\le R_{\rm pre}\le R_t.
$$

Then every value, derivative, and Hessian evaluation in the global proof lies
inside its declared collar. The one-graph class calculation and the two-graph
recurrence are unchanged. Consequently the local transform is a contraction
on the same complete graph class and its unique invariant graph is C2 over the
prescribed domain sequence.

The set identity is the overflow form

$$
\operatorname{graph}(h_{t+1})
=\Phi_t(\operatorname{graph}(h_t))
\cap(U_{t+1}\times Y).
$$

No forward inclusion follows. The domain margin is positive exactly when the
supplied inverse bound is strict; equality is admissible but non-robust.

## L3. Exact coupled witness

Let

$$
\phi(x)=\lambda x+a\sin x,
\qquad f(x,y)=\varepsilon y,
\qquad |h(x)|\le R_y.
$$

For $\lambda>a\ge0$, the mean-value theorem gives

$$
|\phi(x)-\phi(0)|\ge(\lambda-a)|x|.
$$

If $x'=F_h(x)$ and $|x'|\le R_{t+1}$, then

$$
(\lambda-a)|x|
\le|x'|+\varepsilon|h(x)|
\le R_{t+1}+\varepsilon R_y.
$$

Therefore

$$
R_{\rm pre}=\mu(R_{t+1}+\varepsilon R_y),
\qquad \mu=(\lambda-a)^{-1}.
$$

At the frozen fixture this is $3/5$, so the unit input ball has exact
certificate margin $2/5$. The global differential predecessor also passes;
the base inverse bound is $4/7$, while the actual coupled inverse bound is
$40/69$ because $\lambda-a-\varepsilon\kappa=69/40$. Its exact
second-bunching factor is $7520/109503$.

## L4. Counterexamples and reductions

Coverage of $\phi^{-1}$ is insufficient. On $U=U'=[-1,1]$, take
$\phi(x)=2x$, $f(x,y)=y$, and the admissible constant graph $h=-2$. Although
$\phi^{-1}(U)=[-1/2,1/2]\subset U$, the actual equation
$F_h(x)=2x-2=1$ has preimage $x=3/2\notin U$.

Inverse coverage does not imply forward retention: with $f=0$ and
$\phi(x)=2x$, $\phi^{-1}(U)\subset U$ but
$\phi(3/4)=3/2\notin U$.

At $\varepsilon=0$, the analytic coverage bound reduces exactly to the
graph-independent sine bound $\mu R_{t+1}$. The wrapper itself leaves every
global differential coefficient unchanged, so it cannot manufacture a new
smoothness or dimension-selection claim.

Verdict: uniform graph-dependent inverse coverage closes backward-covered
local nonaffine coupled C2. Exact matched full-forward composition, C3+, and
empirical brain identification remain open.
