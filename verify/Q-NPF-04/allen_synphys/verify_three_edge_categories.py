"""새 이동이 앞선 반례를 연결하며 범주 불일치는 거부하는지 검사한다."""
import itertools
import numpy as np
from microns_three_edge_sensitivity import three
from microns_swap_extension import validate

types = np.array([0, 0, 1, 1])
categories = (types[:, None] * 2 + types[None, :]) * 6
initial = np.zeros((4, 4), dtype=bool)
for p in [(0, 2), (0, 3), (1, 0), (2, 1)]:
    initial[p] = True
edges = np.argwhere(initial)
target = np.zeros((4, 4), dtype=bool)
for p in [(0, 1), (0, 3), (1, 2), (2, 0)]:
    target[p] = True
bridges = []
for ids in itertools.permutations(range(4), 3):
    for direction in (1, -1):
        a, e = initial.copy(), edges.copy()
        if three(a, e, ids, direction, categories):
            validate(a, e, initial, categories)
            if np.array_equal(a, target):
                bridges.append((ids, direction))
            assert three(a, e, ids, -direction, categories)
            assert np.array_equal(a, initial) and np.array_equal(e, edges)
assert len(bridges) == 6
for ids, direction in bridges:
    changed_categories = categories.copy()
    changed_categories[0, 1] += 1
    a, e = initial.copy(), edges.copy()
    assert not three(a, e, ids, direction, changed_categories)
    assert np.array_equal(a, initial) and np.array_equal(e, edges)
print('SIX_ORDERED_BRIDGES_VERIFIED_WITH_REVERSIBILITY_AND_CATEGORY_REJECTION')
