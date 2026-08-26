from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R = _load("verified_rational_contour", "verified_rational_contour.py")
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
M = _load("ce_verified_rational_polygon", "verified_rational_polygon_residual.py")


SQUARE = ((-1, -1), (1, -1), (1, 1), (-1, 1))
REFINED_SQUARE = (
    (-1, -1),
    (F(-1, 2), -1),
    (0, -1),
    (F(1, 2), -1),
    (1, -1),
    (1, F(-1, 2)),
    (1, 0),
    (1, F(1, 2)),
    (1, 1),
    (F(1, 2), 1),
    (0, 1),
    (F(-1, 2), 1),
    (-1, 1),
    (-1, F(1, 2)),
    (-1, 0),
    (-1, F(-1, 2)),
)


def _construct(matrix=((0,),), vertices=SQUARE, *, scale=1):
    result = M.exact_polygon_nominal_inverse_witnesses(
        matrix,
        vertices=vertices,
        spectral_reference_scale=scale,
        sqrt_precision=48,
    )
    assert result.approximate_inverses is not None
    return result


def _verified(
    matrix=((0,),),
    vertices=SQUARE,
    uncertainty=(((0, 0),),),
    *,
    scale=1,
):
    construction = _construct(matrix, vertices, scale=scale)
    return M.verified_componentwise_residual_rational_polygon(
        matrix,
        uncertainty_radii=uncertainty,
        vertices=vertices,
        approximate_inverses=construction.approximate_inverses,
        spectral_reference_scale=scale,
        sqrt_precision=48,
    )


def test_square_is_an_exact_counterclockwise_jordan_polygon() -> None:
    polygon = M.verified_rational_jordan_polygon(SQUARE, sqrt_precision=48)
    assert polygon.signed_double_area == 8
    assert polygon.edge_squared_lengths == (4, 4, 4, 4)
    assert polygon.half_edge_length_uppers == (1, 1, 1, 1)
    assert polygon.perimeter_upper == 8
    assert polygon.nonadjacent_edge_pairs_checked == 2
    assert all(all(check) for check in polygon.length_sqrt_self_checks)


def test_square_residual_certifies_the_full_polygon_and_rank_preservation() -> None:
    result = _verified()
    assert result.validation_level == "VERIFIED_RATIONAL_POLYGON_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert result.rank_preserved_for_entire_family
    assert result.normalized_robust_delta_lower is not None
    assert result.normalized_robust_delta_lower > 0
    assert result.normalized_perimeter_upper == 8
    assert result.projector_prefactor_upper == F(4, 3)
    assert result.projector_perturbation_upper == 0


def test_forward_edge_refinement_closes_a_coarse_cover_failure() -> None:
    uncertainty = (((F(1, 2), 0),),)
    coarse = _verified(uncertainty=uncertainty)
    refined = _verified(vertices=REFINED_SQUARE, uncertainty=uncertainty)
    assert coarse.status == "VERIFIED_RATIONAL_POLYGON_RESIDUAL_EDGE_COVER_NONPOSITIVE"
    assert refined.validation_level == "VERIFIED_RATIONAL_POLYGON_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert refined.normalized_robust_delta_lower is not None
    assert refined.normalized_robust_delta_lower > 0
    assert max(refined.polygon.half_edge_length_uppers) == F(1, 4)
    assert len(refined.nodes) == 16


def test_concave_simple_polygon_is_admitted() -> None:
    polygon = M.verified_rational_jordan_polygon(
        ((0, 0), (2, 0), (2, 2), (1, 1), (0, 2)),
        sqrt_precision=48,
    )
    assert polygon.signed_double_area == 6
    assert polygon.nonadjacent_edge_pairs_checked == 5


@pytest.mark.parametrize(
    ("vertices", "message"),
    [
        (((0, 0), (1, 0)), "at least three"),
        (((0, 0), (1, 0), (0, 0)), "unique"),
        (((-1, -1), (-1, 1), (1, 1), (1, -1)), "counterclockwise"),
        (((0, 0), (2, 2), (0, 2), (2, 0)), "intersect"),
        (((0, 0), (2, 0), (2, 2), (1, 0), (0, 2)), "intersect"),
        (((0, 0), (2, 0), (1, 0), (1, 1)), "backtrack"),
        (((0.0, 0), (1, 0), (0, 1)), "canonical"),
    ],
)
def test_invalid_jordan_geometry_fails_closed(vertices: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        M.verified_rational_jordan_polygon(vertices, sqrt_precision=48)


def test_singular_vertex_witness_is_reported_separately() -> None:
    result = M.exact_polygon_nominal_inverse_witnesses(
        ((1,),),
        vertices=((1, 0), (2, 1), (0, 1)),
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert result.status == "EXACT_RATIONAL_POLYGON_NOMINAL_NODE_SINGULAR"
    assert result.validation_level is None
    assert result.failing_node_index == 0
    assert result.approximate_inverses is None


def test_witness_count_must_match_vertex_count() -> None:
    construction = _construct()
    with pytest.raises(ValueError, match="one matrix per polygon vertex"):
        M.verified_componentwise_residual_rational_polygon(
            ((0,),),
            uncertainty_radii=(((0, 0),),),
            vertices=SQUARE,
            approximate_inverses=construction.approximate_inverses[:-1],
            spectral_reference_scale=1,
            sqrt_precision=48,
        )


def test_inexact_witness_is_checked_by_the_residual_gate() -> None:
    construction = _construct(vertices=REFINED_SQUARE)
    inexact = tuple(
        tuple(tuple(entry * F(99, 100) for entry in row) for row in witness)
        for witness in construction.approximate_inverses
    )
    result = M.verified_componentwise_residual_rational_polygon(
        ((0,),),
        uncertainty_radii=(((0, 0),),),
        vertices=REFINED_SQUARE,
        approximate_inverses=inexact,
        spectral_reference_scale=1,
        sqrt_precision=48,
    )
    assert result.validation_level is not None
    assert all(node.residual != ((R.ZERO,),) for node in result.nodes)


def test_raw_spectral_rescaling_preserves_normalized_polygon_result() -> None:
    uncertainty = (((F(1, 2), 0),),)
    base = _verified(vertices=REFINED_SQUARE, uncertainty=uncertainty)
    scaled_vertices = tuple((7 * x, 7 * y) for x, y in REFINED_SQUARE)
    scaled = _verified(
        vertices=scaled_vertices,
        uncertainty=(((F(7, 2), 0),),),
        scale=7,
    )
    assert scaled.status == base.status
    assert scaled.nodes == base.nodes
    assert scaled.polygon == base.polygon
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower
    assert scaled.raw_perimeter_upper == 7 * base.raw_perimeter_upper


def test_provenance_and_rank_value_flags_remain_false() -> None:
    result = _verified()
    assert not result.empirical_matrix_provenance_verified
    assert not result.nominal_rank_value_supplied
