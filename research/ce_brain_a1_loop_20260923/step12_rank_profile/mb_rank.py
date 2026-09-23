"""Discovery: rank profile of the mushroom-body path ALPN -> KC -> MBON (same measures as rank_profile.py)."""
import importlib.util, json
from pathlib import Path
import numpy as np
from scipy import sparse
import rank_profile as rp

def main():
    import pyarrow as pa, pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("g", rp.MALECNS / "neuron_graph.py"); gm = importlib.util.module_from_spec(spec); spec.loader.exec_module(gm)
    graph = gm.load(rp.MALECNS / "neuron_graph_result.json"); n = len(graph["node_ids"])
    A = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(gm.SOURCE_DIR / "annotations.feather"), "r") as s: t = ipc.open_file(s).read_all()
    pos, found = gm.locate(t["bodyId"].to_numpy(), graph["node_ids"])
    cls = {int(p): (c or "", ty or "") for p, f, c, ty in zip(pos, found, t["class"].to_pylist(), t["type"].to_pylist()) if f}
    sel = lambda f: np.array(sorted(v for v, (c, ty) in cls.items() if f(c, ty)))
    idx = {"ALPN": sel(lambda c, ty: c == "ALPN"), "KC": sel(lambda c, ty: ty.startswith("KC")), "MBON": sel(lambda c, ty: c == "MBON")}
    rng = np.random.default_rng(20260923); out = {"sizes": {k: int(len(v)) for k, v in idx.items()}, "paths": []}
    for a, b in (("ALPN", "KC"), ("KC", "MBON")):
        M = A[idx[a], :][:, idx[b]]
        M = M[:, np.asarray(M.sum(axis=0)).ravel() > 0]; M = M[np.asarray(M.sum(axis=1)).ravel() > 0, :]
        Mn = M @ sparse.diags(1 / np.asarray(M.sum(axis=0)).ravel()); frob2 = float(Mn.multiply(Mn).sum())
        k = min(M.shape) - 1; s = rp.spectrum(M, k); _, r90, cov = rp.summaries(s, frob2)
        coo = M.tocoo(); null = sparse.coo_array((coo.data, (coo.row, rng.permutation(coo.col))), shape=M.shape).tocsr(); null.sum_duplicates()
        nn = null @ sparse.diags(1 / np.where(np.asarray(null.sum(axis=0)).ravel() > 0, np.asarray(null.sum(axis=0)).ravel(), 1))
        s0 = rp.spectrum(null, k); _, r90_0, _ = rp.summaries(s0, float(nn.multiply(nn).sum()))
        row = {"from": a, "to": b, "pre": int(M.shape[0]), "post": int(M.shape[1]), "rank90": r90, "min_dim": int(min(M.shape)), "null_rank90": r90_0}
        out["paths"].append(row); print(json.dumps(row), flush=True)
    Path(__file__).with_name("mb_rank.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(out["sizes"])

main()
