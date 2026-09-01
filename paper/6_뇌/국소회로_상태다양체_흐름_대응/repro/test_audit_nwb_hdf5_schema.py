from pathlib import Path

import h5py
import numpy as np

from audit_nwb_hdf5_schema import (
    ALIGNED_SIGNALS,
    FULL_RES_SIGNALS,
    audit_nwb_schema,
    file_sha256,
)


def _make_nwb(path: Path, *, aligned_length: int = 5) -> None:
    with h5py.File(path, "w") as nwb:
        nwb.create_dataset("general/subject/subject_id", data=np.bytes_("Ctrl_2"))
        nwb.create_dataset("processing/ophys/dF/dF/data", shape=(5, 3), dtype="f8")
        nwb.create_dataset(
            "processing/ophys/fluorescence/fluorescence/data", shape=(5, 3), dtype="f4"
        )
        nwb.create_dataset(
            "processing/ophys/neuropil/neuropil fluorescence/data",
            shape=(5, 3),
            dtype="f4",
        )
        nwb.create_dataset(
            "processing/ophys/ImageSegmentation/PlaneSegmentation/id",
            data=np.arange(3),
        )
        for signal in ALIGNED_SIGNALS:
            prefix = f"processing/behavior/2P-aligned behavior/{signal}"
            nwb.create_dataset(f"{prefix}/data", shape=(aligned_length,), dtype="f8")
            nwb.create_dataset(f"{prefix}/timestamps", shape=(aligned_length,), dtype="f8")
        for signal in FULL_RES_SIGNALS:
            prefix = f"processing/behavior/Full temporal resolution behavior/{signal}"
            nwb.create_dataset(f"{prefix}/data", shape=(8,), dtype="f8")
            nwb.create_dataset(f"{prefix}/timestamps", shape=(8,), dtype="f8")


def test_valid_schema_passes(tmp_path: Path) -> None:
    path = tmp_path / "sub-Ctrl-2_ses-ymaze-day0-scan0-novel-arm1_behavior+ophys.nwb"
    _make_nwb(path)
    result = audit_nwb_schema(path, expected_sha256=file_sha256(path))
    assert result["status"] == "NWB_SCHEMA_AUDIT_PASS"
    assert result["identity"] == {
        "subject_id": "Ctrl_2",
        "path_subject": "Ctrl-2",
        "path_day": 0,
    }
    assert result["biological_endpoint_evaluated"] is False


def test_bad_aligned_length_fails(tmp_path: Path) -> None:
    path = tmp_path / "sub-Ctrl-2_ses-ymaze-day0-scan0-novel-arm1_behavior+ophys.nwb"
    _make_nwb(path, aligned_length=4)
    result = audit_nwb_schema(path)
    assert result["status"] == "NWB_SCHEMA_AUDIT_FAIL"
    assert any("neural frame count" in error for error in result["errors"])


def test_bad_hash_fails(tmp_path: Path) -> None:
    path = tmp_path / "sub-Ctrl-2_ses-ymaze-day0-scan0-novel-arm1_behavior+ophys.nwb"
    _make_nwb(path)
    result = audit_nwb_schema(path, expected_sha256="0" * 64)
    assert result["status"] == "NWB_SCHEMA_AUDIT_FAIL"
    assert any("sha256 mismatch" in error for error in result["errors"])
