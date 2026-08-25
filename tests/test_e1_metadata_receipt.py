from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "e1_metadata_receipt.py"


def _load_standalone_module():
    name = "ce_e1_metadata_receipt"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


receipt_core = _load_standalone_module()
build_local_metadata_receipt = receipt_core.build_local_metadata_receipt
E1MetadataReceiptError = receipt_core.E1MetadataReceiptError
canonical_utc_timestamp = receipt_core.canonical_utc_timestamp
canonical_decimal_id = receipt_core.canonical_decimal_id
canonical_session_type = receipt_core.canonical_session_type
specimen_split = receipt_core.specimen_split
specimen_uint64 = receipt_core.specimen_uint64


ROW = {
    "ecephys_session_id": 11,
    "specimen_id": 3,
    "session_type": "brain_observatory_1.1",
    "date_of_acquisition": "2020-01-01T09:00:00+09:00",
    "ignored_optional_source_column": ["not", "retained"],
}
EARLIER = {
    "ecephys_session_id": 3,
    "specimen_id": 2,
    "session_type": "A\u030a",
    "date_of_acquisition": "2020-01-01T00:00:00Z",
}


def test_fixed_vectors_and_integer_split_boundaries_are_deterministic() -> None:
    assert specimen_uint64(0) == 7371522747307704441
    assert specimen_uint64(2) == 17843654490131864117
    assert specimen_uint64(3) == 12960670049301555441
    assert specimen_split(0) == "calibration"
    assert specimen_split(2) == "held_out"
    assert specimen_split(3) == "development"


def test_receipt_has_only_four_core_fields_and_separate_deterministic_streams() -> None:
    first = build_local_metadata_receipt([ROW, EARLIER, dict(ROW)])
    second = build_local_metadata_receipt([EARLIER, dict(reversed(list(ROW.items()))), ROW])

    assert first == second
    assert first.status.accepted
    assert first.status.forbidden_resources_opened is False
    assert first.input_row_count == 3
    assert first.canonical_row_count == 2
    assert first.byte_identical_duplicate_count == 1
    assert first.specimen_count == 2
    assert first.split_counts == (("calibration", 0), ("development", 1), ("held_out", 1))
    assert first.canonical_table_jsonl == (
        b'{"date_of_acquisition":"2020-01-01T00:00:00.000000Z","ecephys_session_id":"3",'
        b'"session_type":"\xc3\x85","specimen_id":"2"}\n'
        b'{"date_of_acquisition":"2020-01-01T00:00:00.000000Z","ecephys_session_id":"11",'
        b'"session_type":"brain_observatory_1.1","specimen_id":"3"}\n'
    )
    assert first.assignment_jsonl == (
        b'{"ecephys_session_id":"3","specimen_id":"2","split":"held_out"}\n'
        b'{"ecephys_session_id":"11","specimen_id":"3","split":"development"}\n'
    )
    assert first.canonical_table_sha256 == "0a36c9339785d3bc785392a0663ba6a872cbda458c219b3b5005da5f1a71eb1e"
    assert first.assignment_sha256 == "eb179eb8f33f14150c35395dc45e5415adc455bb40dd00c03feecbf53d2c3367"
    assert b"ignored_optional_source_column" not in first.canonical_table_jsonl


@pytest.mark.parametrize(
    ("value", "field"),
    [(True, "specimen_id"), (1.0, "specimen_id"), (-1, "specimen_id"), ("1", "specimen_id")],
)
def test_ids_are_builtin_nonnegative_ints_only(value: object, field: str) -> None:
    with pytest.raises(E1MetadataReceiptError, match="E1_FIELD_TYPE_INVALID"):
        canonical_decimal_id(value, field=field)


@pytest.mark.parametrize(
    "value",
    ["", "ok\x00bad", "bad\ud800surrogate", 1, None],
)
def test_session_type_is_nfc_nonempty_control_free_and_utf8(value: object) -> None:
    if value == "":
        with pytest.raises(E1MetadataReceiptError, match="E1_FIELD_TYPE_INVALID"):
            canonical_session_type(value)
    elif isinstance(value, str):
        with pytest.raises(E1MetadataReceiptError, match="E1_FIELD_TYPE_INVALID"):
            canonical_session_type(value)
    else:
        with pytest.raises(E1MetadataReceiptError, match="E1_FIELD_TYPE_INVALID"):
            canonical_session_type(value)
    assert canonical_session_type("A\u030a") == "\u00c5"


@pytest.mark.parametrize(
    "value",
    [
        "2020-01-01T09:00:00",
        "2020-01-01 09:00:00+09:00",
        "2020-01-01T09:00:00.1234567+09:00",
        "2020-01-01T09:00:00+09",
        "2020-01-01T09:00:00EST",
    ],
)
def test_timestamps_fail_closed_without_strict_offset_rfc3339(value: str) -> None:
    expected = "E1_TIMEZONE_UNRESOLVED" if value == "2020-01-01T09:00:00" else "E1_FIELD_TYPE_INVALID"
    with pytest.raises(E1MetadataReceiptError, match=expected):
        canonical_utc_timestamp(value)
    assert canonical_utc_timestamp("2020-01-01T09:00:00.1+09:00") == "2020-01-01T00:00:00.100000Z"


def test_missing_field_and_conflicting_duplicate_fail_closed() -> None:
    with pytest.raises(E1MetadataReceiptError, match="E1_REQUIRED_FIELD_MISSING"):
        build_local_metadata_receipt([{key: value for key, value in ROW.items() if key != "specimen_id"}])
    with pytest.raises(E1MetadataReceiptError, match="E1_INCONSISTENT_DUPLICATE_SESSION"):
        build_local_metadata_receipt([ROW, {**ROW, "specimen_id": 4}])
    with pytest.raises(E1MetadataReceiptError, match="E1_INCONSISTENT_DUPLICATE_SESSION"):
        build_local_metadata_receipt([ROW, {**ROW, "session_type": "changed"}])


def test_empty_response_is_canonical_and_does_not_fake_a_split() -> None:
    receipt = build_local_metadata_receipt([])
    assert receipt.canonical_table_jsonl == b""
    assert receipt.assignment_jsonl == b""
    assert receipt.canonical_row_count == 0
    assert receipt.specimen_count == 0
    assert receipt.split_counts == (("calibration", 0), ("development", 0), ("held_out", 0))
