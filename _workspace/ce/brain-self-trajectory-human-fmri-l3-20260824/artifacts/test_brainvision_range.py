import importlib.util
from pathlib import Path

import numpy as np

MODULE_PATH = Path(__file__).with_name("brainvision_range.py")
SPEC = importlib.util.spec_from_file_location("brainvision_range", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_offset_geometry_is_inclusive_and_anchor_aligned():
    anchor = 10_000
    first, last, start, end = mod.byte_geometry(anchor)
    assert (first, last) == (7_500, 10_500)
    assert end - start + 1 == mod.SAMPLES_PER_WINDOW * mod.CHANNELS * 4
    assert (anchor - first - mod.WARMUP) % mod.DECIMATION == 0


def test_little_endian_multiplexed_float32_parsing():
    original = np.arange(mod.SAMPLES_PER_WINDOW * mod.CHANNELS, dtype="<f4").reshape(mod.SAMPLES_PER_WINDOW, mod.CHANNELS)
    parsed = mod.parse_multiplexed_float32(original.tobytes())
    assert parsed.shape == original.shape
    assert parsed[1, 0] == 64.0
    assert parsed[0, 31] == 31.0


def test_causal_filter_has_no_future_leakage():
    early = np.zeros((mod.SAMPLES_PER_WINDOW, mod.CHANNELS), dtype=np.float64)
    later = early.copy()
    later[2_800:, 0] = 1.0
    first = mod.causal_filter_and_decimate(early)
    second = mod.causal_filter_and_decimate(later)
    # The change begins after the retained output at original sample 2,800;
    # causal lfilter output before that sample cannot change.
    retained_original = mod.WARMUP + np.arange(first.shape[0]) * mod.DECIMATION
    assert np.array_equal(first[retained_original < 2_800], second[retained_original < 2_800])


def test_anchor_decimation_keeps_anchor_on_grid():
    samples = np.tile(np.arange(mod.SAMPLES_PER_WINDOW, dtype=np.float64)[:, None], (1, mod.CHANNELS))
    output = mod.causal_filter_and_decimate(samples)
    retained_original = mod.WARMUP + np.arange(output.shape[0]) * mod.DECIMATION
    assert mod.PRE_ANCHOR in retained_original
    assert output.shape == (126, 63)


def test_qc_requires_64_windows_and_nonzero_mad():
    metric = {"max_abs_common_reference_amplitude": 1.0, "max_abs_first_difference": 2.0}
    try:
        mod.qc_cutoffs([metric] * 64)
    except mod.ApparatusInvalid as error:
        assert "QC_SCALE" in str(error)
    else:
        raise AssertionError("constant QC metrics must fail closed")
