"""Preregistered R2 behavior-state local-bundle analysis on DANDI 001701.

This is outcome-informed single-session development.  It never opens DANDI
001695 and it does not interpret a predictive chart as a biological manifold.
"""

from __future__ import annotations

import importlib.util
import json
import math
import shutil
import tempfile
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
EPOCHS = HERE.parents[2]
R1_PATH = (
    EPOCHS
    / "real-global-affine-fiber-fail"
    / "pivots"
    / "r1-behavior-controlled-fiber"
    / "analyze_behavior_pivot.py"
)
CHARTS = 4
DIMENSIONS = (2, 4, 8)
SHIFT_BINS = 100
MIN_SPLIT_ROWS = 100
MAX_LLOYD_STEPS = 100
RIDGES = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0)

behavior = None
core = None


def load_predecessors() -> None:
    global behavior, core
    if behavior is not None:
        return
    spec = importlib.util.spec_from_file_location("r2_predecessor_behavior", R1_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    behavior = module
    core = module.core


def jsonable(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def ridge(x: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray]:
    xmean, ymean = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - xmean, y - ymean
    coefficient = np.linalg.solve(xc.T @ xc + lam * np.eye(x.shape[1]), xc.T @ yc)
    return coefficient, ymean - xmean @ coefficient


def predict(coefficient: np.ndarray, intercept: np.ndarray, x: np.ndarray) -> np.ndarray:
    return x @ coefficient + intercept


def nmse(target: np.ndarray, estimate: np.ndarray, denominator: float) -> float:
    return float(np.square(target - estimate).sum() / denominator)


def pca(train_x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    _, _, vt = np.linalg.svd(train_x, full_matrices=False)
    return vt.T, vt


def write_json(name: str, value: dict) -> None:
    (HERE / name).write_text(
        json.dumps(jsonable(value), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def assign_charts(phi: np.ndarray, centers: np.ndarray) -> np.ndarray:
    labels = np.full(phi.shape[0], -1, dtype=np.int64)
    valid = np.isfinite(phi).all(axis=1)
    if valid.any():
        distance = np.square(phi[valid, None, :] - centers[None, :, :]).sum(axis=2)
        labels[valid] = np.argmin(distance, axis=1)
    return labels


def fit_behavior_charts(
    phi: np.ndarray,
    rows: np.ndarray,
    charts: int = CHARTS,
    max_steps: int = MAX_LLOYD_STEPS,
) -> tuple[np.ndarray, dict]:
    samples = np.asarray(phi[rows], dtype=float)
    if samples.ndim != 2 or samples.shape[0] < charts or not np.isfinite(samples).all():
        raise ValueError("CHART_INPUT_INVALID")
    mean = samples.mean(axis=0)
    first = int(np.argmin(np.square(samples - mean).sum(axis=1)))
    selected = [first]
    while len(selected) < charts:
        distance = np.square(samples[:, None, :] - samples[selected][None, :, :]).sum(axis=2)
        nearest = distance.min(axis=1)
        nearest[selected] = -math.inf
        selected.append(int(np.argmax(nearest)))
    centers = samples[selected].copy()

    previous = None
    converged_at = None
    for step in range(1, max_steps + 1):
        labels = assign_charts(samples, centers)
        if previous is not None and np.array_equal(labels, previous):
            converged_at = step
            break
        if np.any(labels < 0) or any(not np.any(labels == chart) for chart in range(charts)):
            raise ValueError("EMPTY_CHART")
        centers = np.vstack([samples[labels == chart].mean(axis=0) for chart in range(charts)])
        previous = labels
    if converged_at is None:
        labels = assign_charts(samples, centers)
        if previous is None or not np.array_equal(labels, previous):
            raise ValueError("CHART_NOT_CONVERGED")
        converged_at = max_steps

    order = np.lexsort(tuple(centers[:, column] for column in reversed(range(centers.shape[1]))))
    centers = centers[order]
    counts = np.bincount(assign_charts(samples, centers), minlength=charts)
    return centers, {
        "algorithm": "deterministic_farthest_first_lloyd",
        "charts": charts,
        "iterations": converged_at,
        "train_assignment_counts": counts,
    }


def support_audit(
    labels: np.ndarray,
    rows_by_split: dict[str, np.ndarray],
    n_units: int,
    charts: int = CHARTS,
) -> dict:
    counts = {
        split: [int(np.sum(labels[rows] == chart)) for chart in range(charts)]
        for split, rows in rows_by_split.items()
    }
    required = {
        "train_strictly_greater_than": n_units + 7,
        "development_at_least": MIN_SPLIT_ROWS,
        "evaluation_at_least": MIN_SPLIT_ROWS,
    }
    passes = all(value > n_units + 7 for value in counts.get("train", []))
    if "development" in counts:
        passes = passes and all(value >= MIN_SPLIT_ROWS for value in counts["development"])
    if "evaluation" in counts:
        passes = passes and all(value >= MIN_SPLIT_ROWS for value in counts["evaluation"])
    return {"passes": bool(passes), "counts": counts, "required": required}


def prepare_geometry(
    x: np.ndarray,
    rows: np.ndarray,
    labels: np.ndarray,
    charts: int,
) -> list[dict]:
    geometry = []
    for chart in range(charts):
        selected = rows[labels[rows] == chart]
        if selected.size < 2:
            raise ValueError(f"INSUFFICIENT_GEOMETRY_ROWS:{chart}:{selected.size}")
        mean = x[selected].mean(axis=0)
        _, _, vt = np.linalg.svd(x[selected] - mean, full_matrices=False)
        geometry.append({"mean": mean, "basis": vt.T, "train_rows": int(selected.size)})
    return geometry


def fit_diagonal_fiber(
    features: np.ndarray,
    residual: np.ndarray,
    target: np.ndarray,
    lam: float,
) -> dict:
    feature_mean = features.mean(axis=0)
    residual_mean = residual.mean(axis=0)
    target_mean = target.mean(axis=0)
    fc = features - feature_mean
    rc = residual - residual_mean
    tc = target - target_mean
    gram = fc.T @ fc + lam * np.eye(fc.shape[1])
    feature_target = fc.T @ tc
    feature_residual = fc.T @ rc
    base = np.linalg.solve(gram, feature_target)
    residual_path = np.linalg.solve(gram, feature_residual)
    denominator = np.square(rc).sum(axis=0) + lam - np.sum(feature_residual * residual_path, axis=0)
    numerator = np.sum(rc * tc, axis=0) - np.sum(feature_residual * base, axis=0)
    if np.any(denominator <= 0) or not np.isfinite(denominator).all():
        raise ValueError("FIBER_SCHUR_NOT_POSITIVE")
    diagonal = numerator / denominator
    coefficient = base - residual_path * diagonal[None, :]
    intercept = target_mean - feature_mean @ coefficient - residual_mean * diagonal
    return {"coefficient": coefficient, "diagonal": diagonal, "intercept": intercept}


def fit_local_bundle(
    x: np.ndarray,
    phi: np.ndarray,
    rows: np.ndarray,
    labels: np.ndarray,
    geometry: list[dict],
    d: int,
    lam: float,
) -> dict:
    fits = []
    for chart, item in enumerate(geometry):
        selected = rows[labels[rows] == chart]
        basis = item["basis"][:, :d]
        mean = item["mean"]
        current = x[selected] - mean
        target = x[selected + 1] - mean
        z = current @ basis
        next_z = target @ basis
        residual = current - z @ basis.T
        next_residual = target - next_z @ basis.T
        features = np.c_[z, phi[selected]]
        base_coefficient, base_intercept = ridge(features, next_z, lam)
        fiber = fit_diagonal_fiber(features, residual, next_residual, lam)
        fits.append(
            {
                "mean": mean,
                "basis": basis,
                "base_coefficient": base_coefficient,
                "base_intercept": base_intercept,
                "fiber": fiber,
                "fit_rows": int(selected.size),
            }
        )
    return {"d": d, "lambda": lam, "charts": fits, "geometry": geometry}


def local_bundle_predict(
    model: dict,
    x: np.ndarray,
    phi: np.ndarray,
    rows: np.ndarray,
    labels: np.ndarray,
) -> np.ndarray:
    estimate = np.empty((rows.size, x.shape[1]), dtype=float)
    for chart, fit in enumerate(model["charts"]):
        positions = np.flatnonzero(labels[rows] == chart)
        if positions.size == 0:
            continue
        selected = rows[positions]
        basis, mean = fit["basis"], fit["mean"]
        current = x[selected] - mean
        z = current @ basis
        residual = current - z @ basis.T
        features = np.c_[z, phi[selected]]
        next_z = predict(fit["base_coefficient"], fit["base_intercept"], features)
        fiber = fit["fiber"]
        next_residual = (
            features @ fiber["coefficient"]
            + residual * fiber["diagonal"]
            + fiber["intercept"]
        )
        next_residual -= (next_residual @ basis) @ basis.T
        estimate[positions] = mean + next_z @ basis.T + next_residual
    if np.any(labels[rows] < 0) or not np.isfinite(estimate).all():
        raise ValueError("LOCAL_PREDICTION_UNASSIGNED_OR_NONFINITE")
    return estimate


def select_local_bundle(
    x: np.ndarray,
    phi: np.ndarray,
    train_rows: np.ndarray,
    development_rows: np.ndarray,
    labels: np.ndarray,
    charts: int,
    dimensions: tuple[int, ...] = DIMENSIONS,
) -> tuple[dict, list[dict]]:
    geometry = prepare_geometry(x, train_rows, labels, charts)
    max_basis = min(item["basis"].shape[1] for item in geometry)
    entries = []
    for d in dimensions:
        if d >= x.shape[1] or d > max_basis:
            continue
        for lam in RIDGES:
            model = fit_local_bundle(x, phi, train_rows, labels, geometry, d, lam)
            estimate = local_bundle_predict(model, x, phi, development_rows, labels)
            sse = float(np.square(x[development_rows + 1] - estimate).sum())
            entries.append({"development_sse": sse, "d": d, "lambda": lam, "model": model})
    if not entries:
        raise ValueError("NO_LOCAL_BUNDLE_CANDIDATE")
    entries.sort(key=lambda item: (item["development_sse"], item["d"], -item["lambda"]))
    summary = [
        {"development_sse": item["development_sse"], "d": item["d"], "lambda": item["lambda"]}
        for item in entries
    ]
    return entries[0]["model"], summary


def fit_full_var(
    x: np.ndarray,
    phi: np.ndarray,
    rows: np.ndarray,
    lam: float,
) -> dict:
    coefficient, intercept = ridge(np.c_[x[rows], phi[rows]], x[rows + 1], lam)
    return {"coefficient": coefficient, "intercept": intercept, "lambda": lam}


def full_var_predict(model: dict, x: np.ndarray, phi: np.ndarray, rows: np.ndarray) -> np.ndarray:
    return predict(model["coefficient"], model["intercept"], np.c_[x[rows], phi[rows]])


def select_global_full(
    x: np.ndarray,
    phi: np.ndarray,
    train_rows: np.ndarray,
    development_rows: np.ndarray,
) -> dict:
    entries = []
    for lam in RIDGES:
        model = fit_full_var(x, phi, train_rows, lam)
        sse = float(np.square(x[development_rows + 1] - full_var_predict(model, x, phi, development_rows)).sum())
        entries.append((sse, -lam, model))
    entries.sort(key=lambda item: (item[0], item[1]))
    return entries[0][2]


def fit_local_full(
    x: np.ndarray,
    phi: np.ndarray,
    rows: np.ndarray,
    labels: np.ndarray,
    charts: int,
    lam: float,
) -> dict:
    fits = []
    for chart in range(charts):
        selected = rows[labels[rows] == chart]
        fits.append(fit_full_var(x, phi, selected, lam))
    return {"lambda": lam, "charts": fits}


def local_full_predict(
    model: dict,
    x: np.ndarray,
    phi: np.ndarray,
    rows: np.ndarray,
    labels: np.ndarray,
) -> np.ndarray:
    estimate = np.empty((rows.size, x.shape[1]), dtype=float)
    for chart, fit in enumerate(model["charts"]):
        positions = np.flatnonzero(labels[rows] == chart)
        if positions.size:
            estimate[positions] = full_var_predict(fit, x, phi, rows[positions])
    if np.any(labels[rows] < 0) or not np.isfinite(estimate).all():
        raise ValueError("LOCAL_FULL_PREDICTION_UNASSIGNED_OR_NONFINITE")
    return estimate


def select_local_full(
    x: np.ndarray,
    phi: np.ndarray,
    train_rows: np.ndarray,
    development_rows: np.ndarray,
    labels: np.ndarray,
    charts: int,
) -> dict:
    entries = []
    for lam in RIDGES:
        model = fit_local_full(x, phi, train_rows, labels, charts, lam)
        estimate = local_full_predict(model, x, phi, development_rows, labels)
        sse = float(np.square(x[development_rows + 1] - estimate).sum())
        entries.append((sse, -lam, model))
    entries.sort(key=lambda item: (item[0], item[1]))
    return entries[0][2]


def shift_chart_labels(labels: np.ndarray, blocks: dict[str, tuple[int, int]], shift: int = SHIFT_BINS) -> np.ndarray:
    shifted = np.full_like(labels, -1)
    for begin, end in blocks.values():
        if end - begin > shift:
            shifted[begin + shift : end] = labels[begin : end - shift]
    return shifted


def q_audit(model: dict) -> dict:
    values = [float(np.max(np.abs(fit["fiber"]["diagonal"]))) for fit in model["charts"]]
    return {"q_by_chart_upper_bound": values, "q_max_upper_bound": max(values), "passes": max(values) < 1.0}


def transition_matrix(labels: np.ndarray, rows: np.ndarray, charts: int) -> np.ndarray:
    matrix = np.zeros((charts, charts), dtype=np.int64)
    for row in rows:
        left, right = int(labels[row]), int(labels[row + 1])
        if left >= 0 and right >= 0:
            matrix[left, right] += 1
    return matrix


def tangent_diagnostics(model: dict, train_transitions: np.ndarray, evaluation_transitions: np.ndarray) -> list[dict]:
    output = []
    d = model["d"]
    for left in range(len(model["charts"])):
        for right in range(left + 1, len(model["charts"])):
            ul = model["charts"][left]["basis"]
            ur = model["charts"][right]["basis"]
            singular = np.clip(np.linalg.svd(ul.T @ ur, compute_uv=False), 0.0, 1.0)
            angles = np.degrees(np.arccos(singular))
            chordal = float(
                np.linalg.norm(ul @ ul.T - ur @ ur.T, "fro") / np.sqrt(2.0 * d)
            )
            train_count = int(train_transitions[left, right] + train_transitions[right, left])
            evaluation_count = int(
                evaluation_transitions[left, right] + evaluation_transitions[right, left]
            )
            output.append(
                {
                    "charts": [left, right],
                    "train_transition_count_both_directions": train_count,
                    "evaluation_transition_count_both_directions": evaluation_count,
                    "adjacent_train_at_least_20": train_count >= 20,
                    "projector_chordal": chordal,
                    "principal_angle_degrees": angles,
                }
            )
    return output


def model_rows(
    block: tuple[int, int],
    segments: np.ndarray,
    behavior_valid: np.ndarray,
    labels: np.ndarray,
    lag: int = 0,
) -> np.ndarray:
    rows = core.valid_rows(block, segments, horizon=1, lag=lag)
    return rows[behavior_valid[rows] & (labels[rows] >= 0)]


def main() -> None:
    import h5py

    load_predecessors()
    assert core is not None and behavior is not None
    temporary = Path(tempfile.mkdtemp(prefix="ce-dandi-r2-local-bundle-"))
    receipt = {
        "dandiset": core.DANDISET,
        "version": core.VERSION,
        "asset_id": core.ASSET_ID,
        "downloaded": False,
        "nwb_deleted": False,
        "confirmation_001695_opened": False,
    }
    try:
        nwb_path = temporary / "source.nwb"
        receipt.update(core.download_verified(nwb_path))
        receipt["downloaded"] = True
        with h5py.File(nwb_path, "r") as nwb:
            start, stop, segments, coverage = core.electrical_coverage(nwb)
            spikes = nwb["units/spike_times"]
            indexes = np.asarray(nwb["units/spike_times_index"], dtype=np.int64)
            n_bins = int(math.floor((stop - start) / core.BIN_SECONDS))
            train_end = int(math.floor(0.5 * n_bins))
            development_end = int(math.floor(0.75 * n_bins))
            train_boundary = start + train_end * core.BIN_SECONDS
            evaluation_boundary = start + development_end * core.BIN_SECONDS
            blocks = {
                "train": (0, train_end),
                "development": (train_end, development_end),
                "evaluation": (development_end, n_bins),
            }

            retention_counts, retention_max = core.prefix_unit_statistics(
                spikes, indexes, start, train_boundary
            )
            retained = np.flatnonzero(retention_counts / (train_boundary - start) >= 0.1)
            prefix_counts, prefix_max = core.bins_for_interval(
                spikes, indexes, retained, start, evaluation_boundary, development_end
            )
            behavior_t, position, head_direction, behavior_prefix_meta = behavior.read_behavior(
                nwb, evaluation_boundary
            )
            centers_prefix = start + (np.arange(development_end) + 0.5) * core.BIN_SECONDS
            phi_raw_prefix, behavior_valid_prefix = behavior.behavior_features(
                behavior_t, position, head_direction, centers_prefix
            )

            segment_ids = np.full(n_bins, -1, dtype=np.int64)
            for segment, (left, right) in enumerate(segments):
                first = max(0, int(math.ceil((left - start) / core.BIN_SECONDS)))
                last = min(n_bins, int(math.floor((right - start) / core.BIN_SECONDS)))
                segment_ids[first:last] = segment

            provisional_labels = np.where(behavior_valid_prefix, 0, -1)
            raw_train_rows = model_rows(
                blocks["train"], segment_ids, behavior_valid_prefix, provisional_labels
            )
            phi_mean = phi_raw_prefix[raw_train_rows].mean(axis=0)
            phi_scale = phi_raw_prefix[raw_train_rows].std(axis=0)
            phi_scale[phi_scale == 0] = 1.0
            phi_prefix = (phi_raw_prefix - phi_mean) / phi_scale

            transformed = np.sqrt(prefix_counts + 3.0 / 8.0)
            neural_mean = transformed[:train_end].mean(axis=0)
            neural_scale = transformed[:train_end].std(axis=0)
            neural_scale[neural_scale == 0] = 1.0
            x_prefix = (transformed - neural_mean) / neural_scale

            chart_centers, chart_fit = fit_behavior_charts(phi_prefix, raw_train_rows)
            labels_prefix = assign_charts(phi_prefix, chart_centers)
            labels_prefix[~behavior_valid_prefix] = -1
            train_rows = model_rows(
                blocks["train"], segment_ids, behavior_valid_prefix, labels_prefix
            )
            development_rows = model_rows(
                blocks["development"], segment_ids, behavior_valid_prefix, labels_prefix
            )
            prefix_support = support_audit(
                labels_prefix,
                {"train": train_rows, "development": development_rows},
                retained.size,
            )
            if not prefix_support["passes"]:
                result = {
                    "status": "STOP",
                    "failure_code": "INSUFFICIENT_CHART_SUPPORT_TRAIN_DEVELOPMENT",
                    "chart_support": prefix_support,
                    "claim_ceiling": "Outcome-informed single-session development only; no empirical bridge.",
                    "confirmation_001695_opened": False,
                }
                write_json("result.json", result)
                print(json.dumps(jsonable(result), indent=2))
                return

            selected, candidate_grid = select_local_bundle(
                x_prefix, phi_prefix, train_rows, development_rows, labels_prefix, CHARTS
            )
            global_labels_prefix = np.where(behavior_valid_prefix, 0, -1)
            global_matched, global_grid = select_local_bundle(
                x_prefix,
                phi_prefix,
                train_rows,
                development_rows,
                global_labels_prefix,
                1,
            )
            global_full = select_global_full(x_prefix, phi_prefix, train_rows, development_rows)
            local_full = select_local_full(
                x_prefix, phi_prefix, train_rows, development_rows, labels_prefix, CHARTS
            )
            global_basis, _ = pca(x_prefix[:train_end])
            secondary = behavior.select_simple_controls(
                x_prefix, phi_prefix, train_rows, development_rows, global_basis
            )

            shifted_labels_prefix = shift_chart_labels(labels_prefix, blocks)
            shifted_valid_prefix = behavior_valid_prefix & (shifted_labels_prefix >= 0)
            shifted_train_rows = model_rows(
                blocks["train"],
                segment_ids,
                shifted_valid_prefix,
                shifted_labels_prefix,
                lag=SHIFT_BINS,
            )
            shifted_development_rows = model_rows(
                blocks["development"],
                segment_ids,
                shifted_valid_prefix,
                shifted_labels_prefix,
                lag=SHIFT_BINS,
            )
            shifted_prefix_support = support_audit(
                shifted_labels_prefix,
                {"train": shifted_train_rows, "development": shifted_development_rows},
                retained.size,
            )
            if not shifted_prefix_support["passes"]:
                result = {
                    "status": "STOP",
                    "failure_code": "INSUFFICIENT_SHIFTED_CHART_SUPPORT_TRAIN_DEVELOPMENT",
                    "chart_support": prefix_support,
                    "shifted_chart_support": shifted_prefix_support,
                    "claim_ceiling": "Outcome-informed single-session development only; no empirical bridge.",
                    "confirmation_001695_opened": False,
                }
                write_json("result.json", result)
                print(json.dumps(jsonable(result), indent=2))
                return
            shifted_model, shifted_grid = select_local_bundle(
                x_prefix,
                phi_prefix,
                shifted_train_rows,
                shifted_development_rows,
                shifted_labels_prefix,
                CHARTS,
            )

            selection_lock = {
                "chart_centers": chart_centers,
                "chart_fit": chart_fit,
                "candidate": {"d": selected["d"], "lambda": selected["lambda"]},
                "global_matched": {
                    "d": global_matched["d"],
                    "lambda": global_matched["lambda"],
                },
                "global_full_lambda": global_full["lambda"],
                "local_full_lambda": local_full["lambda"],
                "shifted_candidate": {
                    "d": shifted_model["d"],
                    "lambda": shifted_model["lambda"],
                },
            }
            assert retention_max is None or retention_max < train_boundary
            assert prefix_max is None or prefix_max < evaluation_boundary
            assert prefix_counts.shape[0] == development_end
            model_selected = True
            assert model_selected

            all_counts, _ = core.bins_for_interval(
                spikes,
                indexes,
                retained,
                start,
                start + n_bins * core.BIN_SECONDS,
                n_bins,
            )
            behavior_t_all, position_all, head_all, behavior_full_meta = behavior.read_behavior(
                nwb, None
            )

        centers_all = start + (np.arange(n_bins) + 0.5) * core.BIN_SECONDS
        phi_raw, behavior_valid = behavior.behavior_features(
            behavior_t_all, position_all, head_all, centers_all
        )
        phi = (phi_raw - phi_mean) / phi_scale
        x = (np.sqrt(all_counts + 3.0 / 8.0) - neural_mean) / neural_scale
        labels = assign_charts(phi, chart_centers)
        labels[~behavior_valid] = -1
        evaluation_rows = model_rows(
            blocks["evaluation"], segment_ids, behavior_valid, labels
        )
        all_support = support_audit(
            labels,
            {
                "train": train_rows,
                "development": development_rows,
                "evaluation": evaluation_rows,
            },
            retained.size,
        )

        target = x[evaluation_rows + 1]
        train_mean = x[:train_end].mean(axis=0)
        denominator = float(np.square(target - train_mean).sum())
        if evaluation_rows.size < 300 or denominator <= 0:
            raise ValueError("INSUFFICIENT_EVALUATION_ROWS_OR_DENOMINATOR")

        estimates = {
            "r2_local_bundle": local_bundle_predict(selected, x, phi, evaluation_rows, labels),
            "global_full_var_input": full_var_predict(global_full, x, phi, evaluation_rows),
            "local_full_var_input": local_full_predict(
                local_full, x, phi, evaluation_rows, labels
            ),
            "global_matched_fiber": local_bundle_predict(
                global_matched,
                x,
                phi,
                evaluation_rows,
                np.zeros_like(labels),
            ),
        }
        z_secondary = x @ global_basis[:, : secondary["base"]["d"]]
        estimates.update(
            {
                "global_base_input": predict(
                    secondary["base"]["coef"],
                    secondary["base"]["intercept"],
                    np.c_[z_secondary[evaluation_rows], phi[evaluation_rows]],
                ),
                "input_only": predict(
                    secondary["input"]["coef"],
                    secondary["input"]["intercept"],
                    phi[evaluation_rows],
                ),
                "persistence": x[evaluation_rows],
                "train_mean": np.broadcast_to(train_mean, target.shape),
            }
        )
        errors = {name: np.square(target - estimate).sum(axis=1) for name, estimate in estimates.items()}
        scores = {name: float(error.sum() / denominator) for name, error in errors.items()}
        primary = (
            "global_full_var_input",
            "local_full_var_input",
            "global_matched_fiber",
        )
        improvements = {
            name: 1.0 - scores["r2_local_bundle"] / scores[name] for name in primary
        }
        bootstraps = {
            name: core.bootstrap(errors[name] - errors["r2_local_bundle"], evaluation_rows)
            for name in primary
        }
        contraction = q_audit(selected)

        shifted_labels = shift_chart_labels(labels, blocks)
        shifted_valid = behavior_valid & (shifted_labels >= 0)
        shifted_evaluation_rows = model_rows(
            blocks["evaluation"],
            segment_ids,
            shifted_valid,
            shifted_labels,
            lag=SHIFT_BINS,
        )
        shifted_support = support_audit(
            shifted_labels,
            {
                "train": shifted_train_rows,
                "development": shifted_development_rows,
                "evaluation": shifted_evaluation_rows,
            },
            retained.size,
        )
        reduced_target = x[shifted_evaluation_rows + 1]
        reduced_denominator = float(np.square(reduced_target - train_mean).sum())
        real_reduced = local_bundle_predict(
            selected, x, phi, shifted_evaluation_rows, labels
        )
        shifted_estimate = local_bundle_predict(
            shifted_model, x, phi, shifted_evaluation_rows, shifted_labels
        )
        real_reduced_nmse = nmse(reduced_target, real_reduced, reduced_denominator)
        shifted_nmse = nmse(reduced_target, shifted_estimate, reduced_denominator)

        chart_scores = {}
        for chart in range(CHARTS):
            mask = labels[evaluation_rows] == chart
            chart_denominator = float(np.square(target[mask] - train_mean).sum())
            chart_scores[str(chart)] = {
                "rows": int(mask.sum()),
                "nmse": {
                    name: float(error[mask].sum() / chart_denominator)
                    for name, error in errors.items()
                },
            }

        train_transition = transition_matrix(labels_prefix, train_rows, CHARTS)
        evaluation_transition = transition_matrix(labels, evaluation_rows, CHARTS)
        tangent = tangent_diagnostics(selected, train_transition, evaluation_transition)

        failures = []
        if not all_support["passes"]:
            failures.append("INSUFFICIENT_CHART_SUPPORT")
        if not shifted_support["passes"]:
            failures.append("INSUFFICIENT_SHIFTED_CHART_SUPPORT")
        for name in primary:
            if improvements[name] < 0.01:
                failures.append(f"IMPROVEMENT_BELOW_ONE_PERCENT:{name}")
            interval = bootstraps[name].get("ci95")
            if interval is None or interval[0] <= 0:
                failures.append(f"PAIRED_INTERVAL_NOT_POSITIVE:{name}")
        if not contraction["passes"]:
            failures.append("LOCAL_FIBER_CONTRACTION_FAILED")
        if shifted_nmse <= real_reduced_nmse:
            failures.append("SHIFTED_CHART_MATCHED_OR_BETTER")

        result = {
            "status": "PASS" if not failures else "STOP",
            "failure_code": None if not failures else "R2_EMPIRICAL_KILL_CONDITION",
            "failed_gates": failures,
            "claim_ceiling": "Outcome-informed single-session L2 development only; not an independent holdout, biological manifold, flow, metric, or causal mechanism.",
            "source": {
                "dandiset": core.DANDISET,
                "version": core.VERSION,
                "asset": core.ASSET_PATH,
            },
            "schema": {
                "position": behavior.POSITION,
                "head_direction": behavior.HEAD_DIRECTION,
                "behavior_prefix": behavior_prefix_meta,
                "behavior_full": behavior_full_meta,
            },
            "coverage": coverage,
            "retained_units": int(retained.size),
            "bins": int(n_bins),
            "valid_rows": {
                "train": int(train_rows.size),
                "development": int(development_rows.size),
                "evaluation": int(evaluation_rows.size),
                "shifted_evaluation": int(shifted_evaluation_rows.size),
            },
            "preselection_audit": {
                "retention_scope": "train_only",
                "retention_boundary_seconds": train_boundary,
                "retention_event_max": retention_max,
                "evaluation_boundary_seconds": evaluation_boundary,
                "prefix_event_max": prefix_max,
                "prefix_shape": list(prefix_counts.shape),
                "evaluation_materialized_after_selection": True,
            },
            "selection_lock": selection_lock,
            "candidate_grid": candidate_grid,
            "global_matched_grid": global_grid,
            "shifted_grid": shifted_grid,
            "chart_support": all_support,
            "shifted_chart_support": shifted_support,
            "nmse_denominator": denominator,
            "scores_nmse": scores,
            "improvement": improvements,
            "bootstrap": bootstraps,
            "contraction": contraction,
            "shifted_chart": {
                "real_reduced_nmse": real_reduced_nmse,
                "shifted_refit_nmse": shifted_nmse,
                "real_better": real_reduced_nmse < shifted_nmse,
            },
            "chart_scores": chart_scores,
            "train_transition_matrix": train_transition,
            "evaluation_transition_matrix": evaluation_transition,
            "tangent_diagnostics": tangent,
            "confirmation_001695_opened": False,
        }
        write_json("result.json", result)
        print(
            json.dumps(
                jsonable(
                    {
                        "status": result["status"],
                        "failed_gates": failures,
                        "retained_units": retained.size,
                        "valid_rows": result["valid_rows"],
                        "scores_nmse": scores,
                        "improvement": improvements,
                        "q_max_upper_bound": contraction["q_max_upper_bound"],
                        "shifted_chart": result["shifted_chart"],
                    }
                ),
                indent=2,
            )
        )
    except Exception as exc:
        write_json(
            "result.json",
            {
                "status": "STOP",
                "failure_code": "R2_EXECUTION_OR_SCHEMA_FAILURE",
                "detail": repr(exc),
                "claim_ceiling": "No empirical bridge.",
                "confirmation_001695_opened": False,
            },
        )
        receipt["error"] = repr(exc)
        raise
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        receipt.update(
            {
                "bytes_received": core.EXPECTED_SIZE,
                "sha256": core.EXPECTED_SHA256,
                "schema_paths": {
                    "position": behavior.POSITION,
                    "head_direction": behavior.HEAD_DIRECTION,
                },
                "nwb_deleted": True,
            }
        )
        write_json("source-receipt.json", receipt)


if __name__ == "__main__":
    main()
