"""Execute an inspectable companion of exact pair and complete-path information."""

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
NOTEBOOK = OUT / "history_fisher_companion.ipynb"
PREVIEW = OUT / "history_fisher_companion.html"
SUMMARY = OUT / "history_fisher_summary.json"
FIGURES = OUT / "figures/history-fisher"
if any(path.exists() for path in (NOTEBOOK, PREVIEW, SUMMARY, FIGURES)):
    raise FileExistsError("preserve existing companion outputs")
md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
cells = [md("""# MaleCNS: Endpoint, Adjacent Pair, and Full-Path Information

## tl;dr
The following values are computed from the completed, hash-checked run. An
adjacent observation pair is a true two-time marginal, not the entire coarse
history. Full-path Fisher uses all active raw IDs and terminal category from
step zero. These observations have different information and recording costs.
"""), code("""import hashlib, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.ticker import PercentFormatter
from IPython.display import Image, display
root=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'verify/MaleCNS/history_fisher_result.json').exists())
folder=root/'verify/MaleCNS'
result_path=folder/'history_fisher_result.json'
result=json.loads(result_path.read_text(encoding='utf-8'))
def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()
assert digest(folder/'history_fisher.py')==result['source_code_sha256']
assert digest(root/'tests/test_malecns_history_fisher.py')==result['test_code_sha256']
assert digest(result['parent_result'])==result['parent_result_sha256']
parent=json.loads(Path(result['parent_result']).read_text(encoding='utf-8'))
assert digest(folder/'connection_fisher.py')==result['parent_source_sha256']==parent['source_code_sha256']
artifact=result['artifacts']['history_fisher_arrays.npz']
assert Path(artifact['path']).stat().st_size==artifact['bytes'] and digest(artifact['path'])==artifact['sha256']
parent_cache=parent['artifacts']['connection_fisher_arrays.npz']
assert digest(parent_cache['path'])==parent_cache['sha256']
with np.load(parent_cache['path']) as cache:
    endpoint_truth,endpoint_jac=cache['truth'],cache['jacobian']
    endpoint_information=cache['fisher']
with np.load(artifact['path']) as cache:
    pair,jac,g=cache['pair_probability'],cache['pair_jacobian'],cache['fisher']
    fd,eigen,rank=cache['finite_difference'],cache['eigenvalues'],cache['numerical_rank']
    nonnested=cache['pair60_minus_refined_eigenvalues']
    names,features,levels=cache['cohort_labels'].tolist(),cache['feature_labels'].tolist(),cache['observation_labels'].tolist()
assert pair.shape==(17,60,60,54) and jac.shape==(17,60,60,54,4)
assert g.shape==(17,54,6,4,4) and fd.shape==(3,2,17,60,60,54)
assert np.isfinite(pair).all() and np.min(pair)>=0 and np.isfinite(jac).all()
np.testing.assert_allclose(pair.sum(axis=(1,2)),1,atol=5e-9,rtol=0)
np.testing.assert_allclose(jac.sum(axis=(1,2)),0,atol=5e-9,rtol=0)
np.testing.assert_allclose(pair[1:].sum(axis=2),endpoint_truth[:-1],atol=5e-9,rtol=0)
np.testing.assert_allclose(pair[1:].sum(axis=1),endpoint_truth[1:],atol=5e-9,rtol=0)
np.testing.assert_allclose(jac[1:].sum(axis=2),endpoint_jac[:-1],atol=5e-9,rtol=0)
np.testing.assert_allclose(jac[1:].sum(axis=1),endpoint_jac[1:],atol=5e-9,rtol=0)
np.testing.assert_array_equal(g[:,:,:3],endpoint_information)
assert np.all(jac[...,3]==0) and np.all(g[...,3,:]==0)
def fisher(p,j):
    assert not np.any(j[p==0]!=0)
    score=np.divide(j,np.sqrt(p)[...,None],out=np.zeros_like(j),where=p[...,None]>0)
    return np.einsum('omk,oml->mkl',score,score)
def coarse(value):
    return value[:30,:30]+value[:30,30:]+value[30:,:30]+value[30:,30:]
for t in range(17):
    np.testing.assert_allclose(fisher(pair[t].reshape(-1,54),jac[t].reshape(-1,54,4)),g[t,:,4],atol=5e-9,rtol=0)
    np.testing.assert_allclose(fisher(coarse(pair[t]).reshape(-1,54),coarse(jac[t]).reshape(-1,54,4)),g[t,:,3],atol=5e-9,rtol=0)
for larger,smaller in [(3,0),(4,1),(4,3),(5,4),(5,2)]:
    assert np.linalg.eigvalsh(g[:,:,larger]-g[:,:,smaller]).min()>=-5e-9
assert np.linalg.eigvalsh(g[1:,:,4]-g[:-1,:,1]).min()>=-5e-9
assert np.linalg.eigvalsh(np.diff(g[:,:,5],axis=0)).min()>=-5e-9
np.testing.assert_allclose(g[1,:,4],g[1,:,1],atol=5e-9,rtol=0)
np.testing.assert_allclose(np.linalg.eigvalsh(g[:,:,:,:3,:3]),eigen,atol=1e-12)
np.testing.assert_array_equal(np.sum(eigen>1e-10*np.maximum(1,eigen[...,-1])[...,None],axis=-1),rank)
np.testing.assert_allclose(np.linalg.eigvalsh(g[:,:,4,:3,:3]-g[:,:,2,:3,:3]),nonnested,atol=1e-12)
trace=np.trace(g[:,:,:,:3,:3],axis1=-2,axis2=-1)
assert np.min(trace[1:])>0
cut=5e-9*np.maximum(1,np.max(np.abs(nonnested),axis=-1))
negative,positive=nonnested[...,0]<-cut,nonnested[...,-1]>cut
comparison=np.where(negative&positive,3,np.where(positive,2,np.where(negative,0,1)))
comparison_labels=['Refined endpoint dominates','Numerically equal','Adjacent pair dominates','Direction-dependent / indefinite']
summary={'result_sha256':digest(result_path),'snapshots':[],'nonnested_order_labels':comparison_labels,
         'nonnested_order_counts_by_step':[],'finite_difference':result['finite_difference'],
         'gauge_max_absolute_tangent':float(np.abs(jac[...,3]).max()),'rank_rule':result['rank_rule']}
def stats(values):
    return {'min':float(values.min()),'median':float(np.median(values)),'max':float(values.max()),
            'min_cohort':names[int(values.argmin())],'max_cohort':names[int(values.argmax())]}
for t in [1,2,4,8,16]:
    for r,reference in enumerate(['uniform','out_weight']):
        values=trace[t,r::2]
        extra=values[:,4]-values[:,1]
        summary['snapshots'].append({'step':t,'reference':reference,
            'trace_by_observation':{level:stats(values[:,l]) for l,level in enumerate(levels)},
            'pair60_extra_past_trace':stats(extra),'endpoint60_fraction_of_pair60':stats(values[:,1]/values[:,4]),
            'pair60_fraction_of_path':stats(values[:,4]/values[:,5]),'endpoint60_fraction_of_path':stats(values[:,1]/values[:,5]),
            'extra_past_positive_cohorts':int(np.count_nonzero(extra>5e-9)),
            'nonnested_counts':np.bincount(comparison[t,r::2],minlength=4).tolist(),
            'rank_counts':{level:np.bincount(rank[t,r::2,l],minlength=4).tolist() for l,level in enumerate(levels)}})
for t in range(1,17):
    summary['nonnested_order_counts_by_step'].append({'step':t,'all54_counts':np.bincount(comparison[t],minlength=4).tolist()})
for t in [1,2,16]:
    print('step',t,'pair-minus-refined order counts:',np.bincount(comparison[t],minlength=4).tolist())
print('Exact previous/current marginals, independent pair Fisher, gauge and nested Loewner checks passed.')
figures=folder/'figures/history-fisher'
figures.mkdir(parents=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
"""), md("""## Context & Methods
Three overlapping binary features tilt the same full contact weights, with
normalization over every active, terminal and self destination. The initial
uniform/out-weight probes and observations remain fixed as efficacy changes.
The adjacent-pair probability is summed from the full hidden state, not obtained
by multiplying a coarse Markov model or independent endpoint probabilities.

### Key Assumptions
Terminal absorption is supplied. Steps are model steps, not neural time.
Full-path Fisher sums expected conditional transition-score covariances, including
all feature cross terms. It does not sum endpoint Fisher. Terminal raw-ID
compression is sufficient for the chosen full-path score only when the previous
raw source ID is also observed. This is not a statement about terminal endpoint
ID information, all possible efficacy coordinates, or coarse-history sufficiency.

## Data
Official raw source: https://male-cns.janelia.org/download/ . MaleCNS v1.0,
minconf-0.5. All raw connections remain in the source operator. This companion
reads sealed history_fisher_result.json and its NPZ plus the sealed parent.
Full-path information is checked against tiny fully enumerated paths by tests;
the complete real graph's astronomical path set is not enumerated here.

## Results
### 1. Which observation retains information over the horizon?
Each line is a median over all 27 source cohorts, separately for the two fixed
initial distributions. Curves are not confidence intervals or independent-animal
estimates. Trace uses the stated three structural coordinates and is coordinate
dependent. Step zero has zero information for every coordinate and is omitted
from the logarithmic plot. Increasing full-path information is not a claim that
an adjacent pair or current endpoint must gain information over time.
"""), code("""fig,axes=plt.subplots(1,2,figsize=(14,5.5),sharey=True,layout='constrained')
styles=[(0,'#2667a2',':','Endpoint 30'),(1,'#2667a2','-','Endpoint 60'),
        (2,'#777777','--','Refined endpoint'),(3,'#a56d1c',':','Adjacent pair 30'),
        (4,'#a56d1c','-','Adjacent pair 60'),(5,'#222222','-','Full raw-ID path')]
for r,ax in enumerate(axes):
    for l,color,style,label in styles:
        ax.plot(range(1,17),np.median(trace[1:,r::2,l],axis=1),color=color,linestyle=style,
                linewidth=2 if l==5 else 1.6,label=label)
    ax.set_yscale('log')
    ax.set_xticks([1,4,8,12,16])
    ax.set_xlabel('Endpoint model step')
    ax.set_title(['Uniform fixed initial distribution','Out-weight fixed initial distribution'][r],fontsize=12)
    ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Median trace Fisher across 27 cohorts')
fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=3)
path=figures/'endpoint_pair_path_information.png'
fig.savefig(path,dpi=150)
plt.close(fig)
display(Image(filename=str(path),width=1100))
for item in summary['snapshots']:
    if item['step'] in [1,16]:
        print(item['step'],item['reference'],'trace medians:',{k:round(v['median'],8) for k,v in item['trace_by_observation'].items()})
"""), md("""### 2. What the immediately preceding observation adds
Each point gives current endpoint-60 trace divided by adjacent-pair-60 trace for
one of all 27 cohorts. A value below 100% indicates information available in the
previous observation after the current one is known. It is a ratio of Fisher
traces, not a fraction of observations, a worst-direction guarantee, or a claim
that all older history is preserved. Step 1 equals 100% because the initial
category is fixed within each probe.
"""), code("""fig,axes=plt.subplots(1,2,figsize=(13,12),sharey=True,layout='constrained')
for r,ax in enumerate(axes):
    for t,offset,color,marker,label in [(2,-.12,'#2667a2','o','Step 2'),(16,.12,'#a56d1c','x','Step 16')]:
        values=trace[t,r::2,1]/trace[t,r::2,4]
        assert np.min(values)>=0 and np.max(values)<=1+1e-7
        ax.scatter(values,np.arange(27)+offset,color=color,marker=marker,s=26,label=label)
    ax.set_yticks(range(27),names)
    ax.set_xlim(0,1.025)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel('Current endpoint trace / adjacent-pair trace')
    ax.set_title(['Uniform fixed initial distribution','Out-weight fixed initial distribution'][r],fontsize=12)
    ax.grid(axis='x',alpha=.2)
axes[0].invert_yaxis()
fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=2)
path=figures/'previous_observation_information_share.png'
fig.savefig(path,dpi=150)
plt.close(fig)
display(Image(filename=str(path),width=1100))
for item in summary['snapshots']:
    if item['step'] in [2,16]:
        print(item['step'],item['reference'],'endpoint/pair:',item['endpoint60_fraction_of_pair60'])
        print('pair/path:',item['pair60_fraction_of_path'],'extra-positive cohorts:',item['extra_past_positive_cohorts'])
"""), md("""### 3. More history versus a more detailed current observation
The adjacent pair and refined current endpoint are not nested observations.
For each cohort and step, the matrix pair60 minus refined-endpoint Fisher is
classified by its minimum and maximum eigenvalues with threshold 5e-9 times
max(1, maximum absolute eigenvalue). Indefinite means that the preferred
observation depends on the direction of efficacy change. Dominance/equality
labels are numerical classifications, not universal theorems or significance.
"""), code("""fig,axes=plt.subplots(1,2,figsize=(16,12),sharey=True,layout='constrained')
cmap=ListedColormap(['#5b88a6','#ededed','#aa5263','#d5b55e'])
norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4)
for r,ax in enumerate(axes):
    values=comparison[1:,r::2].T
    artist=ax.imshow(values,cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')
    ax.set_xticks(range(16),range(1,17))
    ax.set_yticks(range(27),names)
    ax.set_xlabel('Endpoint model step (pair uses previous and current)')
    ax.set_title(['Uniform fixed initial distribution','Out-weight fixed initial distribution'][r],fontsize=12)
colorbar=fig.colorbar(artist,ax=axes,location='bottom',ticks=range(4),shrink=.85,pad=.04)
colorbar.ax.set_xticklabels(['Refined dominates','Numerically equal','Pair dominates','Direction-dependent'])
path=figures/'history_vs_current_resolution.png'
fig.savefig(path,dpi=150)
plt.close(fig)
display(Image(filename=str(path),width=1200))
for row in summary['nonnested_order_counts_by_step']:
    print(row['step'],row['all54_counts'])
"""), md("""### 4. Independent nonlinear checks of the entire joint likelihood
For each of all 54 probes, the plotted error is the maximum over 3,600 joint
outcomes and steps 0..16. The two central finite-difference step sizes use fully
renormalized nonlinear operators, including terminal weights. The analytic
joint Jacobian is not used in the nonlinear forward calculation. The vertical
scale is symlog with a linear neighborhood below 1e-13 so exact zeros are not
replaced by artificial positive values.
"""), code("""peak=np.empty((3,2,54))
for k in range(3):
    for hi in range(2):
        error=np.abs(fd[k,hi]-jac[:,:,:,:,k])
        scaled=error/(1e-8+1e-4*np.abs(jac[:,:,:,:,k]))
        assert error.max()<=1e-6 and scaled.max()<=1
        record=result['finite_difference'][2*k+hi]
        np.testing.assert_allclose(error.max(),record['max_absolute_error'],atol=1e-15)
        np.testing.assert_allclose(scaled.max(),record['max_scaled_error'],atol=1e-12)
        peak[k,hi]=error.max(axis=(0,1,2))
fig,axes=plt.subplots(1,3,figsize=(14,5),sharey=True,layout='constrained')
for k,ax in enumerate(axes):
    for p in range(54):
        ax.plot([0,1],peak[k,:,p],color='#2667a2' if p%2==0 else '#a56d1c',alpha=.45,
                linewidth=.8,marker='o' if p%2==0 else 'x',markersize=3)
    ax.set_xticks([0,1],['h = 1e-4','h = 5e-5'])
    ax.set_yscale('symlog',linthresh=1e-13)
    ax.set_ylim(0,max(float(peak.max())*1.5,1e-11))
    ticks=[0]+[10.**power for power in [-12,-10,-8,-6] if 10.**power<ax.get_ylim()[1]]
    ax.set_yticks(ticks)
    ax.set_yticklabels(['0']+[f'$10^{{{int(np.log10(value))}}}$' for value in ticks[1:]])
    ax.set_title(features[k].replace('_',' '),fontsize=11)
    ax.set_xlabel('Central finite-difference step')
    ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Max absolute joint-Jacobian error')
axes[0].plot([],[],color='#2667a2',marker='o',label='Uniform fixed initial distribution')
axes[0].plot([],[],color='#a56d1c',marker='x',label='Out-weight fixed initial distribution')
fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=2)
path=figures/'joint_finite_difference_convergence.png'
fig.savefig(path,dpi=150)
plt.close(fig)
display(Image(filename=str(path),width=1100))
summary['finite_difference_probe_max_error']=peak.tolist()
summary['rank_deficient_future_cases']=[]
for t,p,l in np.argwhere(rank[1:]<3):
    summary['rank_deficient_future_cases'].append({'step':int(t+1),'cohort':names[int(p)//2],
        'reference':['uniform','out_weight'][int(p)%2],'observation':levels[int(l)],
        'rank':int(rank[t+1,p,l]),'eigenvalues':eigen[t+1,p,l].tolist()})
pair_increment=np.linalg.eigvalsh(np.diff(g[1:,:,4,:3,:3],axis=0))
limit=5e-9*np.maximum(1,np.max(np.abs(pair_increment),axis=-1))
summary['pair60_decreasing_transition_probe_cells']=int(np.count_nonzero(pair_increment[...,0]<-limit))
summary['pair60_decreasing_probe_count']=int(np.count_nonzero(np.any(pair_increment[...,0]<-limit,axis=0)))
summary['past_gain_by_step']=[]
for t in range(1,17):
    extra=trace[t,:,4]-trace[t,:,1]
    summary['past_gain_by_step'].append({'step':t,'positive_probes':int(np.count_nonzero(extra>5e-9)),
        'min_extra_trace':float(extra.min()),'median_extra_trace':float(np.median(extra)),'max_extra_trace':float(extra.max())})
with (folder/'history_fisher_summary.json').open('x',encoding='utf-8') as stream:
    json.dump(summary,stream,indent=2,allow_nan=False)
    stream.write('\\n')
print('Joint FD maxima:',[(r['feature'],r['step_size'],r['max_absolute_error']) for r in result['finite_difference']])
print('Pair60 time steps with at least one decreasing direction:',summary['pair60_decreasing_transition_probe_cells'])
print('Future rank-deficient step/probe/observation cells:',len(summary['rank_deficient_future_cases']))
"""), md("""## Takeaways and Limits
An adjacent two-time marginal is a valid probability observation, unlike an
unrepaired signed finite-memory approximation. It still omits most older
history and hidden IDs. A full path has more detailed observations and a longer
recording budget; superiority to a same-budget model has not been tested.

All quantities come from one static animal's full contact-supported probability
proxy with supplied absorption, not observed neural trajectories. Rank and
trace depend on the fixed coordinate and observation choices. No biological
memory, learning, physical space metric, neural time, or independent animal
replication is established. Full coarse-history likelihoods, generic
probability-preserving reductions, new probes, alternative boundaries and
functional calibration remain unfinished.

Sources, hashes, numerical failures and claim boundaries are kept separately
in ledger/malecns_history_fisher_findings.md.
""")]
notebook = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {
    "name": "ce-malecns-history", "display_name": "CE policy wrapper", "language": "python"}})
temporary = Path(tempfile.mkdtemp(prefix="ce-malecns-history-kernel-"))
kernel = temporary / "kernels/ce-malecns-history"
kernel.mkdir(parents=True)
spec = {"argv": [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(ROOT / ".codex/hooks/python.cmd"),
                 "python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "CE policy wrapper", "language": "python",
        "env": {"CE_PYTHON": sys.executable, "PYTHONPATH": os.environ.get("PYTHONPATH", "")}}
(kernel / "kernel.json").write_text(json.dumps(spec), encoding="utf-8")
os.environ["JUPYTER_PATH"] = str(temporary) + os.pathsep + os.environ.get("JUPYTER_PATH", "")
nbformat.validate(notebook)
NotebookClient(notebook, timeout=240, kernel_name="ce-malecns-history", resources={"metadata": {"path": str(ROOT)}}).execute()
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
                sections.append("<img alt='Executed history information result' src='data:image/png;base64," + data + "'>")
PREVIEW.write_text("<!doctype html><meta charset='utf-8'><title>MaleCNS History Information</title><style>body{max-width:1200px;margin:32px auto;padding:0 24px;font:15px/1.5 sans-serif;color:#202020}pre{white-space:pre-wrap;overflow-wrap:anywhere}.prose{font:16px/1.6 sans-serif}img{max-width:100%;height:auto}details{border-top:1px solid #ccc;padding:12px 0}</style>" + "\n".join(sections), encoding="utf-8")
print("HISTORY_FISHER_NOTEBOOK_EXECUTED_AND_VALIDATED", NOTEBOOK, flush=True)
