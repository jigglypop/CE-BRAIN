"""Whole-raw structural walk, first hidden excursions, and mixture Fisher.

Raw source IDs stay distinct. Post-only IDs are lumped by observed category
only because the supplied walk makes them absorbing; their outgoing boundary
weight is never dropped or renormalized away. This is not neural activity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np
import scipy
from scipy import sparse

SPECIAL = ("ANNOTATED_GLIA", "ANNOTATED_UNCLASSIFIED", "UNANNOTATED_SEGMENT")
U32_MAX = 2**32 - 1
TOL = 5e-10


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def locate(values, reference):
    indices = np.searchsorted(reference, values)
    matched = indices < len(reference)
    matched[matched] &= reference[indices[matched]] == values[matched]
    return indices, matched


def build_operators(keys, weights, ids, codes, totals, category_weights, labels, *,
                    expected_terminal_dyads=None, chunk_size=1_000_000, max_working_gib=8):
    n, k = len(ids), len(labels)
    terminal_expected = expected_terminal_dyads if expected_terminal_dyads is not None else 0
    capacity = len(keys) - terminal_expected
    estimate = len(keys)*12 + n*k*20 + capacity*48 + n*200 + chunk_size*100
    if not np.isfinite(max_working_gib) or max_working_gib <= 0 or estimate > max_working_gib*2**30:
        raise MemoryError("conservative sparse working-set estimate exceeds budget")
    if n == 0 or keys.dtype != np.uint64 or len(keys) != len(weights) or np.any(ids[1:] <= ids[:-1]):
        raise ValueError("nonempty sorted source IDs and uint64 dyad keys required")
    if category_weights.shape != (n, k) or totals.shape != (n,) or codes.shape != (n,):
        raise ValueError("source/category shape mismatch")
    if np.any(totals <= 0) or np.any(codes < 0) or np.any(codes >= k):
        raise ValueError("invalid source totals or category codes")
    if not np.array_equal(category_weights.sum(axis=1, dtype=np.uint64), totals):
        raise ValueError("cached source/category weight mismatch")
    indices = np.empty(capacity, dtype=np.int32)
    values = np.empty(capacity, dtype=np.float64)
    indptr = np.zeros(n + 1, dtype=np.int64)
    internal_weights = np.zeros((n, k), dtype=np.uint64)
    seen_totals = np.zeros(n, dtype=np.uint64)
    cursor, terminal_count, terminal_weight, self_count, self_weight = 0, 0, 0, 0, 0
    previous = None
    for start in range(0, len(keys), chunk_size):
        block, weight = keys[start:start+chunk_size], weights[start:start+chunk_size]
        if np.any(block[1:] <= block[:-1]) or (previous is not None and int(block[0]) <= previous):
            raise ValueError("canonical dyad keys must be strictly increasing")
        previous = int(block[-1])
        if np.any(weight <= 0) or np.any(weight > U32_MAX):
            raise ValueError("invalid contact weight")
        pre, post = (block >> np.uint64(32)).astype(np.uint32), (block & np.uint64(U32_MAX)).astype(np.uint32)
        source, found = locate(pre, ids)
        if not found.all():
            raise ValueError("raw source absent from source index")
        target, active = locate(post, ids)
        end = cursor + int(active.sum())
        if end > capacity:
            raise ValueError("active dyad count exceeds expected capacity")
        indices[cursor:end] = target[active]
        values[cursor:end] = weight[active].astype(np.float64) / totals[source[active]]
        np.add.at(indptr, source[active] + 1, 1)
        np.add.at(internal_weights, (source[active], codes[target[active]]), weight[active])
        np.add.at(seen_totals, source, weight)
        terminal_count += int((~active).sum())
        terminal_weight += int(weight[~active].sum(dtype=np.uint64))
        self_count += int((pre == post).sum())
        self_weight += int(weight[pre == post].sum(dtype=np.uint64))
        cursor = end
        if start // chunk_size % 30 == 0:
            print(f"sparse operator {min(start+chunk_size,len(keys))}/{len(keys)}", flush=True)
    if not np.array_equal(seen_totals, totals) or np.any(internal_weights > category_weights):
        raise ValueError("raw and cached category weight conservation failed")
    if expected_terminal_dyads is not None and (cursor != capacity or terminal_count != terminal_expected):
        raise ValueError("terminal dyad count differs from verified census")
    boundary_weights = category_weights.astype(np.uint64) - internal_weights
    if int(boundary_weights.sum()) != terminal_weight:
        raise ValueError("terminal boundary weight conservation failed")
    np.cumsum(indptr, out=indptr)
    transition = sparse.csc_array((values[:cursor], indices[:cursor], indptr), shape=(n, n))
    boundary = sparse.csc_array(boundary_weights.T, dtype=np.float64)
    boundary.data /= np.repeat(totals, np.diff(boundary.indptr))
    observation = sparse.csr_array((np.ones(n), (codes, np.arange(n))), shape=(k, n))
    if not transition.has_canonical_format:
        raise ValueError("active transition is not canonical CSC")
    mass = np.asarray(transition.sum(axis=0)).ravel() + np.asarray(boundary.sum(axis=0)).ravel()
    column_error = float(np.max(np.abs(mass - 1)))
    if column_error > TOL:
        raise ValueError("active plus boundary transition is not stochastic")
    scope = {"source_ids": n, "active_target_dyads": cursor, "terminal_target_dyads": terminal_count,
             "terminal_target_weight": terminal_weight, "self_dyads": self_count, "self_weight": self_weight,
             "weight_sum": int(totals.sum()), "max_column_mass_error": column_error,
             "working_bytes_estimate": estimate, "terminal_category_weights": boundary_weights.sum(axis=0).tolist()}
    return transition, boundary, observation, scope


def fisher_midpoint(pair):
    """Scalar Fisher for mixture alpha at 1/2; zero/zero contributes zero."""
    mean = (pair[:, 0] + pair[:, 1]) * .5
    difference = pair[:, 1] - pair[:, 0]
    values = np.divide(difference*difference, mean, out=np.zeros_like(mean), where=mean > 0)
    return float(values.sum())


def initial_pair(totals, selected):
    positions = np.flatnonzero(selected)
    if not len(positions):
        raise ValueError("empty positive-outflow source cohort")
    pair = np.zeros((len(totals), 2))
    pair[positions, 0] = 1 / len(positions)
    pair[positions, 1] = totals[positions] / totals[positions].sum(dtype=np.float64)
    return pair


def trajectory(transition, boundary, observation, pair, steps):
    active, absorbed = pair.copy(), np.zeros((boundary.shape[0], 2))
    outputs, records = [], []
    previous_fisher = float("inf")
    for step in range(steps + 1):
        grouped = observation @ active + absorbed
        mass_error = float(np.max(np.abs(active.sum(axis=0) + absorbed.sum(axis=0) - 1)))
        refined = fisher_midpoint(active) + fisher_midpoint(absorbed)
        coarse = fisher_midpoint(grouped)
        if not np.isfinite(active).all() or not np.isfinite(absorbed).all() or np.any(active < 0) or mass_error > TOL:
            raise ValueError("invalid propagated probability or mass")
        if coarse > refined + TOL or refined > previous_fisher + TOL or refined > 4 + TOL:
            raise ValueError("Fisher data-processing invariant failed")
        records.append({"step": step, "mass_error": mass_error,
                        "absorbed_probability": absorbed.sum(axis=0).tolist(),
                        "active_id_terminal_category_fisher": refined, "category_fisher": coarse,
                        "category_total_variation": float(np.abs(grouped[:, 1]-grouped[:, 0]).sum()*.5)})
        outputs.append(grouped.T)
        previous_fisher = refined
        if step < steps:
            absorbed += boundary @ active
            active = transition @ active
    return records, np.asarray(outputs)


def hidden_blocks(transition, boundary, category_weights, totals, codes, labels):
    known_categories = np.array([label not in SPECIAL for label in labels])
    known = known_categories[codes]
    hidden = ~known
    hh = transition[hidden, :][:, hidden].tocsc()
    hk = transition[hidden, :][:, known].tocsc()
    # Includes assigned post-only arrivals as well as active assigned arrivals.
    return_projection = sparse.csr_array((category_weights[hidden][:, known_categories] / totals[hidden, None]).T)
    terminal_hidden = np.asarray(boundary[~known_categories, :][:, hidden].sum(axis=0)).ravel()
    partition = np.asarray(hh.sum(axis=0)).ravel() + np.asarray(return_projection.sum(axis=0)).ravel() + terminal_hidden
    if np.any(np.abs(partition - 1) > TOL):
        raise ValueError("hidden continuation/return/terminal partition failed")
    return known, hidden, known_categories, hh, hk, return_projection, terminal_hidden


def first_excursion(blocks, boundary, pair, codes, labels, last_step):
    known, hidden, known_categories, hh, hk, projection, terminal_hidden = blocks
    if np.any(pair[hidden] != 0) or np.any(np.abs(pair.sum(axis=0) - 1) > TOL):
        raise ValueError("first-excursion probes must start wholly in assigned sources")
    state = hk @ pair[known]
    entered = state.sum(axis=0)
    dead = (boundary @ pair)[~known_categories].sum(axis=0)
    direct = 1 - entered - dead
    returned = np.zeros(2)
    records, by_category = [], []
    first_by_middle = []
    for label in SPECIAL:
        part = state * (codes[hidden] == labels.index(label))[:, None]
        first_by_middle.append((projection @ part).T)
    for step in range(2, last_step + 1):
        arrival = projection @ state
        new_dead = terminal_hidden @ state
        state = hh @ state
        returned += arrival.sum(axis=0)
        dead += new_dead
        remainder = state.sum(axis=0)
        error = float(np.max(np.abs(direct + returned + dead + remainder - 1)))
        if error > TOL or np.any(arrival < 0) or not np.isfinite(state).all():
            raise ValueError("first-excursion partition conservation failed")
        records.append({"step": step, "first_return_probability": arrival.sum(axis=0).tolist(),
                        "cumulative_return_probability": returned.tolist(),
                        "hidden_terminal_probability": dead.tolist(),
                        "unresolved_active_hidden_probability": remainder.tolist(), "mass_error": error})
        by_category.append(arrival.T)
    return {"active_hidden_entry_probability": entered.tolist(),
            "hidden_terminal_at_first_step": ((boundary @ pair)[~known_categories].sum(axis=0)).tolist(),
            "assigned_at_first_step": direct.tolist(), "steps": records}, np.asarray(by_category), np.asarray(first_by_middle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dyad-result", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=16)
    parser.add_argument("--return-steps", type=int, default=64)
    parser.add_argument("--max-working-gib", type=float, default=8)
    args = parser.parse_args()
    if args.result.exists() or args.cache_dir.exists():
        raise FileExistsError("preserve existing analysis outputs")
    if args.steps < 1 or args.return_steps < 2:
        raise ValueError("positive trajectory and at least two excursion steps required")
    started = time.perf_counter()
    dyad = json.loads(args.dyad_result.read_text(encoding="utf-8"))
    stamps = {}
    for artifact in dyad["artifacts"].values():
        path = Path(artifact["path"])
        stat = path.stat()
        if stat.st_size != artifact["bytes"] or digest(path) != artifact["sha256"]:
            raise ValueError("dyad artifact changed")
        stamps[str(path)] = (stat.st_size, stat.st_mtime_ns)
    if digest(Path(__file__).with_name("dyad_return_paths.py")) != dyad["source_code_sha256"]:
        raise ValueError("dyad-producing source changed")
    keys = np.load(dyad["artifacts"]["dyad_keys.npy"]["path"], mmap_mode="r")
    weights = np.load(dyad["artifacts"]["dyad_weights.npy"]["path"], mmap_mode="r")
    with np.load(dyad["artifacts"]["source_categories.npz"]["path"]) as cache:
        ids, codes, totals = cache["source_ids"], cache["source_category_codes"], cache["source_out_weight"]
        category_weights, labels = cache["out_category_weight_all"], cache["category_labels"].tolist()
    transition, boundary, observation, scope = build_operators(
        keys, weights, ids, codes, totals, category_weights, labels,
        expected_terminal_dyads=dyad["terminal_target_dyads"], max_working_gib=args.max_working_gib)
    if scope["self_dyads"] != dyad["self_dyads"] or scope["self_weight"] != dyad["self_weight"] or scope["terminal_target_weight"] != dyad["terminal_target_weight"]:
        raise ValueError("operator differs from prior self/terminal census")
    blocks = hidden_blocks(transition, boundary, category_weights, totals, codes, labels)
    records, observed, excursions, middle = [], [], [], []
    for code, label in enumerate(labels):
        if label in SPECIAL:
            continue
        selected = codes == code
        pair = initial_pair(totals, selected)
        trace, outputs = trajectory(transition, boundary, observation, pair, args.steps)
        if trace[0]["category_fisher"] > TOL:
            raise ValueError("initial category observation must agree")
        kernel, arrivals, first_middle = first_excursion(blocks, boundary, pair, codes, labels, args.return_steps)
        records.append({"category": label, "positive_outflow_sources": int(selected.sum()),
                        "cohort_out_weight": int(totals[selected].sum()), "trajectory": trace, "first_excursion": kernel})
        observed.append(outputs)
        excursions.append(arrivals)
        middle.append(first_middle)
        print(f"walk + first return complete: {label} ({len(records)}/27)", flush=True)
    for name, before in stamps.items():
        stat = Path(name).stat()
        if (stat.st_size, stat.st_mtime_ns) != before:
            raise ValueError("input changed during calculation")
    args.cache_dir.mkdir(parents=True)
    sparse.save_npz(args.cache_dir / "active_transition.npz", transition)
    sparse.save_npz(args.cache_dir / "terminal_boundary.npz", boundary)
    np.savez_compressed(args.cache_dir / "source_scope.npz", source_ids=ids, source_codes=codes,
                        source_out_weight=totals, category_labels=np.asarray(labels))
    np.savez_compressed(args.cache_dir / "probe_traces.npz", category_observation=np.asarray(observed),
                        first_return_by_target=np.asarray(excursions), first_return_step2_by_initial_middle=np.asarray(middle),
                        source_categories=np.asarray([r["category"] for r in records]),
                        target_categories=np.asarray(labels), known_target_categories=np.asarray(labels)[blocks[2]],
                        middle_categories=np.asarray(SPECIAL), probe_order=np.asarray(["uniform_source", "out_weight_source"]))
    artifacts = {path.name: {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest(path)}
                 for path in sorted(args.cache_dir.glob("*.npz"))}
    result = {"schema": "malecns-hidden-walk-information-v1", "scope": scope, "cohorts": records,
              "category_order": labels, "probe_order": ["uniform_source", "out_weight_source"],
              "steps": args.steps, "return_steps": args.return_steps, "artifacts": artifacts,
              "dyad_result": str(args.dyad_result.resolve()), "dyad_result_sha256": digest(args.dyad_result),
              "input_artifacts": dyad["artifacts"], "sources": dyad["sources"],
              "source_code_sha256": digest(__file__), "test_code_sha256": digest(Path(__file__).resolve().parents[2] / "tests/test_malecns_hidden_walk.py"),
              "software": {"python": platform.python_version(), "executable": sys.executable,
                           "numpy": np.__version__, "scipy": scipy.__version__},
              "argv": sys.argv, "elapsed_seconds": time.perf_counter() - started,
              "interpretation": "Supplied contact-normalized absorbing structural walk, all raw outgoing weights retained. Active IDs remain distinct; terminal IDs are lumped only by observed category. Fisher coordinate is uniform-vs-outweight source mixture alpha at 0.5. Refined Fisher resolves active IDs plus terminal category, not all terminal IDs. First return means first arrival at any assigned-neuron ID after entering active nonassigned IDs on step 1, including assigned terminal arrivals. Model steps are not physical time. No biological memory, activity, independent sample inference or full Riemannian metric is established."}
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("HIDDEN_WALK_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
