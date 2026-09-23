"""Does fixed-neuron wiring fold the protocerebral-bridge line into a heading circle? (CONTRACT.md)

python ring_fold.py selftest   synthetic ring and line graphs only
python ring_fold.py run        MaleCNS; refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import numpy as np
from scipy import sparse
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MALECNS = ROOT / "verify/MaleCNS"
EPG = re.compile(r"^EPG\(PB08\)_([LR])([1-8])$")
PEN = re.compile(r"^PEN_[ab]\(PB06[ab]\)_([LR])([1-9])$")


def unit(v):
    norm = np.linalg.norm(v, axis=1, keepdims=True)
    return np.divide(v, norm, out=np.zeros_like(v), where=norm > 0)


def effective_distance(adjacency, groups):
    """Angle between concatenated unit input/output profiles of neuron groups (n x G indicator)."""
    out = (groups.T @ adjacency).toarray()
    inp = (adjacency @ groups).T.toarray()
    profile = np.hstack([unit(out), unit(inp)]) / np.sqrt(2)
    return np.arccos(np.clip(profile @ profile.T, -1, 1))


def mds_angles(distance):
    n = len(distance)
    centre = np.eye(n) - 1 / n
    b = -0.5 * centre @ (distance ** 2) @ centre
    values, vectors = np.linalg.eigh(b)
    xy = vectors[:, -2:] * np.sqrt(np.maximum(values[-2:], 0))
    xy -= xy.mean(axis=0)
    radius = np.linalg.norm(xy, axis=1)
    theta = np.arctan2(xy[:, 1], xy[:, 0])
    ordered = np.sort(np.mod(theta, 2 * np.pi))
    gaps = np.diff(np.r_[ordered, ordered[0] + 2 * np.pi])
    return theta, float(radius.std() / radius.mean()), float(np.degrees(2 * np.pi - gaps.max()))


def circ_dist(a, b):
    return np.abs(np.angle(np.exp(1j * (a - b))))


def circ_mean(angles, weights):
    return np.angle(np.sum(weights * np.exp(1j * angles)))


def fold_tests(distance, labels, theta):
    left = [i for i, (s, _) in enumerate(labels) if s == "L"]
    right = [i for i, (s, _) in enumerate(labels) if s == "R"]
    cross = distance[np.ix_(left, right)]
    match = cross.argmin(axis=1)
    bijective = len(set(match.tolist())) == len(right)
    matched = cross[np.arange(len(left)), match]
    mask = np.ones_like(cross, dtype=bool)
    mask[np.arange(len(left)), match] = False
    li = np.array([labels[i][1] for i in left])
    rj = np.array([labels[right[m]][1] for m in match])
    diff_rule, sum_rule = np.unique((rj - li) % 8), np.unique((rj + li) % 8)
    p1 = {"bijective": bijective, "max_matched": float(matched.max()),
          "nonmatched_q05": float(np.quantile(cross[mask], 0.05)),
          "pairs": [f"L{a}-R{b}" for a, b in zip(li, rj)],
          "constant_difference_rule": diff_rule.tolist() if len(diff_rule) == 1 else None,
          "constant_sum_rule": sum_rule.tolist() if len(sum_rule) == 1 else None}
    p1["pass"] = bijective and p1["max_matched"] < p1["nonmatched_q05"] and \
        (p1["constant_difference_rule"] is not None or p1["constant_sum_rule"] is not None)
    iu = np.triu_indices(len(labels), 1)
    u = np.array([(-1 if s == "L" else 1) * k for s, k in labels], dtype=float)
    rho_circle = spearmanr(distance[iu], circ_dist(theta[:, None], theta[None, :])[iu]).statistic
    rho_line = spearmanr(distance[iu], np.abs(u[:, None] - u[None, :])[iu]).statistic
    heading = np.array([np.angle(np.exp(1j * theta[left[k]]) + np.exp(1j * theta[right[m]]))
                        for k, m in enumerate(match)])
    ordered = np.sort(np.mod(heading, 2 * np.pi))
    gaps = np.degrees(np.diff(np.r_[ordered, ordered[0] + 2 * np.pi]))
    p3 = {"gaps_deg": gaps.tolist(), "mean_gap": float(gaps.mean()), "gap_cv": float(gaps.std() / gaps.mean())}
    p3["pass"] = abs(p3["mean_gap"] - 45) <= 10 and p3["gap_cv"] < 0.25
    return p1, {"rho_circle": float(rho_circle), "rho_line": float(rho_line)}, p3


def shift(adjacency, sources, relay, targets, theta_sources, theta_targets):
    """Per relay group: weighted circular mean of input source angles and output target angles."""
    into = (sources.T @ adjacency @ relay).toarray()
    out = (relay.T @ adjacency @ targets).toarray()
    result = []
    for r in range(relay.shape[1]):
        if into[:, r].sum() == 0 or out[r].sum() == 0:
            result.append(None)
            continue
        a_in, a_out = circ_mean(theta_sources, into[:, r]), circ_mean(theta_targets, out[r])
        result.append(float(np.degrees(np.angle(np.exp(1j * (a_out - a_in))))))
    return result


def indicator(n, members, count):
    rows = [i for i, g in members]
    cols = [g for i, g in members]
    return sparse.csr_array((np.ones(len(rows)), (rows, cols)), shape=(n, count))


def selftest():
    rng = np.random.default_rng(3)
    n_per, labels = 3, [("L", k) for k in range(8, 0, -1)] + [("R", k) for k in range(1, 9)]
    heading = {("L", k): (k - 1) % 8 for k in range(1, 9)} | {("R", k): (8 - k) % 8 for k in range(1, 9)}
    members, n_nodes = [], 16 * n_per + 64
    for g, lab in enumerate(labels):
        members += [(g * n_per + r, g) for r in range(n_per)]
    rows, cols, vals = [], [], []
    for i, g in members:
        h = heading[labels[g]]
        for t in range(8):  # partners arranged on a ring of 8 heading targets
            w = np.exp(np.cos(2 * np.pi * (t - h) / 8) * 2) + rng.uniform(0, .05)
            rows += [i, 16 * n_per + t]
            cols += [16 * n_per + t, i]
            vals += [w, w]
    adjacency = sparse.csr_array((vals, (rows, cols)), shape=(n_nodes, n_nodes))
    distance = effective_distance(adjacency, indicator(n_nodes, members, 16))
    theta, radius_cv, span = mds_angles(distance)
    p1, p2, p3 = fold_tests(distance, labels, theta)
    report = {"p1": p1, "p2": p2, "p3": p3, "radius_cv": radius_cv, "span": span}
    assert p1["pass"] and p1["constant_sum_rule"] is not None and p2["rho_circle"] > 0.9 and p3["pass"], report
    assert p2["rho_line"] < p2["rho_circle"] and radius_cv < 0.2 and span > 300, report
    # negative control: partners follow the anatomical line, nothing is identified
    rows, cols, vals = [], [], []
    for i, g in members:
        for t in range(16):
            w = np.exp(-((t - g) / 2.0) ** 2) + rng.uniform(0, .05)
            rows += [i, 16 * n_per + t]
            cols += [16 * n_per + t, i]
            vals += [w, w]
    line = sparse.csr_array((vals, (rows, cols)), shape=(n_nodes, n_nodes))
    line_distance = effective_distance(line, indicator(n_nodes, members, 16))
    line_theta, _, _ = mds_angles(line_distance)
    q1, q2, _ = fold_tests(line_distance, labels, line_theta)
    report["line_control"] = {"p1_pass": q1["pass"], "rho_line": q2["rho_line"]}
    assert not q1["pass"] and q2["rho_line"] > 0.9, report
    print(json.dumps(report, indent=1, default=str))


def run():
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    spec = importlib.util.spec_from_file_location("malecns_neuron_graph", MALECNS / "neuron_graph.py")
    graph_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(graph_module)
    graph = graph_module.load(MALECNS / "neuron_graph_result.json")
    ids, n = graph["node_ids"], len(graph["node_ids"])
    adjacency = sparse.csr_array((graph["weight"].astype(float), graph["indices"], graph["indptr"]), shape=(n, n))
    with pa.memory_map(str(graph_module.SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    body, instance = table["bodyId"].to_numpy(), table["instance"].to_pylist()
    position, found = graph_module.locate(body, ids)
    labels = [("L", k) for k in range(8, 0, -1)] + [("R", k) for k in range(1, 9)]
    epg, pen_groups, pen_members = [], {}, []
    for i, name in enumerate(instance):
        if not found[i] or name is None:
            continue
        m = EPG.match(name)
        if m:
            epg.append((int(position[i]), labels.index((m.group(1), int(m.group(2))))))
        m = PEN.match(name)
        if m:
            key = (m.group(1), int(m.group(2)))
            pen_members.append((int(position[i]), pen_groups.setdefault(key, len(pen_groups))))
    groups = indicator(n, epg, 16)
    distance = effective_distance(adjacency, groups)
    theta, radius_cv, span = mds_angles(distance)
    p1, p2, p3 = fold_tests(distance, labels, theta)
    p2.update({"radius_cv": radius_cv, "angular_span_deg": span})
    p2["pass"] = radius_cv < 0.2 and span > 300 and p2["rho_circle"] > 0.8 and p2["rho_circle"] > p2["rho_line"]
    pens = indicator(n, pen_members, len(pen_groups))
    pen_shift = shift(adjacency, groups, pens, groups, theta, theta)
    sides = {s: [v for (side, _), g in pen_groups.items() if side == s and (v := pen_shift[g]) is not None]
             for s in "LR"}
    mean_side = {s: float(np.degrees(circ_mean(np.radians(v), np.ones(len(v))))) for s, v in sides.items()}
    direct = (groups.T @ adjacency @ groups).toarray()
    direct_shift = [float(np.degrees(np.angle(np.exp(1j * (circ_mean(theta, direct[g]) - theta[g])))))
                    for g in range(16) if direct[g].sum() > 0]
    direct_mean = float(np.degrees(circ_mean(np.radians(direct_shift), np.ones(len(direct_shift)))))
    p4 = {"pen_shift_by_group": {f"{s}{k}": pen_shift[g] for (s, k), g in sorted(pen_groups.items())},
          "mean_shift_L": mean_side["L"], "mean_shift_R": mean_side["R"], "epg_direct_mean_shift": direct_mean,
          "epg_direct_shift_by_group": direct_shift}
    p4["pass"] = np.sign(mean_side["L"]) != np.sign(mean_side["R"]) and \
        all(22.5 <= abs(mean_side[s]) <= 67.5 for s in "LR") and abs(direct_mean) < 22.5
    verdict = "SUPPORTED_STRUCTURE" if all(p["pass"] for p in (p1, p2, p3, p4)) else "NOT_SUPPORTED"
    result = {"schema": "ce-cx-ring-fold-v1", "verdict": verdict, "P1_fold": p1, "P2_circle_not_line": p2,
              "P3_uniform_metric": p3, "P4_direction_shift": p4,
              "labels": [f"{s}{k}" for s, k in labels], "theta_deg": np.degrees(theta).tolist(),
              "distance": distance.tolist(), "epg_neurons": len(epg), "pen_neurons": len(pen_members),
              "code_sha256": code_hash}
    with (HERE / "results_v1.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, default=float)
    print(json.dumps({k: v for k, v in result.items() if k not in ("distance",)}, indent=1, default=float))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("selftest", "run"))
    selftest() if parser.parse_args().stage == "selftest" else run()
