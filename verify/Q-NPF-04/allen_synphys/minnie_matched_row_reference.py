"""Minnie E-E 범위에 Pinky와 같은 거리별 한쪽 차수 모형을 적용한다."""
import csv,json
from collections import Counter
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from pinky_row_reference import prepare
HERE=base.HERE


def main():
    spec=dict(question='Same row-conditioned distance model on Minnie E-E, primary23P label and secondary all-excitatory scope',
        scopes='within existing1348 selected cells; primary broad_type=excitatory AND cell_type=23P; secondary all broad_type=excitatory; keep zero-degree cells',
        geometry='existing transformed soma coordinates and bins50,100,200,400,800um; no new distance calibration or threshold tuning',
        models='same frozen prepare function as Pinky; outgoing and incoming separately; neither fixes both degrees',
        thresholds=[1,3],primary_sampling='2000 direct independent graphs each setting, seed2026090512; every row/bin count checked',
        secondary='analytic moments only, no sampling or tail estimate; not pooled with primary',
        inference='descriptive harmonization on two previously inspected specimens; age, volume, proofreading, coordinate calibration and export censorship differ; no causal or confirmatory replication',
        source_sha256=json.loads(base.CONTRACT.read_text())['source_sha256'],
        code_sha256=base.sha(Path(__file__)),loader_sha256=base.sha(Path(base.__file__)),
        model_sha256=base.sha(HERE/'pinky_row_reference.py'),pinky_result_sha256=base.sha(HERE/'pinky_row_result.json'))
    cp=HERE/'minnie_matched_row_contract.json'
    if cp.exists():assert json.loads(cp.read_text())==spec
    else:cp.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for name,digest in spec['source_sha256'].items():
        p=HERE/name if (HERE/name).exists() else base.DATA/name
        assert base.sha(p)==digest
    counts,categories=base.load_graph();roots=json.loads(base.SELECTED.read_text())['selected_roots']
    with (base.DATA/'v1718_cell_info.csv').open(encoding='utf-8',newline='') as stream:
        cells={int(r['pt_root_id']):r for r in csv.DictReader(stream)}
    results=[];selected={}
    for scope in ('23P','all_excitatory'):
        ids=[i for i,r in enumerate(roots) if cells[r]['broad_type']=='excitatory' and (scope=='all_excitatory' or cells[r]['cell_type']=='23P')]
        selected[scope]=[roots[i] for i in ids];n=len(ids)
        assert n==(347 if scope=='23P' else 1184)
        matrix=counts[np.ix_(ids,ids)];c=categories[np.ix_(ids,ids)]%6;keys=np.arange(n)[:,None]*6+c
        for threshold in spec['thresholds']:
            for model in ('outgoing','incoming'):
                a=matrix>=threshold
                if model=='incoming':a=a.T
                groups,mean,variance=prepare(a,c);observed=int((a&a.T).sum()//2)
                record=dict(scope=scope,cells=n,threshold=threshold,model=model,edges=int(a.sum()),
                    zero_degree_cells=int(np.sum((a.sum(0)+a.sum(1))==0)),observed=observed,analytic_mean=mean,
                    analytic_variance=variance,observed_minus_mean=observed-mean)
                if scope=='23P':
                    hist=Counter();rng=np.random.default_rng(2026090512)
                    expected=np.bincount(keys[a],minlength=n*6)
                    for sample in range(2000):
                        b=np.zeros_like(a)
                        for i,cat,targets,k in groups:
                            if k:b[i,rng.choice(targets,k,replace=False)]=True
                        assert np.array_equal(np.bincount(keys[b],minlength=n*6),expected) and not np.diag(b).any()
                        hist[int((b&b.T).sum()//2)]+=1
                    exceed=sum(v for k,v in hist.items() if k>=observed);tail=exceed/2000
                    record.update(draws=2000,exceedances=exceed,upper_tail_estimate=tail,
                        mc_se_plugin=float(np.sqrt(tail*(1-tail)/2000)),
                        sample_mean=sum(k*v for k,v in hist.items())/2000,
                        histogram={str(k):v for k,v in sorted(hist.items())},
                        tail_note='zero exceedances means unresolved small tail, not zero probability; plugin SE degenerates at endpoints')
                results.append(record);print(json.dumps({k:v for k,v in record.items() if k!='histogram'}),flush=True)
    result=dict(contract_sha256=base.sha(cp),selected_roots=selected,results=results,
        status='HARMONIZED_MODEL_DESCRIPTIVE_COMPARISON_NOT_FULL_REPLICATION')
    out=HERE/'minnie_matched_row_result.json'
    if out.exists():assert json.loads(out.read_text())==result
    else:out.write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':main()
