"""Development: which data statistic makes the fitted rho-penalty constant fold-invariant."""
import numpy as np
import dev_spd_reverse as R
from kc_data import load_table, cohort

t = load_table()
full = cohort(t)
cfg = dict(R.CANDIDATE, pilot="ols_phi", norm="se_median", pen_scale=1.0, reg_scale="1")
cases = {"full": (list(range(7)), 0.05593), "h1": ([1, 2, 3, 4, 5, 6], 0.052595),
         "h2": ([0, 2, 3, 4, 5, 6], 0.045059), "h5": ([0, 1, 2, 3, 5, 6], 0.053006),
         "h7": ([0, 1, 2, 3, 4, 5], 0.045166)}
for name, (tr, c) in cases.items():
    X, Y, SX, SY = (full[k][tr] for k in ("x", "y", "sem_x", "sem_y"))
    phi = X ** cfg["power"]
    m = np.sqrt(phi.mean(axis=0))
    v = m / np.linalg.norm(m)
    s = phi @ v
    col = (v[None, :] * s[:, None]).reshape(-1)
    k0 = R.unweighted_pilot(phi, Y)
    sphi = cfg["power"] * X ** (cfg["power"] - 1) * SX
    var = (SY ** 2 + k0 ** 2 * sphi ** 2).reshape(-1)
    se = np.sqrt(var)
    w = (se / np.median(se)) ** -5
    n = len(tr)
    stats = {"sum_w_col2/sum_w": (w * col ** 2).sum() / w.sum(), "sum_w_col2/N": (w * col ** 2).sum() / (6 * n),
             "mean_w": w.mean(), "col2_mean": (col ** 2).mean(), "s2_mean": (s ** 2).mean(),
             "var_s": s.var(), "wvar_col": np.cov(col, aweights=w), "var_col": col.var(),
             "med_var": np.median(var), "mean_var": var.mean(), "sum_m2": (m ** 2).sum(),
             "n_var_s": n * s.var(), "n_var_s_ddof1": n * s.var(ddof=1),
             "w_centered": (w.reshape(n, 6) * (v[None, :] * (s - s.mean())[:, None]) ** 2).sum(),
             "w_centered_mean": (w.reshape(n, 6) * (v[None, :] * (s - s.mean())[:, None]) ** 2).sum() / w.mean(),
             "n_var_phi": n * phi.var(axis=0).sum()}
    print(name, "c", c, " ".join(f"{k}={c / val:.4f}" for k, val in stats.items()))
