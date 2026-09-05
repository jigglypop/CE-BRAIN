"""연결별 보간 대비와 고정 대조에서 연결 하나씩 제외하는 민감도."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def main():
    old=read('microns_distance_interpolation_result.json')
    assert sha(HERE/'microns_distance_interpolation_support.json')==old['support_sha256']
    support=read('microns_distance_interpolation_support.json')['assignments'];coverage=read('microns_scan_coverage_result.json')['scans']
    save('microns_interpolation_link_influence_contract.json',dict(
        question='Does any single supported annotated-link contribution control the sign of the fixed distance-interpolated mean?',
        method='For every supported link compute its correlation minus its frozen interpolated unlisted control. Preserve ordered per-link values for total/trial_mean/within. Leave each one out and average the remaining link contrasts; never refit controls or change the distance support.',
        selection='All429 assignments including firstscan exclusion sensitivity; all14 scans, all10/first5/last5, both timings and all3 additive components.',
        limits='Post-observation descriptive influence only. Leave-one-link removal is not cell removal, synapse intervention, independent jackknife uncertainty or selection of a preferred result. Shared controls and nuclei remain dependent.',
        code_sha256=sha(Path(__file__)),support_sha256=old['support_sha256'],prior_sha256=sha(HERE/'microns_distance_interpolation_result.json'),coverage_sha256=sha(HERE/'microns_scan_coverage_result.json')))
    prior={ (r['session'],r['scan_idx'],r['assignment_index'],r['subset'],r['timing']):r for r in old['results'] }
    rows=[];arrays={};summaries=[]
    for scan in coverage:
        if scan['status']!='RESPONSE_ANALYZED':continue
        key=(scan['session'],scan['scan_idx']);ss=[s for s in support if (s['session'],s['scan_idx'])==key]
        path=ROOT/f'data/external/microns_functional_nwb/scan_{key[0]}_{key[1]}_repeated_clips.npz';assert sha(path)==scan['input_sha256']
        with np.load(path) as data:
            units=data['unit_ids'].tolist();ui={u:i for i,u in enumerate(units)}
            for subset,sel in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
                for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
                    x=data['values'][mode,:,sel];n=x.shape[1];r=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
                    means=np.broadcast_to(r.mean(axis=2,keepdims=True),r.shape)
                    flat=[a.reshape(-1,len(units)) for a in (r,means,r-means)];flat=[a-a.mean(axis=0) for a in flat]
                    mat=np.stack([a.T@a for a in flat]);denom=np.sqrt(np.outer(np.diag(mat[0]),np.diag(mat[0])));mat/=denom
                    assert np.allclose(mat[0],mat[1]+mat[2],atol=1e-12)
                    local=[]
                    for s in ss:
                        values=[]
                        for m in s['matches']:
                            a,b=[ui[u] for u in m['link']];v=mat[:,a,b].copy()
                            for side,alpha in [('lower',m['lower_weight']),('upper',1-m['lower_weight'])]:
                                for u,w in m[side]:v-=alpha*mat[:,ui[u],ui[w]]/len(m[side])
                            values.append(v)
                        values=np.array(values).T;N=values.shape[1];assert N==s['supported'] and N>1 and np.isfinite(values).all()
                        obs=values.mean(axis=1);omit=(values.sum(axis=1,keepdims=True)-values)/(N-1)
                        assert np.allclose(values[0],values[1]+values[2],atol=1e-12)
                        # Independent direct deletion for boundary positions.
                        for j in (0,N-1):assert np.allclose(omit[:,j],np.delete(values,j,axis=1).mean(axis=1),atol=1e-12)
                        expected=prior[(*key,s['assignment_index'],subset,timing)]['interpolated']
                        assert np.allclose(obs,[expected[k] for k in ('total','trial_mean','within')],rtol=0,atol=1e-12)
                        arraykey=f'{key[0]}_{key[1]}_{s["assignment_index"]}_{subset}_{mode}';arrays[arraykey]=values
                        stats={}
                        for ci,name in enumerate(('total','trial_mean','within')):
                            v=values[ci];o=omit[ci];flips=np.flatnonzero(o*obs[ci]<0)
                            stats[name]=dict(observed=float(obs[ci]),link_value_range=[float(v.min()),float(v.max())],positive_links=int((v>0).sum()),
                                omitted_range=[float(o.min()),float(o.max())],opposite_sign_omissions=len(flips),
                                opposite_sign_links=[s['matches'][int(j)]['link'] for j in flips],
                                max_abs_contribution_link=s['matches'][int(np.argmax(np.abs(v)))]['link'],
                                max_abs_contribution_share=float(np.max(np.abs(v))/np.abs(v).sum()) if np.abs(v).sum() else None)
                        row=dict(session=key[0],scan_idx=key[1],assignment_index=s['assignment_index'],exclude_disputed=s['exclude_disputed'],subset=subset,timing=timing,supported=N,array_key=arraykey,components=stats)
                        rows.append(row)
                        if not s['exclude_disputed']:local.append(row)
                    summaries.append(dict(session=key[0],scan_idx=key[1],subset=subset,timing=timing,assignments=len(local),
                        components={name:dict(assignments_with_sign_flip=sum(v['components'][name]['opposite_sign_omissions']>0 for v in local),
                            omission_range=[min(v['components'][name]['omitted_range'][0] for v in local),max(v['components'][name]['omitted_range'][1] for v in local)]) for name in ('total','trial_mean','within')}))
        print(key,'done',flush=True)
    assert len(rows)==2574
    dest=HERE/'microns_interpolation_link_values.npz'
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,**arrays)
    else:
        with np.load(dest) as a:assert set(a.files)==set(arrays) and all(np.array_equal(a[k],v) for k,v in arrays.items())
    save('microns_interpolation_link_influence_result.json',dict(results=rows,summaries=summaries,array_axes=['component: total, trial_mean, within','link: frozen support matches order'],arrays_sha256=sha(dest),code_sha256=sha(Path(__file__))))
if __name__=='__main__':main()
