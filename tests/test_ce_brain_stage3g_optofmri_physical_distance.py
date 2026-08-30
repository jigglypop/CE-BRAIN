import numpy as np

from examples.brain.ce_brain_stage3f_optofmri_state_rdm import SITES
from examples.brain.ce_brain_stage3g_optofmri_physical_distance import (
    analyze,
    distance_vector,
    exact_source_permutation_p,
    left_source_labels,
    source_centroids,
)


def test_left_source_labels_match_author_files_and_si() -> None:
    labels = left_source_labels()
    assert labels["MOp"] == tuple(range(2018, 2024))
    assert labels["VISp"] == tuple(range(2185, 2192))
    assert labels["RSP"] == (*range(2298, 2304), *range(2325, 2332), *range(2332, 2339))
    assert labels["VISarl"] == (*range(2346, 2353), *range(2353, 2360))


def test_centroids_use_physical_not_array_coordinates() -> None:
    volume = np.zeros((20, 3, 3), dtype=np.int16)
    for index, site in enumerate(SITES):
        volume[2 * index, 1, 1] = left_source_labels()[site][0]
    centroids = source_centroids(
        volume,
        (2.0, 3.0, 4.0),
        (10.0, 20.0, 30.0),
        (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    )
    assert np.allclose(centroids[0], (10.0, 23.0, 34.0))
    assert np.allclose(distance_vector(centroids)[:5], (4.0, 8.0, 12.0, 16.0, 20.0))


def test_exact_source_permutation_recognizes_generic_perfect_geometry() -> None:
    centroids = np.array(
        [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 4], [3, 5, 1], [7, 2, 6]],
        dtype=float,
    )
    distances = distance_vector(centroids)
    p_value = exact_source_permutation_p(np.stack([distances] * 6), np.stack([distances] * 6))
    assert p_value <= 0.05


def test_analysis_requires_reliability_before_physical_claim() -> None:
    centroids = np.array(
        [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 4], [3, 5, 1], [7, 2, 6]],
        dtype=float,
    )
    distances = distance_vector(centroids)
    rows = []
    for genotype in ("Thy1", "VGAT"):
        for index in range(6):
            rows.append(
                {
                    "subject": f"{genotype}-{index}",
                    "genotype": genotype,
                    "repeat_reliability": 0.6 if genotype == "Thy1" else -0.1,
                    "physical_distance_rho": 0.8,
                    "physical_distance_rdm": distances.tolist(),
                    "cross_half_rdm": distances.tolist(),
                }
            )
    result = analyze(rows)
    assert result["gates"]["Thy1"]["passed"] is True
    assert result["gates"]["VGAT"]["passed"] is False
    assert result["status"] == "CONDITION_LIMITED_PHYSICAL_DISTANCE_CANDIDATE"
