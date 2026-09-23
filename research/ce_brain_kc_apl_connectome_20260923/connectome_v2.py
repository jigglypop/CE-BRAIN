"""Connectome quantities for the v2 menu (structure only; never opens calcium data).

h_c   : fraction of all synaptic input onto KCs in compartment c that comes from APL
class : for each compartment, the share of KC input synapses received by each KC class
"""
import json
from pathlib import Path

import numpy as np

import kc_apl_model as base

CLASSES = {"gamma": ("KCg",), "ab": ("KCab",), "apbp": ("KCa'b'",)}


def main():
    graph_module = base.load_module("malecns_neuron_graph", base.MALECNS / "neuron_graph.py")
    roi_module = base.load_module("malecns_neuron_roi", base.MALECNS / "neuron_roi.py")
    graph = graph_module.load(base.MALECNS / "neuron_graph_result.json", verify_hash=False)
    roi = roi_module.load(base.MALECNS / "neuron_roi_result.json", verify_hash=False)
    names = np.array(graph["type_labels"] + [""])[graph["type_code"]]
    everyone = np.ones(len(names), dtype=bool)
    kc, apl = np.char.startswith(names, "KC"), names == "APL"
    index = {name: i for i, name in enumerate(roi["roi_names"])}
    per_roi = lambda counts: np.array([sum(counts[index[f"{r}({s})"]] for s in "LR") for _, r in base.COMPARTMENTS],
                                      dtype=float)
    all_to_kc = per_roi(roi_module.type_roi_counts(graph, roi, everyone, kc))
    apl_to_kc = per_roi(roi_module.type_roi_counts(graph, roi, apl, kc))
    kc_to_kc = per_roi(roi_module.type_roi_counts(graph, roi, kc, kc))
    class_input = {}
    for label, prefixes in CLASSES.items():
        members = np.zeros(len(names), dtype=bool)
        for prefix in prefixes:
            members |= np.char.startswith(names, prefix)
        class_input[label] = per_roi(roi_module.type_roi_counts(graph, roi, everyone, members))
    shares = np.array([class_input[k] for k in CLASSES]).T
    out = {"compartments": [c for c, _ in base.COMPARTMENTS],
           "all_to_kc": all_to_kc.astype(int).tolist(), "apl_to_kc": apl_to_kc.astype(int).tolist(),
           "kc_to_kc": kc_to_kc.astype(int).tolist(),
           "h_apl_input_fraction": (apl_to_kc / all_to_kc).tolist(),
           "class_order": list(CLASSES), "class_input_share": (shares / shares.sum(axis=1, keepdims=True)).tolist(),
           "unclassified_kc_input_share": (1 - shares.sum(axis=1) / all_to_kc).tolist()}
    Path("connectome_v2.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
