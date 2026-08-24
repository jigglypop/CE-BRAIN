# BA-OBS-ID2 implementation

Status: COMPLETE

## Scope

This lane implements only the frozen synthetic witness in `00-contract.md` after
the `20-audit.md` `Gate: PASS`. It does not alter the theorem, assumptions,
query menu, thresholds, or claim ceiling.

`artifacts/validate_active_metric_tomography.py` evaluates the analytic
infinite-support rank-one mobility on real $\ell^2$:

$$
v_n=\sqrt{1-r^2}\,r^{n-1},\quad r=0.60,\qquad
M=I+0.50\,v\otimes v.
$$

It uses $Q(f)=\|f\|^2+0.50\langle v,f\rangle^2$. For each
$N\in\{4,8,16,32\}$ it issues exactly $N^2$ queries in the frozen diagonal,
then lexicographic plus/minus order; reconstructs a symmetric block by real
polarization; adds deterministic alternating noise; and clips only the
measured mobility block to $[1,1.5]$.

The analytic tails use the cancellation-safe contract formulas:

$$
\|M-M_N\|_{\rm HS}=\beta\sqrt{2b_N-b_N^2},
$$

$$
\|G-G_N\|_{\rm HS}=c\sqrt{2a_Nb_N+b_N^2+
\frac{\beta^2a_N^2b_N^2}{(1+\beta a_N)^2}}.
$$

It also constructs $w_N=(r e_{N+1}-e_{N+2})/\sqrt{1+r^2}$ and checks that
$M+0.10w_N\otimes w_N$ remains in the $[1,1.5]$ mobility spectral class, is
invisible to the first $N^2$ queries, and changes the held-out $w_N$ response
by $0.10$.

## Reproduction

```powershell
.codex\hooks\python.cmd doctor
.codex\hooks\python.cmd python -c "from pathlib import Path; p=Path(r'_workspace\ce\brain-complete-active-metric-tomography-20260824\artifacts\validate_active_metric_tomography.py'); compile(p.read_text(encoding='utf-8'), str(p), 'exec'); print('source compile: PASS')"
.codex\hooks\python.cmd python _workspace\ce\brain-complete-active-metric-tomography-20260824\artifacts\validate_active_metric_tomography.py --output _workspace\ce\brain-complete-active-metric-tomography-20260824\artifacts\active_metric_tomography_receipt.json
```

Implementation SHA-256:
`e9f2e70775c4200a2ad8f46bd2b6c740f70a875d8b45f46135ab883e5f1b8572`.

## Interpretation boundary

This is a numerical reproduction of an analytic $\ell^2$ example. PASS means
the frozen arithmetic gates were reproduced; it is neither a proof of T4--T5
nor evidence about biological brains, consciousness, selfhood, hippocampus, or
AGI.
