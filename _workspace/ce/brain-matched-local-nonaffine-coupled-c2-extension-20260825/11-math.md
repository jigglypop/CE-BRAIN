# Mathematics lane

Status: COMPLETE

## M1. Boundary-compatible graph class

Let $U_t,U_{t+1}$ be compact balls and let $\mathcal H_0$ be the predecessor
C2,1 graph class restricted by $h|_{\partial U_t}=0$. Require
$g_t(x,0)=0$ for every $x\in\partial U_t$. Once exact domain equality holds,
the diffeomorphism $F_h$ maps boundary to boundary. Hence for
$x'\in\partial U_{t+1}$ and $x=F_h^{-1}(x')\in\partial U_t$,

$$
(\mathcal Th)(x')
=B_t h(x)+g_t(x,h(x))
=0
$$

so the fiber transform preserves $\mathcal H_0$. In one dimension this reduces
to the two endpoint conditions at $-1$ and $1$.

## M2. Exact matched-domain theorem

Assume the overflow-local nonaffine coupled C2 predecessor and exact uniform
forward/inverse contacts

$$
\sup_h\sup_{x\in U_t}|F_h(x)|=1,
\qquad
\sup_h\sup_{x'\in U_{t+1}}|F_h^{-1}(x')|=1.
$$

The associated upper bounds certify both inclusions. For each admissible $h$,
$F_h(U_t)\subseteq U_{t+1}$, while applying $F_h$ to
$F_h^{-1}(U_{t+1})\subseteq U_t$ gives the reverse inclusion. Hence

$$
F_h(U_t)=U_{t+1}.
$$

Together with M1, the overflow graph identity strengthens to exact full graph
equality. Both domain-contact margins are zero. A positive exact margin would
exclude a boundary point that exact equality must attain.

## M3. Nonzero-coupling witness

For

$$
F_h(x)=x+a x(1-x^2)+\varepsilon h(x),
$$

with $h(\pm1)=0$ and $\|h'\|\le\kappa$,

$$
F_h(\pm1)=\pm1,
$$

and

$$
F_h'(x)=1+a-3ax^2+\varepsilon h'(x)
\ge1-2a-\varepsilon\kappa.
$$

If the last quantity is positive, every $F_h$ is strictly increasing on an
open collar and maps the interval exactly onto itself. At the frozen fixture
the derivative gap is $39/40$, the base inverse bound is $50/49$, and the
actual coupled inverse bound is $40/39$. Moreover

$$
H_\phi=T_\phi=6a=\frac3{50}.
$$

The global differential fixture passes with

$$
\Xi_{\rm out}=\frac{4085248}{30074733},
\quad
\beta_{2,c}=\frac{6272}{59319},
\quad
c_{21,c}=\frac{37888}{3855735},
\quad
c_{20,c}=\frac{1021312}{751868325}.
$$

Since $Y_h=Bh$ in the witness, $Y_h(\pm1)=0$ and the anchored class is
preserved.

## M4. Independent adverse controls

Base boundary fixation alone is insufficient. If $h\equiv1$ and
$\varepsilon>0$, then $F_h(1)=1+\varepsilon$, so the target interval is not
retained. Graph anchoring alone is also insufficient: if $g(1,0)\ne0$, then
the transformed graph has a nonzero boundary value even when $F_h(1)=1$.

When $\varepsilon=0$, the witness reduces exactly to the matched
graph-independent cubic. Removing forward contact retains only the valid
overflow-local theorem. Equality contacts remain non-robust but do not alter
any differential coefficient or recurrence.

Verdict: the boundary-anchored class, preserved fiber boundary, and exact
forward/inverse contacts close matched full-forward local nonaffine coupled
C2. C3+ and empirical brain identification remain open.
