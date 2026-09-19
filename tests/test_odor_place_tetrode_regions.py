import importlib.util
from pathlib import Path
import pytest
PATH=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_tetrode_regions.py'
spec=importlib.util.spec_from_file_location('tetrode_regions',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_tetrode_number_does_not_use_duplicate_reference_row_index():
    assert m.map_tetrodes([2,1],['tetrode1','tetrode1','tetrode2','tetrode2'],['PFC','PFC','CA1','CA1'])==['CA1','PFC']


@pytest.mark.parametrize('raw,groups,areas',[
    ([0],['tetrode1'],['CA1']),([True],['tetrode1'],['CA1']),
    ([2],['tetrode1'],['CA1']),([1],['tetrode1','tetrode1'],['CA1','PFC']),
    ([1],['channel1'],['CA1'])])
def test_bad_or_ambiguous_mapping_is_rejected(raw,groups,areas):
    with pytest.raises(ValueError):m.map_tetrodes(raw,groups,areas)


def evidence():
    return dict(original_source_evidence=[dict(source_epoch=2,cellinfo=dict(areas={'CA1':3}),tetinfo=dict(areas={'CA1':1}))])


def test_every_source_epoch_requires_both_original_area_sources():
    assert m.source_verified(evidence(),'CA1',[2])
    assert not m.source_verified(evidence(),'CA1',[2,4])
    assert not m.source_verified(evidence(),'PFC',[2])
    data=evidence();data['original_source_evidence'][0]['cellinfo']=None
    assert not m.source_verified(data,'CA1',[2])


def test_task_unresolved_has_no_verified_source_epoch():
    assert not m.source_verified(dict(original_source_evidence=[]),'CA1',[])


def test_single_epoch_tetrode_axis_restoration_still_checks_original_area():
    row=dict(tetrode_count=32,tetrodes=[dict(tetrode=7,areas={'PFC':8})])
    supplement=dict(cs41_07=dict(cellinfo_day7_epoch1=row,tetinfo_day7_epoch1=row))
    restored=m.restored_single_epoch_evidence(supplement,7)
    assert m.source_verified(restored,'PFC',[1])
    assert not m.source_verified(restored,'CA1',[1])
    with pytest.raises(ValueError):m.restored_single_epoch_evidence(supplement,8)
