import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("signal", HERE / "id4_development_signal.py")
signal = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(signal)


def test_executable_ranges_add_only_exact_end_boundary_neighbor():
    rows = [
        {"tdat_offset": 1024, "block_bytes": 100, "start_sample": 0, "sample_count": 2048, "discontinuity": True},
        {"tdat_offset": 1124, "block_bytes": 110, "start_sample": 2048, "sample_count": 2048, "discontinuity": False},
        {"tdat_offset": 1234, "block_bytes": 120, "start_sample": 4096, "sample_count": 2048, "discontinuity": False},
    ]
    assert signal.executable_ranges(rows, [[921, 2048]], tdat_bytes=1354) == [(0, 1234)]
    assert signal.executable_ranges(rows, [[100, 1227]], tdat_bytes=1354) == [(0, 1124)]
    assert signal.executable_ranges(rows, [[2047, 3174]], tdat_bytes=1354) == [(0, 1234)]
    bad = [dict(row) for row in rows]; bad[1]["discontinuity"] = True
    try:
        signal.executable_ranges(bad, [[2047, 3174]], tdat_bytes=1354)
        raise AssertionError("discontinuous executable closure accepted")
    except ValueError:
        pass
