# Stage 2 successor models

Status: PREREGISTERED / OUTCOME_BLIND

The registered measurement models are deliberately small:

1. a nonnegative global-gain map from awake to isoflurane raw mean waveform;
2. a scale-free state representation formed by L2-normalizing each trial;
3. a three-state trajectory `awake -> isoflurane -> recovery` in that fixed
   representation.

No spatial metric, graph edge, cell type, spike mechanism or CE-specific term
is fitted. Cross-animal pooling is forbidden because current and valid-channel
availability differ; both animals must independently pass the same
dimensionless criteria.

