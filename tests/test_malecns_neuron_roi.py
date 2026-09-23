"""Independent tiny checks for the ROI-resolved dyad cache, not biological validation."""

import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "malecns_neuron_roi", Path(__file__).resolve().parents[1] / "verify/MaleCNS/neuron_roi.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_batch_dictionary_is_mapped_to_global_codes_and_null_is_none():
    lookup = {"CA(R)": 0, "gL(R)": 1, "aL(R)": 2, module.NONE: 3}
    codes = module.roi_codes(["aL(R)", "CA(R)"], np.array([1, 0, -1, 1]), lookup)
    assert codes.tolist() == [0, 2, 3, 0]


def test_chunk_reduction_and_merge_equal_one_global_count():
    rng = np.random.default_rng(0)
    keys = rng.integers(0, 50, size=1000)
    parts = [module.reduce_keys(chunk) for chunk in np.array_split(keys, 7)]
    merged_keys, merged_counts = module.merge_reduced(parts)
    expected_keys, expected_counts = np.unique(keys, return_counts=True)
    assert np.array_equal(merged_keys, expected_keys) and np.array_equal(merged_counts, expected_counts)


def test_type_roi_counts_filters_by_pre_and_post_masks():
    n, width = 3, 3
    # dyads (0->1, roi 0) x5, (0->1, roi 2) x1, (2->1, roi 1) x4, (1->0, roi 0) x7
    keys = np.array([(0 * n + 1) * width + 0, (0 * n + 1) * width + 2, (1 * n + 0) * width + 0,
                     (2 * n + 1) * width + 1])
    roi = {"key": keys, "count": np.array([5, 1, 7, 4]), "roi_names": ["a", "b", "c"], "node_count": n}
    pre, post = np.array([True, False, True]), np.array([False, True, False])
    assert module.type_roi_counts(None, roi, pre, post).tolist() == [5, 4, 1]
