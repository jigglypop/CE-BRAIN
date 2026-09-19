import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/rey_premention_readout.py'
spec = importlib.util.spec_from_file_location('rey_readout',PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_half_open_window_and_clock_translation():
    spikes = np.array([-1.,0.,.5,1.,2.])
    assert m.spike_count(spikes,0,1)==2
    assert m.spike_count(spikes+1397,1397,1398)==2
    assert m.spike_count([],0,1)==0
    with pytest.raises(ValueError):
        m.spike_count([np.nan],0,1)


def test_variable_vp_width_and_padding():
    counts = m.vp_counts([[199,200,699,700,10000],[201,10000,10000,10000,10000]])
    np.testing.assert_array_equal(counts,[2,1])


def test_predictive_distribution_normalized_and_zero_count_exact():
    model = m.fit_predictive([0,1,2,3],.5)
    probs = np.exp(m.log_predictive(np.arange(500),1.5,model))
    assert probs.sum()==pytest.approx(1,abs=1e-12)
    assert probs[0]==pytest.approx((2/3.5)**6.5)


def test_uninformative_decoder_has_chance_score():
    model = m.fit_predictive([0,1,2],.5)
    logs = m.posterior(np.array([0,2,1,0,1]),1.5,dict(NR=model,R=model))
    scores = m.binary_scores(logs,[0,1,0,1,1],[1,2,1,2,2])
    assert scores['accuracy']==pytest.approx(.5)
    assert scores['brier']==pytest.approx(.25)
    assert scores['log_score_gain_vs_chance']==pytest.approx(0,abs=1e-14)


def test_story_balancing_does_not_reward_duplicated_story_trials():
    values = np.array([1,3,0,2])
    labels,stories = np.array([1,1,0,0]),np.array([1,2,3,4])
    auc = m.balanced_auc(values,labels,stories)
    assert auc==pytest.approx(.75)
    repeat = np.array([0,0,0,1,2,3])
    assert m.balanced_auc(values[repeat],labels[repeat],stories[repeat])==pytest.approx(auc)
    assert m.contrast(values[repeat],labels[repeat],stories[repeat])==pytest.approx(1)


def test_latency_matching_uses_caliper_and_maximum_cardinality():
    pairs = m.match_latencies([2000,2500,12000],[2250,2900,9000],500)
    assert pairs==[(0,0),(1,1)]


def test_shared_window_removes_identity_independent_time_drift():
    retained = [dict(story=s,trial=0,label=int(s<=2),mention_ms=t,behavioural_key=str(s))
                for s,t in ((1,3500),(2,3600),(3,3100),(4,3200))]
    spikes = np.arange(2000,3500,100.)
    lookup = {(s,0):spikes.copy() for s in (1,2,3,4)}
    model = m.fit_predictive([0,1,2],.5)
    result = m.matched_control(retained,dict(R=model,NR=model),lookup)
    assert result['complete_four_story_pairs']
    assert result['statistics']['contrast']==0
    assert result['statistics']['paired_win']==.5
    for row in result['comparisons']:
        assert row['shared_window_ms'][1]<=min(row['r_mention_ms'],row['nr_mention_ms'])
        assert row['r_count']==row['nr_count']


def test_participant_summary_weights_sessions_before_participants():
    from collections import defaultdict
    units = []
    # Two units in session1, one in session2 (same person), one in session3.
    # Unit mean .25, session mean 1/3, participant mean .25 are different contracts.
    for participant,session,value in ((1,1,0.),(1,1,0.),(1,2,1.),(2,3,0.)):
        for site in ('Right Hippocampus','Left Amygdala'):
            units.append(dict(participant=participant,session=session,site=site,
                statistics=defaultdict(lambda v=value:v),
                matched=dict(complete_four_story_pairs=True,matched_comparisons=4,
                    statistics=defaultdict(lambda v=value:v))))
    summary = m.summarize(units)['all']
    assert summary['participants']==2
    for block,metric in ((summary,'premention_accuracy'),(summary['matched'],'accuracy')):
        values = block['statistics'][metric]
        assert values['unit_mean']==pytest.approx(.25)
        assert values['session_mean']==pytest.approx(1/3)
        assert values['participant_mean']==pytest.approx(.25)
        assert values['by_participant']=={'1':.5,'2':0.}
    for region in ('H','A'):
        assert m.summarize(units)[region]['units']==4


def test_inhibitory_vp_decoder_reverses_count_ranking():
    models = dict(R=m.fit_predictive([0,0,1],.5),NR=m.fit_predictive([5,7,6],.5))
    counts = np.array([0,1,5,6])
    labels,stories = np.array([1,1,0,0]),np.arange(1,5)
    logs = m.posterior(counts,1.5,models)
    assert m.balanced_auc(counts,labels,stories)==0
    assert m.balanced_auc(logs[:,1]-logs[:,0],labels,stories)==1


def test_actual_anatomical_names_and_unknown_region():
    assert m.region_for_site('Left Hippocampus')=='H'
    assert m.region_for_site('Right Hippocampus')=='H'
    assert m.region_for_site('Left Amygdala')=='A'
    assert m.region_for_site('Right Amygdala')=='A'
    with pytest.raises(ValueError):
        m.region_for_site('unknown')
