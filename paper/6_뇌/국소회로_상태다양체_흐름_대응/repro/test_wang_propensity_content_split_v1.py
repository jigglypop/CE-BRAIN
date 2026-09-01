from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


RUNNER_PATH = Path(__file__).with_name("run_wang_propensity_content_split_v1.py")
SPEC = importlib.util.spec_from_file_location("wang_split_runner", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {RUNNER_PATH}")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def test_same_cell_rank_series_preserves_nine_paired_vectors() -> None:
    before = np.empty(9, dtype=object)
    after = np.empty(9, dtype=object)
    for index in range(9):
        before[index] = np.asarray([1.0, 2.0, 3.0, 4.0])
        after[index] = np.asarray([1.0, 2.0, 3.0, 4.0]) if index != 8 else np.asarray([4.0, 3.0, 2.0, 1.0])
    result = RUNNER.same_cell_rank_series(
        {"wSI_bef": before, "wSI_aft": after}, "fixture"
    )
    assert len(result["pairs"]) == 9
    assert result["pairs"][0]["same_cell_count"] == 4
    assert result["pairs"][0]["spearman_rho"] == pytest.approx(1.0)
    assert result["pairs"][8]["spearman_rho"] == pytest.approx(-1.0)


def test_content_trend_uses_frozen_pair_coordinates_not_array_ordinal() -> None:
    coordinates = np.asarray([1.0, 2.0, 4.0, 8.0])
    values = 3.0 * coordinates - 2.0
    result = RUNNER.content_stability_trend(
        {"y": values}, "fixture", coordinates
    )
    assert result["pearson_r_vs_pair_start_coordinate"] == pytest.approx(1.0)
    with pytest.raises(RUNNER.ReproductionBlocked, match="coordinates mismatch"):
        RUNNER.content_stability_trend({"y": values}, "fixture", coordinates[:-1])


def test_published_summary_crosscheck_reports_best_order_without_inference() -> None:
    juvenile = np.asarray([0.1, 0.2])
    adult = np.asarray([0.3, 0.4])
    result = RUNNER._summary_crosscheck(
        {"y": np.concatenate([adult, juvenile])}, juvenile, adult
    )
    assert result["available"] is True
    assert result["best_order"] == "adult_then_juvenile"
    assert result["max_absolute_difference"] == 0.0
