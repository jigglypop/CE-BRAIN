import numpy as np

from research import c4_4_ring_diffusion as c4
from research.store import Session


def population(kind, seconds=3000.0, cells=24, msd=1.0, dt=0.005, seed=0):
    """HD cells (von Mises tuning, 60° wide) around a packet that diffuses with MSD slope `msd` or is
    carried by a slowly varying velocity (ballistic sweeps)."""
    rng = np.random.default_rng(seed)
    n = int(seconds / dt)
    if kind == "diffusion":
        theta = np.cumsum(rng.normal(0, np.sqrt(msd * dt), n))
    else:
        v = np.zeros(n)
        for i in range(1, n):
            v[i] = v[i - 1] * (1 - dt / 0.5) + rng.normal(0, 1.5 * np.sqrt(2 * dt / 0.5))
        theta = np.cumsum(v * dt)
    phi = np.sort(rng.uniform(0, 2 * np.pi, cells))
    rate = 0.5 + 20 * np.exp(3 * (np.cos(theta[:, None] - phi[None, :]) - 1))
    counts = rng.poisson(rate * dt)
    t = np.arange(n) * dt
    spikes = [np.sort(np.repeat(t, counts[:, i]) + rng.uniform(0, dt, counts[:, i].sum())) for i in range(cells)]
    s = Session({"spikes": np.concatenate(spikes), "ends": np.cumsum([len(x) for x in spikes])})
    return s, phi, (np.array([0.0]), np.array([seconds]))


def sessions(kind, count=4):
    return [{"rem": c4.pair_sums(s, phi, *spans)} for s, phi, spans in (population(kind, seed=i) for i in range(count))]


def test_diffusion_is_recovered_with_its_msd_slope():
    a = c4.analyse(sessions("diffusion"), "rem", np.random.default_rng(0), boot=200)
    f = a["fits"]
    assert 0.7 < f["diffusion"]["params"][2] < 1.4
    assert f["diffusion"]["chi2_dof"] <= c4.CHI2 < f["sweep"]["chi2_dof"]


def test_velocity_driven_sweeps_are_not_called_diffusion():
    f = c4.analyse(sessions("sweep"), "rem", np.random.default_rng(0), boot=200)["fits"]
    assert f["sweep"]["chi2_dof"] < f["diffusion"]["chi2_dof"]
