from pathlib import Path

import h5py

from examples.brain import ce_brain_stage9_da_schema as schema


def test_schema_ignores_extension_spec_but_finds_real_instance(tmp_path: Path):
    path = tmp_path / "fixture.nwb"
    with h5py.File(path, "w") as handle:
        handle.create_group("specifications/ndx-photometry")
        handle.create_group("acquisition/eventLog")
        handle.create_dataset("processing/photometry/dopamine/data", data=[1.0, 2.0])
    result = schema.schema(path)
    assert result["behavior_event_log"] is True
    assert "processing/photometry" in result["chemical_instance_paths"]


def test_schema_does_not_count_specification_as_measurement(tmp_path: Path):
    path = tmp_path / "fixture.nwb"
    with h5py.File(path, "w") as handle:
        handle.create_group("specifications/ndx-photometry")
        handle.create_group("acquisition/eventLog")
    assert schema.schema(path)["chemical_instance_paths"] == []
