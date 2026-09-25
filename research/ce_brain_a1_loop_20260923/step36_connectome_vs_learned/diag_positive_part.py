"""Post-hoc diagnostic for step 36 (does NOT change the frozen verdict): learned HR->HD weights have negative lobes
(synapse counts cannot); correlate only the positive part of the learned profile with the connectome PEN profile."""
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("c", HERE / "compare_learned.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
L = {k: np.array(v) for k, v in r["learned"].items()}
out = {}
for name, d in r["datasets"].items():
    C = {k: np.array(v) for k, v in d["profiles"].items()}
    idxr = (np.arange(16) * d["reflection"]) % 16
    a, b = ("PEN_R", "PEN_L") if d["side_swap"] else ("PEN_L", "PEN_R")
    pl, pr = np.maximum(L["HR_L"], 0), np.maximum(L["HR_R"], 0)
    out[name] = {"corr_pos_L": c.corr(pl, C[a][idxr]), "corr_pos_R": c.corr(pr, C[b][idxr]),
                 "learned_negative_fraction": float(np.sum(np.minimum(L["HR_L"], 0) ** 2) / np.sum(L["HR_L"] ** 2))}
    print(name, {k: round(v, 3) for k, v in out[name].items()})
(HERE / "diag_positive_part.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
