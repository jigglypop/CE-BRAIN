from __future__ import annotations
import importlib.util, sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_stage3a_worm_metric_r4.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric_r4", MODULE_PATH)
assert SPEC and SPEC.loader
r4 = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = r4; SPEC.loader.exec_module(r4)


def test_r4_freezes_all_revision_files() -> None:
    paths = r4.preregistered_files()
    assert len(paths) == 12
    assert all(path.is_file() for path in paths)
    assert r4.R3_PATH in paths and r4.CONTRACT in paths


def test_exploratory_validation_never_authorizes_stage4() -> None:
    score = r4.r3.base
    common = {"losses": {"N": 1., "R": .7, "F": 1., "S": 1., "O": 1.},
              "comparisons": {"R_vs_N": {"improvement": .3, "lower_95": .1},
                              "winner_vs_runner": {"better": "R", "improvement": .3, "lower_95": .1}},
              "ranking": ["R", "N"]}
    unseen = common
    axioms = {"symmetry": {}, "triangle": {"violation_upper_95": 0.},
              "directionality_F_vs_R": {"improvement": 0., "lower_95": -1.}}
    result = {"heldout_animal_common_pair": common, "heldout_source": unseen, "axioms": axioms,
              "candidate_decision": "RIEMANNIAN_LIKE_LOCAL_RETAINED",
              "decision": "EXPLORATORY_RIEMANNIAN_LIKE_LOCAL_RETAINED", "stage4_authorized": False}
    r4.validate_result(result)
