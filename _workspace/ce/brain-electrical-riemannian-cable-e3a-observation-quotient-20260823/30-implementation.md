# BA-ERC1-E3a implementation

Status: COMPLETE

`artifacts/verify_observation_quotient_e3a.py` implements the frozen 3-by-41 exact observation matrices, equal-weight branch projector, Frobenius unresolved-energy score, and collapsed A0 no-go control. It performs no optimization, random draw, biological fit, or import of the E2 solver.

The verifier fail-closes on hashes of 00/10/11/12/20, all nine E2 predecessor items, the archived preflight audit, Python/NumPy environment, projector algebra, finite outputs, and the no-go control. It refuses to overwrite a receipt.

| pre-build item | result |
|---|---|
| AST source parse | PASS |
| verifier SHA-256 | `9ef1c2074ca2195f617a934102437e13f260ba39a165a74d1e5d1b7a521900fb` |
| preflight audit/archive SHA-256 | `d6112b508ce8c82c9a3f34d100896ca9c201a947eed84bae6c9618b55ab71391` |

Authorized one-shot command:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-electrical-riemannian-cable-e3a-observation-quotient-20260823\artifacts\verify_observation_quotient_e3a.py --output _workspace\ce\brain-electrical-riemannian-cable-e3a-observation-quotient-20260823\artifacts\e3a-receipt.json
```

At pre-build time no numerical result or receipt exists.

## One-shot execution

The authorized command ran once and exited zero. It created `artifacts/e3a-receipt.json`, SHA-256 `4ad4d72e6136d9849fd1f6265c85decd2263ac6090107d878f1da3e1515beb5e`. The recorded verifier hash matches the pre-build hash, every seal/check passes, `failed_checks=[]`, and no apparatus revision or rerun occurred.
