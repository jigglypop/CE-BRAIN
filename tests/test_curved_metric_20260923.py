"""Saved-number and re-fit checks for the pre-registered curved-metric test (research/ce_brain_curved_metric_20260923)."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1] / "research" / "ce_brain_curved_metric_20260923"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kc = _load("kc_data")
M = _load("metric_models")
CONTRACT = json.loads((HERE / "contract_v1.json").read_text(encoding="utf-8"))
RESULTS = json.loads((HERE / "results_v1.json").read_text(encoding="utf-8"))
needs_csv = pytest.mark.skipif(not kc.CSV_PATH.exists(), reason="data/external is gitignored; download the pinned CSV")


def test_contract_froze_the_code_and_data_that_produced_results():
    for name, digest in CONTRACT["frozen_code_sha256"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest
        assert RESULTS["code_sha256"][name] == digest
    assert RESULTS["contract_sha256"] == hashlib.sha256((HERE / "contract_v1.json").read_bytes()).hexdigest()
    assert CONTRACT["data"]["sha256"] == kc.CSV_SHA256 == RESULTS["data"]["sha256"]


def test_verdict_follows_from_saved_numbers():
    base = CONTRACT["baseline"]["published_rmse"]
    curved = {p: RESULTS["panels"][p]["curved_apl_metric"]["rmse"] for p in ("leave1", "leave2", "slot0", "slot1")}
    assert curved["leave1"] < base["leave1"]
    assert curved["leave2"] <= base["leave2"] and curved["slot0"] <= base["slot0"]
    assert curved["slot1"] > base["slot1"]
    fresh = RESULTS["fresh32"]["curved_apl_metric"]
    assert fresh["rmse"] < base["fresh32"] and fresh["rmse_improved_vs_reimplemented_baseline"] == 21
    assert RESULTS["criteria"]["verdict"] == "NOT WIN"


@needs_csv
def test_baseline_reimplementation_matches_published_predictions():
    table = kc.load_table()
    full = kc.cohort(table)
    with (kc.PUBLICATION / "selected_predictions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    saved = np.zeros((7, 6))
    for r in rows:
        saved[int(r["position"]) - 1, kc.REGIONS.index(r["region"])] = float(r["candidate"])
    model = M.PublishedSPD()
    pred = np.array([model.predict(model.fit(M.subset(full, [q for q in range(7) if q != p])), full["x"][p])[0]
                     for p in range(7)])
    assert np.abs(pred - saved).max() < 5e-7
    assert np.sqrt(np.mean((pred - full["y"]) ** 2)) == pytest.approx(
        RESULTS["panels"]["leave1"]["published_constant_spd"]["rmse"], abs=1e-12)


@needs_csv
def test_curved_refit_with_saved_hyperparameters_reproduces_primary_panel():
    tasks = kc.panel_tasks(kc.load_table(), "leave1")
    hypers = RESULTS["panels"]["leave1"]["curved_apl_metric"]["hyper_by_task"]
    pred = np.concatenate([M.CurvedAPL(*h).predict(M.CurvedAPL(*h).fit(t["train"]), t["test_x"])
                           for h, t in zip(hypers, tasks)])
    target = np.concatenate([t["test_y"] for t in tasks])
    assert np.sqrt(np.mean((pred - target) ** 2)) == pytest.approx(
        RESULTS["panels"]["leave1"]["curved_apl_metric"]["rmse"], abs=1e-10)
    flat = M.CurvedAPL(0.0, 0.0)
    task = tasks[0]
    np.testing.assert_allclose(flat.predict(flat.fit(task["train"]), task["test_x"]),
                               M.PublishedSPD().predict(M.PublishedSPD().fit(task["train"]), task["test_x"]), atol=1e-12)


def test_curvature_tensor_against_finite_differences_and_limits():
    rng = np.random.default_rng(3)
    a = rng.normal(size=(6, 6))
    g0 = a @ a.T + 6 * np.eye(6)
    u = np.ones(6) / np.sqrt(6)
    y = rng.uniform(0.1, 0.5, 6)
    betas = M.compartment_betas(-0.65, 0.0)
    analytic = M.curvature_summary(g0, betas, u, 0.4, y)["scalar_curvature"]
    assert analytic == pytest.approx(M.curvature_finite_difference(g0, betas, u, 0.4, y), rel=1e-6)
    assert M.curvature_summary(g0, np.zeros(6), u, 0.4, y)["riemann_frobenius"] == 0.0
    conformal = M.curvature_summary(np.eye(6), np.full(6, 0.4), u, 0.5, y)
    assert abs(conformal["scalar_curvature"]) < 1e-12 and conformal["ricci_frobenius"] > 0.1
