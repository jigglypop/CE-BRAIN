from examples.brain import ce_brain_stage6_allen_apparatus as stage6


def test_collect_assets_follows_pagination():
    pages = {
        "first": {"results": [{"asset_id": "a", "path": "sub-1/sub-1_ses-2.nwb", "size": 10}], "next": "second"},
        "second": {"results": [{"asset_id": "b", "path": "sub-1/sub-1_ses-2_probe-3_ecephys.nwb", "size": 20}], "next": None},
    }
    assert len(stage6.collect_assets(lambda url: pages["first" if "page_size" in url else url])) == 2


def test_receipt_is_endpoint_blind_and_counts_schema():
    rows = [
        {"asset_id": "a", "path": "sub-1/sub-1_ses-2.nwb", "size": 10},
        {"asset_id": "b", "path": "sub-1/sub-1_ses-2_probe-3_ecephys.nwb", "size": 20},
        {"asset_id": "c", "path": "sub-4/sub-4_ses-5.nwb", "size": 30},
    ]
    receipt = stage6.build_receipt(rows)
    assert receipt["subject_count"] == 2
    assert receipt["session_asset_count"] == 2
    assert receipt["probe_asset_count"] == 1
    assert receipt["confirmation_endpoint_opened"] is False
    assert receipt["dandi_001695_opened"] is False


def test_subject_split_is_stable():
    assert stage6.split_for("707296975") == stage6.split_for("707296975")

