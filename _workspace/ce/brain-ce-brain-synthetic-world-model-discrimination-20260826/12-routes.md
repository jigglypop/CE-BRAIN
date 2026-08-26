# Route lane

Status: COMPLETE

Selected route: one deterministic NumPy implementation with explicit generator,
split-sealing, candidate-fit, validation-selection, once-only unseen evaluation,
negative-control and atomic receipt layers.

Rejected routes:

- deep learned classifier: unnecessary capacity and opaque class leakage;
- per-world hand-tuned models: invalidates common-candidate comparison;
- selection on unseen performance: direct leakage;
- training reconstruction ranking: contradicts the manual's intervention gate;
- importing predecessor CCEP outcomes: contaminates a logically prior benchmark.

The implementation owner may optimize linear algebra but may not change features,
seeds, splits, thresholds or expected classes after the preregistration manifest
is sealed.
