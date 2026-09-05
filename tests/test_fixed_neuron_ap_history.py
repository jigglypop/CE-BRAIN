"""Independent mathematical witnesses for the fixed AP-history predictor."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('ap_history_candidate', HERE/'allen_ap_history_prediction.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_recovery_matches_resource_depletion_and_facilitation_sum():
    times = np.array([0., .02, .04, 1.04])
    u, tau = .3, .5
    expected = [1.]
    available_after_release = 1-u
    for dt in np.diff(times):
        recovered = available_after_release+(1-available_after_release)*(1-np.exp(-dt/tau))
        expected.append(recovered)
        available_after_release = recovered*(1-u)
    np.testing.assert_allclose(m.efficacy(times, 'depression', u, tau), expected)
    fac = [1+.7*sum(np.exp(-(t-times[:i])/.1)) for i, t in enumerate(times)]
    np.testing.assert_allclose(m.efficacy(times, 'facilitation', .7, .1), fac)


def test_window_kernel_matches_independent_numerical_integration_with_tail():
    spikes = np.array([0., .02, .04])
    lag, rise, decay = .001, .002, .025
    q = np.array([1., .6, .4])
    peak = np.log(decay/rise)/(1/rise-1/decay)
    norm = np.exp(-peak/decay)-np.exp(-peak/rise)

    def window(center, lo, hi):
        t = center+np.linspace(lo, hi, 10001)
        delta = t[:, None]-spikes[None, :]-lag
        positive = np.maximum(delta, 0)
        signal = ((np.exp(-positive/decay)-np.exp(-positive/rise))/norm) @ q
        return np.trapezoid(signal, t)/(hi-lo)

    expected = [window(t, lo, hi)-window(t, *m.BASELINE) for t in spikes for lo, hi in m.BINS]
    np.testing.assert_allclose(m.kernel_basis(spikes, lag, rise, decay)@q, expected, atol=2e-8)
    # The baseline of pulse2 contains a real tail and cannot be treated as zero.
    assert window(.02, *m.BASELINE) > .5


def test_ap_detector_rejects_passive_step_and_counts_extra_spikes():
    fs = 50000
    v = np.full(1500, -70.)
    v[100:175] = -35.  # Passive jump, no AP threshold/peak.
    ap = np.concatenate([np.linspace(-70, 30, 20), np.linspace(30, -70, 60)])
    v[300:380] = ap
    v[900:980] = ap
    spikes = m.spike_indices(v, fs)
    assert len(spikes) == 2
    np.testing.assert_allclose(spikes, [310, 910], atol=1)
