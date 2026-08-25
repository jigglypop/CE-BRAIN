# Validation record

Status: COMPLETE

## Focused apparatus

Command:

```powershell
.codex\hooks\python.cmd pytest -q tests/test_physical_scale_mobility.py
```

Result: 23/23 passed. Controls cover exact non-unit normalization, the unit-mobility slice, speed/power/rate outputs, oracle containment, series tightening, $q=0$, $q=1$, consistent rescaling, and fail-closed inputs.

## Dimensionless gate

Command:

```powershell
.codex\hooks\python.cmd pytest -q tests/test_dimensionless.py
```

Result: 25/25 passed. The new check verifies the mobility dimension
$[x]^2/([\mathcal V][t])$, dimensionless $\widetilde\mu,q,z$, velocity
$[x]/[t]$, power $[\mathcal V]/[t]$, and rate $[t]^{-1}$.

## Adjacent integration

Command:

```powershell
.codex\hooks\python.cmd pytest -q tests/test_quantitative_graph_transform.py tests/test_physical_scale_mobility.py tests/test_dimensionless.py
```

Result: 74/74 passed. This joins the predecessor's exact per-window tracking bound to the new scale-map apparatus without changing either theorem's premises.

The tests validate supplied exact inputs and algebra only. They do not supply a biological second, energy unit, neural mobility, measured $q$, or consciousness observable.

