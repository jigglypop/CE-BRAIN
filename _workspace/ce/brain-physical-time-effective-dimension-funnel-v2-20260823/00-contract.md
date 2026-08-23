# BA-SRM9 successor contract — JUMP observed-mixing repair only

Status: COMPLETE

Mode: full successor; F2-A locked until fixture plus independent math/status audits pass.

PREDECESSOR: BA-SRM8 ledger row SHA-256 `8256c0eb6b48e5c9a83ba061049e5409044a1d90da9cef85f45027daf48c8c51`, verdict `FORMALIZATION_COMPLETE / SYNTHETIC_DGP_STOP / REAL_ENDPOINT_UNOPENED`.

## 1. Scope and status

BA-SRM9 changes only the JUMP observed sensor mixing that caused the BA-SRM8 synthetic-DGP stop. It does not change the candidate family, physical-time PSD/resolvent formula, F2 panels, gates, ranking, status vocabulary, clock, masking, noise, preprocessing, behavior boundary, or real endpoint.

**[미완성]** No fixture, independent math audit, or status audit has yet passed in BA-SRM9. F2-A may be restarted only after all three occur. BA-SRM8 F2-A has no completed receipt and is never inherited.

## 2. Immutable predecessor inputs

| input | SHA-256 | BA-SRM9 rule |
|---|---|---|
| 48-candidate manifest | `58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c` | exact identity/order source |
| core | `e685568ad4836dab1f301f69afa2e9c9a4d8fcecd7a1a64fb2bdba830a5ebc65` | unchanged |
| valid F0-v3 receipt | `86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7` | carried only by exact hash |
| self-contained F1-v6 runner | `3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7` | carried only by exact hash |
| F1-v6 receipt | `8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca` | carried only by exact hash |
| BA-SRM8 config-v4 | `9248c9fac975ea70ac034d11e45be70eff7abccb13b65eae7be7010850e2de47` | unchanged except JUMP mixing |

The carried F1 outcome is 48 total candidates: 12 short-memory `ABSTAIN`, 36 numerical pass, 32 `PROMOTE`, and 4 `DROPPED_BUDGET`. The exact ordered UTF-8 compact JSON `promoted_ids` array from F1-v6 has SHA-256 `b4c2ef2e4160711b4b26b35195a3ace8c2376eb32910f9aec008973ff7dc678b`. Any mismatch in a required input hash or this array hash is `STOP_RE_RUN_AFFECTED_STAGE`; F0/F1 are not silently carried forward.

## 3. Carried F2 apparatus

**[공리: 분석 apparatus]** Panels, gates, ranking, candidate status, zero-based boundaries, physical clock, missingness, Gaussian noise, prefix preprocessing, $A/B$ anchors, FAR/JUMP threshold, and `MISS50` descriptive-only treatment are exactly those of BA-SRM8 config-v4. No behavior value, behavior model, biological target, or real neural endpoint is opened.

## 4. BA-SRM9 JUMP generator

All BA-SRM8-v2 named clock/latent/noise/mask streams remain unchanged for comparability. BA-SRM9 adds one independent mixing seed: the first eight big-endian bytes of UTF-8 SHA-256 `BA-SRM9-F2-SH-v1|JUMP|<base_seed>|jump_mixing` form an unsigned 64-bit seed. With that seed, generate $Z\in\mathbb R^{12\times12}$ with standard-normal entries and take square reduced-mode `np.linalg.qr(Z, mode="reduced")=(Q,R)`. Put $s_k=\operatorname{sign}(R_{kk})$, replacing zero by $1$, and define

$$
H=Q\operatorname{diag}(s_1,\ldots,s_{12}).
$$

This fixes a deterministic orthogonal orientation rather than a post-hoc rotation. $H$ is C-order `float64`; `all(H != 0)` is a fail-closed fixture condition.

For $t<384$, set $r_t=2$; for $t\ge384$, set $r_t=8$. The JUMP latent signal is

$$
x_t=H_{:,1:r_t}\xi_{1:r_t,t},\qquad \xi_{1:r_t,t}\sim N(0,I_{r_t}),
$$

with the unchanged BA-SRM8 calcium recursion, clock, noise, mask, and prefix preprocessing. This is the only generator change.

## 5. Pre-F2-A fixture gate

The fixture is for the eight $E_A$ JUMP seeds only, must precede F2-A, and must contain no candidate $Q$, candidate status/promotion, behavior, model, or endpoint value. It records Python, NumPy, SciPy, and every $H$ hash because QR bytes can depend on LAPACK. For $r\in\{2,8\}$ it defines the latent pre-calcium covariance $\Sigma_{x,r}=H_{:,1:r}H_{:,1:r}^\mathsf T$ and verifies $|\operatorname{tr}\Sigma_{x,r}-r|\le10^{-10}$ and the infinity residual of sorted `eigvalsh` against $[0]^{12-r}\cup[1]^r$ is at most $10^{-10}$; `matrix_rank` and tolerance-based rank tests are forbidden. It verifies $\|H^\mathsf TH-I\|_\infty\le10^{-12}$, `all(H != 0)`, and every row's first-2 and first-8 energy exceeds $10^{-12}$. Eligibility is exactly $I_i=\{t<460:m_{i,t}=1\}$ with $|I_i|\ge100$, and the clean-calcium $y$ prefix SD with `ddof=0` over $I_i$ exceeds $10^{-12}$ for every channel. Support residuals use latent $x$ against spans $H_{:,1:2}$ and $H_{:,1:8}$, never calcium-$y$ projector equality. Finite/binary mask/increasing clock/determinism checks also pass. Any failure is `SYNTHETIC_DGP_STOP`.

Only after fixture PASS plus independent math and status audits may F2-A restart from its first seed. F2-B/C/D, F2R, behavior, model fitting, and the real endpoint remain unopened.
