# BA-SRM9 formal status audit

Status: COMPLETE

Gate: PASS

Date: 2026-08-23

## 1. Decision

P0: none.  
P1: none.

The independent post-receipt math and status audits pass with P0/P1 none. BA-SRM8 F2-A remains `NOT_INHERITED`. BA-SRM9 has sealed synthetic F2-A and F2-B selection receipts only; their receipts keep `behavior=false`, `model=false`, `real_endpoint_opened=false`, and `downstream_authorized=false`.

## 2. Frozen evidence

| artifact | SHA-256 | audit role |
|---|---|---|
| `00-contract.md` | `e1e24e6c5252b5033f1ebf55ef0fb08fee77918e69d01705f67d4934c96cdb5c` | JUMP mixing, fixture matrix, eligibility, and stop contract |
| `10-sources.md` | `e0e001e063167afc0aae57bf3f1f1875217329d65eb2db48105f04469182502a` | carried Hallinen/OSF/code and synthetic provenance |
| `11-math.md` | `b3f7206ceaddb1c59f830ad2f7a88c3954cc45f3f375e66a973c17a646c769b5` | conditional PSD/resolvent and latent mixing lemma |
| `12-routes.md` | `808969d736ae7e4342555f95bb61085bfdeb153409ac3a5212bff03c784295f8` | successor boundary and unopened routes |
| BA-SRM8 ledger row | `8256c0eb6b48e5c9a83ba061049e5409044a1d90da9cef85f45027daf48c8c51` | predecessor `SYNTHETIC_DGP_STOP / REAL_ENDPOINT_UNOPENED` |
| BA-SRM8 F1-v6 receipt | `8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca` | exact carried 32-candidate receipt |
| BA-SRM8 config-v4 | `9248c9fac975ea70ac034d11e45be70eff7abccb13b65eae7be7010850e2de47` | unchanged non-JUMP F2 apparatus |
| carry receipt | `08ccdcfb27e9e87e4e8608ea2aafca5871ab9103c3b4730a47126a47e47d5b1e` | exact carry-forward verification PASS |
| fixture wrapper | `f8be7234124abc094b71f0000a775121d939c29013eb42921dad09149c342dca` | frozen fixture invocation |
| BA-SRM9 config | `7ac07dda3e1b077fdeb5d0d4f49693499ab6f89c0f68e3f9a89838aa1987eece` | JUMP mixing configuration |
| config receipt | `ec48392bb0343e3a2a20e040e3df61e7c395e0053c2651e0a6d5eaf0c910cb71` | config freeze receipt |
| fixture script | `0aceb288907590fd7fab9010d1238f1bdf5e9b6c40887bad8a92e2e1fb01db81` | E_A8 fixture implementation |
| fixture receipt | `028b24a16cb154fa238b53114de1519fb06531e6436fbf498f5b4d605d34daf4` | E_A8 apparatus PASS |
| sealed F2-A receipt | `24c1099c63b0e7e59f107788e57bc122c62a267936a0313b03c12d88e2be6aab` | numerical F2-A selection receipt |
| sealed F2-B receipt | `ad402c8a872af3461d9600cad4b792eb1440761f5f8222c5b653511cf35f72b2` | numerical F2-B selection receipt |

## 3. Fixture result

All eight E_A fixture seeds passed; non-JUMP mismatch count is `0`. The minimum clean prefix SD is `0.060927299368900928`, every channel's observed count is `396`, and the maximum orthogonality residual is `2.7716728888183493e-15`. The minimum row energy is `0.0017128708194032386` for the first two columns and `0.25942127655406372` for the first eight. Maximum latent support residuals are `1.0987340648312856e-15` before the jump and `2.6667066647611547e-15` after it. These are fixture diagnostics, not predictive or biological results.

## 4. Sealed F2-A result

The sealed receipt used runner `6d763931dbad79586c0c28c5e4799c80c1b69a762cd510ff7c6e612f8b70ebed` and authorization audit `67eb581ba4adc7af45e47dae251166d5ad0a990444b17c2b012123f818008702`. Its promoted-array SHA-256 is `d9cd28edd708abe1c4cf44c81854b0e62461a5eb7593ba71fe8d21d1c12f83f3`. Of 32 candidates, 24 are `PROMOTE`, 8 are `FUTILITY_KILL`, and all other status counts are zero; total runtime is `72.86263369990047` seconds. Each kill has only 2--3 JUMP detections. Across promoted candidates, minimum $\rho$ is approximately `.979`, maximum NMAE is approximately `.0407`, maximum FAR is approximately `.0483`, and minimum detections is 4. This is a frozen synthetic selection result only; it does not open behavior, a model, or the real endpoint.

## 5. Sealed F2-B result

The sealed F2-B receipt used runner `9a7c93f722521e36311694d9f32359b1abc85cbc5008e9c5c28087a265a91287` and execution authorization audit `54268c109f6c28b17f3a5c1559343e0d6700ac75a72713e5ee4fd69076c63006`. Its promoted-array SHA-256 is `270a1885fc649e6700065cf2901a72904d1fe345d61d1e37e9c16abca1d4e722`. Of 24 candidates, 20 are `PROMOTE`, 4 are `DROPPED_BUDGET`, and all other status counts are zero; total runtime is `28.03884949994972` seconds. Across the ROT10/MISS30 scored records, $\rho\in[0.97381158737532,0.997660223387542]$, NMAE $\in[0.0154232695962794,0.0391859037649899]$, and recovery anchor count $\in[588,760]$. Candidate ranking values span $E\in[0.0215889021290078,0.0326016886231097]$, $R\in[0.983302660327477,0.993513547590989]$, and frozen ISO FAR $\in[0.0427919657481129,0.0482860262168209]$. These are synthetic apparatus metrics only. Both independent post-receipt math and status audits PASS with P0/P1 none.

## 6. Authorized scope

1. Retain the exact BA-SRM8 F0-v3/F1-v6 carry-forward receipts and promoted-ID array hash.
2. Retain the BA-SRM9 JUMP config/generator/E_A8 fixture and sealed F2-A receipt.
3. Execute F2-C for the 20 F2-B promoted candidates, with the frozen cap $20\to16$ only.

F2-A and F2-B were sealed under their respective source/environment preflights and their receipts passed both independent post-receipt audits.

## 7. Locked scope

F2-D, confirmation, F2R, behavior, model fitting, real neural data, endpoint scoring, and every biological, synaptic-edge, loop, hippocampal, consciousness, and AGI interpretation remain locked. No BA-SRM8 F2-A result exists to inherit.

## 8. F2-A execution-source seal

The exact-source math audit passes all formula, import, cache, and gate checks conditionally on this seal. The independent status audit passes with P0/P1 none and authorized the sealed F2-A runner.

Runner SHA-256: `6d763931dbad79586c0c28c5e4799c80c1b69a762cd510ff7c6e612f8b70ebed`
Interpreter: `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`
Python: `3.11.9`
NumPy: `2.4.6`
SciPy: `1.17.1`

At the source-seal audit time, numerical F2-A and candidate $Q$ had not run; the sealed F2-A receipt above supersedes that runtime status. Any runner, interpreter, or dependency mismatch remains a fail-closed preflight stop. F2-C/D, F2R, behavior, model, and the real endpoint remain locked.

## 9. F2-B execution-source seal

The two independent F2-B source audits pass with P0/P1 none. At this pre-execution source-seal audit time numerical F2-B had not run and F2-B was the only newly authorized stage; the sealed F2-B receipt in section 5 supersedes that time-qualified runtime status.

F2-B Runner SHA-256: `9a7c93f722521e36311694d9f32359b1abc85cbc5008e9c5c28087a265a91287`
F2-B Interpreter: `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`
F2-B Python: `3.11.9`
F2-B NumPy: `2.4.6`
F2-B SciPy: `1.17.1`

Execute numerical F2-B from its first seed

Any runner, interpreter, or dependency mismatch is a fail-closed preflight stop. F2-D, confirmation, F2R, behavior, model, and the real endpoint remain locked.

## 11. Post-F2-C stable-snapshot audit

The pre-execution authorization bytes for section 10 have SHA-256
`727606ea4a8d7dbc74374bbc6ed7b1b2614a75cf6c106cfb977310d2a02c48fb`.
The one-shot F2-C receipt records that exact authorization hash, runner SHA-256
`361fa1b7b8d6af1576d5a02d76159f5f9e2a6215ecedf5b95bc66cee1e209b80`,
and the frozen Python 3.11.9, NumPy 2.4.6, and SciPy 1.17.1 environment.
Its own SHA-256 is
`a43e14da1e099f30d3cb970f35db199159be83916b9ce33e685f494641958bf2`.

Independent status and mathematics audits found no P0 or P1 defect. The
F2-A and F2-B receipts are present at their frozen paths and rehash to
`24c1099c63b0e7e59f107788e57bc122c62a267936a0313b03c12d88e2be6aab`
and `ad402c8a872af3461d9600cad4b792eb1440761f5f8222c5b653511cf35f72b2`.
The ordered 20-candidate F2-B promoted array is identical to the F2-C input
array and has SHA-256
`270a1885fc649e6700065cf2901a72904d1fe345d61d1e37e9c16abca1d4e722`.
Preflight passed all 16 scenario-by-seed cache entries.

**[산출: 동결 합성 비교]** All 20 candidates are `FUTILITY_KILL`; no
candidate is `PROMOTE`, `DROPPED_BUDGET`, `ABSTAIN`, or `INVALID_KILL`.
For every candidate, BLOCK30 passed both frozen median gates, while ART10
median NMAE passed and ART10 median Spearman recovery failed. Across candidates,
ART10 median recovery lies in
`[0.6136981053328, 0.7404632890000811]`, strictly below the frozen `0.80`
threshold; BLOCK30 lies in
`[0.9284251656475162, 0.9788390822185931]`. Therefore no ranking or cap
tie is involved in the result.

The receipt fixes `downstream_authorized=false`, `behavior_loaded=false`,
`model_fit=false`, `real_endpoint_opened=false`, and `biological_claim=false`.
F2-D, confirmation, F2R, behavior, model fitting, the real endpoint, and every
biological, synaptic-edge, loop, hippocampal, consciousness, and AGI
interpretation remain sealed. This closes BA-SRM9 as
`SYNTHETIC_F2C_FUTILITY_STOP / REAL_ENDPOINT_UNOPENED`. Reopening requires a
new contract and a genuinely different candidate mechanism; changing the
frozen F2-C threshold, panels, or candidates after this result is prohibited.

Gate conclusion: **PASS -- close the run at F2-C; authorize no downstream stage.**

Gate conclusion: **PASS -- F2-C $20\to16$ only; F2-D, confirmation, F2R, behavior/model, and the real endpoint remain locked.**

## 10. F2-C execution-source seal

The independent F2-C math and status source audits PASS with P0/P1 none. At this source-seal time F2-C has not yet run. F2-C is the only newly authorized numerical stage; all downstream stages remain locked.

Execute numerical F2-C from its first seed

F2-C Runner SHA-256: `361fa1b7b8d6af1576d5a02d76159f5f9e2a6215ecedf5b95bc66cee1e209b80`
F2-C Interpreter: `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`
F2-C Python: `3.11.9`
F2-C NumPy: `2.4.6`
F2-C SciPy: `1.17.1`

Any runner, interpreter, or dependency mismatch is a fail-closed preflight stop. F2-D, confirmation, F2R, behavior, model, and the real endpoint remain locked.
