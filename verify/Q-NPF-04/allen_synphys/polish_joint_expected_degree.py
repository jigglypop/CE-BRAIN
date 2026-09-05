"""기존 Minnie t1의 같은 목적함수를 Newton 단계로 정밀화한다. 기준 변경 없음."""
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
import microns_constrained_swaps as base
HERE=base.HERE
oldpath=HERE/'joint_expected_degree_result.json'
old=json.loads(oldpath.read_text());record=next(r for r in old['results'] if r['dataset']=='minnie23P' and r['threshold']==1)
path=base.ROOT/record['fitted_file'];assert base.sha(path)==record['fitted_sha256']
spec=dict(reason='L-BFGS function-change stop before frozen1e-5 margin tolerance; solve identical model with Newton minimum-norm Hessian steps',
    old_result_sha256=base.sha(oldpath),old_fit_sha256=base.sha(path),code_sha256=base.sha(Path(__file__)),
    rule='at most5 steps; Hessian least-squares rcond1e-12 handles gauge redundancy; target1e-8; same1e-5 interpretation gate')
cp=HERE/'joint_expected_polish_contract.json'
if cp.exists():assert json.loads(cp.read_text())==spec
else:cp.write_text(json.dumps(spec,indent=2),encoding='utf-8')
with np.load(path,allow_pickle=False) as saved:theta=saved['theta'].copy();selected=saved['roots'].copy()
full,cats=base.load_graph();allroots=json.loads(base.SELECTED.read_text())['selected_roots'];lookup={r:i for i,r in enumerate(allroots)}
ids=[lookup[int(r)] for r in selected];a=full[np.ix_(ids,ids)]>=1;c=cats[np.ix_(ids,ids)]%6;n=len(a)
out=a.sum(1);inc=a.sum(0);bc=np.bincount(c[a],minlength=6)
allowed=(~np.eye(n,dtype=bool))&(out[:,None]>0)&(inc[None,:]>0)&(bc[c]>0)
u,v=np.nonzero(allowed);bins=c[u,v];target=np.concatenate([out,inc,bc]);history=[]
for step in range(6):
    z=theta[u]+theta[n+v]+theta[2*n+bins];p=expit(z);w=p*(1-p)
    actual=np.concatenate([np.bincount(u,weights=p,minlength=n),np.bincount(v,weights=p,minlength=n),np.bincount(bins,weights=p,minlength=6)])
    g=actual-target;error=float(np.max(abs(g)));history.append(dict(step=step,max_margin_error=error))
    if error<=1e-8 or step==5:break
    h=np.zeros((2*n+6,2*n+6))
    h[np.arange(n),np.arange(n)]=np.bincount(u,weights=w,minlength=n)
    h[n+np.arange(n),n+np.arange(n)]=np.bincount(v,weights=w,minlength=n)
    h[2*n+np.arange(6),2*n+np.arange(6)]=np.bincount(bins,weights=w,minlength=6)
    h[u,n+v]=w;h[n+v,u]=w
    for b in range(6):
        mask=bins==b;wr=np.bincount(u[mask],weights=w[mask],minlength=n);wc=np.bincount(v[mask],weights=w[mask],minlength=n)
        h[:n,2*n+b]=wr;h[2*n+b,:n]=wr;h[n:2*n,2*n+b]=wc;h[2*n+b,n:2*n]=wc
    delta=np.linalg.lstsq(h,g,rcond=1e-12)[0]
    theta-=delta
matrix=np.zeros((n,n));matrix[u,v]=p;q=np.triu(matrix*matrix.T,1)
gp=path.with_name('minnie23P_t1_polished.npz')
if gp.exists():
    with np.load(gp,allow_pickle=False) as saved:assert np.allclose(saved['p'],matrix,atol=1e-12,rtol=0)
else:
    with gp.open('xb') as stream:np.savez_compressed(stream,p=matrix,theta=theta,roots=selected)
result=dict(contract_sha256=base.sha(cp),history=history,gate_pass=error<=1e-5,
    observed=int((a&a.T).sum()//2),reciprocal_mean=float(q.sum()) if error<=1e-5 else None,
    reciprocal_variance=float((q*(1-q)).sum()) if error<=1e-5 else None,
    fitted_file=gp.relative_to(base.ROOT).as_posix(),fitted_sha256=base.sha(gp))
op=HERE/'joint_expected_polish_result.json'
if op.exists():assert json.loads(op.read_text())==result
else:op.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
