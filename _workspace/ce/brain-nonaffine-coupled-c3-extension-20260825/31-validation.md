# Validation

Status: COMPLETE

Required Windows entry point: `.codex/hooks/python.cmd`.

## Environment diagnostic

Command:

```powershell
.codex\hooks\python.cmd doctor
```

Result: failed during package-level `import reality_stone` because the selected
system interpreter does not contain `torch` (`ModuleNotFoundError`).  The new
certificate is standard-library-only, and all focused tests load its source
and direct predecessors without importing the Torch runtime.  No environment,
application-control policy, virtual environment, or dependency was changed.

## Focused validation and revision

Initial command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_nonaffine_coupled_c3_graph_transform.py
```

Initial result: `1 failed, 30 passed in 0.31s`.  The failure was the exact
affine reduction and identified the redundant lower graph-modulus input
described in `30-implementation.md`.

Final corrected result from the same focused command, including explicit C3
class-equality and graph-independent C3,1-bypass controls:

```text
33 passed in 0.15s
```

## Dimensionless validation

Command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_dimensionless.py
```

Result:

```text
40 passed in 0.13s
```

The new $H_\phi,T_\phi,U_\phi$, class radii, bunching factor, and recurrence
coefficients are all audited as normalized dimensionless quantities.  This is
an implementation consistency check, not a physical validation.

## Adjacent hierarchy regression

Command:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_graph_transform.py tests\test_quantitative_c1_graph_transform.py tests\test_quantitative_c2_graph_transform.py tests\test_quantitative_c3_graph_transform.py tests\test_quantitative_coupled_graph_transform.py tests\test_quantitative_coupled_c1_graph_transform.py tests\test_quantitative_coupled_c2_graph_transform.py tests\test_quantitative_coupled_c3_graph_transform.py tests\test_quantitative_nonaffine_c2_graph_transform.py tests\test_quantitative_nonaffine_c3_graph_transform.py tests\test_quantitative_nonaffine_coupled_c1_graph_transform.py tests\test_quantitative_nonaffine_coupled_c2_graph_transform.py tests\test_quantitative_nonaffine_coupled_c3_graph_transform.py
```

Result:

```text
326 passed in 1.27s
```

## Source and residue checks

The exact new source compiled in memory with `compile()` and returned exit
code zero.  The test wrapper created no bytecode for the new module or new
test, no run-owned `__pycache__`, and no pytest cache.  Older ignored cache
directories and files were already present and were not deleted.

No full repository suite, benchmark, package build, network operation,
empirical analysis, dependency installation, or execution-policy change was
performed.
