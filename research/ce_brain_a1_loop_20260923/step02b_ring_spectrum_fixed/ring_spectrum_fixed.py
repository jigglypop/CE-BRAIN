"""A1 loop step 2b: corrected spectral test of the ring memory attractor (CONTRACT.md).

python ring_spectrum_fixed.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eig

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ring_dynamics", HERE.parent / "step01_ring_dynamics/ring_dynamics.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)


def power(v, angles):
    n, total = len(v), np.sum(np.abs(v) ** 2)
    if total == 0:
        return [0.0, 0.0, 0.0]
    p0 = abs(np.sum(v)) ** 2 / (n * total)
    pm = [(abs(np.sum(v * np.exp(-1j * m * angles))) ** 2 + abs(np.sum(v * np.exp(1j * m * angles))) ** 2) / (n * total)
          for m in (1, 2)]
    return [float(p0), float(pm[0]), float(pm[1])]


def analyse(W, kind, label, epg, angles):
    lam, left, right = eig(W, left=True, right=True)
    order = np.argsort(-lam.real)
    modes = []
    for rank, k in enumerate(order):
        p = power(right[epg, k], angles)
        modes.append({"rank": rank, "k": int(k), "re": float(lam[k].real), "im": float(lam[k].imag),
                      "P": p, "dominant": int(np.argmax(p))})
    uniform = next(m for m in modes if m["dominant"] == 0)
    lead = next(m for m in modes if m["dominant"] != 0)
    s1 = lead["dominant"] == 1 and lead["P"][1] >= 0.8
    template = np.column_stack([np.cos(angles), np.sin(angles)])
    out = {"uniform": {k: v for k, v in uniform.items() if k != "k"}, "lead": {k: v for k, v in lead.items() if k != "k"},
           "S1": s1, "top_modes": [{k: v for k, v in m.items() if k != "k"} for m in modes[:8]]}
    if abs(lead["im"]) > 1e-9 * max(1.0, abs(lead["re"])):
        vec = right[:, lead["k"]]
        span, dual_src = np.column_stack([vec.real, vec.imag]), np.column_stack([left[:, lead["k"]].real, left[:, lead["k"]].imag])
        partner = "complex_conjugate"
    else:
        partner = next((m for m in modes if m["k"] != lead["k"] and abs(m["im"]) <= 1e-9 and
                        abs(m["re"] - lead["re"]) <= 0.1 * abs(lead["re"]) and m["P"][1] >= 0.8), None)
        if partner is None:
            out.update({"S2": False, "S3": False})
            return out
        span = np.column_stack([right[:, lead["k"]].real, right[:, partner["k"]].real])
        dual_src = np.column_stack([left[:, lead["k"]].real, left[:, partner["k"]].real])
        partner = {k: v for k, v in partner.items() if k != "k"}
    coef, *_ = np.linalg.lstsq(span[epg], template, rcond=None)
    B = span @ coef
    r2 = float(1 - np.linalg.norm(B[epg] - template) ** 2 / np.linalg.norm(template - template.mean(axis=0)) ** 2)
    dual = dual_src @ np.linalg.inv(B.T @ dual_src)
    identity_error = float(np.abs(dual.T @ B - np.eye(2)).max())
    gamma = np.array([(1.0 if label[i][0] == "L" else -1.0) if kind[i].startswith("PEN") and label[i] else 0.0
                      for i in range(len(kind))])
    Q = dual.T @ (gamma[:, None] * W) @ B
    rho = float(np.linalg.norm((Q - Q.T) / 2) / np.linalg.norm(Q)) if np.linalg.norm(Q) > 0 else 0.0
    lam1 = lead["re"]
    second = next((m for m in modes if m["dominant"] == 2), None)
    out.update({"partner": partner, "span_cos_sin_R2": r2, "S2": r2 >= 0.8, "dual_identity_max_error": identity_error,
                "Q": Q.tolist(), "rho_rotation": rho, "S3": rho >= 0.7,
                "report": {"uniform_over_lead": uniform["re"] / lam1,
                           "second_harmonic_recovery_rate_per_tau": (1 - second["re"] / lam1) if second else None,
                           "rotation_rate_per_unit_u_rad_per_tau": float((Q[1, 0] - Q[0, 1]) / 2 / lam1)}})
    return out


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    w, kind, label = rd.load()
    sign = np.array([-1.0 if k == "Delta7" else 1.0 for k in kind])
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    angles = np.array([rd.phi(*label[i]) for i in epg])
    primary = analyse((w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :], kind, label, epg, angles)
    secondary = analyse(w * sign[None, :], kind, label, epg, angles)
    ok = primary["S1"] and primary["S2"] and primary["S3"]
    result = {"schema": "ce-a1-step02b-ring-spectrum-fixed", "code_sha256": code_hash,
              "verdict": "A1_RING_MEMORY_ATTRACTOR_SUPPORTED" if ok else "A1_RING_MEMORY_ATTRACTOR_NOT_SUPPORTED",
              "primary_input_normalized": primary, "secondary_raw_counts": secondary}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
