"""Offline cohort trial-label joins; no spike, position or LFP values are fitted."""
import hashlib
import itertools
import json
from pathlib import Path
import re

import numpy as np
from scipy.io import loadmat

from odor_place_trial_labels import join

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DATA=ROOT/'data/external/hippocampal_reinstatement'
METADATA=DATA/'dandi001539_0.250815.1203_cohort_metadata_v1'
LABELS=DATA/'figshare19620783_v3_labels_v1'
SUMMARY_SHA='9c98884de317bce80605e70d0bd1dddfb4ecd065dc081ce6e734168687badacc'
LABEL_MANIFEST_SHA='adafd2c31272722d52b6acbc396e10e82d23ace5dcf8a00a7b832a19accb58f8'
REFERENCE_SHA='2479493841cccd87b1165bc68117ff53ac88412fb2ad9589218065025a33962c'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def epochs(day):
    for index,entry in enumerate(np.asarray(day,dtype=object).reshape(-1),1):
        while isinstance(entry,np.ndarray) and entry.dtype==object and entry.size==1:
            entry=entry.reshape(-1)[0]
        if hasattr(entry,'allTriggers'):
            yield index,{k:np.asarray(getattr(entry,k)).reshape(-1) for k in entry._fieldnames}


def label_inventory():
    result=[]
    manifest_path=LABELS/'manifest.json'
    if sha(manifest_path)!=LABEL_MANIFEST_SHA:raise ValueError('Frozen label manifest changed')
    inputs=json.loads(manifest_path.read_text(encoding='utf-8'))['files']['Figure1-6.zip']['extracted_relevant']
    if len(inputs)!=53:raise ValueError('Expected all 53 source label files')
    for record in sorted(inputs,key=lambda r:r['path']):
        path=LABELS/record['path']
        if path.stat().st_size!=record['bytes'] or sha(path)!=record['sha256']:
            raise ValueError('Frozen source label changed')
        match=re.search(r'(CS\d+)(airOdorTriggers|odorTriggers)(\d+)\.mat$',path.name)
        if not match:raise ValueError('Unexpected source label filename')
        rat,kind,day=match.group(1),match.group(2),int(match.group(3))
        cells=np.asarray(loadmat(path,squeeze_me=False,struct_as_record=False)['odorTriggers'],dtype=object)
        if cells.ndim!=2 or cells.shape[0]!=1 or not 1<=day<=cells.shape[1]:raise ValueError('Invalid MATLAB day index')
        for index,label in epochs(cells[0,day-1]):
            result.append(dict(rat=rat,day=day,kind=kind,epoch=index,file=path.name,sha256=sha(path),label=label))
    return result


def exact_match(trials,candidates):
    starts=np.asarray(trials['start_time'])
    matches=[]
    # A converted NWB can concatenate several original task epochs. Preserve
    # their source order, never sort/reorder trial times to force a match.
    groups={}
    for row in candidates:
        if len(row['label']['allTriggers']):groups.setdefault(row['kind'],[]).append(row)
    keys=('allTriggers','leftTriggers','rightTriggers','correctTriggers','incorrectTriggers')
    for group in groups.values():
        ordered=sorted(group,key=lambda r:r['epoch'])
        for length in range(1,len(ordered)+1):
            for sources in itertools.combinations(ordered,length):
                combined={k:np.concatenate([np.asarray(r['label'][k]).reshape(-1) for r in sources]) for k in keys}
                if np.array_equal(starts,combined['allTriggers']):matches.append((sources,combined))
    if len(matches)!=1:raise ValueError(f'Exact source epoch combination count is {len(matches)}')
    sources,label=matches[0]
    return sources,join(trials,label)


def region_reference_status(reference):
    valid_rows=(reference.get('status')=='ok' and not reference.get('electrodes_index_present',True)
        and reference.get('one_integer_per_unit',False) and reference.get('min_row',-1)>=0
        and reference.get('max_row',0)<reference.get('electrode_rows',0))
    if not valid_rows:return 'unresolved'
    if reference.get('target_expected') and reference.get('table_target')=='/general/extracellular_ephys/electrodes':
        return 'verified_table_reference'
    return 'provisional_row_index_only'


def trial_support(rows,epoch_values):
    starts,stops,kinds=[epoch_values[k] for k in ('start_time','stop_time','epoch_type')]
    if not len(starts) or len(starts)!=len(stops) or len(starts)!=len(kinds):raise ValueError('Invalid task epoch table')
    supports=[]
    for row in rows:
        included=[i for i,(a,b,k) in enumerate(zip(starts,stops,kinds)) if a<=row['start_s']<row['stop_s']<=b and k=='odorplace']
        if len(included)!=1:raise ValueError('Trial task-epoch support missing or ambiguous')
        supports.append(included[0])
    return supports


def summarize(rows):
    counts={key:0 for key in ('correct_left','incorrect_left','correct_right','incorrect_right')}
    for r in rows:counts[('correct' if r['correct'] else 'incorrect')+'_'+r['odor_side']]+=1
    return dict(trials=len(rows),**counts,all_four_cells_positive=all(counts.values()))


def main():
    output=HERE/'odor_place_cohort_labels_result.json'
    if output.exists():raise FileExistsError('Preserve cohort result')
    summary_path=METADATA/'all_assets_summary.json'
    if sha(summary_path)!=SUMMARY_SHA:raise ValueError('Frozen cohort metadata changed')
    if sha(HERE/'odor_place_trial_labels.py')!='0f7ad1f7ff823ebef5fb571322f25450ad85303db2c5560b13b772a90d95a080':
        raise ValueError('Frozen join dependency changed')
    metadata=json.loads(summary_path.read_text(encoding='utf-8'))
    reference_path=METADATA/'offline_reference_behavior_check.json'
    if sha(reference_path)!=REFERENCE_SHA:raise ValueError('Frozen table-reference supplement changed')
    reference_rows=json.loads(reference_path.read_text(encoding='utf-8'))['reference_checks']
    references={r['asset_id']:r for r in reference_rows}
    if len(references)!=len(reference_rows) or set(references)!={x['asset_id'] for x in metadata['results']}:
        raise ValueError('Reference supplement asset identities differ')
    labels=label_inventory();sessions=[]
    for item in metadata['results']:
        result={k:item[k] for k in ('asset_id','path','rat','day','status')}
        if item['status']!='ok':
            result.update(join_status='metadata_unavailable',reason=item.get('error'));sessions.append(result);continue
        audit=item['audit'];result['identifier']=audit['/identifier']
        expected=f"{item['rat']}_{item['day']:02d}"
        if result['identifier']!=expected:raise ValueError('Session identifier disagreement')
        candidates=[r for r in labels if r['rat']==item['rat'] and r['day']==item['day']]
        try:
            sources,rows=exact_match(audit['interval_tables']['trials']['values'],candidates)
            support=trial_support(rows,audit['interval_tables']['epoch intervals']['values'])
            if any(source['kind']!='odorTriggers' for source in sources):raise ValueError('Matched air-control label, not normal odor task')
            reference=references[item['asset_id']]
            if reference['identifier']!=expected:raise ValueError('Reference supplement session identity differs')
            result.update(join_status='exact_label_join',sources=[{k:source[k] for k in ('file','sha256','kind','epoch')} for source in sources],
                trials=rows,task_epoch_rows=support,counts=summarize(rows),
                unit_regions=audit['unit_regions'],unit_region_status=region_reference_status(reference),
                table_reference=reference,
                unit_region_note='Null table references retain provisional row-index location counts; they are not verified region joins.')
        except (ValueError,KeyError,TypeError) as error:
            result.update(join_status='unresolved',reason=str(error))
        sessions.append(result)
    valid=[s for s in sessions if s['join_status']=='exact_label_join']
    result=dict(schema='hippocampal.odor-place-cohort-labels.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_odor_place_cohort_labels.py'),summary_sha256=SUMMARY_SHA,
        label_manifest_sha256=LABEL_MANIFEST_SHA,reference_supplement_sha256=REFERENCE_SHA,
        join_dependency_sha256=sha(HERE/'odor_place_trial_labels.py'),sessions=sessions,
        summary=dict(assets=len(sessions),exact_label_joins=len(valid),unresolved=len(sessions)-len(valid),
            rats=sorted({s['rat'] for s in valid}),trials=sum(s['counts']['trials'] for s in valid),
            sessions_with_all_four_cells=sum(s['counts']['all_four_cells_positive'] for s in valid),
            sessions_with_verified_region_table=sum(s['unit_region_status']=='verified_table_reference' for s in valid),
            sessions_with_provisional_region_table=sum(s['unit_region_status']=='provisional_row_index_only' for s in valid)),
        interpretation='All immutable DANDI assets considered without neural-effect selection. '
        'Odor/outcome labels joined by unique exact ordered trial times, exhaustive partitions and reward agreement. '
        'Completed-trial cohort only; cue and learned target are coupled. Trial labels and units are not retrieval evidence. '
        'No spike/LFP/position values, neural decoding or cross-session unit identity assumed.')
    serialized=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    with output.open('x',encoding='utf-8') as stream:stream.write(serialized)
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
