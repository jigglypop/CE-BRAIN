"""Build the endpoint-blind participant/source/receiver split for DISC2."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from collections import defaultdict
from pathlib import Path


EXPECTED_SOURCE_MANIFEST_SHA256 = "9ed8cb9d7a12cf293f8a899aa9a04de7951109b0fad0505e08ebe93f9e11b3c3"
SALT = "BA-OBS-DISC2::ds004080-v1.2.4"
STAGE_QUOTA = {
    "D0": [6, 6, 6, 6],
    "D1": [2, 2, 2, 2],
    "D2": [3, 3, 3, 3],
    "D3": [8, 8, 7, 7],
}
STRATUM_SIZES = [19, 19, 18, 18]
SOURCES_PER_SUBJECT = 8
ANCHORS_PER_SOURCE = 4
EVALUATION_PER_SOURCE = 12
TRIALS_PER_SOURCE = 10


class SplitStop(RuntimeError):
    pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_key(*parts: object) -> bytes:
    return hashlib.sha256("::".join([SALT, *map(str, parts)]).encode("utf-8")).digest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def contiguous_groups(values: list, sizes: list[int]) -> list[list]:
    if sum(sizes) != len(values):
        raise SplitStop(f"group sizes {sizes} do not cover {len(values)} values")
    groups, cursor = [], 0
    for size in sizes:
        groups.append(values[cursor:cursor + size])
        cursor += size
    return groups


def repeatability_partition(trials: list[dict]) -> dict[str, object]:
    if len(trials) < TRIALS_PER_SOURCE:
        raise SplitStop(f"source has only {len(trials)} clean trials")
    selected = sorted(trials, key=lambda row: int(row["event_index"]))[:TRIALS_PER_SOURCE]
    by_orientation: dict[str, list[dict]] = defaultdict(list)
    for trial in selected:
        by_orientation[str(trial["orientation_site"])].append(trial)
    halves = {"A": [], "B": []}
    for orientation_index, (_, group) in enumerate(sorted(by_orientation.items())):
        for local_index, trial in enumerate(group):
            half = "A" if (local_index + orientation_index) % 2 == 0 else "B"
            halves[half].append(trial)
    if len(halves["A"]) != 5 or len(halves["B"]) != 5:
        raise SplitStop(f"polarity-balanced halves are not 5/5: {[len(halves[k]) for k in ('A', 'B')]}")
    for half in halves:
        halves[half].sort(key=lambda row: int(row["event_index"]))
    orientation_groups = {
        orientation: sorted(group, key=lambda row: int(row["event_index"]))
        for orientation, group in sorted(by_orientation.items())
    }
    orientation_count = len(orientation_groups)
    if orientation_count == 1:
        orientation_mode = "single_orientation_temporal_only"
    elif orientation_count == 2 and sorted(len(group) for group in orientation_groups.values()) == [5, 5]:
        orientation_mode = "two_orientation_5_by_5"
    else:
        orientation_mode = "multi_or_unbalanced_orientation"
    return {
        "temporal_repeatability_halves": halves,
        "orientation_mode": orientation_mode,
        "orientation_groups": orientation_groups,
    }


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((float(a[index]) - float(b[index])) ** 2 for index in range(3)))


def receiver_split(subject: str, source: dict, site_map: dict[str, dict]) -> dict[str, object]:
    rows = []
    for site_id in source["receiver_site_ids"]:
        target = site_map.get(site_id)
        if target is None:
            raise SplitStop(f"receiver site absent from catalog: {subject}/{site_id}")
        rows.append({
            "site_id": site_id,
            "site": target["site"],
            "contacts": target["contacts"],
            "center_xyz_mm": target["center_xyz_mm"],
            "distance_mm": distance(source["center_xyz_mm"], target["center_xyz_mm"]),
        })
    rows.sort(key=lambda row: (float(row["distance_mm"]), str(row["site_id"])))
    if len(rows) < ANCHORS_PER_SOURCE + EVALUATION_PER_SOURCE:
        raise SplitStop(f"fewer than 16 receivers: {subject}/{source['site_id']}")
    base, remainder = divmod(len(rows), 4)
    sizes = [base + (1 if index < remainder else 0) for index in range(4)]
    strata = contiguous_groups(rows, sizes)
    if any(len(group) < 4 for group in strata):
        raise SplitStop(f"distance stratum smaller than four: {subject}/{source['site_id']}")
    anchors, evaluation, stratum_summary = [], [], []
    for stratum, group in enumerate(strata):
        ordered = sorted(
            group,
            key=lambda row: digest_key("receiver", subject, source["site_id"], stratum, row["site_id"]),
        )
        anchor = {**ordered[0], "distance_stratum": stratum}
        queries = [{**row, "distance_stratum": stratum} for row in ordered[1:4]]
        anchors.append(anchor)
        evaluation.extend(queries)
        stratum_summary.append({
            "stratum": stratum,
            "available": len(group),
            "min_mm": min(float(row["distance_mm"]) for row in group),
            "max_mm": max(float(row["distance_mm"]) for row in group),
        })
    if len({row["site_id"] for row in anchors + evaluation}) != 16:
        raise SplitStop(f"anchor/evaluation overlap: {subject}/{source['site_id']}")
    return {"anchors": anchors, "evaluation": evaluation, "distance_strata": stratum_summary}


def participant_stages(participants: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    ordered = sorted(participants, key=lambda row: (int(row["age_years"]), str(row["subject"])))
    strata = contiguous_groups(ordered, STRATUM_SIZES)
    assignment_by_subject: dict[str, dict] = {}
    stratum_receipt = []
    for stratum_index, group in enumerate(strata):
        randomized = sorted(group, key=lambda row: digest_key("participant", row["subject"]))
        cursor = 0
        stage_ids = {}
        for stage in ("D0", "D1", "D2", "D3"):
            count = STAGE_QUOTA[stage][stratum_index]
            selected = randomized[cursor:cursor + count]
            cursor += count
            stage_ids[stage] = [row["subject"] for row in selected]
            for stage_rank, row in enumerate(selected):
                if row["subject"] in assignment_by_subject:
                    raise SplitStop(f"participant assigned twice: {row['subject']}")
                assignment_by_subject[row["subject"]] = {
                    "stage": stage,
                    "age_stratum": stratum_index,
                    "stage_stratum_rank": stage_rank,
                    "d0_fold": stage_rank if stage == "D0" else None,
                }
        if cursor != len(group):
            raise SplitStop(f"stratum {stratum_index} has unassigned participants")
        stratum_receipt.append({
            "stratum": stratum_index,
            "count": len(group),
            "age_min": min(int(row["age_years"]) for row in group),
            "age_max": max(int(row["age_years"]) for row in group),
            "stages": stage_ids,
        })
    return assignment_by_subject, stratum_receipt


def build(source_manifest: dict) -> tuple[dict, dict]:
    participants = source_manifest.get("participants", [])
    if len(participants) != 74 or any(not row.get("eligible") for row in participants):
        raise SplitStop("source manifest does not contain 74 eligible participants")
    assignment_by_subject, strata = participant_stages(participants)
    output_subjects = []
    for participant in sorted(participants, key=lambda row: str(row["subject"])):
        subject = str(participant["subject"])
        site_map = {str(row["site_id"]): row for row in participant["site_catalog"]}
        eligible_sources = [row for row in participant["sources"] if int(row["eligible_receiver_count"]) >= 16]
        if len(eligible_sources) < SOURCES_PER_SUBJECT:
            raise SplitStop(f"fewer than eight 16-receiver sources: {subject}")
        selected_sources = sorted(
            eligible_sources,
            key=lambda row: digest_key("source", subject, row["site_id"], row["record_id"]),
        )[:SOURCES_PER_SUBJECT]
        sources = []
        for source in selected_sources:
            split = receiver_split(subject, source, site_map)
            repeatability = repeatability_partition(source["clean_trials"])
            sources.append({
                "site_id": source["site_id"],
                "site": source["site"],
                "contacts": source["contacts"],
                "center_xyz_mm": source["center_xyz_mm"],
                "record_id": source["record_id"],
                "stimulation_type": source["stimulation_type"],
                "current_a": source["current_a"],
                "frequency_hz": source["frequency_hz"],
                "pulsewidth_s": source["pulsewidth_s"],
                **repeatability,
                **split,
            })
        assignment = assignment_by_subject[subject]
        output_subjects.append({
            "subject": subject,
            "age_years": int(participant["age_years"]),
            "sex": participant["sex"],
            **assignment,
            "sources": sources,
        })
    stage_subjects = {
        stage: [row["subject"] for row in output_subjects if row["stage"] == stage]
        for stage in ("D0", "D1", "D2", "D3")
    }
    if {stage: len(rows) for stage, rows in stage_subjects.items()} != {"D0": 24, "D1": 8, "D2": 12, "D3": 30}:
        raise SplitStop("stage participant counts mismatch")
    d0_folds = {
        str(fold): sorted(row["subject"] for row in output_subjects if row["stage"] == "D0" and row["d0_fold"] == fold)
        for fold in range(6)
    }
    if any(len(rows) != 4 for rows in d0_folds.values()):
        raise SplitStop("D0 folds must contain one participant from each age stratum")
    stage_orientation_counts = {
        stage: dict(sorted(defaultdict(int, {
            mode: sum(
                source["orientation_mode"] == mode
                for subject in output_subjects if subject["stage"] == stage
                for source in subject["sources"]
            )
            for mode in {
                source["orientation_mode"]
                for subject in output_subjects if subject["stage"] == stage
                for source in subject["sources"]
            }
        }).items()))
        for stage in ("D0", "D1", "D2", "D3")
    }
    stage_two_orientation_subject_counts = {
        stage: sum(
            any(source["orientation_mode"] == "two_orientation_5_by_5" for source in subject["sources"])
            for subject in output_subjects if subject["stage"] == stage
        )
        for stage in ("D0", "D1", "D2", "D3")
    }
    manifest = {
        "schema": "BA-OBS-DISC2-endpoint-blind-split-v1",
        "status": "PASS_ENDPOINT_UNOPENED",
        "source_manifest_sha256": EXPECTED_SOURCE_MANIFEST_SHA256,
        "salt": SALT,
        "participant_strata": "age-sorted contiguous 19/19/18/18; salted hash within stratum",
        "stage_quota_by_stratum": STAGE_QUOTA,
        "sources_per_subject": SOURCES_PER_SUBJECT,
        "anchors_per_source": ANCHORS_PER_SOURCE,
        "evaluation_receivers_per_source": EVALUATION_PER_SOURCE,
        "trials_per_source": TRIALS_PER_SOURCE,
        "subjects": output_subjects,
        "scientific_endpoint_opened": False,
    }
    stage_hashes = {stage: sha256_bytes(canonical_bytes(rows)) for stage, rows in stage_subjects.items()}
    receipt = {
        "schema": "BA-OBS-DISC2-endpoint-blind-split-receipt-v1",
        "status": "PASS",
        "source_manifest_sha256": EXPECTED_SOURCE_MANIFEST_SHA256,
        "participant_count": len(output_subjects),
        "stage_subject_counts": {stage: len(rows) for stage, rows in stage_subjects.items()},
        "stage_source_counts": {stage: len(rows) * SOURCES_PER_SUBJECT for stage, rows in stage_subjects.items()},
        "stage_evaluation_edge_counts": {
            stage: len(rows) * SOURCES_PER_SUBJECT * EVALUATION_PER_SOURCE for stage, rows in stage_subjects.items()
        },
        "stage_subject_list_sha256": stage_hashes,
        "d0_subject_folds": d0_folds,
        "stage_orientation_source_counts": stage_orientation_counts,
        "stage_two_orientation_subject_counts": stage_two_orientation_subject_counts,
        "age_strata": strata,
        "scientific_endpoint_opened": False,
    }
    return manifest, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    source_bytes = args.source_manifest.read_bytes()
    if sha256_bytes(source_bytes) != EXPECTED_SOURCE_MANIFEST_SHA256:
        raise SplitStop("source manifest hash mismatch")
    manifest, receipt = build(json.loads(source_bytes))
    manifest_hash = dump_atomic(args.manifest, manifest)
    receipt["split_manifest_sha256"] = manifest_hash
    dump_atomic(args.receipt, receipt)
    print(json.dumps({
        "status": receipt["status"],
        "stage_subject_counts": receipt["stage_subject_counts"],
        "stage_source_counts": receipt["stage_source_counts"],
        "scientific_endpoint_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
