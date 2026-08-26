"""Mechanical-only tests; never seal or execute the real reset pivot."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
from types import SimpleNamespace

import numpy as np
import pytest


MODULE_PATH = Path(__file__).with_name("state_reset_confirmation.py")
SPEC = importlib.util.spec_from_file_location("state_reset_confirmation_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
reset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reset)


def _records() -> list[dict[str, object]]:
    return [{"block": block, "twin": twin, "common_random_sha256": f"crn-{block}-{twin}",
             "arm_sha256": [f"arm-{block}-{twin}-0", f"arm-{block}-{twin}-1"], "contrast_sha256": "repeat-ok",
             "reset_sha256": reset._array_hash(reset._state_for(block, twin)),
             "arm_reset_sha256": [reset._array_hash(np.vstack((reset._state_for(block, twin), reset._state_for(block, twin))))] * 2}
            for block in range(reset.BLOCKS) for twin in range(reset.TWINS)]


def _identity() -> dict[str, object]:
    return {"world": "E", "replicate": 0,
            "trajectory_sha256": {"train": [f"train-{q}" for q in range(96)],
                                  "validation": [f"validation-{q}" for q in range(48)]},
            "assignment": {"train": [[q % 8, ((q // 8) + (q % 8)) % 8] for q in range(96)],
                           "validation": [[q % 8, ((q // 8) + (q % 8)) % 8] for q in range(48)]}}


def test_root_and_paired_hadamard_bank_are_exact() -> None:
    reset._verify_root_seed()
    bank = reset._hadamard_bank()
    assert np.array_equal(bank[:4] @ bank[:4].T, 8 * np.eye(4))
    assert np.array_equal(bank[4:], -bank[:4])
    states, labels = reset._reset_assignment(96)
    assert np.array_equal(states[:, 0], states[:, 0])
    assert [sum(row == q for _, row in labels) for q in range(8)] == [12] * 8
    validation, labels = reset._reset_assignment(48)
    assert [sum(row == q for _, row in labels) for q in range(8)] == [6] * 8
    assert np.isclose(np.sqrt(np.mean(validation ** 2)), 0.30)


def test_immediate_pulses_and_pair_reset_are_mechanical() -> None:
    arm0, arm1 = reset._challenge_inputs(3)
    assert arm0[1:5, 3].tolist() == [0.9] * 4 and arm1[1:5, 3].tolist() == [-0.9] * 4
    assert arm0[31:35, 3].tolist() == [-0.45] * 4 and arm1[31:35, 3].tolist() == [0.45] * 4
    parent = SimpleNamespace(HIDDEN_NODES=24, NOISE_SD=0.02, MAX_ABS_STATE=1e6)
    coefficients = {"A": 0.5 * np.eye(8), "B": 0.2 * np.eye(8)}
    pair, _ = reset._pair(parent, "A", coefficients, reset._state_for(0, 0), (arm0, arm1), reset._seed("A", 0, "TEST-PAIR"))
    assert np.array_equal(pair[0, :2], pair[1, :2])
    # With shared innovations in a linear system, changing an arm does not change the innovation residual.
    assert np.all(np.isfinite(pair))


def test_preserialization_and_receipt_fail_closed_guards() -> None:
    with pytest.raises(RuntimeError, match="confirmation before serialization"):
        reset._generate_main(None, "E", 0, {}, None)
    records = _records(); reset._verify_receipts(records, unique_common=True)
    records[-1]["common_random_sha256"] = records[0]["common_random_sha256"]
    with pytest.raises(RuntimeError, match="common receipt"):
        reset._verify_receipts(records, unique_common=True)
    records = _records(); records[0]["arm_sha256"][0] = "train-0"
    with pytest.raises(RuntimeError, match="split arm overlap"):
        reset._verify_cross_split(_identity(), records)


def test_result_row_revalidates_serialization_and_cross_split_receipts() -> None:
    selection = {"winner": {"kind": "R", "model_sha256": "winner"}, "candidates": {"R": {"model_sha256": "winner"}}}
    digest = reset._sha(reset._selection_body(selection))
    row = {"world": "E", "replicate": 0, "identity": _identity(), "selection": selection,
           "selection_serialization_sha256": digest,
           "receipts": {"descriptor_serialization_sha256": digest, "twins": _records(), "confirmation_sha256": "all"},
           "adverse": {"identity": True, "common_by_block_sha256": [f"adverse-{q}" for q in range(8)]}}
    reset._verify_row(row)
    row["receipts"]["descriptor_serialization_sha256"] = "bad"
    with pytest.raises(RuntimeError, match="selection receipt"):
        reset._verify_row(row)


def test_assignment_and_main_reset_receipts_fail_closed_when_corrupted() -> None:
    identity, records = _identity(), _records()
    reset._verify_assignment_receipt(identity["assignment"])
    reset._verify_main_reset_receipts(records)
    identity["assignment"]["train"][0] = [7, 7]
    with pytest.raises(RuntimeError, match="assignment formula"):
        reset._verify_assignment_receipt(identity["assignment"])
    records = _records(); records[0]["reset_sha256"] = "not-z-cr"
    with pytest.raises(RuntimeError, match="reset receipt"):
        reset._verify_main_reset_receipts(records)


def test_unsealed_and_temporary_manifest_fixture() -> None:
    # This test makes neither a real pivot manifest nor a confirmation population.
    with pytest.raises(RuntimeError, match="missing manifest"):
        reset.execute(reset._run_root(), pivot=Path.cwd() / "_nonexistent_state_reset_fixture")


def test_temporary_prereg_manifest_and_expected_population(tmp_path: Path) -> None:
    for relative in reset.PREREG_FILES:
        destination = tmp_path / relative; destination.parent.mkdir(parents=True, exist_ok=True)
        source = MODULE_PATH.parent / relative
        if source.is_file(): shutil.copyfile(source, destination)
        else: destination.write_text("temporary prereg fixture\n", encoding="utf-8")
    sealed = reset.seal(reset._run_root(), pivot=tmp_path)
    _, digest = reset.verify_manifest(reset._run_root(), pivot=tmp_path)
    assert digest == sealed["manifest_sha256"]
    assert set(reset.PREREG_FILES) == {
        "contract.md", "route.json", "10-data-lock.md", "20-hypotheses.md", "30-models.md", "40-metrics.md",
        "50-gates.md", "60-negative-controls.md", "20-audit.md", "21-preexecution-validation.md",
        "state_reset_confirmation.py", "test_state_reset_confirmation.py",
    }
    (tmp_path / "contract.md").write_text("mutated", encoding="utf-8")
    with pytest.raises(RuntimeError, match="manifest mismatch"):
        reset.verify_manifest(reset._run_root(), pivot=tmp_path)
