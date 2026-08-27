# DANDI 001701 implementation

Status: COMPLETE

`analyze_real_dandi.py` downloads only the immutable asset frozen in the
contract to an owned temporary directory. It checks both the byte count and
whole-file SHA-256 before HDF5 decoding, locates NWB `units/spike_times` and
`units/spike_times_index` directly, and deletes the NWB in a `finally` block.

Whole-file/per-unit HDF5 reads are used only to apply the frozen prefix mask.
Before selection, executable assertions require both prefix matrices to end at
the development boundary and every admitted event time to be strictly below the
test boundary. Prefix retention statistics are computed from those masked
events only. The retained-unit set is frozen at 0.1 Hz from `[0, train_end)`;
development and test use that unchanged set. The test-count array is not decoded until the development-selected
affine-fiber dimension/ridge and independently selected full-VAR ridge are
locked; an explicit `test_materialized` assertion enforces that ordering.
It emits only aggregate `result.json` and provenance `source-receipt.json`.

The frozen scoring paths are implemented: coverage metadata and gap handling,
100-ms bins, train-only Anscombe scaling/PCA, split-local rows, affine-fiber
and full-VAR development selection, held-out NMSE (with the mean of all train
bins `x[0:train_end]` in its denominator), moving-block bootstrap,
certificates, secondary invariant residual, multistep horizons, and the
no-wrap 100-bin shifted refit control. No coefficient clipping, post-hoc
selection, synthetic substitution, or Git operation is present.
