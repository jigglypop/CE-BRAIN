import importlib.util
from pathlib import Path
import pytest

PATH=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_region_reference.py'
spec=importlib.util.spec_from_file_location('odor_place_region_reference',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def reference():
    return dict(asset_id='a',identifier='CS1_01',status='ok',reference_attr_present=True,reference_bool=True,
        dereference_succeeded=True,same_object_identity=True,same_object_address=True,dereferenced_name=None,
        dereferenced_object_address=123,expected_object_address=123)


def session():
    return dict(asset_id='a',identifier='CS1_01',rat='CS1',day=1,join_status='exact_label_join',
        unit_region_status='provisional_row_index_only',unit_regions=dict(counts=dict(CA1=2,PFC=3)),
        table_reference=dict(one_integer_per_unit=True,electrodes_index_present=False,min_row=0,max_row=3,electrode_rows=4),
        counts=dict(all_four_cells_positive=True,trials=10))


def test_anonymous_reference_to_same_object_is_accepted():
    assert m.verified_identity(reference())
    row=m.corrected_row(session(),reference(),set())
    assert row['eligible_for_cue_outcome_comparison'] and not row['neural_position_values_acquired']


@pytest.mark.parametrize('changed',[{'reference_bool':False},{'same_object_identity':False},
    {'expected_object_address':124}])
def test_name_cannot_rescue_null_or_wrong_object(changed):
    ref=reference();ref.update(dereferenced_name='/general/extracellular_ephys/electrodes',**changed)
    assert not m.verified_identity(ref)


def test_reference_correction_does_not_bypass_task_support_failure():
    s=session();s.update(join_status='unresolved',reason='Task bounds')
    row=m.corrected_row(s,reference(),{'a'})
    assert row['electrode_reference_verified'] and not row['eligible_for_cue_outcome_comparison']
    assert row['trial_join_reason']=='Task bounds'


def test_single_cue_error_coverage_still_required():
    s=session();s['counts']['all_four_cells_positive']=False
    assert m.corrected_row(s,reference(),set())['ca1_pfc_task_supported']
    assert not m.corrected_row(s,reference(),set())['eligible_for_cue_outcome_comparison']


def test_duplicate_or_mismatched_assets_are_rejected():
    with pytest.raises(ValueError,match='coverage'):m.revise([session()],[reference(),reference()],set())
    ref=reference();ref['identifier']='CS1_02'
    with pytest.raises(ValueError,match='identity'):m.revise([session()],[ref],set())
