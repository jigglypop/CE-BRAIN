from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import disc2_ccep_run as runner
from disc2_ccep_core import ApparatusError


def _trial(index: int, orientation: str = "A-B") -> dict[str, object]:
    return {
        "event_index": index,
        "anchor_sample_zero_based": 10_000 + index,
        "orientation_site": orientation,
    }


def test_trial_plan_links_record_local_events_and_separates_temporal_from_polarity():
    trials = [_trial(index) for index in range(10)]
    source = {
        "temporal_repeatability_halves": {"A": trials[::2], "B": trials[1::2]},
        "orientation_groups": {"A-B": trials},
        "orientation_mode": "single_orientation_temporal_only",
    }
    record = {
        "event_sample_crosswalk": {
            str(index): 10_000 + index for index in range(10)
        }
    }
    ordered, halves, orientation = runner._ordered_trials(source, record)
    assert [trial["event_index"] for trial in ordered] == list(range(10))
    assert halves == ([0, 2, 4, 6, 8], [1, 3, 5, 7, 9])
    assert orientation == {}

    record["event_sample_crosswalk"]["3"] += 1
    with pytest.raises(ApparatusError, match="crosswalk"):
        runner._ordered_trials(source, record)


def test_two_orientation_plan_is_exact_five_by_five():
    forward = [_trial(index, "A-B") for index in range(5)]
    reverse = [_trial(index, "B-A") for index in range(5, 10)]
    source = {
        "temporal_repeatability_halves": {
            "A": [forward[0], reverse[0], forward[2], reverse[2], forward[4]],
            "B": [reverse[1], forward[1], reverse[3], forward[3], reverse[4]],
        },
        "orientation_groups": {"A-B": forward, "B-A": reverse},
        "orientation_mode": "two_orientation_5_by_5",
    }
    record = {
        "event_sample_crosswalk": {
            str(index): 10_000 + index for index in range(10)
        }
    }
    _, _, orientation = runner._ordered_trials(source, record)
    assert orientation == {"A-B": [0, 1, 2, 3, 4], "B-A": [5, 6, 7, 8, 9]}


def _endpoint(two_orientation: bool) -> dict[str, object]:
    energy = [2.0, 3.0, 4.0, 5.0, 6.0]
    groups = {"A-B": energy, "B-A": [2.1, 3.1, 4.1, 5.1, 6.1]} if two_orientation else {}
    return {
        "baseline_sigma_uv": 1.0,
        "energy": energy,
        "pre_energy": [1.0, 1.5, 2.0, 2.5, 3.0],
        "temporal_half_energy": [energy, [2.2, 3.2, 4.2, 5.2, 6.2]],
        "orientation_energy": groups,
    }


def test_d0_apparatus_gate_does_not_count_single_orientation_as_polarity():
    sources = []
    for source_index in range(192):
        two = source_index < 48
        subject_index = source_index % 24
        if two:
            subject_index %= 6
        sources.append(
            {
                "subject": f"sub-{subject_index:02d}",
                "orientation_mode": (
                    "two_orientation_5_by_5"
                    if two
                    else "single_orientation_temporal_only"
                ),
                "targets": [
                    {"endpoint": _endpoint(two)} for _ in range(16)
                ],
            }
        )
    metrics = runner.apparatus_metrics("D0", sources)
    assert metrics["orientation_source_count"] == 48
    assert metrics["orientation_participant_count"] == 6
    assert metrics["status"] == "PASS"
    assert all(metrics["checks"].values())


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_stage_barrier_requires_audited_lock_and_passing_predecessor(tmp_path, monkeypatch):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    audit = tmp_path / "preimplementation-audit-receipt.json"
    _write_json(audit, {"verdict": "PASS", "run_lock_sha256": "lock"})
    monkeypatch.setattr(runner, "ARTIFACTS", artifacts)
    monkeypatch.setattr(runner, "PREIMPLEMENTATION_AUDIT", audit)
    monkeypatch.setattr(runner, "verify_fixture_receipt", lambda: {"status": "PASS"})

    runner.verify_stage_barrier("D0", "lock", opening=True)
    with pytest.raises(RuntimeError, match="PREDECESSOR_RESULT_MISSING"):
        runner.verify_stage_barrier("D1", "lock", opening=True)
    _write_json(
        artifacts / "d0-result.json",
        {"status": "PASS_SELECTION_ONLY", "run_lock_sha256": "lock", "winner": "SC"},
    )
    runner.verify_stage_barrier("D1", "lock", opening=True)
    (artifacts / "d1-opened.json").write_text("{}", encoding="utf-8")
    (artifacts / "d1-endpoints.json").write_text("{}", encoding="utf-8")
    runner.verify_stage_barrier("D1", "lock", opening=False)

    _write_json(
        artifacts / "d1-result.json",
        {"status": "KILLED_INTERMEDIATE", "run_lock_sha256": "lock", "winner": "SC"},
    )
    with pytest.raises(RuntimeError, match="PREDECESSOR_STATUS_STOP"):
        runner.verify_stage_barrier("D2", "lock", opening=True)


def test_contact_plan_rejects_cross_source_or_bad_contact():
    target = {
        "site_id": "ses-1|C-D",
        "contacts": ["C", "D"],
        "site": "C-D",
        "center_xyz_mm": [1.0, 2.0, 3.0],
        "distance_mm": 20.0,
        "distance_stratum": 0,
    }
    source = {
        "contacts": ["A", "B"],
        "anchors": [dict(target, site_id=f"a-{index}") for index in range(4)],
        "evaluation": [dict(target, site_id=f"q-{index}") for index in range(12)],
    }
    # Give every target its own contacts so site IDs and channel indices are unique.
    channels = {}
    for index, item in enumerate(source["anchors"] + source["evaluation"]):
        item["contacts"] = [f"C{index}", f"D{index}"]
        channels[f"C{index}"] = {
            "type": "ECOG",
            "status": "good",
            "resolution": 1.0,
            "index": 2 * index,
            "units": "µV",
        }
        channels[f"D{index}"] = {
            "type": "ECOG",
            "status": "good",
            "resolution": 1.0,
            "index": 2 * index + 1,
            "units": "µV",
        }
    names, pairs, targets = runner._selected_contact_plan(source, {"channels": channels})
    assert len(names) == 32
    assert len(pairs) == len(targets) == 16
    channels["C0"]["status"] = "bad"
    with pytest.raises(ApparatusError, match="not good ECoG"):
        runner._selected_contact_plan(source, {"channels": channels})
