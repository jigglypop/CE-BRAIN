import io
import struct
import unittest
import zipfile

import audit_remote_zip_central_directory as audit


class RemoteZipCentralDirectoryTests(unittest.TestCase):
    def _archive(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README.txt", "schema only")
            archive.writestr("nested/data.csv", "animal,session\n1,2\n")
        return buffer.getvalue()

    def test_eocd_and_central_directory_parse(self):
        payload = self._archive()
        eocd_offset, fields = audit._find_eocd(payload, 0)
        self.assertGreater(eocd_offset, 0)
        cd_size = fields[4]
        cd_offset = fields[5]
        entries = audit.parse_central_directory(
            payload[cd_offset : cd_offset + cd_size], fields[3]
        )
        self.assertEqual([entry["name"] for entry in entries], ["README.txt", "nested/data.csv"])
        self.assertEqual(entries[0]["uncompressed_size"], len("schema only"))

    def test_eocd_rejects_trailing_bytes(self):
        with self.assertRaises(audit.ZipAuditError):
            audit._find_eocd(self._archive() + b"trailing", 0)

    def test_central_directory_rejects_wrong_entry_count(self):
        payload = self._archive()
        _, fields = audit._find_eocd(payload, 0)
        cd_size = fields[4]
        cd_offset = fields[5]
        with self.assertRaises(audit.ZipAuditError):
            audit.parse_central_directory(payload[cd_offset : cd_offset + cd_size], 3)

    def test_content_range_parser(self):
        self.assertEqual(audit._parse_total_size("bytes 0-0/6516027470"), 6516027470)
        with self.assertRaises(audit.ZipAuditError):
            audit._parse_total_size("bytes 0-0/*")

    def test_canonical_hash_is_order_sensitive(self):
        entries = [
            {"name": "a", "compressed_size": 1, "uncompressed_size": 2, "compression_method": 8, "crc32": "00000001", "local_header_offset": 0},
            {"name": "b", "compressed_size": 3, "uncompressed_size": 4, "compression_method": 8, "crc32": "00000002", "local_header_offset": 10},
        ]
        self.assertNotEqual(
            audit._canonical_entry_lines(entries),
            audit._canonical_entry_lines(reversed(entries)),
        )

    def test_zero_disk_count_locator_is_accepted_if_zip64_record_is_single_disk(self):
        total_size = 500
        zip64_offset = 100
        locator = struct.pack("<4sIQI", audit.ZIP64_LOCATOR_SIGNATURE, 0, zip64_offset, 0)
        eocd = struct.pack(
            "<4s4H2LH",
            audit.EOCD_SIGNATURE,
            0,
            0,
            0xFFFF,
            0xFFFF,
            0xFFFFFFFF,
            0xFFFFFFFF,
            0,
        )
        tail_start = total_size - len(locator) - len(eocd)
        tail = locator + eocd
        zip64_record = struct.pack(
            "<4sQ2H2L4Q",
            audit.ZIP64_EOCD_SIGNATURE,
            44,
            45,
            45,
            0,
            0,
            2,
            2,
            120,
            200,
        )
        original = audit._range_request
        audit._range_request = lambda url, start, end: (zip64_record, {})
        try:
            location = audit._directory_location("https://example.invalid/a.zip", total_size, tail, tail_start)
        finally:
            audit._range_request = original
        self.assertTrue(location.zip64)
        self.assertEqual((location.entry_count, location.offset, location.size), (2, 200, 120))


if __name__ == "__main__":
    unittest.main()
