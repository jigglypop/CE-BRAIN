import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('prefix_analysis',Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys/recovery_source_prefix.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    t = np.arange(1100)*module.timing.DT-.1
    onsets = np.r_[np.arange(8)*.02,.26651+np.arange(4)*.02]
    spikes = onsets+.0012
    valid = t>=0
    for onset,spike in zip(onsets,spikes):
        valid &= ~((t<spike+.002)&(t+module.timing.DT>onset-.0005))
    return dict(sweep=37,target='positive',gap_s=.12651,left_times=t,spikes=spikes,valid=valid,y=np.cos(t*20))


@pytest.mark.parametrize('window',['short','long'])
def test_own_and_future_response_cannot_change_current_forecast(window):
    raw = fixture()
    r = module.prefix_design(raw,window)
    changed = copy.deepcopy(raw)
    first = r['indices'][r['pulses']==3][0]
    changed['y'][first:]+=1e6
    after = module.prefix_design(changed,window)
    np.testing.assert_array_equal(after['baseline'][r['pulses']<=3],r['baseline'][r['pulses']<=3])
    assert r['anchor_left'][0]+module.timing.DT<=-.0005+1e-12


def test_prior_response_can_update_later_forecast_but_target_scores_stay_fixed():
    raw = fixture()
    old = module.timing.observation_design(raw,'long')
    new = module.prefix_design(raw,'long')
    np.testing.assert_array_equal(old['observed'],new['observed'])
    np.testing.assert_array_equal(old['indices'],new['indices'])
    pulse1 = new['pulses']==1
    anchor = new['anchors'][pulse1][0]
    assert anchor>old['anchors'][pulse1][0]
    assert raw['valid'][anchor]
    changed = copy.deepcopy(raw)
    changed['y'][anchor]+=123
    after = module.prefix_design(changed,'long')
    np.testing.assert_allclose(after['baseline'][pulse1],new['baseline'][pulse1]+123)


def test_short_long_share_prefix_and_constant_voltage_cancels():
    raw = fixture()
    short,long = [module.prefix_design(raw,w) for w in ('short','long')]
    for pulse in range(12):
        assert short['anchors'][short['pulses']==pulse][0]==long['anchors'][long['pulses']==pulse][0]
    changed = copy.deepcopy(raw)
    changed['y']+=999
    np.testing.assert_allclose(module.prefix_design(changed,'long')['innovation'],long['innovation'],atol=1e-12)
