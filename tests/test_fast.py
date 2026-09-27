import cefast
import numpy as np
import pytest


@pytest.fixture
def trains():
    rng = np.random.default_rng(1)
    cells = [np.sort(rng.uniform(0, 100, n)) for n in (0, 1, 500, 3000)]
    return cells, np.concatenate(cells), np.cumsum([len(c) for c in cells])


def test_bin_counts_match_searchsorted(trains):
    cells, times, ends = trains
    edges = np.r_[-1.0, np.sort(np.random.default_rng(2).uniform(0, 100, 50)), 101.0]
    expected = np.stack([np.diff(np.searchsorted(c, edges)) for c in cells])
    assert np.array_equal(cefast.bin_counts(times, ends, edges), expected)
    assert cefast.bin_counts(times, ends, edges[:1]).shape == (4, 0)


def test_window_counts_allow_overlap(trains):
    cells, times, ends = trains
    starts = np.random.default_rng(3).uniform(0, 100, 200)
    stops = starts + 7.5
    expected = np.stack([np.searchsorted(c, stops) - np.searchsorted(c, starts) for c in cells])
    assert np.array_equal(cefast.window_counts(times, ends, starts, stops), expected)


def test_ccg_matches_all_pair_lags(trains):
    cells, times, ends = trains
    width, half = 0.01, 20
    got = cefast.ccg(times, ends, times, ends, width, half)
    for i, a in enumerate(cells):
        for j, b in enumerate(cells):
            lag = (b[None, :] - a[:, None]).ravel()
            lag = lag[np.abs(lag) < (half + 0.5) * width]
            expected = np.bincount(((lag + (half + 0.5) * width) / width).astype(int), minlength=2 * half + 1)
            assert np.array_equal(got[i, j], expected)
    assert np.array_equal(np.diag(got[:, :, half]) >= np.diff(np.r_[0, ends]), [True] * 4)


def test_rejects_unsorted_or_bad_input():
    times = np.array([2.0, 1.0])
    with pytest.raises(ValueError, match="not sorted"):
        cefast.bin_counts(times, np.array([2]), np.array([0.0, 3.0]))
    with pytest.raises(ValueError, match="end index"):
        cefast.bin_counts(np.sort(times), np.array([3]), np.array([0.0, 3.0]))
    with pytest.raises(ValueError, match="edges"):
        cefast.bin_counts(np.sort(times), np.array([2]), np.array([3.0, 0.0]))


def test_ring_trace_free_diffusion_and_fixed_noise():
    heads, lengths = np.zeros(2000), np.full(2000, 40, np.int64)
    x = cefast.ring_trace(heads, lengths, 40, 0.2, 0.0, 10.0, 0.0, 5.2, 20, 7)
    decay = np.cos(x).mean(0)[[4, 9, 19]]
    assert np.allclose(decay, np.exp(-0.2 * np.array([4.5, 9.5, 19.5])), atol=0.04)
    assert np.array_equal(x, cefast.ring_trace(heads, lengths, 40, 0.2, 0.0, 10.0, 0.0, 5.2, 20, 7))
    short = cefast.ring_trace(heads[:1], np.array([3]), 5, 0.2, 0.0, 10.0, 0.0, 5.2, 20, 7)
    assert np.isnan(short[0, 3:]).all() and np.isfinite(short[0, :3]).all()
