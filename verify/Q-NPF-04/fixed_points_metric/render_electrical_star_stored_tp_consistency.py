"""Plot stored peak sampling and matched-estimator resistance ratios."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    outputs = [HERE / ('electrical_star_stored_tp_consistency.' + ext) for ext in ('png', 'svg')]
    for output in outputs:
        if output.exists():
            raise FileExistsError(output)
    wave_data = json.loads((HERE / 'electrical_star_stored_tp_waveforms_result.json').read_text())
    comparison = json.loads((HERE / 'electrical_star_stored_tp_consistency_result.json').read_text())
    first = wave_data['records'][0]
    wave = np.asarray(first['waveform_raw'])[:, 0]
    baseline = wave[295:371].mean()
    time = np.arange(len(wave)) * .02 - 7.5
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), constrained_layout=True)
    ax = axes[0]
    keep = (time >= -.2) & (time <= .6)
    ax.plot(time[keep], wave[keep] - baseline, '.-', color='#245b86', label='Stored current minus baseline')
    ax.axvspan(.10, .12, alpha=.3, color='#ef9545', label='Property peak: samples at 0.10, 0.12 ms')
    ax.scatter([.11], [wave[380:382].mean() - baseline], marker='s', color='#ba581d', zorder=5)
    feature = first['features_by_waveform_column'][0]
    ax.scatter([feature['peak_time_ms'] - 7.5], [feature['peak_raw'] - baseline], marker='x', color='#903f67', s=65, zorder=5, label='Three-sample mean around minimum')
    ax.axvline(0, color='gray', lw=.8)
    ax.set(xlabel='Time after nominal step onset (ms)', ylabel='Recorded current change (pA)', title='A  Stored TP 17611, device 0')
    ax.legend(fontsize=7, loc='upper right')
    ax = axes[1]
    old, new = [], []
    for row in comparison['records']:
        if row['headstage'] not in (1, 2, 4, 5):
            continue
        record = next(r for r in wave_data['records'] if r['sweep'] == row['sweep'])
        nb = next(r for r in record['notebook_cells'] if r['device'] == row['headstage'])
        old.append(nb['comparison']['peak_ratio_to_nearby_notebook'])
        new.append(row['inserted_to_stored_same_estimator_peak_R_ratio'])
    offsets = np.linspace(-.11, .11, len(old))
    for offset, before, after in zip(offsets, old, new):
        ax.plot([offset, 1 + offset], [before, after], color='#99a6b3', alpha=.35, lw=.6)
    ax.scatter(offsets, old, s=15, color='#8175a8', label='40 channel / sweep observations')
    ax.scatter(1 + offsets, new, s=15, color='#2b7b67')
    ax.axhline(1, color='gray', linestyle='--', lw=1)
    ax.set_xticks([0, 1], ['Inserted estimate /\nnotebook peak R', 'Inserted estimate /\nstored same-estimator R'])
    ax.set(ylabel='Peak resistance ratio', title='B  Same estimation rule changes comparison', xlim=(-.35, 1.35))
    ax.legend(fontsize=7, loc='upper left')
    fig.suptitle('Numerical TP association; no independent electrode calibration', fontsize=12)
    for output in outputs:
        fig.savefig(output, dpi=180)
        print(output.name)
    plt.close(fig)


if __name__ == '__main__':
    main()
