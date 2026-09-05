"""Standalone figures of frozen AP-history holdouts; no refitting."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from allen_ap_history_prediction import predict

HERE = Path(__file__).resolve().parent


def main():
    paths = [HERE/'ap_history_holdouts.png', HERE/'ap_history_holdouts.svg']
    if any(p.exists() for p in paths):
        raise FileExistsError('Preserve existing figures')
    result = json.loads((HERE/'allen_ap_history_modes_result.json').read_text(encoding='utf-8'))
    contract = json.loads((HERE/'allen_ap_history_modes_contract.json').read_text(encoding='utf-8'))
    colors = dict(constant='#2166ac', depression='#b2182b', facilitation='#1b7837')
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for row, summary in enumerate(result['summaries']):
        pair = summary['pair']
        for column, group in enumerate(('temporal', 'frequency')):
            ax = axes[row, column]
            records = [r for r in result['records'] if r['pair_id'] == pair['pair_id'] and r['usable'] and r['sweep'] in contract['split'][group]]
            if not records:
                ax.set_title(f"{pair['pre_cell']} -> {pair['post_cell']} | {group} holdout | n=0")
                ax.text(.5, .5, 'No eligible records for the specified IC measurement', ha='center', transform=ax.transAxes)
                ax.set_axis_off()
                continue
            y = np.array([r['psp_bins_mV'] for r in records]).mean(axis=2)*1000
            q = np.array([r['quiet_bins_mV'] for r in records]).mean(axis=2)*1000
            x = np.arange(1, 13)
            ax.plot(x, y.mean(axis=0), 'o-', color='#222222', label='Observed mean', linewidth=1.8)
            ax.plot(x, q.mean(axis=0), ':', color='#888888', label='Pre-input control', linewidth=1.5)
            for name, model in summary['models'].items():
                values = np.array([predict(r, model).reshape(12, 6).mean(axis=1) for r in records])*1000
                ax.plot(x, values.mean(axis=0), color=colors[name], label=name.capitalize(), linewidth=1.5)
            ax.axvline(8.5, color='#bbbbbb', linestyle='--', linewidth=.8)
            ax.axhline(0, color='#bbbbbb', linewidth=.8)
            ax.set_title(f"{pair['pre_cell']} -> {pair['post_cell']} | {group} holdout | n={len(records)}")
            ax.set_xlabel('Pulse number (1-8 induction; 9-12 recovery)')
            ax.set_ylabel('Baseline-subtracted mean PSP (uV)')
            ax.set_xticks(x)
            ax.grid(axis='y', alpha=.15)
            if row == column == 0:
                ax.legend(fontsize=8, ncol=2)
    fig.suptitle('Fixed neuronal positions: AP-history predictions\nNo held-out refit; voltage responses are not conductance or a measured metric', fontsize=13)
    for p in paths:
        fig.savefig(p, dpi=170)
    plt.close(fig)
    print('SAVED', ', '.join(p.name for p in paths))


if __name__ == '__main__':
    main()
