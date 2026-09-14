"""Execute a small, inspectable companion of the completed projection analysis."""

import base64
import html
import json
import os
from pathlib import Path
import sys
import tempfile

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NOTEBOOK = OUT / "observation_memory_checked_companion.ipynb"
PREVIEW = OUT / "observation_memory_checked_companion.html"
FIGURES = OUT / "figures/observation-memory-checked"
if any(path.exists() for path in (NOTEBOOK, PREVIEW, FIGURES)):
    raise FileExistsError("preserve existing companion outputs")
md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
cells = [md("""# MaleCNS: Observation Boundaries and Projected Memory

## Context & Methods
All raw contact weights and active source IDs remain in the previously verified
absorbing walk. Thirty category outputs hide active versus terminal status;
sixty outputs preserve it. Both are compared with active-ID/terminal-category
information about the same uniform-versus-out-weight mixture coordinate.

### Key Assumptions
Terminal absorption is supplied, not observed neural cessation. Uniform and
out-weight lifting each fix a within-category active composition. The exact
memory identity uses graph-derived kernels and a known initial residual. It is
not independent neural prediction. Finite-lag forecasts use their own predicted
history, with no later truth injection, clipping, or renormalization.

## Data
Official input: https://male-cns.janelia.org/download/ ; v1.0 minconf-0.5.
This notebook reads `observation_memory_result.json` and its NPZ; it does not
rerun the full sparse propagation. The parent analysis and data registry retain
raw scope and source hashes. All 27 source cohorts remain in this report.

## tl;dr
The following values are computed from the completed, hash-checked result.
"""), code("""import hashlib, json, importlib.util
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from IPython.display import Image, display
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'verify/MaleCNS/observation_memory_result.json').exists())
folder = root/'verify/MaleCNS'
result = json.loads((folder/'observation_memory_result.json').read_text(encoding='utf-8'))
def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest(folder/'observation_memory.py') == result['source_code_sha256']
assert digest(root/'tests/test_malecns_observation_memory.py') == result['test_code_sha256']
assert digest(result['parent_result']) == result['parent_result_sha256']
for artifact in result['artifacts'].values():
    assert Path(artifact['path']).stat().st_size == artifact['bytes']
    assert digest(artifact['path']) == artifact['sha256']
with np.load(result['artifacts']['observation_memory_arrays.npz']['path']) as cache:
    truth, information, predictions = cache['truth'], cache['fisher'], cache['forecasts']
    markov, kernels, forcing = cache['markov'], cache['kernels'], cache['forcing']
    names, modes, references = cache['cohort_labels'].tolist(), cache['mode_labels'].tolist(), cache['reference_labels'].tolist()
tol, steps = result['numerical_tolerance'], result['steps']
assert truth.shape == (steps+1, 60, 54) and information.shape == (steps+1, 27, 3)
assert kernels.shape == (2, steps-1, 60, 30) and forcing.shape == (2, steps, 60, 54)
assert np.isfinite(predictions).all()
assert np.all(information[:, :, 0] <= information[:, :, 1]+tol)
assert np.all(information[:, :, 1] <= information[:, :, 2]+tol)
def fisher(pair):
    mean, delta = pair.mean(axis=1), pair[:, 1]-pair[:, 0]
    return np.divide(delta*delta, mean, out=np.zeros_like(mean), where=mean>0).sum()
for t in range(steps+1):
    for c in range(27):
        pair = truth[t, :, 2*c:2*c+2]
        np.testing.assert_allclose([fisher(pair[:30]+pair[30:]), fisher(pair)], information[t, c, :2], atol=tol, rtol=0)
errors = .5*np.abs(predictions-truth[None, None]).sum(axis=3)
peak_error = errors.max(axis=2)
for r in range(2):
    for m, model in enumerate(result['references'][r]['models']):
        np.testing.assert_allclose(errors[r, m], model['half_l1_by_step'], atol=tol, rtol=0)
assert peak_error[:, modes.index('history_full')].max() <= tol
figures = folder/'figures/observation-memory-checked'
figures.mkdir(parents=True)
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
print('Future category+boundary Fisher above numerical tolerance:', int(np.count_nonzero(information[1:, :, 1].max(axis=0)>tol)), '/ 27')
for r, reference in enumerate(references):
    matched = peak_error[r, modes.index('memoryless'), r::2]
    print(f'{reference}: matched memoryless max/median half-L1={matched.max():.8g}/{np.median(matched):.8g}; full-memory max={peak_error[r,modes.index("history_full")].max():.8g}')
print('All hashes, stored forecast errors and nested Fisher calculations checked.')
"""), md("""## Results
### 1. What the boundary flag preserves
Each bar partitions refined scalar Fisher into observed category information,
the additional information preserved by the active/terminal flag, and the
remaining loss from grouping active IDs. Bar width is normalized separately
within each cohort and step. These are nested-observation differences, not
causal contributions, physical signal flows, or cross-animal estimates.
"""), code("""fig, axes = plt.subplots(1, 2, figsize=(14, 12), sharey=True, layout='constrained')
colors = ['#2568a6', '#ba8528', '#c6cdd2']
legend_labels = ['30-category information', 'Additional boundary-flag information', 'Unresolved active-ID information']
for ax, t in zip(axes, [1, steps]):
    values = information[t]
    parts = np.column_stack((values[:, 0], values[:, 1]-values[:, 0], values[:, 2]-values[:, 1]))
    assert np.all(values[:, 2] > tol), 'cannot normalize numerically unresolved refined information'
    shares = parts / values[:, 2, None]
    assert np.min(shares) >= -1e-7
    np.testing.assert_allclose(shares.sum(axis=1), 1, atol=1e-12)
    left = np.zeros(27)
    for column, color, label in zip(shares.T, colors, legend_labels):
        ax.barh(np.arange(27), column, left=left, color=color, label=label, height=.7)
        left += column
    ax.set_yticks(range(27), names)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title(f'Step {t}', fontsize=12)
    ax.set_xlabel('Share of refined scalar Fisher at this step')
axes[0].invert_yaxis()
fig.legend(*axes[0].get_legend_handles_labels(), loc='outside lower center', ncol=1, fontsize=10)
path = figures/'boundary_information_partition.png'
fig.savefig(path, dpi=150)
plt.close(fig)
display(Image(filename=str(path), width=1100))
print('Exact, unnormalized Fisher values remain in the saved NPZ and JSON.')
"""), md("""### 2. Predicting from a finite history
Each thin line is one of all 27 source cohorts, with its initial distribution
matched to the indicated lifting. The known initial residual is then zero.
The horizontal axis counts past active-category vectors; lag 15 includes all
terms needed up to step 16. Errors use the worst separate step in 0..16.
The symmetric-log axis is linear close to numerical zero. Full memory is an
algebraic identity check, not a learned predictor or a fitted success criterion.
"""), code("""chosen = ['memoryless', 'history_1', 'history_2', 'history_4', 'history_8', 'history_full']
indices = [modes.index(name) for name in chosen]
lags = [result['references'][0]['models'][i]['memory_lags'] for i in indices]
fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True, layout='constrained')
for r, ax in enumerate(axes):
    values = peak_error[r, indices, r::2]
    ax.plot(lags, values, color='#b6bec4', linewidth=.7, alpha=.6)
    ax.plot(lags, np.median(values, axis=1), color='#2568a6', marker='o', label='Cohort median', linewidth=2)
    ax.plot(lags, values.max(axis=1), color='#b95732', marker='D', linestyle='--', label='Cohort maximum', linewidth=2)
    ax.set_yscale('symlog', linthresh=tol, linscale=.5)
    ax.set_yticks([0, *np.power(10., np.arange(-8, 0))])
    ax.set_xticks(lags)
    ax.set_xlim(-.3, max(lags)+.3)
    ax.set_ylim(bottom=0)
    ax.set_title(f'{references[r]} lifting; matched initial composition', fontsize=11)
    ax.set_xlabel('Retained memory lags')
    ax.grid(alpha=.2)
axes[0].set_ylabel('Maximum over model steps of half-L1 error')
upper = 1.2*float(peak_error[:, indices].max())
axes[0].set_ylim(0, max(upper, 10*tol))
fig.legend(*axes[0].get_legend_handles_labels(), loc='outside lower center', ncol=2)
path = figures/'memory_length_error.png'
fig.savefig(path, dpi=150)
plt.close(fig)
display(Image(filename=str(path), width=1100))
for r, reference in enumerate(references):
    for index in indices:
        values = peak_error[r, index, r::2]
        print(f'{reference}, {modes[index]}: median={np.median(values):.8g}, max={values.max():.8g}')
"""), md("""### 3. Initial hidden composition is a separate input
Here the initial source distribution is deliberately mismatched to the chosen
lifting. Initial-only uses the exact initial residual but no dynamic memory;
full-without-initial omits that residual despite retaining all dynamic kernels.
The complete identity has both. Every forecast after step zero uses its own
predicted history. The maximum error is half-L1 even if a truncated forecast
becomes signed; no probability repair has been performed.
"""), code("""fig, axes = plt.subplots(1, 2, figsize=(14, 12), sharey=True, layout='constrained')
series = [('initial_only', -.18, '#2568a6', 'o', 'Initial residual only'),
          ('history_full_no_initial', 0, '#b95732', 's', 'Full memory without initial residual'),
          ('history_full', .18, '#262626', 'x', 'Full memory with initial residual')]
max_value = max(float(peak_error[r, modes.index(name), 1-r::2].max()) for r in range(2) for name, *_ in series)
for r, ax in enumerate(axes):
    for name, shift, color, marker, label in series:
        values = peak_error[r, modes.index(name), 1-r::2]
        ax.scatter(values, np.arange(27)+shift, color=color, marker=marker, s=24, label=label)
    ax.set_yticks(range(27), names)
    ax.set_xlim(-.025*max_value, 1.08*max_value)
    ax.set_title(f'{references[r]} lifting; mismatched initial composition', fontsize=11)
    ax.set_xlabel('Maximum over model steps of half-L1 error')
    ax.grid(axis='x', alpha=.2)
    ax.set_axisbelow(True)
axes[0].invert_yaxis()
fig.legend(*axes[0].get_legend_handles_labels(), loc='outside lower center', ncol=1)
path = figures/'initial_residual_comparison.png'
fig.savefig(path, dpi=150)
plt.close(fig)
display(Image(filename=str(path), width=1100))
print('Validity checks count whole step/probe distributions, not individual entries:')
for reference in result['references']:
    for row in reference['models']:
        print(f'{reference["reference"]}, {row["name"]}: invalid={row["invalid_step_probe_distributions"]}; min={row["minimum_probability"]:.8g}; mass error={row["max_mass_error"]:.3g}')
"""), md("""## Takeaways and Limits
The boundary-aware observation and within-category residual address the same
fixed structural operator, not neural activity or independent samples. Source
categories with only two or four members are retained but do not gain population
generality. The signed residual operators are not physical paths or probabilities.

Full memory and a supplied initial residual reproduce a known linear system.
This does not show that a brain learns those kernels, that a finite history is
the best same-budget representation, or that a biological memory time was found.
Kernel construction uses the full graph and initial forcing uses hidden initial
composition. Forecast timing excludes those offline costs, and lag counts are
not a claim of total model size.

Connection-parameter derivatives, alternative boundaries, generic same-budget
reduction, held-out input families, ROI registration and biological calibration
remain separate next tests. Exact sources and interpretation are in
`ledger/malecns_observation_memory_findings.md`.
""")]
notebook = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {
    "name": "ce-malecns-observation", "display_name": "CE policy wrapper", "language": "python"}})
temporary = Path(tempfile.mkdtemp(prefix="ce-malecns-observation-kernel-"))
kernel = temporary/'kernels/ce-malecns-observation'
kernel.mkdir(parents=True)
spec = {"argv": [os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/c', str(ROOT/'.codex/hooks/python.cmd'),
                 'python', '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        "display_name": "CE policy wrapper", "language": "python",
        "env": {"CE_PYTHON": sys.executable, "PYTHONPATH": os.environ.get('PYTHONPATH', '')}}
(kernel/'kernel.json').write_text(json.dumps(spec), encoding='utf-8')
os.environ['JUPYTER_PATH'] = str(temporary) + os.pathsep + os.environ.get('JUPYTER_PATH', '')
nbformat.validate(notebook)
NotebookClient(notebook, timeout=180, kernel_name='ce-malecns-observation', resources={'metadata': {'path': str(ROOT)}}).execute()
nbformat.validate(notebook)
nbformat.write(notebook, NOTEBOOK)
sections = []
for cell in notebook.cells:
    if cell.cell_type == 'markdown':
        sections.append("<pre class='prose'>" + html.escape(cell.source) + '</pre>')
    else:
        sections.append('<details><summary>Calculation</summary><pre>' + html.escape(cell.source) + '</pre></details>')
        for output in cell.outputs:
            if output.output_type == 'stream':
                sections.append('<pre>' + html.escape(output.text) + '</pre>')
            elif 'image/png' in output.get('data', {}):
                data = output.data['image/png']
                base64.b64decode(data, validate=True)
                sections.append("<img alt='Executed boundary-aware memory result' src='data:image/png;base64," + data + "'>")
PREVIEW.write_text("<!doctype html><meta charset='utf-8'><title>MaleCNS Observation and Memory</title><style>body{max-width:1200px;margin:32px auto;padding:0 24px;font:15px/1.5 sans-serif;color:#202020}pre{white-space:pre-wrap;overflow-wrap:anywhere}.prose{font:16px/1.6 sans-serif}img{max-width:100%;height:auto}details{border-top:1px solid #ccc;padding:12px 0}</style>" + '\n'.join(sections), encoding='utf-8')
print('OBSERVATION_MEMORY_NOTEBOOK_EXECUTED_AND_VALIDATED', NOTEBOOK, flush=True)
