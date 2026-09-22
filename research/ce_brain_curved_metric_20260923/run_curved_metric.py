"""Pre-registered test of a state-dependent (curved) SPD metric for KC calcium cohort means.

python run_curved_metric.py --stage development    primary leave-one-odor panel only (no contract needed)
python run_curved_metric.py --stage confirmation   all panels; refuses to run unless contract_v1.json matches the code
"""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
import metric_models as M
from kc_data import (CSV_BYTES, CSV_PATH, CSV_SHA256, FRESH_SEEDS, N_POS, PUBLICATION, REGIONS, cohort,
                     fresh_tasks, git_blob_sha1, load_table, panel_tasks, quality, read_selected_predictions,
                     verify_targets)

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "contract_v1.json"
CODE_FILES = ("kc_data.py", "metric_models.py", "run_curved_metric.py")
BETA_CALYX = (-0.65, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2)
BETA_LOBES = (0.0,)
P_CALYX = (0.625, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
P_LOBES = (0.625,)
CURVED_GRID = [(bc, bl) for bc in BETA_CALYX for bl in BETA_LOBES]
EXPONENT_GRID = [(pc, pl) for pc in P_CALYX for pl in P_LOBES]
FAMILIES = {
    "published_constant_spd": ([()], (), lambda h: M.PublishedSPD()),
    "affine_x": ([()], (), lambda h: M.Affine("x")),
    "affine_phi": ([()], (), lambda h: M.Affine("phi")),
    "curved_apl_metric": (CURVED_GRID, (0.0, 0.0), lambda h: M.CurvedAPL(*h)),
    "flat_input_metric": (CURVED_GRID, (0.0, 0.0), lambda h: M.InputMetric(*h)),
    "flat_exponent_force": (EXPONENT_GRID, (0.625, 0.625), lambda h: M.ExponentForce(*h)),
}
PUBLISHED_BASELINE = {"leave1": 0.03635965190430477, "leave2": 0.039622675324239486,
                      "slot0": 0.06419516470352883, "slot1": 0.07450860016306389, "fresh32": 0.12141653250790259}
PUBLISHED_REGION_RMSE = dict(zip(REGIONS, (0.03756614, 0.01112222, 0.03231115, 0.03090029, 0.01906242, 0.06352175)))
I_CTRL_RANGE = (0.5, 2.0 / 3.0)
TABLE = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def init_worker():
    global TABLE
    TABLE = load_table()


def tasks_for(panel: str) -> list[dict]:
    if panel.startswith("fresh:"):
        return fresh_tasks(TABLE, int(panel.split(":")[1]))
    return panel_tasks(TABLE, panel)


def select(family: str, train: dict) -> tuple[list, dict]:
    """Inner leave-one-condition-out over the outer training conditions only."""
    grid, reference, make = FAMILIES[family]
    if len(grid) == 1:
        return grid, {}
    n = train["x"].shape[0]
    scores = {}
    for h in grid:
        model = make(h)
        try:
            err = [model.predict(model.fit(M.subset(train, [i for i in range(n) if i != j])), train["x"][j])[0]
                   - train["y"][j] for j in range(n)]
            scores[h] = float(np.sqrt(np.mean(np.square(err))))
        except (RuntimeError, np.linalg.LinAlgError, ValueError):
            scores[h] = float("inf")
    best = min(scores.values())
    order = sorted(grid, key=lambda h: (scores[h] > best + 1e-12, scores[h] if scores[h] > best + 1e-12 else 0.0,
                                        float(np.sum(np.abs(np.subtract(h, reference))))))
    return order, scores


def run_job(job: tuple[str, int, str]) -> dict:
    panel, index, family = job
    task = tasks_for(panel)[index]
    order, scores = select(family, task["train"])
    make = FAMILIES[family][2]
    for rank, h in enumerate(order):
        model = make(h)
        try:
            fitted = model.fit(task["train"])
            pred = model.predict(fitted, task["test_x"])
            out = {"panel": panel, "index": index, "family": family, "hyper": list(h), "fallback_rank": rank,
                   "pred": pred.tolist(), "target": task["test_y"].tolist(), "held": task["held"],
                   "inner_best": min(scores.values()) if scores else None}
            if family == "curved_apl_metric":
                out["pred_frozen_metric"] = model.predict(fitted, task["test_x"], frozen=True).tolist()
            return out
        except (RuntimeError, np.linalg.LinAlgError, ValueError):
            continue
    raise RuntimeError(f"all hyperparameters failed: {job}")


def metrics(pred: np.ndarray, target: np.ndarray) -> dict:
    e = pred - target
    return {"rmse": float(np.sqrt(np.mean(e ** 2))), "mae": float(np.mean(np.abs(e))),
            "region_rmse": dict(zip(REGIONS, np.sqrt(np.mean(e ** 2, axis=0)).tolist())), "n_predictions": int(e.size)}


def summarize(rows: list[dict], panels: list[str]) -> dict:
    out = {}
    for panel in panels:
        out[panel] = {}
        for family in FAMILIES:
            sel = sorted((r for r in rows if r["panel"] == panel and r["family"] == family), key=lambda r: r["index"])
            pred = np.concatenate([np.array(r["pred"]) for r in sel])
            target = np.concatenate([np.array(r["target"]) for r in sel])
            entry = metrics(pred, target)
            entry["hyper_by_task"] = [r["hyper"] for r in sel]
            entry["fallbacks"] = int(sum(r["fallback_rank"] > 0 for r in sel))
            if family == "curved_apl_metric":
                frozen = np.concatenate([np.array(r["pred_frozen_metric"]) for r in sel])
                entry["frozen_metric_ablation"] = metrics(frozen, target)
            out[panel][family] = entry
    return out


def fresh_summary(per_seed: dict) -> dict:
    out = {}
    base = [per_seed[f"fresh:{s}"]["published_constant_spd"] for s in FRESH_SEEDS]
    for family in FAMILIES:
        splits = [per_seed[f"fresh:{s}"][family] for s in FRESH_SEEDS]
        sq = sum(sp["rmse"] ** 2 * sp["n_predictions"] for sp in splits)
        ab = sum(sp["mae"] * sp["n_predictions"] for sp in splits)
        n = sum(sp["n_predictions"] for sp in splits)
        improved = int(sum(sp["rmse"] < b["rmse"] for sp, b in zip(splits, base)))
        out[family] = {"rmse": float(np.sqrt(sq / n)), "mae": float(ab / n), "splits": len(splits),
                       "rmse_improved_vs_reimplemented_baseline": improved,
                       "mae_improved_vs_reimplemented_baseline": int(sum(sp["mae"] < b["mae"] for sp, b in zip(splits, base))),
                       "sign_test_p_one_sided": float(binomtest(improved, len(splits), 0.5, alternative="greater").pvalue),
                       "split_rmse": [sp["rmse"] for sp in splits]}
    return out


def final_model(table: dict) -> dict:
    """Full-cohort fit with hyperparameters chosen by the same inner rule over all seven conditions."""
    full = cohort(table)
    data = {k: full[k] for k in ("x", "y", "sem_x", "sem_y")}
    order, scores = select("curved_apl_metric", data)
    h = order[0]
    model = M.CurvedAPL(*h)
    fitted = model.fit(data)
    states = model.predict(fitted, data["x"])
    betas = M.compartment_betas(*h)
    g0 = fitted["metric"][:6, :6]
    rel = states @ fitted["u"] / fitted["s0"] - 1
    om = M.omega(betas, rel)
    metric_at = [np.outer(o, o) * g0 for o in om]
    ref = g0
    curv = [M.curvature_summary(g0, betas, fitted["u"], fitted["s0"], y) for y in states]
    fd = M.curvature_finite_difference(g0, betas, fitted["u"], fitted["s0"], states[0])
    L, b = fitted["L"], fitted["b"]
    return {"selected_beta_calyx": h[0], "selected_beta_lobes": h[1], "inner_rmse": scores[h],
            "inner_rmse_at_beta0": scores[(0.0, 0.0)], "s0": fitted["s0"], "u": fitted["u"].tolist(),
            "metric_G0": fitted["metric"].tolist(), "mobility_L": L.tolist(), "offset_b": b.tolist(),
            "state_relative_activity": rel.tolist(), "omega_squared_by_state": (om ** 2).tolist(),
            "omega_squared_range": [float((om ** 2).min()), float((om ** 2).max())],
            "metric_relative_variation_max": float(max(np.linalg.norm(m - ref) / np.linalg.norm(ref) for m in metric_at)),
            "curvature_by_state": curv, "finite_difference_scalar_check": {
                "analytic": curv[0]["scalar_curvature"], "finite_difference": fd,
                "abs_diff": abs(curv[0]["scalar_curvature"] - fd)},
            "biology": {"interpretation": "beta_g = I_TRPA - I_ctrl: change of the normalised APL divisive gain",
                        "I_ctrl_literature": list(I_CTRL_RANGE),
                        "implied_I_TRPA_calyx": [I + h[0] for I in I_CTRL_RANGE],
                        "implied_APL_gain_ratio_calyx": [((I + h[0]) / (1 - I - h[0])) / (I / (1 - I))
                                                         if 0 < I + h[0] < 1 else None for I in I_CTRL_RANGE]}}


def baseline_reproduction(table: dict, summary: dict, fresh: dict | None, fresh_previous: dict | None) -> dict:
    rows = read_selected_predictions()
    saved = np.zeros((N_POS, 6))
    for r in rows:
        saved[int(r["position"]) - 1, REGIONS.index(r["region"])] = float(r["candidate"])
    full = cohort(table)
    pred = np.array([M.PublishedSPD().predict(M.PublishedSPD().fit(M.subset(full, [q for q in range(N_POS) if q != p])),
                                              full["x"][p])[0] for p in range(N_POS)])
    saved_metric = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])
    full_metric = M.fit_constant_spd({k: full[k] for k in ("x", "y", "sem_x", "sem_y")})
    pub = json.loads((PUBLICATION / "comparison_summary.json").read_text())
    out = {"leave1_saved_candidate_max_abs_error": float(np.abs(pred - saved).max()),
           "full_fit_metric_max_abs_error": float(np.abs(full_metric - saved_metric).max()), "panels": {}}
    for panel, values in summary.items():
        if panel in pub:
            mine = values["published_constant_spd"]
            out["panels"][panel] = {"reimplemented_rmse": mine["rmse"], "published_rmse": pub[panel]["candidate"]["rmse"],
                                    "reimplemented_mae": mine["mae"], "published_mae": pub[panel]["candidate"]["mae"]}
    if fresh is not None:
        pub_fresh = json.loads((PUBLICATION / "fresh32_summary.json").read_text())
        out["fresh32"] = {"reimplemented_rmse": fresh["published_constant_spd"]["rmse"],
                          "published_rmse": pub_fresh["candidate"]["rmse"],
                          "reimplemented_mae": fresh["published_constant_spd"]["mae"],
                          "published_mae": pub_fresh["candidate"]["mae"], "previous_config": fresh_previous}
    return out


def fresh_previous_counts(table: dict) -> dict:
    prev, cand = [], []
    for seed in FRESH_SEEDS:
        ep, ec = [], []
        for task in fresh_tasks(table, seed):
            for cfg, sink in ((M.PREVIOUS, ep), (M.PUBLISHED, ec)):
                g = M.fit_constant_spd(task["train"], cfg)
                sink.append(M.predict_constant_spd(g, task["test_x"], cfg["power"]) - task["test_y"])
        prev.append(np.concatenate(ep).ravel())
        cand.append(np.concatenate(ec).ravel())
    rp = np.array([np.sqrt(np.mean(e ** 2)) for e in prev])
    rc = np.array([np.sqrt(np.mean(e ** 2)) for e in cand])
    mp = np.array([np.mean(np.abs(e)) for e in prev])
    mc = np.array([np.mean(np.abs(e)) for e in cand])
    allp = np.concatenate(prev)
    return {"previous_rmse": float(np.sqrt(np.mean(allp ** 2))), "previous_mae": float(np.mean(np.abs(allp))),
            "rmse_improved": int((rc < rp).sum()), "mae_improved": int((mc < mp).sum()),
            "both_improved": int(((rc < rp) & (mc < mp)).sum()), "published_counts": [17, 18, 16]}


def criteria(summary: dict, fresh: dict, final: dict) -> dict:
    c = "curved_apl_metric"
    primary = summary["leave1"][c]["rmse"]
    flat_best = min(summary["leave1"]["flat_input_metric"]["rmse"], summary["leave1"]["flat_exponent_force"]["rmse"])
    res = {
        "1_primary_below_baseline": primary < PUBLISHED_BASELINE["leave1"],
        "2_other_panels_not_worse": {p: summary[p][c]["rmse"] <= PUBLISHED_BASELINE[p] for p in ("leave2", "slot0", "slot1")},
        "3_fresh32": {"aggregate_below": fresh[c]["rmse"] < PUBLISHED_BASELINE["fresh32"],
                      "majority_improved": fresh[c]["rmse_improved_vs_reimplemented_baseline"] > len(FRESH_SEEDS) // 2,
                      "sign_test_p_one_sided": fresh[c]["sign_test_p_one_sided"]},
        "4_curvature_contributes": {"beats_beta0_constant_metric": primary < summary["leave1"]["published_constant_spd"]["rmse"],
                                    "beats_best_equal_parameter_flat_counterpart": primary < flat_best,
                                    "beats_frozen_metric_ablation": primary < summary["leave1"][c]["frozen_metric_ablation"]["rmse"]},
        "5_biology": {"beta_calyx_in_literature_range": -I_CTRL_RANGE[1] <= final["selected_beta_calyx"] <= 0.0}}
    flat = [res["1_primary_below_baseline"], *res["2_other_panels_not_worse"].values(),
            res["3_fresh32"]["aggregate_below"], res["3_fresh32"]["majority_improved"],
            *res["4_curvature_contributes"].values(), *res["5_biology"].values()]
    res["verdict"] = "WIN" if all(flat) else "NOT WIN"
    return res


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("development", "confirmation"), required=True)
    parser.add_argument("--workers", type=int, default=11)
    args = parser.parse_args()
    content = CSV_PATH.read_bytes()
    table = load_table()
    code = {name: sha256(HERE / name) for name in CODE_FILES}
    header = {"stage": args.stage, "data": {"path": str(CSV_PATH.relative_to(HERE.parents[1])), "sha256": CSV_SHA256,
                                            "bytes": CSV_BYTES, "git_blob": git_blob_sha1(content),
                                            "quality": quality(table), "target_reproduction": verify_targets(table)},
              "code_sha256": code,
              "grids": {"beta_calyx": BETA_CALYX, "beta_lobes": BETA_LOBES, "p_calyx": P_CALYX, "p_lobes": P_LOBES}}
    if args.stage == "confirmation":
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        frozen = contract["frozen_code_sha256"]
        if frozen != {k: code[k] for k in frozen} or contract["data"]["sha256"] != CSV_SHA256 \
                or contract["grids"] != json.loads(json.dumps(header["grids"])):
            raise SystemExit("contract_v1.json does not match the current code/data/grids; create a new version")
        header["contract_sha256"] = sha256(CONTRACT)
        panels = ["leave1", "leave2", "slot0", "slot1"] + [f"fresh:{s}" for s in FRESH_SEEDS]
    else:
        panels = ["leave1"]
    init_worker()
    jobs = [(p, i, f) for p in panels for i in range(len(tasks_for(p))) for f in FAMILIES]
    start = time.time()
    with Pool(args.workers, initializer=init_worker) as pool:
        rows = pool.map(run_job, jobs, chunksize=1)
    header["elapsed_seconds"] = round(time.time() - start, 1)
    fixed = [p for p in panels if not p.startswith("fresh:")]
    summary = summarize(rows, fixed)
    fresh = fresh_prev = None
    if args.stage == "confirmation":
        per_seed = summarize(rows, [p for p in panels if p.startswith("fresh:")])
        fresh = fresh_summary(per_seed)
        fresh_prev = fresh_previous_counts(table)
    final = final_model(table)
    result = dict(header, panels=summary, fresh32=fresh, final_model=final,
                  baseline_reproduction=baseline_reproduction(table, summary, fresh, fresh_prev),
                  published_baseline=PUBLISHED_BASELINE, published_region_rmse_leave1=PUBLISHED_REGION_RMSE)
    if args.stage == "confirmation":
        result["criteria"] = criteria(summary, fresh, final)
    out = HERE / ("results_development_v1.json" if args.stage == "development" else "results_v1.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    brief = {p: {f: round(v["rmse"], 8) for f, v in summary[p].items()} for p in summary}
    print(json.dumps({"out": out.name, "rmse": brief, "fresh32": None if fresh is None else
                      {f: round(v["rmse"], 8) for f, v in fresh.items()},
                      "verdict": result.get("criteria", {}).get("verdict")}, indent=1))


if __name__ == "__main__":
    main()
