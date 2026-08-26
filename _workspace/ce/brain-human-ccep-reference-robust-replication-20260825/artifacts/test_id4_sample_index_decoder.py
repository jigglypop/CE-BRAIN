import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("decoder", HERE / "id4_sample_index_decoder.py")
decoder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(decoder)


def test_cross_library_fixture_proves_exact_half_open_sample_identity():
    receipt = decoder.cross_library_sample_index_fixture()
    assert receipt["status"] == "PASS_CROSS_LIBRARY_SAMPLE_INDEX_FIXTURE"
    assert receipt["sample_index_equivalence_established"] is True
    assert receipt["scope"] == "synthetic-cross-library-capability-only"
    assert not receipt["official_dataset_equivalence_established"] and not receipt["official_decoder_stop_cleared"]
    assert receipt["toc_start_samples"] == [0, 1024, 2048, 3072, 4096]
    assert receipt["toc_sample_counts"] == [1024, 1024, 1024, 1024, 1]
    assert [row["samples"] for row in receipt["windows"]] == [1, 82, 100, 1025, 1027, 1025]
    assert receipt["cleanup"] and not receipt["signal_accessed"] and not receipt["external_data_accessed"]
    for invalid in ((True, 1), (0, 0), (-1, 1), (0, decoder.MAX_WINDOW_SAMPLES + 1)):
        try:
            decoder._validate_window(*invalid)
            raise AssertionError("invalid exact sample window accepted")
        except ValueError:
            pass
    decoder._validate_window(0, 2048, total_samples=4096, max_window_samples=2048)
    known = decoder._known_counts()
    assert known.dtype == np.int32 and len(np.unique(known)) == len(known)
