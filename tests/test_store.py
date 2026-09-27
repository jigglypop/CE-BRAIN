import h5py
import numpy as np
import pytest

from research import harness, store


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, "LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(store, "DATA", tmp_path / "external")
    monkeypatch.setattr(store, "CACHE", tmp_path / "cache")
    return tmp_path


def nwb(file):
    """A tiny NWB-shaped file: two units (one unsorted), epochs with ragged tags, states, one series."""
    with h5py.File(file, "w") as f:
        u = f.create_group("units")
        u["spike_times"], u["spike_times_index"] = [0.5, 0.2, 1.0, 3.0, 2.0], np.array([3, 5], np.uint32)
        u["id"], u["is_head_direction"] = [7, 9], np.array([1, 0], np.uint8)
        u.create_dataset("location", data=["PoS", "ADn"], dtype=h5py.string_dtype())
        e = f.create_group("intervals/epochs")
        e["start_time"], e["stop_time"], e["tags_index"] = [0.0, 2.0], [2.0, 4.0], [1, 2]
        e.create_dataset("tags", data=["home_cage", "wake_square"], dtype=h5py.string_dtype())
        s = f.create_group("intervals/sleep_states")
        s["start_time"], s["stop_time"], s["tags_index"] = [0.0, 1.0], [1.0, 2.0], [0, 0]
        s.create_dataset("tags", shape=(0,), dtype=h5py.string_dtype())
        s.create_dataset("state", data=["wake", "nrem"], dtype=h5py.string_dtype())
        h = f.create_group("processing/behavior/head")
        h.create_dataset("data", data=np.array([10, 20], np.int16)).attrs["conversion"] = 0.5
        h["starting_time"] = 1.0
        h["starting_time"].attrs["rate"] = 2.0


def test_extract_nwb_into_session_format(place):
    nwb(place / "a.nwb")
    row = store.extract("toy", "v1", "sub-1/sub-1_ses-1.nwb", str(place / "a.nwb"), "test",
                        series={"head": "processing/behavior/head"})
    assert row["asset"] == "sub-1_ses-1.npz" and harness.registered("toy")[0]["sha256"] == row["sha256"]
    s = store.load(row)
    assert np.array_equal(s.spikes, [0.2, 0.5, 1.0, 2.0, 3.0]) and np.array_equal(s.ends, [3, 5])
    assert list(s["unit_location"]) == ["PoS", "ADn"] and list(s["unit_id"]) == [7, 9]
    assert list(s["epochs_label"]) == ["home_cage", "wake_square"]
    assert list(s["sleep_states_label"]) == ["wake", "nrem"]
    assert np.allclose(s.series("head")[0], [1.0, 1.5]) and np.allclose(s.series("head")[1], [5, 10])
    assert np.array_equal(s.intervals("sleep_states", "nrem")[0], [1.0])
    hd = s.units(s["unit_is_head_direction"] == 1)
    assert np.array_equal(hd.counts([0, 1, 4]), [[2, 1]]) and list(hd["unit_location"]) == ["PoS"]


def test_old_compressed_extract_reads_through_cache(place):
    file = place / "old.npz"
    np.savez_compressed(file, spike_times=[0.1, 0.2, 0.3], spike_times_index=np.array([1, 3], np.uint32),
                        is_head_direction=np.array([1, 0], np.uint8), ss_state=["nrem"])
    row = {"path": str(file), "sha256": harness.sha256(file)}
    first, again = store.load(row), store.load(row)
    assert (store.CACHE / f"{row['sha256']}.npz").is_file()
    assert np.array_equal(again.window_counts([0.0], [0.25]), [[1], [1]])
    assert list(first["sleep_states_label"]) == ["nrem"] and first.ends.dtype == np.int64


def test_within_keeps_only_spikes_inside_intervals():
    s = store.Session({"spikes": np.array([0.5, 1.5, 2.5, 0.2, 3.5]), "ends": np.array([3, 5])})
    inside = s.within([3.0, 1.0], [4.0, 2.0])
    assert np.array_equal(inside.spikes, [1.5, 3.5]) and np.array_equal(inside.ends, [1, 2])
