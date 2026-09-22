"""Constant-SPD published predictor (reimplemented) and the affine comparators."""
from __future__ import annotations
import numpy as np
from scipy.optimize import brentq, minimize

TYPE = np.array([0, 1, 2, 3, 2, 3])
PAIRS = ((4, 2), (5, 3))
PUBLISHED = {"mode": "mean", "mode_power": 0.5, "precision_power": 2.5, "variance_floor": 0.0,
             "offset_penalty": 0.06, "geometric_step": 0.2, "regularization": 3.0, "power": 0.625,
             "mobility_floor": 0.025}
PREVIOUS = {"mode": "uniform", "mode_power": 0.5, "precision_power": 2.0, "variance_floor": 0.0,
            "offset_penalty": 0.0, "geometric_step": 0.1, "regularization": 1.0, "power": 0.75,
            "mobility_floor": 0.025}


def sym_fn(a: np.ndarray, fn) -> np.ndarray:
    w, v = np.linalg.eigh((a + a.T) / 2)
    return (v * fn(w)) @ v.T


def metric_from(L: np.ndarray, b: np.ndarray) -> np.ndarray:
    Li = np.linalg.inv(L)
    lb = Li @ b
    return np.block([[Li, -lb[:, None]], [-lb[None, :], np.array([[1.0 + b @ lb]])]])


def coupling_direction(phi: np.ndarray, cfg: dict) -> np.ndarray:
    if cfg["mode"] == "mean":
        m = phi.mean(axis=0) ** cfg["mode_power"]
        return m / np.linalg.norm(m)
    return np.ones(phi.shape[1]) / np.sqrt(phi.shape[1])


def pilot_slopes(phi: np.ndarray, y: np.ndarray) -> np.ndarray:
    n = phi.shape[0]
    a = np.zeros((6 * n, 10))
    for p in range(n):
        for c in range(6):
            a[6 * p + c, TYPE[c]] = phi[p, c]
            a[6 * p + c, 4 + c] = 1.0
    return np.linalg.lstsq(a, y.reshape(-1), rcond=None)[0][TYPE]


def precision_weights(data: dict, phi: np.ndarray, cfg: dict) -> np.ndarray:
    p = cfg["precision_power"]
    if p == 0:
        return np.ones(phi.size)
    k0 = pilot_slopes(phi, data["y"])
    s_phi = cfg["power"] * data["x"] ** (cfg["power"] - 1) * data["sem_x"]
    var = data["sem_y"] ** 2 + k0[None, :] ** 2 * s_phi ** 2 + cfg["variance_floor"]
    se = np.sqrt(var).reshape(-1)
    return (se / np.median(se)) ** (-2 * p)


def penalty_rows(n: int, n_par: int, phi: np.ndarray, cfg: dict, rho_index: int, b_index: int):
    rows = []
    if cfg["offset_penalty"] > 0:
        lam = np.sqrt(cfg["offset_penalty"] * n)
        for i, j in PAIRS:
            r = np.zeros(n_par)
            r[b_index + i], r[b_index + j] = lam, -lam
            rows.append(r)
    if cfg["regularization"] > 0:
        r = np.zeros(n_par)
        ss = float(((phi - phi.mean(axis=0)) ** 2).sum()) / 6
        r[rho_index] = np.sqrt(cfg["regularization"] * ss)
        rows.append(r)
    return rows


def eig_constrained_lstsq(a: np.ndarray, r: np.ndarray, theta: np.ndarray, mobility, floor: float) -> np.ndarray:
    """min ||a th - r||^2 s.t. lambda_min(L(th)) >= floor; L affine in th so the feasible set is convex."""
    if np.linalg.eigvalsh(mobility(theta))[0] >= floor:
        return theta

    def grad_min(th):
        w, u = np.linalg.eigh(mobility(th))
        return w[0], np.array([u[:, 0] @ basis @ u[:, 0] for basis in mobility.basis])

    res = minimize(lambda th: 0.5 * np.sum((a @ th - r) ** 2), theta, jac=lambda th: a.T @ (a @ th - r),
                   constraints=[{"type": "ineq", "fun": lambda th: grad_min(th)[0] - floor,
                                 "jac": lambda th: grad_min(th)[1]}],
                   method="SLSQP", options={"ftol": 1e-15, "maxiter": 500})
    ata, atr = a.T @ a, a.T @ r
    polished = res.x.copy()
    for _ in range(50):
        w0, grad = grad_min(polished)
        k = np.block([[ata, grad[:, None]], [grad[None, :], np.zeros((1, 1))]])
        new = np.linalg.solve(k, np.r_[atr, floor - w0 + grad @ polished])[:-1]
        done = np.max(np.abs(new - polished)) < 1e-15
        polished = new
        if done:
            break
    for candidate in (polished, res.x):
        if np.linalg.eigvalsh(mobility(candidate))[0] >= floor - 1e-10:
            return candidate
    raise RuntimeError("SPD-constrained mobility fit failed")


class Mobility:
    """L(th) = diag(d_type) + rho v v^T as an affine map of the parameter vector."""

    def __init__(self, v: np.ndarray, n_par: int):
        self.basis = []
        for s in range(4):
            self.basis.append(np.diag((TYPE == s).astype(float)))
        self.basis.append(np.outer(v, v))
        self.basis += [np.zeros((6, 6))] * (n_par - 5)

    def __call__(self, theta: np.ndarray) -> np.ndarray:
        return sum(t * b for t, b in zip(theta[:5], self.basis[:5]))


def base_fit(data: dict, cfg: dict, force=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Weighted, penalized fit of y = L f + b; f = phi(x) unless a structural force map is supplied."""
    phi = data["x"] ** cfg["power"]
    n = phi.shape[0]
    v = coupling_direction(phi, cfg)
    f = phi if force is None else force(data, phi)
    s = f @ v
    a = np.zeros((6 * n, 11))
    for p in range(n):
        for c in range(6):
            a[6 * p + c, TYPE[c]] = f[p, c]
            a[6 * p + c, 4] = v[c] * s[p]
            a[6 * p + c, 5 + c] = 1.0
    sw = np.sqrt(precision_weights(data, phi, cfg))
    extra = penalty_rows(n, 11, phi, cfg, 4, 5)
    aw = np.vstack([a * sw[:, None]] + ([np.array(extra)] if extra else []))
    rw = np.r_[data["y"].reshape(-1) * sw, np.zeros(len(extra))]
    theta = np.linalg.lstsq(aw, rw, rcond=None)[0]
    mob = Mobility(v, 11)
    theta = eig_constrained_lstsq(aw, rw, theta, mob, cfg["mobility_floor"])
    return metric_from(mob(theta), theta[5:]), theta, v


def spd_correct(metric: np.ndarray, loo_metrics: list[np.ndarray], step: float) -> np.ndarray:
    if step == 0:
        return metric
    gh = sym_fn(metric, np.sqrt)
    gih = sym_fn(metric, lambda w: 1 / np.sqrt(w))
    t = sum(sym_fn(gih @ g @ gih, np.log) for g in loo_metrics) / len(loo_metrics)
    return gh @ sym_fn(t, lambda w: np.exp(-step * w)) @ gh


def subset(data: dict, keep) -> dict:
    return {k: data[k][list(keep)] for k in ("x", "y", "sem_x", "sem_y")}


def fit_constant_spd(data: dict, cfg: dict = PUBLISHED, force=None) -> np.ndarray:
    metric, _, _ = base_fit(data, cfg, force)
    n = data["x"].shape[0]
    loo = [base_fit(subset(data, [i for i in range(n) if i != j]), cfg, force)[0] for j in range(n)] \
        if cfg["geometric_step"] else []
    return spd_correct(metric, loo, cfg["geometric_step"])


def predict_constant_spd(metric: np.ndarray, x: np.ndarray, power: float) -> np.ndarray:
    return np.linalg.solve(metric[:6, :6], (x ** power - metric[:6, 6]).T).T


def readout(metric: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    L = np.linalg.inv(metric[:6, :6])
    return L, -L @ metric[:6, 6]


class PublishedSPD:
    name = "published_constant_spd"

    def fit(self, data: dict) -> dict:
        return {"metric": fit_constant_spd(data, PUBLISHED)}

    def predict(self, fitted: dict, x: np.ndarray) -> np.ndarray:
        return predict_constant_spd(fitted["metric"], np.atleast_2d(x), PUBLISHED["power"])


class Affine:
    """Independent per-region OLS y = k z + c, z = x or x^0.625 (12 coefficients)."""

    def __init__(self, transform: str):
        self.transform = transform

    def _z(self, x):
        return x if self.transform == "x" else x ** PUBLISHED["power"]

    def fit(self, data: dict) -> dict:
        z = self._z(data["x"])
        coef = np.array([np.polyfit(z[:, j], data["y"][:, j], 1) for j in range(6)])
        return {"k": coef[:, 0], "c": coef[:, 1]}

    def predict(self, fitted: dict, x: np.ndarray) -> np.ndarray:
        return fitted["k"] * self._z(np.atleast_2d(x)) + fitted["c"]


CALYX = np.array([1.0, 0, 0, 0, 0, 0])
LOBES = 1.0 - CALYX
OMEGA2_FLOOR = 0.05


def compartment_betas(beta_calyx: float, beta_lobes: float) -> np.ndarray:
    return beta_calyx * CALYX + beta_lobes * LOBES


def omega(betas: np.ndarray, rel) -> np.ndarray:
    """Omega_c = sqrt(1 + beta_c (s/s0 - 1)); rel may be a scalar or a vector of states."""
    w2 = 1.0 + betas * np.asarray(rel, dtype=float)[..., None]
    if np.any(w2 <= OMEGA2_FLOOR):
        raise RuntimeError("compartment factor outside admissible range")
    return np.sqrt(w2)


def fit_compartment_metric(data: dict, om: np.ndarray, cfg: dict = PUBLISHED, rescale=None) -> np.ndarray:
    """Fit G0 from S y = b + L S^-1 phi with S = diag(om) per condition; rescale recomputes om on subsets."""
    n = data["x"].shape[0]

    def one(d, o):
        return base_fit(dict(d, y=d["y"] * o, sem_y=d["sem_y"] * o), cfg, lambda _d, phi: phi / o)[0]
    metric = one(data, om)
    loo = []
    if cfg["geometric_step"]:
        for j in range(n):
            keep = [i for i in range(n) if i != j]
            sub = subset(data, keep)
            loo.append(one(sub, rescale(sub) if rescale else om[keep]))
    return spd_correct(metric, loo, cfg["geometric_step"])


class CurvedAPL:
    """G(y) = S(y) G0 S(y), S = diag(Omega(s(y)), 1), s = v.y; prediction: G_yy(y) y + G_yr(y) = phi(x) at y = y_hat."""

    def __init__(self, beta_calyx: float, beta_lobes: float, cfg: dict = PUBLISHED):
        self.betas, self.cfg = compartment_betas(beta_calyx, beta_lobes), cfg

    def _om_obs(self, data: dict) -> np.ndarray:
        u = coupling_direction(data["x"] ** self.cfg["power"], self.cfg)
        s = data["y"] @ u
        return omega(self.betas, s / s.mean() - 1)

    def fit(self, data: dict) -> dict:
        u = coupling_direction(data["x"] ** self.cfg["power"], self.cfg)
        metric = fit_compartment_metric(data, self._om_obs(data), self.cfg, self._om_obs)
        L, b = readout(metric)
        return {"metric": metric, "L": L, "b": b, "u": u, "s0": float((data["y"] @ u).mean())}

    def state_map(self, fitted: dict, phi: np.ndarray, s: float) -> np.ndarray:
        om = omega(self.betas, s / fitted["s0"] - 1)
        return (fitted["b"] + fitted["L"] @ (phi / om)) / om

    def solve_state(self, fitted: dict, phi: np.ndarray) -> float:
        s0, u = fitted["s0"], fitted["u"]
        s_ref = float(u @ self.state_map(fitted, phi, s0))
        if not np.any(self.betas):
            return s_ref
        lo, hi = -0.999, 20.0
        for beta in (self.betas.min(), self.betas.max()):
            if beta > 0:
                lo = max(lo, (OMEGA2_FLOOR - 1) / beta * 0.999)
            elif beta < 0:
                hi = min(hi, (OMEGA2_FLOOR - 1) / beta * 0.999)
        grid = s0 * (1 + np.linspace(lo, hi, 400))
        vals = np.array([u @ self.state_map(fitted, phi, g) - g for g in grid])
        idx = np.where(np.sign(vals[:-1]) != np.sign(vals[1:]))[0]
        if not len(idx):
            raise RuntimeError("no self-consistent state")
        k = idx[np.argmin(np.abs(grid[idx] - s_ref))]
        return brentq(lambda g: u @ self.state_map(fitted, phi, g) - g, grid[k], grid[k + 1], xtol=1e-14)

    def predict(self, fitted: dict, x: np.ndarray, frozen: bool = False) -> np.ndarray:
        out = []
        for xi in np.atleast_2d(x):
            phi = xi ** self.cfg["power"]
            s = fitted["s0"] if frozen else self.solve_state(fitted, phi)
            out.append(self.state_map(fitted, phi, s))
        return np.array(out)


class InputMetric:
    """Flat counterpart: same S G0 S form but S = S(x) from the control state; constant metric for each input."""

    def __init__(self, beta_calyx: float, beta_lobes: float, cfg: dict = PUBLISHED):
        self.betas, self.cfg = compartment_betas(beta_calyx, beta_lobes), cfg

    def _om(self, x: np.ndarray, u: np.ndarray, s0: float) -> np.ndarray:
        return omega(self.betas, (x ** self.cfg["power"]) @ u / s0 - 1)

    def _om_data(self, data: dict) -> np.ndarray:
        phi = data["x"] ** self.cfg["power"]
        u = coupling_direction(phi, self.cfg)
        s = phi @ u
        return omega(self.betas, s / s.mean() - 1)

    def fit(self, data: dict) -> dict:
        phi = data["x"] ** self.cfg["power"]
        u = coupling_direction(phi, self.cfg)
        metric = fit_compartment_metric(data, self._om_data(data), self.cfg, self._om_data)
        L, b = readout(metric)
        return {"L": L, "b": b, "u": u, "s0": float((phi @ u).mean())}

    def predict(self, fitted: dict, x: np.ndarray) -> np.ndarray:
        x = np.atleast_2d(x)
        om = self._om(x, fitted["u"], fitted["s0"])
        return ((x ** self.cfg["power"]) / om @ fitted["L"].T + fitted["b"]) / om


class ExponentForce:
    """Flat counterpart: constant metric with compartment input exponents (calyx p_c, lobes p_l)."""

    def __init__(self, p_calyx: float, p_lobes: float, cfg: dict = PUBLISHED):
        self.p = p_calyx * CALYX + p_lobes * LOBES
        self.cfg = cfg

    def fit(self, data: dict) -> dict:
        metric = fit_constant_spd(data, self.cfg, lambda d, phi: d["x"] ** self.p)
        L, b = readout(metric)
        return {"L": L, "b": b}

    def predict(self, fitted: dict, x: np.ndarray) -> np.ndarray:
        return np.atleast_2d(x) ** self.p @ fitted["L"].T + fitted["b"]


def _metric_derivatives(g0: np.ndarray, betas: np.ndarray, s0: float, s: float):
    w = np.sqrt(1.0 + betas * (s / s0 - 1))
    w1 = betas / (2 * s0 * w)
    w2 = -betas ** 2 / (4 * s0 ** 2 * w ** 3)
    g = np.outer(w, w) * g0
    g1 = (np.outer(w1, w) + np.outer(w, w1)) * g0
    g2 = (np.outer(w2, w) + 2 * np.outer(w1, w1) + np.outer(w, w2)) * g0
    return g, g1, g2


def riemann_tensor(g0: np.ndarray, betas: np.ndarray, u: np.ndarray, s0: float, y: np.ndarray):
    """Analytic R^r_{s m n} of g(y) = S(s) g0 S(s), s = u.y (metric depends on y only through s)."""
    g, g1, g2 = _metric_derivatives(g0, betas, s0, float(u @ y))
    gi = np.linalg.inv(g)
    gi1 = -gi @ g1 @ gi
    dg = np.einsum("k,ij->kij", u, g1)
    first = 0.5 * (np.einsum("i,kj->kij", u, g1) + np.einsum("j,ki->kij", u, g1) - dg)
    first1 = 0.5 * (np.einsum("i,kj->kij", u, g2) + np.einsum("j,ki->kij", u, g2) - np.einsum("k,ij->kij", u, g2))
    gam = np.einsum("rk,kij->rij", gi, first)
    dgam_ds = np.einsum("rk,kij->rij", gi1, first) + np.einsum("rk,kij->rij", gi, first1)
    dgam = np.einsum("m,rns->rmns", u, dgam_ds)
    riem = np.einsum("rmns->rsmn", dgam) - np.einsum("rnms->rsmn", dgam) \
        + np.einsum("rml,lns->rsmn", gam, gam) - np.einsum("rnl,lms->rsmn", gam, gam)
    return g, riem


def curvature_summary(g0: np.ndarray, betas: np.ndarray, u: np.ndarray, s0: float, y: np.ndarray) -> dict:
    g, riem = riemann_tensor(g0, betas, u, s0, y)
    ric = np.einsum("rsrn->sn", riem)
    scalar = float(np.einsum("sn,sn->", np.linalg.inv(g), ric))
    low = np.einsum("ar,rbcd->abcd", g, riem)
    sect = [low[a, b, a, b] / (g[a, a] * g[b, b] - g[a, b] ** 2) for a in range(6) for b in range(a + 1, 6)]
    return {"scalar_curvature": scalar, "ricci_frobenius": float(np.linalg.norm(ric)),
            "max_abs_sectional_coordinate_planes": float(np.max(np.abs(sect))),
            "riemann_frobenius": float(np.linalg.norm(low))}


def curvature_finite_difference(g0: np.ndarray, betas: np.ndarray, u: np.ndarray, s0: float, y: np.ndarray,
                                h: float = 1e-4) -> float:
    """Independent scalar curvature from finite differences of g(y) (checks the analytic tensor)."""
    def metric(z):
        return _metric_derivatives(g0, betas, s0, float(u @ z))[0]

    def christoffel(z):
        d = np.array([(metric(z + h * e) - metric(z - h * e)) / (2 * h) for e in np.eye(6)])
        first = 0.5 * (np.transpose(d, (1, 0, 2)) + np.transpose(d, (1, 2, 0)) - d)
        return np.einsum("rk,kij->rij", np.linalg.inv(metric(z)), first)
    gam = christoffel(y)
    dgam = np.array([(christoffel(y + h * e) - christoffel(y - h * e)) / (2 * h) for e in np.eye(6)])
    riem = np.einsum("mrns->rsmn", dgam) - np.einsum("nrms->rsmn", dgam) \
        + np.einsum("rml,lns->rsmn", gam, gam) - np.einsum("rnl,lms->rsmn", gam, gam)
    ric = np.einsum("rsrn->sn", riem)
    return float(np.einsum("sn,sn->", np.linalg.inv(metric(y)), ric))


