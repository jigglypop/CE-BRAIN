"""Development: test natural rho-penalty scalings against saved metric and predictions."""
import json
import numpy as np
from scipy.optimize import minimize_scalar
import dev_spd_reverse as R
from kc_data import load_table, cohort, read_selected_predictions, REGIONS, N_POS, PUBLICATION

t = load_table()
full = cohort(t)
Gs = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])
saved = {k: np.zeros((N_POS, 6)) for k in ("previous", "candidate")}
for row in read_selected_predictions():
    for k in saved:
        saved[k][int(row["position"]) - 1, REGIONS.index(row["region"])] = float(row[k])

for scale in ("ss6", "ss5", "wss6", "ss"):
    extra = {"pilot": "ols_phi", "norm": "se_median", "pen_scale": 1.0, "reg_scale": scale}

    def g_err(logc):
        cfg = dict(R.CANDIDATE, **extra, regularization=3.0 * float(np.exp(logc)))
        G = R.fit(full["x"], full["y"], full["sem_x"], full["sem_y"], cfg)
        return float(np.log10(np.abs(G - Gs).max()))

    res = minimize_scalar(g_err, bounds=(-4, 4), method="bounded", options={"xatol": 1e-8})
    cfg_c = dict(R.CANDIDATE, **extra)
    cfg_p = dict(R.PREVIOUS, **extra)
    ec = np.abs(R.leave1(full, cfg_c) - saved["candidate"]).max()
    ep = np.abs(R.leave1(full, cfg_p) - saved["previous"]).max()
    Gc = R.fit(full["x"], full["y"], full["sem_x"], full["sem_y"], cfg_c)
    print(f"{scale:5s} best multiplier {np.exp(res.x):.5f} (log10 G err {res.fun:.2f}); at multiplier 1: "
          f"G err {np.abs(Gc - Gs).max():.2e} cand {ec:.2e} prev {ep:.2e}", flush=True)
