"""Execute and render a hash-checked companion of the connection tangent run."""

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
NOTEBOOK = OUT / "connection_fisher_companion.ipynb"
PREVIEW = OUT / "connection_fisher_companion.html"
SUMMARY = OUT / "connection_fisher_summary.json"
FIGURES = OUT / "figures/connection-fisher"
if any(path.exists() for path in (NOTEBOOK, PREVIEW, SUMMARY, FIGURES)):
    raise FileExistsError("preserve existing companion outputs")
md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
cells = [md("""# MaleCNS: Fixed-Support Connection Sensitivity

## tl;dr
The following summary is calculated from the completed, hash-checked full-graph
result. Three supplied log-efficacy coordinates are distinct from the earlier
initial-mixture coordinate. Common scaling of all outgoing weights at a source
is an exact null direction of this normalized model.
"""), code("""import hashlib, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from IPython.display import Image, display
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'verify/MaleCNS/connection_fisher_result.json').exists())
folder = root/'verify/MaleCNS'
result_path = folder/'connection_fisher_result.json'
result = json.loads(result_path.read_text(encoding='utf-8'))
def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest(folder/'connection_fisher.py') == result['source_code_sha256']
assert digest(root/'tests/test_malecns_connection_fisher.py') == result['test_code_sha256']
assert digest(result['parent_result']) == result['parent_result_sha256']
assert digest(result['dyad_result']) == result['dyad_result_sha256']
artifact = result['artifacts']['connection_fisher_arrays.npz']
assert Path(artifact['path']).stat().st_size == artifact['bytes']
assert digest(artifact['path']) == artifact['sha256']
with np.load(artifact['path']) as cache:
    truth, jac, information = cache['truth'], cache['jacobian'], cache['fisher']
    finite_difference, eigenvalues, rank = cache['finite_difference'], cache['eigenvalues'], cache['numerical_rank']
    threshold, eigenvectors = cache['rank_threshold'], cache['eigenvectors']
    names, features, levels = cache['cohort_labels'].tolist(), cache['feature_labels'].tolist(), cache['observation_labels'].tolist()
    h_values = cache['finite_difference_steps']
assert truth.shape == (17,60,54) and jac.shape == (17,60,54,4)
assert information.shape == (17,54,3,4,4) and finite_difference.shape == (3,2,17,60,54)
assert np.isfinite(information).all() and np.isfinite(jac).all()
assert np.all(jac[...,3] == 0) and np.all(information[...,3,:] == 0)
assert np.all(jac[0] == 0) and np.all(rank[0] == 0)
def fisher(p,j):
    assert not np.any(j[p==0] != 0)
    score = np.divide(j, np.sqrt(p)[...,None], out=np.zeros_like(j), where=p[...,None]>0)
    return np.einsum('omk,oml->mkl', score, score)
for t in range(17):
    np.testing.assert_allclose(fisher(truth[t],jac[t]), information[t,:,1], atol=5e-9, rtol=0)
    np.testing.assert_allclose(fisher(truth[t,:30]+truth[t,30:],jac[t,:30]+jac[t,30:]), information[t,:,0], atol=5e-9, rtol=0)
assert np.min(np.linalg.eigvalsh(information[:,:,1]-information[:,:,0])) >= -5e-9
assert np.min(np.linalg.eigvalsh(information[:,:,2]-information[:,:,1])) >= -5e-9
np.testing.assert_allclose(np.linalg.eigvalsh(information[:,:,:,:3,:3]),eigenvalues,atol=1e-13)
np.testing.assert_array_equal(np.sum(eigenvalues>threshold[...,None],axis=-1),rank)
# Explicit shape: feature, h, step, output, probe.
errors = np.stack([np.abs(finite_difference[k]-jac[None,:,:,:,k]) for k in range(3)])
assert np.max(errors)<=1e-6
for k in range(3):
    for hi in range(2):
        record=result['finite_difference'][2*k+hi]
        np.testing.assert_allclose(errors[k,hi].max(),record['max_absolute_error'],atol=1e-15)
        scaled=errors[k,hi]/(1e-8+1e-4*np.abs(jac[:,:,:,k]))
        assert scaled.max()<=1
figures=folder/'figures/connection-fisher'
figures.mkdir(parents=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
summary={'result_sha256':digest(result_path),'source_sha256':result['source_code_sha256'],
         'gauge_max_absolute_jacobian':float(np.abs(jac[...,3]).max()),'rank_rule':result['rank_rule'],
         'snapshots':[],'finite_difference':result['finite_difference']}
summary['feature_census']=[{'feature':row['feature'],
    'active_raw_id_dyads':row['active']['directed_dyads'],
    'terminal_source_category_cells':row['terminal']['directed_dyads'],
    'active_contact_weight':row['active']['contact_weight'],
    'terminal_contact_weight':row['terminal']['contact_weight']} for row in result['feature_census']]
for t in [1,16]:
    for r,reference in enumerate(['uniform','out_weight']):
        block=information[t,r::2,:,:3,:3]
        entry={'step':t,'reference':reference,'rank_counts_by_observation':{},'diagonal60':[]}
        for l,level in enumerate(levels):
            entry['rank_counts_by_observation'][level]=np.bincount(rank[t,r::2,l],minlength=4).tolist()
        diagonal=np.diagonal(block[:,1],axis1=-2,axis2=-1)
        for k,feature in enumerate(features[:3]):
            values=diagonal[:,k]
            entry['diagonal60'].append({'feature':feature,'min':float(values.min()),'median':float(np.median(values)),
                'max':float(values.max()),'min_cohort':names[int(values.argmin())],'max_cohort':names[int(values.argmax())],
                'at_or_below_1e_minus10': [names[i] for i in np.flatnonzero(values<=1e-10)]})
        traces=np.trace(block,axis1=-2,axis2=-1)
        entry['trace_fraction_of_refined']={}
        for l,level in enumerate(levels[:2]):
            values=np.divide(traces[:,l],traces[:,2],out=np.zeros(27),where=traces[:,2]>0)
            assert np.all(traces[:,2]>0)
            entry['trace_fraction_of_refined'][level]={'min':float(values.min()),'median':float(np.median(values)),
                'max':float(values.max()),'min_cohort':names[int(values.argmin())],'max_cohort':names[int(values.argmax())]}
        summary['snapshots'].append(entry)
        print(f'step {t}, {reference}: rank counts (0,1,2,3)={entry["rank_counts_by_observation"]}')
print('All 54 fixed probes; 3 structural coordinates plus exact gauge; all 60-output FD checks passed.')
print('Maximum finite-difference absolute error:',float(errors.max()))
"""), md("""## Context & Methods
The raw MaleCNS v1.0 minconf-0.5 contact graph is retained by the previously
verified active-ID/terminal-category operator. Three binary edge features tilt
contact weights by exp(theta dot feature), followed by a fresh normalization
over all outgoing contacts, including terminal targets and self contacts.
Features can overlap: active target; same assigned superclass including terminal
targets; reciprocal nonself on the original raw support.

### Key Assumptions
The uniform/out-weight initial distributions, IDs, observation maps and terminal
absorption remain fixed as theta changes. Steps are model steps, not neural time.
Superclass is not anatomical ROI. The Fisher matrix describes endpoint
probabilities in supplied dimensionless coordinates, not physical space,
observed plasticity, or an entire observed trajectory. No ridge or pseudocount
is used. Finite signed memory forecasts are not used as likelihoods.

## Data
Official source: https://male-cns.janelia.org/download/ . This companion reads the
sealed connection_fisher_result.json and its NPZ rather than rerunning all sparse
propagation. Analysis source, test, parent result, and derived NPZ hashes are
checked above. Full source scope and lineage remain in the separate data ledger.
The result census field named terminal.directed_dyads actually counts nonzero
source-by-terminal-category cells, not raw terminal ID dyads. Its contact_weight
still sums original contact weights. The summary uses explicit count names.

## Results
### 1. Sensitivity to each supplied connection coordinate
Each point is one of all 27 source cohorts. Four marks distinguish initial
weighting and endpoint step. Diagonal Fisher is per unit squared log-efficacy.
The axis is symmetric-log with a linear neighborhood of zero at 1e-10, so exact
zeros remain visible and are not replaced by small positive constants.
"""), code("""fig,axes=plt.subplots(1,3,figsize=(17,12),sharey=True,layout='constrained')
series=[(1,0,-.27,'#2667a2','o','Step 1, uniform'),(1,1,-.09,'#2667a2','x','Step 1, out-weight'),
        (16,0,.09,'#b65e31','o','Step 16, uniform'),(16,1,.27,'#b65e31','x','Step 16, out-weight')]
diagonal=np.diagonal(information[:,:,1,:3,:3],axis1=-2,axis2=-1)
upper=max(float(diagonal[[1,16]].max())*1.25,1e-8)
for k,ax in enumerate(axes):
    for t,r,offset,color,marker,label in series:
        ax.scatter(diagonal[t,r::2,k],np.arange(27)+offset,s=19,color=color,marker=marker,label=label)
    ax.set_yticks(range(27),names)
    ax.set_xscale('symlog',linthresh=1e-10)
    ax.set_xlim(-1e-11,upper)
    ticks=[0]+[10.**power for power in range(-8,2,2) if 10.**power<upper]
    ax.set_xticks(ticks)
    ax.set_xticklabels(['0']+[f'$10^{{{int(np.log10(value))}}}$' for value in ticks[1:]])
    ax.set_title(features[k].replace('_',' '),fontsize=12)
    ax.set_xlabel('60-output diagonal Fisher')
    ax.grid(axis='x',alpha=.2)
axes[0].invert_yaxis()
fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=2)
path=figures/'connection_coordinate_sensitivity.png'
fig.savefig(path,dpi=150)
plt.close(fig)
display(Image(filename=str(path),width=1200))
for entry in summary['snapshots']:
    print(entry['step'],entry['reference'],'60-output median diagonal:',[round(x['median'],8) for x in entry['diagonal60']])
"""), md("""### 2. Joint distinguishability after observation grouping
Rank is calculated from the full 3-by-3 structural Fisher matrix, not from three
positive diagonal entries. The threshold is 1e-10 times max(1, largest eigenvalue).
These are numerical ranks, not statistical significance. The fourth, common-scale
gauge coordinate is exactly zero at every observation and is excluded from the
displayed three-coordinate rank. Step zero has rank zero everywhere.
"""), code("""fig,axes=plt.subplots(1,2,figsize=(13,12),sharey=True,layout='constrained')
colors=ListedColormap(['#f1f1f1','#dcc88c','#8eb7bd','#285d83'])
norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4)
for r,ax in enumerate(axes):
    values=np.column_stack([rank[t,r::2,l] for t in [1,16] for l in range(3)])
    artist=ax.imshow(values,cmap=colors,norm=norm,aspect='auto',interpolation='nearest')
    for row in range(27):
        for col in range(6):
            ax.text(col,row,str(values[row,col]),ha='center',va='center',color='white' if values[row,col]==3 else '#202020',fontsize=10)
    ax.set_xticks(range(6),['30\\nt=1','60\\nt=1','Refined\\nt=1','30\\nt=16','60\\nt=16','Refined\\nt=16'])
    ax.set_yticks(range(27),names)
    ax.axvline(2.5,color='white',linewidth=3)
    ax.set_title(['Uniform fixed initial distribution','Out-weight fixed initial distribution'][r],fontsize=12)
fig.colorbar(artist,ax=axes,ticks=[0,1,2,3],label='Numerically resolved structural coordinates',shrink=.55)
path=figures/'observation_numerical_rank.png'
fig.savefig(path,dpi=150)
plt.close(fig)
display(Image(filename=str(path),width=1100))
for entry in summary['snapshots']:
    print(entry['step'],entry['reference'],'trace fractions of same-step refined Fisher:',entry['trace_fraction_of_refined'])
print('Trace fractions use the stated coordinates and are not a worst-direction guarantee.')
"""), md("""### 3. Independent nonlinear finite differences
Each point summarizes the maximum absolute Jacobian error over all 60 outputs
and steps 0..16 for one fixed initial distribution. Lines join the same probe
at central step sizes 1e-4 and 5e-5. All 54 probes remain visible. A decrease near
machine-roundoff floors is not required to follow an exact fourfold ratio.
The separate componentwise scaled-error criterion is also checked.
"""), code("""fig,axes=plt.subplots(1,3,figsize=(14,5),sharey=True,layout='constrained')
peak=errors.max(axis=(2,3))
for k,ax in enumerate(axes):
    for p in range(54):
        ax.plot([0,1],peak[k,:,p],color='#2667a2' if p%2==0 else '#b65e31',alpha=.45,linewidth=.8,
                marker='o' if p%2==0 else 'x',markersize=3)
    ax.set_xticks([0,1],['h = 1e-4','h = 5e-5'])
    ax.set_yscale('symlog',linthresh=1e-13)
    ax.set_ylim(0,max(float(peak.max())*1.5,1e-11))
    ticks=[0]+[10.**power for power in [-12,-10,-8,-6] if 10.**power<ax.get_ylim()[1]]
    ax.set_yticks(ticks)
    ax.set_yticklabels(['0']+[f'$10^{{{int(np.log10(value))}}}$' for value in ticks[1:]])
    ax.set_title(features[k].replace('_',' '),fontsize=11)
    ax.grid(axis='y',alpha=.2)
    ax.set_xlabel('Central finite-difference step')
axes[0].set_ylabel('Max absolute error over endpoints and outputs')
axes[0].plot([],[],color='#2667a2',marker='o',label='Uniform fixed initial distribution')
axes[0].plot([],[],color='#b65e31',marker='x',label='Out-weight fixed initial distribution')
fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=2)
path=figures/'finite_difference_convergence.png'
fig.savefig(path,dpi=150)
plt.close(fig)
display(Image(filename=str(path),width=1100))
summary['finite_difference_probe_max_error']=peak.tolist()
summary['rank_deficient_future_cases']=[]
for t,p,l in np.argwhere(rank[1:]<3):
    summary['rank_deficient_future_cases'].append({'step':int(t+1),'cohort':names[int(p)//2],
        'reference':['uniform','out_weight'][int(p)%2],'observation':levels[int(l)],
        'rank':int(rank[t+1,p,l]),'eigenvalues':eigenvalues[t+1,p,l].tolist(),
        'smallest_eigenvector':eigenvectors[t+1,p,l,:,0].tolist()})
summary['near_zero_coordinate_cases']=[]
for p,k in np.argwhere(np.max(np.abs(jac[1:,:,:,:3]),axis=(0,1))<=1e-10):
    summary['near_zero_coordinate_cases'].append({'cohort':names[int(p)//2],
        'reference':['uniform','out_weight'][int(p)%2],'feature':features[int(k)]})
with (folder/'connection_fisher_summary.json').open('x',encoding='utf-8') as stream:
    json.dump(summary,stream,indent=2,allow_nan=False)
    stream.write('\\n')
print('Maximum absolute/scaled FD errors by feature and h:')
for row in result['finite_difference']:
    print(row['feature'],row['step_size'],row['max_absolute_error'],row['max_scaled_error'])
print('Future rank-deficient step/probe/observation cases:',len(summary['rank_deficient_future_cases']))
print('60-output coordinate tangents <=1e-10 throughout:',summary['near_zero_coordinate_cases'])
"""), md("""## Takeaways and Limits
Connection sensitivity and observation loss are properties of a supplied
contact-supported probability model on one static animal. Numerical rank can
depend on the coordinate definitions, initial probe, endpoint and observation.
The common-source gauge cancels by algebraic normalization, not because all
absolute biological efficacy changes are impossible to observe.

The coarse Fisher matrices are independently recomputed above from saved
probabilities and Jacobians. Refined Fisher is streamed over active IDs by the
full analysis and is hash-checked here; the full active-ID Jacobian is not stored
by this companion. No claim of temporal Fisher contraction, physical curvature,
biological learning, or independent-animal replication follows.

Same-budget probability-preserving reduction, new input families, alternative
boundary models, ROI registration and functional calibration remain unfinished.
Exact evidence and interpretation: ledger/malecns_connection_fisher_findings.md.
""")]
notebook = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {
    "name": "ce-malecns-connection", "display_name": "CE policy wrapper", "language": "python"}})
temporary = Path(tempfile.mkdtemp(prefix="ce-malecns-connection-kernel-"))
kernel = temporary / "kernels/ce-malecns-connection"
kernel.mkdir(parents=True)
spec = {"argv": [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(ROOT / ".codex/hooks/python.cmd"),
                 "python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "CE policy wrapper", "language": "python",
        "env": {"CE_PYTHON": sys.executable, "PYTHONPATH": os.environ.get("PYTHONPATH", "")}}
(kernel / "kernel.json").write_text(json.dumps(spec), encoding="utf-8")
os.environ["JUPYTER_PATH"] = str(temporary) + os.pathsep + os.environ.get("JUPYTER_PATH", "")
nbformat.validate(notebook)
NotebookClient(notebook, timeout=180, kernel_name="ce-malecns-connection", resources={"metadata": {"path": str(ROOT)}}).execute()
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
                sections.append("<img alt='Executed connection sensitivity result' src='data:image/png;base64," + data + "'>")
PREVIEW.write_text("<!doctype html><meta charset='utf-8'><title>MaleCNS Connection Sensitivity</title><style>body{max-width:1200px;margin:32px auto;padding:0 24px;font:15px/1.5 sans-serif;color:#202020}pre{white-space:pre-wrap;overflow-wrap:anywhere}.prose{font:16px/1.6 sans-serif}img{max-width:100%;height:auto}details{border-top:1px solid #ccc;padding:12px 0}</style>" + "\n".join(sections), encoding="utf-8")
print("CONNECTION_FISHER_NOTEBOOK_EXECUTED_AND_VALIDATED", NOTEBOOK, flush=True)
