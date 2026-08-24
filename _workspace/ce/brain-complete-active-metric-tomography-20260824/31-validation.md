# BA-OBS-ID2 validation

Status: COMPLETE

## Executed focused validation

The Windows Python hook reported `PASS` with Python 3.11.9 and NumPy 2.4.6. An
in-memory source `compile()` then passed. The focused frozen validator ran once:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-complete-active-metric-tomography-20260824\artifacts\validate_active_metric_tomography.py --output _workspace\ce\brain-complete-active-metric-tomography-20260824\artifacts\active_metric_tomography_receipt.json
```

```text
BA-OBS-ID2 synthetic active metric tomography: PASS
N=4 exact=1.862e-16 raw=2.646e-08 clip=2.098e-08 Mtail=9.126e-02 Gtail=6.086e-02
N=8 exact=3.713e-16 raw=4.690e-08 clip=3.966e-08 Mtail=1.188e-02 Gtail=7.917e-03
N=16 exact=6.401e-16 raw=8.718e-08 clip=7.817e-08 Mtail=1.995e-04 Gtail=1.330e-04
N=32 exact=1.383e-15 raw=1.673e-07 clip=1.560e-07 Mtail=5.628e-08 Gtail=3.752e-08
```

| N | exact block Frobenius error | $\eta_N$ | clipped block error | mobility HS tail | metric HS tail |
|---:|---:|---:|---:|---:|---:|
| 4 | $1.862\times10^{-16}$ | $2.646\times10^{-8}$ | $2.098\times10^{-8}$ | $9.126\times10^{-2}$ | $6.086\times10^{-2}$ |
| 8 | $3.713\times10^{-16}$ | $4.690\times10^{-8}$ | $3.966\times10^{-8}$ | $1.188\times10^{-2}$ | $7.917\times10^{-3}$ |
| 16 | $6.401\times10^{-16}$ | $8.718\times10^{-8}$ | $7.817\times10^{-8}$ | $1.995\times10^{-4}$ | $1.330\times10^{-4}$ |
| 32 | $1.383\times10^{-15}$ | $1.673\times10^{-7}$ | $1.560\times10^{-7}$ | $5.628\times10^{-8}$ | $3.752\times10^{-8}$ |

All exact block errors are below $10^{-12}$; raw and clipped noisy errors are
at most $\eta_N+10^{-12}$; and both N=32 tails are below $10^{-7}$ and decrease
strictly on the fixed grid. For every size, clipping stayed in $[1,1.5]$, the
finite-support adverse response gap was zero, and its held-out $w_N$ response
gap was `0.10000000000000005`, within the $10^{-12}$ tolerance. Every per-size
and run-level gate in the receipt is `true`.

Receipt SHA-256:
`080f22c9f2c4e03e31f95db73a0f8d1dfd72927ddb3254bd7a2ccaaddbad3743`.

## Interpretation boundary

This validates a deterministic numerical implementation of the preregistered
synthetic formulas and controls. It does not independently prove the
infinite-dimensional statements, remove the finite-query blind-tail no-go,
identify a neural basis, or test any real brain/EEG/fMRI/consciousness/self/AGI
hypothesis. No full test suite was run because it is unrelated to this focused
artifact validation.
