"""Prepare the sealed, mode-aware BA-SRM4 discovery dataset.

Only predecessor-contacted BA-SRM2/3 train sequences are allowed to expose
pulse-response outcomes.  All other slice groups are classified structurally,
but validation and confirmation outcomes are never queried.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from typing import Any, Iterable

import numpy as np


VERSION = "BA-SRM4-MODE-AWARE-DISCOVERY-V2-LIMS-SLICE-GROUP"
SPLIT_SALT = "BA-SRM4-GROUP-SPLIT-V1:"
EXPECTED_DATABASE_SHA256 = (
    "dbf19786f9e0d0d73c26351dc29d69ef8c10a2e67e32e19ac73034a5624d48c5"
)
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "4ddb4a52294a55b011c5118a02432ca28c057ca5b5ebb63d8d7c945923aa62c2"
)
EXPECTED_ELIGIBLE_MANIFEST_SHA256 = (
    "74d6d3b142e48d7906305e133983b91cc8227a40748335985414e674dd1fd81c"
)

TIME_REF_S = 1e-3
VOLTAGE_REF_V = 1e-3
CURRENT_REF_A = 1e-12
RESISTANCE_REF_OHM = 1e6
CAPACITANCE_REF_F = 1e-12
LENGTH_REF_M = 1e-4
TEMPERATURE_REF_K = 310.0

HISTORY_PULSES = tuple(range(0, 8))
TARGET_PULSES = tuple(range(8, 12))
TARGET_FIELDS = (
    "dec_fit_reconv_amp",
    "dec_fit_latency",
    "dec_fit_rise_time",
    "dec_fit_decay_tau",
)

FEATURE_NAMES = (
    "log_frequency_T0",
    "log_recovery_delay_T0",
    "bath_temperature_K_over_Theta0",
    "post_baseline_potential_over_V0",
    "post_baseline_current_over_I0",
    "post_noise_ic_over_V0",
    "post_noise_vc_over_I0",
    "pair_distance_over_L0",
    "post_input_resistance_over_R0",
    "post_capacitance_over_C0",
    "post_time_constant_over_T0",
    "history_mean_log_dt_T0",
    "history_last_log_dt_T0",
    "history_mean_spike_count",
    "history_last_spike_count",
    "history_mean_first_spike_over_T0",
    "history_mean_stim_ic_over_I0",
    "history_last_stim_ic_over_I0",
    "history_mean_stim_vc_over_V0",
    "history_last_stim_vc_over_V0",
    "history_mean_response_ic_over_V0",
    "history_last_response_ic_over_V0",
    "history_slope_response_ic_over_V0",
    "history_mean_response_vc_over_I0",
    "history_last_response_vc_over_I0",
    "history_slope_response_vc_over_I0",
    "history_mean_latency_over_T0",
    "history_mean_rise_over_T0",
    "history_mean_decay_over_T0",
    "history_amp_trace_tau10_typed",
    "history_amp_trace_tau50_typed",
    "history_spike_trace_tau10",
    "history_spike_trace_tau50",
)

TARGET_NAMES = tuple(
    f"p{pulse}:{field}"
    for pulse in TARGET_PULSES
    for field in ("response_amplitude_typed", "latency_over_T0", "rise_over_T0", "decay_over_T0")
)


DISCOVERY_SQL = """
SELECT
    ss.sequence_key,
    ss.slice_ext_id AS manifest_slice_ext_id,
    ss.synapse_type AS manifest_synapse_type,
    sl.id AS observed_slice_id,
    sl.ext_id AS observed_slice_ext_id,
    sy.synapse_type AS observed_synapse_type,
    pa.id AS pair_id,
    post_r.id AS post_recording_id,
    pre_r.id AS pre_recording_id,
    pre_pcr.clamp_mode AS pre_clamp_mode,
    post_pcr.clamp_mode AS post_clamp_mode,
    sp.id AS stim_pulse_id,
    sp.pulse_number,
    sp.onset_time,
    sp.previous_pulse_dt,
    sp.amplitude AS stim_amplitude,
    sp.duration AS stim_duration,
    sp.n_spikes,
    sp.first_spike_time - sp.onset_time AS first_spike_after_onset,
    pr.ex_qc_pass,
    pr.in_qc_pass,
    prf.dec_fit_reconv_amp,
    prf.baseline_dec_fit_reconv_amp,
    prf.dec_fit_latency,
    prf.dec_fit_rise_time,
    prf.dec_fit_decay_tau,
    prf.dec_fit_nrmse,
    mpp.induction_frequency,
    mpp.recovery_delay,
    post_sr.temperature AS bath_temperature,
    post_pcr.baseline_potential,
    post_pcr.baseline_current,
    post_pcr.baseline_noise_stdev,
    pa.distance AS pair_soma_distance,
    post_tp.input_resistance AS post_input_resistance,
    post_tp.capacitance AS post_capacitance,
    post_tp.time_constant AS post_time_constant
FROM selected_discovery_sequence ss
JOIN pair pa ON pa.id = ss.pair_id
JOIN experiment ex ON ex.id = pa.experiment_id
JOIN slice sl ON sl.id = ex.slice_id
JOIN synapse sy
  ON sy.pair_id = pa.id AND sy.synapse_type = ss.synapse_type
JOIN cell pre_c ON pre_c.id = pa.pre_cell_id
JOIN cell post_c ON post_c.id = pa.post_cell_id
JOIN pulse_response pr ON pr.pair_id = pa.id
JOIN stim_pulse sp
  ON sp.id = pr.stim_pulse_id
 AND sp.recording_id = ss.pre_recording_id
JOIN recording post_r
  ON post_r.id = pr.recording_id
 AND post_r.id = ss.post_recording_id
JOIN recording pre_r ON pre_r.id = sp.recording_id
JOIN sync_rec post_sr ON post_sr.id = post_r.sync_rec_id
JOIN sync_rec pre_sr ON pre_sr.id = pre_r.sync_rec_id
JOIN patch_clamp_recording post_pcr
  ON post_pcr.recording_id = post_r.id
JOIN patch_clamp_recording pre_pcr
  ON pre_pcr.recording_id = pre_r.id
JOIN multi_patch_probe mpp
  ON mpp.patch_clamp_recording_id = post_pcr.id
LEFT JOIN pulse_response_fit prf ON prf.pulse_response_id = pr.id
LEFT JOIN test_pulse post_tp ON post_tp.id = post_pcr.nearest_test_pulse_id
WHERE post_r.stim_name IS ss.post_stim_name
  AND mpp.induction_frequency = ss.induction_frequency
  AND mpp.recovery_delay = ss.recovery_delay
  AND post_r.id <> pre_r.id
  AND post_r.sync_rec_id = pre_r.sync_rec_id
  AND post_sr.experiment_id = pa.experiment_id
  AND pre_sr.experiment_id = pa.experiment_id
  AND (sp.cell_id IS NULL OR sp.cell_id = pa.pre_cell_id)
  AND pre_r.electrode_id = pre_c.electrode_id
  AND post_r.electrode_id = post_c.electrode_id
ORDER BY ss.sequence_key, sp.pulse_number, sp.onset_time, sp.id
"""


class PreparationFailure(RuntimeError):
    """Raised when the discovery boundary or typed-unit contract is violated."""


def sha256_file(path: Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_jsonl(path: Path, expected_sha256: str) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_sha256:
        raise PreparationFailure(f"SHA-256 mismatch: {path}")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def split_bucket(group_id: str) -> int:
    digest = hashlib.sha256((SPLIT_SALT + str(group_id)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % 10


def assigned_split(group_id: str, predecessor_groups: set[str]) -> str:
    if str(group_id) in predecessor_groups:
        return "discovery-contaminated"
    bucket = split_bucket(str(group_id))
    if bucket <= 5:
        return "discovery"
    if bucket <= 7:
        return "validation"
    return "confirmation"


def finite(value: Any) -> bool:
    if value is None:
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def number(value: Any) -> float:
    return float(value) if finite(value) else float("nan")


def positive_log(value: Any) -> float:
    raw = number(value)
    return math.log(raw) if math.isfinite(raw) and raw > 0.0 else float("nan")


def finite_mean(values: Iterable[Any]) -> float:
    observed = np.asarray([float(value) for value in values if finite(value)], dtype=float)
    return float(np.mean(observed)) if observed.size else float("nan")


def finite_last(values: Iterable[Any]) -> float:
    observed = [float(value) for value in values if finite(value)]
    return observed[-1] if observed else float("nan")


def finite_slope(values: Iterable[Any]) -> float:
    observed = [(idx, float(value)) for idx, value in enumerate(values) if finite(value)]
    if len(observed) < 2:
        return float("nan")
    x = np.asarray([item[0] for item in observed], dtype=float)
    y = np.asarray([item[1] for item in observed], dtype=float)
    x = x - np.mean(x)
    denominator = float(x @ x)
    return float((x @ (y - np.mean(y))) / denominator) if denominator > 0.0 else float("nan")


def typed_command(value: Any, clamp_mode: str) -> tuple[float, float]:
    raw = number(value)
    if clamp_mode == "ic":
        return raw / CURRENT_REF_A, float("nan")
    if clamp_mode == "vc":
        return float("nan"), raw / VOLTAGE_REF_V
    raise PreparationFailure(f"unsupported presynaptic clamp mode: {clamp_mode}")


def typed_response(value: Any, clamp_mode: str) -> tuple[float, float]:
    raw = number(value)
    if clamp_mode == "ic":
        return raw / VOLTAGE_REF_V, float("nan")
    if clamp_mode == "vc":
        return float("nan"), raw / CURRENT_REF_A
    raise PreparationFailure(f"unsupported postsynaptic clamp mode: {clamp_mode}")


def typed_response_scalar(value: Any, clamp_mode: str) -> float:
    voltage, current = typed_response(value, clamp_mode)
    return voltage if clamp_mode == "ic" else current


def assert_discovery_sql(sql: str) -> None:
    normalized = " ".join(sql.lower().split())
    if "from selected_discovery_sequence" not in normalized:
        raise PreparationFailure("outcome SQL is not selected-discovery scoped")
    for forbidden in (
        "stim_pulse.data",
        "pulse_response.data",
        "baseline.data",
        " validation ",
        " confirmation ",
    ):
        if forbidden in f" {normalized} ":
            raise PreparationFailure(f"forbidden discovery SQL token: {forbidden.strip()}")


def table_columns(con: sqlite3.Connection) -> dict[str, set[str]]:
    tables = [
        str(row[0])
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    return {
        table: {str(row[1]) for row in con.execute(f'PRAGMA table_info("{table}")')}
        for table in tables
    }


def validate_schema(columns: dict[str, set[str]]) -> dict[str, Any]:
    required = {
        "slice": {"id", "ext_id", "lims_specimen_name"},
        "experiment": {"id", "slice_id"},
        "pair": {"id", "experiment_id", "pre_cell_id", "post_cell_id"},
        "recording": {"id", "sync_rec_id", "stim_name"},
        "patch_clamp_recording": {
            "id",
            "recording_id",
            "clamp_mode",
            "baseline_potential",
            "baseline_current",
            "baseline_noise_stdev",
        },
        "stim_pulse": {"id", "recording_id", "pulse_number", "amplitude", "onset_time"},
        "pulse_response": {"id", "pair_id", "recording_id", "stim_pulse_id", "ex_qc_pass", "in_qc_pass"},
        "pulse_response_fit": set(TARGET_FIELDS),
    }
    missing: dict[str, list[str]] = {}
    for table, names in required.items():
        absent = sorted(names - columns.get(table, set()))
        if absent:
            missing[table] = absent
    if missing:
        raise PreparationFailure(f"required schema fields missing: {missing}")
    identity_hits = sorted(
        f"{table}.{column}"
        for table, names in columns.items()
        for column in names
        if any(token in column.lower() for token in ("donor", "animal", "subject", "organism", "specimen"))
    )
    return {
        "required_tables_pass": True,
        "identity_like_columns": identity_hits,
        "highest_stable_group_key": "slice.lims_specimen_name",
        "group_semantics": "conservative LIMS slice-specimen equivalence class, not donor/animal",
        "row_identity_key": "slice.ext_id",
        "donor_identity_status": "UNRESOLVED_IDENTITY_KEY",
        "donor_held_out_claim_allowed": False,
    }


def split_rows(
    con: sqlite3.Connection, predecessor_slice_ext_ids: set[str]
) -> tuple[list[dict[str, Any]], dict[str, str], set[str]]:
    rows = list(
        con.execute(
            "SELECT id, ext_id, lims_specimen_name FROM slice ORDER BY id"
        )
    )
    seen_ext_ids: set[str] = set()
    ext_to_group: dict[str, str] = {}
    for _, ext_id, lims_specimen_name in rows:
        if ext_id is None or not str(ext_id):
            raise PreparationFailure("slice.ext_id is NULL/empty")
        if lims_specimen_name is None or not str(lims_specimen_name):
            raise PreparationFailure("slice.lims_specimen_name is NULL/empty")
        ext = str(ext_id)
        if ext in seen_ext_ids:
            raise PreparationFailure(f"duplicate slice.ext_id: {ext}")
        seen_ext_ids.add(ext)
        ext_to_group[ext] = str(lims_specimen_name)
    absent = predecessor_slice_ext_ids - seen_ext_ids
    if absent:
        raise PreparationFailure(f"predecessor slice rows absent from pinned DB: {len(absent)}")
    predecessor_groups = {
        ext_to_group[ext_id] for ext_id in predecessor_slice_ext_ids
    }

    result: list[dict[str, Any]] = []
    for slice_id, ext_id, lims_specimen_name in rows:
        ext = str(ext_id)
        group_id = str(lims_specimen_name)
        result.append(
            {
                "version": VERSION,
                "slice_id": int(slice_id),
                "slice_ext_id": ext,
                "lims_specimen_name": group_id,
                "group_id": group_id,
                "raw_bucket": split_bucket(group_id),
                "predecessor_contact": group_id in predecessor_groups,
                "assigned_split": assigned_split(group_id, predecessor_groups),
            }
        )
    return result, ext_to_group, predecessor_groups


def create_selected_table(
    con: sqlite3.Connection, selected: Iterable[dict[str, Any]]
) -> None:
    con.execute(
        """
        CREATE TEMP TABLE selected_discovery_sequence(
            sequence_key TEXT PRIMARY KEY,
            slice_ext_id TEXT NOT NULL,
            synapse_type TEXT NOT NULL,
            pair_id INTEGER NOT NULL,
            post_recording_id INTEGER NOT NULL,
            pre_recording_id INTEGER NOT NULL,
            post_stim_name TEXT,
            induction_frequency REAL NOT NULL,
            recovery_delay REAL NOT NULL
        )
        """
    )
    con.executemany(
        "INSERT INTO selected_discovery_sequence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            (
                row["sequence_key"],
                row["slice_ext_id"],
                row["synapse_type"],
                row["pair_id"],
                row["post_recording_id"],
                row["pre_recording_id"],
                row["post_stim_name"],
                row["induction_frequency"],
                row["recovery_delay"],
            )
            for row in selected
        ),
    )


def exact_sequence(rows: list[sqlite3.Row]) -> bool:
    if len(rows) != 12:
        return False
    ordered = sorted(rows, key=lambda row: int(row["pulse_number"]))
    if [int(row["pulse_number"]) for row in ordered] != list(range(12)):
        return False
    onsets = [number(row["onset_time"]) for row in ordered]
    return all(math.isfinite(value) for value in onsets) and all(
        right > left for left, right in zip(onsets, onsets[1:])
    )


def type_matched_qc(rows: list[sqlite3.Row], synapse_type: str) -> bool:
    field = "ex_qc_pass" if synapse_type == "ex" else "in_qc_pass"
    return all(row[field] == 1 for row in rows)


def complete_target(rows: list[sqlite3.Row]) -> bool:
    by_pulse = {int(row["pulse_number"]): row for row in rows}
    return all(
        finite(by_pulse[pulse][field])
        for pulse in TARGET_PULSES
        for field in TARGET_FIELDS
    )


def feature_row(rows: list[sqlite3.Row]) -> tuple[list[float], list[float]]:
    pulses = {int(row["pulse_number"]): row for row in rows}
    history = [pulses[pulse] for pulse in HISTORY_PULSES]
    first = history[0]
    pre_mode = str(first["pre_clamp_mode"])
    post_mode = str(first["post_clamp_mode"])
    if any(str(row["pre_clamp_mode"]) != pre_mode for row in rows):
        raise PreparationFailure("presynaptic clamp mode changes within sequence")
    if any(str(row["post_clamp_mode"]) != post_mode for row in rows):
        raise PreparationFailure("postsynaptic clamp mode changes within sequence")

    dt_scaled = [number(row["previous_pulse_dt"]) / TIME_REF_S for row in history]
    log_dt = [positive_log(value) for value in dt_scaled]
    spikes = [number(row["n_spikes"]) for row in history]
    first_spike = [number(row["first_spike_after_onset"]) / TIME_REF_S for row in history]

    stim_ic: list[float] = []
    stim_vc: list[float] = []
    response_ic: list[float] = []
    response_vc: list[float] = []
    response_typed: list[float] = []
    for row in history:
        ic, vc = typed_command(row["stim_amplitude"], pre_mode)
        stim_ic.append(ic)
        stim_vc.append(vc)
        ric, rvc = typed_response(row["dec_fit_reconv_amp"], post_mode)
        response_ic.append(ric)
        response_vc.append(rvc)
        response_typed.append(ric if post_mode == "ic" else rvc)

    target_onset = number(pulses[8]["onset_time"])
    lags = [target_onset - number(row["onset_time"]) for row in history]
    if not all(math.isfinite(value) and value > 0.0 for value in lags):
        raise PreparationFailure("history-to-target lags are not positive finite")

    def exp_trace(values: list[float], tau_s: float) -> float:
        terms = [
            value * math.exp(-lag / tau_s)
            for value, lag in zip(values, lags)
            if math.isfinite(value)
        ]
        return float(sum(terms)) if terms else float("nan")

    bath_c = number(first["bath_temperature"])
    noise_ic, noise_vc = typed_response(first["baseline_noise_stdev"], post_mode)
    features = [
        positive_log(number(first["induction_frequency"]) * TIME_REF_S),
        positive_log(number(first["recovery_delay"]) / TIME_REF_S),
        (bath_c + 273.15) / TEMPERATURE_REF_K if math.isfinite(bath_c) else float("nan"),
        number(first["baseline_potential"]) / VOLTAGE_REF_V,
        number(first["baseline_current"]) / CURRENT_REF_A,
        noise_ic,
        noise_vc,
        number(first["pair_soma_distance"]) / LENGTH_REF_M,
        number(first["post_input_resistance"]) / RESISTANCE_REF_OHM,
        number(first["post_capacitance"]) / CAPACITANCE_REF_F,
        number(first["post_time_constant"]) / TIME_REF_S,
        finite_mean(log_dt),
        finite_last(log_dt),
        finite_mean(spikes),
        finite_last(spikes),
        finite_mean(first_spike),
        finite_mean(stim_ic),
        finite_last(stim_ic),
        finite_mean(stim_vc),
        finite_last(stim_vc),
        finite_mean(response_ic),
        finite_last(response_ic),
        finite_slope(response_ic),
        finite_mean(response_vc),
        finite_last(response_vc),
        finite_slope(response_vc),
        finite_mean(number(row["dec_fit_latency"]) / TIME_REF_S for row in history),
        finite_mean(number(row["dec_fit_rise_time"]) / TIME_REF_S for row in history),
        finite_mean(number(row["dec_fit_decay_tau"]) / TIME_REF_S for row in history),
        exp_trace(response_typed, 10.0 * TIME_REF_S),
        exp_trace(response_typed, 50.0 * TIME_REF_S),
        exp_trace(spikes, 10.0 * TIME_REF_S),
        exp_trace(spikes, 50.0 * TIME_REF_S),
    ]
    if len(features) != len(FEATURE_NAMES):
        raise AssertionError("feature schema length mismatch")

    target: list[float] = []
    for pulse in TARGET_PULSES:
        row = pulses[pulse]
        target.extend(
            [
                typed_response_scalar(row["dec_fit_reconv_amp"], post_mode),
                number(row["dec_fit_latency"]) / TIME_REF_S,
                number(row["dec_fit_rise_time"]) / TIME_REF_S,
                number(row["dec_fit_decay_tau"]) / TIME_REF_S,
            ]
        )
    if len(target) != len(TARGET_NAMES) or not all(math.isfinite(value) for value in target):
        raise PreparationFailure("target is not finite 16-coordinate vector")
    return features, target


def render_jsonl(rows: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(
        (
            json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        for row in rows
    )


def write_new_bytes(path: Path, payload: bytes) -> None:
    if path.exists():
        raise PreparationFailure(f"refusing to overwrite artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    if partial.exists():
        raise PreparationFailure(f"stale partial artifact: {partial}")
    partial.write_bytes(payload)
    if partial.read_bytes() != payload:
        raise PreparationFailure(f"artifact verification failed: {path}")
    partial.replace(path)


def prepare(
    database: Path,
    source_manifest: Path,
    eligible_manifest: Path,
    split_output: Path,
    dataset_output: Path,
    receipt_output: Path,
) -> dict[str, Any]:
    database = database.resolve(strict=True)
    if sha256_file(database) != EXPECTED_DATABASE_SHA256:
        raise PreparationFailure("database SHA-256 mismatch")
    source_rows = load_jsonl(source_manifest, EXPECTED_SOURCE_MANIFEST_SHA256)
    eligible_rows = load_jsonl(eligible_manifest, EXPECTED_ELIGIBLE_MANIFEST_SHA256)
    source_by_key = {str(row["sequence_key"]): row for row in source_rows}
    if len(source_by_key) != len(source_rows):
        raise PreparationFailure("duplicate source-manifest sequence key")
    selected: list[dict[str, Any]] = []
    for eligible in eligible_rows:
        key = str(eligible["sequence_key"])
        source = source_by_key.get(key)
        if source is None:
            raise PreparationFailure("eligible key absent from source manifest")
        for field in ("slice_id", "slice_ext_id", "synapse_type"):
            if str(source[field]) != str(eligible[field]):
                raise PreparationFailure(f"eligible/source mismatch: {field}")
        selected.append(source)

    predecessor_slice_ext_ids = {
        str(row["slice_ext_id"]) for row in source_rows
    }

    uri = f"file:{database.as_posix()}?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        columns = table_columns(con)
        schema_receipt = validate_schema(columns)
        groups, ext_to_group, predecessor_groups = split_rows(
            con, predecessor_slice_ext_ids
        )
        if any(
            assigned_split(ext_to_group[str(row["slice_ext_id"])], predecessor_groups)
            != "discovery-contaminated"
            for row in selected
        ):
            raise PreparationFailure("selected outcome row escaped predecessor quarantine")
        create_selected_table(con, selected)
        assert_discovery_sql(DISCOVERY_SQL)
        events = list(con.execute(DISCOVERY_SQL))
    finally:
        con.close()

    split_bytes = render_jsonl(groups)
    by_sequence: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in events:
        by_sequence[str(row["sequence_key"])].append(row)
    if set(by_sequence) != {str(row["sequence_key"]) for row in selected}:
        raise PreparationFailure("extracted sequence set differs from frozen eligible set")

    features: list[list[float]] = []
    targets: list[list[float]] = []
    sequence_keys: list[str] = []
    slice_ids: list[str] = []
    group_ids: list[str] = []
    synapse_types: list[str] = []
    pre_modes: list[str] = []
    post_modes: list[str] = []
    source_order = sorted(
        selected,
        key=lambda row: (
            str(row["synapse_type"]),
            str(row["slice_ext_id"]).encode("utf-8"),
            str(row["sequence_key"]),
        ),
    )
    for source in source_order:
        key = str(source["sequence_key"])
        rows = by_sequence[key]
        if not exact_sequence(rows):
            raise PreparationFailure("selected sequence is not exact ordered pulse 0..11")
        if not type_matched_qc(rows, str(source["synapse_type"])):
            raise PreparationFailure("selected sequence lost type-matched response QC")
        if not complete_target(rows):
            raise PreparationFailure("selected sequence lost fixed 16-coordinate target")
        if any(str(row["observed_slice_ext_id"]) != str(source["slice_ext_id"]) for row in rows):
            raise PreparationFailure("observed slice differs from manifest")
        if any(str(row["observed_synapse_type"]) != str(source["synapse_type"]) for row in rows):
            raise PreparationFailure("observed synapse type differs from manifest")
        feature, target = feature_row(rows)
        features.append(feature)
        targets.append(target)
        sequence_keys.append(key)
        slice_ids.append(str(source["slice_ext_id"]))
        group_ids.append(ext_to_group[str(source["slice_ext_id"])])
        synapse_types.append(str(source["synapse_type"]))
        pre_modes.append(str(rows[0]["pre_clamp_mode"]))
        post_modes.append(str(rows[0]["post_clamp_mode"]))

    arrays = {
        "features": np.asarray(features, dtype=float),
        "target": np.asarray(targets, dtype=float),
        "feature_names": np.asarray(FEATURE_NAMES, dtype=str),
        "target_names": np.asarray(TARGET_NAMES, dtype=str),
        "sequence_key": np.asarray(sequence_keys, dtype=str),
        "slice_ext_id": np.asarray(slice_ids, dtype=str),
        "group_id": np.asarray(group_ids, dtype=str),
        "synapse_type": np.asarray(synapse_types, dtype=str),
        "pre_clamp_mode": np.asarray(pre_modes, dtype=str),
        "post_clamp_mode": np.asarray(post_modes, dtype=str),
    }
    if dataset_output.exists():
        raise PreparationFailure(f"refusing to overwrite artifact: {dataset_output}")
    partial_npz = dataset_output.with_name(dataset_output.name + ".partial.npz")
    if partial_npz.exists():
        raise PreparationFailure(f"stale partial artifact: {partial_npz}")
    dataset_output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(partial_npz, **arrays)
    with np.load(partial_npz, allow_pickle=False) as observed:
        if set(observed.files) != set(arrays):
            raise PreparationFailure("dataset NPZ key mismatch")
        for key, expected in arrays.items():
            actual = observed[key]
            if actual.dtype.kind in "fc":
                if not np.array_equal(actual, expected, equal_nan=True):
                    raise PreparationFailure(f"dataset NPZ mismatch: {key}")
            elif not np.array_equal(actual, expected):
                raise PreparationFailure(f"dataset NPZ mismatch: {key}")
    partial_npz.replace(dataset_output)

    group_assignments: dict[str, str] = {}
    for row in groups:
        group_id = str(row["group_id"])
        split = str(row["assigned_split"])
        previous = group_assignments.setdefault(group_id, split)
        if previous != split:
            raise PreparationFailure("one LIMS slice-specimen group spans assigned splits")
    split_counts = Counter(group_assignments.values())
    mode_counts = Counter(
        f"{label}|pre={pre}|post={post}"
        for label, pre, post in zip(synapse_types, pre_modes, post_modes)
    )
    stratum_receipt: dict[str, Any] = {}
    target_array = arrays["target"]
    for label in sorted(mode_counts):
        synapse, pre_item, post_item = label.split("|")
        pre_mode = pre_item.split("=", 1)[1]
        post_mode = post_item.split("=", 1)[1]
        mask = (
            (arrays["synapse_type"] == synapse)
            & (arrays["pre_clamp_mode"] == pre_mode)
            & (arrays["post_clamp_mode"] == post_mode)
        )
        values = target_array[mask]
        med = np.median(values, axis=0)
        mad = np.median(np.abs(values - med[None, :]), axis=0)
        stratum_receipt[label] = {
            "sequences": int(np.sum(mask)),
            "slice_specimen_groups": int(np.unique(arrays["group_id"][mask]).size),
            "slice_rows": int(np.unique(arrays["slice_ext_id"][mask]).size),
            "target_coordinates": int(values.shape[1]),
            "positive_finite_target_mad_count": int(np.sum(np.isfinite(mad) & (mad > 0.0))),
        }

    write_new_bytes(split_output, split_bytes)
    receipt = {
        "status": "PASS_DISCOVERY_DATASET",
        "version": VERSION,
        "database": str(database),
        "database_sha256": EXPECTED_DATABASE_SHA256,
        "source_manifest": str(source_manifest.resolve(strict=True)),
        "source_manifest_sha256": EXPECTED_SOURCE_MANIFEST_SHA256,
        "eligible_manifest": str(eligible_manifest.resolve(strict=True)),
        "eligible_manifest_sha256": EXPECTED_ELIGIBLE_MANIFEST_SHA256,
        "schema": schema_receipt,
        "split_salt": SPLIT_SALT,
        "split_group_counts": dict(sorted(split_counts.items())),
        "split_slice_row_count": len(groups),
        "predecessor_contact_groups": len(predecessor_groups),
        "split_manifest": str(split_output.resolve()),
        "split_manifest_sha256": sha256_bytes(split_bytes),
        "dataset": str(dataset_output.resolve()),
        "dataset_sha256": sha256_file(dataset_output),
        "eligible_sequences": len(sequence_keys),
        "event_rows": len(events),
        "mode_sequence_counts": dict(sorted(mode_counts.items())),
        "strata": stratum_receipt,
        "feature_count": len(FEATURE_NAMES),
        "target_count": len(TARGET_NAMES),
        "typed_unit_contract": {
            "pre_ic_command": "A/I0",
            "pre_vc_command": "V/V0",
            "post_ic_response": "V/V0",
            "post_vc_response": "A/I0",
            "structural_missing_channel": "NaN",
            "zero_fill_before_mode_stratification": False,
        },
        "discovery_outcomes_read": True,
        "all_outcome_rows_predecessor_contacted": True,
        "validation_outcomes_read": False,
        "confirmation_outcomes_read": False,
        "waveform_blobs_read": False,
        "claim_ceiling": "discovery-only empirical candidate; LIMS slice-specimen grouping is not donor-held-out; no causal, AGI, or infinite-rank claim",
    }
    write_new_bytes(
        receipt_output,
        (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--eligible-manifest", type=Path, required=True)
    parser.add_argument("--split-output", type=Path, required=True)
    parser.add_argument("--dataset-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = prepare(
            args.database,
            args.source_manifest,
            args.eligible_manifest,
            args.split_output,
            args.dataset_output,
            args.receipt_output,
        )
    except (PreparationFailure, OSError, sqlite3.Error, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED_DISCOVERY_DATASET", "error": str(exc)}))
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
