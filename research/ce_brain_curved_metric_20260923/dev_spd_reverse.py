"""Development: reverse-engineer undocumented details of the published constant-SPD fit."""
import itertools
import json
import numpy as np
from scipy.optimize import lsq_linear, minimize
from kc_data import load_table, cohort, read_selected_predictions, REGIONS, N_POS, PUBLICATION

TYPE = np.array([0, 1, 2, 3, 2, 3])


def sym_fn(a, fn):
    w, v = np.linalg.eigh((a + a.T) / 2)
    return (v * fn(w)) @ v.T


def unweighted_pilot(x, y, n_types=4, nonneg=False):
    rows, rhs = [], []
    for p in range(x.shape[0]):
        for c in range(6):
            a = np.zeros(n_types + 6)
            a[TYPE[c]] = x[p, c]
            a[n_types + c] = 1
            rows.append(a)
            rhs.append(y[p, c])
    if nonneg:
        lb = np.r_[np.zeros(n_types), np.full(6, -np.inf)]
        coef = lsq_linear(np.array(rows), np.array(rhs), bounds=(lb, np.inf), method="bvls", tol=1e-14).x
    else:
        coef = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)[0]
    return coef[TYPE]


def region_pilot(x, y):
    k = np.zeros(6)
    for c in range(6):
        k[c] = np.polyfit(x[:, c], y[:, c], 1)[0]
    return k


def base_fit(X, Y, SX, SY, cfg, weights=None, v_fixed=None):
    phi = X ** cfg["power"]
    n = X.shape[0]
    if v_fixed is not None:
        v = v_fixed
    elif cfg["mode"] == "mean":
        m = phi.mean(axis=0) ** cfg["mode_power"]
        v = m / np.linalg.norm(m)
    else:
        v = np.ones(6) / np.sqrt(6)
    rows, rhs = [], []
    for p in range(n):
        s = phi[p] @ v
        for c in range(6):
            a = np.zeros(11)
            a[TYPE[c]] = phi[p, c]
            a[4] = v[c] * s
            a[5 + c] = 1
            rows.append(a)
            rhs.append(Y[p, c])
    A = np.array(rows)
    r = np.array(rhs)
    if weights is None:
        weights = make_weights(X, Y, SX, SY, cfg, A, r, phi, v)
    sw = np.sqrt(weights)
    A_w = A * sw[:, None]
    r_w = r * sw
    extra_a, extra_r = [], []
    if cfg["offset_penalty"] > 0:
        lam = np.sqrt(cfg["offset_penalty"] * n * cfg.get("pen_scale", 1.0))
        for i, j in ((4, 2), (5, 3)):
            a = np.zeros(11)
            a[5 + i] = lam
            a[5 + j] = -lam
            extra_a.append(a)
            extra_r.append(0.0)
    if cfg["regularization"] > 0:
        a = np.zeros(11)
        ss = float(((phi - phi.mean(axis=0)) ** 2).sum())
        wm = weights.reshape(n, 6)
        wss = float((wm * (phi - (wm * phi).sum(0) / wm.sum(0)) ** 2).sum())
        scale = {"1": 1.0, "n": n, "6n": 6 * n, "ss6": ss / 6, "ss5": ss / 5, "ss": ss,
                 "wss6": wss / 6, "ssn": ss / n}[cfg["reg_scale"]]
        a[4] = np.sqrt(cfg["regularization"] * scale)
        extra_a.append(a)
        extra_r.append(0.0)
    if extra_a:
        A_w = np.vstack([A_w, np.array(extra_a)])
        r_w = np.concatenate([r_w, extra_r])
    lb = np.full(11, -np.inf)
    lb[:4] = cfg["mobility_floor"]
    lb[4] = cfg.get("rho_lb", 0.0)
    bound_mode = cfg.get("bound_mode", "bvls")
    if bound_mode == "bvls":
        th = lsq_linear(A_w, r_w, bounds=(lb, np.full(11, np.inf)), method="bvls", tol=1e-14, lsmr_tol=None).x
    elif bound_mode == "clip":
        th = np.linalg.lstsq(A_w, r_w, rcond=None)[0]
        th = np.maximum(th, lb)
    elif bound_mode == "clip_refit":
        th = np.linalg.lstsq(A_w, r_w, rcond=None)[0]
        fixed = th < lb
        if fixed.any():
            th = np.where(fixed, lb, th)
            free = ~fixed
            th[free] = np.linalg.lstsq(A_w[:, free], r_w - A_w[:, fixed] @ th[fixed], rcond=None)[0]
    elif bound_mode == "eig":
        lb2 = lb.copy()
        lb2[:5] = -np.inf
        th = lsq_linear(A_w, r_w, bounds=(lb2, np.full(11, np.inf)), method="bvls", tol=1e-14, lsmr_tol=None).x
    elif bound_mode.startswith("hyb"):
        th = np.linalg.lstsq(A_w, r_w, rcond=None)[0]
        floor = cfg["mobility_floor"]
        L = np.diag(th[TYPE]) + th[4] * np.outer(v, v)
        trigger = {"hyb_eig": np.linalg.eigvalsh(L).min() < floor, "hyb_diag": np.diag(L).min() < floor,
                   "hyb_d": th[:4].min() < 0}[cfg.get("trigger", "hyb_eig")]
        if trigger:
            rule = bound_mode
            if rule == "hyb_bvls":
                th = lsq_linear(A_w, r_w, bounds=(lb, np.full(11, np.inf)), method="bvls", tol=1e-14).x
            elif rule == "hyb_clipd":
                th = th.copy()
                th[:4] = np.maximum(th[:4], floor)
            elif rule == "hyb_diagc":
                cons = []
                for c in range(6):
                    g = np.zeros(11)
                    g[TYPE[c]] = 1
                    g[4] = v[c] ** 2
                    cons.append({"type": "ineq", "fun": lambda z, g=g: g @ z - floor, "jac": lambda z, g=g: g})
                f = lambda z: 0.5 * np.sum((A_w @ z - r_w) ** 2)
                jac = lambda z: A_w.T @ (A_w @ z - r_w)
                th = minimize(f, th, jac=jac, constraints=cons, method="SLSQP",
                              options={"ftol": 1e-16, "maxiter": 1000}).x
            elif rule == "hyb_eigc":
                def mineig(z):
                    return np.linalg.eigvalsh(np.diag(z[TYPE]) + z[4] * np.outer(v, v)).min() - floor
                f = lambda z: 0.5 * np.sum((A_w @ z - r_w) ** 2)
                jac = lambda z: A_w.T @ (A_w @ z - r_w)
                th = minimize(f, th, jac=jac, constraints=[{"type": "ineq", "fun": mineig}], method="SLSQP",
                              options={"ftol": 1e-16, "maxiter": 1000}).x
            elif rule == "hyb_eigp":
                L = sym_fn(L, lambda w: np.maximum(w, floor))
                b = th[5:]
                Li = np.linalg.inv(L)
                G = np.block([[Li, -(Li @ b)[:, None]], [-(Li @ b)[None, :], np.array([[1 + b @ Li @ b]])]])
                return G, th, v
            else:
                raise ValueError(rule)
    else:
        raise ValueError(bound_mode)
    if bound_mode == "eig":
        L = np.diag(th[TYPE]) + th[4] * np.outer(v, v)
        L = sym_fn(L, lambda w: np.maximum(w, cfg["mobility_floor"]))
        b = th[5:]
        Li = np.linalg.inv(L)
        G = np.block([[Li, -(Li @ b)[:, None]], [-(Li @ b)[None, :], np.array([[1 + b @ Li @ b]])]])
        return G, th, v
    L = np.diag(th[TYPE]) + th[4] * np.outer(v, v)
    b = th[5:]
    Li = np.linalg.inv(L)
    G = np.block([[Li, -(Li @ b)[:, None]], [-(Li @ b)[None, :], np.array([[1 + b @ Li @ b]])]])
    return G, th, v


def make_weights(X, Y, SX, SY, cfg, A, r, phi, v):
    p = cfg["precision_power"]
    if p == 0:
        return np.ones(A.shape[0])
    kind = cfg["pilot"]
    if kind == "ols_x":
        k0 = unweighted_pilot(X, Y)
        var = SY ** 2 + (k0 ** 2)[None, :] * SX ** 2
    elif kind == "ols_phi":
        k0 = unweighted_pilot(phi, Y, nonneg=cfg.get("pilot_nonneg", False))
        sphi = cfg["power"] * X ** (cfg["power"] - 1) * SX
        var = SY ** 2 + (k0 ** 2)[None, :] * sphi ** 2
    elif kind == "ols_phi_region":
        k0 = region_pilot(phi, Y)
        sphi = cfg["power"] * X ** (cfg["power"] - 1) * SX
        var = SY ** 2 + (k0 ** 2)[None, :] * sphi ** 2
    elif kind == "y_only":
        var = SY ** 2
    elif kind in ("spd_diag", "spd_full"):
        pilot_cfg = dict(cfg, precision_power=0)
        _, th, vv = base_fit(X, Y, SX, SY, pilot_cfg, weights=np.ones(A.shape[0]))
        L = np.diag(th[TYPE]) + th[4] * np.outer(vv, vv)
        sphi = cfg["power"] * X ** (cfg["power"] - 1) * SX
        if kind == "spd_diag":
            var = SY ** 2 + (np.diag(L) ** 2)[None, :] * sphi ** 2
        else:
            var = SY ** 2 + (sphi ** 2) @ (L ** 2).T
    else:
        raise ValueError(kind)
    var = var + cfg["variance_floor"] + cfg.get("eps", 0.0)
    norm = cfg["norm"]
    if norm == "se_mean":
        se = np.sqrt(var)
        se = se / se.mean()
        w = se ** (-2 * p)
    elif norm == "w_mean":
        w = var ** (-p)
        w = w / w.mean()
    elif norm == "se_median":
        se = np.sqrt(var)
        se = se / np.median(se)
        w = se ** (-2 * p)
    elif norm == "var_mean":
        vv = var / var.mean()
        w = vv ** (-p)
    else:
        raise ValueError(norm)
    return w.reshape(-1)


def fit(X, Y, SX, SY, cfg):
    G, th, v = base_fit(X, Y, SX, SY, cfg)
    step = cfg["geometric_step"]
    if step == 0:
        return G
    n = X.shape[0]
    Gh = sym_fn(G, np.sqrt)
    Gih = sym_fn(G, lambda w: 1 / np.sqrt(w))
    T = np.zeros_like(G)
    for j in range(n):
        keep = [i for i in range(n) if i != j]
        Gj, _, _ = base_fit(X[keep], Y[keep], SX[keep], SY[keep], cfg,
                            v_fixed=v if cfg.get("loo_v_fixed") else None)
        T += sym_fn(Gih @ Gj @ Gih, np.log)
    T /= n
    return Gh @ sym_fn(T, lambda w: np.exp(-step * w)) @ Gh


def predict(G, x, power):
    return np.linalg.solve(G[:6, :6], x ** power - G[:6, 6])


def leave1(means, cfg):
    pred = np.zeros((N_POS, 6))
    for h in range(N_POS):
        tr = [p for p in range(N_POS) if p != h]
        G = fit(means["x"][tr], means["y"][tr], means["sem_x"][tr], means["sem_y"][tr], cfg)
        pred[h] = predict(G, means["x"][h], cfg["power"])
    return pred


CANDIDATE = {"mode": "mean", "mode_power": 0.5, "precision_power": 2.5, "variance_floor": 0.0,
             "offset_penalty": 0.06, "geometric_step": 0.2, "regularization": 3.0, "power": 0.625,
             "mobility_floor": 0.025}
PREVIOUS = {"mode": "uniform", "mode_power": 0.5, "precision_power": 2.0, "variance_floor": 0.0,
            "offset_penalty": 0.0, "geometric_step": 0.1, "regularization": 1.0, "power": 0.75,
            "mobility_floor": 0.025}

if __name__ == "__main__":
    t = load_table()
    full = cohort(t)
    rows = read_selected_predictions()
    saved = {k: np.zeros((N_POS, 6)) for k in ("previous", "candidate")}
    for row in rows:
        for k in saved:
            saved[k][int(row["position"]) - 1, REGIONS.index(row["region"])] = float(row[k])
    Gsaved = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])
    results = []
    for pilot, norm, reg_scale, pen_scale in itertools.product(
            ["ols_x", "ols_phi", "spd_diag", "spd_full"], ["w_mean", "se_mean", "var_mean", "se_median"],
            ["1", "n", "6n"], [1.0]):
        extra = {"pilot": pilot, "norm": norm, "reg_scale": reg_scale, "pen_scale": pen_scale}
        cfg = dict(CANDIDATE, **extra)
        Gfull = fit(full["x"], full["y"], full["sem_x"], full["sem_y"], cfg)
        gerr = float(np.abs(Gfull - Gsaved).max())
        pc = leave1(full, cfg)
        pp = leave1(full, dict(PREVIOUS, **extra))
        ec = float(np.abs(pc - saved["candidate"]).max())
        ep = float(np.abs(pp - saved["previous"]).max())
        rm = float(np.sqrt(np.mean((pc - full["y"]) ** 2)))
        results.append((gerr, ec, ep, rm, extra))
        print(f"{pilot:9s} {norm:9s} {reg_scale:3s} G {gerr:.2e} cand {ec:.2e} prev {ep:.2e} rmse {rm:.8f}", flush=True)
