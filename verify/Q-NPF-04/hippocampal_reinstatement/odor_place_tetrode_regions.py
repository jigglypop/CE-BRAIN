"""Correct electrode-number semantics with independent source-region evidence.

This preserves the prior HDF object-identity result but supersedes its regional
interpretation. Converter intent is inferred, not established from converter code.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DIAG=ROOT/'data/external/hippocampal_reinstatement/odor_place_cell_tet_info_v1/electrode_mapping_diagnostic.json'
META=ROOT/'data/external/hippocampal_reinstatement/dandi001539_0.250815.1203_cohort_metadata_v1/all_assets_summary.json'
COHORT=HERE/'odor_place_cohort_labels_result.json'
INDEX=ROOT/'data/local/hippocampal-reinstatement/odor-place-input-index-v2/index.json'
AXIS=ROOT/'data/local/hippocampal-reinstatement/odor-place-cs41-source-axis-v1/cs41_day7_source_area_supplement.json'
PINS={DIAG:'f73bf2f954ec57d17408030c98092ffb04af977b0ed19b4a090a82aed06339d1',
      META:'9c98884de317bce80605e70d0bd1dddfb4ecd065dc081ce6e734168687badacc',
      COHORT:'304968b35ba65a7831ca3a4742e07500efa679834bfee362baa768e6c87b21e3',
      INDEX:'8580a2c9f73057de5c1b3c11292e804792bd8e98b9edb9ddc7db7d2defbd4272',
      AXIS:'c7b9616bc77b67e0e5822bbc8869a798711e40bf6f692def73f7607c74531823'}


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def map_tetrodes(raw_values, group_names, locations):
    if len(group_names)!=len(locations):raise ValueError('Electrode columns differ')
    groups={}
    for name,area in zip(group_names,locations):
        match=re.fullmatch(r'tetrode([1-9][0-9]*)',name)
        if not match:raise ValueError('Unexpected tetrode group name')
        groups.setdefault(int(match.group(1)),set()).add(area)
    labels=[]
    for value in raw_values:
        if not isinstance(value,int) or isinstance(value,bool) or value<=0:raise ValueError('Not a positive tetrode number')
        areas=groups.get(value,set())
        if len(areas)!=1:raise ValueError('Absent or conflicting tetrode areas')
        labels.append(next(iter(areas)))
    return labels


def source_verified(tetrode, region, expected_epochs):
    evidence=tetrode['original_source_evidence']
    if not expected_epochs or len(evidence)!=len(expected_epochs) or {r['source_epoch'] for r in evidence}!=set(expected_epochs):
        return False
    for row in evidence:
        for key in ('cellinfo','tetinfo'):
            data=row.get(key)
            if not data or set(data['areas'])!={region} or any(v<=0 for v in data['areas'].values()):return False
    return True


def restored_single_epoch_evidence(supplement,tetrode):
    data=supplement['cs41_07']
    sources={}
    for key in ('cellinfo','tetinfo'):
        row=data[key+'_day7_epoch1']
        if row['tetrode_count']!=32:raise ValueError('Unexpected restored tetrode axis')
        matches=[r for r in row['tetrodes'] if r['tetrode']==tetrode]
        if len(matches)!=1:raise ValueError('Tetrode source identity ambiguous')
        sources[key]=matches[0]
    return dict(original_source_evidence=[dict(source_epoch=1,**sources)])


def main():
    output=HERE/'odor_place_tetrode_regions_result.json'
    if output.exists():raise FileExistsError('Preserve regional correction')
    for path,digest in PINS.items():
        if sha(path)!=digest:raise ValueError('Frozen input changed: '+str(path))
    diagnostics={s['asset_id']:s for s in json.loads(DIAG.read_text(encoding='utf-8'))['sessions']}
    metadata=json.loads(META.read_text(encoding='utf-8'))['results']
    cohort={s['asset_id']:s for s in json.loads(COHORT.read_text(encoding='utf-8'))['sessions']}
    acquired={s['asset_id'] for s in json.loads(INDEX.read_text(encoding='utf-8'))['sessions']}
    axis=json.loads(AXIS.read_text(encoding='utf-8'))
    for item in axis['inputs'].values():
        if sha(item['path'])!=item['sha256']:raise ValueError('Axis supplement original input changed')
    rows=[]
    for item in metadata:
        aid=item['asset_id'];a=item['audit'];s=cohort[aid];d=diagnostics[aid]
        units=a['units']['values'];table=a['electrodes']['values']
        if units['id']!=d['unit_ids'] or units['electrodes']!=d['raw_unit_electrodes']:raise ValueError('Diagnostic unit identity differs')
        labels=map_tetrodes(units['electrodes'],table['group_name'],table['location'])
        if labels!=[u['mapped_location'] for u in d['units']]:raise ValueError('Independent mapping differs')
        epochs=[source['epoch'] for source in s.get('sources',[])]
        if s['identifier']=='CS41_07':
            if epochs!=[1] or units['electrodes']!=axis['cs41_07']['raw_unit_electrodes']:raise ValueError('Single-epoch correction identity differs')
            evidence=[restored_single_epoch_evidence(axis,t) for t in units['electrodes']]
        else:evidence=[d['tetrodes'][str(t)] for t in units['electrodes']]
        verified=[source_verified(e,region,epochs) for e,region in zip(evidence,labels)]
        supported=s['join_status']=='exact_label_join'
        if supported and not all(verified):raise ValueError('Original source area evidence incomplete')
        counts=dict(Counter(labels));both=counts.get('CA1',0)>0 and counts.get('PFC',0)>0
        eligible=bool(supported and all(verified) and both and s['counts']['all_four_cells_positive'])
        rows.append(dict(asset_id=aid,identifier=s['identifier'],rat=s['rat'],day=s['day'],unit_ids=units['id'],
                         raw_unit_electrodes=units['electrodes'],regions=labels,region_counts=counts,
                         source_area_verified=verified,trial_join_status=s['join_status'],
                         eligible=eligible,acquired=aid in acquired,
                         prior_eligible=d['prior_eligible'],legacy_row_disagreements=d['zero_based_row_location_disagreements']))
    previous={r['asset_id'] for r in rows if r['prior_eligible']};current={r['asset_id'] for r in rows if r['eligible']}
    if not acquired<=current or not previous<=current:raise ValueError('Unexpected acquired/eligible loss')
    summary=dict(assets=len(rows),units=sum(len(r['unit_ids']) for r in rows),
                 source_verified_units=sum(sum(r['source_area_verified']) for r in rows),
                 legacy_row_disagreements=sum(r['legacy_row_disagreements'] for r in rows),
                 mapped_regions=dict(sum((Counter(r['region_counts']) for r in rows),Counter())),
                 task_supported_sessions=sum(r['trial_join_status']=='exact_label_join' for r in rows),
                 prior_eligible=len(previous),eligible=len(current),acquired=len(acquired),
                 acquired_regions=dict(sum((Counter(r['region_counts']) for r in rows if r['acquired']),Counter())),
                 pending_identifiers=[r['identifier'] for r in rows if r['asset_id'] in current-acquired])
    out=dict(schema='hippocampal.odor-place-tetrode-regions.v1',source_sha256=sha(__file__),
             test_sha256=sha(ROOT/'tests/test_odor_place_tetrode_regions.py'),
             inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=h) for p,h in PINS.items()],
             sessions=rows,summary=summary,
             interpretation='Raw unit electrode integers match 1-based tetrode numbers, not zero-based table rows. '
               'Original cellinfo and tetinfo areas agree for every unit in all35 exact-task sessions. '
               'This is a source-supported regional reconstruction; converter implementation is not pinned. '
               'Unit-specific continuous observation and cross-epoch neuron tracking are not established by area agreement. '
               'Old HDF identity verification remains valid, but prior regional counts and eligibility are superseded.')
    with output.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2,ensure_ascii=False,allow_nan=False)
    print(json.dumps(summary))


if __name__=='__main__':main()
