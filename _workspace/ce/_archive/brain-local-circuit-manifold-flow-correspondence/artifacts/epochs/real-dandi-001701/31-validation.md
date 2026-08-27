# DANDI 001701 validation

Status: COMPLETE

## Commands

```powershell
& '.\.codex\hooks\python.cmd' python -c "from pathlib import Path; source=Path(r'_workspace\\ce\\brain-local-circuit-manifold-flow-correspondence\\artifacts\\epochs\\real-dandi-001701\\analyze_real_dandi.py').read_text(encoding='utf-8'); compile(source, 'analyze_real_dandi.py', 'exec'); print('PASS source-memory compile')"
```

Exit `0`:

```text
PASS source-memory compile
```

The sandboxed endpoint first failed with `WinError 10013` when contacting
`api.dandiarchive.org`; no synthetic substitute was used. After the P0/P1
masking and denominator correction, the source-memory command above passed
again and the exact analysis command was run with approved external network
access:

```powershell
& '.\.codex\hooks\python.cmd' python '_workspace\ce\brain-local-circuit-manifold-flow-correspondence\artifacts\epochs\real-dandi-001701\analyze_real_dandi.py'
```

Exit `0`. Aggregate terminal output:

```text
status: FAIL
retained_units: 295
NMSE affine_fiber: 0.9605287919155283
NMSE full_var: 0.9610053890618216
NMSE base_only: 0.9605781410709945
NMSE persistence: 1.575830863045975
q: 1.0955464648693762
kappa: 3.9189690360623772
q*kappa: 4.2934126733906846
```

## Honest endpoint

The verified source receipt records exactly `12,967,760` bytes and SHA-256
`5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3` before
decode; the temporary NWB was deleted afterwards.

The executable masking audit reports train-only retention boundary `487.3`
seconds and maximum admitted retention event `487.2995493098393` seconds;
the test boundary is `730.9000000000001` seconds and maximum admitted prefix
event time is `730.898633781808` seconds. Prefix shape `[7309, 295]` equals
`dev_end`, and no test-derived preselection array/statistic exists. The NMSE
denominator uses the mean
of all train bins `x[0:train_end]`.

This preregistered development endpoint is **FAIL**. The fitted fiber is not
contracting (`q > 1`) and fails bunching (`q*kappa > 1`). In addition, its
full-VAR improvement is only 0.0496%, below the 1% rule, and the paired full-
VAR bootstrap interval is `[-0.1140, 0.4095]`, whose lower bound is not above
zero. The shifted control is weaker, but it cannot repair either failure.

The result is a single-session observational model comparison, not evidence
for a biological invariant manifold, autonomous generator, metric, or any
claim beyond the contract ceiling. No full test suite was relevant or run.
