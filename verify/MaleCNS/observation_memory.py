"""Boundary-aware observations and exact projected memory of the full raw walk.

No raw edge is removed. The unresolved variable here is within-category active
composition, not the nonassigned-ID set of the previous first-return analysis.
Finite-memory forecasts are never clipped or renormalized into probabilities.
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

BASE_PATH = Path(__file__).with_name("hidden_walk_information.py")
SPEC = importlib.util.spec_from_file_location("malecns_hidden_base", BASE_PATH)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
TOL = 5e-9


def dense(value):
    return value.toarray() if sparse.issparse(value) else np.asarray(value)


def observation_and_lift(codes, totals, categories, reference):
    codes, totals = np.asarray(codes), np.asarray(totals)
    if codes.ndim != 1 or totals.shape != codes.shape or not len(codes):
        raise ValueError("nonempty source arrays with matching shapes required")
    if np.any(codes < 0) or np.any(codes >= categories) or np.any(totals <= 0):
        raise ValueError("invalid category or out-weight")
    if reference not in ("uniform", "out_weight"):
        raise ValueError("unknown lifting reference")
    weights = np.ones(len(codes)) if reference == "uniform" else totals.astype(float)
    denominators = np.bincount(codes, weights=weights, minlength=categories)
    if not np.isfinite(weights).all() or np.any(denominators <= 0):
        raise ValueError("every active category must have positive finite weight")
    indices = np.arange(len(codes))
    observed = sparse.csr_array((np.ones(len(codes)), (codes, indices)), shape=(categories, len(codes)))
    lifted = sparse.csr_array((weights / denominators[codes], (indices, codes)), shape=(len(codes), categories))
    if np.max(np.abs(dense(observed @ lifted) - np.eye(categories))) > TOL:
        raise ValueError("observation times lifting is not identity")
    return observed, lifted


def initial_block(uniform, weighted, cohort_codes):
    block = np.empty((uniform.shape[0], 2 * len(cohort_codes)))
    block[:, 0::2] = uniform[:, cohort_codes].toarray()
    block[:, 1::2] = weighted[:, cohort_codes].toarray()
    return block


def truth_trajectory(transition, boundary, observed, initial, steps):
    active, absorbed = initial, np.zeros((boundary.shape[0], initial.shape[1]))
    traces, information = [], []
    for step in range(steps + 1):
        grouped = observed @ active
        split = np.vstack((grouped, absorbed))
        coarse = grouped + absorbed
        rows = []
        for column in range(0, active.shape[1], 2):
            pair = slice(column, column + 2)
            g30 = base.fisher_midpoint(coarse[:, pair])
            g60 = base.fisher_midpoint(split[:, pair])
            refined = base.fisher_midpoint(active[:, pair]) + base.fisher_midpoint(absorbed[:, pair])
            if g30 > g60 + TOL or g60 > refined + TOL:
                raise ValueError("nested Fisher data-processing invariant failed")
            rows.append([g30, g60, refined])
        if not np.isfinite(split).all() or not np.isfinite(rows).all() or np.min(split) < 0 or np.max(np.abs(split.sum(axis=0) - 1)) > TOL:
            raise ValueError("invalid whole-walk probability")
        traces.append(split)
        information.append(rows)
        if step < steps:
            absorbed = absorbed + boundary @ active
            active = transition @ active
    return np.asarray(traces), np.asarray(information)


def residual_step(transition, boundary, observed, lifted, state):
    advanced = transition @ state
    grouped = observed @ advanced
    output = np.vstack((grouped, boundary @ state))
    residual = advanced - lifted @ grouped
    if not np.isfinite(residual).all() or np.max(np.abs(observed @ residual)) > TOL:
        raise ValueError("unresolved state left the zero-category-sum subspace")
    return residual, output


def memory_operators(transition, boundary, observed, lifted, kernel_count):
    categories = observed.shape[0]
    advanced = dense(transition @ lifted)
    top, bottom = observed @ advanced, dense(boundary @ lifted)
    markov = np.block([[top, np.zeros((categories, categories))], [bottom, np.eye(categories)]])
    if np.min(markov) < 0 or np.max(np.abs(markov.sum(axis=0) - 1)) > TOL:
        raise ValueError("memoryless lifted transition is not stochastic")
    state = advanced - lifted @ top
    kernels, diagnostics = [], []
    for lag in range(kernel_count):
        state, kernel = residual_step(transition, boundary, observed, lifted, state)
        column_error = float(np.max(np.abs(kernel.sum(axis=0))))
        if column_error > TOL:
            raise ValueError("memory correction changes total mass")
        kernels.append(kernel)
        diagnostics.append({"lag": lag, "kernel_max_column_l1": float(np.abs(kernel).sum(axis=0).max()),
                            "next_residual_max_column_l1": float(np.abs(state).sum(axis=0).max()),
                            "kernel_column_sum_error": column_error})
    return markov, np.asarray(kernels), diagnostics


def initial_forcing(transition, boundary, observed, lifted, residual, steps):
    if np.max(np.abs(observed @ residual)) > TOL:
        raise ValueError("initial residual must have zero category sums")
    outputs = []
    state = residual.copy()
    for _ in range(steps):
        state, output = residual_step(transition, boundary, observed, lifted, state)
        if np.max(np.abs(output.sum(axis=0))) > TOL:
            raise ValueError("initial correction changes total mass")
        outputs.append(output)
    return np.asarray(outputs)


def forecast(markov, kernels, forcing, initial, memory_lags, include_initial):
    steps, categories = len(forcing), markov.shape[0] // 2
    if not 0 <= memory_lags <= len(kernels):
        raise ValueError("memory lag count outside stored kernel range")
    predicted = np.empty((steps + 1, *initial.shape))
    predicted[0] = initial
    for step in range(steps):
        value = markov @ predicted[step]
        if include_initial:
            value += forcing[step]
        for lag in range(min(step, memory_lags)):
            value += kernels[lag] @ predicted[step - 1 - lag, :categories]
        if not np.isfinite(value).all():
            raise ValueError("nonfinite projected forecast")
        predicted[step + 1] = value
    return predicted


def forecast_summary(predicted, truth):
    # Half-L1 remains defined for signed approximations; it is not then TV.
    errors = .5 * np.abs(predicted - truth).sum(axis=1)
    minimum = predicted.min(axis=1)
    mass_error = np.abs(predicted.sum(axis=1) - 1)
    return {"half_l1_by_step": errors.tolist(), "minimum_by_step": minimum.tolist(),
            "mass_error_by_step": mass_error.tolist(),
            "max_half_l1": float(errors.max()), "max_mass_error": float(mass_error.max()),
            "minimum_probability": float(minimum.min()),
            "invalid_step_probe_distributions": int(np.count_nonzero((minimum < -TOL) | (mass_error > TOL)))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-result", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--max-working-gib", type=float, default=8)
    args = parser.parse_args()
    if args.cache_dir.exists() or args.result.exists():
        raise FileExistsError("preserve existing analysis outputs")
    started = time.perf_counter()
    parent = json.loads(args.parent_result.read_text(encoding="utf-8"))
    if base.digest(BASE_PATH) != parent["source_code_sha256"]:
        raise ValueError("parent source changed")
    stamps = {}
    for artifact in parent["artifacts"].values():
        path = Path(artifact["path"])
        before = path.stat()
        if before.st_size != artifact["bytes"] or base.digest(path) != artifact["sha256"]:
            raise ValueError("parent artifact changed")
        stamps[str(path)] = (before.st_size, before.st_mtime_ns)
    transition = sparse.load_npz(parent["artifacts"]["active_transition.npz"]["path"])
    boundary = sparse.load_npz(parent["artifacts"]["terminal_boundary.npz"]["path"])
    with np.load(parent["artifacts"]["source_scope.npz"]["path"]) as source:
        ids, codes, totals = source["source_ids"], source["source_codes"], source["source_out_weight"]
        labels = source["category_labels"].tolist()
    n, categories, steps = len(ids), len(labels), parent["steps"]
    cohort_codes = [code for code, label in enumerate(labels) if label not in base.SPECIAL]
    if transition.shape != (n, n) or boundary.shape != (categories, n) or steps < 2:
        raise ValueError("invalid parent operator shape or horizon")
    estimate = sum(a.nbytes for op in (transition, boundary) for a in (op.data, op.indices, op.indptr))
    estimate += n * 64 + 6 * n * max(2 * len(cohort_codes), categories) * 8 + 2**30
    if not np.isfinite(args.max_working_gib) or args.max_working_gib <= 0 or estimate > args.max_working_gib * 2**30:
        raise MemoryError("conservative working-set estimate exceeds budget")
    observed, uniform = observation_and_lift(codes, totals, categories, "uniform")
    _, weighted = observation_and_lift(codes, totals, categories, "out_weight")
    truth, fisher = truth_trajectory(transition, boundary, observed, initial_block(uniform, weighted, cohort_codes), steps)
    with np.load(parent["artifacts"]["probe_traces.npz"]["path"]) as source:
        previous = source["category_observation"]
    coarse = truth[:, :categories] + truth[:, categories:]
    previous_current = coarse.reshape(steps + 1, categories, len(cohort_codes), 2).transpose(2, 0, 3, 1)
    parent_error = float(np.max(np.abs(previous_current - previous)))
    if parent_error > TOL:
        raise ValueError("whole-walk replay disagrees with sealed parent")
    previous_fisher = np.array([[t["active_id_terminal_category_fisher"] for t in row["trajectory"]] for row in parent["cohorts"]]).T
    if np.max(np.abs(fisher[:, :, 2] - previous_fisher)) > TOL or np.max(np.diff(fisher[:, :, 2], axis=0)) > TOL:
        raise ValueError("refined Fisher replay or contraction failed")
    print("boundary-aware truth and parent replay complete", flush=True)
    modes = [("memoryless", 0, False), ("initial_only", 0, True)]
    modes += [(f"history_{lag}", lag, True) for lag in (1, 2, 4, 8) if lag < steps - 1]
    modes += [("history_full", steps - 1, True), ("history_full_no_initial", steps - 1, False)]
    delta = (weighted[:, cohort_codes] - uniform[:, cohort_codes]).toarray()
    outputs, model_records, matrices, stored_kernels, stored_forcing = [], [], [], [], []
    for reference_index, (reference, lifted) in enumerate((("uniform", uniform), ("out_weight", weighted))):
        kernel_started = time.perf_counter()
        markov, kernels, diagnostics = memory_operators(transition, boundary, observed, lifted, steps - 1)
        kernel_seconds = time.perf_counter() - kernel_started
        print(f"memory kernels complete: {reference}", flush=True)
        forcing_started = time.perf_counter()
        delta_forcing = initial_forcing(transition, boundary, observed, lifted, delta, steps)
        forcing_seconds = time.perf_counter() - forcing_started
        forcing = np.zeros((steps, 2 * categories, 2 * len(cohort_codes)))
        if reference_index == 0:
            forcing[:, :, 1::2] = delta_forcing
        else:
            forcing[:, :, 0::2] = -delta_forcing
        model_outputs, records = [], []
        for name, lags, use_initial in modes:
            forecast_started = time.perf_counter()
            predicted = forecast(markov, kernels, forcing, truth[0], lags, use_initial)
            forecast_seconds = time.perf_counter() - forecast_started
            summary = forecast_summary(predicted, truth)
            if name == "history_full" and (summary["max_half_l1"] > TOL or summary["invalid_step_probe_distributions"]):
                raise ValueError("full-memory recurrence does not reproduce the raw walk")
            if name == "history_full_no_initial":
                matched = slice(reference_index, None, 2)
                if np.max(np.abs(predicted[:, :, matched] - truth[:, :, matched])) > TOL:
                    raise ValueError("matched lift should not require initial forcing")
            model_outputs.append(predicted)
            records.append({"name": name, "memory_lags": lags, "includes_initial_residual": use_initial,
                            "forecast_seconds": forecast_seconds, "past_active_scalars_per_probe": lags * categories, **summary})
        outputs.append(model_outputs)
        matrices.append(markov)
        stored_kernels.append(kernels)
        stored_forcing.append(forcing)
        model_records.append({"reference": reference, "kernel_seconds": kernel_seconds,
                              "initial_forcing_seconds": forcing_seconds, "kernel_diagnostics": diagnostics, "models": records})
        print(f"all autonomous forecasts complete: {reference}", flush=True)
    for name, before in stamps.items():
        stat = Path(name).stat()
        if (stat.st_size, stat.st_mtime_ns) != before:
            raise ValueError("parent input changed during execution")
    args.cache_dir.mkdir(parents=True)
    cache = args.cache_dir / "observation_memory_arrays.npz"
    np.savez_compressed(cache, truth=truth, fisher=fisher, forecasts=np.asarray(outputs),
                        markov=np.asarray(matrices), kernels=np.asarray(stored_kernels), forcing=np.asarray(stored_forcing),
                        category_labels=np.asarray(labels), cohort_labels=np.asarray(labels)[cohort_codes],
                        reference_labels=np.asarray(["uniform", "out_weight"]), mode_labels=np.asarray([m[0] for m in modes]),
                        fisher_labels=np.asarray(["category30", "active_terminal60", "active_id_terminal_category"]),
                        probe_order=np.asarray(["uniform_source", "out_weight_source"]))
    information = [{"category": labels[code], "positive_sources": int(np.count_nonzero(codes == code)),
                    "fisher_by_step": fisher[:, i].tolist()} for i, code in enumerate(cohort_codes)]
    result = {"schema": "malecns-observation-memory-v1", "steps": steps, "category_count": categories,
              "source_count": n, "working_bytes_estimate": estimate, "parent_replay_max_error": parent_error,
              "numerical_tolerance": TOL, "cohorts": information, "references": model_records,
              "parent_result": str(args.parent_result.resolve()), "parent_result_sha256": base.digest(args.parent_result),
              "input_artifacts": parent["artifacts"], "parent_source_sha256": parent["source_code_sha256"],
              "source_code_sha256": base.digest(__file__),
              "test_code_sha256": base.digest(Path(__file__).resolve().parents[2] / "tests/test_malecns_observation_memory.py"),
              "artifacts": {cache.name: {"path": str(cache.resolve()), "bytes": cache.stat().st_size, "sha256": base.digest(cache)}},
              "software": {"python": platform.python_version(), "executable": sys.executable, "numpy": np.__version__, "scipy": scipy.__version__},
              "argv": sys.argv, "elapsed_seconds": time.perf_counter() - started,
              "interpretation": "Same complete contact-supported absorbing walk. Sixty outputs separate active category and terminal category. Lifting fixes uniform or out-weight active composition. Full-memory recurrence is an algebraic reconstruction with graph-derived kernels and known initial residual, not independent biological prediction. Matched lift has zero initial residual. Finite-memory signed forecasts are not repaired; half-L1 is not TV when probabilities are invalid. No neural time, learning, ROI mechanism or connection-parameter metric is established."}
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("OBSERVATION_MEMORY_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
