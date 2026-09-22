"""Development: odor-specific measurement noise of cohort means after removing per-fly offsets."""
import numpy as np
import metric_models as M
from kc_data import load_table, cohort, REGIONS

t = load_table()
full = cohort(t)
spec = {}
for kind in ("ctrl", "TRPA"):
    s = np.zeros((7, 6))
    for c, region in enumerate(REGIONS):
        v = t[(region, ("31c", kind))]["values"]
        n = v.shape[0]
        e = v - v.mean(axis=1, keepdims=True)
        e = e - e.mean(axis=0, keepdims=True)
        s[:, c] = np.sqrt((e ** 2).sum(axis=0) / (n - 1) * 7 / 6) / np.sqrt(n)
    spec[kind] = s
g = M.fit_constant_spd(full)
L = np.linalg.inv(g[:6, :6])
slope = np.diag(L) * 0.625 * full["x"] ** (-0.375)
floor_full = np.sqrt(np.mean(full["sem_y"] ** 2 + slope ** 2 * full["sem_x"] ** 2))
floor_spec = np.sqrt(np.mean(spec["TRPA"] ** 2 + slope ** 2 * spec["ctrl"] ** 2))
per_region = np.sqrt(np.mean(spec["TRPA"] ** 2 + slope ** 2 * spec["ctrl"] ** 2, axis=0))
print("noise floor using full SEM", floor_full)
print("noise floor using odor-specific SEM (fly offsets removed)", floor_spec)
print("per region", dict(zip(REGIONS, np.round(per_region, 5))))
print("published per-region RMSE", [0.03756614, 0.01112222, 0.03231115, 0.03090029, 0.01906242, 0.06352175])
