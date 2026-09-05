"""기존 대비를 자극 변화와 시간 구간별 catch 변화로 분해한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def main():
    sources=['icms_supported_interval_result.json','icms_supported_interval_counts.npz','icms100_external_result.json','icms100_external_counts.npz','icms101_external_result.json','icms101_external_counts.npz','icms93_posttrain_v2_result.json','icms93_posttrain_v2_counts.npz','icms93_behavior_balance_result.json','icms93_time_matched_result.json']
    save('icms_contrast_components_contract.json',dict(question='Which observed pre/post and matched-catch components produce each existing signed contrast?',
        method='Recompute frozen selected populations and four ordinal blocks. For each unit/current/quality report pre/post stimulated means and stimulated-trial-weighted same-block catch pre/post means. Difference of changes must equal existing result. No new exclusions or endpoint changes.',
        limits='Descriptive decomposition, not causal pathways or independent animals per unit. Development ICMS93, original external100/101 and post-discovery92/98 kept distinct; no common confirmation claim.',code_sha256=sha(Path(__file__)),sources={s:sha(HERE/s) for s in sources}))
    configs=[]
    for subject in ('ICMS100','ICMS101'):
        stem=subject.lower()+'_external';r=read(stem+'_result.json');p=HERE/(stem+'_counts.npz');assert sha(p)==r['counts_sha256']
        with np.load(p) as a:counts=a['counts'];units=a['unit_ids'];assert a['trial_ids'].tolist()==[t['trial_id'] for t in r['trials']]
        configs.append((subject,'original_external',r['trials'],counts,units,r['summaries']))
    r=read('icms_supported_interval_result.json');p=HERE/'icms_supported_interval_counts.npz';assert sha(p)==r['counts_sha256']
    with np.load(p) as a:
        for s in r['sessions']:
            subject=s['subject'];assert a[subject+'_trials'].tolist()==[t['trial_id'] for t in s['trials']]
            configs.append((subject,'post_discovery_supported',s['trials'],a[subject+'_counts'],a[subject+'_units'],s['summaries']))
    r=read('icms93_posttrain_v2_result.json');p=HERE/'icms93_posttrain_v2_counts.npz';assert sha(p)==r['counts_sha256']
    behavior={r['trial_index']:r for r in read('icms93_behavior_balance_result.json')['trials']};rows=[dict(trial_id=t['trial_index'],current=t['current_uA'],good=t['is_good_trial'],geometry_pass=t['geometry_pass'],block=behavior[t['trial_index']]['block']) for t in r['trials']]
    prior=[dict(quality=s['quality'],current=s['current_uA'],status='DEFINED',mean=s['time_matched_mean']) for s in read('icms93_time_matched_result.json')['summaries']]
    with np.load(p) as a:configs.append(('ICMS93','development',rows,a['counts'],a['unit_ids'],prior))
    output=[]
    for subject,lineage,rows,counts,units,prior in configs:
        currents=np.array([r['current'] for r in rows]);blocks=np.array([r['block'] for r in rows]);rate=counts/.5
        for quality in ('good_only','all_quality'):
            eligible=np.array([r['geometry_pass'] and (quality=='all_quality' or r['good']) for r in rows])
            for c in sorted(set(currents)-{0.}):
                sel=eligible&(currents==c);smean=rate[sel].mean(axis=0);ctlmean=np.zeros_like(smean)
                for b in range(4):
                    nb=int((sel&(blocks==b)).sum())
                    if not nb:continue
                    ctl=eligible&(currents==0)&(blocks==b);assert ctl.any();ctlmean+=nb/sel.sum()*rate[ctl].mean(axis=0)
                sd=smean[:,1]-smean[:,0];cd=ctlmean[:,1]-ctlmean[:,0];difference=sd-cd
                old=next(s for s in prior if s['quality']==quality and s['current']==c);assert old['status']=='DEFINED' and abs(difference.mean()-old['mean'])<1e-12
                components=dict(stim_pre=float(smean[:,0].mean()),stim_post=float(smean[:,1].mean()),stim_change=float(sd.mean()),matched_catch_pre=float(ctlmean[:,0].mean()),matched_catch_post=float(ctlmean[:,1].mean()),matched_catch_change=float(cd.mean()),contrast=float(difference.mean()),contrast_median=float(np.median(difference)))
                assert abs(components['stim_change']-components['matched_catch_change']-components['contrast'])<1e-12
                output.append(dict(subject=subject,lineage=lineage,quality=quality,current=float(c),trials=int(sel.sum()),units=len(units),**components,
                    per_unit=[dict(unit=int(u),stim_change=float(s),catch_change=float(cc),contrast=float(d)) for u,s,cc,d in zip(units,sd,cd,difference)]))
    assert len(output)==56
    save('icms_contrast_components_result.json',dict(results=output,code_sha256=sha(Path(__file__))))
    for r in output:
        if r['quality']=='good_only':print(r['subject'],r['current'],*[round(r[k],6) for k in ('stim_change','matched_catch_change','contrast')])
if __name__=='__main__':main()
