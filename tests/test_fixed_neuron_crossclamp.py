"""Independent membrane ODE verifies IC units, compensation and pulse recovery."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

SOURCE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric/allen_crossclamp_prediction.py'
sys.path.insert(0,str(SOURCE.parent))
spec=importlib.util.spec_from_file_location('crossclamp_prediction',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_ic_prediction_against_membrane_ode():
    rs,rm,cm,bridge=20.,180.,100.,12.
    amplitude=-50.
    time=np.arange(0,.041,.0001)
    on,off=.01,.02
    vm=np.zeros(len(time))
    during=(time>=on)&(time<off);after=time>=off
    charge=solve_ivp(lambda t,v:(amplitude*1e-12-v/(rm*1e6))/(cm*1e-12),(on,off),[0.],dense_output=True,rtol=1e-10,atol=1e-13)
    vm[during]=charge.sol(time[during])[0]
    discharge=solve_ivp(lambda t,v:-v/(rm*1e6*cm*1e-12),(off,time[-1]),charge.y[:,-1],dense_output=True,rtol=1e-10,atol=1e-13)
    vm[after]=discharge.sol(time[after])[0]
    measured=vm*1000+during*amplitude*(rs-bridge)*1e-3
    prediction=module.ic_prediction(time,on,off,amplitude,rs,rm,cm,bridge)
    np.testing.assert_allclose(prediction,measured,atol=1e-8)
    uncompensated=module.ic_prediction(time,on,off,amplitude,rs,rm,cm,0.)
    np.testing.assert_allclose(prediction-uncompensated,during*(-amplitude)*bridge*1e-3,atol=1e-12)
