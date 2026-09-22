"""Development: search random record-split protocols that reproduce the published fresh32 aggregates."""
import sys
import numpy as np
import metric_models as M
from kc_data import load_table, cohort, REGIONS, GROUPS, N_POS

t = load_table()
TARGET = {"previous": (0.12496037622517933, 0.09047749403416648),
          "candidate": (0.12141653250790259, 0.08880692863122822)}


def masks_for(seed, protocol):
    rng_kind, order, size_rule, direction = protocol
    rng = np.random.default_rng(seed) if rng_kind == "default" else np.random.RandomState(seed)
    groups = GROUPS if order == "all" else (("31c", "ctrl"), ("31c", "TRPA"))
    a = {}
    for region in REGIONS:
        for group in groups:
            n = t[(region, group)]["values"].shape[0]
            perm = rng.permutation(n)
            k = {"floor": n // 2, "ceil": (n + 1) // 2}[size_rule]
            m = np.zeros(n, dtype=bool)
            m[perm[:k]] = True
            a[(region, group)] = m
    return a


def split_tasks(seed, protocol):
    a = masks_for(seed, protocol)
    keys = [(r, ("31c", g)) for r in REGIONS for g in ("ctrl", "TRPA")]
    set_a = cohort(t, select={k: a[k] for k in keys})
    set_b = cohort(t, select={k: ~a[k] for k in keys})
    pairs = [(set_a, set_b)] if protocol[3] == "a2b" else [(set_a, set_b), (set_b, set_a)]
    tasks = []
    for tr, te in pairs:
        for h in range(N_POS):
            keep = [p for p in range(N_POS) if p != h]
            tasks.append((M.subset(tr, keep), te["x"][h], te["y"][h]))
    return tasks


def aggregate(protocol, cfg, seeds):
    err = []
    for s in seeds:
        for train, x, y in split_tasks(s, protocol):
            g = M.fit_constant_spd(train, cfg)
            err.append(M.predict_constant_spd(g, x[None, :], cfg["power"])[0] - y)
    e = np.concatenate(err)
    return float(np.sqrt(np.mean(e ** 2))), float(np.mean(np.abs(e)))


seeds = list(range(2026091900, 2026091932))
for rng_kind in ("default", "legacy"):
    for order in ("all", "31c"):
        for size_rule in ("floor", "ceil"):
            for direction in ("a2b", "both"):
                protocol = (rng_kind, order, size_rule, direction)
                try:
                    r = aggregate(protocol, M.PREVIOUS, seeds)
                    print(protocol, f"prev rmse {r[0]:.8f} mae {r[1]:.8f} (target {TARGET['previous'][0]:.8f} "
                          f"{TARGET['previous'][1]:.8f})", flush=True)
                except Exception as exc:
                    print(protocol, "failed", exc, flush=True)
sys.exit(0)
