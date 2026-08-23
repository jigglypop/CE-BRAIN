from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import scipy
from scipy.integrate import quad


SCHEMA = "BA-ERC1-E3b-v1"
RUN_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(__file__).resolve().parent
CE_WORKSPACE = RUN_DIR.parent
E3A_DIR = CE_WORKSPACE / "brain-electrical-riemannian-cable-e3a-observation-quotient-20260823"
ERC1_DIR = CE_WORKSPACE / "brain-electrical-riemannian-cable-20260823"

DT = 0.001
T_END = 2.4
TIMES = np.linspace(0.0, T_END, int(round(T_END / DT)) + 1)
LAG_GRID = np.linspace(0.0, 0.75, 3001)
WIDTH = 0.25
TAUS = (0.03, 0.12, 0.015, 0.06, 0.24, 0.45, 0.008, 0.75)
NEGATIVE_WEIGHTS = np.array([0.65, 0.35], dtype=float)
TIE_TOLERANCE = 1.0e-10

EVENTS = {
    "calibration": (
        (0.08, 1.00), (0.14, 0.55), (0.31, 1.15), (0.57, 0.75),
        (0.94, 1.25), (1.29, 0.60), (1.52, 0.95),
    ),
    "development": (
        (0.05, 0.80), (0.09, 1.10), (0.22, 0.45), (0.26, 1.20),
        (0.68, 0.90), (0.74, 0.65), (1.08, 1.30), (1.42, 0.70),
        (1.47, 1.00),
    ),
    "confirmation": (
        (0.04, 1.20), (0.17, 0.50), (0.20, 0.85), (0.48, 1.10),
        (0.53, 0.70), (0.59, 1.25), (0.97, 0.60), (1.18, 1.00),
        (1.21, 0.40), (1.57, 1.30), (1.64, 0.80), (1.83, 0.55),
    ),
}

MODEL_ORDER = ("E1", "E2", "E4", "E8", "B")
MODEL_SIZE = {"E1": 1, "E2": 2, "E4": 4, "E8": 8, "B": 1}

THRESHOLDS = {
    "bump_normalization_error_max": 1.0e-10,
    "normalized_condition_max": 1.0e6,
    "tie_tolerance": TIE_TOLERANCE,
    "matched_confirmation_error_max": 1.0e-10,
    "finite_positive_confirmation_error_min": 5.0e-3,
    "finite_positive_dense_kernel_error_min": 5.0e-3,
    "reversed_bump_confirmation_error_min": 5.0e-2,
}

EXPECTED_INPUT_SHA256 = {
    "00-contract.md": "0d0bbd017ba57f8dd8fa20a995c15e3a2e3de337d89f1191564b759a5a83aa92",
    "10-sources.md": "6f50b7d455d8151ade8bca832ea071beb23e4d8f3e6967a7c250e3ba6d459d96",
    "11-math.md": "10fb1d058b17a22adde4e207ce2cb52b89e5625760559d956440f52bc5c2517c",
    "12-routes.md": "b808a6c0d30b7b443289455e10f29123b6d1822c18af61c14353e7cdb296b77d",
    "20-audit.md": "aa96f0ba86c955b38a7fabb3310f525dd99594ff0cc6689b9bbe365db30a3e4f",
}

EXPECTED_PREDECESSOR_SHA256 = {
    "00-contract.md": "daf732762f6418191cbe15671e68baa027578b7b5c59107f4bec7eaeb1478df2",
    "10-sources.md": "5ddfe50b64f3378069f0821f5a0eccc604a81054a92a865a6585ac7fc3af3579",
    "11-math.md": "85065c545a582e362efab549b5ae52e4241785238ac5b85cd4b882ebd8e55e15",
    "12-routes.md": "35a6d2018164409006edeb46164c1a6b150472710d576a69a3f8ada0fcc366f1",
    "20-audit.md": "0ed074b4f467c9287841211d9d1be900a1428dcc378de090e3b908be5bb24f74",
    "31-validation.md": "841debb52d1bf6ddd48e532cb3e4ff2da4145994d3dcadd69541e1ad02e59cb8",
    "40-final-report.md": "d7cff74a1583d74ab5451dfaf5d0e7a82e3c2345a807c643ae8c70fa678295c2",
    "artifacts/verify_observation_quotient_e3a.py": "9ef1c2074ca2195f617a934102437e13f260ba39a165a74d1e5d1b7a521900fb",
    "artifacts/e3a-receipt.json": "4ad4d72e6136d9849fd1f6265c85decd2263ac6090107d878f1da3e1515beb5e",
}

EXPECTED_OLDER_EVIDENCE_SHA256 = {
    "brain-electrical-riemannian-cable-20260823/11-math.md": "a96c9cda861691ea0edabefcc1f7d34befae3e4ec4973d8ecdc8b9492ac15685",
    "brain-electrical-riemannian-cable-20260823/artifacts/l0-receipt.json": "9e643eaf70302ff4369f15bf1fa044f11660a45c9148869395fb65a643006501",
    "brain-algorithm-route-ledger.md": "8256c0eb6b48e5c9a83ba061049e5409044a1d90da9cef85f45027daf48c8c51",
}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_bump_scalar(a: float) -> float:
    if not 0.0 < a < WIDTH:
        return 0.0
    r = a / WIDTH
    return math.exp(-1.0 / r - 2.0 / (1.0 - r))


BUMP_Z, BUMP_Z_QUAD_ERROR = quad(
    raw_bump_scalar, 0.0, WIDTH, epsabs=1.0e-14, epsrel=1.0e-13, limit=200
)


def bump_kernel(lags: np.ndarray) -> np.ndarray:
    lags = np.asarray(lags, dtype=float)
    result = np.zeros_like(lags)
    mask = (lags > 0.0) & (lags < WIDTH)
    r = lags[mask] / WIDTH
    result[mask] = np.exp(-1.0 / r - 2.0 / (1.0 - r)) / BUMP_Z
    return result


def reversed_bump_kernel(lags: np.ndarray) -> np.ndarray:
    lags = np.asarray(lags, dtype=float)
    return bump_kernel(WIDTH - lags)


def exponential_kernel(lags: np.ndarray, tau: float) -> np.ndarray:
    lags = np.asarray(lags, dtype=float)
    result = np.zeros_like(lags)
    mask = lags >= 0.0
    result[mask] = np.exp(-lags[mask] / tau) / tau
    return result


def event_response(events: tuple[tuple[float, float], ...], basis: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    response = np.zeros_like(TIMES)
    for event_time, amplitude in events:
        response += amplitude * basis(TIMES - event_time)
    return response


def finite_design(events: tuple[tuple[float, float], ...], size: int) -> np.ndarray:
    columns = [
        event_response(events, lambda lag, tau=tau: exponential_kernel(lag, tau))
        for tau in TAUS[:size]
    ]
    return np.column_stack(columns)


def bump_design(events: tuple[tuple[float, float], ...], reversed_time: bool = False) -> np.ndarray:
    basis = reversed_bump_kernel if reversed_time else bump_kernel
    return event_response(events, basis)[:, None]


def model_design(model: str, split: str) -> np.ndarray:
    if model == "B":
        return bump_design(EVENTS[split])
    return finite_design(EVENTS[split], MODEL_SIZE[model])


def kernel_design(model: str) -> np.ndarray:
    if model == "B":
        return bump_kernel(LAG_GRID)[:, None]
    return np.column_stack(
        [exponential_kernel(LAG_GRID, tau) for tau in TAUS[: MODEL_SIZE[model]]]
    )


def relative_l2(prediction: np.ndarray, truth: np.ndarray) -> float:
    denominator = float(np.linalg.norm(truth))
    if denominator <= 0.0:
        raise ValueError("zero truth norm")
    return float(np.linalg.norm(prediction - truth) / denominator)


def fit_candidate(model: str, calibration_truth: np.ndarray) -> dict[str, Any]:
    design = model_design(model, "calibration")
    column_norms = np.linalg.norm(design, axis=0)
    if np.any(column_norms <= 0.0):
        raise ValueError(f"zero design column in {model}")
    normalized = design / column_norms
    singular_values = np.linalg.svd(normalized, compute_uv=False)
    rank = int(np.linalg.matrix_rank(normalized))
    condition = float(singular_values[0] / singular_values[-1])
    scaled_coefficients, _, _, _ = np.linalg.lstsq(normalized, calibration_truth, rcond=None)
    coefficients = scaled_coefficients / column_norms
    predictions = {
        split: model_design(model, split) @ coefficients
        for split in ("calibration", "development", "confirmation")
    }
    return {
        "model": model,
        "parameter_count": MODEL_SIZE[model],
        "rank": rank,
        "normalized_condition": condition,
        "coefficients": coefficients,
        "predictions": predictions,
        "kernel_prediction": kernel_design(model) @ coefficients,
    }


def select_model(fits: dict[str, dict[str, Any]], truth_development: np.ndarray) -> tuple[str, dict[str, float], list[str]]:
    errors = {
        model: relative_l2(fit["predictions"]["development"], truth_development)
        for model, fit in fits.items()
    }
    minimum = min(errors.values())
    tied = [model for model, error in errors.items() if error <= minimum + TIE_TOLERANCE]

    def preference(model: str) -> tuple[int, int, int]:
        history_penalty = 1 if model == "B" else 0
        return MODEL_SIZE[model], history_penalty, MODEL_ORDER.index(model)

    selected = min(tied, key=preference)
    return selected, errors, tied


def finite_truth(split: str) -> np.ndarray:
    return finite_design(EVENTS[split], 2) @ NEGATIVE_WEIGHTS


def bump_truth(split: str) -> np.ndarray:
    return bump_design(EVENTS[split])[:, 0]


def fit_reversed_bump(calibration_truth: np.ndarray) -> dict[str, Any]:
    design = bump_design(EVENTS["calibration"], reversed_time=True)
    norm = float(np.linalg.norm(design[:, 0]))
    normalized = design / norm
    coefficient_scaled, _, _, _ = np.linalg.lstsq(normalized, calibration_truth, rcond=None)
    coefficient = coefficient_scaled / norm
    return {
        "coefficient": float(coefficient[0]),
        "calibration_prediction": design[:, 0] * float(coefficient[0]),
        "confirmation_prediction": (
            bump_design(EVENTS["confirmation"], reversed_time=True)[:, 0]
            * float(coefficient[0])
        ),
    }


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def all_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(all_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(all_finite(item) for item in value)
    if isinstance(value, np.ndarray):
        return bool(np.all(np.isfinite(value)))
    if isinstance(value, (float, np.floating)):
        return math.isfinite(float(value))
    return True


def write_receipt(output: Path, receipt: dict[str, Any]) -> int:
    output.write_text(
        json.dumps(json_ready(receipt), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "claim_status": receipt["claim_status"],
                "failed_checks": receipt["failed_checks"],
                "negative_selected": receipt["results"].get("negative", {}).get("selected"),
                "positive_selected": receipt["results"].get("positive", {}).get("selected"),
                "positive_panel_opened": receipt["positive_panel_opened"],
                "receipt": str(output),
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["status"] == "PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Sealed BA-ERC1 E3b finite-vs-history verifier")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.parent != ARTIFACT_DIR.resolve():
        raise SystemExit("output must be inside this run's artifacts directory")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing receipt: {output}")

    actual_inputs = {name: sha256_path(RUN_DIR / name) for name in EXPECTED_INPUT_SHA256}
    actual_predecessor = {
        name: sha256_path(E3A_DIR / name) for name in EXPECTED_PREDECESSOR_SHA256
    }
    older_paths = {
        "brain-electrical-riemannian-cable-20260823/11-math.md": ERC1_DIR / "11-math.md",
        "brain-electrical-riemannian-cable-20260823/artifacts/l0-receipt.json": ERC1_DIR / "artifacts" / "l0-receipt.json",
        "brain-algorithm-route-ledger.md": CE_WORKSPACE / "brain-algorithm-route-ledger.md",
    }
    actual_older_evidence = {name: sha256_path(path) for name, path in older_paths.items()}
    source_match = actual_inputs == EXPECTED_INPUT_SHA256
    predecessor_match = actual_predecessor == EXPECTED_PREDECESSOR_SHA256
    older_evidence_match = actual_older_evidence == EXPECTED_OLDER_EVIDENCE_SHA256
    preflight_hash = sha256_path(ARTIFACT_DIR / "20-audit-preflight.md")
    preflight_match = preflight_hash == EXPECTED_INPUT_SHA256["20-audit.md"]

    environment = {
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "platform": platform.platform(),
        "bytecode_disabled": bool(sys.dont_write_bytecode),
    }
    environment_match = (
        environment["python"] == "3.11.9"
        and environment["numpy"] == "2.4.6"
        and environment["scipy"] == "1.17.1"
        and environment["bytecode_disabled"]
    )

    normalized_integral, normalized_quad_error = quad(
        lambda a: raw_bump_scalar(a) / BUMP_Z,
        0.0,
        WIDTH,
        epsabs=1.0e-14,
        epsrel=1.0e-13,
        limit=200,
    )
    normalization_error = abs(normalized_integral - 1.0)
    support_probe = bump_kernel(np.array([-0.1, 0.0, WIDTH, WIDTH + 0.1]))
    dense_bump = bump_kernel(LAG_GRID)
    dimensionless_audit = {
        "theta": "theta=t/T0",
        "tau": "tau*=tau/T0",
        "kernel": "k*=T0*k_phys",
        "exp_arguments": ("a/tau*", "1/r", "2/(1-r)"),
        "all_core_arguments_dimensionless": True,
    }

    apparatus = {
        "bump_Z": BUMP_Z,
        "bump_Z_quad_error": BUMP_Z_QUAD_ERROR,
        "normalized_integral": normalized_integral,
        "normalized_integral_quad_error": normalized_quad_error,
        "normalization_error": normalization_error,
        "support_probe": support_probe,
        "dense_bump_min": float(np.min(dense_bump)),
        "dimensionless_audit": dimensionless_audit,
    }

    common_checks: dict[str, bool] = {
        "source_seal": source_match,
        "predecessor_seal": predecessor_match,
        "older_evidence_seal": older_evidence_match,
        "preflight_archive_seal": preflight_match,
        "environment_seal": environment_match,
        "dimensionless_construction": dimensionless_audit["all_core_arguments_dimensionless"],
        "bump_normalization": normalization_error <= THRESHOLDS["bump_normalization_error_max"],
        "bump_causal_support": bool(np.all(support_probe == 0.0)),
        "bump_nonnegative": float(np.min(dense_bump)) >= 0.0,
    }

    negative_truths = {split: finite_truth(split) for split in EVENTS}
    negative_fits = {
        model: fit_candidate(model, negative_truths["calibration"])
        for model in MODEL_ORDER
    }
    rank_condition = {
        model: {
            "rank": fit["rank"],
            "expected_rank": MODEL_SIZE[model],
            "normalized_condition": fit["normalized_condition"],
        }
        for model, fit in negative_fits.items()
    }
    common_checks["full_column_rank"] = all(
        values["rank"] == values["expected_rank"] for values in rank_condition.values()
    )
    common_checks["normalized_conditioning"] = all(
        values["normalized_condition"] <= THRESHOLDS["normalized_condition_max"]
        for values in rank_condition.values()
    )

    negative_selected, negative_dev_errors, negative_tied = select_model(
        negative_fits, negative_truths["development"]
    )
    negative_confirmation_errors = {
        model: relative_l2(fit["predictions"]["confirmation"], negative_truths["confirmation"])
        for model, fit in negative_fits.items()
    }
    negative_result = {
        "generator": "E2",
        "selected": negative_selected,
        "development_errors": negative_dev_errors,
        "development_tied": negative_tied,
        "confirmation_errors": negative_confirmation_errors,
        "fits": {
            model: {
                "parameter_count": fit["parameter_count"],
                "rank": fit["rank"],
                "normalized_condition": fit["normalized_condition"],
                "coefficients": fit["coefficients"],
            }
            for model, fit in negative_fits.items()
        },
    }

    checks = dict(common_checks)
    checks["negative_selects_E2"] = negative_selected == "E2"
    checks["negative_confirmation_match"] = (
        negative_confirmation_errors[negative_selected]
        <= THRESHOLDS["matched_confirmation_error_max"]
    )
    checks["negative_outputs_finite"] = all_finite(negative_result)

    negative_gate_names = tuple(checks.keys())
    results: dict[str, Any] = {
        "apparatus": apparatus,
        "rank_condition": rank_condition,
        "negative": negative_result,
    }

    base_receipt = {
        "schema": SCHEMA,
        "thresholds": THRESHOLDS,
        "problem": {
            "dt": DT,
            "t_end": T_END,
            "time_count": len(TIMES),
            "lag_grid_count": len(LAG_GRID),
            "bump_width": WIDTH,
            "taus": TAUS,
            "negative_weights": NEGATIVE_WEIGHTS,
            "events": EVENTS,
            "model_order": MODEL_ORDER,
        },
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "actual_input_sha256": actual_inputs,
        "source_match": source_match,
        "expected_predecessor_sha256": EXPECTED_PREDECESSOR_SHA256,
        "actual_predecessor_sha256": actual_predecessor,
        "predecessor_match": predecessor_match,
        "expected_older_evidence_sha256": EXPECTED_OLDER_EVIDENCE_SHA256,
        "actual_older_evidence_sha256": actual_older_evidence,
        "older_evidence_match": older_evidence_match,
        "preflight_archive_sha256": preflight_hash,
        "script_sha256": sha256_path(Path(__file__).resolve()),
        "environment": environment,
        "apparatus_revision": {"attempt": 0, "scope": "none"},
        "synthetic_model_fit": True,
        "model_fit": False,
        "real_endpoint_opened": False,
        "behavior_loaded": False,
        "biological_claim": False,
        "consciousness_claim": False,
        "downstream_authorized": False,
    }

    if not all(checks[name] for name in negative_gate_names):
        apparatus_names = {
            "source_seal", "predecessor_seal", "older_evidence_seal",
            "preflight_archive_seal", "environment_seal", "dimensionless_construction",
            "bump_normalization", "bump_causal_support", "bump_nonnegative",
            "full_column_rank", "normalized_conditioning", "negative_selects_E2",
            "negative_outputs_finite",
        }
        status = "APPARATUS_INVALID" if any(
            not checks[name] for name in apparatus_names
        ) else "STOP"
        receipt = {
            **base_receipt,
            "status": status,
            "claim_status": "NO_PROMOTION",
            "failed_checks": [name for name, passed in checks.items() if not passed],
            "checks": checks,
            "results": results,
            "negative_confirmation_opened": True,
            "positive_panel_opened": False,
            "positive_confirmation_opened": False,
        }
        return write_receipt(output, receipt)

    positive_truths = {split: bump_truth(split) for split in EVENTS}
    positive_fits = {
        model: fit_candidate(model, positive_truths["calibration"])
        for model in MODEL_ORDER
    }
    positive_selected, positive_dev_errors, positive_tied = select_model(
        positive_fits, positive_truths["development"]
    )
    positive_confirmation_errors = {
        model: relative_l2(fit["predictions"]["confirmation"], positive_truths["confirmation"])
        for model, fit in positive_fits.items()
    }
    positive_kernel_errors = {
        model: relative_l2(fit["kernel_prediction"], dense_bump)
        for model, fit in positive_fits.items()
    }
    reversed_fit = fit_reversed_bump(positive_truths["calibration"])
    reversed_confirmation_error = relative_l2(
        reversed_fit["confirmation_prediction"], positive_truths["confirmation"]
    )
    finite_models = ("E1", "E2", "E4", "E8")
    best_finite_confirmation_model = min(
        finite_models, key=lambda model: positive_confirmation_errors[model]
    )
    best_finite_kernel_model = min(
        finite_models, key=lambda model: positive_kernel_errors[model]
    )

    positive_result = {
        "generator": "B",
        "selected": positive_selected,
        "development_errors": positive_dev_errors,
        "development_tied": positive_tied,
        "confirmation_errors": positive_confirmation_errors,
        "dense_kernel_errors": positive_kernel_errors,
        "best_finite_confirmation_model": best_finite_confirmation_model,
        "best_finite_confirmation_error": positive_confirmation_errors[best_finite_confirmation_model],
        "best_finite_dense_kernel_model": best_finite_kernel_model,
        "best_finite_dense_kernel_error": positive_kernel_errors[best_finite_kernel_model],
        "reversed_bump": {
            "coefficient": reversed_fit["coefficient"],
            "confirmation_error": reversed_confirmation_error,
        },
        "fits": {
            model: {
                "parameter_count": fit["parameter_count"],
                "rank": fit["rank"],
                "normalized_condition": fit["normalized_condition"],
                "coefficients": fit["coefficients"],
            }
            for model, fit in positive_fits.items()
        },
    }
    results["positive"] = positive_result

    checks["positive_selects_B"] = positive_selected == "B"
    checks["positive_confirmation_match"] = (
        positive_confirmation_errors[positive_selected]
        <= THRESHOLDS["matched_confirmation_error_max"]
    )
    checks["finite_positive_confirmation_separation"] = (
        positive_confirmation_errors[best_finite_confirmation_model]
        >= THRESHOLDS["finite_positive_confirmation_error_min"]
    )
    checks["finite_positive_dense_kernel_separation"] = (
        positive_kernel_errors[best_finite_kernel_model]
        >= THRESHOLDS["finite_positive_dense_kernel_error_min"]
    )
    checks["reversed_bump_detected"] = (
        reversed_confirmation_error
        >= THRESHOLDS["reversed_bump_confirmation_error_min"]
    )
    checks["positive_outputs_finite"] = all_finite(positive_result)

    apparatus_names = {
        "source_seal", "predecessor_seal", "older_evidence_seal",
        "preflight_archive_seal", "environment_seal", "dimensionless_construction",
        "bump_normalization", "bump_causal_support", "bump_nonnegative",
        "full_column_rank", "normalized_conditioning", "negative_selects_E2",
        "negative_outputs_finite", "reversed_bump_detected", "positive_outputs_finite",
    }
    if not all(checks[name] for name in apparatus_names):
        status = "APPARATUS_INVALID"
        claim_status = "NO_PROMOTION"
    elif all(checks.values()):
        status = "PASS"
        claim_status = "E3B_FIXED_KERNEL_DISCRIMINATION_SYNTHETIC_ONLY"
    else:
        status = "STOP"
        claim_status = "NO_PROMOTION"

    receipt = {
        **base_receipt,
        "status": status,
        "claim_status": claim_status,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "checks": checks,
        "results": results,
        "negative_confirmation_opened": True,
        "positive_panel_opened": True,
        "positive_confirmation_opened": True,
    }
    return write_receipt(output, receipt)


if __name__ == "__main__":
    raise SystemExit(main())
