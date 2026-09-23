"""A1 loop step 4: is KC->KC coupling a pattern-completion operator? (CONTRACT.md)

python kc_completion.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.stats import rankdata, spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MALECNS = ROOT / "verify/MaleCNS"
PERMUTATIONS, MIN_PER_SIDE, SEED = 200, 90, 20260923


def residual(y, x):
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def partial_rho(s_rank, c_res, d_rank):
    r = residual(s_rank, d_rank)
    return float(np.corrcoef(r, c_res)[0, 1])


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("g", MALECNS / "neuron_graph.py")
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    graph = gm.load(MALECNS / "neuron_graph_result.json")
    n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as source:
        t = ipc.open_file(source).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    kc, pn = defaultdict(list), defaultdict(list)
    soma = {}
    for p, f, ty, cl, side, loc in zip(pos, found, t["type"].to_pylist(), t["class"].to_pylist(),
                                        t["somaSide"].to_pylist(), t["somaLocation"].to_pylist()):
        if not f:
            continue
        if ty and ty.startswith("KC") and side in ("L", "R") and loc is not None:
            kc[(ty, side)].append(int(p))
            soma[int(p)] = np.array(loc, dtype=float)
        elif cl == "ALPN" and ty:
            pn[ty].append(int(p))
    pn_types = sorted(pn)
    pn_nodes = np.array([v for ty in pn_types for v in pn[ty]])
    pn_col = np.array([i for i, ty in enumerate(pn_types) for _ in pn[ty]])
    agg = sparse.csr_array((np.ones(len(pn_nodes)), (np.arange(len(pn_nodes)), pn_col)), shape=(len(pn_nodes), len(pn_types)))
    rng = np.random.default_rng(SEED)
    units, sym_num, sym_den = [], 0.0, 0.0
    for (ty, side), nodes in sorted(kc.items()):
        if len(nodes) < MIN_PER_SIDE:
            continue
        nodes = np.array(nodes)
        profile = (A[pn_nodes, :][:, nodes].T @ agg).toarray()          # KC x PN-type
        keep = profile.sum(axis=1) > 0
        nodes, profile = nodes[keep], profile[keep]
        unit = profile / np.linalg.norm(profile, axis=1, keepdims=True)
        W = A[nodes, :][:, nodes].toarray()
        sym_num += float(np.sum((W - W.T) ** 2))
        sym_den += float(np.sum((W + W.T) ** 2))
        C = W + W.T
        xyz = np.array([soma[v] for v in nodes])
        D = np.linalg.norm(xyz[:, None, :] - xyz[None, :, :], axis=2)
        iu = np.triu_indices(len(nodes), 1)
        S = unit @ unit.T
        c, d, s = C[iu], D[iu], S[iu]
        d_rank, c_res = rankdata(d), residual(rankdata(c), rankdata(d))
        obs = partial_rho(rankdata(s), c_res, d_rank)
        null = []
        for _ in range(PERMUTATIONS):
            perm = rng.permutation(len(nodes))
            null.append(partial_rho(rankdata(S[np.ix_(perm, perm)][iu]), c_res, d_rank))
        p = (1 + np.sum(np.array(null) >= obs)) / (PERMUTATIONS + 1)
        units.append({"subtype": ty, "side": side, "kcs": int(len(nodes)), "pairs": int(len(c)),
                      "fraction_pairs_connected": float(np.mean(c > 0)),
                      "rho_partial": obs, "p": float(p), "null_mean": float(np.mean(null)), "null_sd": float(np.std(null)),
                      "rho_raw_similarity_coupling": float(spearmanr(s, c).statistic),
                      "rho_coupling_distance": float(spearmanr(c, d).statistic),
                      "pass": bool(obs > 0 and p < 0.01)})
        print(f"{ty} {side}: n={len(nodes)} rho_p={obs:.4f} p={p:.4f} raw={units[-1]['rho_raw_similarity_coupling']:.4f} "
              f"c~d={units[-1]['rho_coupling_distance']:.4f}", flush=True)
    frac = float(np.mean([u["pass"] for u in units]))
    med = float(np.median([u["rho_partial"] for u in units]))
    result = {"schema": "ce-a1-step04-kc-completion", "code_sha256": code_hash, "units": units,
              "K2": {"fraction_units_pass": frac, "median_rho_partial": med, "pass": frac >= 0.6 and med > 0},
              "kc_kc_antisymmetric_energy_fraction": sym_num / sym_den,
              "verdict": "KC_PATTERN_COMPLETION_SUPPORTED" if frac >= 0.6 and med > 0 else "KC_PATTERN_COMPLETION_NOT_SUPPORTED"}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({k: v for k, v in result.items() if k != "units"}, indent=1, default=float))


if __name__ == "__main__":
    main()
