"""Development on the primary leave-one-odor panel only: fixed-beta scans of candidate curved families."""
import numpy as np
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
cfg = M.PUBLISHED


def direction(kind, phi):
    if kind == "uniform":
        return np.ones(6) / 6
    m = np.sqrt(phi.mean(axis=0))
    return m / np.linalg.norm(m)


def make_force(family, beta, ukind):
    def force(data, phi):
        u = direction(ukind, phi)
        s = data["y"] @ u
        s0 = s.mean()
        if family == "A":
            return phi / (1 + beta * (s / s0 - 1))[:, None]
        return phi - (beta / (2 * s0)) * (s ** 2)[:, None] * u[None, :]
    return force


def predict(family, beta, ukind, metric, train, x):
    phi_tr = train["x"] ** cfg["power"]
    u = direction(ukind, phi_tr)
    s0 = (train["y"] @ u).mean()
    L = np.linalg.inv(metric[:6, :6])
    b = -L @ metric[:6, 6]
    out = []
    for xi in np.atleast_2d(x):
        phi = xi ** cfg["power"]
        a, c = u @ L @ phi, u @ b
        if beta == 0:
            z = a + c
        elif family == "A":
            qa, qb, qc = beta / s0, (1 - beta) - beta * c / s0, -c * (1 - beta) - a
            roots = np.roots([qa, qb, qc])
            roots = roots[np.isreal(roots)].real
            z = roots[np.argmin(np.abs(roots - (a + c)))]
        else:
            k = beta * (u @ L @ u) / (2 * s0)
            z = (-1 + np.sqrt(1 + 4 * k * (a + c))) / (2 * k)
        if family == "A":
            out.append(b + L @ phi / (1 + beta * (z / s0 - 1)))
        else:
            out.append(b + L @ phi - (beta / (2 * s0)) * z ** 2 * (L @ u))
    return np.array(out)


def run(family, beta, ukind):
    preds, ys = [], []
    for task in tasks:
        force = None if beta == 0 else make_force(family, beta, ukind)
        g = M.fit_constant_spd(task["train"], cfg, force)
        preds.append(predict(family, beta, ukind, g, task["train"], task["test_x"]))
        ys.append(task["test_y"])
    p, y = np.concatenate(preds), np.concatenate(ys)
    return np.sqrt(np.mean((p - y) ** 2)), np.mean(np.abs(p - y))


print("beta=0", run("A", 0.0, "uniform"))
for family in ("A", "B"):
    for ukind in ("uniform", "v"):
        for beta in (-0.6, -0.4, -0.2, -0.1, 0.1, 0.2, 0.4, 0.6, 1.0):
            try:
                r = run(family, beta, ukind)
                print(family, ukind, beta, f"rmse {r[0]:.8f} mae {r[1]:.8f}", flush=True)
            except Exception as exc:
                print(family, ukind, beta, "failed", exc, flush=True)
