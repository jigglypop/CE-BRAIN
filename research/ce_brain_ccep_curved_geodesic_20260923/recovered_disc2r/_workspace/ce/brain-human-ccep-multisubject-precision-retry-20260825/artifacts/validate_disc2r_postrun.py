"""Read-only post-run validator for the sealed BA-OBS-DISC2R artifacts.

The frozen pre-D0 test intentionally asserts that no stage has been opened.  It
therefore must not be rewritten or reused as a post-run success test.  This
validator checks the immutable run lock, artifact hash chain, disjoint subject
split, range/endpoint cardinalities, numerical gates, sequential stage gates,
and D3 controls without changing or regenerating any scientific result.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = Path(__file__).resolve().parent
RUN_LOCK_SHA256 = "d70f83387143145bb1c40258c1f1a3974c168c30c677d2f67cc5819ffdccd291"

STAGES: dict[str, dict[str, Any]] = {
    "D0": {
        "participants": 24,
        "sources": 192,
        "targets": 3072,
        "ranges": 1920,
        "endpoint_status": "PASS",
        "result_status": "PASS_SELECTION_ONLY",
    },
    "D1": {
        "participants": 8,
        "sources": 64,
        "targets": 1024,
        "ranges": 640,
        "endpoint_status": "PASS_INTEGRITY",
        "result_status": "PASS_INTERMEDIATE",
    },
    "D2": {
        "participants": 12,
        "sources": 96,
        "targets": 1536,
        "ranges": 960,
        "endpoint_status": "PASS_INTEGRITY",
        "result_status": "PASS_INTERMEDIATE",
    },
    "D3": {
        "participants": 30,
        "sources": 240,
        "targets": 3840,
        "ranges": 2400,
        "endpoint_status": "PASS_INTEGRITY",
        "result_status": "PASS_FINAL",
    },
}


class PostrunValidationError(RuntimeError):
    """Raised when a sealed artifact or preregistered gate does not match."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PostrunValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"MISSING::{path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"NOT_OBJECT::{path.name}")
    return value


def close(first: float, second: float, *, tolerance: float = 1.0e-12) -> bool:
    return math.isclose(float(first), float(second), rel_tol=0.0, abs_tol=tolerance)


def iter_fit_records(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, dict):
        if "numerical_gate" in value and "parameters" in value:
            yield value
        for nested in value.values():
            yield from iter_fit_records(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_fit_records(nested)


def verify_numerical_gates(result: Mapping[str, Any], stage: str) -> int:
    count = 0
    for fit in iter_fit_records(result):
        count += 1
        gate = fit["numerical_gate"]
        parameters = fit["parameters"]
        require(
            int(gate["rank"]) == len(parameters),
            f"NUMERICAL_RANK::{stage}::{fit.get('candidate')}",
        )
        condition = float(gate["condition_number"])
        require(math.isfinite(condition), f"NONFINITE_CONDITION::{stage}")
        require(condition <= 1.0e7, f"CONDITION_STOP::{stage}::{condition}")
        require(
            int(fit.get("admissible_start_count", 0)) >= 3,
            f"MULTISTART_STOP::{stage}::{fit.get('candidate')}",
        )
    require(count > 0, f"NO_NUMERICAL_GATES::{stage}")
    return count


def verify_metric_block(
    block: Mapping[str, Any],
    *,
    stage: str,
    positive_minimum: int,
    permutation_maximum: float,
    lower_bound_required: bool,
) -> bool:
    mean = float(block["mean_improvement"])
    positive = int(block["positive_participants"])
    bootstrap = block["bootstrap"]
    permutation = block["geometry_permutation"]
    lower = float(bootstrap["lower_bound"])
    exceedances = int(permutation["exceedances"])
    replicates = int(permutation["replicates"])
    p_value = float(permutation["p_value"])
    require(
        close(p_value, (1 + exceedances) / (replicates + 1)),
        f"PERMUTATION_P_MISMATCH::{stage}",
    )
    derived = mean > 0.0 and positive >= positive_minimum and p_value <= permutation_maximum
    if lower_bound_required:
        derived = derived and lower > 0.0
    require(
        bool(block["passes_stage_gate"]) is derived,
        f"STAGE_GATE_MISMATCH::{stage}",
    )
    return derived


def validate() -> dict[str, Any]:
    sys.path.insert(0, str(ARTIFACTS))
    import disc2r_ccep_run as retry  # noqa: PLC0415

    _, lock_hash = retry.verify_run_lock()
    require(lock_hash == RUN_LOCK_SHA256, "RUN_LOCK_SHA_MISMATCH")
    audit = retry.base.verify_preimplementation_audit(lock_hash)
    fixture = retry.verify_fixture_receipt()
    require(audit["verdict"] == "PASS", "PREIMPLEMENTATION_AUDIT_NOT_PASS")
    require(fixture["status"] == "PASS", "FIXTURE_NOT_PASS")

    all_subjects: set[str] = set()
    previous_result_path: Path | None = None
    stage_summaries: dict[str, Any] = {}
    numerical_fit_count = 0

    for stage, expected in STAGES.items():
        lower = stage.lower()
        opened_path = ARTIFACTS / f"{lower}-opened.json"
        range_path = ARTIFACTS / f"{lower}-range-receipt.json"
        endpoints_path = ARTIFACTS / f"{lower}-endpoints.json"
        endpoint_receipt_path = ARTIFACTS / f"{lower}-endpoint-receipt.json"
        result_path = ARTIFACTS / f"{lower}-result.json"

        opened = load_json(opened_path)
        range_receipt = load_json(range_path)
        endpoints = load_json(endpoints_path)
        endpoint_receipt = load_json(endpoint_receipt_path)
        result = load_json(result_path)

        for label, artifact in (
            ("OPENED", opened),
            ("RANGE", range_receipt),
            ("ENDPOINTS", endpoints),
            ("ENDPOINT_RECEIPT", endpoint_receipt),
            ("RESULT", result),
        ):
            require(artifact.get("stage") == stage, f"STAGE_MISMATCH::{stage}::{label}")
            require(
                artifact.get("run_lock_sha256") == lock_hash,
                f"LOCK_CHAIN::{stage}::{label}",
            )

        require(opened["status"] == "OPENED_IRREVERSIBLY", f"NOT_OPENED::{stage}")
        require(
            opened["preimplementation_audit_sha256"]
            == sha256(ROOT / "preimplementation-audit-receipt.json"),
            f"AUDIT_CHAIN::{stage}",
        )
        expected_predecessor = None if previous_result_path is None else sha256(previous_result_path)
        require(
            opened["predecessor_result_sha256"] == expected_predecessor,
            f"PREDECESSOR_CHAIN::{stage}",
        )

        require(range_receipt["status"] == "PASS", f"RANGE_STATUS::{stage}")
        require(range_receipt["raw_payload_persisted"] is False, f"RAW_PERSISTED::{stage}")
        ranges = range_receipt["ranges"]
        require(len(ranges) == expected["ranges"], f"RANGE_LENGTH::{stage}")
        require(int(range_receipt["range_count"]) == expected["ranges"], f"RANGE_COUNT::{stage}")
        range_groups: Counter[tuple[str, str]] = Counter()
        cache_keys: set[tuple[Any, ...]] = set()
        for item in ranges:
            require(int(item["http_status"]) == 206, f"HTTP_STATUS::{stage}")
            require(
                int(item["expected_bytes"])
                == int(item["byte_end"]) - int(item["byte_start"]) + 1,
                f"BYTE_GEOMETRY::{stage}",
            )
            require(
                item["content_range"].startswith(
                    f"bytes {item['byte_start']}-{item['byte_end']}/"
                ),
                f"CONTENT_RANGE::{stage}",
            )
            require(len(str(item["payload_sha256"])) == 64, f"PAYLOAD_SHA::{stage}")
            require(str(item["version_id"]) in str(item["locked_url"]), f"VERSION_ID::{stage}")
            key = tuple(item["cache_key"])
            require(key not in cache_keys, f"DUPLICATE_RANGE::{stage}::{key}")
            cache_keys.add(key)
            range_groups[(str(item["subject"]), str(item["source_id"]))] += 1
        require(
            len(range_groups) == expected["sources"]
            and set(range_groups.values()) == {10},
            f"TEN_RANGES_PER_SOURCE::{stage}",
        )

        require(int(endpoints["source_count"]) == expected["sources"], f"SOURCE_COUNT::{stage}")
        sources = endpoints["sources"]
        require(len(sources) == expected["sources"], f"SOURCE_LENGTH::{stage}")
        subjects = {str(source["subject"]) for source in sources}
        require(len(subjects) == expected["participants"], f"PARTICIPANT_COUNT::{stage}")
        require(all_subjects.isdisjoint(subjects), f"PARTICIPANT_LEAKAGE::{stage}")
        all_subjects.update(subjects)
        require(
            sum(len(source["targets"]) for source in sources) == expected["targets"],
            f"TARGET_COUNT::{stage}",
        )
        require(
            all(len(source["targets"]) == 16 for source in sources),
            f"SIXTEEN_TARGETS_PER_SOURCE::{stage}",
        )
        require(
            {
                (str(source["subject"]), str(source["source_id"]))
                for source in sources
            }
            == set(range_groups),
            f"RANGE_ENDPOINT_SOURCE_MISMATCH::{stage}",
        )

        require(
            endpoint_receipt["status"] == expected["endpoint_status"],
            f"ENDPOINT_STATUS::{stage}",
        )
        require(endpoint_receipt["raw_payload_persisted"] is False, f"ENDPOINT_RAW::{stage}")
        require(endpoint_receipt["endpoint_sha256"] == sha256(endpoints_path), f"ENDPOINT_SHA::{stage}")
        require(
            endpoint_receipt["range_receipt_sha256"] == sha256(range_path),
            f"RANGE_RECEIPT_SHA::{stage}",
        )
        apparatus = endpoint_receipt["apparatus"]
        require(int(apparatus["source_count"]) == expected["sources"], f"APPARATUS_SOURCE::{stage}")
        require(int(apparatus["target_count"]) == expected["targets"], f"APPARATUS_TARGET::{stage}")

        require(result["status"] == expected["result_status"], f"RESULT_STATUS::{stage}")
        require(result["winner"] == "SC", f"WINNER::{stage}")
        require(
            result["endpoint_receipt_sha256"] == sha256(endpoint_receipt_path),
            f"RESULT_ENDPOINT_CHAIN::{stage}",
        )
        numerical_fit_count += verify_numerical_gates(result, stage)

        stage_summaries[stage] = {
            "participants": len(subjects),
            "sources": len(sources),
            "targets": sum(len(source["targets"]) for source in sources),
            "ranges": len(ranges),
            "endpoint_sha256": sha256(endpoints_path),
            "result_sha256": sha256(result_path),
            "result_status": result["status"],
        }
        previous_result_path = result_path

    require(len(all_subjects) == 74, "TOTAL_PARTICIPANT_COUNT")

    d0 = load_json(ARTIFACTS / "d0-result.json")
    baseline = float(d0["baseline_cv_mean_loss"])
    for name in d0["survivors"]:
        candidate = d0["candidates"][name]
        derived_improvement = 1.0 - float(candidate["cv_mean_loss"]) / baseline
        require(
            close(candidate["cv_relative_improvement"], derived_improvement),
            f"D0_IMPROVEMENT::{name}",
        )
        require(int(candidate["fold_wins"]) >= 4, f"D0_FOLD_WINS::{name}")
        require(derived_improvement >= 0.005, f"D0_MINIMUM_EFFECT::{name}")
    sc_improvement = float(d0["candidates"]["SC"]["cv_relative_improvement"])
    sac_improvement = float(d0["candidates"]["SAC"]["cv_relative_improvement"])
    require(sac_improvement > sc_improvement, "D0_SAC_NOT_RAW_BEST")
    require(sac_improvement - sc_improvement <= 0.005, "D0_TIE_BAND")
    require(int(d0["candidates"]["SC"]["fold_wins"]) == 6, "D0_SC_FOLD_WINS")

    d1 = load_json(ARTIFACTS / "d1-result.json")["primary"]
    require(
        verify_metric_block(
            d1,
            stage="D1",
            positive_minimum=6,
            permutation_maximum=0.20,
            lower_bound_required=False,
        ),
        "D1_GATE_NOT_PASS",
    )

    d2 = load_json(ARTIFACTS / "d2-result.json")["primary"]
    require(
        verify_metric_block(
            d2,
            stage="D2",
            positive_minimum=8,
            permutation_maximum=0.10,
            lower_bound_required=True,
        ),
        "D2_GATE_NOT_PASS",
    )

    d3_result = load_json(ARTIFACTS / "d3-result.json")
    d3 = d3_result["primary"]
    require(
        verify_metric_block(
            d3,
            stage="D3_PRIMARY",
            positive_minimum=20,
            permutation_maximum=0.025,
            lower_bound_required=True,
        ),
        "D3_PRIMARY_NOT_PASS",
    )
    prestimulus = d3_result["controls"]["prestimulus_negative_control"]
    require(
        not verify_metric_block(
            prestimulus,
            stage="D3_PRESTIMULUS",
            positive_minimum=20,
            permutation_maximum=0.025,
            lower_bound_required=True,
        ),
        "D3_NEGATIVE_CONTROL_FALSE_PASS",
    )
    contact_mean = d3_result["controls"]["contact_mean_diagnostic"]
    require(
        verify_metric_block(
            contact_mean,
            stage="D3_CONTACT_MEAN",
            positive_minimum=20,
            permutation_maximum=0.025,
            lower_bound_required=True,
        ),
        "D3_CONTACT_MEAN_NOT_CONCORDANT",
    )
    require(
        d3_result["reference_classification"] == "REFERENCE_CONCORDANT",
        "REFERENCE_CLASSIFICATION",
    )

    return {
        "schema": "BA-OBS-DISC2R-postrun-validation-v1",
        "status": "PASS",
        "run_lock_sha256": lock_hash,
        "participants_disjoint_total": len(all_subjects),
        "range_count_total": sum(stage["ranges"] for stage in STAGES.values()),
        "raw_payload_persisted": False,
        "numerical_fit_records_verified": numerical_fit_count,
        "stages": stage_summaries,
        "d0": {
            "winner": "SC",
            "sc_cv_relative_improvement": sc_improvement,
            "sc_fold_wins": d0["candidates"]["SC"]["fold_wins"],
        },
        "d3": {
            "status": d3_result["status"],
            "mean_improvement": d3["mean_improvement"],
            "positive_participants": d3["positive_participants"],
            "bootstrap_lower_bound": d3["bootstrap"]["lower_bound"],
            "geometry_permutation_p": d3["geometry_permutation"]["p_value"],
            "prestimulus_passes_stage_gate": prestimulus["passes_stage_gate"],
            "reference_classification": d3_result["reference_classification"],
        },
    }


def main() -> int:
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
