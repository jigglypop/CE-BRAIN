import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("ds004080_metadata_audit.py")
SPEC = importlib.util.spec_from_file_location("ds004080_metadata_audit", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_git_blob_and_annex_pointer_identity():
    payload = (
        b"../../../.git/annex/objects/aa/bb/"
        b"SHA256E-s16--0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef.eeg/"
        b"SHA256E-s16--0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef.eeg"
    )
    parsed = mod.parse_annex_pointer(payload, "x.eeg")
    assert parsed["size"] == 16
    assert parsed["extension"] == "eeg"
    assert parsed["sha256"].startswith("01234567")
    assert mod.git_blob_sha(b"test") == "30d74d258442c7c65512eafab474568dd706c430"


def test_brainvision_header_requires_float32_multiplexed_geometry():
    payload = b"""Brain Vision Data Exchange Header File Version 1.0
[Common Infos]
DataFile=x.eeg
MarkerFile=x.vmrk
DataFormat=BINARY
DataOrientation=MULTIPLEXED
NumberOfChannels=2
SamplingInterval=488.28125
[Binary Infos]
BinaryFormat=IEEE_FLOAT_32
[Channel Infos]
Ch1=A,,1
Ch2=B,,0.5
"""
    parsed = mod.parse_brainvision_header(payload, "x.vhdr")
    assert parsed["number_of_channels"] == 2
    assert parsed["sampling_frequency_hz"] == 2048.0
    assert parsed["channels"][1]["resolution"] == 0.5


def test_site_and_interval_rules_are_fail_closed():
    assert mod.parse_site("A1-A2") == ("A1", "A2")
    assert mod.parse_site("A1") is None
    assert mod.parse_site("A1-A2-A3") is None
    assert mod.overlaps(-0.5, 0.12, -0.1, 0.1)
    assert not mod.overlaps(-0.5, -0.1, -0.1, 0.1)


def test_event_sample_start_is_zero_based_and_on_grid():
    anchor, delta = mod.event_anchor_zero(2881.783203125, 1_475_473, 512.0)
    assert anchor == 1_475_473
    assert delta == 0
    try:
        mod.event_anchor_zero(2881.783203125, 1_475_472, 512.0)
    except mod.AuditStop as error:
        assert "zero-based" in str(error)
    else:
        raise AssertionError("off-by-one sample_start must fail closed")


def test_bipolar_source_identity_is_orientation_invariant():
    assert tuple(sorted(mod.parse_site("A1-A2"))) == tuple(sorted(mod.parse_site("A2-A1")))


def test_canonical_json_is_order_independent():
    assert mod.canonical_bytes({"b": 2, "a": 1}) == mod.canonical_bytes({"a": 1, "b": 2})
