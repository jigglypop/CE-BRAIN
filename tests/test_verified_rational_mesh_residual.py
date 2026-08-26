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
V = _load("verified_interval_residual", "verified_interval_residual.py")
M = _load("ce_verified_rational_mesh_residual", "verified_rational_mesh_residual.py")


CARDINAL = ((1, 0), (0, 1), (-1, 0), (0, -1))
RATIONAL_EIGHT = (
    (1, 0),
    (F(3, 5), F(4, 5)),
    (0, 1),
    (F(-3, 5), F(4, 5)),
    (-1, 0),
    (F(-3, 5), F(-4, 5)),
    (0, -1),
    (F(3, 5), F(-4, 5)),
)


def _constructed(matrix, directions=CARDINAL, *, radius=1, scale=1):
    result = M.exact_mesh_nominal_inverse_witnesses(
        matrix,
        directions=directions,
        center=0,
        radius=radius,
        spectral_reference_scale=scale,
        sqrt_precision=40,
    )
    assert result.approximate_inverses is not None
    return result


def _verified(matrix=((0,),), directions=CARDINAL, uncertainty=(((0, 0),),), **overrides):
    construction = _constructed(
        matrix,
        directions,
        radius=overrides.get("radius", 1),
        scale=overrides.get("spectral_reference_scale", 1),
    )
    values = dict(
        nominal_transition=matrix,
        uncertainty_radii=uncertainty,
        directions=directions,
        approximate_inverses=construction.approximate_inverses,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    values.update(overrides)
    return M.verified_componentwise_residual_rational_mesh_circle(**values)


def test_cardinal_mesh_exactly_reproduces_four_node_residual_gate() -> None:
    matrix = ((0, 0), (0, 10))
    uncertainty = (((0, 0), (0, 0)), ((0, 0), (1, 0)))
    construction = _constructed(matrix)
    mesh = _verified(matrix, uncertainty=uncertainty)
    legacy = V.verified_componentwise_residual_circle(
        matrix,
        uncertainty_radii=uncertainty,
        approximate_inverses=construction.approximate_inverses,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert mesh.nodes == legacy.nodes
    assert mesh.normalized_chord_upper == legacy.normalized_chord_upper
    assert mesh.normalized_robust_delta_lower == legacy.normalized_robust_delta_lower
    assert mesh.raw_robust_resolvent_upper == legacy.raw_robust_resolvent_upper
    assert mesh.projector_perturbation_upper == legacy.projector_perturbation_upper


def test_eight_node_rational_mesh_closes_a_four_node_chord_failure() -> None:
    uncertainty = (((F(1, 2), 0),),)
    four = _verified(uncertainty=uncertainty)
    eight = _verified(directions=RATIONAL_EIGHT, uncertainty=uncertainty)
    assert four.status == "VERIFIED_RATIONAL_MESH_RESIDUAL_FULL_CIRCLE_LOWER_NONPOSITIVE"
    assert eight.validation_level == "VERIFIED_RATIONAL_MESH_COMPONENTWISE_RESIDUAL_CONTOUR_BRIDGE"
    assert eight.normalized_chord_upper < four.normalized_chord_upper
    assert eight.normalized_robust_delta_lower is not None
    assert eight.normalized_robust_delta_lower > 0
    assert len(eight.nodes) == 8


def test_mesh_records_exact_oriented_gaps_and_outward_chords() -> None:
    mesh = M.verified_rational_unit_circle_mesh(RATIONAL_EIGHT, sqrt_precision=40)
    assert len(mesh.directions) == 8
    assert all(cross > 0 for cross in mesh.consecutive_cross_products)
    assert max(mesh.consecutive_dot_products) < 1
    assert all(all(checks) for checks in mesh.gap_sqrt_self_checks)
    assert mesh.maximum_chord_factor_upper == max(
        upper for _, upper in mesh.gap_chord_factor_brackets
    )


def test_half_circle_gap_is_admitted_but_is_conservatively_large() -> None:
    mesh = M.verified_rational_unit_circle_mesh(
        ((1, 0), (-1, 0), (0, -1)), sqrt_precision=40
    )
    assert 0 in mesh.consecutive_cross_products
    assert -1 in mesh.consecutive_dot_products
    assert mesh.maximum_chord_factor_upper > 1


@pytest.mark.parametrize(
    "directions",
    [
        ((1, 0), (0, 1)),
        ((1, 0), (0, 1), (F(-1, 2), 0)),
        ((1, 0), (0, 1), (1, 0)),
        ((1, 0), (0, -1), (-1, 0)),
        ((1.0, 0), (0, 1), (-1, 0)),
    ],
)
def test_invalid_or_unordered_meshes_fail_closed(directions: object) -> None:
    with pytest.raises(ValueError):
        M.verified_rational_unit_circle_mesh(directions, sqrt_precision=40)


def test_multiple_counterclockwise_windings_are_rejected() -> None:
    order = (0, 3, 6, 1, 4, 7, 2, 5)
    multiple_winding = tuple(RATIONAL_EIGHT[index] for index in order)
    with pytest.raises(ValueError, match="exactly one"):
        M.verified_rational_unit_circle_mesh(multiple_winding, sqrt_precision=40)


def test_exact_mesh_witness_constructor_separates_singular_node_failure() -> None:
    result = M.exact_mesh_nominal_inverse_witnesses(
        ((1,),),
        directions=CARDINAL,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert result.status == "EXACT_RATIONAL_MESH_NOMINAL_NODE_SINGULAR"
    assert result.validation_level is None
    assert result.failing_node_index == 0
    assert result.approximate_inverses is None


def test_witness_count_must_equal_mesh_size() -> None:
    construction = _constructed(((0,),))
    with pytest.raises(ValueError, match="one matrix per mesh direction"):
        M.verified_componentwise_residual_rational_mesh_circle(
            ((0,),),
            uncertainty_radii=(((0, 0),),),
            directions=CARDINAL,
            approximate_inverses=construction.approximate_inverses[:-1],
            center=0,
            radius=1,
            spectral_reference_scale=1,
            sqrt_precision=40,
        )


def test_inexact_mesh_witness_is_checked_not_trusted() -> None:
    construction = _constructed(((0,),), RATIONAL_EIGHT)
    inexact = tuple(
        tuple(tuple(entry * F(99, 100) for entry in row) for row in witness)
        for witness in construction.approximate_inverses
    )
    result = M.verified_componentwise_residual_rational_mesh_circle(
        ((0,),),
        uncertainty_radii=(((0, 0),),),
        directions=RATIONAL_EIGHT,
        approximate_inverses=inexact,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        sqrt_precision=40,
    )
    assert result.validation_level is not None
    assert all(node.residual != ((R.ZERO,),) for node in result.nodes)


def test_raw_spectral_rescaling_preserves_normalized_mesh_result() -> None:
    base = _verified(directions=RATIONAL_EIGHT, uncertainty=(((F(1, 2), 0),),))
    scaled = _verified(
        matrix=((0,),),
        directions=RATIONAL_EIGHT,
        uncertainty=(((F(7, 2), 0),),),
        radius=7,
        spectral_reference_scale=7,
    )
    assert scaled.status == base.status
    assert scaled.nodes == base.nodes
    assert scaled.normalized_chord_upper == base.normalized_chord_upper
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower


def test_empirical_provenance_remains_false() -> None:
    assert not _verified().empirical_matrix_provenance_verified
