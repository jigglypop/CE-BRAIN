import numpy as np
from scipy.signal import lfilter

from research import c1_9_decoding_noise as c19


def synthetic(phi, sessions=8, windows=3000, sigma=1.0, seed=0):
    """Wake windows whose decoding error is a wrapped-normal AR(1) (lag-1 correlation phi) plus a head-dependent bias."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(sessions):
        head = np.cumsum(rng.normal(0, 0.1, windows))
        noise = lfilter([np.sqrt(1 - phi ** 2)], [1, -phi], rng.standard_normal(windows)) * sigma
        error = np.angle(np.exp(1j * (noise + 0.3 * np.sin(head))))
        still = rng.random(windows) < 0.7
        out.append(np.stack([error, head, still, np.repeat(np.arange(windows // 100), 100)], 1))
    return out


def test_phi_is_recovered_through_the_bias_and_the_bootstrap():
    for truth in (0.0, 0.5, 0.85):
        r = c19.analyse(synthetic(truth), np.random.default_rng(1))
        assert abs(r["still"]["phi"][0] - truth) < 0.07
    assert c19.analyse(synthetic(0.3), np.random.default_rng(1))["still"]["phi_p99"][0] < c19.NEEDED
    assert c19.analyse(synthetic(0.9), np.random.default_rng(1))["still"]["phi_p99"][0] >= c19.NEEDED
