from pathlib import Path

import h5py

from examples.brain.ce_brain_stage3d_dandi001612_apparatus import inspect_nwb


def _fixture(path: Path, *, complete: bool) -> None:
    with h5py.File(path, "w") as nwb:
        trace = nwb.create_group("processing/ophys/Fluorescence_FOV1_pln1_chn1/ROITrace")
        trace.create_dataset("data", shape=(20, 3), dtype="f4")
        presentation = nwb.create_group("stimulus/presentation")
        if complete:
            presentation.create_group("PhotostimulationSeries")
            nwb.create_group("intervals/trials")
            nwb.create_dataset("analysis/photostim_target_id", data=[1, 2])


def test_missing_target_and_timing_refuses_stage3(tmp_path: Path) -> None:
    path = tmp_path / "missing.nwb"
    _fixture(path, complete=False)
    result = inspect_nwb(path)
    assert result["receiver_rois"] == 3
    assert result["status"] == "STAGE3_DANDI001612_TARGET_TIMING_NOT_IDENTIFIABLE"


def test_complete_schema_is_eligible(tmp_path: Path) -> None:
    path = tmp_path / "complete.nwb"
    _fixture(path, complete=True)
    result = inspect_nwb(path)
    assert result["stimulus_series"] == ["PhotostimulationSeries"]
    assert result["status"] == "STAGE3_MULTISOURCE_APPARATUS_ELIGIBLE"
