"""추가 스캔의 세포 제외와 고정 가중 쌍별 기여를 구분한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts
from microns_repeat_shift_control import weights

HERE=Path(__file__).resolve().parent


def main():
    path=ROOT/'data/external/microns_functional_nwb/scan_5_3_repeated_clips.npz'
    receipt=json.loads((HERE/'microns_next_repeats_acquisition.json').read_text());assert sha(path)==receipt['artifact_sha256']
    save('microns_next_cell_influence_contract.json',dict(question='Does one cell account for the late-repeat negative contrast and the change when repeat10 is omitted?',
        selection='All23 single-cell omissions, both timing conventions; all10, first5, last5 and last5 without10. Recompute contrast weights after cell omission; separately decompose last5-minus-without10 using unchanged full-cohort pair weights.',
        limits='Post-observation influence diagnosis. Pair contributions overlap in cells; not additive cell causal effects. No favorable cell exclusions for final claim.',code_sha256=sha(Path(__file__)),response_sha256=sha(path)))
    d=np.load(path);units=d['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)}
    pairs=json.loads((HERE/'microns_next_scan_contrast_pairs.json').read_text())[0]['pairs'];_,w=weights(pairs)
    results=[];decompositions=[]
    for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
        matrices={}
        for subset,repeats in [('all10',list(range(10))),('first5',list(range(5))),('last5',list(range(5,10))),('last_without10',list(range(5,9)))]:
            x=d['values'][mode][:,repeats];n=len(repeats);residual=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
            matrix=np.corrcoef(residual.reshape(-1,23),rowvar=False);matrices[subset]=matrix
            pp=[dict(p,correlation=float(matrix[lookup[p['unit_a']],lookup[p['unit_b']]])) for p in pairs]
            baseline=contrasts(pp)
            omissions=[dict(unit_id=u,**contrasts([p for p in pp if u not in (p['unit_a'],p['unit_b'])])) for u in units]
            results.append(dict(timing=timing,subset=subset,baseline=baseline,omissions=omissions))
        contributions=[]
        for i,p in enumerate(pairs):
            a,b=lookup[p['unit_a']],lookup[p['unit_b']]
            delta=float(matrices['last5'][a,b]-matrices['last_without10'][a,b])
            contributions.append(dict(unit_a=p['unit_a'],unit_b=p['unit_b'],linked=p['linked'],weight=float(w[i]),correlation_change=delta,weighted_change=float(w[i]*delta)))
        direct=float(sum(p['weighted_change'] for p in contributions))
        old=next(r for r in results if r['timing']==timing and r['subset']=='last5')['baseline']['matched_mean_difference']
        new=next(r for r in results if r['timing']==timing and r['subset']=='last_without10')['baseline']['matched_mean_difference']
        assert abs(direct-(old-new))<1e-12
        decompositions.append(dict(timing=timing,total_change=direct,linked_contribution=sum(p['weighted_change'] for p in contributions if p['linked']),unlisted_contribution=sum(p['weighted_change'] for p in contributions if not p['linked']),pairs=sorted(contributions,key=lambda p:abs(p['weighted_change']),reverse=True)))
    save('microns_next_cell_influence_result.json',dict(results=results,decompositions=decompositions,limits='Sensitivity and exact algebraic decomposition; not synaptic causal effects.'))
    for r in results:
        if r['timing']=='positive_delay_sensitivity':
            v=[x['matched_mean_difference'] for x in r['omissions']]
            print(r['subset'],r['baseline']['matched_mean_difference'],min(v),max(v),'positive',sum(x>0 for x in v))
    q=decompositions[1];print('decomposition',q['total_change'],q['linked_contribution'],q['unlisted_contribution']);print('top_pairs',q['pairs'][:3])


if __name__=='__main__':main()
