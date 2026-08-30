from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import h5py
import numpy as np


MODULE_PATH = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_stage3a_worm_metric_r2.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric_r2", MODULE_PATH)
assert SPEC and SPEC.loader
stage3a_r2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = stage3a_r2
SPEC.loader.exec_module(stage3a_r2)


def _minimal_file(path: Path, references: list[bytes]) -> None:
    with h5py.File(path, "w") as nwb:
        pump = nwb.create_group("processing/ophys/PumpProbeGreenSegmentations/PumpProbeGreenPlaneSegmentation")
        pump.create_dataset("id", data=np.arange(len(references)))
        pump.create_dataset("neuropal_ids", data=np.asarray(references))
        pump.create_dataset("centroids", data=np.arange(len(references) * 3).reshape(-1, 3))
        neuropal = nwb.create_group("processing/ophys/NeuroPALSegmentations/NeuroPALPlaneSegmentation")
        neuropal.create_dataset("labels", data=np.asarray([b"AVAL"]))


def test_collect_coordinates_skips_empty_canonical_subject(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "sub-76_ses-test_desc-segmentation_ophys+ogen.nwb"
    _minimal_file(path, [b"1124"])
    monkeypatch.setattr(stage3a_r2.base, "subject_development", lambda subject: True)
    assert stage3a_r2.collect_coordinates([path]) == {}


def test_r2_freezes_r1_and_amendment_files() -> None:
    paths = stage3a_r2.preregistered_files()
    assert len(paths) == 6
    assert all(path.is_file() for path in paths)
    assert stage3a_r2.BASE_PATH in paths
    assert stage3a_r2.CONTRACT in paths
