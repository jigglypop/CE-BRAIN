# LBT-1: local synaptic learning with delayed stochastic execution

This is a **candidate computational mechanism**, not a discovery of the human brain algorithm. No new biological observations were analyzed in this package. Simulated data are explicitly identified.

The local update receives presynaptic events, instructive events, branch execution pulses, local traces and current weights. It never receives task labels, future loss, global replay search results or the evaluator's true-model index.

Read `REPORT_KO.md` for findings and limits and `ALGORITHM_KO.md` for equations, derivations and scope. Run:

```bash
OPENBLAS_NUM_THREADS=1 python test_local_rule.py
OPENBLAS_NUM_THREADS=1 python verify.py
```

The published `validation.json` includes a full final-code rerun check. To reproduce that particular byte check, copy a first final-code `results.json` to `results_final_before_rerun.json`, run `verify.py` once more, then run `check_results.py`. Different library/platform versions may change floating-point bytes; numerical equality is the substantive check.

`simulated_trials.npz` contains synthetic multivariate trials, not real neuronal recordings. `protocol.json` was written locally before the first execution but was not externally preregistered. No files were pushed to GitHub in this step.
