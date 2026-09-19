import importlib.util
from pathlib import Path
import numpy as np
import pytest
PATH=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_choice_readout.py'
spec=importlib.util.spec_from_file_location('choice_readout',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_temporal_blocks_cover_each_trial_once_and_purge_neighbors():
    ids=np.arange(30)
    out=m.folds(ids)
    assert sorted(np.concatenate([v for _,v in out]).tolist())==ids.tolist()
    for train,held in out:
        assert np.min(np.abs(ids[train,None]-ids[held][None,:]))>1


def test_logistic_training_only_scaling_and_held_values_do_not_mutate_fit():
    x=np.c_[np.linspace(-2,2,20),np.ones(20)];y=(x[:,0]>0).astype(int)
    model=m.fit_logistic(x,y,.3);before=model['coef'].copy()
    assert np.array_equal(model['mean'],x.mean(axis=0)) and model['scale'][1]==1
    m.logits(np.array([[1000.,9.]]),model)
    assert np.array_equal(before,model['coef'])
    assert np.all(np.diff(m.logits(x,model))>0)


def test_held_covariate_and_target_mutation_cannot_change_outer_fit():
    x=np.linspace(-2,2,50)[:,None];y=np.tile([0,1],25);ids=np.arange(50)
    train,held=m.folds(ids)[2]
    _,a,report=m.fit_outer_fold(x,y,ids,train,held)
    changed=x.copy();changed[held]=1e6;target=y.copy();target[held]=1-target[held]
    _,b,other=m.fit_outer_fold(changed,target,ids,train,held)
    assert np.array_equal(a['coef'],b['coef']) and np.array_equal(a['mean'],b['mean']) and report==other


def test_proper_loss_penalizes_confident_wrong_prediction():
    assert m.losses(np.array([10.]),np.array([0]))[0]>m.losses(np.array([0.]),np.array([0]))[0]


def test_four_cells_does_not_confuse_choice_presence_with_cue_conditional_support():
    assert not m.four_cells(np.array([0,0,1,1]),np.array([0,0,1,1]))
    assert m.four_cells(np.array([0,0,1,1]),np.array([0,1,0,1]))


def test_single_class_training_is_rejected():
    with pytest.raises(ValueError):m.fit_logistic(np.ones((10,2)),np.ones(10),1.)


def fixture():
    trials=[]
    for j in range(3):
        trials.append(dict(trial_id=j,start_s=j*10.,stop_s=j*10.+1,choice_right=j%2,odor_side='right' if j%2 else 'left',
            correct=True,choice_time_s=j*10.+2,task_epoch_row=0,source_epoch=1,
            windows={k:dict(start_s=j*10.+.5,stop_s=j*10.+1.) for k in ['a','b','c','d']}))
    session=dict(trials=trials,_window_names=['a','b','c','d'])
    arrays=dict(valid=np.ones((3,4),bool),counts=np.arange(36).reshape(3,4,3),motion=np.zeros((3,4,8)))
    return session,arrays


def test_joint_uses_only_ca1_pfc_and_all_models_share_covariates_and_history_availability():
    s,a=fixture();ids,designs,y,cue=m.feature_sets(s,a,['CA1','PFC','OB'],0)
    assert len(ids)==3 and designs['joint_current'].shape==(3,len(m.Q_NAMES)+2)
    assert designs['joint_current_history'].shape==(3,len(m.Q_NAMES)+4)
    for x in designs.values():assert np.array_equal(x[:,:len(m.Q_NAMES)],designs['behavior'])
    assert np.array_equal(designs['behavior'][:,8],[0,1,1])
    s['trials'][1]['source_epoch']=2
    _,changed,_,_=m.feature_sets(s,a,['CA1','PFC','OB'],0)
    assert np.array_equal(changed['behavior'][:,8],[0,0,0])


def test_all_windows_use_same_common_trials_and_current_correct_is_not_a_feature():
    s,a=fixture();a['valid'][1,3]=False
    for wi in range(4):
        ids,_,_,_=m.feature_sets(s,a,['CA1','PFC','OB'],wi)
        assert np.array_equal(ids,[0,2])
    _,before,_,_=m.feature_sets(s,a,['CA1','PFC','OB'],0)
    s['trials'][2]['correct']=False
    _,after,_,_=m.feature_sets(s,a,['CA1','PFC','OB'],0)
    assert np.array_equal(before['behavior'],after['behavior'])


def test_region_identity_and_coverage_fail_closed():
    w=[dict(asset_id='a',unit_ids=[0,1])]
    r=[dict(asset_id='a',unit_ids=[0,1],regions=['CA1','PFC'],source_area_verified=[True,True],eligible=True)]
    assert set(m.region_lookup(w,r))=={'a'}
    with pytest.raises(ValueError):m.region_lookup(w,r+r)
    with pytest.raises(ValueError):m.region_lookup(w,[])
    r[0]['regions']=['CA1']
    with pytest.raises(ValueError):m.region_lookup(w,r)


def test_rat_summary_weights_sessions_then_rats_not_trials():
    rows=[]
    for rat,gain,trials in [('a',0.,1),('a',2.,100),('b',5.,1)]:
        rows.append(dict(rat=rat,status='evaluated',common_trials=trials,windows={'w':dict(
            gain_vs_behavior_nats={name:gain for name in m.MODELS if name!='behavior'},history_increment_nats=gain)}))
    summary=m.aggregate(rows,['w'])
    assert summary['windows']['w']['rat_equal_gain_nats']['joint_current']==3.
    assert summary['evaluated_trials']==102
