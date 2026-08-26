"""Cross-library, signal-free proof for exact MEF3 sample-index reads."""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable
from unittest.mock import patch

import numpy as np

FS_HZ = 2048
FIXTURE_SAMPLES = 4097
BLOCK_SAMPLES = 1024
MAX_WINDOW_SAMPLES = 1127
PYMEF_VERSION = "1.4.8"
MEF3IO_VERSION = "1.1.2"
SAMPLE_INDEX_PASS = "PASS_CROSS_LIBRARY_SAMPLE_INDEX_FIXTURE"
SAMPLE_INDEX_STOP = "APPARATUS_MEF3_SAMPLE_INDEX_STOP"


def _known_counts() -> np.ndarray:
    index = np.arange(FIXTURE_SAMPLES, dtype=np.int64)
    return np.asarray(((index * 104729 + 12345) % 2_000_003) - 1_000_001, dtype=np.int32)


def _validate_window(start: int, end: int, *, total_samples: int = FIXTURE_SAMPLES,
                     max_window_samples: int = MAX_WINDOW_SAMPLES) -> None:
    if (isinstance(start, bool) or isinstance(end, bool) or type(start) is not int or type(end) is not int
            or type(total_samples) is not int or type(max_window_samples) is not int
            or total_samples <= 0 or max_window_samples <= 0
            or start < 0 or end <= start or end > total_samples or end - start > max_window_samples):
        raise ValueError(f"{SAMPLE_INDEX_STOP}:invalid sample window")


def _pymef_version() -> str:
    import pymef

    version = str(getattr(pymef, "__version__", ""))
    if version != PYMEF_VERSION:
        raise RuntimeError(f"{SAMPLE_INDEX_STOP}:pymef version")
    return version


def read_exact_sample_window(session_path: str | Path, channel: str, start: int, end: int,
                             *, allowed_channels: Iterable[str], total_samples: int = FIXTURE_SAMPLES,
                             max_window_samples: int = MAX_WINDOW_SAMPLES) -> np.ndarray:
    """Read one exact half-open sample interval through pymef's sample API."""
    _validate_window(start, end, total_samples=total_samples, max_window_samples=max_window_samples)
    allowed = frozenset(str(item) for item in allowed_channels)
    if not allowed or channel not in allowed:
        raise RuntimeError(f"{SAMPLE_INDEX_STOP}:channel not allowed")
    path = Path(session_path)
    if path.suffix != ".mefd" or not path.is_dir():
        raise RuntimeError(f"{SAMPLE_INDEX_STOP}:executable fixture path required")
    _pymef_version()
    import pymef

    session = pymef.MefSession(str(path), "", check_all_passwords=True)
    values = np.asarray(session.read_ts_channels_sample(channel, [start, end]))
    if values.ndim != 1 or len(values) != end - start or values.nbytes > max_window_samples * 8:
        raise RuntimeError(f"{SAMPLE_INDEX_STOP}:sample cardinality")
    if not np.all(np.isfinite(values)):
        raise RuntimeError(f"{SAMPLE_INDEX_STOP}:nonfinite sample")
    return values


def cross_library_sample_index_fixture() -> dict[str, Any]:
    """Write known counts with mef3io and read exact indices with pymef."""
    import mef3io

    if str(getattr(mef3io, "__version__", "")) != MEF3IO_VERSION:
        raise RuntimeError(f"{SAMPLE_INDEX_STOP}:mef3io version")
    expected = _known_counts()
    windows = ((0, 1), (21, 103), (1000, 1100), (1024, 2049), (2047, 3074), (3072, 4097))
    checked: list[dict[str, Any]] = []
    cleanup = False
    with tempfile.TemporaryDirectory(prefix="ce-mef3-index-") as temporary:
        path = Path(temporary) / "fixture.mefd"
        with patch.dict(os.environ, {"LOCALAPPDATA": temporary}):
            with mef3io.Writer(str(path), overwrite=True, units="microvolts", block_length=BLOCK_SAMPLES,
                               n_threads=1) as writer:
                writer.write_int32("KNOWN", expected, 1.0, 81_209_476_921, FS_HZ)
        with mef3io.Reader(str(path), n_threads=1, cache=None) as reader:
            toc_mef3io = reader.toc("KNOWN")
        import pymef

        session = pymef.MefSession(str(path), "", check_all_passwords=True)
        toc_pymef = np.asarray(session.get_channel_toc("KNOWN"), dtype=np.int64)
        starts_a = [int(row["start_sample"]) for row in toc_mef3io]
        counts_a = [int(row["number_of_samples"]) for row in toc_mef3io]
        starts_b = [int(item) for item in toc_pymef[2]]
        counts_b = [int(item) for item in toc_pymef[1]]
        if starts_a != starts_b or counts_a != counts_b or starts_a != [0, 1024, 2048, 3072, 4096]:
            raise RuntimeError(f"{SAMPLE_INDEX_STOP}:cross-library TOC identity")
        for start, end in windows:
            actual = read_exact_sample_window(path, "KNOWN", start, end, allowed_channels=["KNOWN"])
            wanted = expected[start:end].astype(actual.dtype, copy=False)
            if not np.array_equal(actual, wanted, equal_nan=False):
                raise RuntimeError(f"{SAMPLE_INDEX_STOP}:sample value identity")
            checked.append({"start": start, "end": end, "samples": end - start,
                            "sha256": hashlib.sha256(np.ascontiguousarray(actual).tobytes()).hexdigest()})
        cleanup = True
    if not cleanup or path.exists():
        raise RuntimeError(f"{SAMPLE_INDEX_STOP}:fixture cleanup")
    return {"status": SAMPLE_INDEX_PASS, "mef3io_version": MEF3IO_VERSION, "pymef_version": _pymef_version(),
            "writer": "mef3io.Writer.write_int32", "reader": "pymef.MefSession.read_ts_channels_sample",
            "fs_hz": FS_HZ, "known_samples": len(expected), "block_samples": BLOCK_SAMPLES,
            "blocks": len(toc_mef3io), "toc_start_samples": starts_a, "toc_sample_counts": counts_a,
            "known_counts_sha256": hashlib.sha256(expected.tobytes()).hexdigest(), "windows": checked,
            "scope": "synthetic-cross-library-capability-only",
            "sample_index_equivalence_established": True,
            "official_dataset_equivalence_established": False,
            "official_decoder_stop_cleared": False, "signal_accessed": False,
            "external_data_accessed": False, "development_opened": False,
            "confirmation_opened": False, "cleanup": cleanup}
