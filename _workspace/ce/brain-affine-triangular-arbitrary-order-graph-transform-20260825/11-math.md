# Mathematics lane

Status: COMPLETE

## AN.1 Integer-partition form

For order `n`, let

$$
\mathfrak P_n=\left\{m=(m_1,\ldots,m_n)\in\mathbb N_0^n:
\sum_{j=1}^n j m_j=n\right\}.
$$

Write `|m|=sum m_j` and

$$
C_n(m)=\frac{n!}{\prod_{j=1}^n(j!)^{m_j}m_j!}.
$$

These are exactly the multiplicities of set partitions with `m_j` blocks of
size `j`. Put `R_1=1+kappa` and `R_j=Lambda_j` for `j>=2`. The singleton
partition `e_n=(0,...,0,1)` is separated because its vertical contribution is
already included in `q Lambda_n`.

## AN.2 One-graph Cn class

The exact normalized raw bound is

$$
A_n=q\Lambda_n+
\sum_{m\in\mathfrak P_n\setminus\{e_n\}}
C_n(m)K_{|m|}\prod_{j=1}^nR_j^{m_j}.
$$

For an affine inverse with norm `mu`,

$$\Lambda_{n,\mathrm{out}}=\mu^nA_n.$$

The declared Cn class is preserved iff this is at most `Lambda_n`.

## AN.3 Complete two-graph recurrence

Let `Delta_k` be the uniform distance of the kth graph derivatives and
`Delta_0` the value distance. Then

$$
\Delta_n'\le\sum_{k=0}^n a_{n,k}\Delta_k,
$$

$$a_{n,n}=q\mu^n,$$

and for `1<=k<n`,

$$
a_{n,k}=\mu^n\sum_{m\ne e_n}C_n(m)K_{|m|}m_k
R_k^{m_k-1}\prod_{j\ne k}R_j^{m_j}.
$$

The value coefficient is

$$
a_{n,0}=\mu^n\left[K_2\Lambda_n+
\sum_{m\ne e_n}C_n(m)K_{|m|+1}\prod_jR_j^{m_j}\right].
$$

This formula proves why K(n+1) is needed: the all-singleton partition has
`|m|=n` and its map-value increment uses `K(n+1)`. K(n+1) changes only
`a_n,0`, not the one-graph Cn radius or the other recurrence coefficients.

Strict `q*mu^n<1` at every added level makes the finite nonnegative
upper-triangular recurrence converge. Induction on `n`, using the partition
form of Faà di Bruno and slotwise telescoping, proves the result for every
supplied finite maximum order.

## AN.4 Exact reductions and boundary

At `n=4`, the partition vectors and coefficients are

`(4,0,0,0):1`, `(2,1,0,0):6`, `(1,0,1,0):4`,
`(0,2,0,0):3`, `(0,0,0,1):1`.

The generated class and recurrence exactly equal the frozen C4 certificate.
For the standard fixture, C5 and C6 outputs are `133/4` and `2283/8`, with
margins `27/4` and `917/8`.

At `q*mu^n=1`, choose `x'=x/a`, `y'=y/a^n`. The family

$$h_c(x)=c\max(x,0)^n$$

satisfies `h_c(x/a)=h_c(x)/a^n`, is C(n-1), and has nth one-sided derivatives
0 and `c n!`. Equality therefore cannot force Cn.

The theorem is finite-order and dimension-parametric. It does not supply a
uniform-in-n analytic/Gevrey bound or select the input dimension.
