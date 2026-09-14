import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "type_control", Path(__file__).resolve().parents[1] / "verify/MaleCNS/type_label_control.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_shuffle_preserves_block_margins_and_untouched_sources():
    original = np.array([1, 1, 2, 2, 3, 3, 4, 5])
    blocks = [np.array([0, 1, 2, 3]), np.array([4, 5, 6])]
    shuffled = module.shuffle_within_blocks(original, blocks, np.random.default_rng(11))
    for block in blocks:
        assert np.array_equal(np.sort(shuffled[block]), np.sort(original[block]))
    assert shuffled[7] == original[7]
    assert not np.shares_memory(shuffled, original)
    assert np.array_equal(original, [1, 1, 2, 2, 3, 3, 4, 5])
