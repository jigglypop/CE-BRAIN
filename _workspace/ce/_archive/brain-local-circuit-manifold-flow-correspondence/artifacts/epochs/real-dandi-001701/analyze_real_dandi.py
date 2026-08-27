"""Preregistered, one-session DANDI 001701 affine-fiber analysis.

The script deliberately keeps the test-bin array unmaterialized until the
development selection is locked.  It writes only aggregate JSON/receipt files
next to this script and removes the verified NWB temporary file in ``finally``.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import tempfile
from pathlib import Path

import h5py
import numpy as np
import pandas as pd  # Required analysis environment dependency; no pandas object is persisted.
import requests


DANDISET = "001701"
VERSION = "0.260120.0303"
ASSET_ID = "3f3d0b16-9b3e-42ac-a5e6-327829df1116"
ASSET_PATH = "sub-BaggySweatpants/sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1_behavior+ecephys.nwb"
EXPECTED_SIZE = 12_967_760
EXPECTED_SHA256 = "5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3"
BIN_SECONDS = 0.1
RIDGES = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0)
BOOTSTRAPS = 2000
BLOCK = 100
SEED = 1701
HERE = Path(__file__).resolve().parent


def jsonable(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def fail(code: str, detail: str, receipt: dict | None = None) -> None:
    payload = {"status": "FAIL", "failure_code": code, "detail": detail, "claim_ceiling": "No positive empirical bridge."}
    (HERE / "result.json").write_text(json.dumps(jsonable(payload), indent=2) + "\n", encoding="utf-8")
    if receipt is not None:
        (HERE / "source-receipt.json").write_text(json.dumps(jsonable(receipt), indent=2) + "\n", encoding="utf-8")
    raise RuntimeError(f"{code}: {detail}")


def text_attr(value) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def get_asset_url() -> tuple[str, dict]:
    api = f"https://api.dandiarchive.org/api/dandisets/{DANDISET}/versions/{VERSION}/assets/{ASSET_ID}/"
    response = requests.get(api, timeout=60)
    response.raise_for_status()
    metadata = response.json()
    urls = metadata.get("contentUrl", [])
    if not urls:
        raise RuntimeError("asset metadata has no contentUrl")
    return urls[0], {"asset_api": api, "metadata": metadata}


def download_verified(destination: Path) -> dict:
    url, receipt = get_asset_url()
    digest = hashlib.sha256()
    received = 0
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
    actual = digest.hexdigest()
    receipt.update({"download_url": url, "bytes_received": received, "sha256": actual, "expected_bytes": EXPECTED_SIZE, "expected_sha256": EXPECTED_SHA256})
    if received != EXPECTED_SIZE or actual != EXPECTED_SHA256:
        raise RuntimeError(f"receipt mismatch: bytes={received}, sha256={actual}")
    return receipt


def electrical_coverage(nwb: h5py.File) -> tuple[float, float, list[tuple[float, float]], dict]:
    candidates = []
    def visitor(name, obj):
        if isinstance(obj, h5py.Group) and text_attr(obj.attrs.get("neurodata_type", "")) == "ElectricalSeries":
            candidates.append((name, obj))
    nwb.visititems(visitor)
    if not candidates:
        raise ValueError("COVERAGE_UNAVAILABLE: no ElectricalSeries")
    name, series = candidates[0]
    if "timestamps" in series:
        stamps = np.asarray(series["timestamps"], dtype=float)
        if stamps.size < 2:
            raise ValueError("COVERAGE_UNAVAILABLE: fewer than two timestamps")
        gaps = np.flatnonzero(np.diff(stamps) > 0.15)
        bounds = np.r_[0, gaps + 1, stamps.size - 1]
        segments = [(float(stamps[bounds[i]]), float(stamps[bounds[i + 1]])) for i in range(len(bounds) - 1)]
        return float(stamps[0]), float(stamps[-1]), segments, {"series": name, "mode": "timestamps", "timestamp_gaps_over_150ms": int(gaps.size)}
    if "starting_time" in series and "rate" in series["starting_time"].attrs:
        start = float(np.asarray(series["starting_time"])[()])
        rate = float(series["starting_time"].attrs["rate"])
        if rate <= 0 or "data" not in series:
            raise ValueError("COVERAGE_UNAVAILABLE: invalid implicit timing")
        stop = start + (len(series["data"]) - 1) / rate
        return start, stop, [(start, stop)], {"series": name, "mode": "starting_time_rate", "timestamp_gaps_over_150ms": 0, "rate_hz": rate}
    raise ValueError("COVERAGE_UNAVAILABLE: ElectricalSeries timing absent")


def prefix_unit_statistics(spikes: h5py.Dataset, indexes: np.ndarray, start: float, prefix_stop: float) -> tuple[np.ndarray, float | None]:
    """Frozen masking only: decode vectors, but admit no event at/after prefix_stop."""
    begins = np.r_[0, indexes[:-1]]
    counts = np.zeros(indexes.size, dtype=np.int64)
    admitted_max = None
    for unit in range(indexes.size):
        times = np.asarray(spikes[int(begins[unit]):int(indexes[unit])], dtype=float)
        admitted = times[(times >= start) & (times < prefix_stop)]
        counts[unit] = admitted.size
        if admitted.size:
            candidate = float(admitted.max())
            admitted_max = candidate if admitted_max is None else max(admitted_max, candidate)
    return counts, admitted_max


def bins_for_interval(spikes: h5py.Dataset, indexes: np.ndarray, retained: np.ndarray, start: float, stop: float, n_bins: int) -> tuple[np.ndarray, float | None]:
    counts = np.zeros((n_bins, retained.size), dtype=np.float64)
    begins = np.r_[0, indexes[:-1]]
    admitted_max = None
    for output, unit in enumerate(retained):
        times = np.asarray(spikes[int(begins[unit]):int(indexes[unit])], dtype=float)
        times = times[(times >= start) & (times < stop)]
        if times.size:
            candidate = float(times.max())
            admitted_max = candidate if admitted_max is None else max(admitted_max, candidate)
        indices = np.floor((times - start) / BIN_SECONDS).astype(np.int64)
        indices = indices[(indices >= 0) & (indices < n_bins)]
        if indices.size:
            counts[:, output] = np.bincount(indices, minlength=n_bins)
    return counts, admitted_max


def valid_rows(block: tuple[int, int], segment_ids: np.ndarray, horizon: int = 1, lag: int = 0) -> np.ndarray:
    begin, end = block
    rows = np.arange(begin + lag, end - horizon, dtype=np.int64)
    if lag:
        rows = rows[(rows - lag >= begin)]
    return rows[(segment_ids[rows] >= 0) & (segment_ids[rows] == segment_ids[rows + horizon]) & ((lag == 0) | (segment_ids[rows] == segment_ids[rows - lag]))]


def ridge(x: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray]:
    xmean, ymean = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - xmean, y - ymean
    gram = xc.T @ xc + lam * np.eye(x.shape[1])
    coefficient = np.linalg.solve(gram, xc.T @ yc)
    return coefficient, ymean - xmean @ coefficient


def predict(coefficient: np.ndarray, intercept: np.ndarray, x: np.ndarray) -> np.ndarray:
    return x @ coefficient + intercept


def pca(train_x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    _, _, vt = np.linalg.svd(train_x, full_matrices=False)
    return vt.T, vt


def fit_affine(x: np.ndarray, rows: np.ndarray, basis: np.ndarray, d: int, lam: float) -> dict:
    z, y = x @ basis[:, :d], x @ basis[:, d:]
    base_b, base_d = ridge(z[rows], z[rows + 1], lam)
    fiber_coef, fiber_e = ridge(np.c_[y[rows], z[rows]], y[rows + 1], lam)
    return {"basis": basis, "d": d, "lambda": lam, "B": base_b, "base_intercept": base_d, "A": fiber_coef[: y.shape[1]], "C": fiber_coef[y.shape[1] :], "fiber_intercept": fiber_e}


def affine_predict(model: dict, x: np.ndarray, rows: np.ndarray) -> np.ndarray:
    basis, d = model["basis"], model["d"]
    z, y = x @ basis[:, :d], x @ basis[:, d:]
    next_z = predict(model["B"], model["base_intercept"], z[rows])
    next_y = predict(np.vstack((model["A"], model["C"])), model["fiber_intercept"], np.c_[y[rows], z[rows]])
    return next_z @ basis[:, :d].T + next_y @ basis[:, d:].T


def fit_base_only(x: np.ndarray, rows: np.ndarray, basis: np.ndarray, d: int, lam: float) -> dict:
    z, y = x @ basis[:, :d], x @ basis[:, d:]
    b, bd = ridge(z[rows], z[rows + 1], lam)
    c, e = ridge(z[rows], y[rows + 1], lam)
    return {"basis": basis, "d": d, "B": b, "base_intercept": bd, "C": c, "fiber_intercept": e}


def base_predict(model: dict, x: np.ndarray, rows: np.ndarray) -> np.ndarray:
    basis, d = model["basis"], model["d"]
    z = x @ basis[:, :d]
    next_z = predict(model["B"], model["base_intercept"], z[rows])
    next_y = predict(model["C"], model["fiber_intercept"], z[rows])
    return next_z @ basis[:, :d].T + next_y @ basis[:, d:].T


def nmse(target: np.ndarray, estimate: np.ndarray, denominator: float) -> float:
    return float(np.square(target - estimate).sum() / denominator)


def select_models(x: np.ndarray, train_rows: np.ndarray, dev_rows: np.ndarray, basis: np.ndarray) -> tuple[dict, dict, list[dict]]:
    candidates = []
    max_d = min(8, x.shape[1] - 1)
    for d in (2, 4, 8):
        if d >= min(9, x.shape[1]) or d > max_d:
            continue
        for lam in RIDGES:
            model = fit_affine(x, train_rows, basis, d, lam)
            score = nmse(x[dev_rows + 1], affine_predict(model, x, dev_rows), 1.0)
            candidates.append({"model": model, "development_sse": score, "d": d, "lambda": lam})
    if not candidates:
        raise ValueError("INSUFFICIENT_UNITS_FOR_CANDIDATES")
    candidates.sort(key=lambda item: (item["development_sse"], item["d"], -item["lambda"]))
    affine = candidates[0]["model"]
    full = []
    for lam in RIDGES:
        coef, intercept = ridge(x[train_rows], x[train_rows + 1], lam)
        full.append({"coefficient": coef, "intercept": intercept, "lambda": lam, "development_sse": nmse(x[dev_rows + 1], predict(coef, intercept, x[dev_rows]), 1.0)})
    full.sort(key=lambda item: (item["development_sse"], -item["lambda"]))
    return affine, full[0], candidates


def bootstrap(diff: np.ndarray, rows: np.ndarray) -> dict:
    runs, start = [], 0
    for index in range(1, rows.size + 1):
        if index == rows.size or rows[index] != rows[index - 1] + 1:
            if index - start >= BLOCK:
                runs.extend(diff[left:left + BLOCK] for left in range(start, index - BLOCK + 1))
            start = index
    if len(runs) < 3 or diff.size < 300:
        return {"status": "INSUFFICIENT_TEST_BLOCKS", "n_rows": int(diff.size), "n_candidate_blocks": len(runs)}
    rng = np.random.default_rng(SEED)
    draws = np.array([np.concatenate([runs[index] for index in rng.integers(0, len(runs), size=math.ceil(diff.size / BLOCK))])[: diff.size].mean() for _ in range(BOOTSTRAPS)])
    return {"status": "OK", "mean_improvement": float(diff.mean()), "ci95": [float(np.quantile(draws, .025)), float(np.quantile(draws, .975))], "n_rows": int(diff.size), "n_candidate_blocks": len(runs)}


def main() -> None:
    temp = Path(tempfile.mkdtemp(prefix="ce-dandi-001701-"))
    receipt = {"dandiset": DANDISET, "version": VERSION, "asset_id": ASSET_ID, "asset_path": ASSET_PATH, "downloaded": False, "nwb_deleted": False}
    try:
        nwb_path = temp / "source.nwb"
        receipt.update(download_verified(nwb_path))
        receipt["downloaded"] = True
        with h5py.File(nwb_path, "r") as nwb:
            start, stop, segments, coverage = electrical_coverage(nwb)
            if stop <= start:
                fail("COVERAGE_UNAVAILABLE", "non-positive coverage interval", receipt)
            if "units/spike_times" not in nwb or "units/spike_times_index" not in nwb:
                fail("UNITS_UNAVAILABLE", "NWB lacks units spike_times/index", receipt)
            spikes, indexes = nwb["units/spike_times"], np.asarray(nwb["units/spike_times_index"], dtype=np.int64)
            duration = stop - start
            n_bins = int(math.floor(duration / BIN_SECONDS))
            train_end, dev_end = int(math.floor(.5 * n_bins)), int(math.floor(.75 * n_bins))
            train_boundary = start + train_end * BIN_SECONDS
            test_boundary = start + dev_end * BIN_SECONDS
            test_materialized = False
            retention_events, retention_event_max = prefix_unit_statistics(spikes, indexes, start, train_boundary)
            if retention_event_max is not None:
                assert retention_event_max < train_boundary, "post-train event admitted to retention statistics"
            retained = np.flatnonzero(retention_events / (train_boundary - start) >= 0.1)
            if retained.size < 3 or n_bins < 20:
                fail("INSUFFICIENT_DATA", f"retained_units={retained.size}, bins={n_bins}", receipt)
            segment_ids = np.full(n_bins, -1, dtype=np.int64)
            for segment, (left, right) in enumerate(segments):
                first = max(0, int(math.ceil((left - start) / BIN_SECONDS)))
                last = min(n_bins, int(math.floor((right - start) / BIN_SECONDS)))
                segment_ids[first:last] = segment
            blocks = {"train": (0, train_end), "development": (train_end, dev_end), "test": (dev_end, n_bins)}
            # Only train/development arrays exist before the lock below.
            train_dev_counts, prefix_bin_event_max = bins_for_interval(spikes, indexes, retained, start, test_boundary, dev_end)
            assert train_dev_counts.shape[0] == dev_end, "prefix count matrix must stop exactly at development end"
            if prefix_bin_event_max is not None:
                assert prefix_bin_event_max < test_boundary, "post-test event admitted to prefix counts"
            preselection_audit = {"retention_scope": "train_only", "retention_boundary_seconds": train_boundary, "max_event_admitted_to_retention_count": retention_event_max, "test_boundary_seconds": test_boundary, "max_admitted_prefix_event_time": prefix_bin_event_max, "prefix_shape": list(train_dev_counts.shape), "prefix_rows_equal_development_end": bool(train_dev_counts.shape[0] == dev_end), "no_test_derived_array_or_stat_before_model_selected": True}
            transformed = np.sqrt(train_dev_counts + 3.0 / 8.0)
            train_mean, train_scale = transformed[:train_end].mean(axis=0), transformed[:train_end].std(axis=0, ddof=0)
            train_scale[train_scale == 0] = 1.0
            x_prefix = (transformed - train_mean) / train_scale
            train_rows, dev_rows = valid_rows(blocks["train"], segment_ids), valid_rows(blocks["development"], segment_ids)
            if train_rows.size < 2 or dev_rows.size < 2:
                fail("INSUFFICIENT_ROWS", f"train={train_rows.size}, development={dev_rows.size}", receipt)
            basis, _ = pca(x_prefix[:train_end])
            affine, full_var, candidates = select_models(x_prefix, train_rows, dev_rows, basis)
            assert not test_materialized, "test-derived array/statistic exists before model selection"
            model_selected = True
            assert model_selected and x_prefix.shape[0] == dev_end, "test bins materialized before selection"
            # Now, and only now, decode the remaining physical bins.
            all_counts, _ = bins_for_interval(spikes, indexes, retained, start, start + n_bins * BIN_SECONDS, n_bins)
            test_materialized = True
        x = (np.sqrt(all_counts + 3.0 / 8.0) - train_mean) / train_scale
        test_rows = valid_rows(blocks["test"], segment_ids)
        train_bin_mean = x[:train_end].mean(axis=0)
        denominator = float(np.square(x[test_rows + 1] - train_bin_mean).sum())
        if denominator <= 0:
            fail("UNDEFINED_DENOMINATOR", "train target variance is zero", receipt)
        affine_estimate = affine_predict(affine, x, test_rows)
        full_estimate = predict(full_var["coefficient"], full_var["intercept"], x[test_rows])
        base = fit_base_only(x, train_rows, basis, affine["d"], affine["lambda"])
        base_estimate = base_predict(base, x, test_rows)
        targets = x[test_rows + 1]
        errors = {"affine_fiber": np.square(targets - affine_estimate).sum(axis=1), "full_var": np.square(targets - full_estimate).sum(axis=1), "base_only": np.square(targets - base_estimate).sum(axis=1), "persistence": np.square(targets - x[test_rows]).sum(axis=1), "train_mean": np.square(targets - x[train_rows + 1].mean(axis=0)).sum(axis=1)}
        scores = {name: float(values.sum() / denominator) for name, values in errors.items()}
        try:
            kappa = float(np.linalg.norm(np.linalg.inv(affine["B"]), 2))
        except np.linalg.LinAlgError:
            kappa = math.inf
        q = float(np.linalg.norm(affine["A"], 2))
        hcoef, hintercept = ridge((x @ basis[:, :affine["d"]])[train_rows], (x @ basis[:, affine["d"]:])[train_rows], 1e-2)
        z, y = x @ basis[:, :affine["d"]], x @ basis[:, affine["d"]:]
        graph_left = predict(hcoef, hintercept, predict(affine["B"], affine["base_intercept"], z[test_rows]))
        graph_right = predict(np.vstack((affine["A"], affine["C"])), affine["fiber_intercept"], np.c_[predict(hcoef, hintercept, z[test_rows]), z[test_rows]])
        invariant_den = float(np.square(y[test_rows + 1]).sum())
        invariant = "UNDEFINED" if invariant_den == 0 else float(np.square(graph_left - graph_right).sum() / invariant_den)
        horizons = {}
        for horizon in (1, 2, 5, 10):
            rows = valid_rows(blocks["test"], segment_ids, horizon=horizon)
            current = x[rows].copy()
            for _ in range(horizon):
                current = affine_predict(affine, np.vstack((current, current)), np.arange(current.shape[0])) if False else current
                zz, yy = current @ basis[:, :affine["d"]], current @ basis[:, affine["d"]:]
                current = predict(affine["B"], affine["base_intercept"], zz) @ basis[:, :affine["d"]].T + predict(np.vstack((affine["A"], affine["C"])), affine["fiber_intercept"], np.c_[yy, zz]) @ basis[:, affine["d"]:].T
            horizons[str(horizon)] = {"rows": int(rows.size), "nmse": nmse(x[rows + horizon], current, denominator)}
        shifted_train, shifted_dev, shifted_test = (valid_rows(blocks[name], segment_ids, lag=100) for name in ("train", "development", "test"))
        # These fit rows encode (x[t-100], x[t+1]) by temporarily mapping row r to target r+101.
        # Refit explicitly so the target convention is exact.
        def fit_shift_affine(d, lam, rows):
            z0, y0 = x @ basis[:, :d], x @ basis[:, d:]
            b, bd = ridge(z0[rows - 100], z0[rows + 1], lam)
            fc, fe = ridge(np.c_[y0[rows - 100], z0[rows - 100]], y0[rows + 1], lam)
            return {"basis": basis, "d": d, "lambda": lam, "B": b, "base_intercept": bd, "A": fc[:y0.shape[1]], "C": fc[y0.shape[1]:], "fiber_intercept": fe}
        shifted_candidates = []
        for d in (2, 4, 8):
            if d >= min(9, x.shape[1]):
                continue
            for lam in RIDGES:
                model = fit_shift_affine(d, lam, shifted_train)
                estimate = affine_predict(model, x, shifted_dev - 100)
                shifted_candidates.append((nmse(x[shifted_dev + 1], estimate, 1.0), d, lam, model))
        shifted_candidates.sort(key=lambda item: (item[0], item[1], -item[2]))
        shifted_model = shifted_candidates[0][3]
        shifted_estimate = affine_predict(shifted_model, x, shifted_test - 100)
        reduced_real = affine_predict(affine, x, shifted_test)
        reduced_targets = x[shifted_test + 1]
        shifted_score = nmse(reduced_targets, shifted_estimate, denominator)
        reduced_real_score = nmse(reduced_targets, reduced_real, denominator)
        boot_persistence = bootstrap(errors["persistence"] - errors["affine_fiber"], test_rows)
        boot_full = bootstrap(errors["full_var"] - errors["affine_fiber"], test_rows)
        improvement_persistence = 1.0 - scores["affine_fiber"] / scores["persistence"] if scores["persistence"] else math.nan
        improvement_full = 1.0 - scores["affine_fiber"] / scores["full_var"] if scores["full_var"] else math.nan
        positive = (q < 1 and q * kappa < 1 and improvement_persistence >= .01 and improvement_full >= .01 and boot_persistence.get("ci95", [-math.inf])[0] > 0 and boot_full.get("ci95", [-math.inf])[0] > 0 and shifted_score > reduced_real_score)
        result = {"status": "PASS" if positive else "FAIL", "claim_ceiling": "L2 single-session observational model adequacy only" if positive else "No positive empirical bridge.", "source": {"dandiset": DANDISET, "version": VERSION, "asset": ASSET_PATH}, "coverage": coverage, "duration_seconds": duration, "retained_units": int(retained.size), "bins": int(n_bins), "valid_rows": {name: int(valid_rows(block, segment_ids).size) for name, block in blocks.items()}, "train_variance_denominator": denominator, "nmse_denominator_mean_scope": "all train bins x[0:train_end]", "preselection_audit": preselection_audit, "selected_affine": {"d": affine["d"], "lambda": affine["lambda"]}, "selected_full_var_lambda": full_var["lambda"], "scores_nmse": scores, "improvement": {"over_persistence": improvement_persistence, "over_full_var": improvement_full}, "bootstrap": {"persistence": boot_persistence, "full_var": boot_full}, "certificates": {"q": q, "kappa": kappa, "q_kappa": q * kappa}, "secondary_invariant_residual": invariant, "multi_step_nmse": horizons, "shifted_control": {"rows": int(shifted_test.size), "real_rescored_nmse": reduced_real_score, "shifted_refit_nmse": shifted_score, "passes_falsifier": shifted_score > reduced_real_score}, "test_materialized_after_selection": test_materialized, "candidate_count": len(candidates), "pandas_version": pd.__version__}
        (HERE / "result.json").write_text(json.dumps(jsonable(result), indent=2, allow_nan=False) + "\n", encoding="utf-8")
        receipt["decode"] = {"coverage": coverage, "retained_units": int(retained.size), "n_bins": int(n_bins), "retention_scope": "train_only", "retention_boundary_seconds": train_boundary, "max_event_admitted_to_retention_count": retention_event_max}
        (HERE / "source-receipt.json").write_text(json.dumps(jsonable(receipt), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable({"status": result["status"], "retained_units": retained.size, "scores_nmse": scores, "certificates": result["certificates"]}), indent=2))
    except Exception as error:
        receipt["error"] = repr(error)
        (HERE / "source-receipt.json").write_text(json.dumps(jsonable(receipt), indent=2) + "\n", encoding="utf-8")
        if not (HERE / "result.json").exists():
            (HERE / "result.json").write_text(json.dumps({"status": "FAIL", "failure_code": "EXECUTION_ERROR", "detail": repr(error), "claim_ceiling": "No positive empirical bridge."}, indent=2) + "\n", encoding="utf-8")
        raise
    finally:
        if temp.exists():
            shutil.rmtree(temp)
            receipt["nwb_deleted"] = True
            (HERE / "source-receipt.json").write_text(json.dumps(jsonable(receipt), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
