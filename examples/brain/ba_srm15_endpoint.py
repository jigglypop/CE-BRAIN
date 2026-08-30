"""BA-SRM15 behavior endpoint runner (staged, irreversible openings).

Contract: paper/검증_원장/BA_SRM15_행동_endpoint_계약.md (LOCKED_PRE_RESULT).
Stages (CLI arg): verify | stageA | stageB | stageC. Each stage writes a
one-shot receipt and refuses to run twice. Behavior values are read only from
stageA on, and only for the recordings each stage is allowed to read.

Implementation conventions declared before any behavior value is read
(recorded in the verify receipt):
  - Anchor identity: anchors are recomputed deterministically with the frozen
    SRM13 operator and MUST hash-equal the SRM13 lock's per-split ids_sha256.
  - Positions: anchor IDs are raw volume indices; all lags/targets/segments
    use retained-sequence positions (the arrays after cut/exclusion/majority
    -missing selection). AR lags {0,1,3,6} and target h=6 are retained-sequence
    offsets; the frozen target-side gap rule already bounds physical spacing.
  - nu/kappa use the immediately preceding retained position; rows whose
    predecessor covariance is abstained become nonfinite and drop out of the
    common-row intersection.
  - Segments (for adverse controls) are maximal retained runs with
    dt <= 3 * median positive dt.
  - PHASE_RANDOMIZED randomizes FFT phases independently per unit within each
    segment of the robust-standardized masked z (mask unchanged), rng seeded
    by SHA-256("20260823|<recording_id>|phase-control").
  - TIME_REVERSED reverses z within each segment (mask reversed identically).
  - CIRCULAR_BEHAVIOR_SHIFT shifts finished neural feature rows within each
    scored split segment by max(1, floor(n/3)).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SRM13_LOCK = Path.cwd() / "ba-srm13-neural-input-lock.json"

_spec = importlib.util.spec_from_file_location("srm13", HERE / "ba_srm13_input_audit.py")
M13 = importlib.util.module_from_spec(_spec)
sys.modules["srm13"] = M13
_spec.loader.exec_module(M13)
A7 = M13.A7
causal_q = M13.causal_q

CAND_ID = M13.CANDIDATE_ID
H_TARGET = 6
AR_LAGS = (0, 1, 3, 6)
RIDGE_GRID = (0.0, 0.01, 0.1, 1.0, 10.0, 100.0)
FIXED_D_MENU = (2, 4, 8, 16, 32, 48)
BOOT_BLOCK, BOOT_N, BOOT_SEED = 60, 2000, 20260823
REQUIRED_FAMILIES = ("AR", "CE_SOFT", "FIXED_D", "FIXED_4", "PARTICIPATION_RATIO",
                     "RAW_SPECTRAL", "CAUSAL_UNWEIGHTED", "MASK_ONLY", "RED_CHANNEL")

ROLE_SPLITS = {"train": ("train",), "validation": ("train", "validation"),
               "held_out": ("train", "test")}
SCORED_SPLIT = {"train": "train", "validation": "validation", "held_out": "test"}


def receipt_path(stage: str) -> Path:
    return Path.cwd() / f"ba-srm15-{stage}-receipt.json"


def load_lock():
    return json.loads(SRM13_LOCK.read_text(encoding="utf-8"))


def eig_features(cov, cg, r_star):
    """Eigen data of G~ = cov/cg, descending."""
    mu, vec = np.linalg.eigh(cov / cg)
    order = np.argsort(mu)[::-1]
    return mu[order], vec[:, order]


def soft_matrix(mu, vec):
    return (vec * (mu / (mu + 1.0))) @ vec.T


def prepare_recording(cand, rid, cut, cls, role):
    """SRM13 pipeline, returning arrays instead of a receipt (behavior-blind)."""
    ext = REPO / "data/external/ba_srm6/extracted"
    root = next(rn for rn, (c, _) in A7.ROOTS.items()
                if (ext / rn / (rid + "_MS") / "heatDataMS.mat").exists() and c == cls)
    p = ext / root / (rid + "_MS") / "heatDataMS.mat"
    d = M13.loadmat(p, variable_names=("rRaw", "gRaw", "rPhotoCorr", "gPhotoCorr",
                                       "hasPointsTime", "flagged_volumes"), simplify_cells=True)
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
    rawr, rawg, pr, pg = (x[:, keep_raw] for x in (rawr, rawg, pr, pg))
    use = clock.size
    cal = int(0.6 * use)

    rec = M13.neural_record_v2  # noqa: F841  (kept for provenance; we inline below)
    # Reuse the exact corr/regression steps via a temporary record call is not
    # possible (it returns a receipt), so replicate through A7 helpers exactly
    # as ba_srm13_input_audit.neural_record_v2 does.
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

    R, _ = corr_all(rawr)
    Gc, _ = corr_all(rawg)
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
    kept = (finite >= A7.W) & np.isfinite(sd) & (sd > 1e-12)
    redfinite = np.sum(np.isfinite(R[:, :processed]), axis=1)
    redsd = np.nanstd(cr[:, :processed], axis=1)
    redkept = (redfinite >= A7.W) & np.isfinite(redsd) & (redsd > 1e-12)

    z0, zmask, dvec, _ = M13.robust_z(ci[kept], processed)
    anchors, _, domains, _, _ = M13.split_anchors_v2(
        cand, clock, original_index, rid, clock.size, z0, zmask, dvec, processed)
    return {
        "rid": rid, "cls": cls, "role": role, "mat_path": p,
        "raw_stop": raw_stop, "keep_raw": keep_raw, "valid": valid,
        "clock": clock, "original_index": original_index, "processed": processed,
        "ci_kept": ci[kept], "cr_red": cr[redkept],
        "z0": z0, "zmask": zmask, "dvec": dvec, "domains": domains,
        "anchors": anchors,
    }


def verify_anchor_identity(prep, lock_rec):
    got = {k: prep["anchors"][k]["ids_sha256"] for k in ("train", "validation", "test")}
    want = {k: lock_rec["feature_common_anchors"][k]["ids_sha256"]
            for k in ("train", "validation", "test")}
    return got == want, {"got": got, "want": want}


def collect_anchor_ids(cand, prep):
    """Same loop as split_anchors_v2 but returning the id lists themselves."""
    clock = prep["clock"]
    raw_index = prep["original_index"]
    rid = prep["rid"]
    usable = clock.size
    z0, mask, d = prep["z0"], prep["zmask"], prep["dvec"]
    processed = prep["processed"]
    pos = np.diff(clock)
    pos = pos[np.isfinite(pos) & (pos > 0)]
    gap = 3.0 * np.median(pos) if pos.size else np.nan
    e1, e2 = int(0.6 * usable), int(0.8 * usable)
    domains = prep["domains"]
    q = causal_q(cand, z0, mask, clock, d, max(1, processed))
    covs = q["covariances"]
    ids = {"train": [], "validation": [], "test": []}
    for a in range(A7.W - 1, usable - A7.H):
        s = a - A7.W + 1
        stop = a + A7.H
        if s < A7.GUARD:
            continue
        ds = np.diff(clock[a:stop + 1])
        loc = clock[s:stop + 1]
        if not (np.all(np.isfinite(ds) & (ds > 0) & (ds <= gap))) or any(
            np.any((loc >= left) & (loc <= right)) for left, right in A7.EX.get(rid, ())
        ):
            continue
        role = ("train" if stop < e1 - A7.EMBARGO
                else "validation" if s >= e1 + A7.EMBARGO and stop < e2 - A7.EMBARGO
                else "test" if s >= e2 + A7.EMBARGO else None)
        if role is None or covs[a] is None or not domains:
            continue
        eig = np.linalg.eigvalsh(covs[a])[::-1]
        mx = max(float(eig[0]), 1e-12)
        if any((eig[x - 1] - eig[x]) / mx <= 1e-12 for x in domains if x < len(eig)):
            continue
        ids[role].append(int(raw_index[a]))
    digest = {k: hashlib.sha256(json.dumps(v, separators=(",", ":")).encode()).hexdigest()
              for k, v in ids.items()}
    return ids, digest, q


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if stage != "verify":
        raise SystemExit("only 'verify' is implemented in this runner revision; "
                         "stageA/B/C arrive in the next revision after verify passes")
    out = receipt_path("verify")
    if out.exists():
        raise FileExistsError(out)
    start = time.time()
    cand, man_sha = M13.candidate()
    lock = load_lock()
    lock_by_id = {r["recording_id"]: r for r in lock["recordings"]}
    ext = REPO / "data/external/ba_srm6/extracted"
    rows = []
    all_ok = True
    for rn, (cls, lg) in A7.ROOTS.items():
        for rid, cut in A7.logrows(ext / rn / lg):
            role = (A7.G if cls == "gcamp" else A7.P)[rid]
            prep = prepare_recording(cand, rid, cut, cls, role)
            ids, digest, _ = collect_anchor_ids(cand, prep)
            want = {k: lock_by_id[rid]["feature_common_anchors"][k]["ids_sha256"]
                    for k in ("train", "validation", "test")}
            ok = digest == want
            all_ok = all_ok and ok
            rows.append({"recording_id": rid, "role": role, "cls": cls,
                         "anchor_sha_match": ok,
                         "counts": {k: len(v) for k, v in ids.items()}})
            print(json.dumps({"event": "VERIFY", "id": rid, "match": ok}), flush=True)
    receipt = {
        "schema": "ba-srm15-verify-v1",
        "contract": "paper/검증_원장/BA_SRM15_행동_endpoint_계약.md",
        "carried_candidate": CAND_ID,
        "manifest_sha256": man_sha,
        "srm13_lock_sha256": hashlib.sha256(SRM13_LOCK.read_bytes()).hexdigest(),
        "conventions": __doc__,
        "recordings": rows,
        "anchor_identity_all_match": all_ok,
        "behavior_loaded": False,
        "runtime_seconds": round(time.time() - start, 3),
    }
    A7.dump_fsync(out, receipt)
    print(json.dumps({"event": "COMPLETE", "all_match": all_ok}), flush=True)


if __name__ == "__main__":
    main()
