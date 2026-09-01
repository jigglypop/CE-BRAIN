import tempfile
import unittest
from pathlib import Path

import yaml

from audit_dandi_assets_manifest import audit_manifest


class AuditDandiAssetsManifestTest(unittest.TestCase):
    def _asset(self, path: str, subject: str, identifier: str = "id-1") -> dict:
        return {
            "path": path,
            "identifier": identifier,
            "contentSize": 123,
            "contentUrl": [f"https://example.test/{identifier}"],
            "digest": {"dandi:sha2-256": "a" * 64},
            "encodingFormat": "application/x-nwb",
            "wasAttributedTo": [
                {"schemaKey": "Participant", "identifier": subject}
            ],
        }

    def _write(self, root: Path, assets: list[dict]) -> Path:
        path = root / "assets.yaml"
        path.write_text(yaml.safe_dump(assets), encoding="utf-8")
        return path

    def test_selects_dense_endpoint_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = [
                self._asset(
                    "sub-Ctrl-1/sub-Ctrl-1_ses-ymaze-day0-scan0_behavior+ophys.nwb",
                    "Ctrl-1",
                    "id-1",
                ),
                self._asset(
                    "sub-Ctrl-1/sub-Ctrl-1_ses-ymaze-day3-scan0_behavior+ophys.nwb",
                    "Ctrl-1",
                    "id-2",
                ),
                self._asset(
                    "sub-Cre-1/sub-Cre-1_ses-ymaze-day5-scan0_behavior+ophys.nwb",
                    "Cre-1",
                    "id-3",
                ),
            ]
            result = audit_manifest(
                self._write(root, assets),
                include_patterns=[r"^sub-(?:Ctrl|Cre)-\d+/.+day(?:0|5)-"],
            )
            self.assertEqual(result["status"], "DANDI_ASSET_SELECTION_AUDIT_PASS")
            self.assertEqual(result["selected_assets_summary"]["asset_count"], 2)
            self.assertEqual(result["selected_assets_summary"]["subject_count"], 2)

    def test_participant_path_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = self._asset(
                "sub-Ctrl-1/sub-Ctrl-1_ses-ymaze-day0-scan0.nwb", "Cre-1"
            )
            result = audit_manifest(self._write(root, [asset]))
            self.assertEqual(result["status"], "DANDI_ASSET_SELECTION_AUDIT_FAIL")

    def test_provider_hyphen_underscore_subject_spellings_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = self._asset(
                "sub-Ctrl-1/sub-Ctrl-1_ses-ymaze-day0-scan0.nwb", "Ctrl_1"
            )
            result = audit_manifest(self._write(root, [asset]))
            self.assertEqual(result["status"], "DANDI_ASSET_SELECTION_AUDIT_PASS")
            self.assertEqual(result["all_assets"]["by_group"]["Ctrl"]["subjects"], ["Ctrl_1"])

    def test_duplicate_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = self._asset("sub-Ctrl-1/x.nwb", "Ctrl-1")
            with self.assertRaises(ValueError):
                audit_manifest(self._write(root, [asset, dict(asset)]))


if __name__ == "__main__":
    unittest.main()
