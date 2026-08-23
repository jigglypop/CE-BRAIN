# BA-SELF2 scale-free QC validation

Status: COMPLETE

Focused P0 synthetic validation:

```text
.codex\hooks\python.cmd pytest _workspace\ce\brain-self-trajectory-human-eeg-qc2-l3-20260824\artifacts\test_scale_free_qc.py -p no:cacheprovider
```

Result: `10 passed in 0.11s` with Python 3.11.9 and NumPy 2.4.6. The test file
covers common affine invariance including negative gain and channel offsets,
unit rescaling, disclosed channel-specific-gain non-invariance, zero/nonfinite
fail-closed behavior, deterministic spike/step adverse controls, the unscaled
A2 cutoff law, the production paired/session transfer gate, correct sibling
predecessor resolution, and offline preflight seal ordering.

This synthetic result is a numerical implementation check, not biological
evidence. The real-data apparatus receipts are recorded in
`30-implementation.md`: A1 and A2 passed their exact-range/hard-domain gates,
but D1 scale-free transfer failed at 13/32 paired accepts (8/16 and 5/16 by
session), so no model stage was authorized. No endpoint, target, feature,
loss, model result, self claim, consciousness claim, or biological mechanism
claim was produced.
