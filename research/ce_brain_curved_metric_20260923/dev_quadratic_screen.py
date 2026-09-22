"""Development (primary panel only): does any leading-order quadratic term of a state-dependent metric help?"""
import numpy as np
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
cfg = M.PUBLISHED
SISTER = np.array([0, 1, 4, 5, 2, 3])


def features(phi, name, v):
    s = phi @ v
    if name == "phi_s":
        return phi * s[:, None]
    if name == "phi2":
        return phi ** 2
    if name == "s2":
        return np.repeat((s ** 2)[:, None], 6, axis=1)
    if name == "sister":
        return phi * phi[:, SISTER]
    if name == "calyx":
        return phi * phi[:, [0]]
    if name == "gamma":
        return phi * phi[:, [1]]
    if name == "v_s2":
        return v[None, :] * (s ** 2)[:, None]
    raise ValueError(name)


def fit_extra(train, name, per_type):
    phi = train["x"] ** cfg["power"]
    n = phi.shape[0]
    v = M.coupling_direction(phi, cfg)
    s = phi @ v
    q = features(phi, name, v)
    k = 4 if per_type else 1
    a = np.zeros((6 * n, 11 + k))
    for p in range(n):
        for c in range(6):
            a[6 * p + c, M.TYPE[c]] = phi[p, c]
            a[6 * p + c, 4] = v[c] * s[p]
            a[6 * p + c, 5 + c] = 1.0
            a[6 * p + c, 11 + (M.TYPE[c] if per_type else 0)] = q[p, c]
    sw = np.sqrt(M.precision_weights(train, phi, cfg))
    extra = M.penalty_rows(n, 11 + k, phi, cfg, 4, 5)
    aw = np.vstack([a * sw[:, None], np.array(extra)])
    rw = np.r_[train["y"].reshape(-1) * sw, np.zeros(len(extra))]
    th = np.linalg.lstsq(aw, rw, rcond=None)[0]
    return th, v


def predict_extra(th, v, x, name, per_type):
    phi = np.atleast_2d(x) ** cfg["power"]
    s = phi @ v
    q = features(phi, name, v)
    L = np.diag(th[M.TYPE]) + th[4] * np.outer(v, v)
    coef = th[11 + M.TYPE] if per_type else th[11]
    return phi @ L.T + th[5:11] + coef * q


base = []
for task in tasks:
    th, v = fit_extra(task["train"], "phi2", False)
    base.append(task["test_y"])
ys = np.concatenate(base)
g_preds = np.concatenate([M.predict_constant_spd(M.fit_constant_spd(task["train"], dict(cfg, geometric_step=0)),
                                                 task["test_x"], cfg["power"]) for task in tasks])
print("no-correction constant SPD leave1 rmse", np.sqrt(np.mean((g_preds - ys) ** 2)))
for name in ("phi_s", "phi2", "s2", "sister", "calyx", "gamma", "v_s2"):
    for per_type in (False, True):
        p = np.concatenate([predict_extra(*fit_extra(task["train"], name, per_type), task["test_x"], name, per_type)
                            for task in tasks])
        e = p - ys
        per_region = np.sqrt(np.mean(e ** 2, axis=0))
        print(f"{name:7s} per_type={per_type!s:5s} rmse {np.sqrt(np.mean(e ** 2)):.6f} mae {np.mean(np.abs(e)):.6f} "
              f"regions {np.round(per_region, 4)}", flush=True)
