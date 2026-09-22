"""Development: scan the ridge scale on rho against the saved full-fit metric."""
import json
import numpy as np
from scipy.optimize import minimize_scalar
import dev_spd_reverse as R
from kc_data import load_table, cohort, PUBLICATION

t = load_table()
full = cohort(t)
Gs = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])


def g_err(logc, extra):
    cfg = dict(R.CANDIDATE, **extra, reg_scale="1", regularization=3.0 * np.exp(logc))
    G = R.fit(full["x"], full["y"], full["sem_x"], full["sem_y"], cfg)
    return float(np.abs(G - Gs).max())


for pilot in ["ols_x", "ols_phi", "spd_diag", "spd_full"]:
    for norm in ["w_mean", "se_mean", "var_mean", "se_median"]:
        extra = {"pilot": pilot, "norm": norm}
        grid = np.linspace(-14, 4, 37)
        errs = [g_err(c, extra) for c in grid]
        i = int(np.argmin(errs))
        res = minimize_scalar(lambda c: g_err(c, extra), bounds=(grid[max(i - 1, 0)], grid[min(i + 1, 36)]),
                              method="bounded", options={"xatol": 1e-6})
        print(f"{pilot:9s} {norm:9s} best scale {np.exp(res.x):.4e} G err {res.fun:.3e}", flush=True)
