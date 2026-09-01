import tempfile
import unittest
from pathlib import Path

import numpy as np

import audit_npz_schema_headers as audit


class NpzSchemaHeaderTests(unittest.TestCase):
    def test_audit_records_keys_shapes_and_dtypes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            np.savez_compressed(
                root / "sample.npz",
                animal=np.arange(3, dtype=np.int32),
                response=np.zeros((2, 4), dtype=np.float64),
            )
            result = audit.audit_tree(root)
            self.assertEqual(result["status"], "NPZ_SCHEMA_HEADER_AUDIT_PASS")
            self.assertEqual(result["file_count"], 1)
            arrays = {item["key"]: item for item in result["files"][0]["arrays"]}
            self.assertEqual(arrays["animal"]["shape"], [3])
            self.assertEqual(arrays["animal"]["dtype"], "<i4")
            self.assertEqual(arrays["response"]["shape"], [2, 4])

    def test_empty_tree_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(audit.NpzSchemaError):
                audit.audit_tree(Path(temp))


if __name__ == "__main__":
    unittest.main()
