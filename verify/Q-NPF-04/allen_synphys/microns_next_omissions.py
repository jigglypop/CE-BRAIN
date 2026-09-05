"""추가 스캔의 부호 차이를 모든 조건·회차 제외로 대칭 검사한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts

HERE=Path(__file__).resolve().parent


def main():
    path=ROOT/'data/external/microns_functional_nwb/scan_5_3_repeated_clips.npz'
    receipt=json.loads((HERE/'microns_next_repeats_acquisition.json').read_text());assert sha(path)==receipt['artifact_sha256']
    save('microns_next_omissions_contract.json',dict(question='Does the first5/last5 residual-contrast sign difference depend on one condition or one repeat?',
        method='Both timing conventions; all10/first5/last5. Omit each condition and each repeat separately, recompute condition-specific leave-one-repeat-out residuals in retained data. Keep all23 cells and original pair/geometry weights.',
        limits='Post-observation sensitivity, not independent tests or confidence intervals. No selection of favorable omissions, no causal claim.',code_sha256=sha(Path(__file__)),input_sha256=sha(path)))
    data=np.load(path);lookup={int(u):i for i,u in enumerate(data['unit_ids'])}
    pairs=json.loads((HERE/'microns_next_scan_contrast_pairs.json').read_text())[0]['pairs']
    prior=json.loads((HERE/'microns_next_repeat_contrast_result.json').read_text())['results'];out=[]
    for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
        for subset,repeats in [('all10',list(range(10))),('first5',list(range(5))),('last5',list(range(5,10)))]:
            cases=[('none',None,list(range(6)),repeats)]
            cases += [('condition',c,[i for i in range(6) if i!=c],repeats) for c in range(6)]
            cases += [('repeat',r,list(range(6)),[i for i in repeats if i!=r]) for r in repeats]
            for kind,omitted,conditions,retained in cases:
                x=data['values'][mode][conditions][:,retained];n=len(retained)
                residual=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
                assert np.allclose(residual.sum(axis=1),0,atol=1e-8)
                corr=np.corrcoef(residual.reshape(-1,23),rowvar=False)
                pp=[dict(p,correlation=float(corr[lookup[p['unit_a']],lookup[p['unit_b']]])) for p in pairs]
                summary=contrasts(pp)
                if kind=='none':
                    old=next(r for r in prior if r['timing']==timing and r['repeat_subset']==subset and r['component']=='leave_one_repeat_out_residual')
                    assert abs(summary['matched_mean_difference']-old['matched_mean_difference'])<1e-12
                out.append(dict(timing=timing,repeat_subset=subset,omission=kind,omitted_index_one_based=None if omitted is None else omitted+1,retained_conditions=len(conditions),retained_repeats=n,**summary))
    save('microns_next_omissions_result.json',dict(results=out,limits='Ranges describe omission sensitivity, not statistical uncertainty.'))
    for subset in ('all10','first5','last5'):
        for kind in ('condition','repeat'):
            rows=[r for r in out if r['timing']=='positive_delay_sensitivity' and r['repeat_subset']==subset and r['omission']==kind]
            values=[r['matched_mean_difference'] for r in rows]
            print(subset,kind,min(values),max(values),'positive',sum(v>0 for v in values),'total',len(values))


if __name__=='__main__':main()
