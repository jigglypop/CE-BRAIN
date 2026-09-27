import numpy as np
import pytest

from research import malecns

pytestmark = pytest.mark.skipif(not malecns.available(), reason="MaleCNS ledger files are not on disk")


def test_data_is_the_pinned_version():
    malecns.verify()


def test_glomerulus_label():
    assert malecns.glomerulus("EPG(PB08)_L4") == ("L", 4)
    assert malecns.glomerulus("Delta7(PB15)_L1L9R8_R") is None


def test_roi_counts_add_up_to_the_graph_in_the_same_direction():
    index = malecns.neurons(["EPG", "PEN_a(PEN1)", "Delta7"])
    assert np.array_equal(malecns.weights_in(index), malecns.weights(index))


def test_transmitter_signs():
    index = malecns.neurons(["EPG", "Delta7"])
    sign = dict(zip(malecns.cell_types(index), malecns.signs(index)))
    assert sign == {"EPG": 1.0, "Delta7": -1.0}
