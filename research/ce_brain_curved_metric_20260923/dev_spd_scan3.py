"""Development: fit the rho-penalty constant against saved leave-one predictions of both configs."""
import numpy as np
from scipy.optimize import minimize_scalar
import dev_spd_reverse as R
from kc_data import load_table, cohort, read_selected_predictions, REGIONS, N_POS

t = load_table()
full = cohort(t)
saved = {k: np.zeros((N_POS, 6)) for k in ("previous", "candidate")}
for row in read_selected_predictions():
    for k in saved:
        saved[k][int(row["position"]) - 1, REGIONS.index(row["region"])] = float(row[k])

for name, base in (("candidate", R.CANDIDATE), ("previous", R.PREVIOUS)):
    for pilot in ("ols_phi", "ols_x"):
        extra = {"pilot": pilot, "norm": "se_median", "pen_scale": 1.0, "reg_scale": "1"}

        def err(logc):
            cfg = dict(base, **extra, regularization=base["regularization"] * float(np.exp(logc)))
            return float(np.log10(np.abs(R.leave1(full, cfg) - saved[name]).max()))

        grid = np.linspace(-8, 2, 21)
        e = [err(c) for c in grid]
        i = int(np.argmin(e))
        res = minimize_scalar(err, bounds=(grid[max(i - 1, 0)], grid[min(i + 1, 20)]), method="bounded",
                              options={"xatol": 1e-7})
        print(name, pilot, "c", np.exp(res.x), "kappa", base["regularization"] * np.exp(res.x),
              "log10 max pred err", res.fun, flush=True)
