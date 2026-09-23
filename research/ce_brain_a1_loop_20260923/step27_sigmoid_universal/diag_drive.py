"""Post-hoc diagnostic for step 27 U3 (does NOT change the frozen verdict): at the common operating point
(beta=-1, g=1.5), does the bump move for larger PEN drive, and is the velocity linear/antisymmetric?"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("su", HERE / "sigmoid_universal.py")
su = importlib.util.module_from_spec(spec)
spec.loader.exec_module(su)
U = (-1.0, -0.5, -0.25, 0.25, 0.5, 1.0)


def main():
    h22 = su.load("hemibrain_third", su.LOOP / "step22_hemibrain_third/hemibrain_third.py")
    nets = {}
    A, ty, sd, nt = su.gi.malecns(); nets["malecns"] = su.raw_network(A, ty, su.s25.malecns()[2], sd, nt)
    A, ty, sd, nt = su.gi.flywire(); nets["flywire"] = su.raw_network(A, ty, None, sd, nt)
    A, ty, inst, sd, nt = h22.hemibrain(); nets["hemibrain"] = su.raw_network(A, ty, inst, sd, nt)
    out = {}
    for name, (W, epg, ang, basis, gamma) in nets.items():
        lam1 = su.lambda1(W, epg, ang)
        w0 = 1.5 / (lam1 * su.sig(-1.0) * (1 - su.sig(-1.0)))
        rows = []
        for u in U:
            r = su.run_one(W, epg, ang, -1.0, w0, gamma, u)
            rows.append({"u": u, "fwhm": r["fwhm"], "deg_per_100tau": float(np.degrees(r["velocity"]) * 100), "persistent": r["persistent"]})
        out[name] = rows
        print(name, [(x["u"], x["fwhm"], round(x["deg_per_100tau"], 1), x["persistent"]) for x in rows])
    (HERE / "diag_drive.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
