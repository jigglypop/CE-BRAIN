import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys/vc20hz_command_history.py'
spec = importlib.util.spec_from_file_location('vc20hz_command_history', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fake_records():
    times = np.r_[np.arange(8)*.05, .60151+np.arange(4)*.05]
    x = np.arange(len(module.RESPONSE))
    beta = np.vstack((-np.exp(-x/12), .7*np.exp(-x/23)))
    records = []
    for sweep in range(7):
        amplitude = np.full(12, .5 if sweep < 2 else 1.)
        level = np.full((12, len(module.RESPONSE)), 10.+sweep)
        record = dict(sweep=sweep, times=times, relative_amplitude=amplitude,
                      baselines=dict(level=level, linear=level))
        record['observed'] = level+module.design(record, .15)@beta
        records.append(record)
    return records, beta


def test_native_bin_bounds_and_future_samples_cannot_change_prefix():
    current = np.arange(10000, dtype=float)
    event = [2000]
    pre = module.bin_means(current, event, module.PRE)
    assert pre[0, 0] == np.mean(current[1000:1050])
    assert pre[0, -1] == np.mean(current[1750:1800])
    changed = current.copy()
    changed[1800:] += 1e9
    np.testing.assert_array_equal(module.bin_means(changed, event, module.PRE), pre)
    with pytest.raises(ValueError, match='outside'):
        module.bin_means(current, [100], module.PRE)


def test_level_and_linear_predictions_use_correct_bin_centers():
    pre_t = (module.PRE+(module.BIN-1)/2)/module.FS
    response_t = (module.RESPONSE+(module.BIN-1)/2)/module.FS
    pre = np.array([5+7*pre_t, -2-3*pre_t])
    result = module.baselines(pre)
    np.testing.assert_allclose(result['linear'], np.array([5+7*response_t, -2-3*response_t]), atol=1e-12)
    np.testing.assert_allclose(result['level'][:, 0], pre.mean(axis=1))


def test_history_is_strictly_past_amplitude_aware_and_decays_across_gap():
    t = np.array([1., 1.05, 1.10, 2.])
    u = np.ones(4)
    result = module.history(t, u, .15)
    changed = module.history(t, [1., 1., 100., 100.], .15)
    np.testing.assert_array_equal(result[:3], changed[:3])
    assert changed[3] > result[3]
    assert result[3] < result[2]
    np.testing.assert_allclose(module.history(t+40, u, .15), result, atol=1e-12)
    np.testing.assert_allclose(module.history(t, .5*u, .15), .5*result)


@pytest.mark.parametrize('times,amplitude,tau', [([0,0], [1,1], .1), ([0,1], [1,-1], .1),
                                               ([0,1], [1,1], float('nan'))])
def test_invalid_histories_rejected(times, amplitude, tau):
    with pytest.raises(ValueError, match='Invalid'):
        module.history(times, amplitude, tau)


@pytest.mark.parametrize('policy', ['level', 'linear'])
def test_inner_selection_and_fit_ignore_recovery_and_all_evaluation_sweeps(policy):
    records, _ = fake_records()
    old_tau, old_cv = module.choose_tau(records, policy)
    old_beta, _ = module.fit(records, policy, tau=old_tau)
    changed = copy.deepcopy(records)
    for record in changed:
        region = slice(8, None) if record['sweep'] in module.TRAIN else slice(None)
        record['observed'][region] = -1e12
        record['baselines'][policy][region] = 1e12
    new_tau, new_cv = module.choose_tau(changed, policy)
    new_beta, _ = module.fit(changed, policy, tau=new_tau)
    assert old_tau == new_tau
    assert old_cv == new_cv
    np.testing.assert_array_equal(old_beta, new_beta)


def test_synthetic_history_transport_recovers_held_gap_and_lower_amplitude():
    records, known = fake_records()
    tau, _ = module.choose_tau(records, 'level')
    assert tau == .15
    beta, _ = module.fit(records, 'level', tau=tau)
    np.testing.assert_allclose(beta, known, atol=1e-12)
    for record in records:
        predicted = record['baselines']['level']+module.design(record, tau)@beta
        np.testing.assert_allclose(predicted, record['observed'], atol=1e-12)


def test_fixed_model_has_no_history_column_and_requires_exact_train_membership():
    records, _ = fake_records()
    assert module.design(records[0]).shape == (12, 1)
    with pytest.raises(ValueError, match='sweep set'):
        module.fit([r for r in records if r['sweep'] != 3], 'level')


def test_later_own_command_change_is_specific_to_positive_target():
    records = [dict(sweep=s, target=t, source_command_V=.12,
                    own_command_V=.15 if t == 'positive' and s in (5, 6) else .12)
               for t in module.TARGETS for s in (2, 3, 5, 6)]
    positive = module.command_condition(records, 'positive', (5, 6))
    negative = module.command_condition(records, 'negative', (5, 6))
    assert positive['own_command_V_changed_from_training']
    assert not negative['own_command_V_changed_from_training']
    assert not positive['source_command_V_changed_from_training']
    assert not negative['source_command_V_changed_from_training']
