from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("channelwise_qc", HERE / "channelwise_qc.py")
qc = importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(qc)


def window() -> np.ndarray:
    t, c = np.arange(126.)[:, None], np.arange(63.)[None, :]
    return np.sin(t / 7 + c / 5) + .1 * np.cos(t / 3 - c / 9)


def test_channelwise_affine_invariance_negative_gain_offsets_and_units():
    base = qc.channelwise_qc(window())
    gains, offsets = np.linspace(-3, 4, 63)[None, :], np.linspace(-100, 100, 63)[None, :]
    changed = qc.channelwise_qc(window() * gains + offsets)
    units = qc.channelwise_qc(window() * 1000)
    assert (changed["Q_A"], changed["Q_D"]) == pytest.approx((base["Q_A"], base["Q_D"]))
    assert (units["Q_A"], units["Q_D"]) == pytest.approx((base["Q_A"], base["Q_D"]))


def test_time_varying_gain_and_mixing_are_explicitly_not_invariant():
    x = window(); time_gain = 1 + np.arange(126.)[:, None] / 126
    mixed = x + .5 * np.roll(x, 1, axis=1)
    base = qc.channelwise_qc(x)
    assert qc.channelwise_qc(x * time_gain)["Q_A"] != pytest.approx(base["Q_A"])
    assert qc.channelwise_qc(mixed)["Q_A"] != pytest.approx(base["Q_A"])


def test_spike_step_and_broad_artifact_limitation():
    x, base = window(), qc.channelwise_qc(window())
    spike = x.copy(); spike[50, 3] += 1000
    step = x.copy(); step[63:, 7] += 1000
    broad = x.copy(); broad += 1000 * np.sin(np.arange(126.)[:, None] / 4)
    assert qc.channelwise_qc(spike)["Q_D"] > base["Q_D"]
    assert qc.channelwise_qc(step)["Q_D"] > base["Q_D"]
    broad_metric = qc.channelwise_qc(broad)
    # A large smooth common artifact can inflate its own channel scales and remain bounded.
    assert broad_metric["Q_A"] < 1.1 and broad_metric["Q_D"] < 1.1


@pytest.mark.parametrize("alter", [lambda x: np.where(np.arange(x.size).reshape(x.shape) == 0, np.nan, x), lambda x: np.column_stack((np.ones(126), x[:, 1:]))])
def test_nonfinite_and_zero_channel_scales_fail_closed(alter):
    with pytest.raises(qc.ApparatusInvalid): qc.channelwise_qc(alter(window()))


def test_cutoffs_and_transfer_gate():
    frozen = qc.freeze_cutoffs([{ "Q_A": float(i), "Q_D": float(i + 100)} for i in range(64)])
    assert frozen["Q_A"]["cutoff"] == pytest.approx(31.5 + 6 * 16)
    pairs = [{"accepted": i < 24, "session": "ses-01" if i < 16 else "ses-02"} for i in range(32)]
    assert qc.transfer_gate(pairs)[0] is False
    for p in pairs[24:28]: p["accepted"] = True
    assert qc.transfer_gate(pairs)[0] is True


def test_production_allocation_counts_word_coverage_and_keys():
    import json
    manifest = json.loads((HERE.parents[1] / "brain-self-trajectory-human-fmri-l3-20260824/artifacts/a0-trial-manifest.json").read_text(encoding="utf-8"))
    result = qc.allocation(manifest)
    assert result["counts"] == {"B1": 32, "D2-M": 100}
    assert result["session_counts"] == {"ses-01": {"B1": 16, "D2-M": 57}, "ses-02": {"B1": 16, "D2-M": 43}}
    assert all(len(words) == 8 for words in result["d2m_word_coverage"].values())
    assert result["signal_accessed"] is False
    assert result["scientific_endpoint_opened"] is False
    assert result["model_outcome_opened"] is False
    assert result["model_outcome_computed"] is False
    assert result["self1_brainvision_sha256"] == qc.SELF1_BRAINVISION_SHA256
    assert all(row["allocation_key"] == qc.sha256_bytes((qc.B1_PREFIX + row["trial_hash"]).encode()) for row in result["trials"])


def test_offline_preflight_order_and_failure_receipt(monkeypatch, tmp_path):
    calls = []; monkeypatch.setattr(qc, "sha256_file", lambda p: calls.append(p) or "wrong")
    with pytest.raises(qc.ApparatusInvalid, match="current contract hash mismatch"):
        qc.preflight("A1", tmp_path / "m", tmp_path / "a", tmp_path / "p", tmp_path / "c")
    assert len(calls) == 1
    assert qc.unopened_splits("B1") == ["D2-M", "C1", "C2", "C3"]


def test_real_offline_preflight_receipt_exposes_audit_fields():
    ce = HERE.parents[1]
    receipt = qc.preflight("A1", ce / "brain-self-trajectory-human-fmri-l3-20260824/artifacts/a0-trial-manifest.json",
                           ce / "brain-self-trajectory-human-fmri-l3-20260824/artifacts/a0-metadata-receipt.json",
                           qc.predecessor_default(), HERE.parent / "00-contract.md")
    assert receipt["network_accessed"] is False
    assert receipt["model_outcome_opened"] is False
    assert receipt["self1_brainvision_sha256"] == qc.SELF1_BRAINVISION_SHA256
    assert receipt["filter_geometry"]["postfilter_shape"] == [126, 63]


def test_window_row_uses_self1_for_range_and_absolute_and_self2_only_for_r1():
    calls = []
    class Self1:
        def recording_for(self, a0, subject, session):
            calls.append(("recording_for", subject, session)); return {"eeg_url": "synthetic", "content_length": 1, "etag": "x"}
        def anchor_to_sample(self, anchor): calls.append(("anchor", anchor)); return 10
        def byte_geometry(self, anchor): calls.append(("geometry", anchor)); return (1, 2, 3, 4)
        def fetch_exact_range(self, *args): calls.append(("fetch", args[0])); return (b"raw", {"status": 206})
        def parse_multiplexed_float32(self, raw): calls.append(("parse", raw)); return raw
        def causal_filter_and_decimate(self, raw): calls.append(("filter", raw)); return window()
        def window_qc(self, value): calls.append(("absolute", value.shape)); return {"legacy": "absolute"}
    class Self2:
        def scale_free_qc(self, value): calls.append(("r1", value.shape)); return {"legacy": "r1"}
    trial = {"subject": "sub-02", "session": "ses-01", "task_anchor_s": 1.2}
    row = qc.window_row(Self1(), Self2(), {}, trial, "task", None)
    assert row["matched_absolute_diagnostic"] == {"legacy": "absolute"}
    assert row["matched_self2_r1_diagnostic"] == {"legacy": "r1"}
    assert [name for name, *_ in calls] == ["recording_for", "anchor", "geometry", "fetch", "parse", "filter", "absolute", "r1"]
