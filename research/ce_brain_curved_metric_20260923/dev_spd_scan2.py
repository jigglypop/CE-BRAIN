"""Development: jointly fit penalty scales (offset, rho) per normalization against the saved metric."""
import json
import numpy as np
from scipy.optimize import minimize
import dev_spd_reverse as R
from kc_data import load_table, cohort, PUBLICATION

t = load_table()
full = cohort(t)
Gs = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])


def g_err(z, extra):
    cfg = dict(R.CANDIDATE, **extra, pen_scale=float(np.exp(z[0])), reg_scale="1",
               regularization=3.0 * float(np.exp(z[1])))
    G = R.fit(full["x"], full["y"], full["sem_x"], full["sem_y"], cfg)
    return float(np.log10(np.abs(G - Gs).max() + 1e-18))


for pilot in ["ols_phi", "ols_x", "spd_diag"]:
    for norm in ["w_mean", "se_mean", "se_median", "var_mean"]:
        extra = {"pilot": pilot, "norm": norm}
        best = None
        for z0 in ([0.0, np.log(0.056)], [np.log(3.0), np.log(0.1)], [np.log(0.3), np.log(0.02)],
                   [np.log(30), np.log(0.002)], [np.log(0.03), np.log(1e-3)]):
            res = minimize(g_err, z0, args=(extra,), method="Nelder-Mead",
                           options={"xatol": 1e-9, "fatol": 1e-9, "maxiter": 600})
            if best is None or res.fun < best.fun:
                best = res
        print(f"{pilot:9s} {norm:9s} pen_scale {np.exp(best.x[0]):.6e} reg_c {np.exp(best.x[1]):.6e} "
              f"log10 G err {best.fun:.3f}", flush=True)
