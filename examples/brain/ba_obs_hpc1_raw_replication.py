"""BA-OBS-HPC1: version-pinned, non-persistent BrainVision iEEG reanalysis.

This module intentionally has two barriers. ``source-lock`` reads only Git-annex
pointer text, BrainVision headers, and HTTP HEAD metadata.  ``raw-one-shot`` may
run only after that manifest is present and streams each version-pinned EEG object
once, retaining the two frozen references in memory but never writing voltage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import kurtosis


RUN_DIR = Path("_workspace/ce/brain-human-hippocampal-theta-raw-replication-20260825")
COMMIT = "14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4"
GITHUB_RAW = f"https://raw.githubusercontent.com/OpenNeuroDatasets/ds006065/{COMMIT}"
S3_ROOT = "https://s3.amazonaws.com/openneuro.org/ds006065"
SOURCE_LOCK_SHA256 = "0b3d92f998f626ed37f68d0dfb1188a777afb287975916beec1f623d10d3fc58"
FS = 499.5
N_SAMPLES = 1000
TIME_MS = np.arange(N_SAMPLES, dtype=float) * (1000.0 / FS) - 500.0
WINDOWS = {
    "early": np.flatnonzero((TIME_MS >= 15) & (TIME_MS <= 50)),
    "late": np.flatnonzero((TIME_MS >= 50) & (TIME_MS <= 250)),
    "prestim": np.flatnonzero((TIME_MS >= -300) & (TIME_MS <= -100)),
    "baseline": np.flatnonzero((TIME_MS >= -50) & (TIME_MS <= -10)),
}


@dataclass(frozen=True)
class EPFile:
    protocol: str
    subject: str
    phase: str
    task: str
    blocks: int
    n_channels: int
    clinical: str
    bipolar_second: str

    @property
    def rel_eeg(self) -> str:
        return f"sub-{self.subject}/ieeg/sub-{self.subject}_task-{self.task}_ieeg.eeg"

    @property
    def rel_vhdr(self) -> str:
        return self.rel_eeg[:-3] + "vhdr"


def _files() -> tuple[EPFile, ...]:
    # This is the frozen contract table.  p17/p19 occur in both protocols.
    rows = (
        ("TS", "p16", "pre", "eppre", 90, 168, "RB1", "RB2"),
        ("TS", "p16", "post", "eppost", 60, 168, "RB1", "RB2"),
        ("TS", "p17", "pre", "eppre", 63, 175, "D1", "D2"),
        ("TS", "p17", "post", "eppost", 59, 175, "D1", "D2"),
        ("TS", "p18", "pre", "eppre", 60, 82, "AH2", "AH3"),
        ("TS", "p18", "post", "eppost", 60, 82, "AH2", "AH3"),
        ("TS", "p19", "pre", "eppre", 60, 168, "D1", "D2"),
        ("TS", "p19", "post", "eppost", 60, 168, "D1", "D2"),
        ("PB", "p17", "pre", "epcontrolpre", 60, 175, "D1", "D2"),
        ("PB", "p17", "post", "epcontrolpost", 60, 175, "D1", "D2"),
        ("PB", "p19", "pre", "epcontrolpre", 60, 168, "D1", "D2"),
        ("PB", "p19", "post", "epcontrolpost", 60, 168, "D1", "D2"),
        ("PB", "p20", "pre", "epcontrolpre", 151, 181, "D9", "D10"),
        ("PB", "p20", "post", "epcontrolpost", 149, 181, "D9", "D10"),
        ("PB", "UC004", "pre", "epcontrolpre", 40, 43, "RHH1", "RHH2"),
        ("PB", "UC004", "post", "epcontrolpost", 40, 43, "RHH1", "RHH2"),
        ("PB", "UC005", "pre", "epcontrolpre", 40, 68, "RHB1", "RHB2"),
        ("PB", "UC005", "post", "epcontrolpost", 40, 68, "RHB1", "RHB2"),
    )
    return tuple(EPFile(*row) for row in rows)


FILES = _files()


def _request(url: str, method: str = "GET") -> tuple[dict[str, str], bytes]:
    with urlopen(Request(url, method=method), timeout=60) as response:
        return ({k.lower(): v for k, v in response.headers.items()}, response.read() if method == "GET" else b"")


def _annex_pointer(relpath: str) -> tuple[str, int]:
    _, text = _request(f"{GITHUB_RAW}/{quote(relpath)}")
    match = re.search(rb"SHA256E-s(\d+)--([0-9a-f]{64})\.eeg", text)
    if not match:
        raise ValueError(f"STOP_SOURCE_IDENTITY: annex pointer not understood: {relpath}")
    return match.group(2).decode("ascii"), int(match.group(1))


def _parse_vhdr(blob: bytes) -> dict[str, Any]:
    text = blob.decode("utf-8-sig")
    need = ("DataFormat=BINARY", "DataOrientation=MULTIPLEXED", "BinaryFormat=IEEE_FLOAT_32")
    if not all(term in text for term in need):
        raise ValueError("STOP_SOURCE_IDENTITY: unsupported BrainVision format")
    fields = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
    endian = fields.get("UseBigEndianOrder", "NO")
    if endian != "NO":
        raise ValueError("STOP_SOURCE_IDENTITY: big-endian BrainVision payload")
    n_text, si_text = fields.get("NumberOfChannels"), fields.get("SamplingInterval")
    if n_text is None or si_text is None or "DataFile" not in fields:
        raise ValueError("STOP_SOURCE_IDENTITY: missing required BrainVision field")
    channels = []
    for i in range(1, int(n_text) + 1):
        parts = fields.get(f"Ch{i}", "").split(",")
        if len(parts) < 3 or not parts[0]:
            raise ValueError(f"STOP_SOURCE_IDENTITY: malformed BrainVision channel resolution/unit: {parts!r}")
        try:
            resolution = float(parts[2])
        except ValueError as exc:
            raise ValueError("STOP_SOURCE_IDENTITY: nonnumeric BrainVision resolution") from exc
        unit = (parts[3].strip() if len(parts) >= 4 and parts[3].strip() else "µV").replace("μ", "µ")
        scale = {"µV": 1.0, "uV": 1.0, "mV": 1000.0, "V": 1_000_000.0}.get(unit)
        if scale is None or not np.isfinite(resolution):
            raise ValueError("STOP_SOURCE_IDENTITY: unsupported BrainVision unit")
        channels.append({"name": parts[0], "resolution": resolution, "unit": unit,
                         "unit_declaration": "header" if len(parts) >= 4 and parts[3].strip() else "BrainVision-Core-default-µV",
                         "to_microvolts": resolution * scale})
    if len(channels) != int(n_text):
        raise ValueError("STOP_SOURCE_IDENTITY: malformed BrainVision channel table")
    return {
        "sha256": hashlib.sha256(blob).hexdigest(),
        "number_of_channels": int(n_text),
        "sampling_interval_us": float(si_text),
        "data_file": fields["DataFile"],
        "little_endian": True,
        "endian_declaration": "UseBigEndianOrder=NO" if "UseBigEndianOrder" in fields else "BrainVision-Core/FieldTrip-ieee-le",
        "channels": channels,
    }


def _s3_url(relpath: str, version: str | None = None) -> str:
    base = f"{S3_ROOT}/{quote(relpath)}"
    return base if version is None else f"{base}?versionId={quote(version)}"


def _head_versioned(relpath: str) -> dict[str, str]:
    headers, _ = _request(_s3_url(relpath), "HEAD")
    required = ("x-amz-version-id", "etag", "content-length", "accept-ranges")
    missing = [name for name in required if name not in headers]
    if missing:
        raise ValueError(f"STOP_SOURCE_IDENTITY: missing S3 fields {missing}: {relpath}")
    return {"version_id": headers["x-amz-version-id"], "etag": headers["etag"],
            "content_length": headers["content-length"], "accept_ranges": headers["accept-ranges"]}


def build_source_lock() -> dict[str, Any]:
    """Build a metadata/header-only receipt; no .eeg GET request is made."""
    records: list[dict[str, Any]] = []
    for spec in FILES:
        annex_sha, annex_size = _annex_pointer(spec.rel_eeg)
        eeg_head = _head_versioned(spec.rel_eeg)
        vhdr_head = _head_versioned(spec.rel_vhdr)
        vhdr_get, vhdr_blob = _request(_s3_url(spec.rel_vhdr, vhdr_head["version_id"]))
        if (vhdr_get.get("x-amz-version-id") != vhdr_head["version_id"]
                or vhdr_get.get("etag") != vhdr_head["etag"]):
            raise ValueError(f"STOP_SOURCE_IDENTITY: versioned header GET/HEAD mismatch: {spec.rel_vhdr}")
        vhdr = _parse_vhdr(vhdr_blob)
        if (annex_size != int(eeg_head["content_length"]) or vhdr["number_of_channels"] != spec.n_channels
                or annex_size // (4 * spec.n_channels) != spec.blocks * N_SAMPLES
                or annex_size % (4 * spec.n_channels) != 0):
            raise ValueError(f"STOP_SOURCE_IDENTITY: size/channel/block mismatch: {spec.rel_eeg}")
        if vhdr["data_file"] != Path(spec.rel_eeg).name:
            raise ValueError(f"STOP_SOURCE_IDENTITY: header DataFile mismatch: {spec.rel_vhdr}")
        names = [channel["name"] for channel in vhdr["channels"]]
        if spec.clinical not in names or spec.bipolar_second not in names:
            raise ValueError(f"STOP_MEASUREMENT_APERTURE: frozen contacts absent: {spec.rel_eeg}")
        record = asdict(spec) | {
            "annex_sha256": annex_sha, "annex_size": annex_size,
            "samples": annex_size // (4 * spec.n_channels),
            "eeg": eeg_head, "vhdr": vhdr_head | vhdr,
            "clinical_index": names.index(spec.clinical), "bipolar_second_index": names.index(spec.bipolar_second),
            "clinical_to_microvolts": vhdr["channels"][names.index(spec.clinical)]["to_microvolts"],
            "bipolar_second_to_microvolts": vhdr["channels"][names.index(spec.bipolar_second)]["to_microvolts"],
        }
        records.append(record)
    return {"status": "SOURCE_LOCK_PASS", "commit": COMMIT, "fs_hz": FS,
            "window_indices": {key: value.tolist() for key, value in WINDOWS.items()}, "records": records}


def validate_source_lock(lock: dict[str, Any]) -> None:
    """Reject any lock that is not exactly the frozen 18-object canonical table."""
    if lock.get("status") != "SOURCE_LOCK_PASS" or lock.get("commit") != COMMIT or lock.get("fs_hz") != FS:
        raise ValueError("STOP_SOURCE_IDENTITY: source-lock identity fields")
    if lock.get("window_indices") != {key: value.tolist() for key, value in WINDOWS.items()}:
        raise ValueError("STOP_SOURCE_IDENTITY: source-lock timing grid")
    records = lock.get("records")
    if not isinstance(records, list) or len(records) != len(FILES):
        raise ValueError("STOP_SOURCE_IDENTITY: source-lock record count")
    expected = {(f.protocol, f.subject, f.phase): f for f in FILES}
    actual = {(r.get("protocol"), r.get("subject"), r.get("phase")): r for r in records}
    if len(actual) != len(FILES) or set(actual) != set(expected):
        raise ValueError("STOP_SOURCE_IDENTITY: source-lock duplicate or noncanonical key")
    for key, spec in expected.items():
        r = actual[key]
        for field in ("task", "blocks", "n_channels", "clinical", "bipolar_second"):
            if r.get(field) != getattr(spec, field):
                raise ValueError(f"STOP_SOURCE_IDENTITY: source-lock {field}: {key}")
        vhdr, eeg = r.get("vhdr", {}), r.get("eeg", {})
        if (r.get("samples") != spec.blocks * N_SAMPLES or r.get("annex_size") != 4 * spec.n_channels * spec.blocks * N_SAMPLES
                or int(eeg.get("content_length", -1)) != r["annex_size"]
                or vhdr.get("number_of_channels") != spec.n_channels
                or not np.isclose(vhdr.get("sampling_interval_us", np.nan), 1_000_000 / FS)
                or vhdr.get("data_file") != Path(spec.rel_eeg).name or vhdr.get("little_endian") is not True):
            raise ValueError(f"STOP_SOURCE_IDENTITY: source-lock structural receipt: {key}")
        channels = vhdr.get("channels", [])
        ci, bi = r.get("clinical_index"), r.get("bipolar_second_index")
        if (not isinstance(ci, int) or not isinstance(bi, int) or ci < 0 or bi < 0 or ci >= len(channels) or bi >= len(channels)
                or channels[ci].get("name") != spec.clinical or channels[bi].get("name") != spec.bipolar_second
                or channels[ci].get("to_microvolts") != r.get("clinical_to_microvolts")
                or channels[bi].get("to_microvolts") != r.get("bipolar_second_to_microvolts")):
            raise ValueError(f"STOP_MEASUREMENT_APERTURE: source-lock contact receipt: {key}")
        required = ("version_id", "etag", "content_length", "accept_ranges")
        if any(not eeg.get(x) or not vhdr.get(x) for x in required) or not r.get("annex_sha256") or not vhdr.get("sha256"):
            raise ValueError(f"STOP_SOURCE_IDENTITY: incomplete source-lock receipt: {key}")


def _dft_remove(x: np.ndarray) -> np.ndarray:
    t = np.arange(x.shape[-1], dtype=float) / FS
    columns = [np.ones_like(t)]
    for hz in (60.0, 120.0, 180.0):
        columns.extend((np.sin(2 * np.pi * hz * t), np.cos(2 * np.pi * hz * t)))
    design = np.stack(columns, axis=1)
    beta = np.linalg.lstsq(design, x.T, rcond=None)[0]
    return x - (design @ beta).T + beta[0][:, None]


def process_trials(trials: np.ndarray, subject: str) -> tuple[np.ndarray, np.ndarray]:
    """Return baseline-corrected trials and the contract-defined keep mask.

    MATLAB ``zscore`` operates down the trial dimension with N-1 sample standard
    deviation. MATLAB ``kurtosis(X,[],3)`` is bias-corrected Pearson kurtosis;
    undefined zero-variance z scores are frozen to zero by the contract.
    """
    if trials.ndim != 2 or trials.shape[1] != N_SAMPLES or not np.isfinite(trials).all():
        raise ValueError("IMPLEMENTATION_INVALID: trials must be finite (trial, 1000)")
    x = _dft_remove(np.asarray(trials, dtype=float))
    if subject == "p17":
        b, a = butter(10, 80.0, btype="low", fs=FS)
        x = filtfilt(b, a, x, axis=1)
    # The frozen contract defines x as the filter-and-baseline trace.  Artifact
    # criteria therefore must not inspect the unbaselined intermediate waveform.
    x = x - x[:, WINDOWS["baseline"]].mean(axis=1, keepdims=True)
    outside = (TIME_MS > 50) | (TIME_MS < -50)
    post = TIME_MS > 50
    amplitude_ok = np.max(np.abs(x[:, outside]), axis=1) < 500.0
    k = kurtosis(x[:, post], axis=1, fisher=False, bias=False, nan_policy="propagate")
    std = x.std(axis=0, ddof=1)
    z = np.divide(x - x.mean(axis=0), std, out=np.zeros_like(x), where=std != 0)
    keep = amplitude_ok & (k < 5.0) & ~np.any(np.abs(z) > 5.0, axis=1)
    return x, keep


def p2p_mean(trials: np.ndarray, keep: np.ndarray, window: str) -> float:
    if int(keep.sum()) < 20 or keep.mean() < 0.5:
        raise ValueError("STOP_MEASUREMENT_APERTURE: clean-trial aperture failed")
    waveform = trials[keep].mean(axis=0)
    values = waveform[WINDOWS[window]]
    return float(values.max() - values.min())


def _clean_summary(trials: np.ndarray, keep: np.ndarray) -> dict[str, Any]:
    if int(keep.sum()) < 20 or keep.mean() < 0.5:
        raise ValueError("STOP_MEASUREMENT_APERTURE: clean-trial aperture failed")
    clean = trials[keep]
    return {"clean_trials": int(keep.sum()), "total_trials": int(len(keep)),
            "clean_mean_waveform_microvolts": clean.mean(axis=0).tolist(),
            "clean_trial_p2p_microvolts": {
                window: np.ptp(clean[:, WINDOWS[window]], axis=1).tolist()
                for window in ("early", "late", "prestim")},
            "mean_waveform_p2p_microvolts": {window: p2p_mean(trials, keep, window)
                                               for window in ("early", "late", "prestim")}}


def shared_bootstrap(ts: np.ndarray, pb: np.ndarray, draws: int = 65536, seed: int = 20260825) -> tuple[float, float, float]:
    """Participant-cluster Bayesian bootstrap; overlapping p17/p19 share weights."""
    # Inputs are ordered p16,p17,p18,p19 and p17,p19,p20,UC004,UC005.
    rng = np.random.Generator(np.random.PCG64(seed))
    out = np.empty(draws)
    for i in range(draws):
        w = {name: rng.exponential() for name in ("p16", "p17", "p18", "p19", "p20", "UC004", "UC005")}
        out[i] = (np.average(ts, weights=[w[n] for n in ("p16", "p17", "p18", "p19")])
                  - np.average(pb, weights=[w[n] for n in ("p17", "p19", "p20", "UC004", "UC005")]))
    return float(np.quantile(out, .025)), float(np.quantile(out, .975)), float((out > 0).mean())


def _extract_multiplexed_chunks(chunks: Iterable[bytes], n_channels: int, selected: tuple[int, int], samples: int) -> np.ndarray:
    """Decode a little-endian BrainVision stream without retaining all channels."""
    frame_bytes = 4 * n_channels
    remainder = b""
    out = np.empty((2, samples), dtype=np.float32)
    offset = 0
    for chunk in chunks:
        payload = remainder + chunk
        complete = len(payload) - (len(payload) % frame_bytes)
        if complete:
            frames = np.frombuffer(payload[:complete], dtype="<f4").reshape(-1, n_channels)
            stop = offset + len(frames)
            if stop > samples:
                raise ValueError("STOP_SOURCE_IDENTITY: more samples than source-lock receipt")
            out[:, offset:stop] = frames[:, selected].T
            offset = stop
        remainder = payload[complete:]
    if remainder or offset != samples:
        raise ValueError("STOP_SOURCE_IDENTITY: incomplete multiplexed stream")
    return out


def _stream_selected(spec: EPFile, record: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    """Stream one version-pinned object and return selected µV traces plus receipt."""
    url = _s3_url(spec.rel_eeg, record["eeg"]["version_id"])
    selected = (record["clinical_index"], record["bipolar_second_index"])
    digest = hashlib.sha256()
    received = 0

    def stream() -> Iterable[bytes]:
        nonlocal received
        with urlopen(Request(url), timeout=120) as response:
            headers = {k.lower(): v for k, v in response.headers.items()}
            if (headers.get("x-amz-version-id") != record["eeg"]["version_id"]
                    or headers.get("etag") != record["eeg"]["etag"]):
                raise ValueError(f"STOP_SOURCE_IDENTITY: versioned EEG GET/HEAD mismatch: {spec.rel_eeg}")
            while block := response.read(1024 * 1024):
                digest.update(block)
                received += len(block)
                yield block

    # No full-object byte array or full-channel voltage matrix is retained.
    out = _extract_multiplexed_chunks(stream(), spec.n_channels, selected, spec.blocks * N_SAMPLES)
    if received != record["annex_size"] or digest.hexdigest() != record["annex_sha256"]:
        raise ValueError(f"STOP_SOURCE_IDENTITY: raw hash/size mismatch: {spec.rel_eeg}")
    receipt = {
        "rel_eeg": spec.rel_eeg, "expected_sha256": record["annex_sha256"],
        "observed_sha256": digest.hexdigest(), "expected_size": record["annex_size"],
        "observed_size": received, "version_id": record["eeg"]["version_id"],
        "etag": record["eeg"]["etag"], "header_sha256": record["vhdr"]["sha256"],
        "clinical_index": selected[0], "bipolar_second_index": selected[1],
    }
    scales = np.asarray((record["clinical_to_microvolts"], record["bipolar_second_to_microvolts"]), dtype=np.float32)
    return out.reshape(2, spec.blocks, N_SAMPLES) * scales[:, None, None], receipt


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _commit_raw_success(result_path: Path, progress_path: Path, payload: dict[str, Any]) -> None:
    """Commit final result before terminal progress; either artifact prevents a retry."""
    _atomic_json(result_path, payload)
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["status"] = "RAW_COMPLETE"
    progress["raw_result_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    _atomic_json(progress_path, progress)


def _loo(ts: np.ndarray, pb: np.ndarray) -> dict[str, float]:
    names = ("p16", "p17", "p18", "p19", "p20", "UC004", "UC005")
    ts_names, pb_names = ("p16", "p17", "p18", "p19"), ("p17", "p19", "p20", "UC004", "UC005")
    return {name: float(ts[[i for i, s in enumerate(ts_names) if s != name]].mean()
                        - pb[[i for i, s in enumerate(pb_names) if s != name]].mean())
            for name in names}


def _status_lattice(result: dict[str, Any]) -> dict[str, Any]:
    clinical, bipolar = result["clinical"]["late"], result["bipolar"]["late"]
    pre_lcb = result["clinical"]["prestim"]["bootstrap"][0]
    flags = []
    if clinical["D"] <= 0:
        return {"same_data_status": "SAME_DATA_REANALYSIS_NOT_SUPPORTED",
                "flags": ["CLINICAL_DIRECTION_NONPOSITIVE"],
                "published_model_status": "PUBLISHED_MODEL_ENGINE_UNAVAILABLE",
                "estimand_discordance": "UNASSESSABLE_MODEL_ENGINE_UNAVAILABLE"}
    if clinical["bootstrap"][0] <= 0:
        flags.append("CI_LIMITED")
    if bipolar["D"] <= 0 or bipolar["bootstrap"][0] <= 0:
        flags.append("REFERENCE_SENSITIVE_OR_UNCERTAIN")
    if clinical["paired_p17_p19"] <= 0:
        flags.append("PAIRED_SENSITIVITY_FAIL")
    if pre_lcb > 0:
        flags.append("BASELINE_ARTIFACT_CONCERN")
    if result["clinical"]["early"]["bootstrap"][0] > 0:
        flags.append("EARLY_NONSPECIFICITY_CONCERN")
    if any(value <= 0 for value in clinical["leave_one_participant_out"].values()):
        flags.append("PARTICIPANT_SENSITIVE")
    if not flags:
        status = "SAME_DATA_REANALYSIS_REFERENCE_ROBUST_SUPPORT"
    else:
        status = "SAME_DATA_REANALYSIS_SUPPORT_SENSITIVITY_LIMITED"
    return {"same_data_status": status, "flags": flags,
            "published_model_status": "PUBLISHED_MODEL_ENGINE_UNAVAILABLE",
            "estimand_discordance": "UNASSESSABLE_MODEL_ENGINE_UNAVAILABLE"}


def run_raw_one_shot(lock: dict[str, Any], lock_sha256: str, progress_path: Path) -> dict[str, Any]:
    """Execute the frozen sequential raw analysis after a serialized source lock."""
    by_key = {(x["protocol"], x["subject"], x["phase"]): x for x in lock["records"]}
    result: dict[str, Any] = {"status": "RAW_COMPLETE", "attempt_id": "ATTEMPT1",
                              "source_lock_sha256": lock_sha256,
                              "model_lane": "PUBLISHED_MODEL_ENGINE_UNAVAILABLE", "files": []}
    progress: dict[str, Any] = {"status": "RAW_IN_PROGRESS", "attempt_id": "ATTEMPT1",
                                "source_lock_sha256": lock_sha256, "completed_files": []}
    _atomic_json(progress_path, progress)
    deltas: dict[tuple[str, str, str], float] = {}
    try:
        for spec in FILES:
            record = by_key[(spec.protocol, spec.subject, spec.phase)]
            selected, integrity = _stream_selected(spec, record)
            clinical, other = selected
            refs = {"clinical": clinical, "bipolar": clinical - other}
            measures: dict[str, Any] = {}
            for ref_name, trial_matrix in refs.items():
                cleaned, keep = process_trials(trial_matrix, spec.subject)
                measures[ref_name] = _clean_summary(cleaned, keep)
                for w, value in measures[ref_name]["mean_waveform_p2p_microvolts"].items():
                    deltas[(spec.protocol, spec.subject, f"{ref_name}:{w}:{spec.phase}")] = value
            file_receipt = {"protocol": spec.protocol, "subject": spec.subject, "phase": spec.phase,
                            "task": spec.task, "integrity": integrity, "measures": measures}
            result["files"].append(file_receipt)
            progress["completed_files"].append({key: file_receipt[key] for key in ("protocol", "subject", "phase", "task")} | {"integrity": integrity})
            _atomic_json(progress_path, progress)
    except Exception as exc:
        progress["status"] = "RAW_STOP"
        progress["error"] = f"{type(exc).__name__}: {exc}"
        _atomic_json(progress_path, progress)
        raise
    for ref in ("clinical", "bipolar"):
        result[ref] = {}
        for window in ("early", "late", "prestim"):
            ts = np.array([deltas[("TS", s, f"{ref}:{window}:post")] - deltas[("TS", s, f"{ref}:{window}:pre")]
                           for s in ("p16", "p17", "p18", "p19")])
            pb = np.array([deltas[("PB", s, f"{ref}:{window}:post")] - deltas[("PB", s, f"{ref}:{window}:pre")]
                           for s in ("p17", "p19", "p20", "UC004", "UC005")])
            result[ref][window] = {"ts_deltas": ts.tolist(), "pb_deltas": pb.tolist(),
                                    "D": float(ts.mean() - pb.mean()),
                                    "bootstrap": shared_bootstrap(ts, pb),
                                    "paired_p17_p19": float(np.mean(ts[[1, 3]] - pb[:2])),
                                    "leave_one_participant_out": _loo(ts, pb)}
    result["status_lattice"] = _status_lattice(result)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("source-lock", "raw-one-shot"))
    parser.add_argument("--lock", type=Path, default=RUN_DIR / "artifacts" / "source_lock.json")
    parser.add_argument("--result", type=Path, default=RUN_DIR / "artifacts" / "raw_result.json")
    parser.add_argument("--progress", type=Path, default=RUN_DIR / "artifacts" / "raw_progress.json")
    args = parser.parse_args(argv)
    if args.stage == "source-lock":
        payload = build_source_lock()
        _atomic_json(args.lock, payload)
    else:
        if args.progress.exists() or args.result.exists():
            raise ValueError("IMPLEMENTATION_INVALID: existing one-shot transaction receipt")
        lock_bytes = args.lock.read_bytes()
        if hashlib.sha256(lock_bytes).hexdigest() != SOURCE_LOCK_SHA256:
            raise ValueError("STOP_SOURCE_IDENTITY: source-lock SHA-256 does not match frozen receipt")
        lock = json.loads(lock_bytes)
        validate_source_lock(lock)
        payload = run_raw_one_shot(lock, hashlib.sha256(lock_bytes).hexdigest(), args.progress)
        _commit_raw_success(args.result, args.progress, payload)
    print(json.dumps({"status": payload["status"], "output": str(args.lock if args.stage == "source-lock" else args.result)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
