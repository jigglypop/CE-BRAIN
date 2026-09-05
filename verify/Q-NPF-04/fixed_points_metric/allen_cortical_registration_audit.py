"""Coordinate-only development audit: image correspondence is not a 3D pia normal.

Reuses frozen SQLite and producer definitions. No connection labels are queried.
The domain was chosen during exploratory coordinate inspection, not preregistered.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE / "allen_cortical_registration_audit_result.json"
MODELS = ["centroid", "xy_similarity", "xy_affine", "xyz_affine"]
RCOND = 1e-10


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point(value, dimension):
    try:
        p = np.asarray(json.loads(value), float)
        return p if p.shape == (dimension,) and np.isfinite(p).all() else None
    except (TypeError, ValueError):
        return None


def spectrum(x):
    s = np.linalg.svd(x - x.mean(0), compute_uv=False)
    rank = int(np.sum(s > s[0] * RCOND)) if s[0] > 0 else 0
    return dict(singular_values_um=s.tolist(), rank=rank,
                condition=float(s[0] / s[-1]) if rank == x.shape[1] else None)


def fit(x, y, model):
    """Return row-convention y=(x-center)@B+target_center, B is 3 x 2."""
    xc = x.mean(0); yc = y.mean(0)
    a = x - xc; b = y - yc
    coef = np.zeros((3, 2)); scale = None
    if model == "centroid":
        pass
    elif model == "xy_similarity":
        if spectrum(x[:, :2])["rank"] != 2:
            return None
        u, s, vt = np.linalg.svd(a[:, :2].T @ b)
        scale = float(s.sum() / np.sum(a[:, :2] ** 2))
        coef[:2] = scale * (u @ vt)  # Reflection permitted between image conventions.
    elif model in ["xy_affine", "xyz_affine"]:
        dim = 2 if model == "xy_affine" else 3
        if spectrum(x[:, :dim])["rank"] != dim:
            return None
        coef[:dim] = np.linalg.lstsq(a[:, :dim], b, rcond=RCOND)[0]
    else:
        raise ValueError(model)
    return dict(center_um=xc.tolist(), image_center_um=yc.tolist(), B_3_by_2=coef.tolist(), scale=scale)


def predict(fitted, x):
    return (np.asarray(x) - fitted["center_um"]) @ np.array(fitted["B_3_by_2"]) + fitted["image_center_um"]


def metric_completion(b, weight):
    """For rank-2 image map B, complete its rank-2 pullback in the unseen direction."""
    b = np.asarray(b, float)
    if b.shape != (3, 2) or np.linalg.matrix_rank(b, tol=RCOND) != 2 or weight <= 0:
        raise ValueError("Rank-two map and positive completion weight required")
    u, _, _ = np.linalg.svd(b, full_matrices=True)
    hidden = u[:, -1]
    g = (b @ b.T + weight * np.outer(hidden, hidden)) / 100 ** 2
    return g, hidden


def quantiles(values):
    a = np.asarray(values, float)
    return np.quantile(a, [0, .05, .5, .95, 1]).tolist() if len(a) else None


def evaluate(experiment, cells):
    x = np.array([r["position_3D_um"] for r in cells])
    y = np.array([r["position_2D_um"] for r in cells])
    n = len(cells)
    loo_spectra = [spectrum(x[np.arange(n) != i]) for i in range(n)]
    models = {}
    for model in MODELS:
        full = fit(x, y, model)
        predictions = []; errors = []; coefficients = []
        for i in range(n):
            mask = np.arange(n) != i
            fitted = fit(x[mask], y[mask], model)
            if fitted is None:
                predictions.append(None); errors.append(None); coefficients.append(None)
                continue
            predicted = predict(fitted, x[i])
            predictions.append(predicted.tolist())
            errors.append(float(np.linalg.norm(predicted - y[i])))
            coefficients.append(fitted["B_3_by_2"])
        valid = all(e is not None for e in errors)
        models[model] = dict(full_fit=full, loo_predictions_um=predictions, loo_error_um=errors,
                             loo_B=coefficients, all_loo_identifiable=valid,
                             loo_rmse_um=float(np.sqrt(np.mean(np.square(errors)))) if valid else None,
                             loo_max_error_um=float(max(errors)) if valid else None)

    # Audit the stored 2D-derived depth as an affine scalar field in 3D.
    depth = np.array([r["depth_um"] if r["depth_um"] is not None else np.nan for r in cells])
    depth_result = dict(all_depth_finite=bool(np.isfinite(depth).all()), status="not_evaluated")
    if np.isfinite(depth).all() and all(s["rank"] == 3 for s in loo_spectra):
        center = x.mean(0); dm = depth.mean()
        gradient = np.linalg.lstsq(x-center, depth-dm, rcond=RCOND)[0]
        predictions = []; gradients = []; angles = []
        for i in range(n):
            mask = np.arange(n) != i
            a = np.linalg.lstsq(x[mask]-x[mask].mean(0), depth[mask]-depth[mask].mean(), rcond=RCOND)[0]
            predictions.append(float((x[i]-x[mask].mean(0)) @ a + depth[mask].mean()))
            gradients.append(a.tolist())
            denom = np.linalg.norm(a)*np.linalg.norm(gradient)
            angles.append(float(np.degrees(np.arccos(np.clip(a@gradient/denom, -1, 1)))) if denom > 1e-12 else None)
        errors = np.array(predictions)-depth
        depth_result.update(status="stored_depth_consistency_only", gradient=gradient.tolist(), gradient_norm=float(np.linalg.norm(gradient)),
            loo_predictions_um=predictions, loo_gradients=gradients, loo_angle_to_full_deg=angles,
            loo_rmse_um=float(np.sqrt(np.mean(errors**2))), loo_max_error_um=float(np.max(abs(errors))),
            max_loo_angle_deg=max(angles) if all(v is not None for v in angles) else None)

    pullback = None
    full = models["xyz_affine"]["full_fit"]
    if full is not None:
        b = np.array(full["B_3_by_2"])
        if np.linalg.matrix_rank(b, tol=RCOND) == 2:
            g1, hidden = metric_completion(b, .25); g2, _ = metric_completion(b, 4.)
            delta = x[:, None] - x[None, :]
            q1 = np.einsum("...i,ij,...j->...", delta, g1, delta)
            q2 = np.einsum("...i,ij,...j->...", delta, g2, delta)
            s = np.linalg.svd(b, compute_uv=False)
            pullback = dict(image_map_singular_values=s.tolist(), singular_value_ratio=float(s[0]/s[1]),
                hidden_unit_vector=hidden.tolist(), hidden_image_residual=float(np.linalg.norm(hidden@b)),
                B_z_row_over_Frobenius=float(np.linalg.norm(b[2])/np.linalg.norm(b)),
                completed_g_per_um2=[g1.tolist(),g2.tolist()], completion_weights=[.25,4.],
                minimum_eigenvalues=[float(np.linalg.eigvalsh(g)[0]) for g in [g1,g2]],
                max_pair_cost_difference=float(np.max(abs(q2-q1))),
                scope="Different candidate 3D costs compatible with the same image-coordinate map; connection predictions were not compared")
    return dict(experiment_id=experiment, n=n, cells=cells, full_3D_spectrum=spectrum(x),
                loo_3D_spectra=loo_spectra, models=models, depth=depth_result, pullback=pullback)


def main():
    if OUTPUT.exists():
        raise FileExistsError("Completed coordinate audit is immutable")
    inputs = {
        ROOT/"data/external/allen_synphys_r21/synphys_r2.1_small.sqlite": "7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53",
        ROOT/"verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__pipeline__multipatch__cortical_location.py": "72df5c03dc335acddadcffce796765df703944b813ada5f5dd3f826c42b0b2cd",
        ROOT/"verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__layer_depths.py": "53bb97c5a145763600efe5012b5f5ac9201433d97345e892d1adc40c4f5d805f",
        HERE/"allen_sources/aisynphys__data__experiment.py": "9328c58dd5f4e928819b5d5e7c4ac6f104c5c6d060f1e41efc3017d5d256d8e6",
        HERE/"allen_sources/aisynphys__pipeline__multipatch__experiment.py": "7861fd4fb11a37174120c9d6f07f49d8e7301fbfa2d35b0ed2b8512e3880f938",
    }
    for path, expected in inputs.items():
        assert sha(path) == expected, path
    db = next(iter(inputs))
    with sqlite3.connect(db.resolve().as_uri()+"?mode=ro", uri=True) as con:
        rows = con.execute("""SELECT c.experiment_id,c.id,c.position,l.position,l.distance_to_pia,l.cortical_layer
            FROM cell c JOIN cortical_cell_location l ON l.cell_id=c.id
            JOIN experiment e ON e.id=c.experiment_id JOIN slice s ON s.id=e.slice_id
            WHERE s.species='mouse' AND e.target_region='VisP' ORDER BY c.experiment_id,c.id""").fetchall()
        site_rows = con.execute("SELECT COUNT(*) FROM cortical_site").fetchone()[0]
    groups = {}; invalid = []; large_2d = []
    for experiment, cid, raw3, raw2, depth, layer in rows:
        x = point(raw3, 3); u = point(raw2, 2)
        if x is None or u is None:
            invalid.append(cid); continue
        finite_depth = depth is not None and np.isfinite(depth)
        record = dict(cell_id=cid, position_3D_um=(x*1e6).tolist(), position_2D_um=(u*1e6).tolist(),
                      depth_um=float(depth*1e6) if finite_depth else None, layer=layer)
        groups.setdefault(experiment, []).append(record)
        if np.max(abs(u)) > 1:  # Only a source-diagnostic flag, not a repair or fitting exclusion.
            large_2d.append(dict(experiment_id=experiment, **record))
    excluded = []; results = []
    for experiment, cells in groups.items():
        if len(cells) < 5:
            excluded.append(dict(experiment_id=experiment, n=len(cells), reason="fewer_than_5_matched_cells")); continue
        x = np.array([r["position_3D_um"] for r in cells]); u = np.array([r["position_2D_um"] for r in cells])
        span3 = float(np.max(np.linalg.norm(x[:, None]-x[None, :], axis=2)))
        span2 = float(np.max(np.linalg.norm(u[:, None]-u[None, :], axis=2)))
        if not (0 < span3 <= 1000 and 0 < span2 <= 2000):
            excluded.append(dict(experiment_id=experiment, n=len(cells), reason="outside_exploratory_local_span", span3_um=span3, span2_um=span2)); continue
        results.append(evaluate(experiment, cells))
    common = [r for r in results if all(r["models"][m]["all_loo_identifiable"] for m in MODELS)]
    scores = {}
    for model in MODELS:
        errors = np.concatenate([r["models"][model]["loo_error_um"] for r in common])
        scores[model] = dict(common_experiments=len(common), common_cells=len(errors),
            cell_pooled_rmse_um=float(np.sqrt(np.mean(errors**2))), cell_error_quantiles_um=quantiles(errors),
            experiment_rmse_quantiles_um=quantiles([r["models"][model]["loo_rmse_um"] for r in common]),
            experiments_max_error_le_1um=sum(r["models"][model]["loo_max_error_um"] <= 1 for r in common),
            experiments_max_error_le_5um=sum(r["models"][model]["loo_max_error_um"] <= 5 for r in common))
    depth_rows = [r for r in common if r["depth"]["status"] != "not_evaluated"]
    summary = dict(raw_joined_cells=len(rows), invalid_positions=len(invalid), matched_cells=sum(map(len, groups.values())),
        matched_experiments=len(groups), cortical_site_rows=site_rows,
        extreme_2D_coordinate_cells=len(large_2d), extreme_2D_all_missing_depth=all(r["depth_um"] is None for r in large_2d),
        exclusion_counts=dict(Counter(r["reason"] for r in excluded)), analyzed_experiments=len(results),
        common_identifiable_experiments=len(common), common_identifiable_cells=sum(r["n"] for r in common), scores=scores,
        max_loo_3D_condition_quantiles=quantiles([max(s["condition"] for s in r["loo_3D_spectra"]) for r in common]),
        depth_experiments=len(depth_rows), depth_rmse_quantiles_um=quantiles([r["depth"]["loo_rmse_um"] for r in depth_rows]),
        depth_max_angle_quantiles_deg=quantiles([r["depth"]["max_loo_angle_deg"] for r in depth_rows if r["depth"]["max_loo_angle_deg"] is not None]),
        xy_similarity_full_scale_quantiles=quantiles([r["models"]["xy_similarity"]["full_fit"]["scale"] for r in common]),
        xyz_B_z_fraction_quantiles=quantiles([r["pullback"]["B_z_row_over_Frobenius"] for r in common if r["pullback"] is not None]))
    output = dict(version="allen-cortical-registration-audit-v1", code_sha256=sha(Path(__file__)),
        input_sha256={p.relative_to(ROOT).as_posix():v for p,v in inputs.items()},
        settings=dict(minimum_cells=5, maximum_3D_span_um=1000, maximum_2D_span_um=2000, rank_rcond=RCOND,
            model_names=MODELS, selection_timing="Exploratory geometry inspection preceded these development domain choices",
            geometric_error_thresholds="1 and 5 um are descriptive summaries, not independent physical calibration gates",
            xyz_affine_not_scaled_orthographic=True, raw_coordinate_rescaling=False, connection_labels_queried=False),
        summary=summary, invalid_position_cell_ids=invalid, extreme_2D_cells=large_2d, excluded_experiments=excluded, experiments=results,
        claim_ceiling="Coordinate/source audit L0; no independently calibrated 3D pia normals or metric, no new connection-label endpoint")
    with OUTPUT.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
