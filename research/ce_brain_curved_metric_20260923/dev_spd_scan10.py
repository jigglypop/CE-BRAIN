"""Development: repair rules for an indefinite unconstrained mobility (folds 3 and 6)."""
import numpy as np
import dev_spd_reverse as R
from kc_data import load_table, cohort, read_selected_predictions, REGIONS, N_POS

t = load_table()
full = cohort(t)
saved = {k: np.zeros((N_POS, 6)) for k in ("previous", "candidate")}
for row in read_selected_predictions():
    for k in saved:
        saved[k][int(row["position"]) - 1, REGIONS.index(row["region"])] = float(row[k])
base_extra = {"pilot": "ols_phi", "norm": "se_median", "pen_scale": 1.0, "reg_scale": "ss6", "rho_lb": -np.inf}
for trigger in ("hyb_eig", "hyb_diag", "hyb_d"):
    for rule in ("hyb_bvls", "hyb_clipd", "hyb_diagc", "hyb_eigc", "hyb_eigp"):
        extra = dict(base_extra, bound_mode=rule, trigger=trigger)
        out = []
        for name, base in (("cand", R.CANDIDATE), ("prev", R.PREVIOUS)):
            p = R.leave1(full, dict(base, **extra))
            per = np.abs(p - saved["candidate" if name == "cand" else "previous"]).max(axis=1)
            out.append(name + " " + " ".join(f"{e:.0e}" for e in per))
        print(f"{trigger:8s} {rule:10s}", " | ".join(out), flush=True)
