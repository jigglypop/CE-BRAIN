import numpy as np

from research import c7_1_address as c7
from research.store import Session


def test_synchronous_events_are_found_and_split():
    rng = np.random.default_rng(0)
    bursts = (np.array([100.0, 200.0, 300.0])[:, None] + np.array([0.005, 0.015, 0.025, 0.035])).ravel()
    spikes = [np.sort(np.r_[rng.uniform(0, 400, 2000), bursts]) for _ in range(10)]
    s = Session({"spikes": np.concatenate(spikes), "ends": np.cumsum([len(x) for x in spikes]),
                 "epochs_start": np.array([0.0]), "epochs_stop": np.array([400.0]), "epochs_label": np.array(["PREEpoch"]),
                 "states_start": np.array([0.0]), "states_stop": np.array([400.0]), "states_label": np.array(["Non-REM"])})
    events = c7.participation(s, "PREEpoch", True)
    assert (events.sum(0) == 10).sum() == 3
