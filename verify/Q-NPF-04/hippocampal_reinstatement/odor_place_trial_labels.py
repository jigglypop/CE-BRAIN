"""Offline exact-time label join; no neural features, training or decoding."""
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.io import loadmat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DATA=ROOT/'data/external/hippocampal_reinstatement'
AUDIT=DATA/'dandi001539_0.250815.1203_header_v1/nwb_metadata_audit.json'
LABELS=DATA/'figshare19620783_v3_labels_v1/label_24_CS39odorTriggers06.mat'
AUDIT_SHA='1acac83c2a22bfdaeaa6f4f6ae6976fa28a9924555f69828e2b1859eefa1e451'
LABEL_SHA='9e81070725e4eccee5ce37c4b7ff75237cdbeb48e216e367ae696c8564cf1e7c'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def partition(all_times, first, second):
    a,b=[np.asarray(x,float).reshape(-1) for x in (first,second)]
    if any(not np.isfinite(x).all() or len(np.unique(x))!=len(x) for x in (a,b)):
        raise ValueError('Nonfinite or duplicate partition time')
    if set(a)&set(b) or set(a)|set(b)!=set(all_times):
        raise ValueError('Labels do not partition all trials')
    return set(a),set(b)


def join(trials, label):
    fields=('id','start_time','stop_time','rewarded')
    vectors={k:np.asarray(trials[k]) for k in fields}
    n=len(vectors['id'])
    if not n or any(v.ndim!=1 or len(v)!=n for v in vectors.values()):
        raise ValueError('Trial columns differ in length')
    if len(np.unique(vectors['id']))!=n:
        raise ValueError('Duplicate trial identity')
    start,stop,reward=[vectors[k].astype(float) for k in fields[1:]]
    if not np.isfinite(np.r_[start,stop,reward]).all() or np.any(stop<=start) or np.any(np.diff(start)<=0):
        raise ValueError('Invalid or duplicate trial times')
    all_times=np.asarray(label['allTriggers'],float).reshape(-1)
    if not np.array_equal(start,all_times):
        raise ValueError('Exact ordered source/NWB time match required')
    if not set(reward)<= {0.,1.}:
        raise ValueError('Reward flag is not binary')
    left,right=partition(all_times,label['leftTriggers'],label['rightTriggers'])
    correct,incorrect=partition(all_times,label['correctTriggers'],label['incorrectTriggers'])
    if any(bool(r)!=bool(t in correct) for r,t in zip(reward,start)):
        raise ValueError('NWB reward and source correctness disagree')
    return [dict(trial_id=int(i),start_s=float(t),stop_s=float(end),odor_side='left' if t in left else 'right',
                 correct=bool(t in correct),rewarded=bool(r)) for i,t,end,r in zip(vectors['id'],start,stop,reward)]


def main():
    output=HERE/'odor_place_trial_labels_result.json'
    if output.exists():raise FileExistsError('Preserve existing result')
    if sha(AUDIT)!=AUDIT_SHA or sha(LABELS)!=LABEL_SHA:
        raise ValueError('Frozen input changed')
    audit=json.loads(AUDIT.read_text(encoding='utf-8'))
    if audit['/identifier']!='CS39_06':raise ValueError('Session identity mismatch')
    trials=audit['interval_tables']['trials']['values']
    day=np.asarray(loadmat(LABELS,squeeze_me=True,struct_as_record=False)['odorTriggers'],dtype=object).reshape(-1)[5]
    matches=[]
    for index,epoch in enumerate(np.asarray(day,dtype=object).reshape(-1),start=1):
        if hasattr(epoch,'allTriggers') and np.array_equal(np.asarray(epoch.allTriggers).reshape(-1),trials['start_time']):
            matches.append((index,{k:np.asarray(getattr(epoch,k)).reshape(-1) for k in epoch._fieldnames}))
    if len(matches)!=1:raise ValueError('Source epoch match missing or ambiguous')
    epoch_index,label=matches[0]
    rows=join(trials,label)
    bounds=audit['interval_tables']['epoch intervals']['values']
    if bounds['epoch_type']!=['odorplace'] or len(bounds['start_time'])!=1:
        raise ValueError('Unexpected task epoch')
    if not all(bounds['start_time'][0]<=r['start_s']<r['stop_s']<=bounds['stop_time'][0] for r in rows):
        raise ValueError('Trial outside task epoch')
    units=audit['units']; electrode=audit['electrodes']['values']
    if 'electrodes_index' in units['schema']['children']:
        raise ValueError('This exact asset requires one electrode reference per unit')
    unit_ids=units['values']['id']; indices=units['values']['electrodes']
    if len(unit_ids)!=len(indices) or len(set(unit_ids))!=len(unit_ids):
        raise ValueError('Unit/electrode reference mismatch')
    unit_rows=[]
    for uid,index in zip(unit_ids,indices):
        if not isinstance(index,int) or not 0<=index<len(electrode['id']):raise ValueError('Invalid electrode row index')
        unit_rows.append(dict(unit_id=uid,electrode_row=index,electrode_id=electrode['id'][index],region=electrode['location'][index]))
    result=dict(schema='hippocampal.odor-place-trial-labels.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_odor_place_trial_labels.py'),
        inputs=dict(nwb_audit=dict(path=AUDIT.relative_to(ROOT).as_posix(),sha256=AUDIT_SHA),
                    labels=dict(path=LABELS.relative_to(ROOT).as_posix(),sha256=LABEL_SHA)),
        dandiset='001539',version='0.250815.1203',asset_id='dd3aaf58-c574-4d84-b918-f060f3663878',
        nwb_identifier='CS39_06',source_matlab_day=6,source_matlab_epoch=epoch_index,
        exact_time_match=True,trials=rows,units=unit_rows,
        counts=dict(trials=len(rows),left=sum(r['odor_side']=='left' for r in rows),right=sum(r['odor_side']=='right' for r in rows),
            correct=sum(r['correct'] for r in rows),incorrect=sum(not r['correct'] for r in rows),
            units_by_region={region:sum(u['region']==region for u in unit_rows) for region in sorted({u['region'] for u in unit_rows})}),
        python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        interpretation='Labels joined by exact ordered time and disjoint exhaustive odor/outcome partitions. '
        'Reward correctness agreement established for this source epoch only. Odor side is coupled to learned goal side; '
        'cue decoding alone cannot identify retrieval or hippocampal indexing. Neural spike values/choices were not inferred or fitted.')
    serialized=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    with output.open('x',encoding='utf-8') as stream:stream.write(serialized)
    print(json.dumps(dict(counts=result['counts'],epoch=epoch_index,output=str(output))))


if __name__=='__main__':main()
