# Matched-intervention-twins pre-execution validation

Status: COMPLETE

Focused command:

```powershell
.codex\hooks\python.cmd pytest _workspace\ce\brain-ce-brain-synthetic-world-model-discrimination-20260826\artifacts\epochs\world-e-permutation-marginal-calibration\pivots\matched-intervention-twins\test_twin_confirmation.py -q
```

Stable-snapshot result: `13 passed in 0.20s`.

The suite is mechanical-only and uses fixtures or temporary copied
preregistration files. It does not generate or score the fresh confirmation
population. Covered behavior includes:

1. domain-separated root/purpose seed identity;
2. descriptor-before-confirmation access rejection;
3. uniform block-local permutation shape and deterministic draws;
4. linear twin identity and nonidentity fixtures;
5. parent hash mismatch and missing manifest rejection;
6. temporary manifest seal/verify and mutation rejection;
7. unique arm and CRN receipts while repeated linear contrasts remain allowed;
8. train/validation versus confirmation-arm overlap rejection;
9. equal-arm permutation invariance;
10. result-row selection serialization and descriptor receipt validation;
11. exact run-root and preregistration population.

No actual pivot manifest or result existed when this document was written.
