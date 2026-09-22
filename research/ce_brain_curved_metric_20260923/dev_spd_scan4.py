"""Development: per-fold rho-penalty constant for the saved leave-one predictions."""
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
    extra = {"pilot": "ols_phi", "norm": "se_median", "pen_scale": 1.0, "reg_scale": "1"}
    for h in range(N_POS):
        tr = [p for p in range(N_POS) if p != h]

        def err(logc):
            cfg = dict(base, **extra, regularization=base["regularization"] * float(np.exp(logc)))
            G = R.fit(full["x"][tr], full["y"][tr], full["sem_x"][tr], full["sem_y"][tr], cfg)
            return float(np.log10(np.abs(R.predict(G, full["x"][h], cfg["power"]) - saved[name][h]).max() + 1e-18))

        grid = np.linspace(-8, 2, 41)
        e = [err(c) for c in grid]
        i = int(np.argmin(e))
        res = minimize_scalar(err, bounds=(grid[max(i - 1, 0)], grid[min(i + 1, 40)]), method="bounded",
                              options={"xatol": 1e-8})
        print(name, "held", h + 1, "c", f"{np.exp(res.x):.6f}", "log10 err", f"{res.fun:.2f}", flush=True)
