# Stage 0 pre-execution validation

Status: COMPLETE

Environment: Windows repository hook using its selected non-venv system Python;
NumPy float64 implementation; no dependency resolution or network access.

Focused command:

```powershell
.codex\hooks\python.cmd pytest _workspace\ce\brain-ce-brain-synthetic-world-model-discrimination-20260826\artifacts\test_stage0_synthetic_discrimination.py -q
```

Result after the stable-snapshot changes: `6 passed in 0.87s`.

Covered checks:

1. deterministic seed, split and generator identities;
2. train/validation-only selection API and deterministic descriptor hashing;
3. execute fails closed when the preregistration manifest is absent;
4. real trajectory-overlap verification and unstable-rollout fail-closed paths;
5. incomplete 84-replicate population rejection;
6. all 84 frozen generators and all 252 splits are finite, unique and
   identity-valid.

Independent mathematics validation additionally recomputed all 84
train/validation selections without opening unseen metrics. Every world's
expected class was selected 12/12 times and every registered A--E validation
margin exceeded `0.001`.

No Stage 0 scientific outcome has been produced by this validation. The next
allowed action is manifest sealing, followed by the single execute entry point.
