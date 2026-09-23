"""A1 loop step 6: CA1 convergence to cue templates and recovered-memory choice (CONTRACT.md).

python recovery.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HR = ROOT / "verify/Q-NPF-04/hippocampal_reinstatement"
NPZ = ROOT / "data/local/hippocampal-reinstatement/odor-place-windows-complete-v1/windows.npz"
NPZ_SHA = "890d5033b646bbb7135aedf7b72698c975a1d57aff77b17f30e2cc6841f767c0"
WINDOWS = ("precue", "earlycue", "latecue", "postcue")


def session_metrics(counts, trials, keep_units):
    x_all = np.sqrt(counts[:, :, keep_units] + 3 / 8)
    odor = np.array([t["odor_side"] == "left" for t in trials])
    correct = np.array([bool(t["correct"]) for t in trials])
    out = {}
    for w, name in enumerate(WINDOWS):
        valid = np.array([t["windows"][name]["reasons"] == [] and t["choice_reason"] == "resolved" for t in trials])
        c_idx = np.flatnonzero(valid & correct)
        e_idx = np.flatnonzero(valid & ~correct)
        x = x_all[:, w, :]
        mu, sd = x[c_idx].mean(axis=0), x[c_idx].std(axis=0)
        ok = sd > 0
        z = (x[:, ok] - mu[ok]) / sd[ok]
        own_d, other_d, dcorr = [], [], []
        for i in c_idx:
            rest = c_idx[c_idx != i]
            m_own = z[rest[odor[rest] == odor[i]]].mean(axis=0)
            m_oth = z[rest[odor[rest] != odor[i]]].mean(axis=0)
            a, b = np.linalg.norm(z[i] - m_own), np.linalg.norm(z[i] - m_oth)
            dcorr.append(b - a)
            own_d.append(a)
        tmpl = {o: z[c_idx[odor[c_idx] == o]].mean(axis=0) for o in (True, False)}
        derr = [np.linalg.norm(z[i] - tmpl[not odor[i]]) - np.linalg.norm(z[i] - tmpl[odor[i]]) for i in e_idx]
        between = np.linalg.norm(tmpl[True] - tmpl[False])
        out[name] = {"D_correct": float(np.mean(dcorr)), "D_error": float(np.mean(derr)) if derr else None,
                     "n_error": int(len(derr)), "kappa": float(np.mean(own_d) / between) if between > 0 else None}
    return out


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    if hashlib.sha256(NPZ.read_bytes()).hexdigest() != NPZ_SHA:
        raise SystemExit("window array identity mismatch")
    win = json.loads((HR / "odor_place_windows_complete_result.json").read_text(encoding="utf-8"))
    reg = {s["identifier"]: s for s in json.loads((HR / "odor_place_tetrode_regions_result.json").read_text(encoding="utf-8"))["sessions"]}
    arrays = np.load(NPZ)
    per_region = {}
    for region in ("CA1", "PFC"):
        by_rat = defaultdict(list)
        used = []
        for s in win["sessions"]:
            r = reg[s["identifier"]]
            if list(r["unit_ids"]) != list(s["unit_ids"]):
                raise ValueError(f"unit order mismatch {s['identifier']}")
            keep = np.array([g == region for g in r["regions"]])
            trials = s["trials"]
            correct = np.array([bool(t["correct"]) for t in trials])
            odor = np.array([t["odor_side"] == "left" for t in trials])
            if keep.sum() < 5 or min(np.sum(correct & odor), np.sum(correct & ~odor)) < 8:
                continue
            m = session_metrics(arrays[s["npz_keys"]["counts"]], trials, keep)
            by_rat[s["rat"]].append(m)
            used.append(s["identifier"])
        rats = {}
        for rat, sessions in by_rat.items():
            agg = {}
            for name in WINDOWS:
                vals = lambda key: [x[name][key] for x in sessions if x[name][key] is not None]
                err = [(x[name]["D_error"], x[name]["n_error"]) for x in sessions if x[name]["D_error"] is not None]
                agg[name] = {"D_correct": float(np.mean(vals("D_correct"))),
                             "D_error": float(np.mean([e for e, _ in err])) if err else None,
                             "n_error": int(sum(n for _, n in err)), "kappa": float(np.mean(vals("kappa")))}
            rats[rat] = agg
        r1 = [rats[k]["latecue"]["D_correct"] > rats[k]["precue"]["D_correct"] for k in rats]
        err_rats = [k for k in rats if rats[k]["latecue"]["n_error"] >= 5]
        r3a = [rats[k]["latecue"]["D_error"] < rats[k]["latecue"]["D_correct"] for k in err_rats]
        mean_err = float(np.mean([rats[k]["latecue"]["D_error"] for k in err_rats])) if err_rats else None
        r4 = [rats[k]["latecue"]["kappa"] < rats[k]["earlycue"]["kappa"] for k in rats]
        per_region[region] = {
            "sessions": used, "rats": rats,
            "R1": {"fraction": float(np.mean(r1)), "n": len(r1), "pass": np.mean(r1) >= 0.875},
            "R3": {"rats_with_errors": err_rats, "fraction_error_below_correct": float(np.mean(r3a)) if r3a else None,
                   "rat_mean_D_error_late": mean_err,
                   "pass": bool(r3a) and np.mean(r3a) >= 0.8 and mean_err is not None and mean_err < 0},
            "R4": {"fraction": float(np.mean(r4)), "n": len(r4), "pass": np.mean(r4) >= 0.75}}
    ca1 = per_region["CA1"]
    verdict = "HIPPOCAMPAL_RECOVERY_ATTRACTOR_SUPPORTED" if ca1["R3"]["pass"] and ca1["R4"]["pass"] else \
        "HIPPOCAMPAL_RECOVERY_ATTRACTOR_NOT_SUPPORTED"
    result = {"schema": "ce-a1-step06-hippocampal-recovery", "code_sha256": code_hash, "npz_sha256": NPZ_SHA,
              "verdict": verdict, "regions": per_region}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    for region, res in per_region.items():
        print(f"== {region}: sessions {len(res['sessions'])}, rats {len(res['rats'])}")
        for rat, agg in sorted(res["rats"].items()):
            print("  ", rat, {w: (round(agg[w]["D_correct"], 3), None if agg[w]["D_error"] is None else round(agg[w]["D_error"], 3),
                                  agg[w]["n_error"], round(agg[w]["kappa"], 3)) for w in WINDOWS})
        print("   R1", res["R1"], "\n   R3", res["R3"], "\n   R4", res["R4"])
    print(verdict)


if __name__ == "__main__":
    main()
