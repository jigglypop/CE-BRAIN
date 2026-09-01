from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import platform
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.io import loadmat


EXPECTED_ARCHIVE_BYTES = 483_324_456
EXPECTED_ARCHIVE_SHA256 = (
    "b9962e7760ac7299cc968fa4a23d2c965342d78abdded4f937a4081588f09ba3"
)
EXPECTED_PYTHON_EXECUTABLE = Path(
    r"C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe"
)
EXPECTED_PYTHON_VERSION = "3.11.9"
EXPECTED_NUMPY_VERSION = "2.4.6"
EXPECTED_SCIPY_VERSION = "1.17.1"

BASE = "Figure1/NDNFActivationExperiments/Relearning"
CONDITIONS = ("Control", "Opto")
MOUSE_IDS = (
    "NWO1",
    "NWO3",
    "NWO4",
    "NWO5",
    "NWO6",
    "NWO9",
    "NWO10",
    "NWO11",
    "NWO12",
    "NWO13",
)
TRANSITIONS = {
    "A_to_B": {"session_index": 1, "old_rule": 0, "new_rule": 2},
    "B_to_Aprime": {"session_index": 3, "old_rule": 2, "new_rule": 0},
}
WINDOW_TRIALS = 20
ALPHA = 0.05
LOCK_ROLES = {
    "analysis_contract",
    "analysis_runner",
    "regression_tests",
    "provider_archive",
    "python_runtime",
    "numpy_runtime",
    "scipy_runtime",
}


class SourceError(RuntimeError):
    pass


class SchemaError(RuntimeError):
    pass


class QualityError(RuntimeError):
    pass


class ExecutionLockError(RuntimeError):
    pass


@dataclass(frozen=True)
class Stratum:
    mouse: str
    condition: str
    transition: str
    old_rule: int
    new_rule: int
    relearn: np.ndarray
    trial_side: np.ndarray
    outcome: np.ndarray
    dir_out: np.ndarray
    switch_index: int
    primary_eligible: np.ndarray
    sensitivity_eligible: np.ndarray


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").casefold()


def integer_vector(value: Any, label: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim == 2 and 1 in array.shape:
        array = array.reshape(-1)
    if array.ndim != 1 or array.size == 0:
        raise SchemaError(f"{label} must be a nonempty vector, got {array.shape}")
    if not np.issubdtype(array.dtype, np.number):
        raise SchemaError(f"{label} must be numeric")
    numeric = np.asarray(array, dtype=float)
    if not np.all(np.isfinite(numeric)):
        raise SchemaError(f"{label} contains non-finite values")
    rounded = np.rint(numeric)
    if not np.array_equal(numeric, rounded):
        raise SchemaError(f"{label} contains non-integer codes")
    return rounded.astype(np.int64)


def coded_first_column(value: Any, label: str) -> tuple[np.ndarray, int]:
    array = np.asarray(value)
    if array.ndim != 2 or array.shape[1] < 2 or array.shape[0] == 0:
        raise SchemaError(f"{label} must be an n-by-at-least-2 matrix, got {array.shape}")
    return integer_vector(array[:, 0], f"{label}[:,0]"), int(array.shape[0])


def terminal_new_run_start(
    relearn: np.ndarray, old_rule: int, new_rule: int
) -> int:
    observed = set(int(value) for value in relearn.tolist())
    expected = {old_rule, new_rule}
    if observed != expected:
        raise SchemaError(f"Relearn codes {sorted(observed)} != {sorted(expected)}")
    non_new = np.flatnonzero(relearn != new_rule)
    if non_new.size == 0 or int(non_new[-1]) >= relearn.size - 1:
        raise SchemaError("no nonempty terminal new-rule run")
    start = int(non_new[-1]) + 1
    if not np.all(relearn[start:] == new_rule):
        raise SchemaError("terminal new-rule run is not stable")
    if not np.any(relearn[:start] == old_rule):
        raise SchemaError("old rule is absent before the terminal new-rule run")
    return start


def validate_session(
    session: Any,
    *,
    mouse: str,
    condition: str,
    transition: str,
    old_rule: int,
    new_rule: int,
) -> Stratum:
    label = f"{mouse}/{condition}/{transition}"
    if not isinstance(session, dict):
        raise SchemaError(f"{label}: session is not a structure")
    required = {"Relearn", "TrialTypes", "Outcomes", "DirOut"}
    missing = sorted(required - set(session))
    if missing:
        raise SchemaError(f"{label}: missing fields {missing}")

    relearn = integer_vector(session["Relearn"], f"{label}/Relearn")
    trial_side, n_trial_types = coded_first_column(
        session["TrialTypes"], f"{label}/TrialTypes"
    )
    outcome, n_outcomes = coded_first_column(
        session["Outcomes"], f"{label}/Outcomes"
    )
    dir_out = integer_vector(session["DirOut"], f"{label}/DirOut")
    lengths = {relearn.size, n_trial_types, n_outcomes, dir_out.size}
    if len(lengths) != 1:
        raise SchemaError(f"{label}: row lengths differ {sorted(lengths)}")
    if not set(trial_side.tolist()) <= {0, 1}:
        raise SchemaError(f"{label}: TrialTypes[:,0] contains codes outside 0/1")
    if not set(outcome.tolist()) <= {-1, 0, 1, 3}:
        raise SchemaError(f"{label}: Outcomes[:,0] has an unknown code")
    if not set(dir_out.tolist()) <= {0, 1, 3}:
        raise SchemaError(f"{label}: DirOut has an unknown code")

    switch_index = terminal_new_run_start(relearn, old_rule, new_rule)
    row_index = np.arange(relearn.size, dtype=np.int64)
    post_right = row_index[(row_index >= switch_index) & (trial_side == 0)]
    primary = post_right[np.isin(outcome[post_right], (0, 1))]
    sensitivity = post_right[outcome[post_right] != -1]
    if primary.size < WINDOW_TRIALS:
        raise QualityError(
            f"{label}: {primary.size} primary eligible trials < {WINDOW_TRIALS}"
        )
    if sensitivity.size < WINDOW_TRIALS:
        raise QualityError(
            f"{label}: {sensitivity.size} sensitivity eligible trials < "
            f"{WINDOW_TRIALS}"
        )
    return Stratum(
        mouse=mouse,
        condition=condition,
        transition=transition,
        old_rule=old_rule,
        new_rule=new_rule,
        relearn=relearn,
        trial_side=trial_side,
        outcome=outcome,
        dir_out=dir_out,
        switch_index=switch_index,
        primary_eligible=primary,
        sensitivity_eligible=sensitivity,
    )


def expected_member(condition: str, mouse: str) -> str:
    return f"{BASE}/{condition}/{mouse}.mat"


def verify_archive(path: Path) -> tuple[zipfile.ZipFile, dict[str, Any]]:
    if not path.is_file():
        raise SourceError(f"archive not found: {path}")
    size = path.stat().st_size
    if size != EXPECTED_ARCHIVE_BYTES:
        raise SourceError(f"archive bytes {size} != {EXPECTED_ARCHIVE_BYTES}")
    digest = sha256_file(path)
    if digest != EXPECTED_ARCHIVE_SHA256:
        raise SourceError(f"archive SHA-256 {digest} != {EXPECTED_ARCHIVE_SHA256}")
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise SourceError(f"invalid ZIP: {exc}") from exc
    try:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise SourceError("ZIP contains duplicate member names")
        bad_member = archive.testzip()
        if bad_member is not None:
            raise SourceError(f"ZIP CRC failed at {bad_member}")
        for condition in CONDITIONS:
            prefix = f"{BASE}/{condition}/"
            actual = {
                name
                for name in names
                if name.startswith(prefix)
                and name.endswith(".mat")
                and "/" not in name[len(prefix) :]
            }
            expected = {expected_member(condition, mouse) for mouse in MOUSE_IDS}
            if actual != expected:
                raise SourceError(
                    f"{condition} member set differs: "
                    f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
                )
    except Exception:
        archive.close()
        raise
    return archive, {
        "path": str(path.resolve()),
        "bytes": size,
        "sha256": digest,
        "zip_member_count": len(names),
        "zip_crc": "PASS",
        "paired_mouse_count": len(MOUSE_IDS),
    }


def normalize_sessions(value: Any, label: str) -> list[Any]:
    if isinstance(value, list):
        sessions = value
    elif isinstance(value, np.ndarray) and value.dtype == object:
        sessions = list(value.reshape(-1))
    else:
        raise SchemaError(f"{label}: cont_data is not a session sequence")
    if len(sessions) != 5:
        raise SchemaError(f"{label}: cont_data has {len(sessions)} sessions, not 5")
    return sessions


def load_and_gate(archive: zipfile.ZipFile) -> list[Stratum]:
    strata: list[Stratum] = []
    for condition in CONDITIONS:
        for mouse in MOUSE_IDS:
            member = expected_member(condition, mouse)
            try:
                payload = archive.read(member)
                loaded = loadmat(io.BytesIO(payload), simplify_cells=True)
            except Exception as exc:
                raise SchemaError(f"cannot load {member}: {exc}") from exc
            if "cont_data" not in loaded:
                raise SchemaError(f"{member}: cont_data is absent")
            sessions = normalize_sessions(loaded["cont_data"], member)
            for transition, specification in TRANSITIONS.items():
                session_index = int(specification["session_index"])
                strata.append(
                    validate_session(
                        sessions[session_index],
                        mouse=mouse,
                        condition=condition,
                        transition=transition,
                        old_rule=int(specification["old_rule"]),
                        new_rule=int(specification["new_rule"]),
                    )
                )
    expected_count = len(CONDITIONS) * len(MOUSE_IDS) * len(TRANSITIONS)
    if len(strata) != expected_count:
        raise SchemaError(f"stratum count {len(strata)} != {expected_count}")
    return strata


def crosstab_key(outcome: int, dir_out: int) -> str:
    return f"outcome={outcome}|dirout={dir_out}"


def stratum_result(stratum: Stratum) -> dict[str, Any]:
    primary_rows = stratum.primary_eligible[:WINDOW_TRIALS]
    sensitivity_rows = stratum.sensitivity_eligible[:WINDOW_TRIALS]
    primary_error_count = int(np.sum(1 - stratum.outcome[primary_rows]))
    sensitivity_error_count = int(
        np.sum(stratum.outcome[sensitivity_rows] != 1)
    )
    row_index = np.arange(stratum.outcome.size, dtype=np.int64)
    post_right = row_index[
        (row_index >= stratum.switch_index) & (stratum.trial_side == 0)
    ]
    post_counts = Counter(int(value) for value in stratum.outcome[post_right])
    cross = Counter(
        crosstab_key(int(outcome), int(direction))
        for outcome, direction in zip(stratum.outcome, stratum.dir_out, strict=True)
    )
    valid = np.isin(stratum.outcome, (0, 1))
    mismatch = int(np.sum(valid & (stratum.dir_out != stratum.outcome)))
    return {
        "mouse": stratum.mouse,
        "condition": stratum.condition,
        "transition": stratum.transition,
        "session_trial_count": int(stratum.outcome.size),
        "switch_row_1based_inclusive": stratum.switch_index + 1,
        "post_switch_right_trial_count": int(post_right.size),
        "post_switch_right_outcome_counts": {
            str(code): int(post_counts.get(code, 0)) for code in (-1, 0, 1, 3)
        },
        "post_switch_right_omission_rate": float(
            post_counts.get(3, 0) / post_right.size
        ),
        "post_switch_right_impulsive_rate": float(
            post_counts.get(-1, 0) / post_right.size
        ),
        "primary_eligible_count": int(stratum.primary_eligible.size),
        "primary_window_rows_1based": (primary_rows + 1).tolist(),
        "primary_error_count": primary_error_count,
        "primary_error_rate": primary_error_count / WINDOW_TRIALS,
        "sensitivity_eligible_count": int(stratum.sensitivity_eligible.size),
        "sensitivity_window_rows_1based": (sensitivity_rows + 1).tolist(),
        "sensitivity_error_count": sensitivity_error_count,
        "sensitivity_error_rate": sensitivity_error_count / WINDOW_TRIALS,
        "outcomes_dirout_crosstab_all_session_trials": dict(sorted(cross.items())),
        "valid_outcome_dirout_mismatch_count": mismatch,
    }


def exact_one_sided_signflip(values: list[int]) -> dict[str, Any]:
    if not values:
        raise ValueError("at least one paired value is required")
    observed_sum = int(sum(values))
    tail = 0
    total = 2 ** len(values)
    for signs in itertools.product((-1, 1), repeat=len(values)):
        permuted_sum = sum(sign * value for sign, value in zip(signs, values))
        if permuted_sum >= observed_sum:
            tail += 1
    return {
        "alternative": "mean_interaction_greater_than_zero",
        "observed_sum_error_counts": observed_sum,
        "tail_assignments": tail,
        "total_assignments": total,
        "p_exact_one_sided": tail / total,
    }


def compute_endpoints(strata: list[Stratum]) -> dict[str, Any]:
    results = [stratum_result(stratum) for stratum in strata]
    by_key = {
        (item["mouse"], item["condition"], item["transition"]): item
        for item in results
    }
    mouse_results: list[dict[str, Any]] = []
    primary_interactions: list[int] = []
    sensitivity_interactions: list[int] = []
    primary_d_ab: list[int] = []
    primary_d_ba: list[int] = []
    for mouse in MOUSE_IDS:
        primary_d: dict[str, int] = {}
        sensitivity_d: dict[str, int] = {}
        for transition in TRANSITIONS:
            control = by_key[(mouse, "Control", transition)]
            opto = by_key[(mouse, "Opto", transition)]
            primary_d[transition] = int(
                opto["primary_error_count"] - control["primary_error_count"]
            )
            sensitivity_d[transition] = int(
                opto["sensitivity_error_count"]
                - control["sensitivity_error_count"]
            )
        primary_interaction = primary_d["B_to_Aprime"] - primary_d["A_to_B"]
        sensitivity_interaction = (
            sensitivity_d["B_to_Aprime"] - sensitivity_d["A_to_B"]
        )
        primary_interactions.append(primary_interaction)
        sensitivity_interactions.append(sensitivity_interaction)
        primary_d_ab.append(primary_d["A_to_B"])
        primary_d_ba.append(primary_d["B_to_Aprime"])
        mouse_results.append(
            {
                "mouse": mouse,
                "primary_opto_minus_control_error_counts": primary_d,
                "primary_opto_minus_control_error_rates": {
                    key: value / WINDOW_TRIALS for key, value in primary_d.items()
                },
                "primary_complexity_interaction_error_count": primary_interaction,
                "primary_complexity_interaction_error_rate": (
                    primary_interaction / WINDOW_TRIALS
                ),
                "sensitivity_opto_minus_control_error_counts": sensitivity_d,
                "sensitivity_opto_minus_control_error_rates": {
                    key: value / WINDOW_TRIALS
                    for key, value in sensitivity_d.items()
                },
                "sensitivity_complexity_interaction_error_count": (
                    sensitivity_interaction
                ),
                "sensitivity_complexity_interaction_error_rate": (
                    sensitivity_interaction / WINDOW_TRIALS
                ),
            }
        )

    signflip = exact_one_sided_signflip(primary_interactions)
    mean_primary_interaction = sum(primary_interactions) / (
        len(MOUSE_IDS) * WINDOW_TRIALS
    )
    mean_sensitivity_interaction = sum(sensitivity_interactions) / (
        len(MOUSE_IDS) * WINDOW_TRIALS
    )
    mean_d_ba = sum(primary_d_ba) / (len(MOUSE_IDS) * WINDOW_TRIALS)
    conditions = {
        "primary_mean_interaction_gt_zero": mean_primary_interaction > 0,
        "p_exact_one_sided_lt_alpha": signflip["p_exact_one_sided"] < ALPHA,
        "mean_opto_minus_control_B_to_Aprime_gt_zero": mean_d_ba > 0,
        "omission_inclusive_mean_interaction_gt_zero": (
            mean_sensitivity_interaction > 0
        ),
    }
    supported = all(conditions.values())

    aggregate_cross: Counter[str] = Counter()
    aggregate_mismatch = 0
    for item in results:
        aggregate_cross.update(item["outcomes_dirout_crosstab_all_session_trials"])
        aggregate_mismatch += int(item["valid_outcome_dirout_mismatch_count"])

    return {
        "status": (
            "D3_NDNF_COMPLEX_RELEARNING_SPECIFIC_IMPAIRMENT_SUPPORTED"
            if supported
            else "D3_NDNF_COMPLEX_RELEARNING_SPECIFIC_IMPAIRMENT_NOT_SUPPORTED"
        ),
        "endpoint_definition": {
            "independent_unit": "mouse",
            "mouse_count": len(MOUSE_IDS),
            "window_trials": WINDOW_TRIALS,
            "primary": "first 20 post-switch right trials with Outcomes[:,0] in {0,1}",
            "primary_error": "1 - Outcomes[:,0]",
            "sensitivity": "first 20 post-switch right trials excluding Outcomes[:,0] == -1",
            "sensitivity_error": "Outcomes[:,0] != 1",
            "alpha": ALPHA,
        },
        "schema_receipt": {
            "stratum_count": len(strata),
            "minimum_primary_eligible_count": min(
                int(stratum.primary_eligible.size) for stratum in strata
            ),
            "minimum_sensitivity_eligible_count": min(
                int(stratum.sensitivity_eligible.size) for stratum in strata
            ),
            "all_gates": "PASS",
        },
        "source_qc": {
            "outcomes_dirout_crosstab_all_transition_session_trials": dict(
                sorted(aggregate_cross.items())
            ),
            "valid_outcome_dirout_mismatch_count": aggregate_mismatch,
            "dirout_used_for_endpoint": False,
        },
        "strata": results,
        "per_mouse": mouse_results,
        "aggregate": {
            "primary_mean_complexity_interaction_error_rate": (
                mean_primary_interaction
            ),
            "primary_median_complexity_interaction_error_rate": float(
                np.median(primary_interactions) / WINDOW_TRIALS
            ),
            "primary_positive_mouse_count": int(
                sum(value > 0 for value in primary_interactions)
            ),
            "primary_zero_mouse_count": int(
                sum(value == 0 for value in primary_interactions)
            ),
            "primary_mean_opto_minus_control_A_to_B_error_rate": (
                sum(primary_d_ab) / (len(MOUSE_IDS) * WINDOW_TRIALS)
            ),
            "primary_mean_opto_minus_control_B_to_Aprime_error_rate": mean_d_ba,
            "sensitivity_mean_complexity_interaction_error_rate": (
                mean_sensitivity_interaction
            ),
            "signflip": signflip,
            "decision_conditions": conditions,
        },
    }


def read_execution_lock(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise ExecutionLockError(f"source lock not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required_columns = {"artifact_role", "path", "bytes", "sha256", "version"}
        if reader.fieldnames is None or set(reader.fieldnames) != required_columns:
            raise ExecutionLockError(
                f"source lock columns {reader.fieldnames} != {sorted(required_columns)}"
            )
        rows = list(reader)
    roles = [row["artifact_role"] for row in rows]
    if len(roles) != len(set(roles)) or set(roles) != LOCK_ROLES:
        raise ExecutionLockError(f"source lock roles differ: {roles}")
    return {row["artifact_role"]: row for row in rows}


def verify_execution_lock(
    repo_root: Path, source_lock: Path, archive: Path
) -> dict[str, Any]:
    if not repo_root.is_dir():
        raise ExecutionLockError(f"repo root not found: {repo_root}")
    rows = read_execution_lock(source_lock)
    expected_paths = {
        "analysis_runner": Path(__file__).resolve(),
        "provider_archive": archive.resolve(),
        "python_runtime": Path(sys.executable).resolve(),
        "numpy_runtime": Path(np.__file__).resolve(),
        "scipy_runtime": Path(scipy.__file__).resolve(),
    }
    verified: dict[str, Any] = {}
    for role, row in rows.items():
        locked_path = Path(row["path"])
        if not locked_path.is_absolute():
            locked_path = repo_root / locked_path
        locked_path = locked_path.resolve()
        if role in expected_paths and normalized_path(locked_path) != normalized_path(
            expected_paths[role]
        ):
            raise ExecutionLockError(
                f"{role} path {locked_path} != {expected_paths[role]}"
            )
        if not locked_path.is_file():
            raise ExecutionLockError(f"{role} file not found: {locked_path}")
        actual_bytes = locked_path.stat().st_size
        actual_sha256 = sha256_file(locked_path)
        if actual_bytes != int(row["bytes"]) or actual_sha256 != row["sha256"]:
            raise ExecutionLockError(
                f"{role} bytes/hash {actual_bytes}/{actual_sha256} do not match lock"
            )
        verified[role] = {
            "path": str(locked_path),
            "bytes": actual_bytes,
            "sha256": actual_sha256,
            "version": row["version"],
        }

    runtime_versions = {
        "python_runtime": platform.python_version(),
        "numpy_runtime": np.__version__,
        "scipy_runtime": scipy.__version__,
    }
    expected_versions = {
        "python_runtime": EXPECTED_PYTHON_VERSION,
        "numpy_runtime": EXPECTED_NUMPY_VERSION,
        "scipy_runtime": EXPECTED_SCIPY_VERSION,
    }
    if normalized_path(Path(sys.executable)) != normalized_path(
        EXPECTED_PYTHON_EXECUTABLE
    ):
        raise ExecutionLockError(f"unexpected Python executable: {sys.executable}")
    for role, actual_version in runtime_versions.items():
        if (
            actual_version != expected_versions[role]
            or rows[role]["version"] != actual_version
        ):
            raise ExecutionLockError(
                f"{role} version {actual_version}/{rows[role]['version']} != "
                f"{expected_versions[role]}"
            )
    return {
        "source_lock_path": str(source_lock.resolve()),
        "source_lock_sha256": sha256_file(source_lock),
        "artifacts": verified,
    }


def run_endpoint(
    repo_root: Path, source_lock: Path, archive_path: Path
) -> dict[str, Any]:
    lock_receipt = verify_execution_lock(repo_root, source_lock, archive_path)
    archive, source_receipt = verify_archive(archive_path)
    try:
        strata = load_and_gate(archive)
    finally:
        archive.close()
    result = compute_endpoints(strata)
    result["lineage"] = "ALT_BIO_D3_NDNF_COMPLEX_RELEARNING_v1"
    result["execution_lock"] = lock_receipt
    result["provider_source"] = source_receipt
    result["runtime"] = {
        "python_executable": sys.executable,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    result["interpretation_ceiling"] = (
        "source_locked_component_result; condition order and period/carryover "
        "unidentified; transition complexity confounded with session order; "
        "delta_W, delta_tau, and delta_g not observed"
    )
    return result


def write_json_once(path: Path, payload: dict[str, Any]) -> None:
    if not path.parent.is_dir():
        raise ExecutionLockError(f"output parent does not exist: {path.parent}")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Source-locked Maristany NDNF paired relearning endpoint"
    )
    parser.add_argument("--mode", choices=("endpoint",), required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    if args.output_json.exists():
        print(f"refusing to overwrite existing output: {args.output_json}", file=sys.stderr)
        return 2
    try:
        result = run_endpoint(
            args.repo_root.resolve(), args.source_lock.resolve(), args.archive.resolve()
        )
    except SourceError as exc:
        result = {"status": "D3_SOURCE_BLOCKED", "error": str(exc)}
    except SchemaError as exc:
        result = {"status": "D3_SCHEMA_BLOCKED", "error": str(exc)}
    except QualityError as exc:
        result = {"status": "D3_BLOCKED_QUALITY", "error": str(exc)}
    except ExecutionLockError as exc:
        result = {"status": "D3_EXECUTION_LOCK_BLOCKED", "error": str(exc)}

    write_json_once(args.output_json.resolve(), result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "output_json": str(args.output_json.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 2 if "BLOCKED" in result["status"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
