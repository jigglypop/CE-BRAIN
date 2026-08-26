# Mathematics

Status: COMPLETE

## CIDISC.1 — simultaneous radii

For scores `S_j=max_l e_jl/s_l`, set
`k=ceil((n+1)(1-alpha))`, `q=S_(k)`, and `r_l=s_l q`.

## CIDISC.2 — conditional coverage

If the calibration scores and one future score are exchangeable and `k<=n`, all
future components are simultaneously inside their radii with probability at least
`k/(n+1)>=1-alpha`.

## CIDISC.3 — rank composition

On that simultaneous inclusion event, IDISC applies. Therefore, when the generated
radius matrices pass the strict interval Neumann gate, the future fixed-circle rank
equals the base rank with conditional probability at least `k/(n+1)`.

The fixture has `n=19`, `alpha=1/10`, `k=18`, `q=1`, coverage lower `9/10`,
baseline radius `1/200`, coupling radius `1/500`, and interval rank six.

## CIDISC.4 — held-out falsifier

An independently declared Bernoulli held-out audit uses the exact binomial upper tail.
It is a falsifier, not proof of exchangeability. Source labels/hashes are not external
receipts.
