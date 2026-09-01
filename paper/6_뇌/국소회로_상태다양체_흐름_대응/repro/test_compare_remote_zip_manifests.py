import json
import tempfile
import unittest
from pathlib import Path

from compare_remote_zip_manifests import compare_manifests


class CompareRemoteZipManifestsTest(unittest.TestCase):
    def _write(self, root: Path, name: str, entries: list[dict]) -> Path:
        path = root / name
        path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
        return path

    @staticmethod
    def _entry(name: str, crc: int = 7) -> dict:
        return {
            "name": name,
            "compressed_size": 11,
            "uncompressed_size": 13,
            "crc32": crc,
            "compression_method": 8,
        }

    def test_wrapper_only_repackaging_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self._write(root, "old.json", [self._entry("a/x.npz")])
            new = self._write(
                root,
                "new.json",
                [self._entry("wrapper/"), self._entry("wrapper/a/x.npz")],
            )
            result = compare_manifests(new_path=new, old_path=old, new_strip_prefix="wrapper/")
            self.assertEqual(result["status"], "REMOTE_ZIP_MEMBER_IDENTITY_PASS")
            self.assertEqual(result["old_manifest"]["member_count"], 1)
            self.assertEqual(result["new_manifest"]["member_count"], 1)

    def test_crc_change_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self._write(root, "old.json", [self._entry("x.npz")])
            new = self._write(root, "new.json", [self._entry("x.npz", crc=8)])
            result = compare_manifests(old, new)
            self.assertEqual(result["status"], "REMOTE_ZIP_MEMBER_IDENTITY_FAIL")
            self.assertEqual(result["changed_count"], 1)

    def test_unmatched_member_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self._write(root, "old.json", [self._entry("old.npz")])
            new = self._write(root, "new.json", [self._entry("new.npz")])
            result = compare_manifests(old, new)
            self.assertEqual(result["only_old_count"], 1)
            self.assertEqual(result["only_new_count"], 1)


if __name__ == "__main__":
    unittest.main()
