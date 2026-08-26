# Validation

Status: COMPLETE

The unchanged repository Python environment still lacks optional `torch` for
package-level `doctor`; the new standard-library-only source was loaded
directly and no environment change was made.

Focused command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_c4_graph_transform.py
```

Result: `26 passed in 0.10s`.

Dimensionless command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_dimensionless.py
```

Result: `43 passed in 0.13s`.

Adjacent hierarchy command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_graph_transform.py tests\test_quantitative_c1_graph_transform.py tests\test_quantitative_c2_graph_transform.py tests\test_quantitative_c3_graph_transform.py tests\test_quantitative_c4_graph_transform.py
```

Result: `113 passed in 0.40s`.

Both new sources compiled in memory and printed `OK source compile`. The exact
partition/fixture/witness artifact printed `OK affine triangular C4 partition,
recurrence, and boundary audit`. No full suite, benchmark, network, empirical
analysis, package installation, or irreversible operation was run. No
run-owned pytest cache, bytecode, or fixed basetemp remains.
