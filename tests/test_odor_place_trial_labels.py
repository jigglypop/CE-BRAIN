import importlib.util
from pathlib import Path
import pytest

path=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_trial_labels.py'
spec=importlib.util.spec_from_file_location('odor_place_trial_labels',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    return dict(id=[10,11],start_time=[1.,2.],stop_time=[1.4,2.4],rewarded=[1.,0.]),dict(
        allTriggers=[1.,2.],leftTriggers=[1.],rightTriggers=[2.],correctTriggers=[1.],incorrectTriggers=[2.])


def test_join_retains_wrong_choice_trial_and_labels_source_not_reward_only():
    rows=m.join(*fixture())
    assert rows[1]==dict(trial_id=11,start_s=2.,stop_s=2.4,odor_side='right',correct=False,rewarded=False)


@pytest.mark.parametrize('problem',['time','duplicate','overlap','missing','reward'])
def test_wrong_session_or_nonpartitioned_labels_are_rejected(problem):
    trials,labels=fixture()
    if problem=='time':labels['allTriggers']=[1.,2.000001]
    elif problem=='duplicate':trials['id']=[10,10]
    elif problem=='overlap':labels['rightTriggers']=[1.,2.]
    elif problem=='missing':labels['incorrectTriggers']=[]
    else:trials['rewarded']=[1.,1.]
    with pytest.raises(ValueError):m.join(trials,labels)
