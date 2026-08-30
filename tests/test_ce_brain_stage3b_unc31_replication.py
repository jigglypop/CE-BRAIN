from __future__ import annotations
import importlib.util, sys
from pathlib import Path
import numpy as np

P = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_stage3b_unc31_replication.py"
S = importlib.util.spec_from_file_location("stage3b", P); assert S and S.loader
m = importlib.util.module_from_spec(S); sys.modules[S.name] = m; S.loader.exec_module(m)


def test_run_length_gate_is_contiguous() -> None:
    mask = np.array([[1,1],[1,0],[1,1],[1,0],[0,1]], dtype=bool)
    assert np.array_equal(m.run_length_at_least(mask, 3), [True, False])


def test_positions_are_normalized(tmp_path: Path) -> None:
    path = tmp_path / "p.txt"; path.write_text("#A B C\n0 0 0\n1 2 3\n2 4 6\n")
    result = m.load_positions(path)
    assert set(result) == {"A", "B", "C"}
    assert np.allclose(result["B"], 0)


def _score(winner: str | None) -> dict:
    names = ("N", "R", "F", "S", "O")
    ranking = [winner, "N"] if winner else ["N", "R"]
    comparisons = {"winner_vs_runner": {"better": winner, "improvement": .1, "lower_95": .01}}
    if winner and winner != "N": comparisons[f"{winner}_vs_N"] = {"improvement": .1, "lower_95": .01}
    return {"ranking": ranking, "comparisons": comparisons, "losses": {name: 1. for name in names}}


def test_cross_decision_requires_same_winner() -> None:
    triangle = {"status": "IDENTIFIED", "violation_upper_95": .01}
    direction = {"lower_95": -.1}
    assert m.cross_decision(_score("F"), _score("O"), triangle, direction) == "CROSS_GENOTYPE_REPRESENTATION_TENSION"
    assert m.cross_decision(_score("F"), _score("F"), triangle, direction) == "CROSS_GENOTYPE_F_RETAINED"


def test_r_winner_requires_triangle_gate() -> None:
    direction = {"lower_95": -.1}
    assert m.cross_decision(_score("R"), _score("R"), {"status":"NOT_IDENTIFIABLE","violation_upper_95":1.}, direction).endswith("TENSION")
