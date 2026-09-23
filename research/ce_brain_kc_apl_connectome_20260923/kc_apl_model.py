"""Connectome-fixed KC-APL compartment feedback model (pre-registered in CONTRACT.md).

python kc_apl_model.py selftest     synthetic recovery only, never opens the KC calcium table
python kc_apl_model.py run          contract evaluation; refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from itertools import permutations
import json
from multiprocessing import Pool
import os
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/ce_brain_curved_metric_20260923"))
MALECNS = ROOT / "verify/MaleCNS"
COMPARTMENTS = (("Calyx", "CA"), ("gamma", "gL"), ("beta", "bL"), ("betaprime", "b'L"),
                ("alpha", "aL"), ("alphaprime", "a'L"))
PUBLISHED_SPD = {"leave1": 0.03635965190430477, "leave2": 0.039622675324239486,
                 "slot0": 0.06419516470352883, "slot1": 0.07450860016306389, "fresh32": 0.12141653250790259}
BOUNDS = ([0.05, 0.0, 0.0], [20.0, 20.0, 1e4])
STARTS = ((1.0, 1.0, 1.0), (0.7, 0.5, 10.0))
F_TARGET = 2.5


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def connectome_fractions():
    """a = APL->KC, b = KC->APL synapse fractions over the six compartments (both sides, and per side)."""
    graph_module = load_module("malecns_neuron_graph", MALECNS / "neuron_graph.py")
    roi_module = load_module("malecns_neuron_roi", MALECNS / "neuron_roi.py")
    graph = graph_module.load(MALECNS / "neuron_graph_result.json")
    roi = roi_module.load(MALECNS / "neuron_roi_result.json")
    types = graph["type_labels"] + [""]
    names = np.array(types)[graph["type_code"]]
    kc, apl = np.char.startswith(names, "KC"), names == "APL"
    to_apl = roi_module.type_roi_counts(graph, roi, kc, apl)
    from_apl = roi_module.type_roi_counts(graph, roi, apl, kc)
    index = {name: i for i, name in enumerate(roi["roi_names"])}
    out = {"kc_neurons": int(kc.sum()), "apl_neurons": int(apl.sum()),
           "kc_to_apl_total": int(to_apl.sum()), "apl_to_kc_total": int(from_apl.sum())}
    for label, sides in (("both", ("L", "R")), ("left", ("L",)), ("right", ("R",))):
        raw_b = np.array([sum(to_apl[index[f"{r}({s})"]] for s in sides) for _, r in COMPARTMENTS], dtype=float)
        raw_a = np.array([sum(from_apl[index[f"{r}({s})"]] for s in sides) for _, r in COMPARTMENTS], dtype=float)
        out[label] = {"kc_to_apl": raw_b.astype(int).tolist(), "apl_to_kc": raw_a.astype(int).tolist(),
                      "b": (raw_b / raw_b.sum()).tolist(), "a": (raw_a / raw_a.sum()).tolist()}
    return out


def treated(params, a, b, x):
    """Solve A^T = b.(e x F / (1 + k lam a A^T)); x has shape (m, 6).

    With nonnegative terms g(s) = sum_c b_c d_c / (1 + k lam a_c s) - s is convex and
    decreasing, so Newton from s = 0 rises monotonically to the unique root. Rows with
    a negative term fall back to bisection on the same bracket.
    """
    e, k, lam = params
    x = np.atleast_2d(x)
    A = x @ b
    drive = e * x * (1 + lam * a[None, :] * A[:, None])
    if k * lam == 0:
        return drive
    w, ka = drive * b[None, :], k * lam * a[None, :]
    if np.any(w.sum(axis=1) <= 0):
        raise ValueError("no positive self-consistent APL drive")
    s = np.zeros(len(x))
    convex = np.all(w >= 0, axis=1)
    for _ in range(100):
        q = 1 + ka * s[:, None]
        step = ((w / q).sum(axis=1) - s) / (-(w * ka / q ** 2).sum(axis=1) - 1)
        s = np.where(convex, s - step, s)
        if np.all(np.abs(step[convex]) <= 1e-15 * np.maximum(1, np.abs(s[convex]))):
            break
    if not convex.all():
        g = lambda v: (w / (1 + ka * v[:, None])).sum(axis=1) - v
        lo, hi = np.zeros(len(x)), np.maximum(w.clip(min=0).sum(axis=1), 1e-12) * 2 + 1
        for _ in range(80):
            mid = (lo + hi) / 2
            up = g(mid) > 0
            lo, hi = np.where(up, mid, lo), np.where(up, hi, mid)
        s = np.where(convex, s, (lo + hi) / 2)
    return drive / (1 + ka * s[:, None])


def fit(train, a, b, fixed_lam=None):
    x, y = train["x"], train["y"]
    if fixed_lam is None:
        best = None
        for start in STARTS:
            r = least_squares(lambda p: (treated(p, a, b, x) - y).ravel(), start, bounds=BOUNDS)
            best = r if best is None or r.cost < best.cost else best
        return tuple(best.x)
    r = least_squares(lambda p: (treated((p[0], p[1], fixed_lam), a, b, x) - y).ravel(),
                      (0.7, 0.5), bounds=(BOUNDS[0][:2], BOUNDS[1][:2]))
    return (r.x[0], r.x[1], fixed_lam)


def literature_lam(x, a, b):
    return (F_TARGET - 1) / np.median(a[None, :] * (x @ b)[:, None])


class Model:
    def __init__(self, kind, a=None, b=None):
        self.kind, self.a, self.b = kind, a, b

    def fit_predict(self, train, test_x):
        if self.kind == "M0":
            x, y = train["x"].ravel(), train["y"].ravel()
            return (x @ y) / (x @ x) * test_x
        lam = literature_lam(train["x"], self.a, self.b) if self.kind == "M_lit" else None
        return treated(fit(train, self.a, self.b, lam), self.a, self.b, test_x)


def summarize(errors):
    e = np.concatenate([np.atleast_2d(v) for v in errors])
    return {"rmse": float(np.sqrt(np.mean(e ** 2))), "mae": float(np.mean(np.abs(e))),
            "region_rmse": np.sqrt(np.mean(e ** 2, axis=0)).tolist()}


def evaluate(model, tasks):
    return summarize([model.fit_predict(t["train"], t["test_x"]) - t["test_y"] for t in tasks])


def task_error(job):
    kind, a, b, task = job
    return Model(kind, a, b).fit_predict(task["train"], task["test_x"]) - task["test_y"]


def selftest():
    rng = np.random.default_rng(7)
    a, b = rng.dirichlet(np.ones(6)), rng.dirichlet(np.ones(6))
    truth = (0.6, 0.35, 12.0)
    x = rng.uniform(0.05, 0.6, size=(7, 6))
    y = treated(truth, a, b, x)
    got = fit({"x": x, "y": y}, a, b)
    A, yt = x @ b, y @ b
    residual = np.abs(y - truth[0] * x * (1 + truth[2] * a * A[:, None]) / (1 + truth[1] * truth[2] * a * yt[:, None]))
    lam = literature_lam(x, a, b)
    median_f = np.median(1 + lam * a[None, :] * A[:, None])
    from scipy.optimize import brentq
    probe = np.vstack([rng.uniform(0.01, 1.0, size=(200, 6)), rng.uniform(-0.05, 0.6, size=(200, 6))])
    probe = probe[(probe @ b) > 0.05]
    worst = 0.0
    for params in ((0.6, 0.35, 12.0), (1.3, 4.0, 300.0), (0.2, 0.01, 0.5)):
        fast = treated(params, a, b, probe)
        for row, got_row in zip(probe, fast):
            e_, k_, l_ = params
            d = e_ * row * (1 + l_ * a * (row @ b))
            root = brentq(lambda v: (d / (1 + k_ * l_ * a * v)) @ b - v, 0, 2 * max(d.clip(min=0) @ b, 1e-12) + 1,
                          xtol=1e-15, rtol=1e-15)
            worst = max(worst, float(np.max(np.abs(got_row - d / (1 + k_ * l_ * a * root)))))
    report = {"true": truth, "recovered": [float(v) for v in got], "fixed_point_residual": float(residual.max()),
              "literature_lam_median_F": float(median_f), "newton_vs_brentq_max_abs": worst,
              "probe_rows": int(len(probe)), "probe_rows_with_negative_terms": int((probe < 0).any(axis=1).sum())}
    assert residual.max() < 1e-10 and abs(median_f - F_TARGET) < 1e-12 and worst < 1e-10
    assert np.allclose(got, truth, rtol=1e-4), report
    print(json.dumps(report, indent=1))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def args_workers():
    return max(1, min(12, (os.cpu_count() or 2) - 1))


def run():
    code_hash = sha256(__file__)
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}; freeze it first")
    from kc_data import FRESH_SEEDS, REGIONS, cohort, fresh_tasks, load_table, panel_tasks
    started = time.perf_counter()
    table = load_table()
    conn = connectome_fractions()
    a, b = np.array(conn["both"]["a"]), np.array(conn["both"]["b"])
    if tuple(r for r, _ in COMPARTMENTS) != tuple(REGIONS):
        raise ValueError("compartment order differs from calcium table")
    s = np.sqrt(a * b) / np.sqrt(a * b).sum()
    uniform = np.full(6, 1 / 6)
    models = {"M0": ("M0", None, None), "M_conn": ("M_conn", a, b), "M_lit": ("M_lit", a, b),
              "M_sym": ("M_sym", s, s), "M_unif": ("M_unif", uniform, uniform)}
    panels = {p: panel_tasks(table, p) for p in ("leave1", "leave2", "slot0", "slot1")}
    panels["fresh32"] = [t for seed in FRESH_SEEDS for t in fresh_tasks(table, seed)]
    groups = [((name, p), spec) for name, spec in models.items() for p in panels]
    groups += [((f"M_conn_{side}", "leave1"), ("M_conn", np.array(conn[side]["a"]), np.array(conn[side]["b"])))
               for side in ("left", "right")]
    orders = [list(p) for p in permutations(range(6))]
    groups += [(("perm", i), ("M_conn", a[p], b[p])) for i, p in enumerate(orders)]
    jobs = [(spec[0], spec[1], spec[2], task) for key, spec in groups
            for task in panels["leave1" if key[0] == "perm" else key[1]]]
    with Pool(args_workers()) as pool:
        flat = pool.map(task_error, jobs, chunksize=8)
    errors, cursor = {}, 0
    for key, _ in groups:
        count = len(panels["leave1" if key[0] == "perm" else key[1]])
        errors[key], cursor = flat[cursor:cursor + count], cursor + count
    scores = {}
    for (name, p), errs in errors.items():
        if name != "perm":
            scores.setdefault(name, {})[p] = summarize(errs)
    perm_rmse = [summarize(errors[("perm", i)])["rmse"] for i in range(len(orders))]
    identity = scores["M_conn"]["leave1"]["rmse"]
    if orders[0] != list(range(6)) or abs(perm_rmse[0] - identity) > 1e-12:
        raise ValueError("identity permutation must reproduce M_conn")
    rank = int(sum(r <= identity + 1e-15 for r in perm_rmse))
    full31, full22 = cohort(table, "31c"), cohort(table, "22c")
    fits = {}
    for label, data in (("31c", full31), ("22c", full22)):
        e, k, lam = fit(data, a, b)
        F = 1 + lam * a[None, :] * (data["x"] @ b)[:, None]
        fits[label] = {"e": e, "k": k, "lambda": lam, "median_F": float(np.median(F)),
                       "F_range": [float(F.min()), float(F.max())],
                       "rmse_in_sample": float(np.sqrt(np.mean((treated((e, k, lam), a, b, data["x"]) - data["y"]) ** 2)))}
    confirm = ("leave2", "slot0", "slot1", "fresh32")
    beats = lambda m, ref: sum(scores[m][p]["rmse"] <= ref[p] for p in confirm)
    spd_ok = {m: scores[m]["leave1"]["rmse"] <= PUBLISHED_SPD["leave1"] and beats(m, PUBLISHED_SPD) >= 3
              for m in ("M_conn", "M_lit")}
    sym_ref = {p: scores["M_sym"][p]["rmse"] for p in PUBLISHED_SPD}
    h = {"H1_structure_beats_permutations": {"rank": rank, "of": len(perm_rmse), "pass": rank <= 36,
                                             "perm_rmse_quantiles": np.quantile(perm_rmse, [0, .05, .5, .95, 1]).tolist()},
         "H2_literature_mechanism": {"e_lt_1": fits["31c"]["e"] < 1, "k_lt_1": fits["31c"]["k"] < 1,
                                     "median_F_in_2_3": 2 <= fits["31c"]["median_F"] <= 3},
         "H3_matches_published_spd": {**spd_ok, "pass": any(spd_ok.values())},
         "H4_direction_needed": {"leave1": scores["M_conn"]["leave1"]["rmse"] < sym_ref["leave1"],
                                 "confirm_wins": sum(scores["M_conn"][p]["rmse"] < sym_ref[p] for p in confirm)}}
    h["H2_literature_mechanism"]["pass"] = all(h["H2_literature_mechanism"].values())
    h["H4_direction_needed"]["pass"] = h["H4_direction_needed"]["leave1"] and h["H4_direction_needed"]["confirm_wins"] >= 3
    verdict = "SUPPORTED_DEVELOPMENT" if h["H1_structure_beats_permutations"]["pass"] and h["H2_literature_mechanism"]["pass"] \
        else "NOT_SUPPORTED"
    result = {"schema": "ce-kc-apl-connectome-v1", "verdict": verdict, "hypotheses": h, "connectome": conn,
              "symmetric_s": s.tolist(), "scores": scores, "full_fits": fits, "published_spd_rmse": PUBLISHED_SPD,
              "regions": list(REGIONS), "code_sha256": code_hash,
              "elapsed_seconds": round(time.perf_counter() - started, 2)}
    out = HERE / "results_v1.json"
    with out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({"verdict": verdict, "hypotheses": h, "full_fits": fits,
                      "leave1": {m: round(scores[m]["leave1"]["rmse"], 6) for m in scores}}, indent=1, default=float))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("selftest", "run"))
    selftest() if parser.parse_args().stage == "selftest" else run()
