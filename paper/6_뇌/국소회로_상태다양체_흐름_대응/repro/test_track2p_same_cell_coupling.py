from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("run_track2p_same_cell_coupling.py")
SPEC = importlib.util.spec_from_file_location("track2p_analysis", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Track2pAnalysisTests(unittest.TestCase):
    def test_restore_motion_inserts_nan_at_timestamp_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            move = session / "move_deve"
            move.mkdir()
            timestamps = np.concatenate((np.arange(11.0), np.arange(12.0, 21.0)))
            motion = timestamps * 10.0
            np.save(move / "motion_energy_glob.npy", motion)
            np.save(move / "tstamps.npy", timestamps)
            np.save(move / "interframe_int.npy", np.diff(timestamps))
            restored, receipt = MODULE.restore_motion(session, 21)
            expected = np.arange(21.0) * 10.0
            expected[11] = np.nan
            np.testing.assert_equal(restored, expected)
            self.assertEqual(receipt["missing_positions"], [11])

    def test_effect_subtracts_within_day_noise(self) -> None:
        betas = np.array(
            [
                [0.10, 0.12, 0.50, 0.52],
                [0.20, 0.22, 0.60, 0.62],
            ]
        )
        effect = MODULE.effect_from_betas(betas)
        self.assertAlmostEqual(effect["D_day_change"], 0.40)
        self.assertAlmostEqual(effect["N_split_half_noise"], 0.02)
        self.assertAlmostEqual(effect["E_change_minus_noise"], 0.38)

    def test_exact_sign_tail(self) -> None:
        self.assertEqual(MODULE.exact_one_sided_sign_p(6, 6), 1 / 64)
        self.assertEqual(MODULE.exact_one_sided_sign_p(5, 6), 7 / 64)


if __name__ == "__main__":
    unittest.main()
