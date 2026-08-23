"""Infer discovery-only BA-SRM4 edge-history equations and quotient diagnostics.

The script fits only predecessor-contacted IC->IC discovery rows.  It performs
group-nested selection over a fixed low-order Volterra bank, abstains on sparse
VC strata, and never loads validation or confirmation outcomes.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np


VERSION = "BA-SRM4-DISCOVERY-EQUATION-V2-STABILITY-CORE"
EXPECTED_DATASET_SHA256 = (
    "5516a7523f7525218ad628ef2586ad0ea042e4e9dc5214a58b22d665905e2773"
)
EXPECTED_RECEIPT_SHA256 = (
    "07a1b2743359eeb3383e307de464cc9ea6d7b833025b595608b3af46ef3ef167"
)
RIDGE_GRID = (1e-2, 1e-1, 1.0, 10.0, 100.0)
EFFECTIVE_DIMENSION_LAMBDAS = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0)
OUTER_FOLDS = 5
INNER_FOLDS = 4
MAX_MAIN_TERMS = 8
MAX_INTERACTION_TERMS = 4
MIN_RELATIVE_CV_IMPROVEMENT = 1e-3
MIN_GROUPS_FOR_MODEL = 40
MIN_FINITE_FRACTION = 0.5
MIN_OUTER_SELECTION_FOLDS = 3
RANK_RELATIVE_TOLERANCE = 1e-4
COVARIANCE_SHRINKAGE = 0.5


BASE_FEATURE_NAMES = (
    "log_frequency_T0",
    "log_recovery_delay_T0",
    "bath_temperature_K_over_Theta0",
    "post_baseline_potential_over_V0",
    "post_noise_ic_over_V0",
    "pair_distance_over_L0",
    "post_input_resistance_over_R0",
    "post_capacitance_over_C0",
    "post_time_constant_over_T0",
    "history_mean_log_dt_T0",
    "history_last_log_dt_T0",
    "history_mean_spike_count",
    "history_last_spike_count",
    "history_mean_first_spike_over_T0",
    "history_mean_stim_ic_over_I0",
    "history_last_stim_ic_over_I0",
    "history_mean_response_ic_over_V0",
    "history_last_response_ic_over_V0",
    "history_slope_response_ic_over_V0",
    "history_mean_latency_over_T0",
    "history_mean_rise_over_T0",
    "history_mean_decay_over_T0",
    "history_amp_trace_tau10_typed",
    "history_amp_trace_tau50_typed",
    "history_spike_trace_tau10",
    "history_spike_trace_tau50",
)

INTERACTION_NAME_PAIRS = (
    ("log_frequency_T0", "history_mean_spike_count"),
    ("log_frequency_T0", "history_last_response_ic_over_V0"),
    ("log_recovery_delay_T0", "history_last_response_ic_over_V0"),
    ("history_mean_spike_count", "history_mean_stim_ic_over_I0"),
    ("log_frequency_T0", "history_slope_response_ic_over_V0"),
    ("log_recovery_delay_T0", "history_amp_trace_tau10_typed"),
    ("log_recovery_delay_T0", "history_amp_trace_tau50_typed"),
    ("post_input_resistance_over_R0", "history_last_response_ic_over_V0"),
    ("post_noise_ic_over_V0", "history_last_response_ic_over_V0"),
    ("history_mean_latency_over_T0", "history_mean_decay_over_T0"),
)


class DiscoveryFailure(RuntimeError):
    """Raised when the sealed discovery fit cannot be reproduced."""


def sha256_file(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def deterministic_fold(group_id: str, salt: str, folds: int) -> int:
    digest = hashlib.sha256(f"{salt}:{group_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % folds


def robust_location_scale(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=float)
    if values.ndim != 2:
        raise DiscoveryFailure("robust scaler requires a matrix")
    location = np.empty(values.shape[1], dtype=float)
    scale = np.empty(values.shape[1], dtype=float)
    for column in range(values.shape[1]):
        observed = values[np.isfinite(values[:, column]), column]
        if observed.size == 0:
            location[column] = 0.0
            scale[column] = 1.0
            continue
        center = float(np.median(observed))
        mad = float(np.median(np.abs(observed - center))) * 1.482602218505602
        if not math.isfinite(mad) or mad <= 0.0:
            q25, q75 = np.quantile(observed, [0.25, 0.75])
            mad = float((q75 - q25) / 1.3489795003921634)
        if not math.isfinite(mad) or mad <= 0.0:
            mad = float(np.std(observed, ddof=1)) if observed.size > 1 else 1.0
        if not math.isfinite(mad) or mad <= 0.0:
            mad = 1.0
        location[column] = center
        scale[column] = mad
    return location, scale


def transform(values: np.ndarray, location: np.ndarray, scale: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    filled = np.where(np.isfinite(values), values, location[None, :])
    return (filled - location[None, :]) / scale[None, :]


def available_feature_indices(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    keep: list[int] = []
    for column in range(values.shape[1]):
        observed = values[np.isfinite(values[:, column]), column]
        if observed.size / values.shape[0] < MIN_FINITE_FRACTION:
            continue
        _, scale = robust_location_scale(values[:, [column]])
        if math.isfinite(float(scale[0])) and float(scale[0]) > 0.0:
            if observed.size > 1 and float(np.max(observed) - np.min(observed)) > 0.0:
                keep.append(column)
    return np.asarray(keep, dtype=int)


def build_term_schema(
    base_names: list[str],
) -> tuple[list[str], list[tuple[int, int]]]:
    index = {name: idx for idx, name in enumerate(base_names)}
    interactions = [
        (index[left], index[right])
        for left, right in INTERACTION_NAME_PAIRS
        if left in index and right in index
    ]
    names = list(base_names) + [
        f"({base_names[left]})*({base_names[right]})"
        for left, right in interactions
    ]
    return names, interactions


def build_terms(base: np.ndarray, interactions: list[tuple[int, int]]) -> np.ndarray:
    base = np.asarray(base, dtype=float)
    columns = [base]
    if interactions:
        columns.append(
            np.column_stack([base[:, left] * base[:, right] for left, right in interactions])
        )
    return np.column_stack(columns)


def fit_ridge(terms: np.ndarray, target: np.ndarray, ridge: float) -> np.ndarray:
    terms = np.asarray(terms, dtype=float)
    target = np.asarray(target, dtype=float)
    design = np.column_stack([np.ones(terms.shape[0]), terms])
    penalty = np.eye(design.shape[1]) * float(ridge)
    penalty[0, 0] = 0.0
    system = design.T @ design + penalty
    rhs = design.T @ target
    try:
        return np.linalg.solve(system, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(system, rhs, rcond=None)[0]


def predict_ridge(beta: np.ndarray, terms: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(np.asarray(terms).shape[0]), terms])
    return design @ beta


def group_equal_mse(target: np.ndarray, prediction: np.ndarray, groups: np.ndarray) -> float:
    row_error = np.mean((np.asarray(target) - np.asarray(prediction)) ** 2, axis=1)
    group_values = [
        float(np.mean(row_error[groups == group])) for group in np.unique(groups)
    ]
    if not group_values:
        raise DiscoveryFailure("no groups available for score")
    return float(np.mean(group_values))


def fold_views(
    x: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    fold_ids: np.ndarray,
    interactions: list[tuple[int, int]],
) -> list[dict[str, np.ndarray]]:
    views: list[dict[str, np.ndarray]] = []
    for fold in sorted(np.unique(fold_ids)):
        train = fold_ids != fold
        test = fold_ids == fold
        if not np.any(train) or not np.any(test):
            raise DiscoveryFailure("empty group fold")
        x_location, x_scale = robust_location_scale(x[train])
        y_location, y_scale = robust_location_scale(y[train])
        views.append(
            {
                "train_terms": build_terms(transform(x[train], x_location, x_scale), interactions),
                "test_terms": build_terms(transform(x[test], x_location, x_scale), interactions),
                "train_target": transform(y[train], y_location, y_scale),
                "test_target": transform(y[test], y_location, y_scale),
                "test_groups": groups[test],
            }
        )
    return views


def cv_score(views: list[dict[str, np.ndarray]], selected: list[int], ridge: float) -> float:
    scores: list[float] = []
    for view in views:
        train_terms = view["train_terms"][:, selected] if selected else np.empty((view["train_terms"].shape[0], 0))
        test_terms = view["test_terms"][:, selected] if selected else np.empty((view["test_terms"].shape[0], 0))
        beta = fit_ridge(train_terms, view["train_target"], ridge)
        prediction = predict_ridge(beta, test_terms)
        scores.append(
            group_equal_mse(view["test_target"], prediction, view["test_groups"])
        )
    return float(np.mean(scores))


def best_ridge_score(
    views: list[dict[str, np.ndarray]], selected: list[int]
) -> tuple[float, float]:
    candidates = [(cv_score(views, selected, ridge), ridge) for ridge in RIDGE_GRID]
    return min(candidates, key=lambda item: (item[0], -item[1]))


def greedy_select(
    x: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    fold_ids: np.ndarray,
    base_count: int,
    interactions: list[tuple[int, int]],
) -> dict[str, Any]:
    views = fold_views(x, y, groups, fold_ids, interactions)
    selected: list[int] = []
    current_score, current_ridge = best_ridge_score(views, selected)
    path: list[dict[str, Any]] = []

    for _ in range(MAX_MAIN_TERMS):
        proposals: list[tuple[float, float, int]] = []
        for candidate in range(base_count):
            if candidate in selected:
                continue
            score, ridge = best_ridge_score(views, selected + [candidate])
            proposals.append((score, ridge, candidate))
        if not proposals:
            break
        score, ridge, candidate = min(proposals, key=lambda item: (item[0], item[2]))
        if score >= current_score * (1.0 - MIN_RELATIVE_CV_IMPROVEMENT):
            break
        selected.append(candidate)
        current_score, current_ridge = score, ridge
        path.append({"term_index": candidate, "cv_mse": score, "ridge": ridge})

    for _ in range(MAX_INTERACTION_TERMS):
        proposals = []
        for offset, (left, right) in enumerate(interactions):
            candidate = base_count + offset
            if candidate in selected or left not in selected or right not in selected:
                continue
            score, ridge = best_ridge_score(views, selected + [candidate])
            proposals.append((score, ridge, candidate))
        if not proposals:
            break
        score, ridge, candidate = min(proposals, key=lambda item: (item[0], item[2]))
        if score >= current_score * (1.0 - MIN_RELATIVE_CV_IMPROVEMENT):
            break
        selected.append(candidate)
        current_score, current_ridge = score, ridge
        path.append({"term_index": candidate, "cv_mse": score, "ridge": ridge})

    current_score, current_ridge = best_ridge_score(views, selected)
    return {
        "selected": selected,
        "ridge": current_ridge,
        "cv_mse": current_score,
        "path": path,
    }


def stability_core_indices(
    term_names: list[str],
    selection_frequency: Counter[str],
    base_count: int,
    interactions: list[tuple[int, int]],
) -> list[int]:
    selected = {
        index
        for index, name in enumerate(term_names)
        if selection_frequency[name] >= MIN_OUTER_SELECTION_FOLDS
    }
    # Preserve Volterra hierarchy: an interaction survives only with both parents.
    return sorted(
        index
        for index in selected
        if index < base_count
        or all(parent in selected for parent in interactions[index - base_count])
    )


def output_scaler(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    location, scale = robust_location_scale(values)
    if not np.all(np.isfinite(scale) & (scale > 0.0)):
        raise DiscoveryFailure("target scaler is not positive finite")
    return location, scale


def rank_from_singular(singular: np.ndarray) -> int:
    singular = np.asarray(singular, dtype=float)
    if singular.size == 0 or singular[0] <= 0.0:
        return 0
    return int(np.sum(singular / singular[0] >= RANK_RELATIVE_TOLERANCE))


def jacobians_from_equation(
    standardized_base: np.ndarray,
    beta: np.ndarray,
    selected: list[int],
    base_count: int,
    interactions: list[tuple[int, int]],
) -> np.ndarray:
    coefficient = {term: beta[row + 1] for row, term in enumerate(selected)}
    result = np.zeros(
        (standardized_base.shape[0], beta.shape[1], base_count), dtype=float
    )
    for term, value in coefficient.items():
        if term < base_count:
            result[:, :, term] += value[None, :]
        else:
            left, right = interactions[term - base_count]
            result[:, :, left] += standardized_base[:, right, None] * value[None, :]
            result[:, :, right] += standardized_base[:, left, None] * value[None, :]
    return result


def geometry_receipt(
    x_standardized: np.ndarray,
    beta: np.ndarray,
    selected: list[int],
    base_names: list[str],
    interactions: list[tuple[int, int]],
    standardized_oof_residual: np.ndarray,
) -> dict[str, Any]:
    sample = np.cov(standardized_oof_residual, rowvar=False, ddof=1)
    covariance = (
        (1.0 - COVARIANCE_SHRINKAGE) * sample
        + COVARIANCE_SHRINKAGE * np.diag(np.diag(sample))
    )
    floor = 1e-8 * float(np.median(np.diag(covariance)))
    covariance = covariance + floor * np.eye(covariance.shape[0])
    chol = np.linalg.cholesky(covariance)
    jacobians = jacobians_from_equation(
        x_standardized, beta, selected, len(base_names), interactions
    )
    ranks: list[int] = []
    spectra: list[np.ndarray] = []
    deff: dict[str, list[float]] = {
        f"{value:g}": [] for value in EFFECTIVE_DIMENSION_LAMBDAS
    }
    selected_base = sorted({
        term
        for term in selected
        if term < len(base_names)
    } | {
        parent
        for term in selected
        if term >= len(base_names)
        for parent in interactions[term - len(base_names)]
    })
    increment_counts = Counter({base: 0 for base in selected_base})
    for jacobian in jacobians:
        whitened = np.linalg.solve(chol, jacobian)
        singular = np.linalg.svd(whitened, compute_uv=False)
        rank = rank_from_singular(singular)
        ranks.append(rank)
        metric = whitened.T @ whitened
        eigenvalues = np.maximum(np.linalg.eigvalsh(metric), 0.0)
        spectra.append(eigenvalues)
        for value in EFFECTIVE_DIMENSION_LAMBDAS:
            deff[f"{value:g}"].append(
                float(np.sum(eigenvalues / (eigenvalues + value)))
            )
        active_matrix = whitened[:, selected_base]
        active_rank = rank_from_singular(np.linalg.svd(active_matrix, compute_uv=False))
        for column, base in enumerate(selected_base):
            without = np.delete(active_matrix, column, axis=1)
            without_rank = rank_from_singular(np.linalg.svd(without, compute_uv=False))
            if active_rank > without_rank:
                increment_counts[base] += 1

    spectrum_matrix = np.asarray(spectra)
    return {
        "status": "DISCOVERY_ONLY_TRACE_CLASS_REFERENCE_RECEIPT",
        "reference_chart": "all-discovery robust-standardized finite base chart with identity metric",
        "output_whitening": "global standardized OOF residual covariance, gamma=0.5 diagonal shrinkage",
        "finite_basis_dimension": len(base_names),
        "trace_class_reason": "each pointwise operator is a finite positive-semidefinite matrix",
        "covariance_floor": floor,
        "rank_relative_tolerance": RANK_RELATIVE_TOLERANCE,
        "pointwise_rank_counts": dict(sorted(Counter(ranks).items())),
        "eigenvalue_median_descending": np.median(spectrum_matrix, axis=0)[::-1].tolist(),
        "effective_dimension": {
            key: {
                "q025": float(np.quantile(values, 0.025)),
                "q50": float(np.quantile(values, 0.5)),
                "q975": float(np.quantile(values, 0.975)),
            }
            for key, values in deff.items()
        },
        "conditional_rank_increment_fraction": {
            base_names[base]: increment_counts[base] / len(jacobians)
            for base in selected_base
        },
        "interpretation_boundary": "finite fitted quotient only; not full history-space rank or SPD",
    }


def fit_stratum(
    features: np.ndarray,
    target: np.ndarray,
    groups: np.ndarray,
    full_feature_names: list[str],
    target_names: list[str],
    label: str,
) -> dict[str, Any]:
    full_index = {name: idx for idx, name in enumerate(full_feature_names)}
    missing = [name for name in BASE_FEATURE_NAMES if name not in full_index]
    if missing:
        raise DiscoveryFailure(f"dataset lacks fixed base features: {missing}")
    raw = features[:, [full_index[name] for name in BASE_FEATURE_NAMES]]
    available = available_feature_indices(raw)
    x = raw[:, available]
    base_names = [BASE_FEATURE_NAMES[idx] for idx in available]
    term_names, interactions = build_term_schema(base_names)
    if len(np.unique(groups)) < MIN_GROUPS_FOR_MODEL:
        return {
            "status": "ABSTAIN_INSUFFICIENT_GROUPS",
            "sequences": int(len(groups)),
            "groups": int(len(np.unique(groups))),
            "minimum_groups": MIN_GROUPS_FOR_MODEL,
        }

    outer_ids = np.asarray(
        [deterministic_fold(group, f"BA-SRM4-OUTER-V1:{label}", OUTER_FOLDS) for group in groups],
        dtype=int,
    )
    oof_prediction = np.full_like(target, np.nan, dtype=float)
    oof_candidate_error = np.full(len(groups), np.nan, dtype=float)
    oof_constant_error = np.full(len(groups), np.nan, dtype=float)
    outer_models: list[dict[str, Any]] = []
    for outer in range(OUTER_FOLDS):
        train = outer_ids != outer
        test = outer_ids == outer
        if not np.any(test):
            raise DiscoveryFailure("empty outer fold")
        inner_ids = np.asarray(
            [
                deterministic_fold(group, f"BA-SRM4-INNER-V1:{label}:{outer}", INNER_FOLDS)
                for group in groups[train]
            ],
            dtype=int,
        )
        selection = greedy_select(
            x[train], target[train], groups[train], inner_ids, len(base_names), interactions
        )
        x_location, x_scale = robust_location_scale(x[train])
        y_location, y_scale = output_scaler(target[train])
        train_terms = build_terms(transform(x[train], x_location, x_scale), interactions)
        test_terms = build_terms(transform(x[test], x_location, x_scale), interactions)
        selected = selection["selected"]
        beta = fit_ridge(
            train_terms[:, selected], transform(target[train], y_location, y_scale), selection["ridge"]
        )
        prediction_std = predict_ridge(beta, test_terms[:, selected])
        prediction = y_location[None, :] + prediction_std * y_scale[None, :]
        oof_prediction[test] = prediction
        target_std = transform(target[test], y_location, y_scale)
        oof_candidate_error[test] = np.mean((target_std - prediction_std) ** 2, axis=1)
        oof_constant_error[test] = np.mean(target_std**2, axis=1)
        outer_models.append(
            {
                "outer_fold": outer,
                "selected_terms": [term_names[index] for index in selected],
                "ridge": selection["ridge"],
                "inner_cv_mse": selection["cv_mse"],
            }
        )
    if not np.all(np.isfinite(oof_prediction)):
        raise DiscoveryFailure("nested OOF prediction is incomplete")

    selected_frequency = Counter(
        term
        for model in outer_models
        for term in model["selected_terms"]
    )

    final_fold_ids = np.asarray(
        [deterministic_fold(group, f"BA-SRM4-FINAL-INNER-V1:{label}", OUTER_FOLDS) for group in groups],
        dtype=int,
    )
    final_selection = greedy_select(
        x, target, groups, final_fold_ids, len(base_names), interactions
    )
    selected = stability_core_indices(
        term_names, selected_frequency, len(base_names), interactions
    )
    if not selected:
        selected = list(final_selection["selected"])
    final_views = fold_views(x, target, groups, final_fold_ids, interactions)
    stability_cv_mse, stability_ridge = best_ridge_score(final_views, selected)
    x_location, x_scale = robust_location_scale(x)
    y_location, y_scale = output_scaler(target)
    x_standardized = transform(x, x_location, x_scale)
    all_terms = build_terms(x_standardized, interactions)
    beta = fit_ridge(
        all_terms[:, selected], transform(target, y_location, y_scale), stability_ridge
    )

    standardized_oof_residual = (target - oof_prediction) / y_scale[None, :]
    geometry = geometry_receipt(
        x_standardized,
        beta,
        selected,
        base_names,
        interactions,
        standardized_oof_residual,
    )
    design = np.column_stack([np.ones(len(groups)), all_terms[:, selected]])
    penalty = np.eye(design.shape[1]) * stability_ridge
    penalty[0, 0] = 0.0
    edf = float(np.trace(design @ np.linalg.solve(design.T @ design + penalty, design.T)))
    group_deltas = []
    for group in np.unique(groups):
        mask = groups == group
        group_deltas.append(float(np.mean(oof_constant_error[mask] - oof_candidate_error[mask])))
    return {
        "status": "DISCOVERY_EMPIRICAL_CANDIDATE_UNVALIDATED",
        "sequences": int(len(groups)),
        "slice_specimen_groups": int(len(np.unique(groups))),
        "base_representation_dimension": len(base_names),
        "available_base_features": base_names,
        "selected_terms": [term_names[index] for index in selected],
        "selected_term_indices": selected,
        "selection_rule": f"appeared in at least {MIN_OUTER_SELECTION_FOLDS}/{OUTER_FOLDS} outer-training selections; interaction hierarchy preserved",
        "ridge": stability_ridge,
        "stability_core_cv_mse": stability_cv_mse,
        "all_discovery_greedy_candidate": {
            "selected_terms": [term_names[index] for index in final_selection["selected"]],
            "ridge": final_selection["ridge"],
            "cv_mse": final_selection["cv_mse"],
            "status": "superseded by stability core for the frozen candidate",
        },
        "estimated_degrees_of_freedom": edf,
        "edf_below_half_group_count": edf < len(np.unique(groups)) / 2.0,
        "target_names": target_names,
        "input_location": x_location.tolist(),
        "input_scale": x_scale.tolist(),
        "target_location": y_location.tolist(),
        "target_scale": y_scale.tolist(),
        "beta_intercept_then_selected_terms": beta.tolist(),
        "formula": "y_std = beta_0 + sum_t beta_t phi_t(x_std)",
        "nested_discovery_diagnostic": {
            "outer_models": outer_models,
            "group_mean_delta_mse_constant_minus_candidate": float(np.mean(group_deltas)),
            "group_se_delta_mse": float(np.std(group_deltas, ddof=1) / math.sqrt(len(group_deltas))),
            "outer_selection_frequency": dict(sorted(selected_frequency.items())),
            "evidence_status": "discovery-only selection diagnostic, not validation evidence",
        },
        "geometry": geometry,
        "claim_status": "[경험식][미완성]",
    }


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise DiscoveryFailure(f"refusing to overwrite artifact: {path}")
    payload = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    if partial.exists():
        raise DiscoveryFailure(f"stale partial artifact: {partial}")
    partial.write_bytes(payload)
    if partial.read_bytes() != payload:
        raise DiscoveryFailure("output verification failed")
    partial.replace(path)


def discover(dataset_path: Path, receipt_path: Path, output_path: Path) -> dict[str, Any]:
    if sha256_file(dataset_path) != EXPECTED_DATASET_SHA256:
        raise DiscoveryFailure("V2 dataset SHA-256 mismatch")
    if sha256_file(receipt_path) != EXPECTED_RECEIPT_SHA256:
        raise DiscoveryFailure("V2 receipt SHA-256 mismatch")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "PASS_DISCOVERY_DATASET":
        raise DiscoveryFailure("dataset receipt did not pass")
    if receipt.get("validation_outcomes_read") is not False or receipt.get("confirmation_outcomes_read") is not False:
        raise DiscoveryFailure("sealed outcome boundary was violated")
    if receipt.get("all_outcome_rows_predecessor_contacted") is not True:
        raise DiscoveryFailure("discovery quarantine receipt did not pass")
    if receipt.get("schema", {}).get("highest_stable_group_key") != "slice.lims_specimen_name":
        raise DiscoveryFailure("V2 LIMS slice-specimen grouping is not frozen")

    with np.load(dataset_path, allow_pickle=False) as data:
        arrays = {key: data[key] for key in data.files}
    required = {
        "features",
        "target",
        "feature_names",
        "target_names",
        "group_id",
        "synapse_type",
        "pre_clamp_mode",
        "post_clamp_mode",
    }
    if not required.issubset(arrays):
        raise DiscoveryFailure("dataset schema is incomplete")
    features = np.asarray(arrays["features"], dtype=float)
    target = np.asarray(arrays["target"], dtype=float)
    feature_names = [str(value) for value in arrays["feature_names"]]
    target_names = [str(value) for value in arrays["target_names"]]
    groups = np.asarray(arrays["group_id"], dtype=str)
    synapse = np.asarray(arrays["synapse_type"], dtype=str)
    pre_mode = np.asarray(arrays["pre_clamp_mode"], dtype=str)
    post_mode = np.asarray(arrays["post_clamp_mode"], dtype=str)

    strata: dict[str, Any] = {}
    for synapse_type in ("ex", "in"):
        for pre in ("ic", "vc"):
            label = f"{synapse_type}|pre={pre}|post=ic"
            mask = (synapse == synapse_type) & (pre_mode == pre) & (post_mode == "ic")
            if not np.any(mask):
                strata[label] = {"status": "ABSTAIN_NO_ROWS"}
                continue
            if pre == "vc":
                strata[label] = {
                    "status": "ABSTAIN_INSUFFICIENT_GROUPS",
                    "sequences": int(np.sum(mask)),
                    "slice_specimen_groups": int(np.unique(groups[mask]).size),
                    "reason": "typed VC stratum is retained but not pooled with IC",
                }
                continue
            strata[label] = fit_stratum(
                features[mask], target[mask], groups[mask], feature_names, target_names, label
            )

    result = {
        "status": "DISCOVERY_ONLY_CANDIDATES_COMPLETE",
        "version": VERSION,
        "dataset": str(dataset_path.resolve(strict=True)),
        "dataset_sha256": EXPECTED_DATASET_SHA256,
        "dataset_receipt": str(receipt_path.resolve(strict=True)),
        "dataset_receipt_sha256": EXPECTED_RECEIPT_SHA256,
        "split_group_key": "slice.lims_specimen_name",
        "split_group_semantics": "LIMS slice-specimen equivalence class, not donor/animal",
        "candidate_grammar": "fixed order<=2 sparse Volterra bank",
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS,
        "ridge_grid": list(RIDGE_GRID),
        "effective_dimension_lambda_grid": list(EFFECTIVE_DIMENSION_LAMBDAS),
        "strata": strata,
        "validation_outcomes_read": False,
        "confirmation_outcomes_read": False,
        "claim_ceiling": "[경험식][미완성], discovery-only; no route victory or biological/AGI law",
    }
    write_new_json(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = discover(args.dataset, args.receipt, args.output)
    except (DiscoveryFailure, OSError, ValueError, np.linalg.LinAlgError) as exc:
        print(json.dumps({"status": "BLOCKED_DISCOVERY_EQUATION", "error": str(exc)}))
        return 2
    summary = {
        "status": result["status"],
        "strata": {
            key: {
                "status": value["status"],
                "selected_terms": value.get("selected_terms"),
                "groups": value.get("slice_specimen_groups"),
                "delta_mse": value.get("nested_discovery_diagnostic", {}).get(
                    "group_mean_delta_mse_constant_minus_candidate"
                ),
            }
            for key, value in result["strata"].items()
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
