import numpy as np

from research import c3_1_sleep_trace as c3


def simulate(seed=0, memory=True, events=60, cells=30, diffusion=1 / 30, dt=0.05):
    """HD cells over alternating wake/NREM. In NREM the internal direction starts at the last wake direction
    and diffuses (memory, τ = 2/diffusion) or is redrawn every second (no memory)."""
    rng = np.random.default_rng(seed)
    phi = np.sort(rng.uniform(0, 2 * np.pi, cells))
    theta, gain, states, t, last = [], [], [], 0.0, rng.uniform(0, 2 * np.pi)
    for _ in range(events):
        wake = last + np.cumsum(rng.normal(0, 0.1, int(20 / dt)))
        steps = int(rng.uniform(60, 300) / dt)
        nrem = (wake[-1] + np.cumsum(rng.normal(0, np.sqrt(diffusion * dt), steps)) if memory
                else np.repeat(rng.uniform(0, 2 * np.pi, int(steps * dt) + 1), int(1 / dt))[:steps])
        states += [(t, t + len(wake) * dt, "wake"), (t + len(wake) * dt, t + (len(wake) + steps) * dt, "nrem")]
        theta += [wake, nrem]
        gain += [np.ones(len(wake)), np.full(steps, 0.6)]
        t += (len(wake) + steps) * dt
        last = nrem[-1] if memory else rng.uniform(0, 2 * np.pi)
    theta, gain = np.concatenate(theta), np.concatenate(gain)
    time = np.arange(len(theta)) * dt
    rate = gain[:, None] * (0.5 + 20 * np.exp(3 * (np.cos(theta[:, None] - phi[None, :]) - 1)))
    counts = rng.poisson(rate * dt)
    spikes = [np.repeat(time, counts[:, i]) + rng.uniform(0, dt, counts[:, i].sum()) for i in range(cells)]
    return spikes, states, phi


def test_trace_time_constant_is_recovered():
    r = c3.analyse(c3.Pool([c3.events(*simulate(events=200))]))
    assert r["alignment"][0] > r["first_bin_null_top"]
    assert r["chi2_trace"] <= c3.CHI2 < r["chi2_none"] and 40 < r["tau_s"] < 90


def test_no_memory_is_not_mistaken_for_a_trace():
    r = c3.analyse(c3.Pool([c3.events(*simulate(memory=False))]))
    assert r["alignment"][0] <= r["first_bin_null_top"] or r["chi2_none"] <= c3.CHI2
