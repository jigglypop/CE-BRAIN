"""A1 step 38: operating point -- with the visual teacher shaped like the fly's bump (literature FWHM, unsaturated),
does the same learning rule (Vafidis et al. 2022) give a ring that also obeys Kim 2017's narrow-input selection, while
keeping no wells, one-of-two selection and linear integration at the speeds flies track? (CONTRACT.md)

Network: the authors' learned network trained further with the authors' rule under the calibrated teacher
(calibrate_teacher.py; the chosen teacher and the network file hash are fixed in CONTRACT.md).
Tests: the frozen step 37 battery (C1, S1, S2, S3) with the calibrated teacher as the light cue; rotation criterion at
fly turning speeds (Seelig & Jayaraman 2015: very slow turns are not tracked), 30 deg/s reported.

python operating_point.py    refuses to run unless CONTRACT.md lists this code hash and the network hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s37 = load("learned_selection", LOOP / "step37_learned_ring_selection/learned_selection.py")
TEACHER = {"M": None, "sigma": None}          # fixed from the calibration rule in CONTRACT.md
NET = HERE / "calibrated_network.npz"
SPEEDS_R1, SPEEDS_SLOW = (-180.0, -90.0, -60.0, 60.0, 90.0, 180.0), (-30.0, 30.0)


def rotation(w, speeds):
    every = int(0.05 / s37.P["dt"])
    out = {}
    for om in speeds:
        f, tr = s37.run(w, [(s37.T_LIGHT, s37.light(0.0), 0.0), (s37.T_ROT, s37.DARK, om)], every)
        ph = np.degrees(np.unwrap(np.radians(tr[int(s37.T_LIGHT / 0.05):])))
        t = np.arange(ph.size) * 0.05
        m = t >= s37.FIT_FROM
        coef = np.polyfit(t[m], ph[m], 1)
        pred = np.polyval(coef, t[m])
        r2 = 1 - np.sum((ph[m] - pred) ** 2) / max(np.sum((ph[m] - ph[m].mean()) ** 2), 1e-12)
        out[str(int(om))] = {"gain": float(coef[0] / om), "r2": float(r2), "bump_end": bool(s37.bump_ok(f))}
    return out


def analyse(w):
    r = s37.analyse(w, parts=("C", "S1", "S2", "S3"))
    rot, slow = rotation(w, SPEEDS_R1), rotation(w, SPEEDS_SLOW)
    r["rotation"] = {"speeds": rot, "report_slow": slow,
                     "R1": bool(all(0.8 <= o["gain"] <= 1.2 and o["r2"] >= 0.99 and o["bump_end"] for o in rot.values()))}
    return r


def summary(r):
    return {"dark_bump": r["dark_bump"], "C1": [r["continuity"][k] for k in ("retention", "median_abs_err", "max_abs_err", "C1")],
            "S1": [r["two_cue"]["n_ok"], r["two_cue"]["S1"]], "S2": [r["jump"]["thresholds"], r["jump"]["ratio_180_over_90"], r["jump"]["S2"]],
            "S3": [[round(1e3 * v, 1) for v in r["suppression"]["ref_activity"]], r["suppression"]["S3"]],
            "R1": [{k: (round(o["gain"], 3), round(o["r2"], 4)) for k, o in {**r["rotation"]["speeds"], **r["rotation"]["report_slow"]}.items()}, r["rotation"]["R1"]]}


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in contract:
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    net_hash = hashlib.sha256(NET.read_bytes()).hexdigest()
    if net_hash not in contract:
        raise SystemExit(f"CONTRACT.md does not list the network hash {net_hash}")
    s37.P.update(TEACHER)
    w = np.load(NET)["w"]
    res = {}
    for k, wk in (("calibrated", w), ("control_homogeneous", s37.homogeneous(w))):
        res[k] = analyse(wk)
        print("==", k, json.dumps(summary(res[k]), default=float), flush=True)
    L = res["calibrated"]
    crit = {"C1": L["continuity"]["C1"], "S1": L["two_cue"]["S1"], "S2": L["jump"]["S2"], "R1": L["rotation"]["R1"],
            "S3_secondary": L["suppression"]["S3"]}
    ok = crit["C1"] and crit["S1"] and crit["S2"] and crit["R1"]
    result = {"schema": "ce-a1-step38-operating-point", "code_sha256": code_hash, "network_sha256": net_hash, "teacher": TEACHER,
              "verdict": "LITERATURE_OPERATING_POINT_SELECTS_PERSISTS_ROTATES" if ok else "LITERATURE_OPERATING_POINT_DOES_NOT_SATISFY_ALL",
              "criteria": crit, "networks": res}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", result["verdict"], crit)


if __name__ == "__main__":
    main()
