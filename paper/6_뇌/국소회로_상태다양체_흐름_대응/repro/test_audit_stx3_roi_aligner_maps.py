import pickle
from pathlib import Path

import numpy as np
import pytest

from audit_stx3_roi_aligner_maps import load_day_pair, restricted_loads


def test_plain_integer_map_loads(tmp_path: Path) -> None:
    path = tmp_path / "map.pkl"
    path.write_bytes(
        pickle.dumps(
            {
                0: {
                    5: {
                        "ref_inds": [np.int64(2), np.int64(8)],
                        "targ_inds": [np.int64(1), np.int64(7)],
                    }
                }
            },
            protocol=4,
        )
    )
    reference, target = load_day_pair(path, 0, 5)
    np.testing.assert_array_equal(reference, [2, 8])
    np.testing.assert_array_equal(target, [1, 7])


def test_duplicate_map_index_fails(tmp_path: Path) -> None:
    path = tmp_path / "map.pkl"
    path.write_bytes(
        pickle.dumps(
            {0: {5: {"ref_inds": [2, 2], "targ_inds": [1, 7]}}}, protocol=4
        )
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_day_pair(path, 0, 5)


class _Malicious:
    def __reduce__(self):
        return eval, ("1 + 1",)


def test_unlisted_global_is_blocked() -> None:
    payload = pickle.dumps(_Malicious(), protocol=4)
    with pytest.raises(pickle.UnpicklingError, match="blocked pickle global"):
        restricted_loads(payload)
