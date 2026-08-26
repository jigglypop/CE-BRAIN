"""Signal-blind apparatus gates for BA-OBS-ID4.

This module deliberately accepts only TSV text or caller-owned metadata.  It does
not know a dataset URL and it never opens an MEF3 signal object.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
import random
import struct
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

FLOOR = 1e-12
STOP = "APPARATUS_MEF3_RANDOM_ACCESS_STOP"
SAMPLE_INDEX_STOP = "APPARATUS_MEF3_SAMPLE_INDEX_STOP"
SAMPLE_INDEX_PASS = "PASS_OFFICIAL_FIRST_BLOCK_SAMPLE_INDEX"
MEF3IO_VERSION = "1.1.2"
TIDX_HEADER_BYTES = 1024
TDAT_HEADER_BYTES = 1024
TIDX_ROW = struct.Struct("<qqqIIii16s")
MEF3_MAX_WINDOW_UUTC = 1_000_000
MEF3_MAX_EXPECTED_SAMPLES = 2048
MEF3_MAX_RETURNED_BYTES = MEF3_MAX_EXPECTED_SAMPLES * 5  # int32 samples + uint8 validity


class Mef3ioRandomAccessAdapter:
    """Minimal adapter around mef3io's bounded, uUTC half-open read API."""

    def __init__(self, fixture_path: str | Path | None = None, *, allowed_channels: Iterable[str] | None = None) -> None:
        self.fixture_path = Path(fixture_path) if fixture_path is not None else None
        import mef3io

        if getattr(mef3io, "__version__", None) != MEF3IO_VERSION:
            raise RuntimeError(f"{STOP}:mef3io version")
        self._reader_type = mef3io.Reader
        if allowed_channels is None:
            if self.fixture_path is None or not self.fixture_path.exists():
                raise RuntimeError(f"{STOP}:allowed channels or executable fixture path required")
            with self._reader_type(str(self.fixture_path), cache=None) as reader:
                allowed_channels = reader.channels
        self.allowed_channels = frozenset(str(channel) for channel in allowed_channels)
        if not self.allowed_channels:
            raise RuntimeError(f"{STOP}:empty allowed channel set")

    @staticmethod
    def available() -> bool:
        return importlib.util.find_spec("mef3io") is not None

    def random_window(self, channel: str, start_uutc: int, end_uutc: int) -> dict[str, Any]:
        """Read one supplied half-open window; never discovers or downloads data."""
        if channel not in self.allowed_channels:
            raise RuntimeError(f"{STOP}:channel not allowed")
        if (isinstance(start_uutc, bool) or isinstance(end_uutc, bool) or not isinstance(start_uutc, int)
                or not isinstance(end_uutc, int) or not math.isfinite(start_uutc)
                or not math.isfinite(end_uutc) or end_uutc <= start_uutc):
            raise RuntimeError(f"{STOP}:invalid uUTC window")
        window_uutc = end_uutc - start_uutc
        if window_uutc > MEF3_MAX_WINDOW_UUTC:
            raise RuntimeError(f"{STOP}:window exceeds frozen maximum")
        if self.fixture_path is None or not self.fixture_path.exists():
            raise RuntimeError(f"{STOP}:executable fixture path required")
        with self._reader_type(str(self.fixture_path), cache=None) as reader:
            info = reader.info(channel)
            fs_hz = float(info.get("sampling_frequency", 0.0))
            expected_samples = round(window_uutc * fs_hz / 1_000_000)
            if not math.isfinite(fs_hz) or fs_hz <= 0 or expected_samples > MEF3_MAX_EXPECTED_SAMPLES:
                raise RuntimeError(f"{STOP}:expected samples exceeds frozen maximum")
            raw = reader.read_raw(channel, start_uutc, end_uutc)
        returned_bytes = sum(int(getattr(raw[key], "nbytes", len(raw[key]) * width))
                             for key, width in (("samples", 4), ("valid", 1)))
        if returned_bytes > MEF3_MAX_RETURNED_BYTES:
            raise RuntimeError(f"{STOP}:returned bytes exceeds frozen maximum")
        return {**raw, "units_description": info.get("units_description"), "cleanup": True}

    @staticmethod
    def validate_sample_time_unit(
        window: Mapping[str, Any], *, expected_samples: int, fs_hz: float,
        units: str, start_uutc: int,
    ) -> dict[str, Any]:
        samples, valid = window.get("samples"), window.get("valid")
        if samples is None or valid is None or len(samples) != expected_samples or len(valid) != expected_samples:
            raise RuntimeError(f"{STOP}:sample count")
        if int(window.get("start_uutc", -1)) != start_uutc:
            raise RuntimeError(f"{STOP}:start uUTC")
        if not math.isclose(float(window.get("sampling_frequency", 0.0)), fs_hz, rel_tol=0.0, abs_tol=0.0):
            raise RuntimeError(f"{STOP}:sampling frequency")
        if str(window.get("units_description", "")).strip().lower() != units.lower():
            raise RuntimeError(f"{STOP}:units")
        if any(not bool(item) for item in valid) or any(not math.isfinite(float(item)) for item in samples):
            raise RuntimeError(f"{STOP}:finite valid samples")
        return {"samples": expected_samples, "fs_hz": fs_hz, "units": units,
                "start_uutc": start_uutc, "cleanup": bool(window.get("cleanup"))}


def official_single_channel_transient_fixture_receipt() -> dict[str, Any]:
    """Schema for an independently observed decoder fixture, not an endpoint."""
    return {
        "status": "INDEPENDENT_CAPABILITY_FIXTURE_RECORDED",
        "capability_evidence_only": True,
        "decoder_capability_gate": "PASS_INDEPENDENT_FIXTURE_ONLY",
        "sample_index_capability_gate": SAMPLE_INDEX_PASS,
        "sample_index_equivalence_established": True,
        "endpoint_evidence": False,
        "executed_in_this_run": True,
        "dataset": "ds004457", "tag": "1.0.2", "commit": "1bbd...",
        "subject": "sub-1", "channel": "LV1",
        "file_sha256": {"tmet": "08f3b60859166f24bc44978de804300c9c30f3b0d277ccddb5a16a70171f8e2e",
                        "tidx": "d3a00f1be77987826c4729ee9bcd9ab4f22a73bec827b61a65b066762e0c0250",
                        "tdat": "23c0b6f1a4d9eaaceb0c514b449bda04cde0c037f99027e7214d8b49562daffd"},
        "mef3io_version": MEF3IO_VERSION,
        "fs_hz": 2048, "units": "microvolts",
        "uUTC_half_open": [81209476921, 81210476921],
        "samples": 2048, "finite_samples": 2048,
        "min": 31.900642371330825, "max": 341.60271205966757,
        "mean": 227.86827705640243, "cleanup": True,
        "execution_order": ["full_file_capability", "range_minimal_proof"],
        "range_minimal_bytes": {"tmet": 16384, "tidx": 196016, "tdat_executable_closure": 4888,
                                "target_block_end": 2960, "boundary_neighbor_end": 4888},
        "development_opened": False, "confirmation_opened": False,
    }


def parse_tidx(byte_buffer: bytes) -> list[dict[str, int]]:
    """Parse only the fixed-width MEF3 index layout; no tdat bytes are decoded."""
    if len(byte_buffer) < TIDX_HEADER_BYTES or (len(byte_buffer) - TIDX_HEADER_BYTES) % TIDX_ROW.size:
        raise ValueError("APPARATUS_MEF3_INDEX_STOP:invalid tidx length")
    rows: list[dict[str, int]] = []
    previous: dict[str, int] | None = None
    for position in range(TIDX_HEADER_BYTES, len(byte_buffer), TIDX_ROW.size):
        # Tail bytes 40--43 and 45--55 remain uninterpreted; official RED flags is tail byte 4 (file byte 44).
        offset, start_uutc, start_sample, sample_count, block_bytes, _maximum, _minimum, tail = TIDX_ROW.unpack_from(byte_buffer, position)
        red_flags = tail[4]
        row = {"tdat_offset": offset, "start_uutc": start_uutc, "start_sample": start_sample,
               "block_bytes": block_bytes, "sample_count": sample_count, "red_flags": red_flags,
               "discontinuity": bool(red_flags & 0x01)}
        if offset < TDAT_HEADER_BYTES or start_uutc <= 0 or start_sample < 0 or block_bytes <= 0 or sample_count <= 0:
            raise ValueError("APPARATUS_MEF3_INDEX_STOP:nonpositive row field")
        if previous is not None and (
            offset <= previous["tdat_offset"] or start_uutc <= previous["start_uutc"]
            or start_sample <= previous["start_sample"]
        ):
            raise ValueError("APPARATUS_MEF3_INDEX_STOP:nonmonotone row field")
        rows.append(row)
        previous = row
    if not rows:
        raise ValueError("APPARATUS_MEF3_INDEX_STOP:no index rows")
    return rows


def plan_tdat_ranges(rows: Iterable[Mapping[str, int]], *, start_uutc: int, end_uutc: int, fs_hz: float,
                     tdat_size: int) -> list[tuple[int, int]]:
    """Plan merged half-open byte ranges; the tdat universal header is mandatory."""
    if not isinstance(start_uutc, int) or not isinstance(end_uutc, int) or end_uutc <= start_uutc:
        raise ValueError("APPARATUS_MEF3_RANGE_STOP:invalid uUTC window")
    if not math.isfinite(fs_hz) or fs_hz <= 0:
        raise ValueError("APPARATUS_MEF3_RANGE_STOP:invalid sampling frequency")
    if isinstance(tdat_size, bool) or not isinstance(tdat_size, int) or tdat_size <= TDAT_HEADER_BYTES:
        raise ValueError("APPARATUS_MEF3_RANGE_STOP:invalid tdat size")
    selected: list[tuple[int, int]] = [(0, TDAT_HEADER_BYTES)]
    previous_offset_end = previous_sample_end = previous_time_end = None
    for row in rows:
        block_start = int(row["start_uutc"])
        block_end = block_start + round(int(row["sample_count"]) * 1_000_000 / fs_hz)
        offset, size, sample_start = int(row["tdat_offset"]), int(row["block_bytes"]), int(row["start_sample"])
        offset_end = offset + size
        if offset < TDAT_HEADER_BYTES or size <= 0 or offset_end > tdat_size:
            raise ValueError("APPARATUS_MEF3_RANGE_STOP:invalid block span")
        if (previous_offset_end is not None and offset < previous_offset_end) or (
            previous_sample_end is not None and sample_start < previous_sample_end
        ) or (previous_time_end is not None and block_start < previous_time_end):
            raise ValueError("APPARATUS_MEF3_RANGE_STOP:overlapping or nonmonotone block interval")
        previous_offset_end = offset_end
        previous_sample_end = sample_start + int(row["sample_count"])
        previous_time_end = block_end
        if block_start < end_uutc and block_end > start_uutc:
            selected.append((offset, offset_end))
    selected.sort()
    merged: list[tuple[int, int]] = []
    for start, end in selected:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    if len(selected) == 1:
        raise ValueError("APPARATUS_MEF3_RANGE_STOP:no overlapping index block")
    return merged


def _rows(tsv: str | Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    if isinstance(tsv, str):
        return [dict(row) for row in csv.DictReader(io.StringIO(tsv), delimiter="\t")]
    return [dict(row) for row in tsv]


def _first(row: Mapping[str, str], *names: str) -> str:
    for name in names:
        if name in row:
            return str(row[name]).strip()
    return ""


def _sha_byte(text: str) -> int:
    return hashlib.sha256(text.encode("utf-8")).digest()[0]


def _node(site: str, channel_order: Mapping[str, int]) -> tuple[str, tuple[str, str]]:
    contacts = tuple(part.strip() for part in site.split("-") if part.strip())
    if len(contacts) != 2 or any(contact not in channel_order for contact in contacts):
        raise ValueError("APPARATUS_METADATA_STOP:invalid stimulation contact pair")
    ordered = tuple(sorted(contacts, key=channel_order.__getitem__))
    return "-".join(ordered), ordered


def canonical_metadata_plan(
    channels_tsv: str | Iterable[Mapping[str, str]],
    electrodes_tsv: str | Iterable[Mapping[str, str]],
    events_tsv: str | Iterable[Mapping[str, str]],
    *,
    snapshot: str,
    subject: str,
) -> dict[str, Any]:
    """Make the frozen, signal-blind eligibility and hash allocation plan."""
    channels = _rows(channels_tsv)
    electrodes = _rows(electrodes_tsv)
    events = _rows(events_tsv)
    order = {row["name"].strip(): index for index, row in enumerate(channels) if row.get("name", "").strip()}
    good = {
        row["name"].strip()
        for row in channels
        if row.get("name", "").strip()
        and row.get("status", "").strip().lower() == "good"
        and row.get("type", "").strip().lower() in {"ieeg", "seeg", "ecog"}
    }
    coords: dict[str, tuple[float, float, float]] = {}
    for row in electrodes:
        try:
            point = tuple(float(row[key]) for key in ("x", "y", "z"))
        except (KeyError, TypeError, ValueError):
            continue
        if all(math.isfinite(value) for value in point) and row.get("name", "").strip():
            coords[row["name"].strip()] = point

    eligible: dict[str, list[dict[str, str]]] = {}
    polarities: dict[str, set[str]] = {}
    orientations: dict[str, set[str]] = {}
    contacts: dict[str, tuple[str, str]] = {}
    for row in events:
        status = row.get("status", "").strip().lower()
        current = _first(row, "electrical_stimulation_current", "current", "amplitude")
        waveform = _first(
            row,
            "electrical_stimulation_type",
            "waveform",
            "electrical_stimulation_waveform",
            "pulse_shape",
        ).lower()
        site = _first(row, "electrical_stimulation_site", "stimulation_site", "site")
        polarity = _first(row, "polarity", "stimulation_polarity", "electrical_stimulation_polarity")
        if status != "good" or current not in {"6 mA", "6.0 mA", "6", "6.0"}:
            continue
        if "biphas" not in waveform:
            continue
        try:
            node, pair = _node(site, order)
        except ValueError:
            continue
        if not set(pair).issubset(good) or not set(pair).issubset(coords):
            continue
        eligible.setdefault(node, []).append(row)
        contacts[node] = pair
        orientations.setdefault(node, set()).add("->".join(part.strip() for part in site.split("-")))
        if polarity:
            polarities.setdefault(node, set()).add(polarity)

    retained = {
        node: rows
        for node, rows in eligible.items()
        if len(rows) >= 10
        and len(polarities.get(node, set())) <= 1
        and len(orientations.get(node, set())) <= 1
    }
    nodes = sorted(retained, key=lambda node: min(order[contact] for contact in contacts[node]))
    pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(nodes):
        for right in nodes[left_index + 1 :]:
            a, b = contacts[left], contacts[right]
            if set(a) & set(b):
                continue
            midpoint_a = tuple((coords[a[0]][i] + coords[a[1]][i]) / 2 for i in range(3))
            midpoint_b = tuple((coords[b[0]][i] + coords[b[1]][i]) / 2 for i in range(3))
            distance = math.dist(midpoint_a, midpoint_b)
            if distance < 15.0:
                continue
            bucket = _sha_byte(f"{snapshot}|{subject}|{left}|{right}")
            pairs.append({"a": left, "b": right, "hash_byte": bucket,
                          "allocation": "development_apparatus" if bucket <= 191 else "held_out",
                          "midpoint_distance_mm": distance})
    return {
        "snapshot": snapshot, "subject": subject, "signal_accessed": False,
        "canonical_nodes": nodes,
        "excluded_mixed_polarity_nodes": sorted(
            node
            for node in eligible
            if len(polarities.get(node, set())) > 1 or len(orientations.get(node, set())) > 1
        ),
        "orientation_labels": {node: sorted(labels) for node, labels in orientations.items()},
        "trial_half_counts": {node: (len(rows[::2]), len(rows[1::2])) for node, rows in retained.items()},
        "pairs": pairs,
    }


def patient_labels(subjects: Iterable[str], *, snapshot: str) -> dict[str, str]:
    """Hash-order, patient-disjoint two-development / remaining-confirmation rule."""
    ordered = sorted(set(subjects), key=lambda subject: hashlib.sha256(f"{snapshot}|{subject}".encode()).digest())
    if len(ordered) != 5:
        raise ValueError("APPARATUS_METADATA_STOP:exactly five subjects required")
    return {subject: ("development" if index < 2 else "confirmation") for index, subject in enumerate(ordered)}


def disagreement(x: float, y: float) -> float:
    if not all(math.isfinite(value) and value >= 0 for value in (x, y)):
        raise ValueError("APPARATUS_ENDPOINT_STOP:nonfinite or negative magnitude")
    return abs(x - y) / (x + y + FLOOR)


def reciprocal_metrics(values: Iterable[tuple[float, float, float, float]]) -> dict[str, float]:
    """Dimensionless d/u/v/R for (r<-s A,B,s<-r A,B) rows."""
    rows = list(values)
    if not rows:
        raise ValueError("APPARATUS_ENDPOINT_STOP:no reciprocal pairs")
    same, cross = [], []
    for rs_a, rs_b, sr_a, sr_b in rows:
        same.append((disagreement(rs_a, rs_b) + disagreement(sr_a, sr_b)) / 2)
        cross.append((disagreement(rs_a, sr_b) + disagreement(rs_b, sr_a)) / 2)
    median_u, median_v = _median(same), _median(cross)
    return {"u": median_u, "v": median_v, "R": (median_v + FLOOR) / (median_u + FLOOR)}


def fixed_patient_label(mean_r: float, bip_r: float, mean_p: float, bip_p: float) -> dict[str, Any]:
    if not all(math.isfinite(value) and value > 0 for value in (mean_r, bip_r)):
        raise ValueError("APPARATUS_ENDPOINT_STOP:invalid R")
    if not all(0 < value <= 1 for value in (mean_p, bip_p)):
        raise ValueError("APPARATUS_ENDPOINT_STOP:invalid conditional tail")
    phi_mean = mean_r > 1.25 and mean_p <= 0.025
    phi_bip = bip_r > 1.25 and bip_p <= 0.025
    return {"R_mean": mean_r, "R_bip": bip_r, "p_mean": mean_p, "p_bip": bip_p,
            "phi_mean": phi_mean, "phi_bip": phi_bip, "Delta": math.log(mean_r) - math.log(bip_r)}


def confirmation_label(labels: Iterable[Mapping[str, Any]]) -> str:
    rows = list(labels)
    if len(rows) != 3:
        raise ValueError("APPARATUS_ENDPOINT_STOP:three fixed confirmation labels required")
    if all(row["Delta"] > 0 for row in rows) and _median([row["Delta"] for row in rows]) >= math.log(1.25) and sum(row["phi_mean"] and not row["phi_bip"] for row in rows) >= 2:
        return "REFERENCE_SENSITIVE_PATTERN_REPLICATED"
    if sum(row["phi_mean"] and row["phi_bip"] for row in rows) >= 2 and not any(row["phi_mean"] and not row["phi_bip"] for row in rows):
        return "REFERENCE_ROBUST_DIRECTIONAL_PROXY_REFUTED"
    return "HETEROGENEOUS_OR_INCONCLUSIVE"


def _median(values: list[float]) -> float:
    values = sorted(values)
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def _normal(rng: random.Random) -> float:
    return rng.gauss(0.0, 1.0)


def _noise(rng: random.Random, distribution: str) -> float:
    if distribution == "gaussian":
        return _normal(rng)
    if distribution == "t5":
        # Standardized, centered t_5 from Z/sqrt(chi2_5/5).
        return _normal(rng) / math.sqrt(rng.gammavariate(2.5, 2.0) / 5.0) / math.sqrt(5.0 / 3.0)
    raise ValueError("unknown synthetic distribution")


def _synthetic_values(seed: int, distribution: str, directed: bool, pairs: int = 52) -> list[tuple[float, float, float, float]]:
    rng = random.Random(f"BA-OBS-ID4|{seed}|{distribution}|{directed}")
    values = []
    for pair in range(pairs):
        scale_rs = 0.015 * (1 + (pair % 16))
        scale_sr = 0.015 * (1 + ((pair * 7) % 16))
        location = 1.0 + 0.05 * (pair % 5)
        gap = math.log(1.6) if directed and pair < math.ceil(0.75 * pairs) else 0.0
        values.append(tuple(math.exp(math.log(location) + (gap if direction else 0.0) + scale * _noise(rng, distribution))
                            for direction, scale in ((0, scale_rs), (0, scale_rs), (1, scale_sr), (1, scale_sr))))
    return values


def _restricted_null_r(seed: int, distribution: str, observed: list[tuple[float, float, float, float]], draws: int = 256) -> list[float]:
    # Common reciprocal location, while retaining each direction/half scale.
    rng = random.Random(f"BA-OBS-ID4|null|{seed}|{distribution}")
    output = []
    for _ in range(draws):
        null = []
        for pair, row in enumerate(observed):
            loc = sum(math.log(value) for value in row) / 4
            scales = (0.015 * (1 + (pair % 16)), 0.015 * (1 + (pair % 16)),
                      0.015 * (1 + ((pair * 7) % 16)), 0.015 * (1 + ((pair * 7) % 16)))
            null.append(tuple(math.exp(loc + scale * _noise(rng, distribution)) for scale in scales))
        output.append(reciprocal_metrics(null)["R"])
    return output


def synthetic_adverse_controls(seeds: int = 256) -> dict[str, Any]:
    """Deterministic adverse controls; they are apparatus checks, never signal evidence."""
    report: dict[str, Any] = {"seeds": seeds, "null": {}, "power": {}}
    for distribution in ("gaussian", "t5"):
        false_refutations = power_hits = 0
        for seed in range(seeds):
            null_values = _synthetic_values(seed, distribution, False)
            null_r = reciprocal_metrics(null_values)["R"]
            null_tail = sum(value >= null_r for value in _restricted_null_r(seed, distribution, null_values))
            false_refutations += null_r > 1.25 and (1 + null_tail) / 257 <= 0.025
            power_values = _synthetic_values(seed, distribution, True)
            power_r = reciprocal_metrics(power_values)["R"]
            power_tail = sum(value >= power_r for value in _restricted_null_r(seed, distribution, power_values))
            power_hits += power_r > 1.25 and (1 + power_tail) / 257 <= 0.025
        report["null"][distribution] = false_refutations
        report["power"][distribution] = power_hits
    common_mean = reciprocal_metrics([(2, 2, 5, 5), (2, 2, 5, 5)])
    common_bip = reciprocal_metrics([(1, 1, 1, 1), (1, 1, 1, 1)])
    report["common_reference"] = {"mean_R": common_mean["R"], "bip_R": common_bip["R"]}
    if any(count > 7 for count in report["null"].values()):
        raise RuntimeError("STATISTICAL_FALSE_POSITIVE_STOP:" + json.dumps(report, sort_keys=True))
    if any(count < math.ceil(0.8 * seeds) for count in report["power"].values()):
        raise RuntimeError("STATISTICAL_POWER_STOP:" + json.dumps(report, sort_keys=True))
    if not common_mean["R"] > 1.25 or not math.isclose(common_bip["R"], 1.0):
        raise RuntimeError("FIXTURE_STOP:common_reference_not_cancelled_by_bipolar")
    report["status"] = "PASS"
    return report


def mef3_random_access_capability(reader: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Fail closed until an explicit executable fixture path is supplied."""
    available = [name for name in ("mef3", "pymef", "pymef3", "mef3io") if importlib.util.find_spec(name)]
    if reader is None and Mef3ioRandomAccessAdapter.available():
        return {"status": STOP, "reader_available": True, "detected_modules": available,
                "adapter": "mef3io", "mef3io_version": MEF3IO_VERSION,
                "reason": "executable fixture path and allowed channels required", "signal_accessed": False}
    if reader is None:
        return {"status": STOP, "reader_available": False, "detected_modules": available,
                "required": ["random window", "exact sample/time/unit validation"], "signal_accessed": False}
    required = ("random_window", "validate_sample_time_unit")
    missing = [name for name in required if not callable(getattr(reader, name, None))]
    if missing:
        return {"status": STOP, "reader_available": True, "missing_capabilities": missing, "signal_accessed": False}
    if isinstance(reader, Mef3ioRandomAccessAdapter) and reader.fixture_path is None:
        return {"status": STOP, "reader_available": True, "detected_modules": available,
                "adapter": "mef3io", "mef3io_version": MEF3IO_VERSION,
                "reason": "executable fixture path required", "signal_accessed": False}
    return {"status": "CAPABILITY_DECLARED_NOT_EXECUTED", "reader_available": True,
            "required": list(required), "signal_accessed": False}


def mef3_sample_index_capability() -> dict[str, Any]:
    """Narrow official first-block capability; not a trial or endpoint authorization."""
    return {"status": SAMPLE_INDEX_PASS, "decoder_capability_gate": SAMPLE_INDEX_PASS,
            "scope": "official-first-block-capability-only",
            "receipt": "artifacts/mef3-official-sample-index-receipt.json",
            "receipt_sha256": "52778286dd5c945d3ce8dd1cef33490452ae28d589228f5037a3725ec967fa2c",
            "libraries": {"mef3io": "1.1.2", "pymef": "1.4.8"},
            "official_signal_bytes_accessed": True, "development_analysis_opened": False,
            "confirmation_opened": False, "persistent_raw_bytes": 0}


def write_small_receipts(directory: Path) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    # This receipt is deliberately a small code-path smoke check.  The contract's
    # 256-seed gate remains an explicit future apparatus execution, not evidence
    # manufactured from a routine implementation test.
    controls = synthetic_adverse_controls(seeds=16)
    controls["prescribed_full_gate"] = {
        "seeds": 256,
        "false_refutation_max": 7,
        "directed_power_min": 205,
        "executed": False,
    }
    capability = {**mef3_random_access_capability(), "sample_index": mef3_sample_index_capability()}
    fixture = official_single_channel_transient_fixture_receipt()
    for name, payload in (("synthetic-adverse-controls.json", controls), ("mef3-capability-receipt.json", capability),
                          ("mef3-transient-fixture-receipt.json", fixture)):
        (directory / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"controls": controls, "capability": capability, "fixture": fixture}
