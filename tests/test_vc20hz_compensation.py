import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('vc20hz_compensation', HERE/'vc20hz_compensation.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    keys = ['SweepNum', 'EntrySourceType', 'RsComp Enable']
    values = np.full((3, 3, 9), np.nan)
    values[:, 0, 0] = 0
    values[:, 1, 0] = [0, 0, 1]
    values[0, 2, 2] = 0
    values[2, 2, 2] = 1  # A TP entry must not overwrite acquisition settings.
    return keys, values


def test_numeric_acquisition_and_absent_comment_are_different_sources():
    keys, values = fixture()
    result = module.numeric_settings(keys, values, 0, 2, ['RsComp Enable'])
    assert result['RsComp Enable'] == dict(value=0., raw_row_indices=[0])
    assert module.comment_settings('', 2) == {}
    assert module.comment_settings('HS#2:RsComp Enable: Off\rHS#4:RsComp Enable: On', 2) == {'RsComp Enable': 'Off'}


def test_unknown_entry_type_and_conflicting_acquisition_settings_rejected():
    keys, values = fixture()
    values[1, 1, 0] = np.nan
    with pytest.raises(ValueError, match='EntrySourceType'):
        module.numeric_settings(keys, values, 0, 2, ['RsComp Enable'])
    values[1, 1, 0] = 0
    values[1, 2, 2] = 1
    with pytest.raises(ValueError, match='Conflicting'):
        module.numeric_settings(keys, values, 0, 2, ['RsComp Enable'])


def test_global_column_has_priority_without_inventing_missing_values():
    keys, values = fixture()
    values[0, 2, 8] = 1
    result = module.numeric_settings(keys, values, 0, 2, ['RsComp Enable', 'Absent field'])
    assert result['RsComp Enable']['value'] == 1.
    assert result['Absent field']['value'] is None
