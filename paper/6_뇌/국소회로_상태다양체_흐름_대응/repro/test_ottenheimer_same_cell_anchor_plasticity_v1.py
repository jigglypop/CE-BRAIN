from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np


RUNNER_PATH = Path(__file__).with_name(
    "run_ottenheimer_same_cell_anchor_plasticity_v1.py"
)
SPEC = importlib.util.spec_from_file_location("ottenheimer_d7_runner", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {RUNNER_PATH}")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def stat_roi(x: list[int], y: list[int], med: tuple[float, float] | None = None):
    if med is None:
        med = (float(np.mean(y)), float(np.mean(x)))
    return SimpleNamespace(
        xpix=np.asarray(x, dtype=np.int64),
        ypix=np.asarray(y, dtype=np.int64),
        med=np.asarray(med, dtype=np.float64),
    )


class ProcessRoiTests(unittest.TestCase):
    def test_corrected_edge_removes_x_right_edge_missing_from_author_typo(self) -> None:
        stat = np.asarray(
            [
                stat_roi([511], [100]),
                stat_roi([100], [100]),
                stat_roi([200], [200]),
            ],
            dtype=object,
        )
        iscell = np.column_stack((np.ones(3), np.ones(3)))
        fluorescence = np.ones((3, 5), dtype=float)
        corrected, _ = RUNNER.process_roi_candidates(
            iscell,
            stat,
            fluorescence,
            corrected_edge=True,
            label="fixture/corrected",
        )
        author, _ = RUNNER.process_roi_candidates(
            iscell,
            stat,
            fluorescence,
            corrected_edge=False,
            label="fixture/author",
        )
        np.testing.assert_array_equal(corrected, np.array([1, 2]))
        np.testing.assert_array_equal(author, np.array([0, 1, 2]))

    def test_exact_full_overlap_order_rule_removes_first_three_duplicates(self) -> None:
        stat = np.asarray(
            [
                stat_roi([10, 11], [10, 10]),
                stat_roi([10, 11], [10, 10]),
                stat_roi([10, 11], [10, 10]),
                stat_roi([100], [100]),
                stat_roi([200], [200]),
            ],
            dtype=object,
        )
        iscell = np.column_stack((np.ones(5), np.ones(5)))
        fluorescence = np.ones((5, 5), dtype=float)
        retained, summary = RUNNER.process_roi_candidates(
            iscell,
            stat,
            fluorescence,
            corrected_edge=True,
            label="fixture/duplicates",
        )
        np.testing.assert_array_equal(retained, np.array([3, 4]))
        self.assertEqual(summary["full_overlap_entries"], 3)
        self.assertEqual(summary["duplicate_removed"], 3)


class RegistrationTests(unittest.TestCase):
    @staticmethod
    def candidate_stat() -> np.ndarray:
        return np.asarray(
            [
                stat_roi([0], [0], (0.0, 0.0)),
                stat_roi([20], [0], (0.0, 20.0)),
                stat_roi([40], [0], (0.0, 40.0)),
            ],
            dtype=object,
        )

    def test_collision_is_computed_before_distance_gate(self) -> None:
        track_xy = np.array([[0.0, 0.0], [0.5, 0.0], [40.0, 0.0]])
        result = RUNNER.match_manual_coordinates(
            track_xy,
            np.ones(3, dtype=bool),
            np.array([0, 1, 2]),
            self.candidate_stat(),
            label="fixture/collision",
            max_distance=0.1,
            min_margin=2.0,
        )
        np.testing.assert_array_equal(result.valid, np.array([False, False, True]))
        self.assertEqual(result.summary["collision_failures"], 2)

    def test_author_greedy_reroutes_collision_and_remains_one_to_one(self) -> None:
        track_xy = np.array([[0.0, 0.0], [0.5, 0.0], [40.0, 0.0]])
        result = RUNNER.match_author_greedy(
            track_xy,
            np.ones(3, dtype=bool),
            np.array([0, 1, 2]),
            self.candidate_stat(),
            label="fixture/greedy",
        )
        self.assertEqual(len(set(result.mapped_raw.tolist())), 3)
        self.assertGreaterEqual(result.summary["collision_loop_iterations"], 2)


class SmoothingTests(unittest.TestCase):
    def test_author_weights_use_linear_interpolation(self) -> None:
        weights = RUNNER.author_smoothing_weights()
        source_samples = np.arange(51, dtype=float)
        expected = np.interp(
            np.arange(16, dtype=float) / 15.0,
            source_samples * 0.02,
            np.exp(-0.5 * (source_samples / 15.0) ** 2),
        )
        np.testing.assert_array_equal(weights, expected)

    def test_smoothing_resets_at_segment_boundary(self) -> None:
        activity = np.array([[1.0, 1.0, 1.0, 10.0, 10.0]])
        segments = np.array([0, 0, 0, 1, 1])
        smoothed = RUNNER.causal_halfnormal(activity, segments)
        self.assertEqual(smoothed[0, 0], 1.0)
        self.assertEqual(smoothed[0, 3], 10.0)


class RankTests(unittest.TestCase):
    def test_normalized_midrank_all_tie_is_neutral(self) -> None:
        values = np.zeros(7)
        self.assertEqual(RUNNER.normalized_midrank(values, 3), 0.5)

    def test_unique_minimum_and_maximum_span_unit_interval(self) -> None:
        values = np.array([0.0, 1.0, 2.0])
        self.assertEqual(RUNNER.normalized_midrank(values, 0), 0.0)
        self.assertEqual(RUNNER.normalized_midrank(values, 2), 1.0)

    def test_zero_norm_cosine_rows_are_retained_as_zero(self) -> None:
        source = np.array([[0.0, 0.0], [1.0, 0.0]])
        target = np.array([[0.0, 0.0], [1.0, 0.0]])
        matrix, source_valid, target_valid = RUNNER.cosine_matrix(source, target)
        np.testing.assert_array_equal(source_valid, np.array([False, True]))
        np.testing.assert_array_equal(target_valid, np.array([False, True]))
        np.testing.assert_array_equal(matrix[0], np.zeros(2))
        np.testing.assert_array_equal(matrix[:, 0], np.zeros(2))

    def test_local_rank_uses_true_plus_five_neighbors(self) -> None:
        matrix = np.eye(6)
        xy = np.column_stack((np.arange(6, dtype=float), np.zeros(6)))
        advantage = RUNNER.local_directional_rank_advantage(matrix, xy)
        np.testing.assert_array_equal(advantage, np.full(6, 0.5))


class SignatureAndPlasticityTests(unittest.TestCase):
    @staticmethod
    def event(n_trials: int = 120) -> object:
        labels = np.resize(np.array([1, 2, 3], dtype=np.int8), n_trials)
        return RUNNER.EventData(
            frame_times=np.arange(1000, dtype=float) / 15.0,
            segment_ids=np.zeros(1000, dtype=np.int64),
            cue=np.arange(n_trials, dtype=float) + 2.0,
            cue_labels=labels,
            lick=np.array([], dtype=float),
        )

    def test_cue_centering_sums_to_zero_at_each_bin(self) -> None:
        labels = np.resize(np.array([1, 2, 3], dtype=np.int8), 12)
        responses = np.arange(2 * 12 * 3, dtype=float).reshape(2, 12, 3)
        signature = RUNNER.all_trial_signature(responses, labels, n_bins=3)
        reshaped = signature.reshape(2, 3, 3)
        np.testing.assert_allclose(np.sum(reshaped, axis=1), 0.0, atol=1e-12)

    def test_zero_plasticity_fold_norm_scores_zero_not_blocked(self) -> None:
        event = self.event()
        responses = {
            session: np.zeros((3, 120, RUNNER.PRIMARY_BINS), dtype=float)
            for session in RUNNER.SESSIONS
        }
        events = {session: event for session in RUNNER.SESSIONS}
        result = RUNNER.compute_mouse_plasticity(responses, events)
        self.assertEqual(result["P_zero"], 0.0)
        self.assertEqual(result["P_specific"], 0.0)

    def test_thirds_use_floor(self) -> None:
        early, late, minimum = RUNNER.phase_indices(145, "thirds")
        self.assertEqual(len(early), 48)
        self.assertEqual(len(late), 48)
        self.assertEqual(minimum, 5)

    def test_thirds_insufficient_fold_is_sensitivity_unavailable(self) -> None:
        event = self.event(n_trials=30)
        responses = {
            session: np.zeros((3, 30, RUNNER.PRIMARY_BINS), dtype=float)
            for session in RUNNER.SESSIONS
        }
        events = {session: event for session in RUNNER.SESSIONS}
        with self.assertRaises(RUNNER.SensitivityUnavailableError):
            RUNNER.compute_mouse_plasticity(
                responses,
                events,
                phase_mode="thirds",
                insufficient_is_unavailable=True,
            )


class BehaviorTests(unittest.TestCase):
    def test_behavior_reports_late_discrimination_and_change(self) -> None:
        labels = np.resize(np.array([1, 2, 3], dtype=np.int8), 120)
        cues = np.arange(120, dtype=float) * 10.0 + 5.0
        late_cs_plus = np.flatnonzero((np.arange(120) >= 60) & (labels == 1))
        licks = cues[late_cs_plus] + 1.0
        event = RUNNER.EventData(
            frame_times=np.arange(20_000, dtype=float) / 15.0,
            segment_ids=np.zeros(20_000, dtype=np.int64),
            cue=cues,
            cue_labels=labels,
            lick=licks,
        )
        result = RUNNER.compute_mouse_behavior(event)
        self.assertEqual(result["early_CSplus_minus_CSminus"], 0.0)
        self.assertEqual(result["late_CSplus_minus_CSminus"], 1.0)
        self.assertEqual(result["B"], 1.0)


class SourceLockTests(unittest.TestCase):
    @staticmethod
    def canonical_rows() -> dict[str, dict[str, str]]:
        return {
            role: {"path": str(path)}
            for role, path in RUNNER.canonical_lock_paths().items()
        }

    def test_a1_and_a2_are_separate_required_roles(self) -> None:
        self.assertIn("analysis_contract_amendment_a1", RUNNER.LOCK_ROLES)
        self.assertIn("analysis_contract_amendment_a2", RUNNER.LOCK_ROLES)
        self.assertNotIn("analysis_contract_amendment", RUNNER.LOCK_ROLES)
        rows = self.canonical_rows()
        del rows["analysis_contract_amendment_a2"]
        with self.assertRaises(RUNNER.ExecutionLockError):
            RUNNER.validate_lock_role_paths(rows)

    def test_runner_role_must_use_canonical_path(self) -> None:
        rows = self.canonical_rows()
        rows["analysis_runner"] = {"path": str(RUNNER.TEST_PATH)}
        with self.assertRaises(RUNNER.ExecutionLockError):
            RUNNER.validate_lock_role_paths(rows)


class ExactSignFlipTests(unittest.TestCase):
    def test_all_eight_positive_have_minimum_one_sided_p(self) -> None:
        result = RUNNER.exact_one_sided_signflip([1.0] * 8)
        self.assertEqual(result["total_assignments"], 256)
        self.assertEqual(result["tail_assignments"], 1)
        self.assertEqual(result["p_exact_one_sided"], 1 / 256)

    def test_zeros_are_retained(self) -> None:
        result = RUNNER.exact_one_sided_signflip([0.0] * 8)
        self.assertEqual(result["tail_assignments"], 256)
        self.assertEqual(result["p_exact_one_sided"], 1.0)
        self.assertEqual(result["positive_mice"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
