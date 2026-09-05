"""적합 그래프 모형에서 생성 후 매번 재적합하는 모수 부트스트랩."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.special import expit
import microns_constrained_swaps as base
from joint_expected_degree_reference import fit
HERE=base.HERE
STORE=base.ROOT/'data/external/joint_degree_refit_bootstrap'
CONTRACT=HERE/'joint_degree_refit_bootstrap_contract.json'


def refine(a,c):
    p,theta,diagnostic=fit(a,c)
    if diagnostic['gate_pass']:return p,diagnostic
    n=len(a);out=a.sum(1);inc=a.sum(0);bc=np.bincount(c[a],minlength=6)
    allowed=(~np.eye(n,dtype=bool))&(out[:,None]>0)&(inc[None,:]>0)&(bc[c]>0)
    u,v=np.nonzero(allowed);bins=c[u,v];target=np.concatenate([out,inc,bc]);history=[]
    for step in range(6):
        pp=expit(theta[u]+theta[n+v]+theta[2*n+bins]);w=pp*(1-pp)
        actual=np.concatenate([np.bincount(u,weights=pp,minlength=n),np.bincount(v,weights=pp,minlength=n),np.bincount(bins,weights=pp,minlength=6)])
        g=actual-target;error=float(np.max(abs(g)));history.append(error)
        if error<=1e-8 or step==5:break
        h=np.zeros((2*n+6,2*n+6))
        h[np.arange(n),np.arange(n)]=np.bincount(u,weights=w,minlength=n)
        h[n+np.arange(n),n+np.arange(n)]=np.bincount(v,weights=w,minlength=n)
        h[2*n+np.arange(6),2*n+np.arange(6)]=np.bincount(bins,weights=w,minlength=6)
        h[u,n+v]=w;h[n+v,u]=w
        for b in range(6):
            mask=bins==b;wr=np.bincount(u[mask],weights=w[mask],minlength=n);wc=np.bincount(v[mask],weights=w[mask],minlength=n)
            h[:n,2*n+b]=wr;h[2*n+b,:n]=wr;h[n:2*n,2*n+b]=wc;h[2*n+b,n:2*n]=wc
        theta-=np.linalg.lstsq(h,g,rcond=1e-12)[0]
    p=np.zeros((n,n));p[u,v]=pp
    return p,dict(initial=diagnostic,newton_errors=history,max_absolute_margin_error=error,gate_pass=error<=1e-5)


def main():
    oldpath=HERE/'joint_expected_degree_result.json';polishpath=HERE/'joint_expected_polish_result.json'
    old=json.loads(oldpath.read_text());polish=json.loads(polishpath.read_text())
    pinky=next(r for r in old['results'] if r['dataset']=='pinky' and r['threshold']==1)
    starts=[('minnie23P',polish),('pinky',pinky)]
    spec=dict(question='Does observed reciprocal residual exceed residuals after generation and full refitting under fitted expected-degree model?',
        scope='threshold1 only, both existing fitted datasets; threshold3 not a strong-common-effect test',
        replicates=199,seeds='2026090513000 + dataset_index*10000 + replicate_index; fixed order minnie23P,pinky',
        statistic='mutual-pair count minus refitted mutual-pair mean; one-sided residual >= observed residual',
        refit='same fit function and expected margin model; if1e-5 gate fails, up to5 minimum-norm Newton steps without relaxing tolerance',
        errors='record any failure; never replace draws or compute a success-only p value; interpretation requires all199 fits per dataset pass',
        inference='parametric bootstrap diagnostic, not exact conditional test; fitted-null assumptions and prior model selection remain; MC resolution1/199; report counts and zero-tail upper bound',
        raw_source_sha256=json.loads((HERE/'joint_expected_degree_contract.json').read_text())['source_sha256'],
        original_result_sha256=base.sha(oldpath),polish_result_sha256=base.sha(polishpath),
        fit_code_sha256=base.sha(HERE/'joint_expected_degree_reference.py'),loader_sha256=base.sha(Path(base.__file__)),
        code_sha256=base.sha(Path(__file__)),numpy=np.__version__)
    if CONTRACT.exists():assert json.loads(CONTRACT.read_text())==spec
    else:CONTRACT.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for path,h in spec['raw_source_sha256'].items():assert base.sha(base.ROOT/path)==h
    STORE.mkdir(exist_ok=True)
    _,allcats=base.load_graph();allroots=json.loads(base.SELECTED.read_text())['selected_roots'];lookup={r:i for i,r in enumerate(allroots)}
    with (base.ROOT/'data/external/microns_pinky_v185/soma_valence_v185.csv').open(newline='') as stream:
        pcells={int(r['pt_root_id']):r for r in csv.DictReader(stream) if r['cell_type']=='e'}
    outputs=[]
    for dataset_index,(name,start) in enumerate(starts):
        path=base.ROOT/start['fitted_file'];assert base.sha(path)==start['fitted_sha256']
        with np.load(path,allow_pickle=False) as saved:p=saved['p'].copy();roots=saved['roots'].tolist()
        if name=='minnie23P':
            ids=[lookup[r] for r in roots];c=allcats[np.ix_(ids,ids)]%6
        else:
            xyz=np.array([list(map(int,pcells[r]['pt_position'].strip('[]').split())) for r in roots])*[.00354,.00354,.04]
            c=np.digitize(np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=2),[50,100,200,400,800])
        observed_residual=start['observed']-start['reciprocal_mean'];records=[]
        for index in range(spec['replicates']):
            rp=STORE/f'{name}_{index:03d}.json';seed=2026090513000+dataset_index*10000+index
            rng=np.random.default_rng(seed);a=rng.random(p.shape)<p
            digest=hashlib.sha256(a.tobytes()).hexdigest()
            if rp.exists():
                record=json.loads(rp.read_text());assert record['contract_sha256']==base.sha(CONTRACT) and record['graph_sha256']==digest
            else:
                try:
                    fitted,diag=refine(a,c)
                    mutual=int((a&a.T).sum()//2);mean=float(np.triu(fitted*fitted.T,1).sum())
                    record=dict(contract_sha256=base.sha(CONTRACT),seed=seed,graph_sha256=digest,edges=int(a.sum()),
                        mutual=mutual,fit_mean=mean if diag['gate_pass'] else None,residual=mutual-mean if diag['gate_pass'] else None,diagnostic=diag)
                except Exception as error:
                    record=dict(contract_sha256=base.sha(CONTRACT),seed=seed,graph_sha256=digest,residual=None,error=repr(error),diagnostic=dict(gate_pass=False))
                with rp.open('x') as stream:json.dump(record,stream,indent=2)
            records.append(record)
            if (index+1)%25==0:print(name,'completed',index+1,'failed',sum(not r['diagnostic']['gate_pass'] for r in records),flush=True)
        failures=sum(not r['diagnostic']['gate_pass'] for r in records)
        vals=[r['residual'] for r in records if r['diagnostic']['gate_pass']]
        k=sum(x>=observed_residual for x in vals)
        summary=dict(dataset=name,replicates=len(records),failed=failures,observed_residual=observed_residual,
            exceedances=k,raw_tail_estimate=k/199 if not failures else None,
            adjusted_tail_estimate=(k+1)/200 if not failures else None,
            zero_exceedance_mc_upper95=float(-np.expm1(np.log(.05)/199)) if not failures and k==0 else None,
            bootstrap_residual_mean=float(np.mean(vals)) if not failures else None,
            bootstrap_residual_sd=float(np.std(vals,ddof=1)) if not failures else None,
            max_margin_error=max((r['diagnostic'].get('max_absolute_margin_error',float('inf')) for r in records)),
            record_hashes={f'{name}_{i:03d}.json':base.sha(STORE/f'{name}_{i:03d}.json') for i in range(199)})
        outputs.append(summary);print(json.dumps({k:v for k,v in summary.items() if k!='record_hashes'}),flush=True)
    result=dict(contract_sha256=base.sha(CONTRACT),results=outputs,status='PARAMETRIC_REFIT_DIAGNOSTIC_NOT_FULL_BIOLOGICAL_CONFIRMATION')
    op=HERE/'joint_degree_refit_bootstrap_result.json'
    if op.exists():assert json.loads(op.read_text())==result
    else:op.write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':main()
