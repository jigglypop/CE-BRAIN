from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("scale_free_qc", HERE / "scale_free_qc.py")
qc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(qc)


def valid_window() -> np.ndarray:
    time = np.arange(126, dtype=float)[:, None]
    channel = np.arange(63, dtype=float)[None, :]
    return np.sin(time / 7.0 + channel / 5.0) + 0.1 * np.cos(time / 3.0 - channel / 9.0)


def test_common_affine_invariance_including_negative_gain_and_offsets():
    window = valid_window(); base = qc.scale_free_qc(window)
    offsets = np.linspace(-100.0, 100.0, 63)[None, :]
    changed = qc.scale_free_qc(-3.0 * window + offsets)
    assert changed["Q_A"] == pytest.approx(base["Q_A"])
    assert changed["Q_D"] == pytest.approx(base["Q_D"])


def test_dimensionlessness_under_unit_rescaling():
    base = qc.scale_free_qc(valid_window())
    millivolts = qc.scale_free_qc(valid_window() * 1_000.0)
    assert (millivolts["Q_A"], millivolts["Q_D"]) == pytest.approx((base["Q_A"], base["Q_D"]))


def test_channel_specific_gain_is_explicitly_not_invariant():
    window = valid_window(); base = qc.scale_free_qc(window)
    altered = window.copy(); altered[:, 0] *= 100.0
    changed = qc.scale_free_qc(altered)
    assert changed["Q_A"] != pytest.approx(base["Q_A"])


def test_deterministic_spike_and_step_adverse_controls_increase_their_ratios():
    window = valid_window(); base = qc.scale_free_qc(window)
    spike = window.copy(); spike[50, 10] += 1_000.0
    step = window.copy(); step[63:, 20] += 1_000.0
    spike_metric, step_metric = qc.scale_free_qc(spike), qc.scale_free_qc(step)
    assert spike_metric["Q_A"] > base["Q_A"] and spike_metric["Q_D"] > base["Q_D"]
    assert step_metric["Q_A"] > base["Q_A"] and step_metric["Q_D"] > base["Q_D"]


@pytest.mark.parametrize("mutator", [
    lambda x: np.where(np.arange(x.size).reshape(x.shape) == 0, np.nan, x),
    lambda x: np.column_stack((np.ones(x.shape[0]), x[:, 1:])),
])
def test_nonfinite_and_zero_channel_scales_fail_closed(mutator):
    with pytest.raises(qc.ApparatusInvalid):
        qc.scale_free_qc(mutator(valid_window()))


def test_cutoff_is_median_plus_six_unscaled_mad():
    metrics = [{"Q_A": float(index + 1), "Q_D": float(100 + index)} for index in range(64)]
    frozen = qc.freeze_cutoffs(metrics)
    assert frozen["Q_A"]["cutoff"] == pytest.approx(32.5 + 6.0 * 16.0)
    assert frozen["Q_D"]["cutoff"] == pytest.approx(131.5 + 6.0 * 16.0)


def test_transfer_gate_requires_total_and_each_session():
    pairs = [{"accepted": index < 24, "session": "ses-01" if index < 16 else "ses-02"} for index in range(32)]
    passed, accepted, by_session = qc.transfer_gate(pairs)
    assert not passed and accepted == 24 and by_session == {"ses-01": 16, "ses-02": 8}
    for pair in pairs[24:28]:
        pair["accepted"] = True
    passed, accepted, by_session = qc.transfer_gate(pairs)
    assert passed and accepted == 28 and all(n >= 12 for n in by_session.values())


def test_default_predecessor_is_a_sibling_run_under_workspace_ce():
    path = qc.predecessor_default()
    assert path.parent.name == "artifacts"
    assert path.parent.parent.parent.name == "ce"
    assert path.name == "brainvision_range.py"


def test_preflight_is_offline_and_checks_seal_order(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(qc, "sha256_file", lambda path: calls.append(path) or "wrong")
    with pytest.raises(qc.ApparatusInvalid, match="current contract hash mismatch"):
        qc.preflight("A1", tmp_path / "manifest", tmp_path / "a0", tmp_path / "predecessor", tmp_path / "contract")
    assert len(calls) == 1
