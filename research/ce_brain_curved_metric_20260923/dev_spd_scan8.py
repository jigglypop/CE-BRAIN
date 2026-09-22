"""Development: bound handling and inner-v variants, per-fold agreement with saved predictions."""
import json
import numpy as np
import dev_spd_reverse as R
from kc_data import load_table, cohort, read_selected_predictions, REGIONS, N_POS, PUBLICATION

t = load_table()
full = cohort(t)
Gs = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])
saved = {k: np.zeros((N_POS, 6)) for k in ("previous", "candidate")}
for row in read_selected_predictions():
    for k in saved:
        saved[k][int(row["position"]) - 1, REGIONS.index(row["region"])] = float(row[k])

for bound_mode in ("bvls", "eig"):
    for loo_v_fixed in (False, True):
        extra = {"pilot": "ols_phi", "norm": "se_median", "pen_scale": 1.0, "reg_scale": "ss6",
                 "bound_mode": bound_mode, "rho_lb": -np.inf, "loo_v_fixed": loo_v_fixed}
        out = []
        G = R.fit(full["x"], full["y"], full["sem_x"], full["sem_y"], dict(R.CANDIDATE, **extra))
        out.append(f"G {np.abs(G - Gs).max():.1e}")
        for name, base in (("cand", R.CANDIDATE), ("prev", R.PREVIOUS)):
            p = R.leave1(full, dict(base, **extra))
            per = np.abs(p - saved["candidate" if name == "cand" else "previous"]).max(axis=1)
            out.append(name + " " + " ".join(f"{e:.0e}" for e in per))
        print(bound_mode, loo_v_fixed, " | ".join(out), flush=True)
