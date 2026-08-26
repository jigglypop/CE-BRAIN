"""Bounded official MEF3 first-block capability fixture for the sample-index gate."""
from __future__ import annotations

import hashlib
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any, Mapping, Protocol
from unittest.mock import patch

import numpy as np

import id4_development_index_acquire as acquire
from id4_ccep_apparatus import parse_tidx
from id4_sample_index_decoder import read_exact_sample_window

SNAPSHOT = "ds004457-v1.0.2"
SUBJECT = "sub-1"
CHANNEL = "LV1"
TMET_BYTES = 16_384
TIDX_BYTES = 196_016
TDAT_PREFIX_BYTES = 2_960
TDAT_CLOSURE_BYTES = 4_888
EXPECTED_FIRST_SAMPLES = 2_048
PASS = "PASS_OFFICIAL_FIRST_BLOCK_SAMPLE_INDEX"
STOP = "APPARATUS_MEF3_SAMPLE_INDEX_STOP"


class FixtureTransport(Protocol):
    def get(self, url: str, *, timeout: int, max_bytes: int) -> bytes: ...
    def head(self, url: str, *, timeout: int) -> Mapping[str, str]: ...
    def get_range_with_metadata(self, url: str, *, start: int, end: int, timeout: int,
                                max_bytes: int) -> Mapping[str, Any]: ...


def _paths() -> dict[str, str]:
    pair = acquire._channel_paths(SUBJECT, CHANNEL)
    stem = pair["tidx"][:-5]
    return {"tmet": stem + ".tmet", **pair}


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _header(headers: Mapping[str, str], name: str) -> str:
    return acquire._header(headers, name)


def run_official_first_block_fixture(transport: FixtureTransport) -> dict[str, Any]:
    """Acquire only LV1 metadata/index/first block, compare two readers, then delete it."""
    paths = _paths()
    pointers: dict[str, bytes] = {}
    identities: dict[str, dict[str, Any]] = {}
    bodies: dict[str, bytes] = {}
    for extension in ("tmet", "tidx", "tdat"):
        pointer = transport.get(acquire._url(acquire.RAW_PREFIX, paths[extension]),
                                timeout=acquire.TIMEOUT_SECONDS, max_bytes=acquire.MAX_POINTER_BYTES)
        sha256, size = acquire._annex(pointer)
        pointers[extension] = pointer
        identities[extension] = {"sha256": sha256, "bytes": size, "pointer_sha256": _sha(pointer)}
    if identities["tmet"]["bytes"] != TMET_BYTES or identities["tidx"]["bytes"] != TIDX_BYTES:
        raise RuntimeError(f"{STOP}:frozen metadata size")
    for extension, maximum in (("tmet", TMET_BYTES), ("tidx", TIDX_BYTES)):
        body = transport.get(acquire._url(acquire.S3_PREFIX, paths[extension]),
                             timeout=acquire.TIMEOUT_SECONDS, max_bytes=maximum)
        if len(body) != identities[extension]["bytes"] or _sha(body) != identities[extension]["sha256"]:
            raise RuntimeError(f"{STOP}:{extension} identity")
        bodies[extension] = body
    rows = parse_tidx(bodies["tidx"])
    first = rows[0]
    second = rows[1]
    expected_prefix = first["tdat_offset"] + first["block_bytes"]
    if (first["tdat_offset"] != 1024 or first["start_sample"] != 0
            or first["sample_count"] != EXPECTED_FIRST_SAMPLES or first["red_flags"] != 1
            or second["start_sample"] != EXPECTED_FIRST_SAMPLES or second["discontinuity"]
            or expected_prefix != TDAT_PREFIX_BYTES):
        raise RuntimeError(f"{STOP}:first TOC row")
    tdat_headers = transport.head(acquire._url(acquire.S3_PREFIX, paths["tdat"]), timeout=acquire.TIMEOUT_SECONDS)
    if int(_header(tdat_headers, "Content-Length")) != identities["tdat"]["bytes"]:
        raise RuntimeError(f"{STOP}:tdat object size")
    target_range = transport.get_range_with_metadata(
        acquire._url(acquire.S3_PREFIX, paths["tdat"]), start=0, end=TDAT_PREFIX_BYTES - 1,
        timeout=acquire.TIMEOUT_SECONDS, max_bytes=TDAT_PREFIX_BYTES)
    neighbor_range = transport.get_range_with_metadata(
        acquire._url(acquire.S3_PREFIX, paths["tdat"]), start=TDAT_PREFIX_BYTES, end=TDAT_CLOSURE_BYTES - 1,
        timeout=acquire.TIMEOUT_SECONDS, max_bytes=TDAT_CLOSURE_BYTES - TDAT_PREFIX_BYTES)
    target_prefix = bytes(target_range["body"])
    neighbor = bytes(neighbor_range["body"])
    prefix = target_prefix + neighbor
    if (len(target_prefix) != TDAT_PREFIX_BYTES or len(prefix) != TDAT_CLOSURE_BYTES
            or int(target_range["object_bytes"]) != identities["tdat"]["bytes"]
            or int(neighbor_range["object_bytes"]) != identities["tdat"]["bytes"]
            or second["tdat_offset"] + second["block_bytes"] != TDAT_CLOSURE_BYTES):
        raise RuntimeError(f"{STOP}:tdat range identity")
    tdat_headers_after = transport.head(acquire._url(acquire.S3_PREFIX, paths["tdat"]),
                                        timeout=acquire.TIMEOUT_SECONDS)
    for name in ("Content-Length", "ETag", "x-amz-version-id"):
        if _header(tdat_headers_after, name) != _header(tdat_headers, name):
            raise RuntimeError(f"{STOP}:tdat source changed during ranges")

    cleanup = False
    with tempfile.TemporaryDirectory(prefix="ce-official-mef3-index-") as temporary:
        root = Path(temporary)
        session_path = root / f"{SUBJECT}_ses-ieeg01_task-ccep_run-01_ieeg.mefd"
        segment = session_path / f"{CHANNEL}.timd" / f"{CHANNEL}-000000.segd"
        segment.mkdir(parents=True)
        stem = segment / f"{CHANNEL}-000000"
        stem.with_suffix(".tmet").write_bytes(bodies["tmet"])
        stem.with_suffix(".tidx").write_bytes(bodies["tidx"])
        with stem.with_suffix(".tdat").open("wb") as handle:
            handle.write(prefix)
            handle.truncate(identities["tdat"]["bytes"])
        with patch.dict(os.environ, {"LOCALAPPDATA": temporary}):
            import mef3io

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                with mef3io.Reader(str(session_path), n_threads=1, cache=None) as reader:
                    info = reader.info(CHANNEL)
                    toc = reader.toc(CHANNEL)
                    raw = reader.read_raw(CHANNEL, first["start_uutc"], rows[1]["start_uutc"])
                independent = np.asarray(raw["samples"])
                direct = read_exact_sample_window(session_path, CHANNEL, 0, EXPECTED_FIRST_SAMPLES,
                                                  allowed_channels=[CHANNEL],
                                                  total_samples=rows[-1]["start_sample"] + rows[-1]["sample_count"],
                                                  max_window_samples=EXPECTED_FIRST_SAMPLES)
            warning_text = [str(item.message) for item in caught]
            if warning_text:
                raise RuntimeError(f"{STOP}:decoder warning:{warning_text[0]}")
        if (len(toc) < 1 or int(toc[0]["start_sample"]) != 0
                or int(toc[0]["number_of_samples"]) != EXPECTED_FIRST_SAMPLES):
            raise RuntimeError(f"{STOP}:official TOC identity")
        if (len(independent) != EXPECTED_FIRST_SAMPLES or len(direct) != EXPECTED_FIRST_SAMPLES
                or not np.all(np.isfinite(independent)) or not np.array_equal(direct, independent, equal_nan=False)):
            raise RuntimeError(f"{STOP}:official value identity")
        canonical_direct = np.ascontiguousarray(direct, dtype=np.float64)
        canonical_independent = np.ascontiguousarray(independent, dtype=np.float64)
        direct_sha = hashlib.sha256(canonical_direct.tobytes()).hexdigest()
        independent_sha = hashlib.sha256(canonical_independent.tobytes()).hexdigest()
        statistics = {"min": float(np.min(direct)), "max": float(np.max(direct)),
                      "mean": float(np.mean(direct))}
        fs_hz = float(info["sampling_frequency"])
        units = str(info["units_description"])
        if fs_hz != 2048.0 or units.strip().lower() != "microvolts":
            raise RuntimeError(f"{STOP}:official sample rate or units")
        cleanup = True
    if not cleanup or session_path.exists():
        raise RuntimeError(f"{STOP}:official fixture cleanup")
    return {
        "status": PASS, "scope": "official-first-block-capability-only",
        "implementation_sha256": _sha(Path(__file__).read_bytes()),
        "snapshot": SNAPSHOT, "commit": acquire.COMMIT, "subject": SUBJECT, "channel": CHANNEL,
        "source_paths": paths, "objects": identities,
        "tdat_s3": {"etag": _header(tdat_headers, "ETag"),
                    "version_id": _header(tdat_headers, "x-amz-version-id"),
                    "source_identity_stable_before_after_ranges": True,
                    "ranges": [
                        {"content_range": str(target_range["content_range"]),
                         "sha256": _sha(target_prefix), "bytes": len(target_prefix), "role": "target"},
                        {"content_range": str(neighbor_range["content_range"]),
                         "sha256": _sha(neighbor), "bytes": len(neighbor), "role": "boundary-neighbor"}],
                    "closure_sha256": _sha(prefix), "closure_bytes": len(prefix)},
        "first_toc_row": first, "second_toc_continuity": {
            "start_sample": second["start_sample"], "red_flags": second["red_flags"],
            "discontinuity": second["discontinuity"]}, "fs_hz": fs_hz, "units": units,
        "sample_window_half_open": [0, EXPECTED_FIRST_SAMPLES], "samples": len(direct),
        "direct_sha256": direct_sha, "independent_sha256": independent_sha,
        "canonical_hash_dtype": "float64", "cross_library_value_identity": direct_sha == independent_sha,
        "statistics_stored_counts": statistics, "decoder_warnings": [],
        "official_dataset_equivalence_established": True, "official_decoder_stop_cleared": True,
        "official_signal_bytes_accessed": True,
        "acquired_payload_bytes": TMET_BYTES + TIDX_BYTES + TDAT_CLOSURE_BYTES,
        "transient_tdat_logical_bytes": identities["tdat"]["bytes"], "persistent_raw_bytes": 0,
        "capability_evidence_only": True, "bids_trial_opened": False,
        "development_analysis_opened": False, "endpoint_evidence": False,
        "sub5_opened": False, "confirmation_opened": False, "cleanup": cleanup,
    }
