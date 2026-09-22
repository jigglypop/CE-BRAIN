"""Development check: recover evaluation-unit definitions from documented OLS scores."""
from itertools import combinations
import numpy as np
from kc_data import load_table, cohort, slot_parity_masks, REGIONS, N_POS

TYPE = np.array([0, 1, 2, 3, 2, 3])


def fit_affine(x, y, shared):
    n_types = 4 if shared else 6
    groups = TYPE if shared else np.arange(6)
    rows, rhs = [], []
    for p in range(x.shape[0]):
        for c in range(6):
            a = np.zeros(n_types + 6)
            a[groups[c]] = x[p, c]
            a[n_types + c] = 1.0
            rows.append(a)
            rhs.append(y[p, c])
    coef = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)[0]
    return lambda xx: coef[groups] * xx + coef[n_types:]


def leave_k(train_means, test_means, k, shared):
    preds, targets = [], []
    for held in combinations(range(N_POS), k):
        tr = [p for p in range(N_POS) if p not in held]
        f = fit_affine(train_means["x"][tr], train_means["y"][tr], shared)
        for p in held:
            preds.append(f(test_means["x"][p]))
            targets.append(test_means["y"][p])
    e = np.array(preds) - np.array(targets)
    return float(np.sqrt(np.mean(e ** 2)))


t = load_table()
full = cohort(t)
masks = slot_parity_masks(t)
halves = [cohort(t, select=m) for m in masks]
for shared in (False, True):
    print("shared" if shared else "indep",
          "leave1", round(leave_k(full, full, 1, shared), 8),
          "leave2", round(leave_k(full, full, 2, shared), 8),
          "odd->even", round(leave_k(halves[0], halves[1], 1, shared), 8),
          "even->odd", round(leave_k(halves[1], halves[0], 1, shared), 8))
print("documented indep 0.04325579 0.04615604 0.06977048 0.07857924")
print("documented shared 0.04010733 0.04275535 0.06764384 0.07714325")
