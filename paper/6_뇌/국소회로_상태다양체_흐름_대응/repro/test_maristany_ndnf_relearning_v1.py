from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


RUNNER_PATH = Path(__file__).with_name("run_maristany_ndnf_relearning_v1.py")
SPEC = importlib.util.spec_from_file_location("maristany_ndnf_runner", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {RUNNER_PATH}")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


class TerminalRunTests(unittest.TestCase):
    def test_normal_terminal_run_includes_first_new_rule_trial(self) -> None:
        observed = np.array([0, 0, 0, 2, 2, 2], dtype=int)
        self.assertEqual(RUNNER.terminal_new_run_start(observed, 0, 2), 3)

    def test_transient_new_marker_does_not_define_switch(self) -> None:
        observed = np.array([0, 0, 2, 0, 0, 2, 2, 2], dtype=int)
        self.assertEqual(RUNNER.terminal_new_run_start(observed, 0, 2), 5)

    def test_unexpected_relearn_code_blocks_schema(self) -> None:
        observed = np.array([0, 0, 7, 2, 2], dtype=int)
        with self.assertRaises(RUNNER.SchemaError):
            RUNNER.terminal_new_run_start(observed, 0, 2)

    def test_no_terminal_new_run_blocks_schema(self) -> None:
        observed = np.array([0, 0, 2, 2, 0], dtype=int)
        with self.assertRaises(RUNNER.SchemaError):
            RUNNER.terminal_new_run_start(observed, 0, 2)


class TrialSelectionTests(unittest.TestCase):
    @staticmethod
    def session() -> dict[str, np.ndarray]:
        n = 65
        relearn = np.array([0] * 5 + [2] * (n - 5), dtype=int)
        side = np.zeros(n, dtype=int)
        post_outcomes = np.resize(np.array([-1, 3, 0, 1], dtype=int), n - 5)
        outcomes = np.concatenate((np.ones(5, dtype=int), post_outcomes))
        dir_out = np.resize(np.array([0, 1, 3], dtype=int), n)
        return {
            "Relearn": relearn,
            "TrialTypes": np.column_stack((side, np.arange(n))),
            "Outcomes": np.column_stack((outcomes, np.arange(n))),
            "DirOut": dir_out,
        }

    def test_primary_and_sensitivity_use_distinct_locked_filters(self) -> None:
        stratum = RUNNER.validate_session(
            self.session(),
            mouse="synthetic",
            condition="Control",
            transition="A_to_B",
            old_rule=0,
            new_rule=2,
        )
        primary_outcomes = stratum.outcome[
            stratum.primary_eligible[: RUNNER.WINDOW_TRIALS]
        ]
        sensitivity_outcomes = stratum.outcome[
            stratum.sensitivity_eligible[: RUNNER.WINDOW_TRIALS]
        ]
        self.assertTrue(set(primary_outcomes.tolist()) <= {0, 1})
        self.assertNotIn(-1, sensitivity_outcomes.tolist())
        self.assertIn(3, sensitivity_outcomes.tolist())
        result = RUNNER.stratum_result(stratum)
        self.assertEqual(
            result["primary_error_count"], int(np.sum(1 - primary_outcomes))
        )
        self.assertEqual(
            result["sensitivity_error_count"],
            int(np.sum(sensitivity_outcomes != 1)),
        )

    def test_dirout_three_is_allowed_but_not_used_as_endpoint(self) -> None:
        stratum = RUNNER.validate_session(
            self.session(),
            mouse="synthetic",
            condition="Opto",
            transition="A_to_B",
            old_rule=0,
            new_rule=2,
        )
        result = RUNNER.stratum_result(stratum)
        self.assertTrue(
            any("dirout=3" in key for key in result["outcomes_dirout_crosstab_all_session_trials"])
        )
        expected = int(
            np.sum(
                1
                - stratum.outcome[
                    stratum.primary_eligible[: RUNNER.WINDOW_TRIALS]
                ]
            )
        )
        self.assertEqual(result["primary_error_count"], expected)

    def test_fewer_than_twenty_valid_trials_blocks_quality(self) -> None:
        session = self.session()
        session["Outcomes"][:, 0] = -1
        session["Outcomes"][:5, 0] = 1
        with self.assertRaises(RUNNER.QualityError):
            RUNNER.validate_session(
                session,
                mouse="synthetic",
                condition="Control",
                transition="A_to_B",
                old_rule=0,
                new_rule=2,
            )


class ExactTestTests(unittest.TestCase):
    def test_ten_strictly_positive_pairs_have_minimum_one_sided_p(self) -> None:
        result = RUNNER.exact_one_sided_signflip([1] * 10)
        self.assertEqual(result["tail_assignments"], 1)
        self.assertEqual(result["total_assignments"], 1024)
        self.assertEqual(result["p_exact_one_sided"], 1 / 1024)

    def test_zero_pairs_are_retained(self) -> None:
        result = RUNNER.exact_one_sided_signflip([0] * 10)
        self.assertEqual(result["tail_assignments"], 1024)
        self.assertEqual(result["p_exact_one_sided"], 1.0)


class DecisionTests(unittest.TestCase):
    @staticmethod
    def synthetic_stratum(
        mouse: str, condition: str, transition: str, error_count: int
    ) -> object:
        old_rule, new_rule = ((0, 2) if transition == "A_to_B" else (2, 0))
        switch = 5
        n = switch + RUNNER.WINDOW_TRIALS + 5
        outcome = np.ones(n, dtype=int)
        outcome[switch : switch + error_count] = 0
        relearn = np.array([old_rule] * switch + [new_rule] * (n - switch))
        eligible = np.arange(switch, n, dtype=np.int64)
        return RUNNER.Stratum(
            mouse=mouse,
            condition=condition,
            transition=transition,
            old_rule=old_rule,
            new_rule=new_rule,
            relearn=relearn,
            trial_side=np.zeros(n, dtype=int),
            outcome=outcome,
            dir_out=np.zeros(n, dtype=int),
            switch_index=switch,
            primary_eligible=eligible,
            sensitivity_eligible=eligible,
        )

    def test_all_positive_complexity_interactions_support_locked_decision(self) -> None:
        strata = []
        for mouse in RUNNER.MOUSE_IDS:
            for condition in RUNNER.CONDITIONS:
                for transition in RUNNER.TRANSITIONS:
                    errors = 1 if condition == "Opto" and transition == "B_to_Aprime" else 0
                    strata.append(
                        self.synthetic_stratum(mouse, condition, transition, errors)
                    )
        result = RUNNER.compute_endpoints(strata)
        self.assertEqual(
            result["status"],
            "D3_NDNF_COMPLEX_RELEARNING_SPECIFIC_IMPAIRMENT_SUPPORTED",
        )
        self.assertEqual(
            result["aggregate"]["signflip"]["p_exact_one_sided"], 1 / 1024
        )
        self.assertTrue(
            all(result["aggregate"]["decision_conditions"].values())
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
