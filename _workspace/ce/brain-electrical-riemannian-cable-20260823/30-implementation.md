# BA-ERC1 L0 implementation

Status: COMPLETE

## 1. Implemented scope

The implementation is one deterministic NumPy verifier, `artifacts/verify_electrical_cable_l0.py`. It does not alter the repository runtime, load neural or behavioral data, fit parameters, estimate an effective dimension, or run E2 and later stages. Its only authorized task is to falsify elementary defects in the frozen electrical equation before expensive simulation.

## 2. Five fixtures

| fixture | implementation |
|---|---|
| U0 units | Exact integer SI-dimension vectors in the basis $(\mathrm{kg},\mathrm m,\mathrm s,\mathrm A)$ check the cable PDE, ionic current, metric-energy terms, $D_0$, and $i_0$. It also rejects IC/VC unit addition. |
| K0 Kirchhoff/Ohm | A deterministic three-edge Y junction uses outward edge coordinates and checks both derivative flux and physical outward-current sums. A decreasing voltage profile checks $I_\parallel=-\sigma A\partial_sV$. |
| P0 passive mode | A cell-centered finite-volume Neumann scheme solves $u_t=0.2u_{xx}-0.3u$ from $u(x,0)=\cos(\pi x)$ and compares with the exact mode. It records energy at every explicit-Euler step and compares 32- and 64-cell grids. |
| N0 active nonlinearity | A smooth voltage-dependent gate supplies an HH-type active conductance. Its midpoint residual is compared with an exactly linear fixed-conductance control. |
| H0 causal history | The compact bump $\exp[-1/(u(1-u))]$ on $0<u<1$ is normalized numerically; support, strict-past causality, time reversal, endpoint finite-difference proxies, and closed conductance bounds are checked. |

## 3. Fail-closed source and environment seal

The verifier hashes `00-contract.md`, `10-sources.md`, `11-math.md`, `12-routes.md`, and the execution-time preflight audit before any fixture runs. The preflight audit is preserved byte-for-byte as `artifacts/20-audit-preflight.md`; its SHA-256 is `f7333a259659a4fd758c1fdb7f008c282a777c8f31162f6f447f5eae2e76083a`. The current `20-audit.md` is a later post-run ledger, so its changed hash does not rewrite the source used by the receipt.

The Windows system interpreter selected by `.codex/hooks/python.cmd` was `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`, Python 3.11.9, NumPy 2.4.6, with bytecode disabled.

## 4. Preserved failed attempt and local apparatus revision

Attempt 00 passed U0, K0, P0, and N0 and failed H0 only. Its $10^{-20}$ finite-difference cutoff was below a defensible floating-point proxy scale, and logistic values at arguments $\pm100$ rounded to the closed bounds. The receipt was not overwritten. The exact attempt source was reconstructed from the logged hash and preserved; its hash matches the one embedded in the failed receipt.

Revision 1 changes only two H0 numerical predicates: the endpoint proxy tolerance becomes $1024\epsilon_{64}$ and the floating implementation admits the mathematically prescribed closed interval $[g_{\min},g_{\max}]$. The bump, electrical equations, sources, U0/K0/P0/N0 code, grids, thresholds, and observations are unchanged. The $C^\infty$ endpoint-flat property comes from the exact bump construction, not from the finite-difference tolerance.

## 5. Artifact manifest

| artifact | SHA-256 | role |
|---|---|---|
| `artifacts/verify_electrical_cable_l0_attempt_00.py` | `e27d70fe5543489d11b54f88a5eb0631129da5f69dd00fe17ab14cc7a1e9f7d9` | exact failed-attempt source archive |
| `artifacts/l0-receipt-attempt-00.json` | `848a0a5ab528dc681eff9c384dbb0e733366ba3e89e45a2283399965658b41c4` | preserved H0-only failure |
| `artifacts/verify_electrical_cable_l0.py` | `708740755c0b183aa37aaa7883baa96dcd2a7347a5c76a72df0f46f49b7e9ce8` | final verifier |
| `artifacts/l0-receipt.json` | `9e643eaf70302ff4369f15bf1fa044f11660a45c9148869395fb65a643006501` | final L0 receipt |

The focused source check compiled each verifier in memory. The executed final command was

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-electrical-riemannian-cable-20260823\artifacts\verify_electrical_cable_l0.py --output _workspace\ce\brain-electrical-riemannian-cable-20260823\artifacts\l0-receipt.json
```

This was a sealed one-shot against the archived preflight audit. It is not rerun after the post-run ledger update.
