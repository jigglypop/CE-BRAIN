"""Plot observed anchor events, recipient residuals and association controls."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    outputs = [HERE / ('electrical_star_event_association.' + ext) for ext in ('png', 'svg')]
    for output in outputs:
        if output.exists():
            raise FileExistsError(output)
    result = json.loads((HERE / 'electrical_star_event_association_result.json').read_text())
    original = json.loads((HERE / 'electrical_star_tp_dynamics_result.json').read_text())
    response = np.array(original['observed_response_pA'])
    relative = np.arange(-20, 31)
    time = relative * .02
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 7.8), constrained_layout=True)
    ax = axes[0, 0]
    for event in result['events']:
        if event['role'] != 'evaluate':
            continue
        ax.plot(time, response[event['sweep'], event['peak_index'] + relative, 6] / 1000,
                label='event ' + event['id'])
    ax.set(title='A  Device 7: four events in two recordings', xlabel='Time relative to current peak (ms)', ylabel='Inward current change (nA)')
    ax.legend(fontsize=8)
    ax = axes[0, 1]
    channel = next(c for c in result['channels'] if c['headstage'] == 1)
    model = next(m for m in channel['models'] if m['family'] == 'instantaneous_free')
    event = next(e for e in model['per_event'] if e['id'] == '8:1')
    ax.plot(time, event['observed_residual_pA'], '.-', color='#245b86', label='Observed local residual')
    ax.plot(time, event['predicted_residual_pA'], color='#d68b24', label='Gain learned on events 5:0 and 7:0')
    ax.set(title='B  Device 1 during later event 8:1', xlabel='Time relative to device-7 peak (ms)', ylabel='Quadratic-projected current (pA)')
    ax.legend(fontsize=8)
    ax = axes[1, 0]
    heads = [c['headstage'] for c in result['channels']]
    instant = []; shifted = []; later = []; event_gain = []; control_gain = []
    for channel in result['channels']:
        a = next(m for m in channel['models'] if m['family'] == 'instantaneous_free')
        b = next(m for m in channel['models'] if m['family'] == 'free_with_lead_controls')
        instant.append(a['evaluate']['rmse_over_zero'])
        shifted.append(b['evaluate']['rmse_over_zero'])
        later.append(b['later_events']['rmse_over_zero'])
        event_gain.append(b['evaluate']['mse_gain_over_zero_pA2'])
        control_gain.append(max(c['mse_gain_over_zero_pA2'] for c in b['time_matched_controls'].values()))
    x = np.arange(len(heads))
    ax.plot(x, instant, 'o-', label='Instantaneous, all four evaluation events')
    ax.plot(x, shifted, 's-', label='Time-shift family, all four events')
    ax.plot(x, later, '^-', label='Time-shift family, two later events')
    ax.axhline(1, color='gray', linestyle='--', lw=.8)
    ax.axhline(.8, color='#94516a', linestyle=':', lw=.8)
    ax.set(title='C  Improvement does not transfer to later events', xlabel='Compared device', ylabel='RMSE / zero-prediction RMSE', xticks=x, xticklabels=heads)
    ax.legend(fontsize=7)
    ax = axes[1, 1]
    ax.bar(x - .17, event_gain, .34, label='Actual event recordings')
    ax.bar(x + .17, control_gain, .34, label='Largest gain in time-matched control')
    ax.axhline(0, color='gray', lw=.8)
    ax.set(title='D  Time-locked controls show similar improvement', xlabel='Compared device', ylabel='MSE gain over zero prediction (pA squared)', xticks=x, xticklabels=heads)
    ax.legend(fontsize=7)
    fig.suptitle('Observed-current association: no event-specific transfer or mechanism identification', fontsize=12)
    for output in outputs:
        fig.savefig(output, dpi=180)
        print(output.name)
    plt.close(fig)


if __name__ == '__main__':
    main()
