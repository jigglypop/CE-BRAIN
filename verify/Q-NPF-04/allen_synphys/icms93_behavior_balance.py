"""전류별 시행 순서·행동·고정 창 바퀴 이동의 기술적 비교."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    source=HERE/'icms93_posttrain_v2_result.json';prior=json.loads(source.read_text(encoding='utf-8'))
    path=ROOT/'data/external/xie_icms_plasticity_2025/sub-ICMS93_ses-2023-10-06_behavior+ecephys+ophys.nwb'
    assert sha(path)=='843e8cfabc9d4e8c8413f3c7f3e3046f47976e83328f98c9144f1e0b26993187'
    save('icms93_behavior_balance_contract.json',dict(question='Are catch and current groups comparable in trial order and measured behavior for the fixed posttrain contrast?',
        method='All204 trials, preserve good flags. Four equal ordinal blocks defined with array_split before behavior values. Per-current trial ordinal/time ranges, hit counts and response times. In original pre/post windows compute wheel endpoint displacement and total absolute first differences, with recorded unit/conversion. No movement threshold or effect correction.',
        limits='Post-treatment movement can be mediator or consequence, not automatically a confounder to adjust. Timing distributions do not prove randomization. Wheel total variation includes noise; no still/moving classification.',
        code_sha256=sha(Path(__file__)),prior_sha256=sha(source),input_sha256=sha(path)))
    rows=[]
    with h5py.File(path,'r') as f:
        tr=f['intervals/trials'];wg=f['processing/behavior/wheel/wheel_position_processed'];d=wg['data'];wheel=d[:].astype(float)*float(d.attrs.get('conversion',1))+float(d.attrs.get('offset',0))
        rate=float(wg['starting_time'].attrs['rate']);t=float(wg['starting_time'][()])+np.arange(len(wheel))/rate
        assert np.isfinite(wheel).all();ids=tr['trial_index'][:];assert len(ids)==204
        blocks=np.zeros(len(ids),int)
        for k,ix in enumerate(np.array_split(np.arange(len(ids)),4)):blocks[ix]=k
        pp={r['trial_index']:r for r in prior['trials']};assert set(pp)==set(ids.tolist())
        for i,tid in enumerate(ids):
            p=pp[int(tid)];windows=[]
            for w in p['windows']:
                a,b=np.searchsorted(t,[w['start'],w['stop']],side='left');v=wheel[a:b];assert len(v)>=2
                windows.append(dict(samples=len(v),displacement=float(v[-1]-v[0]),total_variation=float(np.abs(np.diff(v)).sum())))
            rt=float(tr['response_time'][i]);rows.append(dict(trial_index=int(tid),ordinal=i+1,block=int(blocks[i]),current_uA=p['current_uA'],anchor=p['anchor'],
                good=p['is_good_trial'],hit=bool(tr['is_hit'][i]),response_time=rt if np.isfinite(rt) else None,pre=windows[0],post=windows[1]))
        wheelmeta=dict(unit=str(d.attrs.get('unit','unknown')),conversion=float(d.attrs.get('conversion',1)),offset=float(d.attrs.get('offset',0)),description=str(wg.attrs.get('description','')))
    summaries=[]
    for quality in ('good_only','all_quality'):
        for current in sorted({r['current_uA'] for r in rows}):
            rr=[r for r in rows if r['current_uA']==current and (quality=='all_quality' or r['good'])];rts=[r['response_time'] for r in rr if r['response_time'] is not None]
            summaries.append(dict(quality=quality,current_uA=current,n=len(rr),hits=sum(r['hit'] for r in rr),finite_response_times=len(rts),
                ordinal_range=[min(r['ordinal'] for r in rr),max(r['ordinal'] for r in rr)],time_range=[min(r['anchor'] for r in rr),max(r['anchor'] for r in rr)],
                block_counts=[sum(r['block']==k for r in rr) for k in range(4)],
                response_time_median=float(np.median(rts)) if rts else None,
                pre_tv_median=float(np.median([r['pre']['total_variation'] for r in rr])),post_tv_median=float(np.median([r['post']['total_variation'] for r in rr])),
                pre_tv_mean=float(np.mean([r['pre']['total_variation'] for r in rr])),post_tv_mean=float(np.mean([r['post']['total_variation'] for r in rr]))))
    save('icms93_behavior_balance_result.json',dict(trials=rows,summaries=summaries,wheel_metadata=wheelmeta,code_sha256=sha(Path(__file__))))
    print(wheelmeta)
    for s in summaries:
        if s['quality']=='good_only':print(s)
if __name__=='__main__':main()
