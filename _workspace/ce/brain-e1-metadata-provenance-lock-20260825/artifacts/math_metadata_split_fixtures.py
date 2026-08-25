"""Pure-Python adversarial fixtures for the E1 metadata provenance contract.

This is a mathematics/schema oracle, not an AllenSDK client: it performs no
network, file, NWB, unit, channel, probe, or signal access.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
import unicodedata

SALT = b"CE-E1-NEUROPIXELS-V1"
_DECIMAL_ID = re.compile(r"^(0|[1-9][0-9]*)$")
_RFC3339_UTC_OR_OFFSET = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$"
)
_NAIVE_ISO_LOCAL = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?$"
)
_REQUIRED = (
    "ecephys_session_id",
    "specimen_id",
    "session_type",
    "date_of_acquisition",
)


class SchemaError(ValueError):
    """Fail-closed diagnostic from the frozen apparatus."""


def canonical_decimal_id(value: object, *, field: str) -> str:
    """Dependency-free core admits only built-in int, excluding bool."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SchemaError(f"E1_FIELD_TYPE_INVALID:{field}")
    return str(value)


def canonical_utc(value: object) -> str:
    """Accept a strict RFC3339 instant and re-emit UTC at microseconds."""
    if not isinstance(value, str):
        raise SchemaError("E1_FIELD_TYPE_INVALID:date_of_acquisition")
    if _NAIVE_ISO_LOCAL.fullmatch(value):
        raise SchemaError("E1_TIMEZONE_UNRESOLVED")
    if not _RFC3339_UTC_OR_OFFSET.fullmatch(value):
        raise SchemaError("E1_FIELD_TYPE_INVALID:date_of_acquisition")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SchemaError("E1_FIELD_TYPE_INVALID:date_of_acquisition") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SchemaError("E1_TIMEZONE_UNRESOLVED")
    utc = parsed.astimezone(timezone.utc)
    return f"{utc:%Y-%m-%dT%H:%M:%S}.{utc.microsecond:06d}Z"


def canonical_session_type(value: object) -> str:
    """NFC-normalize a nonempty string and reject all Unicode control codes."""
    if not isinstance(value, str):
        raise SchemaError("E1_FIELD_TYPE_INVALID:session_type")
    normalized = unicodedata.normalize("NFC", value)
    if not normalized or any(unicodedata.category(char) == "Cc" for char in normalized):
        raise SchemaError("E1_FIELD_TYPE_INVALID:session_type")
    return normalized


def canonical_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Minimal deterministic core record; optional fields intentionally excluded."""
    if set(_REQUIRED) - set(row):
        raise SchemaError("E1_REQUIRED_FIELD_MISSING")
    return {
        "date_of_acquisition": canonical_utc(row["date_of_acquisition"]),
        "ecephys_session_id": canonical_decimal_id(
            row["ecephys_session_id"], field="ecephys_session_id"
        ),
        "session_type": canonical_session_type(row["session_type"]),
        "specimen_id": canonical_decimal_id(row["specimen_id"], field="specimen_id"),
    }


def canonical_records(rows: Iterable[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Deduplicate only byte-identical session rows; reject conflicting session IDs."""
    normalized = [canonical_row(row) for row in rows]
    by_session: dict[str, bytes] = {}
    for row in normalized:
        raw = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                         allow_nan=False).encode("utf-8")
        old = by_session.setdefault(row["ecephys_session_id"], raw)
        if old != raw:
            raise SchemaError("E1_INCONSISTENT_DUPLICATE_SESSION")
    return tuple(
        json.loads(by_session[session_id]) for session_id in sorted(by_session, key=int)
    )


def _canonical_lines(records: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                   allow_nan=False).encode("utf-8") + b"\n"
        for record in records
    )


def canonical_jsonl(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return _canonical_lines(canonical_records(rows))


def canonical_assignment_jsonl(rows: Iterable[Mapping[str, Any]]) -> bytes:
    """One assignment per canonical session, ordered by integer session identifier."""
    assignments = (
        {
            "ecephys_session_id": record["ecephys_session_id"],
            "specimen_id": record["specimen_id"],
            "split": specimen_split(int(record["specimen_id"])),
        }
        for record in canonical_records(rows)
    )
    return _canonical_lines(assignments)


def specimen_uint64(specimen_id: object) -> int:
    g = canonical_decimal_id(specimen_id, field="specimen_id").encode("ascii")
    return int.from_bytes(hashlib.sha256(SALT + b":" + g).digest()[:8], "big", signed=False)


def specimen_split(specimen_id: object) -> str:
    value = specimen_uint64(specimen_id)
    if value < 1 << 63:
        return "calibration"
    if value < 3 << 62:
        return "development"
    return "held_out"


def _expect_error(fn: object, status: str) -> None:
    try:
        fn()  # type: ignore[operator]
    except SchemaError as error:
        assert str(error).startswith(status), str(error)
    else:
        raise AssertionError(f"expected {status}")


def main() -> None:
    # The vectors distinguish byte order and exact thresholds without float arithmetic.
    vectors = {
        0: (7371522747307704441, "calibration"),
        2: (17843654490131864117, "held_out"),
        3: (12960670049301555441, "development"),
    }
    for specimen, (expected_uint64, expected_split) in vectors.items():
        assert specimen_uint64(specimen) == expected_uint64
        assert specimen_split(specimen) == expected_split
    assert specimen_split(0) == specimen_split(0)  # two-run split determinism

    row = {
        "ecephys_session_id": 11,
        "specimen_id": 3,
        "session_type": "brain_observatory_1.1",
        "date_of_acquisition": "2020-01-01T09:00:00+09:00",
    }
    earlier_row = {
        "ecephys_session_id": 3,
        "specimen_id": 2,
        "session_type": "A\u030a",  # NFC must become U+00C5.
        "date_of_acquisition": "2020-01-01T00:00:00Z",
    }
    first = canonical_jsonl([row, earlier_row])
    first_assignment = canonical_assignment_jsonl([row, earlier_row])
    second = canonical_jsonl([dict(reversed(list(row.items()))), earlier_row])
    second_assignment = canonical_assignment_jsonl([earlier_row, row])
    assert first == second
    assert first_assignment == second_assignment
    assert first.startswith(b'{"date_of_acquisition":"2020-01-01T00:00:00.000000Z",'
                           b'"ecephys_session_id":"3","session_type":"\xc3\x85",'
                           b'"specimen_id":"2"}\n')
    assert first.endswith(b'{"date_of_acquisition":"2020-01-01T00:00:00.000000Z",'
                     b'"ecephys_session_id":"11","session_type":"brain_observatory_1.1",'
                     b'"specimen_id":"3"}\n')
    assert first_assignment == (
        b'{"ecephys_session_id":"3","specimen_id":"2","split":"held_out"}\n'
        b'{"ecephys_session_id":"11","specimen_id":"3","split":"development"}\n'
    )
    assert hashlib.sha256(first).hexdigest() == "0a36c9339785d3bc785392a0663ba6a872cbda458c219b3b5005da5f1a71eb1e"
    assert hashlib.sha256(first_assignment).hexdigest() == "eb179eb8f33f14150c35395dc45e5415adc455bb40dd00c03feecbf53d2c3367"
    assert canonical_jsonl([row, dict(row), earlier_row]) == first
    assert canonical_assignment_jsonl([row, dict(row), earlier_row]) == first_assignment

    _expect_error(lambda: canonical_jsonl([{**row, "date_of_acquisition": "2020-01-01T09:00:00"}]), "E1_TIMEZONE_UNRESOLVED")
    _expect_error(lambda: canonical_jsonl([{**row, "date_of_acquisition": "2020-01-01 09:00:00+09:00"}]), "E1_FIELD_TYPE_INVALID")
    _expect_error(lambda: canonical_jsonl([{**row, "date_of_acquisition": "2020-01-01T09:00:00.1234567+09:00"}]), "E1_FIELD_TYPE_INVALID")
    _expect_error(lambda: canonical_jsonl([{**row, "specimen_id": True}]), "E1_FIELD_TYPE_INVALID")
    _expect_error(lambda: canonical_jsonl([{**row, "session_type": ""}]), "E1_FIELD_TYPE_INVALID")
    _expect_error(lambda: canonical_jsonl([row, {**row, "specimen_id": 4}]), "E1_INCONSISTENT_DUPLICATE_SESSION")
    _expect_error(lambda: canonical_jsonl([{key: value for key, value in row.items() if key != "specimen_id"}]), "E1_REQUIRED_FIELD_MISSING")
    _expect_error(lambda: canonical_decimal_id(-1, field="specimen_id"), "E1_FIELD_TYPE_INVALID")
    _expect_error(lambda: canonical_decimal_id(1.0, field="specimen_id"), "E1_FIELD_TYPE_INVALID")
    _expect_error(lambda: canonical_jsonl([{**row, "session_type": "valid\u0000invalid"}]), "E1_FIELD_TYPE_INVALID")
    print("PASS: E1 metadata canonicalization and specimen-split adversarial fixtures")


if __name__ == "__main__":
    main()
