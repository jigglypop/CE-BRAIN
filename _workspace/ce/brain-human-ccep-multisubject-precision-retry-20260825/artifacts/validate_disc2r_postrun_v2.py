"""Hardened read-only validation of the sealed BA-OBS-DISC2R full run.

Version 1 checked the artifact hash chain, cardinalities, and reported gates.
This version additionally reconstructs the exact sealed split, raw byte-range
geometry, endpoint target descriptors, fold losses, participant statistics,
bootstrap draws, geometry permutations, and optimizer receipt layout from the
hash-locked predecessor manifests and numerical implementation.

It never writes artifacts and never downloads the raw payload again.  Because
the raw bytes were intentionally not persisted, their recorded payload digests
can be bound to the sealed requests but cannot be recomputed without new I/O.
"""

from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import string
import sys
from typing import Any, Mapping, Sequence

import numpy as np

import validate_disc2r_postrun as v1


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = Path(__file__).resolve().parent
STAGE_ORDER = ("D0", "D1", "D2", "D3")
CANDIDATES = ("S0", "SC", "SAC", "SH0", "SHA0")


def require(condition: bool, message: str) -> None:
    v1.require(bool(condition), message)


def close(first: Any, second: Any, *, tolerance: float = 1.0e-12) -> bool:
    try:
        return math.isclose(
            float(first), float(second), rel_tol=0.0, abs_tol=tolerance
        )
    except (TypeError, ValueError):
        return False


def close_sequence(first: Sequence[Any], second: Sequence[Any]) -> bool:
    return len(first) == len(second) and all(
        close(left, right) for left, right in zip(first, second)
    )


def is_sha256(value: Any) -> bool:
    text = str(value)
    return len(text) == 64 and all(character in string.hexdigits for character in text)


def require_scalar_mapping_close(
    actual: Mapping[str, Any], expected: Mapping[str, Any], label: str
) -> None:
    require(set(actual) == set(expected), f"KEYS::{label}")
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if isinstance(expected_value, float):
            require(close(actual_value, expected_value), f"VALUE::{label}::{key}")
        else:
            require(actual_value == expected_value, f"VALUE::{label}::{key}")


def finite_nested(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(finite_nested(item) for item in value.values())
    if isinstance(value, list):
        return all(finite_nested(item) for item in value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.isfinite(float(value))
    return True


def validate_endpoint_values(endpoint: Mapping[str, Any], label: str) -> None:
    expected_keys = {
        "baseline_sigma_uv",
        "contact_mean_baseline_sigma_uv",
        "contact_mean_energy",
        "contact_mean_pre_energy",
        "contact_mean_pre_z",
        "contact_mean_z",
        "energy",
        "orientation_energy",
        "pre_energy",
        "pre_z",
        "temporal_half_energy",
        "z",
    }
    require(set(endpoint) == expected_keys, f"ENDPOINT_KEYS::{label}")
    require(finite_nested(endpoint), f"ENDPOINT_NONFINITE::{label}")
    require(float(endpoint["baseline_sigma_uv"]) > 0.0, f"BASELINE_SCALE::{label}")
    require(
        float(endpoint["contact_mean_baseline_sigma_uv"]) > 0.0,
        f"CONTACT_BASELINE_SCALE::{label}",
    )
    for energy_key, z_key in (
        ("energy", "z"),
        ("pre_energy", "pre_z"),
        ("contact_mean_energy", "contact_mean_z"),
        ("contact_mean_pre_energy", "contact_mean_pre_z"),
    ):
        energy = endpoint[energy_key]
        z_value = endpoint[z_key]
        require(len(energy) == 5 and len(z_value) == 5, f"FIVE_BINS::{label}::{energy_key}")
        require(all(float(value) >= 0.0 for value in energy), f"NEGATIVE_ENERGY::{label}")
        require(
            all(close(z, math.log(float(e) + 1.0e-6)) for e, z in zip(energy, z_value)),
            f"LOG_ENERGY::{label}::{energy_key}",
        )
    halves = endpoint["temporal_half_energy"]
    require(
        len(halves) == 2
        and all(len(half) == 5 for half in halves)
        and all(float(value) >= 0.0 for half in halves for value in half),
        f"TEMPORAL_HALF_ENERGY::{label}",
    )
    orientation = endpoint["orientation_energy"]
    require(isinstance(orientation, dict), f"ORIENTATION_ENERGY_TYPE::{label}")
    require(
        all(
            len(values) == 5 and all(float(value) >= 0.0 for value in values)
            for values in orientation.values()
        ),
        f"ORIENTATION_ENERGY::{label}",
    )


def fit_parameter_vector(core: Any, fit: Mapping[str, Any], candidate: str) -> np.ndarray:
    spec = core.candidate_spec(candidate)
    parameters = fit["parameters"]
    require(set(parameters) == set(spec.parameter_names), f"PARAMETER_KEYS::{candidate}")
    vector = np.asarray([parameters[name] for name in spec.parameter_names], dtype=np.float64)
    require(np.isfinite(vector).all(), f"PARAMETER_NONFINITE::{candidate}")
    require(np.all(vector >= spec.lower) and np.all(vector <= spec.upper), f"PARAMETER_BOUNDS::{candidate}")
    if candidate in ("SC", "SAC"):
        attenuation = float(parameters["a"])
        require(attenuation > 1.0e-4 and attenuation < 20.0 - 1.0e-5, f"A_BOUNDARY::{candidate}")
    if candidate in ("SH0", "SHA0"):
        attenuation = float(parameters["kappa"])
        require(attenuation > 1.0e-4 and attenuation < 20.0 - 1.0e-5, f"KAPPA_BOUNDARY::{candidate}")
    if candidate in ("SAC", "SHA0"):
        require(
            abs(float(parameters["g_x"])) < 1.0 - 1.0e-5
            and abs(float(parameters["g_y"])) < 1.0 - 1.0e-5,
            f"ANISOTROPY_BOUNDARY::{candidate}",
        )
    return vector


def validate_fit_receipt(
    core: Any,
    fit: Mapping[str, Any],
    *,
    candidate: str,
    training: Sequence[Any],
    expected_offset_count: int,
    label: str,
) -> np.ndarray:
    require(fit["candidate"] == candidate, f"FIT_CANDIDATE::{label}")
    parameters = fit_parameter_vector(core, fit, candidate)
    require(math.isfinite(float(fit["objective"])), f"FIT_OBJECTIVE::{label}")
    recomputed_objective = core.equal_weight_objective(
        training, candidate, parameters
    )
    require(
        close(fit["objective"], recomputed_objective, tolerance=2.0e-11),
        f"FIT_OBJECTIVE_RECOMPUTE::{label}",
    )
    _, recomputed_offsets_list = core.profiled_query_vector(
        training, candidate, parameters
    )
    offsets = tuple(float(value) for value in fit["source_offsets"])
    require(len(offsets) == expected_offset_count, f"SOURCE_OFFSET_COUNT::{label}")
    require(all(math.isfinite(value) for value in offsets), f"SOURCE_OFFSET_NONFINITE::{label}")
    require(
        np.allclose(
            np.asarray(offsets, dtype=np.float64),
            np.asarray(recomputed_offsets_list, dtype=np.float64),
            rtol=0.0,
            atol=2.0e-11,
        ),
        f"SOURCE_OFFSETS_RECOMPUTE::{label}",
    )
    require(
        fit["anchor_profile_sha256"] == core.canonical_sha256(offsets),
        f"ANCHOR_PROFILE_HASH::{label}",
    )

    spec = core.candidate_spec(candidate)
    gate = fit["numerical_gate"]
    singular = np.asarray(gate["singular_values"], dtype=np.float64)
    require(
        singular.shape == parameters.shape
        and np.isfinite(singular).all()
        and np.all(singular > 0.0),
        f"SINGULAR_VALUES::{label}",
    )
    require(int(gate["rank"]) == parameters.size, f"FIT_RANK::{label}")
    require(
        close(gate["condition_number"], singular[0] / singular[-1], tolerance=1.0e-9)
        and float(gate["condition_number"]) <= 1.0e7,
        f"FIT_CONDITION::{label}",
    )
    recomputed_gate = core.numerical_gate(training, candidate, parameters)
    require(int(gate["rank"]) == int(recomputed_gate["rank"]), f"GATE_RANK_RECOMPUTE::{label}")
    require(
        close(
            gate["condition_number"],
            recomputed_gate["condition_number"],
            tolerance=2.0e-8,
        ),
        f"GATE_CONDITION_RECOMPUTE::{label}",
    )
    require(
        np.allclose(
            singular,
            np.asarray(recomputed_gate["singular_values"], dtype=np.float64),
            rtol=0.0,
            atol=2.0e-8,
        ),
        f"GATE_SINGULAR_RECOMPUTE::{label}",
    )
    require(int(fit["admissible_start_count"]) == 3, f"CONFIRMED_START_COUNT::{label}")

    common = core.common_within_source_ols_start(training)
    expected_basin = core.deterministic_starts(candidate, common)
    runs = fit["optimizer_runs"]
    basin = [run for run in runs if run["phase"] == "basin_search"]
    confirmation = [
        run for run in runs if run["phase"] == "best_basin_confirmation"
    ]
    require(len(runs) == len(expected_basin) + 3, f"OPTIMIZER_RUN_COUNT::{label}")
    require(len(basin) == len(expected_basin), f"BASIN_COUNT::{label}")
    require(len(confirmation) == 3, f"CONFIRMATION_COUNT::{label}")
    for index, (run, expected_start) in enumerate(zip(basin, expected_basin)):
        require(int(run["run_index"]) == index, f"BASIN_INDEX::{label}::{index}")
        require(
            np.allclose(
                np.asarray(run["start"], dtype=np.float64),
                expected_start,
                rtol=0.0,
                atol=1.0e-12,
            ),
            f"BASIN_START::{label}::{index}",
        )
        require(run.get("objective") is not None, f"BASIN_OBJECTIVE::{label}::{index}")
        require(math.isfinite(float(run["objective"])), f"BASIN_NONFINITE::{label}::{index}")
        if run.get("admissible") is True:
            require(run.get("success") is True, f"BASIN_SUCCESS::{label}::{index}")
            require("gate_error" not in run, f"BASIN_GATE_ERROR::{label}::{index}")
        else:
            require(
                run.get("success") is not True or "gate_error" in run,
                f"BASIN_UNEXPLAINED_REJECTION::{label}::{index}",
            )
    require(any(run.get("admissible") is True for run in basin), f"NO_ADMISSIBLE_BASIN::{label}")
    confirmation.sort(key=lambda run: int(run["run_index"]))
    require([int(run["run_index"]) for run in confirmation] == [0, 1, 2], f"CONFIRMATION_INDEX::{label}")
    for run in confirmation:
        require(run.get("admissible") is True, f"CONFIRMATION_ADMISSIBLE::{label}")
        require(run.get("success") is True, f"CONFIRMATION_SUCCESS::{label}")
        require(run.get("objective") is not None, f"CONFIRMATION_OBJECTIVE::{label}")
        require(math.isfinite(float(run["objective"])), f"CONFIRMATION_NONFINITE::{label}")
    confirmation_objectives = [float(run["objective"]) for run in confirmation]
    require(
        close(fit["objective"], min(confirmation_objectives), tolerance=2.0e-11),
        f"CONFIRMATION_BEST_OBJECTIVE::{label}",
    )
    denominator = max(1.0, abs(min(confirmation_objectives)))
    require(
        all(
            abs(value - min(confirmation_objectives)) / denominator <= 2.0e-4
            for value in confirmation_objectives
        ),
        f"CONFIRMATION_OBJECTIVE_AGREEMENT::{label}",
    )
    normalized_zero = (
        np.asarray(confirmation[0]["start"], dtype=np.float64) - spec.lower
    ) / (spec.upper - spec.lower)
    direction = np.where(np.arange(parameters.size) % 2 == 0, 1.0, -1.0)
    for run, shift in ((confirmation[1], 1.0e-3), (confirmation[2], -1.0e-3)):
        expected_normalized = np.clip(
            normalized_zero + shift * direction, 2.0e-5, 1.0 - 2.0e-5
        )
        expected_start = spec.lower + expected_normalized * (spec.upper - spec.lower)
        require(
            np.allclose(
                np.asarray(run["start"], dtype=np.float64),
                expected_start,
                rtol=0.0,
                atol=1.0e-12,
            ),
            f"CONFIRMATION_START::{label}::{shift}",
        )
    return parameters


def equal_weight_loss(
    sources: Sequence[Any], losses: Mapping[tuple[str, str], float]
) -> float:
    by_subject: dict[str, list[float]] = {}
    for source in sources:
        by_subject.setdefault(source.subject, []).append(
            float(losses[(source.subject, source.source_id)])
        )
    return float(np.mean([np.mean(values) for values in by_subject.values()]))


def verify_exact_linkage(retry: Any) -> tuple[dict[str, set[str]], int, int]:
    _, split, records = retry.load_and_verify_manifests()
    stage_subjects: dict[str, set[str]] = {}
    exact_source_count = 0
    exact_target_count = 0
    seen_event_records: set[tuple[str, str, int]] = set()

    for stage in STAGE_ORDER:
        split_subject_rows = [row for row in split["subjects"] if row["stage"] == stage]
        expected_subjects = {str(row["subject"]) for row in split_subject_rows}
        require(len(expected_subjects) == v1.STAGES[stage]["participants"], f"SPLIT_SUBJECTS::{stage}")
        require(all(len(row["sources"]) == 8 for row in split_subject_rows), f"EIGHT_SOURCES::{stage}")
        stage_subjects[stage] = expected_subjects

        endpoint_document = v1.load_json(ARTIFACTS / f"{stage.lower()}-endpoints.json")
        endpoint_sources = {
            (str(row["subject"]), str(row["record_id"]), str(row["source_id"])): row
            for row in endpoint_document["sources"]
        }
        require(len(endpoint_sources) == len(endpoint_document["sources"]), f"DUPLICATE_ENDPOINT_SOURCE::{stage}")

        range_document = v1.load_json(ARTIFACTS / f"{stage.lower()}-range-receipt.json")
        actual_ranges = {
            (
                str(row["subject"]),
                str(row["record_id"]),
                str(row["source_id"]),
                int(row["event_index"]),
            ): row
            for row in range_document["ranges"]
        }
        require(len(actual_ranges) == len(range_document["ranges"]), f"DUPLICATE_RANGE_KEY::{stage}")

        expected_source_keys: set[tuple[str, str, str]] = set()
        expected_range_keys: set[tuple[str, str, str, int]] = set()
        for subject_row in split_subject_rows:
            subject = str(subject_row["subject"])
            for source in subject_row["sources"]:
                record_id = str(source["record_id"])
                source_id = str(source["site_id"])
                source_key = (subject, record_id, source_id)
                require(source_key not in expected_source_keys, f"DUPLICATE_SPLIT_SOURCE::{stage}")
                expected_source_keys.add(source_key)
                endpoint_source = endpoint_sources.get(source_key)
                require(endpoint_source is not None, f"ENDPOINT_SOURCE_MISSING::{stage}::{source_key}")
                record = records[record_id]

                require(endpoint_source["stage"] == stage, f"ENDPOINT_STAGE::{source_key}")
                require(endpoint_source["source_site"] == source["site"], f"SOURCE_SITE::{source_key}")
                require(endpoint_source["source_contacts"] == source["contacts"], f"SOURCE_CONTACTS::{source_key}")
                require(
                    close_sequence(endpoint_source["source_center_xyz_mm"], source["center_xyz_mm"]),
                    f"SOURCE_COORDS::{source_key}",
                )
                require(close(endpoint_source["age_years"], subject_row["age_years"]), f"SOURCE_AGE::{source_key}")
                expected_fold = int(subject_row["d0_fold"]) if stage == "D0" else None
                require(endpoint_source["d0_fold"] == expected_fold, f"D0_FOLD::{source_key}")
                require(
                    close(
                        endpoint_source["sampling_frequency_hz"],
                        record["authoritative_sampling_frequency_hz"],
                    ),
                    f"SOURCE_FS::{source_key}",
                )
                require(endpoint_source["orientation_mode"] == source["orientation_mode"], f"ORIENTATION_MODE::{source_key}")

                expected_targets: dict[tuple[str, str], Mapping[str, Any]] = {}
                for role, rows in (("anchor", source["anchors"]), ("query", source["evaluation"])):
                    for target in rows:
                        expected_targets[(role, str(target["site_id"]))] = target
                actual_targets = {
                    (str(target["role"]), str(target["site_id"])): target
                    for target in endpoint_source["targets"]
                }
                require(len(actual_targets) == 16, f"TARGET_DUPLICATE::{source_key}")
                require(set(actual_targets) == set(expected_targets), f"TARGET_SET::{source_key}")
                require(Counter(key[0] for key in actual_targets) == {"anchor": 4, "query": 12}, f"TARGET_ROLES::{source_key}")
                for target_key, expected_target in expected_targets.items():
                    target = actual_targets[target_key]
                    require(target["site"] == expected_target["site"], f"TARGET_SITE::{source_key}::{target_key}")
                    require(target["contacts"] == expected_target["contacts"], f"TARGET_CONTACTS::{source_key}::{target_key}")
                    require(
                        close_sequence(target["center_xyz_mm"], expected_target["center_xyz_mm"]),
                        f"TARGET_COORDS::{source_key}::{target_key}",
                    )
                    require(close(target["distance_mm"], expected_target["distance_mm"]), f"TARGET_DISTANCE::{source_key}::{target_key}")
                    require(int(target["distance_stratum"]) == int(expected_target["distance_stratum"]), f"TARGET_STRATUM::{source_key}::{target_key}")
                    expected_delta = [
                        (float(value) - float(origin)) / 50.0
                        for value, origin in zip(
                            expected_target["center_xyz_mm"], source["center_xyz_mm"]
                        )
                    ]
                    require(
                        close_sequence(target["delta_over_50mm"], expected_delta),
                        f"TARGET_DELTA::{source_key}::{target_key}",
                    )
                    validate_endpoint_values(target["endpoint"], f"{stage}::{source_key}::{target_key}")
                    exact_target_count += 1

                ordered_trials, _, _ = retry.ordered_trials(source, record)
                require(len(ordered_trials) == 10, f"ORDERED_TRIAL_COUNT::{source_key}")
                fs = int(round(float(record["authoritative_sampling_frequency_hz"])))
                require(close(fs, record["authoritative_sampling_frequency_hz"]), f"INTEGER_FS::{record_id}")
                channel_count = int(record["header"]["number_of_channels"])
                content_length = int(record["source"]["content_length"])
                for trial in ordered_trials:
                    event_index = int(trial["event_index"])
                    range_key = (subject, record_id, source_id, event_index)
                    require(range_key not in expected_range_keys, f"DUPLICATE_EXPECTED_RANGE::{range_key}")
                    expected_range_keys.add(range_key)
                    receipt = actual_ranges.get(range_key)
                    require(receipt is not None, f"RANGE_MISSING::{range_key}")
                    event_record_key = (subject, record_id, event_index)
                    require(event_record_key not in seen_event_records, f"EVENT_REUSED::{event_record_key}")
                    seen_event_records.add(event_record_key)
                    anchor = int(trial["anchor_sample_zero_based"])
                    first = anchor - fs
                    last = anchor + math.floor(0.120 * fs)
                    byte_start = first * channel_count * 4
                    byte_end = (last + 1) * channel_count * 4 - 1
                    expected_bytes = (last - first + 1) * channel_count * 4
                    require(first >= 0 and last < int(record["sample_count"]), f"SAMPLE_BOUNDS::{range_key}")
                    require(int(receipt["anchor_sample_zero_based"]) == anchor, f"ANCHOR::{range_key}")
                    require(int(receipt["byte_start"]) == byte_start, f"BYTE_START::{range_key}")
                    require(int(receipt["byte_end"]) == byte_end, f"BYTE_END::{range_key}")
                    require(int(receipt["expected_bytes"]) == expected_bytes, f"EXPECTED_BYTES::{range_key}")
                    require(receipt["content_range"] == f"bytes {byte_start}-{byte_end}/{content_length}", f"CONTENT_RANGE_EXACT::{range_key}")
                    require(receipt["etag"] == record["source"]["etag"], f"ETAG::{range_key}")
                    require(receipt["version_id"] == record["source"]["version_id"], f"VERSION::{range_key}")
                    require(receipt["locked_url"] == record["source"]["locked_url"], f"LOCKED_URL::{range_key}")
                    require(receipt["cache_key"] == [stage, subject, record_id, event_index], f"CACHE_KEY::{range_key}")
                    require(int(receipt["http_status"]) == 206, f"HTTP_206::{range_key}")
                    require(is_sha256(receipt["payload_sha256"]), f"PAYLOAD_HASH::{range_key}")
                exact_source_count += 1
        require(set(endpoint_sources) == expected_source_keys, f"EXTRA_ENDPOINT_SOURCE::{stage}")
        require(set(actual_ranges) == expected_range_keys, f"EXTRA_RANGE::{stage}")
    return stage_subjects, exact_source_count, exact_target_count


def verify_d0(core: Any, base: Any, split: Mapping[str, Any]) -> int:
    result = v1.load_json(ARTIFACTS / "d0-result.json")
    require(set(result["candidates"]) == set(CANDIDATES), "D0_CANDIDATE_SET")
    require(result["status"] == "PASS_SELECTION_ONLY", "D0_STATUS")
    sources = base.endpoint_sources(ARTIFACTS / "d0-endpoints.json", "z")
    fold_map = {
        str(row["subject"]): int(row["d0_fold"])
        for row in split["subjects"]
        if row["stage"] == "D0"
    }
    require(set(fold_map.values()) == set(range(6)), "D0_FOLD_SET")
    recomputed_losses: dict[str, list[float]] = {name: [] for name in CANDIDATES}
    fold_wins: dict[str, int] = {name: 0 for name in CANDIDATES if name != "S0"}
    fit_count = 0
    for fold in range(6):
        training = [source for source in sources if fold_map[source.subject] != fold]
        testing = [source for source in sources if fold_map[source.subject] == fold]
        require(len(training) == 160 and len(testing) == 32, f"D0_FOLD_SOURCE_COUNTS::{fold}")
        require(len({source.subject for source in testing}) == 4, f"D0_FOLD_SUBJECTS::{fold}")
        fold_rows = {
            name: result["candidates"][name]["folds"][fold] for name in CANDIDATES
        }
        for name, row in fold_rows.items():
            require(int(row["fold"]) == fold and row["status"] == "PASS", f"D0_FOLD_ROW::{name}::{fold}")
            parameters = validate_fit_receipt(
                core,
                row["fit"],
                candidate=name,
                training=training,
                expected_offset_count=160,
                label=f"D0::{name}::{fold}",
            )
            fit_count += 1
            losses = core.source_losses(testing, name, parameters)
            test_loss = equal_weight_loss(testing, losses)
            require(close(row["test_loss"], test_loss, tolerance=2.0e-11), f"D0_TEST_LOSS::{name}::{fold}")
            recomputed_losses[name].append(test_loss)
        baseline_loss = recomputed_losses["S0"][-1]
        for name in CANDIDATES[1:]:
            row = fold_rows[name]
            improvement = 1.0 - recomputed_losses[name][-1] / baseline_loss
            beats = recomputed_losses[name][-1] < baseline_loss
            require(close(row["relative_improvement"], improvement), f"D0_FOLD_IMPROVEMENT::{name}::{fold}")
            require(bool(row["beats_s0"]) is beats, f"D0_BEATS_S0::{name}::{fold}")
            fold_wins[name] += int(beats)

    baseline_mean = float(np.mean(recomputed_losses["S0"]))
    require(close(result["baseline_cv_mean_loss"], baseline_mean), "D0_BASELINE_MEAN")
    survivors: list[tuple[str, float, int]] = []
    for name in CANDIDATES:
        entry = result["candidates"][name]
        require(entry["admissible"] is True, f"D0_ADMISSIBLE::{name}")
        if name == "S0":
            continue
        mean_loss = float(np.mean(recomputed_losses[name]))
        improvement = 1.0 - mean_loss / baseline_mean
        survives = improvement >= 0.005 and fold_wins[name] >= 4
        require(close(entry["cv_mean_loss"], mean_loss), f"D0_CV_LOSS::{name}")
        require(close(entry["cv_relative_improvement"], improvement), f"D0_CV_IMPROVEMENT::{name}")
        require(int(entry["fold_wins"]) == fold_wins[name], f"D0_FOLD_WINS::{name}")
        require(bool(entry["survives"]) is survives, f"D0_SURVIVES::{name}")
        if survives:
            survivors.append((name, improvement, 1 if name in ("SC", "SH0") else 3))
    survivors.sort(key=lambda row: (-row[1], row[2], row[0]))
    require(result["survivors"] == [row[0] for row in survivors], "D0_SURVIVOR_ORDER")
    best = survivors[0][1]
    tied = [row for row in survivors if best - row[1] <= 0.005]
    tied.sort(key=lambda row: (row[2], row[0]))
    require(result["winner"] == tied[0][0] == "SC", "D0_TIE_BREAK")
    return fit_count


def prior_sources(base: Any, stage: str, endpoint_field: str) -> list[Any]:
    index = STAGE_ORDER.index(stage)
    result: list[Any] = []
    for prior in STAGE_ORDER[:index]:
        result.extend(
            base.endpoint_sources(
                ARTIFACTS / f"{prior.lower()}-endpoints.json", endpoint_field
            )
        )
    return result


def compare_bootstrap(actual: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    require_scalar_mapping_close(actual, expected, f"BOOTSTRAP::{label}")


def compare_permutation(actual: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    require_scalar_mapping_close(actual, expected, f"PERMUTATION::{label}")


def verify_metric_block_v2(
    core: Any,
    base: Any,
    block: Mapping[str, Any],
    *,
    stage: str,
    endpoint_field: str,
    endpoint_label: str,
    expected_subjects: set[str],
    contract_hash: str,
) -> int:
    require(block["endpoint_label"] == endpoint_label, f"ENDPOINT_LABEL::{stage}::{endpoint_label}")
    training = prior_sources(base, stage, endpoint_field)
    testing = base.endpoint_sources(
        ARTIFACTS / f"{stage.lower()}-endpoints.json", endpoint_field
    )
    require({source.subject for source in testing} == expected_subjects, f"METRIC_SUBJECT_SET::{stage}::{endpoint_label}")
    require(len(training) == {"D1": 192, "D2": 256, "D3": 352}[stage], f"TRAINING_SOURCE_COUNT::{stage}")
    baseline_parameters = validate_fit_receipt(
        core,
        block["baseline_fit"],
        candidate="S0",
        training=training,
        expected_offset_count=len(training),
        label=f"{stage}::{endpoint_label}::S0",
    )
    winner_parameters = validate_fit_receipt(
        core,
        block["winner_fit"],
        candidate="SC",
        training=training,
        expected_offset_count=len(training),
        label=f"{stage}::{endpoint_label}::SC",
    )
    participant, source_values = core.participant_improvements(
        testing, baseline_parameters, "SC", winner_parameters
    )
    require_scalar_mapping_close(
        block["participant_improvements"], participant, f"PARTICIPANT::{stage}::{endpoint_label}"
    )
    expected_source_values = {
        f"{key[0]}::{key[1]}": value for key, value in source_values.items()
    }
    require_scalar_mapping_close(
        block["source_improvements"], expected_source_values, f"SOURCE::{stage}::{endpoint_label}"
    )
    mean = float(np.mean(list(participant.values())))
    positive = int(sum(value > 0.0 for value in participant.values()))
    require(close(block["mean_improvement"], mean), f"MEAN::{stage}::{endpoint_label}")
    require(int(block["positive_participants"]) == positive, f"POSITIVE::{stage}::{endpoint_label}")

    quantile = {"D1": 0.20, "D2": 0.20, "D3": 0.025}[stage]
    bootstrap = core.participant_bootstrap(
        participant,
        replicates=8192,
        seed_material=(
            f"BA-OBS-DISC2::participant-bootstrap::{contract_hash}::"
            f"{stage}::{endpoint_label}"
        ),
        lower_quantile=quantile,
    )
    compare_bootstrap(block["bootstrap"], bootstrap, f"{stage}::{endpoint_label}")
    replicate_count = {"D1": 511, "D2": 1023, "D3": 4095}[stage]
    permutation = base.geometry_permutation_test(
        testing,
        baseline_parameters,
        "SC",
        winner_parameters,
        stage=f"{stage}::{endpoint_label}",
        contract_hash=contract_hash,
        replicates=replicate_count,
    )
    compare_permutation(
        block["geometry_permutation"], permutation, f"{stage}::{endpoint_label}"
    )

    if stage == "D1":
        expected_gate = mean > 0.0 and positive >= 6 and permutation["p_value"] <= 0.20
    elif stage == "D2":
        expected_gate = bootstrap["lower_bound"] > 0.0 and positive >= 8 and permutation["p_value"] <= 0.10
    else:
        expected_gate = bootstrap["lower_bound"] > 0.0 and positive >= 20 and permutation["p_value"] <= 0.025
    require(bool(block["passes_stage_gate"]) is expected_gate, f"RECOMPUTED_GATE::{stage}::{endpoint_label}")
    return 2


def verify_later_stages(
    core: Any,
    base: Any,
    stage_subjects: Mapping[str, set[str]],
    contract_hash: str,
) -> tuple[int, int]:
    fit_count = 0
    block_count = 0
    for stage in ("D1", "D2"):
        result = v1.load_json(ARTIFACTS / f"{stage.lower()}-result.json")
        require(result["winner"] == "SC", f"LATER_WINNER::{stage}")
        require(result["controls"] == {}, f"EARLY_CONTROLS::{stage}")
        require(result["reference_classification"] is None, f"EARLY_REFERENCE::{stage}")
        fit_count += verify_metric_block_v2(
            core,
            base,
            result["primary"],
            stage=stage,
            endpoint_field="z",
            endpoint_label="bipolar_poststimulus",
            expected_subjects=stage_subjects[stage],
            contract_hash=contract_hash,
        )
        block_count += 1
        require(result["status"] == "PASS_INTERMEDIATE", f"LATER_STATUS::{stage}")

    d3 = v1.load_json(ARTIFACTS / "d3-result.json")
    require(set(d3["controls"]) == {"prestimulus_negative_control", "contact_mean_diagnostic"}, "D3_CONTROL_SET")
    fit_count += verify_metric_block_v2(
        core,
        base,
        d3["primary"],
        stage="D3",
        endpoint_field="z",
        endpoint_label="bipolar_poststimulus",
        expected_subjects=stage_subjects["D3"],
        contract_hash=contract_hash,
    )
    fit_count += verify_metric_block_v2(
        core,
        base,
        d3["controls"]["prestimulus_negative_control"],
        stage="D3",
        endpoint_field="pre_z",
        endpoint_label="bipolar_prestimulus_negative_control",
        expected_subjects=stage_subjects["D3"],
        contract_hash=contract_hash,
    )
    fit_count += verify_metric_block_v2(
        core,
        base,
        d3["controls"]["contact_mean_diagnostic"],
        stage="D3",
        endpoint_field="contact_mean_z",
        endpoint_label="contact_mean_poststimulus_diagnostic",
        expected_subjects=stage_subjects["D3"],
        contract_hash=contract_hash,
    )
    block_count += 3
    primary_pass = bool(d3["primary"]["passes_stage_gate"])
    pre_pass = bool(
        d3["controls"]["prestimulus_negative_control"]["passes_stage_gate"]
    )
    contact_pass = bool(d3["controls"]["contact_mean_diagnostic"]["passes_stage_gate"])
    expected_status = (
        "NEGATIVE_CONTROL_FAIL / NOT_CONFIRMED"
        if primary_pass and pre_pass
        else "PASS_FINAL"
        if primary_pass
        else "NOT_CONFIRMED"
    )
    expected_reference = (
        "REFERENCE_CONCORDANT" if contact_pass else "REFERENCE_SENSITIVE"
    ) if primary_pass else None
    require(d3["status"] == expected_status == "PASS_FINAL", "D3_DERIVED_STATUS")
    require(
        d3["reference_classification"]
        == expected_reference
        == "REFERENCE_CONCORDANT",
        "D3_DERIVED_REFERENCE",
    )
    require(primary_pass and not pre_pass and contact_pass, "D3_CONTROL_LOGIC")
    return fit_count, block_count


def validate() -> dict[str, Any]:
    version_one = v1.validate()
    sys.path.insert(0, str(ARTIFACTS))
    import disc2r_ccep_run as retry  # noqa: PLC0415
    import disc2_ccep_core as core  # noqa: PLC0415

    _, split, _ = retry.load_and_verify_manifests()
    stage_subjects, source_count, target_count = verify_exact_linkage(retry)
    d0_fit_count = verify_d0(core, retry.base, split)
    contract_hash = v1.sha256(ROOT / "00-contract.md")
    later_fit_count, metric_block_count = verify_later_stages(
        core, retry.base, stage_subjects, contract_hash
    )
    require(d0_fit_count + later_fit_count == 40, "TOTAL_FIT_LAYOUT")
    require(source_count == 592 and target_count == 9472, "TOTAL_EXACT_LINKAGE")

    return {
        "schema": "BA-OBS-DISC2R-postrun-validation-v2",
        "status": "PASS",
        "run_lock_sha256": version_one["run_lock_sha256"],
        "v1_base_status": version_one["status"],
        "manifest_bound_sources": source_count,
        "manifest_bound_targets": target_count,
        "manifest_bound_ranges": version_one["range_count_total"],
        "disjoint_participants": sum(len(values) for values in stage_subjects.values()),
        "d0_fold_losses_recomputed": 30,
        "fit_receipts_structurally_verified": d0_fit_count + later_fit_count,
        "deterministic_bootstrap_permutation_blocks_recomputed": metric_block_count,
        "d3_status": "PASS_FINAL",
        "d3_negative_control_pass": False,
        "payload_digest_limit": (
            "Recorded SHA-256 values are format- and request-bound; raw payloads "
            "were not persisted, so content digests require new download I/O to recompute."
        ),
    }


def main() -> int:
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
