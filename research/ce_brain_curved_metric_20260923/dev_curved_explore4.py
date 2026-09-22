"""Development (primary panel only): dendritic (calyx) vs axonal (lobes) divisive metric, fixed-beta grid."""
import numpy as np
from scipy.optimize import brentq
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
cfg = M.PUBLISHED
CALYX = np.array([1.0, 0, 0, 0, 0, 0])
LOBES = 1 - CALYX


def omega2(bc, bl, rel):
    return 1 + (bc * CALYX + bl * LOBES) * rel


def make_force(bc, bl):
    def force(data, phi):
        u = M.coupling_direction(phi, cfg)
        s = data["y"] @ u
        return phi / omega2(bc, bl, (s / s.mean() - 1)[:, None])
    return force


def predict(metric, train, x, bc, bl):
    u = M.coupling_direction(train["x"] ** cfg["power"], cfg)
    s0 = (train["y"] @ u).mean()
    L = np.linalg.inv(metric[:6, :6])
    b = -L @ metric[:6, 6]
    out = []
    for xi in np.atleast_2d(x):
        phi = xi ** cfg["power"]
        f = lambda s: u @ b + u @ L @ (phi / omega2(bc, bl, s / s0 - 1)) - s
        bmax = max(abs(bc), abs(bl), 1e-9)
        grid = np.linspace(s0 * max(1 - 0.95 / bmax, 1e-6), s0 * (1 + 0.95 / bmax), 4001)
        vals = np.array([f(g) for g in grid])
        idx = np.where(np.sign(vals[:-1]) != np.sign(vals[1:]))[0]
        s_lin = u @ b + u @ L @ phi
        if not len(idx):
            out.append(np.full(6, np.nan))
            continue
        k = idx[np.argmin(np.abs(grid[idx] - s_lin))]
        s = brentq(f, grid[k], grid[k + 1], xtol=1e-15)
        out.append(b + L @ (phi / omega2(bc, bl, s / s0 - 1)))
    return np.array(out)


ys = np.concatenate([task["test_y"] for task in tasks])
for bc in (-0.4, -0.3, -0.2, -0.1, 0.0):
    for bl in (-0.05, 0.0, 0.05, 0.1, 0.2):
        if bc == 0 and bl == 0:
            p = np.concatenate([M.predict_constant_spd(M.fit_constant_spd(task["train"], cfg), task["test_x"],
                                                       cfg["power"]) for task in tasks])
        else:
            p = np.concatenate([predict(M.fit_constant_spd(task["train"], cfg, make_force(bc, bl)), task["train"],
                                        task["test_x"], bc, bl) for task in tasks])
        e = p - ys
        print(f"bc {bc:+.2f} bl {bl:+.2f} rmse {np.sqrt(np.mean(e ** 2)):.8f} mae {np.mean(np.abs(e)):.8f}",
              np.round(np.sqrt(np.mean(e ** 2, axis=0)), 5), flush=True)
