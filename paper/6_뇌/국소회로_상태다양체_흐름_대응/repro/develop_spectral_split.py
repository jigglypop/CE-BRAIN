"""Development analysis: spectral splitting and a count-likelihood scoreboard.

DEVELOPMENT ONLY, on the DANDI 001701 asset that chapters 11 and 12 consumed.

Two questions, both raised by chapter 15's development frontier.

First, chapters 11-15 split the state into base and fibre by principal-component
variance.  The skew-product form the theory needs is a statement about invariant
subspaces of the one-step operator, not about variance.  For any fitted operator
R the form is available exactly: order the eigenvalues, take the fast invariant
subspace as the leading orthonormal block Q1 and complete it with Q2, and then

    Q^T R Q = [[A, C], [0, B]],   A = Q1^T R Q1,  B = Q2^T R Q2,  C = Q1^T R Q2

so that in the coordinates s = Q^T x the base s2 evolves on its own and the
fibre s1 is driven by it.  The prediction is unchanged -- this is a change of
coordinates, not a competing model -- so the whole scientific content sits in
the certificates q = ||A||, kappa = ||B^-1|| and q*kappa.

Second, the NMSE denominator is dominated by Poisson counting noise, so every
comparison so far was fought inside a small fraction of the variance.  The
script therefore also scores each predictor by held-out negative-binomial log
likelihood on counts, mapping a predicted Anscombe value back to a count mean
by inverting the transform.  That bridge is declared, not fitted.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import h5py
import numpy as np
import requests

DANDISET = "001701"
VERSION = "0.260120.0303"
ASSET_ID = "3f3d0b16-9b3e-42ac-a5e6-327829df1116"
EXPECTED_SIZE = 12_967_760
EXPECTED_SHA256 = "5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3"

BIN_SECONDS = 0.1
MIN_TRAIN_RATE_HZ = 0.1
RIDGES = (1e-2, 1e-1, 1.0, 10.0, 1e2, 1e3, 1e4)
BASE_DIMENSIONS = (2, 4, 8, 16, 32, 64, 128)
PCA_REFERENCE = {"d": 2, "rank": 48, "lambda": 1e3}
LYAPUNOV_STEPS = 40
LYAPUNOV_TOLERANCE = 1e-10

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


def resolve_asset() -> tuple[Path, dict, bool]:
    cached = os.environ.get("CE_DANDI_001701_CACHE")
    if cached:
        path = Path(cached)
        if path.exists() and path.stat().st_size == EXPECTED_SIZE:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest == EXPECTED_SHA256:
                return path, {"source": "verified_cache", "sha256": digest, "bytes": path.stat().st_size}, False
    api = f"https://api.dandiarchive.org/api/dandisets/{DANDISET}/versions/{VERSION}/assets/{ASSET_ID}/"
    meta = requests.get(api, timeout=60)
    meta.raise_for_status()
    url = meta.json()["contentUrl"][0]
    handle, name = tempfile.mkstemp(suffix=".nwb")
    os.close(handle)
    path = Path(name)
    digest = hashlib.sha256()
    received = 0
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with path.open("wb") as sink:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    sink.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
    actual = digest.hexdigest()
    if received != EXPECTED_SIZE or actual != EXPECTED_SHA256:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"receipt mismatch: bytes={received}, sha256={actual}")
    return path, {"source": "download", "sha256": actual, "bytes": received, "asset_api": api}, True


def ridge(x: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray]:
    x_mean, y_mean = x.mean(axis=0), y.mean(axis=0)
    xc, yc = x - x_mean, y - y_mean
    coefficient = np.linalg.solve(xc.T @ xc + lam * np.eye(x.shape[1]), xc.T @ yc)
    return coefficient, y_mean - x_mean @ coefficient


def lyapunov_norm(a: np.ndarray) -> float:
    size = a.shape[0]
    p = np.eye(size)
    power = a.copy()
    for _ in range(LYAPUNOV_STEPS):
        increment = power.T @ p @ power
        p = p + increment
        if not np.all(np.isfinite(p)):
            return math.inf
        if np.linalg.norm(increment, 2) < LYAPUNOV_TOLERANCE * np.linalg.norm(p, 2):
            if np.linalg.eigvalsh(p).min() <= 0:
                return math.inf
            factor = np.linalg.cholesky(p)
            return float(np.linalg.norm(factor.T @ a @ np.linalg.inv(factor.T), 2))
        power = power @ power
        if not np.all(np.isfinite(power)):
            return math.inf
    return math.inf


def fast_invariant_basis(values: np.ndarray, vectors: np.ndarray, n_fast: int) -> np.ndarray:
    """Real orthonormal basis of the invariant subspace of the n_fast smallest moduli."""
    order = np.argsort(np.abs(values))
    columns: list[np.ndarray] = []
    index = 0
    while len(columns) < n_fast and index < order.size:
        k = order[index]
        if abs(values[k].imag) < 1e-12:
            columns.append(vectors[:, k].real)
            index += 1
        else:
            columns.append(vectors[:, k].real)
            if len(columns) < n_fast:
                columns.append(vectors[:, k].imag)
            index += 2
    matrix = np.column_stack(columns[:n_fast])
    q, _ = np.linalg.qr(matrix)
    return q


def negbin_scoreboard(counts: np.ndarray, predictions: dict[str, np.ndarray], train_rows: np.ndarray, test_rows: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> dict[str, float]:
    """Held-out negative-binomial log likelihood per bin per unit for each predictor."""
    train_counts = counts[train_rows + 1]
    test_counts = counts[test_rows + 1]
    max_count = int(test_counts.max())
    log_factorial = np.concatenate(([0.0], np.cumsum(np.log(np.arange(1, max_count + 1)))))
    lam_train = np.maximum(train_counts.mean(axis=0), 1e-6)
    excess = np.mean((train_counts - lam_train) ** 2 - lam_train, axis=0)
    alpha = np.maximum(excess / np.maximum(lam_train ** 2, 1e-12), 1e-6)
    size = 1.0 / alpha
    index = test_counts.astype(np.int64)

    scores = {}
    for name, state_prediction in predictions.items():
        anscombe = state_prediction * scale + mean
        rate = np.maximum(anscombe ** 2 - 0.375, 1e-6)
        total = 0.0
        for unit in range(counts.shape[1]):
            ladder = np.concatenate(([0.0], np.cumsum(np.log(size[unit] + np.arange(max_count)))))
            column = rate[:, unit]
            total += float(np.mean(
                ladder[index[:, unit]]
                - log_factorial[index[:, unit]]
                + size[unit] * np.log(size[unit] / (size[unit] + column))
                + test_counts[:, unit] * np.log(column / (size[unit] + column))
            ))
        scores[name] = total / counts.shape[1]
    return scores


def main() -> None:
    path, receipt, temporary = resolve_asset()
    try:
        with h5py.File(path, "r") as nwb:
            lfp = nwb["processing/probe_0_channel_160/LFP/LFP"]
            rate_hz = float(lfp["starting_time"].attrs["rate"])
            start = float(lfp["starting_time"][()])
            stop = start + lfp["data"].shape[0] / rate_hz
            spike_times = nwb["units/spike_times"][:]
            spike_index = nwb["units/spike_times_index"][:]

        n_bins = int(math.floor((stop - start) / BIN_SECONDS))
        train_end, dev_end = int(math.floor(0.5 * n_bins)), int(math.floor(0.75 * n_bins))
        boundary = start + train_end * BIN_SECONDS
        edges = start + BIN_SECONDS * np.arange(n_bins + 1)
        starts = np.concatenate(([0], spike_index[:-1]))
        counts = np.empty((n_bins, spike_index.size))
        prefix = np.empty(spike_index.size)
        for unit, (a, b) in enumerate(zip(starts, spike_index)):
            times = spike_times[a:b]
            counts[:, unit] = np.histogram(times, bins=edges)[0]
            prefix[unit] = np.searchsorted(times, boundary)
        counts = counts[:, (prefix / (boundary - start)) >= MIN_TRAIN_RATE_HZ]

        transformed = np.sqrt(counts + 0.375)
        mean = transformed[:train_end].mean(axis=0)
        scale = transformed[:train_end].std(axis=0)
        scale[scale == 0] = 1.0
        state = (transformed - mean) / scale
        n_units = state.shape[1]

        train = np.arange(0, train_end - 1)
        dev = np.arange(train_end, dev_end - 1)
        test = np.arange(dev_end, n_bins - 1)
        denominator = float(np.square(state[test + 1] - state[:train_end].mean(axis=0)).sum())

        best_lambda, best_dev = None, math.inf
        for lam in RIDGES:
            coefficient, intercept = ridge(state[train], state[train + 1], lam)
            score = float(np.square(state[dev + 1] - (state[dev] @ coefficient + intercept)).sum() / denominator)
            if score < best_dev:
                best_lambda, best_dev, best_fit = lam, score, (coefficient, intercept)
        operator, offset = best_fit
        full_var_test = float(np.square(state[test + 1] - (state[test] @ operator + offset)).sum() / denominator)

        # The dynamics act on column vectors as x' = R x, so R is the transpose
        # of the row-convention regression coefficient.
        r_matrix = operator.T
        values, vectors = np.linalg.eig(r_matrix)
        modulus = np.sort(np.abs(values))[::-1]
        condition = float(np.linalg.cond(vectors))

        splits = []
        for m_base in BASE_DIMENSIONS:
            if m_base >= n_units:
                continue
            q1 = fast_invariant_basis(values, vectors, n_units - m_base)
            full_q, _ = np.linalg.qr(q1, mode="complete")
            q2 = full_q[:, q1.shape[1] :]
            a_block = q1.T @ r_matrix @ q1
            b_block = q2.T @ r_matrix @ q2
            leak = float(np.linalg.norm(q2.T @ r_matrix @ q1, 2))
            try:
                kappa = float(np.linalg.norm(np.linalg.inv(b_block), 2))
            except np.linalg.LinAlgError:
                kappa = math.inf
            q_norm = float(np.linalg.norm(a_block, 2))
            splits.append({
                "base_dimension": m_base,
                "q": q_norm,
                "rho_fibre": float(np.max(np.abs(np.linalg.eigvals(a_block)))),
                "norm_p": lyapunov_norm(a_block),
                "kappa": kappa,
                "q_kappa": q_norm * kappa,
                "rho_base_min": float(np.min(np.abs(np.linalg.eigvals(b_block)))),
                "block_leak_norm": leak,
            })

        eigen_values, eigen_vectors = values, vectors
        inverse = np.linalg.inv(eigen_vectors)
        order = np.argsort(np.abs(eigen_values))[::-1]
        truncations = {}
        predictions = {"train_mean": np.broadcast_to(state[train + 1].mean(axis=0), (test.size, n_units)).copy()}
        for m_base in BASE_DIMENSIONS:
            if m_base >= n_units:
                continue
            keep = np.zeros(n_units, dtype=complex)
            keep[order[:m_base]] = eigen_values[order[:m_base]]
            reduced = np.real(eigen_vectors @ np.diag(keep) @ inverse)
            estimate = state[test] @ reduced.T + offset
            truncations[m_base] = float(np.square(state[test + 1] - estimate).sum() / denominator)
            if m_base in (8, 32):
                predictions[f"modal_{m_base}"] = estimate
        predictions["full_var"] = state[test] @ operator + offset

        z_basis = np.linalg.svd(state[:train_end], full_matrices=False)[2].T
        d, rank, lam = PCA_REFERENCE["d"], PCA_REFERENCE["rank"], PCA_REFERENCE["lambda"]
        z, y = state @ z_basis[:, :d], state @ z_basis[:, d:]
        b_matrix, b_intercept = ridge(z[train], z[train + 1], lam)
        fibre, fibre_intercept = ridge(np.c_[y[train], z[train]], y[train + 1], lam)
        a_full, c_block = fibre[: y.shape[1]], fibre[y.shape[1] :]
        fvt = np.linalg.svd(y[train] @ a_full, full_matrices=False)[2]
        projector = fvt[:rank].T @ fvt[:rank]
        packed = np.vstack((a_full @ projector, c_block))
        pca_estimate = (z[test] @ b_matrix + b_intercept) @ z_basis[:, :d].T + (np.c_[y[test], z[test]] @ packed + fibre_intercept) @ z_basis[:, d:].T
        predictions["pca_reduced_rank"] = pca_estimate

        likelihoods = negbin_scoreboard(counts, predictions, train, test, mean, scale)

        report = {
            "track": "DEVELOPMENT_ONLY",
            "n_units": int(n_units),
            "n_bins": int(n_bins),
            "full_var": {"lambda": best_lambda, "development_nmse": best_dev, "test_nmse": full_var_test},
            "eigenvalue_moduli_top30": modulus[:30].tolist(),
            "eigenvalue_moduli_summary": {
                "above_0.9": int((modulus > 0.9).sum()),
                "above_0.7": int((modulus > 0.7).sum()),
                "above_0.5": int((modulus > 0.5).sum()),
                "above_0.3": int((modulus > 0.3).sum()),
                "max": float(modulus[0]),
            },
            "eigenvector_condition_number": condition,
            "ordered_schur_splits": splits,
            "modal_truncation_test_nmse": truncations,
            "pca_reduced_rank_test_nmse": float(np.square(state[test + 1] - pca_estimate).sum() / denominator),
            "negbin_loglik_per_bin_per_unit": likelihoods,
            "claim_ceiling": "Development measurement on a consumed asset; not a result about the recording family.",
            "source_receipt": receipt,
        }
        (HERE / "development-spectral-split.json").write_text(json.dumps(jsonable(report), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(jsonable({k: v for k, v in report.items() if k not in ("eigenvalue_moduli_top30", "source_receipt")}), indent=2))
    finally:
        if temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
