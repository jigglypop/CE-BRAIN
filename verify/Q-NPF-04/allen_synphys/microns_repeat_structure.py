"""반복 자극의 평균 패턴과 회차별 잔차에서 기존 구조 대비를 계산한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts

HERE=Path(__file__).resolve().parent


def main():
    path=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz'
    receipt=json.loads((HERE/'microns_repeat_response_acquisition.json').read_text())
    assert sha(path)==receipt['artifact_sha256']
    data=np.load(path);values=data['values'];units=data['unit_ids'].tolist()
    old=json.loads((HERE/'microns_structure_response_pairs.json').read_text())[0]['pairs']
    lookup={u:i for i,u in enumerate(units)}
    results=[]
    for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
        for name,selection in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
            x=values[mode,:,selection,:,:];n=x.shape[1]
            signal=x.mean(axis=1)
            residual=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
            assert np.allclose(residual.sum(axis=1),0,rtol=0,atol=1e-8)
            for component,y in [('raw',x),('repeat_mean',signal),('leave_one_repeat_out_residual',residual)]:
                z=y.reshape(-1,len(units));assert np.isfinite(z).all() and (z.std(axis=0)>0).all()
                corr=np.corrcoef(z,rowvar=False)
                pairs=[dict(p,correlation=float(corr[lookup[p['unit_a']],lookup[p['unit_b']]])) for p in old]
                for exclude in (False,True):
                    selected=[p for p in pairs if not exclude or 3151 not in (p['unit_a'],p['unit_b'])]
                    results.append(dict(timing=timing,repeat_subset=name,component=component,exclude_disputed=exclude,rows=len(z),**contrasts(selected)))
    save('microns_repeat_structure_result.json',dict(results=results,code_sha256=sha(Path(__file__)),aligned_data_sha256=sha(path),
        contrast_code_sha256=sha(HERE/'microns_structure_response.py'),
        limits='All36 planned descriptive contrasts reported. Residual correlation is not direct synaptic coupling or behavior-adjusted correlation. Repeat means estimated from finite samples. Same animal and six clip conditions.'))
    for r in results:
        if r['timing']=='positive_delay_sensitivity' and not r['exclude_disputed']:
            print(r['repeat_subset'],r['component'],'difference',r['mean_difference'],'matched',r['matched_mean_difference'])


if __name__=='__main__':main()
