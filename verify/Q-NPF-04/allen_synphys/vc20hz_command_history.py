"""Retrospective conditional current prediction from held-out VC commands.

Templates are fitted only to the initial eight pulses of sweeps 2 and 3.
No AP, synaptic efficacy, membrane capacitance, or physical metric is inferred.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT_SHA = '2f22c6fad05f33ee03ae5d6d39f56d706c883da2207b057692295d8ff333b087'
STATE_SHA = '6880651a236236d1f80576b228f03131b34d158f454541e31dae07ac82ab3e85'
TRAIN = (2, 3)
TAUS = (.05, .15, .5, 1.5)
FS = 100000
BIN = 50
PRE = np.arange(-1000, -200, BIN)
RESPONSE = np.arange(200, 4000, BIN)
POLICIES = ('level', 'linear')
TARGETS = {'positive': 'AD8', 'negative': 'AD2'}
COHORTS = {'training': (2, 3), 'later_same_command': (4,),
           'later_sweeps_5_6': (5, 6), 'earlier_lower_source_command': (0, 1)}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bin_means(current, events, offsets, samples=BIN):
    current = np.asarray(current, float)
    indices = np.asarray(events, int)[:, None, None]+np.asarray(offsets, int)[None, :, None]+np.arange(samples)
    if indices.min() < 0 or indices.max() >= len(current):
        raise ValueError('Window outside observed samples')
    values = current[indices]
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite observed current')
    return values.mean(axis=-1)


def baselines(pre):
    pre = np.asarray(pre, float)
    if pre.ndim != 2 or pre.shape[1] != len(PRE):
        raise ValueError('Pre-window shape mismatch')
    pre_t = (PRE+(BIN-1)/2)/FS
    response_t = (RESPONSE+(BIN-1)/2)/FS
    level = np.broadcast_to(pre.mean(axis=1)[:, None], (len(pre), len(RESPONSE))).copy()
    centered_t = pre_t-pre_t.mean()
    slope = (pre@centered_t)/(centered_t@centered_t)
    return dict(level=level, linear=level+slope[:, None]*(response_t-pre_t.mean()))


def history(times, relative_amplitude, tau):
    times, amplitude = np.asarray(times, float), np.asarray(relative_amplitude, float)
    if (times.ndim != 1 or amplitude.shape != times.shape or len(times) == 0 or not np.isfinite(tau) or tau <= 0
            or not np.isfinite(times).all() or not np.isfinite(amplitude).all()
            or np.any(np.diff(times) <= 0) or np.any(amplitude <= 0)):
        raise ValueError('Invalid command history')
    h = np.zeros(len(times))
    for n in range(1, len(times)):
        h[n] = np.exp(-(times[n]-times[n-1])/tau)*(h[n-1]+amplitude[n-1])
    return h


def design(record, tau=None):
    u = record['relative_amplitude']
    return u[:, None] if tau is None else np.column_stack((u, u*history(record['times'], u, tau)))


def fit(records, policy, sweeps=TRAIN, tau=None):
    selected = [r for r in records if r['sweep'] in sweeps]
    if {r['sweep'] for r in selected} != set(sweeps) or len(selected) != len(sweeps):
        raise ValueError('Training sweep set mismatch')
    x = np.concatenate([design(r, tau)[:8] for r in selected])
    y = np.concatenate([(r['observed']-r['baselines'][policy])[:8] for r in selected])
    beta, _, rank, singular = np.linalg.lstsq(x, y, rcond=None)
    if rank != x.shape[1]:
        raise ValueError('Unidentified template design')
    return beta, float(singular[0]/singular[-1])


def choose_tau(records, policy):
    scores = []
    for tau in TAUS:
        folds = []
        for held in TRAIN:
            train = tuple(s for s in TRAIN if s != held)
            beta, _ = fit(records, policy, train, tau)
            record = next(r for r in records if r['sweep'] == held)
            prediction = record['baselines'][policy]+design(record, tau)@beta
            folds.append(dict(held_sweep=held, mse_pA2=float(np.mean((prediction[:8]-record['observed'][:8])**2))))
        scores.append(dict(tau_s=tau, cv_mse_pA2=float(np.mean([r['mse_pA2'] for r in folds])), folds=folds))
    # Fixed grid order resolves exact ties; no evaluation sweep enters selection.
    return min(scores, key=lambda r: r['cv_mse_pA2'])['tau_s'], scores


def extract(inputs, state):
    raw_rows = {(r['sweep'], r['channel']): r for r in inputs['records']}
    measurement = {(r['sweep'], r['device']): r for r in state['records']}
    records = []
    with np.load(ROOT/inputs['arrays']['path'], allow_pickle=False) as archive:
        for sweep in range(7):
            command = raw_rows[sweep, 'DA5']
            pulses = [x for x in command['all_command_intervals'] if x['delta_min_V'] > 0]
            if len(pulses) != 12 or command['rate'] != FS:
                raise ValueError('Source protocol mismatch')
            starts = np.array([p['start_index'] for p in pulses])
            amplitude = np.array([p['delta_min_V'] for p in pulses])/.12
            if np.any(starts[:-1]+RESPONSE[-1]+BIN > starts[1:]):
                raise ValueError('Response windows overlap the next command')
            for target, channel in TARGETS.items():
                device = 4 if target == 'positive' else 2
                meta, raw = measurement[sweep, device], raw_rows[sweep, channel]
                if (raw['rate'], raw['start'], raw['samples']) != (command['rate'], command['start'], command['samples']):
                    raise ValueError('Raw channel clock mismatch')
                if not (meta['patch']['qc_pass'] == 1 and meta['diagnosis']['embedded_test_pulse']['confirmed']):
                    raise ValueError('Measurement prerequisites missing')
                own = raw_rows[sweep, 'DA'+str(device)]
                own_pulses = [x for x in own['all_command_intervals'] if x['delta_min_V'] > 0]
                if max(x['stop_index'] for x in own_pulses) >= starts[0]+PRE[0]:
                    raise ValueError('Own command overlaps source response prefix')
                current = archive[raw['array_key']]*1e12
                pre = bin_means(current, starts, PRE)
                observed = bin_means(current, starts, RESPONSE)
                records.append(dict(sweep=sweep, target=target, events=starts, times=starts/FS,
                    relative_amplitude=amplitude, observed=observed, pre=pre, baselines=baselines(pre),
                    source_command_V=float(pulses[0]['delta_min_V']), own_command_V=float(own_pulses[0]['delta_min_V']),
                    source_start_NWB_s=raw['start'], own_to_source_gap_s=float((starts[0]-own_pulses[-1]['stop_index'])/FS)))
    return records


def command_condition(records, target, sweeps):
    selected = [r for r in records if r['target'] == target and r['sweep'] in sweeps]
    train = [r for r in records if r['target'] == target and r['sweep'] in TRAIN]
    result = {}
    for field in ('source_command_V', 'own_command_V'):
        reference = sorted(set(r[field] for r in train))
        values = sorted(set(r[field] for r in selected))
        if len(reference) != 1 or not values:
            raise ValueError('Command cohort reference is not unique')
        result[field] = values
        result[field+'_changed_from_training'] = any(not np.isclose(v, reference[0], rtol=1e-6, atol=1e-9) for v in values)
    return result


def analyze(records):
    fits, arrays, scores = [], {}, []
    for target in TARGETS:
        selected = [r for r in records if r['target'] == target]
        for r in selected:
            key = target+'_s'+str(r['sweep'])
            for name in ('observed', 'pre', 'events', 'times', 'relative_amplitude'):
                arrays[key+'_'+name] = r[name]
        for policy in POLICIES:
            tau, cv = choose_tau(selected, policy)
            fixed, fixed_condition = fit(selected, policy)
            candidates = {t: fit(selected, policy, tau=t) for t in TAUS}
            beta, condition = candidates[tau]
            arrays[target+'_'+policy+'_fixed_beta'] = fixed
            for t, (b, _) in candidates.items():
                arrays[target+'_'+policy+'_history_beta_'+str(t)] = b
            fits.append(dict(target=target, baseline=policy, tau_s=tau, tau_at_grid_boundary=tau in (TAUS[0], TAUS[-1]), inner_cv=cv,
                             fixed_design_condition=fixed_condition, history_design_condition=condition))
            for record in selected:
                key = target+'_s'+str(record['sweep'])+'_'+policy
                baseline = record['baselines'][policy]
                predictions = dict(baseline=baseline, fixed=baseline+design(record)@fixed,
                                   history=baseline+design(record, tau)@beta)
                predictions.update({'history_tau_'+str(t): baseline+design(record, t)@b
                                    for t, (b, _) in candidates.items()})
                for name, prediction in predictions.items():
                    arrays[key+'_'+name] = prediction
                    error = prediction-record['observed']
                    for region, pulses in (('initial', slice(0, 8)), ('recovery', slice(8, 12))):
                        for window, columns in (('all', slice(None)), ('early', slice(0, 16)), ('late', slice(16, None))):
                            e = error[pulses, columns]
                            scores.append(dict(target=target, baseline=policy, method=name, sweep=record['sweep'],
                                region=region, window=window, mse_pA2=float(np.mean(e*e)), bias_pA=float(e.mean())))
    summary = []
    for cohort, sweeps in COHORTS.items():
        groups = {}
        for row in scores:
            if row['sweep'] not in sweeps:
                continue
            key = tuple(row[k] for k in ('target', 'baseline', 'method', 'region', 'window'))
            groups.setdefault(key, []).append(row)
        for key, rows in groups.items():
            summary.append(dict(zip(('target', 'baseline', 'method', 'region', 'window'), key),
                cohort=cohort, sweeps=list(sweeps), rmse_pA=float(np.sqrt(np.mean([r['mse_pA2'] for r in rows]))),
                command_condition=command_condition(records, key[0], sweeps),
                bias_pA=float(np.mean([r['bias_pA'] for r in rows]))))
    return fits, scores, summary, arrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE/'vc20hz_command_history_result.json')
    parser.add_argument('--array-output', type=Path,
                        default=ROOT/'data/local/allen-synphys-analysis/vc20hz-command-history-v1/predictions_final.npz')
    args = parser.parse_args()
    if args.output.exists() or args.array_output.exists():
        raise FileExistsError('Preserve previous outputs')
    inputs_path, state_path = HERE/'vc20hz_source_inputs_result.json', HERE/'vc20hz_measurement_state_result.json'
    if sha(inputs_path) != INPUT_SHA or sha(state_path) != STATE_SHA:
        raise ValueError('Frozen input changed')
    inputs, state = [json.loads(p.read_text(encoding='utf-8')) for p in (inputs_path, state_path)]
    if sha(ROOT/inputs['arrays']['path']) != inputs['arrays']['sha256']:
        raise ValueError('Raw arrays changed')
    records = extract(inputs, state)
    fits, scores, summary, arrays = analyze(records)
    out = dict(schema='allen.vc20hz.command-history.v1', source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_vc20hz_command_history.py'), python=platform.python_version(), numpy=np.__version__,
        inputs=dict(metadata_sha256=INPUT_SHA, measurement_state_sha256=STATE_SHA, raw_arrays=inputs['arrays']),
        method=dict(training_sweeps=TRAIN, training_pulses=list(range(8)), tau_grid_s=TAUS,
            response_window_ms=[2, 40], early_window_ms=[2, 10], late_window_ms=[10, 40],
            pre_window_ms=[-10, -2], bin_ms=.5, amplitude_reference_V=.12,
            baseline_policies=POLICIES, selected_tau='Leave-one-training-sweep-out MSE on initial8 and full2..40ms; refit2+3.',
            history='h[0]=0 per sweep; h[n]=exp(-(t[n]-t[n-1])/tau)*(h[n-1]+u[n-1]); u=command_delta/0.12V',
            prediction='baseline + u[n]*(template0[lag]+h[n]*template1[lag])',
            amplitude_transport='Half commands halve the fixed term and quarter the bilinear history term; this is a model assumption.',
            scoring_status='training/initial is in-sample; training/recovery is same-sweep held response; all other sweeps are excluded from template/tau fitting.',
            observation_budget='Only target samples strictly before -2ms set current-event baseline. Earlier responses may affect later baselines.',
            scope='Retrospective selected same cells. Descriptive audit inspected all sweeps before fitting; no blinded population validation.'),
        records=[{k: r[k] for k in ('target', 'sweep', 'source_command_V', 'own_command_V', 'source_start_NWB_s', 'own_to_source_gap_s')} for r in records],
        fits=fits, per_sweep=scores, summary=summary,
        interpretation='Conditional clamp-current prediction. Source commands are not observed APs; history is not identified synaptic plasticity.')
    # Validate metadata serialization before creating either final output.
    json.dumps(out, allow_nan=False)
    args.array_output.parent.mkdir(parents=True, exist_ok=True)
    with args.array_output.open('xb') as stream:
        np.savez_compressed(stream, **arrays)
    out['arrays'] = dict(path=args.array_output.relative_to(ROOT).as_posix(), sha256=sha(args.array_output),
                         bytes=args.array_output.stat().st_size)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(out, indent=2, allow_nan=False))
    print(json.dumps(dict(records=len(records), fits=len(fits), scores=len(scores), arrays=len(arrays), output=str(args.output))))


if __name__ == '__main__':
    main()
