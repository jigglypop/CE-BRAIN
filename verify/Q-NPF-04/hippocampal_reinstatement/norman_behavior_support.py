"""Audit fixed Norman2019 behavior/ripple joins; no neural-effect fit.

Raw labels are preserved. Parser multiplicity is not temporal order; a label
outside the current run is not automatically an erroneous recollection.
"""
import hashlib,json,platform
from collections import Counter,defaultdict
from pathlib import Path
import h5py,numpy as np,scipy
from scipy.io import loadmat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
METADATA=ROOT/'data/external/hippocampal_reinstatement/norman2019_metadata_v1'
SRC=METADATA/'selected_members'
OUTPUT=ROOT/'data/local/hippocampal-reinstatement/norman-behavior-support-v3'
OUTPUT.mkdir(parents=True,exist_ok=True)
RESULT=OUTPUT/'norman_behavior_ripple_join.json'
MANIFEST=OUTPUT/'manifest.json'
if RESULT.exists() or MANIFEST.exists():raise FileExistsError('Preserve existing canonical audit')
BEH=SRC/'Ripple_rate_and_psth_analyses/data/Recall_events_data'
PSTH=SRC/'Ripple_rate_and_psth_analyses/data/ripple_psth_data.mat'
PERIODS=SRC/'Ripple_detection/data/Recall_and_memory_search_periods.mat'
CODE=SRC/'Ripple_detection/ripples_rate_accross_conditions_and_IRI_distribution.m'
SUBJECTS=[f'SUB{i:02d}' for i in range(1,16)]+['SUB13b']
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def chars(h,ref):
 a=np.asarray(h[ref]);return ''.join(chr(int(x)) for x in a.ravel(order='F') if int(x))
def cellstr(h,path):
 ds=h[path];return [chars(h,r) for r in np.asarray(ds).ravel(order='F')]
def vec(h,path,dtype=None):
 a=np.asarray(h[path]).ravel(order='F');return a.astype(dtype) if dtype else a
def rows4(x):
 a=np.asarray(x,dtype=object)
 if a.size==0:return []
 if a.ndim==1 and a.size==4:a=a.reshape(1,4)
 if a.ndim!=2 or a.shape[1]!=4:raise ValueError(f'Unexpected RecallEvents shape {a.shape}')
 return [[str(r[0]),str(r[1]),float(r[2]),float(r[3])] for r in a]

member_manifest=METADATA/'selected_members_manifest.json'
if sha(member_manifest)!='107ad34d60025dc8188d5c2a9ae772c2608e9920778b47ea4d56b9c140053d27':
 raise ValueError('Changed source-member manifest')
expected_members={row['name']:row for row in json.loads(member_manifest.read_text(encoding='utf-8'))['members']}
required=[PSTH,PERIODS,CODE]
for sub in SUBJECTS:
 required.extend([BEH/sub/f'{sub}_RecallEvents.mat']+[BEH/sub/f'stimuli_list_run_{run}.mat' for run in (1,2)])
for path in required:
 expected=expected_members[path.relative_to(SRC).as_posix()]
 if path.stat().st_size!=expected['uncompressed_bytes'] or sha(path)!=expected['sha256']:
  raise ValueError('Changed pinned input: '+str(path))

events=[];stim_summary=[];expected_view_rows=[];behavior_files=[]
for sub in SUBJECTS:
 sd=BEH/sub
 evpath=sd/f'{sub}_RecallEvents.mat';behavior_files.append(evpath)
 ev=loadmat(evpath,simplify_cells=True)['RecallEvents']
 for run in (1,2):
  stimpath=sd/f'stimuli_list_run_{run}.mat';behavior_files.append(stimpath)
  stim=np.asarray(loadmat(stimpath,simplify_cells=True)[f'stimuli_list_run_{run}']).ravel().tolist()
  counts=Counter(map(str,stim));stimset=set(counts)
  stim_summary.append(dict(subject=sub,person='SUB13' if sub=='SUB13b' else sub,run=run,presentations=len(stim),unique_items=len(counts),repetition_counts=dict(Counter(counts.values())),category_counts=dict(Counter('Face' if str(x).startswith('Face') else 'Place' if str(x).startswith('Place') else 'unknown' for x in counts))))
  seen=Counter()
  for x in map(str,stim):
   seen[x]+=1;expected_view_rows.append((sub,run,x,seen[x]))
  seen=Counter()
  for category in ('faces','places'):
   for verbal,label,onset,offset in rows4(ev[f'run{run}'][category]):
    seen[label]+=1;prompt='prompt' in label.lower();matched=label in stimset
    labelcat='Face' if label.startswith('Face') else 'Place' if label.startswith('Place') else 'unknown'
    expected='Face' if category=='faces' else 'Place'
    mismatch=labelcat not in (expected,'unknown')
    events.append(dict(subject=sub,person='SUB13' if sub=='SUB13b' else sub,run=run,source_category=expected,verbal=verbal,label=label,onset_s=onset,offset_s=offset,duration_s=offset-onset,prompt=prompt,matched_stimulus=matched,duplicate_in_parser_order=seen[label]>1,cross_category=(not prompt and mismatch),prompt_table_label_mismatch=(prompt and mismatch),current_run_unmatched=(not matched and not prompt),within_0_150=0<=onset<=offset<=150))

data=loadmat(PSTH,simplify_cells=True)['DATA']
rr=data['recall_trials'];vv=data['viewing_trials']
subj=[str(x) for x in np.asarray(rr['subjid']).ravel()];lab=[str(x) for x in np.asarray(rr['label']).ravel()];run=np.asarray(rr['runid']).ravel().astype(int)
recall_rows=[(s,int(r),l) for s,r,l in zip(subj,run,lab)]
vsub=[str(x) for x in np.asarray(vv['subjid']).ravel()];vlab=[str(x) for x in np.asarray(vv['label']).ravel()];vrun=np.asarray(vv['runid']).ravel().astype(int);vrep=np.asarray(vv['repnum']).ravel().astype(int)
view_rows=[(s,int(r),l,int(q)) for s,r,l,q in zip(vsub,vrun,vlab,vrep)]
recalled_items=[str(x) for x in np.asarray(data['recalled_items']).ravel()];subject_list=[str(x) for x in np.asarray(data['subject_list']).ravel()]
recall_time=np.asarray(rr['time'],float).ravel();view_time=np.asarray(vv['time'],float).ravel()
psth_shapes={'viewing_raster':list(np.asarray(vv['raster']).shape),'recall_raster':list(np.asarray(rr['raster']).shape)}

event_key=Counter((e['subject'],e['run'],e['label']) for e in events)
nonprompt_key=Counter((e['subject'],e['run'],e['label']) for e in events if not e['prompt'])
matched_key=Counter((e['subject'],e['run'],e['label']) for e in events if e['matched_stimulus'] and not e['prompt'])
parser_first_matched_key=Counter((e['subject'],e['run'],e['label']) for e in events if e['matched_stimulus'] and not e['prompt'] and not e['duplicate_in_parser_order'])
psth_key=Counter(recall_rows)
def overlap(a,b):return sum((a&b).values())

period_checks=[]
with h5py.File(PERIODS,'r') as h:
 for sub in SUBJECTS:
  for runid in (1,2):
   g=h[f'/recall_search_times/{sub}/run{runid}']
   rec={cat:np.asarray(g[f'recall_{cat}']).ravel(order='F').astype(bool) for cat in ('F','P')}
   sea={cat:np.asarray(g[f'search_{cat}']).ravel(order='F').astype(bool) for cat in ('F','P')}
   row=dict(subject=sub,run=runid,lengths={k:len(v) for k,v in {**{'recall_F':rec['F'],'recall_P':rec['P']},**{'search_F':sea['F'],'search_P':sea['P']}}.items()},complement_F=bool(np.array_equal(sea['F'],~rec['F'])),complement_P=bool(np.array_equal(sea['P'],~rec['P'])),categories={})
   for cat,source in (('F','Face'),('P','Place')):
    mask=rec[cat];evs=[e for e in events if e['subject']==sub and e['run']==runid and e['source_category']==source]
    expected=np.zeros(75001,bool)
    for e in evs:
     if e['prompt']:continue
     lo=max(0,int(round((e['onset_s']-3.0)*500)));hi=min(75000,int(round(e['offset_s']*500)))
     expected[lo:hi+1]=True
    xor=np.flatnonzero(mask^expected)
    onset_inside=[bool(mask[min(75000,max(0,int(round(e['onset_s']*500))))]) for e in evs if not e['prompt'] and 0<=e['onset_s']<=150]
    row['categories'][cat]=dict(events=len(evs),nonprompt=sum(not e['prompt'] for e in evs),mask_true=int(mask.sum()),expected_true=int(expected.sum()),xor_samples=len(xor),first_xor_sample=int(xor[0]) if len(xor) else None,onsets_in_mask=sum(onset_inside),onsets_tested=len(onset_inside))
   period_checks.append(row)

inputs={str(p.relative_to(SRC)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in [PSTH,PERIODS,CODE]+behavior_files}
out=dict(schema='ce.norman2019.behavior-ripple-join-audit.v3',source_sha256=sha(__file__),inputs=inputs,environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,h5py=h5py.__version__),recordsets=dict(subject_list=subject_list,count=len(subject_list),persons=sorted(set('SUB13' if s=='SUB13b' else s for s in subject_list)),person_count=len(set('SUB13' if s=='SUB13b' else s for s in subject_list)),sub13_recordsets=[s for s in subject_list if s.startswith('SUB13')]),stimuli=dict(runs=stim_summary,total_presentations=sum(x['presentations'] for x in stim_summary),total_unique_subject_run_items=sum(x['unique_items'] for x in stim_summary),psth_exact_order=bool(view_rows==expected_view_rows),psth_multiset_equal=bool(Counter(view_rows)==Counter(expected_view_rows)),psth_repnum_counts=dict(sorted(Counter(x[3] for x in view_rows).items()))),behavior=dict(events=len(events),prompt=sum(e['prompt'] for e in events),nonprompt=sum(not e['prompt'] for e in events),matched_stimulus=sum(e['matched_stimulus'] and not e['prompt'] for e in events),duplicate_in_parser_order=sum(e['duplicate_in_parser_order'] and not e['prompt'] for e in events),cross_category_nonprompt=sum(e['cross_category'] for e in events),prompt_table_label_mismatch=sum(e['prompt_table_label_mismatch'] for e in events),current_run_unmatched=sum(e['current_run_unmatched'] for e in events),outside_0_150=sum(not e['within_0_150'] for e in events),units=dict(onset_offset='seconds from category-specific recall-period onset',stimulus_id='author string such as Face010/Place010; suffix B is part of ID'),events_rows=events),periods=dict(Fs=500,nominal_clock_s=[0,150],author_mask_rule='union of non-Prompt [onset_s - 3.0, offset_s], clipped to [0,150], round-to-500Hz samples, inclusive endpoints',expected_samples=75001,runs=period_checks,all_lengths_75001=all(all(v==75001 for v in x['lengths'].values()) for x in period_checks),all_search_exact_complement=all(x['complement_F'] and x['complement_P'] for x in period_checks),total_xor_samples=sum(y['xor_samples'] for x in period_checks for y in x['categories'].values()),all_nonprompt_onsets_in_mask=all(y['onsets_in_mask']==y['onsets_tested'] for x in period_checks for y in x['categories'].values()),nonprompt_onsets_tested=sum(y['onsets_tested'] for x in period_checks for y in x['categories'].values())),psth=dict(Fs=500,subject_list=subject_list,viewing_rows=len(view_rows),recall_rows=len(recall_rows),recalled_items_count=len(recalled_items),viewing_time=dict(n=len(view_time),min=float(view_time.min()),max=float(view_time.max()),step_median=float(np.median(np.diff(view_time)))),recall_time=dict(n=len(recall_time),min=float(recall_time.min()),max=float(recall_time.max()),step_median=float(np.median(np.diff(recall_time)))),shapes=psth_shapes,recall_join=dict(exactly_all_nonprompt_multiset=bool(psth_key==nonprompt_key),all_behavior_overlap=overlap(psth_key,event_key),nonprompt_overlap=overlap(psth_key,nonprompt_key),matched_overlap=overlap(psth_key,matched_key),parser_first_matched_overlap=overlap(psth_key,parser_first_matched_key),psth_not_in_behavior=list((psth_key-event_key).items())[:20],behavior_not_in_psth_counts=dict(all=sum((event_key-psth_key).values()),nonprompt=sum((nonprompt_key-psth_key).values()),matched=sum((matched_key-psth_key).values()),parser_first_matched=sum((parser_first_matched_key-psth_key).values()))),recall_rows_preview=[list(x) for x in recall_rows[:10]],recalled_items_preview=recalled_items[:10]),limits=['Metadata/join audit only; no ripple effect, decoder, fit, or hypothesis test.','Exact string IDs preserve B suffix and author spelling; unknown labels are not silently normalized.','Recall/search masks are retrospective because they begin 3 seconds before a future verbal-onset annotation; do not use them as an online predictor history.'])
by_category_key=Counter((e['subject'],e['run'],e['source_category'],e['label']) for e in events if not e['prompt'])
out['behavior']['duplicate_excess_subject_run_label']=sum(v-1 for v in nonprompt_key.values())
out['behavior']['duplicate_keys_subject_run_label']=sum(v>1 for v in nonprompt_key.values())
out['behavior']['duplicate_excess_including_source_category']=sum(v-1 for v in by_category_key.values())
out['behavior']['duplicate_keys_including_source_category']=sum(v>1 for v in by_category_key.values())
out['behavior']['flag_definitions']={
 'current_run_unmatched':'Exact author label absent from this recordset/run stimulus list; not an author error annotation.',
 'duplicate_in_parser_order':'Repeated label encountered in faces-then-places parsing; not chronological recall order.',
 'cross_category':'Non-Prompt author label prefix differs from the source recall block category.',
 'prompt_table_label_mismatch':'Prompt label prefix differs from the source recall block; separate from non-Prompt mismatch.'}
out['limits'].extend([
 'Duplicate counts are multiplicity excess, not independent recalled items or a proven temporal repeat sequence.',
 'Current-run unmatched labels may belong to another run or remain unresolved; they are not automatically recall errors.',
 'Recall PSTH join is a subject/run/label multiset match; repeated same-label rows are not assigned absolute event onsets by this join.',
 'SUB13 and SUB13b belong to one participant; observation recordsets are not independent people.'])
if not out['stimuli']['psth_exact_order'] or not out['psth']['recall_join']['exactly_all_nonprompt_multiset']:
 raise ValueError('Unexpected behavior/PSTH alignment')
if out['periods']['total_xor_samples'] or not out['periods']['all_lengths_75001'] or not out['periods']['all_search_exact_complement']:
 raise ValueError('Unexpected retrospective mask rule')
if any(not np.isfinite([e['onset_s'],e['offset_s']]).all() or e['offset_s']<e['onset_s'] for e in events):
 raise ValueError('Invalid event interval')
rp=RESULT;mp=MANIFEST
if rp.exists() or mp.exists():raise FileExistsError('Preserve existing focused audit')
encoded=json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)
with rp.open('x',encoding='utf-8') as stream:stream.write(encoded)
manifest=dict(helper=dict(path=str(Path(__file__)),bytes=Path(__file__).stat().st_size,sha256=sha(__file__)),result=dict(path=str(rp),bytes=rp.stat().st_size,sha256=sha(rp)),reproduce=f'& "C:/dev/ce/ce-agi-runtime-repro-fffd356/.codex/hooks/python.cmd" python "{Path(__file__)}"')
with mp.open('x',encoding='utf-8') as stream:stream.write(json.dumps(manifest,indent=2,allow_nan=False))
print(json.dumps(dict(recordsets=out['recordsets'],stimuli={k:v for k,v in out['stimuli'].items() if k!='runs'},behavior={k:v for k,v in out['behavior'].items() if k not in ('events_rows','units')},periods={k:v for k,v in out['periods'].items() if k!='runs'},psth={k:v for k,v in out['psth'].items() if k not in ('recall_rows_preview','recalled_items_preview')})))
print(json.dumps(manifest))
