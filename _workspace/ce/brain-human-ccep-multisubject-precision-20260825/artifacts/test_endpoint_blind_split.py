import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_endpoint_blind_split.py")
SPEC = importlib.util.spec_from_file_location("build_endpoint_blind_split", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_stage_quotas_exactly_cover_age_strata():
    totals = [sum(mod.STAGE_QUOTA[stage][index] for stage in mod.STAGE_QUOTA) for index in range(4)]
    assert totals == mod.STRATUM_SIZES
    assert sum(mod.STAGE_QUOTA["D3"]) == 30


def test_d0_fold_assignment_is_one_per_age_stratum():
    participants = []
    for index in range(74):
        participants.append({"subject": f"sub-{index:02d}", "age_years": index})
    assignments, _ = mod.participant_stages(participants)
    for fold in range(6):
        rows = [value for value in assignments.values() if value["stage"] == "D0" and value["d0_fold"] == fold]
        assert len(rows) == 4
        assert {row["age_stratum"] for row in rows} == {0, 1, 2, 3}


def test_polarity_balancing_is_five_by_five():
    trials = [
        {"event_index": index, "anchor_sample_zero_based": 100 + index, "orientation_site": "A-B" if index < 5 else "B-A"}
        for index in range(10)
    ]
    partition = mod.repeatability_partition(trials)
    halves = partition["temporal_repeatability_halves"]
    assert len(halves["A"]) == len(halves["B"]) == 5
    assert {row["event_index"] for row in halves["A"]}.isdisjoint(row["event_index"] for row in halves["B"])
    assert {row["orientation_site"] for row in halves["A"]} == {"A-B", "B-A"}
    assert {row["orientation_site"] for row in halves["B"]} == {"A-B", "B-A"}
    assert partition["orientation_mode"] == "two_orientation_5_by_5"
    assert sorted(map(len, partition["orientation_groups"].values())) == [5, 5]


def test_single_orientation_is_temporal_not_polarity_balanced():
    trials = [
        {"event_index": index, "anchor_sample_zero_based": 100 + index, "orientation_site": "A-B"}
        for index in range(10)
    ]
    partition = mod.repeatability_partition(trials)
    assert partition["orientation_mode"] == "single_orientation_temporal_only"
    assert len(partition["temporal_repeatability_halves"]["A"]) == 5
    assert len(partition["temporal_repeatability_halves"]["B"]) == 5


def test_receiver_split_has_disjoint_four_stratum_anchor_and_query():
    site_map = {}
    receiver_ids = []
    for index in range(1, 21):
        site_id = f"ses-1|R{index}"
        receiver_ids.append(site_id)
        site_map[site_id] = {
            "site_id": site_id,
            "site": f"R{index}",
            "contacts": [f"R{index}a", f"R{index}b"],
            "center_xyz_mm": [float(index * 10), 0.0, 0.0],
        }
    source = {"site_id": "ses-1|S", "center_xyz_mm": [0.0, 0.0, 0.0], "receiver_site_ids": receiver_ids}
    split = mod.receiver_split("sub-test", source, site_map)
    assert len(split["anchors"]) == 4
    assert len(split["evaluation"]) == 12
    assert {row["site_id"] for row in split["anchors"]}.isdisjoint(row["site_id"] for row in split["evaluation"])
    assert {row["distance_stratum"] for row in split["anchors"]} == {0, 1, 2, 3}
    assert [sum(row["distance_stratum"] == index for row in split["evaluation"]) for index in range(4)] == [3, 3, 3, 3]
