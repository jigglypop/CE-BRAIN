import hashlib

import pytest

from examples.brain import ce_brain_parallel_download as downloader


def test_byte_ranges_cover_exactly_once():
    ranges = downloader.byte_ranges(10, 4)
    assert ranges == [(0, 0, 3), (1, 4, 7), (2, 8, 9)]
    assert sum(end - start + 1 for _, start, end in ranges) == 10


def test_assemble_requires_and_verifies_all_parts(tmp_path):
    payload = b"abcdefghij"
    ranges = downloader.byte_ranges(len(payload), 4)
    parts = tmp_path / "parts"
    parts.mkdir()
    for index, start, end in ranges:
        downloader.part_path(parts, index).write_bytes(payload[start : end + 1])
    output = tmp_path / "out.bin"
    expected = hashlib.sha256(payload).hexdigest()
    assert downloader.assemble(parts, output, ranges, expected) == expected
    assert output.read_bytes() == payload


def test_assemble_rejects_wrong_hash(tmp_path):
    parts = tmp_path / "parts"
    parts.mkdir()
    downloader.part_path(parts, 0).write_bytes(b"abc")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        downloader.assemble(parts, tmp_path / "out.bin", [(0, 0, 2)], "0" * 64)


def test_assemble_supports_official_md5_receipts(tmp_path):
    parts = tmp_path / "parts"
    parts.mkdir()
    downloader.part_path(parts, 0).write_bytes(b"abc")
    expected = hashlib.md5(b"abc").hexdigest()
    assert downloader.assemble(parts, tmp_path / "out.bin", [(0, 0, 2)], expected, "md5") == expected
