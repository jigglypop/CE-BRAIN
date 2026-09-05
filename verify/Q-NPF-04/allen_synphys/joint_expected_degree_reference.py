"""입출력 차수와 거리별 연결 수를 기대값으로 맞춘 독립 Bernoulli 기준."""
import csv,json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit
import microns_constrained_swaps as base
HERE=base.HERE


def fit(a,c):
    n=len(a);out=a.sum(1);inc=a.sum(0);bin_counts=np.bincount(c[a],minlength=6)
    allowed=(~np.eye(n,dtype=bool))&(out[:,None]>0)&(inc[None,:]>0)&(bin_counts[c]>0)
    assert not np.any(a&~allowed)
    u,v=np.nonzero(allowed);b=c[u,v];y=a[u,v].astype(float)
    def objective(theta):
        z=theta[u]+theta[n+v]+theta[2*n+b]
        error=expit(z)-y
        gradient=np.concatenate([np.bincount(u,weights=error,minlength=n),np.bincount(v,weights=error,minlength=n),np.bincount(b,weights=error,minlength=6)])
        return float(np.sum(np.logaddexp(0,z)-y*z)),gradient
    theta=np.zeros(2*n+6)
    if len(y):
        density=float(y.mean());theta[2*n:]=np.log(density/(1-density)) if 0<density<1 else 0
        result=minimize(objective,theta,jac=True,method='L-BFGS-B',options=dict(maxiter=4000,maxls=50,ftol=1e-15,gtol=1e-8,maxcor=30))
        theta=result.x
        p=np.zeros((n,n));p[u,v]=expit(theta[u]+theta[n+v]+theta[2*n+b])
        residuals=np.concatenate([p.sum(1)-out,p.sum(0)-inc,np.bincount(c[u,v],weights=p[u,v],minlength=6)-bin_counts])
        error=float(np.max(abs(residuals)))
        diagnostic=dict(optimizer_success=bool(result.success),message=str(result.message),iterations=int(result.nit),
            max_absolute_margin_error=error,max_abs_parameter=float(np.max(abs(theta))),objective=float(result.fun))
    else:
        p=np.zeros((n,n));diagnostic=dict(optimizer_success=True,message='all-zero graph',iterations=0,max_absolute_margin_error=0,max_abs_parameter=0,objective=0)
    diagnostic['gate_pass']=diagnostic['max_absolute_margin_error']<=1e-5
    return p,theta,diagnostic


def main():
    a=np.zeros((4,4),dtype=bool);a[np.arange(4),(np.arange(4)+1)%4]=True
    p,_,d=fit(a,np.zeros((4,4),dtype=int));assert d['gate_pass'] and np.allclose(p[~np.eye(4,dtype=bool)],1/3,atol=1e-8)
    minnie=json.loads(base.CONTRACT.read_text())['source_sha256']
    pinky=json.loads((HERE/'pinky_local_contract.json').read_text())['source_sha256']
    sources={**{str((HERE/k if (HERE/k).exists() else base.DATA/k).relative_to(base.ROOT)):v for k,v in minnie.items()},**pinky}
    spec=dict(question='Does reciprocal excess persist when both node degrees and global distance-bin counts are matched in expectation?',
        model='p_ij=logistic(alpha_i+beta_j+gamma_distance); directed edges independent; exact-zero out/in/bin margins remove impossible entries; no penalty or clipping',
        constraints='expected total out-degree per node, expected total in-degree per node, expected global edge count per distance bin; not per-node distance counts and not exact microcanonical degrees',
        scope='Pinky362 as-released e primary3.54nm; Minnie347 existing23P; thresholds1and3; keep all cells',
        solver='L-BFGS-B max4000 iterations; max absolute margin residual <=1e-5 required for interpreting fitted moments; optimizer report retained; boundary estimates may diverge',
        outputs='fitted edge probabilities, analytic reciprocal mean/variance, observed count, all margin diagnostics; no fitted-model p value or causal claim',
        limitations='post-result fit to same graphs; non-nested relative to per-node-bin one-sided model; finite boundary fit not proven unique; source censorship and calibration limits persist',
        source_sha256=sources,code_sha256=base.sha(Path(__file__)),loader_sha256=base.sha(Path(base.__file__)),numpy=np.__version__,scipy=scipy.__version__)
    cp=HERE/'joint_expected_degree_contract.json'
    if cp.exists():assert json.loads(cp.read_text())==spec
    else:cp.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for path,h in sources.items():assert base.sha(base.ROOT/path)==h
    full,cats=base.load_graph();roots=json.loads(base.SELECTED.read_text())['selected_roots']
    with (base.DATA/'v1718_cell_info.csv').open(encoding='utf-8',newline='') as stream:cells={int(r['pt_root_id']):r for r in csv.DictReader(stream)}
    ids=[i for i,r in enumerate(roots) if cells[r]['broad_type']=='excitatory' and cells[r]['cell_type']=='23P']
    datasets=[('minnie23P',full[np.ix_(ids,ids)],cats[np.ix_(ids,ids)]%6,[roots[i] for i in ids])]
    data=base.ROOT/'data/external/microns_pinky_v185'
    cs=sorted([r for r in csv.DictReader((data/'soma_valence_v185.csv').open()) if r['cell_type']=='e'],key=lambda r:int(r['pt_root_id']))
    proots=[int(r['pt_root_id']) for r in cs];index={r:i for i,r in enumerate(proots)}
    xyz=np.array([list(map(int,r['pt_position'].strip('[]').split())) for r in cs])*[.00354,.00354,.04]
    c=np.digitize(np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=2),[50,100,200,400,800]);counts=np.zeros((362,362),dtype=int)
    for r in csv.DictReader((data/'soma_subgraph_synapses_spines_v185.csv').open()):
        u,v=index[int(r['pre_root_id'])],index[int(r['post_root_id'])]
        if u!=v:counts[u,v]+=1
    datasets.append(('pinky',counts,c,proots))
    store=base.ROOT/'data/external/joint_expected_degree_models';store.mkdir(exist_ok=True);results=[]
    for name,counts,c,selected in datasets:
        for t in (1,3):
            a=counts>=t;p,theta,diagnostic=fit(a,c);observed=int((a&a.T).sum()//2)
            q=np.triu(p*p.T,1);mean=float(q.sum());variance=float((q*(1-q)).sum())
            path=store/f'{name}_t{t}.npz'
            if path.exists():
                with np.load(path,allow_pickle=False) as saved:assert np.array_equal(saved['p'],p) and np.array_equal(saved['roots'],selected)
            else:
                with path.open('xb') as stream:np.savez_compressed(stream,p=p,theta=theta,roots=np.array(selected,dtype=np.int64))
            r=dict(dataset=name,threshold=t,cells=len(a),edges=int(a.sum()),observed=observed,diagnostic=diagnostic,
                reciprocal_mean=mean if diagnostic['gate_pass'] else None,reciprocal_variance=variance if diagnostic['gate_pass'] else None,
                fitted_file=path.relative_to(base.ROOT).as_posix(),fitted_sha256=base.sha(path))
            results.append(r);print(json.dumps(r),flush=True)
    output=dict(contract_sha256=base.sha(cp),results=results,status='EXPECTED_MARGIN_MODEL_NOT_EXACT_DEGREE_NULL')
    target=HERE/'joint_expected_degree_result.json'
    if target.exists():assert json.loads(target.read_text())==output
    else:target.write_text(json.dumps(output,indent=2),encoding='utf-8')


if __name__=='__main__':main()
