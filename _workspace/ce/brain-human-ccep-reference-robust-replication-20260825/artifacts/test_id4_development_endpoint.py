import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("endpoint", HERE / "id4_development_endpoint.py")
endpoint = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(endpoint)


def test_car75_site_endpoint_and_gate_are_frozen():
    rng = np.random.default_rng(4457)
    tile = rng.normal(size=(10, 8, endpoint.WINDOW_SAMPLES))
    tile[:, :, endpoint.EARLY] += np.arange(8)[None, :, None] * 0.2
    masks = endpoint.car75_masks(tile, stimulated=(0, 1))
    assert masks.shape == (10, 8) and np.all(masks.sum(axis=1) == 4) and not masks[:, :2].any()
    result = endpoint.site_endpoints(tile, stimulated=(0, 1), halves=["A", "B"] * 5,
                                     receiver_contacts={"R": (2, 3), "S": (4, 5)})
    assert result["selected_per_trial"] == 4 and set(result["endpoints"]) == {"R", "S"}
    assert all(result["endpoints"]["R"][half][mode][window] >= 0
               for half in ("A", "B") for mode in ("mean", "bip") for window in ("early", "prestim"))
    directed = {}
    for index in range(24):
        directed[f"e{index:02d}"] = {
            "A": {"mean_early": index + 2.0, "mean_prestim": 1.0, "bip_early": index + 3.0, "bip_prestim": 1.0},
            "B": {"mean_early": index + 2.1, "mean_prestim": 1.0, "bip_early": index + 3.1, "bip_prestim": 1.0},
        }
    gate = endpoint.development_gate(directed, held_out_pairs=20)
    assert gate["status"] == "DEVELOPMENT_PASS" and all(row["pass"] for row in gate["readouts"].values())


def test_car75_cutoff_tie_fails_closed():
    tile = np.zeros((2, 8, endpoint.WINDOW_SAMPLES))
    try:
        endpoint.car75_masks(tile, stimulated=(0, 1))
        raise AssertionError("cutoff tie accepted")
    except ValueError:
        pass
