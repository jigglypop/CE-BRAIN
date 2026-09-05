"""미리 고정한 ICMS98 다음 날짜 세션의 wheel–발화 방향 검사."""
import json
from pathlib import Path
import h5py
import numpy as np
from scipy.stats import rankdata
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def corr(x,y):
    if len(x)<3 or np.ptp(x)==0 or np.ptp(y)==0:return None
    return float(np.corrcoef(x,y)[0,1])
def main():
    cp=HERE/'icms98_next_session_contract.json';c=read(cp)
    base=ROOT/'data/external/xie_icms_plasticity_2025';p=base/Path(c['asset']['path']).name
    m=read(base/'icms98_20231024_asset_metadata.json')
    assert p.stat().st_size==c['asset']['size'] and sha(p)==m['digest']['dandi:sha2-256']
    save('icms98_next_session_execution_contract.json',dict(code_sha256=sha(Path(__file__)),contract_sha256=sha(cp),input_sha256=sha(p)))
    def stop(reason):
        save('icms98_next_session_result.json',dict(status='UNASSESSED',reason=reason));print(reason)
    with h5py.File(p,'r') as f:
        required=['intervals/trials','intervals/electrical_stimulation','units/spike_times','units/spike_times_index','processing/behavior/wheel/wheel_position_processed']
        if any(n not in f for n in required):return stop('missing required group')
        tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];ids=tr['trial_index'][:]
        if len(ids)<400:return stop('fewer than 400 trials')
        assert len(set(ids.tolist()))==len(ids)
        lookup={int(t):i for i,t in enumerate(ids)}
        wg=f['processing/behavior/wheel/wheel_position_processed'];d=wg['data']
        wheel=d[:].astype(float)*float(d.attrs.get('conversion',1))+float(d.attrs.get('offset',0))
        lo=float(wg['starting_time'][()]);rate=float(wg['starting_time'].attrs['rate']);hi=lo+len(wheel)/rate
        starts=st['start_time'][:];stops=st['stop_time'][:];sids=st['trial_index'][:]
        if not (np.isfinite(wheel).all() and np.isfinite(starts).all() and np.isfinite(stops).all()):return stop('nonfinite wheel or stimulus times')
        nominal=(st['frequency_hz'][:]==100)&(st['pulse_count'][:]==70)&np.isclose(stops-starts,.7,atol=1e-8,rtol=0)
        selected=np.array([lookup[int(t)]<400 for t in sids])&(starts>=lo)&(stops<=hi)&nominal
        if not selected.any():return stop('no supported nominal stimulus for shift')
        delay=float(np.median([starts[j]-float(tr['start_time'][lookup[int(sids[j])]]) for j in np.flatnonzero(selected)]))
        spikes=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int)
        if not len(ends) or not np.isfinite(spikes).all():return stop('missing or nonfinite spikes')
        assert ends[-1]==len(spikes)
        trains=[spikes[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)]
        assert all(np.all(np.diff(s)>=0) for s in trains)
        times=lo+np.arange(len(wheel))/rate;rows=[];rejected=[];candidates=0
        for i in range(400):
            if float(tr['current_uA'][i])!=0 or not bool(tr['is_good_trial'][i]) or bool(tr['is_hit'][i]) or np.isfinite(tr['response_time'][i]):continue
            candidates+=1;origin=float(tr['start_time'][i]);variants=[];valid=True
            for shift in (0.,delay):
                anchor=origin+shift;counts=[];windows=[]
                for a,b in ((anchor-.7,anchor-.2),(anchor+.8,anchor+1.3)):
                    if not (np.isfinite(a) and np.isfinite(b) and a>=lo and b<=hi and not np.any((starts<b)&(stops>a))):valid=False;break
                    ia,ib=np.searchsorted(times,[a,b]);v=wheel[ia:ib]
                    if len(v)<2:valid=False;break
                    windows.append(dict(samples=len(v),tv=float(np.abs(np.diff(v)).sum())))
                    counts.append([int(np.searchsorted(s,b)-np.searchsorted(s,a)) for s in trains])
                if not valid:break
                changes=(np.array(counts[1])-np.array(counts[0]))*2
                variants.append(dict(wheel=windows,counts=counts,mean_unit_change_hz=float(changes.mean())))
            if valid:rows.append(dict(trial_id=int(ids[i]),ordinal=i+1,block=i//100,variants=variants))
            else:rejected.append(int(ids[i]))
    blocks=np.array([r['block'] for r in rows]);sizes=[int((blocks==b).sum()) for b in range(4)]
    result=dict(subject='ICMS98',session='2023-10-24',original_trials=len(ids),units=len(trains),
                candidates=candidates,geometry_rejected=rejected,block_counts=sizes,delay_s=delay,trials=rows,summaries=[])
    if min(sizes)<3:result.update(status='UNASSESSED',reason='fewer than3 eligible catches in a block')
    else:
        for k in (0,1):
            x=np.array([r['variants'][k]['wheel'][1]['tv'] for r in rows]);y=np.array([r['variants'][k]['mean_unit_change_hz'] for r in rows])
            rx=rankdata(x);ry=rankdata(y);rho=corr(rx,ry)
            for b in range(4):
                mask=blocks==b;rx[mask]-=rx[mask].mean();ry[mask]-=ry[mask].mean()
            result['summaries'].append(dict(anchor=('trial_start','shifted')[k],spearman=rho,block_centered_rank_correlation=corr(rx,ry),mean_firing_change=float(y.mean())))
        values=[s[key] for s in result['summaries'] for key in ('spearman','block_centered_rank_correlation')]
        result['status']='UNASSESSED' if any(v is None for v in values) else ('DIRECTION_SUPPORTED' if all(v>0 for v in values) else 'DIRECTION_FAILED')
    save('icms98_next_session_result.json',result)
    print({k:v for k,v in result.items() if k!='trials'})
if __name__=='__main__':main()
