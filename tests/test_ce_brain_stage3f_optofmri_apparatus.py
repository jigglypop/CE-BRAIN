import struct
from io import BytesIO

from examples.brain.ce_brain_stage3f_optofmri_apparatus import (
    BLOCK_HEADER_MAGIC,
    EGG_MAGIC,
    END_MAGIC,
    FILE_HEADER_MAGIC,
    FILENAME_HEADER_MAGIC,
    EXPECTED_SITES,
    audit_entries,
    scan_egg,
)


def _archive(paths: list[str]) -> bytes:
    data = bytearray(struct.pack("<IHII", EGG_MAGIC, 0x0100, 1, 0))
    data += struct.pack("<I", END_MAGIC)
    for index, path in enumerate(paths):
        payload = b"x"
        encoded = path.encode()
        data += struct.pack("<IIq", FILE_HEADER_MAGIC, index, len(payload))
        data += struct.pack("<IBH", FILENAME_HEADER_MAGIC, 0, len(encoded)) + encoded
        data += struct.pack("<I", END_MAGIC)
        data += struct.pack("<I", BLOCK_HEADER_MAGIC)
        data += struct.pack("<HIII", 0, 1, 1, 0)
        data += struct.pack("<I", END_MAGIC) + payload
    data += struct.pack("<I", END_MAGIC)
    return bytes(data)


def test_complete_two_cohort_six_run_schema_is_eligible() -> None:
    paths = []
    for genotype in ("Thy1", "VGAT"):
        for subject in range(1, 13):
            root = f"{genotype}-sub{subject:02d}"
            paths.append(f"{root}/anat/T2w.nii.gz")
            paths.extend(f"{root}/func_{site}/run.nii.gz" for site in EXPECTED_SITES)
    raw = _archive(paths)
    result = audit_entries(scan_egg(BytesIO(raw), len(raw)))
    assert result["genotype_subject_counts"] == {"Thy1": 12, "VGAT": 12}
    assert result["all_six_stimulation_sites_each"] is True
    assert result["status"] == "STAGE3_OPTOFMRI_APPARATUS_ELIGIBLE"


def test_missing_run_refuses_eligibility() -> None:
    raw = _archive(["Thy1-sub01/anat/T2w.nii.gz", "Thy1-sub01/func_1/run.nii.gz"])
    result = audit_entries(scan_egg(BytesIO(raw), len(raw)))
    assert result["status"] == "STAGE3_OPTOFMRI_APPARATUS_INCOMPLETE"
