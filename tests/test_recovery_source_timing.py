import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('timing_analysis',Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys/recovery_source_timing.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(sweep=37):
    t = np.arange(1100)*module.DT-.1
    onsets = np.r_[np.arange(8)*.02,.26651+np.arange(4)*.02]
    spikes = onsets+.00071
    valid = t>=0
    for onset,spike in zip(onsets,spikes):
        valid &= ~((t<spike+.002)&(t+module.DT>onset-.0005))
    return dict(sweep=sweep,target='positive',gap_s=.12651,left_times=t,spikes=spikes,valid=valid,y=30*np.sin(t*30))


@pytest.mark.parametrize('window',['short','long'])
def test_anchor_respects_first_guard_and_all_current_response_exclusions(window):
    raw = fixture()
    r = module.observation_design(raw,window)
    assert r['anchor_left'][0]+module.DT<=-.0005+1e-12
    assert len(np.unique(r['pulses']))==12
    changed = copy.deepcopy(raw)
    changed['y'][r['indices']]+=1000
    after = module.observation_design(changed,window)
    np.testing.assert_array_equal(after['baseline'],r['baseline'])
    np.testing.assert_allclose(after['innovation'],r['innovation']+1000)


def test_short_and_long_windows_share_anchors_and_unchanged_samples():
    raw = fixture()
    short,long = [module.observation_design(raw,w) for w in ('short','long')]
    lookup = {index:i for i,index in enumerate(long['indices'])}
    indices = [lookup[index] for index in short['indices']]
    for name in ('observed','baseline','anchors','left','pulses'):
        np.testing.assert_array_equal(short[name],long[name][indices])


@pytest.mark.parametrize('shift',[-10.,0.,10.])
def test_source_time_shift_is_exact_translation_without_moving_target_data(shift):
    r = module.observation_design(fixture(),'long')
    before = copy.deepcopy(r)
    actual = module.basis_difference(r,shift,1.,1.,16.)
    direct = module.base.kernel_basis(r['left']-shift/1000,r['spikes'],.001,.001,.016)
    direct -= module.base.kernel_basis(r['anchor_left']-shift/1000,r['spikes'],.001,.001,.016)
    np.testing.assert_allclose(actual,direct,atol=1e-12)
    for key in ('observed','baseline','left','anchors'):
        np.testing.assert_array_equal(r[key],before[key])


def test_waveform_error_decomposes_and_does_not_hide_zero_mean_shape():
    r = module.observation_design(fixture(),'short')
    prediction = r['innovation'].copy()
    for pulse in range(12):
        mask = r['pulses']==pulse
        perturbation = np.arange(mask.sum(),dtype=float)
        perturbation -= perturbation.mean()
        prediction[mask] += perturbation
    metrics = module.error_metrics(r,prediction,'initial')
    assert metrics['pulse_mean_mse_uV2']<1e-25
    assert metrics['waveform_mse_uV2']>0
    assert metrics['waveform_mse_uV2']==pytest.approx(metrics['within_pulse_mse_uV2'])


def test_fit_recovers_known_kernel_and_ignores_excluded_target_outcomes(monkeypatch):
    monkeypatch.setattr(module.base,'KERNEL_GRID',((1.,1.,16.),))
    monkeypatch.setattr(module.base,'HISTORY_GRID',[('constant',0.,1.),('depression',.3,.1)])
    records = []
    for sweep in range(37,48):
        raw = fixture(sweep)
        raw['y'] = 123+27*module.base.kernel_basis(raw['left_times'],raw['spikes'],.001,.001,.016).sum(axis=1)
        records.append(module.observation_design(raw,'long'))
    best,profile = module.fit_models(records,0.)
    assert best['constant']['amplitude_uV']==pytest.approx(27)
    assert best['constant']['training_mse_uV2']<1e-20
    changed = copy.deepcopy(records)
    for r in changed:
        r['innovation'][r['pulses']>=8]+=1e6
        if r['sweep']>=47:
            r['innovation'][:]=-1e8
    assert module.fit_models(changed,0.)==(best,profile)


def test_actual_kernel_cannot_see_future_spike_but_negative_shift_control_can():
    times = np.array([.012])
    spike = np.array([.020])
    actual = module.base.kernel_basis(times,spike,.001,.001,.016)
    shifted = module.base.kernel_basis(times,spike-.010,.001,.001,.016)
    assert actual[0,0]==0
    assert shifted[0,0]>0
