"""Mechanical guards only: these tests never generate or score the confirmation population."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil

import numpy as np
import pytest


MODULE_PATH = Path(__file__).with_name("twin_confirmation.py")
SPEC = importlib.util.spec_from_file_location("twin_confirmation_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
twin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(twin)


def _receipt_records() -> list[dict[str, object]]:
    return [{"block": block, "twin": twin_index, "common_random_sha256": f"crn-{block}-{twin_index}",
             "arm_sha256": [f"arm-{block}-{twin_index}-0", f"arm-{block}-{twin_index}-1"],
             "contrast_sha256": "linear-world-shared-contrast"}
            for block in range(twin.BLOCKS) for twin_index in range(twin.TWINS)]


def _split_identity() -> dict[str, object]:
    return {"world": "E", "replicate": 0,
            "trajectory_sha256": {"train": [f"train-{index}" for index in range(96)],
                                  "validation": [f"validation-{index}" for index in range(48)]}}


def test_domain_separated_seed_is_fresh_and_stable() -> None:
    first = twin._seed("E", 3, "TEST-SEED", 1)
    assert first == twin._seed("E", 3, "TEST-SEED", 1)
    assert first != twin._seed("E", 3, "TEST-SEED", 2)
    assert first != twin._seed("E", 4, "TEST-SEED", 1)
    assert first != twin.ROOT_SEED
    twin._verify_root_seed()


def test_confirmation_requires_serialized_descriptor_before_any_twin_access() -> None:
    with pytest.raises(RuntimeError, match="confirmation before serialization"):
        twin._generate_twins(None, "E", 0, {}, None)


def test_blockwise_fisher_yates_is_deterministic_and_does_not_cross_blocks() -> None:
    target = np.zeros((twin.BLOCKS, twin.TWINS, twin.TIMES, twin.NODES), dtype=np.float64)
    target[:, :, 2:] = np.arange(twin.BLOCKS * twin.TWINS).reshape(twin.BLOCKS, twin.TWINS, 1, 1)
    predicted = target.copy()
    loss = twin._permuted_loss(predicted, target, "D", 1, 0)
    assert np.isfinite(loss)
    with pytest.raises(RuntimeError, match="cross block permutation"):
        twin._permuted_loss(predicted[:-1], target, "D", 1, 0)


def test_linear_twin_identity_rule_and_nonidentity_fixture() -> None:
    identical = np.broadcast_to(np.arange(twin.TIMES * twin.NODES, dtype=np.float64).reshape(1, 1, twin.TIMES, twin.NODES),
                                (twin.BLOCKS, twin.TWINS, twin.TIMES, twin.NODES)).copy()
    assert twin._twin_identity(identical)
    nonidentical = identical.copy()
    nonidentical[0, 1, 4, 2] += 1e-4
    assert not twin._twin_identity(nonidentical)


def test_parent_hash_guard_rejects_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "parent.py"
    source.write_text("not the sealed parent", encoding="utf-8")
    with pytest.raises(RuntimeError, match="parent source hash"):
        twin._verify_parent_source(source)


def test_unsealed_execute_fails_before_confirmation_population_generation(tmp_path: Path) -> None:
    # An isolated pivot ensures this remains true even if the real pivot is later sealed.
    with pytest.raises(RuntimeError, match="missing manifest"):
        twin.execute(twin._run_root(), pivot=tmp_path)


def test_temp_prereg_manifest_seals_verifies_and_rejects_a_mutation(tmp_path: Path) -> None:
    for relative in twin.PREREG_FILES:
        source = MODULE_PATH.parent / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    sealed = twin.seal(twin._run_root(), pivot=tmp_path)
    _, digest = twin.verify_manifest(twin._run_root(), pivot=tmp_path)
    assert digest == sealed["manifest_sha256"]
    target = tmp_path / "20-hypotheses.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nfixture mutation\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="manifest mismatch"):
        twin.verify_manifest(twin._run_root(), pivot=tmp_path)


def test_duplicate_arm_receipt_fails_but_repeated_contrasts_are_allowed() -> None:
    records = _receipt_records()
    twin._verify_twin_receipts(records)
    records[-1]["arm_sha256"][1] = records[0]["arm_sha256"][0]
    with pytest.raises(RuntimeError, match="twin receipt"):
        twin._verify_twin_receipts(records)


def test_missing_or_duplicate_common_random_receipt_fails() -> None:
    records = _receipt_records()
    records[0]["common_random_sha256"] = ""
    with pytest.raises(RuntimeError, match="twin receipt"):
        twin._verify_twin_receipts(records)
    records = _receipt_records()
    records[-1]["common_random_sha256"] = records[0]["common_random_sha256"]
    with pytest.raises(RuntimeError, match="twin receipt"):
        twin._verify_twin_receipts(records)


def test_split_and_confirmation_arm_receipts_are_disjoint() -> None:
    identity, records = _split_identity(), _receipt_records()
    twin._verify_cross_split_disjoint(identity, records)
    records[0]["arm_sha256"][0] = "train-0"
    with pytest.raises(RuntimeError, match="split twin overlap"):
        twin._verify_cross_split_disjoint(identity, records)


def test_row_verifier_recomputes_selection_and_twin_receipts() -> None:
    identity, records = _split_identity(), _receipt_records()
    selection = {"winner": {"kind": "R", "model_sha256": "winner-model"},
                 "candidates": {"R": {"model_sha256": "winner-model"}}}
    serialized = twin._sha(twin._selection_serialization_body(selection))
    row = {"world": "E", "replicate": 0, "identity": identity, "selection": selection,
           "selection_serialization_sha256": serialized,
           "twin_receipts": {"descriptor_serialization_sha256": serialized, "twins": records,
                             "confirmation_sha256": "confirmation"}}
    twin._verify_result_row(row)
    row["twin_receipts"]["descriptor_serialization_sha256"] = "mismatch"
    with pytest.raises(RuntimeError, match="selection serialization receipt"):
        twin._verify_result_row(row)


def test_zero_prediction_equal_arm_loss_is_permutation_invariant() -> None:
    target = np.arange(twin.BLOCKS * twin.TWINS * twin.TIMES * twin.NODES, dtype=np.float64)
    target = target.reshape(twin.BLOCKS, twin.TWINS, twin.TIMES, twin.NODES)
    shuffled = np.empty_like(target)
    for block in range(twin.BLOCKS):
        shuffled[block] = target[block, twin._fisher_yates(twin.TWINS, twin._seed("E", 0, "TEST-PERM", block))]
    baseline = twin._equal_arm_control(target)
    permuted = twin._equal_arm_control(shuffled)
    assert np.isclose(baseline["equal_arm_nrmse"], permuted["equal_arm_nrmse"])
    assert baseline["equal_arm_advantage"] == permuted["equal_arm_advantage"] == 0.0
    assert baseline["equal_arm_p_value"] == permuted["equal_arm_p_value"] == 1.0


def test_run_root_and_prereg_population_are_exact() -> None:
    assert twin._run_root() / "artifacts" / "stage0_synthetic_discrimination.py" == MODULE_PATH.parents[5] / "artifacts" / "stage0_synthetic_discrimination.py"
    assert set(twin.PREREG_FILES) == {
        "contract.md", "route.json", "10-data-lock.md", "20-hypotheses.md", "30-models.md",
        "40-metrics.md", "50-gates.md", "60-negative-controls.md", "twin_confirmation.py",
        "test_twin_confirmation.py", "20-audit.md", "21-preexecution-validation.md",
    }
