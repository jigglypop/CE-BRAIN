"""Reverse-proof of E2 (REVERSE_PROOF.md): positive Regge curvature of the column wiring metric.

python reverse_proof.py selftest   synthetic sphere / flat lattices only
python reverse_proof.py run        refuses to run unless REVERSE_PROOF.md lists this code hash
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import discover as d
import regge as rg

HERE = Path(__file__).resolve().parent
SET_A = ("L1", "L2", "L5", "Mi1", "Mi4", "Mi9")
SET_B = ("Tm1", "Tm2", "Tm9", "Tm20", "T1", "C3")
DIRECTIONS = ((1, 0), (0, 1), (1, 1))


class Lattice:
    """Undirected lattice edges with a direction label and per-vertex triangle edge triples."""

    def __init__(self, keys):
        self.keys, index = keys, {k: i for i, k in enumerate(keys)}
        self.edges, self.direction, eid = [], [], {}
        for k, i in index.items():
            for t, (dx, dy) in enumerate(DIRECTIONS):
                j = index.get((k[0] + dx, k[1] + dy))
                if j is not None:
                    eid[(i, j)] = eid[(j, i)] = len(self.edges)
                    self.edges.append((i, j))
                    self.direction.append(t)
        self.direction = np.array(self.direction)
        tri, vert = [], []
        for k, i in index.items():
            rows = []
            for (ax, ay), (bx, by) in rg.TRIANGLES:
                j, m = index.get((k[0] + ax, k[1] + ay)), index.get((k[0] + bx, k[1] + by))
                if j is None or m is None or (j, m) not in eid:
                    break
                rows.append((eid[(i, j)], eid[(i, m)], eid[(j, m)]))
            if len(rows) == 6:
                tri.append(rows)
                vert.append(k)
        self.triangles, self.interior = np.array(tri), vert

    def deficits(self, length):
        a, b, c = (length[self.triangles[..., n]] for n in range(3))
        angles = np.arccos(np.clip((a * a + b * b - c * c) / (2 * a * b), -1, 1))
        return 2 * np.pi - angles.sum(axis=1)


def implied_step_deg(deficits):
    return float(np.degrees(np.sqrt(max(deficits.mean(), 0) / (np.sqrt(3) / 2))))


def smoothed_positive_fraction(lattice, deficits):
    value = dict(zip(lattice.interior, deficits))
    sums = []
    for k in lattice.interior:
        near = [value[(k[0] + dx, k[1] + dy)] for dx in range(-2, 3) for dy in range(-2, 3)
                if max(abs(dx), abs(dy), abs(dx - dy)) <= 2 and (k[0] + dx, k[1] + dy) in value]
        if len(near) >= 15:
            sums.append(sum(near))
    return float(np.mean(np.array(sums) > 0)), len(sums)


def selftest():
    keys = [(x, y) for x in range(-12, 13) for y in range(-12, 13) if max(abs(x), abs(y), abs(x - y)) <= 12]
    lattice = Lattice(keys)
    step = np.radians(5.0)
    planar = {k: np.array([k[0] - 0.5 * k[1], np.sqrt(3) / 2 * k[1]]) * step for k in keys}

    def on_sphere(p):  # azimuthal equidistant chart onto the unit sphere
        r, phi = np.linalg.norm(p), np.arctan2(p[1], p[0])
        return np.array([np.sin(r) * np.cos(phi), np.sin(r) * np.sin(phi), np.cos(r)])
    sphere = {k: on_sphere(p) for k, p in planar.items()}
    geo = np.array([np.arccos(np.clip(sphere[keys[i]] @ sphere[keys[j]], -1, 1)) for i, j in lattice.edges])
    flat = np.array([np.linalg.norm(planar[keys[i]] - planar[keys[j]]) for i, j in lattice.edges])
    ds, df = lattice.deficits(geo), lattice.deficits(flat)
    cap = np.radians(5.0) * 11  # interior vertices reach hex radius 11
    report = {"interior": len(ds), "sphere_integrated": float(ds.sum()), "flat_integrated": float(df.sum()),
              "sphere_implied_step_deg": implied_step_deg(ds), "true_step_deg": 5.0,
              "sphere_smoothed_positive": smoothed_positive_fraction(lattice, ds)[0]}
    assert abs(report["flat_integrated"]) < 1e-9, report
    assert 0.8 < report["sphere_implied_step_deg"] / 5.0 < 1.25 and report["sphere_smoothed_positive"] > 0.95, report
    print(json.dumps(report, indent=1))


def eye(side, types, min_neurons):
    graph, cols = d.columns(side, types)
    keys = sorted(k for k, v in cols.items() if len(v) >= min_neurons)
    prof = d.profile_distance(graph, cols, keys)
    lattice = Lattice(keys)
    length = np.array([prof[i, j] for i, j in lattice.edges])
    return lattice, length


def run():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "REVERSE_PROOF.md").read_text(encoding="utf-8"):
        raise SystemExit(f"REVERSE_PROOF.md does not list this code hash {code_hash}")
    rng = np.random.default_rng(20260923)
    result = {"schema": "ce-visual-sphere-reverse-proof-v1", "code_sha256": code_hash, "RP1_shuffle_null": {},
              "RP2_disjoint_sets": {}, "RP3_spread": {}}
    for side in ("R", "L"):
        lattice, length = eye(side, d.MODULAR, 10)
        observed = lattice.deficits(length)
        null = []
        for _ in range(500):
            shuffled = length.copy()
            for t in range(3):
                idx = np.flatnonzero(lattice.direction == t)
                shuffled[idx] = rng.permutation(length[idx])
            null.append(lattice.deficits(shuffled).sum())
        q975 = float(np.quantile(null, 0.975))
        result["RP1_shuffle_null"][side] = {"observed_sr": float(observed.sum()), "null_mean_sr": float(np.mean(null)),
                                            "null_q975_sr": q975, "null_sd_sr": float(np.std(null)),
                                            "pass": float(observed.sum()) > q975}
        frac, count = smoothed_positive_fraction(lattice, observed)
        result["RP3_spread"][side] = {"smoothed_positive_fraction": frac, "patches": count, "pass": frac >= 0.6}
        for name, types in (("A", SET_A), ("B", SET_B)):
            lat, ln = eye(side, types, 5)
            dv = lat.deficits(ln)
            entry = {"interior": len(dv), "integrated_sr": float(dv.sum()), "implied_step_deg": implied_step_deg(dv)}
            entry["pass"] = entry["integrated_sr"] > 0 and 4.0 <= entry["implied_step_deg"] <= 6.0
            result["RP2_disjoint_sets"][f"{name}_{side}"] = entry
    ok = all(v["pass"] for group in ("RP1_shuffle_null", "RP2_disjoint_sets", "RP3_spread")
             for v in result[group].values())
    result["verdict"] = "E2_REVERSE_PROVED_STRUCTURE" if ok else "E2_NOT_REVERSE_PROVED"
    with (HERE / "results_reverse_proof.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps(result, indent=1, default=float))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("selftest", "run"))
    selftest() if parser.parse_args().stage == "selftest" else run()
