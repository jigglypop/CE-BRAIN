"""Development (primary panel only): self-consistent fit of the divisive metric; zero-parameter recruitment metric."""
import numpy as np
from scipy.optimize import least_squares
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
cfg = M.PUBLISHED


def v_dir(phi):
    return M.coupling_direction(phi, cfg)


def solve_divisive(L, b, phi, u, s0, beta):
    a, c = u @ L @ phi, u @ b
    if beta == 0:
        return b + L @ phi
    roots = np.roots([beta / s0, (1 - beta) - beta * c / s0, -c * (1 - beta) - a])
    roots = roots[np.abs(roots.imag) < 1e-12].real
    roots = roots[1 + beta * (roots / s0 - 1) > 0.05]
    z = roots[np.argmin(np.abs(roots - (a + c)))]
    return b + L @ phi / (1 + beta * (z / s0 - 1))


def fit_divisive_sc(train, beta):
    phi = train["x"] ** cfg["power"]
    n = phi.shape[0]
    v = v_dir(phi)
    s0 = (train["y"] @ v).mean()
    sw = np.sqrt(M.precision_weights(train, phi, cfg))
    g0, th0, _ = M.base_fit(train, cfg)
    pen = np.array(M.penalty_rows(n, 11, phi, cfg, 4, 5))

    def resid(th):
        L = np.diag(th[M.TYPE]) + th[4] * np.outer(v, v)
        pred = np.array([solve_divisive(L, th[5:], phi[p], v, s0, beta) for p in range(n)])
        return np.r_[(pred - train["y"]).reshape(-1) * sw, pen @ th]

    th = least_squares(resid, th0, xtol=1e-14, ftol=1e-14, gtol=1e-14).x
    return th, v, s0


def run_divisive_sc(beta):
    preds, ys = [], []
    for task in tasks:
        th, v, s0 = fit_divisive_sc(task["train"], beta)
        L = np.diag(th[M.TYPE]) + th[4] * np.outer(v, v)
        preds.append(np.array([solve_divisive(L, th[5:], xi ** cfg["power"], v, s0, beta) for xi in task["test_x"]]))
        ys.append(task["test_y"])
    e = np.concatenate(preds) - np.concatenate(ys)
    return np.sqrt(np.mean(e ** 2)), np.mean(np.abs(e))


def recruit_force(data, phi):
    return phi


def fit_recruit(train):
    """L(y) = diag(d) + rho (s(y)/s0) v v^T; structural fit scales the rho column by observed s/s0."""
    phi = train["x"] ** cfg["power"]
    n = phi.shape[0]
    v = v_dir(phi)
    s_obs = train["y"] @ v
    s0 = s_obs.mean()
    a = np.zeros((6 * n, 11))
    for p in range(n):
        for c in range(6):
            a[6 * p + c, M.TYPE[c]] = phi[p, c]
            a[6 * p + c, 4] = v[c] * (phi[p] @ v) * s_obs[p] / s0
            a[6 * p + c, 5 + c] = 1.0
    sw = np.sqrt(M.precision_weights(train, phi, cfg))
    pen = M.penalty_rows(n, 11, phi, cfg, 4, 5)
    th = np.linalg.lstsq(np.vstack([a * sw[:, None], np.array(pen)]),
                         np.r_[train["y"].reshape(-1) * sw, np.zeros(len(pen))], rcond=None)[0]
    return th, v, s0


def predict_recruit(th, v, s0, x):
    out = []
    for xi in np.atleast_2d(x):
        phi = xi ** cfg["power"]
        d = th[M.TYPE]
        base = th[5:] + d * phi
        k = th[4] * (v @ phi) / s0
        s = (v @ base) / (1 - k * (v @ v))
        out.append(base + k * s * v)
    return np.array(out)


ys = np.concatenate([task["test_y"] for task in tasks])
p = np.concatenate([predict_recruit(*fit_recruit(task["train"]), task["test_x"]) for task in tasks])
print("recruitment metric (0 extra params, no SPD step) rmse", np.sqrt(np.mean((p - ys) ** 2)),
      "mae", np.mean(np.abs(p - ys)))
p0 = np.concatenate([M.predict_constant_spd(M.fit_constant_spd(task["train"], dict(cfg, geometric_step=0)),
                                            task["test_x"], cfg["power"]) for task in tasks])
print("constant metric, no SPD step, rmse", np.sqrt(np.mean((p0 - ys) ** 2)))
for beta in (-0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2):
    r = run_divisive_sc(beta)
    print("divisive self-consistent fit (no SPD step)", beta, f"rmse {r[0]:.8f} mae {r[1]:.8f}", flush=True)
