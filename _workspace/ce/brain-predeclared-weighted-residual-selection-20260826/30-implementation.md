# Implementation

Status: COMPLETE

`predeclared_weighted_residual_selection.py` adds:

- immutable candidate, menu, development-result, and final-certificate records;
- exact weight normalization and canonical menu SHA-256;
- reconstruction checks that reject forged or changed menu objects;
- candidate-specific weighted full-circle development scores;
- exact unique-winner, unique-runner, and strict-advantage gates;
- exactly one selected-candidate heldout evaluation;
- separate heldout selected-weight margin and honest empirical/post-hoc flags.

The implementation calls the existing weighted residual verifier unchanged, so
all node contraction, condition-number translation, chord, rank, resolvent, and
projector claims retain predecessor semantics.
