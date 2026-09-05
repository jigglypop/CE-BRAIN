"""Scientific figure for timing, post-pulse events and observable modes."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    outputs = [HERE / ('electrical_star_tp_dynamics.' + ext) for ext in ('png', 'svg')]
    for output in outputs:
        if output.exists():
            raise FileExistsError(output)
    result = json.loads((HERE / 'electrical_star_tp_dynamics_result.json').read_text())
    timing = json.loads((HERE / 'electrical_star_tp_transition_check_result.json').read_text())
    observed = np.array(result['observed_response_pA'])
    time = np.arange(1250) * .02
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    ax = axes[0, 0]
    use = (time >= 7.48) & (time <= 7.70)
    for sweep, color in [(0, '#245b86'), (5, '#d68b24')]:
        ax.plot(time[use] - 7.5, observed[sweep, use].sum(1) / 1000, '.-', color=color, label='Stored TP linked to sweep ' + str(sweep))
    ax.axvline(0, color='gray', lw=.8)
    ax.set(title='A  Recorded total current has a finite rise', xlabel='Time after nominal onset (ms)', ylabel='Summed inward current change (nA)')
    ax.legend(fontsize=8)
    ax = axes[0, 1]
    use = (time >= 17.44) & (time <= 18)
    nominal = np.array(result['blocks'][0]['prediction_pA'])
    corrected = np.array(next(p['prediction_pA'] for p in timing['predictions'] if p['train'] == [0, 1] and p['modes'] == 2 and p['duration_ms'] == 10.02))
    ax.plot(time[use], observed[2, use, 3], '.-', color='#245b86', label='Observed: sweep 2, device 4')
    ax.plot(time[use], nominal[use, 3], color='#b67726', linestyle='--', label='Fixed fit, pulse duration 10.00 ms')
    ax.plot(time[use], corrected[use, 3], color='#368766', label='Same fit, duration 10.02 ms')
    ax.set(title='B  One sample changes offset prediction', xlabel='Time in stored TP (ms)', ylabel='Inward current change (pA)')
    ax.legend(fontsize=8)
    ax = axes[1, 0]
    use = (time >= 17.5) & (time <= 22.2)
    for sweep in range(5, 10):
        ax.plot(time[use], observed[sweep, use, 6] / 1000, lw=1.1, label='sweep ' + str(sweep))
    ax.axhline(.5, color='gray', linestyle=':', lw=.8)
    ax.set(title='C  Device 7 has variable post-pulse events', xlabel='Time in stored TP (ms)', ylabel='Inward current change (nA)')
    ax.legend(fontsize=8, ncol=2)
    ax = axes[1, 1]
    for block, color in zip(result['blocks'], ['#245b86', '#d68b24']):
        proxy = block['mode_proxy']
        ratio = np.array(proxy['signal_singular_values']) / proxy['variability_singular_values'][0]
        ax.plot(range(1, 8), ratio, 'o-', color=color, label='Training pair ' + str(block['train']))
    ax.axhline(3, color='#88485c', linestyle='--', label='Descriptive threshold: 3')
    ax.set(title='D  Seven stable modes are not established', xlabel='Singular-value order', ylabel='Signal / variability operator norm', yscale='log', xticks=range(1, 8))
    ax.legend(fontsize=8)
    fig.suptitle('Common TP development checks: observation model and practical identifiability', fontsize=13)
    for output in outputs:
        fig.savefig(output, dpi=180)
        print(output.name)
    plt.close(fig)


if __name__ == '__main__':
    main()
