import importlib.util
from pathlib import Path
import sys
import pytest

HERE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('odor_place_cohort_labels',HERE/'odor_place_cohort_labels.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    return dict(id=[0,1],start_time=[1.,2.],stop_time=[1.5,2.5],rewarded=[1,0]),dict(
        allTriggers=[1.,2.],leftTriggers=[1.],rightTriggers=[2.],correctTriggers=[1.],incorrectTriggers=[2.])


def candidate(label,epoch=2,kind='odorTriggers'):
    return dict(label=label,epoch=epoch,kind=kind)


def test_exact_session_match_preserves_empty_cue_outcome_cells():
    trials,label=fixture();sources,rows=m.exact_match(trials,[candidate(label)])
    counts=m.summarize(rows)
    assert sources[0]['epoch']==2 and counts['trials']==2
    assert counts['incorrect_left']==0 and not counts['all_four_cells_positive']


@pytest.mark.parametrize('copies',[0,2])
def test_missing_or_ambiguous_epoch_is_not_silently_selected(copies):
    trials,label=fixture()
    with pytest.raises(ValueError,match='epoch combination count'):m.exact_match(trials,[candidate(label)]*copies)


def test_epoch_support_requires_whole_trial_and_task_identity():
    trials,label=fixture();_,rows=m.exact_match(trials,[candidate(label)])
    bounds=dict(start_time=[0.],stop_time=[3.],epoch_type=['odorplace'])
    assert m.trial_support(rows,bounds)==[0,0]
    bounds['stop_time']=[2.2]
    with pytest.raises(ValueError,match='support'):m.trial_support(rows,bounds)


def test_reward_disagreement_remains_a_join_failure():
    trials,label=fixture();trials['rewarded']=[0,0]
    with pytest.raises(ValueError,match='disagree'):m.exact_match(trials,[candidate(label)])


def test_multiple_source_epochs_join_in_source_order():
    trials,label=fixture()
    pieces=[{k:[t for t in times if t==value] for k,times in label.items()} for value in (1.,2.)]
    sources,rows=m.exact_match(trials,[candidate(pieces[1],4),candidate(pieces[0],2)])
    assert [s['epoch'] for s in sources]==[2,4] and len(rows)==2
    with pytest.raises(ValueError,match='combination count'):
        m.exact_match(trials,[candidate(pieces[0],4),candidate(pieces[1],2)])
    with pytest.raises(ValueError,match='combination count'):
        m.exact_match(trials,[candidate(pieces[0],2),candidate(pieces[1],4,'airOdorTriggers')])


def test_concatenation_ambiguity_is_rejected():
    trials,label=fixture()
    pieces=[{k:[t for t in times if t==value] for k,times in label.items()} for value in (1.,2.)]
    with pytest.raises(ValueError,match='combination count is 2'):
        m.exact_match(trials,[candidate(label,1),candidate(pieces[0],2),candidate(pieces[1],4)])


def test_null_table_reference_does_not_become_verified_region():
    ref=dict(status='ok',electrodes_index_present=False,one_integer_per_unit=True,min_row=0,max_row=2,
        electrode_rows=3,target_expected=True,table_target='/general/extracellular_ephys/electrodes')
    assert m.region_reference_status(ref)=='verified_table_reference'
    ref.update(target_expected=False,table_target=None)
    assert m.region_reference_status(ref)=='provisional_row_index_only'
    ref['min_row']=-1
    assert m.region_reference_status(ref)=='unresolved'
