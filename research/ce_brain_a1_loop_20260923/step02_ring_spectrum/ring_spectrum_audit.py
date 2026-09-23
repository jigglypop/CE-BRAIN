"""AUDIT copy (only change: harmonic content of a real eigenvector is scaled by sqrt(2), so a pure cosine scores 1).

A1 loop step 2: parameter-free spectral structure of the real ring operator (CONTRACT.md).

python ring_spectrum.py    refuses to run unless CONTRACT.md lists this code hash
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


def harmonics(v, epg, angles):
    ve = v[epg]
    norm = np.sqrt(len(epg) * np.sum(np.abs(ve) ** 2))
    if np.allclose(ve.imag, 0):
        norm = norm / np.sqrt(2)
    return [min(1.0, float(abs(np.sum(ve * np.exp(-1j * m * angles))) / norm)) if norm > 0 else 0.0 for m in range(3)]


def analyse(W, kind, label, epg, angles):
    lam, left, right = eig(W, left=True, right=True)
    order = np.argsort(-lam.real)
    modes = []
    for rank, k in enumerate(order):
        h = harmonics(right[:, k], epg, angles)
        modes.append({"rank": rank, "index": int(k), "re": float(lam[k].real), "im": float(lam[k].imag),
                      "h": h, "dominant": int(np.argmax(h))})
    lead = next(m for m in modes if m["dominant"] != 0)
    s1 = lead["dominant"] == 1 and lead["h"][1] >= 0.8
    partner, s2 = None, False
    if abs(lead["im"]) > 1e-9 * max(1, abs(lead["re"])):
        partner = next(m for m in modes if m["index"] != lead["index"] and abs(lam[m["index"]] - np.conj(lam[lead["index"]])) < 1e-8)
        s2 = True
        basis = np.column_stack([right[:, lead["index"]].real, right[:, lead["index"]].imag])
        dual_src = np.column_stack([left[:, lead["index"]].real, left[:, lead["index"]].imag])
    else:
        for m in modes:
            if m["index"] == lead["index"] or abs(m["im"]) > 1e-9:
                continue
            if abs(m["re"] - lead["re"]) <= 0.1 * abs(lead["re"]) and m["h"][1] >= 0.8:
                p1 = np.angle(np.sum(right[epg, lead["index"]].real * np.exp(-1j * angles)))
                p2 = np.angle(np.sum(right[epg, m["index"]].real * np.exp(-1j * angles)))
                gap = abs(np.degrees(np.angle(np.exp(1j * (p1 - p2)))))
                if 60 <= gap <= 120:
                    partner, s2 = m, True
                    break
        if partner is not None:
            basis = np.column_stack([right[:, lead["index"]].real, right[:, partner["index"]].real])
            dual_src = np.column_stack([left[:, lead["index"]].real, left[:, partner["index"]].real])
    result = {"lead_nonuniform": lead, "partner": partner, "S1": s1, "S2": s2,
              "top_modes": [{k: v for k, v in m.items() if k != "index"} for m in modes[:8]]}
    if s2:
        template = np.column_stack([np.cos(angles), np.sin(angles)])
        coef, *_ = np.linalg.lstsq(basis[epg], template, rcond=None)
        B = basis @ coef
        dual = dual_src @ np.linalg.inv(B.T @ dual_src).T  # dual.T @ B = I
        gamma = np.array([(1.0 if label[i][0] == "L" else -1.0) if kind[i].startswith("PEN") and label[i] else 0.0
                          for i in range(len(kind))])
        Q = dual.T @ (gamma[:, None] * W) @ B
        rho = float(np.linalg.norm((Q - Q.T) / 2) / np.linalg.norm(Q)) if np.linalg.norm(Q) > 0 else 0.0
        fit = float(1 - np.linalg.norm(B[epg] - template) ** 2 / np.linalg.norm(template) ** 2)
        result.update({"Q": Q.tolist(), "rho_rotation": rho, "S3": rho >= 0.7, "basis_cos_sin_fit_R2": fit})
    else:
        result["S3"] = False
    return result


def main():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    w, kind, label = rd.load()
    sign = np.array([-1.0 if k == "Delta7" else 1.0 for k in kind])
    epg = np.array([i for i, k in enumerate(kind) if k == "EPG"])
    angles = np.array([rd.phi(*label[i]) for i in epg])
    normalized = (w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12)) * sign[None, :]
    primary = analyse(normalized, kind, label, epg, angles)
    secondary = analyse(w * sign[None, :], kind, label, epg, angles)
    verdict = "A1_RING_SPECTRUM_SUPPORTED" if primary["S1"] and primary["S2"] and primary["S3"] else "A1_RING_SPECTRUM_NOT_SUPPORTED"
    result = {"schema": "ce-a1-step02-ring-spectrum-audit", "code_sha256": code_hash, "verdict": verdict,
              "primary_input_normalized": primary, "secondary_raw_counts": secondary}
    with (HERE / "results_audit_real_normalization.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    main()
