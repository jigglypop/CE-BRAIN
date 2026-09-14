"""Fixed-source label permutations for catalogue-conditional type prediction."""

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


def shuffle_within_blocks(labels, blocks, rng):
    shuffled = labels.copy()
    for indices in blocks:
        shuffled[indices] = rng.permutation(labels[indices])
    return shuffled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type-result", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=24)
    args = parser.parse_args()
    if args.result.exists() or args.replicates < 1:
        raise ValueError("existing output or invalid replicate count")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    source = Path(__file__).with_name("type_conditioned_closure.py")
    spec = importlib.util.spec_from_file_location("type_closure", source)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    typed = json.loads(args.type_result.read_text(encoding="utf-8"))
    if core.digest(source) != typed["source_code_sha256"]:
        raise ValueError("scoring source changed")
    whole_path = Path(typed["whole_result"])
    if core.digest(whole_path) != typed["whole_result_sha256"]:
        raise ValueError("whole result changed")
    whole = json.loads(whole_path.read_text(encoding="utf-8"))
    arrays_path = Path(whole["arrays"]["path"])
    ann_path = Path(whole["sources"]["annotations.feather"]["path"])
    if core.digest(arrays_path) != typed["arrays_sha256"] or core.digest(ann_path) != typed["annotation_sha256"]:
        raise ValueError("analysis input changed")
    with np.load(arrays_path, allow_pickle=False) as arrays:
        ids, codes = arrays["annotation_ids"], arrays["category_codes"]
        labels, counts = arrays["category_labels"].tolist(), arrays["out_weight"]
    with pa.memory_map(str(ann_path), "r") as stream:
        table = ipc.open_file(stream).read_all()
    ann_ids = table["bodyId"].combine_chunks().to_numpy()
    order = np.argsort(ann_ids)
    if not np.array_equal(ann_ids[order], ids):
        raise ValueError("annotation identity mismatch")
    types = table["type"].to_pylist()
    types = [types[i] for i in order]
    selected = np.array([labels[c] not in ("ANNOTATED_GLIA", "ANNOTATED_UNCLASSIFIED", "UNANNOTATED_SEGMENT") for c in codes])
    counts, codes = counts[selected], codes[selected]
    types = [t for t, keep in zip(types, selected) if keep]
    lookup = {}
    refined = np.array([lookup.setdefault((int(c), t), len(lookup)) for c, t in zip(codes, types)])
    degree = counts.sum(axis=1)
    eligible = (degree > 0) & np.array([t is not None for t in types])
    families = {"within_superclass": [], "within_superclass_degree_decile": []}
    for c in np.unique(codes):
        indices = np.flatnonzero(eligible & (codes == c))
        if not len(indices):
            continue
        families["within_superclass"].append(indices)
        cuts = np.quantile(degree[indices], np.arange(1, 10) / 10)
        bins = np.searchsorted(cuts, degree[indices], side="right")
        for b in np.unique(bins):
            families["within_superclass_degree_decile"].append(indices[bins == b])
    observed = typed["predictions"][0]
    if observed["total_dirichlet_pseudocount"] != 1:
        raise ValueError("expected primary alpha=1")
    records = []
    for family_index, (family, blocks) in enumerate(families.items()):
        for replicate in range(args.replicates):
            seed = 20260914 + 100000 * family_index + replicate
            shuffled = shuffle_within_blocks(refined, blocks, np.random.default_rng(seed))
            for block in blocks:
                if not np.array_equal(np.sort(refined[block]), np.sort(shuffled[block])):
                    raise ValueError("label margin changed")
            d, peers, base, candidate = core.loo_scores(counts, codes, shuffled, 1)
            summary = core.score_summary(d, peers, base, candidate, np.ones(len(d), bool))
            if abs(summary["parent_loss"] - observed["all"]["parent_loss"]) > 1e-12:
                raise ValueError("parent baseline changed")
            records.append({"family": family, "replicate": replicate, "seed": seed, **summary})
            print(f"{family} {replicate + 1}/{args.replicates} reduction={summary['relative_loss_reduction']:.6f}", flush=True)
    result = {"schema": "malecns-type-label-control-v1", "type_result": str(args.type_result.resolve()),
              "type_result_sha256": core.digest(args.type_result), "source_code_sha256": core.digest(__file__),
              "scoring_code_sha256": core.digest(source), "numpy": np.__version__,
              "replicates_per_family": args.replicates, "total_dirichlet_pseudocount": 1,
              "observed": observed["all"], "controls": records,
              "interpretation": "All source counts and degrees stay fixed. Type labels permute within parent superclass; the second family also preserves within-parent degree-decile label counts. Missing labels and zero-out sources stay fixed. No p-value or independent biological replication is claimed."}
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("TYPE_LABEL_CONTROL_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
