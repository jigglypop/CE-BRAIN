# BA-ERC1-E3b implementation

Status: COMPLETE

`artifacts/verify_synaptic_history_e3b.py` implements the frozen E3b-0 through E3b-2 synthetic discrimination protocol. It fits the finite exponential menu $E_1,E_2,E_4,E_8$ and the one-gain compact $C^\infty$ history bump $B$ on calibration traces, selects on the development traces, and opens the confirmation traces only through the frozen negative-then-positive gate order. The nonlinear Volterra stage E3b-3, conductance re-embedding, biological data, behavior, consciousness, and AGI claims remain unopened.

The verifier uses SVD-based least squares on normalized design columns, checks rank and normalized conditioning, evaluates an independent dense lag grid, and includes a time-reversed bump adverse control. It fail-closes on the frozen input, predecessor, older-evidence, preflight-archive, and interpreter/dependency seals. It refuses to overwrite an existing receipt.

| pre-build item | result |
|---|---|
| memory-only AST source parse | PASS |
| verifier SHA-256 | `b252a274cc24e30c02a369202cfbab99ea8858ba7aa6b81314f97fa253e7c2ee` |
| preflight audit/archive SHA-256 | `aa96f0ba86c955b38a7fabb3310f525dd99594ff0cc6689b9bbe365db30a3e4f` |
| apparatus revision before execution | none |

Authorized one-shot command:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-electrical-synaptic-history-e3b-discrimination-20260823\artifacts\verify_synaptic_history_e3b.py --output _workspace\ce\brain-electrical-synaptic-history-e3b-discrimination-20260823\artifacts\e3b-receipt.json
```

At pre-build time no numerical result or receipt exists.

## One-shot execution

The authorized command ran once and exited zero. It created `artifacts/e3b-receipt.json`, SHA-256 `0f96a49ead927620ecaca06d13bb1ab2ad26d7222a45935df45c29b370283d68`. The recorded verifier hash matches the pre-build hash, all frozen seals and checks pass, `failed_checks=[]`, and no apparatus revision or rerun occurred.

The negative generator selected $E_2$ with confirmation relative error $6.17410328886224\times10^{-16}$. Only after that gate passed, the positive panel opened and selected $B$ with confirmation relative error $1.60615500530870\times10^{-16}$. Its best finite competitor was $E_8$, with confirmation error $0.2270211315620434$ and dense-kernel error $0.2891662558095040$; the reversed-bump adverse control had confirmation error $0.5722092307645735$.
