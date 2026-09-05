"""고정 거리 보간 가중치의 집중도와 회차 이동 대조."""
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def main():
    old=read('microns_distance_interpolation_result.json')
    assert sha(HERE/'microns_distance_interpolation_support.json')==old['support_sha256']
    support=read('microns_distance_interpolation_support.json')['assignments']
    coverage=read('microns_scan_coverage_result.json')['scans'];targets=read('microns_all_scan_targets_result.json')['targets']
    save('microns_interpolation_shift_contract.json',dict(
        question='Are distance-interpolated contrasts concentrated in a few control dyads and where do they lie relative to repeat misalignment?',
        method='Reconstruct unchanged weights from frozen per-link interpolation records. Report max control weight, inverse sum squared weights (concentration only), and maximum incident control mass per nucleus. 999 per-nucleus circular shifts, shared across alternative ROIs and both clocks; all6 conditions and all within-trial times shifted together.',
        seeds=dict(total=20260905,within=20260906),selection='All14 scans, 429 assignments including disputed exclusion, all10/first5/last5, both clocks, total/within components.',
        limits='Exploratory. Concentration count is not independent sample size. Shift tails are not calibrated p-values. Repeat exchangeability and stationarity are unproven; shifts break common inputs too. No observation-driven exclusions or new weights.',
        code_sha256=sha(Path(__file__)),result_sha256=sha(HERE/'microns_distance_interpolation_result.json'),support_sha256=old['support_sha256'],
        coverage_sha256=sha(HERE/'microns_scan_coverage_result.json'),targets_sha256=sha(HERE/'microns_all_scan_targets_result.json')))
    results=[];concentrations=[];draws={};summaries=[]
    prior={(r['session'],r['scan_idx'],r['assignment_index'],r['subset'],r['timing']):r for r in old['results']}
    for scan in coverage:
        if scan['status']!='RESPONSE_ANALYZED':continue
        key=(scan['session'],scan['scan_idx']);ss=[s for s in support if (s['session'],s['scan_idx'])==key]
        path=ROOT/f'data/external/microns_functional_nwb/scan_{key[0]}_{key[1]}_repeated_clips.npz'
        assert sha(path)==scan['input_sha256']
        data=np.load(path);units=data['unit_ids'].tolist();ui={u:i for i,u in enumerate(units)}
        ts={t['unit_id']:t for t in targets if (t['session'],t['scan_idx'])==key};assert set(ts)==set(units)
        nuclei=sorted({t['nucleus_id'] for t in ts.values()});ni={n:i for i,n in enumerate(nuclei)};un=np.array([ni[ts[u]['nucleus_id']] for u in units])
        maps=[]
        for s in ss:
            w=defaultdict(float)
            for m in s['matches']:
                w[tuple(sorted(m['link']))]+=1/s['supported']
                for side,alpha in [('lower',m['lower_weight']),('upper',1-m['lower_weight'])]:
                    for pair in m[side]:w[tuple(sorted(pair))]-=alpha/len(m[side])/s['supported']
            w={p:v for p,v in w.items() if v!=0};assert abs(sum(w.values()))<1e-12
            neg={p:-v for p,v in w.items() if v<0};assert abs(sum(neg.values())-1)<1e-12
            incident=defaultdict(float)
            for pair,v in neg.items():
                for u in pair:incident[ts[u]['nucleus_id']]+=v
            concentrations.append(dict(session=key[0],scan_idx=key[1],assignment_index=s['assignment_index'],exclude_disputed=s['exclude_disputed'],
                control_dyads=len(neg),max_control_weight=max(neg.values()),inverse_squared_weight_sum=1/sum(v*v for v in neg.values()),
                max_nucleus_incident_mass=max(incident.values()),max_control_pairs=[list(p) for p,v in neg.items() if v==max(neg.values())]))
            maps.append(w)
        pairs=sorted(set().union(*(set(w) for w in maps)));aa=np.array([ui[p[0]] for p in pairs]);bb=np.array([ui[p[1]] for p in pairs])
        weights=np.array([[w.get(p,0.) for w in maps] for p in pairs])
        rngs=[np.random.default_rng(20260905),np.random.default_rng(20260906)]
        for subset,sel in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
            n=data['values'][0,:,sel].shape[1];shifts=[rng.integers(0,n,size=(999,len(nuclei)))[:,un] for rng in rngs]
            for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
                x=data['values'][mode,:,sel];r=x-(x.sum(axis=1,keepdims=True)-x)/(n-1);within=r-r.mean(axis=2,keepdims=True)
                z=r.reshape(-1,len(units));tt=z.T@z;denom=np.sqrt(np.outer(np.diag(tt),np.diag(tt)))
                for name,blocks,sh in zip(('total','within'),(r,within),shifts):
                    z=blocks.reshape(-1,len(units));offset=np.stack([z.T@np.roll(blocks,k,axis=1).reshape(z.shape)/denom for k in range(n)])
                    assert np.allclose(offset.mean(axis=0),0,atol=1e-12)
                    shifted=np.stack([np.roll(blocks[:,:,:,j],int(sh[0,j]),axis=1) for j in range(len(units))],axis=-1).reshape(z.shape)
                    ij,ik=np.indices((len(units),len(units)))
                    assert np.allclose(shifted.T@shifted/denom,offset[(sh[0,ik]-sh[0,ij])%n,ij,ik],atol=1e-12)
                    observed=offset[0,aa,bb]@weights;null=offset[(sh[:,bb]-sh[:,aa])%n,aa,bb]@weights
                    assert np.isfinite(null).all()
                    draws[f'{key[0]}_{key[1]}_{subset}_{mode}_{name}']=null
                    local=[]
                    for ai,s in enumerate(ss):
                        expected=prior[(*key,s['assignment_index'],subset,timing)]['interpolated'][name]
                        assert abs(observed[ai]-expected)<1e-12
                        q=np.quantile(null[:,ai],[.025,.5,.975]);pos='below' if observed[ai]<q[0] else 'above' if observed[ai]>q[-1] else 'inside'
                        row=dict(session=key[0],scan_idx=key[1],assignment_index=s['assignment_index'],exclude_disputed=s['exclude_disputed'],subset=subset,timing=timing,component=name,
                            observed=float(observed[ai]),quantiles=q.tolist(),at_least_observed=int((null[:,ai]>=observed[ai]).sum()),position=pos)
                        results.append(row)
                        if not s['exclude_disputed']:local.append(row)
                    summaries.append(dict(session=key[0],scan_idx=key[1],subset=subset,timing=timing,component=name,assignments=len(local),
                        positions={p:sum(v['position']==p for v in local) for p in ('below','inside','above')},tail_range=[min(v['at_least_observed'] for v in local),max(v['at_least_observed'] for v in local)]))
        data.close();print(key,'done',flush=True)
    assert len(results)==5148 and len(concentrations)==429
    dest=HERE/'microns_interpolation_shift_draws.npz'
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,**draws)
    else:
        with np.load(dest) as a:assert set(a.files)==set(draws) and all(np.array_equal(a[k],v) for k,v in draws.items())
    save('microns_interpolation_shift_result.json',dict(results=results,summaries=summaries,concentrations=concentrations,draws_sha256=sha(dest),code_sha256=sha(Path(__file__))))
if __name__=='__main__':main()
