"""Broaden fast transient poles after the first TP fit hit its bounds.

Same exposed data and chronological split. Pulse duration 10.02 ms is the
inserted-command-supported sensitivity candidate, not measured stored DAC.
This is a further development model, never a rescue of independent evidence.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from electrical_star_tp_dynamics import score

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'electrical_star_tp_broadband_result.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def broad_step(time_ms, taus_ms, filter_tau_ms, latency_ms):
    time = np.maximum(np.asarray(time_ms) - latency_ms, 0)
    z = time / filter_tau_ms
    fast = np.exp(-z)
    columns = [-np.expm1(-z) - z * fast]
    for tau in taus_ms:
        delta = 1 - filter_tau_ms / tau
        x = z * delta
        close = np.abs(x) < .05
        value = np.empty_like(time)
        # Analytic removable limit when a transient pole coincides with filter.
        xc = x[close]
        poly = .5 - xc / 3 + xc ** 2 / 8 - xc ** 3 / 30 + xc ** 4 / 144 - xc ** 5 / 840 + xc ** 6 / 5760
        value[close] = z[close] ** 2 * np.exp(-time[close] / tau) * poly
        if (~close).any():
            value[~close] = (np.exp(-time[~close] / tau) - fast[~close] * (1 + x[~close])) / delta ** 2
        columns.append(value)
    return np.column_stack(columns)


def broad_pulse(time, model):
    def basis(t):
        return broad_step(t, model['taus_ms'], model['filter_tau_ms'], model['latency_ms'])
    return (basis(time) - basis(np.asarray(time) - 10.02)) @ np.array(model['coefficients_pA'])


def broad_fit(time, observed, scale, modes):
    target = observed / scale
    def solve(parameters):
        basis = broad_step(time, np.exp(parameters[:modes]), np.exp(parameters[modes]), parameters[modes + 1])
        coefficients = np.linalg.lstsq(basis, target, rcond=1e-11)[0]
        return basis, coefficients
    def residual(parameters):
        basis, coefficients = solve(parameters)
        return (basis @ coefficients - target).ravel()
    starts = [np.r_[np.log(np.geomspace(.02, 15, modes)), np.log(.015), .01],
              np.r_[np.log(np.geomspace(.007, 50, modes)), np.log(.025), .005]]
    fits = []
    for initial in starts:
        fitted = least_squares(residual, initial,
            bounds=([np.log(.004)] * modes + [np.log(.002), 0], [np.log(100)] * modes + [np.log(.08), .06]),
            max_nfev=400, ftol=1e-8, xtol=1e-8, gtol=1e-8)
        basis, coefficients = solve(fitted.x)
        fits.append((float(np.mean((basis @ coefficients - target) ** 2)), fitted, basis, coefficients))
    cost, fit, basis, coefficients = min(fits, key=lambda record: record[0])
    return dict(modes=modes, taus_ms=np.exp(fit.x[:modes]).tolist(), filter_tau_ms=float(np.exp(fit.x[modes])),
        latency_ms=float(fit.x[modes + 1]), coefficients_pA=(coefficients * scale).tolist(),
        scaled_training_rmse=float(np.sqrt(cost)), design_condition=float(np.linalg.cond(basis)),
        optimizer_success=bool(fit.success), starts=[dict(cost=c, success=bool(f.success), nfev=int(f.nfev)) for c, f, _, _ in fits])


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    code_hash = sha(__file__)
    input_path = HERE / 'electrical_star_tp_dynamics_result.json'
    assert sha(input_path) == '6db19733d1daedbf17d874dfe8b42529ed21b4f9c0f6480974350cb35c910b07'
    original = json.loads(input_path.read_text())
    observed = np.asarray(original['observed_response_pA'])
    time = np.arange(1250) * .02 - 7.5
    blocks = []
    for previous in original['blocks']:
        training = observed[previous['train']].mean(0)
        scale = np.array(previous['noise_scale_pA'])
        variability = previous['training_mean_noise_proxy']
        models = []
        for count in range(1, 8):
            model = broad_fit(time[375:875], training[375:875], scale, count)
            model['training_variability_gate'] = model['scaled_training_rmse'] <= 1.25 * variability
            models.append(model)
            print('BROAD', previous['train'], count, model['scaled_training_rmse'], model['design_condition'], flush=True)
        eligible = [m for m in models if m['optimizer_success'] and m['training_variability_gate']]
        selected = min(eligible, key=lambda m: m['modes']) if eligible else min(models, key=lambda m: m['scaled_training_rmse'])
        prediction = broad_pulse(time, selected)
        evaluations = []
        for sweep in previous['train'] + previous['evaluate']:
            evaluations.append(dict(sweep=sweep,
                onset=score(observed[sweep, 375:875], prediction[375:875], training[375:875], scale),
                offset=score(observed[sweep, 875:], prediction[875:], training[875:], scale)))
        blocks.append(dict(train=previous['train'], evaluate=previous['evaluate'], models=models,
            selected_mode_count=selected['modes'], any_training_variability_gate_pass=bool(eligible),
            prediction_pA=prediction.tolist(), evaluations=evaluations))
    result = dict(code_sha256=code_hash, dynamics_result_sha256=sha(input_path),
        score_helper_sha256=sha(HERE / 'electrical_star_tp_dynamics.py'),
        stage='Further posthoc development after examining failures and boundary hits',
        changes=dict(transient_tau_lower_bound_ms=[.1, .004], pulse_duration_ms=[10., 10.02],
            stable_evaluation_at_coincident_poles=True),
        unchanged='Training/evaluation identities, onset-only fitting, per-channel scaling, signed residues, shared two-pole effective filter, latency bounds and gate definitions',
        blocks=blocks,
        limitations=['Wider bandwidth does not calibrate unknown filter or separate it uniquely from neuronal modes',
            '10.02 ms is observed in inserted commands, not directly in stored TP DAC',
            'Results remain development comparisons on exposed waveforms',
            'Sub-sample poles, coincident modes and large design condition can invalidate physical parameter interpretation',
            'No intrinsic G, C, Rs, spatial metric or independent energy-cost prediction'])
    assert sha(__file__) == code_hash
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print('SELECTED', [b['selected_mode_count'] for b in blocks])
    print('SHA256', sha(OUTPUT))


if __name__ == '__main__':
    main()
