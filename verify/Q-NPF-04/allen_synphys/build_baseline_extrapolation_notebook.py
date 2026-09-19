"""Build and execute a compact companion from the completed offline audit."""
import json
import os
from pathlib import Path
import sys
import tempfile

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOTEBOOK = HERE / 'recovery_baseline_extrapolation.ipynb'
FIGURE = HERE / 'figures/recovery_baseline_extrapolation.png'
if NOTEBOOK.exists() or FIGURE.exists():
    raise FileExistsError('Preserve existing companion outputs')

md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
cells = [md('''# Allen recovery gap: baseline extrapolation audit

## tl;dr
Computed values will be inserted after successful execution.

## Context & Methods
One experiment (1574292898.139), sweeps 37–56, one stimulated source and two targets.
The previous operator is post[2,8) ms minus pre[-8,-3) ms, relative to the detected
source spike. The candidate extrapolates an ordinary least-squares line fitted
only to the pre window. All 12 actual pulses and both targets are retained.

### Key Assumptions
Five pseudo events occur 20, 40, 60, 80 and 100 ms after the eighth detected spike.
Their enclosing windows precede pulse 9 and have zero stored source command.
Target commands are also verified from offline NWB blocks. Holding settings,
spontaneous input and residual responses remain: zero is not a known biological
response. **RMS measures contrast magnitude, not prediction error.**
Sweeps are repeated observations of these same cells, not independent animals.
Early/late halves are descriptive checks of already inspected data.

## Data
'''), code('''import hashlib, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import Image, display

root = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p/'verify/Q-NPF-04/allen_synphys/recovery_baseline_extrapolation_result.json').exists())
folder = root/'verify/Q-NPF-04/allen_synphys'
path = folder/'recovery_baseline_extrapolation_result.json'
result = json.loads(path.read_text(encoding='utf-8'))
def digest(p):
    with Path(p).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest(folder/'recovery_baseline_extrapolation.py') == result['code_sha256']
for key, name in dict(train='recovery_train_responses_result.json',
                     targets='ic_full_recording_qc_result.json',
                     inventory='ic_extended_inventory_result.json').items():
    assert digest(folder/name) == result['source_sha256'][key]
for asset in result['input_assets']:
    assert digest(root/asset['path']) == asset['sha256']
rows = result['records']
assert len(rows) == 680 and len(result['input_assets']) == 60
assert len(result['command_verification']['checks']) == 40
assert not result['command_verification']['missing_blocks']
print('Result SHA256:', digest(path))
print('Verified: 60 input archives, 480 actual responses, 200 gap contrasts, 40 target commands.')
print('Maximum old-response mismatch (uV):', result['old_response_reproduction']['max_abs_error_uV'])
'''), md('''## Results

### Contrast magnitude in the recovery gap
Each target/half summary retains every selected sweep and all five pseudo events.
A reduction alone would not establish isolation of the true evoked response.
'''), code('''print(f"{'Target':<10} {'Sweeps':<10} {'Old RMS/uV':>12} {'Linear RMS/uV':>15} {'Ratio':>8} {'Lower/sweeps':>14}")
for summary in result['summary']:
    if summary['kind'] != 'gap_control':
        continue
    old = np.array([r['old_uV'] for r in rows if r['kind']=='gap_control' and r['target']==summary['target']
                    and (summary['half']=='all' or (r['sweep']<=46)==(summary['half']=='early'))])
    assert np.sqrt(np.mean(old**2)) == summary['old']['rms_uV']
    print(f"{summary['target']:<10} {summary['half']:<10} {summary['old']['rms_uV']:12.3f} "
          f"{summary['linear']['rms_uV']:15.3f} {summary['rms_ratio']:8.3f} "
          f"{summary['sweeps_lower_linear_rms']:>7}/{summary['sweeps']:<6}")
noise = result['ideal_noise_geometry']
print('Ideal iid-window noise SD multiplier:', noise['sd_ratio'])
print(noise['assumption'])
'''), md('''### Actual pulse profiles and paired sweep controls
Top: actual contrasts, mean across 20 sweeps; shading is between-sweep SD, not a
confidence interval. Bottom: one point per sweep, RMS over its five gap windows.
Points above the identity line have larger magnitude after linear extrapolation.
The database labels “positive” and “negative” do not describe voltage signs.
'''), code('''plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout='constrained')
colors = {'old':'#176B9B', 'linear':'#C4581B'}
for col, target in enumerate(('positive', 'negative')):
    ax = axes[0,col]
    for method in ('old', 'linear'):
        values = np.array([[next(r[method+'_uV'] for r in rows
                            if r['kind']=='actual' and r['target']==target
                            and r['sweep']==sw and r['pulse']==pulse)
                            for pulse in range(1,13)] for sw in range(37,57)])
        mean, sd = values.mean(axis=0), values.std(axis=0, ddof=1)
        x = np.arange(1,13)
        ax.plot(x, mean, 'o-', color=colors[method], label=method)
        ax.fill_between(x, mean-sd, mean+sd, color=colors[method], alpha=.12)
    ax.axhline(0, color='#777777', linewidth=.8)
    ax.axvline(8.5, color='#777777', linewidth=.8, linestyle=':')
    ax.set(title=f'{target}: actual pulse contrasts', xlabel='Pulse index (8 to 9: recovery gap)', ylabel='Contrast (uV)')
    ax.set_xticks([1,4,8,9,12])
    ax.legend(frameon=False)
    ax = axes[1,col]
    summary = next(s for s in result['summary'] if s['target']==target and s['kind']=='gap_control' and s['half']=='all')
    pairs = summary['per_sweep']
    x = np.array([p['old_rms_uV'] for p in pairs])
    y = np.array([p['linear_rms_uV'] for p in pairs])
    for label, mask, marker in [('sweeps 37-46',np.arange(20)<10,'o'), ('sweeps 47-56',np.arange(20)>=10,'^')]:
        ax.scatter(x[mask],y[mask],label=label,marker=marker,s=42,alpha=.85)
    limit = max(x.max(),y.max())*1.08
    ax.plot([0,limit],[0,limit], '--',color='#555555',linewidth=1)
    ax.set(xlim=(0,limit), ylim=(0,limit), aspect='equal',
           title=f"{target}: gap RMS ratio = {summary['rms_ratio']:.2f}",
           xlabel='Old contrast RMS (uV)', ylabel='Linear contrast RMS (uV)')
    ax.legend(frameon=False,loc='lower right')
fig.suptitle('Recovery-gap measurement audit | one experiment, 20 repeated sweeps',fontsize=14)
figure = folder/'figures/recovery_baseline_extrapolation.png'
figure.parent.mkdir(exist_ok=True)
fig.savefig(figure,dpi=150)
display(Image(filename=str(figure)))
plt.close(fig)
'''), md(r'''## Takeaways
The output is a measurement diagnostic, not an estimate of synaptic efficacy or
learning. Affine extrapolation removes an affine baseline exactly but need not
remove a curved membrane tail and can amplify noise. Keep the original responses.

A fixed passive filter already contains an input history: \(V=K*I\).
In frequency coordinates, \(\widehat V=H(\omega)\widehat I\); a pure delay contributes
\(e^{-i\omega\tau_d}\), while a passive RC membrane contributes
\(R/(1+i\omega RC)\). Thus phase shifts and residual tails can arise with fixed
parameters. This candidate correction does not fit that physical filter.
[Primary textbook derivation](https://neuronaldynamics.epfl.ch/online/Ch1.S3.html).

Source-injected current is not target synaptic current. A future filter comparison
must model the measured input/output chain, preserve timing, and compare held-out
responses before attributing additional history dependence to plasticity.
''')]

notebook = nbformat.v4.new_notebook(cells=cells, metadata={'kernelspec':{
    'name':'ce-recovery-baseline', 'display_name':'CE policy wrapper', 'language':'python'}})
temporary = Path(tempfile.mkdtemp(prefix='ce-recovery-baseline-kernel-'))
kernel = temporary / 'kernels/ce-recovery-baseline'
kernel.mkdir(parents=True)
wrapper = Path(os.environ.get('CE_PYTHON_WRAPPER', str(ROOT / '.codex/hooks/python.cmd'))).resolve()
if not wrapper.is_file():
    raise FileNotFoundError('Set CE_PYTHON_WRAPPER to the preserved approved launcher')
spec = {'argv':[os.environ.get('COMSPEC','cmd.exe'),'/d','/c',str(wrapper),
                 'python','-m','ipykernel_launcher','-f','{connection_file}'],
        'display_name':'CE policy wrapper','language':'python',
        'env':{'CE_PYTHON':sys.executable,'PYTHONPATH':os.environ.get('PYTHONPATH','')}}
(kernel/'kernel.json').write_text(json.dumps(spec), encoding='utf-8')
os.environ['JUPYTER_PATH'] = str(temporary)+os.pathsep+os.environ.get('JUPYTER_PATH','')
nbformat.validate(notebook)
NotebookClient(notebook, timeout=180, kernel_name='ce-recovery-baseline',
               resources={'metadata':{'path':str(ROOT)}}).execute()
result = json.loads((HERE/'recovery_baseline_extrapolation_result.json').read_text(encoding='utf-8'))
lines = []
for row in result['summary']:
    if row['kind']=='gap_control' and row['half']=='all':
        lines.append(f"- {row['target']}: old RMS {row['old']['rms_uV']:.2f} uV; "
                     f"linear RMS {row['linear']['rms_uV']:.2f} uV; ratio {row['rms_ratio']:.2f}. "
                     f"Lower linear RMS in {row['sweeps_lower_linear_rms']}/20 sweeps.")
notebook.cells[0].source = notebook.cells[0].source.replace(
    'Computed values will be inserted after successful execution.',
    '\n'.join(lines)+'\n\nThese are observed contrast magnitudes, not errors against a known response.')
nbformat.validate(notebook)
nbformat.write(notebook, NOTEBOOK)
print('RECOVERY_BASELINE_NOTEBOOK_EXECUTED', NOTEBOOK)
