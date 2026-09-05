"""응답 표지 없는 catch에서 wheel 변화와 발화 변화의 기술적 동반성."""
import json
from pathlib import Path
import h5py
import numpy as np
from scipy.stats import rankdata
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def corr(x,y):
    if len(x)<3 or np.ptp(x)==0 or np.ptp(y)==0:return None
    return float(np.corrcoef(rankdata(x),rankdata(y))[0,1])
def main():
    parent=read('icms_catch_response_split_contract.json')
    split=read('icms_catch_response_split_result.json')['subjects']
    clocks={r['subject']:r for r in read('icms_catch_anchor_audit_result.json')['subjects']}
    save('icms_catch_wheel_coupling_contract.json',dict(
        code_sha256=sha(Path(__file__)),inputs=parent['inputs'],
        parents={n:sha(HERE/n) for n in ['icms_catch_response_split_result.json','icms_catch_anchor_audit_result.json']},
        selection='Existing paired valid good catches with neither hit nor finite response time; both prior anchors.',
        method='Wheel total absolute first difference and signed displacement in same half-open 500ms pre/post windows; trial-level mean-unit firing change; Spearman association with post TV and TV change. Lower half by post TV with trial ID tie-break, floor(n/2).',
        limits='Exploratory description, no motion threshold, causal regression, independent cell sample, or significance test. Lower half is relative wheel variation, not stillness.'))
    results=[]
    for subject in split:
        name=subject['subject'];p=ROOT/parent['inputs'][name]['path']
        assert sha(p)==parent['inputs'][name]['sha256']
        selected=[r for r in subject['trials'] if not(r['hit'] or r['finite_response_time'])]
        with h5py.File(p,'r') as f:
            tr=f['intervals/trials'];lookup={int(t):i for i,t in enumerate(tr['trial_index'][:])}
            wg=f['processing/behavior/wheel/wheel_position_processed'];d=wg['data']
            wheel=d[:].astype(float)*float(d.attrs.get('conversion',1))+float(d.attrs.get('offset',0))
            rate=float(wg['starting_time'].attrs['rate']);start=float(wg['starting_time'][()])
            times=start+np.arange(len(wheel))/rate
            assert np.isfinite(wheel).all() and rate>0
            metadata=dict(unit=str(d.attrs.get('unit','unknown')),rate=rate,description=str(wg.attrs.get('description','')))
            rows=[]
            for r in selected:
                origin=float(tr['start_time'][lookup[r['trial_id']]])
                variants=[]
                for k,shift in enumerate((0.,clocks[name]['delay_quantiles_s'][2])):
                    anchor=origin+shift;windows=[]
                    for left,right in ((anchor-.7,anchor-.2),(anchor+.8,anchor+1.3)):
                        a,b=np.searchsorted(times,[left,right]);v=wheel[a:b]
                        assert len(v)>=2 and left>=start and right<=start+len(wheel)/rate
                        windows.append(dict(samples=len(v),tv=float(np.abs(np.diff(v)).sum()),displacement=float(v[-1]-v[0])))
                    variants.append(dict(pre=windows[0],post=windows[1],mean_unit_change_hz=float(np.mean(r['changes'][k]))))
                rows.append(dict(trial_id=r['trial_id'],variants=variants))
        summaries=[]
        for k in (0,1):
            v=[r['variants'][k] for r in rows]
            pre=np.array([a['pre']['tv'] for a in v]);post=np.array([a['post']['tv'] for a in v]);y=np.array([a['mean_unit_change_hz'] for a in v])
            ix=sorted(range(len(rows)),key=lambda i:(post[i],rows[i]['trial_id']))[:len(rows)//2]
            summaries.append(dict(anchor=('trial_start','shifted')[k],trials=len(v),
                pre_tv_median=float(np.median(pre)),post_tv_median=float(np.median(post)),
                tv_increase_trials=int((post>pre).sum()),post_tv_firing_spearman=corr(post,y),
                tv_change_firing_spearman=corr(post-pre,y),mean_firing_change=float(y.mean()),
                lower_half_trials=[rows[i]['trial_id'] for i in ix],lower_half_mean_firing_change=float(y[ix].mean()),
                lower_half_post_tv_range=[float(post[ix].min()),float(post[ix].max())]))
        results.append(dict(subject=name,wheel_metadata=metadata,trials=rows,summaries=summaries))
    save('icms_catch_wheel_coupling_result.json',dict(subjects=results))
    for r in results:
        for s in r['summaries']:print(r['subject'],s)
if __name__=='__main__':main()
