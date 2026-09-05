"""Posthoc pulse-duration sensitivity and large post-pulse current events.

The inserted acquisition command lasts 10.02 ms. Apply that candidate to
stored TP predictions without refitting any pole, filter, residue or latency.
This does not prove the unrecorded stored-TP DAC waveform has that duration.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

from electrical_star_tp_dynamics import pulse_basis, score

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'electrical_star_tp_transition_check_result.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    code_hash = sha(__file__)
    dynamic_path = HERE / 'electrical_star_tp_dynamics_result.json'
    assert sha(dynamic_path) == '6db19733d1daedbf17d874dfe8b42529ed21b4f9c0f6480974350cb35c910b07'
    dynamic = json.loads(dynamic_path.read_text())
    command_path = HERE / 'electrical_star_vc_inputs_result.json'
    commands = json.loads(command_path.read_text())
    durations = [segment['duration_s'] * 1000 for sweep in commands['sweeps'] for device in sweep['devices']
                 for segment in device['command_segments'] if abs(segment['start_s'] - .0075) < 1e-10]
    assert len(durations) == 70 and np.allclose(durations, 10.02, atol=1e-10, rtol=0)
    observed = np.asarray(dynamic['observed_response_pA'])
    time = np.arange(1250) * .02 - 7.5
    predictions = []
    for block in dynamic['blocks']:
        template = observed[block['train']].mean(0)
        scale = np.array(block['noise_scale_pA'])
        for count in [block['selected_mode_count'], 7]:
            model = next(m for m in block['models'] if m['modes'] == count)
            for duration in (10., 10.02):
                prediction = pulse_basis(time, model['taus_ms'], model['filter_tau_ms'], model['latency_ms'], duration) @ np.array(model['coefficients_pA'])
                evaluations = [dict(sweep=sweep,
                    offset=score(observed[sweep, 875:], prediction[875:], template[875:], scale),
                    primary_four_offset=score(observed[sweep, 875:][:, [1, 2, 3, 4]], prediction[875:][:, [1, 2, 3, 4]], template[875:][:, [1, 2, 3, 4]], scale[[1, 2, 3, 4]]))
                    for sweep in block['train'] + block['evaluate']]
                predictions.append(dict(train=block['train'], evaluate=block['evaluate'], modes=count,
                    duration_ms=duration, evaluations=evaluations,
                    prediction_pA=prediction.tolist() if duration == 10.02 and count == block['selected_mode_count'] else None))
    early_peak_separations = []
    events = []
    for sweep in range(10):
        wave = observed[sweep]
        for column, head in enumerate(dynamic['headstages']):
            onset_peak = 375 + int(np.argmax(wave[375:386, column]))
            offset_peak = 875 + int(np.argmin(wave[875:886, column]))
            early_peak_separations.append(dict(sweep=sweep, headstage=head,
                onset_peak_time_ms=onset_peak * .02, offset_peak_time_ms=offset_peak * .02,
                peak_separation_ms=(offset_peak - onset_peak) * .02))
            # A descriptive event threshold after inspecting the failed prediction.
            indices = np.flatnonzero(wave[890:, column] > 500) + 890
            if not len(indices):
                continue
            peak = 890 + int(np.argmax(wave[890:, column]))
            events.append(dict(sweep=sweep, headstage=head, first_above_threshold_ms=float(indices[0] * .02),
                last_above_threshold_ms=float(indices[-1] * .02), samples_above_threshold=int(len(indices)),
                peak_time_ms=float(peak * .02), peak_inward_current_pA=float(wave[peak, column])))
    result = dict(code_sha256=code_hash, dynamics_sha256=sha(dynamic_path),
        dynamics_helper_sha256=sha(HERE / 'electrical_star_tp_dynamics.py'), command_result_sha256=sha(command_path),
        stage='Posthoc sensitivity prompted by nominal-duration fit failure; no independent validation',
        actual_inserted_command_duration_ms=10.02, inserted_command_channels_checked=70,
        stored_TP_command_duration_status='Unobserved DAC; 10.02 ms is a supported candidate, not a direct measurement',
        prediction_rule='Reuse frozen onset fits and change only pulse duration from 10.00 to 10.02 ms; no fitted parameter changes',
        scoring_window='Original nominal offset window 17.50..24.98 ms, unchanged for comparison',
        predictions=predictions, early_peak_separations=early_peak_separations,
        event_rule='Descriptive posthoc: baseline-subtracted inward current >500 pA after 17.80 ms',
        postpulse_events=events,
        limitations=['Extremum separation does not alone prove command duration or identical onset/offset kernels',
            'Large inward post-pulse events are not classified as spikes, sodium currents, artifacts or direct synaptic connections',
            'The 7-mode fits can be severely ill-conditioned; they are diagnostic predictions, not identified neural states',
            'Primary-four scores are a descriptive subset and do not remove external cells or certify a closed four-cell network'])
    assert sha(__file__) == code_hash
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    for prediction in predictions:
        later = [e for e in prediction['evaluations'] if e['sweep'] in prediction['evaluate']]
        print('PREDICT',prediction['train'],prediction['modes'],prediction['duration_ms'],
              'later_rmse',[round(e['offset']['rmse_pA'],3) for e in later],
              'primary_rmse',[round(e['primary_four_offset']['rmse_pA'],3) for e in later])
    print('EVENTS',events)
    print('SHA256',sha(OUTPUT))


if __name__ == '__main__':
    main()
