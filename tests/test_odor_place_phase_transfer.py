import importlib.util
from pathlib import Path
import numpy as np
import pytest
from scipy.special import expit

PATH=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_phase_transfer.py'
spec=importlib.util.spec_from_file_location('phase_transfer',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_epoch_blocks_never_pool_same_unit_across_source_or_task_epochs():
    session=dict(trials=[dict(source_epoch=a,task_epoch_row=b) for a,b in [(1,0),(1,0),(2,0),(2,0),(2,1),(2,1)]])
    blocks=m.epoch_blocks(session,np.array([True,False,True,True,False,True]))
    assert [(key,ids.tolist()) for key,ids in blocks]==[((1,0),[0]),((2,0),[2,3]),((2,1),[5])]


def test_only_supported_regions_enter_neural_or_joint_designs():
    counts=np.array([[0,1,1000],[2,3,1000]]);motion=np.zeros((2,8))
    x=m.designs(counts,motion,['CA1','PFC','OB'])
    assert x['joint'].shape==(2,2) and x['motion_joint'].shape==(2,10)
    assert np.array_equal(x['motion_joint'][:,:8],motion)
    with pytest.raises(ValueError):m.designs(counts,motion,['CA1','OB','OB'])


def test_target_shift_and_held_label_or_source_changes_do_not_change_source_fit():
    engine=m.estimator();ids=np.arange(60);y=np.tile([0,1,1,0],15)
    source=np.c_[np.sin(ids*.7),y+.1*np.cos(ids)]
    target=source+4.;train,held=engine.folds(ids)[2]
    predictions,a,selection=m.fit_transfer(source,{'source':source,'target':target},y,ids,train,held,engine)
    changed=source.copy();changed[held]=1e6
    flipped=y.copy();flipped[held]=1-flipped[held]
    predicted,b,other=m.fit_transfer(changed,{'target':target-1000},flipped,ids,train,held,engine)
    for key in ('mean','scale','coef'):assert np.array_equal(a[key],b[key])
    assert selection==other and np.array_equal(a['mean'],source[train].mean(axis=0))
    assert np.allclose(predictions['target'],engine.logits(target[held],a))
    assert not np.array_equal(predictions['target'],predicted['target'])


def test_priors_use_training_cue_counts_and_do_not_read_test_outcomes():
    marginal,cue=m.prior_logits(np.array([0,0,0,1,1,1]),np.array([0,0,1,0,1,1]),np.array([1,0,1]))
    assert marginal==0 and cue[0]==cue[2] and cue[0]>0>cue[1]
    with pytest.raises(ValueError):m.prior_logits(np.ones(6,int),np.tile([0,1],3),[0])


def test_error_scores_separate_cue_aligned_prediction_from_actual_choice():
    engine=m.estimator();cue=np.array([0,0,1,1]);y=np.array([0,1,0,1]);eta=6*(2*cue-1)
    out=m.scores(eta,y,cue,np.zeros(4,int),engine)
    assert out['incorrect_trials']==2 and out['incorrect_choice_over_cue_nats']<0
    assert out['incorrect_cue_log_loss']<out['incorrect_choice_log_loss']
    assert out['within_fold_cue_auc_mean']==.5 and out['within_fold_cue_auc_cells']==2


def test_auc_has_no_cross_fold_or_cross_cue_pairs():
    engine=m.estimator();cue=np.array([0,0,1,1]);y=np.array([0,1,0,1])
    out=m.scores(np.array([-10,10,-10,10]),y,cue,np.arange(4),engine)
    assert out['within_fold_cue_auc_mean'] is None and out['within_fold_cue_auc_cells']==0


def test_single_readout_metric_has_null_directions_and_matches_local_kl():
    eta=.3;cov=np.array([1.,2.,0.]);g=m.bernoulli_metric(eta,cov)
    assert np.linalg.matrix_rank(g)==1
    null=np.array([2.,-1.,7.]);assert abs(null@g@null)<1e-12
    delta=np.array([.4,-.1,2.]);eps=1e-4
    p=expit(eta);q=expit(eta+eps*(cov@delta))
    kl=p*np.log(p/q)+(1-p)*np.log((1-p)/(1-q))
    assert np.isclose(2*kl/eps**2,delta@g@delta,rtol=2e-5,atol=1e-7)
    assert not np.linalg.det(g)>0


def test_hierarchical_summary_keeps_blocks_sessions_rats_and_maze_strata_separate():
    def row(rat,session,gain,n):
        window=dict(gain_vs_marginal_nats={k:gain for k in m.MODELS},gain_vs_cue_prior_nats={k:gain for k in m.MODELS},
            neural_increment_over_motion_nats={k:gain for k in ('motion_ca1','motion_pfc','motion_joint')},
            models={k:dict(incorrect_choice_over_cue_nats=gain,within_fold_cue_auc_mean=.5) for k in m.MODELS})
        return dict(rat=rat,identifier=session,status='evaluated',common_trials=n,windows={'w':window})
    rows=[row('CS33','a',0,100),row('CS33','a',10,1),row('CS33','b',1,20),row('CS34','c',9,30),row('CS44','d',100,50)]
    out=m.aggregate(rows,['w'])
    assert out['strata']['full_maze']['rat_equal_windows']['w']['gain_vs_marginal_nats']['joint']==6
    assert out['strata']['shortened_stem']['rat_equal_windows']['w']['gain_vs_marginal_nats']['joint']==100
    assert out['strata']['adjacent_wells']['rat_equal_windows']=={}
