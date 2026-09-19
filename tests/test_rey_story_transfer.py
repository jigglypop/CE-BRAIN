import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/rey_story_transfer.py'
spec = importlib.util.spec_from_file_location('rey_transfer',PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_identity_folds_hold_each_nonadjacent_story_twice_without_leakage():
    stories = np.repeat([1,2,3,4],[5,6,7,8])
    labels = np.isin(stories,[1,3]).astype(int)
    held_count = np.zeros(len(stories),int)
    for train,held,meta in m.identity_splits(stories,labels):
        assert not set(train)&set(held)
        assert not set(stories[train])&set(stories[held])
        assert set(labels[train])==set(labels[held])=={0,1}
        assert len(meta['held_stories'])==len(meta['train_stories'])==2
        held_count[held] += 1
    np.testing.assert_array_equal(held_count,2)


def test_held_features_and_labels_never_enter_fit():
    features = np.array([-2.,-1.,1.,2.,-1.5,1.5])[:,None]
    labels = np.array([0,0,1,1,0,1])
    train,held,keys = np.arange(4),np.array([4,5]),np.array(list('abcdef'))
    first = m.fitted_entry(train,held,features,labels,(0,),keys)
    changed_x,changed_y = features.copy(),labels.copy()
    changed_x[held] *= -100000
    changed_y[held] = 1-changed_y[held]
    second = m.fitted_entry(train,held,changed_x,changed_y,(0,),keys)
    assert json.dumps(first['fit'],sort_keys=True)==json.dumps(second['fit'],sort_keys=True)


def test_constant_feature_imbalanced_classes_shrink_to_chance():
    model = m.fit_logistic(np.full((13,1),7.),[0]*3+[1]*10,(0,))
    assert model['constant']==[True]
    assert model['coefficients']==[0.,0.]
    logs = m.predict_logistic([100.,-100.],model)
    assert m.scores(logs,[0,1])['log_gain']==pytest.approx(0,abs=1e-14)
    assert m.scores(logs,[0,1])['accuracy']==.5


def test_reversed_visual_signal_reaches_nonnegative_boundary():
    model = m.fit_logistic([-2,-1,1,2],[1,1,0,0],(0,))
    assert model['coefficients'][0]==pytest.approx(0,abs=1e-10)
    assert m.scores(m.predict_logistic([-2,2],model),[1,0])['log_gain']==pytest.approx(0,abs=1e-12)
    unconstrained = m.fit_logistic([-2,-1,1,2],[1,1,0,0])
    assert unconstrained['coefficients'][0]<0


def test_extreme_test_logits_remain_finite_and_normalized():
    model = m.fit_logistic([-1e6,-5e5,5e5,1e6],[0,0,1,1],(0,))
    logs = m.predict_logistic([-1e15,1e15],model)
    assert np.isfinite(logs).all()
    np.testing.assert_allclose(np.exp(logs).sum(axis=1),1)
    assert m.scores(logs,[0,1])['accuracy']==1


def test_wrong_overconfidence_can_rank_above_chance_but_fail_proper_score():
    positive = np.array([.01,.02,.03,.04])
    labels = [0,0,1,1]
    metric = m.scores(np.column_stack([np.log1p(-positive),np.log(positive)]),labels)
    assert metric['auc']==1
    assert metric['log_gain']<0


def test_fit_rejects_key_leakage_and_invalid_inputs():
    with pytest.raises(ValueError,match='leakage'):
        m.fitted_entry(np.array([0,1]),np.array([2,3]),np.arange(4)[:,None],np.array([0,1,0,1]),(),np.array(['a','b','a','c']))
    with pytest.raises(ValueError):
        m.fit_logistic([1,np.nan],[0,1])
    with pytest.raises(ValueError):
        m.fit_logistic([1,2],[0,0])
    with pytest.raises(ValueError):
        m.scores(np.zeros((2,2)),[0,1])


def test_story_crossfit_splits_stored_repetitions_exactly_once():
    stories = np.repeat([1,2,3,4],[5,6,7,8])
    trials = np.concatenate([np.arange(n)*2 for n in (5,6,7,8)])
    labels = np.isin(stories,[2,4]).astype(int)
    tested = np.zeros(len(stories),int)
    for train,held,context,meta in m.story_splits(stories,trials,labels):
        json.dumps(meta,allow_nan=False)
        assert not set(train)&set(held)
        assert set(context[train])==set(context[held])=={0,1}
        assert set(stories[train])==set(stories[held])==set(meta['stories'])
        tested[held] += 1
    np.testing.assert_array_equal(tested,1)


def test_small_story_is_explicitly_ineligible_without_dropping_identity():
    stories = np.repeat([1,2,3,4],[5,6,2,8])
    trials = np.concatenate([np.arange(n) for n in (5,6,2,8)])
    gate = m.story_eligibility(stories,trials)
    assert gate==dict(eligible=False,minimum_repetitions_per_story=4,small_cells=[dict(story=3,eligible_repetitions=2)])
    labels = np.isin(stories,[1,3]).astype(int)
    assert len(m.identity_splits(stories,labels))==4
    with pytest.raises(ValueError,match='Insufficient'):
        m.story_splits(stories,trials,labels)


def test_hierarchical_weights_do_not_count_units_as_participants():
    units = []
    for participant,session,value in ((1,1,0.),(1,1,0.),(1,2,1.),(2,3,0.)):
        for region in ('H','A'):
            scores = {metric:value for metric in ('accuracy','auc','log_loss','log_gain','brier')}
            units.append(dict(participant=participant,session=session,region=region,
                              identity=dict(scores=dict(example=scores))))
    result = m.aggregate(units,'identity')
    for region in ('all','H','A'):
        summary = result[region]['models']['example']['log_gain']
        assert summary['unit_mean']==pytest.approx(.25)
        assert summary['session_mean']==pytest.approx(1/3)
        assert summary['participant_mean']==pytest.approx(.25)
        assert summary['by_participant']=={'1':.5,'2':0.}


def test_fold_metrics_receive_equal_weight():
    folds = [dict(models=dict(x=dict(scores={metric:value for metric in ('accuracy','auc','log_loss','log_gain','brier')})))
             for value in (0.,0.,0.,1.)]
    assert m.mean_scores(folds)['x']['log_gain']==.25
