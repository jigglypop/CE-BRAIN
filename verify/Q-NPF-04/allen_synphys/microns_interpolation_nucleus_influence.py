"""고정 연결별 대비에서 한 핵에 의존하는 항 전체를 제외한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def main():
    prior=read('microns_interpolation_link_influence_result.json');path=HERE/'microns_interpolation_link_values.npz'
    assert sha(path)==prior['arrays_sha256']
    contract=read('microns_interpolation_link_influence_contract.json')
    assert sha(HERE/'microns_distance_interpolation_support.json')==contract['support_sha256']
    support=read('microns_distance_interpolation_support.json')['assignments']
    targets=read('microns_all_scan_targets_result.json')['targets']
    save('microns_interpolation_nucleus_influence_contract.json',dict(
        question='Does the sign persist when all frozen comparison terms involving any one nucleus are omitted?',
        method='For each supported link build focal-nucleus set and full dependency set including nonzero-weight interpolation controls. For every registered nucleus separately remove terms touching it, retaining unchanged controls on remaining terms. Report both focal-only and full-dependency omission, remaining count and all3 component means; empty support stays undefined.',
        selection='All429 assignments, 3 temporal subsets and 2 clocks; no preferred nucleus exclusion. Registered nuclei absent from all terms remain with zero removed terms.',
        limits='Post-observation fixed-term sensitivity only, not refitting, causal cell ablation, independent jackknife errors or a new confirmatory result. Omission changes the estimand and may remove many terms.',
        code_sha256=sha(Path(__file__)),prior_sha256=sha(HERE/'microns_interpolation_link_influence_result.json'),arrays_sha256=sha(path),support_sha256=contract['support_sha256'],targets_sha256=sha(HERE/'microns_all_scan_targets_result.json')))
    maps={};geometry=[]
    for s in support:
        key=(s['session'],s['scan_idx'],s['assignment_index'])
        ts={t['unit_id']:t['nucleus_id'] for t in targets if (t['session'],t['scan_idx'])==key[:2]}
        nuclei=sorted(set(ts.values()))
        focal=[];dependencies=[]
        for m in s['matches']:
            f={ts[u] for u in m['link']};d=set(f)
            for side,w in [('lower',m['lower_weight']),('upper',1-m['lower_weight'])]:
                if w>0:
                    for pair in m[side]:d.update(ts[u] for u in pair)
            focal.append(f);dependencies.append(d)
        masks={name:np.array([[n not in deps for deps in groups] for n in nuclei]) for name,groups in [('focal_only',focal),('full_dependency',dependencies)]}
        assert np.all(masks['full_dependency']<=masks['focal_only'])
        maps[key]=(nuclei,masks)
        geometry.append(dict(session=key[0],scan_idx=key[1],assignment_index=key[2],exclude_disputed=s['exclude_disputed'],nuclei=nuclei,supported=s['supported'],
            remaining={name:m.sum(axis=1).tolist() for name,m in masks.items()}))
    rows=[]
    with np.load(path) as arrays:
        for p in prior['results']:
            key=(p['session'],p['scan_idx'],p['assignment_index']);nuclei,masks=maps[key];values=arrays[p['array_key']]
            assert values.shape==(3,p['supported'])
            observed=values.mean(axis=1);result={}
            for name,mask in masks.items():
                counts=mask.sum(axis=1);valid=counts>0;out=np.full((len(nuclei),3),np.nan)
                out[valid]=(mask[valid]@values.T)/counts[valid,None]
                for i in np.flatnonzero(valid)[::max(1,len(nuclei)-1)]:assert np.allclose(out[i],values[:,mask[i]].mean(axis=1),atol=1e-12)
                assert np.allclose(out[valid,0],out[valid,1]+out[valid,2],atol=1e-12)
                result[name]=dict(means_by_nucleus=[v.tolist() if ok else None for v,ok in zip(out,valid)],undefined=int((~valid).sum()),
                    components={component:dict(range=[float(out[valid,c].min()),float(out[valid,c].max())] if valid.any() else None,
                        opposite_sign_nuclei=[n for n,v,ok in zip(nuclei,out[:,c],valid) if ok and v*observed[c]<0]) for c,component in enumerate(('total','trial_mean','within'))})
            rows.append(dict(session=key[0],scan_idx=key[1],assignment_index=key[2],exclude_disputed=p['exclude_disputed'],subset=p['subset'],timing=p['timing'],observed=observed.tolist(),**result))
    assert len(rows)==2574 and len(geometry)==429
    summaries=[]
    for key in sorted({(r['session'],r['scan_idx'],r['subset'],r['timing']) for r in rows}):
        rr=[r for r in rows if (r['session'],r['scan_idx'],r['subset'],r['timing'])==key and not r['exclude_disputed']]
        summaries.append(dict(session=key[0],scan_idx=key[1],subset=key[2],timing=key[3],assignments=len(rr),
            **{mode:{comp:dict(assignments_with_sign_flip=sum(bool(r[mode]['components'][comp]['opposite_sign_nuclei']) for r in rr),
                range=[min(r[mode]['components'][comp]['range'][0] for r in rr if r[mode]['components'][comp]['range']),max(r[mode]['components'][comp]['range'][1] for r in rr if r[mode]['components'][comp]['range'])]) for comp in ('total','trial_mean','within')} for mode in ('focal_only','full_dependency')}))
    save('microns_interpolation_nucleus_influence_result.json',dict(results=rows,geometry=geometry,summaries=summaries,code_sha256=sha(Path(__file__)),component_order=['total','trial_mean','within'],nucleus_order='geometry.nuclei for same scan and assignment'))
    for s in summaries:
        if s['subset']=='all10' and s['timing']=='positive_delay_sensitivity':print(s['session'],s['scan_idx'],s['full_dependency']['total'])
if __name__=='__main__':main()
