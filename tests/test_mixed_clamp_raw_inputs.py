import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('mixed_clamp_raw_inputs',HERE/'mixed_clamp_raw_inputs.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    return [dict(device=d,kind=k,start=100.,rate=20000.,samples=1000,
        unit=('A' if d==1 else 'V') if k=='acquisition' else ('V' if d==1 else 'A'),electrode=f'electrode_{d}')
        for d in m.DEVICES for k in ('acquisition','command')]


def test_si_values_keep_physical_offset_and_scale():
    assert np.allclose(m.si_values(np.array([-1,0,2]),.001,-.07),[-.071,-.070,-.068],rtol=0,atol=1e-15)


@pytest.mark.parametrize('values,conversion,offset',[(np.array([np.nan]),1.,0.),(np.zeros((2,2)),1.,0.),(np.ones(2),0.,0.),(np.ones(2),1.,np.inf)])
def test_invalid_conversion_or_signal_rejected(values,conversion,offset):
    with pytest.raises(ValueError):m.si_values(values,conversion,offset)


@pytest.mark.parametrize('unit,scale',[('A',1e-10),('V',.01)])
def test_commands_preserve_test_pulse_and_final_run_in_si(unit,scale):
    rows=m.command_intervals(np.array([0,-1,-1,0,2,2,0,1])*scale,1000,unit)
    assert [(r['start_index'],r['stop_index']) for r in rows]==[(1,3),(4,6),(7,8)]
    assert rows[0]['delta_min']==pytest.approx(-scale,abs=scale*1e-12)
    assert rows[-1]['stop_s']==.008 and all(r['unit']==unit for r in rows)


def test_mixed_modes_and_common_clock_accepted():
    m.validate_records(fixture())


@pytest.mark.parametrize('change',['clock','unit','identity','duplicate'])
def test_unaligned_or_misbound_records_rejected(change):
    rows=fixture()
    if change=='clock':rows[0]['start']+=.0001
    elif change=='unit':rows[0]['unit']='A'
    elif change=='identity':rows[0]['electrode']='electrode_1'
    else:rows[-1]=rows[0].copy()
    with pytest.raises(ValueError):m.validate_records(rows)
