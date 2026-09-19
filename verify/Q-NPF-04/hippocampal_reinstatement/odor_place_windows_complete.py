"""Extend the frozen historical32 windows with source-qualified CS39_05.

Existing arrays are reused byte-for-value; extraction rules are unchanged.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=HERE/'odor_place_windows_result.json'
INDEX=ROOT/'data/local/hippocampal-reinstatement/odor-place-input-index-v2/index.json'
REGIONS=HERE/'odor_place_tetrode_regions_result.json'
BUILDER=HERE/'odor_place_windows.py'
PINS={OLD:'1c1ac104d1fcc6788e5c87f1859c06eb3fc7a2cb2f8135e2c6956f85790c6dfb',
      INDEX:'8580a2c9f73057de5c1b3c11292e804792bd8e98b9edb9ddc7db7d2defbd4272',
      REGIONS:'30c74fb53563a56a190469a62143f4c5ce0bef427307b7bc14c275820e4b7891',
      BUILDER:'1379b05aa9cef13118241befe1791f5ae089ceb55cb5b412b025634451aadf1d'}


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def extension_ids(old_rows,input_rows,region_rows):
    old={r['asset_id'] for r in old_rows};inputs={r['asset_id'] for r in input_rows}
    eligible={r['asset_id'] for r in region_rows if r['eligible']}
    if len(old)!=len(old_rows) or len(inputs)!=len(input_rows):raise ValueError('Duplicate input identity')
    if not old<=inputs or inputs!=eligible:raise ValueError('Incomplete or different corrected cohort')
    return inputs-old


def main():
    result_path=HERE/'odor_place_windows_complete_result.json'
    npz_path=ROOT/'data/local/hippocampal-reinstatement/odor-place-windows-complete-v1/windows.npz'
    if result_path.exists() or npz_path.exists():raise FileExistsError('Preserve complete windows')
    for path,digest in PINS.items():
        if sha(path)!=digest:raise ValueError('Pinned parent changed')
    spec=importlib.util.spec_from_file_location('odor_place_windows',BUILDER)
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    for path,digest in builder.PINS.items():
        if sha(path)!=digest:raise ValueError('Builder input changed')
    old=json.loads(OLD.read_text(encoding='utf-8'));index=json.loads(INDEX.read_text(encoding='utf-8'))
    regions=json.loads(REGIONS.read_text(encoding='utf-8'))
    added=extension_ids(old['sessions'],index['sessions'],regions['sessions'])
    if len(added)!=1:raise ValueError('Expected one newly source-qualified session')
    cohort=json.loads((HERE/'odor_place_cohort_labels_result.json').read_text(encoding='utf-8'))['sessions']
    metadata=json.loads((builder.DATA/'dandi001539_0.250815.1203_cohort_metadata_v1/all_assets_summary.json').read_text(encoding='utf-8'))['results']
    audits={s['asset_id']:s['audit'] for s in metadata};inputs={s['asset_id']:s for s in index['sessions']}
    old_path=ROOT/old['npz']['path']
    if sha(old_path)!=old['npz']['sha256']:raise ValueError('Old arrays changed')
    with np.load(old_path,allow_pickle=False) as data:arrays={k:data[k] for k in data.files}
    rows={s['asset_id']:s for s in old['sessions']}
    for s in cohort:
        if s['asset_id'] not in added:continue
        row,values=builder.build_session(s,audits[s['asset_id']],inputs[s['asset_id']])
        row['npz_keys']={k:s['identifier']+'_'+k for k in values}
        for key,value in values.items():
            if row['npz_keys'][key] in arrays:raise ValueError('Duplicate NPZ identity')
            arrays[row['npz_keys'][key]]=value
        rows[s['asset_id']]=row
    sessions=[rows[s['asset_id']] for s in cohort if s['asset_id'] in rows]
    for s in sessions:s['region_mapping_status']='Use linked source-supported tetrode region reconstruction; raw unit values are not table row indices.'
    npz_path.parent.mkdir(parents=True,exist_ok=True)
    with npz_path.open('xb') as f:np.savez_compressed(f,**arrays)
    summary=dict(sessions=len(sessions),rats=sorted({s['rat'] for s in sessions}),units=sum(s['units'] for s in sessions),
                 trials=sum(s['summary']['trials'] for s in sessions),choices_resolved=sum(s['summary']['choices_resolved'] for s in sessions),
                 choices_unresolved=sum(s['summary']['choices_unresolved'] for s in sessions),
                 valid_by_window={k:sum(s['summary']['valid_by_window'][k] for s in sessions) for k in builder.WINDOWS},
                 all_windows_valid=sum(s['summary']['all_windows_valid'] for s in sessions))
    out=dict(schema='hippocampal.odor-place-windows-complete.v1',source_sha256=sha(__file__),
             test_sha256=sha(ROOT/'tests/test_odor_place_windows_complete.py'),
             inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=h) for p,h in PINS.items()],
             source_regions=dict(path=REGIONS.relative_to(ROOT).as_posix(),sha256=PINS[REGIONS]),
             windows=old['windows'],window_duration_s=old['window_duration_s'],motion_columns=old['motion_columns'],
             npz=dict(path=npz_path.relative_to(ROOT).as_posix(),bytes=npz_path.stat().st_size,sha256=sha(npz_path)),
             sessions=sessions,summary=summary,cohort_scope='All33 exact-task/four-cell sessions with original-source-supported CA1/PFC tetrode labels; no neural-effect selection.',
             limitations=old['limitations'],extension='Reuse historical32 arrays unchanged and extract CS39_05 with the frozen identical builder. Biological detection completeness is still unknown.')
    with result_path.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2,ensure_ascii=False,allow_nan=False)
    print(json.dumps(summary))


if __name__=='__main__':main()
