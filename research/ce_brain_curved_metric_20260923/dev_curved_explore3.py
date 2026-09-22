"""Development (primary panel only): region-selective divisive metric on Bergmann-significant regions."""
import numpy as np
from scipy.optimize import brentq
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
cfg = M.PUBLISHED
MASK = np.array([1.0, 1.0, 0.0, 1.0, 0.0, 1.0])


def make_force(beta):
    def force(data, phi):
        u = M.coupling_direction(phi, cfg)
        s = data["y"] @ u
        return phi / (1 + beta * MASK[None, :] * (s / s.mean() - 1)[:, None])
    return force


def predict(metric, train, x, beta):
    phi_tr = train["x"] ** cfg["power"]
    u = M.coupling_direction(phi_tr, cfg)
    s0 = (train["y"] @ u).mean()
    L = np.linalg.inv(metric[:6, :6])
    b = -L @ metric[:6, 6]
    out = []
    for xi in np.atleast_2d(x):
        phi = xi ** cfg["power"]
        if beta == 0:
            out.append(b + L @ phi)
            continue
        f = lambda s: u @ b + u @ L @ (phi / (1 + beta * MASK * (s / s0 - 1))) - s
        lo = s0 * (1 - 0.95 / beta) if beta > 0 else 1e-9
        hi = s0 * 10 if beta > 0 else s0 * (1 - 0.95 / beta)
        grid = np.linspace(max(lo, 1e-9), hi, 4001)
        vals = np.array([f(g) for g in grid])
        idx = np.where(np.sign(vals[:-1]) != np.sign(vals[1:]))[0]
        if not len(idx):
            out.append(np.full(6, np.nan))
            continue
        s_lin = u @ b + u @ L @ phi
        k = idx[np.argmin(np.abs(grid[idx] - s_lin))]
        s = brentq(f, grid[k], grid[k + 1], xtol=1e-15)
        out.append(b + L @ (phi / (1 + beta * MASK * (s / s0 - 1))))
    return np.array(out)


ys = np.concatenate([task["test_y"] for task in tasks])
for beta in (-0.3, -0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2, 0.3):
    p = np.concatenate([predict(M.fit_constant_spd(task["train"], cfg, None if beta == 0 else make_force(beta)),
                                task["train"], task["test_x"], beta) for task in tasks])
    e = p - ys
    print(beta, f"rmse {np.sqrt(np.mean(e ** 2)):.8f} mae {np.mean(np.abs(e)):.8f}",
          np.round(np.sqrt(np.mean(e ** 2, axis=0)), 5), flush=True)
