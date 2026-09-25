"""A1 step 55: the axis that switches the compass loop on and off from outside (sleep/wake gate), in three connectomes.
Literature anchor: Raccuglia et al. 2025 Nature (R5 sleep-need network and helicon (ExR1) synchronise at night; R5
hyperpolarises E-PG, helicon depolarises E-PG; helicon activation arouses). (CONTRACT.md)

S1  R5 (ER5) is an external input to the compass: externality e = R5->EPG / (R5->EPG + EPG->R5) >= 0.9 and
    R5->EPG >= 500 synapses.
S2  R5 and helicon are reciprocal: R5->helicon and helicon->R5 both >= 100 synapses.
S3  sign topology: modal transmitter of R5 and of helicon (GABA / glutamate = inhibitory, acetylcholine = excitatory);
    inhibitory R5 with excitatory helicon = excitation-inhibition pair (oscillator), mutual inhibition = flip-flop.
S4  co-innervation: across E-PG neurons, synapses from R5 and from helicon correlate (Pearson r > 0, permutation
    p < 0.05, 2000 permutations).
S5  upstream: among input classes from outside the ellipsoid-body ring circuit (excluding the population's own type,
    the compass/ring class and untyped partners), the largest input class of R5 is the bulb relay TuBu (the
    thalamus-like relay of the anterior visual pathway). Report the same for helicon, the ring-circuit fraction, and
    the brainstem-like class (ascending neurons) where present.
Report: externality of every type with >= 100 synapses onto E-PG.

python sleep_wake_gate.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hashes
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
R5, HEL = "ER5", "ExR1"
N_PERM = 2000
CLASSES = (("bulb_relay_TuBu", r"^TuBu"),
           ("clock", r"^(DN1|DN2|DN3|LNd|l-LNv|s-LNv|LNv|LPN|5th)"),
           ("ascending", r"^(AN|ascending)"),
           ("compass_ring", r"^(ER|ExR|EPG|PEN|PEG|Delta7|EL$|EL_|IbSpsP|LPsP|SpsP)"),
           ("fan_shaped_tangential", r"^FB"),
           ("other_central_complex", r"^(PFN|PFL|PFR|PFG|hDelta|vDelta|FC|FS|FR)"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


c46 = load("connectome_ring_class", LOOP / "step46_connectome_ring_class/connectome_ring_class.py")
INHIB, EXCIT = {"gaba", "glutamate"}, {"acetylcholine"}


def cls(t):
    for name, pat in CLASSES:
        if re.match(pat, t):
            return name
    return "other"


def analyse(A, ty, nt):
    A = A.tocsr()
    AT = A.T.tocsr()
    idx = {t: np.flatnonzero(ty == t) for t in (R5, HEL, "EPG")}
    epg = idx["EPG"]
    out_epg = np.asarray(A[epg, :].sum(axis=0)).ravel()
    in_epg = np.asarray(AT[epg, :].sum(axis=0)).ravel()
    ext = {}
    for t in sorted(set(ty[np.flatnonzero(in_epg > 0)]) - {"", "EPG"}):
        m = np.flatnonzero(ty == t)
        x2e, e2x = float(in_epg[m].sum()), float(out_epg[m].sum())
        if x2e >= 100:
            ext[t] = {"X_to_EPG": x2e, "EPG_to_X": e2x, "externality": x2e / (x2e + e2x), "class": cls(t)}

    def syn(a, b):
        return float(A[idx[a], :][:, idx[b]].sum())

    res = {"n": {k: int(v.size) for k, v in idx.items()}, "externality": ext}
    r5 = ext.get(R5, {"X_to_EPG": 0.0, "externality": 0.0})
    res["S1_R5_external"] = bool(r5["externality"] >= 0.9 and r5["X_to_EPG"] >= 500)
    pair = {"R5_to_helicon": syn(R5, HEL), "helicon_to_R5": syn(HEL, R5), "R5_to_R5": syn(R5, R5), "helicon_to_helicon": syn(HEL, HEL)}
    res["pair"] = pair
    res["S2_reciprocal"] = bool(pair["R5_to_helicon"] >= 100 and pair["helicon_to_R5"] >= 100)
    nts = {k: Counter(nt[v] for v in idx[k]).most_common() for k in (R5, HEL)}
    res["transmitters"] = nts
    top = {k: v[0][0] if v else "" for k, v in nts.items()}
    tied = {k: bool(len(v) > 1 and v[0][1] == v[1][1]) for k, v in nts.items()}
    if tied[R5] or tied[HEL]:
        topo = "undetermined_tie"
    elif top[R5] in INHIB and top[HEL] in EXCIT:
        topo = "excitation_inhibition_pair"
    elif top[R5] in INHIB and top[HEL] in INHIB:
        topo = "mutual_inhibition_flip_flop"
    elif top[R5] in EXCIT and top[HEL] in EXCIT:
        topo = "mutual_excitation"
    else:
        topo = f"other({top[R5]},{top[HEL]})"
    res["S3_topology"] = topo
    a = np.asarray(A[idx[R5], :][:, epg].sum(axis=0)).ravel()
    b = np.asarray(A[idx[HEL], :][:, epg].sum(axis=0)).ravel()
    r = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else float("nan")
    rng = np.random.default_rng(55)
    null = np.array([np.corrcoef(a, rng.permutation(b))[0, 1] for _ in range(N_PERM)]) if np.isfinite(r) else np.array([])
    p = float((1 + np.sum(null >= r)) / (1 + N_PERM)) if null.size else float("nan")
    res["coinnervation"] = {"r": r, "p": p, "frac_EPG_with_both": float(np.mean((a > 0) & (b > 0)))}
    res["S4_coinnervation"] = bool(np.isfinite(r) and r > 0 and p < 0.05)
    up = {}
    for k in (R5, HEL):
        w = np.asarray(AT[idx[k], :].sum(axis=0)).ravel()           # synapses from every neuron onto the population
        by_type, by_cls = defaultdict(float), defaultdict(float)
        for v in np.flatnonzero(w > 0):
            t = ty[v] or "(untyped)"
            by_type[t] += w[v]
            by_cls["self" if ty[v] == k else (cls(t) if ty[v] else "untyped")] += w[v]
        tot = sum(by_cls.values())
        up[k] = {"total_input": tot, "class_fraction": {c: v / tot for c, v in sorted(by_cls.items(), key=lambda x: -x[1])},
                 "top_types": [(t, v) for t, v in sorted(by_type.items(), key=lambda x: -x[1])[:10]]}
    res["upstream"] = up
    outside = {c: v for c, v in up[R5]["class_fraction"].items() if c not in ("untyped", "self", "compass_ring")}
    res["S5_R5_top_class_TuBu"] = bool(outside and max(outside, key=outside.get) == "bulb_relay_TuBu")
    return res


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step46_connectome_ring_class/connectome_ring_class.py", LOOP / "step41_few_neuron_attractor/tl_ring.py",
            LOOP / "step41_few_neuron_attractor/few_neuron_ring.py", LOOP / "step42_kim_support_ring/kim_support_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    res = {}
    for name, (A, ty, inst, sd, nt) in c46.datasets().items():
        res[name] = analyse(A, ty, nt)
        d = res[name]
        print("==", name, "n", d["n"], "S1", d["S1_R5_external"], "S2", d["S2_reciprocal"], json.dumps(d["pair"]), "S3", d["S3_topology"],
              json.dumps(d["transmitters"]), "S4", d["S4_coinnervation"], json.dumps(d["coinnervation"]), "S5", d["S5_R5_top_class_TuBu"], flush=True)
        for k in (R5, HEL):
            print("   upstream", k, {c: round(v, 3) for c, v in d["upstream"][k]["class_fraction"].items()}, d["upstream"][k]["top_types"][:6], flush=True)
    crit = {s: sum(res[k][s] for k in res) for s in ("S1_R5_external", "S2_reciprocal", "S4_coinnervation", "S5_R5_top_class_TuBu")}
    ok = all(v >= 2 for v in crit.values()) and res["malecns"]["S3_topology"] == "excitation_inhibition_pair"
    result = {"schema": "ce-a1-step55-sleep-wake-gate", "hashes": hashes, "criteria_counts": crit,
              "verdict": "GATE_AXIS_STRUCTURE_SUPPORTED" if ok else "GATE_AXIS_STRUCTURE_NOT_SUPPORTED", "datasets": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], crit, "malecns topology", res["malecns"]["S3_topology"])


if __name__ == "__main__":
    main()
