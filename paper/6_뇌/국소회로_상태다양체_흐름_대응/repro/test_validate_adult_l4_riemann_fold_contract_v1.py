from __future__ import annotations

import copy

from validate_adult_l4_riemann_fold_contract_v1 import (
    DEFAULT_CONTRACT,
    load_contract,
    validate_contract,
)


def contract() -> dict:
    return load_contract(DEFAULT_CONTRACT)


def test_canonical_contract_passes() -> None:
    assert validate_contract(contract()) == []


def test_physical_spacetime_claim_fails_closed() -> None:
    mutated = contract()
    mutated["scope"]["physical_lorentz_spacetime_claim"] = True
    assert any("physical spacetime" in error for error in validate_contract(mutated))


def test_regularized_spd_cannot_pass() -> None:
    mutated = contract()
    mutated["fisher"]["regularized_metric_can_pass"] = True
    assert any("regularized metric" in error for error in validate_contract(mutated))


def test_missing_mediator_gate_fails_closed() -> None:
    mutated = contract()
    mutated["required_gates"].remove("G7_MEDIATOR_STATE")
    assert any("L4 gates" in error for error in validate_contract(mutated))


def test_behavior_metric_circularity_fails_closed() -> None:
    mutated = contract()
    mutated["measurements"]["behavior"]["excluded_from_metric_definition"] = False
    assert any("behavior cannot define metric" in error for error in validate_contract(mutated))


def test_underpowered_sample_fails_closed() -> None:
    mutated = contract()
    mutated["cohorts"]["confirmation"]["evaluable_per_arm"] = 27
    mutated["power"]["between_arm"]["n_per_arm"] = 27
    mutated["power"]["between_arm"]["expected_power"] = 0.0
    errors = validate_contract(mutated)
    assert any("evaluable N" in error for error in errors)
    assert any("power" in error for error in errors)


def test_download_budget_drift_fails_closed() -> None:
    mutated = copy.deepcopy(contract())
    mutated["data_budget"]["sample_download_max_mb"] = 1000
    mutated["data_budget"]["bulk_download_authorized"] = True
    errors = validate_contract(mutated)
    assert any("100 MB" in error for error in errors)
    assert any("bulk download" in error for error in errors)


def test_state_rescue_must_leave_theta_lesioned() -> None:
    mutated = contract()
    mutated["interventions"]["theta_must_remain_lesioned_during_state_rescue"] = False
    assert any("must not restore theta" in error for error in validate_contract(mutated))
