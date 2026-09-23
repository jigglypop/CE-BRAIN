"""A1 step 14: cross-species brain->body latent channel and MB expand/compress (CONTRACT.md).

python cross_species.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("latent_confirm", HERE.parent / "step13_latent_confirm/latent_confirm.py")
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)
LARVA = ROOT / "data/external/winding_2023_larva/Supplementary-Data-S1.zip"
WORM = ROOT / "data/external/cook_2019_celegans/SI 5 Connectome adjacency matrices, corrected July 2020.xlsx"
LARVA_ROWS = {"PN", "PN-somato", "LN", "KC", "MBON", "MBIN", "MB-FBN", "MB-FFN", "LHN", "CN", "pre-DN-VNC", "pre-DN-SEZ", "DN-SEZ"}
BODY_MN = ("DA", "DB", "DD", "VA", "VB", "VD", "AS")
COMMAND = ("AVA", "AVB", "AVD", "AVE", "PVC")


def block(rows, cols, W):
    return lc.trim(sparse.csr_array(W[np.ix_(rows, cols)]))


def assess(M, rng):
    real, null = lc.measures(M), lc.measures(lc.edge_swap_null(M, rng))
    return {"real": real, "null_edge_swap": null, "ratio_rank90": real["rank90"] / null["rank90"]}


def larva(rng):
    import pandas as pd
    z = zipfile.ZipFile(LARVA)
    m = pd.read_csv(io.BytesIO(z.read("Supplementary-Data-S1/all-all_connectivity_matrix.csv")), index_col=0)
    ann = pd.read_csv(io.BytesIO(z.read("Supplementary-Data-S1/annotations.csv")))
    ctype = {}
    for _, r in ann.iterrows():
        for side in ("left_id", "right_id"):
            if str(r[side]) != "no pair":
                ctype[str(r[side])] = r["celltype"]
    ids = [str(i) for i in m.index]
    if ids != [str(c) for c in m.columns]:
        raise ValueError("larval matrix rows and columns differ")
    W = m.to_numpy(dtype=float)
    kind = np.array([ctype.get(i, "") for i in ids])
    dn = np.flatnonzero(kind == "DN-VNC")
    rows = np.flatnonzero(np.isin(kind, list(LARVA_ROWS)))
    out = {"total_neurons": len(ids), "channel_neurons": int(len(dn)), "M1": assess(block(rows, dn, W), rng)}
    out["MB_PN_KC"] = assess(block(np.flatnonzero(kind == "PN"), np.flatnonzero(kind == "KC"), W), rng)
    out["MB_KC_MBON"] = assess(block(np.flatnonzero(kind == "KC"), np.flatnonzero(kind == "MBON"), W), rng)
    return out


def worm(rng, gap=False):
    import pandas as pd
    def parse(sheet):
        x = pd.read_excel(WORM, sheet_name=sheet, header=None)
        groups, names = [], []
        g = None
        for i in range(3, x.shape[0]):
            if isinstance(x.iat[i, 0], str):
                g = x.iat[i, 0]
            if isinstance(x.iat[i, 2], str):
                groups.append(g)
                names.append(x.iat[i, 2].strip())
        ccols = [j for j in range(3, x.shape[1]) if isinstance(x.iat[2, j], str)]
        rrows = [i for i in range(3, x.shape[0]) if isinstance(x.iat[i, 2], str)]
        frame = x.iloc[rrows, ccols].apply(pd.to_numeric, errors="coerce").fillna(0)
        frame.index = names
        frame.columns = [str(x.iat[2, j]).strip() for j in ccols]
        return groups, frame
    rgrp, chem = parse("hermaphrodite chemical")
    if gap:
        _, gj = parse("hermaphrodite gap jn symmetric")
        gj = gj.groupby(level=0).sum().T.groupby(level=0).sum().T  # merge any duplicated labels
        chem = chem + gj.reindex(index=chem.index, columns=chem.columns).fillna(0)
    rnames, cnames = list(chem.index), list(chem.columns)
    W = chem.to_numpy(dtype=float)
    body = [j for j, c in enumerate(cnames) if c.startswith(BODY_MN) and c[len(c.rstrip("0123456789")):].isdigit()]
    inter = [i for i, gname in enumerate(rgrp) if gname == "INTERNEURONS"]
    out_total = W.sum(axis=1)
    to_body = W[:, body].sum(axis=1)
    channel_rows = [i for i in inter if out_total[i] > 0 and to_body[i] / out_total[i] >= 0.2]
    channel_names = [rnames[i] for i in channel_rows]
    col_of = {c: j for j, c in enumerate(cnames)}
    channel_cols = [col_of[n] for n in channel_names if n in col_of]
    m1_rows = [i for i in inter if i not in channel_rows]
    res = {"channel_neurons": len(channel_cols), "channel_names": channel_names,
           "total_neurons": len(rnames),
           "M1": assess(block(m1_rows, channel_cols, W), rng),
           "M2": assess(block(channel_rows, body, W), rng)}
    cmd_names = [n for n in rnames if n.startswith(COMMAND)]
    cmd_cols = [col_of[n] for n in cmd_names if n in col_of]
    cmd_rows = [rnames.index(n) for n in cmd_names]
    res["alt_command_channel"] = {"names": cmd_names,
                                  "M1": assess(block([i for i in inter if i not in cmd_rows], cmd_cols, W), rng)}
    return res


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    rng = np.random.default_rng(lc.SEED)
    adult = json.loads((HERE.parent / "step13_latent_confirm/results.json").read_text(encoding="utf-8"))
    A = {"total_neurons": 199713, "channel_neurons": 1308, "M1": adult["matrices"]["M1"], "M2": adult["matrices"]["M2"],
         "MB_PN_KC": adult["matrices"]["M5"], "MB_KC_MBON": adult["matrices"]["M4"]}
    L = larva(rng)
    Wm = worm(rng)
    Wg = worm(rng, gap=True)
    r = lambda d: d["M1"]["real"]["rank90"]
    util = lambda d: r(d) / d["channel_neurons"]
    x1 = r(Wm) < r(L) < r(A)
    x2 = all(0.22 <= util(d) <= 0.37 for d in (L, Wm))
    x3 = all(d["M1"]["ratio_rank90"] <= 0.8 for d in (L, Wm))
    x4 = 0.9 <= L["MB_PN_KC"]["ratio_rank90"] <= 1.1 and L["MB_KC_MBON"]["ratio_rank90"] < 0.7
    n = np.log([Wm["total_neurons"], L["total_neurons"], A["total_neurons"]])
    y = np.log([r(Wm), r(L), r(A)])
    slope = float(np.polyfit(n, y, 1)[0])
    result = {"schema": "ce-a1-step14-cross-species", "code_sha256": code_hash, "adult": A, "larva": L, "worm_chemical": Wm,
              "worm_chemical_plus_gap": Wg,
              "X1_ordering": bool(x1), "X2_utilization": {"adult": util(A), "larva": util(L), "worm": util(Wm), "pass": bool(x2)},
              "X3_structure": {"larva": L["M1"]["ratio_rank90"], "worm": Wm["M1"]["ratio_rank90"], "pass": bool(x3)},
              "X4_mb_larva": {"PN_KC": L["MB_PN_KC"]["ratio_rank90"], "KC_MBON": L["MB_KC_MBON"]["ratio_rank90"], "pass": bool(x4)},
              "report_loglog_slope_rank90_vs_total_neurons": slope}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    brief = lambda d: {k: (v["real"]["rank90"], round(v["real"]["PR"], 1), v["null_edge_swap"]["rank90"], round(v["ratio_rank90"], 3))
                       for k, v in d.items() if isinstance(v, dict) and "real" in v}
    print(json.dumps({"adult": brief(A), "larva": brief(L), "worm": brief(Wm), "worm_gap": brief(Wg),
                      "worm_channel": Wm["channel_names"], "worm_alt_command": brief(Wm["alt_command_channel"]),
                      "channels": {"adult": A["channel_neurons"], "larva": L["channel_neurons"], "worm": Wm["channel_neurons"]},
                      **{k: result[k] for k in ("X1_ordering", "X2_utilization", "X3_structure", "X4_mb_larva",
                                                "report_loglog_slope_rank90_vs_total_neurons")}}, indent=1, default=float))


if __name__ == "__main__":
    main()
