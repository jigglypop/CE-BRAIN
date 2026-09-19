"""Fixed retrospective CML item-associated HFA readout, not an online decoder.

No recall-based feature, channel, time-window or temperature selection. The four
candidates use the known recalled list/category. Content and temporal context
are not identified separately. Native event alignment remains an assumption.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
META = ROOT / 'data/external/hippocampal_reinstatement/cml_catfr1_metadata_v1/responses'
PROBE = ROOT / 'data/external/hippocampal_reinstatement/cml_catfr1_edf_probe_v1'
FS = 1600
BETA_PREFERENCE = (0., -1., 1., -2., 2., -4., 4.)
CONFIG = dict(encoding_window_samples=[400, 1200], recall_window_samples=[-1600, -800],
              frequency_hz=[70, 150], exclude_120hz_distance_le=2, alpha=1,
              baseline_subtraction=False, feature='log integrated Hann periodogram power',
              scale='all 40 encoding rows only; population SD; drop SD<=1e-12',
              beta_preference=list(BETA_PREFERENCE), beta_fit='equal-list loss outside held list',
              repeat_policy='first correct same-list item, before other eligibility guards',
              prior_speech_gap_samples_must_exceed=1600,
              primary='equal-list mean log(q1_true/q0_true)',
              q0='softmax(beta*(serialpos-6.5)/6)', q1='softmax(log q0 + cosine)',
              channel_rule='all existing bipolar ECOG pairs with two mono ECOG components')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def log_hfa(samples):
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 800 or not np.isfinite(x).all():
        raise ValueError('finite channel-by-800 sample matrix required')
    window = np.hanning(800)
    transformed = np.fft.rfft((x - x.mean(axis=1, keepdims=True)) * window, axis=1)
    f = np.fft.rfftfreq(800, 1 / FS)
    keep = (f >= 70) & (f < 150) & (np.abs(f - 120) > 2)
    # All selected bins are non-DC and non-Nyquist; one-sided PSD factor is two.
    power = 2 * np.square(np.abs(transformed[:, keep])).sum(axis=1) / (FS * np.square(window).sum()) * (FS / 800)
    if np.any(power <= 0) or not np.isfinite(power).all():
        raise ValueError('nonpositive/nonfinite HFA power; do not silently impute')
    return np.log(power)


def encoding_scale(features):
    x = np.asarray(features, dtype=float)
    if x.ndim != 2 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError('finite encoding feature matrix required')
    center, scale = x.mean(axis=0), x.std(axis=0)
    keep = scale > 1e-12
    if not keep.any():
        raise ValueError('no varying encoding features')
    return center, scale, keep


def standardized(x, center, scale, keep):
    y = (np.asarray(x, dtype=float)[..., keep] - center[keep]) / scale[keep]
    if not np.isfinite(y).all():
        raise ValueError('nonfinite standardized feature')
    return y


def cosine_scores(query, candidates):
    query, candidates = np.asarray(query, float), np.asarray(candidates, float)
    if candidates.shape != (4, query.size) or not np.isfinite(query).all() or not np.isfinite(candidates).all():
        raise ValueError('four finite candidate vectors required')
    qnorm, norms = np.linalg.norm(query), np.linalg.norm(candidates, axis=1)
    denominator = qnorm * norms
    return np.divide(candidates @ query, denominator, out=np.zeros(4), where=denominator > 0).clip(-1, 1)


def log_softmax(values):
    x = np.asarray(values, float)
    if x.shape != (4,) or not np.isfinite(x).all():
        raise ValueError('four finite logits required')
    x = x - x.max()
    return x - np.log(np.exp(x).sum())


def equal_list_mean(values, lists):
    values, lists = np.asarray(values, float), np.asarray(lists)
    if values.shape != lists.shape or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError('nonempty finite aligned scores required')
    return float(np.mean([values[lists == key].mean() for key in np.unique(lists)]))


def select_beta(rows, held_list):
    training = [r for r in rows if r['list'] != held_list]
    if not training:
        raise ValueError('no outside-list prior training rows')
    losses = []
    for beta in BETA_PREFERENCE:
        loss = [-log_softmax(beta * (np.asarray(r['serialpos']) - 6.5) / 6)[r['true_index']] for r in training]
        losses.append(equal_list_mean(loss, [r['list'] for r in training]))
    # Stable first minimum implements the stated preference, without a fitted tolerance.
    index = int(np.argmin(losses))
    return BETA_PREFERENCE[index], dict(training_event_rows=[r['row'] for r in training],
        training_lists=sorted(set(r['list'] for r in training)), losses=losses,
        preference=list(BETA_PREFERENCE), beta=BETA_PREFERENCE[index])


def score_rows(rows):
    scored = []
    for row in rows:
        beta, fit = select_beta(rows, row['list'])
        logq0 = log_softmax(beta * (np.asarray(row['serialpos']) - 6.5) / 6)
        logq1 = log_softmax(logq0 + np.asarray(row['cosine']))
        k = row['true_index']
        ties = np.flatnonzero(logq1 == logq1.max())
        scored.append(dict(**row, prior_fit=fit, logq0=logq0.tolist(), logq1=logq1.tolist(),
            incremental_log_gain=float(logq1[k] - logq0[k]),
            uniform_log_gain=float(logq1[k] + np.log(4)),
            prior_uniform_log_gain=float(logq0[k] + np.log(4)),
            true_rank_mid=float(1 + np.sum(logq1 > logq1[k]) + .5 * (np.sum(logq1 == logq1[k]) - 1)),
            top1_credit=float(1 / len(ties) if k in ties else 0)))
    metrics = ('incremental_log_gain', 'uniform_log_gain', 'prior_uniform_log_gain', 'true_rank_mid', 'top1_credit')
    summary = {m: dict(equal_list=equal_list_mean([r[m] for r in scored], [r['list'] for r in scored]),
                       equal_item=float(np.mean([r[m] for r in scored]))) for m in metrics}
    return scored, summary


def table(pattern):
    paths = list(META.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f'ambiguous metadata: {pattern}')
    with paths[0].open(encoding='utf-8-sig', newline='') as stream:
        return paths[0], list(csv.DictReader(stream, delimiter='\t'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--record-index', type=Path, required=True, help='JSON with rawblocks: path, first_record, record_count, bytes, sha256')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if sha(args.plan) != 'ccd2cf570ead661699e1f6f283d5e9abd4adb72fa0fe76159fca1c1cbfb43adf':
        raise ValueError('input plan changed')
    plan = json.loads(args.plan.read_text(encoding='utf-8'))
    index = json.loads(args.record_index.read_text(encoding='utf-8'))
    events_path, events = table('*events.tsv')
    mono_path, mono = table('*acq-monopolar_channels.tsv')
    bipolar_path, bipolar = table('*acq-bipolar_channels.tsv')
    if sha(events_path) != 'ee70a1e2170eaa5ea4bfd0ac39f3a208f072b7ebd03ccad3cef44e4bf9a08ba0':
        raise ValueError('event table changed')
    if sha(mono_path) != '1120fe4251c93bfe25b5f75dc28d3b6ec735e365edc13964719b78a58f6a2ea3' or sha(bipolar_path) != '38461ff8e43acccb9a34628c5941235259b89b005e8d45f7f8dc4d91c8c8c502':
        raise ValueError('channel metadata changed')
    by_name = {r['name']: r for r in mono}
    pairs = []
    for row in bipolar:
        parts = row['name'].split('-')
        if row['type'] == 'ECOG' and len(parts) == 2 and all(by_name[v]['type'] == 'ECOG' for v in parts):
            pairs.append(parts)
    labels = [r['name'] for r in mono]
    pair_indices = np.array([[labels.index(v) for v in pair] for pair in pairs])
    parser_path = Path(__file__).with_name('cml_edf_records.py')
    if sha(parser_path) != '07dba354b4411b3d16bb9c161b8af3c0906f4c60f2e9619c1ad6d8a9165817f5':
        raise ValueError('EDF parser changed')
    spec = importlib.util.spec_from_file_location('cml_edf_records_fixed', parser_path)
    reader = importlib.util.module_from_spec(spec); spec.loader.exec_module(reader)
    fixed, rest = PROBE/'header_fixed_0_255.bin', PROBE/'header_rest.bin'
    if sha(fixed) != '28f16a01465f0ef4bfae1da9fd6bdec5b691cd394fa8b70decd5645025818a83' or sha(rest) != '216cd632bc6fdaf28556a9974e39fabd4502ad277bb6e1b0d1d0b505a197b459':
        raise ValueError('EDF header changed')
    header = reader.parse_header(fixed.read_bytes() + rest.read_bytes())
    blocks, record_map, pins = [], {}, []
    for block in index['rawblocks']:
        path = Path(block['path'])
        if not path.is_absolute():
            path = args.record_index.parent / path
        if path.stat().st_size != block['bytes'] or sha(path) != block['sha256']:
            raise ValueError('rawblock pin mismatch')
        raw = path.read_bytes()
        if len(raw) != block['record_count'] * header['record_bytes']:
            raise ValueError('rawblock record count mismatch')
        dec = reader.decode_records(header, raw, block['first_record'], labels)
        if set(dec['units']) != {'uV'} or dec['sample_rate_hz'] != FS:
            raise ValueError('unexpected units or sample rate')
        for j in range(block['record_count']):
            rec = block['first_record'] + j
            if rec in record_map:
                raise ValueError('duplicate raw record')
            record_map[rec] = raw[j * header['record_bytes']:(j + 1) * header['record_bytes']]
        pins.append(dict(path=str(path), bytes=path.stat().st_size, sha256=block['sha256']))
    def feature(sample, interval):
        start, stop = sample + interval[0], sample + interval[1]
        span = reader.record_span(header, labels[0], start, stop)
        packed = b''.join(record_map[r] for r in range(span['first_record'], span['first_record'] + span['record_count']))
        dec = reader.decode_records(header, packed, span['first_record'], labels)
        x = reader.sample_interval(dec, start, stop)
        return log_hfa(x[pair_indices[:, 0]] - x[pair_indices[:, 1]])
    selections = plan['selection']['rows']
    enc = {w['row_zero_based']: w for row in selections for w in row['candidate_word_rows']}
    if len(enc) != 40:
        raise ValueError('encoding denominator changed')
    enc_ids = sorted(enc)
    enc_features = np.stack([feature(enc[i]['sample'], CONFIG['encoding_window_samples']) for i in enc_ids])
    center, scale, keep = encoding_scale(enc_features)
    templates = dict(zip(enc_ids, standardized(enc_features, center, scale, keep)))
    rows, excluded, seen = [], [], set()
    for item in sorted(selections, key=lambda r:r['recall']['row_zero_based']):
        recall, candidates = item['recall'], item['candidate_word_rows']
        rid, sample, list_id = recall['row_zero_based'], recall['sample'], recall['list']
        event = events[rid]
        if event['trial_type'] != 'REC_WORD' or int(event['sample']) != sample or event['item_name'] != recall['item']:
            raise ValueError('recall metadata identity mismatch')
        key = (list_id, recall['item'])
        reasons = ['repeat'] if key in seen else []
        seen.add(key)
        prior = [int(r['sample']) for r in events[:rid] if r['trial_type'] in ('REC_WORD', 'REC_WORD_VV')]
        gap = sample - max(prior) if prior else None
        if gap is not None and gap <= 1600:
            reasons.append('prior_speech_gap_le_1s')
        starts = [int(r['sample']) for r in events[:rid] if r['trial_type']=='REC_START' and int(r['list'])==list_id]
        if len(starts) != 1:
            raise ValueError('ambiguous recall phase')
        if sample - 1600 < starts[0]:
            reasons.append('window_before_recall_start')
        if reasons:
            excluded.append(dict(row=rid, reasons=reasons, prior_speech_gap_samples=gap)); continue
        cids = [w['row_zero_based'] for w in candidates]
        query = standardized(feature(sample, CONFIG['recall_window_samples']), center, scale, keep)
        sims = cosine_scores(query, np.stack([templates[i] for i in cids]))
        rows.append(dict(row=rid, list=list_id, item=recall['item'], category=recall['category'],
            candidate_rows=cids, candidate_items=[w['item'] for w in candidates],
            serialpos=[w['serialpos'] for w in candidates], true_index=cids.index(item['true_candidate_row_zero_based']),
            prior_speech_gap_samples=gap, cosine=sims.tolist()))
    if len(rows) != 12:
        raise ValueError('eligible denominator changed')
    scored, summary = score_rows(rows)
    all_inputs = [args.plan, args.record_index, events_path, mono_path, bipolar_path, parser_path, fixed, rest, Path(__file__)]
    result = dict(schema='ce.cml.withincategory.readout.v1', config=CONFIG,
        inputs=[dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p)) for p in all_inputs], rawblocks=pins,
        encoding_rows=enc_ids, pairs=pairs, varying_pairs=int(keep.sum()),
        encoding_center=center.tolist(), encoding_scale=scale.tolist(), encoding_keep=keep.tolist(),
        denominator=dict(events=len(scored), lists=len(set(r['list'] for r in scored)), subjects=1, sessions=1),
        excluded=excluded, rows=scored, summary=summary,
        limits=['Conditional native sample alignment; no independent behavioral synchronization.',
                'Known true list and category; retrospective identification, not next-item prediction.',
                'HFA/cosine can reflect item or temporal context and has no causal interpretation.',
                'Single-session candidate measurement; not ripple detection, learned physical metric or whole brain state.'])
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    np.savez_compressed(args.output/'encoding_features.npz', rows=np.array(enc_ids), log_hfa=enc_features)
    (args.output/'manifest.json').write_text(json.dumps(dict(files=[dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p))
        for p in sorted(args.output.iterdir())]), indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(denominator=result['denominator'], summary=summary, result_sha256=sha(args.output/'result.json'))))


if __name__ == '__main__':
    main()
