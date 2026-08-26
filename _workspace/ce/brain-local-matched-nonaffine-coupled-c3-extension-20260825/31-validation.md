# Validation

Status: COMPLETE

The repository Windows Python wrapper was used. Its package-level `doctor`
diagnostic is already known on this unchanged environment to stop at the
missing optional `torch` dependency; no dependency or execution policy was
changed. The new modules are standard-library-only and were loaded directly.

Focused command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_local_matched_nonaffine_coupled_c3_graph_transform.py
```

Result: `28 passed in 0.12s`.

Dimensionless command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_dimensionless.py
```

Result: `42 passed in 0.13s`.

Adjacent predecessor command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_nonaffine_coupled_c3_graph_transform.py tests\test_quantitative_local_nonaffine_coupled_c2_graph_transform.py tests\test_quantitative_matched_local_nonaffine_coupled_c2_graph_transform.py tests\test_quantitative_local_matched_nonaffine_coupled_c3_graph_transform.py
```

Result: `134 passed in 0.50s`.

The exact three new sources compiled in memory and printed `OK source compile`.
The independent exact-rational audit printed `OK local/matched nonaffine
coupled C3 exact collar audit`. No full suite, benchmark, network, empirical
analysis, package install, or irreversible stage was run. The wrapper left no
run-owned pytest cache, bytecode, or fixed basetemp.
