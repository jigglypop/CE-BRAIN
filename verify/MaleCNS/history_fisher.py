"""Exact adjacent-observation likelihoods and full-path efficacy information.

The full raw operator, fixed initial probes, and three supplied log-efficacy
coordinates are reused. A two-time marginal is not an all-history likelihood.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np
import scipy
from scipy import sparse

PARENT_SOURCE = Path(__file__).with_name("connection_fisher.py")
SPEC = importlib.util.spec_from_file_location("malecns_connection_base", PARENT_SOURCE)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
TOL = 5e-9
LEVELS = ("endpoint30", "endpoint60", "endpoint_refined", "pair30", "pair60", "full_path")


def psd_min(matrix, name):
    if not np.isfinite(matrix).all():
        raise ValueError(f"nonfinite {name}")
    eigen = np.linalg.eigvalsh(matrix)
    scale = np.maximum(1., np.max(np.abs(eigen), axis=-1))
    minimum = float(np.min(eigen[..., 0] / scale))
    if minimum < -TOL:
        raise ValueError(f"{name} is not PSD within numerical tolerance")
    return minimum


def pair_operator(a, b, observed, codes):
    """Rows are previous-observation * output-count + current-observation."""
    count = 2 * b.shape[0]
    readout = sparse.vstack((observed @ a, b), format="csc")
    for block, source, _ in base.entry_blocks(readout):
        readout.indices[block] += count * codes[source]
    paired = sparse.csc_array((readout.data, readout.indices, readout.indptr),
                              shape=(count * count, a.shape[1]))
    if not paired.has_canonical_format:
        raise ValueError("pair source/observation mapping is not canonical")
    return paired


def source_covariance(fa, fb, means, codes, assigned):
    moment = np.empty((3, 3, len(codes)))
    for k in range(3):
        moment[k, k] = means[k]
    moment[0, 1] = moment[1, 0] = base.columns(fa[1])
    moment[0, 2] = moment[2, 0] = means[2]
    overlap = base.same_category(fa[2], codes, assigned)
    moment[1, 2] = moment[2, 1] = base.columns(overlap)
    covariance = moment - means[:, None, :] * means[None, :, :]
    minimum = 0.
    for start in range(0, len(codes), 65536):
        minimum = min(minimum, psd_min(np.moveaxis(covariance[:, :, start:start + 65536], -1, 0), "source feature covariance"))
    return covariance, minimum


def paired_observation(w, active, absorbed, count):
    result = (w @ active).reshape(count, count, active.shape[1])
    terminal = np.arange(count // 2, count)
    result[terminal, terminal] += absorbed
    return result


def paired_tangent(w, wk, means, active, da, db, count):
    values = np.stack([w @ (da[k] - means[k, :, None] * active) + wk[k] @ active for k in range(3)])
    result = values.reshape(3, count, count, active.shape[1])
    terminal = np.arange(count // 2, count)
    result[:, terminal, terminal] += db
    return result


def coarse_pair(pair, categories):
    return (pair[..., :categories, :categories, :] + pair[..., :categories, categories:, :] +
            pair[..., categories:, :categories, :] + pair[..., categories:, categories:, :])


def joint_fisher(pair, tangent):
    return base.fisher(pair.reshape(-1, pair.shape[-1]), tangent.reshape(3, -1, pair.shape[-1]))


def tangent_run(a, b, observed, fa, fb, means, w, wk, covariance, initial, steps,
                endpoint_truth, endpoint_jacobian, endpoint_fisher):
    n, probes = initial.shape
    categories, count = b.shape[0], 2 * b.shape[0]
    active, absorbed = initial.copy(), np.zeros((categories, probes))
    da, db = np.zeros((3, n, probes)), np.zeros((3, categories, probes))
    pairs = np.zeros((steps + 1, count, count, probes))
    jacobian = np.zeros((*pairs.shape, 4))
    information = np.zeros((steps + 1, probes, len(LEVELS), 4, 4))
    information[:, :, :3] = endpoint_fisher
    diagonal = np.arange(count)
    pairs[0, diagonal, diagonal] = np.vstack((observed @ active, absorbed))
    path = np.zeros((probes, 3, 3))
    checks = {"marginal_probability_max_error": 0., "marginal_tangent_max_error": 0.,
              "joint_mass_max_error": 0., "joint_tangent_mass_max_error": 0.,
              "scaled_loewner_min_eigenvalue": 0.}
    for step in range(1, steps + 1):
        pair = paired_observation(w, active, absorbed, count)
        tangent = paired_tangent(w, wk, means, active, da, db, count)
        increment = (covariance.reshape(9, n) @ active).reshape(3, 3, probes).transpose(2, 0, 1)
        psd_min(increment, "path information increment")
        path += increment
        if not np.isfinite(pair).all() or np.min(pair) < 0:
            raise ValueError("invalid joint probability")
        checks["joint_mass_max_error"] = max(checks["joint_mass_max_error"], float(np.max(np.abs(pair.sum(axis=(0, 1)) - 1))))
        checks["joint_tangent_mass_max_error"] = max(checks["joint_tangent_mass_max_error"], float(np.max(np.abs(tangent.sum(axis=(1, 2))))))
        for marginal, expected in ((pair.sum(axis=1), endpoint_truth[step - 1]), (pair.sum(axis=0), endpoint_truth[step])):
            checks["marginal_probability_max_error"] = max(checks["marginal_probability_max_error"], float(np.max(np.abs(marginal - expected))))
        for marginal, expected in ((tangent.sum(axis=2), endpoint_jacobian[step - 1, :, :, :3].transpose(2, 0, 1)),
                                   (tangent.sum(axis=1), endpoint_jacobian[step, :, :, :3].transpose(2, 0, 1))):
            checks["marginal_tangent_max_error"] = max(checks["marginal_tangent_max_error"], float(np.max(np.abs(marginal - expected))))
        if any(value > TOL for key, value in checks.items() if key != "scaled_loewner_min_eigenvalue"):
            raise ValueError("joint probability, tangent mass or sealed marginal replay failed")
        g30 = joint_fisher(coarse_pair(pair, categories), coarse_pair(tangent, categories))
        g60 = joint_fisher(pair, tangent)
        current = endpoint_fisher[step, :, :, :3, :3]
        previous = endpoint_fisher[step - 1, :, :, :3, :3]
        differences = (g30, g60 - g30, g30 - current[:, 0], g60 - current[:, 1],
                       g30 - previous[:, 0], g60 - previous[:, 1], path - g60, path - current[:, 2])
        for matrix in differences:
            checks["scaled_loewner_min_eigenvalue"] = min(checks["scaled_loewner_min_eigenvalue"], psd_min(matrix, "nested observation information"))
        pairs[step], jacobian[step, :, :, :, :3] = pair, tangent.transpose(1, 2, 3, 0)
        information[step, :, 3:, :3, :3] = np.stack((g30, g60, path), axis=1)
        if step < steps:
            next_active = a @ active
            for k in range(3):
                centered = da[k] - means[k, :, None] * active
                db[k] += b @ centered + fb[k] @ active
                da[k] = a @ centered + (next_active if k == 0 else fa[k] @ active)
            absorbed += b @ active
            active = next_active
    if np.max(np.abs(information[1, :, 4] - endpoint_fisher[1, :, 1])) > TOL:
        raise ValueError("fixed initial category adds no first-step pair information")
    return pairs, jacobian, information, checks


def nonlinear_pairs(a, b, observed, w, initial, steps):
    count = 2 * b.shape[0]
    active, absorbed = initial.copy(), np.zeros((b.shape[0], initial.shape[1]))
    output = np.zeros((steps + 1, count, count, initial.shape[1]))
    diagonal = np.arange(count)
    output[0, diagonal, diagonal] = np.vstack((observed @ active, absorbed))
    for step in range(1, steps + 1):
        pair = paired_observation(w, active, absorbed, count)
        if not np.isfinite(pair).all() or np.min(pair) < 0 or np.max(np.abs(pair.sum(axis=(0, 1)) - 1)) > TOL:
            raise ValueError("invalid nonlinear pair probability")
        output[step] = pair
        if step < steps:
            absorbed += b @ active
            active = a @ active
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-result", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--batch-cohorts", type=int, default=3)
    parser.add_argument("--max-working-gib", type=float, default=10)
    args = parser.parse_args()
    if args.cache_dir.exists() or args.result.exists():
        raise FileExistsError("preserve all existing outputs")
    if args.batch_cohorts < 1:
        raise ValueError("positive batch size required")
    started = time.perf_counter()
    parent = json.loads(args.parent_result.read_text(encoding="utf-8"))
    digest = base.prior.base.digest
    if parent.get("schema") != "malecns-connection-fisher-v1" or digest(PARENT_SOURCE) != parent["source_code_sha256"]:
        raise ValueError("sealed connection parent source changed")
    parent_test = Path(__file__).resolve().parents[2] / "tests/test_malecns_connection_fisher.py"
    if digest(parent_test) != parent["test_code_sha256"] or digest(base.PARENT_SOURCE) != parent["parent_source_sha256"] or digest(base.prior.BASE_PATH) != parent["hidden_source_sha256"]:
        raise ValueError("sealed parent dependency changed")
    if digest(Path(parent["parent_result"])) != parent["parent_result_sha256"] or digest(Path(parent["dyad_result"])) != parent["dyad_result_sha256"]:
        raise ValueError("parent ancestry result changed")
    _, dyad, hidden_path = base.read_ancestry(Path(parent["parent_result"]), Path(parent["dyad_result"]))
    artifacts = {**parent["input_artifacts"], **parent["artifacts"]}
    paths = [args.parent_result, PARENT_SOURCE, parent_test, base.PARENT_SOURCE, base.prior.BASE_PATH,
             Path(parent["parent_result"]), Path(parent["dyad_result"]), hidden_path]
    for artifact in artifacts.values():
        path = Path(artifact["path"])
        if path.stat().st_size != artifact["bytes"] or digest(path) != artifact["sha256"]:
            raise ValueError("sealed input artifact changed")
        paths.append(path)
    stamps = {str(path): (path.stat().st_size, path.stat().st_mtime_ns) for path in paths}
    a = sparse.load_npz(artifacts["active_transition.npz"]["path"])
    b = sparse.load_npz(artifacts["terminal_boundary.npz"]["path"])
    with np.load(artifacts["source_scope.npz"]["path"]) as source:
        codes, totals, labels = source["source_codes"], source["source_out_weight"], source["category_labels"]
    with np.load(artifacts["connection_fisher_arrays.npz"]["path"]) as source:
        endpoint_truth, endpoint_jacobian, endpoint_fisher = source["truth"], source["jacobian"], source["fisher"]
        cohort_labels = source["cohort_labels"]
    assigned = np.array([label not in base.prior.base.SPECIAL for label in labels])
    cohorts = np.flatnonzero(assigned)
    n, categories, steps, probes = len(codes), len(labels), parent["steps"], 2 * len(cohorts)
    if a.shape != (n, n) or b.shape != (categories, n) or not np.array_equal(cohort_labels, labels[cohorts]):
        raise ValueError("source identity or parent cohort mismatch")
    sparse_bytes = sum(x.nbytes for op in (a, b) for x in (op.data, op.indices, op.indptr))
    estimate = 6 * sparse_bytes + 5 * n * max(2 * args.batch_cohorts, probes) * 8 + 2**30
    if not np.isfinite(args.max_working_gib) or args.max_working_gib <= 0 or estimate > args.max_working_gib * 2**30:
        raise MemoryError("conservative working-set estimate exceeds budget")
    observed, uniform = base.prior.observation_and_lift(codes, totals, categories, "uniform")
    _, weighted = base.prior.observation_and_lift(codes, totals, categories, "out_weight")
    fa, fb, means = base.features(a, b, codes, assigned)
    base.check_reciprocal_census(base.integer_weight(fa[2], totals), dyad)
    covariance, covariance_min = source_covariance(fa, fb, means, codes, assigned)
    w = pair_operator(a, b, observed, codes)
    wk = [pair_operator(fa[k], fb[k], observed, codes) for k in range(3)]
    column_error = float(np.max(np.abs(base.columns(w) - 1)))
    tangent_column_error = float(np.max(np.abs(np.stack([base.columns(value) for value in wk]) - means * base.columns(w)[None])))
    if column_error > TOL or tangent_column_error > TOL:
        raise ValueError("pair operator probability or tangent column sums failed")
    print("full pair operators and source feature covariances verified", flush=True)
    pairs = np.zeros((steps + 1, 2 * categories, 2 * categories, probes))
    jacobian = np.zeros((*pairs.shape, 4))
    information = np.zeros((steps + 1, probes, len(LEVELS), 4, 4))
    diagnostics = []
    analytic_started = time.perf_counter()
    for start in range(0, len(cohorts), args.batch_cohorts):
        selected = cohorts[start:start + args.batch_cohorts]
        block = slice(2 * start, 2 * (start + len(selected)))
        initial = base.prior.initial_block(uniform, weighted, selected)
        joint, tangent, g, checks = tangent_run(a, b, observed, fa, fb, means, w, wk, covariance, initial, steps,
                                               endpoint_truth[:, :, block], endpoint_jacobian[:, :, block], endpoint_fisher[:, block])
        pairs[:, :, :, block], jacobian[:, :, :, block], information[:, block] = joint, tangent, g
        diagnostics.append({"cohort_start": start, "cohort_count": len(selected), **checks})
        print(f"exact history and path information: {start + len(selected)}/{len(cohorts)} cohorts", flush=True)
    analytic_seconds = time.perf_counter() - analytic_started
    fd = np.zeros((3, len(base.FD_STEPS), *pairs.shape))
    fd_records = []
    initial = base.prior.initial_block(uniform, weighted, cohorts)
    for k in range(3):
        for hi, h in enumerate(base.FD_STEPS):
            tick = time.perf_counter()
            outputs = []
            for sign in (1, -1):
                changed_a, changed_b = base.axis_tilt(a, b, fa[k], fb[k], sign * h)
                changed_w = pair_operator(changed_a, changed_b, observed, codes)
                outputs.append(nonlinear_pairs(changed_a, changed_b, observed, changed_w, initial, steps))
                del changed_a, changed_b, changed_w
            fd[k, hi] = (outputs[0] - outputs[1]) / (2 * h)
            error = np.abs(fd[k, hi] - jacobian[:, :, :, :, k])
            scaled = error / (1e-8 + 1e-4 * np.abs(jacobian[:, :, :, :, k]))
            record = {"feature": base.FEATURES[k], "step_size": h, "max_absolute_error": float(error.max()),
                      "max_scaled_error": float(scaled.max()), "elapsed_seconds": time.perf_counter() - tick,
                      "max_error_location_step_previous_current_probe": list(map(int, np.unravel_index(error.argmax(), error.shape)))}
            fd_records.append(record)
            print(f"joint finite difference: {record}", flush=True)
            if record["max_absolute_error"] > 1e-6 or record["max_scaled_error"] > 1:
                raise ValueError("nonlinear full joint finite difference failed")
    eigenvalues = np.linalg.eigvalsh(information[:, :, :, :3, :3])
    rank = np.sum(eigenvalues > 1e-10 * np.maximum(1., eigenvalues[..., -1])[..., None], axis=-1)
    nonnested_difference = np.linalg.eigvalsh(information[:, :, 4, :3, :3] - information[:, :, 2, :3, :3])
    if np.any(jacobian[..., 3] != 0) or np.any(information[..., 3, :] != 0) or np.any(information[..., :, 3] != 0):
        raise ValueError("common-source gauge must remain exactly null")
    for name, before in stamps.items():
        stat = Path(name).stat()
        if (stat.st_size, stat.st_mtime_ns) != before:
            raise ValueError("sealed input changed during execution")
    args.cache_dir.mkdir(parents=True)
    cache = args.cache_dir / "history_fisher_arrays.npz"
    np.savez_compressed(cache, pair_probability=pairs, pair_jacobian=jacobian, fisher=information,
                        finite_difference=fd, eigenvalues=eigenvalues, numerical_rank=rank,
                        pair60_minus_refined_eigenvalues=nonnested_difference,
                        category_labels=labels, cohort_labels=cohort_labels, feature_labels=np.asarray(base.FEATURES),
                        observation_labels=np.asarray(LEVELS), probe_order=np.asarray(["uniform_source", "out_weight_source"]),
                        finite_difference_steps=np.asarray(base.FD_STEPS))
    result = {"schema": "malecns-history-fisher-v1", "steps": steps, "source_count": n, "probe_count": probes,
              "cohort_labels": cohort_labels.tolist(), "feature_labels": list(base.FEATURES), "observation_labels": list(LEVELS),
              "numerical_tolerance": TOL, "working_bytes_estimate": estimate, "analytic_seconds": analytic_seconds,
              "pair_operator_nonzero_source_joint_cells": w.nnz, "feature_pair_operator_nonzero_cells": [value.nnz for value in wk],
              "pair_operator_column_max_error": column_error, "pair_tangent_column_max_error": tangent_column_error,
              "source_covariance_scaled_min_eigenvalue": covariance_min, "diagnostics": diagnostics, "finite_difference": fd_records,
              "rank_rule": parent["rank_rule"], "input_artifacts": artifacts,
              "parent_result": str(args.parent_result.resolve()), "parent_result_sha256": digest(args.parent_result),
              "parent_source_sha256": digest(PARENT_SOURCE), "parent_test_sha256": digest(parent_test),
              "source_code_sha256": digest(__file__),
              "test_code_sha256": digest(Path(__file__).resolve().parents[2] / "tests/test_malecns_history_fisher.py"),
              "artifacts": {cache.name: {"path": str(cache.resolve()), "bytes": cache.stat().st_size, "sha256": digest(cache)}},
              "software": {"python": platform.python_version(), "executable": sys.executable, "numpy": np.__version__, "scipy": scipy.__version__},
              "argv": sys.argv, "elapsed_seconds": time.perf_counter() - started,
              "interpretation": "Same full contact-supported absorbing proxy and three fixed shared log-efficacy coordinates plus common-source gauge. Pair observation is exactly (Y[t-1],Y[t]), not full coarse history and not independent repeated trials. Full-path Fisher observes all active raw IDs and terminal category from step0 and sums expected conditional score covariances, not endpoint Fisher. Source-specific terminal-category compression is sufficient for the chosen full-path score but not claimed sufficient for coarse paths or endpoint terminal ID information. Pair60 and refined endpoint are nonnested. No probability repair, biological learning, neural time or physical metric is established."}
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("HISTORY_FISHER_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
