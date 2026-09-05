"""Scientific numerical witnesses, without opening any biological response."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

SOURCE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric/allen_testpulse_model.py'
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location('fixed_neuron_testpulse', SOURCE)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def test_passive_circuit_recovery_and_offset_prediction():
    t = np.arange(0, .04, .00002)
    onset, offset, amplitude, tau = .01, .02, -10., .0017
    # Rs=20 MOhm, Rm=180 MOhm, C=tau/(Rs||Rm).
    def circuit_current(time, start, stop, volts):
        rs, rm, capacitance = 20e6, 180e6, tau/(18e6)
        circuit_tau = capacitance/(1/rs+1/rm)
        vm = np.zeros_like(time)
        during = (time >= start) & (time < stop)
        after = time >= stop
        vm[during] = volts*rm/(rs+rm)*(1-np.exp(-(time[during]-start)/circuit_tau))
        v_end = volts*rm/(rs+rm)*(1-np.exp(-(stop-start)/circuit_tau))
        vm[after] = v_end*np.exp(-(time[after]-stop)/circuit_tau)
        return (volts*during-vm)/rs*1e12
    current = circuit_current(t, onset, offset, amplitude/1000)
    # Fit onset only. Offset and the second pulse are not fitting observations.
    mask = (t >= onset+.0002) & (t < offset-.0002)
    record = dict(time=t, onset=onset, offset=offset, amplitude_mV=amplitude, current=current, mask=mask)
    fit = model.fit_rc([record], {'tau_bounds_s':[.00005, .03], 'tau_grid_size':161})
    assert fit['train_rmse_pA'] < 1e-5
    np.testing.assert_allclose([fit['Ginf_nS'], fit['Gtrans_nS'], fit['tau_ms']], [5,45,1.7], rtol=1e-6)
    np.testing.assert_allclose([fit['conditional_effective_circuit']['Rs_MOhm'], fit['conditional_effective_circuit']['Rm_MOhm']], [20,180], rtol=1e-6)
    assert np.all(current[t < onset] == 0)
    assert current[np.searchsorted(t, offset)] > 0
    heldout = circuit_current(t, .012, .018, .005)
    prediction = model.pulse_basis(t, .012, .018, 5., fit['tau_ms']/1000) @ np.array([fit['Ginf_nS'],fit['Gtrans_nS']])
    np.testing.assert_allclose(prediction, heldout, atol=1e-5)


def test_same_metric_with_and_without_circulation():
    # A stronger ambiguity than reversing an already known circulation.
    k = 4*np.eye(3)-np.ones((3,3))
    d = .5*np.array([[0,1,-1],[-1,0,1],[1,-1,0]])
    h_inv = k-d@np.linalg.solve(k,d)
    passive = (67*np.eye(3)-17*np.ones((3,3)))/16
    np.testing.assert_allclose(h_inv, passive, atol=1e-14)
    assert np.linalg.eigvalsh(passive).min() > 0
    # Origin edges remain 1; other edges are 17/16, all strictly positive.
    np.testing.assert_allclose(passive.sum(axis=1), np.ones(3))
    assert np.linalg.norm(d) > 0


def test_common_mode_cannot_identify_connections():
    laplacian = 3*np.eye(3)-np.ones((3,3))
    membrane = np.diag([2.,3.,4.])
    common = np.ones(3)
    np.testing.assert_array_equal((membrane+laplacian)@common, membrane@common)
    assert not np.allclose((membrane+laplacian)@np.eye(3)[:,0], membrane@np.eye(3)[:,0])
