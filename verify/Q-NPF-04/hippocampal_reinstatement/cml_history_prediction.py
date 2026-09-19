"""Retrospective held-list prediction of cortical HFA from strictly past bins.

This measures a fixed predictor's incremental marginal log score, not directed
physical causality, item reinstatement, ripple timing, or a neuronal metric.
The raw-record cohort was selected around subsequently known memory events.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FS, BIN, LAGS, RIDGE = 1600, 800, 4, 1.0
MODELS = ('c_current', 'c_history', 'c_history_h_current',
          'c_history_h_history', 'c_history_control_history')
HIPPOCAMPAL = ['LOTD2-LOTD3', 'LOTD3-LOTD4', 'LOTD4-LOTD5', 'LOTD5-LOTD6']


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pinned_module(name, filename, expected):
    path = Path(__file__).with_name(filename)
    if sha(path) != expected:
        raise ValueError(f'changed dependency: {filename}')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def list_weights(lists):
    lists = np.asarray(lists)
    keys, counts = np.unique(lists, return_counts=True)
    if not len(keys):
        raise ValueError('no training lists')
    return np.array([1.0 / (len(keys) * counts[np.flatnonzero(keys == key)[0]])
                     for key in lists])


def weighted_scale(values, weights):
    values, weights = np.asarray(values, float), np.asarray(weights, float)
    if (values.ndim != 2 or weights.shape != (len(values),)
            or not np.isfinite(values).all() or np.any(weights <= 0)
            or not np.isclose(weights.sum(), 1.0)):
        raise ValueError('finite matrix and positive normalized weights required')
    center = weights @ values
    scale = np.sqrt(weights @ np.square(values - center))
    return center, scale


def fit_predict(x_train, y_train, x_test, weights, ridge=RIDGE):
    """Minimize list-weighted standardized squared loss + ridge * ||B||^2."""
    if ridge <= 0:
        raise ValueError('positive fixed ridge required')
    xm, xs = weighted_scale(x_train, weights)
    ym, ys = weighted_scale(y_train, weights)
    if np.any(ys <= 1e-12):
        raise ValueError('constant training target; no silent target selection')
    keep = xs > 1e-12
    z = (x_train[:, keep] - xm[keep]) / xs[keep]
    y = (y_train - ym) / ys
    root_weights = np.sqrt(weights)[:, None]
    xw, yw = z * root_weights, y * root_weights
    if xw.shape[1] <= xw.shape[0]:
        b = np.linalg.solve(xw.T @ xw + ridge * np.eye(xw.shape[1]), xw.T @ yw)
    else:
        b = xw.T @ np.linalg.solve(xw @ xw.T + ridge * np.eye(xw.shape[0]), yw)
    prediction = ym + ((x_test[:, keep] - xm[keep]) / xs[keep]) @ b * ys
    coefficient = np.zeros((x_train.shape[1], y_train.shape[1]))
    coefficient[keep] = b
    return prediction, dict(x_center=xm, x_scale=xs, x_keep=keep,
                            y_center=ym, y_scale=ys, coefficient=coefficient)


def make_design(features, run_ids, lists, starts, n_cortex, n_hip=4, n_control=4):
    """Keep every complete 4-past-bin/next-bin row; never cross a native gap."""
    features = np.asarray(features, float)
    run_ids, lists, starts = map(np.asarray, (run_ids, lists, starts))
    if (features.ndim != 2 or features.shape[1] != n_cortex + n_hip + n_control
            or not np.isfinite(features).all()
            or any(v.shape != (len(features),) for v in (run_ids, lists, starts))):
        raise ValueError('aligned finite feature rows required')
    if len(np.unique(starts)) != len(starts):
        raise ValueError('duplicate native bins')
    rows, histories = [], []
    for i in range(LAGS, len(features)):
        past = np.arange(i - 1, i - LAGS - 1, -1)
        span = np.arange(i - LAGS, i + 1)
        if len(np.unique(run_ids[span])) != 1:
            continue
        if len(np.unique(lists[span])) != 1:
            raise ValueError('list boundary inside a continuous run')
        if not np.all(np.diff(starts[span]) == BIN):
            continue
        rows.append(i)
        histories.append(past)
    if not rows:
        raise ValueError('no complete forecast rows')
    rows, histories = np.asarray(rows), np.asarray(histories)
    past = features[histories]
    c = past[:, :, :n_cortex].reshape(len(rows), -1)
    h = past[:, :, n_cortex:n_cortex+n_hip]
    control = past[:, :, n_cortex+n_hip:]
    designs = dict(c_current=past[:, 0, :n_cortex], c_history=c,
                   c_history_h_current=np.concatenate((c, h[:, 0]), axis=1),
                   c_history_h_history=np.concatenate((c, h.reshape(len(rows), -1)), axis=1),
                   c_history_control_history=np.concatenate((c, control.reshape(len(rows), -1)), axis=1))
    return dict(designs=designs, targets=features[rows, :n_cortex],
                rows=rows, histories=histories, lists=lists[rows],
                runs=run_ids[rows], starts=starts[rows])


def evaluate(design):
    y, lists = design['targets'], design['lists']
    predictions = {name: np.empty_like(y) for name in MODELS}
    errors = {name: np.empty_like(y) for name in ('training_mean',) + MODELS}
    folds, arrays = [], {}
    if len(np.unique(lists)) < 3:
        raise ValueError('at least three held-list folds required')
    for held in np.unique(lists):
        train, test = np.flatnonzero(lists != held), np.flatnonzero(lists == held)
        weights = list_weights(lists[train])
        ym, ys = weighted_scale(y[train], weights)
        if np.any(ys <= 1e-12):
            raise ValueError('constant training target')
        errors['training_mean'][test] = np.square((y[test] - ym) / ys)
        fold = dict(held_list=int(held), train_rows=train.tolist(), test_rows=test.tolist(),
                    train_lists=np.unique(lists[train]).astype(int).tolist(), models={})
        arrays[f'fold_{held}_weights'] = weights
        arrays[f'fold_{held}_y_center'] = ym
        arrays[f'fold_{held}_y_scale'] = ys
        for name in MODELS:
            x = design['designs'][name]
            pred, params = fit_predict(x[train], y[train], x[test], weights)
            predictions[name][test] = pred
            errors[name][test] = np.square((y[test] - pred) / ys)
            fold['models'][name] = dict(features=x.shape[1], varying_features=int(params['x_keep'].sum()),
                                       standardized_mse=float(errors[name][test].mean()))
            for key, value in params.items():
                arrays[f'fold_{held}_{name}_{key}'] = value
        folds.append(fold)
    contrasts = dict(cortical_history=('c_current', 'c_history'),
                     hippocampal_current=('c_history', 'c_history_h_current'),
                     hippocampal_history=('c_history', 'c_history_h_history'),
                     hippocampal_older_history=('c_history_h_current', 'c_history_h_history'),
                     control_history=('c_history', 'c_history_control_history'),
                     hippocampal_vs_control=('c_history_control_history', 'c_history_h_history'))
    summary = {}
    for name, (baseline, candidate) in contrasts.items():
        gains = 0.5 * (errors[baseline] - errors[candidate]).mean(axis=1)
        by_list = {str(int(key)): float(gains[lists == key].mean()) for key in np.unique(lists)}
        summary[name] = dict(baseline=baseline, candidate=candidate,
                             equal_list=float(np.mean(list(by_list.values()))),
                             equal_bin=float(gains.mean()), by_list=by_list)
        arrays[f'gain_{name}'] = gains
    for name, values in predictions.items():
        arrays[f'prediction_{name}'] = values
    for name, values in errors.items():
        arrays[f'squared_error_{name}'] = values
    return dict(folds=folds, contrasts=summary,
                model_mse_equal_list={name: float(np.mean([v[lists == key].mean() for key in np.unique(lists)]))
                                      for name, v in errors.items()}), arrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--support', type=Path, required=True)
    parser.add_argument('--record-index', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('use a new output directory; no replacement or retuning')
    support = json.loads(args.support.read_text(encoding='utf-8-sig'))
    index = json.loads(args.record_index.read_text(encoding='utf-8-sig'))
    old = pinned_module('cml_fixed_content_helpers', 'cml_withincategory_readout.py',
                        '90f97372e56072e9774ea390d95a60a2385fa97c183d940263c3bb54b64ebe0f')
    reader = pinned_module('cml_fixed_edf_helpers', 'cml_edf_records.py',
                           '07dba354b4411b3d16bb9c161b8af3c0906f4c60f2e9619c1ad6d8a9165817f5')
    mono_path, mono = old.table('*acq-monopolar_channels.tsv')
    bip_path, bipolar = old.table('*acq-bipolar_channels.tsv')
    if sha(mono_path) != '1120fe4251c93bfe25b5f75dc28d3b6ec735e365edc13964719b78a58f6a2ea3':
        raise ValueError('changed monopolar table')
    if sha(bip_path) != '38461ff8e43acccb9a34628c5941235259b89b005e8d45f7f8dc4d91c8c8c502':
        raise ValueError('changed bipolar table')
    labels = [row['name'] for row in mono]
    types = {row['name']: row['type'] for row in mono}
    cortex = [row['name'] for row in bipolar if row['type'] == 'ECOG'
              and all(types[part] == 'ECOG' for part in row['name'].split('-'))]
    controls = support['control_pairs']
    if len(cortex) != 140 or len(controls) != 4 or len(set(controls)) != 4:
        raise ValueError('unexpected pair support')
    hip_contacts = set('-'.join(HIPPOCAMPAL).split('-'))
    names = {row['name'] for row in bipolar}
    for pair in HIPPOCAMPAL + controls:
        parts = pair.split('-')
        if pair not in names or len(parts) != 2 or any(types[p] != 'SEEG' for p in parts):
            raise ValueError('invalid depth pair')
        if pair in controls and hip_contacts.intersection(parts):
            raise ValueError('depth control shares a hippocampal contact')
    pairs = cortex + HIPPOCAMPAL + controls
    indices = np.array([[labels.index(part) for part in pair.split('-')] for pair in pairs])
    fixed, rest = old.PROBE / 'header_fixed_0_255.bin', old.PROBE / 'header_rest.bin'
    if sha(fixed) != '28f16a01465f0ef4bfae1da9fd6bdec5b691cd394fa8b70decd5645025818a83' or sha(rest) != '216cd632bc6fdaf28556a9974e39fabd4502ad277bb6e1b0d1d0b505a197b459':
        raise ValueError('changed EDF header')
    header = reader.parse_header(fixed.read_bytes() + rest.read_bytes())
    raw_records, pins = {}, []
    for block in index['rawblocks']:
        path = Path(block['path'])
        if not path.is_absolute():
            path = args.record_index.parent / path
        if path.stat().st_size != block['bytes'] or sha(path) != block['sha256']:
            raise ValueError('changed raw block')
        raw = path.read_bytes()
        if len(raw) != block['record_count'] * header['record_bytes']:
            raise ValueError('invalid rawblock length')
        pins.append(dict(path=str(path), bytes=len(raw), sha256=block['sha256']))
        for offset in range(block['record_count']):
            rec = block['first_record'] + offset
            if rec in raw_records:
                raise ValueError('duplicate record')
            raw_records[rec] = raw[offset*header['record_bytes']:(offset+1)*header['record_bytes']]
    features, run_ids, lists, starts, seen = [], [], [], [], set()
    if len({run['run_id'] for run in support['runs']}) != len(support['runs']):
        raise ValueError('duplicate run identity')
    for run in support['runs']:
        recs = range(run['first_record'], run['first_record'] + run['record_count'])
        if seen.intersection(recs):
            raise ValueError('duplicate run support')
        seen.update(recs)
        decoded = reader.decode_records(header, b''.join(raw_records[r] for r in recs),
                                        run['first_record'], labels)
        if decoded['sample_rate_hz'] != FS or set(decoded['units']) != {'uV'}:
            raise ValueError('unsupported signal clock/units')
        if (run['start_sample'] != decoded['first_sample'] or run['stop_sample'] != decoded['stop_sample']
                or decoded['values'].shape[1] % BIN != 0):
            raise ValueError('run boundaries disagree with native bins')
        diffs = decoded['values'][indices[:, 0]] - decoded['values'][indices[:, 1]]
        for j in range(diffs.shape[1] // BIN):
            features.append(old.log_hfa(diffs[:, j*BIN:(j+1)*BIN]))
            run_ids.append(run['run_id'])
            lists.append(run['list'])
            starts.append(decoded['first_sample'] + j * BIN)
    excluded = set()
    for run in support['excluded_runs']:
        recs = set(range(run['first_record'], run['first_record'] + run['record_count']))
        if seen.intersection(recs) or excluded.intersection(recs) or not run['reason']:
            raise ValueError('overlapping or unexplained excluded records')
        excluded.update(recs)
    if seen | excluded != set(raw_records):
        raise ValueError('analyzed and excluded runs must partition all held records')
    features, run_ids, lists, starts = map(np.asarray, (features, run_ids, lists, starts))
    design = make_design(features, run_ids, lists, starts, len(cortex))
    if len(design['targets']) != sum(run['forecast_rows'] for run in support['runs']):
        raise ValueError('metadata forecast denominator mismatch')
    result, arrays = evaluate(design)
    result.update(schema='ce.cml.history-prediction.v1',
                  runtime=dict(python=sys.version, executable=sys.executable, numpy=np.__version__, platform=platform.platform()),
                  config=dict(bin_samples=BIN, sampling_hz=FS, past_bins=LAGS, fixed_ridge=RIDGE,
                              primary='hippocampal_history equal-list marginal Gaussian log gain per cortical pair',
                              training='equal-list weighted center, population SD, and ridge loss; held list excluded',
                              covariance='common target training SD for every model; marginal scores, not measured joint covariance',
                              features='same frozen 70<=f<150Hz log-Hann power; no 120Hz +/-2; no cross-bin filtering',
                              prior_exposure='single pair raw plot and previous cohort content features/scores observed; exploratory new endpoint'),
                  denominator=dict(subjects=1, sessions=1, lists=len(np.unique(design['lists'])),
                                   continuous_runs=len(support['runs']), analyzed_records=len(seen),
                                   held_records=len(raw_records), excluded_records=len(excluded),
                                   bins=len(features), forecast_rows=len(design['targets']), cortical_pairs=len(cortex)),
                  pairs=dict(cortex=cortex, hippocampal=HIPPOCAMPAL, control=controls),
                  excluded_runs=support['excluded_runs'], rawblocks=pins,
                  inputs=[dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))
                          for path in (args.support, args.record_index, Path(__file__), mono_path, bip_path,
                                       Path(old.__file__), Path(reader.__file__), fixed, rest)],
                  limits=['retrospective event-selected cohort and other-list calibration, not prospective online performance',
                          'marginal prediction gain is not causal, item-specific, ripple, phase, physical-cost or metric evidence',
                          'overlapping histories and shared contacts are not independent replicates',
                          'unmeasured common input, pathological activity, speech and nonstationarity remain possible'])
    arrays.update(features=features, bin_run=run_ids, bin_list=lists, bin_start=starts,
                  target_rows=design['rows'], history_rows=design['histories'],
                  target_list=design['lists'], target_run=design['runs'], target_start=design['starts'],
                  observed_target=design['targets'])
    args.output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(args.output / 'predictions.npz', **arrays)
    (args.output / 'result.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    manifest = [dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p))
                for p in sorted(args.output.iterdir()) if p.is_file()]
    (args.output / 'manifest.json').write_text(json.dumps(dict(files=manifest), indent=2), encoding='utf-8')
    print(json.dumps(dict(denominator=result['denominator'], contrasts=result['contrasts']), allow_nan=False))


if __name__ == '__main__':
    main()
