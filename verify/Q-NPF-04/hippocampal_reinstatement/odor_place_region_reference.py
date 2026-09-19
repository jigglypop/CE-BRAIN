"""Correct name-based region qualification using actual HDF object identity.

Retain the frozen cohort's trial-support failures and previous decisions.
This adds no neural-effect selection and does not overwrite prior evidence.
"""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
COHORT=HERE/'odor_place_cohort_labels_result.json'
REFERENCE=ROOT/'data/local/hippocampal-reinstatement/odor-place-electrode-reference-identity-v1/electrode_reference_identity_result.json'
POSTCHECK=ROOT/'data/local/hippocampal-reinstatement/odor-place-neural-position-postcheck-v1/offline_value_diagnostics.json'
PINS={COHORT:'304968b35ba65a7831ca3a4742e07500efa679834bfee362baa768e6c87b21e3',
    REFERENCE:'4e3e1efe1049d696ee298f6ab69aaaab58d3118428f72a6fba9b521dcdaf6d44',
    POSTCHECK:'e32682238b2c3a32674bd99b4eecc053e3edfa530288875f949be88f10eb3919'}


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def verified_identity(ref):
    return (ref.get('status')=='ok' and ref.get('reference_attr_present') is True
        and ref.get('reference_bool') is True and ref.get('dereference_succeeded') is True
        and ref.get('same_object_identity') is True and ref.get('same_object_address') is True
        and ref.get('dereferenced_object_address') is not None
        and ref.get('dereferenced_object_address')==ref.get('expected_object_address'))


def corrected_row(session,reference,acquired):
    if session['asset_id']!=reference['asset_id'] or session['identifier']!=reference['identifier']:
        raise ValueError('Reference/session identity differs')
    identity=verified_identity(reference)
    supported=session['join_status']=='exact_label_join'
    region=session.get('unit_regions',{}).get('counts',{})
    rows=session.get('table_reference',{})
    row_contract=(rows.get('one_integer_per_unit') is True and rows.get('electrodes_index_present') is False
        and rows.get('min_row',-1)>=0 and rows.get('max_row',0)<rows.get('electrode_rows',0))
    both=bool(identity and row_contract and supported and region.get('CA1',0)>0 and region.get('PFC',0)>0)
    eligible=both and session['counts']['all_four_cells_positive']
    return dict(asset_id=session['asset_id'],identifier=session['identifier'],rat=session['rat'],day=session['day'],
        previous_unit_region_status=session.get('unit_region_status'),
        electrode_reference_verified=identity,electrode_row_contract=bool(row_contract),
        reference_name=reference.get('dereferenced_name'),trial_join_status=session['join_status'],
        trial_join_reason=session.get('reason'),unit_region_counts=region,trial_counts=session.get('counts'),
        ca1_pfc_task_supported=both,eligible_for_cue_outcome_comparison=bool(eligible),
        neural_position_values_acquired=session['asset_id'] in acquired)


def revise(cohort,references,acquired):
    lookup={r['asset_id']:r for r in references}
    if len(lookup)!=len(references) or set(lookup)!={s['asset_id'] for s in cohort}:
        raise ValueError('Reference asset coverage differs or duplicates')
    return [corrected_row(s,lookup[s['asset_id']],acquired) for s in cohort]


def main():
    output=HERE/'odor_place_region_reference_result.json'
    if output.exists():raise FileExistsError('Preserve corrected reference result')
    for path,digest in PINS.items():
        if sha(path)!=digest:raise ValueError('Frozen input changed: '+str(path))
    cohort=json.loads(COHORT.read_text(encoding='utf-8'))['sessions']
    refs=json.loads(REFERENCE.read_text(encoding='utf-8'))['rows']
    post=json.loads(POSTCHECK.read_text(encoding='utf-8'))['sessions']
    acquired={r['asset_id'] for r in post if r['status']=='ok'}
    rows=revise(cohort,refs,acquired)
    old={s['asset_id'] for s in cohort if s.get('unit_region_status')=='verified_table_reference'
        and s['join_status']=='exact_label_join' and s['unit_regions']['counts'].get('CA1',0)>0
        and s['unit_regions']['counts'].get('PFC',0)>0 and s['counts']['all_four_cells_positive']}
    new={s['asset_id'] for s in rows if s['eligible_for_cue_outcome_comparison']}
    if not old<=new or not acquired<=new:raise ValueError('Unexpected loss or acquired cohort disagreement')
    summary=dict(assets=len(rows),electrode_identity_verified=sum(r['electrode_reference_verified'] for r in rows),
        exact_trial_supported=sum(r['trial_join_status']=='exact_label_join' for r in rows),
        ca1_pfc_task_supported=sum(r['ca1_pfc_task_supported'] for r in rows),
        prior_eligible=len(old),corrected_eligible=len(new),acquired=len(acquired),
        added_identifiers=[r['identifier'] for r in rows if r['asset_id'] in new-old],
        pending_values_identifiers=[r['identifier'] for r in rows if r['asset_id'] in new-acquired])
    out=dict(schema='hippocampal.odor-place-region-reference.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_odor_place_region_reference.py'),
        inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=h) for p,h in PINS.items()],sessions=rows,summary=summary,
        correction='h5py dereferenced .name=None was incorrectly treated as null/unresolved in prior reports. '
            'Present non-null references to the same HDF object and address are verified regardless of name. '
            'Frozen trial support and four-cell criteria remain unchanged. No neural-effect selection or decoding. '
            'The previously acquired23 remain valid; nine newly eligible assets still require value acquisition.')
    with output.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2,allow_nan=False)
    print(json.dumps(summary))


if __name__=='__main__':main()
