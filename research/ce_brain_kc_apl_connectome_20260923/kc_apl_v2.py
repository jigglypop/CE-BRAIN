"""v2 menu from CONTRACT_v2.md: input-normalized APL weight and class-specific excitability.

python kc_apl_v2.py selftest    synthetic recovery only
python kc_apl_v2.py run         refuses to run unless CONTRACT_v2.md lists this code hash
"""
from __future__ import annotations

import argparse
from itertools import permutations
import json
from multiprocessing import Pool
from pathlib import Path
import time

import numpy as np
from scipy.optimize import least_squares

import kc_apl_model as v1

HERE = Path(__file__).resolve().parent
CONNECTOME = json.loads((HERE / "connectome_v2.json").read_text(encoding="utf-8"))
S = np.array(CONNECTOME["class_input_share"])
H = np.array(CONNECTOME["h_apl_input_fraction"])
MENU = {"V0b": (None, True), "V2a": ("h", False), "V2b": ("h", True), "V2c": ("a", True)}


def unpack(p, per_class):
    if per_class:
        return S @ np.asarray(p[:3]), p[3], p[4]
    return p[0], p[1], p[2]


def predict(p, spec, x):
    w, b, per_class = spec
    if w is None:
        return (S @ np.asarray(p[:3]))[None, :] * np.atleast_2d(x)
    e, k, lam = unpack(p, per_class)
    return v1.treated((e, k, lam), w, b, x)


def fit(train, spec):
    w, _, per_class = spec
    x, y = train["x"], train["y"]
    if w is None:
        r = least_squares(lambda p: (predict(p, spec, x) - y).ravel(), (1.0, 1.0, 1.0),
                          bounds=([0.05] * 3, [20.0] * 3))
        return tuple(r.x)
    n_e = 3 if per_class else 1
    lower, upper = [0.05] * n_e + [0.0, 0.0], [20.0] * n_e + [20.0, 1e4]
    best = None
    for start in ([1.0] * n_e + [1.0, 1.0], [0.7] * n_e + [0.5, 10.0]):
        r = least_squares(lambda p: (predict(p, spec, x) - y).ravel(), start, bounds=(lower, upper))
        best = r if best is None or r.cost < best.cost else best
    return tuple(best.x)


def task_error(job):
    spec, task = job
    return predict(fit(task["train"], spec), spec, task["test_x"]) - task["test_y"]


def spec_for(name, a, b, order=None):
    kind, per_class = MENU[name]
    w = None if kind is None else (H if kind == "h" else a)
    if order is not None:
        w, b = w[order], b[order]
    return (w, b, per_class)


def selftest():
    rng = np.random.default_rng(11)
    b = rng.dirichlet(np.ones(6))
    x = rng.uniform(0.05, 0.6, size=(7, 6))
    truth = (0.3, 0.8, 0.6, 0.4, 25.0)
    spec = (H, b, True)
    y = predict(truth, spec, x)
    got = fit({"x": x, "y": y}, spec)
    e_c = S @ np.array(truth[:3])
    direct = e_c * x * (1 + truth[4] * H * (x @ b)[:, None]) / (1 + truth[3] * truth[4] * H * (y @ b)[:, None])
    report = {"true": truth, "recovered": [float(v) for v in got], "fixed_point_residual": float(np.abs(y - direct).max())}
    assert report["fixed_point_residual"] < 1e-12 and np.allclose(got, truth, rtol=1e-4), report
    print(json.dumps(report, indent=1))


def run():
    code_hash = v1.sha256(__file__)
    if code_hash not in (HERE / "CONTRACT_v2.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT_v2.md does not list this code hash {code_hash}")
    from kc_data import FRESH_SEEDS, cohort, fresh_tasks, load_table, panel_tasks
    started = time.perf_counter()
    table = load_table()
    conn = json.loads((HERE / "results_v1.json").read_text(encoding="utf-8"))["connectome"]["both"]
    a, b = np.array(conn["a"]), np.array(conn["b"])
    panels = {p: panel_tasks(table, p) for p in ("leave1", "leave2", "slot0", "slot1")}
    panels["fresh32"] = [t for seed in FRESH_SEEDS for t in fresh_tasks(table, seed)]
    groups = [((name, p), spec_for(name, a, b)) for name in MENU for p in panels]
    jobs = [(spec, task) for (name, p), spec in groups for task in panels[p]]
    with Pool(v1.args_workers()) as pool:
        flat = pool.map(task_error, jobs, chunksize=8)
        scores, cursor = {}, 0
        for (name, p), _ in groups:
            n = len(panels[p])
            scores.setdefault(name, {})[p] = v1.summarize(flat[cursor:cursor + n])
            cursor += n
        best = min(("V2a", "V2b", "V2c"), key=lambda m: scores[m]["leave1"]["rmse"])
        orders = [list(o) for o in permutations(range(6))]
        perm_jobs = [(spec_for(best, a, b, o), task) for o in orders for task in panels["leave1"]]
        perm_flat = pool.map(task_error, perm_jobs, chunksize=8)
    k1 = len(panels["leave1"])
    perm_rmse = [v1.summarize(perm_flat[i * k1:(i + 1) * k1])["rmse"] for i in range(len(orders))]
    if abs(perm_rmse[0] - scores[best]["leave1"]["rmse"]) > 1e-12:
        raise ValueError("identity permutation must reproduce the selected model")
    rank = int(sum(r <= perm_rmse[0] + 1e-15 for r in perm_rmse))
    c31, c22 = cohort(table, "31c"), cohort(table, "22c")
    spec = spec_for(best, a, b)
    p31 = fit(c31, spec)
    e22 = np.array(fit(c22, spec_for("V0b", a, b)))
    e_c, k, lam = unpack(p31, MENU[best][1])
    w = spec[0]
    F = 1 + lam * w[None, :] * (c31["x"] @ b)[:, None]
    e_class = np.array(p31[:3]) if MENU[best][1] else np.full(3, p31[0])
    adapt = e_class / e22
    confirm = ("leave2", "slot0", "slot1", "fresh32")
    h = {"selected": best,
         "H0_feedback_needed": {"leave1": scores[best]["leave1"]["rmse"] < scores["V0b"]["leave1"]["rmse"],
                                "confirm_wins": sum(scores[best][p]["rmse"] < scores["V0b"][p]["rmse"] for p in confirm)},
         "H1_apl_structure": {"rank": rank, "of": len(orders), "pass": rank <= 36,
                              "perm_rmse_quantiles": np.quantile(perm_rmse, [0, .05, .5, .95, 1]).tolist()},
         "H2_literature": {"k": k, "k_lt_1": k < 1, "median_F": float(np.median(F)),
                           "median_F_in_2_3": 2 <= float(np.median(F)) <= 3,
                           "e31_class": e_class.tolist(), "e22_class": e22.tolist(),
                           "adapt_class": adapt.tolist(), "adapt_all_lt_1": bool(np.all(adapt < 1))},
         "H3_vs_published_spd": {"leave1": scores[best]["leave1"]["rmse"] <= v1.PUBLISHED_SPD["leave1"],
                                 "confirm_wins": sum(scores[best][p]["rmse"] <= v1.PUBLISHED_SPD[p] for p in confirm)}}
    h["H0_feedback_needed"]["pass"] = h["H0_feedback_needed"]["leave1"] and h["H0_feedback_needed"]["confirm_wins"] >= 3
    h["H2_literature"]["pass"] = h["H2_literature"]["k_lt_1"] and h["H2_literature"]["median_F_in_2_3"] \
        and h["H2_literature"]["adapt_all_lt_1"]
    ok = h["H0_feedback_needed"]["pass"] and h["H1_apl_structure"]["pass"] and h["H2_literature"]["pass"]
    result = {"schema": "ce-kc-apl-connectome-v2", "verdict": "SUPPORTED_DEVELOPMENT" if ok else "NOT_SUPPORTED",
              "hypotheses": h, "scores": scores, "full_fit_31c": [float(v) for v in p31], "lambda": lam,
              "F_range": [float(F.min()), float(F.max())], "code_sha256": code_hash,
              "elapsed_seconds": round(time.perf_counter() - started, 2)}
    with (HERE / "results_v2.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({"verdict": result["verdict"], "hypotheses": h,
                      "rmse": {m: {p: round(scores[m][p]["rmse"], 5) for p in scores[m]} for m in scores},
                      "full_fit_31c": result["full_fit_31c"]}, indent=1, default=float))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("selftest", "run"))
    selftest() if parser.parse_args().stage == "selftest" else run()
