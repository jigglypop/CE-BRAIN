"""Development: diagnose folds 3 and 6 (floors) and test pilot non-negativity."""
import numpy as np
import dev_spd_reverse as R
from kc_data import load_table, cohort, read_selected_predictions, REGIONS, N_POS

np.set_printoptions(precision=4, suppress=True, linewidth=160)
t = load_table()
full = cohort(t)
saved = {k: np.zeros((N_POS, 6)) for k in ("previous", "candidate")}
for row in read_selected_predictions():
    for k in saved:
        saved[k][int(row["position"]) - 1, REGIONS.index(row["region"])] = float(row[k])
base_extra = {"pilot": "ols_phi", "norm": "se_median", "pen_scale": 1.0, "reg_scale": "ss6", "rho_lb": -np.inf}
cfg = dict(R.CANDIDATE, **base_extra, bound_mode="eig")
for h in (2, 5):
    tr = [p for p in range(N_POS) if p != h]
    subsets = [tr] + [[p for p in tr if p != j] for j in tr]
    for s in subsets:
        X, Y = full["x"][s], full["y"][s]
        phi = X ** cfg["power"]
        k0 = R.unweighted_pilot(phi, Y)
        _, th, v = R.base_fit(X, Y, full["sem_x"][s], full["sem_y"][s], cfg)
        L = np.diag(th[R.TYPE]) + th[4] * np.outer(v, v)
        flag = "*" if (k0 < 0).any() or np.linalg.eigvalsh(L).min() < 0.025 or (th[:4] < 0.025).any() else ""
        if flag:
            print("held", h + 1, "subset", [p + 1 for p in s], "pilot", k0[[0, 1, 2, 3]], "d,rho", th[:5],
                  "eigmin", np.linalg.eigvalsh(L).min())
for bound_mode in ("bvls", "eig", "clip"):
    for nonneg in (False, True):
        extra = dict(base_extra, bound_mode=bound_mode, pilot_nonneg=nonneg)
        out = []
        for name, base in (("cand", R.CANDIDATE), ("prev", R.PREVIOUS)):
            p = R.leave1(full, dict(base, **extra))
            per = np.abs(p - saved["candidate" if name == "cand" else "previous"]).max(axis=1)
            out.append(name + " " + " ".join(f"{e:.0e}" for e in per))
        print(bound_mode, "pilot_nonneg", nonneg, " | ".join(out), flush=True)
