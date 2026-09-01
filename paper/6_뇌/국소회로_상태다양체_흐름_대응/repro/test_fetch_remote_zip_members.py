import io
import json
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

import audit_remote_zip_central_directory as central
import fetch_remote_zip_members as fetch


class RemoteZipMemberTests(unittest.TestCase):
    def _archive_and_entries(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("group/a.txt", "alpha")
            archive.writestr("group/b.txt", "beta")
        payload = buffer.getvalue()
        _, fields = central._find_eocd(payload, 0)
        entries = central.parse_central_directory(
            payload[fields[5] : fields[5] + fields[4]], fields[3]
        )
        return payload, fields[5], entries

    def test_decode_member_checks_crc_and_size(self):
        payload, _, entries = self._archive_and_entries()
        self.assertEqual(fetch._decode_member(payload, 0, entries[0]), b"alpha")
        broken = bytearray(payload)
        entry = entries[0]
        cursor = int(entry["local_header_offset"])
        header = struct.unpack_from("<4s5H3L2H", broken, cursor)
        data_start = cursor + 30 + header[-2] + header[-1]
        broken[data_start] ^= 1
        with self.assertRaises((central.ZipAuditError, zlib.error)):
            fetch._decode_member(bytes(broken), 0, entry)

    def test_safe_destination_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(central.ZipAuditError):
                fetch._safe_destination(root, "../escape.txt")

    def test_adjacent_selected_records_are_coalesced(self):
        _, central_offset, entries = self._archive_and_entries()
        boundaries = fetch._record_boundaries(entries, central_offset)
        groups = fetch._coalesced_groups(entries, boundaries, 1024 * 1024)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 2)


if __name__ == "__main__":
    unittest.main()
