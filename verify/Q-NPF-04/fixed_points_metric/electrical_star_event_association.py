"""Development association of large device-7 events and simultaneous currents.

Device 7 is an observed anchor, not an established causal source. Event and
time-matched control windows undergo the same local quadratic projection.
All raw inputs were exposed previously; these are not independent biological
holdouts, causal interventions, electrode calibration, or metric estimates.
"""
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks, lfilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE / 'electrical_star_event_association_result.json'
RELATIVE = np.arange(-20, 31)
DT = .02
HEADS = [0, 1, 2, 4, 5, 6, 7]
CONTROLS = [0, 1, 2, 3, 4, 6]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def remove_quadratic(values):
    time = RELATIVE * DT
    design = np.column_stack([np.ones(len(time)), time, time ** 2])
    return values - design @ np.linalg.lstsq(design, values, rcond=None)[0]


def feature(response, event, tau, delay):
    anchor = response[event['sweep'], :, 6]
    if tau:
        coefficient = np.exp(-DT / tau)
        anchor = lfilter([1 - coefficient], [1, -coefficient], anchor)
    indices = event['peak_index'] + RELATIVE - round(delay / DT)
    assert min(indices) >= 0 and max(indices) < len(anchor)
    return remove_quadratic(anchor[indices])


def gain_fit(features, targets, sign):
    x = np.concatenate(features)
    y = np.concatenate(targets)
    denominator = float(x @ x)
    gain = 0. if denominator == 0 else float(x @ y / denominator)
    if sign == 'positive':
        gain = max(0., gain)
    elif sign == 'negative':
        gain = min(0., gain)
    return gain, float(np.mean((y - gain * x) ** 2))


def summary_score(targets, predictions):
    y = np.concatenate(targets)
    p = np.concatenate(predictions)
    mse = float(np.mean((y - p) ** 2))
    zero = float(np.mean(y ** 2))
    return dict(rmse_pA=float(np.sqrt(mse)), zero_rmse_pA=float(np.sqrt(zero)),
        rmse_over_zero=float(np.sqrt(mse / zero)), mse_gain_over_zero_pA2=zero - mse,
        improved_events=int(sum(np.mean((v - w) ** 2) < np.mean(v ** 2) for v, w in zip(targets, predictions))),
        event_count=len(targets))


def connection_inventory():
    path = ROOT / 'data/external/allen_synphys_r21/synphys_r2.1_small.sqlite'
    assert sha(path) == '7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        cells = [dict(row) for row in connection.execute('SELECT cell.id, electrode.device_id FROM cell JOIN electrode ON electrode.id=cell.electrode_id WHERE cell.experiment_id=2771 ORDER BY electrode.device_id')]
        pairs = [dict(row) for row in connection.execute('SELECT id, pre_cell_id, post_cell_id, has_synapse, has_electrical, has_polysynapse, crosstalk_artifact, n_ex_test_spikes, n_in_test_spikes FROM pair WHERE experiment_id=2771 AND (pre_cell_id=15837 OR post_cell_id=15837) ORDER BY pre_cell_id, post_cell_id')]
    return dict(database_sha256=sha(path), cells=cells, anchor_cell_id=15837, pairs=pairs,
        interpretation='Manual pair annotations; do not classify the source of these TP events')


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    code_hash = sha(__file__)
    input_path = HERE / 'electrical_star_tp_dynamics_result.json'
    assert sha(input_path) == '6db19733d1daedbf17d874dfe8b42529ed21b4f9c0f6480974350cb35c910b07'
    original = json.loads(input_path.read_text())
    response = np.array(original['observed_response_pA'])
    events = []
    for sweep in range(10):
        peaks, properties = find_peaks(response[sweep, 890:, 6], height=500, prominence=500, distance=25)
        for number, index in enumerate(peaks):
            peak = int(index + 890)
            events.append(dict(id=str(sweep) + ':' + str(number), sweep=sweep, peak_index=peak,
                peak_time_ms=peak * DT, peak_inward_pA=float(response[sweep, peak, 6]),
                prominence_pA=float(properties['prominences'][number]),
                role='train' if sweep in [5, 7] else 'evaluate',
                time_class='first_after_pulse' if peak * DT < 19 else 'later_event'))
    assert len(events) == 6 and sum(e['role'] == 'train' for e in events) == 2
    assert all(e['sweep'] in [5, 7, 8, 9] for e in events)
    train = [e for e in events if e['role'] == 'train']
    evaluate = [e for e in events if e['role'] == 'evaluate']
    windows = {e['id']: remove_quadratic(response[e['sweep'], e['peak_index'] + RELATIVE]) for e in events}
    control_windows = {e['id']: {control: remove_quadratic(response[control, e['peak_index'] + RELATIVE]) for control in CONTROLS} for e in events}
    families = dict(instantaneous_free=[(0., 0., 'free')],
        instantaneous_negative=[(0., 0., 'negative')],
        positive_causal=[(tau, delay, 'positive') for tau in [0., .02, .05, .1, .2, .5] for delay in [0., .1, .2, .3]],
        free_with_lead_controls=[(tau, delay, 'free') for tau in [0., .02, .05, .1, .2, .5] for delay in [-.3, -.2, -.1, 0., .1, .2, .3]])
    channels = []
    for column, head in enumerate(HEADS[:-1]):
        models = []
        for family, choices in families.items():
            candidates = []
            for tau, delay, sign in choices:
                features = [feature(response, e, tau, delay) for e in train]
                targets = [windows[e['id']][:, column] for e in train]
                gain, mse = gain_fit(features, targets, sign)
                candidates.append((mse, tau, delay, gain, sign))
            mse, tau, delay, gain, sign = min(candidates, key=lambda item: item[0])
            predictions = [gain * feature(response, e, tau, delay) for e in evaluate]
            targets = [windows[e['id']][:, column] for e in evaluate]
            evaluated = summary_score(targets, predictions)
            controls = {str(control): summary_score([control_windows[e['id']][control][:, column] for e in evaluate], predictions) for control in CONTROLS}
            later_indices = [i for i, e in enumerate(evaluate) if e['time_class'] == 'later_event']
            later_score = summary_score([targets[i] for i in later_indices], [predictions[i] for i in later_indices])
            max_control_gain = max(v['mse_gain_over_zero_pA2'] for v in controls.values())
            gate = bool(evaluated['rmse_over_zero'] <= .8 and evaluated['improved_events'] >= 3
                and evaluated['mse_gain_over_zero_pA2'] > max_control_gain and later_score['rmse_over_zero'] < 1)
            models.append(dict(family=family, tau_ms=tau, delay_ms=delay, gain=gain,
                training_rmse_pA=float(np.sqrt(mse)), evaluate=evaluated, later_events=later_score,
                time_matched_controls=controls, event_specificity_gate=gate,
                per_event=[dict(id=e['id'], score=summary_score([target], [prediction]),
                    observed_residual_pA=target.tolist(), predicted_residual_pA=prediction.tolist())
                    for e, target, prediction in zip(evaluate, targets, predictions)]))
        channels.append(dict(headstage=head, models=models))
        print('CHANNEL',head,[(m['family'],round(m['gain'],5),m['delay_ms'],round(m['evaluate']['rmse_over_zero'],3),m['event_specificity_gate']) for m in models],flush=True)
    result = dict(code_sha256=code_hash, input_sha256=sha(input_path),
        config=dict(stage='Posthoc development association, no independent biological holdout',
            event_rule='Device7 inward current peaks after17.80ms, height/prominence>=500pA, minimum separation0.50ms',
            train='Events in TP5 and7', evaluate='Four events in TP8 and9; two recording units, not four independent repeats',
            controls=CONTROLS, window_ms=[-.4, .6], nuisance='Per-window quadratic least-squares projection, acausal descriptive operation',
            regression='Same projection on target and filtered/shifted observed anchor; target channels never choose events',
            delay_sign='Positive delay predicts a target after the observed anchor; negative delay is a lead control',
            gate='Evaluation RMSE/zero<=0.8, improvement in>=3of4events, MSE gain greater than every time-matched control, later-event RMSE/zero<1'),
        events=events, connection_inventory=connection_inventory(), channels=channels,
        limitations=['Device7 has incoming chemical connection annotations; its large current need not be the initiating source',
            'The event occurs after a common command; time-locked background can create apparent association',
            'Local quadratic projection uses future samples and is not a physiological drift separation or online causal filter',
            'Observed-anchor regression is simultaneous association, not an exogenous intervention or temporal forecast',
            'Unknown relative filters, gains, common reference, multiple internal sources and shared noise prevent a unique mechanism conclusion',
            'Controls are time matched but stored holding states are not independently confirmed identical',
            'A passed descriptive gate would not calibrate resistance or establish a direct synapse or a spatial metric'])
    assert sha(__file__) == code_hash
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print('EVENTS',[(e['id'],e['peak_time_ms']) for e in events])
    print('SHA256',sha(OUTPUT))


if __name__ == '__main__':
    main()
