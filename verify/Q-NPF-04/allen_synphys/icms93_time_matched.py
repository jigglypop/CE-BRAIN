"""고정 네 시간 구간의 catch를 사용한 전후 발화 대비."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def main():
    behavior=read('icms93_behavior_balance_result.json');prior=read('icms93_posttrain_v2_result.json');p=HERE/'icms93_posttrain_v2_counts.npz'
    assert sha(p)==prior['counts_sha256']
    save('icms93_time_matched_contract.json',dict(question='Does posttrain-minus-pre minus catch remain negative when catch is matched within the frozen four ordinal blocks?',
        method='Same windows, units and good-only/all-quality selections. Within each block subtract per-unit catch mean paired difference from current mean paired difference. Average blocks by number of eligible stimulated trials; do not extrapolate absent current blocks. Preserve original global-catch contrast and all block results.',
        limits='Exploratory coarse time stratification. Blocks are not independent replicates, within-block drift and movement remain. No p-value or causal identification.',code_sha256=sha(Path(__file__)),behavior_sha256=sha(HERE/'icms93_behavior_balance_result.json'),prior_sha256=sha(HERE/'icms93_posttrain_v2_result.json'),counts_sha256=sha(p)))
    with np.load(p) as a:counts=a['counts'];ids=a['trial_ids'];units=a['unit_ids']
    byid={r['trial_index']:r for r in behavior['trials']};geom={r['trial_index']:r['geometry_pass'] for r in prior['trials']};rows=[byid[int(i)] for i in ids]
    assert len(rows)==204 and len(units)==33
    delta=(counts[:,:,1]-counts[:,:,0])/.5;block=np.array([r['block'] for r in rows]);current=np.array([r['current_uA'] for r in rows])
    summaries=[];details=[]
    for quality in ('good_only','all_quality'):
        eligible=np.array([geom[r['trial_index']] and (quality=='all_quality' or r['good']) for r in rows]);globalcatch=delta[eligible&(current==0)].mean(axis=0)
        for c in sorted(set(current)-{0.}):
            total=np.zeros(len(units));den=0;missing=[];supported=[]
            for b in range(4):
                sel=eligible&(current==c)&(block==b);ctl=eligible&(current==0)&(block==b)
                if not sel.any():
                    details.append(dict(quality=quality,current_uA=float(c),block=b,status='CURRENT_ABSENT',stim_trials=0,catch_trials=int(ctl.sum())));continue
                if not ctl.any():missing.append(b);continue
                d=delta[sel].mean(axis=0)-delta[ctl].mean(axis=0);total+=sel.sum()*d;den+=int(sel.sum());supported.append(b)
                details.append(dict(quality=quality,current_uA=float(c),block=b,status='DEFINED',stim_trials=int(sel.sum()),catch_trials=int(ctl.sum()),per_unit=d.tolist(),mean=float(d.mean())))
            assert not missing and den==int((eligible&(current==c)).sum())
            matched=total/den;original=delta[eligible&(current==c)].mean(axis=0)-globalcatch
            # Trialwise lookup independently verifies weighted block construction.
            direct=np.array([delta[i]-delta[eligible&(current==0)&(block==block[i])].mean(axis=0) for i in np.flatnonzero(eligible&(current==c))]).mean(axis=0)
            assert np.allclose(matched,direct,atol=1e-12)
            old=next(s for s in prior['summaries'] if s['quality']==quality and s['current_uA']==c)
            assert abs(original.mean()-old['mean_catch_adjusted_delta_hz'])<1e-12
            summaries.append(dict(quality=quality,current_uA=float(c),trials=den,supported_blocks=supported,global_catch_mean=float(original.mean()),time_matched_mean=float(matched.mean()),
                per_unit=matched.tolist(),positive_units=int((matched>0).sum()),negative_units=int((matched<0).sum())))
    save('icms93_time_matched_result.json',dict(summaries=summaries,blocks=details,unit_ids=units.tolist(),code_sha256=sha(Path(__file__))))
    for s in summaries:print({k:v for k,v in s.items() if k!='per_unit'})
    for s in details:
        if s['quality']=='good_only':print({k:v for k,v in s.items() if k!='per_unit'})
if __name__=='__main__':main()
