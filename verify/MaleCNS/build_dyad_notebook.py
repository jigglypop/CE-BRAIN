"""Execute a read-only result companion through the approved CE kernel."""

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
NOTEBOOK = OUT / "dyad_return_companion.ipynb"
PREVIEW = OUT / "dyad_return_companion.html"
FIGURES = OUT / "figures/dyad-return"
if any(path.exists() for path in (NOTEBOOK, PREVIEW, FIGURES)):
    raise FileExistsError("preserve existing companion outputs")
result = json.loads((OUT / "dyad_return_result.json").read_text(encoding="utf-8"))
md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
cells = [md(f"""# MaleCNS: Exact Dyads and Actual-ID Return Paths

## tl;dr
All {result['raw_rows']:,} raw records give {result['unique_dyads']:,} unique
directed segment pairs. {result['reciprocal_directed_fraction']:.4%} of nonself
dyads have a reverse edge. These are structural observations in one male CNS,
not measurements of neural activity or memory.

## Context & Methods
Every raw row is retained before exact duplicate aggregation. Reverse-key
lookup finds reciprocity; two-edge walks join on the actual middle ID.
Superclass-assigned endpoints include all 27 native categories.

### Key Assumptions
Self-edges remain in the cache but are excluded from the diagnostics below.
Post-only segments remain in the graph but cannot mediate a two-edge walk
in this observed version. Unknown segments are not assumed to be independent
neurons. Type identity is not anatomical ROI. Walk counts are unique triples,
not unique endpoint pairs, synapse chains, or independent biological replicates.

## Data
Source: https://male-cns.janelia.org/download/ ; version v1.0.
Full calculation: `verify/MaleCNS/dyad_return_paths.py`.
This companion reads its completed result and caches; it does not rescan Arrow.
"""), code("""import hashlib, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import Image, display
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'verify/MaleCNS/dyad_return_result.json').exists())
folder = root / 'verify/MaleCNS'
result_path = folder / 'dyad_return_result.json'
data = json.loads(result_path.read_text(encoding='utf-8'))
def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest(folder/'dyad_return_paths.py') == data['source_code_sha256']
assert digest(data['whole_result']) == data['whole_result_sha256']
for artifact in data['artifacts'].values():
    assert Path(artifact['path']).stat().st_size == artifact['bytes']
    assert digest(artifact['path']) == artifact['sha256']
keys = np.load(data['artifacts']['dyad_keys.npy']['path'], mmap_mode='r')
weights = np.load(data['artifacts']['dyad_weights.npy']['path'], mmap_mode='r')
assert len(keys) == len(weights) == data['unique_dyads']
figures = folder / 'figures/dyad-return'
figures.mkdir(parents=True)
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
print('Input and cache SHA-256 checks passed.')
print('Analysis environment:', data['software'])
print('Figure environment:', matplotlib.__version__, np.__version__)
"""), md("""## Results
### 1. Reciprocity and its denominator
The first panel counts nonself unique directed dyads. The second uses their
aggregate contact weights. A dyad can have a reverse edge with much smaller
weight, so reverse-edge weight and balanced minimum weight are distinct metrics.
All raw categories are preserved in the all-segment scope.
"""), code("""assigned_den = data['assigned_to_assigned_nonself_dyads']
assigned_num = data['assigned_to_assigned_reciprocal_dyads']
edge_values = [100*data['reciprocal_directed_fraction'], 100*assigned_num/assigned_den]
weight_values = [100*data['weight_on_reciprocal_edges_fraction'], 100*data['balanced_reciprocal_weight_fraction']]
fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), layout='constrained')
for ax, values, names, title in [
    (axes[0], edge_values, ['All raw segments', 'Assigned-neuron endpoints only'], 'Reverse edge exists: unique directed dyad denominator'),
    (axes[1], weight_values, ['Weight on reverse-connected edges', 'Balanced min(forward, reverse) weight'], 'All raw segments: nonself contact-weight denominator')]:
    bars = ax.barh(names, values, color='#2568a6', height=.5)
    ax.bar_label(bars, labels=[f'{v:.4f}%' for v in values], padding=5)
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.set_xlabel('Percent of the stated denominator')
    ax.set_title(title, fontsize=12)
    ax.grid(axis='x', alpha=.2)
    ax.set_axisbelow(True)
path = figures / 'exact_reciprocity.png'
fig.savefig(path, dpi=150)
plt.close(fig)
display(Image(filename=str(path), width=1000))
print(f"All: {data['reciprocal_directed_dyads']:,} / {data['nonself_unique_dyads']:,}")
print(f'Assigned endpoints: {assigned_num:,} / {assigned_den:,}')
print(f"Post-only target dyads: {data['terminal_target_dyads']:,}; weight: {data['terminal_target_weight']:,}")
"""), md("""### 2. Actual middle IDs
For each middle ID, multiply its incoming assigned-source count by its outgoing
assigned-target count. Closed walks return to the same starting ID; subtracting
them leaves three-distinct-ID paths. Dots use a log count axis, not a linear
length comparison. A zero would be labelled explicitly, not silently dropped.
"""), code("""rows = data['two_edge_paths']
names = ['Assigned neuron', 'Annotated glia', 'Annotated unclassified', 'Unannotated segment']
fig, ax = plt.subplots(figsize=(11, 5), layout='constrained')
for key, offset, color, marker, label in [
    ('three_distinct_id_paths', -.12, '#2568a6', 'o', 'Three distinct IDs'),
    ('closed_two_edge_walks_same_start_id', .12, '#b95732', 's', 'Same start/end ID')]:
    values = np.array([r[key] for r in rows], dtype=np.uint64)
    y = np.arange(len(rows)) + offset
    ax.scatter(np.maximum(values, 1), y, color=color, marker=marker, label=label, s=50)
    for value, yy in zip(values, y):
        ax.annotate(f'{int(value):,}', (max(int(value), 1), yy), xytext=(7, 0), textcoords='offset points', va='center', fontsize=10)
ax.set_yticks(range(len(rows)), names)
ax.invert_yaxis()
ax.set_xscale('log')
max_value = max(r['two_edge_walks_assigned_to_assigned'] for r in rows)
ax.set_xlim(.6, max(10, max_value*50))
ax.set_xlabel('Unique (start, middle, end) triples; logarithmic count scale')
ax.set_title('MaleCNS v1.0: assigned-neuron endpoints, all middle-ID categories')
ax.grid(axis='x', alpha=.2)
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.17), ncol=2)
path = figures / 'actual_id_two_edge_paths.png'
fig.savefig(path, dpi=150)
plt.close(fig)
display(Image(filename=str(path), width=1000))
for row in rows:
    assert row['two_edge_walks_assigned_to_assigned'] == row['three_distinct_id_paths'] + row['closed_two_edge_walks_same_start_id']
    print(row['middle_group'], 'mediators=', row['mediating_ids'], 'total triples=', row['two_edge_walks_assigned_to_assigned'])
"""), md("""### 3. Inspectable witnesses
These are deterministic high-count examples, not representative or held-out
samples. Each displayed path is verified against both packed raw-dyad keys.
Only the first witness per group is printed; all selected witnesses are checked.
"""), code("""for row in rows:
    for example in row['witnesses']:
        u, v, end = example['start_id'], example['middle_id'], example['end_id']
        query = np.array([(u << 32) | v, (v << 32) | end], dtype=np.uint64)
        positions = np.searchsorted(keys, query)
        assert np.all(positions < len(keys)) and np.array_equal(keys[positions], query)
        assert weights[positions].tolist() == example['edge_weights']
        assert (u == end) == example['backtrack']
    if row['witnesses']:
        print(row['middle_group'], json.dumps(row['witnesses'][0]))
print('All saved witnesses verified against the canonical raw graph.')
"""), md("""## Takeaways
Full-graph reciprocity and assigned-neuron-only reciprocity answer different
questions. Actual middle-ID joins separate supported structural paths from
artificial paths introduced by category aggregation. Missing annotation and
observed post-only segments remain explicit boundaries.

These observations do not identify neuronal dynamics, inhibitory signs, causal
memory, or a Riemannian metric. No confidence interval or p-value is inferred
from a single graph census. Next work compares hidden-state return operators
under a stated structural-walk model and separately investigates anatomical ROI.

Detailed methods and limitations: `ledger/malecns_dyad_return_findings.md`.
""")]
notebook = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {
    "name": "ce-malecns-dyads", "display_name": "CE policy wrapper", "language": "python"}})
temporary = Path(tempfile.mkdtemp(prefix="ce-malecns-dyad-kernel-"))
kernel = temporary / "kernels/ce-malecns-dyads"
kernel.mkdir(parents=True)
spec = {"argv": [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(ROOT / ".codex/hooks/python.cmd"),
                 "python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "CE policy wrapper", "language": "python",
        "env": {"CE_PYTHON": sys.executable, "PYTHONPATH": os.environ.get("PYTHONPATH", "")}}
(kernel / "kernel.json").write_text(json.dumps(spec), encoding="utf-8")
os.environ["JUPYTER_PATH"] = str(temporary) + os.pathsep + os.environ.get("JUPYTER_PATH", "")
nbformat.validate(notebook)
NotebookClient(notebook, timeout=180, kernel_name="ce-malecns-dyads",
               resources={"metadata": {"path": str(ROOT)}}).execute()
nbformat.validate(notebook)
nbformat.write(notebook, NOTEBOOK)
sections = []
for cell in notebook.cells:
    if cell.cell_type == "markdown":
        sections.append("<pre class='prose'>" + html.escape(cell.source) + "</pre>")
    else:
        sections.append("<details><summary>Calculation</summary><pre>" + html.escape(cell.source) + "</pre></details>")
        for output in cell.outputs:
            if output.output_type == "stream":
                sections.append("<pre>" + html.escape(output.text) + "</pre>")
            elif "image/png" in output.get("data", {}):
                data = output.data["image/png"]
                base64.b64decode(data, validate=True)
                sections.append("<img alt='Executed exact-dyad result' src='data:image/png;base64," + data + "'>")
PREVIEW.write_text("<!doctype html><meta charset='utf-8'><title>MaleCNS Exact Dyads</title><style>body{max-width:1100px;margin:32px auto;padding:0 24px;font:15px/1.5 sans-serif;color:#202020}pre{white-space:pre-wrap;overflow-wrap:anywhere}.prose{font:16px/1.6 sans-serif}img{max-width:100%;height:auto}details{border-top:1px solid #ccc;padding:12px 0}</style>" + "\n".join(sections), encoding="utf-8")
print("DYAD_NOTEBOOK_EXECUTED_AND_VALIDATED", NOTEBOOK, flush=True)
