"""Encoding-assigned candidate identification in processed aggregate M2.

This is not a next-recall, ripple-history, causal, or physical-metric test.
All adaptation uses the author-processed encoding repetitions. Upstream
normalization and M2 event aggregation are not independently reconstructed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.io import loadmat
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parents[3]
MAT = ROOT / 'data/external/hippocampal_reinstatement/norman2019_mvpa_v1/multivariate_pattern_all_visual_channels.mat'
SUPPORT = ROOT / 'data/local/hippocampal-reinstatement/norman-item-support-v1/norman_mvpa_item_support.json'
PINS = {
    MAT: '7c776aafe3a44310e25946a36d7528cef15b7540b956bad69bec2c0e6e89ec70',
    SUPPORT: '933fc9001ea8bdeb28d3e3ff10b7a99d80af4de542006d31c72efb3adb9d1eeb',
}
ALPHAS = np.array([0., 1/16, 1/8, 1/4, 1/2, 1., 2., 4.])


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fit_encoding(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """x: seven items x training repetitions x channels; no target access."""
    assert x.ndim == 3 and x.shape[0] == 7 and x.shape[1] >= 2
    assert np.isfinite(x).all()
    mu = x.mean(axis=1)
    variance = ((x - mu[:, None, :]) ** 2).sum(axis=(0, 1)) / (7 * (x.shape[1] - 1))
    keep = np.isfinite(variance) & (variance > 0)
    if not keep.any():
        raise ValueError('all_encoding_within_item_variances_zero')
    floor = float(np.median(variance[keep]) * 1e-3)
    variance[keep] = np.maximum(variance[keep], floor)
    return mu, variance, keep


def distances(z: np.ndarray, fitted: tuple) -> np.ndarray:
    mu, variance, keep = fitted
    delta = z[:, keep][:, None, :] - mu[:, keep][None, :, :]
    result = .5 * np.sum(delta * delta / variance[keep], axis=2)
    assert np.isfinite(result).all()
    return result


def log_prob(distance: np.ndarray, alpha: float) -> np.ndarray:
    score = -alpha * distance
    return score - logsumexp(score, axis=-1, keepdims=True)


def calibrate(x: np.ndarray) -> tuple[float, list[float], list[int]]:
    # Each fold holds the same repetition number out of all seven items.
    losses = np.zeros(len(ALPHAS))
    dimensions = []
    for held in range(4):
        fitted = fit_encoding(x[:, np.arange(4) != held, :])
        dimensions.append(int(fitted[2].sum()))
        dist = distances(x[:, held, :], fitted)
        for index, alpha in enumerate(ALPHAS):
            losses[index] -= np.diag(log_prob(dist, float(alpha))).sum() / 28
    selected = int(np.flatnonzero(losses <= losses.min() + 1e-12)[0])
    return float(ALPHAS[selected]), losses.tolist(), dimensions


def metrics(rows: list[dict], window: str) -> dict:
    if not rows:
        return dict(items=0, mean_log_gain_nats=None, mean_tie_split_top1=None)
    return dict(items=len(rows),
                mean_log_gain_nats=float(np.mean([r[window]['log_gain_nats'] for r in rows])),
                mean_tie_split_top1=float(np.mean([r[window]['tie_split_top1'] for r in rows])))


def run(output: Path) -> None:
    for path, expected in PINS.items():
        assert sha(path) == expected, f'input drift: {path}'
    support = json.loads(SUPPORT.read_text(encoding='utf-8'))
    names = ['M0singletrial', 'M2', 'I', 'Iall', 'included_subjects', 'included_channels',
             'bin_centers', 'bin_centers_stim']
    data = loadmat(MAT, variable_names=names, simplify_cells=True)
    labels = [str(x) for x in data['I']]
    repeats = [str(x) for x in data['Iall']]
    assert labels == support['global_labels']['I'] and repeats == support['global_labels']['Iall']
    ids = {name: index for index, name in enumerate(labels)}
    rep_ids = {name: index for index, name in enumerate(repeats)}
    times = np.asarray(data['bin_centers']).ravel()
    stim_times = np.asarray(data['bin_centers_stim']).ravel()
    assert np.array_equal(times, np.arange(-525, 526, 10))
    assert np.array_equal(stim_times, np.arange(-225, 2126, 10))
    encoding_mask = (stim_times > 100) & (stim_times <= 500)
    windows = {'pre': (times >= -250) & (times < -50),
               'post': (times > 50) & (times <= 250)}
    assert encoding_mask.sum() == 40 and all(mask.sum() == 20 for mask in windows.values())
    encoding = np.asarray(data['M0singletrial'])[encoding_mask].mean(axis=0).T
    recall = np.asarray(data['M2'])
    assert encoding.shape == (112, 212) and recall.shape == (106, 212, 28)
    assert np.isfinite(encoding).all()
    tasks, observations, records = [], [], []
    counts = dict(raw_candidates=0, unresolved_candidates=0, exact_candidates=0,
                  M2_missing_exact=0, M2_observed_exact=0, evaluated_items=0)
    for rec in support['recordsets']:
        channels = np.asarray(rec['channel_indices_zero_based'], dtype=int)
        assert all(str(data['included_subjects'][ch]) == rec['recordset'] for ch in channels)
        assert [str(data['included_channels'][ch]) for ch in channels] == [r['name'] for r in rec['channels']]
        start = len(observations)
        for run_info in rec['runs']:
            for category, supplied in run_info['M2_support_by_category'].items():
                candidates = [row['raw_label'] for row in supplied['items']]
                counts['raw_candidates'] += len(candidates)
                assert len(candidates) == 7 and len(set(candidates)) == 7
                task = dict(recordset=rec['recordset'], person=rec['person'],
                            encoding_run=run_info['run'], category=category, candidates=candidates)
                tasks.append(task)
                if any(label not in ids for label in candidates):
                    counts['unresolved_candidates'] += 7
                    task['status'] = 'unresolved_raw_id_task'
                    continue
                counts['exact_candidates'] += 7
                x = np.stack([encoding[[rep_ids[f'{label}-{rep}'] for rep in range(1, 5)]][:, channels]
                              for label in candidates])
                available = []
                for supplied_item in supplied['items']:
                    y = recall[:, channels, ids[supplied_item['raw_label']]]
                    if np.isnan(y).all():
                        assert supplied_item['status'] == 'all_channels_nan'
                        counts['M2_missing_exact'] += 1
                        available.append(False)
                    else:
                        assert np.isfinite(y).all() and supplied_item['status'] == 'all_channels_finite'
                        counts['M2_observed_exact'] += 1
                        available.append(True)
                task['M2_observed'] = int(sum(available))
                task['M2_missing'] = 7 - task['M2_observed']
                try:
                    alpha, cv_loss, fold_dimensions = calibrate(x)
                    fitted = fit_encoding(x)
                except ValueError as exc:
                    task['status'] = str(exc)
                    continue
                task.update(status='calibrated', alpha=alpha, calibration_loss=cv_loss,
                            fold_dimensions=fold_dimensions, final_dimensions=int(fitted[2].sum()))
                for true_index, label in enumerate(candidates):
                    if not available[true_index]:
                        continue
                    row = dict(recordset=rec['recordset'], person=rec['person'],
                               encoding_run=run_info['run'], category=category, raw_label=label,
                               candidates=candidates, alpha=alpha)
                    y = recall[:, channels, ids[label]]
                    for window, mask in windows.items():
                        z = y[mask].mean(axis=0)[None, :]
                        lq = log_prob(distances(z, fitted), alpha)[0]
                        q = np.exp(lq)
                        assert np.isclose(q.sum(), 1., atol=1e-12)
                        maxima = np.isclose(lq, lq.max(), rtol=0., atol=1e-12)
                        gain = float(lq[true_index] + math.log(7))
                        top1 = float(maxima[true_index] / maxima.sum())
                        if alpha == 0:
                            assert abs(gain) < 1e-12 and abs(top1 - 1/7) < 1e-12
                        row[window] = dict(probabilities=q.tolist(), log_gain_nats=gain,
                                           tie_split_top1=top1)
                    observations.append(row)
                    counts['evaluated_items'] += 1
        own = observations[start:]
        records.append(dict(recordset=rec['recordset'], person=rec['person'],
                            **{window: metrics(own, window) for window in windows}))
    assert [counts[k] for k in ('raw_candidates','unresolved_candidates','exact_candidates',
                                'M2_missing_exact','M2_observed_exact')] == [448,56,392,188,204]
    persons = []
    for person in sorted({r['person'] for r in records}):
        matched = [r for r in records if r['person'] == person and r['post']['items']]
        if not matched:
            continue
        persons.append(dict(person=person, contributing_recordsets=[r['recordset'] for r in matched],
            **{w: {field: float(np.mean([r[w][field] for r in matched]))
                   for field in ('mean_log_gain_nats','mean_tie_split_top1')} for w in windows}))
    summary = dict(counts=counts, evaluable_persons=len(persons),
        **{w: dict(person_mean_log_gain_nats=float(np.mean([p[w]['mean_log_gain_nats'] for p in persons])) if persons else None,
                   person_mean_tie_split_top1=float(np.mean([p[w]['mean_tie_split_top1'] for p in persons])) if persons else None,
                   positive_persons=sum(p[w]['mean_log_gain_nats'] > 0 for p in persons)) for w in windows})
    report = dict(schema='ce.norman.aggregate-item-template-transfer.v1',
        inputs={str(p.relative_to(ROOT)): expected for p, expected in PINS.items()}, source_sha256=sha(Path(__file__)),
        environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
        method=dict(distance='0.5 * sum_channel((z-mu_k)^2 / pooled_within_item_variance)',
                    posterior='softmax(-alpha * distance)', variance_floor='median_positive_variance * 0.001',
                    alpha_grid=ALPHAS.tolist(), alpha_scope='each encoding-assigned run/category task',
                    calibration='four leave-one-repetition-out folds; all estimators refit from three training repetitions',
                    aggregation='item mean within recordset, recordset mean within person, equal-person mean',
                    encoding_bins_ms=stim_times[encoding_mask].tolist(),
                    evaluation_bins_ms={w: times[mask].tolist() for w, mask in windows.items()}, primary_window='post'),
        summary=summary, tasks=tasks, observations=observations, recordsets=records, persons=persons,
        limits=['Retrospective identification in aggregate M2 conditional on M2 availability; not next recall or ripple-history prediction.',
                'Candidate run is the encoding-assigned run; actual recall event/run membership is not available.',
                'Upstream preprocessing and event aggregation are not reconstructed; encoding CV is calibration on provided processed features.',
                'No best-time selection, target tuning, p-values, independent-item inference, causal pre/post contrast, or physical metric claim.'])
    output.mkdir(parents=True, exist_ok=False)
    result = output / 'norman_item_template_transfer.json'
    with result.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    manifest = dict(source=dict(path=str(Path(__file__)), bytes=Path(__file__).stat().st_size, sha256=sha(Path(__file__))),
                    result=dict(path=str(result), bytes=result.stat().st_size, sha256=sha(result)))
    with (output / 'manifest.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(summary=summary, persons=persons, manifest=manifest), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    run(parser.parse_args().output_dir)
