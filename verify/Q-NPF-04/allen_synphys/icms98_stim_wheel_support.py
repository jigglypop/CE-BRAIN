"""자극 시행의 행동 입력이 개발 catch 범위에 있는지 검사한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text(encoding='utf-8'))
def main():
    base=ROOT/'data/external/xie_icms_plasticity_2025'
    paths={date:base/f'sub-ICMS98_ses-{date}_behavior+ecephys+ophys.nwb' for date in ('2023-10-20','2023-10-24')}
    ranges=[s['development_tv_range'] for s in read('icms98_behavior_model_transfer_result.json')['summaries']]
    save('icms98_stim_wheel_support_contract.json',dict(code_sha256=sha(Path(__file__)),
        inputs={d:sha(p) for d,p in paths.items()},model_sha256=sha(HERE/'icms98_behavior_model_transfer_result.json'),
        method='First400 ordinal trials each session; good nonzero-current trials with nominal100Hz70pulse700ms train. Anchor at recorded stimulus start; original pre/post half-open500ms windows. Both windows within wheel record, no train overlaps. Compare post TV against each frozen development catch range; no outcome-dependent filtering.',
        report='Per current and response-indicator group, below/within/above range counts. Also development same-block catch range for primary anchor.',
        limits='Input-support audit only. Do not compute direct-effect residual or infer causal adjustment validity from range overlap.'))
    development=next(s for s in read('icms_catch_wheel_coupling_result.json')['subjects'] if s['subject']=='ICMS98')
    original=next(s for s in read('icms_supported_interval_result.json')['sessions'] if s['subject']=='ICMS98')
    blockmap={r['trial_id']:r['block'] for r in original['trials']}
    localranges={}
    for b in range(4):
        vals=[r['variants'][0]['post']['tv'] for r in development['trials'] if blockmap[r['trial_id']]==b]
        localranges[b]=[min(vals),max(vals)]
    results=[]
    for date,p in paths.items():
        with h5py.File(p,'r') as f:
            tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];ids=tr['trial_index'][:]
            assert len(ids)>=400 and len(set(ids.tolist()))==len(ids)
            starts=st['start_time'][:];stops=st['stop_time'][:];lookup={int(t):j for j,t in enumerate(st['trial_index'][:])}
            assert len(lookup)==len(starts)
            wg=f['processing/behavior/wheel/wheel_position_processed'];d=wg['data']
            w=d[:].astype(float)*float(d.attrs.get('conversion',1))+float(d.attrs.get('offset',0))
            lo=float(wg['starting_time'][()]);rate=float(wg['starting_time'].attrs['rate']);hi=lo+len(w)/rate;times=lo+np.arange(len(w))/rate
            assert np.isfinite(w).all()
            rows=[];excluded=[]
            for i in range(400):
                if not tr['is_good_trial'][i] or tr['current_uA'][i]==0:continue
                tid=int(ids[i]);j=lookup.get(tid)
                if j is None or st['frequency_hz'][j]!=100 or st['pulse_count'][j]!=70 or not np.isclose(stops[j]-starts[j],.7,atol=1e-8,rtol=0):
                    excluded.append(dict(trial_id=tid,reason='non_nominal_or_missing_stim'));continue
                anchor=float(starts[j]);windows=[(anchor-.7,anchor-.2),(anchor+.8,anchor+1.3)]
                if not all(a>=lo and b<=hi and not np.any((starts<b)&(stops>a)) for a,b in windows):
                    excluded.append(dict(trial_id=tid,reason='geometry'));continue
                a,b=np.searchsorted(times,windows[1]);v=w[a:b];assert len(v)>=2
                tv=float(np.abs(np.diff(v)).sum());status=lambda r:'below' if tv<r[0] else ('above' if tv>r[1] else 'within')
                rows.append(dict(trial_id=tid,current=float(tr['current_uA'][i]),block=i//100,
                    response_indicator=bool(tr['is_hit'][i] or np.isfinite(tr['response_time'][i])),post_tv=tv,
                    global_support=[status(r) for r in ranges],development_block_support=status(localranges[i//100])))
        summaries=[]
        for current in sorted({r['current'] for r in rows}):
            for response in (False,True):
                rr=[r for r in rows if r['current']==current and r['response_indicator']==response]
                if not rr:continue
                summaries.append(dict(current=current,response_indicator=response,trials=len(rr),
                    global_counts=[{s:sum(r['global_support'][k]==s for r in rr) for s in ('below','within','above')} for k in (0,1)],
                    development_block_counts={s:sum(r['development_block_support']==s for r in rr) for s in ('below','within','above')}))
        totals=[{s:sum(r['global_support'][k]==s for r in rows) for s in ('below','within','above')} for k in (0,1)]
        results.append(dict(session=date,eligible=len(rows),excluded=excluded,totals=totals,summaries=summaries,trials=rows))
        print(date,'eligible',len(rows),'excluded',len(excluded),'totals',totals)
        print('groups',summaries)
    save('icms98_stim_wheel_support_result.json',dict(development_ranges=ranges,development_block_ranges=localranges,sessions=results))
if __name__=='__main__':main()
