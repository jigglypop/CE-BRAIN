"""Source-locked, signal-blind development tdat range planner for BA-OBS-ID4."""
from __future__ import annotations

import csv
import hashlib
import io
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
from typing import Any, Iterable, Mapping

from id4_ccep_apparatus import TDAT_HEADER_BYTES, canonical_metadata_plan, parse_tidx

FROZEN_SNAPSHOT = "ds004457-v1.0.2"
DEVELOPMENT_SUBJECTS = frozenset({"sub-1", "sub-5"})
EXPECTED_FS_HZ = 2048
PRECISION_CONVENTION = "decimal-onset-lexical-ulp-sample-grid-v4"
PRECISION_CONVENTION_VERSION = 4
SHARED_START_SAMPLE = 0
ACQUISITION_WINDOW_SAMPLES = (-1024, 103)
BASELINE_WINDOW_SAMPLES = (-1024, -10)
EARLY_WINDOW_SAMPLES = (21, 103)
PRESTIM_WINDOW_SAMPLES = (-512, -430)
DATASET_LABEL_COLUMNS = ("source", "dataset", "dataset_id", "snapshot")
SUBJECT_LABEL_COLUMNS = ("subject", "participant_id")
ACCEPTED_DATASET_LABELS = frozenset({FROZEN_SNAPSHOT})


def _rows(tsv: str) -> list[dict[str, str]]:
    return [dict(row) for row in csv.DictReader(io.StringIO(tsv), delimiter="\t")]


def _first(row: Mapping[str, str], *names: str) -> str:
    for name in names:
        if name in row:
            return str(row[name]).strip()
    return ""


def _merge(ranges: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _node(site: str, order: Mapping[str, int]) -> str | None:
    contacts = tuple(part.strip() for part in site.split("-") if part.strip())
    if len(contacts) != 2 or any(contact not in order for contact in contacts):
        return None
    return "-".join(sorted(contacts, key=order.__getitem__))


def _validate_event_provenance(events: list[Mapping[str, str]], *, snapshot: str, subject: str) -> None:
    """Nonblank recognized labels are locked exact strings, never aliases."""
    for row in events:
        for column in DATASET_LABEL_COLUMNS:
            value = _first(row, column)
            if value and value not in ACCEPTED_DATASET_LABELS:
                raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:event dataset label mismatch")
        for column in SUBJECT_LABEL_COLUMNS:
            value = _first(row, column)
            if value and value != subject:
                raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:event subject label mismatch")


def _onset_sample(lexeme: str, fs_hz: int) -> tuple[int, Decimal, Decimal]:
    """Map a hash-locked decimal onset to its unique compatible sample."""
    try:
        onset = Decimal(lexeme)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:invalid onset") from exc
    if not onset.is_finite():
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:invalid onset")
    product = onset * Decimal(fs_hz)
    integral = product.to_integral_value()
    if product == integral:
        return int(integral), Decimal(0), Decimal(0)
    lexical_ulp = abs(Decimal(1).scaleb(onset.as_tuple().exponent))
    half_ulp_samples = Decimal(fs_hz) * lexical_ulp / Decimal(2)
    lower = (product - half_ulp_samples).to_integral_value(rounding=ROUND_CEILING)
    upper = (product + half_ulp_samples).to_integral_value(rounding=ROUND_FLOOR)
    if lower != upper:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:ambiguous onset sample")
    sample = int(lower)
    return sample, product - Decimal(sample), half_ulp_samples


def _event_windows(events_tsv: str, channels_tsv: str, retained_nodes: set[str], *,
                   snapshot: str, subject: str, fs_hz: int) -> list[tuple[int, int]]:
    channels = _rows(channels_tsv)
    order = {row["name"].strip(): index for index, row in enumerate(channels) if row.get("name", "").strip()}
    windows: list[tuple[int, int]] = []
    mapped: set[tuple[str, int]] = set()
    events = _rows(events_tsv)
    _validate_event_provenance(events, snapshot=snapshot, subject=subject)
    for row in events:
        if row.get("status", "").strip().lower() != "good":
            continue
        if _first(row, "electrical_stimulation_current", "current", "amplitude") not in {"6 mA", "6.0 mA", "6", "6.0"}:
            continue
        if "biphas" not in _first(row, "electrical_stimulation_type", "waveform", "electrical_stimulation_waveform").lower():
            continue
        if _node(_first(row, "electrical_stimulation_site", "stimulation_site", "site"), order) not in retained_nodes:
            continue
        node = _node(_first(row, "electrical_stimulation_site", "stimulation_site", "site"), order)
        center, _, _ = _onset_sample(_first(row, "onset"), fs_hz)
        identity = (str(node), center)
        if identity in mapped:
            raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:duplicate site sample")
        mapped.add(identity)
        windows.append((center + ACQUISITION_WINDOW_SAMPLES[0], center + ACQUISITION_WINDOW_SAMPLES[1]))
    if not windows:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:no eligible event windows")
    return _merge(windows)


def development_event_table(*, snapshot: str, subject: str, events_tsv: str, channels_tsv: str,
                            electrodes_tsv: str, fs_hz: int) -> list[dict[str, Any]]:
    """Frozen eligible trials sorted within site and assigned onset-order A/B halves."""
    if snapshot != FROZEN_SNAPSHOT or subject not in DEVELOPMENT_SUBJECTS or fs_hz != EXPECTED_FS_HZ:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:locked development event table")
    metadata = canonical_metadata_plan(channels_tsv, electrodes_tsv, events_tsv,
                                       snapshot=snapshot, subject=subject)
    retained = set(metadata["canonical_nodes"])
    channels = _rows(channels_tsv)
    order = {row["name"].strip(): index for index, row in enumerate(channels) if row.get("name", "").strip()}
    events = _rows(events_tsv)
    _validate_event_provenance(events, snapshot=snapshot, subject=subject)
    grouped: dict[str, list[dict[str, Any]]] = {node: [] for node in retained}
    for source_row, row in enumerate(events):
        if row.get("status", "").strip().lower() != "good":
            continue
        if _first(row, "electrical_stimulation_current", "current", "amplitude") not in {"6 mA", "6.0 mA", "6", "6.0"}:
            continue
        if "biphas" not in _first(row, "electrical_stimulation_type", "waveform", "electrical_stimulation_waveform").lower():
            continue
        node = _node(_first(row, "electrical_stimulation_site", "stimulation_site", "site"), order)
        if node not in retained:
            continue
        center, error, half_ulp = _onset_sample(_first(row, "onset"), fs_hz)
        grouped[str(node)].append({"source_row": source_row, "node": node, "center_sample": center,
                                   "decimal_error_samples": str(error), "half_ulp_samples": str(half_ulp)})
    output: list[dict[str, Any]] = []
    for node in sorted(grouped, key=lambda item: tuple(order[part] for part in item.split("-"))):
        rows = sorted(grouped[node], key=lambda item: (item["center_sample"], item["source_row"]))
        centers = [item["center_sample"] for item in rows]
        if len(centers) < 10 or len(set(centers)) != len(centers):
            raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:invalid retained trial centers")
        for trial_index, item in enumerate(rows):
            output.append({**item, "trial_index": trial_index, "half": "A" if trial_index % 2 == 0 else "B",
                           "acquisition": [item["center_sample"] + ACQUISITION_WINDOW_SAMPLES[0],
                                           item["center_sample"] + ACQUISITION_WINDOW_SAMPLES[1]]})
    if not output:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:no development events")
    return output


def _select_union_ranges(rows: list[Mapping[str, int]], windows: list[tuple[int, int]], *, fs_hz: int,
                         tdat_size: int) -> tuple[list[tuple[int, int]], int]:
    """Validate every index row once and select sorted window/block overlaps once."""
    if isinstance(tdat_size, bool) or not isinstance(tdat_size, int) or tdat_size <= TDAT_HEADER_BYTES:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:invalid tdat size")
    selected: list[tuple[int, int]] = [(0, TDAT_HEADER_BYTES)]
    selected_blocks = 0
    window_index, cursor = 0, windows[0][0]
    previous_offset_end = previous_sample_end = None
    pending_sample_end: int | None = None
    for row in rows:
        offset, size = int(row["tdat_offset"]), int(row["block_bytes"])
        sample_start, sample_count = int(row["start_sample"]), int(row["sample_count"])
        block_sample_end, offset_end = sample_start + sample_count, offset + size
        if offset < TDAT_HEADER_BYTES or size <= 0 or offset_end > tdat_size:
            raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:invalid tdat span")
        if (previous_offset_end is not None and offset < previous_offset_end) or (
            previous_sample_end is not None and sample_start < previous_sample_end
        ):
            raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:overlapping index interval")
        previous_offset_end, previous_sample_end = offset_end, block_sample_end
        selected_this_block = False
        while window_index < len(windows) and block_sample_end > windows[window_index][0]:
            start, end = windows[window_index]
            if sample_start > cursor:
                raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:gap or uncovered window")
            if pending_sample_end is not None and (sample_start != pending_sample_end or bool(row.get("discontinuity", True))):
                raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:planned sample-index discontinuity")
            if block_sample_end > cursor and not selected_this_block:
                selected.append((offset, offset_end))
                selected_blocks += 1
                selected_this_block = True
            cursor = max(cursor, block_sample_end)
            if cursor < end:
                pending_sample_end = block_sample_end
                break
            window_index += 1
            pending_sample_end = None
            if window_index < len(windows):
                cursor = windows[window_index][0]
    if window_index != len(windows):
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:gap or uncovered window")
    return _merge(selected), selected_blocks


def plan_development_ranges(
    *, snapshot: str, subject: str, events_tsv: str, channels_tsv: str, electrodes_tsv: str,
    tidx_by_channel: Mapping[str, bytes], tdat_size_by_channel: Mapping[str, int], fs_hz: int,
) -> dict[str, Any]:
    """Return JSON-safe tdat ranges only; caller owns all source bytes and paths."""
    if snapshot != FROZEN_SNAPSHOT or subject not in DEVELOPMENT_SUBJECTS:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:source or subject not development-locked")
    if fs_hz != EXPECTED_FS_HZ:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:unexpected sampling frequency")
    metadata = canonical_metadata_plan(channels_tsv, electrodes_tsv, events_tsv, snapshot=snapshot, subject=subject)
    retained_nodes = set(metadata["canonical_nodes"])
    channel_rows = _rows(channels_tsv)
    good_channels = {row["name"].strip() for row in channel_rows if row.get("name", "").strip()
                     and row.get("status", "").strip().lower() == "good"
                     and row.get("type", "").strip().lower() in {"ieeg", "seeg", "ecog"}}
    if not tidx_by_channel or set(tidx_by_channel) != set(tdat_size_by_channel) or set(tidx_by_channel) != good_channels:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:invalid CAR75 channel inputs")
    indexes = {channel: parse_tidx(payload) for channel, payload in tidx_by_channel.items()}
    first_times = {rows[0]["start_uutc"] for rows in indexes.values()}
    first_samples = {rows[0]["start_sample"] for rows in indexes.values()}
    if len(first_times) != 1 or first_samples != {SHARED_START_SAMPLE}:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:inconsistent channel timing")
    windows = _event_windows(events_tsv, channels_tsv, retained_nodes, snapshot=snapshot, subject=subject, fs_hz=fs_hz)
    per_channel = []
    for channel in sorted(indexes):
        rows = indexes[channel]
        ranges, block_count = _select_union_ranges(rows, windows, fs_hz=fs_hz, tdat_size=tdat_size_by_channel[channel])
        per_channel.append({"snapshot": snapshot, "subject": subject, "channel": channel,
                            "ranges": [[start, end] for start, end in ranges], "block_count": block_count,
                            "bytes": sum(end - start for start, end in ranges),
                            "tidx_sha256": hashlib.sha256(tidx_by_channel[channel]).hexdigest()})
    total = sum(row["bytes"] for row in per_channel)
    return {"snapshot": snapshot, "subject": subject, "fs_hz": fs_hz,
            "precision_convention": PRECISION_CONVENTION, "precision_convention_version": PRECISION_CONVENTION_VERSION,
            "shared_first_uutc": next(iter(first_times)),
            "shared_start_sample": SHARED_START_SAMPLE, "windows_samples": [[start, end] for start, end in windows],
            "epoch_windows_samples": {"acquisition": list(ACQUISITION_WINDOW_SAMPLES), "baseline": list(BASELINE_WINDOW_SAMPLES),
                                      "early": list(EARLY_WINDOW_SAMPLES), "prestim": list(PRESTIM_WINDOW_SAMPLES)},
            "index_cardinality": {"universal_header_bytes": 1024, "entry_bytes": 56},
            "channels": per_channel,
            "aggregate": {"supplied_tidx_bytes": sum(len(payload) for payload in tidx_by_channel.values()),
                          "planned_tdat_bytes": total, "max_per_channel_planned_tdat_bytes": max(row["bytes"] for row in per_channel),
                          "planned_persistent_raw_bytes": 0, "excluded_until_supplied": ["tmet", "HTTP overhead"]},
            "signal_accessed": False}


def prepare_development_channels(*, snapshot: str, subject: str, events_tsv: str, channels_tsv: str,
                                 electrodes_tsv: str, fs_hz: int) -> tuple[set[str], set[str]]:
    if snapshot != FROZEN_SNAPSHOT or subject not in DEVELOPMENT_SUBJECTS or fs_hz != EXPECTED_FS_HZ:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:locked development contract")
    metadata = canonical_metadata_plan(channels_tsv, electrodes_tsv, events_tsv, snapshot=snapshot, subject=subject)
    rows = _rows(channels_tsv)
    good = {row["name"].strip() for row in rows if row.get("name", "").strip()
            and row.get("status", "").strip().lower() == "good"
            and row.get("type", "").strip().lower() in {"ieeg", "seeg", "ecog"}}
    return good, set(metadata["canonical_nodes"])


def plan_development_channel(*, snapshot: str, subject: str, events_tsv: str, channels_tsv: str,
                             retained_nodes: set[str], shared_first_uutc: int, tidx_bytes: bytes,
                             tdat_size: int, fs_hz: int) -> dict[str, Any]:
    rows = parse_tidx(tidx_bytes)
    if rows[0]["start_uutc"] != shared_first_uutc or rows[0]["start_sample"] != SHARED_START_SAMPLE:
        raise ValueError("APPARATUS_DEVELOPMENT_RANGE_STOP:inconsistent channel timing")
    windows = _event_windows(events_tsv, channels_tsv, retained_nodes, snapshot=snapshot, subject=subject, fs_hz=fs_hz)
    ranges, block_count = _select_union_ranges(rows, windows, fs_hz=fs_hz, tdat_size=tdat_size)
    return {"precision_convention": PRECISION_CONVENTION, "precision_convention_version": PRECISION_CONVENTION_VERSION,
            "shared_first_uutc": shared_first_uutc,
            "shared_start_sample": SHARED_START_SAMPLE, "windows_samples": [[start, end] for start, end in windows],
            "epoch_windows_samples": {"acquisition": list(ACQUISITION_WINDOW_SAMPLES), "baseline": list(BASELINE_WINDOW_SAMPLES),
                                      "early": list(EARLY_WINDOW_SAMPLES), "prestim": list(PRESTIM_WINDOW_SAMPLES)},
            "ranges": [[start, end] for start, end in ranges],
            "block_count": block_count, "bytes": sum(end - start for start, end in ranges),
            "tidx_sha256": hashlib.sha256(tidx_bytes).hexdigest()}
