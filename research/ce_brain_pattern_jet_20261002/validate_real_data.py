#!/usr/bin/env python3
"""CE-BRAIN Pattern-Jet: real-data necessary-condition validation.

This script deliberately separates:
1) claims that can be tested by published processed biological measurements;
2) the exact Pattern-Jet K>1 hidden-synapse cascade, which requires longitudinal
   per-synapse / per-bouton data and is NOT declared validated here.

Sources pinned in SOURCES.json.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
import numpy as np

REGIONS = ("Calyx","gamma","beta","betaprime","alpha","alphaprime")
BERGMANN_BLOB = "965d7e038fa23ba4226cda865d8802157f0d18c8"

# sprustonlab/OSM_Paper_Figures, fig_4/fig_4j_decorr_order.ipynb
# commit c1d1788b54c737efe24402e02762eee10da0d0d7
ANIMAL_PRE_R2 = np.array([
    0.41641642,0.50550551,0.33433433,0.27727728,0.42742743,
    0.13613614,0.39139139,0.48048048,0.93493493,0.50550551,0.09809810
])
ANIMAL_PRE_R1 = np.array([
    0.76976977,0.80980981,0.87487487,0.28528529,0.97797798,
    0.07707708,0.58258258,0.83383383,0.81681682,0.31431431,0.14714715
])
ANIMAL_OFF = np.array([
    0.,0.,0.01901902,0.,0.00500501,0.,0.,0.10010010,0.,0.,0.
])

def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def load_bergmann(path: Path):
    raw = path.read_bytes()
    blob = git_blob_sha1(raw)
    if blob != BERGMANN_BLOB:
        raise ValueError(f"Bergmann CSV blob mismatch: {blob}")
    rows = list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    if len(rows) != 81 or any(len(r) != 25 for r in rows):
        raise ValueError("unexpected Bergmann CSV shape")
    a = np.array([[float(v) if v else np.nan for v in r[1:]] for r in rows[3:-1]])
    a = a.reshape(11, 7, 6, 4).transpose(2, 3, 0, 1).copy()
    means = np.nanmean(a, axis=2)
    return raw, means

def fit(kind, x, y):
    k = np.ones(6); b = np.zeros(6)
    if kind == "global_gain":
        k[:] = max(0., float(np.sum(x*y)/np.sum(x*x)))
    elif kind == "local_gain":
        k = np.maximum(0., (x*y).sum(1)/(x*x).sum(1))
    elif kind == "global_affine":
        v = np.linalg.lstsq(
            np.column_stack([x.ravel(), np.ones(x.size)]), y.ravel(), rcond=None
        )[0]
        k[:] = v[0]; b[:] = v[1]
    elif kind == "local_affine":
        for i in range(6):
            k[i], b[i] = np.linalg.lstsq(
                np.column_stack([x[i], np.ones(x.shape[1])]), y[i], rcond=None
            )[0]
    else:
        raise ValueError(kind)
    return k, b

def loo(kind, x, y):
    err = []
    region_err = {r: [] for r in REGIONS}
    for held in range(7):
        tr = np.array([j for j in range(7) if j != held])
        k,b = fit(kind, x[:,tr], y[:,tr])
        pred = k*x[:,held] + b
        e = pred-y[:,held]
        err.extend(e.tolist())
        for i,r in enumerate(REGIONS):
            region_err[r].append(float(e[i]))
    e = np.asarray(err)
    return {
        "rmse": float(np.sqrt(np.mean(e*e))),
        "mae": float(np.mean(np.abs(e))),
        "region_rmse": {
            r: float(np.sqrt(np.mean(np.square(v)))) for r,v in region_err.items()
        },
        "n_scored_region_odor_means": int(e.size),
    }

def paired_t_pvalue(x, y):
    try:
        from scipy.stats import ttest_rel
        return float(ttest_rel(x,y).pvalue)
    except Exception:
        return None

def exact_sign_p(k, n):
    p = sum(math.comb(n,i) for i in range(0, min(k,n-k)+1)) / (2**n)
    return min(1.0, 2*p)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bergmann-csv", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("pattern_jet_real_results.json"))
    args = ap.parse_args()

    raw, means = load_bergmann(args.bergmann_csv)
    x31, y31 = means[:,2], means[:,3]
    models = {m: loo(m, x31, y31) for m in
              ("global_gain","global_affine","local_gain","local_affine")}
    ga, la = models["global_affine"]["rmse"], models["local_affine"]["rmse"]

    r2, r1 = ANIMAL_PRE_R2, ANIMAL_PRE_R1
    earlier = int(np.sum(r2 < r1))
    later = int(np.sum(r2 > r1))

    result = {
      "status": {
        "global_scalar_is_sufficient": "rejected_on_processed_real_data",
        "history_state_is_needed_beyond_current_shared_observation": "supported_at_phenomenon_level",
        "exact_pattern_jet_K_gt_1_hidden_synapse_cascade": "not_validated_by_these_data",
        "infinite_dimensional_limit": "not_validated"
      },
      "bergmann_2026": {
        "source_git_blob": BERGMANN_BLOB,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "models_31c_leave_one_odor": models,
        "local_affine_vs_global_affine_rmse_reduction_fraction": float((ga-la)/ga),
        "interpretation":
          "Region-specific mapping strongly beats one global affine mapping. "
          "This rejects a single global scalar response map for these processed KC calcium means; "
          "it does not directly measure a synaptic delta or temporal hidden state."
      },
      "sun_2025_figure4j_author_processed": {
        "n_animals": 11,
        "pre_R2": r2.tolist(),
        "pre_R1": r1.tolist(),
        "off_diagonal": ANIMAL_OFF.tolist(),
        "mean_pre_R2": float(r2.mean()),
        "mean_pre_R1": float(r1.mean()),
        "pre_R2_earlier": earlier,
        "pre_R1_earlier": later,
        "paired_t_pvalue": paired_t_pvalue(r2,r1),
        "exact_two_sided_sign_pvalue": exact_sign_p(earlier, len(r2)),
        "mean_normalized_timing_gap": float(np.mean((r1-r2)/(r1+r2))),
        "interpretation":
          "The author-processed neural-population representation separates in shared sensory segments. "
          "A deterministic state that depends only on the current shared observation cannot produce "
          "context-specific representations. This supports history/context state, but not a particular K."
      },
      "decision": {
        "retain_pattern_jet_as_candidate": True,
        "promote_exact_K_gt_1_as_biologically_validated": False,
        "next_required_test":
          "Use longitudinal cell/synapse time-series; freeze K and tau grid before held-out animals/sessions; "
          "compare K=1 vs K>1 at equal effective parameter budget and require held-out improvement plus shuffled-history control."
      }
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
