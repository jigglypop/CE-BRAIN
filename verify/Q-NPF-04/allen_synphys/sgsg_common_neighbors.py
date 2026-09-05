"""공통 입력/출력 수별 상호연결 잔차의 탐색적 분해."""
import json
from pathlib import Path
import numpy as np
import sgsg_refit_residual as base

HERE=base.HERE


def summarize(a,p,distance):
    x=a.astype(np.int32)
    common={'input':x.T@x,'output':x@x.T}
    u,v=np.triu_indices(len(a),1)
    mutual=(a[u,v]&a[v,u]).astype(int)
    expected=p[u,v]*p[v,u]
    residual=mutual-expected
    result={}
    for name,matrix in common.items():
        values=matrix[u,v]
        group=np.digitize(values,[1,2,4])
        rows=[]
        for b in range(6):
            for k in range(4):
                mask=(distance[u,v]==b)&(group==k)
                n=int(mask.sum());r=int(mutual[mask].sum());mu=float(expected[mask].sum())
                rows.append(dict(distance_bin=b,common_group=k,opportunities=n,mutual=r,
                                 expectation=mu,residual=r-mu))
        totals=[]
        for k in range(4):
            mask=group==k;n=int(mask.sum());r=int(mutual[mask].sum());mu=float(expected[mask].sum())
            totals.append(dict(common_group=k,opportunities=n,mutual=r,expectation=mu,
                               residual=r-mu,residual_per_1000_dyads=1000*(r-mu)/n if n else None))
        assert np.isclose(sum(r['residual'] for r in rows),residual.sum(),atol=1e-9)
        result[name]=dict(rows=rows,totals=totals,max_common_count=int(values.max()),
                          weighted_residual=float(np.dot(values,residual)))
    return result


def main():
    prior_path=HERE/'sgsg_refit_residual_result.json'
    prior=json.loads(prior_path.read_text());assert prior['failed']==0
    spec=dict(question='Does reciprocal residual concentrate in pairs sharing presynaptic or postsynaptic neighbors?',
              scope='Same347selected23Pcells only; all60031unordered nonselfdyads; neighbors outside population unobserved',
              common_inputs='sum_k Aki*Akj',common_outputs='sum_k Aik*Ajk',
              endpoint_exclusion='Diagonal A=0 makes k=i,j terms zero; direct dyad edges do not enter its common-neighbor count',
              groups=['0','1','2-3','4+'],distance_bins_um=[50,100,200,400,800],
              design='After seeing global residual, fixed these descriptive strata before new calculation; no new fits, draws, or parameter selection',
              comparison='Compute graph-specific strata anew for observed and64generatedgraphs; report opportunities, mutual, fitted expectation and residual; differing strata memberships are not matched causal groups',
              caveats='Existing fitted probabilities are plug-in references, not a conditional likelihood given strata. Fitting uses wholegraph; overlapping dyads/neighbor paths are dependent. No pvalue or independent heldout prediction.',
              code_sha256=base.BASE.sha(Path(__file__)),prior_sha256=base.BASE.sha(prior_path),
              location_sha256=base.BASE.sha(HERE/'sgsg_residual_location_result.json'))
    cp=HERE/'sgsg_common_neighbors_contract.json'
    base.source.run.shared.source.write_once(cp,spec)
    roots,xyz,obs,c=base.source.run.shared.source.data()
    old=json.loads((HERE/'joint_expected_polish_result.json').read_text())
    path=base.BASE.ROOT/old['fitted_file'];assert base.BASE.sha(path)==old['fitted_sha256']
    with np.load(path,allow_pickle=False) as f:
        assert f['roots'].tolist()==roots;p=f['p']
    observed=summarize(obs,p,c)
    generated=[]
    for r in prior['records']:
        name=f'{r["index"]:02}.npz';ap=base.source.STORE/name;pp=base.STORE/name
        assert base.BASE.sha(ap)==r['input_sha256'] and base.BASE.sha(pp)==r['fitted_sha256']
        with np.load(ap,allow_pickle=False) as f:
            assert f['roots'].tolist()==roots;a=f['adjacency']
        with np.load(pp,allow_pickle=False) as f:
            assert f['roots'].tolist()==roots;p=f['p']
        generated.append(dict(index=r['index'],summary=summarize(a,p,c)))
    comparisons={}
    for axis in ('input','output'):
        comparisons[axis]=[]
        for k in range(4):
            group=[r['summary'][axis]['totals'][k] for r in generated]
            vals=[g['residual'] for g in group]
            comparisons[axis].append(dict(common_group=k,observed=observed[axis]['totals'][k],
                generated_mean_opportunities=float(np.mean([g['opportunities'] for g in group])),
                generated_mean_mutual=float(np.mean([g['mutual'] for g in group])),
                generated_mean_expectation=float(np.mean([g['expectation'] for g in group])),
                generated_mean_residual=float(np.mean(vals)),generated_residual_range=[min(vals),max(vals)],
                generated_residual_mc_se=float(np.std(vals,ddof=1)/8),
                residual_difference=observed[axis]['totals'][k]['residual']-float(np.mean(vals))))
        assert np.isclose(sum(r['residual_difference'] for r in comparisons[axis]),prior['comparison']['residual_gap'],atol=1e-9)
    result=dict(contract_sha256=base.BASE.sha(cp),observed=observed,generated=generated,comparisons=comparisons)
    base.source.run.shared.source.write_once(HERE/'sgsg_common_neighbors_result.json',result)
    print(json.dumps(comparisons),flush=True)


if __name__=='__main__':main()
