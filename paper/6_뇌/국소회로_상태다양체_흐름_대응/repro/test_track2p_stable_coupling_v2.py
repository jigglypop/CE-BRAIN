from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from scipy.stats import spearmanr


SCRIPT = Path(__file__).with_name("run_track2p_stable_coupling_v2.py")
SPEC = importlib.util.spec_from_file_location("track2p_v2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Track2pStableCouplingV2Tests(unittest.TestCase):
    def test_source_gate_blocks_same_size_crc_damage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "selected"
            root.mkdir()
            source = root / "member.bin"
            source.write_bytes(b"abcd")
            expected_crc32, expected_size = MODULE.crc32_and_size(source)
            source.write_bytes(b"abce")
            with mock.patch.object(
                MODULE,
                "selected_manifest_entries",
                return_value={"member.bin": (expected_size, expected_crc32)},
            ):
                with self.assertRaises(MODULE.SourceError):
                    MODULE.verify_source_layout(Path(temporary) / "manifest.json", root)

    def test_restore_motion_inserts_only_timestamp_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            move = session / "move_deve"
            move.mkdir()
            timestamps = np.concatenate((np.arange(11.0), np.arange(12.0, 21.0)))
            motion = timestamps * 10.0
            motion[4] = np.nan
            np.save(move / "motion_energy_glob.npy", motion)
            np.save(move / "tstamps.npy", timestamps)
            np.save(move / "interframe_int.npy", np.diff(timestamps))
            restored, receipt = MODULE.restore_motion(session, 21)
            self.assertTrue(np.isnan(restored[4]))
            self.assertTrue(np.isnan(restored[11]))
            self.assertEqual(receipt["missing_positions"], [11])

    def test_endpoint_thirds_keep_middle_as_guard(self) -> None:
        first, guard, last = MODULE.endpoint_thirds(12)
        values = np.arange(12)
        np.testing.assert_array_equal(values[first], [0, 1, 2, 3])
        np.testing.assert_array_equal(values[guard], [4, 5, 6, 7])
        np.testing.assert_array_equal(values[last], [8, 9, 10, 11])

    def test_spearman_matches_scipy_with_ties(self) -> None:
        motion = np.array([0.0, 1.0, 1.0, 3.0, 4.0])
        activity = np.array(
            [[5.0, 4.0, 4.0, 2.0, 1.0], [0.0, 1.0, 2.0, 3.0, 5.0]]
        )
        actual = MODULE.spearman_per_cell(activity, motion)
        expected = np.array([spearmanr(row, motion).statistic for row in activity])
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-15)

    def test_coupling_metrics(self) -> None:
        betas = np.array(
            [
                [0.10, 0.20, 0.50, 0.60],
                [-0.20, -0.10, -0.40, -0.30],
            ]
        )
        metrics = MODULE.coupling_metrics(betas)
        self.assertAlmostEqual(metrics["Q_first"], 0.02)
        self.assertAlmostEqual(metrics["Q_last"], 0.21)
        self.assertAlmostEqual(metrics["G_last_minus_first"], 0.19)
        self.assertAlmostEqual(
            metrics["R_crossvalidated_reorganization_descriptive"], 0.10
        )

    def test_exact_sign_tail(self) -> None:
        self.assertEqual(MODULE.exact_one_sided_sign_p(6, 6), 1 / 64)
        self.assertEqual(MODULE.exact_one_sided_sign_p(5, 6), 7 / 64)

    def test_preflight_never_calls_spearman_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "selected"
            root.mkdir()
            argv = [
                str(SCRIPT),
                "--manifest",
                str(Path(temporary) / "manifest.json"),
                "--selected-root",
                str(root),
                "--mode",
                "preflight",
            ]
            subject_receipt = {"subject": "synthetic"}
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(MODULE, "verify_source_layout", return_value={}),
                mock.patch.object(
                    MODULE,
                    "prepare_subject",
                    return_value=(np.array([0]), [], subject_receipt),
                ) as prepare,
                mock.patch.object(MODULE, "spearman_per_cell") as spearman,
                contextlib.redirect_stdout(io.StringIO()) as output,
            ):
                self.assertEqual(MODULE.main(), 0)
            self.assertEqual(prepare.call_count, len(MODULE.EXPECTED_SESSIONS))
            spearman.assert_not_called()
            self.assertEqual(json.loads(output.getvalue())["decision"], "D1_PREFLIGHT_PASS")

    def test_any_mouse_preflight_failure_blocks_all_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "selected"
            root.mkdir()
            argv = [
                str(SCRIPT),
                "--manifest",
                str(Path(temporary) / "manifest.json"),
                "--selected-root",
                str(root),
                "--mode",
                "endpoint",
            ]
            calls = 0

            def prepare_with_one_failure(*_args: object) -> tuple[object, object, object]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise MODULE.QualityError("synthetic all-mouse gate failure")
                return np.array([0]), [], {"subject": "synthetic"}

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(MODULE, "verify_source_layout", return_value={}),
                mock.patch.object(
                    MODULE, "prepare_subject", side_effect=prepare_with_one_failure
                ) as prepare,
                mock.patch.object(MODULE, "compute_subject") as endpoint,
                mock.patch.object(MODULE, "spearman_per_cell") as spearman,
                contextlib.redirect_stdout(io.StringIO()) as output,
            ):
                self.assertEqual(MODULE.main(), 1)
            self.assertEqual(prepare.call_count, len(MODULE.EXPECTED_SESSIONS))
            endpoint.assert_not_called()
            spearman.assert_not_called()
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["decision"], "D1_BLOCKED_QUALITY")
            self.assertNotIn("inference", receipt)
            self.assertNotIn("metrics", output.getvalue())


if __name__ == "__main__":
    unittest.main()
