# BA-SRM9 implementation record

Status: COMPLETE

## Authorized scope

This implementation record closes the already executed, behavior-blind BA-SRM9
synthetic funnel. The pre-execution audit authorized only F2-C for the 20
candidates promoted by F2-B. It did not authorize F2-D, confirmation, F2R,
behavior access, model fitting, real neural data, or a biological endpoint.

The sealed runner is `artifacts/run_f2c.py`, SHA-256
`361fa1b7b8d6af1576d5a02d76159f5f9e2a6215ecedf5b95bc66cee1e209b80`.
The one-shot receipt is `artifacts/f2c-receipt.json`, SHA-256
`a43e14da1e099f30d3cb970f35db199159be83916b9ce33e685f494641958bf2`.
It records the authorized interpreter
`C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`, Python
3.11.9, NumPy 2.4.6, and SciPy 1.17.1. The predecessor F2-A and F2-B receipt
hashes are respectively
`24c1099c63b0e7e59f107788e57bc122c62a267936a0313b03c12d88e2be6aab`
and `ad402c8a872af3461d9600cad4b792eb1440761f5f8222c5b653511cf35f72b2`.

## Frozen computation

For each candidate and each of the eight $E_C$ seeds, the runner evaluates the
BLOCK30 and ART10 scenarios. A candidate passes a scenario only when its median
Spearman recovery satisfies $\rho\ge0.80$ and its median normalized mean
absolute error satisfies $\operatorname{NMAE}\le0.20$. It is promoted only if
both scenarios pass; the cap from 20 to 16 is applied after this gate.

The execution opened exactly 20 F2-B candidates and 16 scenario-by-seed cache
entries. All 20 candidates failed before ranking because ART10 median recovery
was below $0.80$. Consequently the receipt has an empty promoted array and
`downstream_authorized=false`.

## Read-only validator

`artifacts/validate_f2c_receipt.py`, SHA-256
`5c443a7f4a1a57ec759b181e3fd66818a6a5cfacbe5e69d3e0503bd44c1c8f50`,
checks the immutable receipt chain, ordered candidate identity, exact status
counts, frozen gate calculation, and sealed downstream flags without executing
the scientific stage again.

No production runtime, brain model, AGI runtime, or real-data code was changed.

