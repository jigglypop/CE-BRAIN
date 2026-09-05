"""고정 외부 세션의 시행 표와 저장 신호 시간 범위를 대조한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    cp=HERE/'icms_external_first_sessions_contract.json';contract=json.loads(cp.read_text(encoding='utf-8'))
    save('icms_external_time_extent_contract.json',dict(question='Are nonstandard stimulus rows within the time extent of stored signals?',
        method='Inspect all5 fixed first sessions without response estimation. Compare each trial and electrical interval with processed wheel interval [start,start+N/rate). Record last stored spike as descriptive endpoint, not proof of continuous recording. Preserve all out-of-range rows and nominal stimulus flags.',
        limits='A wheel-duration proxy and last spike do not identify the raw acquisition schedule or the origin of unmatched metadata. No correction or exclusion from the prior test.',selection_sha256=sha(cp),code_sha256=sha(Path(__file__))))
    result=[]
    for asset in contract['selected']:
        subject=asset['path'].split('/')[0][4:];base=ROOT/'data/external/xie_icms_plasticity_2025';path=base/Path(asset['path']).name
        meta=json.loads((base/('external_'+asset['asset_id']+'_metadata.json')).read_text(encoding='utf-8'));assert sha(path)==meta['digest']['dandi:sha2-256']
        with h5py.File(path,'r') as f:
            w=f['processing/behavior/wheel/wheel_position_processed'];lo=float(w['starting_time'][()]);hi=lo+len(w['data'])/float(w['starting_time'].attrs['rate'])
            sp=f['units/spike_times'][:];assert np.isfinite(sp).all();last=float(sp.max())
            tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];lookup={int(k):i for i,k in enumerate(st['trial_index'][:])};rows=[]
            for i,tid in enumerate(tr['trial_index'][:]):
                start=float(tr['start_time'][i]);stop=float(tr['stop_time'][i]);j=lookup.get(int(tid));stim=None
                if j is not None:
                    a=float(st['start_time'][j]);b=float(st['stop_time'][j]);pulses=int(st['pulse_count'][j]);freq=float(st['frequency_hz'][j]);nominal=pulses==70 and freq==100 and bool(np.isclose(b-a,.7,atol=1e-8,rtol=0))
                    stim=dict(start=a,stop=b,pulses=pulses,frequency=freq,nominal=nominal,inside_wheel=bool(a>=lo and b<=hi),start_after_last_spike=a>last)
                rows.append(dict(trial_id=int(tid),start=start,stop=stop,current=float(tr['current_uA'][i]),inside_wheel=bool(start>=lo and stop<=hi),start_after_wheel=start>=hi,stim=stim))
            outside=[r for r in rows if not r['inside_wheel']];nonstandard=[r for r in rows if r['stim'] and not r['stim']['nominal']]
            summary=dict(subject=subject,input_sha256=sha(path),wheel_interval=[lo,hi],last_stored_spike=last,trials=len(rows),trial_rows_outside_wheel=len(outside),
                outside_trial_ids=[r['trial_id'] for r in outside],nonstandard_stimuli=len(nonstandard),nonstandard_inside_wheel=sum(r['stim']['inside_wheel'] for r in nonstandard),
                outside_catch=sum(r['stim'] is None for r in outside),rows=rows)
            result.append(summary);print({k:v for k,v in summary.items() if k not in ('rows','outside_trial_ids','input_sha256')})
    save('icms_external_time_extent_result.json',dict(sessions=result,code_sha256=sha(Path(__file__))))
if __name__=='__main__':main()
