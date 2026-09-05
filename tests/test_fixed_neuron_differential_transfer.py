"""A nonsymmetric response distinguishes target/source orientation and input rank."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

SOURCE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/fixed_points_metric/allen_differential_transfer.py'
sys.path.insert(0,str(SOURCE.parent))
spec=importlib.util.spec_from_file_location('differential_transfer',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_directed_transfer_and_new_input():
    z=np.array([[100.,2.,-3.],[7.,80.,1.],[0.,-4.,150.]])
    u=np.array([[-20.,1.,0.],[0.,-15.,2.],[3.,0.,-30.]])
    fitted=module.estimate_transfer(u,z@u*1e-3)
    np.testing.assert_allclose(fitted,z,atol=1e-12)
    heldout=np.array([10.,-5.,7.])
    np.testing.assert_allclose(fitted@heldout*1e-3,z@heldout*1e-3)
    assert not np.allclose(z,z.T)


def test_rank_one_common_input_rejected():
    with pytest.raises(ValueError,match='does not identify'):
        module.estimate_transfer(np.ones((3,3)),np.eye(3))


def test_nonzero_unstimulated_command_is_not_crosscell_evidence():
    z=np.diag([100.,200.,150.])
    # Tiny changes in other command channels can drive their own membrane.
    u=np.diag([10.,-15.,12.])+.04*(np.ones((3,3))-np.eye(3))
    prediction=z@u*1e-3
    measured=prediction+.001
    full,diagonal,ratio=module.offdiagonal_errors(prediction,prediction,measured)
    assert ratio==1.
    assert full==diagonal
