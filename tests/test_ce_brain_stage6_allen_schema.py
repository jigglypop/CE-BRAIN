from pathlib import Path

import h5py
import numpy as np

from examples.brain import ce_brain_stage6_allen_schema as schema


def make_nwb(path: Path, visual_units: int = 200) -> None:
    with h5py.File(path, "w") as nwb:
        nwb.create_dataset("identifier", data=np.bytes_(schema.EXPECTED_SESSION))
        units = nwb.create_group("units")
        units.create_dataset("id", data=np.arange(visual_units))
        units.create_dataset("spike_times", data=np.array([], dtype=float))
        units.create_dataset("spike_times_index", data=np.zeros(visual_units, dtype=int))
        units.create_dataset("peak_channel_id", data=np.arange(visual_units))
        electrodes = nwb.create_group("general/extracellular_ephys/electrodes")
        electrodes.create_dataset("id", data=np.arange(visual_units))
        electrodes.create_dataset("location", data=np.array([b"VISp"] * visual_units))
        movie = nwb.create_group("intervals/natural_movie_one_presentations")
        frames = np.tile(np.arange(900), 10)
        starts = np.arange(len(frames), dtype=float)
        movie.create_dataset("frame", data=frames)
        movie.create_dataset("start_time", data=starts)
        movie.create_dataset("stop_time", data=starts + 0.5)
        movie.create_dataset("stimulus_block", data=np.repeat([4, 12], [4500, 4500]))
        nwb.create_group("processing/running/running_speed")


def test_schema_accepts_repeated_movie_and_visual_population(tmp_path):
    path = tmp_path / "eligible.nwb"
    make_nwb(path)
    result = schema.audit(path, verify_hash=False)
    assert result["decision"] == "STAGE6_DEVELOPMENT_SCHEMA_ELIGIBLE"
    assert result["natural_movie_one"]["repeat_count"] == 10


def test_schema_stops_when_visual_population_is_too_small(tmp_path):
    path = tmp_path / "small.nwb"
    make_nwb(path, visual_units=199)
    assert schema.audit(path, verify_hash=False)["decision"] == "STAGE6_SCHEMA_STOP"

