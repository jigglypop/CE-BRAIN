"""BA-SRM13 phase-1 neural input re-audit (behavior sealed).

Contract: paper/검증_원장/BA_SRM13_실데이터_입력재감사_계약.md (LOCKED_PRE_RESULT).
Single structural change versus the frozen BA-SRM7 audit: anchor eligibility is
the SRM12-confirmed physical-time causal covariance validity (POWER_theta2_p1p5
gamma2 radial_huber_c3, n_eff>=8) on robust-standardized (median/1.4826*MAD,
clip +-4) causal I, instead of the strict W-window gap rule. Everything else —
archives, splits, cuts, exclusions, photobleach/regression/causal pipeline,
60/20/20 + EMBARGO/GUARD geometry, eigengap rule, >=100 anchors per split,
staged behavior sealing — is carried verbatim. Behavior values are never read.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SRM7ART = REPO / "_workspace/ce/brain-adaptive-effective-dimension-validation-v2-20260823/artifacts"
SRM8 = REPO / "_workspace/ce/brain-physical-time-effective-dimension-funnel-20260823/artifacts"
OUT_LOCK = Path.cwd() / "ba-srm13-neural-input-lock.json"
OUT_AUDIT = Path.cwd() / "ba-srm13-input-audit.json"

EXPECTED_SRM7_AUDIT_SHA = "a5bd9961c867d8f4707a41649cc865558f7570626bf7feb6186911b41f40b27"
CANDIDATE_ID = "POWER_theta2_p1p5__gamma2__radial_huber_c3"
CLIP = 4.0
MADC = 1.4826

_spec = importlib.util.spec_from_file_location("srm7_input_audit", SRM7ART / "input_audit.py")
A7 = importlib.util.module_from_spec(_spec)
sys.modules["srm7_input_audit"] = A7
_spec.loader.exec_module(A7)

sys.path.insert(0, str(SRM8))
from funnel_core_v2 import causal_q, manifest  # noqa: E402

W, H, GUARD, EMBARGO, GAP_FACTOR = A7.W, A7.H, A7.GUARD, A7.EMBARGO, A7.GAP_FACTOR
loadmat = A7.loadmat if hasattr(A7, "loadmat") else None
from scipy.io import loadmat  # noqa: E402


def candidate():
    man, man_sha = manifest()
    rows = [c for c in man["candidates"] if c["id"] == CANDIDATE_ID]
    if len(rows) != 1:
        raise RuntimeError("carried candidate not found in frozen manifest")
    return rows[0], man_sha


def robust_z(ci: np.ndarray, prefix_end: int):
    """Confirmed robust standardization on causal I; returns z0 (0-filled), mask,
    per-unit reliability D, and indices of units excluded for degenerate MAD."""
    mask = np.isfinite(ci)
    n = ci.shape[0]
    z0 = np.zeros_like(ci, dtype=np.float64)
    d = np.empty(n, dtype=np.float64)
    excluded = []
    for i in range(n):
        obs = mask[i, :prefix_end]
        prefix = ci[i, :prefix_end][obs]
        center = float(np.median(prefix))
        scale = MADC * float(np.median(np.abs(prefix - center)))
        if not np.isfinite(scale) or scale <= 1e-12:
            excluded.append(i)
            continue
        z = np.clip((ci[i] - center) / scale, -CLIP, CLIP)
        z0[i] = np.where(mask[i], z, 0.0)
        d[i] = np.sqrt(float(np.mean(obs)))
    keep = np.ones(n, dtype=bool)
    keep[excluded] = False
    return z0[keep], mask[keep].astype(np.uint8), d[keep], excluded


def split_anchors_v2(cand, clock, raw_index, rid, usable, z0, mask, d, processed):
    """Role geometry, exclusions, target-side gap rule, and eigengap are carried
    from BA-SRM7; history-side validity is causal_q covariance validity."""
    pos = np.diff(clock)
    pos = pos[np.isfinite(pos) & (pos > 0)]
    gap = GAP_FACTOR * np.median(pos) if pos.size else np.nan
    e1, e2 = int(0.6 * usable), int(0.8 * usable)
    n_kept = z0.shape[0]
    domains = [x for x in (2, 4, 8, 16, 32, 48) if x < min(n_kept, W - 1)]
    q = causal_q(cand, z0, mask, clock, d, max(1, processed))
    covs, reasons = q["covariances"], q["reasons"]
    ids = {"train": [], "validation": [], "test": []}
    total = {"train": 0, "validation": 0, "test": 0}
    rejected = {"target_gap": 0, "operator_abstain": 0, "eigengap": 0}
    for a in range(W - 1, usable - H):
        s = a - W + 1
        stop = a + H
        if s < GUARD:
            continue
        ds = np.diff(clock[a:stop + 1])
        loc = clock[s:stop + 1]
        if not (np.all(np.isfinite(ds) & (ds > 0) & (ds <= gap))) or any(
            np.any((loc >= left) & (loc <= right)) for left, right in A7.EX.get(rid, ())
        ):
            rejected["target_gap"] += 1
            continue
        role = ("train" if stop < e1 - EMBARGO
                else "validation" if s >= e1 + EMBARGO and stop < e2 - EMBARGO
                else "test" if s >= e2 + EMBARGO else None)
        if role is None:
            continue
        total[role] += 1
        if covs[a] is None:
            rejected["operator_abstain"] += 1
            continue
        if not domains:
            continue
        eig = np.linalg.eigvalsh(covs[a])[::-1]
        mx = max(float(eig[0]), 1e-12)
        if any((eig[x - 1] - eig[x]) / mx <= 1e-12 for x in domains if x < len(eig)):
            rejected["eigengap"] += 1
            continue
        ids[role].append(int(raw_index[a]))
    meta = {}
    for k, v in ids.items():
        canonical = json.dumps(v, separators=(",", ":"))
        meta[k] = {
            "count": len(v),
            "ids_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "first_id": v[0] if v else None,
            "last_id": v[-1] if v else None,
        }
    reason_counts = {}
    for r in reasons:
        if r is not None:
            reason_counts[r] = reason_counts.get(r, 0) + 1
    return meta, total, domains, rejected, reason_counts


def neural_record_v2(cand, p, rid, cut, cls, role):
    """BA-SRM7 neural_record carried verbatim up to z construction, then the
    confirmed robust operator replaces standardization and anchor eligibility."""
    d = loadmat(p, variable_names=("rRaw", "gRaw", "rPhotoCorr", "gPhotoCorr",
                                   "hasPointsTime", "flagged_volumes"), simplify_cells=True)
    req = ("rRaw", "gRaw", "rPhotoCorr", "gPhotoCorr", "hasPointsTime")
    missing = [x for x in req if x not in d]
    base = {"recording_id": rid, "signal_class": cls, "outer_role": role,
            "cut_volume": cut, "mat_bytes": p.stat().st_size, "mat_sha256": A7.sha(p),
            "raw_schema_missing": missing}
    if missing:
        return base | {"schema_passed": False}
    clock = np.asarray(d["hasPointsTime"], float).reshape(-1)
    full = clock.size
    raw_stop = min(full, (cut + 1 if cut is not None else full))
    clock = clock[:raw_stop]
    rawr = np.asarray(d["rRaw"], float)[:, :raw_stop]
    rawg = np.asarray(d["gRaw"], float)[:, :raw_stop]
    pr = np.asarray(d["rPhotoCorr"], float)[:, :raw_stop]
    pg = np.asarray(d["gPhotoCorr"], float)[:, :raw_stop]
    original_index = np.arange(raw_stop)
    excluded = np.zeros(raw_stop, dtype=bool)
    for left, right in A7.EX.get(rid, ()):
        excluded |= (clock >= left) & (clock <= right)
    keep_raw = ~excluded
    original_index = original_index[keep_raw]
    clock = clock[keep_raw]
    rawr, rawg = rawr[:, keep_raw], rawg[:, keep_raw]
    pr, pg = pr[:, keep_raw], pg[:, keep_raw]
    use = clock.size
    schema = rawr.ndim == 2 and rawr.shape == rawg.shape == pr.shape == pg.shape and rawr.shape[1] == use
    if not schema:
        return base | {"schema_passed": False}
    cal = int(0.6 * use)

    # Prefix-fit photobleach correction, carried byte-for-byte in behavior from A7.
    def corr_all(raw):
        out = raw.copy()
        falls = 0
        x = original_index[:cal].astype(float) / 6.0
        xa = original_index.astype(float) / 6.0
        sm = A7.medfilt(raw[:, :cal], (1, 77))
        for i in range(raw.shape[0]):
            y = sm[i]
            ok = np.isfinite(y)
            identity = False
            try:
                scale = float(np.nanmean(y))
                xmax = float(x[-1])
                ys = y / scale
                if ok.sum() < 4 or not np.isfinite(scale) or abs(scale) <= 1e-12:
                    raise ValueError()
                bounds = ([0.0, 1 / (8 * xmax), 0.0],
                          [float(np.nanmax(ys[ok]) * 1.5), 0.5, float(2 * np.nanmean(ys))])
                pp, _ = A7.curve_fit(A7.expf, x[ok], ys[ok],
                                     p0=[np.nanmax(ys) / 2, 2 / xmax, np.nanmean(ys)], bounds=bounds)
                rr = ys - A7.expf(x, *pp)
                good = ok & (np.abs(rr) <= 3 * np.nanstd(rr))
                pp, _ = A7.curve_fit(A7.expf, x[good], ys[good], p0=pp, bounds=bounds)
                pp = np.asarray(pp)
                pp[[0, 2]] *= scale
                cv = A7.expf(xa, *pp)
                if not np.all(np.isfinite(cv)) or np.nansum((raw[i, :cal] - A7.expf(x, *pp)) ** 2) > np.nansum(
                        (raw[i, :cal] - np.nanmean(raw[i, :cal])) ** 2):
                    identity = True
            except Exception:
                identity = True
            if identity:
                falls += 1
            else:
                out[i] = pp[0] * raw[i] / cv
        return out, falls

    R, fr = corr_all(rawr)
    Gc, fg = corr_all(rawg)
    R[np.isnan(pr)] = np.nan
    Gc[np.isnan(pg)] = np.nan
    R = A7.closeholes(R)
    Gc = A7.closeholes(Gc)
    if "flagged_volumes" in d and np.asarray(d["flagged_volumes"]).size:
        ix = np.asarray(d["flagged_volumes"]).reshape(-1).astype(int)
        ix = ix[(ix >= 0) & (ix < raw_stop)]
        ix = np.flatnonzero(np.isin(original_index, ix))
        R[:, ix] = np.nan
        Gc[:, ix] = np.nan
    I = np.full_like(Gc, np.nan)
    for i in range(I.shape[0]):
        ok = np.isfinite(R[i, :cal]) & np.isfinite(Gc[i, :cal])
        if ok.sum() >= 2:
            b, c = np.linalg.lstsq(np.c_[R[i, :cal][ok], np.ones(ok.sum())],
                                   Gc[i, :cal][ok], rcond=None)[0]
            I[i] = Gc[i] - (b * R[i] + c)
    fmask = np.isfinite(I)
    valid = np.mean(~fmask, axis=0) < 0.5
    I, R = I[:, valid], R[:, valid]
    clock, original_index = clock[valid], original_index[valid]
    processed = int(0.6 * clock.size)
    ci = A7.causal(I)
    cr = A7.causal(R)
    finite = np.sum(np.isfinite(I[:, :processed]), axis=1)
    sd = np.nanstd(ci[:, :processed], axis=1)
    kept = (finite >= W) & np.isfinite(sd) & (sd > 1e-12)
    redfinite = np.sum(np.isfinite(R[:, :processed]), axis=1)
    redsd = np.nanstd(cr[:, :processed], axis=1)
    redkept = (redfinite >= W) & np.isfinite(redsd) & (redsd > 1e-12)

    # --- single structural change begins here ---
    z0, zmask, dvec, mad_excluded = robust_z(ci[kept], processed)
    ac, at, domain, rejected, reason_counts = split_anchors_v2(
        cand, clock, original_index, rid, clock.size, z0, zmask, dvec, processed)
    # --- single structural change ends here ---

    unitok = bool(kept.sum() > 0 and redkept.sum() > 0 and z0.shape[0] > 0)
    anchorok = bool(min((x["count"] for x in ac.values()), default=0) >= 100)
    return base | {
        "schema_passed": True,
        "usable_timepoints": int(clock.size),
        "photobleach_identity_fallbacks": {"red": int(fr), "green": int(fg)},
        "processed_calibration_timepoints": int(processed),
        "kept_primary_units": int(kept.sum()),
        "kept_red_units": int(redkept.sum()),
        "robust_scale_excluded_units": len(mad_excluded),
        "operator_units": int(z0.shape[0]),
        "fixed_d_domain": domain,
        "feature_common_anchors": ac,
        "feature_common_anchor_counts": {k: v["count"] for k, v in ac.items()},
        "feature_common_anchors_passed": anchorok,
        "pre_operator_anchor_counts": at,
        "anchor_rejections": rejected,
        "operator_abstain_reason_counts": reason_counts,
        "unit_eligibility_passed": unitok,
        "eligibility_passed": unitok,
    }


def focused_preflight(cand):
    """Frozen synthetic check: irregular clock with a long gap must reject the
    old strict-window rule at many anchors while the ESS operator stays valid,
    and a zero-information tail must trigger the operator abstain."""
    rng = np.random.default_rng(5)
    n, t = 8, 400
    dt = rng.uniform(0.75, 1.25, t)
    dt[150] = 40.0  # one long gap: kills every strict window crossing it
    clock = np.cumsum(dt)
    values = rng.standard_normal((n, t))
    mask = (rng.random((n, t)) >= 0.1).astype(np.uint8)
    z0 = np.where(mask == 1, np.clip(values, -CLIP, CLIP), 0.0)
    d = np.sqrt(mask[:, :240].mean(axis=1))
    q = causal_q(cand, z0, mask, clock, d, 240)
    # The strict W-window rule invalidates every anchor whose 60-sample window
    # crosses the long gap (indices 151..210). The operator must recover far
    # sooner: require at least half of that dead zone to be valid again.
    operator_valid_in_dead_zone = sum(
        q["covariances"][i] is not None for i in range(151, 211))
    strict_valid_in_dead_zone = 0  # by construction: every window spans the gap
    ess_abstain_total = sum(c is None for c in q["covariances"])
    checks = {
        "operator_valid_in_dead_zone": int(operator_valid_in_dead_zone),
        "strict_valid_in_dead_zone": strict_valid_in_dead_zone,
        "ess_abstain_total": int(ess_abstain_total),
        "pass": bool(operator_valid_in_dead_zone >= 30 and ess_abstain_total >= 1),
    }
    if not checks["pass"]:
        raise RuntimeError(f"FOCUSED_PREFLIGHT_FAIL: {checks}")
    return checks


def main():
    for out in (OUT_LOCK, OUT_AUDIT):
        if out.exists():
            raise FileExistsError(out)
    start = time.time()
    srm7_sha = A7.sha(SRM7ART / "input_audit.py")
    cand, man_sha = candidate()
    checks = focused_preflight(cand)
    print(json.dumps({"event": "FOCUSED_PREFLIGHT", **checks}), flush=True)

    root = REPO / "data/external/ba_srm6"
    ext = root / "extracted"
    archives = []
    for name, (bs, h) in A7.ARCHIVES.items():
        p = root / name
        digest = A7.sha(p)
        archives.append({"name": name, "bytes": p.stat().st_size, "sha256": digest,
                         "passed": p.exists() and p.stat().st_size == bs and digest == h})
    records = []
    for rn, (cls, lg) in A7.ROOTS.items():
        for rid, cut in A7.logrows(ext / rn / lg):
            row = neural_record_v2(cand, ext / rn / (rid + "_MS") / "heatDataMS.mat",
                                   rid, cut, cls, (A7.G if cls == "gcamp" else A7.P)[rid])
            records.append(row)
            print(json.dumps({
                "event": "RECORDING", "id": rid,
                "anchors": row.get("feature_common_anchor_counts"),
                "passed": row.get("feature_common_anchors_passed"),
            }), flush=True)

    schema_ok = all(x.get("schema_passed") for x in records)
    elig = all(x.get("eligibility_passed") for x in records)
    anchor = all(min(x.get("feature_common_anchor_counts", {}).values(), default=0) >= 100
                 for x in records)
    passed = all(x["passed"] for x in archives) and schema_ok and elig and anchor
    lock = {
        "schema": "ce.ba_srm13.neural_input_lock.v1",
        "contract": "paper/검증_원장/BA_SRM13_실데이터_입력재감사_계약.md",
        "carried_candidate": CANDIDATE_ID,
        "manifest_sha256": man_sha,
        "srm7_input_audit_sha256": srm7_sha,
        "focused_preflight": checks,
        "archives": archives,
        "recordings": sorted(records, key=lambda x: x["recording_id"]),
        "summary": {"archive_passed": all(x["passed"] for x in archives),
                    "schema_passed": schema_ok, "eligibility_passed": elig,
                    "feature_common_anchors_passed": anchor,
                    "neural_lock_passed": passed},
        "behavior_loaded": False,
        "neural_lock_created_before_behavior": True,
    }
    A7.dump_fsync(OUT_LOCK, lock)
    audit = {
        "schema": "ce.ba_srm13.input_audit.v1",
        "neural_input_lock_sha256": A7.sha(OUT_LOCK),
        "behavior_values_scored": False,
        "model_fit": False,
        "validation_opened": False,
        "test_opened": False,
        "endpoint_opened": False,
        "summary": lock["summary"],
        "runtime_seconds": round(time.time() - start, 3),
    }
    A7.dump_fsync(OUT_AUDIT, audit)
    print(json.dumps({"event": "COMPLETE", "summary": lock["summary"],
                      "lock_sha256": audit["neural_input_lock_sha256"]}), flush=True)


if __name__ == "__main__":
    main()
