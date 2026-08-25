# Mathematics routes -- verified rational four-node contour enclosure

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-verified-contour-enclosure-20260825`

| Route | Target | Frozen/tunable choices | Falsifier | Matched control |
|---|---|---|---|---|
| R1 | V1 exact $\mathbb Q(i)$ inverse plus dyadic Frobenius lower enclosure | declared precision $p$, frozen before target | zero exact pivot or failed squared enclosure check | exact scalar and singular-node Fraction fixtures |
| R2 | V2 central $N=4$ full-circle certificate | no mesh choice: $N=4$, chord $\sqrt{2-\sqrt2}$ | singular node or $\underline\delta_4\le0$ | $U=[1/2],c=0,r=1$: must be nonpositive, not crossing |
| R3 | V3 diagonal witness, annulus exclusion, and central $P_4$ error | predeclared rational $q>1$, witness, and $p$ | invalid $UV=V\Lambda$, singular V, annulus value, boundary failure | oblique diagonalizable fixture versus defective Jordan fixture |
| R4 | simultaneous-unit-rescaling invariant certificate | exact reference normalization precedes dyadic grid | normalized output/status changes after common rational scale factor | scalar rescaling pair in `11-math.md` |

R1--R3 are finite-mathematics routes only. No neural observable, dimension
selection, consciousness claim, or empirical endpoint appears in them. There
is no look-elsewhere multiplicity within a frozen certificate: $N=4$,
$p$, $q$, reference scale, and witness are all recorded before result.
Changing any after a failure starts a distinct request, not a confirmation.

R4 is mandatory because raw-unit fixed-grid rounding is mathematically safe
but not unit-invariant. The revised normalize-first contract makes every
dimensionless rational input unchanged under common positive rational
rescaling; derived raw separation/resolvent transform with the stated units.

Reproduction:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-verified-contour-enclosure-20260825\artifacts\math_spotchecks.py
```

All routes stop at named failure conditions. A failed exact certificate is
not evidence that a contour intersects the spectrum.
