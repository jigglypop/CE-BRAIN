"""Fixed-support log-efficacy tangents of the complete absorbing MaleCNS walk.

Initial distributions and observations remain fixed. These are endpoint Fisher
matrices for supplied structural coordinates, not measured neural plasticity.
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

PARENT_SOURCE = Path(__file__).with_name("observation_memory.py")
SPEC = importlib.util.spec_from_file_location("malecns_observation_base", PARENT_SOURCE)
prior = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prior)
TOL = 5e-9
FD_STEPS = (1e-4, 5e-5)
FEATURES = ("active_target", "same_assigned_superclass", "reciprocal_nonself", "source_common_gauge")
LEVELS = ("category30", "active_terminal60", "active_id_terminal_category")


def read_ancestry(parent_path, dyad_path):
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    if parent.get("schema") != "malecns-observation-memory-v1":
        raise ValueError("unexpected observation parent")
    hidden_path = Path(parent["parent_result"])
    if prior.base.digest(hidden_path) != parent["parent_result_sha256"]:
        raise ValueError("hidden parent result changed")
    hidden = json.loads(hidden_path.read_text(encoding="utf-8"))
    if prior.base.digest(dyad_path) != hidden["dyad_result_sha256"]:
        raise ValueError("dyad result is outside sealed parent ancestry")
    dyad = json.loads(dyad_path.read_text(encoding="utf-8"))
    if dyad.get("schema") != "malecns-raw-dyad-return-v1":
        raise ValueError("unexpected dyad parent")
    return parent, dyad, hidden_path


def check_reciprocal_census(census, dyad):
    if (census["directed_dyads"] != dyad["reciprocal_directed_dyads"] or
            census["contact_weight"] != int(np.asarray(dyad["category_reciprocal_weights"], dtype=np.uint64).sum())):
        raise ValueError("reciprocal feature disagrees with sealed whole-raw census")


def columns(op):
    return np.asarray(op.sum(axis=0)).reshape(-1)


def entry_blocks(op, size=1_000_000):
    for start in range(0, op.nnz, size):
        stop = min(op.nnz, start + size)
        source = np.searchsorted(op.indptr, np.arange(start, stop), side="right") - 1
        yield slice(start, stop), source, op.indices[start:stop]


def same_category(op, codes, assigned, terminal=False):
    selected = op.copy()
    for block, source, target in entry_blocks(selected):
        source_code = codes[source]
        target_code = target if terminal else codes[target]
        keep = assigned[source_code] & assigned[target_code] & (source_code == target_code)
        selected.data[block] *= keep
    selected.eliminate_zeros()
    return selected


def features(transition, boundary, codes, assigned):
    within = same_category(transition, codes, assigned)
    within_boundary = same_category(boundary, codes, assigned, terminal=True)
    reciprocal = transition.multiply(transition.astype(bool).T).tocsc()
    for block, source, target in entry_blocks(reciprocal):
        reciprocal.data[block] *= source != target
    reciprocal.eliminate_zeros()
    zero = sparse.csc_array(boundary.shape, dtype=float)
    active_features = (transition, within, reciprocal)
    boundary_features = (zero, within_boundary, zero)
    means = np.stack([columns(a) + columns(b) for a, b in zip(active_features, boundary_features)])
    if not np.isfinite(means).all() or np.min(means) < 0 or np.max(means) > 1 + TOL:
        raise ValueError("invalid binary-feature source means")
    return active_features, boundary_features, means


def integer_weight(op, totals):
    weight, error = 0, 0.
    for block, source, _ in entry_blocks(op):
        recovered = op.data[block] * totals[source]
        rounded = np.rint(recovered)
        error = max(error, float(np.max(np.abs(recovered - rounded), initial=0)))
        weight += int(rounded.astype(np.uint64).sum(dtype=np.uint64))
    if error > 1e-7:
        raise ValueError("normalized feature weights do not recover integer contacts")
    return {"directed_dyads": op.nnz, "contact_weight": weight, "integer_recovery_max_error": error}


def fisher(probability, tangent, block_size=65536):
    """tangent has (coordinate, outcome, probe); never add a pseudocount."""
    if tangent.shape[1:] != probability.shape:
        raise ValueError("tangent and probability shapes differ")
    output = np.zeros((probability.shape[1], tangent.shape[0], tangent.shape[0]))
    for start in range(0, len(probability), block_size):
        p = probability[start:start + block_size]
        j = tangent[:, start:start + block_size]
        if not np.isfinite(p).all() or not np.isfinite(j).all() or np.min(p) < 0:
            raise ValueError("invalid Fisher input")
        if np.any(j[:, p == 0] != 0):
            raise ValueError("nonzero tangent outside fixed support")
        score = np.zeros_like(j)
        np.divide(j, np.sqrt(p)[None], out=score, where=p[None] > 0)
        output += np.einsum("irm,jrm->mij", score, score, optimize=True)
    return output


def tangent_trajectory(a, b, observed, fa, fb, means, initial, steps):
    count = initial.shape[1]
    active, absorbed = initial.copy(), np.zeros((b.shape[0], count))
    da, db = np.zeros((3, *active.shape)), np.zeros((3, *absorbed.shape))
    truth = np.zeros((steps + 1, 2 * b.shape[0], count))
    jacobian = np.zeros((*truth.shape, 4))
    information = np.zeros((steps + 1, count, 3, 4, 4))
    mass_error, derivative_error, loewner_min = 0., 0., 0.
    for step in range(steps + 1):
        grouped = observed @ active
        dgrouped = np.stack([observed @ d for d in da])
        split = np.vstack((grouped, absorbed))
        dsplit = np.concatenate((dgrouped, db), axis=1)
        if np.min(split) < 0 or not np.isfinite(split).all():
            raise ValueError("invalid probability trajectory")
        mass_error = max(mass_error, float(np.max(np.abs(split.sum(axis=0) - 1))))
        derivative_error = max(derivative_error, float(np.max(np.abs(dsplit.sum(axis=1)))))
        if mass_error > TOL or derivative_error > TOL:
            raise ValueError("probability or tangent mass conservation failed")
        g30 = fisher(grouped + absorbed, dgrouped + db)
        g60 = fisher(split, dsplit)
        refined = fisher(active, da) + fisher(absorbed, db)
        for matrix in (g30, g60 - g30, refined - g60):
            eigen = np.linalg.eigvalsh(matrix)
            scale = np.maximum(1., np.max(np.abs(eigen), axis=-1))
            current = float(np.min(eigen[:, 0] / scale))
            loewner_min = min(loewner_min, current)
            if current < -TOL:
                raise ValueError("same-step Fisher PSD or Loewner ordering failed")
        truth[step] = split
        jacobian[step, :, :, :3] = dsplit.transpose(1, 2, 0)
        information[step, :, :, :3, :3] = np.stack((g30, g60, refined), axis=1)
        if step < steps:
            next_active = a @ active
            for k in range(3):
                centered = da[k] - means[k, :, None] * active
                db[k] += b @ centered + fb[k] @ active
                da[k] = a @ centered + (next_active if k == 0 else fa[k] @ active)
            absorbed += b @ active
            active = next_active
    return truth, jacobian, information, {"mass_max_error": mass_error,
        "tangent_mass_max_error": derivative_error, "loewner_scaled_min_eigenvalue": loewner_min}


def axis_tilt(a, b, fa, fb, amount):
    """Independent nonlinear forward operator, normalized on all destinations."""
    changed_a = (a + np.expm1(amount) * fa).tocsc()
    changed_b = (b + np.expm1(amount) * fb).tocsc()
    normalizer = columns(changed_a) + columns(changed_b)
    if np.any(normalizer <= 0) or not np.isfinite(normalizer).all():
        raise ValueError("invalid tilted source normalizer")
    for op in (changed_a, changed_b):
        for block, source, _ in entry_blocks(op):
            op.data[block] /= normalizer[source]
        if np.min(op.data, initial=0) < 0:
            raise ValueError("tilted probability became negative")
    if np.max(np.abs(columns(changed_a) + columns(changed_b) - 1)) > TOL:
        raise ValueError("tilted operator lost stochasticity")
    return changed_a, changed_b


def forward(a, b, observed, initial, steps):
    active, absorbed = initial.copy(), np.zeros((b.shape[0], initial.shape[1]))
    output = []
    for step in range(steps + 1):
        split = np.vstack((observed @ active, absorbed))
        if not np.isfinite(split).all() or np.min(split) < 0 or np.max(np.abs(split.sum(axis=0) - 1)) > TOL:
            raise ValueError("nonlinear forward probability invalid")
        output.append(split)
        if step < steps:
            absorbed += b @ active
            active = a @ active
    return np.asarray(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-result", type=Path, required=True)
    parser.add_argument("--dyad-result", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--batch-cohorts", type=int, default=3)
    parser.add_argument("--max-working-gib", type=float, default=8)
    args = parser.parse_args()
    if args.cache_dir.exists() or args.result.exists():
        raise FileExistsError("preserve existing analysis outputs")
    if args.batch_cohorts < 1:
        raise ValueError("positive batch size required")
    started = time.perf_counter()
    parent, dyad, hidden_path = read_ancestry(args.parent_result, args.dyad_result)
    if prior.base.digest(PARENT_SOURCE) != parent["source_code_sha256"] or prior.base.digest(prior.BASE_PATH) != parent["parent_source_sha256"]:
        raise ValueError("sealed parent source changed")
    artifacts = {**parent["input_artifacts"], **parent["artifacts"]}
    stamps = {str(path): (path.stat().st_size, path.stat().st_mtime_ns)
              for path in (args.parent_result, args.dyad_result, hidden_path, PARENT_SOURCE, prior.BASE_PATH)}
    for artifact in artifacts.values():
        path = Path(artifact["path"])
        stat = path.stat()
        if stat.st_size != artifact["bytes"] or prior.base.digest(path) != artifact["sha256"]:
            raise ValueError("sealed input artifact changed")
        stamps[str(path)] = (stat.st_size, stat.st_mtime_ns)
    a = sparse.load_npz(artifacts["active_transition.npz"]["path"])
    b = sparse.load_npz(artifacts["terminal_boundary.npz"]["path"])
    with np.load(artifacts["source_scope.npz"]["path"]) as source:
        codes, totals, labels = source["source_codes"], source["source_out_weight"], source["category_labels"]
    n, categories, steps = len(codes), len(labels), parent["steps"]
    assigned = np.array([label not in prior.base.SPECIAL for label in labels])
    cohort_codes = np.flatnonzero(assigned)
    cohort_count, probe_count = len(cohort_codes), 2 * len(cohort_codes)
    if a.shape != (n, n) or b.shape != (categories, n) or not a.has_canonical_format or not b.has_canonical_format:
        raise ValueError("invalid parent sparse operator")
    if np.min(a.data) <= 0 or np.min(b.data) <= 0 or np.max(np.abs(columns(a) + columns(b) - 1)) > TOL:
        raise ValueError("parent operator is not supported stochastic transition")
    sparse_bytes = sum(x.nbytes for op in (a, b) for x in (op.data, op.indices, op.indptr))
    estimate = 6 * sparse_bytes + 12 * n * max(2 * args.batch_cohorts, probe_count // 4) * 8 + 2**30
    if not np.isfinite(args.max_working_gib) or args.max_working_gib <= 0 or estimate > args.max_working_gib * 2**30:
        raise MemoryError("conservative working-set estimate exceeds budget")
    observed, uniform = prior.observation_and_lift(codes, totals, categories, "uniform")
    _, weighted = prior.observation_and_lift(codes, totals, categories, "out_weight")
    fa, fb, means = features(a, b, codes, assigned)
    tangent_column_error = float(np.max(np.abs(means * (1 - columns(a) - columns(b)))))
    if tangent_column_error > TOL:
        raise ValueError("operator tangent does not have zero column sums")
    census = [{"feature": FEATURES[k], "active": integer_weight(fa[k], totals), "terminal": integer_weight(fb[k], totals)} for k in range(3)]
    check_reciprocal_census(census[2]["active"], dyad)
    print("full fixed-support features and reciprocal census verified", flush=True)
    truth = np.zeros((steps + 1, 2 * categories, probe_count))
    jacobian = np.zeros((*truth.shape, 4))
    information = np.zeros((steps + 1, probe_count, 3, 4, 4))
    diagnostics = []
    analytic_started = time.perf_counter()
    for start in range(0, cohort_count, args.batch_cohorts):
        selected = cohort_codes[start:start + args.batch_cohorts]
        initial = prior.initial_block(uniform, weighted, selected)
        tr, jac, g, checks = tangent_trajectory(a, b, observed, fa, fb, means, initial, steps)
        block = slice(2 * start, 2 * (start + len(selected)))
        truth[:, :, block], jacobian[:, :, block], information[:, block] = tr, jac, g
        diagnostics.append({"cohort_start": start, "cohort_count": len(selected), **checks})
        print(f"analytic trajectories complete: {start + len(selected)}/{cohort_count} cohorts", flush=True)
    analytic_seconds = time.perf_counter() - analytic_started
    with np.load(artifacts["observation_memory_arrays.npz"]["path"]) as source:
        replay_error = float(np.max(np.abs(truth - source["truth"])))
    if replay_error > TOL:
        raise ValueError("baseline trajectory differs from sealed observation result")
    fd = np.zeros((3, len(FD_STEPS), *truth.shape))
    fd_records = []
    initial = prior.initial_block(uniform, weighted, cohort_codes)
    for k in range(3):
        for h_index, h in enumerate(FD_STEPS):
            tick = time.perf_counter()
            outputs = []
            for sign in (1, -1):
                changed_a, changed_b = axis_tilt(a, b, fa[k], fb[k], sign * h)
                outputs.append(forward(changed_a, changed_b, observed, initial, steps))
                del changed_a, changed_b
            fd[k, h_index] = (outputs[0] - outputs[1]) / (2 * h)
            error = np.abs(fd[k, h_index] - jacobian[:, :, :, k])
            scaled = error / (1e-8 + 1e-4 * np.abs(jacobian[:, :, :, k]))
            record = {"feature": FEATURES[k], "step_size": h, "max_absolute_error": float(error.max()),
                      "max_scaled_error": float(scaled.max()), "elapsed_seconds": time.perf_counter() - tick,
                      "max_error_location_step_output_probe": list(map(int, np.unravel_index(error.argmax(), error.shape)))}
            fd_records.append(record)
            print(f"finite difference: {record}", flush=True)
            if record["max_absolute_error"] > 1e-6 or record["max_scaled_error"] > 1:
                raise ValueError("independent nonlinear finite difference failed")
    eigenvalues, eigenvectors = np.linalg.eigh(information[:, :, :, :3, :3])
    rank_threshold = 1e-10 * np.maximum(1., eigenvalues[:, :, :, -1])
    rank = np.sum(eigenvalues > rank_threshold[:, :, :, None], axis=-1)
    if np.any(jacobian[..., 3] != 0) or np.any(information[..., 3, :] != 0) or np.any(information[..., :, 3] != 0):
        raise ValueError("common-source gauge must be exactly null")
    for name, before in stamps.items():
        stat = Path(name).stat()
        if (stat.st_size, stat.st_mtime_ns) != before:
            raise ValueError("parent artifact changed during execution")
    args.cache_dir.mkdir(parents=True)
    cache = args.cache_dir / "connection_fisher_arrays.npz"
    np.savez_compressed(cache, truth=truth, jacobian=jacobian, fisher=information, finite_difference=fd,
                        eigenvalues=eigenvalues, eigenvectors=eigenvectors, numerical_rank=rank, rank_threshold=rank_threshold,
                        category_labels=labels, cohort_labels=labels[cohort_codes], feature_labels=np.asarray(FEATURES),
                        observation_labels=np.asarray(LEVELS), probe_order=np.asarray(["uniform_source", "out_weight_source"]),
                        finite_difference_steps=np.asarray(FD_STEPS))
    result = {"schema": "malecns-connection-fisher-v1", "steps": steps, "source_count": n,
              "cohort_labels": labels[cohort_codes].tolist(), "probe_count": probe_count, "feature_labels": list(FEATURES),
              "feature_census": census, "analytic_seconds": analytic_seconds, "diagnostics": diagnostics,
              "operator_tangent_column_max_error": tangent_column_error,
              "parent_replay_max_error": replay_error, "finite_difference": fd_records,
              "working_bytes_estimate": estimate, "numerical_tolerance": TOL,
              "rank_rule": "eigenvalue > 1e-10 * max(1, largest eigenvalue) of three structural coordinates; gauge is additional exact zero",
              "finite_difference_rule": "all 54 fixed probes, all 60 outputs and steps 0..16; central h=1e-4 and 5e-5; max absolute <=1e-6 and error/(1e-8+1e-4*abs(analytic))<=1",
              "parent_result": str(args.parent_result.resolve()), "parent_result_sha256": prior.base.digest(args.parent_result),
              "dyad_result": str(args.dyad_result.resolve()), "dyad_result_sha256": prior.base.digest(args.dyad_result),
              "input_artifacts": artifacts, "parent_source_sha256": parent["source_code_sha256"],
              "hidden_source_sha256": parent["parent_source_sha256"], "source_code_sha256": prior.base.digest(__file__),
              "test_code_sha256": prior.base.digest(Path(__file__).resolve().parents[2] / "tests/test_malecns_connection_fisher.py"),
              "artifacts": {cache.name: {"path": str(cache.resolve()), "bytes": cache.stat().st_size, "sha256": prior.base.digest(cache)}},
              "software": {"python": platform.python_version(), "executable": sys.executable, "numpy": np.__version__, "scipy": scipy.__version__},
              "argv": sys.argv, "elapsed_seconds": time.perf_counter() - started,
              "interpretation": "Full contact-supported absorbing proxy; baseline weights, support, initial U/W, identities and observation maps fixed. Binary log-efficacy coordinates are active target, same assigned superclass including terminal targets, and reciprocal nonself. All outgoing contacts form the normalizer. Source-common scaling is null only for this normalized model. Endpoint Fisher is not trajectory Fisher, initial-mixture Fisher, physical spatial metric or biological efficacy measurement. Same-step Loewner ordering is checked, temporal contraction is not assumed. No ridge, pseudocount or signed memory approximation is used."}
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("CONNECTION_FISHER_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
