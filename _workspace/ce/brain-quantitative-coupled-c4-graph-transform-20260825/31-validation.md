# Validation

Status: COMPLETE

The unchanged package-level `doctor` remains unavailable because optional
`torch` is absent. The standard-library-only sources were loaded directly; no
dependency or policy was changed.

Focused command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_coupled_c4_graph_transform.py
```

Initial result: `1 failed, 21 passed in 0.24s`. The failure was the predecessor
status expectation described in `30-implementation.md`. Final result from the
same focused command: `22 passed in 0.12s`.

Dimensionless command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_dimensionless.py
```

Result: `44 passed in 0.14s`.

Adjacent hierarchy command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_coupled_graph_transform.py tests\test_quantitative_coupled_c1_graph_transform.py tests\test_quantitative_coupled_c2_graph_transform.py tests\test_quantitative_coupled_c3_graph_transform.py tests\test_quantitative_coupled_c4_graph_transform.py tests\test_quantitative_c4_graph_transform.py
```

Result: `141 passed in 0.61s`.

The two new sources compiled in memory. The independent scalar-series,
triangular-reduction and equality audit printed `OK affine coupled C4 identity,
reduction, and boundary audit`. No full suite, benchmark, network, data,
package installation, or irreversible operation was run. No run-owned cache,
bytecode, or fixed basetemp remains.
