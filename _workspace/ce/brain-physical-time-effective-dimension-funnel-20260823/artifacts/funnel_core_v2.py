"""BA-SRM8 v2: original-index, fail-closed causal covariance primitives."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "candidate-manifest.json"


def canonical(value):
    return (json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    data = canonical(value)
    with path.open("wb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())


def manifest() -> tuple[dict, str]:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids = [x["id"] for x in value["candidates"]]
    if len(ids) != 48 or len(set(ids)) != 48:
        raise ValueError("manifest candidate invariant failed")
    return value, sha(MANIFEST)


def _kernel(c: dict, u: np.ndarray) -> np.ndarray:
    x = c["formula_components"]["kernel"]; p = x["parameters"]
    if x["family"] == "EXP": return np.exp(-u / p["theta"])
    if x["family"] == "BIEXP": return p["a"] * np.exp(-u / p["theta_1"]) + (1-p["a"]) * np.exp(-u / p["theta_2"])
    if x["family"] == "POWER": return (1 + u / p["theta"]) ** (-p["p"])
    if x["family"] == "COMPACT":
        good = u < p["L"]; out = np.zeros_like(u); v = u[good] / p["L"]
        out[good] = np.exp(-1 / (1-v*v)); return out
    raise ValueError("unknown kernel")


def robust(c: dict, x: np.ndarray) -> np.ndarray:
    spec = c["formula_components"]["robust_map"]["parameters"]
    if spec["kind"] == "identity": return x
    radius = np.linalg.norm(x) / math.sqrt(x.size)
    if radius == 0: return np.zeros_like(x)
    factor = min(1., spec["c"] / radius) if spec["kind"] == "radial_huber" else math.tanh(radius/spec["c"]) / (radius/spec["c"])
    return x * factor


def causal_q(c: dict, values: np.ndarray, mask: np.ndarray, clock: np.ndarray, d: np.ndarray, calibration_end: int) -> dict:
    """Use original anchors throughout; never derives rank from numerical rank."""
    n, count = values.shape
    if mask.shape != values.shape or d.shape != (n,) or not 1 <= calibration_end <= count:
        raise ValueError("shape or calibration_end invalid")
    if not (np.isfinite(values).all() and np.isfinite(clock).all() and np.isfinite(d).all()):
        raise ValueError("nonfinite input")
    if np.any(np.diff(clock) <= 0) or np.any((mask != 0) & (mask != 1)) or np.any(d < 0):
        raise ValueError("clock/mask/D invalid")
    tau0 = float(np.median(np.diff(clock)))
    if not math.isfinite(tau0) or tau0 <= 0: raise ValueError("invalid tau0")
    delta = np.r_[1., np.minimum(3., np.diff(clock)/tau0)]
    q = mask.mean(0); gamma = c["formula_components"]["quality_exponent"]
    transformed = np.column_stack([robust(c, d * mask[:,j] * values[:,j]) for j in range(count)])
    covs, rs, neff = [None]*count, np.zeros(count), np.zeros(count)
    reasons = [None]*count
    for t in range(count):
        u = (clock[t]-clock[:t+1])/tau0
        a = _kernel(c,u) * q[:t+1]**gamma * delta[:t+1]
        total = float(a.sum()); nplus = int(np.count_nonzero(a > 0)); rstar = min(n, nplus-1)
        if not math.isfinite(total) or total <= 0: reasons[t] = "ABSTAIN_ZERO_OR_NONFINITE_WEIGHT"; continue
        w = a/total; neff[t] = 1/float(w@w); rs[t] = rstar
        if nplus < 2 or neff[t] < 8: reasons[t] = "ABSTAIN_INSUFFICIENT_INFORMATION"; continue
        x = transformed[:,:t+1]; mean = x@w; centered = x-mean[:,None]
        cov = (centered*w)@centered.T/(1-float(w@w))
        if not np.isfinite(cov).all(): reasons[t] = "ABSTAIN_NONFINITE_COVARIANCE"; continue
        covs[t] = cov
    terms = [float(np.trace(covs[t])/rs[t]) for t in range(calibration_end) if covs[t] is not None and rs[t] > 0]
    if not terms or not np.isfinite(terms).all(): raise ValueError("invalid calibration scale terms")
    cg = float(np.median(terms))
    if not math.isfinite(cg) or cg <= 1e-12: raise ValueError("invalid calibration scale")
    Q = np.full(count,np.nan); min_eigs = np.full(count,np.nan)
    for t,cov in enumerate(covs):
        if cov is None: continue
        eig = np.linalg.eigvalsh(cov/cg); min_eigs[t] = eig.min(); Q[t] = float(np.sum(eig/(eig+1))/rs[t])
    return {"Q":Q,"cG":cg,"covariances":covs,"min_eigs":min_eigs,"n_eff":neff,"n_plus":rs+1,"r_star":rs,"q":q,"reasons":reasons}


def average_rank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="stable"); ranks = np.empty(x.size,float); i=0
    while i < x.size:
        j=i+1
        while j < x.size and x[order[j]] == x[order[i]]: j += 1
        ranks[order[i:j]] = (i+j-1)/2; i=j
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 3 or np.ptp(x) == 0 or np.ptp(y) == 0: return float("nan")
    return float(np.corrcoef(average_rank(x),average_rank(y))[0,1])
