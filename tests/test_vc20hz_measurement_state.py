import copy
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('vc20hz_measurement_state', HERE/'vc20hz_measurement_state.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture_record():
    recording = dict(id=12, electrode_id=9, stim_meta=dict(type='Stimulus', items=[
        dict(type='Offset', args=dict(units='V', amplitude=-.07), items=[]),
        dict(type='SquarePulse', args=dict(description='test pulse', start_time=.0075,
             duration=.01001, amplitude=-.01), items=[]),
        dict(type='SquarePulseTrain', args=dict(start_time=1.05, n_pulses=1, interval=.05,
             pulse_duration=.0015, amplitude=.06), items=[])]))
    patch = dict(id=15, clamp_mode='vc', qc_pass=1, baseline_potential=-.07,
                 baseline_current=-300e-12, access_adj_baseline_potential=-.062)
    pulse = dict(id=17, recording_id=12, electrode_id=9, start_index=0,
                 stop_index=2500, access_resistance_lowpass=40e6, baseline_current=-200e-12)
    command = dict(samples=505902, rate=100000, initial_command_V=0., all_command_intervals=[
        dict(start_index=750, stop_index=1751, start_s=.0075, duration_s=.01001,
             delta_min_V=-.01, delta_max_V=-.01),
        dict(start_index=105000, stop_index=105150, start_s=1.05, duration_s=.0015,
             delta_min_V=.06, delta_max_V=.06)])
    return recording, patch, pulse, command


def test_holding_and_signed_baseline_ir_drop_not_pulse_voltage_correction():
    fixture = fixture_record()
    before = copy.deepcopy(fixture)
    result = module.diagnose(*fixture)
    assert not result['issues']
    assert result['embedded_test_pulse']['confirmed']
    assert result['baseline_ir_drop_estimate_V'] == pytest.approx(-.062)
    assert result['baseline_ir_drop_formula_residual_V'] == pytest.approx(0.)
    assert result['baseline_ir_drop_current_source'] == 'test_pulse.baseline_current'
    assert result['command_intervals'][1]['commanded_min_V'] == pytest.approx(-.01)
    assert fixture == before


@pytest.mark.parametrize('change', ['missing_indices', 'different_electrode', 'different_recording',
                                    'not_covering', 'wrong_metadata'])
def test_same_id_alone_does_not_establish_embedded_test_pulse(change):
    recording, patch, pulse, command = fixture_record()
    if change == 'missing_indices':
        pulse['start_index'] = pulse['stop_index'] = None
    elif change == 'different_electrode':
        pulse['electrode_id'] = 8
    elif change == 'different_recording':
        pulse['recording_id'] = 11
    elif change == 'not_covering':
        pulse['stop_index'] = 1000
    else:
        recording['stim_meta']['items'][1]['args']['amplitude'] = -.005
    result = module.diagnose(recording, patch, pulse, command)
    assert not result['embedded_test_pulse']['confirmed']
    assert 'embedded_test_pulse_not_established' in result['issues']


def test_missing_patch_and_test_pulse_preserve_missingness():
    recording, _, _, command = fixture_record()
    patch = dict.fromkeys(module.FIELDS['p'])
    pulse = dict.fromkeys(module.FIELDS['t'])
    result = module.diagnose(recording, patch, pulse, command)
    assert result['baseline_ir_drop_estimate_V'] is None
    assert result['command_intervals'] == []
    assert 'missing_or_non_vc_patch' in result['issues']
    assert 'minimal_qc_not_passed' in result['issues']
    assert 'embedded_test_pulse_not_established' in result['issues']


def test_holding_disagreement_and_missing_filtered_resistance_are_visible():
    recording, patch, pulse, command = fixture_record()
    patch['baseline_potential'] = -.06
    pulse['access_resistance_lowpass'] = None
    result = module.diagnose(recording, patch, pulse, command)
    assert result['baseline_ir_drop_estimate_V'] is None
    assert 'holding_baseline_disagreement' in result['issues']


def test_one_sample_quantization_allowed_but_wrong_train_time_rejected():
    recording, patch, pulse, command = fixture_record()
    command['all_command_intervals'][1]['duration_s'] += 1/command['rate']
    assert module.diagnose(recording, patch, pulse, command)['positive_command_schedule']['matches']
    recording['stim_meta']['items'][2]['args']['start_time'] += .001
    result = module.diagnose(recording, patch, pulse, command)
    assert not result['positive_command_schedule']['matches']
    assert 'positive_command_metadata_disagreement' in result['issues']


def test_indexed_left_join_retains_missing_qc_and_missing_nearest_pulse():
    db = module.apsw.Connection(':memory:')
    try:
        for alias, name in (('r', 'recording'), ('p', 'patch_clamp_recording'), ('t', 'test_pulse')):
            fields = ['id INTEGER PRIMARY KEY']+[
                k+' INTEGER' if k.endswith('_id') else k
                for k in module.FIELDS[alias] if k != 'id']
            db.execute('CREATE TABLE '+name+' ('+', '.join(fields)+')')
        db.execute('CREATE INDEX ix_recording_sync_rec_id ON recording(sync_rec_id)')
        db.execute('CREATE UNIQUE INDEX ix_patch_clamp_recording_recording_id ON patch_clamp_recording(recording_id)')
        db.execute('INSERT INTO recording(id,sync_rec_id,electrode_id) VALUES (1,20,2),(2,20,4),(3,21,5)')
        db.execute('INSERT INTO patch_clamp_recording(id,recording_id,nearest_test_pulse_id) VALUES (7,1,99)')
        plans = []
        rows = module.indexed_query(db, module.JOIN, (20,2,4,5), plans)
        assert {x['r_id'] for x in rows} == {1,2}
        assert next(x for x in rows if x['r_id'] == 1)['t_id'] is None
        assert next(x for x in rows if x['r_id'] == 2)['p_id'] is None
        assert not any('SCAN ' in x['detail'] for x in plans[0]['plan'])
        with pytest.raises(ValueError, match='scan'):
            module.indexed_query(db, 'SELECT * FROM test_pulse WHERE input_resistance=?', (1,), [])
        assert module.indexed_query(db, module.JOIN, (30,2,4,5), []) == []
    finally:
        db.close()
