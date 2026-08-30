from examples.brain.ce_brain_stage9_da_r6_causal_persistence import (
    analyze,
    animal_endpoints,
)


def _rows(effect: float) -> list[dict[str, object]]:
    layout = {0: (4, 2), 3: (1, 2), 5: (3, 2)}
    rows = []
    for cohort, (treated, controls) in layout.items():
        for group, count in (("chr2", treated), ("ctrl", controls)):
            for mouse in range(count):
                for session in (3, 4):
                    for repeat in range(2):
                        rows.append(
                            {
                                "mouse_id": f"{cohort}-{group}-{mouse}",
                                "cohort": cohort,
                                "target_syllable": repeat,
                                "syllable": repeat,
                                "stim_duration": 0.25,
                                "bin_start": 1770.0,
                                "bin_end": 1800.0,
                                "rle": False,
                                "area": "snc (axon)" if group == "chr2" else "ctrl",
                                "opsin": group,
                                "experiment_type": "reinforcement",
                                "session_number": session,
                                "change_usage": effect if group == "chr2" else 0.0,
                            }
                        )
    return rows


def test_collapses_repeated_sessions_to_animals() -> None:
    endpoints = animal_endpoints(_rows(0.2))
    assert len(endpoints) == 14
    assert sum(row["group"] == "chr2" for row in endpoints) == 8


def test_strong_persistent_effect_passes_locked_gate() -> None:
    result = analyze(_rows(0.2))
    assert result["permutations"] == 450
    assert result["primary_exact_p"] <= 0.01
    assert result["status"] == "DA_CAUSAL_PERSISTENCE_ESTABLISHED_DEVELOPMENT"


def test_null_effect_does_not_pass() -> None:
    result = analyze(_rows(0.0))
    assert result["primary_exact_p"] == 1.0
    assert result["status"] == "DA_CAUSAL_PERSISTENCE_NOT_ESTABLISHED"
