"""행동 상태를 확인한 뒤 모든 회차 제외 민감도를 같은 규칙으로 검사한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts

HERE=Path(__file__).resolve().parent


def main():
    path=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz'
    data=np.load(path);units=data['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)}
    pairs=json.loads((HERE/'microns_structure_response_pairs.json').read_text())[0]['pairs']
    behavior=json.loads((HERE/'microns_repeat_behavior_result.json').read_text())
    save('microns_repeat_state_sensitivity_contract.json',dict(question='How much does the structural residual contrast depend on any single repeat block, including the high-running block?',
        scope='Post-observation sensitivity; omit each of10 repeats symmetrically across all6 conditions. Recompute leave-one-repeat-out means in retained9. Both timing conventions and unit3151 inclusion/exclusion.',
        limits='Not a behavioral causal adjustment. Remaining pupil missingness and state confounding retained. No new significance claim.',code_sha256=sha(Path(__file__)),response_sha256=sha(path),behavior_sha256=sha(HERE/'microns_repeat_behavior_result.json')))
    result=[]
    for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
        for omit in range(10):
            x=data['values'][mode][:,[r for r in range(10) if r!=omit]]
            residual=x-(x.sum(axis=1,keepdims=True)-x)/8
            assert np.allclose(residual.sum(axis=1),0,atol=1e-8)
            corr=np.corrcoef(residual.reshape(-1,53),rowvar=False)
            row_pairs=[dict(p,correlation=float(corr[lookup[p['unit_a']],lookup[p['unit_b']]])) for p in pairs]
            for exclude in (False,True):
                selected=[p for p in row_pairs if not exclude or 3151 not in (p['unit_a'],p['unit_b'])]
                result.append(dict(timing=timing,omitted_repeat_one_based=omit+1,exclude_disputed=exclude,**contrasts(selected)))
    save('microns_repeat_state_sensitivity_result.json',dict(results=result,repeat_mean_absolute_speed_m_per_s=behavior['summary']['speed']['per_repeat_mean'],limits='All40 sensitivity cases; biological state is observed, not randomized.'))
    for r in result:
        if r['timing']=='positive_delay_sensitivity' and not r['exclude_disputed']:print(r['omitted_repeat_one_based'],r['matched_mean_difference'])


if __name__=='__main__':main()
