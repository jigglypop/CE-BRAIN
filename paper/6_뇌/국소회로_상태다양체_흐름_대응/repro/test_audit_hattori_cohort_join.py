import json
import tempfile
import unittest
from pathlib import Path

from audit_hattori_cohort_join import audit_cohort_join


class AuditHattoriCohortJoinTest(unittest.TestCase):
    def _manifest(self, root: Path, names: list[str]) -> Path:
        path = root / "manifest.json"
        entries = [
            {"name": name, "uncompressed_size": index + 1}
            for index, name in enumerate(names)
        ]
        path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
        return path

    def test_disjoint_neural_and_intervention_ids_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._manifest(
                root,
                [
                    "wrap/Imaging/RH1/x.npz",
                    "wrap/Inactivation/group/RH2/x.npz",
                    "wrap/paAIP2/group/RH3/x.npz",
                ],
            )
            result = audit_cohort_join(path, wrapper_prefix="wrap/")
            self.assertEqual(result["l4_join_gate"], "FAIL_DISJOINT_COHORTS")
            self.assertEqual(result["neural_intervention_mouse_intersection"], [])

    def test_overlap_is_candidate_not_claimed_mediation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._manifest(
                root,
                [
                    "Imaging/RH1/x.npz",
                    "Inactivation/group/RH1/x.npz",
                    "paAIP2/group/RH3/x.npz",
                ],
            )
            result = audit_cohort_join(path)
            self.assertEqual(result["l4_join_gate"], "PASS_CANDIDATE")
            self.assertFalse(result["biological_endpoint_evaluated"])

    def test_directory_entries_are_not_counted_as_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._manifest(root, ["Imaging/RH1/", "Imaging/RH1/x.npz"])
            result = audit_cohort_join(path)
            self.assertEqual(result["cohorts"]["Imaging"]["file_count"], 1)


if __name__ == "__main__":
    unittest.main()
