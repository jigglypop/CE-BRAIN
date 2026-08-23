"""Fail-closed causal physical-time covariance primitives for BA-SRM8 F0/F1."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "candidate-manifest.json"


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_fsynced(path: Path, value: object) -> None:
    payload = canonical_bytes(value)
    with path.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def load_manifest() -> tuple[dict, str]:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ids = [item["id"] for item in data["candidates"]]
    if len(ids) != 48 or len(set(ids)) != 48 or data["candidate_count_expected"] != 48:
        raise ValueError("manifest candidate invariant failed")
    return data, sha256_path(MANIFEST_PATH)


def kernel(candidate: dict, u: np.ndarray) -> np.ndarray:
    part = candidate["formula_components"]["kernel"]
    family, p = part["family"], part["parameters"]
    if family == "EXP":
        return np.exp(-u / p["theta"])
    if family == "BIEXP":
        return p["a"] * np.exp(-u / p["theta_1"]) + (1 - p["a"]) * np.exp(-u / p["theta_2"])
    if family == "POWER":
        return (1 + u / p["theta"]) ** (-p["p"])
    if family == "COMPACT":
        inside = u < p["L"]
        out = np.zeros_like(u, dtype=float)
        v = u[inside] / p["L"]
        out[inside] = np.exp(-1 / (1 - v * v))
        return out
    raise ValueError("unknown kernel family")


def robust(candidate: dict, x: np.ndarray) -> np.ndarray:
    spec = candidate["formula_components"]["robust_map"]["parameters"]
    kind = spec["kind"]
    if kind == "identity":
        return x
    radius = np.linalg.norm(x) / math.sqrt(x.size)
    if radius == 0:
        return np.zeros_like(x)
    c = spec["c"]
    if kind == "radial_huber":
        return x * min(1.0, c / radius)
    if kind == "radial_tanh":
        return x * (math.tanh(radius / c) / (radius / c))
    raise ValueError("unknown robust map")


def causal_q(candidate: dict, values: np.ndarray, mask: np.ndarray, clock: np.ndarray, d: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[str | None]]:
    """Return Q and n_eff, abstaining per anchor with NaN Q and a reason."""
    if values.ndim != 2 or values.shape != mask.shape or values.shape[0] != d.size:
        raise ValueError("shape mismatch")
    if not (np.isfinite(values).all() and np.isfinite(clock).all() and np.isfinite(d).all()):
        raise ValueError("nonfinite input")
    if np.any(np.diff(clock) <= 0) or np.any((mask != 0) & (mask != 1)) or np.any(d < 0):
        raise ValueError("invalid clock/mask/D")
    n, t_count = values.shape
    tau0 = float(np.median(np.diff(clock)))
    if not math.isfinite(tau0) or tau0 <= 0:
        raise ValueError("invalid tau0")
    delta = np.empty(t_count)
    delta[0] = 1.0
    delta[1:] = np.minimum(3.0, np.diff(clock) / tau0)
    q = mask.mean(axis=0)
    if np.any(q < 0) or np.any(q > 1):
        raise ValueError("quality out of range")
    gamma = candidate["formula_components"]["quality_exponent"]
    transformed = np.column_stack([robust(candidate, d * (mask[:, j] * values[:, j])) for j in range(t_count)])
    result = np.full(t_count, np.nan)
    neff = np.zeros(t_count)
    reasons: list[str | None] = []
    covariances: list[np.ndarray | None] = []
    for t in range(t_count):
        u = (clock[t] - clock[: t + 1]) / tau0
        a = kernel(candidate, u) * np.power(q[: t + 1], gamma) * delta[: t + 1]
        total = float(a.sum())
        if not math.isfinite(total) or total <= 0:
            reasons.append("ABSTAIN_ZERO_OR_NONFINITE_WEIGHT")
            covariances.append(None)
            continue
        w = a / total
        effective = 1.0 / float(np.dot(w, w))
        neff[t] = effective
        if effective < 8 or np.count_nonzero(a) < 2:
            reasons.append("ABSTAIN_INSUFFICIENT_INFORMATION")
            covariances.append(None)
            continue
        x = transformed[:, : t + 1]
        mean = x @ w
        centered = x - mean[:, None]
        covariance = (centered * w) @ centered.T / (1.0 - float(np.dot(w, w)))
        if not np.isfinite(covariance).all():
            reasons.append("ABSTAIN_NONFINITE_COVARIANCE")
            covariances.append(None)
            continue
        covariances.append(covariance)
        reasons.append(None)
    usable = [c for c in covariances if c is not None]
    if not usable:
        return result, neff, reasons
    ranks = [min(n, max(1, int(np.linalg.matrix_rank(c)))) for c in usable]
    scales = [float(np.trace(c)) / r for c, r in zip(usable, ranks)]
    calibration = scales[: max(1, int(math.ceil(0.7 * len(scales))))]
    c_g = float(np.median(calibration))
    if not math.isfinite(c_g) or c_g <= 1e-12:
        return result, neff, [reason or "ABSTAIN_INVALID_SCALE" for reason in reasons]
    for index, covariance in enumerate(covariances):
        if covariance is None:
            continue
        r_star = min(n, max(1, int(np.linalg.matrix_rank(covariance))))
        eig = np.linalg.eigvalsh(covariance / c_g)
        result[index] = float(np.sum(eig / (eig + 1.0)) / r_star)
    return result, neff, reasons


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3:
        return float("nan")
    ra = np.argsort(np.argsort(a, kind="stable"), kind="stable").astype(float)
    rb = np.argsort(np.argsort(b, kind="stable"), kind="stable").astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])

