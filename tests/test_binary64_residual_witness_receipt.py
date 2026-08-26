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


_load("verified_rational_contour", "verified_rational_contour.py")
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
M = _load("ce_binary64_residual_witness_receipt", "binary64_residual_witness_receipt.py")


ZERO = "0000000000000000"
NEG_ZERO = "8000000000000000"
ONE = "3ff0000000000000"
NEG_ONE = "bff0000000000000"


def _scalar_witness_bits(zero: str = ZERO):
    return (
        (((ONE, zero),),),
        (((zero, NEG_ONE),),),
        (((NEG_ONE, zero),),),
        (((zero, ONE),),),
    )


def _receipt(**overrides):
    values = dict(
        nominal_transition=((0,),), uncertainty_radii=(((0, 0),),),
        approximate_inverse_binary64_bits=_scalar_witness_bits(),
        center=0, radius=1, spectral_reference_scale=1,
        nodes=4, sqrt_precision=40,
    )
    values.update(overrides)
    return M.binary64_residual_witness_circle_receipt(**values)


def test_binary64_bits_are_decoded_to_exact_rational_residual_witnesses() -> None:
    result = _receipt()
    assert result.validation_level is not None
    assert result.rank_preserved_for_entire_family is True
    assert result.binary64_stored_value_decoding_verified is True
    assert result.solver_operation_rounding_mode_verified is False
    assert result.solver_algorithm_verified is False
    assert result.empirical_matrix_provenance_verified is False
    assert all(node.residual[0][0].is_zero() for node in result.residual_circle.nodes)


def test_known_binary64_point_one_is_recovered_exactly() -> None:
    decoded = M.decode_binary64_hex("3fb999999999999a")
    assert decoded.classification == "normal"
    assert decoded.exact_value == F(3602879701896397, 36028797018963968)


def test_smallest_subnormal_is_recovered_without_underflow() -> None:
    decoded = M.decode_binary64_hex("0000000000000001")
    assert decoded.classification == "subnormal"
    assert decoded.exact_value == F(1, 1 << 1074)


def test_signed_zero_is_numerically_zero_but_retained_in_receipt_diagnostics() -> None:
    decoded = M.decode_binary64_hex(NEG_ZERO)
    assert decoded.exact_value == 0
    assert decoded.negative_zero is True
    result = _receipt(approximate_inverse_binary64_bits=_scalar_witness_bits(NEG_ZERO))
    assert result.validation_level is not None
    assert result.negative_zero_count == 4


@pytest.mark.parametrize("bits", ["7ff0000000000000", "fff0000000000000", "7ff8000000000000"])
def test_infinity_and_nan_are_rejected(bits: str) -> None:
    with pytest.raises(ValueError, match="NaN and infinity"):
        M.decode_binary64_hex(bits)


@pytest.mark.parametrize("bits", ["3FF0000000000000", "0x3ff0000000000000", "3ff0", 0])
def test_bit_encoding_must_be_canonical_lowercase_fixed_width(bits) -> None:
    with pytest.raises(ValueError, match="sixteen lowercase"):
        M.decode_binary64_hex(bits)


def test_bad_float_witness_fails_at_unchanged_exact_residual_gate() -> None:
    zeros = tuple(((((ZERO, ZERO),),)) for _ in range(4))
    result = _receipt(approximate_inverse_binary64_bits=zeros)
    assert result.status == "VERIFIED_RESIDUAL_NODE_CONTRACTION_UNAVAILABLE"
    assert result.validation_level is None
    assert result.rank_preserved_for_entire_family is False


def test_interval_uncertainty_failure_is_not_overridden_by_good_float_witnesses() -> None:
    result = _receipt(uncertainty_radii=(((1, 0),),))
    assert result.validation_level is None
    assert result.rank_preserved_for_entire_family is False


def test_digest_is_deterministic_and_changes_with_original_signed_zero_bits() -> None:
    first = _receipt()
    repeat = _receipt()
    signed = _receipt(approximate_inverse_binary64_bits=_scalar_witness_bits(NEG_ZERO))
    assert repeat.witness_bits_sha256 == first.witness_bits_sha256
    assert signed.witness_bits_sha256 != first.witness_bits_sha256
    assert signed.decoded_approximate_inverses == first.decoded_approximate_inverses


def test_normalize_first_scale_covariance_preserves_residual_certificate() -> None:
    base = _receipt()
    scaled = _receipt(radius=7, spectral_reference_scale=7)
    assert scaled.validation_level is not None
    assert tuple(node.residual for node in scaled.residual_circle.nodes) == tuple(
        node.residual for node in base.residual_circle.nodes
    )


@pytest.mark.parametrize(
    "witnesses",
    [
        (),
        _scalar_witness_bits()[:3],
        (((ONE, ZERO),),) * 4,
        (((((ONE, ZERO), (ZERO, ZERO)),),),) * 4,
    ],
)
def test_witness_node_matrix_and_complex_pair_shapes_fail_closed(witnesses) -> None:
    with pytest.raises(ValueError):
        _receipt(approximate_inverse_binary64_bits=witnesses)


def test_underlying_four_node_and_precision_contracts_are_preserved() -> None:
    with pytest.raises(ValueError):
        _receipt(nodes=8)
    with pytest.raises(ValueError):
        _receipt(sqrt_precision=True)
