"""시간 범위 불일치 발견 후 고정한 관측 구간 조건부 탐색."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    ep=HERE/'icms_external_time_extent_result.json';extent=json.loads(ep.read_text(encoding='utf-8'))
    plans=[]
    for subject in ('ICMS92','ICMS98'):
        e=next(s for s in extent['sessions'] if s['subject']==subject)
        selected=[r['trial_id'] for r in e['rows'] if r['inside_wheel'] and (r['stim'] is None or (r['stim']['inside_wheel'] and r['stim']['nominal']))]
        plans.append(dict(subject=subject,selected_trial_ids=selected,excluded_trial_ids=[r['trial_id'] for r in e['rows'] if r['trial_id'] not in selected],input_sha256=e['input_sha256']))
    save('icms_supported_interval_contract.json',dict(question='Within the recorded-time subset of ICMS92/98, what is the fixed posttrain contrast relative to local catch?',
        selection=plans,selection_basis='Previously audited wheel-time support and nominal stimulus geometry only, before reading neural responses in these subjects. Post-discovery exploratory revision; prior5-animal failure remains.',
        method='Use selected trial list, partition into four equal ordinal blocks before good-trial selection. Same pre[-.7,-.2), post[.8,1.3) windows. Reject geometry failures; all original electrical trains used for overlap check. All provided units. Good-only primary and all-quality sensitivity. Per-unit paired change minus block catch; weight blocks by stimulated trial counts. Any missing catch block makes that current undefined.',
        limits='Wheel interval is proxy, not continuous per-unit detection proof. No causal effect or retrospective confirmation claim. No replacement of original whole-session estimand.',code_sha256=sha(Path(__file__)),extent_sha256=sha(ep)))
    results=[];draws={}
    for plan in plans:
        subject=plan['subject'];path=next((ROOT/'data/external/xie_icms_plasticity_2025').glob('sub-'+subject+'*.nwb'));assert sha(path)==plan['input_sha256']
        with h5py.File(path,'r') as f:
            tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];idx={int(v):i for i,v in enumerate(tr['trial_index'][:])};sl={int(v):i for i,v in enumerate(st['trial_index'][:])};starts=st['start_time'][:];stops=st['stop_time'][:]
            wheel=f['processing/behavior/wheel/wheel_position_processed'];lo=float(wheel['starting_time'][()]);hi=lo+len(wheel['data'])/float(wheel['starting_time'].attrs['rate'])
            ids=plan['selected_trial_ids'];units=f['units/id'][:];ends=f['units/spike_times_index'][:].astype(int);sp=f['units/spike_times'][:];assert np.isfinite(sp).all() and ends[-1]==len(sp)
            trains=[sp[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)];assert all(np.all(np.diff(s)>=0) for s in trains)
            counts=np.zeros((len(ids),len(units),2),int);blocks=np.zeros(len(ids),int)
            for b,ix in enumerate(np.array_split(np.arange(len(ids)),4)):blocks[ix]=b
            rows=[]
            for rowid,tid in enumerate(ids):
                i=idx[tid];j=sl.get(tid);current=float(tr['current_uA'][i]);assert (j is None)==(current==0)
                anchor=float(starts[j]) if j is not None else float(tr['start_time'][i]);valid=True
                for k,(a,b) in enumerate([(-.7,-.2),(.8,1.3)]):
                    left,right=anchor+a,anchor+b;valid=valid and left>=lo and right<=hi and not np.any((starts<right)&(stops>left))
                    for u,s in enumerate(trains):
                        ia,ib=np.searchsorted(s,[left,right]);counts[rowid,u,k]=ib-ia
                rows.append(dict(trial_id=tid,current=current,block=int(blocks[rowid]),good=bool(tr['is_good_trial'][i]),geometry_pass=bool(valid)))
        delta=(counts[:,:,1]-counts[:,:,0])/.5;curr=np.array([r['current'] for r in rows]);summaries=[];br=[]
        for quality in ('good_only','all_quality'):
            eligible=np.array([r['geometry_pass'] and (quality=='all_quality' or r['good']) for r in rows])
            for c in sorted(set(curr)-{0.}):
                selected=eligible&(curr==c);missing=[];w=np.zeros(len(ids));n=int(selected.sum())
                if n:w[selected]=1/n
                for b in range(4):
                    sm=selected&(blocks==b);cm=eligible&(curr==0)&(blocks==b)
                    if not sm.any():continue
                    if not cm.any():missing.append(b);continue
                    w[cm]-=sm.sum()/n/cm.sum();dv=delta[sm].mean(axis=0)-delta[cm].mean(axis=0)
                    br.append(dict(quality=quality,current=float(c),block=b,stim=int(sm.sum()),catch=int(cm.sum()),mean=float(dv.mean())))
                if missing or not n:summaries.append(dict(quality=quality,current=float(c),status='UNDEFINED',missing=missing));continue
                assert abs(w.sum())<1e-12;obs=w@delta
                direct=np.array([delta[i]-delta[eligible&(curr==0)&(blocks==blocks[i])].mean(axis=0) for i in np.flatnonzero(selected)]).mean(axis=0)
                assert np.allclose(obs,direct,atol=1e-12)
                summaries.append(dict(quality=quality,current=float(c),status='DEFINED',trials=n,mean=float(obs.mean()),median=float(np.median(obs)),positive=int((obs>0).sum()),negative=int((obs<0).sum()),per_unit=obs.tolist()))
        draws[subject+'_counts']=counts;draws[subject+'_units']=units;draws[subject+'_trials']=np.array(ids)
        result=dict(subject=subject,selected_trials=len(ids),excluded_trial_ids=plan['excluded_trial_ids'],units=units.tolist(),geometry_failures=sum(not r['geometry_pass'] for r in rows),trials=rows,summaries=summaries,blocks=br)
        results.append(result);print(subject,'selected',len(ids),'units',len(units),'geometry',result['geometry_failures'])
        for s in summaries:
            if s['quality']=='good_only':print({k:v for k,v in s.items() if k!='per_unit'})
    dest=HERE/'icms_supported_interval_counts.npz'
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,**draws)
    else:
        with np.load(dest) as a:assert all(np.array_equal(a[k],v) for k,v in draws.items())
    save('icms_supported_interval_result.json',dict(sessions=results,code_sha256=sha(Path(__file__)),counts_sha256=sha(dest)))
if __name__=='__main__':main()
