"""Plot observed common input and hypothetical distinguishing predictions."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    source = HERE/'open_boundary_metric_result.json'
    r = json.loads(source.read_text(encoding='utf8'))['common_mode']
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), layout='constrained')
    colors = ['#2878b5', '#e07b22', '#358458']
    x = np.arange(5)
    axes[0].scatter(x, r['current_change_pA'], marker='x', color='black', s=55,
                    zorder=5, label='Observed clamp change (L1)')
    dv = np.array(r['common_command_mV'])
    for k, (w, color) in enumerate(zip(r['witnesses'], colors)):
        predicted = np.array(w['Y_nS'])@dv
        label = f"Edge coefficient = {w['edge_coefficient_nS']:g} nS"
        axes[0].scatter(x, predicted, s=80+90*k, facecolors='none', edgecolors=color,
                        linewidths=1.3, label=label)
        axes[1].plot([1, 2], w['fixed_direction_costs'], 'o-', color=color, label=label)
        axes[2].bar(x+(k-1)*.24, w['predicted_1mV_individual_probe_pA'], .22,
                    color=color, label=label)
    axes[0].set(title='A. Same common-input response', ylabel='Current change (pA)')
    axes[0].set_xticks(x, [str(i) for i in r['cell_ids']], rotation=35)
    axes[0].set_xlabel('Fixed neuron ID')
    axes[0].legend(fontsize=7.5, loc='lower right')
    axes[1].set(title='B. Different candidate metric costs', ylabel='Dimensionless directional cost')
    axes[1].set_xticks([1, 2], ['24114 to 24118', '24119 to 24115'])
    axes[1].set_xlabel('Unit direction between fixed points')
    axes[1].set_xlim(.8, 2.2)
    axes[2].set(title='C. Distinguishing individual input', ylabel='Predicted current change (pA)')
    axes[2].set_xticks(x, [str(i) for i in r['cell_ids']], rotation=35)
    axes[2].set_xlabel('1 mV applied to cell 24114 only')
    for axis in axes:
        axis.axhline(0, color='#999999', linewidth=.6)
        axis.spines[['right', 'top']].set_visible(False)
    fig.suptitle('Open-boundary identifiability: one observed input, multiple candidate geometries', fontsize=13)
    fig.supxlabel('A: reused observation. B: hypothetical compensated boundary. C: unperformed prediction. All metrics remain L0.',
                  fontsize=9)
    for extension in ['png', 'svg']:
        output = HERE/f'open_boundary_identifiability.{extension}'
        if output.exists():
            raise FileExistsError(output)
        fig.savefig(output, dpi=180, metadata={'Description': 'Input SHA-256 '+hashlib.sha256(source.read_bytes()).hexdigest()})
    plt.close(fig)


if __name__ == '__main__':
    main()
