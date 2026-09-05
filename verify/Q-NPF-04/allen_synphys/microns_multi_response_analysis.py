"""9/3·9/4의 모든 핵별 ROI 선택에서 같은 반응 대비를 계산한다."""
import argparse,csv,itertools,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts
from microns_repeat_shift_control import weights

HERE=Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def main(scan):
    prefix=f'microns_multi9{scan}'
    path=ROOT/f'data/external/microns_functional_nwb/scan_9_{scan}_repeated_clips.npz'
    receipt=read(prefix+'_repeats_acquisition.json');assert sha(path)==receipt['artifact_sha256']
    support=next(r for r in read('microns_multi_unit_support_result.json')['scans'] if r['scan_idx']==scan)
    assignments=support['assignments'];nuclei=support['nuclei']
    meta=read(prefix+'_scan_result.json');targets=meta['targets']
    source=ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather'
    assert sha(source)==read('microns_multi_unit_contract.json')['structure_sha256']
    save(prefix+'_analysis_contract.json',dict(
        question='How sensitive are total and within-trial structural contrasts to every recorded one-ROI-per-nucleus assignment?',
        method='All frozen Cartesian assignments; original field-distance weighting and cuts; raw/repeat mean/LOO residual; exact trial-level covariance decomposition normalized by total residual SDs. All10/first5/last5, both timings.',
        control='999 independent per-nucleus circular repeat shifts. Same nucleus shift for alternative ROIs, shared across timing and assignments. Total seed20260905; within seed20260906; conditions and entire within-trial blocks moved together.',
        timing_amendment_sha256=sha(HERE/'microns_multi_unit_timing_amendment.json'),
        limits='No preferred assignment, independent-ROI pseudoreplication, calibrated p-value or causal claim. Field weights change with chosen ROI; full outcomes retained.',
        code_sha256=sha(Path(__file__)),input_sha256=sha(path),assignment_source_sha256=sha(HERE/'microns_multi_unit_support_result.json'),
        identity_sha256=sha(HERE/(prefix+'_scan_result.json')),weight_code_sha256=sha(HERE/'microns_repeat_shift_control.py')))
    data=np.load(path);units=data['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)}
    byunit={t['unit_id']:t for t in targets};assert set(units)==set(byunit)
    nucleus_index={n:i for i,n in enumerate(nuclei)}
    u_to_n=np.array([nucleus_index[byunit[u]['nucleus_id']] for u in units])
    with (ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv').open(encoding='utf-8',newline='') as f:cells={int(r['id']):r for r in csv.DictReader(f)}
    xyz={n:np.array([int(cells[n]['pt_position_'+a]) for a in 'xyz'])*[.004,.004,.040] for n in nuclei}
    cuts=np.array(read('microns_structure_response_result.json')['distance_quartiles_um'])
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    tab=feather.read_table(source,columns=['pre_pt_root_id','post_pt_root_id']).to_pydict();edges=Counter(zip(tab['pre_pt_root_id'],tab['post_pt_root_id']))
    pairs=[]
    for i,j in itertools.combinations(range(len(units)),2):
        a,b=byunit[units[i]],byunit[units[j]]
        if a['nucleus_id']==b['nucleus_id']:continue
        distance=float(np.linalg.norm(xyz[a['nucleus_id']]-xyz[b['nucleus_id']]))
        count=edges[a['root_v1718'],b['root_v1718']]+edges[b['root_v1718'],a['root_v1718']]
        pairs.append(dict(unit_a=units[i],unit_b=units[j],i=i,j=j,fields=sorted([a['field'],b['field']]),distance_bin=int(np.searchsorted(cuts,distance)),linked=bool(count)))
    a=np.array([p['i'] for p in pairs]);b=np.array([p['j'] for p in pairs])
    w=np.zeros((len(pairs),len(assignments)));selected_ids=[]
    for k,assignment in enumerate(assignments):
        chosen=set(assignment['unit_ids']);assert len(chosen)==len(nuclei)
        assert {byunit[u]['nucleus_id'] for u in chosen}==set(nuclei)
        ids=[i for i,p in enumerate(pairs) if p['unit_a'] in chosen and p['unit_b'] in chosen]
        pp=[pairs[i] for i in ids];_,ww=weights(pp);w[ids,k]=ww;selected_ids.append(ids)
        diag=contrasts([dict(p,correlation=0.) for p in pp])
        assert len(ids)==len(nuclei)*(len(nuclei)-1)//2
        assert diag['linked_dyads']==assignment['linked'] and diag['matched_strata']==assignment['matched_strata']
        assert diag['matched_dyads']==assignment['matched_dyads'] and diag['matched_linked_dyads']==assignment['matched_linked']
    rngs=[np.random.default_rng(20260905),np.random.default_rng(20260906)]
    results=[];draw_store={};summaries=[]
    for subset,sel in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
        n=data['values'][0,:,sel].shape[1]
        shift_sets=[rng.integers(0,n,size=(999,len(nuclei)))[:,u_to_n] for rng in rngs]
        for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
            x=data['values'][mode,:,sel];r=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
            assert np.isfinite(r).all() and np.allclose(r.sum(axis=1),0,atol=1e-8)
            means=r.mean(axis=2,keepdims=True);within=r-means
            flat=r.reshape(-1,len(units));flat=flat-flat.mean(axis=0)
            level=np.broadcast_to(means,r.shape).reshape(flat.shape);level=level-level.mean(axis=0)
            inner=within.reshape(flat.shape);inner=inner-inner.mean(axis=0)
            tt,bb,ii=flat.T@flat,level.T@level,inner.T@inner
            assert (np.diag(tt)>0).all() and np.allclose(tt,bb+ii,rtol=1e-12,atol=1e-6)
            assert np.allclose(level.T@inner,0,rtol=0,atol=1e-6)
            denom=np.sqrt(np.outer(np.diag(tt),np.diag(tt)))
            matrices={'total':tt/denom,'trial_mean':bb/denom,'within':ii/denom,
                'raw':np.corrcoef(x.reshape(-1,len(units)),rowvar=False),
                'repeat_mean':np.corrcoef(x.mean(axis=1).reshape(-1,len(units)),rowvar=False)}
            assert np.allclose(matrices['total'],np.corrcoef(flat,rowvar=False),atol=1e-12)
            obs={key:m[a,b]@w for key,m in matrices.items()}
            assert np.allclose(obs['total'],obs['trial_mean']+obs['within'],atol=1e-12)
            nulls={}
            for name,blocks,shifts in zip(('total','within'),(r,within),shift_sets):
                z=blocks.reshape(flat.shape)
                offsets=np.stack([z.T@np.roll(blocks,k,axis=1).reshape(flat.shape)/denom for k in range(n)])
                assert np.allclose(offsets.mean(axis=0),0,atol=1e-12)
                assert np.allclose(offsets[0],matrices[name],atol=1e-12)
                s=shifts[0]
                explicit=np.stack([np.roll(blocks[:,:,:,j],int(s[j]),axis=1) for j in range(len(units))],axis=-1).reshape(flat.shape)
                jj,kk=np.indices((len(units),len(units)))
                assert np.allclose(explicit.T@explicit/denom,offsets[(s[kk]-s[jj])%n,jj,kk],atol=1e-12)
                nulls[name]=offsets[(shifts[:,b]-shifts[:,a])%n,a,b]@w
                draw_store[f'{subset}_{mode}_{name}']=nulls[name]
            for k,assignment in enumerate(assignments):
                direct=contrasts([dict(pairs[j],correlation=float(matrices['total'][a[j],b[j]])) for j in selected_ids[k]])
                assert abs(direct['matched_mean_difference']-obs['total'][k])<1e-12
                results.append(dict(subset=subset,timing=timing,assignment_index=k,
                    **{name:float(v[k]) for name,v in obs.items()},
                    controls={name:dict(quantiles=np.quantile(v[:,k],[.025,.5,.975]).tolist(),at_least_observed=int((v[:,k]>=obs[name][k]).sum()),draws=999) for name,v in nulls.items()}))
            summary=dict(subset=subset,timing=timing,assignments=len(assignments),
                ranges={key:[float(v.min()),float(v.max())] for key,v in obs.items()},
                positive_counts={key:int((v>0).sum()) for key,v in obs.items()},
                tail_count_ranges={key:[int((v>=obs[key]).sum(axis=0).min()),int((v>=obs[key]).sum(axis=0).max())] for key,v in nulls.items()})
            summaries.append(summary)
            if mode==1:print(summary,flush=True)
    dest=HERE/(prefix+'_analysis_draws.npz')
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,**draw_store)
    else:
        with np.load(dest) as old:
            assert set(old.files)==set(draw_store) and all(np.array_equal(old[k],v) for k,v in draw_store.items())
    save(prefix+'_analysis_result.json',dict(results=results,summaries=summaries,nuclei=nuclei,assignments=assignments,
        artifact_sha256=sha(path),draws_sha256=sha(dest),code_sha256=sha(Path(__file__)),
        limits='All assignment alternatives retained; no independent-cell duplication or assignment selection. Not calibrated p-values or causal effects.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scan',type=int,choices=[3,4],required=True)
    main(parser.parse_args().scan)
