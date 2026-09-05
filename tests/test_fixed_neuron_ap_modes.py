"""A mixed auxiliary clamp must not alter a target's PSP measurement."""
import importlib.util
import sys
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('ap_modes_candidate', HERE/'allen_ap_history_modes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_auxiliary_vc_preserves_psp_and_target_vc_is_excluded(tmp_path):
    fs = 50000
    t = np.arange(80000)/fs
    onsets = np.r_[.6+np.arange(8)*.02, .99152+np.arange(4)*.02]
    source = np.full(len(t), -.07)
    command = np.zeros(len(t))
    target = np.full(len(t), -.07)
    for start in onsets:
        a = round(start*fs)
        source[a:a+80] = np.r_[np.linspace(-.07, .03, 20), np.linspace(.03, -.07, 60)]
        command[a:a+75] = 500e-12
        dt = np.maximum(t-start-.002, 0)
        target += .0001*(np.exp(-dt/.02)-np.exp(-dt/.002))
    with h5py.File(tmp_path/'mixed.nwb', 'w') as f:
        for kind, group in [('voltage', 'acquisition/timeseries'), ('command', 'stimulus/presentation')]:
            for device in (0, 1, 3, 5, 6):
                node = f.create_group(f'{group}/data_00036_D{device}')
                node.create_dataset('electrode_name', data=np.array([f'electrode_{device}'.encode()]))
                values = source if device == 0 else target if device == 5 else np.full(len(t), -.07)
                if kind == 'command':
                    values = command if device == 0 else np.zeros(len(t))
                ds = node.create_dataset('data', data=values)
                ds.attrs['unit'] = 'V' if kind == 'voltage' else 'A'
                ds.attrs['conversion'] = 1.
                ds.attrs['offset'] = 0.
                clock = node.create_dataset('starting_time', data=[0.])
                clock.attrs['rate'] = fs
        db = dict(pulses=[dict(onset_time=float(s), n_spikes=1, first_spike_time=None) for s in onsets])
        pair = dict(pair_id=121538, pre_device=0, post_device=5)
        before = m.old.extract(f, 36, pair, db)
        assert before['usable']
        aux_adc = f['acquisition/timeseries/data_00036_D1/data']
        aux_cmd = f['stimulus/presentation/data_00036_D1/data']
        aux_adc.attrs['unit'], aux_cmd.attrs['unit'] = 'A', 'V'
        aux_adc[:] = 10e-12
        aux_cmd[:] = -.07
        nodes, modes = m.inspect_modes(f, 36)
        after = m.extract(f, 36, pair, db, nodes, modes)
        assert after['usable'] and after['modes'][1] == 'vc'
        np.testing.assert_array_equal(after['psp_bins_mV'], before['psp_bins_mV'])
        np.testing.assert_array_equal(after['quiet_bins_mV'], before['quiet_bins_mV'])
        changed_target = m.extract(f, 36, dict(pair_id=121566, pre_device=6, post_device=1), db, nodes, modes)
        assert not changed_target['usable'] and changed_target['exclusion'] == 'target_clamp_mode_changed'
