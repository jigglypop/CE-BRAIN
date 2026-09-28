import numpy as np

from research import c3_6_wake_overwrite as c36


def synthetic(tau_w, sessions=8, per=150, seed=0):
    """Triplets whose NREM₂ directions sit near arg(e^{−w/τ_w}e^{iθ₁} + (1 − e^{−w/τ_w})e^{iθ_w}); τ_w = 0 is a full reset."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(sessions):
        found = []
        for _ in range(per):
            wake = np.exp(rng.uniform(np.log(10), np.log(640)))
            slept = rng.uniform(-np.pi, np.pi)
            woke = slept + rng.normal(0, 1.2)
            keep = np.exp(-wake / tau_w) if tau_w else 0.0
            centre = np.angle(keep * np.exp(1j * slept) + (1 - keep) * np.exp(1j * woke))
            theta = np.where(rng.random(60) < 0.4, centre + rng.vonmises(0, 2, 60), rng.uniform(-np.pi, np.pi, 60))
            found.append({"slept": slept, "woke": woke, "wake": wake, "u": np.exp(1j * theta)})
        out.append(found)
    return out


def test_selective_overwrite_is_recovered():
    r = c36.analyse(synthetic(20.0), 743.0, np.random.default_rng(0))
    assert r["survives_p1"] > 0 and c36.BAND[0] <= r["tau_star"] <= c36.BAND[1]
    assert r["tau_star_interval"][1] <= 743 / c36.SELECTIVE
    assert r["shortfall_predicted"] <= c36.SHORTFALL < r["shortfall_single"]


def test_single_time_constant_and_reset_are_told_apart():
    one = c36.analyse(synthetic(743.0), 743.0, np.random.default_rng(0))
    assert one["tau_star"] > 743 / c36.SELECTIVE and one["shortfall_single"] <= c36.SHORTFALL
    reset = c36.analyse(synthetic(0), 743.0, np.random.default_rng(0))
    assert reset["survives_p1"] <= 0 and reset["tau_star"] < c36.BAND[0]
