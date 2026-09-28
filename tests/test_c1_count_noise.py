import numpy as np

from research import c1_11_count_noise as c111


def test_count_proportional_noise_constant_is_recovered():
    rng = np.random.default_rng(0)
    truth, sessions = 0.05, []
    for _ in range(6):
        events = []
        for _ in range(30):
            k = 200
            state = rng.uniform(-np.pi, np.pi) + np.cumsum(rng.normal(0, 0.05, k))
            na, nb = rng.poisson(rng.uniform(5, 60, k)), rng.poisson(rng.uniform(5, 60, k))
            a = state + rng.vonmises(0, truth * na + 1e-9)
            b = state + rng.vonmises(0, truth * nb + 1e-9)
            events.append(np.stack([state, a, b, na, nb], 1))
        sessions.append(events)
    c, check = c111.calibrate(sessions)
    assert abs(np.log(c / truth)) < 0.15 and all(abs(o - f) < 0.03 for o, f in check)
