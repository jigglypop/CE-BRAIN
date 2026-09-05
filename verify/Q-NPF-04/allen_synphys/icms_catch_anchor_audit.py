"""기록된 자극 지연과 catch 시간 기준의 탐색적 민감도 검사."""
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
BASE = ROOT / 'data/external/xie_icms_plasticity_2025'
DATES = {'ICMS93':'2023-10-06', 'ICMS100':'2023-10-26',
         'ICMS101':'2023-10-27', 'ICMS92':'2023-08-30', 'ICMS98':'2023-10-20'}

def main():
    paths = {s: BASE / f'sub-{s}_ses-{date}_behavior+ecephys+ophys.nwb'
             for s, date in DATES.items()}
    source = BASE / 'code/processing/dataloader.py'
    save('icms_catch_anchor_audit_contract.json', dict(
        question='Does using a session-median pseudo-stimulation delay change catch pre/post firing?',
        status='EXPLORATORY_SOURCE_AND_CLOCK_SENSITIVITY',
        code_sha256=sha(Path(__file__)), loader_sha256=sha(source),
        inputs={s:dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for s,p in paths.items()},
        selection='First 400 trials for ICMS92/98; all trials otherwise. Good catch trials only.',
        windows=[[-.7,-.2],[.8,1.3]],
        anchors=['trial_start','trial_start + median supported stimulation delay'],
        geometry='Both windows inside wheel recording and no electrical train overlap; report rejected counts.',
        limitation='Session median is a sensitivity diagnostic, not reconstruction of per-MAT-file original loader; no cue/reward causal attribution.',
        claim_ceiling='L1 scope-limited catch firing observation; no causal mechanism'))
    results=[]
    for subject,path in paths.items():
        with h5py.File(path,'r') as f:
            tr=f['intervals/trials']; st=f['intervals/electrical_stimulation']
            ids=tr['trial_index'][:]; current=tr['current_uA'][:]
            supported=np.arange(len(ids)) < (400 if subject in ('ICMS92','ICMS98') else len(ids))
            starts=st['start_time'][:]; stops=st['stop_time'][:]
            lookup={int(t):i for i,t in enumerate(ids)}
            delay=np.array([a-float(tr['start_time'][lookup[int(t)]])
                            for t,a in zip(st['trial_index'][:],starts) if supported[lookup[int(t)]]])
            assert np.isfinite(delay).all()
            median=float(np.median(delay))
            wheel=f['processing/behavior/wheel/wheel_position_processed']
            lo=float(wheel['starting_time'][()]); hi=lo+len(wheel['data'])/float(wheel['starting_time'].attrs['rate'])
            sp=f['units/spike_times'][:]; ends=f['units/spike_times_index'][:].astype(int)
            trains=[sp[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)]
            selected=np.flatnonzero(supported & (current==0) & tr['is_good_trial'][:].astype(bool))
            rows=[]
            for i in selected:
                variants=[]
                for shift in (0.,median):
                    anchor=float(tr['start_time'][i])+shift
                    windows=[(anchor-.7,anchor-.2),(anchor+.8,anchor+1.3)]
                    valid=all(a>=lo and b<=hi and not np.any((starts<b)&(stops>a)) for a,b in windows)
                    counts=[[int(np.searchsorted(s,b)-np.searchsorted(s,a)) for a,b in windows] for s in trains]
                    variants.append(dict(geometry_pass=bool(valid),counts=counts))
                rows.append(dict(trial_id=int(ids[i]),variants=variants))
            paired=[r for r in rows if all(v['geometry_pass'] for v in r['variants'])]
            summaries=[]
            for k in (0,1):
                counts=np.array([r['variants'][k]['counts'] for r in paired])
                assert len(counts)>0
                change=(counts[:,:,1]-counts[:,:,0])*2
                summaries.append(dict(anchor=('trial_start','shifted')[k],trials=len(paired),
                    mean_change_hz=float(change.mean()),per_unit_change_hz=change.mean(axis=0).tolist()))
            event_names=[]
            f.visit(lambda name: event_names.append(name) if any(t in name.lower() for t in ('reward','cue','tone')) else None)
            results.append(dict(subject=subject,delay_count=len(delay),
                delay_quantiles_s=np.quantile(delay,[0,.25,.5,.75,1]).tolist(),
                catch_trials=len(selected),paired_geometry_rejected=len(rows)-len(paired),
                summaries=summaries,trials=rows,cue_reward_named_paths=event_names,
                trial_descriptions={k:str(tr[k].attrs.get('description','')) for k in tr.keys()}))
    save('icms_catch_anchor_audit_result.json',dict(subjects=results))
    for r in results:
        print(r['subject'], 'delay',r['delay_quantiles_s'],'catch',r['catch_trials'],
              'rejected',r['paired_geometry_rejected'],
              'changes',[s['mean_change_hz'] for s in r['summaries']],
              'event_paths',r['cue_reward_named_paths'])

if __name__=='__main__':main()
