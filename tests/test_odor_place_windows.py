import importlib.util
from pathlib import Path
import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_windows.py'
spec = importlib.util.spec_from_file_location('odor_place_windows', PATH)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_count_uses_half_open_interval_with_duplicate_events():
    assert m.count_window(np.array([.0, .1, .1, .5, .6]), .1, .5) == 2


def test_choice_cannot_cross_next_trial_or_epoch_boundary():
    assert m.first_choice([(2., 1), (4., 0)], 1., 2.) == (None, 'no_well_entry')
    assert m.first_choice([(2., 1), (4., 0)], 1., 3.) == ((2., 1), 'resolved')


def test_opposite_wells_at_same_first_time_are_ambiguous():
    assert m.first_choice([(2., 0), (2., 1), (3., 0)], 1., 4.)[1] == 'simultaneous_opposite_wells'


def test_short_nosepoke_is_not_relabelled_as_full_sampling():
    for kind, bounds in zip(m.WINDOWS, m.window_bounds(1., 1.4)):
        reasons = m.temporal_reasons(kind, *bounds, 1., 1.4, (0., 4.), .5, 3., 2.5)
        assert ('nosepoke_shorter_than_500ms' in reasons) == (kind in {'earlycue', 'latecue'})


def test_postcue_window_cannot_include_actual_choice():
    reasons = m.temporal_reasons('postcue', 2., 2.5, 1., 2., (0., 4.), .5, 3., 2.4)
    assert reasons == ['includes_choice_or_later']


def test_task_boundary_applies_to_all_windows():
    assert 'outside_task_epoch' in m.temporal_reasons('precue', .5, 1., 1., 2., (.6, 4.), 0., 3., 2.8)


@pytest.mark.parametrize('times', [np.array([.2,.3,.4]), np.array([0.,.01,.3,.4]), np.array([.01])])
def test_position_missing_edges_internal_gap_or_samples_are_rejected(times):
    result, support = m.position_window(times, np.ones((len(times), 3)), 0., .5)
    assert result is None and support['reasons']


def test_real_position_samples_are_used_without_interpolation():
    times = np.arange(.01, .5, .03)
    values = np.c_[times*2, times*0, np.ones(len(times))*2]
    features, support = m.position_window(times, values, 0., .5)
    assert not support['reasons'] and support['samples'] == len(times)
    assert features[2] == 2 and np.isclose(features[4], values[-1,0]-values[0,0])


def test_ragged_spikes_preserve_empty_unit_without_inventing_events():
    units = m.unit_spikes(np.array([1.,2.,3.]), np.array([2,2,3], dtype=np.uint64), 3)
    assert len(units[1]) == 0 and np.array_equal(units[2], [3.])


def test_ragged_spikes_reject_unsorted_and_incomplete_index():
    with pytest.raises(ValueError): m.unit_spikes(np.array([2.,1.]), np.array([2]), 1)
    with pytest.raises(ValueError): m.unit_spikes(np.array([1.,2.]), np.array([1]), 1)


def test_unverified_single_dio_slot_is_not_assigned_to_later_epoch():
    from types import SimpleNamespace
    channels = np.empty(2, dtype=object)
    channels[0] = SimpleNamespace(time=np.array([1.,2.]))
    channels[1] = SimpleNamespace(time=np.array([1.,3.]))
    value, reason = m.resolve_slot([channels], 2, True, np.array([10.,20.]), 'dio')
    assert value is None and reason == 'unresolved'
