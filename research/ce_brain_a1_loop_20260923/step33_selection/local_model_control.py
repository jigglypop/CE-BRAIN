"""Positive control for step 33 (pre-freeze): a 'local model' ring (narrow excitation + global inhibition, Kim et al.
2017 local model) run through the same pipeline; and a 'global cosine' ring for contrast."""
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sel", HERE / "selection.py")
sel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sel)


def ring(kind, n=48):
    ang = np.repeat(np.arange(16) * 2 * np.pi / 16, n // 16)
    d = ang[:, None] - ang[None, :]
    if kind == "local":
        W = np.exp(6.0 * (np.cos(d) - 1)) - 0.35
    else:
        W = 0.2 + np.cos(d)
    W = W * (1 + 1e-3 * np.random.default_rng(1).standard_normal(W.shape))
    return W, np.arange(n), ang


out = {}
for kind in ("local", "global"):
    W, epg, ang = ring(kind)
    out[kind] = sel.analyse(W, epg, ang)
    r = out[kind]
    print(kind, "base", r["base_bump"], "two-cue", r["two_cue_final"], "S1", r["S1_unique"], "S2", r["S2_local_signature"],
          "ratio", r["ratio_180_over_90"], "jump thr", r["jump_threshold"])
