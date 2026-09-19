"""Observe pre-well approach activity independently of the odor-period readout.

Stored event counts and position support are preserved; continuous unit detection
and a pure spatial representation are not established by these windows.
"""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PINS={
 HERE/'odor_place_windows.py':'1379b05aa9cef13118241befe1791f5ae089ceb55cb5b412b025634451aadf1d',
 HERE/'odor_place_windows_complete_result.json':'4df360cb600b6894cdaec746e6cb9843aedada5f4efc671f0aa8ca32a4dca166',
 HERE/'odor_place_tetrode_regions_result.json':'30c74fb53563a56a190469a62143f4c5ce0bef427307b7bc14c275820e4b7891',
 ROOT/'data/local/hippocampal-reinstatement/odor-place-input-index-v2/index.json':'8580a2c9f73057de5c1b3c11292e804792bd8e98b9edb9ddc7db7d2defbd4272',
 ROOT/'data/external/hippocampal_reinstatement/dandi001539_0.250815.1203_cohort_metadata_v1/all_assets_summary.json':'9c98884de317bce80605e70d0bd1dddfb4ecd065dc081ce6e734168687badacc',
}


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def window_builder():
    path=HERE/'odor_place_windows.py'
    if sha(path)!=PINS[path]:raise ValueError('Frozen window builder changed')
    spec=importlib.util.spec_from_file_location('frozen_odor_windows',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def temporal_window(trial,epoch,next_onset):
    choice=trial['choice_time_s']
    if choice is None:return None,['unresolved_choice']
    bounds=(float(choice)-.5,float(choice));start,stop=bounds
    if not np.isfinite([start,stop,*epoch,next_onset]).all():
        raise ValueError('Nonfinite trial or task times')
    reasons=[]
    if not epoch[0]<=start<stop<=epoch[1]:reasons.append('outside_task_epoch')
    if start<trial['stop_s']+.5:reasons.append('overlaps_postcue_or_nosepoke')
    if stop>next_onset:reasons.append('overlaps_next_nosepoke')
    return bounds,reasons


def load_values(entry,key):
    record=entry['hdf'][key];path=ROOT/record['path']
    if path.stat().st_size!=record['bytes'] or sha(path)!=record['sha256']:raise ValueError('Payload changed')
    return np.fromfile(path,dtype=np.dtype(record['dtype_str'])).reshape(record['shape'])


def build_session(session,audit,entry,previous_valid,builder):
    spikes_raw=load_values(entry,'/units/spike_times')
    ends=load_values(entry,'/units/spike_times_index')
    times=load_values(entry,'/processing/behavior/Position/SpatialSeries/timestamps')
    positions=load_values(entry,'/processing/behavior/Position/SpatialSeries/data')
    positions=positions*entry['position_conversion']+entry['position_offset']
    ids=audit['units']['values']['id']
    if ids!=session['unit_ids']:raise ValueError('Unit identity differs')
    if times.ndim!=1 or positions.shape!=(len(times),3) or not np.isfinite(times).all() or np.any(np.diff(times)<=0) or not np.isfinite(positions).all():
        raise ValueError('Invalid observed Position')
    spikes=builder.unit_spikes(spikes_raw,ends,len(ids))
    n=len(session['trials']);u=len(ids)
    if previous_valid.shape!=(n,4) or previous_valid.dtype!=bool:raise ValueError('Invalid parent mask')
    counts=np.zeros((n,u),np.int32);motion=np.zeros((n,8));valid=np.zeros(n,bool);records=[]
    epochs=audit['interval_tables']['epoch intervals']['values']
    for j,t in enumerate(session['trials']):
        row=t['task_epoch_row'];epoch=(epochs['start_time'][row],epochs['stop_time'][row])
        next_onset=session['trials'][j+1]['start_s'] if j+1<n else epoch[1]
        bounds,reasons=temporal_window(t,epoch,next_onset)
        support=None
        if bounds is not None:
            features,support=builder.position_window(times,positions,*bounds)
            reasons.extend(support['reasons'])
            if not reasons:
                valid[j]=True;motion[j]=features
                counts[j]=[builder.count_window(s,*bounds) for s in spikes]
        records.append(dict(trial_index=j,trial_id=t['trial_id'],source_epoch=t['source_epoch'],
            task_epoch_row=row,start_s=None if bounds is None else bounds[0],stop_s=None if bounds is None else bounds[1],
            reasons=reasons,position_support=support))
    common=previous_valid.all(axis=1)&valid
    output=dict(asset_id=session['asset_id'],identifier=session['identifier'],rat=session['rat'],day=session['day'],
                unit_ids=ids,trials=records,summary=dict(trials=n,approach_valid=int(valid.sum()),
                all_five_valid=int(common.sum()),reasons=dict(Counter(r for t in records for r in t['reasons']))))
    return output,dict(counts=counts,motion=motion,valid=valid,common_valid=common)


def main():
    result_path=HERE/'odor_place_approach_windows_result.json'
    npz_path=ROOT/'data/local/hippocampal-reinstatement/odor-place-approach-windows-v1/windows.npz'
    if result_path.exists() or npz_path.exists():raise FileExistsError('Preserve previous approach windows')
    for path,digest in PINS.items():
        if sha(path)!=digest:raise ValueError('Frozen input changed: '+str(path))
    builder=window_builder()
    parent=json.loads((HERE/'odor_place_windows_complete_result.json').read_text(encoding='utf-8'))
    previous_path=ROOT/parent['npz']['path']
    if sha(previous_path)!=parent['npz']['sha256']:raise ValueError('Parent arrays changed')
    previous=np.load(previous_path,allow_pickle=False)
    index=json.loads((ROOT/'data/local/hippocampal-reinstatement/odor-place-input-index-v2/index.json').read_text(encoding='utf-8'))
    entries={s['asset_id']:s for s in index['sessions']}
    regions=json.loads((HERE/'odor_place_tetrode_regions_result.json').read_text(encoding='utf-8'))
    eligible={s['asset_id'] for s in regions['sessions'] if s['eligible']}
    if set(entries)!=eligible or {s['asset_id'] for s in parent['sessions']}!=eligible:raise ValueError('Cohort coverage differs')
    metadata_path=ROOT/'data/external/hippocampal_reinstatement/dandi001539_0.250815.1203_cohort_metadata_v1/all_assets_summary.json'
    audits={s['asset_id']:s['audit'] for s in json.loads(metadata_path.read_text(encoding='utf-8'))['results']}
    rows=[];payload={}
    for session in parent['sessions']:
        row,arrays=build_session(session,audits[session['asset_id']],entries[session['asset_id']],previous[session['npz_keys']['valid']],builder)
        prefix=session['identifier'];row['npz_keys']={k:prefix+'_'+k for k in arrays}
        payload.update({prefix+'_'+k:v for k,v in arrays.items()});rows.append(row)
    npz_path.parent.mkdir(parents=True,exist_ok=True)
    with npz_path.open('xb') as f:np.savez_compressed(f,**payload)
    result=dict(schema='hippocampal.odor-place-approach-windows.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_odor_place_approach_windows.py'),
        inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=h) for p,h in PINS.items()],
        parent_npz=parent['npz'],window='[first reward-well entry - 0.5s, first reward-well entry)',
        minimum_choice_latency_s=1.0,motion_columns=parent['motion_columns'],sessions=rows,
        summary=dict(sessions=len(rows),trials=sum(s['summary']['trials'] for s in rows),
                     approach_valid=sum(s['summary']['approach_valid'] for s in rows),
                     all_five_valid=sum(s['summary']['all_five_valid'] for s in rows)),
        npz=dict(path=npz_path.relative_to(ROOT).as_posix(),bytes=npz_path.stat().st_size,sha256=sha(npz_path)),
        interpretation='Pre-contact activity can contain location, trajectory, motion, intended action and reward expectation. '
                       'It is not a pure place-memory template or validated continuous unit observation. '
                       'Same-source-epoch transfer must be evaluated separately; no effect selection here.')
    with result_path.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
