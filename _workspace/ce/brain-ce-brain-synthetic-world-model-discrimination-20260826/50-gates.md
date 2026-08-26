# Stage 0 gates

Status: COMPLETE

The complete conjunction is frozen in `00-contract.md`:

- expected winner at least 10/12 per world;
- median validation margin at least 0.001 for A--E;
- median selected unseen composite NRMSE at most 0.50 for every world;
- at least 10/12 replicates per world improve on persistence by at least 20%;
- all 84 replicates preserve generator, split, serialization and finite-metric
  identities.

Any A--E failure produces `STAGE0_STRUCTURE_DISCRIMINATION_STOP`. F/G-only
failure produces `STAGE0_HISTORY_IDENTIFIABILITY_STOP`. Only the full conjunction
produces `STAGE0_PASS` and authorizes Stage 1.
