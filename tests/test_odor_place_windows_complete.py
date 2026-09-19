import importlib.util
from pathlib import Path
import pytest
PATH=Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/hippocampal_reinstatement/odor_place_windows_complete.py'
spec=importlib.util.spec_from_file_location('windows_complete',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_extend_only_newly_qualified_identity():
    assert m.extension_ids([{'asset_id':'a'}],[{'asset_id':'a'},{'asset_id':'b'}],
        [{'asset_id':'a','eligible':True},{'asset_id':'b','eligible':True}])=={'b'}


def test_duplicate_payloads_cannot_pass_as_cohort_coverage():
    with pytest.raises(ValueError):m.extension_ids([], [{'asset_id':'a'},{'asset_id':'a'}],[{'asset_id':'a','eligible':True}])


def test_missing_newly_qualified_session_fails():
    with pytest.raises(ValueError):m.extension_ids([{'asset_id':'a'}],[{'asset_id':'a'}],
        [{'asset_id':'a','eligible':True},{'asset_id':'b','eligible':True}])
