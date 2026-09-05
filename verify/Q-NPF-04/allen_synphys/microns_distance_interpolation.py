"""거리 양쪽의 미기록 쌍을 보간하는 사후 민감도 분석. 외삽하지 않는다."""
import csv,itertools,json,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_repeat_shift_control import weights

HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))

def build_weights(pairs):
    groups=defaultdict(list)
    for i,p in enumerate(pairs):groups[(tuple(p['fields']),p['distance_bin'])].append(i)
    corrected=np.zeros(len(pairs));baseline=corrected.copy();records=[];excluded=[]
    for ids in groups.values():
        uu=[i for i in ids if not pairs[i]['linked']]
        for i in ids:
            if not pairs[i]['linked']:continue
            d=pairs[i]['distance_um']
            lower=[j for j in uu if pairs[j]['distance_um']<=d]
            upper=[j for j in uu if pairs[j]['distance_um']>=d]
            if not lower or not upper:
                excluded.append([pairs[i]['unit_a'],pairs[i]['unit_b']]);continue
            lo=max(pairs[j]['distance_um'] for j in lower);hi=min(pairs[j]['distance_um'] for j in upper)
            ll=[j for j in lower if pairs[j]['distance_um']==lo];hh=[j for j in upper if pairs[j]['distance_um']==hi]
            alpha=1. if hi==lo else (hi-d)/(hi-lo)
            corrected[i]+=1.;baseline[i]+=1.;baseline[uu]-=1./len(uu)
            corrected[ll]-=alpha/len(ll);corrected[hh]-=(1-alpha)/len(hh)
            assert abs(alpha*lo+(1-alpha)*hi-d)<1e-10
            records.append(dict(link=[pairs[i]['unit_a'],pairs[i]['unit_b']],distance_um=d,
                lower=[[pairs[j]['unit_a'],pairs[j]['unit_b']] for j in ll],
                upper=[[pairs[j]['unit_a'],pairs[j]['unit_b']] for j in hh],
                lower_weight=alpha,gap_um=hi-lo))
    if records:
        corrected/=len(records);baseline/=len(records)
        dist=np.array([p['distance_um'] for p in pairs]);label=np.array([p['linked'] for p in pairs])
        assert abs(corrected.sum())<1e-12 and abs(corrected@dist)<1e-10
        assert abs(corrected[label].sum()-1)<1e-12 and abs(baseline.sum())<1e-12
    return corrected,baseline,records,excluded

def main():
    cellfile=ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv'
    synfile=ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather'
    previous=read('microns_distance_balance_contract.json')
    assert sha(cellfile)==previous['cells_sha256'] and sha(synfile)==previous['synapses_sha256']
    coverage=read('microns_scan_coverage_result.json')['scans']
    save('microns_distance_interpolation_contract.json',dict(
        question='Does the observed contrast persist under local distance interpolation within the existing strata?',
        selection='All14 response scans, all32/384 ROI assignments, firstscan exclude3151 sensitivity, all10/first5/last5 and both clocks. Geometry alone selects controls.',
        method='For each annotated dyad use nearest lower and upper unlisted distances within the same field-pair and original quartile. Linear convex interpolation; average exact-distance ties; never extrapolate; no gap cutoff. Average equally over supported annotated dyads.',
        comparisons='Original contrast, original stratum controls restricted to supported annotated dyads, interpolated controls on the same supported dyads. Total residual and additive trial-mean/within components.',
        caveats='Exploratory after observing prior outcomes, not independent confirmation. Linear local smoothness assumed, broad gaps reported, reused controls dependent. No p-values or causal correction claim. No alternative algorithm selected after outcomes.',
        code_sha256=sha(Path(__file__)),distance_contract_sha256=sha(HERE/'microns_distance_balance_contract.json'),
        coverage_sha256=sha(HERE/'microns_scan_coverage_result.json'),targets_sha256=sha(HERE/'microns_all_scan_targets_result.json'),
        cuts_sha256=sha(HERE/'microns_structure_response_result.json'),weight_code_sha256=sha(HERE/'microns_repeat_shift_control.py')))
    with cellfile.open(encoding='utf-8',newline='') as f:cells={int(r['id']):r for r in csv.DictReader(f)}
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    tab=feather.read_table(synfile,columns=['pre_pt_root_id','post_pt_root_id']).to_pydict();edges=Counter(zip(tab['pre_pt_root_id'],tab['post_pt_root_id']))
    cuts=np.array(read('microns_structure_response_result.json')['distance_quartiles_um'])
    targets=read('microns_all_scan_targets_result.json')['targets'];results=[];support=[];summaries=[]
    for scan in coverage:
        if scan['status']!='RESPONSE_ANALYZED':continue
        key=(scan['session'],scan['scan_idx']);ts=[t for t in targets if (t['session'],t['scan_idx'])==key]
        path=ROOT/f'data/external/microns_functional_nwb/scan_{key[0]}_{key[1]}_repeated_clips.npz'
        assert sha(path)==scan['input_sha256'] and sha(HERE/scan['source'])==scan['source_sha256']
        old=read(scan['source']);multi=scan['assignment_count']>1
        assignments=[dict(unit_ids=a['unit_ids'],exclude_disputed=False) for a in old['assignments']] if multi else [dict(unit_ids=[t['unit_id'] for t in ts],exclude_disputed=False)]
        if key==(4,7):assignments.append(dict(unit_ids=[t['unit_id'] for t in ts if t['unit_id']!=3151],exclude_disputed=True))
        pairs=[]
        xyz=lambda t:np.array([int(cells[t['nucleus_id']]['pt_position_'+a]) for a in 'xyz'])*[.004,.004,.040]
        for a,b in itertools.combinations(ts,2):
            if a['nucleus_id']==b['nucleus_id']:continue
            d=float(np.linalg.norm(xyz(a)-xyz(b)))
            pairs.append(dict(unit_a=a['unit_id'],unit_b=b['unit_id'],distance_um=d,fields=sorted([a['field'],b['field']]),
                distance_bin=int(np.searchsorted(cuts,d)),linked=bool(edges[a['root_v1718'],b['root_v1718']]+edges[b['root_v1718'],a['root_v1718']])))
        ww=np.zeros((len(pairs),len(assignments),3))
        for ai,assignment in enumerate(assignments):
            chosen=set(assignment['unit_ids']);ids=[i for i,p in enumerate(pairs) if p['unit_a'] in chosen and p['unit_b'] in chosen];pp=[pairs[i] for i in ids]
            corr,base,records,excluded=build_weights(pp);assert records
            _,original=weights(pp)
            ww[ids,ai,0]=original;ww[ids,ai,1]=base;ww[ids,ai,2]=corr
            support.append(dict(session=key[0],scan_idx=key[1],assignment_index=ai,exclude_disputed=assignment['exclude_disputed'],
                supported=len(records),annotated=sum(p['linked'] for p in pp),excluded=excluded,
                gap_quantiles_um=np.quantile([r['gap_um'] for r in records],[0,.5,.95,1]).tolist(),matches=records))
        # Only now read activity values: support and interpolation weights are fixed.
        with np.load(path) as data:
            units=data['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)};assert set(units)=={t['unit_id'] for t in ts}
            aa=np.array([lookup[p['unit_a']] for p in pairs]);bb=np.array([lookup[p['unit_b']] for p in pairs])
            for subset,sel in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
                for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
                    x=data['values'][mode,:,sel];n=x.shape[1];r=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
                    means=np.broadcast_to(r.mean(axis=2,keepdims=True),r.shape);inner=r-means
                    flats=[v.reshape(-1,len(units)) for v in (r,means,inner)];flats=[v-v.mean(axis=0) for v in flats]
                    matrices=[v.T@v for v in flats];denom=np.sqrt(np.outer(np.diag(matrices[0]),np.diag(matrices[0])))
                    matrices=[m/denom for m in matrices];assert np.isfinite(matrices).all()
                    assert np.allclose(matrices[0],matrices[1]+matrices[2],atol=1e-12)
                    obs=np.stack([np.einsum('p,pak->ak',m[aa,bb],ww) for m in matrices])
                    assert np.allclose(obs[0],obs[1]+obs[2],atol=1e-12)
                    for ai,assignment in enumerate(assignments):
                        prior=next(v for v in old['results'] if v['timing']==timing and v['subset']==subset and ((v['assignment_index']==ai) if multi else v.get('exclude_disputed',False)==assignment['exclude_disputed']))
                        expected=[prior[k] for k in (('total','trial_mean','within') if multi else ('total_matched','trial_mean_component','within_trial_component'))]
                        assert np.allclose(obs[:,ai,0],expected,atol=1e-12,rtol=0)
                        results.append(dict(session=key[0],scan_idx=key[1],assignment_index=ai,exclude_disputed=assignment['exclude_disputed'],subset=subset,timing=timing,
                            **{method:{name:float(obs[c,ai,k]) for c,name in enumerate(('total','trial_mean','within'))} for k,method in enumerate(('original','supported_baseline','interpolated'))}))
                    primary=obs[:,:scan['assignment_count'],:]
                    summaries.append(dict(session=key[0],scan_idx=key[1],subset=subset,timing=timing,assignments=scan['assignment_count'],
                        **{method:{name:dict(range=[float(primary[c,:,k].min()),float(primary[c,:,k].max())],positive=int((primary[c,:,k]>0).sum())) for c,name in enumerate(('total','trial_mean','within'))} for k,method in enumerate(('original','supported_baseline','interpolated'))}))
        print(key,'assignments',len(assignments),'done',flush=True)
    assert len(support)==429 and len(results)==2574
    save('microns_distance_interpolation_support.json',dict(assignments=support))
    save('microns_distance_interpolation_result.json',dict(results=results,summaries=summaries,code_sha256=sha(Path(__file__)),support_sha256=sha(HERE/'microns_distance_interpolation_support.json')))

if __name__=='__main__':main()
