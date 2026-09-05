"""Development test of filtered common-pulse prediction and visible modes.

All ten waveforms were previously exposed. Fit onset data from the first two
records of each chronological block; predict offset and later repetitions.
The two-pole filter is an effective candidate, not calibrated hardware.
No intrinsic G, C, Rs, or spatial metric is estimated.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
INPUT = HERE / 'electrical_star_stored_tp_waveforms_result.json'
EXPECTED_INPUT = '192c6275adaa6e4c904af19d71130ce8fa43e286769346eb7e774ef18dfa0c30'
OUTPUT = HERE / 'electrical_star_tp_dynamics_result.json'
DT_MS = .02
HEADS = [0, 1, 2, 4, 5, 6, 7]
CONFIG = dict(stage='Posthoc development; all input waveforms previously exposed',
    blocks=[dict(train=[0, 1], evaluate=[2, 3, 4]), dict(train=[5, 6], evaluate=[7, 8, 9])],
    holding_interpretation='Chronological blocks, not confirmed stored-TP holding-voltage groups',
    baseline_indices_inclusive=[295, 370], onset_indices_halfopen=[375, 875],
    offset_indices_halfopen=[875, 1250], pulse_duration_ms=10,
    mode_counts=list(range(1, 8)), decay_tau_bounds_ms=[.1, 100],
    effective_filter='Two identical cascaded first-order low-pass stages, common to all channels',
    filter_tau_bounds_ms=[.002, .08], latency_bounds_ms=[0, .06],
    coefficient_constraints='Signed per-channel exponential coefficients; reciprocity and passivity not imposed',
    noise_scale='Mean training baseline sample SD per channel, floored at 1 pA',
    selection='Smallest mode count with whitened onset residual <=1.25*RMS(training difference/2); else minimum onset residual as diagnostic only',
    response_gate='Each evaluated waveform: joint RMSE/noise<=2, maximum channel RMSE/noise<=3, RMSE/zero<=0.2, for onset and offset separately',
    derivative_mode_proxy='0.1 ms averages; first differences between onset bins 2..97; signal=training mean, variability=(train0-train1)/2',
    reproducible_mode_rule='Signal singular value >3*largest variability singular value; descriptive threshold, not a confidence interval')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def step_basis(time_ms, taus_ms, filter_tau_ms, latency_ms):
    time = np.maximum(np.asarray(time_ms) - latency_ms, 0)
    z = time / filter_tau_ms
    fast = np.exp(-z)
    columns = [-np.expm1(-z) - z * fast]
    for tau in taus_ms:
        rate = 1 / filter_tau_ms - 1 / tau
        column = (np.exp(-time / tau) - fast * (1 + time * rate)) / (1 - filter_tau_ms / tau) ** 2
        columns.append(column)
    return np.column_stack(columns)


def pulse_basis(time_ms, taus_ms, filter_tau_ms, latency_ms, duration_ms=10):
    return step_basis(time_ms, taus_ms, filter_tau_ms, latency_ms) - step_basis(np.asarray(time_ms) - duration_ms, taus_ms, filter_tau_ms, latency_ms)


def fit_onset(time_ms, observed, noise_scale, modes, max_nfev=300):
    """Variable projection: nonlinear shared poles, linear channel residues."""
    target = np.asarray(observed) / noise_scale
    def solve(parameters):
        taus = np.exp(parameters[:modes])
        tau_filter = np.exp(parameters[modes])
        latency = parameters[modes + 1]
        basis = step_basis(time_ms, taus, tau_filter, latency)
        coefficients = np.linalg.lstsq(basis, target, rcond=1e-11)[0]
        return basis, coefficients
    def residual(parameters):
        basis, coefficients = solve(parameters)
        return (basis @ coefficients - target).ravel()
    lower = [np.log(.1)] * modes + [np.log(.002), 0]
    upper = [np.log(100)] * modes + [np.log(.08), .06]
    starts = [np.r_[np.log(np.geomspace(.2, 15, modes)), np.log(.015), .01],
              np.r_[np.log(np.geomspace(.12, 50, modes)), np.log(.025), .005]]
    candidates = []
    for initial in starts:
        fit = least_squares(residual, initial, bounds=(lower, upper), max_nfev=max_nfev,
                            ftol=1e-8, xtol=1e-8, gtol=1e-8)
        basis, coefficients = solve(fit.x)
        candidates.append(dict(parameters=fit.x, basis=basis, coefficients=coefficients,
            cost=float(np.mean((basis @ coefficients - target) ** 2)),
            optimizer_success=bool(fit.success), optimizer_status=int(fit.status), nfev=int(fit.nfev)))
    best = min(candidates, key=lambda item: item['cost'])
    parameters = best['parameters']
    return dict(modes=modes, taus_ms=np.exp(parameters[:modes]).tolist(),
        filter_tau_ms=float(np.exp(parameters[modes])), latency_ms=float(parameters[modes + 1]),
        coefficients_pA=(best['coefficients'] * noise_scale).tolist(),
        whitened_training_rmse=float(np.sqrt(best['cost'])),
        design_condition=float(np.linalg.cond(best['basis'])),
        optimizer_success=best['optimizer_success'], optimizer_status=best['optimizer_status'],
        starts=[dict(cost=c['cost'], optimizer_success=c['optimizer_success'], nfev=c['nfev']) for c in candidates])


def predict(model, time_ms):
    return pulse_basis(time_ms, model['taus_ms'], model['filter_tau_ms'], model['latency_ms']) @ np.array(model['coefficients_pA'])


def mode_proxy(train):
    averaged = train[:, 375:875].reshape(2, 100, 5, 7).mean(2)
    differences = np.diff(averaged[:, 2:98], axis=1)
    signal = differences.mean(0)
    variability = (differences[0] - differences[1]) / 2
    _, singular, vectors = np.linalg.svd(signal, full_matrices=False)
    noise_singular = np.linalg.svd(variability, compute_uv=False)
    threshold = 3 * noise_singular[0]
    return dict(signal_singular_values=singular.tolist(), variability_singular_values=noise_singular.tolist(),
        threshold=float(threshold), above_threshold_count=int(np.sum(singular > threshold)),
        seventh_to_variability_operator_ratio=float(singular[-1] / noise_singular[0]),
        channel_vectors=vectors.tolist(), interpretation='Repeat-stable finite-difference modes; not intrinsic membrane rank or a statistical confidence bound')


def score(observed, predicted, template, noise_scale):
    error = observed - predicted
    channel_rmse = np.sqrt(np.mean(error ** 2, axis=0))
    white_channel = channel_rmse / noise_scale
    relative_zero = float(np.sqrt(np.mean(error ** 2) / np.mean(observed ** 2)))
    joint = float(np.sqrt(np.mean((error / noise_scale) ** 2)))
    return dict(rmse_pA=float(np.sqrt(np.mean(error ** 2))), rmse_by_channel_pA=channel_rmse.tolist(),
        rmse_over_noise_by_channel=white_channel.tolist(), joint_rmse_over_noise=joint,
        rmse_over_zero=relative_zero, full_training_template_rmse_pA=float(np.sqrt(np.mean((observed - template) ** 2))),
        response_gate=bool(joint <= 2 and max(white_channel) <= 3 and relative_zero <= .2))


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    assert sha(INPUT) == EXPECTED_INPUT
    code_hash = sha(__file__)
    source = json.loads(INPUT.read_text(encoding='utf8'))
    waves = np.array([r['waveform_raw'] for r in source['records']])
    assert waves.shape == (10, 1250, 7)
    assert all(r['sorted_valid_headstage_mapping_hypothesis'] == HEADS for r in source['records'])
    baselines = waves[:, 295:371].mean(1)
    # Positive response means inward current under the negative voltage step.
    responses = -(waves - baselines[:, None, :])
    time = np.arange(1250) * DT_MS - 7.5
    blocks = []
    rise = []
    for index, response in enumerate(responses):
        total = response.sum(1)
        sd = float(total[295:371].std(ddof=1))
        early = total[375:386]
        rise.append(dict(sweep=index, baseline_total_sd_pA=sd,
            first_11_samples_after_nominal_onset_pA=early.tolist(),
            maximum_total_time_after_nominal_onset_ms=float(np.argmax(early) * DT_MS),
            sample_0p04ms_to_0p06ms_increase_pA=float(early[3] - early[2]),
            increase_over_baseline_sd=float((early[3] - early[2]) / sd)))
    for specification in CONFIG['blocks']:
        training = responses[specification['train']]
        mean = training.mean(0)
        scale = np.maximum(waves[specification['train'], 295:371].std(1, ddof=1).mean(0), 1.)
        variation = float(np.sqrt(np.mean(((training[0, 375:875] - training[1, 375:875]) / (2 * scale)) ** 2)))
        models = []
        for modes in CONFIG['mode_counts']:
            model = fit_onset(time[375:875], mean[375:875], scale, modes)
            model['training_noise_gate'] = bool(model['whitened_training_rmse'] <= 1.25 * variation)
            models.append(model)
            print('FIT', specification['train'], modes, 'noise_rmse', model['whitened_training_rmse'], 'success', model['optimizer_success'], flush=True)
        passing = [m for m in models if m['training_noise_gate'] and m['optimizer_success']]
        selected = min(passing, key=lambda m: m['modes']) if passing else min(models, key=lambda m: m['whitened_training_rmse'])
        prediction = predict(selected, time)
        evaluated = []
        for sweep in specification['train'] + specification['evaluate']:
            evaluated.append(dict(sweep=sweep, role='onset_fit_only' if sweep in specification['train'] else 'later_repetition',
                onset=score(responses[sweep, 375:875], prediction[375:875], mean[375:875], scale),
                offset=score(responses[sweep, 875:1250], prediction[875:1250], mean[875:1250], scale)))
        block = dict(**specification, noise_scale_pA=scale.tolist(), training_mean_noise_proxy=variation,
            mode_proxy=mode_proxy(training), models=models, selected_mode_count=selected['modes'],
            any_training_noise_gate_pass=bool(passing), prediction_pA=prediction.tolist(), evaluations=evaluated)
        block['all_later_repetition_onset_offset_gates'] = all(r[part]['response_gate'] for r in evaluated if r['role'] == 'later_repetition' for part in ('onset', 'offset'))
        blocks.append(block)
    result = dict(code_sha256=code_hash, input_sha256=sha(INPUT), numpy_version=np.__version__, scipy_version=scipy.__version__,
        config=CONFIG, headstages=HEADS, baselines_pA=baselines.tolist(), early_total_current_rise=rise, blocks=blocks,
        observed_response_pA=responses.tolist(),
        interpretation='Descriptive prediction and observability checks under an uncalibrated effective filter; no intrinsic circuit or spatial metric fit',
        limitations=['All waveforms had been exposed before this development specification',
            'Acquisition 10 kHz setting is not independently attached to the stored TP timestamp',
            'Unknown channel filters, parasitic capacitance, drift and holding conditions can alter apparent modes',
            'Signed residues and a shared effective filter do not establish a reciprocal passive RC realization',
            'A low visible-mode count at this noise level does not prove exact low intrinsic dimension',
            'Full training waveform template uses training offsets; the fitted model uses training onsets only',
            'Optimizer success and waveform prediction do not establish parameter uniqueness or true electrode calibration'])
    assert sha(__file__) == code_hash
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print('DONE', [(b['selected_mode_count'], b['mode_proxy']['above_threshold_count'], b['all_later_repetition_onset_offset_gates']) for b in blocks])
    print('SHA256', sha(OUTPUT))


if __name__ == '__main__':
    main()
