"""Real DANDI 001701 behavior-controlled affine-fiber development endpoint."""
from __future__ import annotations

import importlib.util
import json
import math
import shutil
import tempfile
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
CORE_PATH = HERE / "analyze_real_dandi.py"
if not CORE_PATH.exists():
    CORE_PATH = HERE.parents[2] / "real-dandi-001701" / "analyze_real_dandi.py"
SPEC = importlib.util.spec_from_file_location("real_dandi_core", CORE_PATH)
core = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(core)

POSITION = "processing/behavior/Position/position"
HEAD_DIRECTION = "processing/behavior/CompassDirection/head direction"
BEHAVIOR_START = 3.907897
BEHAVIOR_RATE = 60.0
MAX_GAP = 0.5


def write_json(name: str, value: dict) -> None:
    (HERE / name).write_text(
        json.dumps(core.jsonable(value), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def implicit_timebase(group: h5py.Group) -> tuple[float, float]:
    if "starting_time" not in group:
        raise ValueError("BEHAVIOR_STARTING_TIME_MISSING")
    ds = group["starting_time"]
    start = float(np.asarray(ds)[()])
    rate = float(ds.attrs.get("rate", math.nan))
    if not np.isfinite(start) or not np.isfinite(rate) or rate <= 0:
        raise ValueError("BEHAVIOR_TIMEBASE_INVALID")
    if abs(start - BEHAVIOR_START) > 1e-9 or abs(rate - BEHAVIOR_RATE) > 1e-12:
        raise ValueError(f"BEHAVIOR_TIMEBASE_CHANGED:{start},{rate}")
    return start, rate


def read_behavior(nwb: h5py.File, stop: float | None) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    pg, hg = nwb[POSITION], nwb[HEAD_DIRECTION]
    ps, pr = implicit_timebase(pg)
    hs, hr = implicit_timebase(hg)
    if ps != hs or pr != hr:
        raise ValueError("BEHAVIOR_CLOCK_MISMATCH")
    total = min(len(pg["data"]), len(hg["data"]))
    count = total if stop is None else min(total, max(0, int(math.ceil((stop - ps) * pr))))
    pos = np.asarray(pg["data"][:count], dtype=float)
    hd = np.asarray(hg["data"][:count], dtype=float).reshape(-1)
    if pos.ndim != 2 or pos.shape[1] != 2 or hd.shape[0] != pos.shape[0]:
        raise ValueError("BEHAVIOR_SHAPE_INVALID")
    unit = str(hg["data"].attrs.get("unit", hg.attrs.get("unit", ""))).lower()
    if "deg" in unit:
        hd = np.deg2rad(hd)
        hd_unit = "degrees_to_radians"
    elif unit in {"rad", "radian", "radians"} or "rad" in unit:
        hd_unit = "radians"
    else:
        raise ValueError(f"HEAD_DIRECTION_UNIT_UNSUPPORTED:{unit}")
    times = ps + np.arange(count, dtype=float) / pr
    return times, pos, hd, {"start": ps, "rate_hz": pr, "samples_read": count, "head_direction_unit": hd_unit}


def interpolation_valid(source_t: np.ndarray, finite: np.ndarray, target_t: np.ndarray) -> np.ndarray:
    good_t = source_t[finite]
    if good_t.size < 2:
        return np.zeros(target_t.size, dtype=bool)
    right = np.searchsorted(good_t, target_t, side="left")
    inside = (right > 0) & (right < good_t.size)
    clipped = np.clip(right, 1, good_t.size - 1)
    gap = good_t[clipped] - good_t[clipped - 1]
    return inside & (gap <= MAX_GAP)


def behavior_features(source_t: np.ndarray, pos: np.ndarray, hd: np.ndarray, centers: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pos_ok = np.isfinite(pos).all(axis=1)
    hd_ok = np.isfinite(hd)
    valid = interpolation_valid(source_t, pos_ok, centers) & interpolation_valid(source_t, hd_ok, centers)
    p = np.empty((centers.size, 2), dtype=float)
    for j in range(2):
        p[:, j] = np.interp(centers, source_t[pos_ok], pos[pos_ok, j])
    ss = np.interp(centers, source_t[hd_ok], np.sin(hd[hd_ok]))
    cc = np.interp(centers, source_t[hd_ok], np.cos(hd[hd_ok]))
    norm = np.hypot(ss, cc)
    valid &= norm >= 1e-8
    ss = np.divide(ss, norm, out=np.zeros_like(ss), where=norm >= 1e-8)
    cc = np.divide(cc, norm, out=np.zeros_like(cc), where=norm >= 1e-8)
    velocity = np.zeros_like(p)
    velocity[1:] = np.diff(p, axis=0) / core.BIN_SECONDS
    valid[0] = False
    valid[1:] &= valid[:-1]
    phi = np.c_[p, ss, cc, velocity]
    valid &= np.isfinite(phi).all(axis=1)
    return phi, valid


def model_rows(block: tuple[int, int], segments: np.ndarray, behavior_valid: np.ndarray, lag: int = 0) -> np.ndarray:
    rows = core.valid_rows(block, segments, horizon=1, lag=lag)
    return rows[behavior_valid[rows]]


def ridge_models(x: np.ndarray, y: np.ndarray, rows: np.ndarray) -> dict[float, tuple[np.ndarray, np.ndarray]]:
    return {lam: core.ridge(x[rows], y[rows + 1], lam) for lam in core.RIDGES}


def diagonal_interaction_path(
    xb: np.ndarray,
    y: np.ndarray,
    phi: np.ndarray,
    target: np.ndarray,
    rows: np.ndarray,
) -> dict[float, dict]:
    xb0, y0, p0, t0 = xb[rows], y[rows], phi[rows], target[rows + 1]
    xb_mean, target_mean = xb0.mean(0), t0.mean(0)
    xbc, tc = xb0 - xb_mean, t0 - target_mean
    j = y0[:, :, None] * p0[:, None, :]
    j_mean = j.mean(0)
    jc = j - j_mean
    n, m, k = jc.shape
    gx = xbc.T @ xbc
    xy = xbc.T @ tc
    xj_flat = xbc.T @ jc.reshape(n, m * k)
    jj = np.einsum("nkj,nkl->kjl", jc, jc, optimize=True)
    jy = np.einsum("nkj,nk->kj", jc, tc, optimize=True)
    out = {}
    for lam in core.RIDGES:
        g = gx + lam * np.eye(gx.shape[0])
        solved = np.linalg.solve(g, np.c_[xy, xj_flat])
        gy = solved[:, :m]
        gj = solved[:, m:].reshape(xb.shape[1], m, k)
        beta = np.empty_like(gy)
        a = np.empty((m, k), dtype=float)
        for unit in range(m):
            cross = xj_flat[:, unit * k:(unit + 1) * k]
            schur = jj[unit] + lam * np.eye(k) - cross.T @ gj[:, unit, :]
            rhs = jy[unit] - cross.T @ gy[:, unit]
            schur = 0.5 * (schur + schur.T)
            a[unit] = np.linalg.solve(schur, rhs)
            beta[:, unit] = gy[:, unit] - gj[:, unit, :] @ a[unit]
        intercept = target_mean - xb_mean @ beta - np.einsum("kj,kj->k", j_mean, a)
        out[lam] = {"beta": beta, "a": a, "intercept": intercept}
    return out


def fiber_predict(fit: dict, xb: np.ndarray, y: np.ndarray, phi: np.ndarray, rows: np.ndarray) -> np.ndarray:
    return xb[rows] @ fit["beta"] + y[rows] * (phi[rows] @ fit["a"].T) + fit["intercept"]


def fit_candidate_grid(x: np.ndarray, phi: np.ndarray, train: np.ndarray, dev: np.ndarray, basis: np.ndarray) -> tuple[dict, list[dict]]:
    entries = []
    for d in (2, 4, 8):
        if d >= min(9, x.shape[1]):
            continue
        z, y = x @ basis[:, :d], x @ basis[:, d:]
        z_features = np.c_[z, phi]
        z_path = ridge_models(z_features, z, train)
        xb = np.c_[y, z, phi]
        fiber_path = diagonal_interaction_path(xb, y, phi, y, train)
        for lam in core.RIDGES:
            zc, zi = z_path[lam]
            pred_z = core.predict(zc, zi, z_features[dev])
            pred_y = fiber_predict(fiber_path[lam], xb, y, phi, dev)
            pred = pred_z @ basis[:, :d].T + pred_y @ basis[:, d:].T
            sse = float(np.square(x[dev + 1] - pred).sum())
            entries.append({"development_sse": sse, "d": d, "lambda": lam, "B": zc, "base_intercept": zi, "fiber": fiber_path[lam], "basis": basis})
    if not entries:
        raise ValueError("NO_R1_CANDIDATE")
    entries.sort(key=lambda q: (q["development_sse"], q["d"], -q["lambda"]))
    return entries[0], entries


def candidate_predict(model: dict, x: np.ndarray, phi: np.ndarray, rows: np.ndarray) -> np.ndarray:
    basis, d = model["basis"], model["d"]
    z, y = x @ basis[:, :d], x @ basis[:, d:]
    zf = np.c_[z, phi]
    xb = np.c_[y, z, phi]
    pred_z = core.predict(model["B"], model["base_intercept"], zf[rows])
    pred_y = fiber_predict(model["fiber"], xb, y, phi, rows)
    return pred_z @ basis[:, :d].T + pred_y @ basis[:, d:].T


def select_simple_controls(x: np.ndarray, phi: np.ndarray, train: np.ndarray, dev: np.ndarray, basis: np.ndarray) -> dict:
    full = []
    for lam in core.RIDGES:
        coef, intercept = core.ridge(np.c_[x[train], phi[train]], x[train + 1], lam)
        pred = core.predict(coef, intercept, np.c_[x[dev], phi[dev]])
        full.append((float(np.square(x[dev + 1] - pred).sum()), -lam, coef, intercept, lam))
    full.sort(key=lambda q: (q[0], q[1]))
    inp = []
    for lam in core.RIDGES:
        coef, intercept = core.ridge(phi[train], x[train + 1], lam)
        pred = core.predict(coef, intercept, phi[dev])
        inp.append((float(np.square(x[dev + 1] - pred).sum()), -lam, coef, intercept, lam))
    inp.sort(key=lambda q: (q[0], q[1]))
    base = []
    for d in (2, 4, 8):
        if d >= min(9, x.shape[1]):
            continue
        z = x @ basis[:, :d]
        features = np.c_[z, phi]
        for lam in core.RIDGES:
            coef, intercept = core.ridge(features[train], x[train + 1], lam)
            pred = core.predict(coef, intercept, features[dev])
            base.append((float(np.square(x[dev + 1] - pred).sum()), d, -lam, coef, intercept, lam))
    base.sort(key=lambda q: (q[0], q[1], q[2]))
    return {
        "full": {"coef": full[0][2], "intercept": full[0][3], "lambda": full[0][4]},
        "input": {"coef": inp[0][2], "intercept": inp[0][3], "lambda": inp[0][4]},
        "base": {"d": base[0][1], "coef": base[0][3], "intercept": base[0][4], "lambda": base[0][5]},
    }


def contraction_audit(model: dict, phi: np.ndarray, rows: np.ndarray) -> dict:
    """Certify q<1, certify q>1, or compute exact norms in the unresolved band."""
    d = model["d"]
    m = model["basis"].shape[1] - d
    a0 = model["fiber"]["beta"][:m, :]
    modulation = phi[rows] @ model["fiber"]["a"].T
    diagonal = np.diag(a0)
    base_column_sq = np.square(a0).sum(axis=0)
    column_sq = base_column_sq[None, :] - np.square(diagonal)[None, :] + np.square(diagonal[None, :] + modulation)
    lower = float(np.sqrt(np.maximum(column_sq, 0.0)).max())
    upper = float(np.linalg.norm(a0, 2) + np.abs(modulation).max())
    if lower > 1.0:
        return {"value": lower, "kind": "certified_lower_bound", "passes": False, "upper_bound": upper}
    if upper < 1.0:
        return {"value": upper, "kind": "certified_upper_bound", "passes": True, "lower_bound": lower}
    maximum = max(float(np.linalg.norm(a0 + np.diag(row), 2)) for row in modulation)
    return {"value": maximum, "kind": "exact", "passes": maximum < 1.0, "lower_bound": lower, "upper_bound": upper}


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="ce-dandi-r1-full-"))
    receipt = {"dandiset": core.DANDISET, "version": core.VERSION, "asset_id": core.ASSET_ID, "downloaded": False, "nwb_deleted": False}
    try:
        path = tmp / "source.nwb"
        receipt.update(core.download_verified(path))
        receipt["downloaded"] = True
        with h5py.File(path, "r") as nwb:
            start, stop, segments, coverage = core.electrical_coverage(nwb)
            spikes = nwb["units/spike_times"]
            indexes = np.asarray(nwb["units/spike_times_index"], dtype=np.int64)
            n_bins = int(math.floor((stop - start) / core.BIN_SECONDS))
            train_end, dev_end = int(math.floor(.5 * n_bins)), int(math.floor(.75 * n_bins))
            train_boundary = start + train_end * core.BIN_SECONDS
            test_boundary = start + dev_end * core.BIN_SECONDS
            retention_counts, retention_max = core.prefix_unit_statistics(spikes, indexes, start, train_boundary)
            retained = np.flatnonzero(retention_counts / (train_boundary - start) >= .1)
            prefix_counts, prefix_max = core.bins_for_interval(spikes, indexes, retained, start, test_boundary, dev_end)
            bt, bp, bh, behavior_meta = read_behavior(nwb, test_boundary)
            centers_prefix = start + (np.arange(dev_end) + .5) * core.BIN_SECONDS
            phi_raw, behavior_valid_prefix = behavior_features(bt, bp, bh, centers_prefix)
            segment_ids = np.full(n_bins, -1, dtype=np.int64)
            for sid, (left, right) in enumerate(segments):
                first = max(0, int(math.ceil((left - start) / core.BIN_SECONDS)))
                last = min(n_bins, int(math.floor((right - start) / core.BIN_SECONDS)))
                segment_ids[first:last] = sid
            blocks = {"train": (0, train_end), "development": (train_end, dev_end), "test": (dev_end, n_bins)}
            train_phi_bins = np.arange(train_end)[behavior_valid_prefix[:train_end]]
            if train_phi_bins.size < 300:
                raise ValueError("INSUFFICIENT_TRAIN_BEHAVIOR_BINS")
            phi_mean = phi_raw[train_phi_bins].mean(0)
            phi_scale = phi_raw[train_phi_bins].std(0)
            phi_scale[phi_scale == 0] = 1.0
            phi_prefix = (phi_raw - phi_mean) / phi_scale
            transformed = np.sqrt(prefix_counts + 3.0 / 8.0)
            neural_mean = transformed[:train_end].mean(0)
            neural_scale = transformed[:train_end].std(0)
            neural_scale[neural_scale == 0] = 1.0
            x_prefix = (transformed - neural_mean) / neural_scale
            basis, _ = core.pca(x_prefix[:train_end])
            train_rows = model_rows(blocks["train"], segment_ids, behavior_valid_prefix)
            dev_rows = model_rows(blocks["development"], segment_ids, behavior_valid_prefix)
            selected, candidates = fit_candidate_grid(x_prefix, phi_prefix, train_rows, dev_rows, basis)
            controls = select_simple_controls(x_prefix, phi_prefix, train_rows, dev_rows, basis)
            model_selected = True
            assert retention_max is None or retention_max < train_boundary
            assert prefix_max is None or prefix_max < test_boundary
            assert x_prefix.shape[0] == dev_end and model_selected
            all_counts, _ = core.bins_for_interval(spikes, indexes, retained, start, start + n_bins * core.BIN_SECONDS, n_bins)
            bt_all, bp_all, bh_all, behavior_meta_all = read_behavior(nwb, None)
        centers = start + (np.arange(n_bins) + .5) * core.BIN_SECONDS
        phi_all_raw, behavior_valid = behavior_features(bt_all, bp_all, bh_all, centers)
        phi = (phi_all_raw - phi_mean) / phi_scale
        x = (np.sqrt(all_counts + 3.0 / 8.0) - neural_mean) / neural_scale
        test_rows = model_rows(blocks["test"], segment_ids, behavior_valid)
        denominator = float(np.square(x[test_rows + 1] - x[:train_end].mean(0)).sum())
        if test_rows.size < 300 or denominator <= 0:
            raise ValueError("INSUFFICIENT_TEST_ROWS_OR_DENOMINATOR")
        target = x[test_rows + 1]
        estimate = candidate_predict(selected, x, phi, test_rows)
        full_est = core.predict(controls["full"]["coef"], controls["full"]["intercept"], np.c_[x[test_rows], phi[test_rows]])
        input_est = core.predict(controls["input"]["coef"], controls["input"]["intercept"], phi[test_rows])
        z_base = x @ basis[:, :controls["base"]["d"]]
        base_est = core.predict(controls["base"]["coef"], controls["base"]["intercept"], np.c_[z_base[test_rows], phi[test_rows]])
        errors = {
            "candidate": np.square(target - estimate).sum(1),
            "full_var_input": np.square(target - full_est).sum(1),
            "base_input": np.square(target - base_est).sum(1),
            "input_only": np.square(target - input_est).sum(1),
            "persistence": np.square(target - x[test_rows]).sum(1),
        }
        scores = {k: float(v.sum() / denominator) for k, v in errors.items()}
        boot_full = core.bootstrap(errors["full_var_input"] - errors["candidate"], test_rows)
        boot_base = core.bootstrap(errors["base_input"] - errors["candidate"], test_rows)
        imp_full = 1 - scores["candidate"] / scores["full_var_input"]
        imp_base = 1 - scores["candidate"] / scores["base_input"]
        contraction = contraction_audit(selected, phi, test_rows)
        qvalue = contraction["value"]
        shift_phi_prefix = np.full_like(phi_prefix, np.nan)
        shift_valid_prefix = np.zeros(dev_end, dtype=bool)
        for begin, end in (blocks["train"], blocks["development"]):
            shift_phi_prefix[begin + 100:end] = phi_prefix[begin:end - 100]
            shift_valid_prefix[begin + 100:end] = behavior_valid_prefix[begin:end - 100]
        shift_train = model_rows(blocks["train"], segment_ids, shift_valid_prefix, lag=100)
        shift_dev = model_rows(blocks["development"], segment_ids, shift_valid_prefix, lag=100)
        shifted_model, _ = fit_candidate_grid(x_prefix, shift_phi_prefix, shift_train, shift_dev, basis)
        shift_phi = np.full_like(phi, np.nan)
        shift_valid = np.zeros(n_bins, dtype=bool)
        for begin, end in blocks.values():
            shift_phi[begin + 100:end] = phi[begin:end - 100]
            shift_valid[begin + 100:end] = behavior_valid[begin:end - 100]
        shift_test = model_rows(blocks["test"], segment_ids, shift_valid, lag=100)
        shifted_score = core.nmse(x[shift_test + 1], candidate_predict(shifted_model, x, shift_phi, shift_test), denominator)
        real_reduced = core.nmse(x[shift_test + 1], candidate_predict(selected, x, phi, shift_test), denominator)
        positive = (
            imp_full >= .01 and imp_base >= .01
            and boot_full.get("ci95", [-math.inf])[0] > 0
            and boot_base.get("ci95", [-math.inf])[0] > 0
            and contraction["passes"] and shifted_score > real_reduced
        )
        result = {
            "status": "PASS" if positive else "STOP",
            "failure_code": None if positive else "R1_EMPIRICAL_KILL_CONDITION",
            "claim_ceiling": "Outcome-informed L2 development only; independent confirmation unopened.",
            "source": {"dandiset": core.DANDISET, "version": core.VERSION, "asset": core.ASSET_PATH},
            "schema": {"position": POSITION, "head_direction": HEAD_DIRECTION, "behavior_prefix": behavior_meta, "behavior_full": behavior_meta_all},
            "coverage": coverage,
            "retained_units": int(retained.size), "bins": int(n_bins),
            "valid_rows": {"train": int(train_rows.size), "development": int(dev_rows.size), "test": int(test_rows.size)},
            "preselection_audit": {"retention_scope": "train_only", "retention_boundary_seconds": train_boundary, "retention_event_max": retention_max, "test_boundary_seconds": test_boundary, "prefix_event_max": prefix_max, "prefix_shape": list(prefix_counts.shape), "test_materialized_after_selection": True},
            "selected": {"d": selected["d"], "lambda": selected["lambda"], "candidate_count": len(candidates)},
            "controls": {"full_var_input_lambda": controls["full"]["lambda"], "base_input_d": controls["base"]["d"], "base_input_lambda": controls["base"]["lambda"], "input_only_lambda": controls["input"]["lambda"]},
            "nmse_denominator": denominator, "scores_nmse": scores,
            "improvement": {"over_full_var_input": imp_full, "over_base_input": imp_base},
            "bootstrap": {"full_var_input": boot_full, "base_input": boot_base},
            "q_max": qvalue, "contraction_audit": contraction,
            "shifted_behavior": {"rows": int(shift_test.size), "real_rescored_nmse": real_reduced, "shifted_refit_nmse": shifted_score, "real_better": shifted_score > real_reduced},
            "confirmation_001695_opened": False,
        }
        write_json("result.json", result)
        receipt.update({"bytes_received": core.EXPECTED_SIZE, "sha256": core.EXPECTED_SHA256, "schema_paths": {"position": POSITION, "head_direction": HEAD_DIRECTION}, "nwb_deleted": False})
        print(json.dumps(core.jsonable({"status": result["status"], "retained_units": retained.size, "rows": result["valid_rows"], "scores_nmse": scores, "improvement": result["improvement"], "q_max": qvalue, "shifted": result["shifted_behavior"]}), indent=2))
    except Exception as exc:
        write_json("result.json", {"status": "STOP", "failure_code": "R1_EXECUTION_OR_SCHEMA_FAILURE", "detail": repr(exc), "claim_ceiling": "No empirical bridge."})
        receipt["error"] = repr(exc)
        raise
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
        receipt["nwb_deleted"] = True
        write_json("source-receipt.json", receipt)


if __name__ == "__main__":
    main()
