"""Development: joint penalty-scale fit for further weight variants (ddof, pilot grouping)."""
import json
import numpy as np
from scipy.optimize import minimize
import dev_spd_reverse as R
from kc_data import load_table, cohort, PUBLICATION

t = load_table()
full = cohort(t)
Gs = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])
ddof0 = {"sem_x": full["sem_x"] * np.sqrt((full["n_x"] - 1) / full["n_x"]),
         "sem_y": full["sem_y"] * np.sqrt((full["n_y"] - 1) / full["n_y"])}


def g_err(z, extra, sems):
    cfg = dict(R.CANDIDATE, **extra, pen_scale=float(np.exp(z[0])), reg_scale="1",
               regularization=3.0 * float(np.exp(z[1])))
    G = R.fit(full["x"], full["y"], sems["sem_x"], sems["sem_y"], cfg)
    return float(np.log10(np.abs(G - Gs).max() + 1e-18))


for sem_name, sems in (("ddof1", full), ("ddof0", ddof0)):
    for pilot in ("ols_phi", "ols_phi_region", "y_only"):
        extra = {"pilot": pilot, "norm": "se_median"}
        best = None
        for z0 in ([0.0, np.log(0.056)], [np.log(3.0), np.log(0.1)], [np.log(0.3), np.log(0.02)]):
            res = minimize(g_err, z0, args=(extra, sems), method="Nelder-Mead",
                           options={"xatol": 1e-9, "fatol": 1e-9, "maxiter": 400})
            if best is None or res.fun < best.fun:
                best = res
        print(f"{sem_name} {pilot:15s} pen_scale {np.exp(best.x[0]):.6e} reg_c {np.exp(best.x[1]):.6e} "
              f"log10 G err {best.fun:.3f}", flush=True)
