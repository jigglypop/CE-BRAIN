"""Metadata-only source lock for the multi-subject ds004080 CCEP study.

This program deliberately does not decode a scientific EEG endpoint.  It pins
the OpenNeuro snapshot, verifies Git blobs and git-annex identities, validates
BrainVision byte geometry, and builds an endpoint-blind source/receiver
manifest for the later sequential experiment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


DATASET = "ds004080"
TAG = "1.2.4"
TREE_SHA = "c4fd7418883e33b024292468eb14da1649f51aae"
TREE_URL = f"https://api.github.com/repos/OpenNeuroDatasets/{DATASET}/git/trees/{TREE_SHA}?recursive=1"
RAW_ROOT = f"https://raw.githubusercontent.com/OpenNeuroDatasets/{DATASET}/{TAG}"
S3_ROOT = f"https://s3.amazonaws.com/openneuro.org/{DATASET}"
EXPECTED_SUBJECTS = 74
EXPECTED_RECORDINGS = 117
USER_AGENT = "CE-BA-OBS-DISC2-metadata-audit/1"
ANNEX_RE = re.compile(r"SHA256E-s(?P<size>\d+)--(?P<sha>[0-9a-f]{64})\.(?P<ext>[A-Za-z0-9]+)")
CHANNEL_RE = re.compile(r"^Ch(?P<index>\d+)=(?P<name>[^,]+),(?P<reference>[^,]*),(?P<resolution>[^,]*)(?:,(?P<unit>.*))?$")
RUN_RE = re.compile(
    r"^(?P<subject>sub-[^/]+)/(?P<session>ses-[^/]+)/ieeg/"
    r"(?P<stem>.+)_ieeg\.eeg$"
)
REQUIRED_EVENT_COLUMNS = {
    "onset", "duration", "trial_type", "sub_type", "sample_start", "sample_end",
    "electrical_stimulation_type", "electrical_stimulation_site",
    "electrical_stimulation_current", "electrical_stimulation_frequency",
    "electrical_stimulation_pulsewidth",
}


class AuditStop(RuntimeError):
    """A source identity, schema, or byte-geometry invariant failed."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def dump_atomic(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return sha256_bytes(path.read_bytes())


def request_bytes(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
                  timeout: int = 90) -> tuple[bytes, int, dict[str, str]]:
    merged = {"User-Agent": USER_AGENT, **(headers or {})}
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=merged, method=method)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read() if method != "HEAD" else b""
                return body, response.status, {k.lower(): v for k, v in response.headers.items()}
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(0.25 * (2 ** attempt))
    raise AuditStop(f"transport failed after three attempts: {url}: {last_error}")


def parse_tsv(payload: bytes, path: str) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise AuditStop(f"UTF-8 decode failed: {path}") from error
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    if not reader.fieldnames:
        raise AuditStop(f"empty TSV header: {path}")
    return list(reader)


def finite_float(value: str, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise AuditStop(f"non-numeric {field}: {value!r}") from error
    if not math.isfinite(result):
        raise AuditStop(f"non-finite {field}: {value!r}")
    return result


def parse_annex_pointer(payload: bytes, path: str) -> dict[str, object]:
    try:
        target = payload.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise AuditStop(f"annex pointer is not UTF-8: {path}") from error
    match = ANNEX_RE.search(target)
    if not match:
        raise AuditStop(f"annex pointer grammar mismatch: {path}")
    return {
        "pointer_target": target,
        "size": int(match.group("size")),
        "sha256": match.group("sha"),
        "extension": match.group("ext"),
    }


def parse_brainvision_header(payload: bytes, path: str) -> dict[str, object]:
    if not payload.startswith(b"Brain Vision Data Exchange Header File Version 1.0"):
        raise AuditStop(f"BrainVision header signature mismatch: {path}")
    text = payload.decode("utf-8-sig")
    fields: dict[str, str] = {}
    channels: list[dict[str, object]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("["):
            continue
        channel = CHANNEL_RE.match(line)
        if channel:
            resolution_text = channel.group("resolution") or "1"
            resolution = finite_float(resolution_text, "channel resolution")
            channels.append({
                "index": int(channel.group("index")),
                "name": channel.group("name"),
                "reference": channel.group("reference"),
                "resolution": resolution,
                "unit": channel.group("unit") or "",
            })
        elif "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    required = {
        "DataFile": fields.get("DataFile"),
        "MarkerFile": fields.get("MarkerFile"),
        "DataFormat": fields.get("DataFormat"),
        "DataOrientation": fields.get("DataOrientation"),
        "NumberOfChannels": fields.get("NumberOfChannels"),
        "SamplingInterval": fields.get("SamplingInterval"),
        "BinaryFormat": fields.get("BinaryFormat"),
    }
    if any(value in (None, "") for value in required.values()):
        raise AuditStop(f"BrainVision required field missing: {path}: {required}")
    n_channels = int(required["NumberOfChannels"])
    sampling_interval_us = finite_float(required["SamplingInterval"], "SamplingInterval")
    sample_rate = 1_000_000.0 / sampling_interval_us
    if required["DataFormat"] != "BINARY" or required["DataOrientation"] != "MULTIPLEXED":
        raise AuditStop(f"unsupported BrainVision layout: {path}: {required}")
    if required["BinaryFormat"] != "IEEE_FLOAT_32":
        raise AuditStop(f"unsupported BrainVision binary format: {path}: {required['BinaryFormat']}")
    if len(channels) != n_channels or [row["index"] for row in channels] != list(range(1, n_channels + 1)):
        raise AuditStop(f"BrainVision channel table mismatch: {path}")
    return {
        "data_file": required["DataFile"],
        "marker_file": required["MarkerFile"],
        "data_format": required["DataFormat"],
        "orientation": required["DataOrientation"],
        "binary_format": required["BinaryFormat"],
        "number_of_channels": n_channels,
        "sampling_interval_us": sampling_interval_us,
        "sampling_frequency_hz": sample_rate,
        "channels": channels,
    }


def parse_site(value: str) -> tuple[str, str] | None:
    parts = value.strip().split("-")
    if len(parts) != 2 or not all(parts):
        return None
    return parts[0], parts[1]


def normalize_token(value: str) -> str:
    return value.strip().lower()


def overlaps(left_start: float, left_end: float, right_start: float, right_end: float) -> bool:
    return left_start < right_end and right_start < left_end


def event_anchor_zero(onset_s: float, sample_start: int, sample_rate: float) -> tuple[int, int]:
    """Validate the dataset's zero-based sample_start against onset seconds."""
    onset_samples = onset_s * sample_rate
    rounded_onset = round(onset_samples)
    if not math.isclose(onset_samples, rounded_onset, rel_tol=0.0, abs_tol=1e-6):
        raise AuditStop(f"event onset is off the sampling grid: {onset_s!r} at {sample_rate!r} Hz")
    delta = sample_start - rounded_onset
    if delta != 0:
        raise AuditStop(f"sample_start is not zero-based onset sample: delta={delta}")
    return sample_start, delta


def s3_identity(path: str, annex: dict[str, object]) -> dict[str, object]:
    url = f"{S3_ROOT}/{urllib.parse.quote(path, safe='/')}"
    _, status, headers = request_bytes(url, method="HEAD")
    if status != 200:
        raise AuditStop(f"S3 HEAD status {status}: {path}")
    size = int(headers.get("content-length", "-1"))
    if size != annex["size"]:
        raise AuditStop(f"S3/annex size mismatch: {path}: {size} != {annex['size']}")
    etag = headers.get("etag")
    version_id = headers.get("x-amz-version-id")
    if not etag or not version_id:
        raise AuditStop(f"S3 version identity missing: {path}")
    locked_url = url + "?versionId=" + urllib.parse.quote(version_id, safe="")
    end = min(size, 64) - 1
    body, range_status, range_headers = request_bytes(
        locked_url,
        headers={"Range": f"bytes=0-{end}", "If-Match": etag},
    )
    expected_range = f"bytes 0-{end}/{size}"
    if (
        range_status != 206
        or range_headers.get("content-range") != expected_range
        or len(body) != end + 1
        or range_headers.get("etag") != etag
        or range_headers.get("x-amz-version-id") != version_id
    ):
        raise AuditStop(f"S3 range identity mismatch: {path}")
    return {
        "url": url,
        "locked_url": locked_url,
        "content_length": size,
        "etag": etag,
        "version_id": version_id,
        "last_modified": headers.get("last-modified"),
        "accept_ranges": headers.get("accept-ranges"),
        "probe_content_range": range_headers.get("content-range"),
        "probe_sha256": sha256_bytes(body),
    }


def exact_small_s3(path: str, annex: dict[str, object]) -> bytes:
    url = f"{S3_ROOT}/{urllib.parse.quote(path, safe='/')}"
    body, status, _ = request_bytes(url)
    if status != 200 or len(body) != annex["size"] or sha256_bytes(body) != annex["sha256"]:
        raise AuditStop(f"small annex content mismatch: {path}")
    return body


def build_tree() -> tuple[dict[str, dict], dict[str, object]]:
    body, status, _ = request_bytes(TREE_URL)
    if status != 200:
        raise AuditStop(f"GitHub tree status {status}")
    payload = json.loads(body)
    if payload.get("sha") != TREE_SHA or payload.get("truncated") is not False:
        raise AuditStop("GitHub tree identity/truncation mismatch")
    entries = {row["path"]: row for row in payload["tree"]}
    subjects = sorted({path.split("/", 1)[0] for path in entries if path.startswith("sub-")})
    eeg_paths = sorted(path for path in entries if path.endswith("_ieeg.eeg"))
    if len(subjects) != EXPECTED_SUBJECTS or len(eeg_paths) != EXPECTED_RECORDINGS:
        raise AuditStop(f"snapshot count mismatch: subjects={len(subjects)}, recordings={len(eeg_paths)}")
    return entries, {
        "tree_sha": TREE_SHA,
        "entry_count": len(entries),
        "tree_payload_sha256": sha256_bytes(body),
        "subjects": subjects,
        "recording_paths": eeg_paths,
    }


def fetch_git_blobs(entries: dict[str, dict], paths: set[str]) -> dict[str, bytes]:
    missing = sorted(path for path in paths if path not in entries or entries[path].get("type") != "blob")
    if missing:
        raise AuditStop(f"required Git blobs missing: {missing[:5]}")

    def acquire(path: str) -> tuple[str, bytes]:
        body, status, _ = request_bytes(f"{RAW_ROOT}/{urllib.parse.quote(path, safe='/')}")
        if status != 200 or git_blob_sha(body) != entries[path]["sha"]:
            raise AuditStop(f"Git blob identity mismatch: {path}")
        return path, body

    with ThreadPoolExecutor(max_workers=16) as executor:
        return dict(executor.map(acquire, sorted(paths)))


def run_spec(eeg_path: str) -> dict[str, str]:
    match = RUN_RE.match(eeg_path)
    if not match:
        raise AuditStop(f"run path grammar mismatch: {eeg_path}")
    subject, session, stem = match.group("subject"), match.group("session"), match.group("stem")
    directory = f"{subject}/{session}/ieeg"
    if not stem.startswith(f"{subject}_{session}_"):
        raise AuditStop(f"run stem identity mismatch: {eeg_path}")
    return {
        "subject": subject,
        "session": session,
        "stem": stem,
        "record_id": stem,
        "eeg": eeg_path,
        "vhdr": f"{directory}/{stem}_ieeg.vhdr",
        "vmrk": f"{directory}/{stem}_ieeg.vmrk",
        "ieeg_json": f"{directory}/{stem}_ieeg.json",
        "events": f"{directory}/{stem}_events.tsv",
        "channels": f"{directory}/{stem}_channels.tsv",
        "electrodes": f"{directory}/{subject}_{session}_electrodes.tsv",
        "coordsystem": f"{directory}/{subject}_{session}_coordsystem.json",
    }


def coordinates(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        name = row.get("name", "").strip()
        if not name or name in result:
            raise AuditStop(f"missing/duplicate electrode name: {name!r}")
        xyz: list[float] | None
        try:
            xyz = [finite_float(row[axis], f"electrode {name} {axis}") for axis in ("x", "y", "z")]
        except AuditStop:
            xyz = None
        result[name] = {
            "xyz_mm": xyz,
            "group": row.get("group", ""),
            "hemisphere": row.get("hemisphere", ""),
            "silicon": row.get("silicon", ""),
            "soz": row.get("soz", ""),
            "resected": row.get("resected", ""),
            "edge": row.get("edge", ""),
            "destrieux_label": row.get("Destrieux_label", ""),
            "destrieux_text": row.get("Destrieux_label_text", ""),
        }
    return result


def inspect_record(spec: dict[str, str], blobs: dict[str, bytes], entries: dict[str, dict]) -> dict[str, object]:
    pointers = {kind: parse_annex_pointer(blobs[spec[kind]], spec[kind]) for kind in ("eeg", "vhdr", "vmrk")}
    if any(pointers[kind]["extension"] != kind for kind in pointers):
        raise AuditStop(f"annex extension mismatch: {spec['record_id']}")
    header_payload = exact_small_s3(spec["vhdr"], pointers["vhdr"])
    marker_payload = exact_small_s3(spec["vmrk"], pointers["vmrk"])
    header = parse_brainvision_header(header_payload, spec["vhdr"])
    if header["data_file"] != Path(spec["eeg"]).name or header["marker_file"] != Path(spec["vmrk"]).name:
        raise AuditStop(f"BrainVision file linkage mismatch: {spec['record_id']}")
    source = s3_identity(spec["eeg"], pointers["eeg"])
    bytes_per_sample = int(header["number_of_channels"]) * 4
    if int(source["content_length"]) % bytes_per_sample:
        raise AuditStop(f"binary byte geometry remainder: {spec['record_id']}")
    sample_count = int(source["content_length"]) // bytes_per_sample
    header_sample_rate = float(header["sampling_frequency_hz"])

    ieeg = json.loads(blobs[spec["ieeg_json"]])
    events = parse_tsv(blobs[spec["events"]], spec["events"])
    channels = parse_tsv(blobs[spec["channels"]], spec["channels"])
    electrode_rows = parse_tsv(blobs[spec["electrodes"]], spec["electrodes"])
    coordsystem = json.loads(blobs[spec["coordsystem"]])
    if events and not REQUIRED_EVENT_COLUMNS.issubset(events[0]):
        raise AuditStop(f"event schema mismatch: {spec['events']}")
    if len(channels) != header["number_of_channels"]:
        raise AuditStop(f"channels/header count mismatch: {spec['record_id']}")
    header_names = [row["name"] for row in header["channels"]]
    channel_names = [row.get("name", "") for row in channels]
    if header_names != channel_names:
        raise AuditStop(f"channels/header ordering mismatch: {spec['record_id']}")
    json_rate = finite_float(str(ieeg.get("SamplingFrequency")), "JSON SamplingFrequency")
    # FieldTrip writes some 2048-Hz SamplingInterval values with only seven
    # significant digits (488.2812 us).  Accept only that decimal-serialization
    # precision, then use the BIDS JSON integer rate for all sample geometry.
    if not math.isclose(header_sample_rate, json_rate, rel_tol=1e-6, abs_tol=1e-6):
        raise AuditStop(
            f"header/JSON sample-rate mismatch: {spec['record_id']}: "
            f"header={header_sample_rate}, json={json_rate}"
        )
    sample_rate = json_rate
    duration = sample_count / sample_rate
    json_duration = finite_float(str(ieeg.get("RecordingDuration")), "RecordingDuration")
    if not math.isclose(duration, json_duration, rel_tol=0.0, abs_tol=1.0 / sample_rate):
        raise AuditStop(f"duration/byte geometry mismatch: {spec['record_id']}: {duration} != {json_duration}")
    for row in channels:
        row_rate = finite_float(row.get("sampling_frequency", ""), "channel sampling_frequency")
        if not math.isclose(row_rate, sample_rate, rel_tol=0.0, abs_tol=1e-9):
            raise AuditStop(f"channel sampling-rate mismatch: {spec['record_id']}")

    electrode_map = coordinates(electrode_rows)
    channel_map = {
        row["name"]: {
            "index": index,
            "type": row.get("type", ""),
            "units": row.get("units", ""),
            "reference": row.get("reference", ""),
            "group": row.get("group", ""),
            "status": row.get("status", ""),
            "status_description": row.get("status_description", ""),
            "resolution": header["channels"][index]["resolution"],
        }
        for index, row in enumerate(channels)
    }

    artifacts: list[tuple[float, float, str]] = []
    for row in events:
        if normalize_token(row.get("trial_type", "")) != "artefact":
            continue
        onset = finite_float(row.get("onset", ""), "artefact onset")
        duration_event = finite_float(row.get("duration", "0") or "0", "artefact duration")
        offset_value = row.get("offset", "")
        offset = finite_float(offset_value, "artefact offset") if offset_value not in ("", "n/a") else onset + duration_event
        artifacts.append((onset, max(offset, onset + duration_event), normalize_token(row.get("electrodes_involved_onset", ""))))

    crosswalk = Counter()
    electrical_rows: list[dict[str, object]] = []
    for event_index, row in enumerate(events):
        event_type = normalize_token(row.get("trial_type", ""))
        if event_type != "electrical_stimulation":
            continue
        onset = finite_float(row.get("onset", ""), "event onset")
        sample_start = int(round(finite_float(row.get("sample_start", ""), "sample_start")))
        try:
            anchor_zero, delta = event_anchor_zero(onset, sample_start, sample_rate)
        except AuditStop as error:
            raise AuditStop(f"event/onset sample crosswalk mismatch: {spec['record_id']} event {event_index}: {error}") from error
        crosswalk[str(delta)] += 1
        site_text = row.get("electrical_stimulation_site", "").strip()
        site = parse_site(site_text)
        if site is None:
            raise AuditStop(f"stimulation-site grammar mismatch: {spec['record_id']}: {site_text!r}")
        current = finite_float(row.get("electrical_stimulation_current", ""), "stimulation current")
        frequency = finite_float(row.get("electrical_stimulation_frequency", ""), "stimulation frequency")
        pulsewidth = finite_float(row.get("electrical_stimulation_pulsewidth", ""), "stimulation pulsewidth")
        if min(current, frequency, pulsewidth) <= 0:
            raise AuditStop(f"nonpositive stimulation parameter: {spec['record_id']} event {event_index}")
        pre_s, post_s = 0.500, 0.120
        global_artifact_overlap = any(
            involved in ("all", "n/a", "") and overlaps(onset - pre_s, onset + post_s, start, end)
            for start, end, involved in artifacts
        )
        in_bounds = anchor_zero - round(pre_s * sample_rate) >= 0 and anchor_zero + round(post_s * sample_rate) < sample_count
        electrical_rows.append({
            "event_index": event_index,
            "onset_s": onset,
            "anchor_sample_zero_based": anchor_zero,
            "site": site_text,
            "contacts": list(site),
            "stimulation_type": row.get("electrical_stimulation_type", "").strip(),
            "current_a": current,
            "frequency_hz": frequency,
            "pulsewidth_s": pulsewidth,
            "global_artifact_overlap": global_artifact_overlap,
            "in_bounds": in_bounds,
        })

    # The acquisition protocol reverses polarity after five pulses in 27
    # subjects.  A-B and B-A are therefore one anatomical bipolar source with
    # ten pulses, not two five-trial sources.  Keep the original orientation on
    # every trial so the later apparatus can audit polarity balance.
    grouped: dict[tuple, list[dict[str, object]]] = defaultdict(list)
    for row in electrical_rows:
        unordered_contacts = tuple(sorted(row["contacts"]))
        key = (
            unordered_contacts, row["stimulation_type"], row["current_a"],
            row["frequency_hz"], row["pulsewidth_s"],
        )
        grouped[key].append(row)
    source_blocks = []
    for key, trials in sorted(grouped.items(), key=lambda item: tuple(map(str, item[0]))):
        unordered_contacts, stimulation_type, current, frequency, pulsewidth = key
        contacts = list(unordered_contacts)
        site_text = "-".join(contacts)
        contact_rows = [channel_map.get(contact) for contact in contacts]
        electrode_rows_for_site = [electrode_map.get(contact) for contact in contacts]
        channel_valid = all(
            row is not None and normalize_token(str(row["type"])) == "ecog" and normalize_token(str(row["status"])) == "good"
            for row in contact_rows
        )
        coordinate_valid = all(row is not None and row["xyz_mm"] is not None for row in electrode_rows_for_site)
        pathology_clean = all(
            row is not None and normalize_token(str(row.get("soz", ""))) != "yes" and normalize_token(str(row.get("silicon", ""))) != "yes"
            for row in electrode_rows_for_site
        )
        clean_trials = [row for row in trials if not row["global_artifact_overlap"] and row["in_bounds"]]
        center = None
        if coordinate_valid:
            center = [
                sum(float(row["xyz_mm"][axis]) for row in electrode_rows_for_site) / 2.0
                for axis in range(3)
            ]
        source_blocks.append({
            "site": site_text,
            "contacts": contacts,
            "stimulation_type": stimulation_type,
            "current_a": current,
            "frequency_hz": frequency,
            "pulsewidth_s": pulsewidth,
            "trial_count": len(trials),
            "clean_trial_count": len(clean_trials),
            "clean_trials": clean_trials,
            "polarity_orientation_counts": dict(sorted(Counter(str(row["site"]) for row in trials).items())),
            "channel_valid": channel_valid,
            "coordinate_valid": coordinate_valid,
            "pathology_clean": pathology_clean,
            "center_xyz_mm": center,
        })

    file_hashes = {
        key: {
            "path": spec[key],
            "git_blob_sha1": entries[spec[key]]["sha"],
            "payload_sha256": sha256_bytes(blobs[spec[key]]),
        }
        for key in ("eeg", "vhdr", "vmrk", "ieeg_json", "events", "channels", "electrodes", "coordsystem")
    }
    return {
        "subject": spec["subject"],
        "session": spec["session"],
        "record_id": spec["record_id"],
        "paths": spec,
        "file_hashes": file_hashes,
        "annex": pointers,
        "source": source,
        "header": {
            key: value for key, value in header.items() if key != "channels"
        },
        "authoritative_sampling_frequency_hz": sample_rate,
        "sample_count": sample_count,
        "duration_s": duration,
        "ieeg": {
            "sampling_frequency_hz": json_rate,
            "recording_duration_s": json_duration,
            "manufacturer": ieeg.get("Manufacturer"),
            "model": ieeg.get("ManufacturersModelName"),
            "ieeg_reference": ieeg.get("iEEGReference"),
            "ieeg_ground": ieeg.get("iEEGGround"),
            "ecog_channel_count": ieeg.get("ECOGChannelCount"),
        },
        "coordsystem": coordsystem,
        "channel_summary": {
            "count": len(channels),
            "type_counts": dict(sorted(Counter(row.get("type", "") for row in channels).items())),
            "status_counts": dict(sorted(Counter(row.get("status", "") for row in channels).items())),
            "reference_counts": dict(sorted(Counter(row.get("reference", "") for row in channels).items())),
        },
        "channels": channel_map,
        "electrodes": electrode_map,
        "event_count": len(events),
        "electrical_event_count": len(electrical_rows),
        "event_sample_crosswalk": dict(sorted(crosswalk.items())),
        "marker_payload_sha256": sha256_bytes(marker_payload),
        "source_blocks": source_blocks,
    }


def add_receiver_manifests(records: list[dict[str, object]]) -> list[dict[str, object]]:
    by_subject: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        by_subject[str(record["subject"])].append(record)
    participants = []
    for subject, subject_records in sorted(by_subject.items()):
        canonical_candidates: dict[tuple[str, str], list[tuple[dict[str, object], dict[str, object]]]] = defaultdict(list)
        for record in subject_records:
            for block in record["source_blocks"]:
                if (
                    block["clean_trial_count"] >= 10
                    and block["channel_valid"]
                    and block["coordinate_valid"]
                    and block["pathology_clean"]
                ):
                    canonical_candidates[(str(record["session"]), str(block["site"]))].append((record, block))
        canonical: list[dict[str, object]] = []
        for (session, site), candidates in sorted(canonical_candidates.items()):
            chosen_record, chosen_block = sorted(
                candidates,
                key=lambda pair: (
                    -int(pair[1]["clean_trial_count"]), str(pair[0]["record_id"]),
                    str(pair[1]["stimulation_type"]), float(pair[1]["current_a"]),
                    float(pair[1]["pulsewidth_s"]), float(pair[1]["frequency_hz"]),
                ),
            )[0]
            canonical.append({
                "site_id": f"{session}|{site}",
                "subject": subject,
                "session": session,
                "site": site,
                "contacts": chosen_block["contacts"],
                "center_xyz_mm": chosen_block["center_xyz_mm"],
                "record_id": chosen_record["record_id"],
                "clean_trial_count": chosen_block["clean_trial_count"],
                "clean_trials": [
                    {
                        "event_index": trial["event_index"],
                        "anchor_sample_zero_based": trial["anchor_sample_zero_based"],
                        "orientation_site": trial["site"],
                    }
                    for trial in chosen_block["clean_trials"]
                ],
                "stimulation_type": chosen_block["stimulation_type"],
                "current_a": chosen_block["current_a"],
                "frequency_hz": chosen_block["frequency_hz"],
                "pulsewidth_s": chosen_block["pulsewidth_s"],
            })
        valid_sources = []
        for source in canonical:
            source_record = next(record for record in subject_records if record["record_id"] == source["record_id"])
            source_contacts = set(source["contacts"])
            receivers = []
            for target in canonical:
                if target["session"] != source["session"] or target["site"] == source["site"]:
                    continue
                if source_contacts.intersection(target["contacts"]):
                    continue
                target_channel_rows = [source_record["channels"].get(contact) for contact in target["contacts"]]
                if not all(
                    row is not None and normalize_token(str(row["type"])) == "ecog" and normalize_token(str(row["status"])) == "good"
                    for row in target_channel_rows
                ):
                    continue
                delta = [float(target["center_xyz_mm"][axis]) - float(source["center_xyz_mm"][axis]) for axis in range(3)]
                distance = math.sqrt(sum(value * value for value in delta))
                if distance < 15.0:
                    continue
                receivers.append({
                    "site_id": target["site_id"],
                    "site": target["site"],
                    "contacts": target["contacts"],
                    "center_xyz_mm": target["center_xyz_mm"],
                    "delta_xyz_mm": delta,
                    "distance_mm": distance,
                })
            receivers.sort(key=lambda row: (row["distance_mm"], row["site"]))
            if len(receivers) >= 6:
                distances = [float(row["distance_mm"]) for row in receivers]
                valid_sources.append({
                    **source,
                    "receiver_site_ids": [row["site_id"] for row in receivers],
                    "eligible_receiver_count": len(receivers),
                    "distance_min_mm": min(distances),
                    "distance_max_mm": max(distances),
                })
        site_catalog = [
            {
                "site_id": source["site_id"],
                "session": source["session"],
                "site": source["site"],
                "contacts": source["contacts"],
                "center_xyz_mm": source["center_xyz_mm"],
            }
            for source in canonical
        ]
        participants.append({
            "subject": subject,
            "recording_count": len(subject_records),
            "canonical_source_count": len(canonical),
            "valid_source_count": len(valid_sources),
            "eligible": len(valid_sources) >= 8,
            "site_catalog": site_catalog,
            "sources": valid_sources,
        })
    return participants


def execute() -> tuple[dict[str, object], dict[str, object]]:
    entries, tree_summary = build_tree()
    specs = [run_spec(path) for path in tree_summary["recording_paths"]]
    top = {"README", "dataset_description.json", "participants.tsv", "participants.json", "events.json"}
    required = set(top)
    for spec in specs:
        required.update(spec[key] for key in ("eeg", "vhdr", "vmrk", "ieeg_json", "events", "channels", "electrodes", "coordsystem"))
    blobs = fetch_git_blobs(entries, required)
    description = json.loads(blobs["dataset_description.json"])
    participant_rows = parse_tsv(blobs["participants.tsv"], "participants.tsv")
    if len(participant_rows) != EXPECTED_SUBJECTS or description.get("DatasetDOI") != "doi:10.18112/openneuro.ds004080.v1.2.4":
        raise AuditStop("dataset description/participant identity mismatch")

    def inspect(spec: dict[str, str]) -> dict[str, object]:
        return inspect_record(spec, blobs, entries)

    with ThreadPoolExecutor(max_workers=10) as executor:
        records = list(executor.map(inspect, specs))
    records.sort(key=lambda row: str(row["record_id"]))
    participants = add_receiver_manifests(records)
    age_map = {row["participant_id"]: int(row["age"]) for row in participant_rows}
    sex_map = {row["participant_id"]: row["sex"] for row in participant_rows}
    for participant in participants:
        participant["age_years"] = age_map[participant["subject"]]
        participant["sex"] = sex_map[participant["subject"]]

    compact_records = []
    for record in records:
        compact_records.append({
            key: value for key, value in record.items()
            if key not in {"electrodes", "source_blocks"}
        })
    manifest = {
        "schema": "BA-OBS-DISC2-ds004080-metadata-source-manifest-v1",
        "status": "METADATA_ONLY_ENDPOINT_UNOPENED",
        "dataset": DATASET,
        "snapshot": TAG,
        "tree_sha": TREE_SHA,
        "dataset_doi": description["DatasetDOI"],
        "license": description.get("License"),
        "top_level_hashes": {
            path: {"git_blob_sha1": entries[path]["sha"], "payload_sha256": sha256_bytes(blobs[path])}
            for path in sorted(top)
        },
        "participants": participants,
        "recordings": compact_records,
        "scientific_endpoint_opened": False,
    }
    eligible = [row for row in participants if row["eligible"]]
    rates = Counter(str(int(round(float(row["header"]["sampling_frequency_hz"])))) for row in records)
    coordinate_systems = Counter(str(row["coordsystem"].get("iEEGCoordinateSystem")) for row in records)
    stim_parameters = Counter()
    for record in records:
        for block in record["source_blocks"]:
            stim_parameters[
                f"{block['stimulation_type']}|{block['current_a']:.9g}|{block['frequency_hz']:.9g}|{block['pulsewidth_s']:.9g}"
            ] += int(block["trial_count"])
    receipt = {
        "schema": "BA-OBS-DISC2-ds004080-metadata-audit-v1",
        "status": "PASS" if len(eligible) >= 60 else "STOP_INSUFFICIENT_ELIGIBLE_SUBJECTS",
        "dataset": DATASET,
        "snapshot": TAG,
        "tree_sha": TREE_SHA,
        "tree_entry_count": tree_summary["entry_count"],
        "tree_payload_sha256": tree_summary["tree_payload_sha256"],
        "dataset_doi": description["DatasetDOI"],
        "license": description.get("License"),
        "bids_version": description.get("BIDSVersion"),
        "subject_count": len(participants),
        "recording_count": len(records),
        "eligible_subject_count": len(eligible),
        "eligible_subjects": [row["subject"] for row in eligible],
        "valid_source_count": sum(int(row["valid_source_count"]) for row in eligible),
        "sampling_frequency_recording_counts": dict(sorted(rates.items())),
        "coordinate_system_recording_counts": dict(sorted(coordinate_systems.items())),
        "stimulation_parameter_event_counts": dict(sorted(stim_parameters.items())),
        "all_event_sample_crosswalks": dict(sorted(Counter(
            key for record in records for key in record["event_sample_crosswalk"]
        ).items())),
        "source_identity": {
            "all_git_blobs_verified": True,
            "all_annex_pointers_parsed": True,
            "all_small_vhdr_vmrk_sha256_verified": True,
            "all_eeg_head_and_version_locked_range_probes_verified": True,
            "all_binary_geometry_verified": True,
        },
        "scientific_endpoint_opened": False,
    }
    return receipt, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt, manifest = execute()
        manifest_hash = dump_atomic(args.manifest, manifest)
        receipt["manifest_sha256"] = manifest_hash
        dump_atomic(args.receipt, receipt)
    except Exception as error:
        failed = {
            "schema": "BA-OBS-DISC2-ds004080-metadata-audit-v1",
            "status": "SOURCE_OR_SCHEMA_STOP",
            "error": f"{type(error).__name__}: {error}",
            "dataset": DATASET,
            "snapshot": TAG,
            "tree_sha": TREE_SHA,
            "scientific_endpoint_opened": False,
        }
        dump_atomic(args.receipt, failed)
        print(json.dumps(failed, sort_keys=True))
        return 2
    print(json.dumps({
        "status": receipt["status"],
        "subjects": receipt["subject_count"],
        "recordings": receipt["recording_count"],
        "eligible_subjects": receipt["eligible_subject_count"],
        "valid_sources": receipt["valid_source_count"],
        "scientific_endpoint_opened": False,
    }, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
