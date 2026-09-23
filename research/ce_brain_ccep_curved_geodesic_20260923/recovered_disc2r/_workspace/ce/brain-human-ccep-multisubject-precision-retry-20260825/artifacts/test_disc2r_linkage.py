from __future__ import annotations

from copy import deepcopy

import pytest

import disc2r_ccep_run as retry
from disc2_ccep_core import ApparatusError


def test_all_74_participants_and_592_selected_sources_link_exactly():
    _, split, records = retry.load_and_verify_manifests()
    checked_sources = 0
    checked_trials = 0
    subjects = set()
    for subject in split["subjects"]:
        subjects.add(subject["subject"])
        for source in subject["sources"]:
            ordered, halves, orientations = retry.ordered_trials(
                source, records[source["record_id"]]
            )
            assert len(ordered) == 10
            assert sorted(halves[0] + halves[1]) == list(range(10))
            if source["orientation_mode"] == "two_orientation_5_by_5":
                assert len(orientations) == 2
            else:
                assert orientations == {}
            checked_sources += 1
            checked_trials += len(ordered)
    assert len(subjects) == 74
    assert checked_sources == 74 * 8
    assert checked_trials == 74 * 8 * 10


def test_histogram_and_clean_trial_mismatches_fail_before_range():
    _, split, records = retry.load_and_verify_manifests()
    subject = split["subjects"][0]
    source = subject["sources"][0]
    record = records[source["record_id"]]

    bad_record = deepcopy(record)
    bad_record["event_sample_crosswalk"] = {"0": record["electrical_event_count"] - 1}
    with pytest.raises(ApparatusError, match="delta histogram"):
        retry.ordered_trials(source, bad_record)

    bad_source = deepcopy(source)
    bad_source["temporal_repeatability_halves"]["A"][0][
        "anchor_sample_zero_based"
    ] += 1
    with pytest.raises(ApparatusError, match="anchor/orientation"):
        retry.ordered_trials(bad_source, record)


def test_retry_reuses_exact_scientific_inputs_and_has_no_endpoint():
    assert retry._sha256(retry.OLD_ROOT / "run-lock.json") == retry.OLD_RUN_LOCK_SHA256
    assert retry._sha256(retry.base.SOURCE_MANIFEST) == (
        "9ed8cb9d7a12cf293f8a899aa9a04de7951109b0fad0505e08ebe93f9e11b3c3"
    )
    assert retry._sha256(retry.base.SPLIT_MANIFEST) == (
        "d4b03a984f03529c870df6d2c62034443b08611ddacd3cfe4244067bb5ff96f7"
    )
    fixture = retry.verify_fixture_receipt()
    assert fixture["status"] == "PASS"
    assert not retry.base.opened_path("D0").exists()
    assert not retry.base.endpoint_path("D0").exists()
