# Mathematics

Status: COMPLETE

## CC.1 — simultaneous split-conformal radii

For frozen positive scales `s_j`, define `S_i=max_j e_ij/s_j`.  With `n`
calibration vectors,

```text
k = ceil((n+1)(1-alpha)),  q = S_(k),  r_j=s_j q.
```

If `k<=n` and the calibration plus one future vector are exchangeable, rank
symmetry gives simultaneous whole-vector coverage at least
`k/(n+1)>=1-alpha`.  This is marginal future-vector coverage, not conditional
coverage and not a drift guarantee.

## CC.2 — held-out undercoverage falsifier

Under an independently declared iid Bernoulli hit model and null `p<=p0`, the
upper-tail probability for at least `h` hits in `N` trials is

```text
sum_(j=h)^N choose(N,j) p0^j (1-p0)^(N-j).
```

Failure to fall below audit alpha refuses the coverage apparatus.

## CC.3 — deterministic rank composition

Require the complete ordered `2n^2` real/imag family, reshape its radii into a
complex rectangular matrix box, and invoke IVSPEC.  On the conformal coverage
event, every covered future matrix belongs to the IVSPEC family and therefore
has its certified Riesz rank.
