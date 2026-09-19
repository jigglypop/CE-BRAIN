import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/cml_withincategory_readout.py'
spec=importlib.util.spec_from_file_location('cml_readout',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_spectral_power_units_dc_removal_and_mains_exclusion():
    t=np.arange(800)/1600
    x=np.sin(2*np.pi*80*t)
    base=m.log_hfa(x[None])[0]
    assert m.log_hfa((3*x+20)[None])[0]-base==pytest.approx(np.log(9),abs=1e-10)
    mains=m.log_hfa(np.sin(2*np.pi*120*t)[None])[0]
    assert base-mains>np.log(1e6)
    with pytest.raises(ValueError,match='nonpositive'):
        m.log_hfa(np.ones((2,800)))


def test_identical_neural_scores_cannot_improve_prior():
    rows=[dict(row=i,list=i//2,item=str(i),serialpos=[1,2,7,8],true_index=i%4,cosine=[.4]*4) for i in range(6)]
    scored,summary=m.score_rows(rows)
    assert summary['incremental_log_gain']['equal_list']==pytest.approx(0,abs=1e-14)
    for row in scored:
        assert row['list'] not in row['prior_fit']['training_lists']
        assert row['row'] not in row['prior_fit']['training_event_rows']


def test_held_list_labels_cannot_change_its_prior_and_ties_prefer_zero():
    rows=[dict(row=i,list=i//4,serialpos=[1,2,7,8],true_index=i%4) for i in range(12)]
    a=m.select_beta(rows,0)
    for row in rows[:4]:row['true_index']=3
    b=m.select_beta(rows,0)
    assert a==b and a[0]==0


def test_list_weighting_tie_credit_and_cosine_zero_vector():
    assert m.equal_list_mean([1,1,1,-1],[1,1,1,2])==0
    np.testing.assert_array_equal(m.cosine_scores(np.zeros(2),np.eye(4,2)),np.zeros(4))
    rows=[dict(row=i,list=i//4,serialpos=[1,2,7,8],true_index=i%4,cosine=[0]*4) for i in range(8)]
    scored,summary=m.score_rows(rows)
    assert summary['top1_credit']['equal_list']==.25
    assert summary['true_rank_mid']['equal_list']==2.5


def test_reversed_content_can_hurt_proper_score():
    rows=[dict(row=i,list=i//4,serialpos=[1,2,7,8],true_index=i%4,
               cosine=[-1 if j==i%4 else 1 for j in range(4)]) for i in range(8)]
    _,summary=m.score_rows(rows)
    assert summary['incremental_log_gain']['equal_list']<0
    assert summary['top1_credit']['equal_list']==0
